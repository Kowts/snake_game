import math
import os
import sys
import json
import pygame
import random
import logging
import numpy as np
from scipy.io import wavfile
from configs import initialize_game_config
from enhancements import GameEnhancements

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='snake_game.log'
)

# Enhanced Configuration Management
class GameConfig:
    """Centralized configuration management for the Snake game."""
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 20
    INITIAL_SPEED = 5
    MAX_SPEED = 15
    INITIAL_LIVES = 3
    DIFFICULTY_LEVELS = {
        'EASY': {
            'initial_speed': 3,
            'lives': 5,
            'power_up_chance': 0.4,
            'apple_score': 1
        },
        'MEDIUM': {
            'initial_speed': 5,
            'lives': 3,
            'power_up_chance': 0.3,
            'apple_score': 2
        },
        'HARD': {
            'initial_speed': 7,
            'lives': 1,
            'power_up_chance': 0.2,
            'apple_score': 3
        }
    }

    @classmethod
    def get_difficulty_config(cls, difficulty='MEDIUM'):
        """Retrieve configuration for a specific difficulty level."""
        return cls.DIFFICULTY_LEVELS.get(difficulty, cls.DIFFICULTY_LEVELS['MEDIUM'])

# Color Palette
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    DARK_GREEN = (0, 100, 0)
    GRAY = (100, 100, 100)
    BLUE = (0, 0, 255)
    GOLD = (255, 215, 0)
    HOT_PINK = (255, 105, 180)
    LIGHT_BLUE = (100, 149, 237)

class SoundManager:
    """Manage game sound effects and background music."""
    def __init__(self):
        """Initialize sound system."""
        pygame.mixer.init()
        self.sounds = {}
        self.music = None
        self.volume = 0.5
        self.load_sounds()

    def load_sounds(self):
        """Load game sound effects from audio folder."""
        sound_files = {
            'eat': 'audio/eat.wav',
            'power_up': 'audio/power_up.wav',
            'game_over': 'audio/game_over.wav'
        }

        # Create audio directory if it doesn't exist
        os.makedirs('audio', exist_ok=True)

        for name, filename in sound_files.items():
            try:
                sound = pygame.mixer.Sound(filename)
                sound.set_volume(self.volume)
                self.sounds[name] = sound
            except pygame.error as e:
                logging.warning(f"Could not load sound {filename}: {e}")
                # Optional: create placeholder sound files if they don't exist
                self.create_placeholder_sound(filename)

    def create_placeholder_sound(self, filename):
        """Create a placeholder sound file if it doesn't exist."""
        import numpy as np

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Only create if file doesn't exist
        if not os.path.exists(filename):
            # Generate a simple tone
            sample_rate = 44100
            duration = 0.5  # half a second
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone

            # Scale to 16-bit integers
            scaled = np.int16(tone * 32767)

            # Write WAV file
            wavfile.write(filename, sample_rate, scaled)
            logging.info(f"Created placeholder sound file: {filename}")

    def play_sound(self, sound_name):
        """Play a specific sound effect."""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
        else:
            logging.warning(f"Sound {sound_name} not found")

    def set_volume(self, volume):
        """Set volume for all sounds."""
        self.volume = max(0, min(1, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

class HighScoreManager:
    """Manage high scores with persistent storage."""
    HIGHSCORE_FILE = 'highscores.json'

    @classmethod
    def save_score(cls, score, username='Player'):
        """Save a new high score."""
        try:
            # Load existing high scores
            if os.path.exists(cls.HIGHSCORE_FILE):
                with open(cls.HIGHSCORE_FILE, 'r') as f:
                    high_scores = json.load(f)
            else:
                high_scores = []

            # Add new score
            high_scores.append({
                'name': username,
                'score': score,
                'timestamp': pygame.time.get_ticks()
            })

            # Sort and keep top 10
            high_scores = sorted(high_scores, key=lambda x: x['score'], reverse=True)[:10]

            # Save back to file
            with open(cls.HIGHSCORE_FILE, 'w') as f:
                json.dump(high_scores, f)

        except Exception as e:
            logging.error(f"Error saving high score: {e}")

    @classmethod
    def get_high_scores(cls):
        """Retrieve top high scores."""
        try:
            if os.path.exists(cls.HIGHSCORE_FILE):
                with open(cls.HIGHSCORE_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"Error reading high scores: {e}")
            return []

class ScreenShake:
    def __init__(self):
        self.duration = 0
        self.intensity = 0
        self.offset = (0, 0)

    def start(self, duration=20, intensity=5):
        self.duration = duration
        self.intensity = intensity

    def update(self):
        if self.duration > 0:
            self.offset = (
                random.randint(-self.intensity, self.intensity),
                random.randint(-self.intensity, self.intensity)
            )
            self.duration -= 1
        else:
            self.offset = (0, 0)

class BackgroundMusic:
    def __init__(self):

        # Music tracks
        self.tracks = {
            'menu': 'audio/music.wav',
            'gameplay': 'audio/game_play.wav',
            'gameover': 'audio/game_over.wav',
        }
        self.current_track = None
        self.load_tracks()

    def load_tracks(self):
        for name, path in self.tracks.items():
            if not os.path.exists(path):
                self.create_placeholder_music(path)

    def create_placeholder_music(self, filename):
        sample_rate = 44100
        duration = 10
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        melody = np.sin(2 * np.pi * 440 * t) * 0.3
        wavfile.write(filename, sample_rate, (melody * 32767).astype(np.int16))

    def play(self, track_name, loop=True):
        if self.current_track != track_name:
            pygame.mixer.music.load(self.tracks[track_name])
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_track = track_name
class MovingFood:
    def __init__(self, x, y, speed=2):
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])
        self.move_counter = 0

    def update(self):
        # Change direction randomly
        if self.move_counter % 30 == 0:
            self.direction = random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])

        # Move food
        if self.direction == 'UP':
            self.y = max(0, self.y - self.speed)
        elif self.direction == 'DOWN':
            self.y = min(GameConfig.SCREEN_HEIGHT - GameConfig.BLOCK_SIZE, self.y + self.speed)
        elif self.direction == 'LEFT':
            self.x = max(0, self.x - self.speed)
        elif self.direction == 'RIGHT':
            self.x = min(GameConfig.SCREEN_WIDTH - GameConfig.BLOCK_SIZE, self.x + self.speed)

        self.move_counter += 1

class PowerUp:
    """Enhanced Power-up class with duration and type management."""
    TYPES = {
        'speed_boost': {
            'color': Colors.BLUE,
            'duration': 5000,  # 5 seconds
            'effect': lambda game: setattr(game, 'current_speed', min(game.current_speed + 2, GameConfig.MAX_SPEED)),
            'description': 'Temporarily increase snake speed'
        },
        'invincibility': {
            'color': Colors.GOLD,
            'duration': 3000,  # 3 seconds
            'effect': lambda game: game.set_invincibility(True),
            'description': 'Become temporarily invincible'
        },
        'extra_points': {
            'color': Colors.HOT_PINK,
            'duration': 0,  # Immediate effect
            'effect': lambda game: setattr(game, 'score', game.score + 5),
            'description': 'Instantly gain bonus points'
        },
        'length_increase': {
            'color': Colors.GREEN,
            'duration': 0,
            'effect': lambda game: game.grow_snake(),  # Using a dedicated method for growing
            'description': 'Instantly grow snake length'
        }
    }

    def __init__(self, x, y, power_type):
        """Initialize a power-up with position and type."""
        self.x = x
        self.y = y
        self.power_type = power_type
        self.creation_time = pygame.time.get_ticks()
        self.config = self.TYPES[power_type]

    def apply_effect(self, game):
        """Apply the power-up's effect to the game."""
        # Apply the effect
        self.config['effect'](game)

        # Optional: Add visual or temporary effect
        if self.config['duration'] > 0:
            game.screen_shake.start(duration=10, intensity=3)

    def is_expired(self):
        """Check if power-up has expired."""
        return self.config['duration'] > 0 and \
               pygame.time.get_ticks() - self.creation_time > self.config['duration']

class AchievementManager:
    """Manage game achievements and tracking."""
    ACHIEVEMENTS = {
        'long_snake': {
            'name': 'Snake Charmer',
            'description': 'Grow snake to 20 segments',
            'condition': lambda game: len(game.snake) >= 20,
            'reward': 50
        },
        'speed_demon': {
            'name': 'Speed Demon',
            'description': 'Reach maximum speed',
            'condition': lambda game: game.current_speed >= game.config['gameplay']['max_speed'],
            'reward': 30
        },
        'power_up_master': {
            'name': 'Power-Up Collector',
            'description': 'Collect 10 power-ups',
            'condition': lambda game: game.achievements.get('power_ups_collected', 0) >= 10,
            'reward': 40
        },
        'survival_master': {
            'name': 'Survival Expert',
            'description': 'Complete game with all lives',
            'condition': lambda game: game.lives == game.config['gameplay']['initial_lives'],
            'reward': 25
        }
    }

    @classmethod
    def check_achievements(cls, game):
        """
        Check and return any newly unlocked achievements.

        Args:
            game (SnakeGame): Current game instance

        Returns:
            list: Newly unlocked achievements
        """
        unlocked = []

        # Ensure power_ups_collected is tracked
        if 'power_ups_collected' not in game.achievements:
            game.achievements['power_ups_collected'] = 0

        for key, achievement in cls.ACHIEVEMENTS.items():
            # Check if achievement condition is met
            if achievement['condition'](game):
                # Check if this achievement was already unlocked
                if not game.achievements.get(f'achievement_{key}_unlocked', False):
                    # Mark as unlocked and add to list
                    game.achievements[f'achievement_{key}_unlocked'] = True
                    game.score += achievement['reward']
                    unlocked.append(achievement)

        return unlocked

class SnakeGame:

    def __init__(self, difficulty='MEDIUM'):
        """Initialize the game with all necessary setup."""
        pygame.init()

        # Load dynamic configuration
        self.config = initialize_game_config()

        # Challenge mode attributes
        self.challenge_mode = None
        self.challenge_start_time = None
        self.current_mission = None
        self.obstacles = []
        self.games_since_challenge = 0

        # Screen and display setup
        self.screen = pygame.display.set_mode((
            self.config['screen']['width'],
            self.config['screen']['height']
        ))
        pygame.display.set_caption(self.config['screen']['title'])
        self.clock = pygame.time.Clock()

        # Store difficulty configuration as an instance attribute
        self.difficulty_config = self.config['difficulty_levels'].get(difficulty, self.config['difficulty_levels']['MEDIUM'])

        # Sound management
        self.sound_manager = SoundManager()

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Game state tracking
        self.score = 0
        self.high_score = 0

        # Use difficulty-specific configuration
        self.lives = self.difficulty_config['lives']
        self.current_speed = self.difficulty_config['initial_speed']
        self.power_up_chance = self.difficulty_config.get('power_up_chance', 0.3)

        self.is_invincible = False
        self.invincibility_timer = 0

        # Game elements setup
        self.screen_shake = ScreenShake()
        self.background_music = BackgroundMusic()
        self.moving_food = None
        self.background_music.play('menu')

        # Challenge mode setup
        self.challenge_mode = None
        self.obstacles = []
        self.current_mission = None

        # Power-up system
        self.power_ups = []
        self.power_up_spawn_timer = 0

        # Achievements tracking
        self.achievements = {
            'longest_snake': 0,
            'max_speed_reached': self.current_speed,
            'total_apples_eaten': 0,
            'power_ups_collected': 0
        }

        # Game modes
        self.game_state = 'START'

        # Initialize game
        self.reset_game()

    def initialize_challenge_mode(self):
        """
        Determines whether to start challenge mode based on various game factors
        and player performance. Returns a tuple of (should_start, difficulty_multiplier).
        """
        # Track consecutive games without challenge mode
        if not hasattr(self, 'games_since_challenge'):
            self.games_since_challenge = 0

        # Base probability calculation based on player skill metrics
        base_probability = 0.2  # Starting 20% chance

        # Factor 1: Recent Performance
        high_scores = HighScoreManager.get_high_scores()
        if high_scores:
            recent_scores = high_scores[-3:]  # Last 3 scores
            avg_recent_score = sum(score['score'] for score in recent_scores) / len(recent_scores)
            if avg_recent_score > 50:  # Player is doing well
                base_probability += 0.1

        # Factor 2: Games since last challenge
        challenge_modifier = min(0.15, self.games_since_challenge * 0.05)  # +5% per game, max 15%
        base_probability += challenge_modifier

        # Factor 3: Time of day variety (more challenging during peak gaming hours)
        current_hour = pygame.time.get_ticks() // 3600000 % 24  # Convert to hours
        if 20 <= current_hour <= 23 or 14 <= current_hour <= 16:  # Peak gaming hours
            base_probability += 0.05

        # Factor 4: Achievement progress
        achievement_count = sum(1 for key in self.achievements if key.startswith('achievement_') and self.achievements[key])
        if achievement_count > 2:  # Player has some experience
            base_probability += 0.1

        # Calculate difficulty multiplier based on player skill
        difficulty_multiplier = 1.0
        if hasattr(self, 'current_speed') and self.current_speed > self.config['gameplay']['initial_speed']:
            speed_factor = (self.current_speed - self.config['gameplay']['initial_speed']) / (self.config['gameplay']['max_speed'] - self.config['gameplay']['initial_speed'])
            difficulty_multiplier += speed_factor * 0.5  # Up to 50% harder based on speed

        # Ensure reasonable bounds
        final_probability = min(0.75, max(0.1, base_probability))  # Between 10% and 75%

        # Make the decision
        should_start = random.random() < final_probability

        if should_start:
            self.games_since_challenge = 0
            logging.info(f"Starting challenge mode with difficulty multiplier: {difficulty_multiplier}")
        else:
            self.games_since_challenge += 1
            logging.info(f"Not starting challenge mode. Games since last challenge: {self.games_since_challenge}")

        return should_start, difficulty_multiplier

    def apply_challenge_mode_difficulty(self, base_settings, difficulty_multiplier):
        """
        Adjusts challenge mode settings based on calculated difficulty multiplier.
        """
        adjusted_settings = base_settings.copy()

        # Adjust time limit based on difficulty
        adjusted_settings['time_limit'] = int(base_settings['time_limit'] / difficulty_multiplier)

        # Adjust target score
        adjusted_settings['target_score'] = int(base_settings['target_score'] * difficulty_multiplier)

        # Adjust obstacle count and movement
        if base_settings.get('obstacles', False):
            adjusted_settings['obstacle_count'] = int(3 * difficulty_multiplier)
            adjusted_settings['obstacle_speed'] = 1 + (difficulty_multiplier - 1) * 0.5

        # Special conditions for very high difficulty
        if difficulty_multiplier > 1.5:
            adjusted_settings['moving_walls'] = True
            adjusted_settings['special_apple_spawn'] = True

        return adjusted_settings

    def display_achievements(self, screen):
        """Display unlocked achievements on the screen."""
        y_offset = GameConfig.SCREEN_HEIGHT//2 + 250

        achievements_title = self.small_font.render('Unlocked Achievements:', True, Colors.GREEN)
        achievements_title_rect = achievements_title.get_rect(
            center=(GameConfig.SCREEN_WIDTH//2, y_offset - 40)
        )
        screen.blit(achievements_title, achievements_title_rect)

        for key, achievement in AchievementManager.ACHIEVEMENTS.items():
            if self.achievements.get(f'achievement_{key}_unlocked', False):
                achievement_text = self.small_font.render(
                    f"{achievement['name']}: {achievement['description']}",
                    True,
                    Colors.GOLD
                )
                achievement_rect = achievement_text.get_rect(
                    center=(GameConfig.SCREEN_WIDTH//2, y_offset)
                )
                screen.blit(achievement_text, achievement_rect)
                y_offset += 30

    def display_achievements_page(self):
        """
        Create a dedicated achievements page/screen.
        Displays all possible achievements with their status.
        """
        while True:
            self.screen.fill(Colors.BLACK)

            # Achievements Title
            title = self.title_font.render('Achievements', True, Colors.GREEN)
            title_rect = title.get_rect(center=(GameConfig.SCREEN_WIDTH//2, 100))
            self.screen.blit(title, title_rect)

            # Iterate through all possible achievements
            y_offset = 200
            for key, achievement in AchievementManager.ACHIEVEMENTS.items():
                # Check if achievement is unlocked
                is_unlocked = self.achievements.get(f'achievement_{key}_unlocked', False)

                # Choose color based on unlock status
                text_color = Colors.GOLD if is_unlocked else Colors.GRAY

                # Render achievement name
                achievement_text = self.font.render(
                    f"{achievement['name']}: {achievement['description']}",
                    True,
                    text_color
                )

                # Add unlock status
                status_text = self.small_font.render(
                    'Unlocked' if is_unlocked else 'Locked',
                    True,
                    Colors.GREEN if is_unlocked else Colors.RED
                )

                # Position achievement text
                achievement_rect = achievement_text.get_rect(
                    center=(GameConfig.SCREEN_WIDTH//2, y_offset)
                )
                status_rect = status_text.get_rect(
                    center=(GameConfig.SCREEN_WIDTH//2, y_offset + 30)
                )

                # Render texts
                self.screen.blit(achievement_text, achievement_rect)
                self.screen.blit(status_text, status_rect)

                y_offset += 80

            # Back instructions
            back_text = self.small_font.render('Press SPACE to go back', True, Colors.GRAY)
            back_rect = back_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT - 100))
            self.screen.blit(back_text, back_rect)

            pygame.display.update()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return  # Go back to previous screen

    def start_challenge_mode(self):
        """
        Start a challenge mode with enhanced game mechanics.
        Generates dynamic challenges and modifies game parameters.
        """
        # Generate challenge mode settings
        self.challenge_mode = GameEnhancements.create_challenge_mode(self)

        # Add dynamic obstacles if enabled
        if self.challenge_mode.get('obstacles', False):
            self.obstacles = GameEnhancements.add_dynamic_obstacles(self)

        # Generate a mini-mission
        self.current_mission = GameEnhancements.create_mini_missions(self)

        # Track challenge start time
        self.challenge_start_time = pygame.time.get_ticks()

        # Optional: Additional challenge mode modifications
        if self.challenge_mode.get('moving_walls', False):
            # Placeholder for moving wall mechanics if implemented
            pass

        # Optional: Special apple spawn
        if self.challenge_mode.get('special_apple_spawn', False):
            # You could implement a special apple with unique properties
            # For now, we'll just generate a new apple
            self.apple = self.generate_apple()

        # Print challenge information to console
        print(f"Challenge Mode Activated!")
        print(f"Mission: {self.current_mission['description']}")
        print(f"Time Limit: {self.challenge_mode['time_limit']} seconds")
        print(f"Target Score: {self.challenge_mode['target_score']}")

    def draw_obstacles(self):
        """Draw obstacles on the game board."""
        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, Colors.GRAY,
                            (obstacle[0], obstacle[1],
                            self.config['screen']['block_size'],
                            self.config['screen']['block_size']))

    def check_obstacle_collision(self):
        """Check if snake collides with obstacles."""
        head = self.snake[-1]
        return head in self.obstacles

    def set_invincibility(self, state):
        """Set invincibility state and timer."""
        self.is_invincible = state
        if state:
            self.invincibility_timer = pygame.time.get_ticks()

    def reset_game(self):
        """Reset the game state to initial conditions."""

        # Store challenge mode state before reset
        previous_games_since_challenge = self.games_since_challenge

        # Snake starts in the middle of the screen
        center_x = GameConfig.SCREEN_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2

        # Initial snake with 3 segments
        self.snake = [
            (center_x - GameConfig.BLOCK_SIZE * 2, center_y),
            (center_x - GameConfig.BLOCK_SIZE, center_y),
            (center_x, center_y)
        ]

        # Initial direction
        self.direction = 'RIGHT'

        # Generate first apple
        self.apple = self.generate_apple()

        # Reset power-ups
        self.power_ups = []
        self.power_up_spawn_timer = 0
        self.is_invincible = False
        self.invincibility_timer = 0

        # Restore challenge mode tracking
        self.games_since_challenge = previous_games_since_challenge

        # Reset score and speed if starting new game
        if self.game_state != 'PAUSED':
            # Update achievements
            self.achievements['longest_snake'] = max(
                self.achievements['longest_snake'],
                len(self.snake)
            )
            self.achievements['max_speed_reached'] = max(
                self.achievements['max_speed_reached'],
                self.current_speed
            )

            # Reset game state variables
            if self.score > self.high_score:
                self.high_score = self.score

            self.score = 0

            # Use gameplay configuration for initial speed
            self.current_speed = self.config['gameplay']['initial_speed']

            # Use gameplay configuration for lives
            self.lives = self.config['gameplay']['initial_lives']

        # Reset game state
        self.game_state = 'PLAYING'

    def generate_power_up(self):
        """Generate a random power-up on the map."""
        # Ensure tracking attribute exists
        if 'power_ups_collected' not in self.achievements:
            self.achievements['power_ups_collected'] = 0

        while True:
            x = random.randint(0, (GameConfig.SCREEN_WIDTH // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE
            y = random.randint(0, (GameConfig.SCREEN_HEIGHT // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE

            # Ensure power-up doesn't appear on snake body or existing power-ups
            if (x, y) not in self.snake and \
            not any(pu.x == x and pu.y == y for pu in self.power_ups):
                # Randomly select power-up type
                power_type = random.choice(list(PowerUp.TYPES.keys()))
                power_up = PowerUp(x, y, power_type)
                self.power_ups.append(power_up)
                break

    def generate_apple(self):
        """Generate a new apple at a random location not occupied by the snake."""
        while True:
            # Calculate grid positions
            x = random.randint(0, (GameConfig.SCREEN_WIDTH // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE
            y = random.randint(0, (GameConfig.SCREEN_HEIGHT // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE

            # Ensure apple doesn't appear on snake body or power-ups
            if random.random() < 0.3:  # 30% chance for moving food
                return MovingFood(x, y)
            return (x, y)

    def draw_game(self):
        """Render all game elements with screen shake effect."""
        self.screen_shake.update()
        offset_x, offset_y = self.screen_shake.offset

        self.screen.fill(Colors.BLACK)

        # Draw obstacles if in challenge mode
        if self.obstacles:
            self.draw_obstacles()

        # Draw all game elements with offset
            # Draw snake with offset
        for i, (x, y) in enumerate(self.snake):
            body_color = Colors.GREEN if i == len(self.snake) - 1 else Colors.DARK_GREEN
            if self.is_invincible:
                body_color = Colors.GOLD if pygame.time.get_ticks() % 500 < 250 else Colors.GREEN
            pygame.draw.rect(self.screen, body_color,
                            (x + offset_x, y + offset_y, GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))

        # Draw apple with offset
        if isinstance(self.apple, MovingFood):
            self.apple.update()
            apple_x, apple_y = self.apple.x, self.apple.y
        else:
            apple_x, apple_y = self.apple[0], self.apple[1]
        pygame.draw.rect(self.screen, Colors.RED,
                        (apple_x + offset_x, apple_y + offset_y, GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))

        # Draw power-ups with offset
        for power_up in self.power_ups:
            pygame.draw.rect(self.screen, power_up.config['color'],
                            (power_up.x + offset_x, power_up.y + offset_y,
                            GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))

        # Draw UI elements (no offset)
        score_text = self.font.render(f'Score: {self.score} High Score: {self.high_score}', True, Colors.WHITE)
        lives_text = self.font.render(f'Lives: {self.lives}', True, Colors.WHITE)
        speed_text = self.small_font.render(f'Speed: {self.current_speed:.1f}', True, Colors.WHITE)

        if self.is_invincible:
            invincible_text = self.small_font.render('INVINCIBLE', True, Colors.GOLD)
            self.screen.blit(invincible_text, (10, 120))

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (10, 50))
        self.screen.blit(speed_text, (10, 90))

        pygame.display.update()

    def handle_events(self):
        """Process pygame events and handle game controls."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.game_state == 'START':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_a:
                        self.display_achievements_page()
                    elif event.key == pygame.K_d:
                        self.cycle_difficulty()

            elif self.game_state == 'GAME_OVER':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()

                    if hasattr(self, 'game_over_buttons'):
                        if self.game_over_buttons['restart'].collidepoint(mouse_pos):
                            HighScoreManager.save_score(self.score)
                            self.reset_game()
                        elif self.game_over_buttons['high_scores'].collidepoint(mouse_pos):
                            self.show_high_scores()
                        elif self.game_over_buttons['achievements'].collidepoint(mouse_pos):
                            self.display_achievements_page()
                        elif self.game_over_buttons['exit'].collidepoint(mouse_pos):
                            pygame.quit()
                            sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        HighScoreManager.save_score(self.score)
                        self.reset_game()
                    elif event.key == pygame.K_h:
                        self.show_high_scores()
                    elif event.key == pygame.K_a:
                        self.display_achievements_page()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            elif self.game_state == 'PLAYING':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.game_state = 'PAUSED'

                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP] and self.direction != 'DOWN':
                    self.direction = 'UP'
                elif keys[pygame.K_DOWN] and self.direction != 'UP':
                    self.direction = 'DOWN'
                elif keys[pygame.K_LEFT] and self.direction != 'RIGHT':
                    self.direction = 'LEFT'
                elif keys[pygame.K_RIGHT] and self.direction != 'LEFT':
                    self.direction = 'RIGHT'

            elif self.game_state == 'PAUSED':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.game_state = 'PLAYING'
                    elif event.key == pygame.K_m:
                        self.sound_manager.set_volume(0 if self.sound_manager.volume > 0 else 0.5)

    def move_snake(self):
        """
        Move the snake based on current direction with enhanced mission tracking and collision detection.
        """
        head = self.snake[-1]

        # Calculate new head position
        if self.direction == 'UP':
            new_head = (head[0], head[1] - GameConfig.BLOCK_SIZE)
        elif self.direction == 'DOWN':
            new_head = (head[0], head[1] + GameConfig.BLOCK_SIZE)
        elif self.direction == 'LEFT':
            new_head = (head[0] - GameConfig.BLOCK_SIZE, head[1])
        elif self.direction == 'RIGHT':
            new_head = (head[0] + GameConfig.BLOCK_SIZE, head[1])

        # Add new head
        self.snake.append(new_head)

        # Collision detection with more precise overlap checking
        is_apple_eaten = False
        if isinstance(self.apple, MovingFood):
            # Check for overlap within the block size
            is_apple_eaten = (
                abs(new_head[0] - self.apple.x) < GameConfig.BLOCK_SIZE and
                abs(new_head[1] - self.apple.y) < GameConfig.BLOCK_SIZE
            )
        else:
            # Existing tuple-based collision
            is_apple_eaten = new_head == self.apple

        # Mission and apple eating logic
        if is_apple_eaten:
            # Play eat sound
            self.sound_manager.play_sound('eat')

            # Increase score based on difficulty level
            apple_score = self.difficulty_config.get('apple_score', 1)
            self.score += apple_score

            # Mission progress tracking
            if self.current_mission:
                # Mission: Eat specific number of apples
                if self.current_mission['description'] == 'Eat 5 apples without hitting walls':
                    self.current_mission['current_progress'] += 1

                    # Check if mission is completed
                    if self.current_mission['current_progress'] >= self.current_mission['goal']:
                        print("Mission Completed: Ate 5 apples!")
                        self.score += self.current_mission['reward']
                        # Optionally reset or generate a new mission
                        self.current_mission = GameEnhancements.create_mini_missions(self)

            # Achievements tracking
            self.achievements['total_apples_eaten'] += 1

            # Speed increase logic
            self.current_speed = min(self.current_speed + 0.5, GameConfig.MAX_SPEED)

            # Update max speed achievement
            self.achievements['max_speed_reached'] = max(
                self.achievements['max_speed_reached'],
                self.current_speed
            )

            # Challenge mode: check for specific mission tracking
            if self.challenge_mode:
                # Example: Reach max speed mission
                if self.current_mission and self.current_mission['description'] == 'Reach max speed':
                    if self.current_speed >= self.current_mission['goal']:
                        self.current_mission['current_progress'] = self.current_mission['goal']
                        print("Mission Completed: Max Speed Reached!")
                        self.score += self.current_mission['reward']

            # Generate new apple
            self.apple = self.generate_apple()

            # Chance to spawn power-up
            if random.random() < self.power_up_chance:
                self.generate_power_up()
        else:
            # Remove tail if no apple eaten
            self.snake.pop(0)

        # Power-up spawn timer
        self.power_up_spawn_timer += 1
        if self.power_up_spawn_timer >= 50:  # Spawn power-up every 50 frames
            self.power_up_spawn_timer = 0
            if random.random() < 0.2:  # 20% chance
                self.generate_power_up()

        # Manage invincibility timer
        if self.is_invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincibility_timer > 3000:  # 3 seconds of invincibility
                self.is_invincible = False

        # Optional: Additional debug or logging
        if self.challenge_mode and self.current_mission:
            print(f"Current Mission Progress: {self.current_mission['current_progress']}/{self.current_mission['goal']}")

    def grow_snake(self):
        """
        Safely grow the snake by one segment.
        Adds the new segment to the tail, ensuring no immediate collision.
        """
        tail = self.snake[0]
        second_last = self.snake[1]

        # Calculate direction of tail growth
        growth_x = tail[0] - second_last[0]
        growth_y = tail[1] - second_last[1]

        new_tail = (tail[0] + growth_x, tail[1] + growth_y)
        self.snake.insert(0, new_tail)

    def check_power_up_collision(self):
        """Check if snake collects a power-up."""
        head = self.snake[-1]

        for power_up in self.power_ups[:]:
            if head == (power_up.x, power_up.y):
                # Play power-up sound
                self.sound_manager.play_sound('power_up')

                # Apply the power-up effect
                power_up.apply_effect(self)

                # Track achievement
                self.achievements['power_ups_collected'] = self.achievements.get('power_ups_collected', 0) + 1

                # Remove the power-up
                self.power_ups.remove(power_up)

                return True

        return False

    def check_collision(self):
        """Check for collisions with walls, self, and obstacles."""
        head = self.snake[-1]

        # Log position
        logging.info(f"Checking collision for head position: {head}")

        # Power-Up Collision
        for power_up in self.power_ups:
            if head == (power_up.x, power_up.y):
                logging.info(f"Power-up collected at {power_up.x, power_up.y}")

        # Wall Collision
        if head[0] < 0 or head[0] >= GameConfig.SCREEN_WIDTH or \
        head[1] < 0 or head[1] >= GameConfig.SCREEN_HEIGHT:
            logging.warning("Wall collision detected!")
            return self.handle_collision()

        # Self Collision
        if head in self.snake[:-1]:
            logging.warning("Self collision detected!")
            return self.handle_collision()

        # Obstacle Collision
        if self.obstacles and head in self.obstacles:
            logging.warning("Obstacle collision detected!")
            return self.handle_collision()

        return True

    def handle_collision(self):
        """Handle snake collision, reduce lives or end game."""
        self.lives -= 1

        # Reset speed to initial speed when losing a life
        # Use the initial speed from gameplay configuration
        self.current_speed = self.config['gameplay']['initial_speed']

        if self.lives <= 0:
            # Game Over
            self.sound_manager.play_sound('game_over')
            self.game_state = 'GAME_OVER'
            return False

        # Reset snake position but keep lives and score
        self.game_state = 'PLAYING'

        # Reset snake position
        center_x = GameConfig.SCREEN_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2

        self.snake = [
            (center_x - GameConfig.BLOCK_SIZE * 2, center_y),
            (center_x - GameConfig.BLOCK_SIZE, center_y),
            (center_x, center_y)
        ]
        self.direction = 'RIGHT'

        # Generate new apple and reset power-ups
        self.apple = self.generate_apple()
        self.power_ups = []

        return True

    def show_high_scores(self):
        """Display high scores screen."""
        high_scores = HighScoreManager.get_high_scores()

        while True:
            self.screen.fill(Colors.BLACK)

            # High Scores Title
            title = self.title_font.render('High Scores', True, Colors.GREEN)
            title_rect = title.get_rect(center=(GameConfig.SCREEN_WIDTH//2, 100))
            self.screen.blit(title, title_rect)

            # Display high scores
            for i, score_entry in enumerate(high_scores[:10], 1):
                score_text = self.font.render(
                    f"{i}. {score_entry['name']}: {score_entry['score']}",
                    True,
                    Colors.WHITE
                )
                score_rect = score_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, 200 + i*40))
                self.screen.blit(score_text, score_rect)

            # Back instructions
            back_text = self.small_font.render('Press SPACE to go back', True, Colors.GRAY)
            back_rect = back_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT - 100))
            self.screen.blit(back_text, back_rect)

            pygame.display.update()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return  # Go back to game over screen

    def draw_start_screen(self):
        """Render the start screen."""
        self.screen.fill(Colors.BLACK)

        # Title
        title = self.title_font.render('Snake Game', True, Colors.GREEN)
        title_rect = title.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 150))
        self.screen.blit(title, title_rect)

        # Difficulty selection
        difficulty_text = self.font.render(f'Difficulty: {list(self.config.keys())[0]}', True, Colors.WHITE)
        difficulty_rect = difficulty_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 50))
        self.screen.blit(difficulty_text, difficulty_rect)

        # Instructions
        instructions = [
            'Press SPACE to Start',
            'Use Arrow Keys to Move',
            'Eat Apples to Grow',
            'Avoid Walls and Yourself',
            f'You Have {self.lives} Lives',
            'Collect Power-Ups for Bonuses',
            'Press A to View Achievements'  # New line
        ]

        for i, line in enumerate(instructions):
            text = self.font.render(line, True, Colors.WHITE)
            text_rect = text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + i*40))
            self.screen.blit(text, text_rect)

        pygame.display.update()

    def draw_game_over_screen(self):
        """Render an enhanced game over screen with interactive elements."""
        # Create a semi-transparent overlay
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Transparent black
        self.screen.blit(overlay, (0, 0))

        # Game Over Title with pulsing effect
        current_time = pygame.time.get_ticks()
        pulse_scale = 1 + 0.1 * math.sin(current_time * 0.01)

        game_over_font = pygame.font.Font(None, int(64 * pulse_scale))
        game_over = game_over_font.render('GAME OVER', True, Colors.RED)
        game_over_rect = game_over.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 220))

        # Rotate game over text slightly for dynamic effect
        rotated_game_over = pygame.transform.rotate(game_over, math.sin(current_time * 0.01) * 5)
        rotated_rect = rotated_game_over.get_rect(center=game_over_rect.center)
        self.screen.blit(rotated_game_over, rotated_rect)

        # Score Display with shadow effect
        score_font = pygame.font.Font(None, 48)

        # Shadow effect
        shadow_score = score_font.render(f'Your Score: {self.score}', True, Colors.GRAY)
        self.screen.blit(shadow_score, (GameConfig.SCREEN_WIDTH//2 - shadow_score.get_width()//2 + 3,
                                    GameConfig.SCREEN_HEIGHT//2 - 120 + 3))

        # Actual score
        score_text = score_font.render(f'Your Score: {self.score}', True, Colors.WHITE)
        score_rect = score_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 120))
        self.screen.blit(score_text, score_rect)

        # High Score
        high_score_text = score_font.render(f'High Score: {self.high_score}', True, Colors.GOLD)
        high_score_rect = high_score_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 70))
        self.screen.blit(high_score_text, high_score_rect)

        # Interactive Buttons
        button_font = pygame.font.Font(None, 36)
        button_y_start = GameConfig.SCREEN_HEIGHT//2

        # Restart Button
        restart_text = button_font.render('Restart Game', True, Colors.GREEN)
        restart_rect = restart_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, button_y_start + 10))

        # High Scores Button
        high_scores_text = button_font.render('View High Scores', True, Colors.BLUE)
        high_scores_rect = high_scores_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, button_y_start + 50))

        # Achievements Button
        achievements_text = button_font.render('View Achievements', True, Colors.GOLD)
        achievements_rect = achievements_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, button_y_start + 80))

        # Exit Button
        exit_text = button_font.render('Exit Game', True, Colors.RED)
        exit_rect = exit_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, button_y_start + 110))

        # Hover effects
        mouse_pos = pygame.mouse.get_pos()

        # Restart button hover
        if restart_rect.collidepoint(mouse_pos):
            restart_text = button_font.render('Restart Game', True, Colors.WHITE)

        # High Scores button hover
        if high_scores_rect.collidepoint(mouse_pos):
            high_scores_text = button_font.render('View High Scores', True, Colors.WHITE)

        # Achievements button hover
        if achievements_rect.collidepoint(mouse_pos):
            achievements_text = button_font.render('View Achievements', True, Colors.WHITE)

        # Exit button hover
        if exit_rect.collidepoint(mouse_pos):
            exit_text = button_font.render('Exit Game', True, Colors.WHITE)

        # Blit buttons
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(high_scores_text, high_scores_rect)
        self.screen.blit(achievements_text, achievements_rect)
        self.screen.blit(exit_text, exit_rect)

        # Store button rects for click handling
        self.game_over_buttons = {
            'restart': restart_rect,
            'high_scores': high_scores_rect,
            'achievements': achievements_rect,
            'exit': exit_rect
        }

        pygame.display.update()

    def show_challenge_notification(self):
        """Display a notification when challenge mode activates."""
        notification_text = [
            "CHALLENGE MODE ACTIVATED!",
            f"Time Limit: {self.challenge_mode['time_limit']} seconds",
            f"Target Score: {self.challenge_mode['target_score']} points"
        ]

        # Create notification overlay
        overlay = pygame.Surface((self.config['screen']['width'], self.config['screen']['height']), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black

        # Display notification
        y_offset = self.config['screen']['height'] // 3
        for line in notification_text:
            text = self.font.render(line, True, (255, 255, 255))
            rect = text.get_rect(center=(self.config['screen']['width'] // 2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 40

        # Update display and pause briefly
        pygame.display.update()
        pygame.time.wait(2000)  # Show notification for 2 seconds

    def run(self):
        """
        Main game loop with enhanced challenge mode and achievement tracking.
        Manages game states, challenge mode, and overall game progression.
        """

        # Initial game setup
        should_start_challenge, difficulty_multiplier = self.initialize_challenge_mode()

        if should_start_challenge:
            # Create and adjust challenge settings
            base_settings = GameEnhancements.create_challenge_mode(self)
            adjusted_settings = self.apply_challenge_mode_difficulty(
                base_settings,
                difficulty_multiplier
            )

            # Start challenge mode with adjusted settings
            self.challenge_mode = adjusted_settings

            # Optional: Notify player about challenge mode
            self.show_challenge_notification()

        while True:
            # Handle events
            self.handle_events()

            # Render appropriate screen based on game state
            if self.game_state == 'START':
                self.draw_start_screen()
                self.clock.tick(10)  # Slower refresh for start screen
                continue

            elif self.game_state == 'GAME_OVER':
                self.draw_game_over_screen()
                self.clock.tick(10)  # Slower refresh for game over screen
                continue

            elif self.game_state == 'PAUSED':
                # Existing pause screen logic
                pause_overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT), pygame.SRCALPHA)
                pause_overlay.fill((128, 128, 128, 128))
                self.screen.blit(pause_overlay, (0, 0))

                pause_text = self.title_font.render('PAUSED', True, Colors.WHITE)
                pause_rect = pause_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2))
                self.screen.blit(pause_text, pause_rect)

                unpause_text = self.small_font.render('Press P to Resume', True, Colors.WHITE)
                unpause_rect = unpause_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 50))
                self.screen.blit(unpause_text, unpause_rect)

                mute_text = self.small_font.render('Press M to Mute/Unmute', True, Colors.WHITE)
                mute_rect = mute_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 80))
                self.screen.blit(mute_text, mute_rect)

                pygame.display.update()
                self.clock.tick(10)
                continue

            # Challenge mode specific logic
            if self.challenge_mode:
                # Check time limit
                current_time = pygame.time.get_ticks()
                time_elapsed = (current_time - self.challenge_start_time) / 1000  # Convert to seconds

                # Check if time limit exceeded
                if time_elapsed > self.challenge_mode['time_limit']:
                    print("Challenge Mode: Time Limit Exceeded!")
                    self.game_state = 'GAME_OVER'
                    continue

                # Check target score
                if self.score >= self.challenge_mode['target_score']:
                    print("Challenge Mode: Target Score Achieved!")
                    # Potential bonus or special reward
                    self.score += 50  # Bonus points
                    # Reset challenge mode
                    self.challenge_mode = None
                    self.current_mission = None

                # Mission progress tracking
                if self.current_mission:
                    # You can add more specific mission tracking here
                    pass

            # Game playing state
            # Move snake
            self.move_snake()

            # Check for power-up collisions
            self.check_power_up_collision()

            # Check achievements
            achievements = AchievementManager.check_achievements(self)
            if achievements:
                for achievement in achievements:
                    print(f"Achievement Unlocked: {achievement['name']}")
                    # Optional: Add a sound effect or visual notification
                    try:
                        self.sound_manager.play_sound('achievement')
                    except Exception:
                        # Fallback if achievement sound is not defined
                        pass

            # Check for collisions
            if not self.check_collision():
                continue

            # Draw game state
            self.draw_game()

            # Control game speed
            self.clock.tick(self.current_speed)

def main():
    """Entry point of the game."""
    # You could add difficulty selection logic here in the future
    game = SnakeGame(difficulty='MEDIUM')
    game.run()

if __name__ == '__main__':
    main()
