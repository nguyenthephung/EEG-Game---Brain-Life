import asyncio
from bleak import BleakClient, BleakScanner
from .constants import SERVICE_UUID, READ_CHARACTERISTIC_UUID, WRITE_CHARACTERISTIC_UUID, HEX_SIGNAL_TO_START, HEX_SIGNAL_TO_STOP

class BLEManager:
    def __init__(self, loop):
        self.ble_client = None
        self.devices = []
        self.selected_device = None
        self.loop = loop

    async def scan(self):
        try:
            self.devices = await BleakScanner.discover(timeout=5)
            return [d for d in self.devices if d.name == "BrainLife Focus+"]
        except Exception as e:
            raise Exception(f"Scan error: {e}")

    async def connect(self, address, notify_callback):
        try:
            self.ble_client = BleakClient(address)
            await self.ble_client.connect()
            # is_connected is now a property, not a coroutine
            if self.ble_client.is_connected:
                await self.ble_client.start_notify(READ_CHARACTERISTIC_UUID, notify_callback)
                return True
            return False
        except Exception as e:
            raise Exception(f"Connection error: {e}")

    async def disconnect(self):
        try:
            if self.ble_client and self.ble_client.is_connected:
                await self.ble_client.disconnect()
            self.ble_client = None
        except Exception as e:
            raise Exception(f"Disconnect error: {e}")

    async def send_data(self, data):
        try:
            await self.ble_client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, data)
        except Exception as e:
            raise Exception(f"Send failed: {e}")

    def send_start_command(self):
        asyncio.run_coroutine_threadsafe(self.send_data(HEX_SIGNAL_TO_START), self.loop)

    def send_stop_command(self):
        asyncio.run_coroutine_threadsafe(self.send_data(HEX_SIGNAL_TO_STOP), self.loop)