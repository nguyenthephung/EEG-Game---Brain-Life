# 🧠 Mock EEG System - Usage Guide

## 📋 Overview

Hệ thống Mock EEG cho phép bạn phát triển và test ứng dụng Brain-Computer Interface mà **không cần thiết bị EEG thật**. Hệ thống mô phỏng tín hiệu não bộ thực tế với các trạng thái tinh thần khác nhau.

## 🚀 Quick Start

### 1. Test Hệ Thống
```bash
# Test toàn bộ mock system
python test_mock_system.py
```

### 2. Chạy App với Mock Data
```bash
# Chạy main app với mock EEG data
python main_mock.py
```

### 3. Test Game Integration
```bash
# Test game với mock EOG commands
python game/test_standalone.py
```

## 🎛️ Main App Features

### Mock Device Control
- **🚀 Start Streaming**: Bắt đầu stream mock EEG data
- **⏹ Stop Streaming**: Dừng streaming
- **📊 Reset Buffers**: Xóa data buffers

### Mental State Control
- **Preset States**: 
  - `resting`: Trạng thái nghỉ ngơi
  - `focused`: Tập trung cao
  - `stressed`: Căng thẳng
  - `meditation`: Thiền định
  - `left_thinking`: Suy nghĩ bên trái
  - `right_thinking`: Suy nghĩ bên phải

- **Manual Control**:
  - Alertness: Độ tỉnh táo (0-100%)
  - Focus: Độ tập trung (0-100%)

### Processing Modes
- **👁️ EOG Mode**: Phát hiện chuyển động mắt
- **🧠 EEG Mode**: Phân tích sóng alpha/beta
- **🔀 Hybrid Mode**: Kết hợp cả hai

### Game Integration
- **🚀 Launch Test Game**: Mở game test
- **📊 Test Commands**: Gửi test commands đến game
- **🔧 Server Status**: Kiểm tra trạng thái TCP server

## 📊 Signal Generation

### Frequency Bands
- **Alpha (8-13 Hz)**: Sóng alpha, liên quan đến thư giãn
- **Beta (13-30 Hz)**: Sóng beta, liên quan đến tập trung
- **Noise**: Nhiễu tự nhiên của tín hiệu EEG

### Mental States
```python
# Các trạng thái có sẵn
states = {
    "resting": {"alpha": 0.8, "beta": 0.3, "alertness": 0.4},
    "focused": {"alpha": 0.4, "beta": 0.9, "alertness": 0.8},
    "stressed": {"alpha": 0.2, "beta": 1.2, "alertness": 0.9},
    "meditation": {"alpha": 1.0, "beta": 0.2, "alertness": 0.3},
    "left_thinking": {"alpha": 0.5, "beta": 0.7, "alertness": 0.7},
    "right_thinking": {"alpha": 0.5, "beta": 0.7, "alertness": 0.7}
}
```

## 🎮 Game Integration

### EOG Commands
Mock system tự động tạo các commands:
- `left`: Chuyển động mắt trái
- `right`: Chuyển động mắt phải  
- `up`: Chuyển động mắt lên
- `down`: Chuyển động mắt xuống
- `center`: Trở về giữa
- `blink`: Chớp mắt (bắn đạn)

### Game Controls
- **Arrow Keys**: Di chuyển manual
- **Space**: Bắn đạn manual
- **ESC**: Thoát game

## 🔧 Technical Details

### Architecture
```
Mock EEG Generator → BLE Packet Simulator → Decoder → Processor → Charts/Game
```

### Components
1. **EEGSignalGenerator**: Tạo tín hiệu EEG thực tế
2. **MockBLEAdapter**: Chuyển đổi thành BLE packets
3. **BLEPacketDecoder**: Decode packets (existing)
4. **EOGProcessor**: Xử lý EOG/EEG (existing)
5. **ChartManager**: Hiển thị real-time (existing)

### Data Flow
```python
# 1. Generate realistic EEG signals
af3, af4 = generator.generate_sample()

# 2. Convert to BLE packets  
packets = adapter.create_eeg_packets(af3_data, af4_data)

# 3. Process through existing pipeline
decoder.process_packet(packet)
processor.detect_eye_movement_wavelet()
chart_manager.update_charts()
```

## 📈 Performance

### Streaming Rate
- **244 Hz**: Tốc độ sampling thực tế
- **18.5 Hz**: Chart update rate (optimized)
- **Real-time**: EOG detection và game commands

### Memory Usage
- **Circular Buffers**: Giới hạn memory usage
- **Efficient Processing**: Chỉ xử lý khi cần
- **Background Threads**: Không block UI

## 🧪 Testing

### Test Components
```bash
# Test signal generation
python test_mock_system.py

# Expected output:
# ✅ Signal generation: PASS
# ✅ Packet conversion: PASS  
# ✅ Decoder integration: PASS
# ✅ EOG processing: PASS
# ✅ Streaming mode: PASS
# ✅ Mental state changes: PASS
```

### Debug Features
- **Console Logging**: Real-time activity log
- **Chart Display**: Visual feedback
- **Status Indicators**: Connection và processing status
- **Error Handling**: Graceful error recovery

## 🎯 Use Cases

### Development
- **No Hardware Required**: Phát triển không cần thiết bị
- **Reproducible Tests**: Test cases nhất quán
- **Mental State Simulation**: Test các trạng thái khác nhau

### Research
- **Algorithm Testing**: Test EOG detection algorithms
- **UI Development**: Phát triển giao diện
- **Performance Optimization**: Tối ưu hóa performance

### Demo/Presentation
- **Stable Demo**: Demo ổn định không cần setup hardware
- **Controlled Environment**: Kiểm soát hoàn toàn input
- **Visual Appeal**: Charts và game đẹp mắt

## ⚠️ Limitations

### Mock vs Real
- **No Real Brain Signals**: Chỉ là simulation
- **Simplified Artifacts**: Artifacts đơn giản hơn thực tế
- **Perfect Sync**: Không có jitter như hardware thật

### Performance
- **CPU Usage**: Continuous signal generation
- **Thread Management**: Multiple background threads
- **Memory Growth**: Buffers cần được monitor

## 🔧 Troubleshooting

### Common Issues

#### "No display available"
```bash
# Windows: Ensure you're not in headless mode
# Linux: Set DISPLAY variable
export DISPLAY=:0
```

#### "Pygame not installed"
```bash
pip install pygame
```

#### "Mock streaming not starting"
- Check console for errors
- Verify decoder is initialized
- Try reset buffers

#### "Game not connecting"
- Check TCP server status
- Verify port 8766 is available
- Try restart game server

### Debug Mode
```python
# Enable debug logging
mock_adapter.debug = True
eog_processor.debug = True
```

## 📚 API Reference

### EEGSignalGenerator
```python
generator = EEGSignalGenerator()
generator.set_mental_state("focused")
af3, af4 = generator.generate_sample()
```

### MockBLEAdapter
```python
adapter = MockBLEAdapter(decoder, chart_manager, processor)
adapter.start_mock_streaming("meditation")
adapter.change_mental_state("stressed")
adapter.stop_streaming()
```

## 🎉 Ready to Use!

Hệ thống mock EEG đã sẵn sàng để:
- ✅ Phát triển và test không cần hardware
- ✅ Demo ổn định và mượt mà  
- ✅ Research algorithms EOG/EEG
- ✅ Training và education

**Happy coding! 🧠💻**
