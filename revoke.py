from pathlib import Path
from sys import argv
from util.util import validate_number_of_arguments_provided, validate_file_existence, load_config_parser, \
    get_value_from_sections_key, create_directory
from vm_revoker.poisson_vm_revoker import PoissonVMRevoker


def main(argv_list: list) -> None:
    # Begin
    # Validate number of arguments provided
    number_of_arguments_expected = 1
    arguments_expected_list = ["vm_revoker_config_file"]
    validate_number_of_arguments_provided(argv_list,
                                          number_of_arguments_expected,
                                          arguments_expected_list)
    # Get VM Revoker config file
    vm_revoker_config_file = Path(argv_list[1])
    # Validate VM Revoker config file existence
    validate_file_existence(vm_revoker_config_file)
    # Load ConfigParser for VM Revoker config file
    vm_revoker_config_parser = load_config_parser(vm_revoker_config_file)
    # Get AWS config file
    aws_config_file = \
        Path(get_value_from_sections_key(vm_revoker_config_parser,
                                         "AWS Settings",
                                         "aws_config_file")).resolve()
    # Validate AWS config file existence
    validate_file_existence(aws_config_file)
    # Get VM instances ids list file
    vm_instances_ids_list_file = \
        Path(get_value_from_sections_key(vm_revoker_config_parser,
                                         "Input Settings",
                                         "vm_instances_ids_list_file")).resolve()
    # Validate VM instances ids list file existence
    validate_file_existence(vm_instances_ids_list_file)
    # Get logging directory
    logging_directory = \
        Path(get_value_from_sections_key(vm_revoker_config_parser,
                                         "Output Settings",
                                         "logging_directory")).resolve()
    # Create logging directory (if needed)
    create_directory(logging_directory)
    # Get VMs revoking behavior
    vms_revoking_behavior = str(get_value_from_sections_key(vm_revoker_config_parser,
                                                            "General Settings",
                                                            "vms_revoking_behavior"))
    # Get discrete probability distribution model
    discrete_probability_distribution_model = \
        get_value_from_sections_key(vm_revoker_config_parser,
                                    "General Settings",
                                    "discrete_probability_distribution_model")
    # Poisson discrete probability distribution
    if discrete_probability_distribution_model == "Poisson":
        # Get average time between events in seconds
        average_time_between_events_in_seconds = \
            int(get_value_from_sections_key(vm_revoker_config_parser,
                                            "Poisson Distribution Model Settings",
                                            "average_time_between_events_in_seconds"))
        # Get stopping criterion
        stopping_criterion = \
            str(get_value_from_sections_key(vm_revoker_config_parser,
                                            "Poisson Distribution Model Settings",
                                            "stopping_criterion"))
        # Get stopping criterion value
        max_observation_length_in_seconds = None
        max_number_of_observable_events = None
        if stopping_criterion == "max_observation_length_in_seconds":
            # Get max observation length in seconds
            max_observation_length_in_seconds = \
                int(get_value_from_sections_key(vm_revoker_config_parser,
                                                "Poisson Distribution Model Settings",
                                                "max_observation_length_in_seconds"))
        elif stopping_criterion == "max_number_of_observable_events":
            # Get max number of observable events
            max_number_of_observable_events = \
                int(get_value_from_sections_key(vm_revoker_config_parser,
                                                "Poisson Distribution Model Settings",
                                                "max_number_of_observable_events"))
        # Init PoissonVMRevoker object
        pvmr = PoissonVMRevoker(average_time_between_events_in_seconds=average_time_between_events_in_seconds,
                                lambda_rate=(1 / average_time_between_events_in_seconds),
                                stopping_criterion=stopping_criterion,
                                max_number_of_observable_events=max_number_of_observable_events,
                                max_observation_length_in_seconds=max_observation_length_in_seconds,
                                vms_revoking_behavior=vms_revoking_behavior,
                                aws_config_file=aws_config_file,
                                logging_directory=logging_directory)
        # Generate inter-arrival times and arrival times lists, and start monitoring and revoking the VMs (if any)
        pvmr.start()
        # Load VM instances ids list
        pvmr.load_vm_instances_ids_list_from_file(vm_instances_ids_list_file)
        # Delete PoissonVMRevoker object
        del pvmr
    # End
    exit(0)


if __name__ == "__main__":
    main(argv)
