#!/usr/bin/env python3
"""
🎮 Meteor Dodge Game - Standalone Test
EOG-controlled game that can run with keyboard controls for testing

CONTROLS:
- SPACE: Start/Stop Game
- Arrow Keys: Move character (debug mode)
- P: Pause/Resume
- R: Reset
- ESC: Exit

EOG Integration:
- Connect to TCP server on localhost:8766
- Receives commands: left, right, idle, blink, center, up, down
- Maps to character movement as per research
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import game
from meteor_dodge_game import MeteorDodgeGame

def main():
    """Main function to run the game"""
    print("🎮 EOG Meteor Dodge Game")
    print("=" * 30)
    print("📡 Will attempt to connect to EOG server on localhost:8766")
    print("🎮 If no server found, use keyboard controls for testing")
    print()
    print("🎯 Game Controls:")
    print("   SPACE - Start/Stop Game")
    print("   ← → ↓ - Move character (debug mode)")
    print("   P - Pause/Resume")
    print("   R - Reset")
    print("   ESC - Exit")
    print()
    print("🧠 EOG Commands (when connected):")
    print("   👁️ Left/Right - Move character")
    print("   👁️ Up/Down/Blink/Center - Stop character")
    print()
    
    try:
        game = MeteorDodgeGame()
        print("✅ Game initialized successfully")
        print("🚀 Starting game loop...")
        game.start_game()
        
    except KeyboardInterrupt:
        print("\n🛑 Game interrupted by user")
    except Exception as e:
        print(f"❌ Game error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Game ended. Thanks for playing!")

if __name__ == "__main__":
    main()
