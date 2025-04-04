# Assuming Location class is imported if needed for type hinting, but not strictly necessary for this structure
# from location import Location
# Assuming Daemon class is imported
from daemon import Daemon
import logging

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

    def get_healthy_daemons(self):
        """Returns a list of Daemons in the roster that are not fainted."""
        return [d for d in self.daemons if not d.is_fainted()]

    def get_first_healthy_daemon(self):
        """Returns the first available healthy Daemon or None."""
        healthy_daemons = self.get_healthy_daemons()
        return healthy_daemons[0] if healthy_daemons else None

    def display_status(self, world_map):
         """Prints the player's current status."""
         current_loc = self.get_current_location(world_map)
         location_name = current_loc.name if current_loc else "Unknown"

         print("\n--- Player Status ---")
         print(f" Name: {self.name}")
         print(f" Location: {location_name} ({self.location})")
         print(" Daemons:")
         if not self.daemons:
              print("   None")
         else:
              for i, daemon in enumerate(self.daemons):
                   status = "Active" if not daemon.is_fainted() else "Deactivated"
                   print(f"   {i+1}: {daemon.name} (Lv.{daemon.level}) - HP: {daemon.stats['hp']}/{daemon.stats['max_hp']} [{status}]")

    def display_detailed_daemons(self):
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
    def from_dict(cls, data):
        """Create player from saved dictionary"""
        from daemon import Daemon
        
        player = cls(
            data["name"],
            data["location"],
            []  # Empty daemon list to start
        )
        
        # Add daemons
        for daemon_data in data["daemons"]:
            player.daemons.append(Daemon.from_dict(daemon_data))
            
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
    print("\nHealthy Daemons:", [d.name for d in test_player.get_healthy_daemons()])
    print("\nFirst Healthy:", test_player.get_first_healthy_daemon().name if test_player.get_first_healthy_daemon() else "None")
    print("\nDetailed Daemons:")
    test_player.display_detailed_daemons()

    print("\nAttempting move...")
    test_player.move("east", test_world_map)
    test_player.display_status(test_world_map)
    test_player.move("north", test_world_map) # Invalid move
    test_player.move("west", test_world_map)
    test_player.display_status(test_world_map)
