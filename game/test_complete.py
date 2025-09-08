#!/usr/bin/env python3
"""
🎮 EOG Game Integration Test
Complete test for EOG-controlled Meteor Dodge Game

This file tests the complete pipeline:
EOG Detection → TCP Server → Game Client → Character Movement
"""

import sys
import os
import time
import threading
import subprocess
import json
import socket

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_complete_integration():
    """Test the complete EOG → Game integration"""
    print("🎮 EOG Game Integration Test")
    print("=" * 50)
    
    # Option 1: Test with mock EOG commands
    print("\n🤖 OPTION 1: Mock EOG Commands Test")
    print("-" * 30)
    print("1. Run this script: python test_complete.py")
    print("2. Start game: python test_standalone.py")
    print("3. Press SPACE to start game")
    print("4. Watch character move with mock commands")
    
    # Option 2: Test with real EOG
    print("\n🧠 OPTION 2: Real EOG Integration Test") 
    print("-" * 30)
    print("1. Run main EOG app: python ../main.py")
    print("2. Connect BLE device")
    print("3. Start eye tracking")
    print("4. Start game: python test_standalone.py")
    print("5. Use eye movements to control character")
    
    print("\n🚀 Starting Mock EOG Server...")
    print("📡 Server will send commands to game every 2 seconds")
    print("🎮 Start the game now with: python test_standalone.py")
    print("⏹ Press Ctrl+C to stop")
    
    start_mock_eog_server()

def start_mock_eog_server():
    """Start mock EOG server that sends test commands"""
    try:
        # Import and start TCP server
        from eog_tcp_server import MockEOGProcessor
        
        mock_processor = MockEOGProcessor()
        server_thread = mock_processor.start_tcp_server()
        
        print("📡 Mock EOG TCP Server started on localhost:8766")
        
        # Send test commands (EOG classes that processor actually sends)
        commands = [
            "center", "left", "left", "center", 
            "right", "right", "center",
            "blink", "center", "up", "down",  # These will map to idle
            "left", "right", "center"
        ]
        
        print("🧠 Starting command sequence...")
        counter = 0
        
        while True:
            command = commands[counter % len(commands)]
            mock_processor.simulate_eog_detection(command)
            
            counter += 1
            time.sleep(2)  # Send command every 2 seconds (research spec)
            
            # Status update every 10 commands
            if counter % 10 == 0:
                status = mock_processor.tcp_server.get_status()
                print(f"📊 Status: {status['connected_clients']} clients, {status['command_count']} commands sent")
                
    except KeyboardInterrupt:
        print("\n🛑 Mock EOG server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'mock_processor' in locals():
            mock_processor.tcp_server.stop()

def quick_connection_test():
    """Quick test to verify TCP connection works"""
    print("🔌 Quick Connection Test")
    print("-" * 25)
    
    try:
        # Test socket connection
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        
        print("📡 Testing connection to localhost:8766...")
        test_socket.connect(("localhost", 8766))
        print("✅ Connection successful!")
        
        # Send test message
        test_message = json.dumps({"command": "test", "timestamp": time.time()}) + "\n"
        test_socket.send(test_message.encode('utf-8'))
        print("✅ Test message sent!")
        
        test_socket.close()
        return True
        
    except ConnectionRefusedError:
        print("❌ Connection refused - No server running")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎮 EOG Meteor Dodge - Integration Test Suite")
    print("=" * 50)
    
    choice = input("""
Choose test mode:
1. 🤖 Mock EOG Server (recommended for testing)
2. 🔌 Quick Connection Test
3. 📋 Show Integration Instructions

Enter choice (1-3): """).strip()
    
    if choice == "1":
        test_complete_integration()
    elif choice == "2":
        success = quick_connection_test()
        if not success:
            print("\n💡 Start the mock server first:")
            print("   python eog_tcp_server.py")
    elif choice == "3":
        test_complete_integration()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
