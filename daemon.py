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
    """
    Daemon class represents a program daemon in the CNRD game.
    """
    
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
        self.types = types if isinstance(types, list) else [types]
        self.level = level
        self.base_hp = base_hp
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_speed = base_speed
        self.base_special = base_special
        self.capture_rate = capture_rate
        self.programs = programs if programs is not None else []

        # Calculate actual stats based on level
        self._calculate_stats()

        # Set current HP to max HP
        self.hp = self.max_hp

        # Experience points
        self.xp = 0
        self.xp_needed = self._calculate_xp_needed()

        # Status effect
        self.status_effect = None # e.g., "PARALYZED", "POISONED", None
        
    @classmethod
    def create_from_base(cls, base_id, level=1, custom_name=None):
        """
        Create a daemon from a base type ID.
        
        Args:
            base_id (str): The base daemon ID (e.g., "virulet", "pyrowall")
            level (int): The level for the new daemon
            custom_name (str): Optional custom name for the daemon
            
        Returns:
            Daemon: A new Daemon instance with appropriate stats and programs
        """
        # Define base stats for standard daemons
        base_stats = {
            "virulet": {
                "name": "Virulet",
                "types": ["VIRUS"],
                "base_hp": 45,
                "base_attack": 55,
                "base_defense": 40,
                "base_speed": 60,
                "base_special": 50,
                "capture_rate": 45,
                "programs": [
                    Program(1, "Data Siphon", 40, 95, "VIRUS", "damage", "Drains data from the target"),
                    Program(2, "Infect", 30, 100, "VIRUS", "special", "Infects the target with status effects")
                ]
            },
            "pyrowall": {
                "name": "Pyrowall",
                "types": ["FIREWALL"],
                "base_hp": 45, 
                "base_attack": 45,
                "base_defense": 65,
                "base_speed": 45,
                "base_special": 50,
                "capture_rate": 45,
                "programs": [
                    Program(3, "Firewall", 40, 95, "FIREWALL", "damage", "Attacks with a wall of fire"),
                    Program(4, "Defense Protocol", 0, 100, "FIREWALL", "defend", "Increases defense")
                ]
            },
            "aquabyte": {
                "name": "Aquabyte",
                "types": ["CRYPTO"],
                "base_hp": 45,
                "base_attack": 50, 
                "base_defense": 50,
                "base_speed": 50,
                "base_special": 55,
                "capture_rate": 45,
                "programs": [
                    Program(5, "Encryption", 40, 95, "CRYPTO", "damage", "Attacks with encrypted data"),
                    Program(6, "Decrypt", 30, 100, "CRYPTO", "special", "Weakens target's defenses")
                ]
            }
        }
        
        # Check if the base_id exists in our definitions
        if base_id.lower() not in base_stats:
            logging.error(f"Unknown daemon base ID: {base_id}")
            # Default to virulet if base_id not found
            base_id = "virulet"
            
        # Get the base stats for this daemon type
        stats = base_stats[base_id.lower()]
        
        # Create the daemon
        name = custom_name if custom_name else stats["name"]
        daemon = cls(
            name=name,
            types=stats["types"],
            level=level,
            base_hp=stats["base_hp"],
            base_attack=stats["base_attack"],
            base_defense=stats["base_defense"],
            base_speed=stats["base_speed"],
            base_special=stats["base_special"],
            capture_rate=stats["capture_rate"],
            programs=stats["programs"]
        )
        
        return daemon

    def add_program(self, program):
        """
        Add a program to this daemon.
        
        Args:
            program: The Program object to add to this daemon
        Returns:
            bool: True if program was added successfully
        """
        if program is None:
            raise ValueError("Cannot add None as a program")
        self.programs.append(program)
        return True

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
        """Convert daemon data to dictionary for saving"""
        programs_data = [prog.to_dict() for prog in self.programs]
        
        return {
            "name": self.name,
            "level": self.level,
            "types": self.types,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "xp": self.xp,
            "xp_next_level": self.xp_next_level,
            "programs": programs_data,
            "status_effect": self.status_effect
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create a Daemon instance from saved dictionary data"""
        from program import Program
        
        # Load programs
        programs = []
        for prog_data in data.get("programs", []):
            program = Program.from_dict(prog_data)
            programs.append(program)
        
        # Create the daemon
        daemon = cls(
            name=data.get("name", "Unknown"),
            types=data.get("types", ["NORMAL"]),
            level=data.get("level", 1),
            programs=programs
        )
        
        # Set stats directly
        daemon.hp = data.get("hp", 10)
        daemon.max_hp = data.get("max_hp", 10)
        daemon.attack = data.get("attack", 5)  
        daemon.defense = data.get("defense", 5)
        daemon.speed = data.get("speed", 5)
        daemon.xp = data.get("xp", 0)
        daemon.xp_next_level = data.get("xp_next_level", 100)
        daemon.status_effect = data.get("status_effect", None)
        
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
