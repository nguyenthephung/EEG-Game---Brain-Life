import pygame
import math

class Character:
    """
    Character class implementing vector-based movement system
    Based on research methodology for eye-controlled character movement
    """
    
    def __init__(self):
        # Position and dimensions
        self.width = 40
        self.height = 60
        self.x = 600  # Start at center of screen
        self.y = 800 - 80  # Above ground level
        
        # Movement vector (research-based)
        self.velocity = 0.0  # Initially 0 (character stands still)
        self.max_speed = 1.0
        self.speed_increment = 0.1
        
        # Visual properties
        self.color = (0, 100, 255)  # Blue character
        self.direction = 0  # -1 left, 0 idle, 1 right
        
        # Animation
        self.animation_frame = 0
        self.animation_speed = 0.2
        
        print("👤 Character initialized at center position")
    
    def move_left(self):
        """
        Decrease vector magnitude by 0.1 units (research specification)
        Negative vector makes character move left
        """
        self.velocity -= self.speed_increment
        self.velocity = max(self.velocity, -self.max_speed)
        self.direction = -1
        print(f"⬅️ Moving left, velocity: {self.velocity:.2f}")
    
    def move_right(self):
        """
        Increase vector magnitude by 0.1 units (research specification) 
        Positive vector makes character move right
        """
        self.velocity += self.speed_increment
        self.velocity = min(self.velocity, self.max_speed)
        self.direction = 1
        print(f"➡️ Moving right, velocity: {self.velocity:.2f}")
    
    def stop(self):
        """
        Set vector magnitude to 0 immediately (research specification)
        Allows character to stop with no delay
        """
        self.velocity = 0.0
        self.direction = 0
        print("⏹ Character stopped")
    
    def increase_speed(self):
        """
        Command 7: Two successive similar movements increase speed
        """
        current_speed = abs(self.velocity)
        new_speed = min(current_speed + self.speed_increment, self.max_speed)
        self.velocity = new_speed if self.velocity >= 0 else -new_speed
        print(f"⚡ Speed increased to: {abs(self.velocity):.2f}")
    
    def decrease_speed(self):
        """
        Command 8: Two successive opposite movements decrease speed
        """
        current_speed = abs(self.velocity)
        new_speed = max(current_speed - self.speed_increment, 0)
        self.velocity = new_speed if self.velocity >= 0 else -new_speed
        print(f"🐌 Speed decreased to: {abs(self.velocity):.2f}")
    
    def update(self, dt: float):
        """
        Update character position based on velocity vector
        dt: delta time in seconds
        """
        # Move character based on velocity (pixels per frame)
        movement_speed = self.velocity * 300 * dt  # Scale for smooth movement
        self.x += movement_speed
        
        # Keep character within screen bounds
        self.x = max(self.width // 2, min(self.x, 1200 - self.width // 2))
        
        # Update animation
        if abs(self.velocity) > 0.01:
            self.animation_frame += self.animation_speed
            if self.animation_frame >= 4:
                self.animation_frame = 0
        else:
            self.animation_frame = 0
    
    def draw(self, screen):
        """Draw character with simple animation"""
        # Character body (rectangle)
        char_rect = pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height,
            self.width,
            self.height
        )
        pygame.draw.rect(screen, self.color, char_rect)
        
        # Character head (circle)
        head_radius = self.width // 3
        pygame.draw.circle(screen, self.color,
                         (int(self.x), int(self.y - self.height - head_radius)),
                         head_radius)
        
        # Movement indicator
        if abs(self.velocity) > 0.01:
            # Draw arrow indicating direction
            arrow_length = 30
            arrow_x = self.x + (arrow_length * (1 if self.velocity > 0 else -1))
            arrow_y = self.y - self.height // 2
            
            # Arrow body
            pygame.draw.line(screen, (255, 255, 0),
                           (self.x, arrow_y), (arrow_x, arrow_y), 3)
            
            # Arrow head
            if self.velocity > 0:  # Right arrow
                pygame.draw.polygon(screen, (255, 255, 0), [
                    (arrow_x, arrow_y),
                    (arrow_x - 10, arrow_y - 5),
                    (arrow_x - 10, arrow_y + 5)
                ])
            else:  # Left arrow
                pygame.draw.polygon(screen, (255, 255, 0), [
                    (arrow_x, arrow_y),
                    (arrow_x + 10, arrow_y - 5),
                    (arrow_x + 10, arrow_y + 5)
                ])
        
        # Speed indicator (bar above character)
        if abs(self.velocity) > 0:
            bar_width = 50
            bar_height = 6
            bar_x = self.x - bar_width // 2
            bar_y = self.y - self.height - 40
            
            # Background bar
            pygame.draw.rect(screen, (50, 50, 50),
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Speed bar (proportional to velocity)
            speed_ratio = abs(self.velocity) / self.max_speed
            speed_width = int(bar_width * speed_ratio)
            speed_color = (255, int(255 * (1 - speed_ratio)), 0)  # Red to yellow
            
            pygame.draw.rect(screen, speed_color,
                           (bar_x, bar_y, speed_width, bar_height))
    
    def check_collision(self, meteor) -> bool:
        """
        Check collision with meteor using rectangular collision detection
        Returns True if collision occurred
        """
        char_rect = pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height,
            self.width,
            self.height
        )
        
        meteor_rect = pygame.Rect(
            meteor.x - meteor.size // 2,
            meteor.y - meteor.size // 2,
            meteor.size,
            meteor.size
        )
        
        return char_rect.colliderect(meteor_rect)
    
    def reset(self):
        """Reset character to initial state"""
        self.x = 600  # Center position
        self.velocity = 0.0
        self.direction = 0
        self.animation_frame = 0
        print("👤 Character reset to initial position")
