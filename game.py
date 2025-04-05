import sys
import os
import random
import logging
from pathlib import Path
import pygame # Import Pygame
import time # For potential delays

# Local imports - alphabetical order
from daemon import Daemon, Program, TYPE_CHART, STATUS_EFFECTS
from data_manager import load_game_data, load_game, save_game
from location import Location
from player import Player

# Pygame Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Global game data (populated by initialize_game)
DAEMON_BASE_STATS = {}
PROGRAMS = {}
world_map = {} # Will store Location objects, keyed by ID

def initialize_game():
    """Initialize the game data and objects, populating global variables."""
    # Load game data from config files
    game_data = load_game_data()

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

# --- Helper Functions ---
def draw_text(surface, text, font, color, x, y):
    """Helper function to draw text on a surface."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

# Global combat log
combat_log = []

def add_combat_log(message):
    """Adds a message to the combat log."""
    logging.info(f"Combat Log: {message}") # Also log it
    combat_log.append(message)
    # Optional: Limit log size
    MAX_LOG_SIZE = 20 # Limit log to prevent excessive memory use
    if len(combat_log) > MAX_LOG_SIZE:
        combat_log.pop(0)

# --- Drawing Functions ---
def draw_roaming(screen, font, player, location, world_map):
    """Draws the UI for the roaming state."""
    screen.fill(BLACK) # Clear screen

    # Draw Location Info
    draw_text(screen, f"Location: {location.name}", font, WHITE, 10, 10)
    # Basic word wrapping for description
    desc_lines = []
    words = location.description.split(' ')
    current_line = ""
    max_line_width = SCREEN_WIDTH - 20 # Allow some padding
    for word in words:
        test_line = current_line + word + " "
        test_surface = font.render(test_line, True, WHITE)
        if test_surface.get_width() < max_line_width:
            current_line = test_line
        else:
            desc_lines.append(current_line)
            current_line = word + " "
    desc_lines.append(current_line) # Add the last line

    y_offset = 50
    for line in desc_lines:
        draw_text(screen, line.strip(), font, WHITE, 10, y_offset)
        y_offset += font.get_linesize()

    # Draw Exits
    y_offset += 20 # Add some space
    draw_text(screen, "Exits:", font, WHITE, 10, y_offset)
    y_offset += font.get_linesize()
    if location.exits:
        for direction, dest_id in location.exits.items():
            dest_name = world_map.get(dest_id, Location(dest_id, "Unknown Area", "", {})).name # Safer lookup
            draw_text(screen, f"- {direction.capitalize()}: {dest_name}", font, WHITE, 20, y_offset)
            y_offset += font.get_linesize()
    else:
        draw_text(screen, "  None", font, WHITE, 20, y_offset)

    # TODO: Draw Player Status (simplified for now)
    y_offset = SCREEN_HEIGHT - 50
    active_daemon = player.get_active_daemon()
    status_text = f"Player: {player.name} | Active: {active_daemon.name if active_daemon else 'None'}"
    draw_text(screen, status_text, font, WHITE, 10, y_offset)

    # Draw Command Prompts
    y_offset = SCREEN_HEIGHT - 100 # Move prompts up a bit
    draw_text(screen, "Actions:", font, WHITE, 10, y_offset)
    y_offset += font.get_linesize()
    draw_text(screen, "- Move: [Arrow Keys]", font, WHITE, 20, y_offset)
    # TODO: Add prompts for other actions (Scan [S], Train [T], Status [C], Daemons [D], Save [V], Quit [Q]) once input is handled

def draw_hp_bar(surface, x, y, width, height, current_hp, max_hp):
    """Draws a health bar."""
    if max_hp <= 0: return # Avoid division by zero
    # Ensure current_hp doesn't exceed max_hp for drawing
    current_hp = min(current_hp, max_hp)
    fill_pct = current_hp / max_hp
    fill_width = int(width * fill_pct)

    # Border
    border_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, WHITE, border_rect, 2)

    # Fill color based on HP percentage
    if fill_pct > 0.6:
        fill_color = GREEN
    elif fill_pct > 0.3:
        fill_color = YELLOW
    else:
        fill_color = RED

    # Fill rectangle (ensure width is at least 0)
    if fill_width > 0:
        fill_rect = pygame.Rect(x + 1, y + 1, fill_width - 2, height - 2) # Inset fill slightly
        pygame.draw.rect(surface, fill_color, fill_rect)

def draw_combat(screen, font, player, player_daemon, enemy_daemon):
    """Draws the UI for the combat state."""
    screen.fill(BLACK)

    # --- Enemy Area (Top Right) ---
    enemy_area_x = SCREEN_WIDTH * 0.55
    enemy_area_y = 20
    draw_text(screen, f"{enemy_daemon.name} (Lv.{enemy_daemon.level})", font, WHITE, enemy_area_x, enemy_area_y)
    draw_hp_bar(screen, enemy_area_x, enemy_area_y + 35, 200, 20, enemy_daemon.hp, enemy_daemon.max_hp)
    draw_text(screen, f"HP: {enemy_daemon.hp}/{enemy_daemon.max_hp}", font, WHITE, enemy_area_x, enemy_area_y + 60)
    if enemy_daemon.status_effect:
        draw_text(screen, f"Status: {enemy_daemon.status_effect}", font, RED, enemy_area_x, enemy_area_y + 85)
    # TODO: Draw enemy sprite placeholder (e.g., a simple rect)
    pygame.draw.rect(screen, RED, (enemy_area_x + 50, enemy_area_y + 120, 100, 100), 1)


    # --- Player Area (Bottom Left) ---
    player_area_x = 30
    player_area_y = SCREEN_HEIGHT - 180
    # Use player_daemon which could be the last active one if current is fainted
    draw_text(screen, f"{player_daemon.name} (Lv.{player_daemon.level})", font, WHITE, player_area_x, player_area_y)
    draw_hp_bar(screen, player_area_x, player_area_y + 35, 200, 20, player_daemon.hp, player_daemon.max_hp)
    draw_text(screen, f"HP: {player_daemon.hp}/{player_daemon.max_hp}", font, WHITE, player_area_x, player_area_y + 60)
    if player_daemon.status_effect:
        draw_text(screen, f"Status: {player_daemon.status_effect}", font, RED, player_area_x, player_area_y + 85)
    # TODO: Draw player sprite placeholder
    pygame.draw.rect(screen, GREEN, (player_area_x + 50, player_area_y - 120, 100, 100), 1)


    # --- Action/Info Area (Bottom Right) ---
    menu_x = SCREEN_WIDTH * 0.5
    menu_y = SCREEN_HEIGHT - 150
    menu_width = SCREEN_WIDTH * 0.45
    menu_height = 130

    # Draw menu box
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
    pygame.draw.rect(screen, BLUE, menu_rect, 3) # Blue border

    # Draw content based on combat sub-state
    if combat_sub_state == "player_choose_action":
        draw_text(screen, "Actions:", font, WHITE, menu_x + 10, menu_y + 10)
        draw_text(screen, "[F]ight", font, WHITE, menu_x + 20, menu_y + 40)
        draw_text(screen, "[S]witch", font, WHITE, menu_x + 20, menu_y + 70)
        draw_text(screen, "[C]apture", font, WHITE, menu_x + 180, menu_y + 40)
        draw_text(screen, "[R]un", font, WHITE, menu_x + 180, menu_y + 70)
    elif combat_sub_state == "player_choose_program":
        draw_text(screen, "Choose Program:", font, WHITE, menu_x + 10, menu_y + 10)
        if player_daemon.programs:
            for i, prog in enumerate(player_daemon.programs):
                 # Simple two-column layout
                 col = i % 2
                 row = i // 2
                 prog_text = f"{i+1}. {prog.name}"
                 draw_text(screen, prog_text, font, WHITE, menu_x + 20 + col * 180, menu_y + 40 + row * 30)
            # Add back option
            draw_text(screen, "0. Back", font, WHITE, menu_x + 20, menu_y + 40 + ((len(player_daemon.programs) + 1) // 2) * 30)
        else:
            draw_text(screen, "No programs available!", font, RED, menu_x + 20, menu_y + 40)
            draw_text(screen, "0. Back", font, WHITE, menu_x + 20, menu_y + 70)
    elif combat_sub_state == "player_action_execute":
        draw_text(screen, "Executing action...", font, WHITE, menu_x + 10, menu_y + 10)
    elif combat_sub_state == "enemy_turn":
        draw_text(screen, "Enemy's turn...", font, WHITE, menu_x + 10, menu_y + 10)
    elif combat_sub_state == "apply_status_effects":
        draw_text(screen, "Applying status effects...", font, WHITE, menu_x + 10, menu_y + 10)
    elif combat_sub_state == "combat_end_check":
         draw_text(screen, "Checking combat result...", font, WHITE, menu_x + 10, menu_y + 10)
    elif combat_sub_state == "combat_fled":
         draw_text(screen, "Got away safely!", font, WHITE, menu_x + 10, menu_y + 10)
    # TODO: Add drawing for other sub-states (switch, capture result, combat end messages)


    # --- Message Log Area (Middle Bottom) ---
    log_x = 10
    log_y = SCREEN_HEIGHT - 250 # Position above player area and menu
    log_height = 100
    log_max_lines = 4 # Number of lines to show

    # Draw log box
    log_rect = pygame.Rect(log_x, log_y, SCREEN_WIDTH - 20, log_height)
    pygame.draw.rect(screen, BLUE, log_rect, 1) # Thin border

    # Draw messages (newest at bottom)
    start_index = max(0, len(combat_log) - log_max_lines)
    for i, message in enumerate(combat_log[start_index:]):
         draw_text(screen, message, font, WHITE, log_x + 5, log_y + 5 + i * font.get_linesize())

def create_daemon(daemon_id, level=1):
    """Create a new daemon object from the base stats based on its ID and level."""
    if daemon_id not in DAEMON_BASE_STATS:
        logging.error(f"Unknown daemon ID: {daemon_id}")
        return None

    base_stats = DAEMON_BASE_STATS[daemon_id]

    # Create programs for the daemon based on learnset and level
    daemon_programs = []
    learnset = base_stats.get("learnset", {}) # Learnset should be like {"1": ["prog1"], "5": ["prog2"]}

    # Track if we found valid programs for this daemon
    found_valid_programs = False

    for lvl_str, program_ids in learnset.items():
        try:
            learn_level = int(lvl_str)
            if level >= learn_level:
                # Ensure program_ids is a list
                if not isinstance(program_ids, list):
                    program_ids = [program_ids]  # Convert single string to list
                    logging.warning(f"Program IDs for level {learn_level} in '{daemon_id}' learnset is not a list: {program_ids}. Converting to list.")

                for program_id in program_ids:
                    if program_id in PROGRAMS:
                        program_data = PROGRAMS[program_id]
                        # Avoid adding duplicates if learned at multiple levels below current
                        if not any(p.id == program_id for p in daemon_programs):
                            program = Program(
                                program_id,
                                program_data.get("name", f"Unknown Program {program_id}"),
                                program_data.get("power", 0),
                                program_data.get("accuracy", 100),
                                program_data.get("type", "Untyped"),
                                program_data.get("effect", "none"),
                                program_data.get("description", "")
                            )
                            daemon_programs.append(program)
                            found_valid_programs = True
                    else:
                         logging.warning(f"Program ID '{program_id}' listed in learnset for '{daemon_id}' but not found in PROGRAMS.")
        except ValueError:
            logging.warning(f"Invalid level '{lvl_str}' in learnset for daemon '{daemon_id}'.")

    # If no valid programs were found, add default programs based on daemon type
    if not found_valid_programs or not daemon_programs:
        logging.warning(f"Daemon {daemon_id} (level {level}) has no valid programs. Adding default programs.")
        # Get primary type from daemon
        daemon_types = base_stats.get("types", [])
        primary_type = daemon_types[0] if isinstance(daemon_types, list) and daemon_types else base_stats.get("type", "UNTYPED")

        # Add default damage program based on type
        default_program_id = None

        # Map types to default program IDs
        type_program_map = {
            "VIRUS": "data_siphon",
            "FIREWALL": "firewall_bash",
            "CRYPTO": "hash_attack",
            "TROJAN": "backdoor_exploit",
            "NEURAL": "neural_shock",
            "SHELL": "shell_smash",
            "GHOST": "ghost_touch",
            "UNTYPED": "basic_attack"
        }

        # Get default program ID based on daemon type
        if primary_type.upper() in type_program_map:
            default_program_id = type_program_map[primary_type.upper()]
        else:
            default_program_id = "basic_attack"  # Fallback

        # Check if default program exists in PROGRAMS, otherwise use backup
        if default_program_id in PROGRAMS:
            program_data = PROGRAMS[default_program_id]
        else:
            # Create a basic attack program as last resort
            program_data = {
                "name": f"{daemon_id.capitalize()} Attack",
                "power": 40,
                "accuracy": 95,
                "type": primary_type,
                "effect": "damage",
                "description": "A basic attack."
            }
            default_program_id = "basic_attack"

        # Create and add default program
        default_program = Program(
            default_program_id,
            program_data.get("name", f"{daemon_id.capitalize()} Attack"),
            program_data.get("power", 40),
            program_data.get("accuracy", 95),
            program_data.get("type", primary_type),
            program_data.get("effect", "damage"),
            program_data.get("description", "A basic attack.")
        )
        daemon_programs.append(default_program)
        logging.info(f"Added default program '{default_program.name}' to daemon {daemon_id}")

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

# --- Combat Turn Handlers ---

def handle_player_action_execute(player, player_daemon, enemy_daemon, action, program):
    """Executes the chosen player action and returns the next sub-state."""
    global combat_sub_state # Need to modify global state

    if action == "fight":
        if program:
            result = player_daemon.use_program(program, enemy_daemon)
            add_combat_log(result["message"])

            if result["hit"] and result["damage"] is not None:
                # Calculate type effectiveness for display message
                multiplier = 1.0
                for target_type in enemy_daemon.types:
                    type_key = program.type.upper()
                    target_key = target_type.upper()
                    if type_key in TYPE_CHART and target_key in TYPE_CHART[type_key]:
                        multiplier *= TYPE_CHART[type_key][target_key]

                # Show effectiveness message
                if multiplier > 1.5: add_combat_log("It's super effective!")
                elif 0 < multiplier < 0.6: add_combat_log("It's not very effective...")
                elif multiplier == 0: add_combat_log("It has no effect...")

                # Apply damage
                if enemy_daemon.take_damage(result["damage"]):
                    add_combat_log(f"{enemy_daemon.name} fainted!")
                    return "combat_end_check" # Combat might be over

            # Handle status effects from special programs
            if result["effect_applied"] and "status" in result["effect_applied"]:
                status_type = result["effect_applied"].split(":")[1]
                if status_type in STATUS_EFFECTS:
                    enemy_daemon.status_effect = status_type
                    add_combat_log(f"{enemy_daemon.name} was afflicted with {status_type}!")
        else:
            # Basic "Struggle" if no programs
            add_combat_log(f"{player_daemon.name} flailed wildly!")
            struggle_damage = max(1, int(player_daemon.attack / 4))
            if enemy_daemon.take_damage(struggle_damage):
                 add_combat_log(f"{enemy_daemon.name} fainted!")
                 return "combat_end_check" # Combat might be over

    elif action == "switch":
        # TODO: Implement switch logic
        add_combat_log("Switching... (Not fully implemented)")
        pass # For now, just skip to enemy turn after attempting switch
    elif action == "capture":
        # TODO: Implement capture logic
        add_combat_log("Attempting capture... (Not fully implemented)")
        pass # For now, just skip to enemy turn after attempting capture
    elif action == "run":
        add_combat_log("Attempting to run...")
        # Base flee chance of 90% for wild battles (adjust as needed)
        flee_chance = 0.9
        # Modify flee chance based on speed comparison
        speed_ratio = player_daemon.speed / max(1, enemy_daemon.speed) # Avoid division by zero
        flee_chance *= speed_ratio
        flee_chance = min(1.0, flee_chance) # Cap at 100%

        if random.random() < flee_chance:
            add_combat_log("Got away safely!")
            return "combat_fled" # Transition to fled state
        else:
            add_combat_log("Couldn't get away!")
            # If failed, proceed to enemy's turn

    # After player action (if not run success), check if enemy fainted before proceeding to enemy turn
    if enemy_daemon.is_fainted():
        return "combat_end_check"

    # If combat continues, move to enemy's turn
    return "enemy_turn"

def handle_enemy_turn(player_daemon, enemy_daemon):
    """Handles the enemy's turn logic and returns the next sub-state."""
    add_combat_log(f"--- {enemy_daemon.name}'s Turn ---")

    # Check if enemy can act (e.g., status effects like LOCK)
    if enemy_daemon.status_effect == "LOCKED":
        if random.random() < 0.3:
            add_combat_log(f"{enemy_daemon.name} is LOCKED and unable to act!")
            return "apply_status_effects" # Skip action, go to status effects
        else:
            add_combat_log(f"{enemy_daemon.name} fights against the LOCK!")

    # Simple AI: Choose highest damage program if low HP, otherwise random
    enemy_program = None
    if enemy_daemon.programs:
        if enemy_daemon.hp < enemy_daemon.max_hp * 0.3:
            enemy_program = max(enemy_daemon.programs, key=lambda p: p.power)
        else:
            enemy_program = random.choice(enemy_daemon.programs)

    if enemy_program:
        result = enemy_daemon.use_program(enemy_program, player_daemon)
        add_combat_log(result["message"])

        if result["hit"] and result["damage"] is not None:
            # Calculate type effectiveness
            multiplier = 1.0
            for target_type in player_daemon.types:
                type_key = enemy_program.type.upper()
                target_key = target_type.upper()
                if type_key in TYPE_CHART and target_key in TYPE_CHART[type_key]:
                    multiplier *= TYPE_CHART[type_key][target_key]

            if multiplier > 1.5: add_combat_log("It's super effective!")
            elif 0 < multiplier < 0.6: add_combat_log("It's not very effective...")
            elif multiplier == 0: add_combat_log("It has no effect...")

            # Apply damage
            if player_daemon.take_damage(result["damage"]):
                add_combat_log(f"{player_daemon.name} fainted!")
                return "combat_end_check" # Combat might be over

        # Handle status effects
        if result["effect_applied"] and "status" in result["effect_applied"]:
            status_type = result["effect_applied"].split(":")[1]
            if status_type in STATUS_EFFECTS:
                player_daemon.status_effect = status_type
                add_combat_log(f"{player_daemon.name} was afflicted with {status_type}!")
    else:
        # Struggle
        add_combat_log(f"{enemy_daemon.name} flailed wildly!")
        struggle_damage = max(1, int(enemy_daemon.attack / 4))
        if player_daemon.take_damage(struggle_damage):
             add_combat_log(f"{player_daemon.name} fainted!")
             return "combat_end_check" # Combat might be over

    # After enemy action, check if player fainted before proceeding
    if player_daemon.is_fainted():
        return "combat_end_check"

    # Move to apply status effects phase
    return "apply_status_effects"

def handle_apply_status_effects(player_daemon, enemy_daemon):
    """Applies end-of-turn status effects and returns the next sub-state."""
    fainted_by_status = False

    # Player daemon status effects
    if player_daemon.status_effect == "CORRUPTED":
        damage = max(1, int(player_daemon.max_hp / 16))
        add_combat_log(f"{player_daemon.name} is damaged by CORRUPTION! (-{damage} HP)")
        if player_daemon.take_damage(damage):
            add_combat_log(f"{player_daemon.name} fainted from CORRUPTION!")
            fainted_by_status = True

    # Enemy daemon status effects (only if not already fainted)
    if not enemy_daemon.is_fainted() and enemy_daemon.status_effect == "CORRUPTED":
        damage = max(1, int(enemy_daemon.max_hp / 16))
        add_combat_log(f"{enemy_daemon.name} is damaged by CORRUPTION! (-{damage} HP)")
        if enemy_daemon.take_damage(damage):
            add_combat_log(f"{enemy_daemon.name} fainted from CORRUPTION!")
            fainted_by_status = True

    if fainted_by_status:
        return "combat_end_check"
    else:
        # Start next turn
        add_combat_log("--- Your Turn ---") # Prompt for next turn
        return "player_choose_action"

def handle_combat_end_check(player, player_daemon, enemy_daemon):
    """Checks if combat has ended and returns the next game_state or combat_sub_state."""
    global game_state, current_enemy_daemon # Need to modify game state

    player_lost = not player.get_active_daemon() # Check if ANY conscious daemons remain
    enemy_lost = enemy_daemon.is_fainted()

    if player_lost:
        add_combat_log("You have no more conscious Daemons!")
        add_combat_log("You blacked out!")
        # TODO: Implement proper game over / return to safe spot logic
        player.heal_all_daemons() # Simple recovery for now
        game_state = "roaming" # Go back to roaming
        # current_enemy_daemon = None # Cleared in main loop when game_state changes
        return game_state # Return the main game state
    elif enemy_lost:
        add_combat_log(f"You defeated {enemy_daemon.name}!")
        # Award XP
        xp_gain = enemy_daemon.level * 15 # Basic XP
        if player_daemon and not player_daemon.is_fainted(): # Ensure the one fighting gets XP
             player_daemon.gain_xp(xp_gain)
             add_combat_log(f"{player_daemon.name} gained {xp_gain} XP!")
             # TODO: Add level up check and message
        # TODO: Add potential item drops or other rewards
        game_state = "roaming" # Go back to roaming
        # current_enemy_daemon = None # Cleared in main loop when game_state changes
        return game_state # Return the main game state
    else:
        # Combat continues, should not normally reach here if called correctly
        logging.error("Entered combat_end_check but no one fainted?")
        return "player_choose_action" # Fallback


# --- Old Combat Function (Keep for reference or remove later) ---
# def run_combat(player, enemy_daemon): ... (Original function content)


def start_training_battle(player, difficulty="normal"):
    """
    Initialize a training battle with selected difficulty and daemon type.
    (Needs adaptation for Pygame UI)
    """
    # ... (Keep existing logic for now, but it uses input()) ...
    # This function needs to be refactored to use Pygame menus/states
    logging.warning("start_training_battle needs refactoring for Pygame UI")
    return False # Prevent use until refactored


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

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CNRD - Pygame Edition")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36) # Default font

    # Initialize game data and get starting location ID
    try:
        start_location_id = initialize_game()
    except Exception as e:
        logging.critical(f"Failed to initialize game data: {e}", exc_info=True)
        # TODO: Display error graphically instead of print
        print(f"CRITICAL ERROR during initialization: {e}. Check logs and config files.")
        pygame.quit()
        sys.exit(1)

    # --- Player Loading/Creation (Temporary - needs graphical interface) ---
    player_name = "karl" # Hardcode for now, or load default
    player = None
    try:
        player_data = load_game(player_name.lower())
        if player_data:
            player = Player.from_dict(player_data, world_map)
            logging.info(f"Loaded player: {player.name}")
            if player.location not in world_map:
                logging.warning(f"Loaded player location '{player.location}' invalid. Resetting.")
                player.location = start_location_id
                if start_location_id not in world_map:
                     logging.critical("Start location invalid after reset! Cannot proceed.")
                     pygame.quit()
                     sys.exit(1)
        else:
             logging.info(f"No save found for {player_name}, creating new player.")
    except Exception as e:
        logging.error(f"Failed to load game for {player_name}: {e}", exc_info=True)
        logging.info("Starting a new game.")

    if player is None:
        # Create a default new player if loading failed or no save exists
        starter_id = "virulet" # Default starter
        starter_daemon = create_daemon(starter_id, level=5)
        if starter_daemon:
            player = Player(player_name, start_location_id, [starter_daemon])
            logging.info(f"Created new player {player.name} with {starter_daemon.name}")
        else:
            logging.critical(f"Failed to create default starter daemon '{starter_id}'. Exiting.")
            # TODO: Display error graphically
            pygame.quit()
            sys.exit(1)
    # --- End Temporary Player Loading ---

    # Game state management
    global game_state, current_enemy_daemon, combat_sub_state # Make global for modification
    game_state = "roaming" # Possible states: roaming, combat, menu, etc.
    current_enemy_daemon = None # Holds the daemon for the current combat encounter
    combat_sub_state = "player_choose_action" # For combat flow

    # Variables to store player's combat choice between frames/states
    player_chosen_action = None
    player_selected_program = None
    # player_selected_switch_target = None # For later

    # Game loop
    playing = True
    while playing:
        # --- Event Handling ---
        # Input handling should only change state or set variables, not execute logic directly
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing = False
            elif event.type == pygame.KEYDOWN:
                if game_state == "roaming":
                    direction = None
                    if event.key == pygame.K_UP: direction = "north"
                    elif event.key == pygame.K_DOWN: direction = "south"
                    elif event.key == pygame.K_LEFT: direction = "west"
                    elif event.key == pygame.K_RIGHT: direction = "east"
                    # TODO: Add keys for Scan, Train, Status, Daemons, Save, Quit

                    if direction:
                        current_loc_id = player.location
                        if current_loc_id in world_map:
                            location = world_map[current_loc_id]
                            if direction in location.exits:
                                destination_id = location.exits[direction]
                                if destination_id in world_map:
                                    # Move player
                                    player.location = destination_id
                                    new_location = world_map[destination_id]
                                    logging.info(f"Player moved {direction} to {new_location.name}")
                                    # --- Random Encounter Check ---
                                    if random.random() < new_location.encounter_rate:
                                        wild_info = new_location.get_random_wild_daemon_info()
                                        if wild_info:
                                            daemon_id = wild_info.get("id")
                                            min_lvl = wild_info.get("min_lvl", 1)
                                            max_lvl = wild_info.get("max_lvl", min_lvl)
                                            level = random.randint(min_lvl, max_lvl)
                                            if daemon_id:
                                                current_enemy_daemon = create_daemon(daemon_id, level)
                                                if current_enemy_daemon:
                                                    logging.info(f"Encounter! {current_enemy_daemon.name} (Lv.{level})")
                                                    combat_log.clear() # Clear log for new battle
                                                    add_combat_log(f"Wild {current_enemy_daemon.name} (Lv.{level}) appeared!")
                                                    player_active = player.get_active_daemon()
                                                    if player_active:
                                                         add_combat_log(f"Go, {player_active.name}!")
                                                    else:
                                                         add_combat_log("No conscious daemons!")
                                                         # TODO: Handle this case properly (force switch/run?)
                                                    combat_sub_state = "player_choose_action" # Reset sub-state
                                                    game_state = "combat" # Switch state
                                                else:
                                                    logging.error(f"Failed to create wild daemon '{daemon_id}'")
                                else:
                                    # No valid direction pressed for movement
                                    pass
                elif game_state == "combat":
                    # Handle input based on combat sub-state (only when waiting for player input)
                    if combat_sub_state == "player_choose_action":
                        if event.key == pygame.K_f:
                            add_combat_log("Choose program:")
                            combat_sub_state = "player_choose_program"
                        elif event.key == pygame.K_s:
                            add_combat_log("Player chose Switch (Not implemented)")
                            # TODO: Transition to 'player_choose_switch' sub-state
                            # combat_sub_state = "player_choose_switch"
                        elif event.key == pygame.K_c:
                            add_combat_log("Player chose Capture (Not implemented)")
                            player_chosen_action = "capture"
                            combat_sub_state = "player_action_execute"
                        elif event.key == pygame.K_r:
                            # add_combat_log("Player chose Run") # Log moved to handler
                            player_chosen_action = "run"
                            combat_sub_state = "player_action_execute"

                    elif combat_sub_state == "player_choose_program":
                        player_daemon = player.get_active_daemon()
                        if event.key == pygame.K_0: # Back option
                            add_combat_log("Choose action:")
                            combat_sub_state = "player_choose_action"
                        elif pygame.K_1 <= event.key <= pygame.K_9:
                            choice_index = event.key - pygame.K_1
                            if player_daemon and 0 <= choice_index < len(player_daemon.programs):
                                player_selected_program = player_daemon.programs[choice_index] # Store selected program
                                player_chosen_action = "fight" # Store chosen action
                                add_combat_log(f"Selected {player_selected_program.name}")
                                combat_sub_state = "player_action_execute" # Move to execute state
                            else:
                                add_combat_log("Invalid program number.")
                        else:
                             add_combat_log("Invalid input (Use 1-9, 0).")

                    # TODO: Add key handling for player_choose_switch sub-state

                # TODO: Add key handling for other game states (menus)

        # --- Game Logic Update (Runs every frame) ---
        if game_state == "combat":
            player_daemon = player.get_active_daemon() # Get current active daemon

            # Execute player action if ready (and not waiting for input)
            if combat_sub_state == "player_action_execute":
                 if player_daemon and current_enemy_daemon and player_chosen_action:
                      next_sub_state = handle_player_action_execute(
                          player, player_daemon, current_enemy_daemon,
                          player_chosen_action, player_selected_program
                      )
                      combat_sub_state = next_sub_state
                      # Reset choices for next turn/state
                      player_chosen_action = None
                      player_selected_program = None
                 else:
                      logging.error("Entered player_action_execute without necessary data!")
                      combat_sub_state = "player_choose_action" # Attempt recovery

            # Handle enemy turn if it's their time
            elif combat_sub_state == "enemy_turn":
                 if player_daemon and current_enemy_daemon:
                     next_sub_state = handle_enemy_turn(player_daemon, current_enemy_daemon)
                     combat_sub_state = next_sub_state
                 else:
                     logging.error("Entered enemy_turn without necessary data!")
                     combat_sub_state = "player_choose_action" # Attempt recovery

            # Handle status effects application
            elif combat_sub_state == "apply_status_effects":
                 # Need player_daemon even if fainted for status check
                 current_player_daemon_obj = player.get_active_daemon() or player.get_last_active_daemon()
                 if current_player_daemon_obj and current_enemy_daemon:
                     next_sub_state = handle_apply_status_effects(current_player_daemon_obj, current_enemy_daemon)
                     combat_sub_state = next_sub_state
                 else:
                     logging.error("Entered apply_status_effects without necessary data!")
                     combat_sub_state = "player_choose_action" # Attempt recovery

            # Handle combat end check
            elif combat_sub_state == "combat_end_check":
                 # Need player_daemon even if fainted for XP check in handler
                 current_player_daemon_obj = player.get_active_daemon() or player.get_last_active_daemon() # Get last active if current is None
                 if player and current_player_daemon_obj and current_enemy_daemon:
                     next_state = handle_combat_end_check(player, current_player_daemon_obj, current_enemy_daemon)
                     if next_state in ["roaming", "game_over"]: # Check if it returned a main game state
                         game_state = next_state
                         if game_state == "roaming": current_enemy_daemon = None # Clear enemy only if returning to roaming
                     else: # Otherwise, it returned a combat sub-state (shouldn't happen often here)
                         combat_sub_state = next_state
                 else:
                     logging.error("Entered combat_end_check without necessary data!")
                     game_state = "roaming" # Attempt recovery by going back to roaming
                     current_enemy_daemon = None

            # Handle transition after fleeing
            elif combat_sub_state == "combat_fled":
                 game_state = "roaming"
                 current_enemy_daemon = None # Clear enemy


        # Other game logic updates might go here later

        # --- Drawing ---
        screen.fill(BLACK) # Clear screen each frame

        # Draw based on game state
        if game_state == "roaming":
            current_loc_id = player.location
            if current_loc_id in world_map:
                location = world_map[current_loc_id]
                draw_roaming(screen, font, player, location, world_map)
            else:
                # Handle invalid location graphically
                screen.fill(BLACK)
                draw_text(screen, f"ERROR: Invalid Location ID {current_loc_id}", font, RED, 10, 10)

        elif game_state == "combat":
            player_daemon = player.get_active_daemon()
            # Need to handle case where player might not have *any* active daemon if last one fainted from status
            last_active_daemon = player.get_last_active_daemon() # Get potentially fainted daemon for drawing
            active_or_last_daemon = player_daemon or last_active_daemon

            if not active_or_last_daemon and not player.get_healthy_daemons():
                 # If no healthy daemons left at all, combat should end immediately (handled by end_check)
                 draw_text(screen, "All Daemons Fainted!", font, RED, 100, 100)
            elif active_or_last_daemon and current_enemy_daemon:
                 # Draw using the active one if available, otherwise the last one (likely fainted)
                 draw_combat(screen, font, player, active_or_last_daemon, current_enemy_daemon)
            elif not current_enemy_daemon:
                 # Enemy fainted, combat should be ending (or we fled)
                 # The main loop logic should transition game_state back to roaming quickly
                 # We might briefly see this if drawing happens before state change processes
                 if combat_sub_state == "combat_fled":
                      draw_text(screen, "Got away safely!", font, WHITE, 100, 100)
                 else:
                      draw_text(screen, "Enemy Fainted!", font, GREEN, 100, 100)
            else:
                 # Should ideally be handled by forcing switch or ending combat
                 screen.fill(BLACK)
                 error_msg = "ERROR: Combat drawing error - inconsistent state!"
                 draw_text(screen, error_msg, font, RED, 10, 10)


        # TODO: Add drawing for other states (menu, title, etc.)

        # --- Update Display ---
        pygame.display.flip()

        # --- Cap Frame Rate ---
        clock.tick(FPS)

    # --- Game Exit ---
    logging.info("Game shutting down")
    # TODO: Add save prompt before quitting
    pygame.quit()
    sys.exit()


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
