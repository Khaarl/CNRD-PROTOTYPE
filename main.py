import os
import sys
import json
import time
import random
import logging
from pathlib import Path

import player
from daemon import Daemon, Program
from location import Location
from combat import Combat

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game.log'),
        logging.StreamHandler()
    ]
)

class Game:
    """Main game class that handles the game loop and state."""
    
    def __init__(self):
        """Initialize the game."""
        logging.info("Game starting up")
        print("Game starting up")
        
        # Load game data
        self.daemons_data = self._load_json_data('config/daemons.json')
        self.programs_data = self._load_json_data('config/programs.json')
        
        # Load locations
        self.locations_data = self._load_json_data('config/locations.json')
        self.world_map = self._create_world_map()
        
        logging.info("Game data loaded successfully")
        print("Game data loaded successfully")
        
        # Initialize player (to be set during game)
        self.player = None
        self.running = True
        
        logging.info("Game initialized with data from config files and Location objects created.")
        print("Game initialized with data from config files and Location objects created.")
    
    def _load_json_data(self, filepath):
        """Load JSON data from a file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            logging.info(f"Successfully loaded data from {filepath}")
            print(f"Successfully loaded data from {filepath}")
            return data
        except FileNotFoundError:
            logging.error(f"Could not find file {filepath}")
            print(f"Could not find file {filepath}")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Error parsing JSON in {filepath}")
            print(f"Error parsing JSON in {filepath}")
            return {}
    
    def _create_world_map(self):
        """Create the world map from location data."""
        world_map = {}
        for location_id, location_data in self.locations_data.items():
            location = Location(
                id=location_id,
                name=location_data["name"],
                description=location_data["description"],
                exits=location_data["exits"],
                encounter_rate=location_data.get("encounter_rate", 0.3)
            )
            world_map[location_id] = location
        return world_map
    
    def start_game(self):
        """Start the game loop."""
        self._display_title_screen()
        
        username = input("\nEnter your username: ")
        self.player = self._load_or_create_player(username)
        
        self._game_loop()
    
    def _load_or_create_player(self, username):
        """Load a player from a save file or create a new one."""
        save_path = Path(f"saves/{username}.json")
        
        if save_path.exists():
            try:
                with open(save_path, 'r') as f:
                    player_data = json.load(f)
                loaded_player = player.Player.from_dict(player_data)
                print(f"Welcome back, {username}!")
                return loaded_player
            except Exception as e:
                logging.error(f"Error loading save file: {e}")
                print("Error loading save file. Creating new profile...")
                return self._create_new_player(username)
        else:
            logging.warning(f"Save file not found: {save_path}")
            print(f"Save file not found: {save_path}")
            return self._create_new_player(username)
    
    def _create_new_player(self, username):
        """Create a new player."""
        print(f"\nCreating new profile for {username}...")
        
        # Let player select starter daemon
        print("\nChoose your starting daemon:")
        print("1. Virulet (Malware type - balanced)")
        print("2. Pyrowall (Shell type - high defense)")
        print("3. Aquabyte (Encryption type - balanced)")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-3): "))
                if choice < 1 or choice > 3:
                    print("Invalid choice. Please enter a number between 1 and 3.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Create player and add starter daemon
        new_player = player.Player(username)
        
        # Map choice to daemon name
        daemon_choices = ["virulet", "pyrowall", "aquabyte"]
        daemon_name = daemon_choices[choice - 1]
        
        # Create starter daemon with programs
        starter_daemon = new_player.create_starter_daemon(daemon_name)
        new_player.add_daemon(starter_daemon)
        
        print(f"\nWelcome, {username}! You've chosen {daemon_name} as your starting daemon.")
        return new_player
    
    def _display_title_screen(self):
        """Display the game's title screen."""
        print("\n" + "=" * 60)
        print("Welcome to CNRD - Cyber Network Roguelike with Daemons")
        print("=" * 60)

    # ...existing code...