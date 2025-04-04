Okay, great! Using `curses` will give you much finer control and a more polished retro feel. Let's outline how to structure your prototype using `curses`.

**1. Basic `curses` Setup (`game.py` or `main.py`)**

You'll need a main function wrapped by `curses.wrapper` to handle initialization and cleanup automatically.

```python
import curses
import time # For delays, etc.
from player import Player # Assuming player.py
from location import Location # Assuming location.py
from daemon import Daemon # Assuming daemon.py
# ... other necessary imports (random, json for data loading, etc.) ...

# --- Placeholder Data (Load from JSON later) ---
# (Same world_map dictionary and Daemon creation as before)
world_map = {
    "dark_alley": Location("dark_alley", "Dark Alley", "A grimy, narrow alley flickering under a broken neon sign.", {"north": "market_square"}, encounter_rate=0.2, wild_daemons=[{"id": "rat_bot", "min_lvl": 1, "max_lvl": 2}]), # Added encounter data
    "market_square": Location("market_square", "Market Square", "Bustling with data-hawkers and synth-food stalls.", {"south": "dark_alley", "east": "dataport_hub"}, encounter_rate=0.1, wild_daemons=[{"id": "glitch_sprite", "min_lvl": 2, "max_lvl": 3}]),
    "dataport_hub": Location("dataport_hub", "Dataport Hub", "Rows of public access dataports hum.", {"west": "market_square"}, encounter_rate=0.0) # Safe zone
}
# Assume function like load_daemons() exists to load base daemon data
LOADED_DAEMONS = {
    "rat_bot": {'name': 'Rat Bot', 'types': ['Shell'], 'base_stats': {'hp': 30, 'attack': 25, 'defense': 25, 'speed': 30}},
    "glitch_sprite": {'name': 'Glitch Sprite', 'types': ['Ghost'], 'base_stats': {'hp': 35, 'attack': 30, 'defense': 20, 'speed': 40}},
    "virulet": {'name': 'Virulet', 'types': ['Malware'], 'base_stats': {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60}}
}
# Need a factory function
def create_daemon(daemon_id, level):
    base_data = LOADED_DAEMONS[daemon_id]
    # Simplified creation for now, skipping programs
    return Daemon(base_data['name'], base_data['types'], base_data['base_stats'], level=level)

starter_virulet = create_daemon("virulet", 5)
player = Player("Runner", world_map["dark_alley"])
player.daemons.append(starter_virulet)

game_state = "roaming" # Possible states: roaming, combat, menu, message
message_log = [] # Store messages to display


# --- UI Functions (Could be in a separate ui.py) ---

def setup_colors():
    """Initializes color pairs used by the game."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Default
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # Accent / HP High
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning / HP Mid
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)   # Danger / HP Low
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Info / Location Names
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE) # Highlighted Menu Item

def draw_borders(stdscr, windows):
    """Draw borders around all defined windows."""
    stdscr.box() # Border around the whole screen
    for name, win_data in windows.items():
        win_data['win'].box()

def draw_map_window(win, current_location):
    """Draws the content of the map/location window."""
    win.erase() # Clear previous content
    win.box()
    h, w = win.getmaxyx()
    # Basic: Just show description and exits
    win.addstr(1, 2, current_location.name, curses.color_pair(5) | curses.A_BOLD)
    # Simple text wrapping
    desc_lines = []
    current_line = ""
    for word in current_location.description.split():
        if len(current_line) + len(word) + 1 < w - 4: # Check width limit
            current_line += word + " "
        else:
            desc_lines.append(current_line)
            current_line = word + " "
    desc_lines.append(current_line) # Add the last line

    for i, line in enumerate(desc_lines):
         if 1 + i + 1 < h - 2: # Check height limit
              win.addstr(1 + i + 1, 2, line.strip())

    exit_str = "Exits: " + ", ".join(current_location.exits.keys())
    if h > 4 + len(desc_lines): # Ensure space for exits line
        win.addstr(h - 2, 2, exit_str)

    # --- OPTIONAL: Simple ASCII Map ---
    # If location has an 'ascii_map' attribute (list of strings)
    # if hasattr(current_location, 'ascii_map') and current_location.ascii_map:
    #     map_h = len(current_location.ascii_map)
    #     map_w = len(current_location.ascii_map[0])
    #     start_y = (h // 2) - (map_h // 2)
    #     start_x = (w // 2) - (map_w // 2)
    #     for r, row_str in enumerate(current_location.ascii_map):
    #         if start_y + r < h -1:
    #            win.addstr(start_y + r, start_x, row_str[:w-start_x-1]) # Draw map, respecting window bounds


def draw_status_window(win, player_obj):
    """Draws player and daemon status."""
    win.erase()
    win.box()
    win.addstr(1, 2, f"Runner: {player_obj.name}", curses.color_pair(1))
    win.addstr(2, 2, f"Location: {player_obj.current_location.name}", curses.color_pair(5))

    win.addstr(4, 2, "Daemons:", curses.A_UNDERLINE)
    h, w = win.getmaxyx()
    for i, daemon in enumerate(player_obj.daemons):
        if 5 + i >= h - 1: break # Stop if no more space
        hp = daemon.stats['hp']
        max_hp = daemon.stats['max_hp']
        hp_perc = hp / max_hp
        hp_color = curses.color_pair(2) # Green default
        if hp_perc < 0.6: hp_color = curses.color_pair(3) # Yellow
        if hp_perc < 0.3: hp_color = curses.color_pair(4) # Red

        status_line = f"{i+1}: {daemon.name} L{daemon.level} "
        hp_bar_str = f"HP:{hp}/{max_hp}"
        # Check if enough space before adding HP bar
        if len(status_line) + len(hp_bar_str) < w - 3:
             status_line += hp_bar_str

        win.addstr(5 + i, 3, status_line, hp_color)


def draw_message_window(win, log):
    """Draws recent messages from the log."""
    win.erase()
    win.box()
    h, w = win.getmaxyx()
    win.addstr(0, 2, " Log ", curses.A_REVERSE) # Title in border
    # Display last few messages, newest at the bottom
    lines_available = h - 2
    start_index = max(0, len(log) - lines_available)
    for i, message in enumerate(log[start_index:]):
        win.addstr(1 + i, 2, message[:w-3]) # Truncate long messages


def add_message(log, message):
    """Adds a message to the log, keeping it a reasonable size."""
    log.append(message)
    if len(log) > 50: # Keep only last 50 messages
        del log[0]

# --- Main Game Function ---
def main_loop(stdscr):
    global game_state, message_log, player # Allow modification

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

    windows = {
        'map': {'win': curses.newwin(map_h, map_w, 0, 0)},
        'status': {'win': curses.newwin(stat_h, stat_w, 0, map_w)},
        'message': {'win': curses.newwin(msg_h, msg_w, map_h, 0)}
    }

    add_message(message_log, "Welcome to Cyberpunk NetRunner!")
    add_message(message_log, f"You are in {player.current_location.name}.")
    add_message(message_log, "Use Arrows or WASD to move, Q to quit.")

    # --- Main Loop ---
    while True:
        stdscr.clear() # Clear whole screen
        draw_borders(stdscr, windows) # Redraw borders

        # --- Draw based on Game State ---
        if game_state == "roaming":
            draw_map_window(windows['map']['win'], player.current_location)
            draw_status_window(windows['status']['win'], player)
            draw_message_window(windows['message']['win'], message_log)
        elif game_state == "combat":
            # --- TODO: Implement Combat Drawing ---
            # Need functions like: draw_combat_status(win, player_daemon, enemy_daemon)
            # draw_combat_options(win, current_selection)
            windows['map']['win'].erase()
            windows['map']['win'].box()
            windows['map']['win'].addstr(1, 2, "COMBAT ACTIVE", curses.color_pair(4) | curses.A_BOLD)
            # Draw combatants in status/map windows, options in message window? Layout needs design.
            draw_message_window(windows['message']['win'], message_log) # Show combat messages
        # Add other states like "menu", "dialogue" etc. if needed

        # Refresh individual windows efficiently
        for name, win_data in windows.items():
            win_data['win'].refresh()

        # Get Input
        key = stdscr.getch() # Blocking call

        # --- Process Input based on Game State ---
        if game_state == "roaming":
            moved = False
            direction = None
            if key == curses.KEY_UP or key == ord('w'): direction = "north"
            elif key == curses.KEY_DOWN or key == ord('s'): direction = "south"
            elif key == curses.KEY_LEFT or key == ord('a'): direction = "west"
            elif key == curses.KEY_RIGHT or key == ord('d'): direction = "east"
            elif key == ord('q'):
                break # Quit

            if direction:
                if direction in player.current_location.exits:
                    destination_id = player.current_location.exits[direction]
                    if destination_id in world_map:
                        player.current_location = world_map[destination_id]
                        add_message(message_log, f"Moved {direction} to {player.current_location.name}.")
                        moved = True
                    else:
                        add_message(message_log, f"Error: Destination {destination_id} not found.")
                else:
                    add_message(message_log, "You can't go that way.")

            # --- Check for Random Encounter AFTER successful move ---
            if moved:
                 loc = player.current_location
                 if hasattr(loc, 'encounter_rate') and loc.encounter_rate > 0 and random.random() < loc.encounter_rate:
                       if hasattr(loc, 'wild_daemons') and loc.wild_daemons:
                             # --- Trigger Combat ---
                             selected_enc = random.choice(loc.wild_daemons)
                             enemy_level = random.randint(selected_enc['min_lvl'], selected_enc['max_lvl'])
                             enemy_daemon = create_daemon(selected_enc['id'], enemy_level) # Use factory

                             add_message(message_log, f"ALERT! Wild {enemy_daemon.name} [Lv.{enemy_level}] appears!")
                             game_state = "combat"
                             # Need to store the enemy_daemon somewhere accessible by combat logic
                             # e.g., global current_enemy or pass to a combat handler function
                       else:
                             add_message(message_log, f"DEBUG: Encounter triggered but no wild_daemons defined for {loc.name}")


        elif game_state == "combat":
             # --- TODO: Process Combat Input ---
             # Map keys (F, S, R, C or 1, 2, 3, 4 for programs) to combat actions
             # Example:
             if key == ord('r'): # Try to run
                 add_message(message_log, "You attempt to escape...")
                 # Add run logic (for prototype, maybe always succeed vs wild)
                 add_message(message_log, "...and succeeded!")
                 game_state = "roaming" # Go back to roaming
             elif key == ord('q'): # Forfeit? Or handle differently in combat?
                  add_message(message_log, "Quitting combat...")
                  game_state = "roaming" # Or game over?
             else:
                 add_message(message_log, f"Combat action '{chr(key)}' not implemented yet.")


# --- Start the Game ---
curses.wrapper(main_loop)
print("Game Over. Terminal restored.") # Message after curses exits
```

**Explanation and Next Steps:**

1.  **`curses.wrapper(main_loop)`:** Handles all the setup and cleanup (restoring terminal state). Your main game logic goes inside `main_loop`.
2.  **Window Layout:** We defined three non-overlapping windows: `map` (top-left), `status` (top-right), `message` (bottom). Adjust sizes (`//`, `-`) as needed.
3.  **Drawing Functions:** Separate functions draw the content of each window. They take the `window` object and relevant game data (`player`, `location`, `message_log`) as input.
    *   `draw_map_window`: Shows location name, description (with basic wrapping), and exits. Includes commented-out code for adding a simple ASCII map if you define one in your `Location` objects.
    *   `draw_status_window`: Shows player name, location, and lists Daemons with colored HP status.
    *   `draw_message_window`: Shows the last few messages from `message_log`.
4.  **`add_message`:** A helper function to keep the message log tidy.
5.  **Main Loop:**
    *   Clears the `stdscr` (standard screen).
    *   Calls `draw_borders`.
    *   **Checks `game_state`:** Calls the appropriate drawing functions based on whether you're roaming or in combat (combat drawing is placeholder).
    *   **Refreshes Windows:** Crucially, `win.refresh()` is called on each sub-window. (For optimization on complex screens, look into `noutrefresh()` and `doupdate()`, but this is fine for now).
    *   **Gets Input:** `stdscr.getch()` waits for a single key press (Arrow keys, WASD, Q). `keypad(True)` is essential for arrow keys.
    *   **Processes Input:** The `if/elif` block handles input *based on the current `game_state`*. Roaming handles movement and quitting. Combat input is placeholder.
    *   **Encounter Check:** After a successful move, it checks the location's encounter rate and potentially switches `game_state` to `"combat"`.
6.  **Combat Implementation:**
    *   You need to design the combat screen layout (where enemy info, player info, action menu go).
    *   Create `draw_combat_...` functions.
    *   Implement the combat turn logic within the `if game_state == "combat":` input processing block. This will involve:
        *   Getting player action (fight, switch, run, capture).
        *   If fighting, selecting a program.
        *   Determining turn order.
        *   Executing actions, calculating damage, checking for faints.
        *   Adding combat results to `message_log`.
        *   Changing `game_state` back to `"roaming"` or `"game_over"` when combat ends.

This structure gives you a solid foundation for a `curses`-based TUI. Run this (after installing `windows-curses` if needed and putting placeholder classes in separate files), and you should see a basic layout where you can move between the defined locations and trigger encounter messages!