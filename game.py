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

# --- Drawing Functions ---
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
    help_text = "Move: Arrow Keys | Menu: ESC | Quit: Q"
    draw_text(screen, help_text, help_font, GRAY, SCREEN_WIDTH//2 - help_font.render(help_text, True, GRAY).get_width()//2, 
              SCREEN_HEIGHT - 25)

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
    """Draws the UI for the combat state with improved visuals."""
    # Create gradient background (similar to main menu)
    gradient_rect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        # Combat gradient - more red-purple tones for battle intensity
        r = int(DARK_PURPLE[0] + (DARK_BLUE[0] - DARK_PURPLE[0]) * y / SCREEN_HEIGHT * 0.5 + 10)
        g = int(DARK_PURPLE[1] + (DARK_BLUE[1] - DARK_PURPLE[1]) * y / SCREEN_HEIGHT * 0.5)
        b = int(DARK_PURPLE[2] + (DARK_BLUE[2] - DARK_PURPLE[2]) * y / SCREEN_HEIGHT * 0.5 + 5)
        pygame.draw.line(gradient_rect, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    screen.blit(gradient_rect, (0, 0))
    
    # Add subtle grid pattern
    for x in range(0, SCREEN_WIDTH, 20):
        pygame.draw.line(screen, (100, 50, 150, 30), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 20):
        pygame.draw.line(screen, (100, 50, 150, 30), (0, y), (SCREEN_WIDTH, y), 1)
    
    # Get current time for animations
    current_time = pygame.time.get_ticks()
    pulse = (math.sin(current_time / 500) + 1) / 2  # Value between 0 and 1
    
    # --- Combat header ---
    header_height = 30
    header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, header_height)
    pygame.draw.rect(screen, (40, 20, 60), header_rect)
    pygame.draw.line(screen, CYAN, (0, header_height), (SCREEN_WIDTH, header_height), 2)
    
    # Draw combat title
    title_font = pygame.font.Font(None, 36)
    battle_title = "COMBAT"
    battle_text = title_font.render(battle_title, True, LIGHT_BLUE)
    title_x = SCREEN_WIDTH // 2 - battle_text.get_width() // 2
    screen.blit(battle_text, (title_x, 5))

    # --- Enemy Area (Top Right) with panel ---
    enemy_panel_width = 350
    enemy_panel_height = 200
    enemy_panel_x = SCREEN_WIDTH - enemy_panel_width - 20
    enemy_panel_y = 40
    
    # Enemy panel background
    enemy_panel = pygame.Rect(enemy_panel_x, enemy_panel_y, enemy_panel_width, enemy_panel_height)
    pygame.draw.rect(screen, (60, 30, 70, 180), enemy_panel)
    
    # Pulsing border for enemy
    enemy_border_color = list(RED)
    if len(enemy_border_color) == 3:
        enemy_border_color = list(enemy_border_color) + [int(100 + 155 * pulse)]
    pygame.draw.rect(screen, enemy_border_color, enemy_panel, 2)
    
    # Enemy info
    enemy_name_font = pygame.font.Font(None, 40)
    enemy_name_text = f"{enemy_daemon.name}"
    enemy_name_render = enemy_name_font.render(enemy_name_text, True, WHITE)
    screen.blit(enemy_name_render, (enemy_panel_x + 15, enemy_panel_y + 15))
    
    # Enemy level with smaller font
    enemy_lvl_font = pygame.font.Font(None, 28)
    enemy_lvl_text = f"Level {enemy_daemon.level}"
    enemy_lvl_render = enemy_lvl_font.render(enemy_lvl_text, True, LIGHT_BLUE)
    screen.blit(enemy_lvl_render, (enemy_panel_x + 15, enemy_panel_y + 50))
    
    # Enemy HP text and bar
    enemy_hp_text = f"HP: {enemy_daemon.hp}/{enemy_daemon.max_hp}"
    enemy_hp_render = enemy_lvl_font.render(enemy_hp_text, True, WHITE)
    screen.blit(enemy_hp_render, (enemy_panel_x + 15, enemy_panel_y + 80))
    
    # Styled HP bar for enemy
    hp_bar_width = 250
    hp_bar_height = 15
    draw_hp_bar(screen, enemy_panel_x + 15, enemy_panel_y + 110, 
                hp_bar_width, hp_bar_height, enemy_daemon.hp, enemy_daemon.max_hp)
    
    # Enemy status effect if any
    if enemy_daemon.status_effect:
        status_font = pygame.font.Font(None, 28)
        status_text = f"STATUS: {enemy_daemon.status_effect}"
        status_render = status_font.render(status_text, True, RED)
        screen.blit(status_render, (enemy_panel_x + 15, enemy_panel_y + 140))
    
    # Enemy sprite placeholder
    sprite_size = 120
    sprite_x = enemy_panel_x + enemy_panel_width - sprite_size - 15
    sprite_y = enemy_panel_y + (enemy_panel_height - sprite_size) // 2
    pygame.draw.rect(screen, RED, (sprite_x, sprite_y, sprite_size, sprite_size), 0)
    # Add inner detail lines to sprite
    for i in range(3):
        pygame.draw.line(screen, (100, 0, 0), 
                         (sprite_x + 10, sprite_y + 20 + i*30), 
                         (sprite_x + sprite_size - 10, sprite_y + 20 + i*30), 2)

    # --- Player Area (Bottom Left) with panel ---
    player_panel_width = 350
    player_panel_height = 200
    player_panel_x = 20
    player_panel_y = SCREEN_HEIGHT - player_panel_height - 120
    
    # Player panel background
    player_panel = pygame.Rect(player_panel_x, player_panel_y, player_panel_width, player_panel_height)
    pygame.draw.rect(screen, (30, 50, 80, 180), player_panel)
    
    # Pulsing border for player
    player_border_color = list(CYAN)
    if len(player_border_color) == 3:
        player_border_color = list(player_border_color) + [int(100 + 155 * pulse)]
    pygame.draw.rect(screen, player_border_color, player_panel, 2)
    
    # Player daemon info
    player_name_font = pygame.font.Font(None, 40)
    player_name_text = f"{player_daemon.name}"
    player_name_render = player_name_font.render(player_name_text, True, WHITE)
    screen.blit(player_name_render, (player_panel_x + 15, player_panel_y + 15))
    
    # Player daemon level
    player_lvl_font = pygame.font.Font(None, 28)
    player_lvl_text = f"Level {player_daemon.level}"
    player_lvl_render = player_lvl_font.render(player_lvl_text, True, LIGHT_BLUE)
    screen.blit(player_lvl_render, (player_panel_x + 15, player_panel_y + 50))
    
    # Player HP text and bar
    player_hp_text = f"HP: {player_daemon.hp}/{player_daemon.max_hp}"
    player_hp_render = player_lvl_font.render(player_hp_text, True, WHITE)
    screen.blit(player_hp_render, (player_panel_x + 15, player_panel_y + 80))
    
    # Styled HP bar for player
    draw_hp_bar(screen, player_panel_x + 15, player_panel_y + 110, 
                hp_bar_width, hp_bar_height, player_daemon.hp, player_daemon.max_hp)
    
    # Player daemon status if any
    if player_daemon.status_effect:
        player_status_font = pygame.font.Font(None, 28)
        player_status_text = f"STATUS: {player_daemon.status_effect}"
        player_status_render = player_status_font.render(player_status_text, True, RED)
        screen.blit(player_status_render, (player_panel_x + 15, player_panel_y + 140))
    
    # Player daemon sprite placeholder
    player_sprite_x = player_panel_x + player_panel_width - sprite_size - 15
    player_sprite_y = player_panel_y + (player_panel_height - sprite_size) // 2
    pygame.draw.rect(screen, BLUE, (player_sprite_x, player_sprite_y, sprite_size, sprite_size), 0)
    # Add inner detail lines to sprite
    for i in range(3):
        pygame.draw.line(screen, (0, 100, 200), 
                         (player_sprite_x + 10, player_sprite_y + 20 + i*30), 
                         (player_sprite_x + sprite_size - 10, player_sprite_y + 20 + i*30), 2)

    # --- Combat Log Area (Middle) ---
    log_panel_width = SCREEN_WIDTH - 40
    log_panel_height = 100
    log_panel_x = 20
    log_panel_y = player_panel_y - log_panel_height - 20
    
    # Log panel background
    log_panel = pygame.Rect(log_panel_x, log_panel_y, log_panel_width, log_panel_height)
    pygame.draw.rect(screen, (20, 20, 40, 180), log_panel)
    pygame.draw.rect(screen, LIGHT_BLUE, log_panel, 1)
    
    # Log header
    log_header_font = pygame.font.Font(None, 28)
    log_header = log_header_font.render("BATTLE LOG", True, LIGHT_BLUE)
    screen.blit(log_header, (log_panel_x + 10, log_panel_y + 5))
    
    # Draw horizontal separator line
    pygame.draw.line(screen, LIGHT_BLUE, 
                     (log_panel_x + 5, log_panel_y + 30), 
                     (log_panel_x + log_panel_width - 5, log_panel_y + 30), 1)
    
    # Draw messages (newest at bottom)
    log_message_font = pygame.font.Font(None, 24)
    start_index = max(0, len(combat_log) - 4)  # Show up to 4 most recent messages
    for i, message in enumerate(combat_log[start_index:]):
        draw_text(screen, message, log_message_font, WHITE, 
                  log_panel_x + 10, log_panel_y + 35 + i * log_message_font.get_linesize())

    # --- Action/Info Area (Bottom) ---
    action_panel_width = SCREEN_WIDTH - 40
    action_panel_height = 100
    action_panel_x = 20
    action_panel_y = SCREEN_HEIGHT - action_panel_height - 15
    
    # Action panel background
    action_panel = pygame.Rect(action_panel_x, action_panel_y, action_panel_width, action_panel_height)
    pygame.draw.rect(screen, (30, 30, 50, 180), action_panel)
    
    # Add a pulsing highlight to the action area when waiting for player input
    if combat_sub_state in ["player_choose_action", "player_choose_program"]:
        action_highlight = list(CYAN)
        if len(action_highlight) == 3:
            action_highlight = list(action_highlight) + [int(100 + 155 * pulse)]
        pygame.draw.rect(screen, action_highlight, action_panel, 2)
    else:
        pygame.draw.rect(screen, LIGHT_BLUE, action_panel, 1)
    
    # Draw content based on combat sub-state
    action_font = pygame.font.Font(None, 32)
    
    if combat_sub_state == "player_choose_action":
        action_header = action_font.render("Choose Action:", True, YELLOW)
        screen.blit(action_header, (action_panel_x + 10, action_panel_y + 10))
        
        # Action buttons with highlights
        button_width = 130
        button_height = 40
        button_spacing = 25
        buttons = [
            {"text": "[F] Fight", "x": action_panel_x + 20, "y": action_panel_y + 50},
            {"text": "[S] Switch", "x": action_panel_x + 20 + button_width + button_spacing, "y": action_panel_y + 50},
            {"text": "[C] Capture", "x": action_panel_x + 20 + (button_width + button_spacing) * 2, "y": action_panel_y + 50},
            {"text": "[R] Run", "x": action_panel_x + 20 + (button_width + button_spacing) * 3, "y": action_panel_y + 50}
        ]
        
        for button in buttons:
            button_rect = pygame.Rect(button["x"], button["y"], button_width, button_height)
            pygame.draw.rect(screen, (60, 60, 100), button_rect)
            pygame.draw.rect(screen, WHITE, button_rect, 1)
            
            button_text = pygame.font.Font(None, 28).render(button["text"], True, WHITE)
            text_x = button["x"] + (button_width - button_text.get_width()) // 2
            text_y = button["y"] + (button_height - button_text.get_height()) // 2
            screen.blit(button_text, (text_x, text_y))
            
    elif combat_sub_state == "player_choose_program":
        program_header = action_font.render("Choose Program:", True, YELLOW)
        screen.blit(program_header, (action_panel_x + 10, action_panel_y + 10))
        
        if player_daemon.programs:
            # Calculate grid layout
            cols = 3  # Number of columns
            col_width = action_panel_width / cols - 10
            
            for i, prog in enumerate(player_daemon.programs):
                col = i % cols
                row = i // cols
                
                # Program slot background
                prog_x = action_panel_x + 10 + col * (col_width + 5)
                prog_y = action_panel_y + 45 + row * 25
                
                # Draw program option
                prog_text = f"{i+1}. {prog.name}"
                prog_font = pygame.font.Font(None, 24)
                draw_text(screen, prog_text, prog_font, WHITE, prog_x, prog_y)
            
            # Back option at the bottom
            back_y = action_panel_y + 45 + (((len(player_daemon.programs) - 1) // cols) + 1) * 25
            back_text = "0. Back"
            back_font = pygame.font.Font(None, 24)
            draw_text(screen, back_text, back_font, LIGHT_BLUE, action_panel_x + 10, back_y)
        else:
            no_prog_text = "No programs available!"
            draw_text(screen, no_prog_text, action_font, RED, action_panel_x + 10, action_panel_y + 50)
            back_text = "0. Back"
            draw_text(screen, back_text, action_font, LIGHT_BLUE, action_panel_x + 10, action_panel_y + 80)
            
    elif combat_sub_state == "player_action_execute":
        executing_text = "Executing action..."
        draw_text(screen, executing_text, action_font, YELLOW, action_panel_x + 10, action_panel_y + 30)
    elif combat_sub_state == "enemy_turn":
        enemy_turn_text = f"{enemy_daemon.name}'s turn..."
        draw_text(screen, enemy_turn_text, action_font, RED, action_panel_x + 10, action_panel_y + 30)
    elif combat_sub_state == "apply_status_effects":
        status_text = "Applying status effects..."
        draw_text(screen, status_text, action_font, PURPLE, action_panel_x + 10, action_panel_y + 30)
    elif combat_sub_state == "combat_end_check":
        checking_text = "Checking combat result..."
        draw_text(screen, checking_text, action_font, WHITE, action_panel_x + 10, action_panel_y + 30)
    elif combat_sub_state == "combat_fled":
        fled_text = "Got away safely!"
        draw_text(screen, fled_text, action_font, GREEN, action_panel_x + 10, action_panel_y + 30)
    # TODO: Add drawing for other sub-states (switch, capture result, combat end messages)

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
                        handle_menu_selection(menu_selected_index, player)
                
                # Handle other states and inputs here
                # ...
        
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
        elif game_state == "roaming":
            current_location = world_map.get(player.location)
            if current_location:
                draw_roaming(screen, font, player, current_location, world_map)
        elif game_state == "combat":
            # Get the active daemon and enemy for combat
            player_daemon = player.get_active_daemon()
            enemy_daemon = None  # This would be set during combat initialization
            if player_daemon and enemy_daemon:
                draw_combat(screen, font, player, player_daemon, enemy_daemon)
        
        # Display to screen
        pygame.display.flip()
        clock.tick(FPS)
    
    # When game ends, save game log
    save_game_log()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()  # This line already exists, but we need to ensure it calls a function named 'main'
else:
    # For importing, ensure the main function is available when imported
    # This way bootstrap.py can call game.main() successfully
    __all__ = ['main']  # Explicitly expose 'main' when importing this module
