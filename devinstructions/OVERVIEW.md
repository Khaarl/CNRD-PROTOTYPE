# CNRD Project: Code Architecture Overview

## Project Structure

The Cyberpunk NetRunner: Digital Hunters (CNRD) game follows a modular architecture with several key components:

```
CNRD PROTOTYPE/
├── bootstrap.py        # Entry point with error handling and logging setup
├── game.py             # Main game loop and core gameplay functions
├── daemon.py           # Daemon class and battle mechanics
├── player.py           # Player class and player-related functionality
├── location.py         # Location class and world navigation
├── data_manager.py     # Data loading, saving, and validation
├── config/             # Configuration files (JSON)
│   ├── daemons.json    # Daemon base stats and definitions
│   ├── programs.json   # Program definitions and effects
│   └── locations.json  # World map and location data
├── saves/              # Player save files
├── logs/               # Game logs
└── tests/              # Unit tests
    └── test_data_manager.py  # Tests for data validation
```

## Core Systems

### 1. Bootstrapping and Initialization

The game uses a bootstrap pattern for startup:

- **bootstrap.py**: Handles initialization, sets up logging, creates required directories, and provides global error catching.
- **Initialization Flow**:
  1. Setup logging (both console and file)
  2. Ensure required directories exist
  3. Initialize game data through `game.initialize_game()`
  4. Run main game loop with error handling

### 2. Data Management and Persistence

#### Config System

- **data_manager.py**: Central module for all data loading, saving, and validation
- **Configuration Files**: JSON-based configs for game data
  - Default configs are created if they don't exist
  - Loaded configs are validated against schemas
  - Failed validations fall back to default data

#### Schema Validation

Robust JSON schema validation system:
- Validates type constraints (string, number, boolean, etc.)
- Enforces required properties
- Validates nested structures (objects within objects, arrays)
- Provides detailed error messages with context

```python
# Schema example for daemons
DAEMON_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "hp": {"type": "number"},
        "attack": {"type": "number"},
        "defense": {"type": "number"},
        "speed": {"type": "number"},
        "special": {"type": "number"},
        "programs": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["type", "hp", "attack", "defense", "speed", "special", "programs"]
}
```

#### Save/Load System

- Player progress is saved to JSON files in the `saves/` directory
- Supports multiple save files through player-named files
- Serialization/deserialization through to_dict/from_dict methods

### 3. World Navigation System

#### Location Management

- **location.py**: Defines the Location class that represents areas in the game world
- World structure is a graph of connected locations:
  - Each location has a unique ID
  - Locations store exits as a dictionary of {direction: destination_id}
  - Movement is handled by updating player.location to a new location ID

```python
# Example location structure
{
    "central_hub": {
        "name": "Central Network Hub",
        "description": "The main connection point for the city's networks",
        "encounter_rate": 40,
        "exits": {
            "west": "uptown",
            "south": "downtown",
            "north": "daemon_lab"
        }
    }
}
```

#### Path Navigation

- Player movement uses the exit dictionary from current location
- Command parsing in game.py handles "go [direction]" commands
- Valid paths are determined by the exits available in the current location
- Error handling prevents movement in invalid directions

### 4. Daemon and Combat System

#### Daemon Class (daemon.py)

- Represents capturable entities with:
  - Base stats scaled by level
  - Types (affecting combat effectiveness)
  - Programs (moves that can be used in battle)
  - Status effects
  - XP and leveling system

#### Type System

- Type chart defines effectiveness multipliers between different daemon types
- Combat damage calculation incorporates:
  - Type effectiveness
  - STAB (Same Type Attack Bonus)
  - Random variance
  - Stat-based calculations

```python
# Type chart excerpt
TYPE_CHART = {
    "VIRUS": {
        "VIRUS": 1.0,
        "FIREWALL": 0.5,
        "CRYPTO": 1.0,
        ...
    },
    ...
}
```

#### Combat Loop

- Turn-based system similar to classic RPGs
- Determines action order based on speed stats
- Handles various actions: fight, switch daemon, use items, run
- Status effects influence combat options and outcomes

### 5. Error Handling and Logging

- Comprehensive logging throughout the codebase
- Multiple log levels (DEBUG, INFO, ERROR)
- Log output to both console and dated log files
- Crash reporting system in bootstrap.py creates detailed error reports

## Database Architecture

The game uses a file-based "database" using JSON:

### Core Data Files

1. **daemons.json**: Stores base stats for all daemon types
   ```json
   {
     "virulet": {
       "type": "VIRUS",
       "hp": 20,
       "attack": 12,
       "defense": 8,
       "speed": 10,
       "special": 9,
       "programs": ["DATA_SIPHON", "ENCRYPT_SHIELD"]
     },
     ...
   }
   ```

2. **programs.json**: Defines all available programs/moves
   ```json
   {
     "DATA_SIPHON": {
       "name": "Data Siphon",
       "power": 40,
       "accuracy": 95,
       "type": "VIRUS",
       "effect": "damage",
       "description": "Siphons data from the target causing damage"
     },
     ...
   }
   ```

3. **locations.json**: Defines the world map
   ```json
   {
     "start_location": "home",
     "locations": {
       "home": {
         "name": "Home Terminal",
         "description": "Your personal terminal.",
         "encounter_rate": 0,
         "exits": {
           "east": "downtown"
         }
       },
       ...
     }
   }
   ```

### Save File Structure

Player save files include:
- Player information (name, location)
- Captured daemons with all their stats
- Progress markers

### Data Flow

1. **Bootstrap**: Ensures config directory exists
2. **Loading**: data_manager.py loads and validates all config files
3. **Runtime**: Game operates on in-memory objects
4. **Persistence**: Player data is serialized back to JSON on save

## Testing Architecture

- Unit tests for data validation in tests/test_data_manager.py
- Test cases cover schema validation, JSON loading, and error handling
- Tests use a temporary directory to avoid affecting game files

## Development Roadmap

According to the development log, upcoming features include:
- Full NPC trainer system
- Inventory system with healing items and capture tools
- More sophisticated AI decision making
- Experience sharing system for inactive daemons
- Achievement tracking system

## Running the Game

The game can be started in two ways:
1. Using bootstrap.py (recommended): `python bootstrap.py`
2. Using game.py directly (for development): `python game.py`