# UUID Constants
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
READ_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
WRITE_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
HEX_SIGNAL_TO_START = bytes.fromhex("2201230D")
HEX_SIGNAL_TO_STOP = bytes.fromhex("2200220D")

# EEG frequency bands
BANDS = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta': (13, 30),
    'Gamma': (30, 45),
}