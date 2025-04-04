import json
import logging
import shutil
import traceback
from pathlib import Path

# Add schema validation functionality
def validate_json_against_schema(data, schema, context=""):
    """
    Validate JSON data against a simple schema.
    Args:
        data: The JSON data to validate
        schema: A dictionary defining the expected structure
        context: Optional context string for error reporting
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if schema is None:
        return True, ""
        
    # Check if data is of the expected type
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "object" and not isinstance(data, dict):
            return False, f"{context}: Expected an object, got {type(data).__name__}"
        elif expected_type == "array" and not isinstance(data, list):
            return False, f"{context}: Expected an array, got {type(data).__name__}"
        elif expected_type == "string" and not isinstance(data, str):
            return False, f"{context}: Expected a string, got {type(data).__name__}"
        elif expected_type == "number" and not isinstance(data, (int, float)):
            return False, f"{context}: Expected a number, got {type(data).__name__}"
        elif expected_type == "boolean" and not isinstance(data, bool):
            return False, f"{context}: Expected a boolean, got {type(data).__name__}"
    
    # Check required properties for objects
    if isinstance(data, dict) and "required" in schema:
        for prop in schema["required"]:
            if prop not in data:
                return False, f"{context}: Required property '{prop}' is missing"
    
    # Check properties format
    if isinstance(data, dict) and "properties" in schema:
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                prop_context = f"{context}.{prop}" if context else prop
                is_valid, error = validate_json_against_schema(data[prop], prop_schema, prop_context)
                if not is_valid:
                    return False, error
    
    # Check array items
    if isinstance(data, list) and "items" in schema:
        for index, item in enumerate(data):
            item_context = f"{context}[{index}]" if context else f"[{index}]"
            is_valid, error = validate_json_against_schema(item, schema["items"], item_context)
            if not is_valid:
                return False, error
    
    return True, ""

def ensure_config_directory():
    """Ensure the config directory exists"""
    config_dir = Path("config")
    if not config_dir.exists():
        try:
            config_dir.mkdir(exist_ok=True)
            logging.info("Created config directory")
        except Exception as e:
            logging.error(f"Failed to create config directory: {e}")
            raise RuntimeError(f"Cannot create required directory: {e}")

def create_default_config(config_name, default_data):
    """Create a default config file if it doesn't exist"""
    config_path = Path("config") / f"{config_name}.json"
    if not config_path.exists():
        try:
            with open(config_path, 'w') as f:
                json.dump(default_data, f, indent=2)
            logging.info(f"Created default config file: {config_name}.json")
        except Exception as e:
            logging.error(f"Failed to create config file {config_name}.json: {e}")
            # Don't raise here, let's continue with default data

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                logging.info(f"Successfully loaded data from {file_path}")
                return data
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing error in {file_path}: {e.msg} at line {e.lineno}, column {e.colno}")
                return None
    except IOError as e:
        logging.error(f"IO error loading {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading {file_path}: {e}")
        logging.debug(traceback.format_exc())
        return None

# Define schemas for validation
DAEMON_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "hp": {"type": "number"},
        "attack": {"type": "number"},
        "defense": {"type": "number"},
        "speed": {"type": "number"},
        "special": {"type": "number"},
        "programs": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["type", "hp", "attack", "defense", "speed", "special", "programs"]
}

PROGRAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "power": {"type": "number"},
        "accuracy": {"type": "number"},
        "type": {"type": "string"},
        "effect": {"type": "string"},
        "description": {"type": "string"}
    },
    "required": ["name", "power", "accuracy", "type", "effect"]
}

LOCATION_SCHEMA = {
    "type": "object",
    "properties": {
        "start_location": {"type": "string"},
        "locations": {
            "type": "object",
            "properties": {},  # Dynamic properties for each location
        }
    },
    "required": ["start_location", "locations"]
}

LOCATION_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "encounter_rate": {"type": "number"},
        "scan_encounter_rate": {"type": "number"},
        "exits": {"type": "object"}
    },
    "required": ["name", "description"]
}

def validate_config(config_name, data):
    """Validate configuration data against its schema"""
    schema = None
    if config_name == "daemons":
        # For daemons, each entry needs to be validated
        for daemon_id, daemon_data in data.items():
            is_valid, error = validate_json_against_schema(daemon_data, DAEMON_SCHEMA, daemon_id)
            if not is_valid:
                logging.warning(f"Invalid daemon configuration: {error}")
                return False
        return True
    elif config_name == "programs":
        # For programs, each entry needs to be validated
        for program_id, program_data in data.items():
            is_valid, error = validate_json_against_schema(program_data, PROGRAM_SCHEMA, program_id)
            if not is_valid:
                logging.warning(f"Invalid program configuration: {error}")
                return False
        return True
    elif config_name == "locations":
        # First validate the overall structure
        is_valid, error = validate_json_against_schema(data, LOCATION_SCHEMA)
        if not is_valid:
            logging.warning(f"Invalid locations configuration: {error}")
            return False
            
        # Then validate each location entry
        for loc_id, loc_data in data.get("locations", {}).items():
            is_valid, error = validate_json_against_schema(loc_data, LOCATION_ENTRY_SCHEMA, loc_id)
            if not is_valid:
                logging.warning(f"Invalid location entry: {error}")
                return False
        return True
    else:
        logging.warning(f"No validation schema for config: {config_name}")
        return True  # No schema means no validation

def load_game_data():
    """Load all game data from config files"""
    ensure_config_directory()
    
    # Default data (will be used if config files don't exist)
    default_daemons = {
        "virulet": {
            "type": "VIRUS",
            "hp": 20,
            "attack": 12,
            "defense": 8,
            "speed": 10,
            "special": 9,
            "programs": ["DATA_SIPHON", "ENCRYPT_SHIELD"]
        },
        "pyrowall": {
            "type": "FIREWALL",
            "hp": 18,
            "attack": 9,
            "defense": 12,
            "speed": 8,
            "special": 11,
            "programs": ["FIREWALL_BASH", "ENCRYPT_SHIELD"]
        },
        "aquabyte": {
            "type": "CRYPTO",
            "hp": 19,
            "attack": 10,
            "defense": 10,
            "speed": 10,
            "special": 10,
            "programs": ["DATA_SIPHON", "CRYPTO_SCRAMBLE"]
        },
        "rat_bot": {
            "type": "TROJAN",
            "hp": 15,
            "attack": 13,
            "defense": 7,
            "speed": 12,
            "special": 8,
            "programs": ["EXPLOIT_CRACK", "DATA_SIPHON"]
        },
        "glitch_sprite": {
            "type": "VIRUS",
            "hp": 17,
            "attack": 8,
            "defense": 9,
            "speed": 15,
            "special": 12,
            "programs": ["DATA_SIPHON", "EXPLOIT_CRACK"]
        }
    }
    
    default_programs = {
        "DATA_SIPHON": {
            "name": "Data Siphon",
            "power": 40,
            "accuracy": 95,
            "type": "VIRUS",
            "effect": "damage",
            "description": "Siphons data from the target causing damage"
        },
        "FIREWALL_BASH": {
            "name": "Firewall Bash",
            "power": 45,
            "accuracy": 90,
            "type": "FIREWALL",
            "effect": "damage",
            "description": "A powerful strike with firewall code"
        },
        "ENCRYPT_SHIELD": {
            "name": "Encrypt Shield",
            "power": 0,
            "accuracy": 100,
            "type": "CRYPTO",
            "effect": "defend",
            "description": "Creates an encrypted shield to boost defense"
        },
        "EXPLOIT_CRACK": {
            "name": "Exploit Crack",
            "power": 35,
            "accuracy": 100,
            "type": "TROJAN",
            "effect": "damage",
            "description": "Exploits vulnerabilities for guaranteed damage"
        },
        "CRYPTO_SCRAMBLE": {
            "name": "Crypto Scramble",
            "power": 30,
            "accuracy": 90,
            "type": "CRYPTO",
            "effect": "special",
            "description": "Scrambles target's code to lower their attack"
        }
    }
    
    default_locations = {
        "start_location": "home",
        "locations": {
            "home": {
                "name": "Home",
                "description": "Your small apartment with a computer setup",
                "encounter_rate": 0,
                "exits": {
                    "north": "uptown",
                    "east": "downtown"
                }
            },
            "uptown": {
                "name": "Uptown District",
                "description": "A clean, high-tech area with corporate buildings",
                "encounter_rate": 20,
                "exits": {
                    "south": "home",
                    "east": "central_hub"
                }
            },
            "downtown": {
                "name": "Downtown District",
                "description": "A gritty area with old tech and sketchy connections",
                "encounter_rate": 30,
                "exits": {
                    "west": "home",
                    "north": "central_hub"
                }
            },
            "central_hub": {
                "name": "Central Network Hub",
                "description": "The main connection point for the city's networks",
                "encounter_rate": 40,
                "exits": {
                    "west": "uptown",
                    "south": "downtown",
                    "north": "daemon_lab"
                }
            },
            "daemon_lab": {
                "name": "Daemon Research Lab",
                "description": "A high-security facility studying daemon code",
                "encounter_rate": 60,
                "exits": {
                    "south": "central_hub"
                }
            }
        }
    }
    
    # Create default config files if they don't exist
    create_default_config("daemons", default_daemons)
    create_default_config("programs", default_programs)
    create_default_config("locations", default_locations)
    
    # Load data from config files
    configs_to_load = [
        ("daemons", default_daemons),
        ("programs", default_programs),
        ("locations", default_locations)
    ]
    
    loaded_configs = {}
    
    for config_name, default_data in configs_to_load:
        file_path = Path("config") / f"{config_name}.json"
        data = load_json_data(file_path)
        
        if data is None:
            logging.warning(f"Failed to load {file_path}, falling back to default data")
            data = default_data
        else:
            # Validate the loaded data
            if not validate_config(config_name, data):
                logging.warning(f"Validation failed for {file_path}, falling back to default data")
                data = default_data
        
        loaded_configs[config_name] = data
    
    logging.info("Game data loaded successfully")
    
    return {
        "daemons": loaded_configs["daemons"],
        "programs": loaded_configs["programs"],
        "locations": loaded_configs["locations"]
    }

def save_game(player_data, save_name="default"):
    """Save player data to a JSON file"""
    save_dir = Path("saves")
    try:
        save_dir.mkdir(exist_ok=True)
        
        save_path = save_dir / f"{save_name}.json"
        
        try:
            with open(save_path, 'w') as f:
                json.dump(player_data, f)
            logging.info(f"Game saved successfully to {save_path}")
            return True
        except Exception as e:
            logging.error(f"Error saving game to {save_path}: {str(e)}")
            logging.debug(traceback.format_exc())
            return False
    except Exception as e:
        logging.error(f"Error creating save directory: {str(e)}")
        logging.debug(traceback.format_exc())
        return False

def load_game(save_name="default"):
    """Load player data from a JSON file"""
    save_path = Path("saves") / f"{save_name}.json"
    
    if not save_path.exists():
        logging.warning(f"Save file not found: {save_path}")
        return None
    
    try:
        with open(save_path, 'r') as f:
            try:
                player_data = json.load(f)
                logging.info(f"Game loaded successfully from {save_path}")
                return player_data
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing error loading save file {save_path}: {e.msg} at line {e.lineno}, column {e.colno}")
                return None
    except IOError as e:
        logging.error(f"IO error loading save file {save_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading save file {save_path}: {e}")
        logging.debug(traceback.format_exc())
        return None
