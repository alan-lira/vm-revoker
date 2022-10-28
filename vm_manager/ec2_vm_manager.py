from boto3 import client, resource
from botocore.exceptions import ClientError
from typing import Any


class EC2VMManager:

    def __init__(self,
                 service_name: str,
                 region_name: str) -> None:
        self.__ec2_resource = resource(service_name=service_name, region_name=region_name)
        self.__ec2_client = client(service_name=service_name, region_name=region_name)

    def __get_ec2_instance_from_id(self,
                                   instance_id: str) -> Any:
        return self.__ec2_resource.Instance(instance_id)

    def get_active_ec2_instances_list(self,
                                      instances_id_list: list) -> list:
        active_ec2_instances_list = []
        for instance_id in instances_id_list:
            instance = self.__get_ec2_instance_from_id(instance_id)
            try:
                if instance and instance.state["Name"] == "running":
                    print(type(instance))
                    active_ec2_instances_list.append(instance)
            except ClientError:
                pass  # Instance entry removed by AWS
        return active_ec2_instances_list

    def reboot_ec2_instance(self,
                            instance_id: str) -> None:
        self.__ec2_client.reboot_instances(InstanceIds=[instance_id])

    def terminate_ec2_instance(self,
                               instance_id: str) -> None:
        self.__ec2_client.terminate_instances(InstanceIds=[instance_id])
