import os
import tempfile
import unittest

from configuration import Config, FiltersConfig, LLMConfig, OutlookConfig, TrelloConfig, DatabaseConfig
from configuration.configuration_service import ConfigStorage, FileConfigStorage, ConfigurationService


class DummyStorage(ConfigStorage):
    """In-memory dummy storage for testing ConfigurationService."""

    def __init__(self):
        self.store = None

    def read(self) -> Config:
        return self.store

    def write(self, config: Config) -> None:
        self.store = config


class TestConfigurationService(unittest.TestCase):
    """Test suite for ConfigurationService using a dummy storage."""

    def setUp(self):
        self.storage = DummyStorage()
        self.service = ConfigurationService(self.storage)
        self.test_config = Config(
            database=DatabaseConfig(name="db", user="u", password="p", host="h", port=1),
            email={"outlook": OutlookConfig(
                name="outlook", tenant_id="tid", client_id="cid",
                client_secret="secret", redirect_uri="uri"
            )},
            board={"trello": TrelloConfig(
                name="trello", api_key="key", api_token="token", board="board"
            )},
            filters=FiltersConfig(recipients=["a@example.com"]),
            llm_config=LLMConfig(host="h", model="m", api_key="k", provider="p"),
            confidence_level=0.5
        )

    def test_retrieve_before_update_returns_none(self):
        self.assertIsNone(self.service.retrieve())

    def test_update_and_retrieve(self):
        self.service.update(self.test_config)
        retrieved = self.service.retrieve()
        self.assertIs(retrieved, self.test_config)


class TestFileConfigStorage(unittest.TestCase):
    """Test suite for FileConfigStorage with actual file operations."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.test_dir, "config_test.yaml")
        self.storage = FileConfigStorage(self.file_path)
        self.test_config = Config(
            database=DatabaseConfig(name="db", user="u", password="p", host="h", port=1),
            email={"outlook": OutlookConfig(
                name="outlook", tenant_id="tid", client_id="cid",
                client_secret="secret", redirect_uri="uri"
            )},
            board={"trello": TrelloConfig(
                name="trello", api_key="key", api_token="token", board="board"
            )},
            filters=FiltersConfig(recipients=["a@example.com"]),
            llm_config=LLMConfig(host="h", model="m", api_key="k", provider="p"),
            confidence_level=0.5
        )

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        os.rmdir(self.test_dir)

    def test_read_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.storage.read()

    def test_write_and_read(self):
        self.storage.write(self.test_config)
        loaded = self.storage.read()
        self.assertEqual(loaded, self.test_config)


if __name__ == "__main__":
    unittest.main()
