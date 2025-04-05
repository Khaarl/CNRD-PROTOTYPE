import random
import logging
from pathlib import Path

# Type effectiveness chart 
# A value of 2.0 means super effective (double damage)
# A value of 1.0 means normal effectiveness
# A value of 0.5 means not very effective (half damage)
# A value of 0.0 means no effect
TYPE_CHART = {
    "VIRUS": {
        "VIRUS": 1.0,
        "FIREWALL": 0.5,
        "CRYPTO": 1.0,
        "TROJAN": 1.0,
        "NEURAL": 2.0,
        "SHELL": 0.5,
        "GHOST": 0.5
    },
    "FIREWALL": {
        "VIRUS": 2.0,
        "FIREWALL": 0.5,
        "CRYPTO": 0.5, 
        "TROJAN": 2.0,
        "NEURAL": 1.0,
        "SHELL": 1.0,
        "GHOST": 1.0
    },
    "CRYPTO": {
        "VIRUS": 1.0,
        "FIREWALL": 2.0,
        "CRYPTO": 0.5,
        "TROJAN": 0.5,
        "NEURAL": 1.0,
        "SHELL": 1.0,
        "GHOST": 2.0
    },
    "TROJAN": {
        "VIRUS": 1.0,
        "FIREWALL": 0.5,
        "CRYPTO": 2.0,
        "TROJAN": 0.5,
        "NEURAL": 2.0,
        "SHELL": 1.0,
        "GHOST": 0.5
    },
    "NEURAL": {
        "VIRUS": 0.5,
        "FIREWALL": 1.0,
        "CRYPTO": 1.0,
        "TROJAN": 0.5,
        "NEURAL": 1.0,
        "SHELL": 2.0,
        "GHOST": 2.0
    },
    "SHELL": {
        "VIRUS": 2.0,
        "FIREWALL": 1.0,
        "CRYPTO": 1.0,
        "TROJAN": 1.0,
        "NEURAL": 0.5,
        "SHELL": 0.5,
        "GHOST": 1.0
    },
    "GHOST": {
        "VIRUS": 2.0,
        "FIREWALL": 1.0,
        "CRYPTO": 0.5,
        "TROJAN": 2.0,
        "NEURAL": 0.5,
        "SHELL": 1.0,
        "GHOST": 1.0
    }
}

# Status effect constants
STATUS_EFFECTS = {
    "CORRUPTED": {"description": "Loses HP each turn", "duration": (2, 5)},
    "LOCKED": {"description": "Cannot act occasionally", "duration": (2, 4)},
    "OVERLOADED": {"description": "Attack reduced", "duration": (3, 6)},
    "FRAGMENTED": {"description": "Defense reduced", "duration": (3, 6)},
    "LAGGING": {"description": "Speed reduced", "duration": (3, 6)}
}

class Program:
    """A program that a daemon can use in battle"""
    
    def __init__(self, id, name, power, accuracy, program_type, effect, description):
        self.id = id
        self.name = name
        self.power = power
        self.accuracy = accuracy
        self.type = program_type
        self.effect = effect
        self.description = description
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "power": self.power,
            "accuracy": self.accuracy,
            "type": self.type,
            "effect": self.effect,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Program from a dictionary"""
        return cls(
            data["id"],
            data["name"],
            data["power"],
            data["accuracy"],
            data["type"],
            data["effect"],
            data["description"]
        )

class Daemon:
    """A daemon that can be captured and used in battle"""

    def __init__(self, name, types, level=1, base_hp=0, base_attack=0,
                 base_defense=0, base_speed=0, base_special=0, capture_rate=100, programs=None):
        """
        Initializes a new Daemon.
        Args:
            name (str): The Daemon's name.
            types (list[str]): List of type strings (e.g., ["Malware", "Ghost"]).
            level (int): Starting level.
            base_hp (int): Base HP stat.
            base_attack (int): Base Attack stat.
            base_defense (int): Base Defense stat.
            base_speed (int): Base Speed stat.
            base_special (int): Base Special stat (can represent special attack/defense).
            capture_rate (int): Base rate for capture difficulty (lower is harder).
            programs (list[Program]): List of starting programs.
        """
        self.name = name
        self.types = types # Changed from daemon_type
        self.level = level
        self.base_hp = base_hp
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_speed = base_speed
        self.base_special = base_special
        self.capture_rate = capture_rate # Added capture rate

        # Calculate actual stats based on level
        self._calculate_stats()

        # Set current HP to max HP
        self.hp = self.max_hp

        # Experience points
        self.xp = 0
        self.xp_needed = self._calculate_xp_needed()

        # Programs (moves)
        self.programs = programs if programs is not None else []

        # Status effect
        self.status_effect = None # e.g., "PARALYZED", "POISONED", None

    def _calculate_stats(self):
        """Calculate the daemon's stats based on base stats and level"""
        level_multiplier = 1 + (self.level - 1) * 0.1
        
        self.max_hp = int(self.base_hp * level_multiplier)
        self.attack = int(self.base_attack * level_multiplier)
        self.defense = int(self.base_defense * level_multiplier)
        self.speed = int(self.base_speed * level_multiplier)
        self.special = int(self.base_special * level_multiplier)

    def _calculate_xp_needed(self):
        """Calculate the XP needed for the next level"""
        # Simple formula: 100 XP for level 1, then increases by 50 each level
        return 100 + (self.level - 1) * 50
    
    def gain_xp(self, amount):
        """Gain experience points and level up if necessary"""
        self.xp += amount
        logging.info(f"{self.name} gained {amount} XP. Total: {self.xp}/{self.xp_needed}")
        
        # Check for level up
        while self.xp >= self.xp_needed:
            self.level_up()
    
    def level_up(self):
        """Level up the daemon"""
        # Subtract XP needed
        self.xp -= self.xp_needed
        
        # Increase level
        self.level += 1
        
        # Recalculate stats
        old_max_hp = self.max_hp
        old_attack = self.attack
        old_defense = self.defense
        old_speed = self.speed
        old_special = self.special
        
        self._calculate_stats()
        
        # Update XP needed for next level
        self.xp_needed = self._calculate_xp_needed()
        
        # Heal on level up
        self.hp = self.max_hp
        
        logging.info(f"{self.name} leveled up to {self.level}!")
        logging.info(f"HP: {old_max_hp} -> {self.max_hp}")
        logging.info(f"Attack: {old_attack} -> {self.attack}")
        logging.info(f"Defense: {old_defense} -> {self.defense}")
        logging.info(f"Speed: {old_speed} -> {self.speed}")
        logging.info(f"Special: {old_special} -> {self.special}")

    def is_fainted(self):
        """Checks if the Daemon has 0 or less HP."""
        return self.hp <= 0

    def take_damage(self, amount):
        """Applies damage to the Daemon's HP."""
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0
        logging.info(f"{self.name} took {amount} damage! Remaining HP: {self.hp}/{self.max_hp}")
        # Return True if fainted as a result
        return self.is_fainted()

    def display_summary(self):
        """Prints a basic summary of the Daemon."""
        print(f"--- {self.name} (Lv.{self.level}) ---")
        print(f"  Type(s): {', '.join(self.types)}")
        print(f"  HP: {self.hp}/{self.max_hp}")
        print(f"  Stats: Atk={self.attack}, Def={self.defense}, Spd={self.speed}, Spc={self.special}")
        print(f"  XP: {self.xp}/{self.xp_needed}")
        program_names = [p.name for p in self.programs]
        print(f"  Programs: {', '.join(program_names) if program_names else 'None'}")
        if self.status_effect:
            print(f"  Status: {self.status_effect}")
        print("-" * (len(self.name) + 12))

    def calculate_damage(self, program, target):
        """Calculates damage based on program, attacker, and target stats."""
        # Type effectiveness lookup
        type_effectiveness = 1.0
        for target_type in target.types:
            type_effectiveness *= TYPE_CHART.get(program.type.upper(), {}).get(target_type.upper(), 1.0)

        # STAB (Same Type Attack Bonus)
        stab_bonus = 1.5 if program.type in self.types else 1.0

        # Random variance (e.g., 85% to 100%)
        variance = random.uniform(0.85, 1.00)

        # Simplified damage formula inspired by Pokemon Gen 1-ish
        damage = (((((2 * self.level) / 5) + 2) * program.power * (self.attack / target.defense)) / 50) + 2
        damage = int(damage * stab_bonus * type_effectiveness * variance)

        return max(1, damage) # Ensure at least 1 damage

    def use_program(self, program, target):
        """
        Attempts to use a program on a target daemon.
        Returns a dictionary containing the result:
        {
            "hit": bool,
            "message": str,
            "damage": int | None,
            "effect_applied": str | None
        }
        """
        result = {
            "hit": False,
            "message": "",
            "damage": None,
            "effect_applied": None
        }

        # Check if program is known
        if program not in self.programs:
            logging.warning(f"{self.name} doesn't know the program {program.name}!")
            result["message"] = f"{self.name} doesn't know that program!"
            return result

        # Check for accuracy
        if random.randint(1, 100) > program.accuracy:
            result["message"] = f"{self.name}'s {program.name} missed!"
            return result

        result["hit"] = True
        result["message"] = f"{self.name} used {program.name}!"

        # Handle different program effects
        if program.effect == "damage":
            damage = self.calculate_damage(program, target)
            result["damage"] = damage
            # Note: Actual damage application happens via target.take_damage(damage) in the combat loop
            result["message"] += f" It dealt {damage} damage to {target.name}!"

        elif program.effect == "defend":
            # Example: Boost own defense (temporary effect handling needed in combat loop)
            # For now, just report the intention
            result["effect_applied"] = "boost_defense"
            result["message"] += f" {self.name}'s defense rose!" # Simplified message

        elif program.effect == "special":
            # Example: Lower target's attack (temporary effect handling needed)
            result["effect_applied"] = "lower_attack"
            result["message"] += f" {target.name}'s attack fell!" # Simplified message

        # TODO: Add more effects (status conditions, healing, etc.)

        else:
            logging.warning(f"Unknown program effect: {program.effect}")
            result["message"] += f" But it had an unknown effect!"
            result["hit"] = False # Treat unknown effect as failure for now

        return result

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "daemon_type": self.types[0] if len(self.types) > 0 else "UNKNOWN", # For backwards compatibility 
            "types": self.types, 
            "level": self.level,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "base_speed": self.base_speed,
            "base_special": self.base_special,
            "capture_rate": self.capture_rate, 
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "special": self.special,
            "xp": self.xp,
            "xp_needed": self.xp_needed,
            "status_effect": self.status_effect, # Fixed - was incorrectly using data.get()
            "programs": [p.to_dict() for p in self.programs]
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Daemon from a dictionary"""
        # Handle type backward compatibility (list 'types' vs string 'daemon_type')
        daemon_types = data.get("types")
        if not isinstance(daemon_types, list) or not daemon_types: # Check if 'types' is missing or not a non-empty list
            old_type = data.get("daemon_type") # Check for the old key
            if isinstance(old_type, str):
                daemon_types = [old_type] # Convert old string to list
                logging.warning(f"Loaded daemon '{data.get('name')}' using legacy 'daemon_type'. Converted to types: {daemon_types}")
            else:
                daemon_types = ["UNKNOWN"] # Default if neither is valid
                logging.error(f"Could not determine type for daemon '{data.get('name')}'. Defaulting to UNKNOWN.")

        # First create the daemon without programs
        daemon = cls(
            data["name"],
            daemon_types, # Use the determined types list
            data["level"],
            data["base_hp"],
            data["base_attack"],
            data["base_defense"],
            data["base_speed"],
            data["base_special"],
            data.get("capture_rate", 100) # Added capture rate with default
        )

        # Then add saved values that would be calculated
        daemon.hp = data["hp"]
        daemon.max_hp = data["max_hp"]
        daemon.attack = data["attack"]
        daemon.defense = data["defense"]
        daemon.speed = data["speed"]
        daemon.special = data["special"]
        daemon.xp = data["xp"]
        daemon.xp_needed = data["xp_needed"]
        daemon.status_effect = data.get("status_effect") # Added status effect

        # Add programs
        daemon.programs = [Program.from_dict(p) for p in data["programs"]]

        return daemon

# --- Example Daemon Creation (for testing if run directly) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Setup logging for testing

    # Example program definitions
    data_siphon = Program(1, "Data Siphon", 40, 90, "Malware", "damage", "Drains data from the target.")
    firewall_bash = Program(2, "Firewall Bash", 35, 95, "Shell", "damage", "Bashes the target with a firewall.")
    encrypt_shield = Program(3, "Encrypt Shield", 0, 100, "Encryption", "defend", "Raises defense by encrypting data.")
    glitch_pulse = Program(4, "Glitch Pulse", 50, 85, "Ghost", "special", "Lowers target's attack.")


    # Base stats definition
    virulet_base = {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60, 'special': 50}
    rat_bot_base = {'hp': 50, 'attack': 60, 'defense': 50, 'speed': 40, 'special': 40}

    # Create instances
    starter_virulet = Daemon("Virulet", ["Malware"], level=5, base_hp=virulet_base['hp'],
                             base_attack=virulet_base['attack'], base_defense=virulet_base['defense'],
                             base_speed=virulet_base['speed'], base_special=virulet_base['special'],
                             programs=[data_siphon, firewall_bash])

    enemy_rat_bot = Daemon("Rat Bot", ["Physical"], level=3, base_hp=rat_bot_base['hp'],
                           base_attack=rat_bot_base['attack'], base_defense=rat_bot_base['defense'],
                           base_speed=rat_bot_base['speed'], base_special=rat_bot_base['special'],
                           programs=[firewall_bash])


    print("--- Initial State ---")
    starter_virulet.display_summary()
    enemy_rat_bot.display_summary()

    print("\n--- Testing Level Up ---")
    starter_virulet.gain_xp(100) # Example XP gain
    starter_virulet.gain_xp(500) # Gain more XP to test multiple level ups

    print("\n--- Testing Combat ---")
    # Turn 1: Virulet uses Data Siphon on Rat Bot
    result1 = starter_virulet.use_program(data_siphon, enemy_rat_bot)
    print(result1["message"])
    if result1["hit"] and result1["damage"] is not None:
        enemy_rat_bot.take_damage(result1["damage"])

    enemy_rat_bot.display_summary()

    # Turn 2: Rat Bot uses Firewall Bash on Virulet
    result2 = enemy_rat_bot.use_program(firewall_bash, starter_virulet)
    print(result2["message"])
    if result2["hit"] and result2["damage"] is not None:
        starter_virulet.take_damage(result2["damage"])

    starter_virulet.display_summary()

    print("\n--- Testing Faint ---")
    # Make Rat Bot faint
    while not enemy_rat_bot.is_fainted():
         result_faint = starter_virulet.use_program(data_siphon, enemy_rat_bot)
         print(result_faint["message"])
         if result_faint["hit"] and result_faint["damage"] is not None:
              if enemy_rat_bot.take_damage(result_faint["damage"]):
                   print(f"{enemy_rat_bot.name} fainted!")
                   break # Exit loop once fainted
         elif not result_faint["hit"]:
              print("Attack missed, trying again...") # Avoid infinite loop on miss
