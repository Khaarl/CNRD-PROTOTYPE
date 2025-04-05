#!/usr/bin/env python3
"""
Bootstrap script for Cyberpunk NetRunner: Digital Hunters
Handles initialization, error catching, and graceful shutdowns
"""
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path

import game

def setup_logging():
    """Setup logging to both console and file"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"cnrd_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Logging initialized")
    return log_file

def ensure_directories_exist():
    """Ensure all required directories exist"""
    directories = ["saves", "logs", "config", "logs/crashes"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True, parents=True)
            logging.info(f"Created directory: {directory}")

def run_game_with_error_handling():
    """Run the game with error handling and crash reporting."""
    try:
        # Fix: Import game module and call the 'main' function that exists
        import game
        # The game.py has a function named 'main', not a class, so call it directly
        game.main()
    except KeyboardInterrupt:
        logging.info("Game interrupted by user (CTRL+C)")
        print("\nGame terminated by user.")
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        print("\n" + "!" * 60)
        print("CRITICAL ERROR: The game has encountered an unhandled exception.")
        print("Creating crash report and terminating...")
        print("!" * 60)
        create_crash_report(e)
        sys.exit(1)

def create_crash_report(exception):
    """Create a detailed crash report"""
    crash_dir = Path("logs/crashes")
    crash_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_file = crash_dir / f"crash_{timestamp}.txt"
    
    with open(crash_file, 'w') as f:
        f.write("=" * 50 + "\n")
        f.write("CNRD CRASH REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python version: {sys.version}\n\n")
        
        f.write("Exception details:\n")
        f.write(f"Type: {type(exception).__name__}\n")
        f.write(f"Message: {str(exception)}\n\n")
        
        f.write("Traceback:\n")
        f.write(traceback.format_exc())
        
        # Add combat state information if available
        try:
            f.write("\nGame State Information:\n")
            game_state_info = get_game_state_info()
            for key, value in game_state_info.items():
                f.write(f"{key}: {value}\n")
        except Exception as e:
            f.write(f"\nFailed to collect game state info: {e}\n")
    
    logging.info(f"Crash report created: {crash_file}")

def get_game_state_info():
    """Collect relevant game state information for crash reports"""
    info = {}
    
    # Try to access game module attributes safely
    try:
        if hasattr(game, 'game_state'):
            info['game_state'] = getattr(game, 'game_state')
        
        # Check if we're in combat
        if hasattr(game, 'current_enemy_daemon') and getattr(game, 'current_enemy_daemon'):
            enemy = getattr(game, 'current_enemy_daemon')
            info['in_combat'] = True
            info['enemy_daemon'] = f"{enemy.name} (Lv.{enemy.level})"
            info['enemy_hp'] = f"{enemy.hp}/{enemy.max_hp}"
        else:
            info['in_combat'] = False
            
        # Check if in training mode
        if hasattr(game, 'is_training_battle'):
            info['training_mode'] = getattr(game, 'is_training_battle', False)
            
    except Exception as e:
        info['error_collecting'] = str(e)
    
    return info

def main():
    """Main bootstrap function"""
    # Setup logging first
    log_file = setup_logging()
    
    logging.info("Starting CNRD bootstrap process")
    
    # Pre-flight checks
    ensure_directories_exist()
    
    # Run game with error handling
    run_game_with_error_handling()
    
    logging.info("Game execution completed")

if __name__ == "__main__":
    main()