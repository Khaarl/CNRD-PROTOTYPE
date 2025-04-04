import sys
import os
import random
import logging
from player import Player
from daemon import Daemon, Program, TYPE_CHART, STATUS_EFFECTS  # Added imports for TYPE_CHART and STATUS_EFFECTS
from location import Location # Added Location import
import data_manager

# Global game data (populated by initialize_game)
DAEMON_BASE_STATS = {}
PROGRAMS = {}
world_map = {} # Will store Location objects, keyed by ID

def initialize_game():
    """Initialize the game data and objects, populating global variables."""
    # Load game data from config files
    game_data = data_manager.load_game_data()

    # Create global variables with loaded data
    global DAEMON_BASE_STATS, PROGRAMS, world_map # Ensure we modify the global world_map
    DAEMON_BASE_STATS = game_data.get("daemons", {}) # Use .get for safety
    PROGRAMS = game_data.get("programs", {})

    # Load world map data first
    world_data = game_data.get("locations", {})
    raw_locations = world_data.get("locations", {}) # This is the dict from JSON

    # Create Location objects from the raw data
    world_map = {}
    start_location_id = world_data.get("start_location") # Get start ID early for logging if needed

    for loc_id, loc_data in raw_locations.items():
        # Check if loc_data is a dictionary before accessing keys
        if isinstance(loc_data, dict):
            world_map[loc_id] = Location(
                loc_id=loc_id,
                name=loc_data.get("name", f"Unknown Location {loc_id}"), # Use .get with defaults
                description=loc_data.get("description", ""),
                exits=loc_data.get("exits", {}),
                encounter_rate=loc_data.get("encounter_rate", 0.0),
                wild_daemons=loc_data.get("wild_daemons", [])
            )
        else:
            logging.error(f"Invalid data format for location ID '{loc_id}' in config. Expected a dictionary, got {type(loc_data)}")

    logging.info("Game initialized with data from config files and Location objects created.")

    if not start_location_id or start_location_id not in world_map:
         logging.error(f"Start location ID '{start_location_id}' missing or invalid in config. Defaulting.")
         # Try to find *any* valid location ID as a fallback
         valid_ids = list(world_map.keys())
         start_location_id = valid_ids[0] if valid_ids else None
         if not start_location_id:
              logging.critical("No valid locations found in config! Cannot start game.")
              print("CRITICAL ERROR: No valid locations defined. Check config/locations.json")
              sys.exit(1)
         logging.warning(f"Defaulting start location to '{start_location_id}'.")


    return start_location_id # Just return the start ID

def create_daemon(daemon_id, level=1):
    """Create a new daemon object from the base stats based on its ID and level."""
    if daemon_id not in DAEMON_BASE_STATS:
        logging.error(f"Unknown daemon ID: {daemon_id}")
        return None

    base_stats = DAEMON_BASE_STATS[daemon_id]

    # Create programs for the daemon based on learnset and level
    daemon_programs = []
    learnset = base_stats.get("learnset", {}) # Learnset should be like {"1": ["prog1"], "5": ["prog2"]}
    for lvl_str, program_ids in learnset.items():
        try:
            learn_level = int(lvl_str)
            if level >= learn_level:
                # Ensure program_ids is a list
                if not isinstance(program_ids, list):
                    logging.warning(f"Program IDs for level {learn_level} in '{daemon_id}' learnset is not a list: {program_ids}. Skipping.")
                    continue

                for program_id in program_ids:
                    if program_id in PROGRAMS:
                        program_data = PROGRAMS[program_id]
                        # Avoid adding duplicates if learned at multiple levels below current
                        if not any(p.id == program_id for p in daemon_programs):
                            program = Program(
                                program_id,
                                program_data.get("name", f"Unknown Program {program_id}"), # Use .get
                                program_data.get("power", 0),
                                program_data.get("accuracy", 100),
                                program_data.get("type", "Untyped"),
                                program_data.get("effect", "none"),
                                program_data.get("description", "")
                            )
                            daemon_programs.append(program)
                    else:
                         logging.warning(f"Program ID '{program_id}' listed in learnset for '{daemon_id}' but not found in PROGRAMS.")
        except ValueError:
            logging.warning(f"Invalid level '{lvl_str}' in learnset for daemon '{daemon_id}'.")


    # Create and return the daemon
    # Ensure 'types' is a list, handle potential single string from older config
    daemon_types = base_stats.get("types", ["Untyped"]) # Default to list with "Untyped"
    if isinstance(daemon_types, str):
        daemon_types = [daemon_types] # Convert single string to list

    return Daemon(
        name=base_stats.get("name", daemon_id), # Use name from data, fallback to ID
        types=daemon_types, # Use the list of types
        level=level,
        base_hp=base_stats.get("hp", 10), # Use .get with defaults for safety
        base_attack=base_stats.get("attack", 5),
        base_defense=base_stats.get("defense", 5),
        base_speed=base_stats.get("speed", 5),
        base_special=base_stats.get("special", 5),
        capture_rate=base_stats.get("capture_rate", 100), # Add capture rate
        programs=daemon_programs
    )

# --- Combat Function ---
def run_combat(player, enemy_daemon):
    """Handles the turn-based combat loop.
    Returns:
        str: Combat outcome ("player_win", "enemy_win", "run", "capture")
    """
    logging.info(f"Combat started: Player vs {enemy_daemon.name} (Lv.{enemy_daemon.level})")
    print("\n" + "!" * 10 + f" Wild {enemy_daemon.name} (Lv.{enemy_daemon.level}) appeared! " + "!" * 10)

    player_active_daemon = player.get_active_daemon()
    if not player_active_daemon:
        print("You have no conscious Daemons to fight with!")
        logging.warning("Combat started with no active player daemon.")
        return "run" # Treat as running away immediately

    print(f"Go, {player_active_daemon.name}!")

    combat_state = "ongoing" # ongoing, player_win, enemy_win, run, capture

    while combat_state == "ongoing":
        print("\n" + "-" * 20)
        print(f"Enemy: {enemy_daemon.name} (Lv.{enemy_daemon.level}) HP: {enemy_daemon.hp}/{enemy_daemon.max_hp}")
        if enemy_daemon.status_effect: print(f"       Status: {enemy_daemon.status_effect}")
        print(f"Your : {player_active_daemon.name} (Lv.{player_active_daemon.level}) HP: {player_active_daemon.hp}/{player_active_daemon.max_hp}")
        if player_active_daemon.status_effect: print(f"       Status: {player_active_daemon.status_effect}")
        print("-" * 20)

        # --- Player Turn ---
        action_chosen = False
        player_action = None
        selected_program = None
        target_daemon = None # For switching

        # Check if player daemon can act based on status effects
        can_act = True
        if player_active_daemon.status_effect == "LOCKED":
            # 30% chance of being unable to act when LOCKED
            if random.random() < 0.3:
                print(f"{player_active_daemon.name} is LOCKED and unable to act this turn!")
                can_act = False
                player_action = "locked" # Skip turn
                action_chosen = True
            else:
                print(f"{player_active_daemon.name} fights against the LOCK!") 

        while not action_chosen:
            print("\nChoose action:")
            print("  [F]ight")
            print("  [S]witch Daemon")
            print("  [C]apture")
            print("  [R]un")
            choice = input("> ").lower().strip()

            if choice == 'f':
                # Choose program
                print("Choose program:")
                if not player_active_daemon.programs:
                    print("  No programs available!")
                    continue
                for i, prog in enumerate(player_active_daemon.programs):
                    print(f"  {i+1}. {prog.name} ({prog.type}, Pow:{prog.power}, Acc:{prog.accuracy})")
                print("  0. Back")
                prog_choice = input("> ").strip()
                if prog_choice.isdigit():
                    prog_idx = int(prog_choice) - 1
                    if 0 <= prog_idx < len(player_active_daemon.programs):
                        player_action = "fight"
                        selected_program = player_active_daemon.programs[prog_idx]
                        action_chosen = True
                    elif prog_idx == -1: # Back option
                        continue
                    else:
                        print("Invalid program number.")
                else:
                    print("Invalid input.")

            elif choice == 's':
                available_daemons = player.get_healthy_daemons(exclude=player_active_daemon)
                if not available_daemons:
                    print("No other conscious Daemons to switch to!")
                    continue
                print("Switch to which Daemon?")
                for i, d in enumerate(available_daemons):
                    print(f"  {i+1}. {d.name} (Lv.{d.level}) HP: {d.hp}/{d.max_hp}")
                print("  0. Back")
                switch_choice = input("> ").strip()
                if switch_choice.isdigit():
                    switch_idx = int(switch_choice) - 1
                    if 0 <= switch_idx < len(available_daemons):
                        player_action = "switch"
                        target_daemon = available_daemons[switch_idx]
                        action_chosen = True
                    elif switch_idx == -1: # Back option
                        continue
                    else:
                        print("Invalid daemon number.")
                else:
                    print("Invalid input.")

            elif choice == 'c':
                # Basic capture logic
                player_action = "capture"
                action_chosen = True

            elif choice == 'r':
                # Simple run logic for now
                player_action = "run"
                action_chosen = True # Assume success for now against wild

            else:
                print("Invalid choice.")

        # --- Enemy Turn (Simple AI) ---
        # Check if enemy can act based on status effects
        enemy_can_act = True
        if enemy_daemon.status_effect == "LOCKED":
            # 30% chance of being unable to act when LOCKED
            if random.random() < 0.3:
                print(f"{enemy_daemon.name} is LOCKED and unable to act this turn!")
                enemy_can_act = False
                enemy_action = "locked" # Skip turn
            else:
                print(f"{enemy_daemon.name} fights against the LOCK!")
                enemy_can_act = True
        
        # If enemy can act, determine its action
        if enemy_can_act:
            # Improved enemy AI: choose highest damage program if HP low, otherwise random
            enemy_action = "fight"
            if enemy_daemon.programs:
                if enemy_daemon.hp < enemy_daemon.max_hp * 0.3:
                    # Find highest power program for aggressive behavior when low HP
                    best_program = max(enemy_daemon.programs, key=lambda p: p.power)
                    enemy_program = best_program
                else:
                    # Otherwise random choice
                    enemy_program = random.choice(enemy_daemon.programs)
            else:
                 enemy_action = "struggle" # Or some default action if no programs
        else:
            enemy_action = "locked" # Skip turn 
            enemy_program = None

        # --- Determine Turn Order ---
        player_goes_first = player_active_daemon.speed >= enemy_daemon.speed

        # Apply status effect modifiers
        if player_active_daemon.status_effect == "LAGGING":
            # Speed reduced when LAGGING
            player_goes_first = False
            
        # --- Execute Turns ---
        participants = [(player, player_active_daemon, player_action, selected_program, target_daemon),
                        (None, enemy_daemon, enemy_action, enemy_program, None)] # None for player indicates enemy
        if not player_goes_first:
            participants.reverse()

        for current_player, current_daemon, action, program, switch_target in participants:
            if combat_state != "ongoing": break # Stop if combat ended mid-turn
            if current_daemon.is_fainted(): continue # Skip turn if fainted before action

            is_player_turn = (current_player is not None)
            opponent = enemy_daemon if is_player_turn else player_active_daemon

            print("-" * 10)
            
            # Skip turn if locked and failed to break free (handled above)
            if action == "locked":
                print(f"{current_daemon.name}'s turn was skipped due to being LOCKED!")
                continue

            if action == "fight":
                if program:
                    result = current_daemon.use_program(program, opponent)
                    print(result["message"])
                    
                    if result["hit"] and result["damage"] is not None:
                        # Calculate type effectiveness for display message
                        multiplier = 1.0
                        for target_type in opponent.types:
                            type_key = program.type.upper()
                            target_key = target_type.upper()
                            if type_key in TYPE_CHART and target_key in TYPE_CHART[type_key]:
                                multiplier *= TYPE_CHART[type_key][target_key]
                        
                        # Show effectiveness message
                        if multiplier > 1.5:
                            print("It's super effective!")
                        elif 0 < multiplier < 0.6: 
                            print("It's not very effective...")
                        elif multiplier == 0:
                            print("It has no effect...")
                            
                        # Apply damage
                        if opponent.take_damage(result["damage"]):
                            print(f"{opponent.name} fainted!")
                            combat_state = "player_win" if is_player_turn else "enemy_win"
                            # Don't break here yet, let the other participant act if they haven't
                    
                    # Handle status effects from special programs
                    if result["effect_applied"] and "status" in result["effect_applied"]:
                        status_type = result["effect_applied"].split(":")[1] 
                        if status_type in STATUS_EFFECTS:
                            opponent.status_effect = status_type
                            print(f"{opponent.name} was afflicted with {status_type}!")
                else:
                    # Basic "Struggle" if no programs
                    print(f"{current_daemon.name} flailed wildly!")
                    # Simple typeless damage
                    struggle_damage = max(1, int(current_daemon.attack / 4))
                    if opponent.take_damage(struggle_damage):
                         print(f"{opponent.name} fainted!")
                         combat_state = "player_win" if is_player_turn else "enemy_win"


            elif action == "switch":
                if is_player_turn:
                    # Check if switch_target is already fainted (shouldn't happen with get_healthy_daemons)
                    if switch_target.is_fainted():
                         print(f"{switch_target.name} is already fainted!")
                         # Force player to choose again? For now, just skip turn.
                         print(f"{current_daemon.name}'s turn was skipped.")
                    else:
                         player_active_daemon = switch_target
                         player.set_active_daemon(player_active_daemon) # Assumes Player class has this method
                         print(f"You switched to {player_active_daemon.name}!")
                else:
                    # Enemy switch logic (not implemented for simple AI)
                    pass

            elif action == "capture":
                 # Calculate catch chance (simplified from design doc)
                max_hp = enemy_daemon.max_hp
                current_hp = enemy_daemon.hp
                base_rate = enemy_daemon.capture_rate # Lower is harder
                # More HP missing = higher chance. Max factor is 1 when HP is 1/3 or less.
                hp_factor = max(0.1, (max_hp * 3 - current_hp * 2) / (max_hp * 3))
                
                # Status bonus - update to use proper status effects 
                status_bonus = 1.0
                if enemy_daemon.status_effect:
                    # Give bonuses based on status
                    if enemy_daemon.status_effect == "LOCKED":
                        status_bonus = 2.0  # Easier to capture when locked
                    elif enemy_daemon.status_effect == "CORRUPTED":
                        status_bonus = 1.7  # Easier when losing HP
                    else:
                        status_bonus = 1.5  # Other status effects

                # Simplified chance calculation (adjust divisor for balance)
                catch_chance = min(1.0, (base_rate / 255.0) * hp_factor * status_bonus)

                print(f"Attempting capture... (Chance: {catch_chance:.2f})")
                if random.random() < catch_chance:
                    print(f"Gotcha! {enemy_daemon.name} was captured!")
                    # Create a copy for the player, don't give the actual enemy object
                    captured_daemon = Daemon.from_dict(enemy_daemon.to_dict())
                    player.add_daemon(captured_daemon) # Assumes Player class has add_daemon
                    combat_state = "capture" # Use distinct state for capture
                    # No XP for capture? Or maybe some? Design decision.
                else:
                    print(f"Oh no! The Daemon broke free!")
                    # Enemy gets its turn after failed capture attempt (handled by loop structure)

            elif action == "run":
                if is_player_turn:
                    # Base flee chance of 90% for wild battles
                    flee_chance = 0.9
                    
                    # Modify flee chance based on speed comparison
                    speed_ratio = player_active_daemon.speed / max(1, enemy_daemon.speed)
                    flee_chance *= speed_ratio
                    
                    if random.random() < flee_chance:
                        print("You ran away safely!")
                        combat_state = "run"
                    else:
                        print("Couldn't get away!")
                else:
                    # Enemy doesn't run in this simple AI
                    pass

            # Check if opponent fainted AFTER the action, if combat still ongoing
            if opponent.is_fainted() and combat_state == "ongoing":
                 print(f"{opponent.name} fainted!")
                 combat_state = "player_win" if is_player_turn else "enemy_win"

            # End of participant's turn processing
            if combat_state != "ongoing": break # Exit inner loop if combat ended

        # --- End of Turn ---
        # Apply status effects
        if combat_state == "ongoing":
            # Player daemon status effects
            if player_active_daemon.status_effect == "CORRUPTED":
                damage = max(1, int(player_active_daemon.max_hp / 16))  # 1/16 of max HP
                print(f"{player_active_daemon.name} is damaged by CORRUPTION! (-{damage} HP)")
                if player_active_daemon.take_damage(damage):
                    print(f"{player_active_daemon.name} fainted from CORRUPTION!")
                    combat_state = "enemy_win"
            
            # Enemy daemon status effects
            if combat_state == "ongoing" and enemy_daemon.status_effect == "CORRUPTED":
                damage = max(1, int(enemy_daemon.max_hp / 16))  # 1/16 of max HP
                print(f"{enemy_daemon.name} is damaged by CORRUPTION! (-{damage} HP)")
                if enemy_daemon.take_damage(damage):
                    print(f"{enemy_daemon.name} fainted from CORRUPTION!")
                    combat_state = "player_win"

        # Check if player needs to switch after their daemon fainted mid-round
        if player_active_daemon.is_fainted() and combat_state == "ongoing":
             print(f"{player_active_daemon.name} fainted!")
             player_active_daemon = player.get_active_daemon() # Check if another is auto-selected or prompt
             if not player_active_daemon:
                  print("You have no more conscious Daemons!")
                  combat_state = "enemy_win" # Player loses
             else:
                  # Need to prompt player to switch
                  print("You need to switch to another Daemon.")
                  available_daemons = player.get_healthy_daemons()
                  if not available_daemons: # Should not happen if get_active_daemon worked, but safety check
                       print("Error: No healthy daemons available despite check.")
                       combat_state = "enemy_win"
                  else:
                       while True:
                            print("Switch to which Daemon?")
                            for i, d in enumerate(available_daemons):
                                print(f"  {i+1}. {d.name} (Lv.{d.level}) HP: {d.hp}/{d.max_hp}")
                            switch_choice = input("> ").strip()
                            if switch_choice.isdigit():
                                switch_idx = int(switch_choice) - 1
                                if 0 <= switch_idx < len(available_daemons):
                                    player_active_daemon = available_daemons[switch_idx]
                                    player.set_active_daemon(player_active_daemon)
                                    print(f"Go, {player_active_daemon.name}!")
                                    break # Valid switch made
                                else:
                                    print("Invalid daemon number.")
                            else:
                                print("Invalid input.")


    # --- Combat End ---
    if combat_state == "player_win":
        print(f"\nYou defeated {enemy_daemon.name}!")
        # Award XP (simple: give to active daemon that participated)
        # TODO: More complex XP calculation based on level difference & participation
        xp_gain = enemy_daemon.level * 15 # Basic XP formula
        # Ensure the final active daemon isn't fainted before giving XP
        final_active = player.get_active_daemon()
        if final_active and not final_active.is_fainted():
             final_active.gain_xp(xp_gain)
        else:
             # Maybe distribute XP to others later? For now, no XP if last one fainted.
             logging.info("Last active daemon fainted, no XP awarded.")

    elif combat_state == "enemy_win":
        print("\nYou were defeated...")
        # TODO: Implement consequences (e.g., return to safe spot, lose creds)
        print("You blacked out!") # Classic message
    elif combat_state == "run":
        pass # Message already printed during action
    elif combat_state == "capture":
        pass # Message already printed during action

    return combat_state # Return final status

def main(): # Explicitly ensure zero indentation
    # Configure logging
    # Use rotating file handler later if needed
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'game.log')

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)

    logging.info("Game starting up")

    # Initialize game data and get starting location ID
    try:
        start_location_id = initialize_game()
    except Exception as e:
        logging.critical(f"Failed to initialize game data: {e}", exc_info=True)
        print(f"CRITICAL ERROR during initialization: {e}. Check logs and config files.")
        sys.exit(1)

    # Welcome message
    print("\n" + "=" * 60)
    print("Welcome to CNRD - Cyber Network Roguelike with Daemons")
    print("=" * 60)

    # Create player
    player_name = input("\nEnter your username: ")

    # Try to load saved game
    player = None
    try:
        player_data = data_manager.load_game(player_name.lower())
        if player_data:
            # Create player from saved data
            player = Player.from_dict(player_data, world_map) # Pass world_map if needed by Player.from_dict
            print(f"Welcome back, {player.name}!")
            # Ensure player location is valid after loading
            if player.location not in world_map:
                 logging.warning(f"Loaded player location '{player.location}' is invalid. Resetting to start location '{start_location_id}'.")
                 player.location = start_location_id
    except Exception as e:
        logging.error(f"Failed to load game for {player_name}: {e}", exc_info=True)
        print(f"Error loading saved game: {e}. Starting a new game.")
        player = None # Ensure player is None if loading failed

    if player is None:
        # Create new player
        print(f"\nCreating new profile for {player_name}...")

        # Choose starting daemon
        print("\nChoose your starting daemon:")
        print("1. Virulet (Malware type - balanced)") # Updated type based on daemon.py example
        print("2. Pyrowall (Shell type - high defense)") # Assuming Shell type
        print("3. Aquabyte (Encryption type - balanced)") # Assuming Encryption type

        valid_choice = False
        starter_daemon = None
        starter_id = None

        while not valid_choice:
            choice = input("\nEnter your choice (1-3): ")

            if choice == "1":
                starter_id = "virulet"
                valid_choice = True
            elif choice == "2":
                starter_id = "pyrowall"
                valid_choice = True
            elif choice == "3":
                starter_id = "aquabyte"
                valid_choice = True
            else:
                print("Invalid choice, please try again.")

        if starter_id:
             starter_daemon = create_daemon(starter_id, level=5)

        # Ensure the chosen starter is not None before proceeding
        if starter_daemon:
            player = Player(player_name, start_location_id, [starter_daemon]) # Use start_location_id
            print(f"\nWelcome, {player.name}! You've chosen {starter_daemon.name} as your starting daemon.")
        else:
            logging.critical(f"Failed to create starter daemon '{starter_id}'. Exiting.")
            print(f"Error: Could not create your starting daemon '{starter_id}'. Please check config files.")
            sys.exit(1)

    # Game state management
    game_state = "roaming" # Possible states: roaming, combat
    current_enemy_daemon = None # Holds the daemon for the current combat encounter

    # Game loop
    playing = True
    while playing:
        # --- State: Roaming ---
        if game_state == "roaming":
            # Get current location object
            current_loc_id = player.location
            if current_loc_id not in world_map:
                logging.error(f"Player location ID '{current_loc_id}' not found in world_map. Resetting to start.")
                player.location = start_location_id
                if not player.location or player.location not in world_map: # Still no valid location
                     logging.critical("Cannot find any valid location after reset. Exiting.")
                     print("CRITICAL ERROR: Cannot determine player location. Check config.")
                     sys.exit(1)
                current_loc_id = player.location

            location = world_map[current_loc_id] # Get the Location object

            # Display location info using Location object's method
            location.display()

            # Show available exits using Location object's exits
            print("\nAvailable directions:")
            if location.exits:
                for direction, destination_id in location.exits.items():
                    # Ensure destination exists before trying to access its name
                    dest_name = world_map[destination_id].name if destination_id in world_map else "Unknown Area"
                    print(f"- {direction.capitalize()}: {dest_name}")
            else:
                print("  None")

            # Player commands
            print("\nCommands: move [direction], scan, status, daemons, save, quit")
            command_input = input("\nWhat would you like to do? ").lower().strip()
            parts = command_input.split()
            if not parts: continue
            command = parts[0]
            args = parts[1:]

            if command == "move":
                if not args:
                    print("Move where? (e.g., move north)")
                    continue
                direction = args[0]

                if direction in location.exits:
                    destination_id = location.exits[direction]
                    if destination_id in world_map:
                        # Move player
                        player.location = destination_id
                        new_location = world_map[destination_id] # Get the new Location object
                        print(f"Moving {direction} to {new_location.name}...")

                        # --- Random Encounter Check ---
                        if random.random() < new_location.encounter_rate:
                            wild_info = new_location.get_random_wild_daemon_info()
                            if wild_info:
                                daemon_id = wild_info.get("id")
                                min_lvl = wild_info.get("min_lvl", 1)
                                max_lvl = wild_info.get("max_lvl", min_lvl) # Default max to min if missing
                                level = random.randint(min_lvl, max_lvl)

                                if not daemon_id:
                                     logging.error(f"Wild daemon info in {new_location.name} is missing 'id': {wild_info}")
                                else:
                                     current_enemy_daemon = create_daemon(daemon_id, level)
                                     if current_enemy_daemon:
                                         game_state = "combat" # Switch state
                                         # No need for combat options here, handled by the combat state block
                                     else:
                                         logging.error(f"Failed to create wild daemon '{daemon_id}' (Level {level}) for encounter in {new_location.name}.")
                            else:
                                logging.info(f"Encounter triggered in {new_location.name} but no wild_daemons defined or list is empty.")
                    else:
                        print(f"Error: Destination '{destination_id}' not found in world map.")
                        logging.error(f"Exit '{direction}' in location '{current_loc_id}' points to invalid destination '{destination_id}'.")
                else:
                    print("You can't go that way.")

            elif command == "scan":
                print(f"Scanning {location.name}...")
                
                # Provide more detailed information about the area
                print(f"\nDetailed scan of {location.name}:")
                print(f"  {location.description}")
                
                # Check if this location has wild daemons defined
                if location.wild_daemons:
                    print("  Daemon signals detected in this area.")
                else:
                    print("  No daemon signals detected in this area.")
                    
                # Add a bit more detail about exits
                if location.exits:
                    print("\nDetailed exit analysis:")
                    for direction, destination_id in location.exits.items():
                        dest_name = world_map[destination_id].name if destination_id in world_map else "Unknown Area"
                        print(f"  {direction.capitalize()} → {dest_name}")
                
                # Determine the scan encounter rate (default to location's normal rate * 1.5)
                scan_encounter_rate = getattr(location, "scan_encounter_rate", 
                                              min(1.0, location.encounter_rate * 1.5))
                
                # --- Random Encounter Check for Scanning ---
                if location.wild_daemons and random.random() < scan_encounter_rate:
                    print("\nYour scanning activity has alerted nearby daemons!")
                    wild_info = location.get_random_wild_daemon_info()
                    if wild_info:
                        daemon_id = wild_info.get("id")
                        min_lvl = wild_info.get("min_lvl", 1)
                        max_lvl = wild_info.get("max_lvl", min_lvl)
                        # Scanning tends to attract slightly higher level daemons
                        level_bonus = random.randint(0, 2)  # 0-2 level bonus
                        level = min(max_lvl + level_bonus, max_lvl + 2)
                        
                        if daemon_id:
                            current_enemy_daemon = create_daemon(daemon_id, level)
                            if current_enemy_daemon:
                                game_state = "combat"
                            else:
                                logging.error(f"Failed to create wild daemon '{daemon_id}' during scan.")
                    else:
                        logging.info("Scan encounter triggered but no wild_daemons defined or list is empty.")

            elif command == "status":
                player.display_status(world_map) # Pass world_map to display location name

            elif command == "daemons":
                 if not player.daemons:
                      print("You have no Daemons.")
                 else:
                      print("\nYour Daemons:")
                      for i, daemon in enumerate(player.daemons):
                           print(f"\n--- Daemon {i+1} ---")
                           daemon.display_summary() # Use the detailed display from Daemon class

            elif command == "save":
                try:
                    success = data_manager.save_game(player.to_dict(), player.name.lower())
                    if success:
                        print("Game saved successfully.")
                    else:
                        # data_manager should log the error
                        print("Error saving game. Check logs.")
                except Exception as e:
                    logging.error(f"Exception during save command: {e}", exc_info=True)
                    print(f"An unexpected error occurred while saving: {e}")


            elif command == "quit":
                # Ask to save before quitting
                save_choice = input("Save game before quitting? (y/n): ").lower()
                if save_choice == 'y':
                    try:
                        success = data_manager.save_game(player.to_dict(), player.name.lower())
                        if success:
                            print("Game saved successfully.")
                        else:
                            print("Error saving game. Check logs.")
                    except Exception as e:
                         logging.error(f"Exception during quit-save: {e}", exc_info=True)
                         print(f"An unexpected error occurred while saving: {e}")

                print("Thanks for playing CNRD!")
                playing = False

            else:
                print("Unknown command. Try 'move [direction]', 'status', 'daemons', 'save', or 'quit'.")

        # --- State: Combat ---
        elif game_state == "combat":
            if not current_enemy_daemon:
                 logging.error("Entered combat state but current_enemy_daemon is None.")
                 game_state = "roaming" # Recover by going back to roaming
                 continue

            # Ensure player has an active daemon before starting combat turn
            if not player.get_active_daemon():
                 print("You have no conscious Daemons left!")
                 combat_result = "enemy_win" # Treat as immediate loss if no daemon available
            else:
                 combat_result = run_combat(player, current_enemy_daemon)

            # Handle combat outcome
            if combat_result == "enemy_win":
                 # Player lost - implement consequences (e.g., game over or return to safe spot)
                 print("\nReturning to the last safe point...") # Placeholder consequence
                 # Find a safe location (e.g., encounter_rate 0 or a specific tagged location)
                 safe_loc_id = start_location_id # Default to start for now
                 # Find first location with 0 encounter rate
                 found_safe = False
                 for loc_id, loc in world_map.items():
                      if loc.encounter_rate == 0:
                           safe_loc_id = loc_id
                           found_safe = True
                           break
                 if not found_safe:
                      logging.warning("No location with encounter_rate 0 found. Returning to absolute start.")

                 player.location = safe_loc_id
                 # Heal player's daemons?
                 player.heal_all_daemons() # Assumes Player class has this method
                 print("Your Daemons have been stabilized.")

            # Reset state after combat
            current_enemy_daemon = None
            game_state = "roaming"

        # --- Other States (e.g., menu, dialogue) ---
        else:
             logging.error(f"Unhandled game state: {game_state}")
             game_state = "roaming" # Attempt recovery

    logging.info("Game shutting down")

if __name__ == "__main__":
    # Ensure necessary directories exist before starting
    # Moved log dir creation inside main() to happen after basicConfig potentially
    save_dir = 'saves'
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            print(f"Error creating save directory '{save_dir}': {e}")
            # Decide if this is critical enough to exit
    # Config dir check might be handled by data_manager or bootstrap

    main()
