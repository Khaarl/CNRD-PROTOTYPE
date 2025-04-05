import os
import sys
from pathlib import Path

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.save_dir = Path("saves")
        
    def display_menu(self):
        """Display the main menu options"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 50)
        print("     CYBERPUNK NETRUNNER: DIGITAL HUNTERS")
        print("=" * 50)
        print("\n1. New Game")
        print("2. Load Game")
        print("3. Quick Fight")
        print("4. Quit")
        print("\n" + "=" * 50)
    
    def get_save_files(self):
        """Get a list of available save files"""
        saves = []
        if self.save_dir.exists():
            saves = list(self.save_dir.glob("*.json"))
        return saves
    
    def run(self):
        """Run the main menu logic and return the selected action"""
        while True:
            self.display_menu()
            try:
                choice = input("Enter your choice (1-4): ")
                
                if choice == "1":  # New Game
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\n--- New Game ---")
                    player_name = input("Enter your runner name: ").strip()
                    if player_name:
                        return {"action": "new_game", "player_name": player_name}
                    else:
                        print("Invalid name. Please try again.")
                        input("Press Enter to continue...")
                        
                elif choice == "2":  # Load Game
                    saves = self.get_save_files()
                    if not saves:
                        print("\nNo save files found.")
                        input("Press Enter to continue...")
                        continue
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\n--- Load Game ---")
                    for i, save in enumerate(saves):
                        print(f"{i+1}. {save.stem}")
                    print(f"{len(saves)+1}. Back to Main Menu")
                    
                    try:
                        save_choice = int(input(f"Select save file (1-{len(saves)+1}): "))
                        if 1 <= save_choice <= len(saves):
                            return {"action": "load_game", "save_file": saves[save_choice-1]}
                        elif save_choice == len(saves) + 1:
                            continue  # Back to main menu
                        else:
                            print("Invalid choice.")
                            input("Press Enter to continue...")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                        input("Press Enter to continue...")
                        
                elif choice == "3":  # Quick Fight
                    return {"action": "quick_fight"}
                    
                elif choice == "4":  # Quit
                    print("\nThanks for playing!")
                    sys.exit(0)
                    
                else:
                    print("\nInvalid choice. Please enter a number between 1 and 4.")
                    input("Press Enter to continue...")
                    
            except Exception as e:
                print(f"\nError: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    # Test the main menu
    menu = MainMenu(game=None)
    result = menu.run()
    print("Menu returned:", result)