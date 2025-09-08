# 🧠 Luồng Commands từ Thiết Bị Thật đến Game

## 📍 **Commands từ thiết bị thật nằm ở đâu?**

### 1. **Signal Processing** - `signal_processing/eeg_processor.py`
```python
def process_data(self, direction_label, mental_label):
    # ... xử lý tín hiệu EEG từ thiết bị BLE ...
    
    # 🧠 Phát hiện chuyển động mắt
    eye_movement = self.detect_eye_movement_wavelet(af3_eog_corrected, af4_eog_corrected)
    
    # 🎮 Gửi command đến game (QUAN TRỌNG!)
    self.send_command_to_game(eye_movement)
```

### 2. **TCP Server** - `signal_processing/eog_processor.py`
```python
def send_command_to_game(self, command: str):
    """Gửi EOG command đến game đang kết nối"""
    if self.tcp_server and self.game_connected:
        self.tcp_server.send_command(command)
        print(f"🎮 Sent to game: {command}")
```

### 3. **Game Client** - `game/eog_client.py`
```python
def _receive_data(self):
    """Nhận commands từ EOG processor"""
    data = self.socket.recv(1024)
    message = json.loads(data.decode('utf-8'))
    command = message['command']
    
    # Gửi đến game để xử lý
    self.command_queue.put(command)
```

### 4. **Game Processing** - `game/meteor_dodge_game.py`
```python
def process_eog_command(self, command: str):
    """Xử lý EOG command và cập nhật character movement"""
    if command == "left":
        self.character.move_left()
    elif command == "right":
        self.character.move_right()
    else:  # idle, up, down, blink, center
        self.character.stop()
```

## 🔄 **Luồng hoàn chình:**

```
🧠 Thiết bị EEG (BLE)
    ↓ Raw EEG signals
📡 BLE Decoder (ble/ble_decoder.py)
    ↓ AF3, AF4 data
🔬 EOG Processor (signal_processing/eeg_processor.py)
    ↓ Eye movement detection
🌐 TCP Server (signal_processing/eog_processor.py)
    ↓ JSON commands {"command": "left"}
🎮 Game TCP Client (game/eog_client.py)
    ↓ Processed commands
🕹️ Character Controller (game/meteor_dodge_game.py)
    ↓ Movement actions
👾 Game Character (game/character.py)
```

## 🚀 **Để test commands từ thiết bị thật:**

### Bước 1: Khởi động EOG app với TCP server
```bash
python main.py
```
✅ Điều này sẽ:
- Khởi động BLE connection
- Xử lý tín hiệu EEG thành EOG commands
- **Tự động khởi động TCP server** trên localhost:8766

### Bước 2: Khởi động game CHÍNH
```bash
cd game
python main.py
```
✅ Game sẽ:
- Tự động kết nối đến TCP server
- Nhận commands từ EOG processor
- Điều khiển character theo eye movements

### Bước 3: Test eye movements
👁️ **Left** → Character moves left  
👁️ **Right** → Character moves right  
👁️ **Up/Down/Blink/Center** → Character stops  

## ⚠️ **Lưu ý quan trọng:**

1. **TCP Server** được khởi động **tự động** khi chạy `python main.py`
2. **Commands** được gửi **realtime** từ EOG detection
3. **Game** sẽ connect automatically nếu EOG app đang chạy
4. **Debug mode**: Nếu không có EOG, dùng arrow keys để test

## 🔧 **Files đã được cập nhật:**

- ✅ `signal_processing/eog_processor.py` - Thêm `self.send_command_to_game(eye_movement)`
- ✅ `ui/app_ui.py` - Thêm `self.eog_processor.start_game_server()`
- ✅ `game/eog_client.py` - TCP client để nhận commands
- ✅ `game/meteor_dodge_game.py` - Xử lý commands thành character movement

**🎯 Bây giờ commands từ thiết bị thật sẽ được gửi đến game tự động!**
