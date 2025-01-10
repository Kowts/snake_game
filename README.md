# Advanced Snake Game

## Overview
This is an enhanced version of the classic Snake game, featuring multiple difficulty levels, power-ups, moving food, and various gameplay mechanics.

## Features

### Gameplay Mechanics
- Classic Snake game with advanced features
- Multiple difficulty levels (Easy, Medium, Hard)
- Moving food items
- Power-up system
- Screen shake effect
- Sound effects and background music
- High score tracking

### Difficulty Levels
- **Easy**:
  - 5 lives
  - Slower initial speed
  - Higher power-up spawn chance
  - Lower score per apple

- **Medium** (Default):
  - 3 lives
  - Balanced speed and difficulty
  - Moderate power-up spawn chance
  - Standard score per apple

- **Hard**:
  - 1 life
  - Faster initial speed
  - Lower power-up spawn chance
  - Higher score per apple

### Power-ups
Three unique power-ups to enhance gameplay:
1. **Speed Boost**: Temporarily increases snake speed
2. **Invincibility**: Protects snake from collisions
3. **Extra Points**: Instantly adds bonus points to score

### Achievements
Track your performance with in-game achievements:
- Longest snake length
- Maximum speed reached
- Total apples eaten

## Controls

### Game Navigation
- **SPACE**: Start game / Restart after game over
- **P**: Pause/Unpause game
- **M**: Mute/Unmute sound
- **H**: View high scores

### Snake Movement
- **Arrow Keys**: Control snake direction
  - Up Arrow: Move Up
  - Down Arrow: Move Down
  - Left Arrow: Move Left
  - Right Arrow: Move Right

## Requirements
- Python 3.7+
- Pygame
- NumPy
- SciPy

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/snake-game.git
cd snake-game
```

2. Install required dependencies
```bash
pip install pygame numpy scipy
```

3. Run the game
```bash
python main.py
```

## Logging
The game generates a `snake_game.log` file to track game events and potential issues.

## High Scores
High scores are persistently stored in `highscores.json` and displayed on the high scores screen.

## Customization
- Modify `GameConfig` class to adjust game parameters
- Extend `PowerUp.TYPES` to add new power-ups
- Customize difficulty levels

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
[Insert your license information here]

## Acknowledgments
- Pygame for game development framework
- Inspiration from classic Snake game
