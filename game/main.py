#!/usr/bin/env python3
"""
🎮 EOG Meteor Dodge Game - MAIN ENTRY POINT
This is the main game file that connects to EOG processor automatically
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import game
from meteor_dodge_game import MeteorDodgeGame

def main():
    """Main game entry point - connects to EOG processor automatically"""
    print("🎮 EOG Meteor Dodge Game - Main Entry Point")
    print("=" * 50)
    print("📡 Connecting to EOG processor on localhost:8766...")
    print("🧠 Make sure EOG app is running: python main.py")
    print()
    print("🎯 Game will be controlled by eye movements:")
    print("   👁️ Left/Right - Move character")
    print("   👁️ Up/Down/Blink/Center - Stop character")
    print()
    print("⚡ Debug controls (if EOG not connected):")
    print("   SPACE - Start/Stop Game")
    print("   ← → ↓ - Move character")
    print("   P - Pause, R - Reset, ESC - Exit")
    print()
    
    # Wait a moment for user to read
    time.sleep(2)
    
    try:
        # Create and start game
        game = MeteorDodgeGame()
        print("✅ Game initialized - Starting game loop...")
        print("🎮 Press SPACE to start game once window opens")
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
