#!/usr/bin/env python3
"""
🎮 Main App with Mock EEG Integration
Runs the main BLE app using mock EEG data instead of real device

Usage:
1. python main_mock.py - Start with mock data
2. Select mental states from UI
3. Watch real-time charts and EOG/EEG processing
4. Test game integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# Import existing components
from ble.ble_decoder import BLEPacketDecoder
from ui.chart_manager import EOGChartManager
from signal_processing.eeg_processor import EOGProcessor
from utils.websocket_server import WebSocketServer
from mock_ble_adapter import MockBLEAdapter
import asyncio

class MockBLEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BrainLife EOG Eye Tracker - MOCK MODE")
        
        # Core components
        self.decoder = BLEPacketDecoder()
        self.chart_manager = EOGChartManager(self.root)
        self.eog_processor = EOGProcessor(self.decoder, self.chart_manager)
        
        # Mock adapter instead of real BLE manager
        self.mock_adapter = MockBLEAdapter(self.decoder, self.chart_manager, self.eog_processor)
        
        # WebSocket server for external connections
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.websocket_server = WebSocketServer(self.loop, self.eog_processor)
        
        # 🎮 Start game TCP server for EOG commands
        self.eog_processor.start_game_server()
        
        self.running = True
        self.streaming_active = False
        self.setup_ui()
        self.websocket_server.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10)

        # Mock Device Control Frame
        mock_frame = tk.LabelFrame(main_frame, text="🧠 Mock EEG Device", font=("Arial", 10))
        mock_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Status
        self.connection_status = tk.Label(mock_frame, text="📡 Mock Device Ready", font=("Arial", 10), fg="green")
        self.connection_status.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Control buttons
        tk.Button(mock_frame, text="🚀 Start Streaming", command=self.start_streaming).grid(row=1, column=0, padx=5)
        tk.Button(mock_frame, text="⏹ Stop Streaming", command=self.stop_streaming).grid(row=1, column=1, padx=5)
        tk.Button(mock_frame, text="📊 Reset Buffers", command=self.reset_buffers).grid(row=1, column=2, padx=5)

        # Mental State Control Frame
        state_frame = tk.LabelFrame(main_frame, text="🧠 Mental State Control", font=("Arial", 10))
        state_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # State selection
        tk.Label(state_frame, text="Select State:").grid(row=0, column=0, padx=5)
        self.state_var = tk.StringVar(value="resting")
        states = ["resting", "focused", "stressed", "meditation", "left_thinking", "right_thinking"]
        self.state_combo = ttk.Combobox(state_frame, textvariable=self.state_var, values=states, state="readonly")
        self.state_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(state_frame, text="🔄 Apply State", command=self.change_state).grid(row=0, column=2, padx=5)
        
        # Manual parameter controls
        tk.Label(state_frame, text="Alertness:").grid(row=1, column=0, padx=5, sticky="w")
        self.alertness_scale = tk.Scale(state_frame, from_=0, to=100, orient="horizontal", length=120)
        self.alertness_scale.set(50)
        self.alertness_scale.grid(row=1, column=1, padx=5)
        
        tk.Label(state_frame, text="Focus:").grid(row=2, column=0, padx=5, sticky="w")
        self.focus_scale = tk.Scale(state_frame, from_=0, to=100, orient="horizontal", length=120)
        self.focus_scale.set(50)
        self.focus_scale.grid(row=2, column=1, padx=5)
        
        tk.Button(state_frame, text="⚙️ Apply Manual", command=self.apply_manual_params).grid(row=2, column=2, padx=5)

        # EOG Processing Frame
        eog_frame = tk.LabelFrame(main_frame, text="👁️ EOG/EEG Processing", font=("Arial", 10))
        eog_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Processing mode selection
        mode_frame = tk.Frame(eog_frame)
        mode_frame.grid(row=0, column=0, columnspan=3, pady=5)
        tk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
        self.processing_mode = tk.StringVar(value="EOG")
        tk.Radiobutton(mode_frame, text="👁️ EOG (Eye Movement)", variable=self.processing_mode, 
                      value="EOG").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="🧠 EEG (Alpha/Beta)", variable=self.processing_mode, 
                      value="EEG").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="🔀 Hybrid (Both)", variable=self.processing_mode, 
                      value="HYBRID").pack(side=tk.LEFT, padx=5)
        
        # Processing controls
        control_frame = tk.Frame(eog_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=5)
        tk.Button(control_frame, text="▶️ Start Processing", command=self.start_processing).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏹ Stop Processing", command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="👁️ Calibrate", command=self.calibrate_system).pack(side=tk.LEFT, padx=5)
        
        # Status labels
        self.direction_label = tk.Label(eog_frame, text="Movement: None", font=("Arial", 12), fg="blue")
        self.direction_label.grid(row=2, column=0, columnspan=3, pady=5)
        self.mental_label = tk.Label(eog_frame, text="Status: Ready", font=("Arial", 12), fg="green")
        self.mental_label.grid(row=3, column=0, columnspan=3, pady=5)

        # Game Integration Frame  
        game_frame = tk.LabelFrame(main_frame, text="🎮 Game Integration", font=("Arial", 10))
        game_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        self.game_status = tk.Label(game_frame, text="🎮 Game Server: Ready", font=("Arial", 10))
        self.game_status.grid(row=0, column=0, columnspan=3, pady=5)
        
        tk.Button(game_frame, text="🚀 Launch Test Game", command=self.launch_test_game).grid(row=1, column=0, padx=5)
        tk.Button(game_frame, text="📊 Test Commands", command=self.test_game_commands).grid(row=1, column=1, padx=5)
        tk.Button(game_frame, text="🔧 Server Status", command=self.check_game_server).grid(row=1, column=2, padx=5)

        # Log Frame
        log_frame = tk.LabelFrame(main_frame, text="📝 Activity Log", font=("Arial", 10))
        log_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        self.log = tk.Text(log_frame, height=8, width=90, bg="#1e1e1e", fg="#00ff00", insertbackground="white")
        self.log.grid(row=0, column=0, pady=5)
        
        # Scrollbar for log
        scrollbar = tk.Scrollbar(log_frame, command=self.log.yview)
        scrollbar.grid(row=0, column=1, sticky="nsew")
        self.log.config(yscrollcommand=scrollbar.set)

        # Initialize charts
        self.chart_manager.initialize_charts()
        
        # Initial log message
        self.log_message("🧠 Mock EEG System Ready")
        self.log_message("📡 No real BLE device needed - using simulated brain signals")

    def log_message(self, msg):
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log.see(tk.END)
        except Exception:
            pass

    def start_streaming(self):
        """Start mock EEG streaming"""
        if self.streaming_active:
            messagebox.showwarning("Warning", "Streaming already active")
            return
        
        state = self.state_var.get()
        self.mock_adapter.start_mock_streaming(state)
        self.streaming_active = True
        self.connection_status.config(text="📡 Mock Device Streaming", fg="green")
        self.log_message(f"🚀 Started streaming with '{state}' mental state")

    def stop_streaming(self):
        """Stop mock EEG streaming"""
        self.mock_adapter.stop_streaming()
        self.streaming_active = False
        self.connection_status.config(text="📡 Mock Device Stopped", fg="orange")
        self.log_message("⏹ Stopped EEG streaming")

    def reset_buffers(self):
        """Reset decoder buffers"""
        self.decoder.eeg_af3.clear()
        self.decoder.eeg_af4.clear()
        self.decoder.ppg.clear()
        self.log_message("🔄 Reset data buffers")

    def change_state(self):
        """Change mental state"""
        if not self.streaming_active:
            messagebox.showwarning("Warning", "Start streaming first")
            return
        
        state = self.state_var.get()
        self.mock_adapter.change_mental_state(state)
        self.log_message(f"🧠 Changed to '{state}' mental state")

    def apply_manual_params(self):
        """Apply manual parameter controls"""
        if not self.streaming_active:
            messagebox.showwarning("Warning", "Start streaming first")
            return
        
        alertness = self.alertness_scale.get() / 100.0
        focus = self.focus_scale.get() / 100.0
        
        self.mock_adapter.change_mental_state("custom", alertness=alertness, focus=focus)
        self.log_message(f"⚙️ Manual params: alertness={alertness:.2f}, focus={focus:.2f}")

    def start_processing(self):
        """Start EOG/EEG processing"""
        if not self.streaming_active:
            messagebox.showwarning("Warning", "Start streaming first")
            return
        
        mode = self.processing_mode.get()
        self.log_message(f"▶️ Started {mode} processing mode")

    def stop_processing(self):
        """Stop processing"""
        self.log_message("⏹ Processing stopped")

    def calibrate_system(self):
        """Calibrate system"""
        mode = self.processing_mode.get()
        if mode in ["EOG", "HYBRID"]:
            self.eog_processor.calibrate()
            self.log_message("👁️ EOG calibration started")
        else:
            self.log_message("🧠 EEG mode - calibration not required")

    def launch_test_game(self):
        """Launch test game"""
        self.log_message("🚀 Launching test game...")
        import subprocess
        import os
        try:
            game_path = os.path.join(os.path.dirname(__file__), "game", "test_standalone.py")
            subprocess.Popen(["python", game_path], cwd=os.path.dirname(game_path))
            self.log_message("🎮 Test game launched successfully")
        except Exception as e:
            self.log_message(f"❌ Failed to launch game: {e}")

    def test_game_commands(self):
        """Test sending commands to game"""
        test_commands = ["left", "right", "up", "down", "blink", "center"]
        self.log_message("📊 Testing game commands...")
        
        for cmd in test_commands:
            self.eog_processor.send_command_to_game(cmd)
            self.log_message(f"   Sent: {cmd}")
            time.sleep(0.5)

    def check_game_server(self):
        """Check game server status"""
        if self.eog_processor.game_connected:
            self.game_status.config(text="🎮 Game Server: Connected", fg="green")
            self.log_message("✅ Game server is running and connected")
        else:
            self.game_status.config(text="🎮 Game Server: Disconnected", fg="red")
            self.log_message("❌ Game server not connected")

    def on_closing(self):
        """Clean shutdown"""
        self.log_message("🛑 Shutting down...")
        self.running = False
        
        if self.streaming_active:
            self.stop_streaming()
        
        if hasattr(self, 'websocket_server'):
            try:
                self.websocket_server.close()
            except Exception as e:
                print(f"WebSocket close error: {e}")
        
        if hasattr(self, 'eog_processor'):
            try:
                self.eog_processor.stop_game_server()
            except Exception as e:
                print(f"Game server stop error: {e}")
        
        # Stop event loop
        if hasattr(self, 'loop'):
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception as e:
                print(f"Loop stop error: {e}")
        
        self.root.destroy()

def main():
    """Main application entry point"""
    print("🧠 BrainLife Mock EEG System")
    print("=" * 40)
    print("📡 Using simulated EEG data - no hardware required")
    print("🎮 Full system testing available")
    print()
    
    root = tk.Tk()
    app = MockBLEApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        print("✅ Application closed")

if __name__ == "__main__":
    main()
