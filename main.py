import pygame
from scipy.io import wavfile
import sys
import random
import json
import logging
import os

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
    GRAY = (128, 128, 128)
    BLUE = (0, 0, 255)
    GOLD = (255, 215, 0)
    HOT_PINK = (255, 105, 180)

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

class PowerUp:
    """Enhanced Power-up class with duration and type management."""
    TYPES = {
        'speed_boost': {
            'color': Colors.BLUE,
            'duration': 5000,  # 5 seconds
            'effect': lambda game: setattr(game, 'current_speed', min(game.current_speed + 2, GameConfig.MAX_SPEED))
        },
        'invincibility': {
            'color': Colors.GOLD,
            'duration': 3000,  # 3 seconds
            'effect': lambda game: game.set_invincibility(True)
        },
        'extra_points': {
            'color': Colors.HOT_PINK,
            'duration': 0,  # Immediate effect
            'effect': lambda game: setattr(game, 'score', game.score + 5)
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
        self.config['effect'](game)

    def is_expired(self):
        """Check if power-up has expired."""
        return self.config['duration'] > 0 and \
               pygame.time.get_ticks() - self.creation_time > self.config['duration']

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

class SnakeGame:
    def __init__(self, difficulty='MEDIUM'):
        """Initialize the game with all necessary setup."""
        pygame.init()

        # Game configuration
        self.config = GameConfig.get_difficulty_config(difficulty)

        # Screen and display setup
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption('Advanced Snake Game')
        self.clock = pygame.time.Clock()

        # Sound management
        self.sound_manager = SoundManager()

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Game state tracking
        self.score = 0
        self.high_score = 0
        self.lives = self.config['lives']
        self.current_speed = self.config['initial_speed']
        self.power_up_chance = self.config['power_up_chance']
        self.is_invincible = False
        self.invincibility_timer = 0

        # Power-up system
        self.power_ups = []
        self.power_up_spawn_timer = 0

        # Achievements tracking
        self.achievements = {
            'longest_snake': 0,
            'max_speed_reached': self.current_speed,
            'total_apples_eaten': 0
        }

        # Game modes
        self.game_state = 'START'

        # Initialize game
        self.reset_game()

    def set_invincibility(self, state):
        """Set invincibility state and timer."""
        self.is_invincible = state
        if state:
            self.invincibility_timer = pygame.time.get_ticks()

    def reset_game(self):
        """Reset the game state to initial conditions."""
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
            self.current_speed = self.config['initial_speed']
            self.lives = self.config['lives']

        # Reset game state
        self.game_state = 'PLAYING'

    def generate_power_up(self):
        """Generate a random power-up on the map."""
        power_up_types = list(PowerUp.TYPES.keys())

        while True:
            x = random.randint(0, (GameConfig.SCREEN_WIDTH // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE
            y = random.randint(0, (GameConfig.SCREEN_HEIGHT // GameConfig.BLOCK_SIZE - 1)) * GameConfig.BLOCK_SIZE

            # Ensure power-up doesn't appear on snake body or existing power-ups
            if (x, y) not in self.snake and \
               not any(pu.x == x and pu.y == y for pu in self.power_ups):
                power_type = random.choice(power_up_types)
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
            if (x, y) not in self.snake and \
               not any(pu.x == x and pu.y == y for pu in self.power_ups):
                return (x, y)

    def draw_game(self):
        """Render all game elements on the screen."""
        # Clear screen
        self.screen.fill(Colors.BLACK)

        # Draw snake body with additional effect for invincibility
        for i, (x, y) in enumerate(self.snake):
            # Darker green for head, lighter for body
            body_color = Colors.GREEN
            if self.is_invincible:
                # Flash effect during invincibility
                body_color = Colors.GOLD if pygame.time.get_ticks() % 500 < 250 else Colors.GREEN

            if i == len(self.snake) - 1:
                pygame.draw.rect(self.screen, body_color, (x, y, GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))
            else:
                pygame.draw.rect(self.screen, Colors.DARK_GREEN, (x, y, GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))

        # Draw apple
        pygame.draw.rect(self.screen, Colors.RED, (self.apple[0], self.apple[1], GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE))

        # Draw power-ups
        for power_up in self.power_ups:
            pygame.draw.rect(
                self.screen,
                power_up.config['color'],
                (power_up.x, power_up.y, GameConfig.BLOCK_SIZE, GameConfig.BLOCK_SIZE)
            )

        # Draw score and lives
        score_text = self.font.render(f'Score: {self.score} High Score: {self.high_score}', True, Colors.WHITE)
        lives_text = self.font.render(f'Lives: {self.lives}', True, Colors.WHITE)
        speed_text = self.small_font.render(f'Speed: {self.current_speed:.1f}', True, Colors.WHITE)

        # Draw invincibility status
        if self.is_invincible:
            invincible_text = self.small_font.render('INVINCIBLE', True, Colors.GOLD)
            self.screen.blit(invincible_text, (10, 120))

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (10, 50))
        self.screen.blit(speed_text, (10, 90))

        # Update display
        pygame.display.update()

    def handle_events(self):
        """Process pygame events and handle game controls."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.game_state == 'START':
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()

            elif self.game_state == 'GAME_OVER':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Save high score before resetting
                        HighScoreManager.save_score(self.score)
                        self.reset_game()
                    elif event.key == pygame.K_h:
                        self.show_high_scores()

            elif self.game_state == 'PLAYING':
                # Pause functionality
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.game_state = 'PAUSED'

                # Movement controls
                if event.type == pygame.KEYDOWN:
                    # Prevent 180-degree turns
                    if event.key == pygame.K_UP and self.direction != 'DOWN':
                        self.direction = 'UP'
                    elif event.key == pygame.K_DOWN and self.direction != 'UP':
                        self.direction = 'DOWN'
                    elif event.key == pygame.K_LEFT and self.direction != 'RIGHT':
                        self.direction = 'LEFT'
                    elif event.key == pygame.K_RIGHT and self.direction != 'LEFT':
                        self.direction = 'RIGHT'

            elif self.game_state == 'PAUSED':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.game_state = 'PLAYING'
                    elif event.key == pygame.K_m:
                        # Toggle mute/unmute
                        self.sound_manager.set_volume(0 if self.sound_manager.volume > 0 else 0.5)

    def move_snake(self):
        """Move the snake based on current direction."""
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

        # Check if snake ate the apple
        if new_head == self.apple:
            # Play eat sound
            self.sound_manager.play_sound('eat')

            # Increase score based on difficulty
            self.score += self.config['apple_score']

            # Achievements tracking
            self.achievements['total_apples_eaten'] += 1

            # Increase speed gradually (up to max speed)
            self.current_speed = min(self.current_speed + 0.5, GameConfig.MAX_SPEED)

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

    def check_power_up_collision(self):
        """Check if snake collects a power-up."""
        head = self.snake[-1]

        for power_up in self.power_ups[:]:
            if head == (power_up.x, power_up.y):
                # Play power-up sound
                self.sound_manager.play_sound('power_up')

                # Apply power-up effect
                power_up.apply_effect(self)

                # Remove power-up
                self.power_ups.remove(power_up)

    def check_collision(self):
        """Check for collisions with walls or self."""
        head = self.snake[-1]

        # Ignore collision if invincible
        if self.is_invincible:
            return True

        # Wall collision
        if (head[0] < 0 or head[0] >= GameConfig.SCREEN_WIDTH or
            head[1] < 0 or head[1] >= GameConfig.SCREEN_HEIGHT):
            return self.handle_collision()

        # Self collision
        if head in self.snake[:-1]:
            return self.handle_collision()

        return True

    def handle_collision(self):
        """Handle snake collision, reduce lives or end game."""
        self.lives -= 1

        # Reset speed to initial speed when losing a life
        self.current_speed = self.config['initial_speed']

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
            'Collect Power-Ups for Bonuses'
        ]

        for i, line in enumerate(instructions):
            text = self.font.render(line, True, Colors.WHITE)
            text_rect = text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + i*40))
            self.screen.blit(text, text_rect)

        pygame.display.update()

    def draw_game_over_screen(self):
        """Render the game over screen with achievements."""
        self.screen.fill(Colors.BLACK)

        # Game Over Title
        game_over = self.title_font.render('Game Over', True, Colors.RED)
        game_over_rect = game_over.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 200))
        self.screen.blit(game_over, game_over_rect)

        # Score Display
        score_text = self.font.render(f'Your Score: {self.score}', True, Colors.WHITE)
        score_rect = score_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 100))
        self.screen.blit(score_text, score_rect)

        # High Score
        high_score_text = self.font.render(f'High Score: {self.high_score}', True, Colors.WHITE)
        high_score_rect = high_score_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 - 50))
        self.screen.blit(high_score_text, high_score_rect)

        # Achievements
        achievements_title = self.font.render('Achievements:', True, Colors.GREEN)
        achievements_rect = achievements_title.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2))
        self.screen.blit(achievements_title, achievements_rect)

        # Display achievements
        achievements_list = [
            f'Longest Snake: {self.achievements["longest_snake"]} segments',
            f'Max Speed Reached: {self.achievements["max_speed_reached"]:.1f}',
            f'Total Apples Eaten: {self.achievements["total_apples_eaten"]}'
        ]

        for i, achievement in enumerate(achievements_list):
            achievement_text = self.small_font.render(achievement, True, Colors.WHITE)
            achievement_rect = achievement_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + i*30 + 50))
            self.screen.blit(achievement_text, achievement_rect)

        # Restart and High Scores Instructions
        restart_text = self.small_font.render('Press SPACE to Restart', True, Colors.GRAY)
        restart_rect = restart_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 180))
        self.screen.blit(restart_text, restart_rect)

        high_scores_text = self.small_font.render('Press H to View High Scores', True, Colors.GRAY)
        high_scores_rect = high_scores_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 210))
        self.screen.blit(high_scores_text, high_scores_rect)

        pygame.display.update()

    def run(self):
        """Main game loop."""
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
                # Draw a pause overlay
                pause_overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT), pygame.SRCALPHA)
                pause_overlay.fill((128, 128, 128, 128))
                self.screen.blit(pause_overlay, (0, 0))

                pause_text = self.title_font.render('PAUSED', True, Colors.WHITE)
                pause_rect = pause_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2))
                self.screen.blit(pause_text, pause_rect)

                # Add pause instructions
                unpause_text = self.small_font.render('Press P to Resume', True, Colors.WHITE)
                unpause_rect = unpause_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 50))
                self.screen.blit(unpause_text, unpause_rect)

                mute_text = self.small_font.render('Press M to Mute/Unmute', True, Colors.WHITE)
                mute_rect = mute_text.get_rect(center=(GameConfig.SCREEN_WIDTH//2, GameConfig.SCREEN_HEIGHT//2 + 80))
                self.screen.blit(mute_text, mute_rect)

                pygame.display.update()
                self.clock.tick(10)
                continue

            # Game playing state
            # Move snake
            self.move_snake()

            # Check for power-up collisions
            self.check_power_up_collision()

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
