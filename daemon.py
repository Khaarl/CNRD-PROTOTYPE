import random # Might need later for combat calculations, etc.

class Program:
    """Represents a single program/ability a Daemon can use."""
    def __init__(self, name, p_type, power, effect=None):
        self.name = name
        self.type = p_type # e.g., "Malware", "Encryption"
        self.power = power # Base damage/effect strength
        self.effect = effect # Optional: e.g., status change like "raise_defense"

# --- Example Basic Programs ---
# Define some programs globally or load them from data later
DATA_SIPHON = Program("Data Siphon", "Malware", 40)
FIREWALL_BASH = Program("Firewall Bash", "Shell", 35)
ENCRYPT_SHIELD = Program("Encrypt Shield", "Encryption", 0, effect="raise_defense") # Example effect


class Daemon:
    """Represents a Digital Entity (CyberPet)."""

    def __init__(self, name, types, base_stats, level=1, programs=None, xp=0):
        """
        Initializes a new Daemon.
        Args:
            name (str): The Daemon's name.
            types (list[str]): List of type strings (e.g., ["Malware", "Ghost"]).
            base_stats (dict): Dictionary of base stats like
                               {'hp': 45, 'attack': 49, 'defense': 49, 'speed': 45}.
            level (int): Starting level.
            programs (list[Program]): List of starting programs.
            xp (int): Current experience points.
        """
        self.name = name
        self.types = types
        self.level = level
        self.xp = xp
        self.base_stats = base_stats # Store base stats for recalculation if needed

        # Calculate current stats based on base and level (simplified for prototype)
        self.stats = self._calculate_stats()

        self.programs = programs if programs else []
        self.status_effect = None # e.g., "PARALYZED", None
        self.xp_next_level = self._calculate_xp_needed(self.level) # Calculate initial XP needed

    def _calculate_stats(self):
        """Calculates current stats based on base stats and level."""
        # In a full game, this would be more complex (IVs, EVs, complex formula)
        # Simple linear scaling for prototype
        stats = {
            'max_hp': self.base_stats['hp'] + (self.level * 2),
            'attack': self.base_stats['attack'] + self.level,
            'defense': self.base_stats['defense'] + self.level,
            'speed': self.base_stats['speed'] + self.level,
        }
        # Ensure current HP doesn't exceed new max HP if stats are recalculated
        current_hp = stats['max_hp'] # Default to full health
        if hasattr(self, 'stats'): # If stats already exist (e.g., level up), preserve HP ratio
            hp_ratio = self.stats['hp'] / self.stats['max_hp'] if self.stats['max_hp'] > 0 else 1
            current_hp = int(stats['max_hp'] * hp_ratio)

        stats['hp'] = current_hp
        return stats

    def _calculate_xp_needed(self, level):
        """Calculates XP needed for the next level (simple example)."""
        # Could use a standard formula like medium-fast from Pokémon, or simpler:
        return int(10 * (level ** 1.5)) # Example simple curve

    def is_fainted(self):
        """Checks if the Daemon has 0 or less HP."""
        return self.stats['hp'] <= 0

    def take_damage(self, amount):
        """Applies damage to the Daemon's HP."""
        damage = max(0, amount) # Ensure damage isn't negative
        self.stats['hp'] -= damage
        if self.stats['hp'] < 0:
            self.stats['hp'] = 0
        # print(f"{self.name} took {damage} damage! Remaining HP: {self.stats['hp']}/{self.stats['max_hp']}") # Removed print
        if self.is_fainted():
            # print(f"{self.name} has been deactivated!") # Removed print
            pass # Caller should handle messaging

    def heal(self, amount):
        """Heals the Daemon's HP."""
        heal_amount = max(0, amount)
        self.stats['hp'] += heal_amount
        if self.stats['hp'] > self.stats['max_hp']:
            self.stats['hp'] = self.stats['max_hp']
        # print(f"{self.name} recovered {heal_amount} HP. Current HP: {self.stats['hp']}/{self.stats['max_hp']}") # Removed print

    def display_summary(self):
        """Prints a basic summary of the Daemon. (Primarily for non-curses debugging)."""
        # print(f"--- {self.name} (Lv.{self.level}) ---")
        # print(f"  Type(s): {', '.join(self.types)}")
        # print(f"  HP: {self.stats['hp']}/{self.stats['max_hp']}")
        # print(f"  Stats: Atk={self.stats['attack']}, Def={self.stats['defense']}, Spd={self.stats['speed']}")
        # print(f"  XP: {self.xp}/{self.xp_next_level}")
        # program_names = [p.name for p in self.programs]
        # print(f"  Programs: {', '.join(program_names) if program_names else 'None'}")
        # if self.status_effect:
        #     print(f"  Status: {self.status_effect}")
        # print("-" * (len(self.name) + 12))
        pass # Curses UI handles display

    def add_xp(self, amount):
        """Adds XP and checks for level up."""
        if self.is_fainted(): # Can't gain XP if fainted
             # print(f"{self.name} is deactivated and cannot gain XP.") # Removed print
             return False # Indicate no XP gained
        if self.level >= 100: # Assuming level cap
             # print(f"{self.name} is at max level!") # Removed print
             return False # Indicate no XP gained

        self.xp += amount
        # print(f"{self.name} gained {amount} XP!") # Removed print
        leveled_up = False
        while self.xp >= self.xp_next_level and self.level < 100:
             self.level_up()
             leveled_up = True
        return leveled_up # Return true if a level up occurred

    def level_up(self):
        """Handles the level-up process."""
        self.level += 1
        # Remove XP needed for the level just gained
        xp_needed_for_prev_level = self.xp_next_level # Store threshold before recalculating
        self.xp -= xp_needed_for_prev_level
        if self.xp < 0: self.xp = 0 # Prevent negative XP

        # print(f"{self.name} grew to Level {self.level}!") # Removed print

        # Recalculate stats and update next level XP threshold
        old_max_hp = self.stats['max_hp']
        old_hp = self.stats['hp'] # Store current HP before recalculating stats
        new_stats = self._calculate_stats() # Calculate new stats
        hp_increase = new_stats['max_hp'] - old_max_hp
        self.stats = new_stats # Assign new stats
        # Restore HP based on the increase in max_hp, maintaining current HP if possible
        self.stats['hp'] = min(self.stats['max_hp'], old_hp + hp_increase)

        self.xp_next_level = self._calculate_xp_needed(self.level)

        # self.display_summary() # Removed print

        # Add logic here later to check for learning new programs at certain levels
        # Example: self.check_learn_new_program()
        # Return value could indicate if new program was learned

# --- Example Daemon Creation (for testing if run directly) ---
if __name__ == "__main__":
    # Base stats definition
    virulet_base = {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60}
    # Create an instance
    starter_virulet = Daemon("Virulet", ["Malware"], virulet_base, level=5, programs=[DATA_SIPHON])

    starter_virulet.display_summary()
    starter_virulet.take_damage(15)
    starter_virulet.add_xp(100) # Example XP gain
    starter_virulet.add_xp(500) # Gain more XP to test multiple level ups
    starter_virulet.take_damage(100) # Test fainting
    starter_virulet.add_xp(50) # Test no XP gain when fainted
