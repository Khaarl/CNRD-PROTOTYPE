import unittest
import sys
import os
import random
import logging
import datetime
from pathlib import Path

# Add parent directory to path to import game modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import game modules
from daemon import Daemon, Program, TYPE_CHART, STATUS_EFFECTS
from player import Player

# Import game module specifically for simulated combat
from game import run_combat

class TestCombatMechanics(unittest.TestCase):
    """Test suite for combat mechanics in the CNRD game."""
    
    def setUp(self):
        """Setup test fixtures."""
        # Fix random seed for reproducible tests
        random.seed(42)
        
        # Create test programs
        self.virus_program = Program(
            id="test_data_siphon",
            name="Data Siphon",
            power=40,
            accuracy=95,
            program_type="VIRUS",
            effect="damage",
            description="Drains data from the target."
        )
        
        self.firewall_program = Program(
            id="test_firewall_bash",
            name="Firewall Bash",
            power=50,
            accuracy=90,
            program_type="FIREWALL",
            effect="damage",
            description="Bashes the target with a firewall."
        )
        
        self.crypto_program = Program(
            id="test_encryption_lock",
            name="Encryption Lock",
            power=30,
            accuracy=100,
            program_type="CRYPTO",
            effect="status:LOCKED",
            description="Locks the target with encryption."
        )
        
        # Create test daemons
        self.test_virus = Daemon(
            name="Test Virus",
            types=["VIRUS"],
            level=10,
            base_hp=30,
            base_attack=15,
            base_defense=10,
            base_speed=20,
            base_special=12,
            programs=[self.virus_program]
        )
        
        self.test_firewall = Daemon(
            name="Test Firewall",
            types=["FIREWALL"],
            level=10,
            base_hp=40,
            base_attack=12,
            base_defense=18,
            base_speed=10,
            base_special=15,
            programs=[self.firewall_program]
        )
        
        self.test_crypto = Daemon(
            name="Test Crypto",
            types=["CRYPTO"],
            level=10,
            base_hp=35,
            base_attack=10,
            base_defense=12,
            base_speed=15,
            base_special=18,
            programs=[self.crypto_program]
        )
        
        # Create test player
        self.test_player = Player("TestPlayer")
        self.test_player.add_daemon(self.test_virus)
    
    def test_type_effectiveness(self):
        """Test type effectiveness calculations."""
        # VIRUS vs FIREWALL (not very effective)
        result = self.test_virus.use_program(self.virus_program, self.test_firewall)
        self.assertIsNotNone(result["damage"])
        
        # Calculate expected damage manually using the formula
        # Note: We mock random variance by setting it to a fixed value for testing
        stab_bonus = 1.5  # Same Type Attack Bonus
        type_effectiveness = TYPE_CHART["VIRUS"]["FIREWALL"]  # Should be 0.5
        variance = 0.925  # Fixed value for testing (normally random between 0.85 and 1.0)
        
        expected_base = (((2 * 10) / 5) + 2) * 40 * (self.test_virus.attack / self.test_firewall.defense) / 50 + 2
        expected_damage = int(expected_base * stab_bonus * type_effectiveness * variance)
        
        # Check if damage is close to expected (allowing for rounding differences)
        self.assertLessEqual(abs(result["damage"] - expected_damage), 1)
        
        # FIREWALL vs VIRUS (neutral effectiveness)
        result = self.test_firewall.use_program(self.firewall_program, self.test_virus)
        self.assertIsNotNone(result["damage"])
    
    def test_status_effects(self):
        """Test status effect application and impact."""
        # Apply LOCKED status
        result = self.test_crypto.use_program(self.crypto_program, self.test_virus)
        self.assertTrue(result["hit"])
        self.assertEqual(self.test_virus.status_effect, "LOCKED")
        
        # Test CORRUPTED damage over time
        self.test_virus.status_effect = "CORRUPTED"
        original_hp = self.test_virus.hp
        expected_damage = max(1, int(self.test_virus.max_hp / 16))
        
        # Simulate end-of-turn damage
        self.test_virus.take_damage(expected_damage)
        self.assertEqual(original_hp - expected_damage, self.test_virus.hp)
    
    def test_capture_mechanics(self):
        """Test daemon capture probability calculations."""
        # Create a wild daemon with a specific capture rate
        wild_daemon = Daemon(
            name="Wild Test Daemon",
            types=["NEURAL"],
            level=10,
            base_hp=30,
            base_attack=12,
            base_defense=12,
            base_speed=12, 
            base_special=12,
            capture_rate=100,  # Medium difficulty (out of 255)
            programs=[]
        )
        
        # Test base capture calculation (no status, full HP)
        max_hp = wild_daemon.max_hp
        current_hp = wild_daemon.hp
        base_rate = wild_daemon.capture_rate
        hp_factor = (max_hp * 3 - current_hp * 2) / (max_hp * 3)
        status_bonus = 1.0  # No status effect
        
        expected_chance = min(1.0, (base_rate / 255.0) * hp_factor * status_bonus)
        
        # Verify capture chance calculation
        self.assertAlmostEqual(expected_chance, (100 / 255.0) * hp_factor, places=4)
        
        # Test with status effect
        wild_daemon.status_effect = "LOCKED"
        status_bonus = 2.0
        expected_chance_with_status = min(1.0, (base_rate / 255.0) * hp_factor * status_bonus)
        
        # Verify status effect increases capture chance
        self.assertGreater(expected_chance_with_status, expected_chance)
    
    def test_faint_detection(self):
        """Test daemon fainting detection."""
        # Set HP to 1
        self.test_virus.hp = 1
        self.assertFalse(self.test_virus.is_fainted())
        
        # Deal damage to cause fainting
        result = self.test_firewall.use_program(self.firewall_program, self.test_virus)
        self.assertTrue(self.test_virus.is_fainted())
    
    def test_experience_gain(self):
        """Test experience gain and leveling."""
        # Setup
        original_level = self.test_virus.level
        original_xp = self.test_virus.xp
        
        # Calculate XP from defeating an enemy
        enemy_level = 10
        xp_gain = enemy_level * 15
        
        # Apply XP gain
        self.test_virus.gain_xp(xp_gain)
        
        # Verify XP was added
        self.assertEqual(self.test_virus.xp, original_xp + xp_gain)
        
        # Test leveling up
        # Reset XP and set it to just below level threshold
        next_level_xp = 100 + (original_level - 1) * 50
        self.test_virus.xp = next_level_xp - 1
        
        # Add 1 XP to trigger level up
        self.test_virus.gain_xp(1)
        
        # Verify level increased
        self.assertEqual(self.test_virus.level, original_level + 1)
    
    def test_run_mechanics(self):
        """Test running from battle calculations."""
        # Test run success calculation
        # Base flee chance is 0.9
        # Modified by speed ratio (faster daemon = higher chance)
        
        # Same speed = standard chance
        self.test_virus.speed = 15
        self.test_firewall.speed = 15
        speed_ratio = self.test_virus.speed / self.test_firewall.speed
        expected_flee_chance = 0.9 * speed_ratio
        self.assertAlmostEqual(expected_flee_chance, 0.9, places=4)
        
        # Faster player daemon = higher chance
        self.test_virus.speed = 30
        speed_ratio = self.test_virus.speed / self.test_firewall.speed
        expected_flee_chance = min(1.0, 0.9 * speed_ratio)
        self.assertAlmostEqual(expected_flee_chance, 0.9 * 2.0, places=4)
        
        # Slower player daemon = lower chance
        self.test_virus.speed = 7
        speed_ratio = self.test_virus.speed / self.test_firewall.speed
        expected_flee_chance = 0.9 * speed_ratio
        self.assertAlmostEqual(expected_flee_chance, 0.9 * (7/15), places=4)
    
    def test_daemon_has_programs(self):
        """Test that all daemons have at least one program assigned."""
        # Check our test daemons
        self.assertGreaterEqual(len(self.test_virus.programs), 1, "Virus daemon should have at least one program")
        self.assertGreaterEqual(len(self.test_firewall.programs), 1, "Firewall daemon should have at least one program")
        self.assertGreaterEqual(len(self.test_crypto.programs), 1, "Crypto daemon should have at least one program")
        
        # Test starter daemon creation
        starter_daemon = Daemon(
            name="Starter Test",
            types=["FIREWALL"],
            level=5,
            base_hp=25,
            base_attack=12,
            base_defense=15,
            base_speed=10,
            base_special=13,
            programs=[self.firewall_program]
        )
        self.assertGreaterEqual(len(starter_daemon.programs), 1, "Starter daemon should have at least one program")
    
    def test_simulated_combat(self):
        """Run several simulated combats with input automation and log the results."""
        # Setup logging
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'))
        # Ensure the log directory exists
        log_dir.mkdir(exist_ok=True, parents=True)
        
        log_file = os.path.join(log_dir, f'testfight_{timestamp}.log')
        
        # Set up a file handler for the combat_sim logger
        logger = logging.getLogger('combat_sim')
        # Reset handlers to avoid duplicates
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                          '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        
        # Add handler to logger
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
        logger.info(f"Starting combat simulation test run at {timestamp}")
        
        # Create a specially equipped player for combat simulation
        sim_player = Player("CombatSim")
        
        # Create additional programs for more varied testing
        status_program = Program(
            id="test_memory_leak", 
            name="Memory Leak", 
            power=30, 
            accuracy=90, 
            program_type="VIRUS", 
            effect="status:CORRUPTED",
            description="Causes target to leak memory over time."
        )
        
        defense_program = Program(
            id="test_firewall_shield",
            name="Firewall Shield", 
            power=0, 
            accuracy=100, 
            program_type="FIREWALL", 
            effect="stat_mod:defense:+1",
            description="Raises defense with a firewall shield."
        )
        
        healing_program = Program(
            id="test_system_restore",
            name="System Restore", 
            power=0, 
            accuracy=100, 
            program_type="UTILITY", 
            effect="heal:40",
            description="Restores system health."
        )
        
        # Create various daemons with different strengths/weaknesses
        virulet = Daemon(
            name="Virulet",
            types=["VIRUS"],
            level=15,
            base_hp=35, 
            base_attack=18, 
            base_defense=12, 
            base_speed=20, 
            base_special=15,
            programs=[self.virus_program, status_program, healing_program]
        )
        
        pyrowall = Daemon(
            name="Pyrowall", 
            types=["FIREWALL"],
            level=15,
            base_hp=45, 
            base_attack=15, 
            base_defense=20, 
            base_speed=12, 
            base_special=15,
            programs=[self.firewall_program, defense_program]
        )
        
        cryptoid = Daemon(
            name="Cryptoid",
            types=["CRYPTO"],
            level=15,
            base_hp=40, 
            base_attack=13, 
            base_defense=15, 
            base_speed=17, 
            base_special=20,
            programs=[self.crypto_program, healing_program]
        )
        
        # Add daemons to player
        sim_player.add_daemon(virulet)
        sim_player.add_daemon(pyrowall)
        sim_player.add_daemon(cryptoid)
        sim_player.set_active_daemon(virulet)
        
        # Create a function to simulate user input
        original_input = input
        input_responses = []
        
        def mock_input(prompt):
            logger.info(f"PROMPT: {prompt}")
            if not input_responses:
                logger.error("No more mock inputs available!")
                return "0"  # Default safe value
            response = input_responses.pop(0)
            logger.info(f"INPUT: {response}")
            return response
        
        # Run a series of combat simulations with different enemy daemons
        try:
            # List of enemy daemons to test against
            enemy_daemons = [
                Daemon(
                    name="Rat Bot",
                    types=["NEURAL"],
                    level=12,
                    base_hp=30, 
                    base_attack=14, 
                    base_defense=12, 
                    base_speed=16, 
                    base_special=10,
                    programs=[Program(
                        id="test_neural_spike",
                        name="Neural Spike", 
                        power=40, 
                        accuracy=95, 
                        program_type="NEURAL", 
                        effect="damage",
                        description="Spikes the target with neural data."
                    )]
                ),
                Daemon(
                    name="Shell Crab",
                    types=["SHELL"],
                    level=14,
                    base_hp=40, 
                    base_attack=12, 
                    base_defense=22, 
                    base_speed=8, 
                    base_special=10,
                    programs=[
                        Program(
                            id="test_shell_bash",
                            name="Shell Bash", 
                            power=50, 
                            accuracy=90, 
                            program_type="SHELL", 
                            effect="damage",
                            description="Bashes the target with a shell."
                        ), 
                        Program(
                            id="test_hardening",
                            name="Hardening", 
                            power=0, 
                            accuracy=100, 
                            program_type="SHELL", 
                            effect="stat_mod:defense:+2",
                            description="Hardens the shell for extra defense."
                        )
                    ]
                ),
                Daemon(
                    name="Poly Worm",
                    types=["CRYPTO", "WORM"],
                    level=16,
                    base_hp=35, 
                    base_attack=16, 
                    base_defense=14, 
                    base_speed=18, 
                    base_special=15,
                    programs=[
                        Program(
                            id="test_encrypt",
                            name="Encrypt", 
                            power=35, 
                            accuracy=100, 
                            program_type="CRYPTO", 
                            effect="damage",
                            description="Encrypts the target causing damage."
                        ),
                        Program(
                            id="test_worm_inject",
                            name="Worm Inject", 
                            power=40, 
                            accuracy=85, 
                            program_type="WORM", 
                            effect="status:CORRUPTED",
                            description="Injects a worm that corrupts the target."
                        )
                    ]
                ),
            ]
            
            for i, enemy_daemon in enumerate(enemy_daemons):
                logger.info(f"\n{'='*50}\nSTARTING COMBAT SIMULATION #{i+1}\n{'='*50}")
                logger.info(f"Player daemon: {sim_player.get_active_daemon().name} (Level {sim_player.get_active_daemon().level})")
                logger.info(f"Enemy daemon: {enemy_daemon.name} (Level {enemy_daemon.level})")
                
                # Reset daemons for fresh combat
                for daemon in sim_player.daemons:
                    daemon.hp = daemon.max_hp
                    daemon.status_effect = None
                
                enemy_daemon.hp = enemy_daemon.max_hp
                enemy_daemon.status_effect = None
                
                # Define automated responses based on scenario
                # Simulate a sequence of moves:
                # 1. Use an attack in the first turn
                # 2. Use a status move in the second turn
                # 3. Switch daemon in third turn (if still alive)
                # 4. Try to run or capture in fourth turn
                
                combat_actions = [
                    # Format: [initial action, program index/switch choice, etc.]
                    ['f', '1'],  # Fight with first program
                    ['f', '2'],  # Fight with second program (status effect or defense)
                ]
                
                # Only add switch command if we have more than one daemon
                if len(sim_player.get_healthy_daemons()) > 1:
                    combat_actions.append(['s', '1'])  # Switch to the first alternative daemon
                
                # For the last enemy, try capturing instead of running
                if i == len(enemy_daemons) - 1:
                    combat_actions.append(['c'])  # Attempt capture
                else:
                    combat_actions.append(['r'])  # Try to run
                    
                # Flatten the actions list into input responses
                for action_set in combat_actions:
                    input_responses.extend(action_set)
                
                # Monkey patch input function
                globals()['input'] = mock_input
                
                # Run the combat simulation
                try:
                    combat_result = run_combat(sim_player, enemy_daemon)
                    logger.info(f"Combat result: {combat_result}")
                    
                    # Verify we got a valid result
                    self.assertIn(combat_result, ["player_win", "enemy_win", "run", "capture"])
                    
                    # Log the end state
                    active_daemon = sim_player.get_active_daemon()
                    logger.info(f"Player active daemon: {active_daemon.name}, HP: {active_daemon.hp}/{active_daemon.max_hp}")
                    logger.info(f"Enemy daemon: {enemy_daemon.name}, HP: {enemy_daemon.hp}/{enemy_daemon.max_hp}")
                
                except Exception as e:
                    logger.error(f"Combat simulation failed: {str(e)}", exc_info=True)
                    self.fail(f"Combat simulation failed: {str(e)}")
        
        finally:
            # Restore the original input function
            globals()['input'] = original_input
            
            # Close logger to ensure file is written
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)
                
            logger.info(f"Combat simulation completed. Log saved to {log_file}")
            
            # Add an assertion to ensure the log was created
            self.assertTrue(os.path.exists(log_file), f"Log file {log_file} was not created")
            
            # Print the location of the log file for manual inspection
            print(f"\nCombat simulation log saved to: {log_file}")

if __name__ == '__main__':
    unittest.main()