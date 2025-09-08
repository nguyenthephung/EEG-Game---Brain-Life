import asyncio
import websockets
import json
import numpy as np

class WebSocketServer:
    def __init__(self, loop, eeg_processor):
        self.loop = loop
        self.eeg_processor = eeg_processor
        self.websocket_server = None
        self.running = True

    def start(self):
        async def handle_client(websocket, path):
            try:
                while self.running:
                    data = {
                        "direction": self.eeg_processor.directions[-1] if self.eeg_processor.directions else "none",
                        "mental_state": self.eeg_processor.mental_state,
                        "speed": self.eeg_processor.calculate_speed(),
                        "stress_level": np.std(np.array(self.eeg_processor.decoder.ppg)) / 10000 if self.eeg_processor.decoder.ppg else 0
                    }
                    await websocket.send(json.dumps(data))
                    await asyncio.sleep(0.1)
            except websockets.exceptions.ConnectionClosed:
                pass

        async def start_server():
            self.server = await websockets.serve(handle_client, "localhost", 8765)
            print("🌐 WebSocket server started on ws://localhost:8765")

        asyncio.run_coroutine_threadsafe(start_server(), self.loop)

    def close(self):
        """Properly close the WebSocket server"""
        if hasattr(self, 'server') and self.server:
            try:
                # Close the server
                self.server.close()
                # Wait for it to close (schedule on the event loop)
                asyncio.run_coroutine_threadsafe(self.server.wait_closed(), self.loop)
            except Exception as e:
                print(f"Error closing WebSocket server: {e}")
        
        # Clear connected clients
        self.connected_clients.clear()