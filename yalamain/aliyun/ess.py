# -*- coding:utf-8 -*-
from flask import current_app
from aliyunsdkcore.client import AcsClient
from aliyunsdkess.request.v20140828 import DescribeScalingGroupsRequest
from aliyunsdkess.request.v20140828 import DescribeScalingInstancesRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
import json


class AliyunESS(object):

    def __init__(self, region_id='cn-hangzhou'):
        self.access_key_id = current_app.config['ACCESS_KEY_ID']
        self.access_key_secret = current_app.config['ACCESS_KEY_SECRET']
        self.region_id = region_id

        self.client = AcsClient(self.access_key_id, self.access_key_secret, self.region_id)

    def aliyun_request(self, request):
        try:
            response = json.loads(self.client.do_action_with_exception(request))
        except ServerException as err:
            # 包含常见异常返回和公共错误码
            current_app.logger.error(err)
            return None
        except ClientException as err:
            current_app.logger.error(err)
            return None
        except Exception as err:
            current_app.logger.error(err)
            return None
        return response

    def describe_ess_groups(self):
        request = DescribeScalingGroupsRequest.DescribeScalingGroupsRequest()
        request.set_accept_format('json')
        response = self.aliyun_request(request)
        return response.get('ScalingGroups').get('ScalingGroup')

    def aliyun_describe_ess_groups_instances(self, scaling_group_id):
        """
        :获取指定scaling_group_id中的所有instances
        :param scaling_group_id: 弹性伸缩组ID
        :return: 指定Client所在Region，指定scaling_group_id的所有主机列表
        """
        ess_page_size = 50  # 阿里云ESS接口一次最多可返回50条数据
        ecs_page_size = 100  # 阿里云ECS接口一次最多可返回100条数据
        instance_id_list = []
        ecs_instance_list = []

        try:
            request = DescribeScalingInstancesRequest.DescribeScalingInstancesRequest()
            request.set_accept_format('json')
            request.set_ScalingGroupId(scaling_group_id)
            request.set_PageSize(PageSize=ess_page_size)

            response = json.loads(self.client.do_action_with_exception(request))
        except ClientException as e:
            current_app.logger.error(e)
            return []
        except ServerException as e:
            current_app.logger.error(e)
            return []
        except Exception as e:
            current_app.logger.error(e)
            return []

        if response is not None:
            instance_total_count = response.get('TotalCount')
            # 阿里云接口默认会返回50条数据，所以如果scaling_instance_list<50可直接处理，如果>50，进入条件instance_total_count > 50
            scaling_instance_list = response.get('ScalingInstances').get('ScalingInstance')
            for scaling_instance in scaling_instance_list:
                instance_id_list.append(scaling_instance.get('InstanceId', str(0)))
        else:
            current_app.logger.warning('Response is None.')
            return []

        if instance_total_count > 50:
            total_page_num = int(instance_total_count / ess_page_size) + 1
            page_num = 2

            while page_num <= total_page_num:
                # while按每次请求50条数据的方式处理instance_total_count>50
                request.set_PageNumber(PageNumber=page_num)
                response = json.loads(self.client.do_action_with_exception(request))
                if response is not None:
                    scaling_instance_list = response.get('ScalingInstances').get('ScalingInstance')
                    for scaling_instance in scaling_instance_list:
                        instance_id_list.append(scaling_instance.get('InstanceId', str(0)))
                else:
                    current_app.logger.warning('Response is None.')
                    continue
                page_num += 1

        # 因为阿里云SDK一次查询最长支持100个instance id，所以以100为长度对列表进行分段成新的列表
        instance_id_list_100s = [instance_id_list[x:x + 100] for x in range(0, len(instance_id_list), 100)]

        ecs_request = DescribeInstancesRequest.DescribeInstancesRequest()
        ecs_request.set_PageSize(PageSize=ecs_page_size)
        ecs_request.set_accept_format('json')

        for i in instance_id_list_100s:
            ecs_request.set_InstanceIds(i)

            ecs_response = json.loads(self.client.do_action_with_exception(ecs_request))
            if ecs_response is not None:
                ecs_list = ecs_response['Instances']['Instance']
                ecs_instance_list = ecs_instance_list + ecs_list
            else:
                current_app.logger.warning('Response is None.')
                continue
        return ecs_instance_list
