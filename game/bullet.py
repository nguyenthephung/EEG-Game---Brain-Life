import pygame
import math
from typing import List, Tuple

class Bullet:
    """
    Bullet fired by character when blinking
    Travels upward to hit rewards
    """
    
    def __init__(self, start_x: float, start_y: float):
        self.x = start_x
        self.y = start_y
        self.width = 8
        self.height = 12
        self.speed = 5.0  # Fast upward movement
        
        # Visual properties
        self.color = (0, 255, 255)  # Cyan color
        self.trail_color = (0, 200, 200)
        self.active = True
        
        # Trail effect
        self.trail_positions = []
        self.max_trail_length = 5
        
    def update(self, dt: float):
        """Update bullet position and trail"""
        if not self.active:
            return
            
        # Store current position for trail
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
            
        # Move upward
        self.y -= self.speed * dt * 60  # 60 FPS normalization
        
        # Remove if off screen
        if self.y < -50:
            self.active = False
    
    def draw(self, screen: pygame.Surface):
        """Draw bullet with trail effect"""
        if not self.active:
            return
            
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail_positions):
            alpha = int(255 * (i + 1) / len(self.trail_positions))
            trail_surface = pygame.Surface((self.width//2, self.height//2), pygame.SRCALPHA)
            trail_surface.fill((*self.trail_color, alpha//2))
            screen.blit(trail_surface, (trail_x - self.width//4, trail_y - self.height//4))
        
        # Draw main bullet
        bullet_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                                 self.width, self.height)
        pygame.draw.ellipse(screen, self.color, bullet_rect)
        pygame.draw.ellipse(screen, (255, 255, 255), bullet_rect, 1)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                          self.width, self.height)
    
    def hit_target(self):
        """Mark bullet as hit target"""
        self.active = False


class BulletManager:
    """
    Manages all bullets fired by the character
    Handles collision detection with rewards
    """
    
    def __init__(self):
        self.bullets: List[Bullet] = []
        self.last_fire_time = 0
        self.fire_cooldown = 0.5  # 0.5 second cooldown between shots
        
        # Statistics
        self.bullets_fired = 0
        self.bullets_hit = 0
        
    def fire_bullet(self, character_x: float, character_y: float) -> bool:
        """
        Fire a bullet from character position
        Returns True if bullet was fired, False if on cooldown
        """
        import time
        current_time = time.time()
        
        if current_time - self.last_fire_time >= self.fire_cooldown:
            # Fire bullet from character's top
            bullet = Bullet(character_x, character_y - 30)
            self.bullets.append(bullet)
            
            self.bullets_fired += 1
            self.last_fire_time = current_time
            return True
        
        return False
    
    def update(self, dt: float):
        """Update all bullets"""
        active_bullets = []
        for bullet in self.bullets:
            bullet.update(dt)
            if bullet.active:
                active_bullets.append(bullet)
        
        self.bullets = active_bullets
    
    def draw(self, screen: pygame.Surface):
        """Draw all active bullets"""
        for bullet in self.bullets:
            bullet.draw(screen)
    
    def check_reward_collisions(self, rewards: List) -> List[Tuple[int, int]]:
        """
        Check collisions between bullets and rewards
        Returns list of (bullet_index, reward_index) collision pairs
        """
        collisions = []
        
        for bullet_idx, bullet in enumerate(self.bullets):
            if not bullet.active:
                continue
                
            bullet_rect = bullet.get_rect()
            
            for reward_idx, reward in enumerate(rewards):
                if not reward.active:
                    continue
                    
                reward_rect = reward.get_rect()
                
                if bullet_rect.colliderect(reward_rect):
                    collisions.append((bullet_idx, reward_idx))
                    bullet.hit_target()
                    self.bullets_hit += 1
                    break  # Bullet can only hit one reward
        
        return collisions
    
    def get_active_bullets(self) -> List[Bullet]:
        """Get list of active bullets"""
        return [b for b in self.bullets if b.active]
    
    def clear_all(self):
        """Clear all bullets"""
        self.bullets.clear()
    
    def get_accuracy(self) -> float:
        """Get shooting accuracy percentage"""
        if self.bullets_fired == 0:
            return 0.0
        return (self.bullets_hit / self.bullets_fired) * 100.0
    
    def reset_stats(self):
        """Reset shooting statistics"""
        self.bullets_fired = 0
        self.bullets_hit = 0
