from collections import deque
import numpy as np

class BLEPacketDecoder:
    def __init__(self):
        self.eeg_af3 = deque(maxlen=2000)
        self.eeg_af4 = deque(maxlen=2000)
        self.ppg = deque(maxlen=200)

    def decode_packet(self, hex_packet):
        try:
            raw = bytes.fromhex(hex_packet)
            if len(raw) < 3 or raw[-1] != 0x0A:
                return None
            header = raw[0]
            payload_bytes = raw[1:-1]
            payload_str = payload_bytes.decode("ascii").strip()
            value = int(payload_str)

            if header == 0x24:
                self.eeg_af4.append(value)
                print(f"[DEBUG] AF4 value: {value}")
                return ("EEG AF4 (Right)", value)
            elif header == 0x26:
                self.eeg_af3.append(value)
                print(f"[DEBUG] AF3 value: {value}")
                return ("EEG AF3 (Left)", value)
            elif header == 0x25:
                if value < 1000000:
                    self.ppg.append(value)
                    print(f"[DEBUG] PPG value: {value}")
                    return ("PPG", value)
                else:
                    print(f"[DEBUG] Ignored PPG value (too large): {value}")
                    return None
            else:
                print(f"[DEBUG] Unknown packet: header={hex(header)}, value={value}")
                return ("Unknown", value)
        except Exception as e:
            print(f"[Decode Error] {e} → Raw: {hex_packet}")
            return None

    def clear_noise(self):
        if len(self.eeg_af3) > 100 and np.mean(np.abs(np.array(self.eeg_af3) - 8809000)) < 2000:
            print("[DEBUG] Cleared noise due to low AF3 amplitude")
            self.eeg_af3.clear()
            self.eeg_af4.clear()
            self.ppg.clear()