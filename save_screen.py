import os
import pygame
import logging
from pathlib import Path
from data_manager import get_available_saves, save_game, delete_save

# Configure logger
logger = logging.getLogger("CNRD.SaveScreen")

class SaveScreen:
    """A class to manage the save game screen interface"""
    
    def __init__(self, game):
        """Initialize the save screen
        
        Args:
            game: Reference to the main game object
        """
        self.game = game
        self.running = False
        self.save_slots = []  # List of save slots
        self.selected_index = 0
        self.message = ""
        self.new_save_name = ""
        self.entering_name = False
        
    def run(self):
        """Run the save screen interface
        
        Returns:
            dict: Action result
        """
        self.running = True
        self.refresh_saves()
        
        # Main loop for the text-based interface
        while self.running:
            self.display_screen()
            command = input("\nEnter choice: ").strip().lower()
            self.process_command(command)
            
        # Return action result
        return {"action": "return_to_game"}
        
    def refresh_saves(self):
        """Refresh the list of available save games"""
        self.save_slots = get_available_saves()
        if self.save_slots and self.selected_index >= len(self.save_slots):
            self.selected_index = len(self.save_slots) - 1
            
    def display_screen(self):
        """Display the save screen interface"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 50)
        print("                SAVE GAME")
        print("=" * 50)
        
        # Show message if any
        if self.message:
            print(f"\n{self.message}")
            self.message = ""
            
        # If entering a new save name
        if self.entering_name:
            print("\nEnter a name for your save file:")
            print(f"Current input: {self.new_save_name}")
            print("\n[Enter] to confirm  [ESC] to cancel")
            return
            
        # Show available save slots
        print("\nAVAILABLE SAVES:")
        if not self.save_slots:
            print("\nNo save files found.")
        else:
            for i, save in enumerate(self.save_slots):
                marker = ">" if i == self.selected_index else " "
                print(f"{marker} {i+1}. {save['player_name']} - {save['time_str']}")
                
        # Show current player name
        if self.game.player:
            print(f"\nCurrent player: {self.game.player.name}")
            
        # Show commands
        print("\nCommands:")
        print("  [number] - Select a save slot")
        print("  s - Save game to selected slot")
        print("  l - Load game from selected slot")
        print("  n - Create new save")
        print("  d - Delete selected save")
        print("  r - Return to game")
        print("  q - Save and quit to main menu")
        
    def process_command(self, command):
        """Process user input for the save screen
        
        Args:
            command (str): User input command
        """
        # Check if entering new save name
        if self.entering_name:
            if command == "":  # Enter key
                if self.new_save_name:
                    self.create_new_save(self.new_save_name)
                self.entering_name = False
                self.new_save_name = ""
            elif command.lower() == "esc":  # Escape key
                self.entering_name = False
                self.new_save_name = ""
            else:
                # Add to save name
                self.new_save_name += command
            return
                
        # Normal command processing
        if command.isdigit() and 1 <= int(command) <= len(self.save_slots):
            # Select a save slot
            self.selected_index = int(command) - 1
            
        elif command == "s":
            # Save game to selected slot
            self.save_current_game()
            
        elif command == "l":
            # Load game from selected slot
            self.load_selected_game()
            
        elif command == "n":
            # Create new save
            self.start_new_save()
            
        elif command == "d":
            # Delete selected save
            self.delete_selected_save()
            
        elif command == "r":
            # Return to game
            self.running = False
            
        elif command == "q":
            # Save and quit
            self.save_current_game()
            self.running = False
            self.game.running = False
            
    def save_current_game(self):
        """Save the current game to the selected slot or create new save"""
        if not self.game.player:
            self.message = "Error: No active player to save."
            return
            
        try:
            # If a slot is selected, use that save name
            if self.save_slots and 0 <= self.selected_index < len(self.save_slots):
                save_name = Path(self.save_slots[self.selected_index]["path"]).stem
            else:
                save_name = self.game.player.name.lower()
                
            # Save the game
            success = self.game.save_game(save_name)
            
            if success:
                self.message = f"Game saved successfully as '{save_name}'."
                # Refresh the save list
                self.refresh_saves()
            else:
                self.message = "Error saving game."
                
        except Exception as e:
            logger.error(f"Error in save_current_game: {e}", exc_info=True)
            self.message = f"Error saving game: {e}"
            
    def start_new_save(self):
        """Start entering a new save name"""
        if not self.game.player:
            self.message = "Error: No active player to save."
            return
            
        self.entering_name = True
        self.new_save_name = self.game.player.name.lower()
        
    def create_new_save(self, save_name):
        """Create a new save with the specified name
        
        Args:
            save_name (str): Name for the save file
        """
        if not self.game.player:
            self.message = "Error: No active player to save."
            return
            
        try:
            # Save the game
            success = self.game.save_game(save_name)
            
            if success:
                self.message = f"Game saved successfully as '{save_name}'."
                # Refresh the save list
                self.refresh_saves()
            else:
                self.message = "Error saving game."
                
        except Exception as e:
            logger.error(f"Error in create_new_save: {e}", exc_info=True)
            self.message = f"Error saving game: {e}"
            
    def load_selected_game(self):
        """Load the game from the selected slot"""
        if not self.save_slots or self.selected_index >= len(self.save_slots):
            self.message = "No save file selected."
            return
            
        try:
            save_path = self.save_slots[self.selected_index]["path"]
            
            # Confirm before loading
            print(f"\nLoad game '{self.save_slots[self.selected_index]['player_name']}'?")
            confirm = input("Any unsaved progress will be lost. Proceed? (y/n): ").lower()
            
            if confirm == "y":
                # Load the game
                if self.game.load_game(save_path):
                    self.message = f"Game loaded successfully."
                    self.running = False  # Return to game
                else:
                    self.message = "Error loading game."
                    
        except Exception as e:
            logger.error(f"Error in load_selected_game: {e}", exc_info=True)
            self.message = f"Error loading game: {e}"
            
    def delete_selected_save(self):
        """Delete the selected save file"""
        if not self.save_slots or self.selected_index >= len(self.save_slots):
            self.message = "No save file selected."
            return
            
        try:
            save_path = self.save_slots[self.selected_index]["path"]
            save_name = self.save_slots[self.selected_index]["player_name"]
            
            # Confirm before deleting
            print(f"\nDelete save '{save_name}'?")
            confirm = input("This cannot be undone. Proceed? (y/n): ").lower()
            
            if confirm == "y":
                # Delete the save
                if delete_save(save_path):
                    self.message = f"Save '{save_name}' deleted."
                    # Refresh the save list
                    self.refresh_saves()
                else:
                    self.message = "Error deleting save."
                    
        except Exception as e:
            logger.error(f"Error in delete_selected_save: {e}", exc_info=True)
            self.message = f"Error deleting save: {e}"