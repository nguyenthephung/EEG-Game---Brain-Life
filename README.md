# BrainLife EEG - Brain Wave Game Controller

## 📋 Giới thiệu dự án

**BrainLife EEG** là một hệ thống tích hợp cho phép điều khiển game thông qua tín hiệu sóng não (EEG). Dự án bao gồm:

- **Tool Python**: Ứng dụng thu thập và xử lý tín hiệu EEG từ thiết bị BLE (Bluetooth Low Energy)
- **Unity Game**: Game được điều khiển bằng sóng não thông qua dữ liệu EEG

### ✨ Tính năng chính

- 🧠 **Thu thập sóng não**: Kết nối với thiết bị EEG "BrainLife Focus+" qua BLE
- 📊 **Xử lý tín hiệu**: Giải mã và phân tích dữ liệu EEG/PPG real-time
- 🎮 **Điều khiển game**: Truyền dữ liệu sóng não đến Unity game qua WebSocket
- 📈 **Trực quan hóa**: Hiển thị biểu đồ sóng não trực tiếp trong giao diện
- 🔧 **Phát hiện nhiễu**: Tự động loại bỏ dữ liệu lỗi và nhiễu

## 🛠️ Yêu cầu hệ thống

### Tool Python
- Python 3.11+
- Windows 10/11 (có hỗ trợ Bluetooth)
- Thiết bị EEG "BrainLife Focus+"

### Unity Game
- Unity 2022.3 LTS hoặc mới hơn
- Windows 10/11

## 🚀 Cách cài đặt và chạy

### 1. Cài đặt Tool Python

```bash
# Clone repository
git clone https://github.com/nguyenthephung/EEG-Game---Brain-Life.git
cd EEG_Conncet_Data

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Chạy Tool Python

```bash
# Chạy ứng dụng EEG
python main.py
```

#### Hướng dẫn sử dụng Tool:
1. **Quét thiết bị**: Nhấn "🔍 Scan Devices" để tìm thiết bị BLE
2. **Kết nối**: Chọn thiết bị "BrainLife Focus+" và nhấn "🔌 Connect"
3. **Hiệu chỉnh**: Nhấn "⚙️ Calibrate EEG" để hiệu chỉnh cảm biến
4. **Bắt đầu**: Nhấn "🎮 Start Brain Wave Tracking" để bắt đầu thu thập dữ liệu
5. **WebSocket**: Tool sẽ tự động khởi chạy server WebSocket trên cổng 8765

### 3. Chạy Unity Game

#### Cách 1: Từ Unity Editor
```bash
# Kiểm tra phiên bản Unity cần thiết
type "game\ProjectSettings\ProjectVersion.txt"

# Mở Unity Hub → Add Project → Chọn thư mục 'game'
# Trong Unity Editor: Nhấn nút Play ▶️
```

#### Cách 2: Build game
```bash
# Trong Unity Editor:
# File → Build Settings → Add Open Scenes → Build
```

#### Cách 3: Command Line (nếu đã cài Unity)
```bash
# Thay <VERSION> bằng phiên bản trong ProjectVersion.txt
"C:\Program Files\Unity\Hub\Editor\<VERSION>\Editor\Unity.exe" -projectPath "game" -buildWindows64Player "Build\BrainLifeGame.exe" -quit -batchmode
```

## 🔗 Kết nối Tool và Game

1. **Khởi chạy Tool Python trước** để WebSocket server sẵn sàng
2. **Kết nối thiết bị EEG** và bắt đầu tracking
3. **Chạy Unity Game** - game sẽ tự động kết nối WebSocket tại `ws://localhost:8765`
4. **Điều khiển game** thông qua tín hiệu sóng não!

## 📁 Cấu trúc dự án

```
EEG_Conncet_Data/
├── main.py                    # Entry point của ứng dụng
├── ble/                       # Module xử lý BLE
│   ├── ble_manager.py         # Quản lý kết nối BLE
│   ├── ble_decoder.py         # Giải mã gói dữ liệu BLE
│   └── constants.py           # Hằng số BLE
├── ui/                        # Giao diện người dùng
│   ├── app_ui.py              # UI chính
│   └── chart_manager.py       # Quản lý biểu đồ EEG
├── signal_processing/         # Xử lý tín hiệu
│   └── eeg_processor.py       # Xử lý tín hiệu EEG
├── utils/                     # Tiện ích
│   └── websocket_server.py    # WebSocket server
└── game/                      # Unity game project
    ├── Assets/                # Tài nguyên game
    ├── ProjectSettings/       # Cài đặt Unity
    └── Packages/              # Unity packages
```

## 🎯 Cách hoạt động

1. **Thu thập dữ liệu**: Tool Python kết nối với thiết bị EEG qua BLE
2. **Xử lý tín hiệu**: Giải mã và phân tích dữ liệu EEG/PPG real-time
3. **Truyền dữ liệu**: Gửi dữ liệu đã xử lý qua WebSocket
4. **Điều khiển game**: Unity game nhận dữ liệu và thực hiện hành động tương ứng

## 🔧 Cấu hình

### WebSocket Settings
- **Host**: localhost
- **Port**: 8765
- **Protocol**: WebSocket

### EEG Settings
- **Sampling Rate**: 244 Hz
- **Channels**: AF3, AF4 (EEG) + PPG
- **Buffer Size**: 5000 samples (EEG), 500 samples (PPG)

## 🐛 Xử lý sự cố

### Tool Python không kết nối được thiết bị
- Kiểm tra Bluetooth đã bật
- Đảm bảo thiết bị "BrainLife Focus+" đang ở chế độ pairing
- Thử quét lại thiết bị

### Unity Game không nhận dữ liệu
- Kiểm tra Tool Python đã chạy và WebSocket server đã khởi động
- Kiểm tra firewall có chặn cổng 8765 không
- Kiểm tra console Unity để xem log kết nối

### Dữ liệu EEG nhiễu
- Tool tự động phát hiện và loại bỏ dữ liệu nhiễu
- Thử hiệu chỉnh lại cảm biến
- Kiểm tra kết nối vật lý với thiết bị EEG

## 📞 Hỗ trợ

- **GitHub**: [EEG-Game---Brain-Life](https://github.com/nguyenthephung/EEG-Game---Brain-Life)
- **Issues**: Báo cáo lỗi tại GitHub Issues
- **Branch hiện tại**: New

## 📄 License

Dự án này được phát triển cho mục đích nghiên cứu và giáo dục.

---

**Phát triển bởi**: Nguyễn Thế Phụng  
**Ngày cập nhật**: September 18, 2025