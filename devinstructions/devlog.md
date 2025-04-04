# CNRD Development Log

## Version 0.1.1 - Stability Update (Current)

### Bug Fixes
- Fixed crash that occurred after entering player name
- Fixed variable scope issues in game.py main() function
- Added improved error handling in data_manager.py
- Added validation to player location initialization
- Ensured all required directories exist on startup

### New Features
- Added comprehensive logging system
  - Logs stored in "logs" directory with timestamp
  - Different log levels (DEBUG, INFO, ERROR)
  - Console and file logging simultaneously
- Created bootstrap.py for safer startup
  - Global exception handling
  - Crash reporting
  - Pre-flight checks for required directories

### Technical Improvements
- Added detailed exception handling throughout the codebase
- Better validation of save/load operations
- More informative error messages for troubleshooting
- Created development log for tracking changes

## How to Run the Game

The game can be started in two ways:

1. Using bootstrap.py (recommended):
   ```
   python bootstrap.py
   ```
   This runs the game with error catching and creates all necessary directories.

2. Using game.py directly (for development):
   ```
   python game.py
   ```

## Known Issues

- Combat balance needs adjustment
- Limited set of wild Daemons available
- No inventory system implemented yet

## Future Plans

- Implement improved combat type advantages
- Add more locations and Daemons
- Add inventory and item system
- Create proper NPC trainers and dialogue system