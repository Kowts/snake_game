import random
import pygame

class GameEnhancements:
    @staticmethod
    def add_dynamic_obstacles(game):
        """
        Add dynamic obstacles to the game board.

        Args:
            game (SnakeGame): The current game instance

        Returns:
            list: Obstacles coordinates
        """
        obstacles = []
        num_obstacles = random.randint(1, 5)

        for _ in range(num_obstacles):
            while True:
                x = random.randint(0, (game.config['screen']['width'] // game.config['screen']['block_size'] - 1)) * game.config['screen']['block_size']
                y = random.randint(0, (game.config['screen']['height'] // game.config['screen']['block_size'] - 1)) * game.config['screen']['block_size']

                # Ensure obstacle doesn't overlap with snake, apple, or other obstacles
                if ((x, y) not in game.snake and
                    (x, y) != game.apple and
                    all((x, y) != (obs_x, obs_y) for obs_x, obs_y in obstacles)):
                    obstacles.append((x, y))
                    break

        return obstacles

    @staticmethod
    def create_challenge_mode(game):
        """
        Create a challenge mode with additional game mechanics.

        Args:
            game (SnakeGame): The current game instance

        Returns:
            dict: Challenge mode settings
        """
        challenge_settings = {
            'time_limit': random.randint(30, 120),  # 30-120 seconds
            'target_score': random.randint(50, 200),
            'obstacles': True,
            'moving_walls': random.choice([True, False]),
            'special_apple_spawn': random.choice([True, False])
        }

        return challenge_settings

    @staticmethod
    def create_mini_missions(game):
        """
        Generate mini-missions during the game.

        Args:
            game (SnakeGame): The current game instance

        Returns:
            dict: Mini-mission configuration
        """
        missions = [
            {
                'description': 'Eat 5 apples without hitting walls',
                'goal': 5,
                'current_progress': 0,
                'reward': 10
            },
            {
                'description': 'Reach max speed',
                'goal': game.config['gameplay']['max_speed'],
                'current_progress': 0,
                'reward': 15
            },
            {
                'description': 'Collect 3 power-ups',
                'goal': 3,
                'current_progress': 0,
                'reward': 20
            }
        ]

        return random.choice(missions)

    @staticmethod
    def add_weather_effects():
        """
        Create dynamic weather effects.

        Returns:
            dict: Weather effects configuration
        """
        weather_types = [
            {
                'name': 'Sunny',
                'color_shift': (50, 50, 0),  # Slight yellow tint
                'speed_modifier': 1.0
            },
            {
                'name': 'Rainy',
                'color_shift': (-50, -50, 50),  # Blue tint
                'speed_modifier': 0.8  # Slower movement
            },
            {
                'name': 'Windy',
                'color_shift': (0, 30, -30),  # Green-blue tint
                'speed_modifier': 1.2  # Faster movement
            }
        ]

        return random.choice(weather_types)
