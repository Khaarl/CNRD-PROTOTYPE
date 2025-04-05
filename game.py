import sys
import os
import random
import logging
from pathlib import Path
import pygame # Import Pygame
import time # For potential delays
import json # For JSON file handling
import math # For animations

# Local imports - alphabetical order
from daemon import Daemon, Program, TYPE_CHART, STATUS_EFFECTS
from data_manager import load_game, save_game
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
GRAY = (128, 128, 128)
# Add new colors for menu improvements
DARK_BLUE = (20, 30, 60)
LIGHT_BLUE = (60, 130, 240)
CYAN = (0, 200, 255)
PURPLE = (120, 40, 140)
DARK_PURPLE = (50, 0, 80)

# Main menu options
MENU_OPTIONS = ["New Game", "Load Game", "Options", "Quit"]

# Global game data (populated by initialize_game)
LOADED_DAEMONS = {}  # Will store daemon definitions
LOADED_PROGRAMS = {}  # Will store program definitions
DAEMON_BASE_STATS = {}  # Alias for LOADED_DAEMONS for compatibility with existing code
PROGRAMS = {}  # Alias for LOADED_PROGRAMS for compatibility
world_map = {}  # Will store Location objects, keyed by ID

# Game log to save
GAME_LOG = []

def add_to_game_log(message):
    """Add a message to the game log for later saving"""
    GAME_LOG.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    logging.info(message)

def save_game_log():
    """Save the game log to a file in the logs directory"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    game_log_file = os.path.join(log_dir, f'game_session_{timestamp}.log')
    
    try:
        with open(game_log_file, 'w') as f:
            f.write("\n".join(GAME_LOG))
        logging.info(f"Game log saved to {game_log_file}")
        print(f"Game log saved to {game_log_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to save game log: {e}")
        return False

def load_game_data(file_path):
    """Load game data from specified JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading game data from {file_path}: {str(e)}")
        raise

def load_dev_instruction(filename):
    """Load development instruction from the devinstruction folder."""
    try:
        instruction_path = os.path.join("devinstruction", filename)
        if os.path.exists(instruction_path):
            with open(instruction_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logging.warning(f"Dev instruction file {filename} not found")
            return None
    except Exception as e:
        logging.error(f"Error loading dev instruction {filename}: {e}")
        return None

def process_dev_instructions():
    """Process all development instructions to set up game configuration."""
    # Load main instruction file first
    main_instructions = load_dev_instruction("main_instructions.txt")
    if main_instructions:
        logging.info("Loaded main development instructions")
    
    # Load menu instructions
    menu_instructions = load_dev_instruction("menu_instructions.txt")
    if menu_instructions:
        logging.info("Loaded menu development instructions")
        # Parse menu structure if needed
        # This could modify MENU_OPTIONS or add submenu configurations
    
    # Return whether we successfully loaded instructions
    return main_instructions is not None

def initialize_game():
    """Initialize game data from config files."""
    try:
        global LOADED_DAEMONS, LOADED_PROGRAMS, world_map, DAEMON_BASE_STATS, PROGRAMS
        # Load daemon data
        daemon_data = load_game_data("config/daemons.json")
        LOADED_DAEMONS = daemon_data
        DAEMON_BASE_STATS = daemon_data  # Set the alias for compatibility
        
        # Load program data
        program_data = load_game_data("config/programs.json")
        LOADED_PROGRAMS = program_data
        PROGRAMS = program_data  # Set the alias for compatibility
        
        # Load location data and construct Location objects
        locations_data = load_game_data("config/locations.json")
        world_map = {}
        
        # Get the starting location ID (with fallback)
        start_location_id = locations_data.get("start_location", "market_square")
        # For backward compatibility - some config files use "start_location" rather than "start_location_id"
        if "start_location_id" in locations_data:
            start_location_id = locations_data["start_location_id"]
            
        # Create Location objects from the data
        locations = locations_data.get("locations", {})
        for loc_id, loc_data in locations.items():
            name = loc_data.get("name", "Unknown Area")
            desc = loc_data.get("description", "No description available.")
            exits = loc_data.get("exits", {})
            encounter_rate = loc_data.get("encounter_rate", 0.0)
            scan_encounter_rate = loc_data.get("scan_encounter_rate", 0.0)
            wild_daemons = loc_data.get("wild_daemons", [])
            
            world_map[loc_id] = Location(loc_id, name, desc, exits, 
                                         encounter_rate=encounter_rate, 
                                         scan_encounter_rate=scan_encounter_rate, 
                                         wild_daemons=wild_daemons)
        logging.info("Game initialized with data from config files and Location objects created.")
        return start_location_id
    except Exception as e:
        logging.critical(f"Failed to initialize game data: {e}", exc_info=True)
        raise

# --- Helper Functions ---
def draw_text(surface, text, font, color, x, y):
    """Helper function to draw text on a surface."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def draw_hp_bar(screen, current_hp, max_hp, rect):
    """Draw a health bar with current and max values"""
    if max_hp <= 0:  # Prevent division by zero
        fill_percent = 0
    else:
        fill_percent = max(0, min(current_hp / max_hp, 1.0))  # Clamp between 0-1
    
    # Draw background
    pygame.draw.rect(screen, (60, 60, 60), rect)
    
    # Draw the filled portion
    if fill_percent > 0:
        fill_rect = pygame.Rect(rect.x, rect.y, int(rect.width * fill_percent), rect.height)
        
        # Color changes based on HP percentage
        if fill_percent > 0.5:
            color = (0, 230, 0)  # Green for high health
        elif fill_percent > 0.2:
            color = (230, 230, 0)  # Yellow for medium health
        else:
            color = (230, 0, 0)  # Red for low health
        
        pygame.draw.rect(screen, color, fill_rect)
    
    # Draw border
    pygame.draw.rect(screen, (200, 200, 200), rect, 1)
    
    # Draw text showing hp/max_hp
    font = pygame.font.Font(None, 18)
    hp_text = f"{current_hp}/{max_hp}"
    text_surf = font.render(hp_text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

# Global combat log
combat_log = []

def add_combat_log(message):
    """Adds a message to the combat log."""
    add_to_game_log(f"Combat Log: {message}") # Also log it
    combat_log.append(message)
    # Optional: Limit log size
    MAX_LOG_SIZE = 20 # Limit log to prevent excessive memory use
    if len(combat_log) > MAX_LOG_SIZE:
        combat_log.pop(0)

def roll_for_encounter(player, location):
    """Check if a random encounter should occur based on location encounter rate."""
    if not hasattr(location, 'encounter_rate') or location.encounter_rate <= 0:
        return False
        
    roll = random.random()  # 0.0 to 1.0
    if roll < location.encounter_rate:
        logging.debug(f"Encounter roll: {roll} < {location.encounter_rate} - Encounter triggered!")
        return True
    else:
        logging.debug(f"Encounter roll: {roll} >= {location.encounter_rate} - No encounter")
        return False

def initialize_combat(player, location):
    """Initialize combat with a random wild daemon based on location."""
    global game_state, combat_sub_state, enemy_daemon, combat_log
    
    # Clear combat log for new combat
    combat_log.clear()
    
    # Set combat state
    game_state = "combat"
    combat_sub_state = "combat_start"
    
    # Select random daemon from location's wild_daemons list
    if not hasattr(location, 'wild_daemons') or not location.wild_daemons:
        # Fallback if no wild daemons specified
        daemon_options = list(DAEMON_BASE_STATS.keys())
        daemon_id = random.choice(daemon_options)
        wild_level = random.randint(1, 5)  # Default level range
    else:
        # Select from location's specified daemons
        daemon_entry = random.choice(location.wild_daemons)
        
        # Handle both simple strings and dict entries with level ranges
        if isinstance(daemon_entry, dict):
            daemon_id = daemon_entry.get("id", "virulet")
            min_level = daemon_entry.get("min_level", 1)
            max_level = daemon_entry.get("max_level", 5)
            wild_level = random.randint(min_level, max_level)
        else:
            daemon_id = daemon_entry
            wild_level = random.randint(1, 5)  # Default level range
    
    # Create the enemy daemon
    enemy_daemon = Daemon.create_from_base(daemon_id, wild_level)
    
    # Give the daemon some programs
    if wild_level <= 3:
        program_count = 1
    elif wild_level <= 6:
        program_count = 2
    else:
        program_count = 3
        
    # Add basic attack program
    data_siphon = Program(
        id="DATA_SIPHON",
        name="Data Siphon",
        power=35,
        accuracy=95,
        program_type="VIRUS",
        effect="damage",
        description="Drains data from the target"
    )
    enemy_daemon.add_program(data_siphon)
    
    # Add additional programs based on level
    if program_count > 1:
        # Add a status effect program
        glitch = Program(
            id="GLITCH",
            name="Glitch",
            power=20,
            accuracy=80,
            program_type="BUG",
            effect="slow",
            description="Causes system lag"
        )
        enemy_daemon.add_program(glitch)
        
    if program_count > 2:
        # Add a stronger attack program
        purge = Program(
            id="PURGE",
            name="Data Purge",
            power=50,
            accuracy=75,
            program_type=enemy_daemon.daemon_type,
            effect="damage",
            description="Violently erases data"
        )
        enemy_daemon.add_program(purge)
        
    # Log encounter start
    add_combat_log(f"Wild {enemy_daemon.name} appeared!")
    add_combat_log(f"Level {enemy_daemon.level} {enemy_daemon.daemon_type} type")
    
    # Update state for player's turn
    combat_sub_state = "player_choose_action"
    
    return enemy_daemon

def handle_combat_turn(player, player_daemon, enemy):
    """Process a turn of combat based on the current combat sub-state."""
    global combat_sub_state, combat_result
    
    if combat_sub_state == "combat_start":
        # Just transition to player's turn
        combat_sub_state = "player_choose_action"
        
    elif combat_sub_state == "player_action_execute":
        # This is called after player has selected a program to use
        if hasattr(player, 'selected_program') and player.selected_program:
            program = player.selected_program
            player.selected_program = None  # Reset after use
            
            # Calculate hit
            hit_roll = random.randint(1, 100)
            if hit_roll <= program.accuracy:
                # Hit - calculate damage
                damage = calculate_damage(player_daemon, enemy, program)
                enemy.take_damage(damage)
                
                add_combat_log(f"{player_daemon.name} used {program.name}!")
                
                if program.effect and program.effect != "damage":
                    # Apply status effect
                    if random.random() < 0.7:  # 70% chance for status effect
                        enemy.status_effect = program.effect
                        add_combat_log(f"{enemy.name} is now {program.effect}!")
                    
                add_combat_log(f"Dealt {damage} damage to {enemy.name}!")
            else:
                add_combat_log(f"{player_daemon.name}'s {program.name} missed!")
                
        # Check if enemy fainted
        if enemy.hp <= 0:
            combat_sub_state = "combat_victory"
            add_combat_log(f"Wild {enemy.name} fainted!")
            return
            
        # Move to enemy turn
        combat_sub_state = "enemy_turn"
        
    elif combat_sub_state == "enemy_turn":
        # Enemy selects a random program and attacks
        if not enemy.programs:
            add_combat_log(f"Wild {enemy.name} has no programs!")
            combat_sub_state = "apply_status_effects"
            return
            
        enemy_program = random.choice(enemy.programs)
        
        # Status effects may prevent turn
        if enemy.status_effect == "stun" and random.random() < 0.5:
            add_combat_log(f"{enemy.name} is stunned and couldn't move!")
        elif enemy.status_effect == "slow" and random.random() < 0.3:
            add_combat_log(f"{enemy.name} is slowed and couldn't move!")
        else:
            # Calculate hit
            hit_roll = random.randint(1, 100)
            if hit_roll <= enemy_program.accuracy:
                # Hit - calculate damage
                damage = calculate_damage(enemy, player_daemon, enemy_program)
                player_daemon.take_damage(damage)
                
                add_combat_log(f"Wild {enemy.name} used {enemy_program.name}!")
                
                if enemy_program.effect and enemy_program.effect != "damage":
                    # Apply status effect
                    if random.random() < 0.7:  # 70% chance for status effect
                        player_daemon.status_effect = enemy_program.effect
                        add_combat_log(f"{player_daemon.name} is now {enemy_program.effect}!")
                        
                add_combat_log(f"Took {damage} damage!")
            else:
                add_combat_log(f"Wild {enemy.name}'s {enemy_program.name} missed!")
        
        # Check if player fainted
        if player_daemon.hp <= 0:
            combat_sub_state = "combat_defeat"
            add_combat_log(f"{player_daemon.name} fainted!")
            return
            
        # Move to status effect phase
        combat_sub_state = "apply_status_effects"
        
    elif combat_sub_state == "apply_status_effects":
        # Apply damage from status effects like "burn"
        if player_daemon.status_effect == "burn":
            burn_damage = max(1, int(player_daemon.max_hp * 0.08))
            player_daemon.take_damage(burn_damage)
            add_combat_log(f"{player_daemon.name} took {burn_damage} damage from burn!")
            
        if enemy.status_effect == "burn":
            burn_damage = max(1, int(enemy.max_hp * 0.08))
            enemy.take_damage(burn_damage)
            add_combat_log(f"{enemy.name} took {burn_damage} damage from burn!")
            
        # Check if either fainted from status
        if player_daemon.hp <= 0:
            combat_sub_state = "combat_defeat"
            add_combat_log(f"{player_daemon.name} fainted!")
            return
            
        if enemy.hp <= 0:
            combat_sub_state = "combat_victory"
            add_combat_log(f"Wild {enemy.name} fainted!")
            return
            
        # Status effect may end
        if player_daemon.status_effect and random.random() < 0.2:
            add_combat_log(f"{player_daemon.name} recovered from {player_daemon.status_effect}!")
            player_daemon.status_effect = None
            
        if enemy.status_effect and random.random() < 0.2:
            add_combat_log(f"{enemy.name} recovered from {enemy.status_effect}!")
            enemy.status_effect = None
        
        # Return to player's turn
        combat_sub_state = "player_choose_action"
        
    elif combat_sub_state == "combat_victory":
        # Handle victory: gain XP, possible daemon capture
        xp_gained = calculate_xp(enemy)
        player_daemon.gain_xp(xp_gained)
        add_combat_log(f"Gained {xp_gained} XP!")
        
        # Check for level up
        if player_daemon.check_level_up():
            add_combat_log(f"{player_daemon.name} grew to level {player_daemon.level}!")
            
        # End combat
        combat_sub_state = "combat_end"
        
    elif combat_sub_state == "combat_defeat":
        # Handle defeat
        add_combat_log("You lost the battle!")
        combat_sub_state = "combat_end"
        
    elif combat_sub_state == "combat_fled":
        # Handle fleeing
        add_combat_log("Got away safely!")
        combat_sub_state = "combat_end"
        
    elif combat_sub_state == "combat_capture_attempt":
        # Handle daemon capture
        capture_chance = calculate_capture_chance(enemy)
        if random.random() < capture_chance:
            # Capture success
            add_combat_log(f"{enemy.name} was captured!")
            player.add_daemon(enemy)
            combat_sub_state = "combat_end"
        else:
            # Capture failed
            add_combat_log(f"{enemy.name} broke free!")
            combat_sub_state = "enemy_turn"
            
    elif combat_sub_state == "combat_end":
        # Wait for player acknowledgment, then exit combat
        # This is handled by key press to game_state = "roaming"
        pass

def calculate_damage(attacker, defender, program):
    """Calculate damage based on attacker/defender types and program."""
    # Base damage from program power and attacker level
    base_damage = int(program.power * (0.8 + attacker.level * 0.04))
    
    # Type effectiveness
    type_multiplier = 1.0
    if program.program_type in TYPE_CHART and defender.daemon_type in TYPE_CHART[program.program_type]:
        # Super effective
        type_multiplier = 1.5
        add_combat_log("It's super effective!")
    elif defender.daemon_type in TYPE_CHART and program.program_type in TYPE_CHART[defender.daemon_type]:
        # Not very effective
        type_multiplier = 0.5
        add_combat_log("It's not very effective...")
        
    # Random factor (0.85 to 1.15)
    random_factor = random.uniform(0.85, 1.15)
    
    # Calculate final damage
    damage = int(base_damage * type_multiplier * random_factor)
    return max(1, damage)  # Minimum 1 damage

def calculate_xp(defeated_daemon):
    """Calculate XP gained from defeating a daemon."""
    # Formula based on daemon level
    base_xp = 20 + (defeated_daemon.level * 5)
    return base_xp

def calculate_capture_chance(wild_daemon):
    """Calculate chance of capturing a wild daemon."""
    # Base chance depends on daemon's remaining HP percentage
    hp_factor = 1.0 - (wild_daemon.hp / wild_daemon.max_hp)
    
    # Level makes it harder
    level_factor = 1.0 / (1.0 + (wild_daemon.level * 0.1))
    
    # Status effects help
    status_bonus = 0.2 if wild_daemon.status_effect else 0.0
    
    # Calculate final chance (between 0.1 and 0.9)
    chance = 0.3 + (hp_factor * 0.4) + (level_factor * 0.2) + status_bonus
    return min(0.9, max(0.1, chance))

def save_current_game(player, save_name=None):
    """Save the current game state to a file"""
    if save_name is None:
        save_name = player.name.lower()
    
    # Create save data dictionary
    save_data = {
        "name": player.name,
        "location": player.location,
        "daemons": []
    }
    
    # Add daemon data
    for daemon in player.daemons:
        daemon_data = {
            "name": daemon.name,
            "level": daemon.level,
            "types": daemon.types if hasattr(daemon, 'types') else [daemon.daemon_type],
            "hp": daemon.hp,
            "max_hp": daemon.max_hp,
            "attack": daemon.attack if hasattr(daemon, 'attack') else 10,
            "defense": daemon.defense if hasattr(daemon, 'defense') else 10,
            "speed": daemon.speed if hasattr(daemon, 'speed') else 10,
            "xp": daemon.xp,
            "xp_next_level": daemon.xp_next_level,
            "programs": []
        }
        
        # Add program data
        for program in daemon.programs:
            program_data = {
                "id": program.id if hasattr(program, 'id') else program.name.lower().replace(" ", "_"),
                "name": program.name,
                "power": program.power,
                "accuracy": program.accuracy,
                "type": program.program_type if hasattr(program, 'program_type') else program.type,
                "effect": program.effect,
                "description": program.description if hasattr(program, 'description') else ""
            }
            daemon_data["programs"].append(program_data)
        
        save_data["daemons"].append(daemon_data)
    
    # Save to file using data_manager
    result = save_game(save_data, save_name)
    if result:
        add_to_game_log(f"Game saved as '{save_name}'")
        logging.info(f"Game saved successfully as '{save_name}'")
    else:
        add_to_game_log("Failed to save game")
        logging.error("Failed to save game")
    
    return result

def load_saved_game(save_name):
    """Load a saved game file and return player data"""
    from data_manager import load_game as load_game_data
    
    # Load the save file
    player_data = load_game_data(save_name)
    if not player_data:
        logging.error(f"Failed to load save file: {save_name}")
        return None
    
    # Return the loaded data
    logging.info(f"Successfully loaded save file: {save_name}")
    return player_data

def create_player_from_save(player_data, start_location_id):
    """Create a player object from saved data"""
    # Create player with basic info
    player = Player(player_data.get("name", "Runner"), player_data.get("location", start_location_id))
    
    # Load daemons
    for daemon_data in player_data.get("daemons", []):
        daemon = Daemon(
            name=daemon_data.get("name", "Unknown Daemon"),
            daemon_type=daemon_data.get("types", ["VIRUS"])[0],  # Use first type as daemon_type
            level=daemon_data.get("level", 1)
        )
        
        # Set daemon stats
        daemon.hp = daemon_data.get("hp", 10)
        daemon.max_hp = daemon_data.get("max_hp", 10)
        daemon.attack = daemon_data.get("attack", 10)
        daemon.defense = daemon_data.get("defense", 10)
        daemon.speed = daemon_data.get("speed", 10)
        daemon.xp = daemon_data.get("xp", 0)
        daemon.xp_next_level = daemon_data.get("xp_next_level", 100)
        
        # Load programs
        for program_data in daemon_data.get("programs", []):
            program = Program(
                id=program_data.get("id", "unknown_program"),
                name=program_data.get("name", "Unknown Program"),
                power=program_data.get("power", 10),
                accuracy=program_data.get("accuracy", 80),
                program_type=program_data.get("type", "NORMAL"),
                effect=program_data.get("effect", "damage"),
                description=program_data.get("description", "")
            )
            daemon.add_program(program)
        
        # Add daemon to player
        player.add_daemon(daemon)
    
    # Set active daemon if player has any
    if player.daemons:
        player.set_active_daemon(player.daemons[0])
    
    return player

def draw_load_game(screen, font, save_files, selected_index):
    """Draw the load game screen with save file selection"""
    # Create gradient background
    gradient_rect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        r = int(DARK_PURPLE[0] + (DARK_BLUE[0] - DARK_PURPLE[0]) * y / SCREEN_HEIGHT)
        g = int(DARK_PURPLE[1] + (DARK_BLUE[1] - DARK_PURPLE[1]) * y / SCREEN_HEIGHT)
        b = int(DARK_PURPLE[2] + (DARK_BLUE[2] - DARK_PURPLE[2]) * y / SCREEN_HEIGHT)
        pygame.draw.line(gradient_rect, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    screen.blit(gradient_rect, (0, 0))
    
    # Draw title
    title_font = pygame.font.Font(None, 64)
    title_text = "LOAD GAME"
    title_surface = title_font.render(title_text, True, LIGHT_BLUE)
    screen.blit(title_surface, (SCREEN_WIDTH//2 - title_surface.get_width()//2, 50))
    
    # Draw decorative line
    pygame.draw.line(screen, LIGHT_BLUE, (150, 120), (SCREEN_WIDTH - 150, 120), 2)
    
    if not save_files:
        # No save files message
        no_saves_font = pygame.font.Font(None, 36)
        no_saves_text = "No save files found!"
        no_saves_surface = no_saves_font.render(no_saves_text, True, RED)
        screen.blit(no_saves_surface, (SCREEN_WIDTH//2 - no_saves_surface.get_width()//2, SCREEN_HEIGHT//2 - 20))
        
        # Back option
        back_text = "Back to Main Menu"
        back_surface = font.render(back_text, True, CYAN)
        screen.blit(back_surface, (SCREEN_WIDTH//2 - back_surface.get_width()//2, SCREEN_HEIGHT//2 + 40))
    else:
        # Draw save files list
        file_y = 170
        file_spacing = 50
        panel_width = SCREEN_WIDTH - 200
        
        # Save files panel
        pygame.draw.rect(screen, (30, 40, 70, 180), (100, 150, panel_width, 300))
        pygame.draw.rect(screen, LIGHT_BLUE, (100, 150, panel_width, 300), 2)
        
        for i, save_file in enumerate(save_files):
            # Extract save name without extension
            save_name = save_file.stem
            
            # Determine color based on selection
            color = CYAN if i == selected_index else WHITE
            
            # Draw save file entry
            save_surface = font.render(save_name, True, color)
            x_pos = SCREEN_WIDTH//2 - save_surface.get_width()//2
            screen.blit(save_surface, (x_pos, file_y))
            
            # Draw selection indicator
            if i == selected_index:
                pygame.draw.rect(screen, CYAN, (x_pos - 15, file_y - 5, 
                                save_surface.get_width() + 30, save_surface.get_height() + 10), 2)
                # Triangle indicators
                pygame.draw.polygon(screen, CYAN, [(x_pos - 10, file_y + save_surface.get_height()//2), 
                                                 (x_pos - 5, file_y + save_surface.get_height()//2 - 5),
                                                 (x_pos - 5, file_y + save_surface.get_height()//2 + 5)])
            
            file_y += file_spacing
        
        # Draw back option at the bottom
        back_index = len(save_files)
        back_text = "Back to Main Menu"
        back_color = CYAN if back_index == selected_index else WHITE
        back_surface = font.render(back_text, True, back_color)
        back_x = SCREEN_WIDTH//2 - back_surface.get_width()//2
        back_y = file_y
        
        screen.blit(back_surface, (back_x, back_y))
        
        if back_index == selected_index:
            pygame.draw.rect(screen, CYAN, (back_x - 15, back_y - 5, 
                            back_surface.get_width() + 30, back_surface.get_height() + 10), 2)
    
    # Draw navigation help
    help_font = pygame.font.Font(None, 24)
    help_text = "Navigate: Arrow Keys | Select: Enter | Back: Escape"
    help_surface = help_font.render(help_text, True, GRAY)
    screen.blit(help_surface, (SCREEN_WIDTH//2 - help_surface.get_width()//2, SCREEN_HEIGHT - 40))

def get_save_files():
    """Get a list of available save files"""
    save_dir = Path("saves")
    if not save_dir.exists():
        save_dir.mkdir(exist_ok=True)
        return []
    
    return list(save_dir.glob("*.json"))

def handle_menu_selection(selected_index, player, start_location_id):
    """Handle selection from the main menu"""
    global game_state
    
    if selected_index == 0:  # New Game
        # We'll need to implement a name input system
        # For now, just start with a default name
        player.name = "Runner"  # Default name
        game_state = "roaming"
        logging.info("Starting new game")
    
    elif selected_index == 1:  # Load Game
        # Load game state
        game_state = "load_game"
        logging.info("Load game selected")
    
    elif selected_index == 2:  # Options
        # Would implement options menu
        logging.info("Options menu selected (not yet implemented)")
        # No state change for now
    
    elif selected_index == 3:  # Quit
        pygame.quit()
        sys.exit()

def draw_roaming(screen, font, player, location, world_map):
    """Draws the UI for the roaming state with improved visuals."""
    # Create gradient background (similar to main menu)
    gradient_rect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        # Slightly different gradient - darker blue tones for exploration
        r = int(DARK_BLUE[0] + (DARK_PURPLE[0] - DARK_BLUE[0]) * y / SCREEN_HEIGHT * 0.7)
        g = int(DARK_BLUE[1] + (DARK_PURPLE[1] - DARK_BLUE[1]) * y / SCREEN_HEIGHT * 0.7)
        b = int(DARK_BLUE[2] + (DARK_PURPLE[2] - DARK_BLUE[2]) * y / SCREEN_HEIGHT * 0.7)
        pygame.draw.line(gradient_rect, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    screen.blit(gradient_rect, (0, 0))
    
    # Add subtle grid pattern
    for x in range(0, SCREEN_WIDTH, 20):
        pygame.draw.line(screen, (50, 100, 150, 30), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 20):
        pygame.draw.line(screen, (50, 100, 150, 30), (0, y), (SCREEN_WIDTH, y), 1)
    
    # Get current time for animations
    current_time = pygame.time.get_ticks()
    pulse = (math.sin(current_time / 500) + 1) / 2  # Value between 0 and 1

    # Location header box
    header_height = 40
    header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, header_height)
    pygame.draw.rect(screen, (20, 40, 80), header_rect)
    pygame.draw.line(screen, CYAN, (0, header_height), (SCREEN_WIDTH, header_height), 2)
    
    # Draw Location Title with glow effect
    title_font = pygame.font.Font(None, 48)
    location_title = location.name
    
    # Draw glowing version
    glow_color = (CYAN[0], CYAN[1], CYAN[2], int(100 + 155 * pulse))
    if len(glow_color) == 3:  # Ensure it's RGBA
        glow_color = list(glow_color) + [int(100 + 155 * pulse)]
    title_glow = title_font.render(location_title, True, glow_color)
    screen.blit(title_glow, (15, 5))
    
    # Draw solid title
    title_text = title_font.render(location_title, True, WHITE)
    screen.blit(title_text, (15, 5))

    # Description panel
    desc_panel_rect = pygame.Rect(10, 50, SCREEN_WIDTH - 20, 150)
    pygame.draw.rect(screen, (30, 40, 70, 180), desc_panel_rect)
    pygame.draw.rect(screen, LIGHT_BLUE, desc_panel_rect, 1)

    # Description text with word wrapping
    desc_lines = []
    words = location.description.split(' ')
    current_line = ""
    max_line_width = desc_panel_rect.width - 20
    desc_font = pygame.font.Font(None, 28)
    
    for word in words:
        test_line = current_line + word + " "
        test_surface = desc_font.render(test_line, True, WHITE)
        if test_surface.get_width() < max_line_width:
            current_line = test_line
        else:
            desc_lines.append(current_line)
            current_line = word + " "
    desc_lines.append(current_line)  # Add the last line

    y_offset = desc_panel_rect.y + 15
    for line in desc_lines:
        draw_text(screen, line.strip(), desc_font, WHITE, desc_panel_rect.x + 10, y_offset)
        y_offset += desc_font.get_linesize()

    # Exits panel
    exits_panel_rect = pygame.Rect(10, 220, SCREEN_WIDTH - 20, 150)
    pygame.draw.rect(screen, (30, 40, 70, 180), exits_panel_rect)
    pygame.draw.rect(screen, LIGHT_BLUE, exits_panel_rect, 1)
    
    # Exits title
    exit_title_font = pygame.font.Font(None, 36)
    exit_title = exit_title_font.render("Exits:", True, LIGHT_BLUE)
    screen.blit(exit_title, (exits_panel_rect.x + 10, exits_panel_rect.y + 10))
    
    # List exits with directional icons
    exit_font = pygame.font.Font(None, 28)
    y_offset = exits_panel_rect.y + 50
    
    direction_symbols = {
        "north": "↑",
        "south": "↓",
        "east": "→",
        "west": "←",
        "up": "⇑",
        "down": "⇓"
    }
    
    if location.exits:
        for direction, dest_id in location.exits.items():
            dest_name = world_map.get(dest_id, Location(dest_id, "Unknown Area", "", {})).name
            dir_symbol = direction_symbols.get(direction.lower(), "•")
            exit_text = f"{dir_symbol} {direction.capitalize()}: {dest_name}"
            draw_text(screen, exit_text, exit_font, WHITE, exits_panel_rect.x + 30, y_offset)
            y_offset += exit_font.get_linesize() + 5
    else:
        draw_text(screen, "No exits available", exit_font, WHITE, exits_panel_rect.x + 30, y_offset)

    # Player status panel at bottom
    status_panel_height = 80
    status_panel_rect = pygame.Rect(0, SCREEN_HEIGHT - status_panel_height, SCREEN_WIDTH, status_panel_height)
    pygame.draw.rect(screen, (20, 30, 60), status_panel_rect)
    pygame.draw.line(screen, CYAN, (0, SCREEN_HEIGHT - status_panel_height), (SCREEN_WIDTH, SCREEN_HEIGHT - status_panel_height), 2)
    
    # Player info
    active_daemon = player.get_active_daemon()
    status_font = pygame.font.Font(None, 32)
    player_text = f"Runner: {player.name}"
    draw_text(screen, player_text, status_font, WHITE, 15, SCREEN_HEIGHT - status_panel_height + 15)
    
    daemon_text = f"Active Daemon: {active_daemon.name if active_daemon else 'None'}"
    if active_daemon:
        draw_text(screen, daemon_text, status_font, LIGHT_BLUE, 15, SCREEN_HEIGHT - status_panel_height + 45)
        
        # Show health if active daemon exists
        hp_text = f"HP: {active_daemon.hp}/{active_daemon.max_hp}"
        hp_width = status_font.render(hp_text, True, WHITE).get_width()
        draw_text(screen, hp_text, status_font, WHITE, SCREEN_WIDTH - hp_width - 20, SCREEN_HEIGHT - status_panel_height + 15)
        
        # Small HP bar
        hp_bar_width = 200
        hp_bar_height = 10
        draw_hp_bar(screen, SCREEN_WIDTH - hp_bar_width - 20, SCREEN_HEIGHT - status_panel_height + 45, 
                   hp_bar_width, hp_bar_height, active_daemon.hp, active_daemon.max_hp)
    else:
        draw_text(screen, daemon_text, status_font, RED, 15, SCREEN_HEIGHT - status_panel_height + 45)

    # Command help at the very bottom
    help_font = pygame.font.Font(None, 24)
    help_text = "Move: Arrow Keys/WASD | Inventory: I | Save: F5 | Menu: ESC | Quit: Q"
    draw_text(screen, help_text, help_font, GRAY, SCREEN_WIDTH//2 - help_font.render(help_text, True, GRAY).get_width()//2, 
              SCREEN_HEIGHT - 25)

def draw_daemons_tab(screen, player, content_rect):
    """Draw the daemons tab content"""
    if not player.daemons:
        draw_centered_text(screen, "No daemons in your collection", content_rect.centerx, content_rect.centery, WHITE)
        return
    
    # Draw column headers
    header_font = pygame.font.Font(None, 22)
    headers = ["Name", "Level", "Type", "HP", "Status"]
    header_widths = [0.25, 0.1, 0.25, 0.25, 0.15]  # Proportional widths
    
    for i, header in enumerate(headers):
        x_pos = content_rect.x + sum(header_widths[:i]) * content_rect.width
        header_text = header_font.render(header, True, CYAN)
        screen.blit(header_text, (x_pos, content_rect.y + 5))
    
    # Draw horizontal separator
    pygame.draw.line(screen, GRAY, 
                     (content_rect.x, content_rect.y + 25),
                     (content_rect.right, content_rect.y + 25), 1)
    
    # Draw daemon entries
    entry_height = 40
    for i, daemon in enumerate(player.daemons):
        y_pos = content_rect.y + 30 + (i * entry_height)
        
        # Highlight active daemon
        if player.active_daemon == daemon:
            highlight_rect = pygame.Rect(content_rect.x, y_pos, content_rect.width, entry_height)
            pygame.draw.rect(screen, (50, 70, 120), highlight_rect)
            pygame.draw.rect(screen, CYAN, highlight_rect, 1)
        
        # Name
        name_text = pygame.font.Font(None, 24).render(daemon.name, True, WHITE)
        screen.blit(name_text, (content_rect.x + 5, y_pos + 5))
        
        # Level
        level_text = pygame.font.Font(None, 24).render(f"Lv.{daemon.level}", True, WHITE)
        screen.blit(level_text, (content_rect.x + content_rect.width * 0.25 + 5, y_pos + 5))
        
        # Type (may have multiple types)
        type_text = pygame.font.Font(None, 20).render("/".join(daemon.types), True, YELLOW)
        screen.blit(type_text, (content_rect.x + content_rect.width * 0.35 + 5, y_pos + 5))
        
        # HP Bar
        hp_bar_rect = pygame.Rect(
            content_rect.x + content_rect.width * 0.6, 
            y_pos + 5,
            content_rect.width * 0.2,
            20
        )
        draw_hp_bar(screen, daemon.stats['hp'], daemon.stats['max_hp'], hp_bar_rect)
        
        # Status
        status_color = GREEN if daemon.stats['hp'] > 0 else RED
        status_text = "Ready" if daemon.stats['hp'] > 0 else "Fainted"
        if daemon.status_effect:
            status_text = daemon.status_effect
            status_color = YELLOW
        
        status_font = pygame.font.Font(None, 20)
        status_render = status_font.render(status_text, True, status_color)
        screen.blit(status_render, (content_rect.x + content_rect.width * 0.85, y_pos + 5))

def draw_programs_tab(screen, player, content_rect):
    """Draw the programs tab content"""
    # Check if player has an active daemon
    if not player.active_daemon:
        draw_centered_text(screen, "No active daemon selected", content_rect.centerx, content_rect.centery, WHITE)
        return
    
    # Draw which daemon's programs we're viewing
    daemon_header = f"{player.active_daemon.name}'s Programs:"
    header_font = pygame.font.Font(None, 28)
    header_text = header_font.render(daemon_header, True, CYAN)
    screen.blit(header_text, (content_rect.x + 5, content_rect.y + 5))
    
    # Draw horizontal separator
    pygame.draw.line(screen, GRAY, 
                     (content_rect.x, content_rect.y + 35),
                     (content_rect.right, content_rect.y + 35), 1)
    
    # Check if daemon has programs
    if not player.active_daemon.programs:
        draw_centered_text(screen, "No programs installed", content_rect.centerx, content_rect.centery, WHITE)
        return
    
    # Draw program entries
    entry_height = 60
    for i, program in enumerate(player.active_daemon.programs):
        y_pos = content_rect.y + 45 + (i * entry_height)
        
        # Draw program box
        program_rect = pygame.Rect(content_rect.x + 5, y_pos, content_rect.width - 10, entry_height - 5)
        pygame.draw.rect(screen, (40, 50, 80), program_rect)
        pygame.draw.rect(screen, LIGHT_BLUE, program_rect, 1)
        
        # Program name and type
        name_font = pygame.font.Font(None, 26)
        name_text = name_font.render(program.name, True, WHITE)
        screen.blit(name_text, (program_rect.x + 10, program_rect.y + 5))
        
        type_font = pygame.font.Font(None, 20)
        type_text = type_font.render(f"Type: {program.type}", True, YELLOW)
        screen.blit(type_text, (program_rect.x + program_rect.width - type_text.get_width() - 10, program_rect.y + 5))
        
        # Program stats
        stats_font = pygame.font.Font(None, 20)
        power_text = stats_font.render(f"Power: {program.power}", True, WHITE)
        screen.blit(power_text, (program_rect.x + 10, program_rect.y + 30))
        
        accuracy_text = stats_font.render(f"Accuracy: {program.accuracy}%", True, WHITE)
        screen.blit(accuracy_text, (program_rect.x + 150, program_rect.y + 30))
        
        # Effect
        effect_text = stats_font.render(f"Effect: {program.effect}", True, CYAN)
        screen.blit(effect_text, (program_rect.x + 300, program_rect.y + 30))

def draw_items_tab(screen, player, content_rect):
    """Draw the items tab content"""
    # Draw header
    header_font = pygame.font.Font(None, 28)
    header_text = header_font.render("Inventory Items", True, CYAN)
    screen.blit(header_text, (content_rect.x + 5, content_rect.y + 5))
    
    # Draw horizontal separator
    pygame.draw.line(screen, GRAY, 
                     (content_rect.x, content_rect.y + 35),
                     (content_rect.right, content_rect.y + 35), 1)
    
    # Check if player has items
    if not hasattr(player, 'items') or not player.items:
        draw_centered_text(screen, "No items in inventory", content_rect.centerx, content_rect.centery, WHITE)
        return
    
    # Draw column headers
    col_font = pygame.font.Font(None, 22)
    col_headers = ["Item Name", "Quantity", "Description"]
    col_widths = [0.3, 0.1, 0.6]  # Proportional widths
    
    for i, header in enumerate(col_headers):
        x_pos = content_rect.x + sum(col_widths[:i]) * content_rect.width
        header_text = col_font.render(header, True, CYAN)
        screen.blit(header_text, (x_pos, content_rect.y + 40))
    
    # Draw items list
    entry_height = 30
    y_start = content_rect.y + 65
    
    for i, (item_name, item_data) in enumerate(player.items.items()):
        y_pos = y_start + (i * entry_height)
        
        # Item name
        name_text = pygame.font.Font(None, 22).render(item_name, True, WHITE)
        screen.blit(name_text, (content_rect.x + 5, y_pos))
        
        # Quantity
        qty_text = pygame.font.Font(None, 22).render(f"x{item_data['quantity']}", True, WHITE)
        screen.blit(qty_text, (content_rect.x + content_rect.width * 0.3 + 5, y_pos))
        
        # Description (truncate if too long)
        desc = item_data.get('description', "No description")
        if len(desc) > 60:  # Truncate long descriptions
            desc = desc[:57] + "..."
        desc_text = pygame.font.Font(None, 20).render(desc, True, GRAY)
        screen.blit(desc_text, (content_rect.x + content_rect.width * 0.4 + 5, y_pos))

def draw_centered_text(screen, text, x, y, color):
    """Helper function to draw centered text"""
    font = pygame.font.Font(None, 28)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def draw_inventory_tabs(screen, player, tab_index):
    """Draw inventory with tabbed interface for daemons, programs, and items"""
    # Draw background panel
    panel_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
    pygame.draw.rect(screen, DARK_BLUE, panel_rect)
    pygame.draw.rect(screen, LIGHT_BLUE, panel_rect, 2)
    
    # Draw tab headers
    tab_width = (panel_rect.width - 20) // 3
    tab_height = 30
    tab_y = panel_rect.y - tab_height + 2
    
    tabs = ["Daemons", "Programs", "Items"]
    for i, tab_name in enumerate(tabs):
        tab_x = panel_rect.x + 10 + (i * tab_width)
        tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
        
        # Active tab has different color
        if i == tab_index:
            pygame.draw.rect(screen, LIGHT_BLUE, tab_rect)
        else:
            pygame.draw.rect(screen, DARK_BLUE, tab_rect)
            
        # Always draw border
        pygame.draw.rect(screen, CYAN, tab_rect, 1)
        
        # Tab text
        font = pygame.font.Font(None, 24)
        text = font.render(tab_name, True, WHITE)
        text_rect = text.get_rect(center=(tab_x + tab_width//2, tab_y + tab_height//2))
        screen.blit(text, text_rect)
    
    # Draw content based on active tab
    content_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, 
                              panel_rect.width - 20, panel_rect.height - 20)
    
    if tab_index == 0:
        # DAEMONS TAB
        draw_daemons_tab(screen, player, content_rect)
    elif tab_index == 1:
        # PROGRAMS TAB
        draw_programs_tab(screen, player, content_rect)
    elif tab_index == 2:
        # ITEMS TAB
        draw_items_tab(screen, player, content_rect)
    
    # Draw footer with controls
    footer_font = pygame.font.Font(None, 20)
    footer_text = "Controls: [Tab] Switch tabs | [E] Examine | [Esc] Close"
    footer = footer_font.render(footer_text, True, GRAY)
    footer_rect = footer.get_rect(bottom=panel_rect.bottom - 5, centerx=panel_rect.centerx)
    screen.blit(footer, footer_rect)

# Define the main function that bootstrap.py will call
def main():
    """Main entry point for the game. Called by bootstrap.py."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk NetRunner: Digital Hunters")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()
    
    # Process any development instructions
    process_dev_instructions()
    
    # Initialize game state
    global game_state, menu_selected_index, combat_sub_state, combat_log
    game_state = "main_menu"
    menu_selected_index = 0
    inventory_tab = 0  # Track which inventory tab is selected (0: Daemons, 1: Programs, 2: Items)
    combat_sub_state = "player_choose_action"  # Default combat sub-state
    
    # Initialize game data
    start_location_id = initialize_game()
    
    # Create a new player with starter daemon (or load from save later)
    player = Player("Runner", start_location_id)
    
    # Add a starter daemon to the player
    starter_daemon = Daemon.create_from_base("virulet", 5)
    player.add_daemon(starter_daemon)
    player.set_active_daemon(starter_daemon)
    
    # Add basic programs to the starter daemon
    data_siphon_program = Program(
        id="DATA_SIPHON",
        name="Data Siphon",
        power=40,
        accuracy=95,
        program_type="VIRUS",
        effect="damage",
        description="Drains data from the target"
    )
    starter_daemon.add_program(data_siphon_program)
    
    # Main game loop
    running = True
    load_game_selected_index = 0  # Track selected save file index
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle key presses based on game state
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    # Quit on Q press from any state
                    running = False
                elif game_state == "main_menu":
                    # Main menu controls
                    if event.key == pygame.K_UP:
                        menu_selected_index = (menu_selected_index - 1) % len(MENU_OPTIONS)
                    elif event.key == pygame.K_DOWN:
                        menu_selected_index = (menu_selected_index + 1) % len(MENU_OPTIONS)
                    elif event.key == pygame.K_RETURN:
                        handle_menu_selection(menu_selected_index, player, start_location_id)
                
                elif game_state == "load_game":
                    # Load game controls
                    save_files = get_save_files()
                    if event.key == pygame.K_UP:
                        load_game_selected_index = (load_game_selected_index - 1) % (len(save_files) + 1)
                    elif event.key == pygame.K_DOWN:
                        load_game_selected_index = (load_game_selected_index + 1) % (len(save_files) + 1)
                    elif event.key == pygame.K_RETURN:
                        if load_game_selected_index < len(save_files):
                            save_name = save_files[load_game_selected_index].stem
                            player_data = load_saved_game(save_name)
                            if player_data:
                                player = create_player_from_save(player_data, start_location_id)
                                game_state = "roaming"
                                logging.info(f"Loaded game from save: {save_name}")
                        else:
                            game_state = "main_menu"
                    elif event.key == pygame.K_ESCAPE:
                        game_state = "main_menu"
                
                # Add roaming state controls
                elif game_state == "roaming":
                    # Movement controls
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        logging.debug(f"Attempting to move north from {player.location}")
                        success = player.move("north", world_map)
                        if not success:
                            add_to_game_log("Cannot move in that direction.")
                        else:
                            current_location = world_map.get(player.location)
                            if roll_for_encounter(player, current_location):
                                initialize_combat(player, current_location)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        logging.debug(f"Attempting to move south from {player.location}")
                        success = player.move("south", world_map)
                        if not success:
                            add_to_game_log("Cannot move in that direction.")
                        else:
                            current_location = world_map.get(player.location)
                            if roll_for_encounter(player, current_location):
                                initialize_combat(player, current_location)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        logging.debug(f"Attempting to move west from {player.location}")
                        success = player.move("west", world_map)
                        if not success:
                            add_to_game_log("Cannot move in that direction.")
                        else:
                            current_location = world_map.get(player.location)
                            if roll_for_encounter(player, current_location):
                                initialize_combat(player, current_location)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        logging.debug(f"Attempting to move east from {player.location}")
                        success = player.move("east", world_map)
                        if not success:
                            add_to_game_log("Cannot move in that direction.")
                        else:
                            current_location = world_map.get(player.location)
                            if roll_for_encounter(player, current_location):
                                initialize_combat(player, current_location)
                    # Inventory key
                    elif event.key == pygame.K_i:
                        game_state = "inventory"
                        logging.debug("Opening inventory")
                    # Menu key
                    elif event.key == pygame.K_ESCAPE:
                        game_state = "main_menu"
                        logging.debug("Returning to main menu")
                    # Save game key
                    elif event.key == pygame.K_F5:
                        save_current_game(player)
                
                elif game_state == "inventory":
                    # Inventory navigation
                    if event.key == pygame.K_TAB:
                        inventory_tab = (inventory_tab + 1) % 3  # Cycle through tabs
                        logging.debug(f"Switched to inventory tab {inventory_tab}")
                    elif event.key == pygame.K_LEFT:
                        inventory_tab = (inventory_tab - 1) % 3  # Previous tab
                        logging.debug(f"Switched to inventory tab {inventory_tab}")
                    elif event.key == pygame.K_RIGHT:
                        inventory_tab = (inventory_tab + 1) % 3  # Next tab
                        logging.debug(f"Switched to inventory tab {inventory_tab}")
                    # Close inventory
                    elif event.key == pygame.K_i or event.key == pygame.K_ESCAPE:
                        game_state = "roaming"
                        logging.debug("Closing inventory, returning to roaming")
                
                elif game_state == "combat":
                    # Combat controls based on sub-state
                    if combat_sub_state == "player_choose_action":
                        # Main combat menu
                        if event.key in [pygame.K_1, pygame.K_KP1]:
                            # ATTACK - Show programs
                            combat_sub_state = "player_choose_program"
                            logging.debug("Combat: Selected ATTACK")
                        elif event.key in [pygame.K_2, pygame.K_KP2]:
                            # ITEMS - Not implemented yet
                            add_combat_log("Items not available in prototype.")
                            logging.debug("Combat: Selected ITEMS (not implemented)")
                        elif event.key in [pygame.K_3, pygame.K_KP3]:
                            # CAPTURE - Try to capture the daemon
                            combat_sub_state = "combat_capture_attempt"
                            logging.debug("Combat: Selected CAPTURE")
                        elif event.key in [pygame.K_4, pygame.K_KP4]:
                            # FLEE - Try to escape
                            # 70% chance to flee successfully
                            if random.random() < 0.7:
                                combat_sub_state = "combat_fled"
                                add_combat_log("Got away safely!")
                            else:
                                add_combat_log("Couldn't escape!")
                                combat_sub_state = "enemy_turn"
                            logging.debug("Combat: Selected FLEE")
                            
                    elif combat_sub_state == "player_choose_program":
                        active_daemon = player.get_active_daemon()
                        
                        # Program selection (number keys 1-4)
                        if event.key in [pygame.K_1, pygame.K_KP1] and len(active_daemon.programs) >= 1:
                            player.selected_program = active_daemon.programs[0]
                            combat_sub_state = "player_action_execute"
                        elif event.key in [pygame.K_2, pygame.K_KP2] and len(active_daemon.programs) >= 2:
                            player.selected_program = active_daemon.programs[1]
                            combat_sub_state = "player_action_execute"
                        elif event.key in [pygame.K_3, pygame.K_KP3] and len(active_daemon.programs) >= 3:
                            player.selected_program = active_daemon.programs[2]
                            combat_sub_state = "player_action_execute"
                        elif event.key in [pygame.K_4, pygame.K_KP4] and len(active_daemon.programs) >= 4:
                            player.selected_program = active_daemon.programs[3]
                            combat_sub_state = "player_action_execute"
                        elif event.key == pygame.K_ESCAPE:
                            # Back to main combat menu
                            combat_sub_state = "player_choose_action"
                            
                    elif combat_sub_state in ["combat_victory", "combat_defeat", "combat_fled", "combat_end"]:
                        # Return to roaming after combat ends
                        if event.key == pygame.K_RETURN:
                            game_state = "roaming"
                            
                    # Process the combat turn if needed
                    handle_combat_turn(player, player.get_active_daemon(), enemy_daemon)
        
        # Update game logic based on state
        if game_state == "main_menu":
            # Main menu doesn't need updates
            pass
        elif game_state == "roaming":
            # Handle roaming state updates
            pass
        elif game_state == "combat":
            # Handle combat state updates
            pass
        
        # Render based on state
        screen.fill(BLACK)  # Clear the screen
        if game_state == "main_menu":
            draw_main_menu(screen, font, menu_selected_index)
        elif game_state == "load_game":
            save_files = get_save_files()
            draw_load_game(screen, font, save_files, load_game_selected_index)
        elif game_state == "roaming":
            current_location = world_map.get(player.location)
            if current_location:
                draw_roaming(screen, font, player, current_location, world_map)
        elif game_state == "combat":
            # Get the active daemon and enemy for combat
            player_daemon = player.get_active_daemon()
            if player_daemon and enemy_daemon:
                draw_combat(screen, font, player, player_daemon, enemy_daemon)
        elif game_state == "inventory":
            draw_inventory_tabs(screen, player, inventory_tab)
        
        # Display to screen
        pygame.display.flip()
        clock.tick(FPS)
    
    # When game ends, save game log
    save_game_log()
    pygame.quit()
    sys.exit()

def draw_main_menu(screen, font, selected_index):
    """Draws the main menu UI with improved visuals."""
    # Create gradient background
    gradient_rect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        r = int(DARK_PURPLE[0] + (DARK_BLUE[0] - DARK_PURPLE[0]) * y / SCREEN_HEIGHT)
        g = int(DARK_PURPLE[1] + (DARK_BLUE[1] - DARK_PURPLE[1]) * y / SCREEN_HEIGHT)
        b = int(DARK_PURPLE[2] + (DARK_BLUE[2] - DARK_PURPLE[2]) * y / SCREEN_HEIGHT)
        pygame.draw.line(gradient_rect, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    screen.blit(gradient_rect, (0, 0))
    
    # Draw title
    title_font = pygame.font.Font(None, 64)
    title_text = "CYBERPUNK NETRUNNER: DIGITAL HUNTERS"
    title_surface = title_font.render(title_text, True, LIGHT_BLUE)
    screen.blit(title_surface, (SCREEN_WIDTH//2 - title_surface.get_width()//2, 100))
    
    # Draw decorative line
    pygame.draw.line(screen, LIGHT_BLUE, (150, 170), (SCREEN_WIDTH - 150, 170), 2)
    
    # Draw menu options
    option_y = 250
    for i, option in enumerate(MENU_OPTIONS):
        color = CYAN if i == selected_index else WHITE
        option_surface = font.render(option, True, color)
        x_pos = SCREEN_WIDTH//2 - option_surface.get_width()//2
        screen.blit(option_surface, (x_pos, option_y))
        
        # Draw selection indicator for current selection
        if i == selected_index:
            pygame.draw.rect(screen, CYAN, (x_pos - 20, option_y - 5, 
                             option_surface.get_width() + 40, option_surface.get_height() + 10), 2)
            # Draw triangle indicators
            pygame.draw.polygon(screen, CYAN, [(x_pos - 15, option_y + option_surface.get_height()//2), 
                                              (x_pos - 5, option_y + option_surface.get_height()//2 - 5),
                                              (x_pos - 5, option_y + option_surface.get_height()//2 + 5)])
            pygame.draw.polygon(screen, CYAN, [(x_pos + option_surface.get_width() + 15, option_y + option_surface.get_height()//2), 
                                              (x_pos + option_surface.get_width() + 5, option_y + option_surface.get_height()//2 - 5),
                                              (x_pos + option_surface.get_width() + 5, option_y + option_surface.get_height()//2 + 5)])
        
        option_y += 60
    
    # Draw version info
    version_font = pygame.font.Font(None, 24)
    version_text = "v0.6.0 - Prototype"
    version_surface = version_font.render(version_text, True, GRAY)
    screen.blit(version_surface, (SCREEN_WIDTH - version_surface.get_width() - 10, SCREEN_HEIGHT - version_surface.get_height() - 10))
    
    # Draw navigation help
    help_font = pygame.font.Font(None, 24)
    help_text = "Navigate: Arrow Keys | Select: Enter"
    help_surface = help_font.render(help_text, True, GRAY)
    screen.blit(help_surface, (10, SCREEN_HEIGHT - help_surface.get_height() - 10))

if __name__ == "__main__":
    main()  # This line already exists, but we need to ensure it calls a function named 'main'
else:
    # For importing, ensure the main function is available when imported
    # This way bootstrap.py can call game.main() successfully
    __all__ = ['main']  # Explicitly expose 'main' when importing this module
