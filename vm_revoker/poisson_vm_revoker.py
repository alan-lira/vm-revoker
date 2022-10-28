from logging import basicConfig, getLogger, INFO
from pathlib import Path
from random import choice, expovariate, randrange
from re import search
from threading import Thread
from time import sleep
from vm_manager.ec2_vm_manager import EC2VMManager


class PoissonVMRevoker:
    """
    Implementation of the Poisson process to simulate virtual machines (VMs) revocation.

    average_time_between_events_in_seconds : the average interval of time in seconds between events' arrival.

    lambda_rate : the average number of events per second (event rate or rate parameter).

    stopping_criterion : the stopping criterion for the Poisson process.
    Supported criteria: max_number_of_observable_events | max_observation_length_in_seconds

    max_number_of_observable_events : the maximum number of observable events.

    max_observation_length_in_seconds : the maximum observation length in seconds for events to arrive.

    vms_revoking_behavior : the behavior of the simulated revocations.
    Supported behaviors: terminate | reboot

    aws_config_file : the AWS configuration file.

    logging_directory : the directory to save execution logs.
    """
    def __init__(self,
                 average_time_between_events_in_seconds: float,
                 lambda_rate: float,
                 stopping_criterion: str,
                 max_number_of_observable_events: int,
                 max_observation_length_in_seconds: float,
                 vms_revoking_behavior: str,
                 aws_config_file: Path,
                 logging_directory: Path) -> None:
        self.__average_time_between_events_in_seconds = average_time_between_events_in_seconds
        self.__lambda_rate = lambda_rate
        self.__stopping_criterion = stopping_criterion
        self.__max_number_of_observable_events = max_number_of_observable_events
        self.__max_observation_length_in_seconds = max_observation_length_in_seconds
        self.__vms_revoking_behavior = vms_revoking_behavior
        self.__aws_config_file = aws_config_file
        self.__logging_directory = logging_directory
        self.__arrival_times_in_seconds = []
        self.__inter_arrival_times_in_seconds = []
        self.__vms_list = []
        self.__logger = None

    def __set_logger(self) -> None:
        random_execution_id = randrange(start=1, stop=99999999)
        logger_name = "vm-revoker_execution_id_" + str(random_execution_id) + ".log"
        basicConfig(filename=Path(self.__logging_directory).joinpath(logger_name),
                    format="%(asctime)s %(message)s",
                    level=INFO)
        self.__logger = getLogger()

    def __calculate_inter_arrival_time_in_seconds(self) -> float:
        return expovariate(self.__lambda_rate)

    def __generate_arrival_times_lists_in_seconds(self) -> None:
        arrival_time_in_seconds = 0
        if self.__stopping_criterion == "max_number_of_observable_events":
            while True:
                inter_arrival_time = self.__calculate_inter_arrival_time_in_seconds()
                self.__inter_arrival_times_in_seconds.append(inter_arrival_time)
                arrival_time_in_seconds = arrival_time_in_seconds + inter_arrival_time
                if len(self.__arrival_times_in_seconds) == self.__max_number_of_observable_events:
                    break
                self.__arrival_times_in_seconds.append(arrival_time_in_seconds)
        elif self.__stopping_criterion == "max_observation_length_in_seconds":
            while True:
                inter_arrival_time = self.__calculate_inter_arrival_time_in_seconds()
                self.__inter_arrival_times_in_seconds.append(inter_arrival_time)
                arrival_time_in_seconds = arrival_time_in_seconds + inter_arrival_time
                if arrival_time_in_seconds > self.__max_observation_length_in_seconds:
                    break
                self.__arrival_times_in_seconds.append(arrival_time_in_seconds)

    def __print_lambda_rate(self) -> None:
        lambda_rate_message = "Lambda Rate λ (Average Number of Events per Second): 1/{0} = {1}" \
            .format(self.__average_time_between_events_in_seconds,
                    self.__lambda_rate)
        print("-------\n" + lambda_rate_message)
        self.__logger.info(lambda_rate_message)

    def __print_stopping_criterion(self) -> None:
        stopping_criterion_variable = self.__max_number_of_observable_events \
            if self.__stopping_criterion == "max_number_of_observable_events" \
            else self.__max_observation_length_in_seconds
        stopping_criterion_message = "Stopping Criterion: {0} = {1}" \
            .format(self.__stopping_criterion,
                    stopping_criterion_variable)
        print(stopping_criterion_message + "\n-------")
        self.__logger.info(stopping_criterion_message)

    def __print_vms_revoking_behavior(self) -> None:
        vms_revoking_behavior_message = "VMs Revoking Behavior: {0}" \
            .format(self.__vms_revoking_behavior)
        print(vms_revoking_behavior_message + "\n-------")
        self.__logger.info(vms_revoking_behavior_message)

    def __print_arrival_times_lists_in_seconds(self) -> None:
        arrival_times_notation_message = "{0}\n{1}\n{2}" \
            .format("IAT: Inter-Arrival Time in Seconds (Exponential Distribution)",
                    "AT: Arrival Time in Seconds (Gamma Distribution)",
                    "IAT \t\t AT")
        print(arrival_times_notation_message)
        self.__logger.info(arrival_times_notation_message)
        arrival_times_message = ""
        for i in range(len(self.__arrival_times_in_seconds)):
            arrival_times_message = "{0} \t\t {1}" \
                .format(round(self.__inter_arrival_times_in_seconds[i], 2),
                        round(self.__arrival_times_in_seconds[i], 2))
            print(arrival_times_message)
        print("-------")
        self.__logger.info(arrival_times_message)

    def __get_aws_config_region_name(self) -> str:
        aws_region = None
        with open(self.__aws_config_file, mode="r") as aws_config_file:
            for line in iter(lambda: aws_config_file.readline(), ""):
                match_aws_region = search("region = (.*)$", line)
                if match_aws_region:
                    aws_region = match_aws_region.groups()[0]
        return aws_region

    def __monitor_and_terminate_vms_list(self,
                                         arguments_dictionary: dict) -> None:
        service_name = arguments_dictionary.get("service_name")
        region_name = arguments_dictionary.get("region_name")
        ec2vmm = EC2VMManager(service_name=service_name,
                              region_name=region_name)
        start_message = "Starting the Poisson Process to Simulate VMs Revocation..."
        print(start_message)
        self.__logger.info(start_message)
        event_counter = 1
        while self.__inter_arrival_times_in_seconds and self.__arrival_times_in_seconds:
            next_inter_arrival_time = self.__inter_arrival_times_in_seconds.pop(0)
            next_arrival_time = self.__arrival_times_in_seconds.pop(0)
            sleep(next_inter_arrival_time)
            active_vms_list = ec2vmm.get_active_ec2_instances_list(self.__vms_list)
            if active_vms_list:
                vm_to_revoke = choice(active_vms_list)
                ec2vmm.terminate_ec2_instance(vm_to_revoke.id)
                active_vms_list.remove(vm_to_revoke)
                revoke_message = "\t t{0} = {1} s: \t VM instance ID = '{2}' revoked (terminated)!" \
                    .format(event_counter,
                            round(next_arrival_time, 2),
                            vm_to_revoke.id)
                print(revoke_message)
                self.__logger.info(revoke_message)
            else:
                non_revoke_message = "\t t{0} = {1} s: \t Event occurred, but no active VM instances to revoke!" \
                    .format(event_counter,
                            round(next_arrival_time, 2))
                print(non_revoke_message)
                self.__logger.info(non_revoke_message)
            event_counter += 1
        end_message = "Poisson Process Simulation Completed!"
        print(end_message)
        self.__logger.info(end_message)

    def __monitor_and_reboot_vms_list(self,
                                      arguments_dictionary: dict) -> None:
        service_name = arguments_dictionary.get("service_name")
        region_name = arguments_dictionary.get("region_name")
        ec2vmm = EC2VMManager(service_name=service_name,
                              region_name=region_name)
        start_message = "Starting the Poisson Process to Simulate VMs Revocation..."
        print(start_message)
        self.__logger.info(start_message)
        event_counter = 1
        active_vms_list = ec2vmm.get_active_ec2_instances_list(self.__vms_list)
        while self.__inter_arrival_times_in_seconds and self.__arrival_times_in_seconds:
            next_inter_arrival_time = self.__inter_arrival_times_in_seconds.pop(0)
            next_arrival_time = self.__arrival_times_in_seconds.pop(0)
            sleep(next_inter_arrival_time)
            if active_vms_list:
                vm_to_revoke = choice(active_vms_list)
                ec2vmm.reboot_ec2_instance(vm_to_revoke.id)
                active_vms_list.remove(vm_to_revoke)
                revoke_message = "\t t{0} = {1} s: \t VM instance ID = '{2}' revoked (rebooted)!" \
                    .format(event_counter,
                            round(next_arrival_time, 2),
                            vm_to_revoke.id)
                print(revoke_message)
                self.__logger.info(revoke_message)
            else:
                non_revoke_message = "\t t{0} = {1} s: \t Event occurred, but no active VM instances to revoke!" \
                    .format(event_counter,
                            round(next_arrival_time, 2))
                print(non_revoke_message)
                self.__logger.info(non_revoke_message)
            event_counter += 1
        end_message = "Poisson Process Simulation Completed!"
        print(end_message)
        self.__logger.info(end_message)

    def start(self) -> None:
        # Set logger
        self.__set_logger()
        # Print lambda rate
        self.__print_lambda_rate()
        # Print stopping criterion
        self.__print_stopping_criterion()
        # Print VMs revoking behavior
        self.__print_vms_revoking_behavior()
        # Generate inter-arrival times and arrival times lists
        self.__generate_arrival_times_lists_in_seconds()
        # Print inter-arrival times and arrival times lists
        self.__print_arrival_times_lists_in_seconds()
        # Set target simulated revocation function according to the revoking behavior
        target_simulated_revocation_function = None
        if self.__vms_revoking_behavior == "terminate":
            target_simulated_revocation_function = self.__monitor_and_terminate_vms_list
        elif self.__vms_revoking_behavior == "reboot":
            target_simulated_revocation_function = self.__monitor_and_reboot_vms_list
        # Get AWS config region name
        region_name = self.__get_aws_config_region_name()
        # Set target simulated revocation function arguments dictionary
        arguments_dictionary = {"service_name": "ec2",
                                "region_name": region_name}
        # Start VMs list's monitoring and revoking thread
        vms_list_monitor_thread = Thread(target=target_simulated_revocation_function,
                                         name="vms_list_monitoring_and_revoking_thread",
                                         args=[arguments_dictionary],
                                         daemon=False)
        vms_list_monitor_thread.start()

    def load_vm_instances_ids_list_from_file(self,
                                             vm_instances_ids_list_file: Path) -> None:
        with open(vm_instances_ids_list_file) as instances_list:
            instances = [instance.rstrip() for instance in instances_list]
        self.__vms_list = [instance for instance in instances if instance]
        vm_instances_list_message = "VM Instances IDs List: " + str(self.__vms_list)
        print(vm_instances_list_message + "\n-------")
        self.__logger.info(vm_instances_list_message)
