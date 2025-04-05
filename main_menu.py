import os
import sys
import pygame
from pathlib import Path
import logging
from data_manager import get_save_files

class MainMenu:
    """Main menu interface for the CNRD game"""
    
    def __init__(self, game_instance):
        """
        Initialize the main menu
        
        Args:
            game_instance: The Game object
        """
        self.game = game_instance
        self.running = True
        self.menu_options = ["New Game", "Load Game", "Quick Fight", "Options", "Exit"]
        self.selected_option = 0
        
        # Initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()
            
        # Set up display
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("CNRD Prototype")
        
        # Load fonts
        self.title_font = pygame.font.Font(None, 64)
        self.menu_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Set colors
        self.bg_color = (10, 10, 20)
        self.title_color = (0, 200, 255)
        self.option_color = (200, 200, 200)
        self.selected_color = (255, 255, 0)
        
        # Set menu state
        self.state = "MAIN"  # MAIN, NEW_GAME, LOAD_GAME, OPTIONS
        self.player_name_input = ""
        self.save_files = []
        self.selected_save = 0
        
    def run(self):
        """
        Run the main menu
        
        Returns:
            dict: The result of the menu selection
        """
        clock = pygame.time.Clock()
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return {"action": "exit"}
                    
                self.handle_event(event)
                
            # Draw the menu
            self.draw()
            
            # Update display
            pygame.display.flip()
            
            # Cap frame rate
            clock.tick(60)
            
        # Return the menu result
        return self.get_result()
        
    def handle_event(self, event):
        """Handle pygame events"""
        if self.state == "MAIN":
            self.handle_main_menu_event(event)
        elif self.state == "NEW_GAME":
            self.handle_new_game_event(event)
        elif self.state == "LOAD_GAME":
            self.handle_load_game_event(event)
        elif self.state == "OPTIONS":
            self.handle_options_event(event)
            
    def handle_main_menu_event(self, event):
        """Handle events for the main menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                self.select_main_menu_option()
                
    def handle_new_game_event(self, event):
        """Handle events for the new game menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if len(self.player_name_input) > 0:
                    self.running = False
            elif event.key == pygame.K_BACKSPACE:
                self.player_name_input = self.player_name_input[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.state = "MAIN"
            else:
                # Add character to player name input
                if len(self.player_name_input) < 15 and event.unicode.isprintable():
                    self.player_name_input += event.unicode
                    
    def handle_load_game_event(self, event):
        """Handle events for the load game menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_save = (self.selected_save - 1) % max(1, len(self.save_files))
            elif event.key == pygame.K_DOWN:
                self.selected_save = (self.selected_save + 1) % max(1, len(self.save_files))
            elif event.key == pygame.K_RETURN:
                if self.save_files:
                    self.running = False
            elif event.key == pygame.K_ESCAPE:
                self.state = "MAIN"
                
    def handle_options_event(self, event):
        """Handle events for the options menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "MAIN"
                
    def select_main_menu_option(self):
        """Select the current main menu option"""
        option = self.menu_options[self.selected_option]
        
        if option == "New Game":
            self.state = "NEW_GAME"
            self.player_name_input = ""
        elif option == "Load Game":
            self.state = "LOAD_GAME"
            self.load_save_files()
        elif option == "Quick Fight":
            self.running = False
        elif option == "Options":
            self.state = "OPTIONS"
        elif option == "Exit":
            self.running = False
            pygame.quit()
            sys.exit()
            
    def load_save_files(self):
        """Load the list of save files"""
        self.save_files = get_save_files()
        self.selected_save = 0
        
    def get_result(self):
        """Get the result of the menu selection"""
        if not self.running:
            option = self.menu_options[self.selected_option]
            
            if option == "New Game":
                return {
                    "action": "new_game",
                    "player_name": self.player_name_input
                }
            elif option == "Load Game" and self.save_files:
                return {
                    "action": "load_game",
                    "save_file": str(self.save_files[self.selected_save])
                }
            elif option == "Quick Fight":
                return {
                    "action": "quick_fight"
                }
                
        return {"action": "exit"}
        
    def draw(self):
        """Draw the menu"""
        self.screen.fill(self.bg_color)
        
        if self.state == "MAIN":
            self.draw_main_menu()
        elif self.state == "NEW_GAME":
            self.draw_new_game()
        elif self.state == "LOAD_GAME":
            self.draw_load_game()
        elif self.state == "OPTIONS":
            self.draw_options()
            
        pygame.display.update()
        
    def draw_main_menu(self):
        """Draw the main menu"""
        # Draw title
        title_text = self.title_font.render("CNRD Prototype", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw version
        version_text = self.small_font.render("v0.1 Alpha", True, (150, 150, 150))
        version_rect = version_text.get_rect(bottomright=(self.screen_width - 20, self.screen_height - 20))
        self.screen.blit(version_text, version_rect)
        
        # Draw options
        for i, option in enumerate(self.menu_options):
            color = self.selected_color if i == self.selected_option else self.option_color
            option_text = self.menu_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.screen_width // 2, 200 + i * 50))
            self.screen.blit(option_text, option_rect)
            
    def draw_new_game(self):
        """Draw the new game menu"""
        # Draw title
        title_text = self.title_font.render("New Game", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw prompt
        prompt_text = self.menu_font.render("Enter your name:", True, self.option_color)
        prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(prompt_text, prompt_rect)
        
        # Draw input box
        pygame.draw.rect(self.screen, self.option_color, (200, 250, 400, 50), 2)
        
        # Draw input text
        input_text = self.menu_font.render(self.player_name_input, True, self.option_color)
        input_rect = input_text.get_rect(center=(self.screen_width // 2, 275))
        self.screen.blit(input_text, input_rect)
        
        # Draw instructions
        instructions_text = self.small_font.render("Press Enter to continue, Escape to cancel", True, (150, 150, 150))
        instructions_rect = instructions_text.get_rect(center=(self.screen_width // 2, 350))
        self.screen.blit(instructions_text, instructions_rect)
        
    def draw_load_game(self):
        """Draw the load game menu"""
        # Draw title
        title_text = self.title_font.render("Load Game", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw list of save files
        if not self.save_files:
            # No save files
            no_saves_text = self.menu_font.render("No save files found", True, self.option_color)
            no_saves_rect = no_saves_text.get_rect(center=(self.screen_width // 2, 250))
            self.screen.blit(no_saves_text, no_saves_rect)
        else:
            # Draw save files
            for i, save_file in enumerate(self.save_files):
                color = self.selected_color if i == self.selected_save else self.option_color
                
                # Extract player name from filename
                player_name = save_file.stem.replace("_", " ").title()
                
                save_text = self.menu_font.render(player_name, True, color)
                save_rect = save_text.get_rect(center=(self.screen_width // 2, 200 + i * 40))
                self.screen.blit(save_text, save_rect)
                
        # Draw instructions
        instructions_text = self.small_font.render("Press Enter to load, Escape to cancel", True, (150, 150, 150))
        instructions_rect = instructions_text.get_rect(center=(self.screen_width // 2, 500))
        self.screen.blit(instructions_text, instructions_rect)
        
    def draw_options(self):
        """Draw the options menu"""
        # Draw title
        title_text = self.title_font.render("Options", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw placeholder
        options_text = self.menu_font.render("Options not yet implemented", True, self.option_color)
        options_rect = options_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(options_text, options_rect)
        
        # Draw instructions
        instructions_text = self.small_font.render("Press Escape to return to main menu", True, (150, 150, 150))
        instructions_rect = instructions_text.get_rect(center=(self.screen_width // 2, 500))
        self.screen.blit(instructions_text, instructions_rect)