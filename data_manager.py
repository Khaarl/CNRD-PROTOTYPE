import json
import os
from daemon import Daemon, Program
from location import Location

DATA_DIR = "data"
SAVE_DIR = "saves"

def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_game_data():
    ensure_dir_exists(DATA_DIR)
    daemons = load_json(os.path.join(DATA_DIR, "daemons.json"), {})
    programs = load_json(os.path.join(DATA_DIR, "programs.json"), {})
    locations = load_json(os.path.join(DATA_DIR, "locations.json"), {})
    return {"daemons": daemons, "programs": programs, "locations": locations}

def load_json(filepath, default=None):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Notice: {e}. Using default values.")
        return default if default is not None else {}

def save_game(player, world_map, filename):
    ensure_dir_exists(SAVE_DIR)
    player_data = {
        "name": player.name,
        "current_location_id": player.current_location_id,
        "daemons": [
            {
                "name": d.name,
                "types": d.types,
                "level": d.level,
                "xp": d.xp,
                "base_stats": d.base_stats,
                "stats": d.stats,
                "programs": [{"name": p.name, "type": p.type, "power": p.power, "effect": p.effect} for p in d.programs],
                "status_effect": d.status_effect
            }
            for d in player.daemons
        ]
    }
    save_path = os.path.join(SAVE_DIR, f"{filename}.json")
    try:
        with open(save_path, 'w') as f:
            json.dump({"player": player_data}, f, indent=2)
        print(f"Game saved as '{filename}'")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def load_save(filename, world_map):
    from player import Player
    save_path = os.path.join(SAVE_DIR, f"{filename}.json")
    try:
        with open(save_path, 'r') as f:
            save_data = json.load(f)
        player_data = save_data["player"]
        player = Player(player_data["name"], player_data["current_location_id"], world_map)
        for d_data in player_data["daemons"]:
            programs = [Program(p["name"], p["type"], p["power"], p["effect"]) for p in d_data["programs"]]
            daemon = Daemon(d_data["name"], d_data["types"], d_data["base_stats"], d_data["level"], programs, d_data["xp"])
            daemon.stats = d_data["stats"]
            daemon.status_effect = d_data["status_effect"]
            player.add_daemon(daemon)
        print(f"Game loaded from '{filename}'")
        return player
    except Exception as e:
        print(f"Error loading save: {e}")
        return None

def export_current_data(world_map, daemon_stats, programs):
    ensure_dir_exists(DATA_DIR)
    daemon_data = {d_id: {"base_stats": {k: v for k, v in stats.items() if k != "types"}, "types": stats["types"]} for d_id, stats in daemon_stats.items()}
    with open(os.path.join(DATA_DIR, "daemons.json"), 'w') as f:
        json.dump(daemon_data, f, indent=2)
    program_data = {p_id: {"type": prog.type, "power": prog.power, "effect": prog.effect} for p_id, prog in programs.items()}
    with open(os.path.join(DATA_DIR, "programs.json"), 'w') as f:
        json.dump(program_data, f, indent=2)
    location_data = {loc_id: {"name": loc.name, "description": loc.description, "exits": loc.exits, "encounter_rate": loc.encounter_rate, "wild_daemons": loc.wild_daemons} for loc_id, loc in world_map.items()}
    with open(os.path.join(DATA_DIR, "locations.json"), 'w') as f:
        json.dump(location_data, f, indent=2)
    print("Current game data exported to 'data' directory.")
