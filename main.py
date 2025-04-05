import os
import sys
import logging
import json
from pathlib import Path

# Import game modules
from player import Player
from world import World
from combat import Combat
from main_menu import MainMenu
from daemon import Daemon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='game.log'
)

class Game:
    def __init__(self):
        self.world = World()
        self.player = None
        self.running = True
        self.save_dir = Path("saves")
        self.save_dir.mkdir(exist_ok=True)
        
    def initialize(self):
        # Initialize the game world
        self.world.load_locations()
        
    def run(self):
        """Main game loop"""
        self.initialize()
        
        # Show main menu and handle selection
        menu = MainMenu(self)
        menu_result = menu.run()
        
        # Process menu selection
        if menu_result["action"] == "new_game":
            self.start_new_game(menu_result["player_name"])
        elif menu_result["action"] == "load_game":
            self.load_game(menu_result["save_file"])
        elif menu_result["action"] == "quick_fight":
            self.start_quick_fight()
            # Return to main menu after quick fight
            self.run()
            return
            
        # Main game loop
        while self.running:
            self.display_current_location()
            command = input("\nWhat will you do? > ").strip().lower()
            self.process_command(command)
            
    def start_new_game(self, player_name):
        """Create a new game with the specified player name"""
        self.player = Player(player_name, "home")
        
        # Let player select a starter daemon
        print(f"\nWelcome, {player_name}! Choose your starter daemon:")
        print("1: Virulet (Virus type)")
        print("2: Pyrowall (Firewall type)")
        print("3: Aquabyte (Crypto type)")
        
        valid_choice = False
        while not valid_choice:
            try:
                choice = int(input("Enter choice (1-3): "))
                if choice == 1:
                    daemon = self.player.create_starter_daemon("virulet")
                    valid_choice = True
                elif choice == 2:
                    daemon = self.player.create_starter_daemon("pyrowall")
                    valid_choice = True
                elif choice == 3:
                    daemon = self.player.create_starter_daemon("aquabyte")
                    valid_choice = True
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except ValueError:
                print("Please enter a number (1-3).")
                
        self.player.add_daemon(daemon)
        print(f"You've chosen {daemon.name} as your starter daemon!")
        print("Your journey into the digital wilderness begins now...")
        input("Press Enter to continue...")
        
        # Save the initial game state
        self.save_game()
        
    def load_game(self, save_file_path):
        """Load a game from the specified save file"""
        try:
            with open(save_file_path, 'r') as f:
                save_data = json.load(f)
            
            # Create player from save data
            self.player = Player.from_dict(save_data, self.world.locations)
            print(f"Welcome back, {self.player.name}!")
            input("Press Enter to continue...")
        except Exception as e:
            logging.error(f"Error loading game: {e}", exc_info=True)
            print(f"Error loading game: {e}")
            input("Press Enter to return to main menu...")
            self.run()
            
    def start_quick_fight(self):
        """Start a test battle for quick gameplay"""
        if not self.player:
            # Create a temporary player for quick fight
            self.player = Player("TestPlayer", "home")
            test_daemon = self.player.create_starter_daemon("virulet")
            self.player.add_daemon(test_daemon)
            
        # Create an opponent with a random daemon
        from npc import NPC
        test_opponent = NPC("Test Opponent", "wild_daemon")
        opponent_daemon = self.player.create_starter_daemon("pyrowall")
        test_opponent.daemons = [opponent_daemon]
        
        print("\nStarting Quick Fight!")
        print(f"Your {self.player.daemons[0].name} vs. Opponent's {opponent_daemon.name}")
        input("Press Enter to start the battle...")
        
        # Start combat
        combat = Combat(self.player, test_opponent)
        result = combat.start_battle()
        
        print("\nQuick Fight Complete!")
        if result["winner"] == "player":
            print("You won!")
        else:
            print("You lost!")
        
        # Heal daemons after battle
        self.player.heal_all_daemons()
        input("Press Enter to return to main menu...")
        
    def display_current_location(self):
        """Display information about the player's current location"""
        if not self.player:
            return
            
        current_loc = self.player.get_current_location(self.world.locations)
        if not current_loc:
            print("Error: You're in an invalid location.")
            return
            
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 50)
        print(f"Location: {current_loc.name}")
        print("=" * 50)
        print(current_loc.description)
        
        # Show available exits
        print("\nAvailable exits:")
        for direction, location_id in current_loc.exits.items():
            exit_loc = self.world.locations.get(location_id)
            if exit_loc:
                print(f"  {direction.capitalize()}: {exit_loc.name}")
        
        # Show player status
        self.player.display_status()
        
    def process_command(self, command):
        """Process user commands"""
        if command == "quit" or command == "exit":
            self.save_game()
            print("Thanks for playing!")
            self.running = False
            
        elif command.startswith("go "):
            direction = command[3:].strip()
            self.player.move(direction, self.world.locations)
            self.check_for_encounters()
            
        elif command in ["north", "south", "east", "west", "up", "down"]:
            self.player.move(command, self.world.locations)
            self.check_for_encounters()
            
        elif command == "look":
            # Just redisplay the current location
            pass
            
        elif command == "status":
            self.player.display_status(self.world.locations)
            input("\nPress Enter to continue...")
            
        elif command == "daemons":
            self.player.display_daemons_detailed()
            input("\nPress Enter to continue...")
            
        elif command == "help":
            self.display_help()
            
        elif command == "save":
            self.save_game()
            print("Game saved successfully!")
            input("Press Enter to continue...")
            
        elif command == "menu":
            self.return_to_menu()
            
        else:
            print("I don't understand that command. Type 'help' for a list of commands.")
            input("Press Enter to continue...")
            
    def check_for_encounters(self):
        """Check for random encounters when moving"""
        # Placeholder for encounter system
        pass
        
    def save_game(self):
        """Save the current game state"""
        if not self.player:
            return
            
        save_data = self.player.to_dict()
        save_path = self.save_dir / f"{self.player.name.lower()}.json"
        
        try:
            with open(save_path, 'w') as f:
                json.dump(save_data, f)
            logging.info(f"Game saved to {save_path}")
        except Exception as e:
            logging.error(f"Error saving game: {e}", exc_info=True)
            print(f"Error saving game: {e}")
            
    def display_help(self):
        """Display available commands"""
        print("\n=== Available Commands ===")
        print("go <direction> - Move in a direction (north, south, east, west, up, down)")
        print("<direction> - Shortcut for go <direction>")
        print("look - Look around your current location")
        print("status - Display player status")
        print("daemons - Display detailed daemon information")
        print("save - Save your game")
        print("menu - Return to main menu")
        print("help - Display this help message")
        print("quit/exit - Save and quit the game")
        print("========================")
        input("\nPress Enter to continue...")
        
    def return_to_menu(self):
        """Save and return to main menu"""
        self.save_game()
        self.run()  # Restart from menu

# Start game if run directly
if __name__ == "__main__":
    game = Game()
    try:
        game.run()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Unhandled exception: {e}")
        input("Press Enter to exit...")
        sys.exit(1)