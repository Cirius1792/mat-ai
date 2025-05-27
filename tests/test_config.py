import unittest
import tempfile
import os
from configuration import Config, FiltersConfig, LLMConfig, OutlookConfig, TrelloConfig, DatabaseConfig

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')
        
        # Sample test configuration
        self.test_email_config = OutlookConfig(
            name="test_outlook",
            tenant_id="test_tenant",
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost"
        )
        
        self.test_board_config = TrelloConfig(
            name="test_trello",
            api_key="test_key",
            api_token="test_token",
            board="test_board"
        )
        
        self.test_filters = FiltersConfig(
            recipients=["test@example.com"]
        )
        
        self.test_database_config = DatabaseConfig(
            name="test_db",
            user="test_user",
            password="test_pass",
            host="localhost",
            port=5432
        )

        self.test_config = Config(
            database=self.test_database_config,
            email={"outlook": self.test_email_config},
            board={"trello": self.test_board_config},
            filters=self.test_filters,
                        llm_config=LLMConfig(
                            host="",
                            api_key="", 
                            model="gpt-3.5-turbo",
            ),
            confidence_level=0.9
        )

    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_save_and_load_config(self):
        """Test saving and loading configuration works correctly"""
        # Save configuration
        Config.save_config_to_yaml(self.test_config, self.config_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.config_path))
        
        # Load configuration
        loaded_config = Config.load_config_from_yaml(self.config_path)
        
        # Verify loaded configuration matches original
        self.assertEqual(loaded_config.confidence_level, self.test_config.confidence_level)
        self.assertEqual(loaded_config.filters.recipients, self.test_config.filters.recipients)
        
        # Check email config
        self.assertEqual(
            loaded_config.email["outlook"].tenant_id,
            self.test_config.email["outlook"].tenant_id
        )
        
        # Check board config
        self.assertEqual(
            loaded_config.board["trello"].api_key,
            self.test_config.board["trello"].api_key
        )

        # Check database config
        self.assertEqual(
            loaded_config.database.name,
            self.test_config.database.name
        )
        self.assertEqual(
            loaded_config.database.user,
            self.test_config.database.user
        )
        self.assertEqual(
            loaded_config.database.port,
            self.test_config.database.port
        )

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file raises FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            Config.load_config_from_yaml("nonexistent.yaml")

    def test_save_invalid_config(self):
        """Test saving invalid configuration raises TypeError"""
        invalid_config = {"invalid": "config"}
        with self.assertRaises(TypeError):
            Config.save_config_to_yaml(invalid_config, self.config_path)

    def test_remove_recipient(self):
        """Test that removing a recipient from filters is saved correctly"""
        # Add a recipient to the filters if it's not already present
        if "remove@example.com" not in self.test_config.filters.recipients:
            self.test_config.filters.recipients.append("remove@example.com")
        # Save configuration with the new recipient
        Config.save_config_to_yaml(self.test_config, self.config_path)
        # Load configuration and verify the recipient exists
        loaded_config = Config.load_config_from_yaml(self.config_path)
        self.assertIn("remove@example.com", loaded_config.filters.recipients)
        # Remove the recipient and save again
        loaded_config.filters.recipients.remove("remove@example.com")
        Config.save_config_to_yaml(loaded_config, self.config_path)
        # Reload and verify the recipient has been removed
        updated_config = Config.load_config_from_yaml(self.config_path)
        self.assertNotIn("remove@example.com", updated_config.filters.recipients)

if __name__ == '__main__':
    unittest.main()
