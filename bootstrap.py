#!/usr/bin/env python3
"""
Bootstrap script for Cyberpunk NetRunner: Digital Hunters
Handles initialization, error catching, and graceful shutdowns
"""
import os
import sys
import traceback
from datetime import datetime

def ensure_directories_exist():
    """Create necessary directories if they don't exist"""
    dirs = ["logs", "saves", "data", "devinstructions"]
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log unhandled exceptions"""
    # Skip KeyboardInterrupt handling
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    # Log the error
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    crash_log = os.path.join(log_dir, f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    with open(crash_log, "w") as f:
        f.write(f"=== CNRD CRASH REPORT - {error_time} ===\n\n")
        f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        f.write("\n\n=== END OF CRASH REPORT ===\n")
    
    print(f"\n\n!!! CRITICAL ERROR !!!")
    print(f"The game encountered an unexpected error and must shut down.")
    print(f"Error type: {exc_type.__name__}")
    print(f"Error details: {exc_value}")
    print(f"\nA crash log has been written to: {crash_log}")
    print("Please report this issue with the crash log attached.")
    print("Press Enter to exit...")
    input()  # Wait for Enter press before closing

def start_game():
    """Initialize and launch the game with error handling"""
    print("Initializing Cyberpunk NetRunner: Digital Hunters...")
    
    try:
        # Set up global exception handler
        sys.excepthook = handle_exception
        
        # Ensure necessary directories exist
        ensure_directories_exist()
        
        # Import and start the main game
        from game import main
        main()
        
    except ImportError as e:
        print(f"Failed to import required module: {e}")
        print("Make sure all game files are in the correct location.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Unhandled error during initialization: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    start_game()