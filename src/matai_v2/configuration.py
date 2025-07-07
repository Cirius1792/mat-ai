import yaml
from typing import List
from dataclasses import dataclass, field

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class OutlookConfig:
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""


@dataclass
class TrelloConfig():
    api_key: str = ""
    api_token: str = ""
    board: str = ""


@dataclass
class EmailFilter:
    recipients: List[str] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    path: str = "matai.db"


@dataclass
class LLMConfig:
    # TODO: all the fields should be mandatory
    host: str = ""
    model: str = ""
    api_key: str = ""


@dataclass
class Config:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    outlook_config: OutlookConfig = field(default_factory=OutlookConfig)
    trello_config: TrelloConfig = field(default_factory=TrelloConfig)
    filters: EmailFilter = field(default_factory=EmailFilter)
    llm_config: LLMConfig = field(default_factory=LLMConfig)
   # confidence_level: float = 0.85

    def to_dict(self) -> dict:
        """Convert config to dictionary format"""
        return {
            'database': self.database.__dict__,
            'outlook_config': self.outlook_config.__dict__,
            'trello_config': self.trello_config.__dict__,
            'filters': self.filters.__dict__,
            'llm_config': self.llm_config.__dict__,
            # 'confidence_level': self.confidence_level
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create config from dictionary data"""
        database_config = DatabaseConfig(**data.get('database', {}))
        email_configs = OutlookConfig(**data['outlook_config'])

        trello_config = TrelloConfig(**data['trello_config'])
        # for k, v in data['board'].items():
        #     if k == 'trello':
        #         board_configs[k] = TrelloConfig(**v)

        # database_config = DatabaseConfig()
        # if 'database' in data:
        #     database_config = DatabaseConfig(**data['database'])
        filters = EmailFilter()
        if 'filters' in data:
            filters = EmailFilter(**data['filters'])
        # llm_config = LLMConfig(host="",
        #                        model="",
        #                        api_key=""
        #                        )
        llm_config = LLMConfig()
        if 'llm_config' in data:
            llm_config = LLMConfig(**data['llm_config'])
        return cls(
            database=database_config,
            outlook_config=email_configs,
            trello_config=trello_config,
            filters=filters,
            llm_config=llm_config,
            # confidence_level=data['confidence_level']
        )


def create_sample_config() -> Config:
    """Create a sample configuration with default values."""
    return Config(
        database=DatabaseConfig(path="matai.db"),
        outlook_config=OutlookConfig(
            tenant_id="your_tenant_id",
            client_id="your_client_id",
            client_secret="your_client_secret",
            redirect_uri="http://localhost:8000/callback"
        ),
        trello_config=TrelloConfig(
            api_key="your_api_key",
            api_token="your_api_token",
            board="your_board_id"
        ),
        llm_config=LLMConfig(
            host="https://api.example.com",
            model="gpt-3.5-turbo",
            api_key="your_llm_api_key",
        )
    )


def save_config_to_yaml(config: Config, file_path='config.yaml'):
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

    path = Path(file_path)
    # Ensure the directory exists before writing
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open('w') as file:
        yaml.safe_dump(config.to_dict(), file, default_flow_style=False)


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
        try:
            config_dict = yaml.safe_load(file)
        except yaml.constructor.ConstructorError:
            # Fallback for legacy YAML files containing Python-specific tags
            file.seek(0)
            config_dict = yaml.unsafe_load(file)
        config = Config.from_dict(config_dict)
        logger.info("Loaded configuration: %s", config)
        return config
