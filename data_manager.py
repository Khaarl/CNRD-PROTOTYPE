"""
Data Manager for CNRD Prototype

Handles saving and loading game data to/from files.
"""
import os
import json
import logging
from pathlib import Path

def ensure_save_directory():
    """Ensure the saves directory exists"""
    save_dir = Path("saves")
    save_dir.mkdir(exist_ok=True)
    return save_dir

def save_game(game_data, save_name):
    """
    Save game data to a JSON file
    
    Args:
        game_data (dict): Game data to save
        save_name (str): Name of the save file (without extension)
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    save_dir = ensure_save_directory()
    
    # Ensure save_name is valid
    save_name = save_name.lower().replace(" ", "_")
    
    # Add .json extension if not present
    if not save_name.endswith(".json"):
        save_name += ".json"
    
    # Full path to save file
    save_path = save_dir / save_name
    
    try:
        with open(save_path, 'w') as f:
            json.dump(game_data, f, indent=4)
        logging.info(f"Game saved successfully to {save_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to save game: {e}", exc_info=True)
        return False

def load_game(save_name):
    """
    Load game data from a JSON file
    
    Args:
        save_name (str): Name of the save file (without extension)
        
    Returns:
        dict: The loaded game data, or None if loading failed
    """
    save_dir = ensure_save_directory()
    
    # Ensure save_name is valid
    save_name = save_name.lower().replace(" ", "_")
    
    # Add .json extension if not present
    if not save_name.endswith(".json"):
        save_name += ".json"
    
    # Full path to save file
    save_path = save_dir / save_name
    
    if not save_path.exists():
        logging.error(f"Save file not found: {save_path}")
        return None
    
    try:
        with open(save_path, 'r') as f:
            game_data = json.load(f)
        logging.info(f"Game loaded successfully from {save_path}")
        return game_data
    except Exception as e:
        logging.error(f"Failed to load game: {e}", exc_info=True)
        return None

def get_save_files():
    """
    Get a list of available save files
    
    Returns:
        list: List of Path objects for save files
    """
    save_dir = ensure_save_directory()
    return list(save_dir.glob("*.json"))

def delete_save_file(save_name):
    """
    Delete a save file
    
    Args:
        save_name (str): Name of the save file (without extension)
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    save_dir = ensure_save_directory()
    
    # Ensure save_name is valid
    save_name = save_name.lower().replace(" ", "_")
    
    # Add .json extension if not present
    if not save_name.endswith(".json"):
        save_name += ".json"
    
    # Full path to save file
    save_path = save_dir / save_name
    
    if not save_path.exists():
        logging.error(f"Cannot delete: Save file not found: {save_path}")
        return False
    
    try:
        os.remove(save_path)
        logging.info(f"Save file deleted: {save_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to delete save file: {e}", exc_info=True)
        return False
