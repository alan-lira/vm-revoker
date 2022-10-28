from configparser import ConfigParser
from pathlib import Path
from typing import Any


def validate_number_of_arguments_provided(argv_list: list,
                                          number_of_arguments_expected: int,
                                          arguments_expected_list: list) -> None:
    number_of_arguments_provided = len(argv_list) - 1
    if number_of_arguments_provided != number_of_arguments_expected:
        number_of_arguments_expected_message = \
            "".join([str(number_of_arguments_expected),
                     " arguments were" if number_of_arguments_expected > 1 else " argument was"])
        number_of_arguments_provided_message = \
            "".join([str(number_of_arguments_provided),
                     " arguments were" if number_of_arguments_provided > 1 else " argument was"])
        invalid_number_of_arguments_message = \
            "Invalid number of arguments provided!\n" \
            "{0} expected: {1}\n" \
            "{2} provided: {3}".format(number_of_arguments_expected_message,
                                       ", ".join(arguments_expected_list),
                                       number_of_arguments_provided_message,
                                       ", ".join(argv_list[1:]))
        raise ValueError(invalid_number_of_arguments_message)


def validate_file_existence(file_path: Path) -> None:
    if not file_path.is_file():
        file_not_found_message = "'{0}' not found. The application will halt!".format(str(file_path))
        raise FileNotFoundError(file_not_found_message)


def create_directory(directory_path: Path) -> None:
    directory_path.mkdir(exist_ok=True)


def load_config_parser(config_file_path: Path) -> ConfigParser:
    config_parser = ConfigParser()
    config_parser.optionxform = str  # Case preservation of all section names
    config_parser.read(filenames=config_file_path,
                       encoding="utf-8")
    return config_parser


def get_value_from_sections_key(config_parser: ConfigParser,
                                section: str,
                                key: str) -> Any:
    return config_parser.get(section, key)
