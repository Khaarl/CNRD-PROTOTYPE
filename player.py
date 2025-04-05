import logging
import json
import os
import random
from pathlib import Path
# Import daemon module components when needed to avoid circular imports

class Player:
    """Player class representing the user in the CNRD game."""

    def __init__(self, name, start_location_id="Home", daemons=None):
        """
        Initializes the Player.
        Args:
            name (str): Player's chosen name.
            start_location_id (str): The ID of the starting location.
            daemons (list): List of Daemon objects the player owns.
        """
        self.name = name
        self.current_location = start_location_id  # Store location ID directly
        self.daemons = daemons if daemons is not None else []
        self.credits = 1000  # Starting money
        self.items = []      # Inventory items
        
    def create_starter_daemon(self, daemon_type):
        """Create a starter daemon of the specified type"""
        from daemon import Daemon
        return Daemon.create_from_base(daemon_type, level=5)
        
    def get_current_location(self, world_map):
        """Get the current Location object from the world map"""
        if self.current_location in world_map:
            return world_map[self.current_location]
        return None
        
    def move(self, direction, world_map):
        """Move the player in the specified direction"""
        current_loc = self.get_current_location(world_map)
        if not current_loc:
            print("Error: You're in an invalid location.")
            return False
            
        direction = direction.lower()
        if direction in current_loc.exits:
            self.current_location = current_loc.exits[direction]
            return True
        else:
            print(f"You can't go {direction} from here.")
            return False
            
    def add_daemon(self, daemon_instance):
        """Add a daemon to the player's collection"""
        if daemon_instance:
            self.daemons.append(daemon_instance)
            return True
        return False
        
    def get_active_daemon(self):
        """Get the player's active daemon (first in the list)"""
        if self.daemons:
            return self.daemons[0]
        return None
        
    def set_active_daemon(self, daemon_to_set):
        """Set a daemon as the active daemon (moves to front of list)"""
        if daemon_to_set in self.daemons:
            self.daemons.remove(daemon_to_set)
            self.daemons.insert(0, daemon_to_set)
            return True
        return False
        
    def heal_all_daemons(self):
        """Fully restore HP for all daemons"""
        for daemon in self.daemons:
            daemon.hp = daemon.max_hp
            
    def get_healthy_daemons(self, exclude=None):
        """Get all daemons with HP > 0, optionally excluding one"""
        return [d for d in self.daemons if d != exclude and d.hp > 0]
        
    def display_status(self, world_map=None):
        """Display player status information"""
        print(f"\n=== {self.name}'s Status ===")
        if world_map:
            current_loc = self.get_current_location(world_map)
            if current_loc:
                print(f"Location: {current_loc.name}")
                
        # Display active daemon
        active_daemon = self.get_active_daemon()
        if active_daemon:
            print(f"Active Daemon: {active_daemon.name} (Lv.{active_daemon.level})")
            
        # Display party summary
        print(f"Party: {len(self.daemons)} daemon(s)")
        for i, daemon in enumerate(self.daemons):
            status = "OK" if daemon.hp > 0 else "FAINTED"
            print(f"  {i+1}. {daemon.name} (Lv.{daemon.level}) - HP: {daemon.hp}/{daemon.max_hp} - {status}")
            
    def display_daemons_detailed(self):
        """Display detailed information about all daemons"""
        if not self.daemons:
            print("You don't have any daemons yet.")
            return
            
        for daemon in self.daemons:
            daemon.display_summary()
            
    def to_dict(self):
        """Convert player data to dictionary for saving"""
        # Convert daemons to dictionaries
        daemons_data = [daemon.to_dict() for daemon in self.daemons]
        
        # Create the player data dictionary
        player_data = {
            "name": self.name,
            "location": self.current_location,
            "daemons": daemons_data,
            "items": self.items,
            "credits": self.credits
        }
        
        return player_data
        
    @classmethod
    def from_dict(cls, data, world_locations):
        """Create a Player instance from saved dictionary data"""
        from daemon import Daemon
        
        # Create the player
        player = cls(data['name'], data['location'])
        
        # Load player's daemons
        for daemon_data in data.get('daemons', []):
            daemon = Daemon.from_dict(daemon_data)
            player.daemons.append(daemon)
            
        # Load inventory items
        if 'items' in data:
            player.items = data['items']
            
        # Load credits
        if 'credits' in data:
            player.credits = data['credits']
            
        return player
        
    def get_last_active_daemon(self):
        """Get the last non-fainted daemon"""
        for daemon in self.daemons:
            if daemon.hp > 0:
                return daemon
        return None

# --- Example Player Creation (for testing if run directly) ---
if __name__ == "__main__":
    # Need dummy Location and Daemon classes/objects for testing here
    class DummyLocation:
        def __init__(self, id, name, exits):
            self.id = id
            self.name = name
            self.exits = exits
    class DummyDaemon:
        def __init__(self, name, level, hp, max_hp):
            self.name = name
            self.level = level
            self.stats = {'hp': hp, 'max_hp': max_hp, 'attack': 10, 'defense': 10, 'speed': 10}
            self.types = ["Test"]
            self.xp = 0
            self.xp_next_level = 100
            self.programs = []
            self.status_effect = None
        def is_fainted(self): return self.stats['hp'] <= 0
        def display_summary(self): print(f"Summary for {self.name} Lv.{self.level}")

    # Dummy world map
    test_world_map = {
        "start": DummyLocation("start", "Starting Area", {"east": "next"}),
        "next": DummyLocation("next", "Next Area", {"west": "start"})
    }

    # Create player
    test_player = Player("Tester", "start")

    # Add dummy daemons
    d1 = DummyDaemon("TestBot1", 5, 25, 25)
    d2 = DummyDaemon("TestBot2", 3, 0, 20) # Fainted
    test_player.add_daemon(d1)
    test_player.add_daemon(d2)

    # Test methods
    test_player.display_status(test_world_map)
    print("\nHealthy Daemons:", [(d.name, d.stats['hp']) for d in test_player.get_healthy_daemons()])
    active = test_player.get_active_daemon()
    print("\nActive Daemon:", active.name if active else "None")
    print("\nDetailed Daemons:")
    test_player.display_daemons_detailed() # Use renamed method

    print("\nSetting d1 as active...")
    test_player.set_active_daemon(d1)
    active = test_player.get_active_daemon()
    print("New Active Daemon:", active.name if active else "None")
    print("Party order:", [d.name for d in test_player.daemons])

    print("\nAttempting move...")
    test_player.move("east", test_world_map)
    test_player.display_status(test_world_map)
    test_player.move("north", test_world_map) # Invalid move
    test_player.move("west", test_world_map)
    test_player.display_status(test_world_map)
