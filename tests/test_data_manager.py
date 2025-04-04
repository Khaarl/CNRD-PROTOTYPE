import sys
import os
import json
import unittest
from pathlib import Path

# Add parent directory to path so we can import data_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import data_manager

class TestDataManager(unittest.TestCase):
    """Test cases for data_manager module"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_config")
        self.test_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove test files
        for file in self.test_dir.glob("*"):
            file.unlink()
        self.test_dir.rmdir()
    
    def test_json_validation_valid_data(self):
        """Test JSON validation with valid data"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }
        
        valid_data = {
            "name": "test",
            "value": 42
        }
        
        is_valid, error = data_manager.validate_json_against_schema(valid_data, schema)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_json_validation_missing_required(self):
        """Test JSON validation with missing required property"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }
        
        invalid_data = {
            "name": "test"
            # Missing "value"
        }
        
        is_valid, error = data_manager.validate_json_against_schema(invalid_data, schema)
        self.assertFalse(is_valid)
        self.assertIn("Required property 'value' is missing", error)
    
    def test_json_validation_wrong_type(self):
        """Test JSON validation with wrong type"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            }
        }
        
        invalid_data = {
            "name": "test",
            "value": "not a number"
        }
        
        is_valid, error = data_manager.validate_json_against_schema(invalid_data, schema, "test_context")
        self.assertFalse(is_valid)
        self.assertIn("Expected a number", error)
    
    def test_json_validation_array(self):
        """Test JSON validation with array schema"""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"}
                },
                "required": ["id"]
            }
        }
        
        valid_data = [
            {"id": "item1"},
            {"id": "item2"}
        ]
        
        is_valid, error = data_manager.validate_json_against_schema(valid_data, schema)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_create_default_config(self):
        """Test creating default config file"""
        test_data = {"test": "value"}
        config_path = self.test_dir / "test.json"
        
        # Patch data_manager to use test directory
        original_path = data_manager.Path
        data_manager.Path = lambda path: Path(path.replace("config/", str(self.test_dir) + "/"))
        
        try:
            data_manager.create_default_config("test", test_data)
            self.assertTrue(config_path.exists())
            
            with open(config_path, 'r') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data, test_data)
        finally:
            # Restore original Path
            data_manager.Path = original_path
    
    def test_load_json_data_valid(self):
        """Test loading valid JSON data"""
        test_data = {"test": "value"}
        test_file = self.test_dir / "valid.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loaded_data = data_manager.load_json_data(test_file)
        self.assertEqual(loaded_data, test_data)
    
    def test_load_json_data_invalid(self):
        """Test loading invalid JSON data"""
        test_file = self.test_dir / "invalid.json"
        
        with open(test_file, 'w') as f:
            f.write("{invalid json")
        
        loaded_data = data_manager.load_json_data(test_file)
        self.assertIsNone(loaded_data)
    
    def test_daemon_schema_validation(self):
        """Test daemon schema validation"""
        valid_daemon = {
            "type": "VIRUS",
            "hp": 20,
            "attack": 12,
            "defense": 8,
            "speed": 10,
            "special": 9,
            "programs": ["DATA_SIPHON", "ENCRYPT_SHIELD"]
        }
        
        result = data_manager.validate_config("daemons", {"test_daemon": valid_daemon})
        self.assertTrue(result)
        
        invalid_daemon = {
            "type": "VIRUS",
            "hp": 20,
            # Missing "attack"
            "defense": 8,
            "speed": 10,
            "special": 9,
            "programs": ["DATA_SIPHON", "ENCRYPT_SHIELD"]
        }
        
        result = data_manager.validate_config("daemons", {"test_daemon": invalid_daemon})
        self.assertFalse(result)
    
    def test_program_schema_validation(self):
        """Test program schema validation"""
        valid_program = {
            "name": "Test Program",
            "power": 40,
            "accuracy": 95,
            "type": "TEST",
            "effect": "damage",
            "description": "Test program"
        }
        
        result = data_manager.validate_config("programs", {"TEST_PROGRAM": valid_program})
        self.assertTrue(result)
        
        invalid_program = {
            "name": "Invalid Program",
            "power": "not a number", # Wrong type
            "accuracy": 95,
            "type": "TEST",
            "effect": "damage"
        }
        
        result = data_manager.validate_config("programs", {"INVALID_PROGRAM": invalid_program})
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()