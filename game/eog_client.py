import socket
import json
import threading
import time
import queue
from typing import Optional, Dict, Any

class EOGClient:
    """
    TCP client to receive EOG commands from the classification module
    Implements research interface: Classification Module ↔ Game Module via TCP/IP
    """
    
    def __init__(self, game_instance):
        self.game = game_instance
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        
        # Connection settings
        self.host = "localhost"
        self.port = 8766  # Different from websocket port (8765)
        
        # Command processing
        self.command_queue = queue.Queue()
        self.last_command_time = 0
        self.command_interval = 1.0  # 1 second intervals (research specification)
        
        # Threading
        self.receive_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        print(f"📡 EOG Client initialized - Ready to connect to {self.host}:{self.port}")
    
    def start(self):
        """Start the EOG client and connection threads"""
        self.running = True
        
        # Start connection thread
        self.receive_thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.receive_thread.start()
        
        # Start command processing thread
        self.process_thread = threading.Thread(target=self._process_commands, daemon=True)
        self.process_thread.start()
        
        print("📡 EOG Client started")
    
    def stop(self):
        """Stop the EOG client and close connections"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("📡 EOG Client stopped")
    
    def _connection_loop(self):
        """Main connection loop - attempts to connect and receive data"""
        retry_delay = 2.0
        
        while self.running:
            try:
                if not self.connected:
                    self._attempt_connection()
                    if not self.connected:
                        time.sleep(retry_delay)
                        continue
                
                # Receive data
                self._receive_data()
                
            except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                print(f"📡 Connection lost: {e}")
                self.connected = False
                if self.socket:
                    self.socket.close()
                    self.socket = None
                time.sleep(retry_delay)
            except Exception as e:
                print(f"📡 Unexpected error: {e}")
                time.sleep(retry_delay)
    
    def _attempt_connection(self):
        """Attempt to connect to EOG classification server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"📡 Connected to EOG server at {self.host}:{self.port}")
        except (ConnectionRefusedError, socket.timeout):
            # Server not ready yet - silent retry (don't spam console)
            if self.socket:
                self.socket.close()
                self.socket = None
        except Exception as e:
            print(f"📡 Connection attempt failed: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
    
    def _receive_data(self):
        """Receive and parse EOG command data"""
        if not self.socket:
            return
        
        try:
            # Set a reasonable timeout for receiving
            self.socket.settimeout(1.0)
            data = self.socket.recv(1024)
            
            if not data:
                raise ConnectionResetError("No data received")
            
            # Parse JSON command(s) - handle multiple messages
            message_text = data.decode('utf-8')
            lines = message_text.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    try:
                        command_data = json.loads(line)
                        self.command_queue.put(command_data)
                    except json.JSONDecodeError as e:
                        print(f"📡 Invalid JSON line: {line[:50]}... Error: {e}")
                
        except socket.timeout:
            # Timeout is normal - just continue
            pass
    
    def _process_commands(self):
        """
        Process commands from queue with timing constraints
        Commands are processed every 1 second (research specification)
        """
        while self.running:
            try:
                current_time = time.time()
                
                # Check if enough time has passed since last command
                if current_time - self.last_command_time >= self.command_interval:
                    try:
                        # Get most recent command (non-blocking)
                        command_data = self.command_queue.get_nowait()
                        self._handle_command(command_data)
                        self.last_command_time = current_time
                        
                        # Clear any remaining commands (keep only most recent)
                        while not self.command_queue.empty():
                            try:
                                self.command_queue.get_nowait()
                            except queue.Empty:
                                break
                                
                    except queue.Empty:
                        # No commands available
                        pass
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"📡 Command processing error: {e}")
                time.sleep(0.5)
    
    def _handle_command(self, command_data: Dict[str, Any]):
        """
        Handle received EOG command and forward to game
        Expected format: {"command": "left|right|up|down|center|blink", "timestamp": 123.45}
        """
        try:
            command = command_data.get("command", "idle").lower()
            timestamp = command_data.get("timestamp", time.time())
            
            # Validate command
            valid_commands = ["left", "right", "up", "down", "center", "blink", "idle"]
            if command not in valid_commands:
                print(f"📡 Invalid command received: {command}")
                return
            
            # Map EOG classes to game commands (research specification)
            game_command = self._map_eog_to_game_command(command)
            
            # Forward to game
            if self.game and self.game.game_active:
                self.game.process_eog_command(game_command)
            
            print(f"📡 Processed: {command} → {game_command} (t={timestamp:.2f})")
            
        except Exception as e:
            print(f"📡 Error handling command: {e}")
    
    def _map_eog_to_game_command(self, eog_command: str) -> str:
        """
        Map 6 EOG classes to 3 game commands (research Table 2)
        
        Research mapping:
        - left, right → respective movement commands
        - center, up, down, blink → idle command
        """
        if eog_command == "left":
            return "left"
        elif eog_command == "right":
            return "right"
        else:  # center, up, down, blink
            return "idle"
    
    def send_game_state(self, game_state: Dict[str, Any]):
        """
        Send game state back to EOG server (optional feedback)
        Format: {"character_pos": x, "score": score, "meteors": count}
        """
        if not self.connected or not self.socket:
            return
        
        try:
            data = json.dumps(game_state).encode('utf-8')
            self.socket.send(data)
        except Exception as e:
            print(f"📡 Error sending game state: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status for UI display"""
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "commands_queued": self.command_queue.qsize(),
            "last_command_time": self.last_command_time
        }

class MockEOGServer:
    """
    Mock EOG server for testing game without actual EOG input
    Simulates eye movement commands for development/testing
    """
    
    def __init__(self, port: int = 8766):
        self.port = port
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None
        
        # Mock command patterns
        self.commands = ["left", "right", "idle", "center", "blink"]
        self.command_index = 0
        
    def start(self):
        """Start mock server for testing"""
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        print(f"🤖 Mock EOG server started on port {self.port}")
    
    def stop(self):
        """Stop mock server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        print("🤖 Mock EOG server stopped")
    
    def _server_loop(self):
        """Main server loop"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("localhost", self.port))
            self.server_socket.listen(1)
            
            print(f"🤖 Mock server listening on port {self.port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    self.client_socket, addr = self.server_socket.accept()
                    print(f"🤖 Game client connected: {addr}")
                    
                    self._handle_client()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"🤖 Server error: {e}")
                    
        except Exception as e:
            print(f"🤖 Server startup error: {e}")
    
    def _handle_client(self):
        """Handle connected game client"""
        try:
            while self.running and self.client_socket:
                # Send mock command every 2 seconds
                command = self.commands[self.command_index % len(self.commands)]
                self.command_index += 1
                
                command_data = {
                    "command": command,
                    "timestamp": time.time()
                }
                
                data = json.dumps(command_data).encode('utf-8')
                self.client_socket.send(data)
                
                print(f"🤖 Sent mock command: {command}")
                time.sleep(2.0)
                
        except Exception as e:
            print(f"🤖 Client handling error: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

# For testing - run mock server
if __name__ == "__main__":
    mock_server = MockEOGServer()
    mock_server.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mock_server.stop()
