import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ble.ble_manager import BLEManager
from ble.ble_decoder import BLEPacketDecoder
from ui.chart_manager import ChartManager
from signal_processing.eeg_processor import EEGProcessor
from utils.websocket_server import WebSocketServer

class BLEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BrainLife EEG Maze Controller")
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.ble_manager = BLEManager(self.loop)
        self.decoder = BLEPacketDecoder()
        self.chart_manager = ChartManager(self.root)
        self.eeg_processor = EEGProcessor(self.decoder, self.chart_manager)
        self.websocket_server = WebSocketServer(self.loop, self.eeg_processor)
        self.running = True
        self.game_active = False
        self.setup_ui()
        self.websocket_server.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10)

        # BLE Connection Frame
        ble_frame = tk.LabelFrame(main_frame, text="BLE Connection", font=("Arial", 10))
        ble_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(ble_frame, text="🔍 Scan Devices", command=self.scan_devices).grid(row=0, column=0, padx=5)
        tk.Button(ble_frame, text="🔌 Connect", command=self.connect_device).grid(row=0, column=1, padx=5)
        tk.Button(ble_frame, text="❌ Disconnect", command=self.disconnect_device).grid(row=0, column=2, padx=5)
        self.device_list = ttk.Treeview(ble_frame, columns=("name", "address"), show="headings", height=5)
        self.device_list.heading("name", text="Device Name")
        self.device_list.heading("address", text="Address")
        self.device_list.grid(row=1, column=0, columnspan=3, pady=5)

        # Game Control Frame
        game_frame = tk.LabelFrame(main_frame, text="Game Control", font=("Arial", 10))
        game_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(game_frame, text="▶️ Start Game", command=self.start_game).grid(row=0, column=0, padx=5)
        tk.Button(game_frame, text="⏹ Stop Game", command=self.stop_game).grid(row=0, column=1, padx=5)
        tk.Button(game_frame, text="🧠 Calibrate", command=self.eeg_processor.calibrate).grid(row=0, column=2, padx=5)
        self.direction_label = tk.Label(game_frame, text="Direction: None", font=("Arial", 12))
        self.direction_label.grid(row=1, column=0, columnspan=3, pady=5)
        self.mental_label = tk.Label(game_frame, text="Mental State: Unknown", font=("Arial", 12))
        self.mental_label.grid(row=2, column=0, columnspan=3, pady=5)

        # Log Frame
        log_frame = tk.LabelFrame(main_frame, text="Log", font=("Arial", 10))
        log_frame.grid(row=2, column=0, columnspan=2, pady=10)
        self.log = tk.Text(log_frame, height=10, width=75, bg="#1e1e1e", fg="#00ff00", insertbackground="white")
        self.log.grid(row=0, column=0, pady=5)

        self.chart_manager.setup_charts(main_frame)

    def log_message(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def scan_devices(self):
        self.log_message("🔍 Scanning for 'BrainLife Focus+' BLE devices...")
        asyncio.run_coroutine_threadsafe(self._scan(), self.loop)

    async def _scan(self):
        try:
            self.ble_manager.devices = await self.ble_manager.scan()
            self.device_list.delete(*self.device_list.get_children())
            for d in self.ble_manager.devices:
                self.device_list.insert("", tk.END, values=(d.name, d.address))
            self.log_message(f"✅ Found {len(self.ble_manager.devices)} device(s).")
        except Exception as e:
            self.log_message(f"❌ Scan error: {e}")

    def connect_device(self):
        selected = self.device_list.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a device.")
            return
        idx = self.device_list.index(selected[0])
        device = self.ble_manager.devices[idx]
        self.ble_manager.selected_device = device
        self.log_message(f"🔗 Connecting to {device.name} ({device.address})...")
        asyncio.run_coroutine_threadsafe(self._connect(device.address), self.loop)

    async def _connect(self, address):
        try:
            await self.ble_manager.connect(address, self.handle_notify)
            self.log_message("✅ Connected successfully!")
        except Exception as e:
            self.log_message(f"❌ Connection error: {e}")

    def handle_notify(self, sender, data):
        if not self.running:
            return
        if not self.game_active:
            return
        hex_stream = data.hex()
        packets = hex_stream.split("0a")
        for p in packets:
            p = p.strip()
            if len(p) < 2:
                continue
            result = self.decoder.decode_packet(p + "0a")
            if result:
                signal_type, value = result
                self.log_message(f"[{signal_type}] {value}")
                self.eeg_processor.process_eeg_data(self.mental_label, self.direction_label)
                self.decoder.clear_noise()

    def disconnect_device(self):
        if self.ble_manager.ble_client:
            asyncio.run_coroutine_threadsafe(self.ble_manager.disconnect(), self.loop)
            self.log_message("❎ Disconnected.")

    def start_game(self):
        if self.ble_manager.ble_client:
            self.game_active = True
            self.log_message("🎮 Game started - EEG processing active")
            self.ble_manager.send_start_command()

    def stop_game(self):
        if self.ble_manager.ble_client:
            self.game_active = False
            self.log_message("⏹ Game stopped - EEG processing paused")
            self.direction_label.config(text="Direction: Stopped")
            self.mental_label.config(text="Mental State: Paused")
            self.ble_manager.send_stop_command()

    def on_closing(self):
        self.running = False
        self.disconnect_device()
        self.websocket_server.close()
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()