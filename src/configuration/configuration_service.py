"""
Configuration service module.
This module defines interfaces and implementations for persisting
and managing application configuration using different strategies.
"""
from abc import ABC, abstractmethod

from . import Config


class ConfigStorage(ABC):
    """Interface for configuration persistence strategies."""

    @abstractmethod
    def read(self) -> Config:
        """Read and return the configuration object."""
        ...

    @abstractmethod
    def write(self, config: Config) -> None:
        """Persist the given configuration object."""
        ...


class FileConfigStorage(ConfigStorage):
    """File-based configuration storage using YAML format."""

    def __init__(self, file_path: str = 'config.yaml') -> None:
        self._file_path = file_path

    def read(self) -> Config:
        """Load configuration from a YAML file."""
        return Config.load_config_from_yaml(self._file_path)

    def write(self, config: Config) -> None:
        """Save configuration to a YAML file."""
        Config.save_config_to_yaml(config, self._file_path)


class ConfigurationService:
    """Service for retrieving and updating application configuration."""

    def __init__(self, storage: ConfigStorage) -> None:
        self._storage = storage

    def retrieve(self) -> Config:
        """Retrieve the current stored configuration."""
        return self._storage.read()

    def update(self, config: Config) -> None:
        """Update and persist the current configuration."""
        self._storage.write(config)