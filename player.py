import logging
from pathlib import Path

class Player:
    """Represents the player character."""
    def __init__(self, name, start_location_id, daemons=None):
        """
        Initializes the Player.
        Args:
            name (str): Player's chosen name.
            start_location_id (str): The ID of the starting location.
            daemons (list): List of Daemon objects the player owns.
        """
        self.name = name
        self.location = start_location_id  # Store location ID directly
        self.daemons = daemons if daemons else []
        
        # No need to validate here as we're getting the location ID directly from locations.json
        # This removes the validation that was causing the crash

    def get_current_location(self, world_map):
        """Returns the Location object corresponding to the player's current location ID."""
        location = world_map.get(self.location)
        if not location:
            logging.error(f"Invalid location ID: {self.location}")
        return location

    def move(self, direction, world_map):
        """Attempts to move the player in a given direction."""
        current_loc = self.get_current_location(world_map)
        if not current_loc:
            logging.error("Error: Player's current location not found in world map.")
            print("Error: Player's current location not found in world map.")
            return False # Cannot move if current location is invalid

        if direction in current_loc.exits:
            destination_id = current_loc.exits[direction]
            if destination_id in world_map:
                self.location = destination_id
                print(f"You move {direction}.")
                # Return True to indicate successful movement, potentially triggering encounters
                return True
            else:
                # This case should ideally not happen if the world map is consistent
                logging.error(f"Error: Destination location ID '{destination_id}' not found.")
                print(f"Error: Destination location ID '{destination_id}' not found.")
                return False
        else:
            print("You can't go that way.")
            return False

    def add_daemon(self, daemon_instance):
        """Adds a Daemon instance to the player's roster."""
        from daemon import Daemon  # Import here to avoid circular imports
        if isinstance(daemon_instance, Daemon):
            self.daemons.append(daemon_instance)
            print(f"{daemon_instance.name} added to your roster.")
        else:
            import logging
            logging.error("Error: Attempted to add invalid object as Daemon.")
            print("Error: Attempted to add invalid object as Daemon.")

    def get_active_daemon(self):
        """Returns the first available healthy Daemon in the current party order, or None."""
        for d in self.daemons:
            if not d.is_fainted():
                return d
        return None

    def set_active_daemon(self, daemon_to_set):
        """Moves the specified daemon to the front of the list if it's healthy."""
        if daemon_to_set in self.daemons and not daemon_to_set.is_fainted():
            # Check if it's already the first active one
            first_active = self.get_active_daemon()
            if daemon_to_set == first_active:
                 return True # Already active, do nothing

            self.daemons.remove(daemon_to_set)
            self.daemons.insert(0, daemon_to_set)
            logging.info(f"Set {daemon_to_set.name} as the active daemon.")
            return True
        elif daemon_to_set not in self.daemons:
            logging.warning(f"Attempted to set non-existent daemon {daemon_to_set.name} as active.")
            return False
        else: # Daemon is fainted
             logging.warning(f"Attempted to set fainted daemon {daemon_to_set.name} as active.")
             print(f"{daemon_to_set.name} is unable to battle!")
             return False

    def heal_all_daemons(self):
        """Restores HP and removes status effects for all daemons."""
        logging.info(f"Healing all daemons for player {self.name}.")
        for daemon in self.daemons:
            # Use max_hp attribute which should exist after _calculate_stats
            daemon.hp = daemon.max_hp
            daemon.status_effect = None # Clear status effects too
        print("All your Daemons have been fully restored.")

    def get_healthy_daemons(self, exclude=None):
        """Returns a list of Daemons in the roster that are not fainted, optionally excluding one."""
        healthy = []
        for d in self.daemons:
            # Check if daemon is not fainted AND is not the one to exclude
            if not d.is_fainted() and d != exclude:
                healthy.append(d)
        return healthy

    # get_first_healthy_daemon is effectively replaced by get_active_daemon now
    # def get_first_healthy_daemon(self):
    #     """Returns the first available healthy Daemon or None."""
    #     healthy_daemons = self.get_healthy_daemons()
    #     return healthy_daemons[0] if healthy_daemons else None

    def display_status(self, world_map=None):
         """Prints the player's current status."""
         # world_map can be optional with a simple summary display if not provided
         if world_map:
             current_loc_obj = world_map.get(self.location) # Use .get for safety
             location_name = current_loc_obj.name if current_loc_obj else "Unknown Location"
             location_display = f" Location: {location_name} (ID: {self.location})" # Show ID too for debugging
         else:
             # Simple display without location details if world_map not provided
             location_display = f" Location ID: {self.location}"

         print("\n--- Player Status ---")
         print(f" Name: {self.name}")
         print(location_display)
         print(" Daemons:")
         if not self.daemons:
              print("   None")
         else:
              active_daemon = self.get_active_daemon() # Get the current active one
              for i, daemon in enumerate(self.daemons):
                   # Safely access stats
                   hp = daemon.hp if hasattr(daemon, 'hp') else daemon.stats.get('hp', 0) 
                   max_hp = daemon.max_hp if hasattr(daemon, 'max_hp') else daemon.stats.get('max_hp', 0)
                   status = "Fainted" if daemon.is_fainted() else "Ready"
                   active_marker = " (Active)" if daemon == active_daemon and not daemon.is_fainted() else ""
                   print(f"   {i+1}: {daemon.name} (Lv.{daemon.level}) - HP: {hp}/{max_hp} [{status}]{active_marker}")

    # Renaming this to match the command used in game.py
    def display_daemons_detailed(self):
        """Uses the Daemon's display_summary for each owned Daemon."""
        if not self.daemons:
            print("You have no Daemons.")
        else:
            print("\n--- Your Daemons ---")
            for daemon in self.daemons:
                daemon.display_summary()
                print("") # Add a newline for spacing

    def to_dict(self):
        """Convert player data to dictionary for saving"""
        return {
            "name": self.name,
            "location": self.location,
            "daemons": [daemon.to_dict() for daemon in self.daemons]
        }
    @classmethod
    def from_dict(cls, data, world_map=None): # Add world_map for potential validation if needed later
        """Create player from saved dictionary"""
        from daemon import Daemon # Keep import here

        # Use .get for safer dictionary access
        name = data.get("name", "Unnamed Player")
        location = data.get("location", None) # Get location ID

        # Validate location? For now, assume game.py handles invalid location after load
        # if world_map and location not in world_map:
        #     logging.warning(f"Loaded player location '{location}' is invalid. Resetting needed.")
        #     # Handle reset logic here or in game.py

        player = cls(
            name,
            location,
            []  # Empty daemon list to start
        )

        # Add daemons safely
        loaded_daemons_data = data.get("daemons", [])
        if isinstance(loaded_daemons_data, list):
            for daemon_data in loaded_daemons_data:
                 if isinstance(daemon_data, dict):
                      try:
                           player.daemons.append(Daemon.from_dict(daemon_data))
                      except Exception as e:
                           logging.error(f"Failed to load daemon from data: {daemon_data}. Error: {e}", exc_info=True)
                 else:
                      logging.warning(f"Skipping invalid daemon data entry: {daemon_data}")
        else:
             logging.warning(f"Invalid format for 'daemons' in save data: {loaded_daemons_data}")

        return player

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
