#!/usr/bin/env python3
"""
🎮 Test standalone game với mock EOG data
Simple test để verify game integration với mock data

Usage: python game/test_standalone.py
"""

import sys
import os
import time
import threading
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from meteor_dodge_game import MeteorDodgeGame

class MockEOGGenerator:
    """Simple mock EOG command generator for testing"""
    
    def __init__(self, game):
        self.game = game
        self.running = False
        self.thread = None
        
    def start(self):
        """Start generating mock EOG commands"""
        self.running = True
        self.thread = threading.Thread(target=self._generate_commands, daemon=True)
        self.thread.start()
        print("🤖 Mock EOG generator started")
        
    def stop(self):
        """Stop generating commands"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("🛑 Mock EOG generator stopped")
        
    def _generate_commands(self):
        """Generate random EOG commands for testing"""
        commands = ["left", "right", "up", "down", "center"]
        
        while self.running:
            # Random command every 2-4 seconds
            time.sleep(random.uniform(2, 4))
            
            if self.running:
                cmd = random.choice(commands)
                print(f"👁️ Mock EOG: {cmd}")
                
                # Send command to game
                if hasattr(self.game, 'process_eog_command'):
                    self.game.process_eog_command(cmd)
                    
            # Random blink every 5-8 seconds
            if random.random() < 0.3:  # 30% chance
                time.sleep(random.uniform(1, 2))
                if self.running:
                    print("😉 Mock Blink!")
                    if hasattr(self.game, 'process_eog_command'):
                        self.game.process_eog_command("blink")

class TestStandaloneGame:
    """Standalone test game with mock EOG"""
    
    def __init__(self):
        self.game = None
        self.mock_eog = None
        
    def run(self):
        """Run the test game"""
        print("🎮 Test Standalone Game")
        print("=" * 40)
        print("🤖 Mock EOG commands will be generated automatically")
        print("👁️ Watch for eye movement simulations")
        print("� Try to dodge meteors and collect rewards")
        print("😉 Blinks will shoot bullets")
        print()
        print("⌨️ Keyboard controls also available:")
        print("   Arrow keys: Move")
        print("   Space: Shoot")
        print("   ESC: Quit")
        print()
        print("🚀 Starting game in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
            
        try:
            # Initialize game
            self.game = MeteorDodgeGame(debug_mode=True)
            
            # Start mock EOG generator
            self.mock_eog = MockEOGGenerator(self.game)
            self.mock_eog.start()
            
            print("✅ Game started!")
            print("🤖 Mock EOG active - automatic commands enabled")
            
            # Run game
            self.game.run()
            
        except Exception as e:
            print(f"❌ Game error: {e}")
            
        finally:
            # Cleanup
            if self.mock_eog:
                self.mock_eog.stop()
            print("🏁 Game ended")

def main():
    """Main function"""
    try:
        # Check if pygame is available
        import pygame
        pygame.init()
        
        # Check display
        info = pygame.display.Info()
        if info.bitsize == 0:
            print("❌ No display available")
            return 1
            
        print(f"📺 Display: {info.current_w}x{info.current_h}")
        
    except ImportError:
        print("❌ Pygame not installed")
        print("   Install with: pip install pygame")
        return 1
    except Exception as e:
        print(f"❌ Display error: {e}")
        return 1
    
    # Run test game
    test_game = TestStandaloneGame()
    test_game.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
