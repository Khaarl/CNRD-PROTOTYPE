import json
import os
import logging
from daemon import Daemon, Program
from location import Location

DATA_DIR = "data"
SAVE_DIR = "saves"

def ensure_dir_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"Created directory: {directory}")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            print(f"Error: Failed to create directory {directory}")

def load_game_data():
    """Load game data from JSON files"""
    ensure_dir_exists(DATA_DIR)
    try:
        daemons = load_json(os.path.join(DATA_DIR, "daemons.json"), {})
        programs = load_json(os.path.join(DATA_DIR, "programs.json"), {})
        locations = load_json(os.path.join(DATA_DIR, "locations.json"), {})
        logging.info("Game data loaded successfully")
        return {"daemons": daemons, "programs": programs, "locations": locations}
    except Exception as e:
        logging.error(f"Error in load_game_data: {e}")
        print(f"Error loading game data: {e}")
        # Return default empty data
        return {"daemons": {}, "programs": {}, "locations": {}}

def load_json(filepath, default=None):
    """Load data from a JSON file with error handling"""
    try:
        if not os.path.exists(filepath):
            logging.warning(f"File not found: {filepath}, using default values")
            return default if default is not None else {}
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            logging.info(f"Loaded data from {filepath}")
            return data
    except json.JSONDecodeError as e:
        logging.error(f"JSON error in {filepath}: {e}")
        print(f"Error: Invalid JSON in {filepath}")
        return default if default is not None else {}
    except Exception as e:
        logging.error(f"Error loading {filepath}: {e}")
        print(f"Error loading {filepath}: {e}")
        return default if default is not None else {}

def save_game(player, world_map, filename):
    """Save current game state to a file"""
    ensure_dir_exists(SAVE_DIR)
    try:
        # Create serializable player data
        player_data = {
            "name": player.name,
            "current_location_id": player.current_location_id,
            "daemons": []
        }
        
        # Convert each daemon to a dictionary
        for d in player.daemons:
            daemon_dict = {
                "name": d.name,
                "types": d.types,
                "level": d.level,
                "xp": d.xp,
                "base_stats": d.base_stats,
                "stats": d.stats,
                "programs": [],
                "status_effect": d.status_effect
            }
            # Convert programs to dictionaries
            for p in d.programs:
                program_dict = {
                    "name": p.name,
                    "type": p.type,
                    "power": p.power,
                    "effect": p.effect
                }
                daemon_dict["programs"].append(program_dict)
            
            player_data["daemons"].append(daemon_dict)
        
        # Write to file
        save_path = os.path.join(SAVE_DIR, f"{filename}.json")
        with open(save_path, 'w') as f:
            json.dump({"player": player_data}, f, indent=2)
        
        logging.info(f"Game saved as '{filename}'")
        print(f"Game saved as '{filename}'")
        return True
        
    except Exception as e:
        logging.error(f"Error saving game: {e}")
        print(f"Error saving game: {e}")
        return False

def load_save(filename, world_map):
    """Load a saved game"""
    from player import Player
    save_path = os.path.join(SAVE_DIR, f"{filename}.json")
    
    if not os.path.exists(save_path):
        logging.error(f"Save file not found: {save_path}")
        print(f"Error: Save file '{filename}.json' not found.")
        return None
    
    try:
        # Read save file
        with open(save_path, 'r') as f:
            save_data = json.load(f)
        
        # Validate save data structure
        if "player" not in save_data:
            logging.error(f"Invalid save file format: {filename}.json")
            print(f"Error: Invalid save file format.")
            return None
            
        player_data = save_data["player"]
        
        # Validate required fields
        required_fields = ["name", "current_location_id", "daemons"]
        for field in required_fields:
            if field not in player_data:
                logging.error(f"Missing required field in save file: {field}")
                print(f"Error: Save file is missing required data.")
                return None
        
        # Validate location exists in world map
        location_id = player_data["current_location_id"]
        if location_id not in world_map:
            logging.error(f"Save file references invalid location: {location_id}")
            print(f"Error: Save file references an invalid location.")
            return None
        
        # Create player
        player = Player(player_data["name"], player_data["current_location_id"], world_map)
        
        # Load daemons
        for d_data in player_data["daemons"]:
            # Create programs
            programs = []
            if "programs" in d_data:
                for p in d_data["programs"]:
                    program = Program(
                        p.get("name", "Unknown Program"),
                        p.get("type", "Normal"),
                        p.get("power", 10),
                        p.get("effect", None)
                    )
                    programs.append(program)
            
            # Create daemon
            base_stats = d_data.get("base_stats", {'hp': 40, 'attack': 40, 'defense': 40, 'speed': 40})
            daemon = Daemon(
                d_data.get("name", "Unknown Daemon"),
                d_data.get("types", ["Normal"]),
                base_stats,
                d_data.get("level", 1),
                programs,
                d_data.get("xp", 0)
            )
            
            # Set stats
            if "stats" in d_data:
                daemon.stats = d_data["stats"]
                
            # Set status effect
            daemon.status_effect = d_data.get("status_effect", None)
            
            # Add daemon to player
            player.add_daemon(daemon)
        
        logging.info(f"Game loaded from '{filename}'")
        print(f"Game loaded from '{filename}'")
        return player
        
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in save file: {save_path}")
        print(f"Error: Save file is corrupted or not valid JSON.")
        return None
    except Exception as e:
        logging.error(f"Error loading save: {e}")
        print(f"Error loading save: {e}")
        return None

def export_current_data(world_map, daemon_stats, programs):
    """Export current game data to JSON files"""
    ensure_dir_exists(DATA_DIR)
    try:
        # Export daemon data
        daemon_data = {d_id: {"base_stats": {k: v for k, v in stats.items() if k != "types"}, 
                             "types": stats["types"]} 
                      for d_id, stats in daemon_stats.items()}
        with open(os.path.join(DATA_DIR, "daemons.json"), 'w') as f:
            json.dump(daemon_data, f, indent=2)
        
        # Export program data
        program_data = {p_id: {"type": prog.type, "power": prog.power, "effect": prog.effect} 
                       for p_id, prog in programs.items()}
        with open(os.path.join(DATA_DIR, "programs.json"), 'w') as f:
            json.dump(program_data, f, indent=2)
        
        # Export location data
        location_data = {loc_id: {"name": loc.name, 
                                 "description": loc.description, 
                                 "exits": loc.exits, 
                                 "encounter_rate": loc.encounter_rate, 
                                 "wild_daemons": loc.wild_daemons} 
                        for loc_id, loc in world_map.items()}
        with open(os.path.join(DATA_DIR, "locations.json"), 'w') as f:
            json.dump(location_data, f, indent=2)
            
        logging.info("Current game data exported to 'data' directory.")
        print("Current game data exported to 'data' directory.")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting game data: {e}")
        print(f"Error exporting game data: {e}")
        return False
