Okay, this is a fantastic and detailed concept! "Cyberpunk NetRunner: Digital Hunters" has a great ring to it, and the cyberpunk adaptation of the Pokémon formula is rich with potential.

Let's consolidate this into a design document, incorporating the technical and UX decisions as requested.

---

**Game Design Document: Cyberpunk NetRunner: Digital Hunters**

**1. Core Concept & Genre**

*   **Game Title:** Cyberpunk NetRunner: Digital Hunters
*   **Genre:** Cyberpunk Pet Battler / Monster Collector RPG (inspired by Pokémon Red/Blue)
*   **Theme:** Dystopian Cyberpunk Sci-Fi. Players navigate both the physical city and the digital "Grid".
*   **Core Objective:** Become a skilled netrunner by capturing, training, and evolving digital entities ("Daemons"). Defeat 8 "Corporate Servers", disrupt the antagonist group "DataSec", challenge the "Firewall Four", complete the "DigEntDex", and uncover secrets within the Grid.
*   **Primary Interaction:** **Text-based commands** entered via the keyboard (e.g., `go north`, `scan area`, `use <program> on <target daemon>`, `capture <target daemon>`).
    *   *(Rationale for Text Input):* While WSAD/Arrows/Mouse were initially suggested, implementing that smoothly requires libraries beyond pure standard Python (like `curses` or graphical libraries like Pygame). For a pure Python console approach, text commands are the most feasible and robust starting point. `curses` could be a *potential future enhancement* for more direct key input if desired.

**2. Core Gameplay Mechanics**

*   **Movement:**
    *   Players navigate a map represented by interconnected locations (nodes/rooms).
    *   Movement between locations is handled via text commands (e.g., `go west`, `enter datastream`, `jack out`).
    *   The game will describe the current location and available exits/actions.
    *   Minimalistic retro aesthetic achieved through descriptive text and potentially simple ASCII representations if desired later.
*   **Digital Entities ("Daemons"):**
    *   Players collect and command Daemons.
    *   **Types:** Daemons have code types (Encryption, Malware, Shell, Ghost, Worm, Neural, Physical, etc.) with rock-paper-scissors style advantages/disadvantages.
    *   **Stats:** Each Daemon has `HP` (Health Points), `Attack` (or similar stat for program power), `Defense`, `Speed` (determines turn order), and a list of learned `Programs` (moves/skills).
    *   **Evolution:** Daemons evolve ("Code Optimization") upon reaching certain levels or meeting specific conditions (like trading, potentially).
    *   **Capture:** Weaken wild Daemons in combat and use a "Capture Routine" command. Success rate depends on the target's remaining HP and potentially other factors.
*   **Combat:**
    *   **Trigger:** Random encounters while navigating specific Grid areas or scripted battles with rival netrunners/corporate security.
    *   **System:** Turn-based.
    *   **Flow:**
        1.  Encounter starts, combat interface described via text.
        2.  Player chooses an action: `use <program>`, `switch <daemon>`, `item` (future), `run`.
        3.  Enemy AI chooses an action.
        4.  Actions resolve based on Daemon `Speed` stat.
        5.  Damage/effects calculated based on Attacker's `Attack`, Defender's `Defense`, Program power, and Type matchups.
        6.  Results are described textually ("Virulet uses Data Siphon! It's super effective! Enemy Daemon takes X damage.").
        7.  Repeat until one side's active Daemon is defeated (HP <= 0) or the player runs away.
        8.  Defeating Daemons grants Experience Points (XP). Reaching XP thresholds results in level-ups, increasing stats and potentially learning new Programs.
*   **Player Attributes:** The player character doesn't have direct combat stats, but manages their roster of Daemons, their location, inventory (future), and potentially currency ("Creds"?).
*   **Items:** Not included in the initial version to maintain focus, but planned for future expansion (e.g., healing items ("Repair Kits"?), capture devices ("Shackles"?), temporary stat boosters ("Overclock Chips"?)).

**3. World Building & Content**

*   **World Structure:** A network of distinct locations described via text. Key areas include: The Darknet Slums, various Corporate City sectors, Corporate Servers (data fortresses), Grid pathways, hidden nodes, Zion Corp HQ.
*   **Key Elements:**
    *   **Player:** Novice netrunner starting in the slums.
    *   **Starters:** Virulet (Infiltration), Pyrowall (Defense), Aquabyte (Data Extraction).
    *   **Device:** "NetDeck" (interface for interacting with the Grid and Daemons).
    *   **Goal Structures:** 8 Corporate Servers, Firewall Four, Zion Corp.
    *   **Antagonists:** DataSec group, rival netrunners, corporate security Daemons.
    *   **Collection:** DigEntDex (aiming for a smaller, manageable subset of the 151 for the initial version, e.g., 15-30 Daemons to establish the system).
*   **Narrative:** Begin by receiving the NetDeck and a starter Daemon from a mentor. Follow the progression path: explore, battle rivals, challenge Servers, uncover DataSec's plot, confront the Firewall Four. Hints of the mythical "Neuromancer" can be included.
*   **Atmosphere:** Text descriptions focusing on cyberpunk tropes: neon lights, rain-slicked streets, corporate logos, digital static, data streams, jargon ("ICE", "Subroutines", "Backdoors"), contrast between high-tech Grid and grimy physical world.

**4. Technical Design (Python Focus)**

*   **Interface:** Standard Python `print()` for output and `input()` for commands. No external libraries initially.
*   **Game State Representation:** Use **Object-Oriented Programming (OOP)**.
    *   Define classes: `Player`, `Daemon`, `Program`, `Location`, `GameManager`, etc.
    *   `Player` class stores: current location object, list of owned `Daemon` objects, inventory (dict/list, future), etc.
    *   `Daemon` class stores: name, type(s), stats (HP, max HP, attack, defense, speed), list of learned `Program` objects, current XP, level.
    *   `Location` class stores: name, description, dictionary of exits (e.g., `{"north": "location_id_north", "server_entrance": "server_id_1"}`), list of possible wild Daemons, NPCs/events.
    *   Game World: A dictionary mapping unique location IDs to their `Location` objects.
*   **Input Parsing:**
    *   Read the full line using `input()`.
    *   Convert to lowercase and split into words (e.g., `command = input("> ").lower().split()`).
    *   Use `if/elif/else` structure or a dictionary mapping command verbs (e.g., `command[0]`) to functions that handle the action.
    *   Start with simple `verb noun` or `verb target` structures (e.g., `go north`, `use datasiphon`). Handle basic error messages for invalid commands.
*   **Game Loop:**
    *   Main loop: `while game_running:`
        1.  Display current location description and prompt.
        2.  `get_player_input()`
        3.  `parse_and_process_input(input)` - This function determines the action and calls appropriate methods (move player, initiate combat, show status, etc.).
        4.  `update_game_state()` (if necessary, e.g., random events - maybe later).
    *   Combat loop (nested within process_input if combat starts): Handles turn order, action selection, resolution, and checking win/loss conditions for the battle.
*   **Data Persistence (Save/Load):**
    *   Use the **`json`** module.
    *   Create functions `save_game(player_data, world_state, filename)` and `load_game(filename)`.
    *   When saving, convert relevant object data (player stats, location, owned Daemons with their stats/programs, potentially key world flags) into dictionaries and lists compatible with JSON.
    *   When loading, parse the JSON file back into dictionaries/lists and use them to reconstruct the game state (re-instantiate Player, Daemons, set current location, etc.). Save files could be named based on player name or slots.

**5. Refinement & User Experience**

*   **Feedback:** Provide clear, concise text feedback for every player action and game event (movement confirmation, combat results, capture success/failure, errors). Implement a `status` or `check` command to view player info and detailed Daemon stats.
*   **Help/Guidance:** Implement a `help` command listing available actions. Contextual prompts (e.g., listing programs when `use` is typed alone in combat). A brief introductory sequence explaining the basic premise and commands.
*   **Difficulty/Balancing:** Start with simple, predictable mechanics. Define base stats for Daemons, a clear type-advantage chart (e.g., x2 damage for super effective, x0.5 for not very effective), and a basic XP curve for leveling. Balancing will require significant playtesting later; initial focus is functionality.
*   **Start & End:** Game starts with an introduction setting the scene in the Darknet Slums. A clear win condition message upon defeating the final boss (Firewall Four / Zion Corp Champion). A loss condition might occur if the player runs out of usable Daemons during a critical story battle or perhaps in specific high-stakes situations (though simple "fainting" and returning to a safe spot like Pokémon is more player-friendly).

Okay, let's outline these core components with the goal of creating a functional, basic prototype. We'll keep things simple to start.

**a) Basic `Daemon` Class Structure**

We'll focus on the essential attributes and a couple of key methods needed for basic display and combat checks.

```python
import random # Might need later for combat calculations, etc.

class Program:
    """Represents a single program/ability a Daemon can use."""
    def __init__(self, name, p_type, power, effect=None):
        self.name = name
        self.type = p_type # e.g., "Malware", "Encryption"
        self.power = power # Base damage/effect strength
        self.effect = effect # Optional: e.g., status change like "reduce_defense"

# --- Example Basic Programs ---
data_siphon = Program("Data Siphon", "Malware", 40)
firewall_bash = Program("Firewall Bash", "Shell", 35)
encrypt_shield = Program("Encrypt Shield", "Encryption", 0, effect="raise_defense") # Example effect


class Daemon:
    """Represents a Digital Entity (CyberPet)."""

    def __init__(self, name, types, base_stats, level=1, programs=None):
        """
        Initializes a new Daemon.
        Args:
            name (str): The Daemon's name.
            types (list[str]): List of type strings (e.g., ["Malware", "Ghost"]).
            base_stats (dict): Dictionary of base stats like
                               {'hp': 45, 'attack': 49, 'defense': 49, 'speed': 45}.
            level (int): Starting level.
            programs (list[Program]): List of starting programs.
        """
        self.name = name
        self.types = types
        self.level = level
        self.xp = 0
        self.xp_next_level = self._calculate_xp_needed(level) # Needs helper function

        # Calculate current stats based on base and level (simplified for prototype)
        # In a full game, this would be more complex (IVs, EVs, complex formula)
        self.stats = {
            'max_hp': base_stats['hp'] + (level * 2), # Very simple scaling
            'hp': base_stats['hp'] + (level * 2), # Start at full health
            'attack': base_stats['attack'] + level,
            'defense': base_stats['defense'] + level,
            'speed': base_stats['speed'] + level,
        }

        self.programs = programs if programs else []
        self.status_effect = None # e.g., "PARALYZED", None

    def _calculate_xp_needed(self, level):
        """Calculates XP needed for the next level (simple example)."""
        # Could use a standard formula like medium-fast from Pokémon, or simpler:
        return int(10 * (level ** 1.5)) # Example simple curve

    def is_fainted(self):
        """Checks if the Daemon has 0 or less HP."""
        return self.stats['hp'] <= 0

    def take_damage(self, amount):
        """Applies damage to the Daemon's HP."""
        self.stats['hp'] -= amount
        if self.stats['hp'] < 0:
            self.stats['hp'] = 0
        print(f"{self.name} took {amount} damage! Remaining HP: {self.stats['hp']}/{self.stats['max_hp']}")

    def display_summary(self):
        """Prints a basic summary of the Daemon."""
        print(f"--- {self.name} (Lv.{self.level}) ---")
        print(f"  Type(s): {', '.join(self.types)}")
        print(f"  HP: {self.stats['hp']}/{self.stats['max_hp']}")
        print(f"  Stats: Atk={self.stats['attack']}, Def={self.stats['defense']}, Spd={self.stats['speed']}")
        print(f"  XP: {self.xp}/{self.xp_next_level}")
        program_names = [p.name for p in self.programs]
        print(f"  Programs: {', '.join(program_names) if program_names else 'None'}")
        if self.status_effect:
            print(f"  Status: {self.status_effect}")
        print("-" * (len(self.name) + 12))

    def add_xp(self, amount):
        """Adds XP and checks for level up."""
        if self.is_fainted(): # Can't gain XP if fainted
             return
        self.xp += amount
        print(f"{self.name} gained {amount} XP!")
        while self.xp >= self.xp_next_level:
             self.level_up()

    def level_up(self):
        """Handles the level-up process."""
        self.level += 1
        # Remove XP needed for the level just gained
        self.xp -= self.xp_next_level
        self.xp_next_level = self._calculate_xp_needed(self.level)
        print(f"{self.name} grew to Level {self.level}!")

        # Improve stats (simple example)
        self.stats['max_hp'] += 2
        self.stats['hp'] = self.stats['max_hp'] # Full heal on level up (like Pokémon)
        self.stats['attack'] += 1
        self.stats['defense'] += 1
        self.stats['speed'] += 1
        self.display_summary() # Show new stats

        # Add logic here later to check for learning new programs at certain levels


# --- Example Daemon Creation ---
# Base stats definition
virulet_base = {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60}
# Create an instance
starter_virulet = Daemon("Virulet", ["Malware"], virulet_base, level=5, programs=[data_siphon])

# starter_virulet.display_summary()
# starter_virulet.take_damage(15)
# starter_virulet.add_xp(100) # Example XP gain
```

**b) Main Game Loop Structure**

This focuses on turn-based interaction: show state, get input, process input.

```python
# Assume Player and Location classes exist, and world_map dictionary is populated
# from location import Location # Assuming location.py holds Location class
# from player import Player     # Assuming player.py holds Player class
# from daemon import Daemon, Program # Assuming daemon.py holds Daemon/Program

# --- Placeholder Classes/Data (Replace with actual imports) ---
class Location:
    def __init__(self, loc_id, name, description, exits):
        self.id = loc_id
        self.name = name
        self.description = description
        self.exits = exits # {"north": "street_1", "shop_door": "shop_interior"}

    def display(self):
        print(f"\n=== {self.name} ===")
        print(self.description)
        exit_list = ", ".join(self.exits.keys())
        print(f"Exits: {exit_list if exit_list else 'None'}")

class Player:
    def __init__(self, name, start_location):
        self.name = name
        self.current_location = start_location # This should be a Location object
        self.daemons = [] # List of Daemon objects

    def move(self, direction, world_map):
        current_exits = self.current_location.exits
        if direction in current_exits:
            destination_id = current_exits[direction]
            if destination_id in world_map:
                self.current_location = world_map[destination_id]
                return True
            else:
                print(f"Error: Location ID '{destination_id}' not found in world map.")
                return False
        else:
            print("You can't go that way.")
            return False

    def display_status(self):
         print("\n--- Player Status ---")
         print(f"Name: {self.name}")
         print(f"Current Location: {self.current_location.name}")
         print("Daemons:")
         if not self.daemons:
              print("  None")
         else:
              for i, daemon in enumerate(self.daemons):
                   print(f"  {i+1}: {daemon.name} (Lv.{daemon.level}) - HP: {daemon.stats['hp']}/{daemon.stats['max_hp']}")


# --- World Map Setup (Example) ---
world_map = {
    "dark_alley": Location("dark_alley", "Dark Alley", "A grimy, narrow alley flickering under a broken neon sign.", {"north": "market_square"}),
    "market_square": Location("market_square", "Market Square", "A bustling square filled with data-hawkers and synth-food stalls.", {"south": "dark_alley", "east": "dataport_hub"}),
    "dataport_hub": Location("dataport_hub", "Dataport Hub", "Rows of public access dataports hum with activity.", {"west": "market_square"})
}

# --- Game Initialization ---
player = Player("Runner", world_map["dark_alley"]) # Start player in the alley
player.daemons.append(starter_virulet) # Give player the starter Daemon

# --- Main Game Loop ---
game_running = True
while game_running:
    # 1. Display current state
    player.current_location.display()

    # 2. Get player input
    command_input = input("> ").lower().strip()
    parts = command_input.split()
    if not parts:
        continue # Ask again if empty input
    verb = parts[0]
    args = parts[1:] # Arguments provided after the verb

    # 3. Parse and execute command
    if verb == "quit":
        print("Exiting NetRunner...")
        game_running = False
    elif verb == "look" or verb == "l":
        # Already displayed by the start of the loop
        pass # Or maybe provide more detail on 'look'
    elif verb == "go":
        if args:
            direction = args[0]
            player.move(direction, world_map)
        else:
            print("Go where? (e.g., go north)")
    elif verb == "status" or verb == "stat":
         player.display_status()
    elif verb == "daemons" or verb == "d":
         if not player.daemons:
              print("You have no Daemons.")
         else:
              print("\nYour Daemons:")
              for daemon in player.daemons:
                   daemon.display_summary() # Use the detailed display
    elif verb == "help" or verb == "h":
         print("\nAvailable commands:")
         print("  go [direction] - Move to a new location (e.g., go north)")
         print("  look / l       - See the description of your current location")
         print("  status / stat  - Show your player status and daemon list summary")
         print("  daemons / d    - Show detailed status of all your Daemons")
         # Add more commands as they are implemented (scan, capture, use, fight...)
         print("  help / h       - Show this help message")
         print("  quit           - Exit the game")
    # --- Placeholder for Combat/Other Actions ---
    # elif verb == "scan":
    #     print("Scanning area... (Not implemented yet)")
    # elif verb == "fight":
    #     print("Initiating combat... (Not implemented yet)")
    else:
        print(f"Unknown command: '{verb}'. Type 'help' for options.")

```

**c) Handling the World Map (Connecting Locations)**

This is already demonstrated within the code for Part (b), but let's explicitly summarize the approach:

1.  **`Location` Class:** Each distinct area is an instance of the `Location` class. Crucially, it contains an `id` (unique string identifier) and an `exits` dictionary.
2.  **`exits` Dictionary:** This dictionary within each `Location` object maps a command word (like `"north"`, `"enter"`, `"west"`) to the *unique `id` string* of the `Location` object you arrive at when using that exit.
    *   Example: `Location("A", ..., exits={"east": "B", "up": "C"})` means going `east` from location A leads to the location with ID `"B"`, and going `up` leads to the location with ID `"C"`.
3.  **`world_map` Dictionary:** A global (or accessible within the game manager) dictionary holds all the created `Location` objects. The *keys* of this dictionary are the unique `Location` `id` strings, and the *values* are the corresponding `Location` objects themselves.
    *   Example: `world_map = {"A": location_a_object, "B": location_b_object, "C": location_c_object}`
4.  **Movement Logic (`Player.move`):**
    *   When the player types `go <direction>`:
    *   Look at the `exits` dictionary of the `player.current_location`.
    *   If `<direction>` is a valid key in `exits`, get the `destination_id` string (the value associated with that key).
    *   Use this `destination_id` string to look up the actual `Location` object in the main `world_map` dictionary.
    *   Update the `player.current_location` to this newly retrieved `Location` object.

**Putting it Together for a Prototype:**

*   Create separate files (e.g., `daemon.py`, `location.py`, `player.py`, `game.py`).
*   Put the class definitions in their respective files.
*   In `game.py`, import the necessary classes.
*   Define your initial `world_map` locations in `game.py`.
*   Create the `player` object in `game.py`.
*   Run the main game loop from `game.py`.

Okay, let's outline how to approach implementing these next crucial steps for your "Cyberpunk NetRunner" prototype:

**1. Implementing Random Encounters**

*   **Goal:** Trigger battles with wild Daemons based on player movement in certain areas.
*   **Steps:**
    1.  **Enhance `Location` Class:**
        *   Add attributes:
            *   `encounter_rate` (float): Probability (0.0 to 1.0) of an encounter occurring upon entering this location. Set to 0 for safe zones.
            *   `wild_daemons` (list of dicts): Define potential encounters. Each dict could specify a Daemon type ID and a level range.
                *   Example: `wild_daemons = [{"id": "rat_bot", "min_lvl": 2, "max_lvl": 4}, {"id": "glitch_sprite", "min_lvl": 3, "max_lvl": 5}]`
    2.  **Modify Player Movement (`Player.move` or main loop):**
        *   After a successful move (`player.move` returns `True` and the player is in the new location):
        *   Check the `encounter_rate` of the `player.current_location`.
        *   Generate a random float: `roll = random.random()`.
        *   If `roll < player.current_location.encounter_rate`:
            *   Trigger an encounter!
    3.  **Trigger Encounter Logic:**
        *   If an encounter is triggered:
            *   Select a Daemon entry randomly from `player.current_location.wild_daemons`.
            *   Determine the level randomly within the `min_lvl` and `max_lvl` range.
            *   Use a "factory" function/method (see Expansion below) to create an instance of the wild `Daemon` with the chosen ID and level.
            *   Print an encounter message (e.g., "A wild Glitch Sprite [Lv.4] flickers into view!").
            *   **Crucially:** Change the game state. Introduce a variable like `game_state` (e.g., in your main game manager or global scope) and set it to `"combat"`. This tells the main loop to switch from handling movement commands to handling combat commands.
            *   Initiate the combat loop (see next section).

**2. Implementing the Combat Loop**

*   **Goal:** Create the turn-based battle system.
*   **Steps:**
    1.  **Combat State Management:**
        *   Use the `game_state` variable mentioned above. The main game loop will now look something like:
            ```python
            game_state = "roaming"
            # ... other init ...
            while game_running:
                if game_state == "roaming":
                    # Handle movement, looking, status, etc.
                    # Check for encounters after successful move, potentially changing game_state to "combat"
                elif game_state == "combat":
                    # Run the combat turn logic
                    # Combat logic will eventually change game_state back to "roaming" or "game_over"
                elif game_state == "game_over":
                     # Show game over message and exit or offer restart
                     break
                # ... other states maybe ...
            ```
    2.  **Combat Setup Function:** When `game_state` becomes `"combat"`:
        *   Identify combatants: `player_active_daemon` (player must choose or default to first healthy one) and `enemy_daemon` (the one generated by the encounter).
        *   Display initial combat screen: Show both Daemons, their levels, and HP.
    3.  **Combat Turn Function/Loop:** This runs when `game_state == "combat"`.
        *   **Choose Player Action:**
            *   Prompt player: "Choose action: [F]ight, [S]witch, [I]tem, [R]un".
            *   If Fight: Prompt for which program to use. List available programs for `player_active_daemon`.
            *   If Switch: List other available (healthy) Daemons in the player's roster and prompt for choice.
            *   If Item: (Implement later) List items.
            *   If Run: Attempt to escape (simple check for prototype: always succeed against wild, fail against trainers? Or calculate based on speed?). If successful, set `game_state = "roaming"` and exit combat loop.
        *   **Choose Enemy Action (AI):**
            *   For a prototype: Randomly choose one of the `enemy_daemon`'s available programs. (More sophisticated AI later).
        *   **Determine Turn Order:** Compare `speed` stats of `player_active_daemon` and `enemy_daemon`.
        *   **Execute Actions (Resolution):**
            *   Execute the faster Daemon's action, then the slower one's.
            *   If using a program:
                *   Calculate damage: Use a formula involving attacker's `Attack`, defender's `Defense`, program `power`, random variance, and type effectiveness multiplier (need a type chart!).
                *   Apply damage using the `take_damage` method.
                *   Print descriptive text ("Virulet uses Data Siphon! It's super effective!").
            *   If switching: Change the `player_active_daemon`.
        *   **Check for Fainted Daemons:** After each action resolves, check `is_fainted()` on the target.
            *   If `enemy_daemon` faints: Combat ends (player wins).
            *   If `player_active_daemon` faints: Prompt player to switch to another Daemon. If no healthy Daemons remain, combat ends (player loses).
        *   **Apply Status Effects:** (Implement later) Apply end-of-turn effects like poison damage.
        *   **Loop:** Continue turns until a win/loss/run condition is met.
    4.  **Combat End Function:**
        *   If player won:
            *   Award XP to participating player Daemon(s) using `add_xp()`.
            *   Print victory message.
            *   Set `game_state = "roaming"`.
        *   If player lost (all Daemons fainted):
            *   Print defeat message ("You blacked out!").
            *   Implement consequence (e.g., return to last safe location, lose money - for prototype, maybe just set `game_state = "game_over"`).
        *   If player ran:
            *   Print escape message.
            *   Set `game_state = "roaming"`.

**3. Implementing Capture Mechanics**

*   **Goal:** Allow the player to attempt to capture weakened wild Daemons.
*   **Steps:**
    1.  **Add Capture Command:** Add a `[C]apture` option to the player's combat actions. Only allow against wild Daemons (not trainers).
    2.  **Capture Attempt Logic:**
        *   When the player chooses Capture:
            *   Calculate `catch_chance` (0.0 to 1.0). This is the core formula. A simplified version:
                `base_rate = enemy_daemon.capture_rate` (add this attribute to base Daemon data)
                `hp_factor = (enemy_daemon.stats['max_hp'] * 3 - enemy_daemon.stats['hp'] * 2) / (enemy_daemon.stats['max_hp'] * 3)`
                `status_bonus = 1.5 if enemy_daemon.status_effect in ["SLEEP", "FREEZE"] else 1.0 # etc.`
                `catch_chance = min(1.0, (base_rate / 255) * hp_factor * status_bonus)` *(Adjust divisor 255 as needed for balance)*
            *   Roll a random float: `roll = random.random()`.
            *   If `roll < catch_chance`:
                *   **Success:** Add a *copy* of the `enemy_daemon` to `player.daemons` (check roster limit later). Print success message. End combat (player wins, but maybe no XP?). Set `game_state = "roaming"`.
            *   Else:
                *   **Failure:** Print failure message ("The capture routine failed!"). The `enemy_daemon` gets its turn normally (or maybe gets a free attack). Combat continues.

**4. Expanding World Map and Daemon List (Data-Driven Design)**

*   **Goal:** Make adding new locations and Daemons easy without rewriting core game logic.
*   **Steps:**
    1.  **External Data Files:** Create separate files (e.g., `data/locations.json`, `data/daemons.json`, `data/programs.json`).
    2.  **JSON Structure:** Define the data structures within these files (as shown in the previous thought process example). Include all base stats, types, encounter rates, wild daemon lists, program learnsets, evolution details, etc.
    3.  **Loading Function:** Write Python code (e.g., in a `load_data.py` module) that runs at the start of the game:
        *   Opens and reads the JSON files.
        *   Parses the JSON data into Python dictionaries or lists. Store these loaded structures globally or in a game manager object (e.g., `LOADED_DAEMONS`, `LOADED_LOCATIONS`).
    4.  **World Map Population:** Instead of defining `Location` objects directly in `game.py`, loop through the loaded location data and create `Location` instances, populating the `world_map` dictionary.
    5.  **Daemon Factory:** Create a function `create_daemon(daemon_id, level)`:
        *   Takes the ID (e.g., `"virulet"`) and desired level.
        *   Looks up the base data for `daemon_id` in `LOADED_DAEMONS`.
        *   Creates a new `Daemon` instance.
        *   Calculates stats based on the base stats and the given `level`.
        *   Determines which programs it should know based on its `learnset` and the given `level` (looking up program details in `LOADED_PROGRAMS`).
        *   Returns the fully initialized `Daemon` object.
        *   Use this factory whenever you need a new Daemon (starters, wild encounters, trainer rosters).

**By implementing these steps, focusing on state management (`game_state`) and data-driven design for content, you can build out the core gameplay loop of your Cyberpunk NetRunner prototype.** Start simple with each step (basic combat math, simple AI, small data files) and refine as you go.