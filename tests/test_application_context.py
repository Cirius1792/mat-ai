import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
import unittest
from unittest.mock import MagicMock, patch

from configuration import Config, FiltersConfig, LLMConfig, OutlookConfig, TrelloConfig, DatabaseConfig
from configuration.application_configuration import ApplicationContext


class TestApplicationContext(unittest.TestCase):
    """Test suite for the ApplicationContext class."""

    def setUp(self):
        """Set up test configurations and mocks before each test."""
        # Reset the singleton instance before each test
        ApplicationContext._instance = None
        
        # Create base test configuration
        self.create_test_config()
        
        # Set up patches for all external dependencies
        self.setup_patches()

    def create_test_config(self):
        """Create test configurations for testing."""
        # Email config
        self.email_config = OutlookConfig(
            name="outlook",
            tenant_id="test_tenant_id",
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost"
        )
        
        # Board config
        self.board_config = TrelloConfig(
            name="trello",
            api_key="test_api_key",
            api_token="test_api_token",
            board="test_board_id"
        )
        
        # Database config
        self.db_config = DatabaseConfig(
            name="sqlite",
            host=":memory:",
            user="",
            password="",
            port=0
        )
        
        # Filters config
        self.filters_config = FiltersConfig(
            recipients=["test@example.com"]
        )

        # LLM Config
        self.llm_config = LLMConfig(
            host="",
            model="gpt-3.5-turbo",
            api_key=""
        )
        
        # Create complete config
        self.config = Config(
            database=self.db_config,
            email={"outlook": self.email_config},
            board={"trello": self.board_config},
            filters=self.filters_config,
            llm_config=self.llm_config,
            confidence_level=0.85
        )
        
        # Create a modified config for testing configuration changes
        self.modified_config = Config(
            database=self.db_config,
            email={"outlook": OutlookConfig(
                name="outlook",
                tenant_id="new_tenant_id",  # Changed value
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost"
            )},
            board={"trello": self.board_config},
            filters=self.filters_config,
            llm_config=self.llm_config,
            confidence_level=0.85
        )
        
        # Create a config with different database for testing configuration changes
        self.db_config_changed = DatabaseConfig(
            name="supabase",  # Changed database type
            host="http://localhost",
            user="test_user",
            password="test_password",
            port=5432
        )
        
        self.db_changed_config = Config(
            database=self.db_config_changed,
            email={"outlook": self.email_config},
            board={"trello": self.board_config},
            filters=self.filters_config,
            llm_config=self.llm_config,
            confidence_level=0.85
        )

    def setup_patches(self):
        """Set up patches for external dependencies."""
        # Create mock patch for initDAOs
        self.mock_dao_patch = patch('configuration.application_configuration.initDAOs')
        self.mock_init_daos = self.mock_dao_patch.start()
        
        # Create mock return values for DAOs
        self.mock_action_dao = MagicMock()
        self.mock_email_dao = MagicMock()
        self.mock_participant_dao = MagicMock()
        self.mock_run_config_dao = MagicMock()
        self.mock_execution_dao = MagicMock()
        
        # Set return value for initDAOs
        self.mock_init_daos.return_value = (
            self.mock_action_dao, 
            self.mock_email_dao, 
            self.mock_participant_dao,
            self.mock_run_config_dao,
            self.mock_execution_dao
        )
        
        # Mock email client
        self.mock_email_client_patch = patch('configuration.application_configuration.initEmailClient')
        self.mock_init_email_client = self.mock_email_client_patch.start()
        
        self.mock_email_client = MagicMock()
        self.mock_o365_account = MagicMock()
        self.mock_init_email_client.return_value = (self.mock_email_client, self.mock_o365_account)
        
        # Mock email processor
        self.mock_processor_patch = patch('configuration.application_configuration.EmailProcessor')
        self.mock_email_processor = self.mock_processor_patch.start()
        self.mock_processor_instance = MagicMock()
        self.mock_email_processor.return_value = self.mock_processor_instance
        
        # Mock email manager
        self.mock_manager_patch = patch('configuration.application_configuration.EmailManager')
        self.mock_email_manager = self.mock_manager_patch.start()
        self.mock_manager_instance = MagicMock()
        self.mock_email_manager.return_value = self.mock_manager_instance
        
        # Mock OpenAI
        self.mock_openai_patch = patch('configuration.application_configuration.OpenAI')
        self.mock_openai = self.mock_openai_patch.start()
        self.mock_openai_instance = MagicMock()
        self.mock_openai.return_value = self.mock_openai_instance
        
        # Mock integration manager
        self.mock_integration_patch = patch('configuration.application_configuration.initIntegrationManager')
        self.mock_init_integration = self.mock_integration_patch.start()
        self.mock_integration_instance = MagicMock()
        self.mock_init_integration.return_value = self.mock_integration_instance

    def tearDown(self):
        """Clean up after each test."""
        # Stop all patches
        self.mock_dao_patch.stop()
        self.mock_email_client_patch.stop()
        self.mock_processor_patch.stop()
        self.mock_manager_patch.stop()
        self.mock_openai_patch.stop()
        self.mock_integration_patch.stop()
        
        # Reset singleton instance
        ApplicationContext._instance = None

    def test_init_creates_new_instance(self):
        """Test that init creates a new instance when none exists."""
        # Verify no instance exists
        self.assertIsNone(ApplicationContext._instance)
        
        # Initialize context
        app_context = ApplicationContext.init(self.config)
        
        # Verify instance was created
        self.assertIsNotNone(app_context)
        self.assertIsInstance(app_context, ApplicationContext)
        
        # Verify all dependencies were initialized
        self.mock_init_daos.assert_called_once_with(self.config.database)
        self.mock_init_email_client.assert_called_once_with(self.config.email['outlook'])
        self.mock_email_processor.assert_called_once()
        self.mock_email_manager.assert_called_once()
        self.mock_init_integration.assert_called_once_with(self.config.board["trello"])
        
        # Verify configuration was stored
        self.assertEqual(app_context.configuration, self.config)

    def test_init_returns_existing_instance_if_config_unchanged(self):
        """Test that init returns existing instance when config is unchanged."""
        # Create first instance
        first_instance = ApplicationContext.init(self.config)
        
        # Reset all mocks to verify they're not called again
        self.mock_init_daos.reset_mock()
        self.mock_init_email_client.reset_mock()
        self.mock_email_processor.reset_mock()
        self.mock_email_manager.reset_mock()
        self.mock_init_integration.reset_mock()
        
        # Get instance again with same config
        second_instance = ApplicationContext.init(self.config)
        
        # Verify same instance is returned
        self.assertIs(first_instance, second_instance)
        
        # Verify no initialization functions were called again
        self.mock_init_daos.assert_not_called()
        self.mock_init_email_client.assert_not_called()
        self.mock_email_processor.assert_not_called()
        self.mock_email_manager.assert_not_called()
        self.mock_init_integration.assert_not_called()

    def test_init_creates_new_instance_if_config_changed(self):
        """Test that init creates a new instance when config changes."""
        # Create first instance
        first_instance = ApplicationContext.init(self.config)
        
        # Verify first instance was created
        self.assertIsNotNone(first_instance)
        
        # Reset all mocks to verify they're called again
        self.mock_init_daos.reset_mock()
        self.mock_init_email_client.reset_mock()
        self.mock_email_processor.reset_mock()
        self.mock_email_manager.reset_mock()
        self.mock_init_integration.reset_mock()
        
        # Create second instance with modified config
        second_instance = ApplicationContext.init(self.modified_config)
        
        # Verify new instance was returned (but singleton pattern means it's the same object)
        self.assertIs(first_instance, second_instance)
        
        # Verify configuration was updated
        self.assertEqual(second_instance.configuration, self.modified_config)
        
        # Verify initialization functions were called again
        self.mock_init_daos.assert_called_once()
        self.mock_init_email_client.assert_called_once()
        self.mock_email_processor.assert_called_once()
        self.mock_email_manager.assert_called_once()
        self.mock_init_integration.assert_called_once()

    def test_is_configuration_changed_detects_email_changes(self):
        """Test that is_configuration_changed detects changes in email config."""
        # Create instance
        app_context = ApplicationContext.init(self.config)
        
        # Test with modified email config
        self.assertTrue(app_context.is_configuration_changed(self.modified_config))

    def test_is_configuration_changed_detects_database_changes(self):
        """Test that is_configuration_changed detects changes in database config."""
        # Create instance
        app_context = ApplicationContext.init(self.config)
        
        # Test with modified database config
        self.assertTrue(app_context.is_configuration_changed(self.db_changed_config))

    def test_init_with_different_database_type(self):
        """Test initialization with different database types."""
        # Create SQLite instance
        sqlite_instance = ApplicationContext.init(self.config)
        
        # Verify SQLite was initialized
        self.mock_init_daos.assert_called_with(self.db_config)
        
        # Reset mock
        self.mock_init_daos.reset_mock()
        
        # Initialize with Supabase config
        supabase_instance = ApplicationContext.init(self.db_changed_config)
        
        # Verify Supabase was initialized
        self.mock_init_daos.assert_called_with(self.db_config_changed)
        
        # Verify configuration was updated
        self.assertEqual(supabase_instance.configuration, self.db_changed_config)

    def test_init_with_different_confidence_level(self):
        """Test initialization with different confidence level."""
        # Create original instance
        original_instance = ApplicationContext.init(self.config)
        
        # Create modified config with different confidence level
        modified_confidence_config = Config(
            database=self.db_config,
            email={"outlook": self.email_config},
            board={"trello": self.board_config},
            filters=self.filters_config,
            llm_config=self.llm_config,
            confidence_level=0.95  # Different confidence level
        )
        
        # Verify confidence level change is detected
        self.assertTrue(original_instance.is_configuration_changed(modified_confidence_config))
        
        # Reset all mocks
        self.mock_init_daos.reset_mock()
        self.mock_init_email_client.reset_mock()
        self.mock_email_processor.reset_mock()
        self.mock_email_manager.reset_mock()
        self.mock_init_integration.reset_mock()
        
        # Initialize with new confidence level
        new_instance = ApplicationContext.init(modified_confidence_config)
        
        # Verify initialization was called again
        self.mock_init_daos.assert_called_once()
        self.mock_init_email_client.assert_called_once()
        self.mock_email_processor.assert_called_once()
        
        # Verify configuration was updated
        self.assertEqual(new_instance.configuration, modified_confidence_config)
        self.assertEqual(new_instance.configuration.confidence_level, 0.95)

    def test_init_preserves_singleton_pattern(self):
        """Test that even with configuration changes, the singleton pattern is maintained."""
        # Create first instance
        first_instance = ApplicationContext.init(self.config)
        first_id = id(first_instance)
        
        # Create second instance with different config
        second_instance = ApplicationContext.init(self.modified_config)
        second_id = id(second_instance)
        
        # Verify it's the same object (singleton pattern)
        self.assertEqual(first_id, second_id)


if __name__ == '__main__':
    unittest.main()
