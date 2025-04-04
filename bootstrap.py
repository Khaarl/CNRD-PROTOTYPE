#!/usr/bin/env python3
"""
Bootstrap script for Cyberpunk NetRunner: Digital Hunters
Handles initialization, error catching, and graceful shutdowns
"""
import os
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
    directories = ["saves", "logs", "config"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logging.info(f"Created directory: {directory}")

def run_game_with_error_handling():
    """Run the game with global error handling"""
    try:
        game.main()
    except KeyboardInterrupt:
        logging.info("Game terminated by user (KeyboardInterrupt)")
    except Exception as e:
        logging.critical(f"Unhandled exception: {str(e)}")
        logging.critical(traceback.format_exc())
        
        # Create crash report
        create_crash_report(e)
        
        print("\n" + "=" * 60)
        print("The game has encountered an unexpected error and needs to close.")
        print("A crash report has been created in the 'logs' directory.")
        print("=" * 60)

def create_crash_report(exception):
    """Create a detailed crash report"""
    crash_dir = Path("logs/crashes")
    crash_dir.mkdir(exist_ok=True)
    
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
    
    logging.info(f"Crash report created: {crash_file}")

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