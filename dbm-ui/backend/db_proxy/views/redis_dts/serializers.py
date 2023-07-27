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
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from backend.db_proxy.views.serialiers import BaseProxyPassSerialier


class IsDtsserverInBlacklistSerializer(BaseProxyPassSerialier):
    ip = serializers.IPAddressField(help_text=_("DTS_server IP"), required=True)


class DtsJobSerializer(BaseProxyPassSerialier):
    bill_id = serializers.IntegerField(help_text=_("任务ID"), required=True)
    src_cluster = serializers.CharField(help_text=_("源集群"), required=True)
    dst_cluster = serializers.CharField(help_text=_("目标集群"), required=True)


class DtsJobTasksSerializer(BaseProxyPassSerialier):
    bill_id = serializers.IntegerField(help_text=_("任务ID"), required=True)
    src_cluster = serializers.CharField(help_text=_("源集群"), required=True)
    dst_cluster = serializers.CharField(help_text=_("目标集群"), required=True)


class DtsDistributeLockSerializer(BaseProxyPassSerialier):
    lockkey = serializers.CharField(help_text=_("锁key名"), required=True)
    holder = serializers.CharField(help_text=_("锁持有者"), required=True)
    ttl_sec = serializers.IntegerField(help_text=_("锁ttl时间(seconds)"), required=False)


class DtsServerMigatingTasksSerializer(BaseProxyPassSerialier):
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"), required=True)
    dts_server = serializers.IPAddressField(help_text=_("DTS_server IP"), required=True)
    db_type = serializers.CharField(help_text=_("db类型"), required=True)
    task_types = serializers.ListField(
        help_text=_("task类型列表"), child=serializers.CharField(), allow_empty=False, required=True
    )


class DtsServerMaxSyncPortSerializer(BaseProxyPassSerialier):
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"), required=True)
    dts_server = serializers.IPAddressField(help_text=_("DTS_server IP"), required=True)
    db_type = serializers.CharField(help_text=_("db类型"), required=True)
    task_types = serializers.ListField(
        help_text=_("task类型列表"), child=serializers.CharField(), allow_empty=False, required=True
    )


class DtsLast30DaysToExecTasksSerializer(BaseProxyPassSerialier):
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"), required=True)
    dts_server = serializers.IPAddressField(help_text=_("DTS_server IP"), required=True)
    db_type = serializers.CharField(help_text=_("db类型"), required=True)
    task_type = serializers.CharField(help_text=_("task类型"), required=True)
    limit = serializers.IntegerField(help_text=_("限制条数"), required=False)
    status = serializers.IntegerField(help_text=_("任务状态"), required=False)


class DtsLast30DaysToScheduleJobsSerializer(BaseProxyPassSerialier):
    bk_cloud_id = serializers.IntegerField(help_text=_("云区域ID"), required=True)
    max_data_size = serializers.IntegerField(help_text=_("最大数据量"), required=True)
    zone_name = serializers.CharField(help_text=_("城市名"), required=True)
    db_type = serializers.CharField(help_text=_("db类型"), required=True)


class DtsJobToScheduleTasksSerializer(BaseProxyPassSerialier):
    bill_id = serializers.IntegerField(help_text=_("任务ID"), required=True)
    src_cluster = serializers.CharField(help_text=_("源集群"), required=True)
    dst_cluster = serializers.CharField(help_text=_("目标集群"), required=True)


class DtsJobSrcIPRunningTasksSerializer(BaseProxyPassSerialier):
    bill_id = serializers.IntegerField(help_text=_("任务ID"), required=True)
    src_cluster = serializers.CharField(help_text=_("源集群"), required=True)
    dst_cluster = serializers.CharField(help_text=_("目标集群"), required=True)
    src_ip = serializers.IPAddressField(help_text=_("源redis slave IP"), required=True)
    task_types = serializers.ListField(
        help_text=_("task类型列表"), child=serializers.CharField(), allow_empty=False, required=True
    )


class DtsTaskByTaskIDSerializer(BaseProxyPassSerialier):
    task_id = serializers.IntegerField(help_text=_("子任务ID"), required=True)


class DtsTasksUpdateSerializer(BaseProxyPassSerialier):
    task_ids = serializers.ListField(
        help_text=_("子任务ID列表"), child=serializers.IntegerField(), allow_empty=False, required=True
    )
    col_to_val = serializers.DictField(child=serializers.CharField())


class DtsDataCopyBaseItemSLZ(serializers.Serializer):
    src_cluster = serializers.CharField(help_text=_("源集群"), required=True)
    src_cluster_password = serializers.CharField(help_text=_("源集群密码"), allow_blank=True)
    dst_cluster = serializers.CharField(help_text=_("目标集群"), required=True)
    dst_cluster_password = serializers.CharField(help_text=_("目标集群密码"), allow_blank=True)


class DtsTestRedisConnectionSLZ(BaseProxyPassSerialier):
    data_copy_type = serializers.CharField(help_text=_("数据复制类型"), required=True)
    infos = serializers.ListField(
        help_text=_("复制列表"), child=DtsDataCopyBaseItemSLZ(), allow_empty=False, required=True
    )
