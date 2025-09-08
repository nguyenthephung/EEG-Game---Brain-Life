import pygame
import sys
import random
import time
import json
import socket
import threading
from typing import Optional, List, Tuple

# Import game components
from character import Character
from meteor import Meteor, MeteorSpawner
from reward import Reward, RewardSpawner
from bullet import Bullet, BulletManager
from eog_client import EOGClient
from game_evaluator import GameEvaluator

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)

# Game Physics
GRAVITY = 0.01
CHARACTER_SPEED_INCREMENT = 0.1
MAX_CHARACTER_SPEED = 1.0
METEOR_BASE_SPEED = 0.1
METEOR_ACCELERATION = 0.01
MAX_METEORS = 5
METEOR_SPAWN_POINTS = 5

class MeteorDodgeGame:
    """
    Main game class implementing the EOG-controlled Meteor Dodge game
    Based on research: 2D platformer with obstacle evasion mechanics
    """
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EOG Meteor Dodge - Brain-Computer Interface Game")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.game_active = False
        self.paused = False
        
        # Initialize game components
        self.character = Character()
        self.meteors = []
        self.meteor_spawner = MeteorSpawner(SCREEN_WIDTH)
        self.reward_spawner = RewardSpawner(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.bullet_manager = BulletManager()
        self.eog_client = EOGClient(self)
        self.evaluator = GameEvaluator()
        
        # Game scoring
        self.score = 0
        self.rewards_collected = 0
        self.meteors_avoided = 0
        
        # Command system
        self.last_command = "idle"
        self.command_history = []
        self.command_timestamp = time.time()
        
        # UI elements
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        print("🎮 Meteor Dodge Game initialized")
        print("📡 Waiting for EOG commands...")
    
    def start_game(self):
        """Start the main game loop"""
        self.eog_client.start()
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            
            if self.game_active and not self.paused:
                self.update(dt)
            
            self.draw()
            
        self.cleanup()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.toggle_game()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                # Debug controls (for testing without EOG)
                elif event.key == pygame.K_LEFT:
                    self.process_eog_command("left")
                elif event.key == pygame.K_RIGHT:
                    self.process_eog_command("right")
                elif event.key == pygame.K_DOWN:
                    self.process_eog_command("idle")
    
    def toggle_game(self):
        """Toggle between game active and menu state"""
        self.game_active = not self.game_active
        if self.game_active:
            self.reset_game()
            print("🎮 Game Started - Use eye movements to control character")
        else:
            print("⏹ Game Stopped")
    
    def reset_game(self):
        """Reset game to initial state"""
        self.character.reset()
        self.meteors.clear()
        self.meteor_spawner.reset()
        self.reward_spawner.clear_all()
        self.bullet_manager.clear_all()
        self.bullet_manager.reset_stats()
        self.evaluator.reset()
        self.command_history.clear()
        
        # Reset scoring
        self.score = 0
        self.rewards_collected = 0
        self.meteors_avoided = 0
        
        print("🔄 Game Reset")
    
    def process_eog_command(self, command: str):
        """
        Process EOG command and update character movement
        Based on research Table 2 command mapping
        """
        current_time = time.time()
        
        # Add to command history for analysis
        self.command_history.append({
            'command': command,
            'timestamp': current_time,
            'character_pos': self.character.x
        })
        
        # Keep only recent history (last 10 commands)
        if len(self.command_history) > 10:
            self.command_history.pop(0)
        
        # Process command according to research methodology
        if command == "left":
            self.character.move_left()
            self.evaluator.record_command("left", self.character.x)
        elif command == "right":
            self.character.move_right()
            self.evaluator.record_command("right", self.character.x)
        elif command == "blink":
            # 👁️ BLINK = FIRE BULLET!
            bullet_fired = self.bullet_manager.fire_bullet(self.character.x, self.character.y)
            if bullet_fired:
                print("💥 Bullet fired!")
            self.evaluator.record_command("blink", self.character.x)
        else:  # idle, up, down, center
            self.character.stop()
            self.evaluator.record_command("idle", self.character.x)
        
        # Advanced command detection (Command 7-8 from research)
        self.check_advanced_commands()
        
        self.last_command = command
        self.command_timestamp = current_time
        
        print(f"🧠 EOG Command: {command} | Character Speed: {self.character.velocity:.2f}")
    
    def check_advanced_commands(self):
        """
        Detect advanced commands from sequence patterns
        Command 7: Two successive similar movements → Speed up
        Command 8: Two successive opposite movements → Speed down
        """
        if len(self.command_history) >= 2:
            last_two = [cmd['command'] for cmd in self.command_history[-2:]]
            
            # Command 7: Double same direction
            if last_two[0] == last_two[1] and last_two[0] in ["left", "right"]:
                self.character.increase_speed()
                print("⚡ Speed Boost! (Double same direction)")
            
            # Command 8: Opposite directions
            elif (last_two == ["left", "right"] or last_two == ["right", "left"]):
                self.character.decrease_speed()
                print("🐌 Speed Reduced! (Opposite directions)")
    
    def update(self, dt: float):
        """Update game state"""
        # Update character
        self.character.update(dt)
        
        # Spawn meteors (semirandom pattern from research)
        new_meteors = self.meteor_spawner.update(dt, self.meteors)
        self.meteors.extend(new_meteors)
        
        # Update meteors
        for meteor in self.meteors[:]:
            meteor.update(dt)
            
            # Remove meteors that hit ground
            if meteor.y > SCREEN_HEIGHT:
                self.meteors.remove(meteor)
                self.meteors_avoided += 1  # Count avoided meteors
        
        # 🎁 Update rewards
        self.reward_spawner.update(dt)
        
        # 💥 Update bullets
        self.bullet_manager.update(dt)
        
        # 🎯 Check bullet-reward collisions
        bullet_reward_collisions = self.bullet_manager.check_reward_collisions(
            self.reward_spawner.get_active_rewards()
        )
        
        # Process reward hits
        for bullet_idx, reward_idx in bullet_reward_collisions:
            reward = self.reward_spawner.rewards[reward_idx]
            reward.collect()
            self.score += reward.value
            self.rewards_collected += 1
            print(f"🎯 Reward shot! +{reward.value} points | Total: {self.score}")
        
        # Check direct character-reward collisions (backup collection method)
        character_rect = self.character.get_rect()
        for reward in self.reward_spawner.get_active_rewards():
            reward_rect = reward.get_rect()
            if character_rect.colliderect(reward_rect):
                reward.collect()
                self.score += reward.value // 2  # Half points for direct collection
                self.rewards_collected += 1
                print(f"🎁 Reward collected! +{reward.value//2} points | Total: {self.score}")
        
        # Check meteor-character collisions (separate loop)
        for meteor in self.meteors[:]:
            # Check collision with character
            if self.character.check_collision(meteor):
                self.evaluator.record_collision(meteor.x, self.character.x)
                self.meteors.remove(meteor)
                print(f"💥 Collision! Score: {self.evaluator.get_score()}")
            else:
                # Check if meteor was successfully avoided
                if meteor.y > SCREEN_HEIGHT - 100:  # Near ground level
                    self.evaluator.record_meteor_avoided()
    
    def draw(self):
        """Render game graphics"""
        self.screen.fill(BLACK)
        
        if not self.game_active:
            self.draw_menu()
        else:
            self.draw_game()
            
        if self.paused:
            self.draw_pause_overlay()
        
        pygame.display.flip()
    
    def draw_menu(self):
        """Draw main menu"""
        title = self.font.render("EOG Meteor Dodge", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.small_font.render("Brain-Computer Interface Game", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
        self.screen.blit(subtitle, subtitle_rect)
        
        instructions = [
            "SPACE - Start/Stop Game",
            "P - Pause/Resume", 
            "R - Reset Game",
            "ESC - Exit",
            "",
            "EOG Control (when connected):",
            "👁️ Left/Right - Move character",
            "👁️ Up/Down/Blink/Center - Stop character",
            "",
            "Debug Control (for testing):",
            "← → Keys - Move character",
            "↓ Key - Stop character"
        ]
        
        y_offset = SCREEN_HEIGHT // 2 - 20
        for instruction in instructions:
            text = self.small_font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30
    
    def draw_game(self):
        """Draw game elements"""
        # Draw platform (ground)
        pygame.draw.rect(self.screen, GRAY, 
                        (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        
        # Draw character
        self.character.draw(self.screen)
        
        # Draw meteors
        for meteor in self.meteors:
            meteor.draw(self.screen)
        
        # 🎁 Draw rewards
        self.reward_spawner.draw(self.screen)
        
        # 💥 Draw bullets
        self.bullet_manager.draw(self.screen)
        
        # Draw UI
        self.draw_hud()
    
    def draw_hud(self):
        """Draw heads-up display"""
        # Command info
        command_text = f"Last Command: {self.last_command.upper()}"
        text = self.small_font.render(command_text, True, WHITE)
        self.screen.blit(text, (10, 10))
        
        # Character speed
        speed_text = f"Speed: {self.character.velocity:.2f}"
        text = self.small_font.render(speed_text, True, WHITE)
        self.screen.blit(text, (10, 35))
        
        # 🎯 New scoring system
        total_score_text = f"Total Score: {self.score}"
        text = self.small_font.render(total_score_text, True, YELLOW)
        self.screen.blit(text, (10, 60))
        
        rewards_text = f"Rewards Shot: {self.rewards_collected}"
        text = self.small_font.render(rewards_text, True, (255, 215, 0))  # Gold
        self.screen.blit(text, (10, 85))
        
        meteors_text = f"Meteors Avoided: {self.meteors_avoided}"
        text = self.small_font.render(meteors_text, True, GREEN)
        self.screen.blit(text, (10, 110))
        
        # 💥 Shooting accuracy
        accuracy = self.bullet_manager.get_accuracy()
        accuracy_text = f"Shooting Accuracy: {accuracy:.1f}%"
        text = self.small_font.render(accuracy_text, True, (0, 255, 255))  # Cyan
        self.screen.blit(text, (10, 135))
        
        # Performance metrics (EOG evaluation)
        metrics = self.evaluator.get_metrics()
        if metrics:
            precision_text = f"EOG Precision: {metrics['precision']:.1f}%"
            sensitivity_text = f"EOG Sensitivity: {metrics['sensitivity']:.1f}%"
            specificity_text = f"EOG Specificity: {metrics['specificity']:.1f}%"
            
            text = self.small_font.render(precision_text, True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH - 220, 10))
            
            text = self.small_font.render(sensitivity_text, True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH - 220, 35))
            
            text = self.small_font.render(specificity_text, True, GREEN)
            self.screen.blit(text, (SCREEN_WIDTH - 220, 60))
        
        # 🎮 Game instructions
        instructions_text = "BLINK to SHOOT • ← → to MOVE • SPACE to START"
        text = self.small_font.render(instructions_text, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(text, text_rect)
    
    def draw_pause_overlay(self):
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)
    
    def cleanup(self):
        """Cleanup resources"""
        self.eog_client.stop()
        pygame.quit()
        print("🎮 Game shut down")

if __name__ == "__main__":
    game = MeteorDodgeGame()
    game.start_game()
