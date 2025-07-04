import unittest
import tempfile
import os

from matai_v2.configuration import Config, OutlookConfig, load_config_from_yaml, save_config_to_yaml

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')
        
        # Sample test configuration
        self.test_email_config = OutlookConfig(
            tenant_id="test_tenant",
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost"
        )
        
        self.test_config = Config(
            outlook_config=self.test_email_config
        )

    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_save_and_load_config(self):
        """Test saving and loading configuration works correctly"""
        # Save configuration
        save_config_to_yaml(self.test_config, self.config_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.config_path))
        
        # Load configuration
        loaded_config = load_config_from_yaml(self.config_path)
        
        
        # Check email config
        self.assertEqual(
            loaded_config.outlook_config.tenant_id,
            self.test_config.outlook_config.tenant_id
        )

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file raises FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            load_config_from_yaml("nonexistent.yaml")

    def test_save_invalid_config(self):
        """Test saving invalid configuration raises TypeError"""
        invalid_config = {"invalid": "config"}
        with self.assertRaises(TypeError):
            save_config_to_yaml(invalid_config, self.config_path) #type: ignore

