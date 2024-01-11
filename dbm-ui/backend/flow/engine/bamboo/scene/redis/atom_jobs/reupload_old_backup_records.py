# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-DB管理系统(BlueKing-BK-DBM) available.
Copyright (C) 2017-2023 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at https://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import base64
import json
import logging
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict

from django.utils.translation import ugettext as _

from backend.components.mysql_backup.client import RedisBackupApi
from backend.configuration.constants import DBType
from backend.constants import DEFAULT_BK_CLOUD_ID
from backend.flow.consts import WriteContextOpType
from backend.flow.engine.bamboo.scene.common.builder import SubBuilder
from backend.flow.engine.bamboo.scene.common.get_file_list import GetFileList
from backend.flow.plugins.components.collections.redis.exec_actuator_script import ExecuteDBActuatorScriptComponent
from backend.flow.plugins.components.collections.redis.exec_shell_script import ExecuteShellScriptComponent
from backend.flow.plugins.components.collections.redis.get_redis_payload import GetRedisActPayloadComponent
from backend.flow.plugins.components.collections.redis.trans_flies import TransFileComponent
from backend.flow.utils.redis.redis_act_playload import RedisActPayload
from backend.flow.utils.redis.redis_context_dataclass import ActKwargs

logger = logging.getLogger("flow")


def get_last_n_days_backup_records(n_days: int, bk_cloud_id: 0, server_ip: str) -> list:
    """逐天获取最近n天的备份记录"""
    records_unique = set()
    records_ret = []
    now = datetime.now()
    for i in range(n_days):
        start_date = (now - timedelta(days=i + 1)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (now - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
        query_param = {
            "bk_cloud_id": bk_cloud_id,
            "source_ip": server_ip,
            "begin_date": start_date,
            "end_date": end_date,
            "filename": "",
        }
        query_result = RedisBackupApi.query(query_param)
        for record in query_result:
            if record["task_id"] in records_unique:
                continue
            records_unique.add(record["task_id"])
            records_ret.append(record)
    return records_ret


def RedisReuploadOldBackupRecordsAtomJob(root_id, ticket_data, sub_kwargs: ActKwargs, params: Dict) -> SubBuilder:
    """### 将备份记录重新上报到bklog
    params (Dict): {
        "bk_biz_id": "3",
        "bk_cloud_id": 0,
        "server_ip": "a.a.a.a",
        "server_ports":[30000,30001,30002],
        "cluster_domain":"cache.test.test.db",
        "cluster_type":"TwemproxyRedisInstance",
        "meta_role":"redis_slave",
        "server_shards":{
            "a.a.a.a:30000":"0-14999",
            "a.a.a.a:30001":"15000-29999",
            "a.a.a.a:30002":"30000-44999"
        },
        "ndays": 7
    }
    """
    # 查询历史备份记录
    bk_biz_id = params["bk_biz_id"]
    bk_cloud_id = params.get("bk_cloud_id", DEFAULT_BK_CLOUD_ID)
    server_ip = params["server_ip"]
    ndays = params.get("ndays", 7) + 1
    query_result = get_last_n_days_backup_records(ndays, bk_cloud_id, server_ip)
    encode_str = str(base64.b64encode(json.dumps(query_result).encode("utf-8")), "utf-8")

    local_file = "/data/dbbak/last_n_days_gcs_backup_record.txt"
    act_kwargs = deepcopy(sub_kwargs)
    sub_pipeline = SubBuilder(root_id=root_id, data=ticket_data)

    sub_pipeline.add_act(
        act_name=_("初始化配置"), act_component_code=GetRedisActPayloadComponent.code, kwargs=asdict(act_kwargs)
    )
    # 下发介质包
    trans_files = GetFileList(db_type=DBType.Redis)
    act_kwargs.exec_ip = server_ip
    act_kwargs.file_list = trans_files.redis_actuator_backend()
    sub_pipeline.add_act(
        act_name=_("{}下发介质包").format(server_ip), act_component_code=TransFileComponent.code, kwargs=asdict(act_kwargs)
    )
    # 保存备份记录到本地文件
    act_kwargs.exec_ip = server_ip
    act_kwargs.write_op = WriteContextOpType.APPEND.value
    act_kwargs.cluster[
        "shell_command"
    ] = f"""
cat > {local_file} << EOF
{encode_str}
EOF
    """
    sub_pipeline.add_act(
        act_name=_("{}-gcs上备份记录保存到本地文件:{}").format(server_ip, local_file),
        act_component_code=ExecuteShellScriptComponent.code,
        kwargs=asdict(act_kwargs),
    )
    # 上报备份记录到bklog
    act_kwargs.exec_ip = server_ip
    act_kwargs.cluster = {
        "bk_biz_id": str(bk_biz_id),
        "bk_cloud_id": bk_cloud_id,
        "server_ip": server_ip,
        "server_ports": params["server_ports"],
        "cluster_domain": params["cluster_domain"],
        "cluster_type": params["cluster_type"],
        "meta_role": params["meta_role"],
        "server_shards": params.get("server_shards", {}),
        "records_file": local_file,
        "force": True,
    }
    act_kwargs.get_redis_payload_func = RedisActPayload.redis_reupload_old_backup_records_payload.__name__
    sub_pipeline.add_act(
        act_name=_("{}-备份记录上报到bklog").format(server_ip),
        act_component_code=ExecuteDBActuatorScriptComponent.code,
        kwargs=asdict(act_kwargs),
    )
    return sub_pipeline.build_sub_process(sub_name=_("{}-重新上报备份记录").format(server_ip))
