import pygame
import random
import math
from typing import List, Tuple

class Reward:
    """
    Reward item that falls slowly from the top
    Player can shoot these with bullets (blink command)
    """
    
    def __init__(self, x: float, y: float = -50):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 0.5  # Slower than meteors
        self.value = 100  # Points when collected/shot
        
        # Visual properties
        self.color = (255, 215, 0)  # Gold color
        self.outline_color = (255, 255, 255)
        self.shine_offset = 0
        
        # Physics
        self.active = True
        self.collected = False
        
    def update(self, dt: float):
        """Update reward position and animation"""
        if not self.active:
            return
            
        # Move down slowly
        self.y += self.speed * dt * 60  # 60 FPS normalization
        
        # Shine animation
        self.shine_offset += dt * 3
        if self.shine_offset > 2 * math.pi:
            self.shine_offset = 0
            
        # Remove if off screen
        if self.y > 850:  # Screen height + buffer
            self.active = False
    
    def draw(self, screen: pygame.Surface):
        """Draw the reward with golden shine effect"""
        if not self.active:
            return
            
        # Main reward body (star shape)
        center = (int(self.x), int(self.y))
        
        # Draw star shape
        points = []
        for i in range(10):  # 5-pointed star (10 points total)
            angle = (i * math.pi / 5) + self.shine_offset * 0.1
            if i % 2 == 0:
                # Outer points
                radius = self.width // 2
            else:
                # Inner points
                radius = self.width // 4
                
            point_x = center[0] + radius * math.cos(angle)
            point_y = center[1] + radius * math.sin(angle)
            points.append((point_x, point_y))
        
        # Draw star
        pygame.draw.polygon(screen, self.color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 2)
        
        # Shine effect
        shine_alpha = int(128 + 127 * math.sin(self.shine_offset))
        shine_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(shine_surface, (*self.color, shine_alpha//2), 
                         (self.width//2, self.height//2), self.width//3)
        screen.blit(shine_surface, (self.x - self.width//2, self.y - self.height//2))
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                          self.width, self.height)
    
    def collect(self):
        """Mark reward as collected"""
        self.collected = True
        self.active = False


class RewardSpawner:
    """
    Manages spawning and lifecycle of rewards
    Spawns rewards less frequently than meteors
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rewards: List[Reward] = []
        
        # Spawning parameters
        self.spawn_timer = 0
        self.spawn_interval = 8.0  # Spawn every 8 seconds (slower than meteors)
        self.max_rewards = 3  # Maximum rewards on screen
        
        # Difficulty scaling
        self.game_time = 0
        self.difficulty_factor = 1.0
        
    def update(self, dt: float):
        """Update all rewards and spawning"""
        self.game_time += dt
        
        # Update difficulty (more frequent spawning over time)
        self.difficulty_factor = 1.0 + (self.game_time / 60.0) * 0.3  # 30% faster per minute
        effective_interval = self.spawn_interval / self.difficulty_factor
        
        # Spawning logic
        self.spawn_timer += dt
        if (self.spawn_timer >= effective_interval and 
            len([r for r in self.rewards if r.active]) < self.max_rewards):
            self.spawn_reward()
            self.spawn_timer = 0
        
        # Update existing rewards
        active_rewards = []
        for reward in self.rewards:
            reward.update(dt)
            if reward.active:
                active_rewards.append(reward)
        
        self.rewards = active_rewards
    
    def spawn_reward(self):
        """Spawn a new reward at random position"""
        # Random x position with margins
        margin = 50
        x = random.randint(margin, self.screen_width - margin)
        
        reward = Reward(x)
        self.rewards.append(reward)
    
    def draw(self, screen: pygame.Surface):
        """Draw all active rewards"""
        for reward in self.rewards:
            reward.draw(screen)
    
    def get_active_rewards(self) -> List[Reward]:
        """Get list of active rewards"""
        return [r for r in self.rewards if r.active]
    
    def clear_all(self):
        """Clear all rewards"""
        self.rewards.clear()
        self.spawn_timer = 0
        self.game_time = 0
        self.difficulty_factor = 1.0
