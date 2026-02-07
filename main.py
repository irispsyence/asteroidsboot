import pygame
import sys
import random
import json
import os
from datetime import datetime
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, ASTEROID_MIN_RADIUS
from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot

HIGH_SCORES_FILE = "high_scores.json"

def load_high_scores():
    """Load high scores from file, return empty list if file doesn't exist"""
    if os.path.exists(HIGH_SCORES_FILE):
        with open(HIGH_SCORES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_high_scores(scores):
    """Save high scores to file"""
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)

def add_score(score, time_elapsed):
    """Add new score and return rank (1-5) if it's a high score, otherwise None"""
    high_scores = load_high_scores()
    
    new_entry = {
        "score": score,
        "time": time_elapsed,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    high_scores.append(new_entry)
    high_scores.sort(key=lambda x: x["score"], reverse=True)
    high_scores = high_scores[:5]  # Keep only top 5
    
    save_high_scores(high_scores)
    
    # Find rank of new score
    for i, entry in enumerate(high_scores):
        if (entry["score"] == score and 
            entry["time"] == time_elapsed and 
            entry["date"] == new_entry["date"]):
            return i + 1  # Return rank (1-based)
    
    return None  # Not in top 5

def format_time(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def main():
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    Player.containers = (updatable, drawable)

    asteroids = pygame.sprite.Group()
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable,)

    shots = pygame.sprite.Group()
    Shot.containers = (shots, updatable, drawable)

    pygame.init()
    font = pygame.font.Font(None, 36)  # Add font for score display
    score = 0  # Initialize score
    start_time = pygame.time.get_ticks()

    clock = pygame.time.Clock()
    dt = 0
    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

    asteroid_field = AsteroidField()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while True:
        log_state()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        screen.fill("black")
        updatable.update(dt)
        
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000.0

        for asteroid in asteroids:
            if player.collides_with(asteroid):
                log_event("player_hit")

                rank = add_score(score, elapsed_time)
                high_scores = load_high_scores()

                print("\n" + "="*50)
                print("GAME OVER!")
                print("="*50)
                print(f"Your Score: {score}")
                print(f"Time Survived: {format_time(elapsed_time)}")
                print()

                if rank:
                    print(f"🎉 NEW HIGH SCORE! You are #{rank} on the Leaderboard! 🎉")
                    print()
                
                print("TOP 5 HIGH SCORES:")
                print("-"*50)
                for i, entry in enumerate(high_scores):
                    marker = "→ " if (rank and i == rank - 1) else "  "
                    print(f"{marker}{i+1}. Score: {entry['score']:>6} | Time: {format_time(entry['time'])} | {entry['date']}")
                print("="*50 + "\n")

                sys.exit()
        
        for asteroid in asteroids:
            for shot in shots:
                if asteroid.collides_with(shot):
                    if asteroid.radius >= ASTEROID_MIN_RADIUS * 3:  # Large
                        score += 100
                    elif asteroid.radius >= ASTEROID_MIN_RADIUS * 2:  # Medium
                        score += 200
                    else:  # Small
                        score += 300
                    
                    log_event("asteroid_shot")
                    asteroid.split()
                    shot.kill()
                    break
        

        for sprite in drawable:
            sprite.draw(screen)

        score_text = font.render(f"Score: {score}", True, "white")
        time_text = font.render(f"Time: {format_time(elapsed_time)}", True, "red")
        screen.blit(score_text, (10, 10))
        screen.blit(time_text, (10, 50))

        pygame.display.flip()

        dt = clock.tick(60) / 1000

if __name__ == "__main__":
    main()
