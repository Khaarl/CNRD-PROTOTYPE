import random
import logging

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
    
    def __init__(self, name, daemon_type, level=1, base_hp=0, base_attack=0, 
                 base_defense=0, base_speed=0, base_special=0, programs=None):
        self.name = name
        self.daemon_type = daemon_type
        self.level = level
        self.base_hp = base_hp
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_speed = base_speed
        self.base_special = base_special
        
        # Calculate actual stats based on level
        self._calculate_stats()
        
        # Set current HP to max HP
        self.hp = self.max_hp
        
        # Experience points
        self.xp = 0
        self.xp_needed = self._calculate_xp_needed()
        
        # Programs (moves)
        self.programs = programs if programs is not None else []
    
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
    
    def use_program(self, program, target):
        """Use a program on a target daemon"""
        # Check if program is one of this daemon's programs
        if program not in self.programs:
            logging.warning(f"{self.name} doesn't know the program {program.name}!")
            return False, f"{self.name} doesn't know that program!"
        
        # Check for accuracy
        hit = random.randint(1, 100) <= program.accuracy
        
        if not hit:
            return False, f"{self.name}'s {program.name} missed!"
        
        # Handle different program effects
        if program.effect == "damage":
            # Calculate damage
            type_bonus = 1.0
            if program.type == self.daemon_type:
                type_bonus = 1.5  # STAB (Same Type Attack Bonus)
            
            damage = int((self.attack * program.power / 100) * type_bonus)
            
            # Apply damage
            target.hp -= damage
            if target.hp < 0:
                target.hp = 0
            
            return True, f"{self.name} used {program.name} and dealt {damage} damage to {target.name}!"
            
        elif program.effect == "defend":
            # For simplicity, just a temporary defense boost
            self.defense += int(self.defense * 0.2)  # 20% boost
            
            return True, f"{self.name} used {program.name} and boosted its defense!"
            
        elif program.effect == "special":
            # For simplicity, lower target's attack
            target.attack = int(target.attack * 0.8)  # 20% reduction
            
            return True, f"{self.name} used {program.name} and lowered {target.name}'s attack!"
            
        else:
            return False, f"Unknown program effect: {program.effect}"
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "daemon_type": self.daemon_type,
            "level": self.level,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "base_speed": self.base_speed,
            "base_special": self.base_special,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "special": self.special,
            "xp": self.xp,
            "xp_needed": self.xp_needed,
            "programs": [p.to_dict() for p in self.programs]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Daemon from a dictionary"""
        # First create the daemon without programs
        daemon = cls(
            data["name"],
            data["daemon_type"],
            data["level"],
            data["base_hp"],
            data["base_attack"],
            data["base_defense"],
            data["base_speed"],
            data["base_special"]
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
        
        # Add programs
        daemon.programs = [Program.from_dict(p) for p in data["programs"]]
        
        return daemon

# --- Example Daemon Creation (for testing if run directly) ---
if __name__ == "__main__":
    # Example program definitions
    data_siphon = Program(1, "Data Siphon", 40, 90, "Malware", "damage", "Drains data from the target.")
    firewall_bash = Program(2, "Firewall Bash", 35, 95, "Shell", "damage", "Bashes the target with a firewall.")
    encrypt_shield = Program(3, "Encrypt Shield", 0, 100, "Encryption", "defend", "Raises defense by encrypting data.")
    
    # Base stats definition
    virulet_base = {'hp': 40, 'attack': 55, 'defense': 40, 'speed': 60, 'special': 50}
    # Create an instance
    starter_virulet = Daemon("Virulet", "Malware", level=5, base_hp=virulet_base['hp'], 
                             base_attack=virulet_base['attack'], base_defense=virulet_base['defense'], 
                             base_speed=virulet_base['speed'], base_special=virulet_base['special'], 
                             programs=[data_siphon, firewall_bash])

    starter_virulet.gain_xp(100) # Example XP gain
    starter_virulet.gain_xp(500) # Gain more XP to test multiple level ups
    starter_virulet.use_program(data_siphon, starter_virulet) # Test program usage
