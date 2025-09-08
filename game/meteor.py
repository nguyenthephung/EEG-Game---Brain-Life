import pygame
import random
import math

class Meteor:
    """
    Meteor class implementing falling obstacle mechanics
    Based on research: semirandom meteor patterns with physics
    """
    
    def __init__(self, x: float, y: float):
        # Position
        self.x = x
        self.y = y
        
        # Size and appearance
        self.size = random.randint(20, 40)
        self.color = (255, 100 + random.randint(0, 100), 0)  # Orange variations
        
        # Physics (from research)
        self.speed = 0.1  # Initial speed (research specification)
        self.max_speed = 0.1  # Maximum speed (research specification)
        self.acceleration = 0.01  # Downward acceleration (research specification)
        
        # Visual effects
        self.rotation = 0
        self.rotation_speed = random.uniform(-5, 5)
        self.trail_positions = []
        
        # Difficulty scaling
        self.difficulty_multiplier = 1.0
    
    def update(self, dt: float):
        """
        Update meteor position with physics
        dt: delta time in seconds
        """
        # Apply acceleration (research: 0.01 units downward)
        self.speed += self.acceleration * dt * 60  # Scale for frame rate
        self.speed = min(self.speed, self.max_speed * 10)  # Reasonable max speed
        
        # Move downward
        movement = self.speed * 300 * dt  # Scale for pixel movement
        self.y += movement
        
        # Update rotation for visual effect
        self.rotation += self.rotation_speed * dt * 60
        if self.rotation >= 360:
            self.rotation -= 360
        
        # Update trail effect
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)
    
    def draw(self, screen):
        """Draw meteor with visual effects"""
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail_positions):
            alpha = (i + 1) / len(self.trail_positions)
            trail_size = self.size * alpha * 0.5
            trail_color = (
                int(self.color[0] * alpha),
                int(self.color[1] * alpha * 0.5),
                0
            )
            
            if trail_size > 2:
                pygame.draw.circle(screen, trail_color,
                                 (int(trail_x), int(trail_y)), int(trail_size))
        
        # Draw main meteor body
        pygame.draw.circle(screen, self.color,
                         (int(self.x), int(self.y)), self.size)
        
        # Draw meteor details (rocky texture simulation)
        detail_color = (
            max(0, self.color[0] - 50),
            max(0, self.color[1] - 30),
            0
        )
        
        # Small rock details
        for i in range(3):
            detail_x = self.x + math.cos(self.rotation + i * 120) * (self.size * 0.3)
            detail_y = self.y + math.sin(self.rotation + i * 120) * (self.size * 0.3)
            detail_size = max(2, self.size // 6)
            
            pygame.draw.circle(screen, detail_color,
                             (int(detail_x), int(detail_y)), detail_size)
        
        # Core highlight
        highlight_x = self.x - self.size * 0.2
        highlight_y = self.y - self.size * 0.2
        highlight_size = max(3, self.size // 4)
        highlight_color = (255, 200, 100)
        
        pygame.draw.circle(screen, highlight_color,
                         (int(highlight_x), int(highlight_y)), highlight_size)
    
    def set_difficulty(self, difficulty: float):
        """
        Scale meteor properties based on difficulty level
        difficulty: 1.0 = normal, >1.0 = harder
        """
        self.difficulty_multiplier = difficulty
        self.max_speed = 0.1 * difficulty
        self.acceleration = 0.01 * difficulty
        
        # Larger meteors for higher difficulty
        if difficulty > 1.5:
            self.size = min(self.size * 1.2, 60)

class MeteorSpawner:
    """
    Manages meteor spawning according to research specifications:
    - 5 spawn points evenly distributed across screen top
    - Semirandomized release times and delays
    - Average 3 meteors per repetition
    - No more than 5 meteors at once
    """
    
    def __init__(self, screen_width: int):
        self.screen_width = screen_width
        
        # 5 spawn points evenly distributed (research specification)
        self.spawn_points = [
            screen_width * 0.1,   # Point 1
            screen_width * 0.3,   # Point 2
            screen_width * 0.5,   # Point 3
            screen_width * 0.7,   # Point 4
            screen_width * 0.9    # Point 5
        ]
        
        # Spawn timing for each point (semirandomized)
        self.spawn_timers = [0.0] * 5
        self.spawn_delays = [random.uniform(2.0, 5.0) for _ in range(5)]
        
        # Global spawn control
        self.last_spawn_time = 0
        self.spawn_cooldown = 0.5  # Minimum time between any spawns
        
        # Difficulty progression
        self.difficulty = 1.0
        self.difficulty_increase_rate = 0.01
        
        print("☄️ Meteor spawner initialized with 5 spawn points")
    
    def update(self, dt: float, meteors: list) -> list:
        """
        Update spawn timers and create new meteors
        Returns list of new meteors to add
        """
        current_time = pygame.time.get_ticks() / 1000.0
        new_meteors = []
        
        # Don't spawn if at maximum capacity
        if len(meteors) >= 5:  # MAX_METEORS from research
            return new_meteors
        
        # Check cooldown
        if current_time - self.last_spawn_time < self.spawn_cooldown:
            return new_meteors
        
        # Update each spawn point
        for i, spawn_x in enumerate(self.spawn_points):
            self.spawn_timers[i] += dt
            
            # Check if this point should spawn
            if self.spawn_timers[i] >= self.spawn_delays[i]:
                # Spawn probability (average 3 meteors per cycle)
                if random.random() < 0.6:  # 60% chance when timer expires
                    meteor = Meteor(spawn_x, 0)
                    meteor.set_difficulty(self.difficulty)
                    new_meteors.append(meteor)
                    
                    self.last_spawn_time = current_time
                    print(f"☄️ Meteor spawned at point {i+1} (x={spawn_x:.0f})")
                
                # Reset timer with new random delay
                self.spawn_timers[i] = 0
                self.spawn_delays[i] = random.uniform(1.5, 4.0)
        
        # Gradually increase difficulty
        self.difficulty += self.difficulty_increase_rate * dt
        
        return new_meteors
    
    def reset(self):
        """Reset spawner to initial state"""
        self.spawn_timers = [0.0] * 5
        self.spawn_delays = [random.uniform(2.0, 5.0) for _ in range(5)]
        self.last_spawn_time = 0
        self.difficulty = 1.0
        print("🔄 Meteor spawner reset")
