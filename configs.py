import json
import os
import random

class GameConfigManager:
    """
    Dynamic configuration management for the Snake game.
    Allows loading, saving, and modifying game configurations.
    """
    DEFAULT_CONFIG = {
        "screen": {
            "width": 800,
            "height": 600,
            "block_size": 20,
            "title": "Advanced Snake Game"
        },
        "gameplay": {
            "initial_speed": 5,
            "max_speed": 15,
            "initial_lives": 3,
            "speed_increment": 0.5,
            "power_up_spawn_chance": 0.3
        },
        "difficulty_levels": {
            "EASY": {
                "initial_speed": 3,
                "lives": 5,
                "power_up_chance": 0.4,
                "apple_score": 1
            },
            "MEDIUM": {
                "initial_speed": 5,
                "lives": 3,
                "power_up_chance": 0.3,
                "apple_score": 2
            },
            "HARD": {
                "initial_speed": 7,
                "lives": 1,
                "power_up_chance": 0.2,
                "apple_score": 3
            }
        },
        "power_ups": {
            "types": {
                "speed_boost": {
                    "duration": 5000,
                    "speed_increase": 2
                },
                "invincibility": {
                    "duration": 3000
                },
                "extra_points": {
                    "points": 5
                }
            }
        },
        "colors": {
            "snake_head": [0, 255, 0],
            "snake_body": [0, 100, 0],
            "apple": [255, 0, 0],
            "power_up": [255, 105, 180]
        }
    }

    CONFIG_FILE = 'game_config.json'

    @classmethod
    def load_config(cls):
        """
        Load game configuration from file or return default.

        Returns:
            dict: Game configuration
        """
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge default and user config
                    return cls._deep_merge(cls.DEFAULT_CONFIG.copy(), user_config)
            return cls.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}. Using default configuration.")
            return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config):
        """
        Save game configuration to file.

        Args:
            config (dict): Configuration to save
        """
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            print("Configuration saved successfully.")
        except Exception as e:
            print(f"Error saving config: {e}")

    @classmethod
    def _deep_merge(cls, default, update):
        """
        Recursively merge two dictionaries.

        Args:
            default (dict): Default configuration
            update (dict): User-provided configuration

        Returns:
            dict: Merged configuration
        """
        for key, value in update.items():
            if isinstance(value, dict):
                default[key] = cls._deep_merge(default.get(key, {}), value)
            else:
                default[key] = value
        return default

    @classmethod
    def create_config_interface(cls):
        """
        Create an interactive configuration interface.

        Returns:
            dict: Updated configuration
        """
        config = cls.load_config()

        print("\n=== Snake Game Configuration ===")

        # Screen settings
        print("\nScreen Settings:")
        config['screen']['width'] = int(input(f"Screen Width [{config['screen']['width']}]: ") or config['screen']['width'])
        config['screen']['height'] = int(input(f"Screen Height [{config['screen']['height']}]: ") or config['screen']['height'])
        config['screen']['block_size'] = int(input(f"Block Size [{config['screen']['block_size']}]: ") or config['screen']['block_size'])
        config['screen']['title'] = input(f"Game Title [{config['screen']['title']}]: ") or config['screen']['title']

        # Gameplay settings
        print("\nGameplay Settings:")
        config['gameplay']['initial_speed'] = float(input(f"Initial Speed [{config['gameplay']['initial_speed']}]: ") or config['gameplay']['initial_speed'])
        config['gameplay']['max_speed'] = float(input(f"Max Speed [{config['gameplay']['max_speed']}]: ") or config['gameplay']['max_speed'])
        config['gameplay']['initial_lives'] = int(input(f"Initial Lives [{config['gameplay']['initial_lives']}]: ") or config['gameplay']['initial_lives'])

        # Difficulty levels
        print("\nDifficulty Levels:")
        for difficulty in ['EASY', 'MEDIUM', 'HARD']:
            print(f"\n{difficulty} Difficulty:")
            config['difficulty_levels'][difficulty]['initial_speed'] = float(
                input(f"Initial Speed [{config['difficulty_levels'][difficulty]['initial_speed']}]: ")
                or config['difficulty_levels'][difficulty]['initial_speed']
            )
            config['difficulty_levels'][difficulty]['lives'] = int(
                input(f"Lives [{config['difficulty_levels'][difficulty]['lives']}]: ")
                or config['difficulty_levels'][difficulty]['lives']
            )

        # Save the updated configuration
        cls.save_config(config)
        return config

def initialize_game_config():
    """
    Initialize game configuration, optionally allowing user customization.

    Returns:
        dict: Game configuration
    """
    # Check if user wants to modify configuration
    modify = input("Would you like to modify game configuration? (y/n): ").lower() == 'y'

    if modify:
        return GameConfigManager.create_config_interface()
    else:
        return GameConfigManager.load_config()
