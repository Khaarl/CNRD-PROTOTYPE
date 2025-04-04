import sys
import os
import random
import logging
from player import Player
from daemon import Daemon, Program
import data_manager

# Remove hardcoded dictionaries and load from config
def initialize_game():
    """Initialize the game data and objects"""
    # Load game data from config files
    game_data = data_manager.load_game_data()
    
    # Create global variables with loaded data
    global DAEMON_BASE_STATS, PROGRAMS, world_map
    DAEMON_BASE_STATS = game_data["daemons"]
    PROGRAMS = game_data["programs"]
    
    # Load world map
    world_data = game_data["locations"]
    world_map = world_data["locations"]
    
    logging.info("Game initialized with data from config files")
    return world_data["start_location"], world_map

def create_daemon(daemon_name, level=1):
    """Create a new daemon object from the base stats"""
    if daemon_name not in DAEMON_BASE_STATS:
        logging.error(f"Unknown daemon: {daemon_name}")
        return None
        
    base_stats = DAEMON_BASE_STATS[daemon_name]
    
    # Create programs for the daemon
    daemon_programs = []
    for program_id in base_stats.get("programs", []):
        if program_id in PROGRAMS:
            program_data = PROGRAMS[program_id]
            program = Program(
                program_id,
                program_data["name"], 
                program_data["power"], 
                program_data["accuracy"],
                program_data["type"],
                program_data["effect"],
                program_data["description"]
            )
            daemon_programs.append(program)
    
    # Create and return the daemon
    return Daemon(
        name=daemon_name,
        daemon_type=base_stats["type"],
        level=level,
        base_hp=base_stats["hp"],
        base_attack=base_stats["attack"],
        base_defense=base_stats["defense"],
        base_speed=base_stats["speed"],
        base_special=base_stats["special"],
        programs=daemon_programs
    )

def main():
    # Configure logging
    logging.basicConfig(
        filename='logs/game.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)
    
    logging.info("Game starting up")
    
    # Initialize game data and get starting location
    start_location, world_map = initialize_game()
    
    # Welcome message
    print("\n" + "=" * 60)
    print("Welcome to CNRD - Cyber Network Roguelike with Daemons")
    print("=" * 60)
    
    # Create player
    player_name = input("\nEnter your username: ")
    
    # Try to load saved game
    player_data = data_manager.load_game(player_name.lower())
    
    if player_data:
        # Create player from saved data
        player = Player.from_dict(player_data)
        print(f"Welcome back, {player.name}!")
    else:
        # Create new player
        print(f"\nCreating new profile for {player_name}...")
        
        # Choose starting daemon
        print("\nChoose your starting daemon:")
        print("1. Virulet (Virus type - balanced)")
        print("2. Pyrowall (Firewall type - high defense)")
        print("3. Aquabyte (Crypto type - balanced)")
        
        valid_choice = False
        starter_daemon = None
        
        while not valid_choice:
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                starter_daemon = create_daemon("virulet", level=5)
                valid_choice = True
            elif choice == "2":
                starter_daemon = create_daemon("pyrowall", level=5)
                valid_choice = True
            elif choice == "3":
                starter_daemon = create_daemon("aquabyte", level=5)
                valid_choice = True
            else:
                print("Invalid choice, please try again.")
        
        # Create new player
        player = Player(player_name, start_location, [starter_daemon])
        print(f"\nWelcome, {player.name}! You've chosen {starter_daemon.name} as your starting daemon.")
    
    # Game loop
    playing = True
    while playing:
        # Get current location
        current_loc = player.location
        
        # Verify the location exists in world map
        if current_loc not in world_map:
            logging.error(f"Invalid location ID: {current_loc}")
            print(f"Error: Invalid location ID '{current_loc}'. Moving to start location.")
            player.location = start_location
            current_loc = start_location
        
        # Get location data
        location = world_map[current_loc]
        
        # Display location info
        print("\n" + "=" * 60)
        print(f"Location: {location['name']}")
        print(location['description'])
        print("=" * 60)
        
        # Show available exits
        print("\nAvailable directions:")
        for direction, destination in location['exits'].items():
            dest_name = world_map[destination]['name']
            print(f"- {direction.capitalize()}: {dest_name}")
        
        # Player commands
        print("\nCommands: move, status, save, quit")
        command = input("\nWhat would you like to do? ").lower()
        
        if command == "move":
            direction = input("Which direction? ").lower()
            
            if direction in location['exits']:
                # Move player
                new_location = location['exits'][direction]
                player.location = new_location
                print(f"Moving {direction} to {world_map[new_location]['name']}...")
                
                # Random encounter check
                if random.randint(1, 100) <= world_map[new_location]['encounter_rate']:
                    # Wild daemon encounter
                    wild_daemon_names = list(DAEMON_BASE_STATS.keys())
                    wild_daemon_name = random.choice(wild_daemon_names)
                    wild_daemon = create_daemon(wild_daemon_name, level=random.randint(1, 10))
                    
                    print(f"\nA wild {wild_daemon.name} appeared!")
                    
                    # Combat options
                    print("\nWhat will you do?")
                    print("1. Fight")
                    print("2. Run")
                    
                    combat_choice = input("Enter your choice (1-2): ")
                    
                    if combat_choice == "1":
                        print("\nFighting not fully implemented yet.")
                        # Here would be the combat system
                        
                        # Temporarily, add the wild daemon to player's collection
                        print(f"You've captured {wild_daemon.name}!")
                        player.add_daemon(wild_daemon)
                    else:
                        print("You ran away safely!")
            else:
                print("You can't go that way.")
                
        elif command == "status":
            print("\n----- Player Status -----")
            print(f"Name: {player.name}")
            print(f"Location: {world_map[player.location]['name']}")
            print("\nDaemons:")
            
            for i, daemon in enumerate(player.daemons, 1):
                print(f"{i}. {daemon.name} (Lvl {daemon.level}) - {daemon.daemon_type} type")
                
            # Detailed daemon info
            if player.daemons:
                daemon_choice = input("\nEnter daemon number for details (or press Enter to skip): ")
                
                if daemon_choice.isdigit():
                    daemon_idx = int(daemon_choice) - 1
                    
                    if 0 <= daemon_idx < len(player.daemons):
                        selected_daemon = player.daemons[daemon_idx]
                        
                        print(f"\n----- {selected_daemon.name} Details -----")
                        print(f"Type: {selected_daemon.daemon_type}")
                        print(f"Level: {selected_daemon.level}")
                        print(f"HP: {selected_daemon.hp}/{selected_daemon.max_hp}")
                        print(f"Attack: {selected_daemon.attack}")
                        print(f"Defense: {selected_daemon.defense}")
                        print(f"Speed: {selected_daemon.speed}")
                        print(f"Special: {selected_daemon.special}")
                        
                        print("\nPrograms:")
                        for program in selected_daemon.programs:
                            print(f"- {program.name}: {program.description}")
                
        elif command == "save":
            success = data_manager.save_game(player.to_dict(), player.name.lower())
            if success:
                print("Game saved successfully.")
            else:
                print("Error saving game.")
                
        elif command == "quit":
            # Ask to save before quitting
            save_choice = input("Save game before quitting? (y/n): ").lower()
            
            if save_choice == "y":
                success = data_manager.save_game(player.to_dict(), player.name.lower())
                if success:
                    print("Game saved successfully.")
                else:
                    print("Error saving game.")
                    
            print("Thanks for playing CNRD!")
            playing = False
            
        else:
            print("Unknown command. Try 'move', 'status', 'save', or 'quit'.")
    
    logging.info("Game shutting down")

if __name__ == "__main__":
    main()
