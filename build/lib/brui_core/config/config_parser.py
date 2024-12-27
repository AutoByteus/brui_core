from abc import ABC, abstractmethod
from brui_core.singleton_meta import ABCSingletonMeta
import toml
import os

class ConfigParser(ABC):
    """
    ConfigParser is an abstract base class for configuration file parsers.
    """

    @abstractmethod
    def parse(self, config_file: str) -> dict:
        pass


class TOMLConfigParser(ConfigParser):
    """
    TOMLConfigParser is a class that parses TOML configuration files.
    """

    def parse(self, config_file: str) -> dict:
        with open(config_file, "r") as file:
            return toml.load(file)


class EnvironmentConfigParser(ConfigParser):
    """
    EnvironmentConfigParser is a class that reads the config path from an environment variable
    and loads the config using the TOMLConfigParser.
    """

    def __init__(self, env_var: str):
        self.env_var = env_var

    def parse(self) -> dict:
        config_path = os.environ.get(self.env_var)
        if config_path is None:
            raise ValueError(f"Environment variable '{self.env_var}' is not set.")

        toml_parser = TOMLConfigParser()
        return toml_parser.parse(config_path)