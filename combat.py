import random
import logging
import time

class Combat:
    """Handles combat encounters between player and opponent daemons."""
    
    def __init__(self, player_daemon, opponent_daemon):
        """Initialize combat."""
        self.player_daemon = player_daemon
        self.opponent_daemon = opponent_daemon
        self.turn = 0
        self.is_wild = True  # Flag to determine if this is a wild encounter
        self.is_training = False  # Flag to determine if this is a training session
        
        logging.info(f"Combat started: Player vs {opponent_daemon.name} (Lv.{opponent_daemon.level})")
        print(f"Combat started: Player vs {opponent_daemon.name} (Lv.{opponent_daemon.level})")
    
    def start(self, player_daemons):
        """Start combat and process turns until it's over."""
        print(f"\n!!!!!!!!!! Wild {self.opponent_daemon.name} (Lv.{self.opponent_daemon.level}) appeared! !!!!!!!!!!")
        print(f"Go, {self.player_daemon.name}!")
        
        # Combat loop
        while True:
            self.turn += 1
            
            # Display combat status
            self._display_status()
            
            # Player's turn
            if self._player_turn(player_daemons):
                break
            
            # Check if combat is over
            if self.opponent_daemon.is_fainted():
                print(f"{self.opponent_daemon.name} has been defeated!")
                self._handle_victory()
                break
            
            # Opponent's turn
            if self._opponent_turn():
                break
            
            # Check if combat is over
            if self.player_daemon.is_fainted():
                # Check if player has any healthy daemons left
                has_healthy = False
                for daemon in player_daemons:
                    if not daemon.is_fainted():
                        has_healthy = True
                        break
                
                if has_healthy:
                    print(f"{self.player_daemon.name} has been defeated! Choose another daemon!")
                    # Switch daemon logic would go here
                    # For now, just end combat
                    print("All your daemons have been defeated!")
                    return False
                else:
                    print("All your daemons have been defeated!")
                    return False
    
    def _display_status(self):
        """Display the current combat status."""
        print("\n" + "-" * 20)
        print(f"Enemy: {self.opponent_daemon.name} (Lv.{self.opponent_daemon.level}) HP: {self.opponent_daemon.hp}/{self.opponent_daemon.max_hp}")
        print(f"Your : {self.player_daemon.name} (Lv.{self.player_daemon.level}) HP: {self.player_daemon.hp}/{self.player_daemon.max_hp}")
        print("-" * 20)
    
    def _player_turn(self, player_daemons):
        """Handle player's turn."""
        valid_choice = False
        
        while not valid_choice:
            print("\nChoose action:")
            print("  [F]ight")
            print("  [S]witch Daemon")
            print("  [C]apture")
            print("  [R]un")
            
            action = input("> ").upper()
            
            if action == 'F':
                # Check if the daemon has any programs
                if not self.player_daemon.programs or len(self.player_daemon.programs) == 0:
                    print("No programs available! Your daemon can't attack!")
                    return False
                
                # Display available programs
                print("Choose program:")
                for i, program in enumerate(self.player_daemon.programs):
                    print(f"  [{i+1}] {program.name} ({program.program_type}, Power: {program.power}, Acc: {program.accuracy}%)")
                
                try:
                    prog_choice = int(input("> ")) - 1
                    if 0 <= prog_choice < len(self.player_daemon.programs):
                        selected_program = self.player_daemon.programs[prog_choice]
                        
                        # Use the program
                        result = self.player_daemon.use_program(selected_program, self.opponent_daemon)
                        
                        if result["hit"]:
                            if "damage" in result:
                                print(f"{self.player_daemon.name} used {selected_program.name} and dealt {result['damage']} damage!")
                            if "effect" in result:
                                print(f"{result['effect']}")
                        else:
                            print(f"{self.player_daemon.name}'s {selected_program.name} missed!")
                        
                        valid_choice = True
                    else:
                        print("Invalid program choice.")
                except (ValueError, IndexError):
                    print("Invalid input. Please enter a number.")
            
            elif action == 'S':
                # List healthy daemons
                healthy_daemons = [d for d in player_daemons if not d.is_fainted() and d != self.player_daemon]
                
                if not healthy_daemons:
                    print("No other healthy daemons available to switch to!")
                    continue
                
                print("Choose daemon to switch to:")
                for i, daemon in enumerate(healthy_daemons):
                    print(f"  [{i+1}] {daemon.name} (Lv.{daemon.level}) HP: {daemon.hp}/{daemon.max_hp}")
                
                try:
                    daemon_choice = int(input("> ")) - 1
                    if 0 <= daemon_choice < len(healthy_daemons):
                        old_daemon = self.player_daemon
                        self.player_daemon = healthy_daemons[daemon_choice]
                        print(f"Switched from {old_daemon.name} to {self.player_daemon.name}!")
                        valid_choice = True
                    else:
                        print("Invalid daemon choice.")
                except (ValueError, IndexError):
                    print("Invalid input. Please enter a number.")
            
            elif action == 'C':
                if not self.is_wild:
                    print("You can't capture trained daemons!")
                    continue
                
                # Capture logic would go here
                print("Attempting to capture daemon...")
                capture_chance = self._calculate_capture_chance()
                
                if random.random() < capture_chance:
                    print(f"Successfully captured {self.opponent_daemon.name}!")
                    return True
                else:
                    print(f"Failed to capture {self.opponent_daemon.name}!")
                    valid_choice = True
            
            elif action == 'R':
                # Try to run
                if self._try_to_run():
                    print("Got away safely!")
                    return True
                else:
                    print("Couldn't escape!")
                    valid_choice = True
            
            else:
                print("Invalid choice.")
        
        return False
    
    def _opponent_turn(self):
        """Handle opponent's turn."""
        if not self.opponent_daemon.programs or len(self.opponent_daemon.programs) == 0:
            print(f"{self.opponent_daemon.name} has no programs and can't attack!")
            return False
        
        # Choose a random program
        program = random.choice(self.opponent_daemon.programs)
        
        # Use the program
        result = self.opponent_daemon.use_program(program, self.player_daemon)
        
        if result["hit"]:
            if "damage" in result:
                print(f"{self.opponent_daemon.name} used {program.name} and dealt {result['damage']} damage!")
            if "effect" in result:
                print(f"{result['effect']}")
        else:
            print(f"{self.opponent_daemon.name}'s {program.name} missed!")
        
        time.sleep(1)  # Short delay for better readability
        return False
    
    def _calculate_capture_chance(self):
        """Calculate chance of capturing the opponent daemon."""
        # Base formula: (captureRate * (3*maxHP - 2*currentHP)) / (3*maxHP)
        max_hp = self.opponent_daemon.max_hp
        current_hp = self.opponent_daemon.hp
        base_rate = getattr(self.opponent_daemon, 'capture_rate', 100)  # Default to 100 if not set
        
        # HP factor ranges from 1/3 (full HP) to ~1 (almost fainted)
        hp_factor = (max_hp * 3 - current_hp * 2) / (max_hp * 3)
        
        # Status effects increase capture chance
        status_bonus = 1.0
        if self.opponent_daemon.status_effect == "LOCKED":
            status_bonus = 2.0
        elif self.opponent_daemon.status_effect in ["CORRUPTED", "FRAGMENTED"]:
            status_bonus = 1.5
        
        # Calculate final chance (capped at 1.0)
        chance = min(1.0, (base_rate / 255) * hp_factor * status_bonus)
        
        logging.info(f"Capture chance calculated: {chance:.2f} (base_rate={base_rate}, hp_factor={hp_factor:.2f}, status={self.opponent_daemon.status_effect})")
        return chance
    
    def _try_to_run(self):
        """Try to run from combat."""
        # Base chance is 90%
        chance = 0.9
        
        # Modify based on speed comparison
        if hasattr(self.player_daemon, 'speed') and hasattr(self.opponent_daemon, 'speed'):
            speed_ratio = self.player_daemon.speed / max(1, self.opponent_daemon.speed)
            chance *= speed_ratio
        
        # Cap at 100% and minimum of 10%
        chance = min(1.0, max(0.1, chance))
        
        logging.info(f"Run attempt: chance={chance:.2f}")
        return random.random() < chance
    
    def _handle_victory(self):
        """Handle victory consequences (XP gain, etc.)."""
        # Calculate XP gain
        xp_gain = self.opponent_daemon.level * 15
        original_level = self.player_daemon.level
        
        self.player_daemon.gain_xp(xp_gain)
        
        print(f"{self.player_daemon.name} gained {xp_gain} XP!")
        
        if self.player_daemon.level > original_level:
            print(f"{self.player_daemon.name} leveled up to level {self.player_daemon.level}!")
            
            # Calculate new stats
            self.player_daemon._calculate_stats()
            
            # Heal up after leveling
            self.player_daemon.hp = self.player_daemon.max_hp
    
    @staticmethod
    def create_training_combat(player_daemon, opponent_type, difficulty):
        """Create a training combat session."""
        from daemon import Daemon
        
        # Map difficulty to level range
        level_ranges = {
            "easy": (1, 3),
            "medium": (4, 7),
            "hard": (8, 12)
        }
        
        difficulty = difficulty.lower()
        if difficulty not in level_ranges:
            difficulty = "medium"
        
        min_level, max_level = level_ranges[difficulty]
        level = random.randint(min_level, max_level)
        
        # Basic stats for training opponent
        base_stats = {
            "hp": 15 + level * 2,
            "attack": 10 + level,
            "defense": 10 + level,
            "speed": 10 + level,
            "special": 10 + level
        }
        
        # Create programs for the opponent
        programs = []
        from daemon import Program
        
        # Basic attack program based on type
        attack_program = Program(
            name=f"{opponent_type.capitalize()} Strike",
            power=35 + level * 2,
            accuracy=90,
            program_type=opponent_type.upper(),
            effect="damage"
        )
        programs.append(attack_program)
        
        # Status effect program for higher levels
        if level > 3:
            effect_program = Program(
                name=f"{opponent_type.capitalize()} Debuff",
                power=0,
                accuracy=75,
                program_type=opponent_type.upper(),
                effect="status:CORRUPTED"
            )
            programs.append(effect_program)
        
        # Create the opponent daemon
        opponent = Daemon(
            name=opponent_type,
            level=level,
            types=[opponent_type.upper()],
            base_stats=base_stats,
            programs=programs
        )
        
        # Create the combat
        combat = Combat(player_daemon, opponent)
        combat.is_wild = False
        combat.is_training = True
        
        logging.info(f"Training combat initiated with {opponent_type} (Level {level})")
        print(f"Training combat initiated with {opponent_type} (Level {level})")
        
        return combat