# Assuming Location class is imported if needed for type hinting, but not strictly necessary for this structure
# from location import Location
# Assuming Daemon class is imported
from daemon import Daemon

class Player:
    """Represents the player character."""
    def __init__(self, name, start_location_id, world_map):
        """
        Initializes the Player.
        Args:
            name (str): Player's chosen name.
            start_location_id (str): The ID of the starting location.
            world_map (dict): The dictionary mapping location IDs to Location objects.
        """
        self.name = name
        self.current_location_id = start_location_id
        self.daemons = [] # List of Daemon objects the player owns
        # Add inventory, currency, etc. later
        # self.inventory = {}
        # self.creds = 100

    def get_current_location(self, world_map):
        """Returns the Location object corresponding to the player's current location ID."""
        return world_map.get(self.current_location_id)

    def move(self, direction, world_map):
        """Attempts to move the player in a given direction."""
        current_loc = self.get_current_location(world_map)
        if not current_loc:
            print("Error: Player's current location not found in world map.")
            return False # Cannot move if current location is invalid

        if direction in current_loc.exits:
            destination_id = current_loc.exits[direction]
            # Check if the destination exists in the map *after* confirming the exit exists
            if destination_id in world_map:
                self.current_location_id = destination_id
                # print(f"You move {direction}.") # Removed print for curses compatibility
                # Return True to indicate successful movement, potentially triggering encounters
                return True
            else:
                # This case means the exit points to a non-existent location ID
                # print(f"Error: Destination location ID '{destination_id}' not found.") # Keep print for critical errors? Or log?
                return False
        else:
            # This means the direction itself is not a valid exit from the current location
            # print("You can't go that way.") # Removed print for curses compatibility
            return False

    def add_daemon(self, daemon_instance):
        """Adds a Daemon instance to the player's roster."""
        # Add checks for roster size limit later
        if isinstance(daemon_instance, Daemon):
            self.daemons.append(daemon_instance)
            # print(f"{daemon_instance.name} added to your roster.") # Removed print for curses compatibility
            # Caller should add message to log if needed
        else:
            # print("Error: Attempted to add invalid object as Daemon.") # Removed print
            # Consider logging this error differently
            pass # Or raise an error

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
         print(f" Location: {location_name} ({self.current_location_id})")
         # print(f" Creds: {self.creds}") # Future addition
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
    test_player = Player("Tester", "start", test_world_map)

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
