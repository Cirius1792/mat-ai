import yaml
from abc import ABC
from typing import Dict, List
from dataclasses import dataclass, field

import logging 
logger = logging.getLogger(__name__)


@dataclass
class OutlookConfig:
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""


@dataclass
class BoardConfig(ABC):
    name: str = ""


@dataclass
class TrelloConfig(BoardConfig):
    api_key: str = ""
    api_token: str = ""
    board: str = ""


@dataclass
class FiltersConfig:
    recipients: List[str] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    name: str = "pmai_sqlite.db"
    user: str = "sqlite"
    password: str = ""
    host: str = ""
    port: int = 5432

@dataclass
class LLMConfig: 
    host: str = ""
    model: str = ""
    api_key: str = ""
    provider: str = ""

@dataclass
class Config:
    # database: DatabaseConfig
    outlook_config: OutlookConfig = field(default_factory=OutlookConfig)
    # board: Dict[str, BoardConfig]
    # filters: FiltersConfig
    llm_config: LLMConfig = field(default_factory=LLMConfig)
   # confidence_level: float = 0.85

    def to_dict(self) -> dict:
        """Convert config to dictionary format"""
        return {
            # 'database': self.database.__dict__,
            'outlook_config': self.outlook_config.__dict__,
            # 'board': {k: v.__dict__ for k, v in self.board.items()},
            # 'filters': self.filters.__dict__,
            # 'llm_config': self.llm_config.__dict__,
            # 'confidence_level': self.confidence_level
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create config from dictionary data"""
        email_configs = OutlookConfig(**data['outlook_config'])

        # board_configs = {}
        # for k, v in data['board'].items():
        #     if k == 'trello':
        #         board_configs[k] = TrelloConfig(**v)

        # database_config = DatabaseConfig()
        # if 'database' in data:
        #     database_config = DatabaseConfig(**data['database'])
        # filters = FiltersConfig()
        # if 'filters' in data:
        #     filters = FiltersConfig(**data['filters'])
        # llm_config = LLMConfig(host="", 
        #                        model="",
        #                        api_key=""
        #                        )
        llm_config = LLMConfig()
        if 'llm_config' in data:
            llm_config = LLMConfig(**data['llm_config'])
        return cls(
            # database=database_config,
            outlook_config=email_configs,
            # board=board_configs,
            # filters=filters,
            llm_config=llm_config,
            # confidence_level=data['confidence_level']
        )


def save_config_to_yaml(config:Config, file_path='config.yaml'):
    """Save configuration to YAML file

    Args:
        config: Config object to save
        file_path: Path to save YAML file

    Raises:
        TypeError: If config is not a Config instance
    """
    if not isinstance(config, Config):
        raise TypeError("config must be an instance of Config")

    logger.debug("Configuration: %s", config)
    logger.debug(f"Saving config to {file_path}")

    with open(file_path, 'w') as file:
        yaml.dump(config.to_dict(), file, default_flow_style=False)

def load_config_from_yaml(file_path='config.yaml') -> Config:
    """Load configuration from a YAML file.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        Config: Loaded configuration object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    logger.debug(f"Loading config from {file_path}")
    with open(file_path, 'r') as file:
        config_dict = yaml.safe_load(file)
        return Config.from_dict(config_dict)


