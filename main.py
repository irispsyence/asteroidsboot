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
    """Load high scores from file, return empty dict with mode keys if file doesn't exist"""
    if os.path.exists(HIGH_SCORES_FILE):
        with open(HIGH_SCORES_FILE, 'r') as f:
            scores = json.load(f)
            
            # Handle migration from old format (list) to new format (dict)
            if isinstance(scores, list):
                # Old format detected - migrate to new format
                scores = {
                    "original": scores,  # Put old scores in original mode
                    "time_attack": [],
                    "one_in_chamber": [],
                    "master_of_evasion": []
                }
                save_high_scores(scores)  # Save migrated format
                return scores
            
            # Ensure all modes exist (for new format)
            if "original" not in scores:
                scores["original"] = []
            if "time_attack" not in scores:
                scores["time_attack"] = []
            if "one_in_chamber" not in scores:
                scores["one_in_chamber"] = []
            if "master_of_evasion" not in scores:
                scores["master_of_evasion"] = []
            return scores
    return {"original": [], "time_attack": [], "one_in_chamber": [], "master_of_evasion": []}

def save_high_scores(scores):
    """Save high scores to file"""
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)

def add_score(mode, score, time_elapsed, shots_remaining=None):
    """Add new score and return rank (1-5) if it's a high score, otherwise None"""
    high_scores = load_high_scores()

    new_entry = {
        "score": score,
        "time": time_elapsed,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if mode == "one_in_chamber":
        new_entry["shots_remaining"] = shots_remaining

    high_scores[mode].append(new_entry)
    
    # Sort based on mode-specific criteria
    if mode == "original":
        # 1) Highest score, 2) Lowest time
        high_scores[mode].sort(key=lambda x: (-x["score"], x["time"]))
    elif mode == "time_attack":
        # 1) Highest score, 2) Less time remaining (higher time_elapsed = survived longer)
        high_scores[mode].sort(key=lambda x: (-x["score"], -x["time"]))
    elif mode == "one_in_chamber":
        # 1) Highest score, 2) Most shots remaining, 3) Lowest time
        high_scores[mode].sort(key=lambda x: (-x["score"], -x["shots_remaining"], x["time"]))
    elif mode == "master_of_evasion":
        # 1) Longest survival time (highest time)
        high_scores[mode].sort(key=lambda x: -x["time"])
    
    high_scores[mode] = high_scores[mode][:5]  # Keep only top 5

    save_high_scores(high_scores)

    # Find rank of new score
    for i, entry in enumerate(high_scores[mode]):
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

def show_menu(screen):
    """Display game mode selection menu and return selected mode"""
    font_title = pygame.font.Font(None, 72)
    font_option = pygame.font.Font(None, 48)
    font_desc = pygame.font.Font(None, 28)
    
    title_text = font_title.render("ASTEROIDS", True, "white")
    
    modes = [
        ("1", "Original", "Classic asteroids survival"),
        ("2", "Time Attack", "Survive for 5 minutes"),
        ("3", "One In The Chamber", "Limited shots - hit to reload")
    ]
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "original"
                elif event.key == pygame.K_2:
                    return "time_attack"
                elif event.key == pygame.K_3:
                    return "one_in_chamber"
        
        screen.fill("black")
        
        # Draw title
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw menu options
        y_offset = 250
        for key, name, desc in modes:
            option_text = font_option.render(f"{key}. {name}", True, "cyan")
            desc_text = font_desc.render(desc, True, "gray")
            
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 35))
            
            screen.blit(option_text, option_rect)
            screen.blit(desc_text, desc_rect)
            
            y_offset += 100
        
        instruction_text = font_desc.render("Press 1, 2, or 3 to select", True, "yellow")
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()

def display_game_over(screen, mode, score, elapsed_time, shots_remaining=None, master_of_evasion=False):
    """Display game over screen with high scores"""
    rank = add_score(mode, score, elapsed_time, shots_remaining)
    high_scores = load_high_scores()
    
    print("\n" + "="*60)
    print("GAME OVER!")
    print("="*60)
    
    if master_of_evasion or mode == "master_of_evasion":
        print("🌟 MASTER OF EVASION!!! 🌟")
        if mode == "master_of_evasion":
            print("You missed your only shot but survived as long as you could!")
        else:
            print("You survived 5 minutes without hitting a single asteroid!")
        print()
    
    print(f"Mode: {mode.replace('_', ' ').title()}")
    
    if mode != "master_of_evasion":
        print(f"Your Score: {score}")
    
    if mode == "time_attack":
        print(f"Time Survived: {format_time(elapsed_time)} / 05:00")
    elif mode == "master_of_evasion":
        print(f"Time Survived: {format_time(elapsed_time)} / 05:00")
    else:
        print(f"Time Survived: {format_time(elapsed_time)}")
    
    if mode == "one_in_chamber" and shots_remaining is not None:
        print(f"Shots Remaining: {shots_remaining}")
    
    print()
    
    if rank:
        print(f"🎉 NEW HIGH SCORE! You are #{rank} on the Leaderboard! 🎉")
        print()
    
    print(f"TOP 5 HIGH SCORES - {mode.replace('_', ' ').upper()}:")
    print("-"*60)
    
    for i, entry in enumerate(high_scores[mode]):
        marker = "→ " if (rank and i == rank - 1) else "  "
        if mode == "one_in_chamber":
            print(f"{marker}{i+1}. Score: {entry['score']:>6} | Time: {format_time(entry['time'])} | Shots: {entry['shots_remaining']:>3} | {entry['date']}")
        elif mode == "master_of_evasion":
            print(f"{marker}{i+1}. Time: {format_time(entry['time'])} | {entry['date']}")
        else:
            print(f"{marker}{i+1}. Score: {entry['score']:>6} | Time: {format_time(entry['time'])} | {entry['date']}")
    
    print("="*60 + "\n")

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Show menu and get selected mode
    game_mode = show_menu(screen)
    
    # Set up game groups
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    Player.containers = (updatable, drawable)

    asteroids = pygame.sprite.Group()
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable,)

    shots = pygame.sprite.Group()
    Shot.containers = (shots, updatable, drawable)

    font = pygame.font.Font(None, 36)
    score = 0
    start_time = pygame.time.get_ticks()
    shots_remaining = 1 if game_mode == "one_in_chamber" else None
    evasion_mode_activated = False  # Track if we switched to evasion mode
    evasion_start_time = None  # Track when evasion mode started
    zero_shots_zero_score_time = None  # Track when player first had 0 shots and 0 score
    
    # Time Attack mode settings
    time_limit = 300 if game_mode == "time_attack" else None  # 5 minutes = 300 seconds

    clock = pygame.time.Clock()
    dt = 0
    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    
    # Modify player shooting for One In The Chamber mode
    if game_mode == "one_in_chamber":
        player.game_mode = "one_in_chamber"
        player.shots_remaining = shots_remaining
    
    print(f"Starting Asteroids - {game_mode.replace('_', ' ').title()} Mode")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

    asteroid_field = AsteroidField()

    while True:
        log_state()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        screen.fill("black")
        
        # Handle input for One In The Chamber mode
        if game_mode == "one_in_chamber":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and player.can_shoot and shots_remaining > 0:
                # Player wants to shoot and has shots
                player.shoot()
                shots_remaining -= 1
            
            # Update for regular movement
            player.update(dt)
            
            # Update other objects
            for obj in updatable:
                if obj != player:
                    obj.update(dt)
        else:
            # Normal update for other modes
            updatable.update(dt)

        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000.0

        # One In The Chamber: Check if player has 0 shots and 0 score for 5 seconds
        if game_mode == "one_in_chamber" and not evasion_mode_activated:
            if shots_remaining == 0 and score == 0:
                # Start or continue tracking
                if zero_shots_zero_score_time is None:
                    zero_shots_zero_score_time = pygame.time.get_ticks()
                else:
                    # Check if 5 seconds have passed
                    time_in_zero_state = (pygame.time.get_ticks() - zero_shots_zero_score_time) / 1000.0
                    if time_in_zero_state >= 5.0:
                        # Activate Master of Evasion mode
                        evasion_mode_activated = True
                        evasion_start_time = pygame.time.get_ticks()
                        print("\n🌟 MASTER OF EVASION MODE ACTIVATED! 🌟")
                        print("You missed your shot! Survive for 5 minutes!\n")
            else:
                # Reset the timer if they gain shots or points
                zero_shots_zero_score_time = None

        # Calculate evasion time if in evasion mode
        evasion_elapsed = 0
        if evasion_mode_activated:
            evasion_elapsed = (pygame.time.get_ticks() - evasion_start_time) / 1000.0

        # Check if survived 5 minutes in evasion mode
        if evasion_mode_activated and evasion_elapsed >= 300:  # 5 minutes
            display_game_over(screen, "master_of_evasion", 0, evasion_elapsed)
            sys.exit()

        # Time Attack mode: Check if time limit reached (WIN CONDITION)
        if game_mode == "time_attack" and elapsed_time >= time_limit:
            master_of_evasion = (score == 0)
            display_game_over(screen, game_mode, score, elapsed_time, master_of_evasion=master_of_evasion)
            sys.exit()

        # Check player collision with asteroids
        for asteroid in asteroids:
            if player.collides_with(asteroid):
                log_event("player_hit")
                
                if evasion_mode_activated:
                    # In evasion mode, show evasion time instead
                    display_game_over(screen, "master_of_evasion", 0, evasion_elapsed)
                elif game_mode == "one_in_chamber":
                    display_game_over(screen, game_mode, score, elapsed_time, shots_remaining)
                else:
                    display_game_over(screen, game_mode, score, elapsed_time)
                
                sys.exit()

        # Check shot collisions with asteroids
        for asteroid in asteroids:
            for shot in shots:
                if asteroid.collides_with(shot):
                    # Award points based on asteroid size
                    if asteroid.radius >= ASTEROID_MIN_RADIUS * 3:  # Large
                        score += 100
                        if game_mode == "one_in_chamber":
                            shots_remaining += 1
                    elif asteroid.radius >= ASTEROID_MIN_RADIUS * 2:  # Medium
                        score += 200
                        if game_mode == "one_in_chamber":
                            shots_remaining += 2
                    else:  # Small
                        score += 300
                        if game_mode == "one_in_chamber":
                            shots_remaining += 3

                    log_event("asteroid_shot")
                    asteroid.split()
                    shot.kill()
                    break

        # Draw all sprites
        for sprite in drawable:
            sprite.draw(screen)

        # Display HUD based on mode
        score_text = font.render(f"Score: {score}", True, "white")
        screen.blit(score_text, (10, 10))
        
        if evasion_mode_activated:
            # Show Master of Evasion countdown
            time_remaining = max(0, 300 - evasion_elapsed)
            mode_text = font.render("MASTER OF EVASION MODE", True, "gold")
            time_text = font.render(f"Time: {format_time(time_remaining)}", True, "yellow")
            shots_text = font.render(f"Shots: 0", True, "red")
            screen.blit(mode_text, (10, 50))
            screen.blit(time_text, (10, 90))
            screen.blit(shots_text, (10, 130))
        elif game_mode == "time_attack":
            time_remaining = max(0, time_limit - elapsed_time)
            time_text = font.render(f"Time: {format_time(time_remaining)}", True, "yellow")
            screen.blit(time_text, (10, 50))
        elif game_mode == "one_in_chamber":
            time_text = font.render(f"Time: {format_time(elapsed_time)}", True, "yellow")
            shots_text = font.render(f"Shots: {shots_remaining}", True, "cyan")
            screen.blit(time_text, (10, 50))
            screen.blit(shots_text, (10, 90))
        else:  # Original mode
            time_text = font.render(f"Time: {format_time(elapsed_time)}", True, "yellow")
            screen.blit(time_text, (10, 50))

        pygame.display.flip()

        dt = clock.tick(60) / 1000

if __name__ == "__main__":
    main()
