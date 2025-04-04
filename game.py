import curses
import time # For delays, etc.
import random
import sys

# Import classes from other files
from location import Location
from player import Player
from daemon import Daemon, Program, DATA_SIPHON, FIREWALL_BASH, ENCRYPT_SHIELD # Import example programs

# --- Game Data ---

# Define Base Daemon Stats (Could be loaded from JSON later)
# Ensure these IDs match the ones used in Location wild_daemons lists
DAEMON_BASE_STATS = {
    "virulet": {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60, 'types': ["Malware"]},
    "pyrowall": {'hp': 50, 'attack': 40, 'defense': 65, 'speed': 40, 'types': ["Shell", "Encryption"]},
    "aquabyte": {'hp': 45, 'attack': 50, 'defense': 50, 'speed': 50, 'types': ["Ghost", "Worm"]},
    "rat_bot": {'hp': 30, 'attack': 40, 'defense': 30, 'speed': 70, 'types': ["Physical"]},
    "glitch_sprite": {'hp': 35, 'attack': 60, 'defense': 35, 'speed': 55, 'types': ["Ghost", "Malware"]},
}

# Define Programs (Could be loaded from JSON later)
PROGRAMS = {
    "Data Siphon": DATA_SIPHON,
    "Firewall Bash": FIREWALL_BASH,
    "Encrypt Shield": ENCRYPT_SHIELD,
    "Scratch": Program("Scratch", "Physical", 30),
    "Static Shock": Program("Static Shock", "Worm", 40, effect="paralyze_chance"), # Placeholder effect
}

# Define World Map
world_map = {
    "dark_alley": Location(
        loc_id="dark_alley",
        name="Dark Alley",
        description="A grimy, narrow alley flickering under a broken neon sign advertising 'SynthNoodles'. The air smells of ozone and stale rain.",
        exits={"north": "market_square"},
        encounter_rate=0.2, # Added encounter data
        wild_daemons=[{"id": "rat_bot", "min_lvl": 1, "max_lvl": 2}]
    ),
    "market_square": Location(
        loc_id="market_square",
        name="Market Square",
        description="Bustling with data-hawkers shouting deals, and synth-food stalls emitting questionable steam. A public dataport hub is visible to the east.",
        exits={"south": "dark_alley", "east": "dataport_hub"},
        encounter_rate=0.1, # Lower encounter rate here
        wild_daemons=[{"id": "glitch_sprite", "min_lvl": 2, "max_lvl": 3}]
    ),
    "dataport_hub": Location(
        loc_id="dataport_hub",
        name="Dataport Hub",
        description="Rows of public access dataports hum with activity. Netrunners jack in and out, their faces illuminated by the glow of virtual interfaces.",
        exits={"west": "market_square"},
        encounter_rate=0.0 # Safe zone
    )
}

# --- Global Game Variables ---
# These might be better encapsulated in a GameManager class later
game_state = "roaming" # Possible states: roaming, combat, menu, message
message_log = [] # Store messages to display
player = None # Will be initialized in main_loop
current_enemy = None # Holds the enemy Daemon during combat

# --- Combat State Variables ---
# Moved outside handle_combat to persist across calls within the main loop's combat state
combat_options = ["Fight", "Switch", "Item", "Run"] # Add Item later
combat_current_selection = 0
combat_player_action = None
combat_enemy_action = None
combat_turn_phase = "player_choice" # player_choice, enemy_choice, resolution, end_check, force_switch
combat_player_active_daemon = None # Store the active daemon for the duration of combat

# --- Combat Logic ---
# Now processes a single step/input based on the current phase
def handle_combat_step(stdscr, windows, key):
    global game_state, message_log, player, current_enemy
    global combat_options, combat_current_selection, combat_player_action, combat_enemy_action, combat_turn_phase, combat_player_active_daemon

    # Ensure we have an active daemon at the start or if forced to switch
    if not combat_player_active_daemon or combat_turn_phase == "force_switch":
        combat_player_active_daemon = player.get_first_healthy_daemon()

    # Use the persisted combat_player_active_daemon
    player_active_daemon = combat_player_active_daemon
    if not player_active_daemon:
        add_message(message_log, "You have no active Daemons!")
        game_state = "roaming"
        return

    # --- Processing based on phase --- (Logic remains, but references need update)
    if combat_turn_phase == "player_choice": # Use global variable
        if key == curses.KEY_UP:
            combat_current_selection = (combat_current_selection - 1) % len(combat_options) # Use global
        elif key == curses.KEY_DOWN:
            combat_current_selection = (combat_current_selection + 1) % len(combat_options) # Use global
        elif key == curses.KEY_ENTER or key == ord('\n') or key == ord(' '):
            chosen_action = combat_options[combat_current_selection] # Use global
            add_message(message_log, f"Player chose: {chosen_action}")

            if chosen_action == "Fight":
                # TODO: Implement program selection sub-menu
                add_message(message_log, "Fight selected (Program choice TODO)")
                if player_active_daemon.programs:
                    combat_player_action = player_active_daemon.programs[0] # Use global
                    combat_turn_phase = "enemy_choice" # Use global
                else:
                    add_message(message_log, f"{player_active_daemon.name} has no programs!")
                    combat_player_action = None # Use global
                    combat_turn_phase = "enemy_choice" # Use global

            elif chosen_action == "Switch":
                # TODO: Implement Daemon selection sub-menu
                add_message(message_log, "Switch selected (Daemon choice TODO)")
                if len(player.get_healthy_daemons()) > 1:
                     add_message(message_log, "Switching...")
                     # combat_player_active_daemon = ... # Update active daemon - TODO
                     combat_player_action = "switch" # Use global
                     combat_turn_phase = "enemy_choice" # Use global
                else:
                     add_message(message_log, "No other Daemons to switch to!")
                     # Stay in player_choice phase

            elif chosen_action == "Item":
                add_message(message_log, "Item selected (Not implemented)")
                # Stay in player_choice phase

            elif chosen_action == "Run":
                add_message(message_log, "Attempting to run...")
                add_message(message_log, "Successfully escaped!")
                game_state = "roaming" # Exit combat loop
                combat_player_active_daemon = None # Reset active daemon on leaving combat

        elif key == ord('q'): # Allow quitting combat?
             add_message(message_log, "Quitting combat...")
             game_state = "roaming"
             combat_player_active_daemon = None # Reset

    elif combat_turn_phase == "enemy_choice": # Use global
        if current_enemy and current_enemy.programs:
            combat_enemy_action = random.choice(current_enemy.programs) # Use global
            add_message(message_log, f"Enemy {current_enemy.name} prepares {combat_enemy_action.name}!")
        else:
            combat_enemy_action = None # Use global
            add_message(message_log, f"Enemy {current_enemy.name} does nothing.")
        combat_turn_phase = "resolution" # Use global

    elif combat_turn_phase == "resolution": # Use global
        add_message(message_log, "--- Turn Resolution ---")
        player_first = player_active_daemon.stats['speed'] >= current_enemy.stats['speed']

        actors = [(player_active_daemon, combat_player_action, current_enemy), (current_enemy, combat_enemy_action, player_active_daemon)] # Use global actions
        if not player_first:
            actors.reverse()

        for attacker, action, defender in actors:
            if action == "switch":
                add_message(message_log, f"{attacker.name} was switched out.")
                continue
            elif isinstance(action, Program):
                add_message(message_log, f"{attacker.name} uses {action.name}!")
                damage = (action.power * attacker.stats['attack'] // defender.stats['defense']) // 2 + random.randint(0, action.power // 10)
                damage = max(1, damage)
                defender.take_damage(damage)
                add_message(message_log, f"{defender.name} took {damage} damage! (HP: {defender.stats['hp']}/{defender.stats['max_hp']})")
            elif action is None:
                add_message(message_log, f"{attacker.name} did nothing.")

            if defender.is_fainted():
                add_message(message_log, f"{defender.name} deactivated!")
                combat_turn_phase = "end_check" # Use global
                break

        if combat_turn_phase == "resolution": # Check if phase wasn't changed by fainting
             combat_turn_phase = "end_check" # Use global

    elif combat_turn_phase == "end_check": # Use global
        if current_enemy.is_fainted():
            xp_gain = current_enemy.level * 15
            add_message(message_log, f"{player_active_daemon.name} gained {xp_gain} XP!")
            leveled_up = player_active_daemon.add_xp(xp_gain)
            if leveled_up:
                add_message(message_log, f"{player_active_daemon.name} grew to Level {player_active_daemon.level}!")

            add_message(message_log, "You won the battle!")
            game_state = "roaming"
            current_enemy = None
            combat_player_active_daemon = None # Reset active daemon

        elif player_active_daemon.is_fainted():
            add_message(message_log, f"Your {player_active_daemon.name} deactivated!")
            if not player.get_healthy_daemons():
                add_message(message_log, "All your Daemons are down! You blacked out...")
                game_state = "game_over"
                combat_player_active_daemon = None # Reset
            else:
                add_message(message_log, "You need to switch Daemon!")
                # TODO: Force switch sub-menu
                combat_turn_phase = "force_switch" # Use global - Need to handle this phase
                # For now, just go back to player choice - requires player input again
                # combat_turn_phase = "player_choice" # This might be better handled by a dedicated switch menu state

        else:
            # If no one fainted, start next turn
            combat_turn_phase = "player_choice" # Use global
            add_message(message_log, "--- Next Turn ---")

# --- Main Game Function ---
def main_loop(stdscr):
    global game_state, message_log, player, current_enemy # Allow modification
    global combat_options, combat_current_selection, combat_player_action, combat_enemy_action, combat_turn_phase, combat_player_active_daemon # Add combat state globals

    # Setup curses
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(False) # Make getch blocking initially
    stdscr.keypad(True) # Enable reading arrow keys, etc.
    setup_colors()

    # Define windows layout
    height, width = stdscr.getmaxyx()
    map_h, map_w = height // 2, width // 2
    stat_h, stat_w = height // 2, width - map_w
    msg_h, msg_w = height - map_h, width

    # Ensure minimum size
    if height < 10 or width < 30:
        print("Terminal too small. Please resize.")
        return

    windows = {
        'map': {'win': curses.newwin(map_h, map_w, 0, 0)},
        'status': {'win': curses.newwin(stat_h, stat_w, 0, map_w)},
        'message': {'win': curses.newwin(msg_h, msg_w, map_h, 0)}
    }

    # Initialize Player
    player = Player("Runner", "dark_alley", world_map) # Pass world_map here
    starter_daemon = create_daemon("virulet", 5)
    if starter_daemon:
        player.add_daemon(starter_daemon) # Use player's method
        add_message(message_log, f"{starter_daemon.name} added to your roster.") # Add message here
    else:
        # Need to handle this error gracefully in curses
        stdscr.addstr(0, 0, "Error creating starter daemon. Press any key to exit.")
        stdscr.getch()
        return

    add_message(message_log, "Welcome to Cyberpunk NetRunner!")
    add_message(message_log, f"You are in {player.get_current_location(world_map).name}.") # Use getter
    add_message(message_log, "Use Arrows or WASD to move, Q to quit.")

    # --- Main Loop ---
    while True:
        # Get current location (needed for drawing and logic)
        current_location = player.get_current_location(world_map)
        if not current_location:
            add_message(message_log, "Error: Player location invalid!")
            break # Exit if location is broken

        # --- Drawing ---
        stdscr.clear() # Clear whole screen
        draw_borders(stdscr, windows) # Redraw borders

        key = -1 # Default key value if not read

        # Draw based on Game State
        if game_state == "roaming":
            draw_map_window(windows['map']['win'], current_location)
            draw_status_window(windows['status']['win'], player)
            draw_message_window(windows['message']['win'], message_log)
        elif game_state == "combat":
            # Draw combat specific layout
            draw_combat_layout(windows, combat_player_active_daemon, current_enemy)
            draw_message_window(windows['message']['win'], message_log) # Show combat log
            # Draw options only if it's player's turn to choose
            if combat_turn_phase == "player_choice":
                 draw_combat_options(windows['message']['win'], combat_options, combat_current_selection)
            # No separate call to handle_combat for drawing

        elif game_state == "game_over":
             # Simple game over screen
             stdscr.clear()
             h, w = stdscr.getmaxyx()
             msg = "GAME OVER"
             stdscr.addstr(h // 2, (w - len(msg)) // 2, msg, curses.color_pair(4) | curses.A_BOLD)
             stdscr.addstr(h // 2 + 1, (w - len("Press Q to exit")) // 2, "Press Q to exit")
             stdscr.refresh() # Use refresh here as it's a final screen
             while True: # Wait for Q
                 q_key = stdscr.getch()
                 if q_key == ord('q'):
                     return # Exit main_loop

        # Refresh screen after drawing all components for the current state
        for name, win_data in windows.items():
             try:
                 win_data['win'].noutrefresh() # Mark for update
             except curses.error:
                 pass # Ignore refresh errors if window is too small
        curses.doupdate() # Update physical screen

        # --- Input & State Update ---
        # Get Input
        # Make getch non-blocking during automated phases (enemy turn, resolution)
        if combat_turn_phase in ["enemy_choice", "resolution", "end_check"]:
             stdscr.nodelay(True) # Don't wait for input
             key = stdscr.getch() # Check if key was pressed during auto phase (e.g., skip delay)
             stdscr.nodelay(False) # Go back to blocking
             if key == -1: # If no key pressed, add delay for automated phases
                 time.sleep(0.5) # Small delay to make auto turns visible
         else: # Player choice phases (roaming, combat player_choice, game_over handled above)
             key = stdscr.getch() # Blocking call

        # Process based on Game State
        if game_state == "roaming":
            # Process Roaming Input
            moved = False
            direction = None
            if key == curses.KEY_UP or key == ord('w'): direction = "north"
            elif key == curses.KEY_DOWN or key == ord('s'): direction = "south"
            elif key == curses.KEY_LEFT or key == ord('a'): direction = "west"
            elif key == curses.KEY_RIGHT or key == ord('d'): direction = "east"
            elif key == ord('q'):
                break # Quit

            if direction:
                moved = player.move(direction, world_map) # Use player's move method
                if moved:
                    add_message(message_log, f"Moved {direction} to {player.get_current_location(world_map).name}.")
                    # --- Check for Random Encounter AFTER successful move ---
                    loc = player.get_current_location(world_map)
                    if loc.encounter_rate > 0 and random.random() < loc.encounter_rate:
                           if loc.wild_daemons:
                                 # --- Trigger Combat ---
                                 selected_enc = random.choice(loc.wild_daemons)
                                 enemy_level = random.randint(selected_enc['min_lvl'], selected_enc['max_lvl'])
                                 enemy_daemon = create_daemon(selected_enc['id'], enemy_level)

                                 if enemy_daemon:
                                     add_message(message_log, f"ALERT! Wild {enemy_daemon.name} [Lv.{enemy_level}] appears!")
                                     current_enemy = enemy_daemon # Store enemy globally for combat
                                     game_state = "combat"
                                     combat_turn_phase = "player_choice" # Reset combat phase
                                     combat_current_selection = 0 # Reset selection
                                     combat_player_active_daemon = None # Ensure it gets set at start of handle_combat_step
                                     message_log.clear() # Clear log for combat
                                     add_message(message_log, f"Combat started with {current_enemy.name}!")
                                 else:
                                     add_message(message_log, f"DEBUG: Failed to create daemon {selected_enc['id']}")
                           # else: # No wild daemons defined here
                           #    add_message(message_log, f"DEBUG: Encounter triggered but no wild_daemons defined for {loc.name}")
                elif not moved and direction in current_location.exits:
                     add_message(message_log, f"Error: Map inconsistency for exit '{direction}'.")
                elif not moved:
                     add_message(message_log, "You can't go that way.")

            # Add other roaming commands here (scan, status, etc.)
            elif key == ord('h'): # Example help
                 add_message(message_log, "Help: Use Arrows/WASD to move, Q to quit.")

        elif game_state == "combat":
             # Process Combat Input / Step
             handle_combat_step(stdscr, windows, key) # Pass key to the step function

# --- Start the Game ---
try:
    curses.wrapper(main_loop)
    print("Game exited normally. Terminal restored.")
except Exception as e:
    # Ensure terminal is restored even if there's an error
    curses.endwin()
    print("\nAn error occurred:")
    print(e)
    import traceback
    traceback.print_exc()
finally:
    # Just in case wrapper didn't finish
    try:
        curses.endwin()
    except:
        pass
