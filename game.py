import random
import sys # For exiting the game

# Import classes from other files
from location import Location
from player import Player
from daemon import Daemon, Program, DATA_SIPHON, FIREWALL_BASH, ENCRYPT_SHIELD # Import example programs

# --- Game Data ---

# Define Base Daemon Stats (Could be loaded from JSON later)
DAEMON_BASE_STATS = {
    "virulet": {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60, 'types': ["Malware"]},
    "pyrowall": {'hp': 50, 'attack': 40, 'defense': 65, 'speed': 40, 'types': ["Shell", "Encryption"]},
    "aquabyte": {'hp': 45, 'attack': 50, 'defense': 50, 'speed': 50, 'types': ["Ghost", "Worm"]},
    "rat_bot": {'hp': 30, 'attack': 40, 'defense': 30, 'speed': 70, 'types': ["Physical"]},
    "glitch_sprite": {'hp': 35, 'attack': 60, 'defense': 35, 'speed': 55, 'types': ["Ghost", "Malware"]},
}

# Define Programs (Could be loaded from JSON later)
# Using the ones defined in daemon.py for now
PROGRAMS = {
    "Data Siphon": DATA_SIPHON,
    "Firewall Bash": FIREWALL_BASH,
    "Encrypt Shield": ENCRYPT_SHIELD,
    # Add more programs here
    "Scratch": Program("Scratch", "Physical", 30),
    "Static Shock": Program("Static Shock", "Worm", 40, effect="paralyze_chance"), # Placeholder effect
}

# Define World Map
# Using Location objects imported from location.py
world_map = {
    "dark_alley": Location(
        loc_id="dark_alley",
        name="Dark Alley",
        description="A grimy, narrow alley flickering under a broken neon sign advertising 'SynthNoodles'. The air smells of ozone and stale rain.",
        exits={"north": "market_square"}
    ),
    "market_square": Location(
        loc_id="market_square",
        name="Market Square",
        description="A bustling square choked with neon signs, data-hawkers shouting deals, and synth-food stalls emitting questionable steam. A public dataport hub is visible to the east.",
        exits={"south": "dark_alley", "east": "dataport_hub"},
        encounter_rate=0.25, # 25% chance of encounter
        wild_daemons=[
            {"id": "rat_bot", "min_lvl": 2, "max_lvl": 4},
            {"id": "glitch_sprite", "min_lvl": 3, "max_lvl": 5}
        ]
    ),
    "dataport_hub": Location(
        loc_id="dataport_hub",
        name="Dataport Hub",
        description="Rows of public access dataports hum with activity. Netrunners jack in and out, their faces illuminated by the glow of virtual interfaces.",
        exits={"west": "market_square"},
        encounter_rate=0.1, # Lower chance here
        wild_daemons=[
            {"id": "rat_bot", "min_lvl": 1, "max_lvl": 3},
        ]
    )
    # Add more locations later
}

# --- Helper Functions ---

def create_daemon(daemon_id, level):
    """Factory function to create Daemon instances from base data."""
    if daemon_id not in DAEMON_BASE_STATS:
        print(f"Error: Unknown daemon ID '{daemon_id}'")
        return None

    base_data = DAEMON_BASE_STATS[daemon_id]
    # Determine starting programs based on level (very basic example)
    known_programs = []
    if daemon_id == "virulet":
        known_programs.append(PROGRAMS["Data Siphon"])
        if level >= 4:
             known_programs.append(PROGRAMS["Scratch"]) # Example of learning a move
    elif daemon_id == "rat_bot":
        known_programs.append(PROGRAMS["Scratch"])
    elif daemon_id == "glitch_sprite":
        known_programs.append(PROGRAMS["Static Shock"])
        if level >= 5:
            known_programs.append(PROGRAMS["Data Siphon"])
    # Add more logic for other daemons and levels

    # Create the instance
    daemon = Daemon(
        name=daemon_id.capitalize(), # Simple name generation
        types=base_data['types'],
        base_stats=base_data,
        level=level,
        programs=known_programs
    )
    return daemon

def display_help():
    """Prints the available commands."""
    print("\n--- Available Commands ---")
    print("  go [direction] - Move (e.g., go north)")
    print("  look / l       - Describe the current location")
    print("  status / stat  - Show player status and daemon summary")
    print("  daemons / d    - Show detailed status of your Daemons")
    print("  scan           - Look for nearby Daemons (triggers encounter check)")
    # print("  fight          - (Currently initiated by 'scan' or random encounters)")
    # print("  capture        - (Used during combat)")
    # print("  use [program] (on [target]) - (Used during combat)")
    # print("  switch [daemon number/name] - (Used during combat)")
    # print("  run            - (Used during combat)")
    print("  help / h       - Show this help message")
    print("  quit           - Exit the game")
    print("-------------------------")

# --- Combat System (Basic Placeholder) ---
def start_combat(player, enemy_daemon, world_map):
    """Initiates and handles the combat loop."""
    print("\n" + "="*10 + " COMBAT START " + "="*10)
    print(f"A wild {enemy_daemon.name} (Lv.{enemy_daemon.level}) appears!")

    player_active_daemon = player.get_first_healthy_daemon()
    if not player_active_daemon:
        print("You have no active Daemons to fight!")
        print("="*34)
        return # End combat immediately if no usable daemon

    print(f"Go, {player_active_daemon.name}!")
    print("-" * 34)

    combat_over = False
    while not combat_over:
        # Display combat status
        print(f"Your {player_active_daemon.name}: HP {player_active_daemon.stats['hp']}/{player_active_daemon.stats['max_hp']}")
        print(f"Enemy {enemy_daemon.name}: HP {enemy_daemon.stats['hp']}/{enemy_daemon.stats['max_hp']}") # Approximate HP display?
        print("-" * 34)

        # Player Turn
        action_chosen = False
        while not action_chosen:
            command_input = input("Combat Action ([F]ight, [S]witch, [R]un): ").lower().strip()
            verb = command_input.split()[0] if command_input else ""

            if verb == "fight" or verb == "f":
                # --- Fight Logic ---
                print("Choose a program:")
                for i, prog in enumerate(player_active_daemon.programs):
                    print(f"  {i+1}: {prog.name} (Type: {prog.type}, Power: {prog.power})")

                program_choice = input("Program number: ")
                try:
                    choice_index = int(program_choice) - 1
                    if 0 <= choice_index < len(player_active_daemon.programs):
                        chosen_program = player_active_daemon.programs[choice_index]
                        print(f"{player_active_daemon.name} uses {chosen_program.name}!")
                        # TODO: Implement damage calculation (needs type chart)
                        damage = chosen_program.power // 2 # Very basic placeholder damage
                        enemy_daemon.take_damage(damage)
                        action_chosen = True
                    else:
                        print("Invalid program number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            elif verb == "switch" or verb == "s":
                 # --- Switch Logic ---
                 print("Choose a Daemon to switch to:")
                 healthy_daemons = player.get_healthy_daemons()
                 available_switches = [d for d in healthy_daemons if d != player_active_daemon]

                 if not available_switches:
                     print("No other healthy Daemons available to switch!")
                     continue # Ask for action again

                 for i, d in enumerate(available_switches):
                     print(f"  {i+1}: {d.name} (Lv.{d.level}) HP: {d.stats['hp']}/{d.stats['max_hp']}")

                 switch_choice = input("Switch to number (or 'cancel'): ")
                 if switch_choice.lower() == 'cancel':
                     continue

                 try:
                     choice_index = int(switch_choice) - 1
                     if 0 <= choice_index < len(available_switches):
                         player_active_daemon = available_switches[choice_index]
                         print(f"Come back! Go, {player_active_daemon.name}!")
                         action_chosen = True # Switching takes the turn
                     else:
                         print("Invalid switch number.")
                 except ValueError:
                     print("Invalid input. Please enter a number or 'cancel'.")


            elif verb == "run" or verb == "r":
                # --- Run Logic ---
                print("Attempting to jack out...")
                # Simple success for prototype against wild
                print("Successfully escaped!")
                combat_over = True
                action_chosen = True # Running counts as the action
                # No enemy turn if run is successful immediately

            else:
                print("Invalid combat command. Choose [F]ight, [S]witch, or [R]un.")

        # Check if combat ended due to running
        if combat_over:
            break

        # Check if enemy fainted after player's attack
        if enemy_daemon.is_fainted():
            print(f"Enemy {enemy_daemon.name} deactivated!")
            # Award XP
            player_active_daemon.add_xp(enemy_daemon.level * 10) # Simple XP formula
            combat_over = True
            break

        # Enemy Turn (Very Simple AI)
        print("-" * 34)
        if enemy_daemon.programs:
            enemy_program = random.choice(enemy_daemon.programs)
            print(f"Enemy {enemy_daemon.name} uses {enemy_program.name}!")
            # TODO: Implement damage calculation
            damage = enemy_program.power // 2 # Placeholder
            player_active_daemon.take_damage(damage)
        else:
            print(f"Enemy {enemy_daemon.name} doesn't know any programs!")

        # Check if player daemon fainted after enemy's attack
        if player_active_daemon.is_fainted():
            print(f"Your {player_active_daemon.name} deactivated!")
            healthy_daemons = player.get_healthy_daemons()
            if not healthy_daemons:
                print("All your Daemons have been deactivated!")
                print("You blacked out...")
                # TODO: Handle player loss (return to safe spot, etc.)
                # For prototype, just end combat
                combat_over = True
                # Potentially set a 'game_over' flag here
            else:
                # Force player to switch
                print("You must switch to another Daemon.")
                switched = False
                while not switched:
                    print("Choose a Daemon:")
                    for i, d in enumerate(healthy_daemons):
                        print(f"  {i+1}: {d.name} (Lv.{d.level}) HP: {d.stats['hp']}/{d.stats['max_hp']}")
                    switch_choice = input("Switch to number: ")
                    try:
                        choice_index = int(switch_choice) - 1
                        if 0 <= choice_index < len(healthy_daemons):
                            player_active_daemon = healthy_daemons[choice_index]
                            print(f"Go, {player_active_daemon.name}!")
                            switched = True
                        else:
                            print("Invalid switch number.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
        # End of turn checks done

    # Combat finished
    print("="*10 + " COMBAT END " + "="*12)
    # Return to roaming state happens in the main loop

# --- Main Game Function ---
def main():
    """Runs the main game loop."""
    print("Welcome to Cyberpunk NetRunner: Digital Hunters (Prototype)")
    player_name = input("Enter your NetRunner handle: ")

    # Initialize Player
    player = Player(player_name, "dark_alley", world_map)

    # Give Starter Daemon (Example: Virulet)
    starter_daemon = create_daemon("virulet", 5)
    if starter_daemon:
        player.add_daemon(starter_daemon)
    else:
        print("Error: Could not create starter daemon. Exiting.")
        return

    print(f"\nWelcome, {player.name}. You find yourself in a dark alley...")
    print("Type 'help' for a list of commands.")

    game_running = True
    game_state = "roaming" # Possible states: "roaming", "combat", "game_over"

    while game_running:
        current_location = player.get_current_location(world_map)
        if not current_location:
            print("Critical Error: Current location is invalid. Exiting.")
            break

        if game_state == "roaming":
            # Display current location at the start of each turn in roaming mode
            current_location.display()

            # Get player input
            command_input = input("> ").lower().strip()
            parts = command_input.split()
            if not parts:
                continue # Ask again if empty input
            verb = parts[0]
            args = parts[1:] # Arguments provided after the verb

            # Parse and execute command
            if verb == "quit":
                print("Exiting NetRunner...")
                game_running = False
            elif verb == "look" or verb == "l":
                # Already displayed by the start of the loop
                pass # Or maybe provide more detail on 'look'
            elif verb == "go":
                if args:
                    direction = args[0]
                    moved_successfully = player.move(direction, world_map)
                    if moved_successfully:
                        # Check for encounter after successful move
                        new_location = player.get_current_location(world_map)
                        if new_location.encounter_rate > 0 and random.random() < new_location.encounter_rate:
                            wild_info = new_location.get_random_wild_daemon_info()
                            if wild_info:
                                level = random.randint(wild_info['min_lvl'], wild_info['max_lvl'])
                                enemy_daemon = create_daemon(wild_info['id'], level)
                                if enemy_daemon:
                                    game_state = "combat"
                                    start_combat(player, enemy_daemon, world_map)
                                    # After combat, return to roaming
                                    game_state = "roaming"
                                    # Re-display location info after combat ends
                                    player.get_current_location(world_map).display()
                                else:
                                    print(f"Error creating wild daemon {wild_info['id']}")
                else:
                    print("Go where? (e.g., go north)")
            elif verb == "status" or verb == "stat":
                 player.display_status(world_map)
            elif verb == "daemons" or verb == "d":
                 player.display_detailed_daemons()
            elif verb == "help" or verb == "h":
                 display_help()
            elif verb == "scan":
                 print("Scanning the area...")
                 # Explicitly trigger encounter check based on current location
                 if current_location.encounter_rate > 0 and random.random() < (current_location.encounter_rate * 2.0): # Higher chance on scan?
                     wild_info = current_location.get_random_wild_daemon_info()
                     if wild_info:
                         level = random.randint(wild_info['min_lvl'], wild_info['max_lvl'])
                         enemy_daemon = create_daemon(wild_info['id'], level)
                         if enemy_daemon:
                             print("Scan detected a digital entity!")
                             game_state = "combat"
                             start_combat(player, enemy_daemon, world_map)
                             game_state = "roaming"
                             player.get_current_location(world_map).display()
                         else:
                             print(f"Error creating wild daemon {wild_info['id']}")
                     else:
                         print("...but found nothing.")
                 else:
                     print("...found nothing unusual.")

            # --- Placeholder for Combat/Other Actions ---
            # elif verb == "fight": # Combat is triggered by scan/random encounters now
            #     print("You need to encounter a Daemon first (try 'scan').")
            else:
                print(f"Unknown command: '{verb}'. Type 'help' for options.")

        elif game_state == "combat":
            # The combat loop is handled within start_combat function now
            # This state might be used for more complex transitions if needed later
            pass # Should transition back to roaming after combat

        elif game_state == "game_over":
            print("Game Over.") # Add more detail later
            game_running = False

    print("\nThanks for playing!")

# --- Run the Game ---
if __name__ == "__main__":
    main()
