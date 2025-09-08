#!/usr/bin/env python3
"""
EOG TCP Server
Sends EOG commands from the processor to the game via TCP connection
"""

import socket
import json
import time
import threading
from typing import Optional, List

class EOGTCPServer:
    """
    TCP Server that sends EOG commands to the game
    Implements research interface: EOG Classification → Game via TCP/IP
    """
    
    def __init__(self, eog_processor):
        self.eog_processor = eog_processor
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[socket.socket] = []
        self.running = False
        
        # Server settings
        self.host = "localhost"
        self.port = 8766
        
        # Command tracking
        self.last_command = "idle"
        self.command_count = 0
        
        print(f"🔌 EOG TCP Server initialized on {self.host}:{self.port}")
    
    def start(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"📡 EOG TCP Server listening on {self.host}:{self.port}")
            print("🎮 Waiting for game connection...")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"🎮 Game connected from {address}")
                    
                    self.clients.append(client_socket)
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"❌ Server error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.stop()
    
    def _handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        try:
            while self.running:
                # Keep connection alive
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Client {address} error: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            print(f"🔌 Game disconnected: {address}")
    
    def send_command(self, command: str):
        """Send EOG command to all connected games"""
        if not self.clients:
            return
        
        self.command_count += 1
        self.last_command = command
        
        # Create command message
        message = {
            "command": command,
            "timestamp": time.time(),
            "sequence": self.command_count
        }
        
        message_str = json.dumps(message) + "\n"
        
        # Send to all connected clients
        for client in self.clients[:]:  # Copy list to avoid modification during iteration
            try:
                client.send(message_str.encode('utf-8'))
                print(f"📡 Sent to game: {command} (#{self.command_count})")
            except Exception as e:
                print(f"❌ Failed to send to client: {e}")
                if client in self.clients:
                    self.clients.remove(client)
                try:
                    client.close()
                except:
                    pass
    
    def stop(self):
        """Stop the server and close all connections"""
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("🔌 EOG TCP Server stopped")
    
    def get_status(self):
        """Get server status"""
        return {
            "running": self.running,
            "connected_clients": len(self.clients),
            "last_command": self.last_command,
            "command_count": self.command_count
        }

# Mock EOG processor for testing
class MockEOGProcessor:
    """Mock EOG processor for testing TCP server"""
    
    def __init__(self):
        self.tcp_server = EOGTCPServer(self)
        self.current_movement = "idle"
    
    def start_tcp_server(self):
        """Start the TCP server in a separate thread"""
        server_thread = threading.Thread(target=self.tcp_server.start, daemon=True)
        server_thread.start()
        return server_thread
    
    def simulate_eog_detection(self, command: str):
        """Simulate EOG command detection and send to game"""
        self.current_movement = command
        self.tcp_server.send_command(command)
        print(f"🧠 EOG Detection: {command}")

if __name__ == "__main__":
    # Test the TCP server
    print("🧪 Testing EOG TCP Server")
    
    mock_processor = MockEOGProcessor()
    server_thread = mock_processor.start_tcp_server()
    
    try:
        print("📡 Server started. Testing command sending...")
        time.sleep(2)
        
        # Simulate some commands
        commands = ["left", "right", "idle", "blink", "up", "down", "center"]
        
        for i, command in enumerate(commands * 3):  # Repeat 3 times
            mock_processor.simulate_eog_detection(command)
            time.sleep(1.5)  # Send every 1.5 seconds
            
            if i % 7 == 6:  # Every cycle
                print(f"📊 Server status: {mock_processor.tcp_server.get_status()}")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        mock_processor.tcp_server.stop()
        print("✅ Test completed")
