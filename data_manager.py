import json
import os
import logging
import shutil
from pathlib import Path

def ensure_config_directory():
    """Ensure the config directory exists"""
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir(exist_ok=True)
        logging.info("Created config directory")

def create_default_config(config_name, default_data):
    """Create a default config file if it doesn't exist"""
    config_path = Path(f"config/{config_name}.json")
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(default_data, f, indent=2)
        logging.info(f"Created default config file: {config_name}.json")

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {file_path}: {str(e)}")
        return None

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
    daemons_data = load_json_data("config/daemons.json") or default_daemons
    programs_data = load_json_data("config/programs.json") or default_programs
    locations_data = load_json_data("config/locations.json") or default_locations
    
    logging.info("Game data loaded successfully from config files")
    
    return {
        "daemons": daemons_data,
        "programs": programs_data,
        "locations": locations_data
    }

def save_game(player_data, save_name="default"):
    """Save player data to a JSON file"""
    save_dir = Path("saves")
    save_dir.mkdir(exist_ok=True)
    
    save_path = save_dir / f"{save_name}.json"
    
    try:
        with open(save_path, 'w') as f:
            json.dump(player_data, f)
        logging.info(f"Game saved successfully to {save_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving game: {str(e)}")
        return False

def load_game(save_name="default"):
    """Load player data from a JSON file"""
    save_path = Path(f"saves/{save_name}.json")
    
    if not save_path.exists():
        logging.warning(f"Save file not found: {save_path}")
        return None
    
    try:
        with open(save_path, 'r') as f:
            player_data = json.load(f)
        logging.info(f"Game loaded successfully from {save_path}")
        return player_data
    except Exception as e:
        logging.error(f"Error loading game: {str(e)}")
        return None
