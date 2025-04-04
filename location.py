class Location:
    """Represents a single location in the game world."""
    def __init__(self, loc_id, name, description, exits, encounter_rate=0.0, wild_daemons=None, 
                 scan_encounter_rate=None):
        """
        Initializes a new Location.
        Args:
            loc_id (str): Unique identifier for the location (e.g., "dark_alley").
            name (str): Human-readable name (e.g., "Dark Alley").
            description (str): Text description shown to the player.
            exits (dict): Dictionary mapping exit commands (e.g., "north")
                          to destination location IDs (e.g., "market_square").
            encounter_rate (float): Probability (0.0 to 1.0) of a random encounter.
            wild_daemons (list[dict]): List of possible wild Daemons in this area.
                                       Each dict specifies 'id' and level range ('min_lvl', 'max_lvl').
                                       Example: [{"id": "rat_bot", "min_lvl": 2, "max_lvl": 4}]
            scan_encounter_rate (float): Probability of encounter when scanning. Defaults to 1.5x encounter_rate.
        """
        self.id = loc_id
        self.name = name
        self.description = description
        self.exits = exits if exits else {}
        self.encounter_rate = encounter_rate
        self.wild_daemons = wild_daemons if wild_daemons else []
        
        # Set scan_encounter_rate to provided value or default to 1.5x normal encounter rate (capped at 1.0)
        if scan_encounter_rate is not None:
            self.scan_encounter_rate = scan_encounter_rate
        else:
            self.scan_encounter_rate = min(1.0, encounter_rate * 1.5)
        
        # Add potential for NPCs, items, events later
        # self.npcs = []
        # self.items = []

    def display(self):
        """Prints the location's information to the console."""
        print(f"\n=== {self.name} ===")
        print(self.description)
        exit_list = ", ".join(self.exits.keys())
        print(f"Exits: {exit_list if exit_list else 'None'}")
        # Optionally, hint at potential encounters or other details
        # if self.encounter_rate > 0:
        #     print("(You sense digital entities nearby...)")

    def get_random_wild_daemon_info(self):
        """Selects a random wild daemon entry from this location's list."""
        import random
        if not self.wild_daemons:
            return None
        return random.choice(self.wild_daemons)

# --- Example Location Creation (for testing if run directly) ---
if __name__ == "__main__":
    loc1 = Location("dark_alley", "Dark Alley", "A grimy, narrow alley.", {"north": "market_square"})
    loc2 = Location(
        "market_square",
        "Market Square",
        "Bustling with data-hawkers.",
        {"south": "dark_alley"},
        encounter_rate=0.2,
        wild_daemons=[
            {"id": "glitch_sprite", "min_lvl": 3, "max_lvl": 5},
            {"id": "rat_bot", "min_lvl": 2, "max_lvl": 4}
        ]
    )

    loc1.display()
    print("-" * 20)
    loc2.display()
    print("-" * 20)
    wild_info = loc2.get_random_wild_daemon_info()
    if wild_info:
        print(f"Potential wild daemon: {wild_info['id']} (Lv.{wild_info['min_lvl']}-{wild_info['max_lvl']})")
    else:
        print("No wild daemons defined for loc2.")
