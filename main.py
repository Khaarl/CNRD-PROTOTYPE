import os
import sys
import logging
import json
from pathlib import Path
import traceback
import pygame

# Import game modules
from player import Player
from world import World
from combat import Combat
from main_menu import MainMenu
from daemon import Daemon
from save_screen import SaveScreen

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "game.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("CNRD")

class Game:
    def __init__(self):
        self.world = World()
        self.player = None
        self.running = True
        self.state = "menu"  # States: menu, roaming, combat, pause
        self.save_dir = Path("saves")
        self.save_dir.mkdir(exist_ok=True)
        
        # Initialize pygame
        if not pygame.get_init():
            pygame.init()
        
    def initialize(self):
        # Initialize the game world
        self.world.load_locations()
        
    def run(self):
        """Main game loop"""
        self.initialize()
        
        # Main game loop
        self.running = True
        self.state = "roaming"
        
        while self.running:
            if self.state == "roaming":
                self.display_current_location()
                command = input("\nWhat will you do? > ").strip().lower()
                self.process_command(command)
            elif self.state == "save_screen":
                self.show_save_screen()
            
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
        """Load a saved game from a file"""
        try:
            from data_manager import load_game as load_game_from_file
            player_data = load_game_from_file(save_file_path)
            
            if not player_data:
                logging.error(f"Failed to load game data from {save_file_path}")
                print("Failed to load game. Check the logs for details.")
                return False
                
            # Create player from saved data
            from player import Player
            self.player = Player.from_dict(player_data, self.world.locations)
            
            logging.info(f"Game loaded successfully for player {self.player.name}")
            print(f"Welcome back, {self.player.name}!")
            
            # Set game to roaming state
            self.state = "roaming"
            return True
            
        except Exception as e:
            logging.error(f"Error during load_game: {e}", exc_info=True)
            print(f"Error loading game: {e}")
            return False
            
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
            # Switch to save screen
            self.state = "save_screen"
            
        elif command == "menu":
            self.return_to_menu()
            
        else:
            print("I don't understand that command. Type 'help' for a list of commands.")
            input("Press Enter to continue...")
            
    def check_for_encounters(self):
        """Check for random encounters when moving"""
        # Placeholder for encounter system
        pass
        
    def show_save_screen(self):
        """Show the save game screen"""
        save_screen = SaveScreen(self)
        result = save_screen.run()
        
        # Handle result
        if result["action"] == "return_to_game":
            self.state = "roaming"
        
    def save_game(self, save_name=None):
        """Save the current game state"""
        if not self.player:
            logging.warning("Attempted to save game but no player exists")
            return False
            
        save_data = self.player.to_dict()
        if save_name is None:
            save_name = self.player.name.lower()
        
        try:
            from data_manager import save_game as save_game_to_file
            success = save_game_to_file(save_data, save_name)
            
            if success:
                logging.info(f"Game saved successfully as {save_name}")
                return True
            else:
                logging.error("Failed to save game")
                return False
        except Exception as e:
            logging.error(f"Error during save_game: {e}", exc_info=True)
            return False
            
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
        print("Returning to main menu...")
        # This is where we would return to the main menu, 
        # but for now just exit as we need to restructure the flow
        self.running = False

def main():
    """Main entry point for the game"""
    logger = setup_logging()
    logger.info("Starting CNRD Prototype")
    
    try:
        # Initialize game object (minimal initialization for menu)
        game_instance = Game()
        game_instance.initialize()
        
        # Create and run the main menu
        menu = MainMenu(game_instance)
        menu_result = menu.run()
        
        logger.info(f"Main menu returned: {menu_result}")
        
        # Handle menu result
        if menu_result["action"] == "new_game":
            logger.info(f"Starting new game with player name: {menu_result['player_name']}")
            game_instance.start_new_game(menu_result["player_name"])
            game_instance.run()
            
        elif menu_result["action"] == "load_game":
            logger.info(f"Loading game from: {menu_result['save_file']}")
            if game_instance.load_game(menu_result["save_file"]):
                game_instance.run()
            
        elif menu_result["action"] == "quick_fight":
            logger.info("Starting quick fight")
            game_instance.start_quick_fight()
            game_instance.run()
            
    except Exception as e:
        logger.error(f"Error in game: {e}")
        logger.error(traceback.format_exc())
        print(f"\nError: {e}")
        print("The game crashed. Check the logs for details.")
        input("Press Enter to exit...")
        
    logger.info("Game session ended")

if __name__ == "__main__":
    main()