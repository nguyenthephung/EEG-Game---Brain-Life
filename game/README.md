# 🎮 EOG Meteor Dodge Game

Brain-Computer Interface game controlled by eye movements (EOG) based on research methodology.

## 📁 Core Files

### Game Engine
- **`meteor_dodge_game.py`** - Main game class with Pygame implementation
- **`character.py`** - Player character with physics and movement
- **`meteor.py`** - Meteor obstacles with spawning system
- **`game_evaluator.py`** - Performance metrics (Precision/Sensitivity/Specificity)

### Communication
- **`eog_tcp_server.py`** - TCP server for EOG commands
- **`eog_client.py`** - TCP client in game to receive commands

### Testing
- **`test_standalone.py`** - ⭐ **MAIN TEST FILE** - Run the game
- **`test_complete.py`** - Complete integration testing

## 🚀 Quick Start

### Option 1: Full EOG Integration (MAIN USE CASE)
```bash
# Terminal 1: Start EOG processor
python main.py

# Terminal 2: Start game (MAIN ENTRY POINT)
cd game
python main.py
```

### Option 2: Standalone Game Test  
```bash
cd game
python test_standalone.py
```
- Press SPACE to start
- Use arrow keys to test movement
- Game connects to EOG server automatically if available

### Option 3: Mock EOG Testing
```bash
# Terminal 1: Start mock EOG server
cd game
python test_complete.py

# Terminal 2: Start game
cd game  
python main.py
```

## 🎯 Game Controls

### EOG Commands (Research-based)
- **Left/Right** → Move character
- **Up/Down/Blink/Center** → Stop character
- **Double same direction** → Speed boost
- **Double opposite direction** → Speed reduction

### Debug Controls (Keyboard)
- **SPACE** - Start/Stop game
- **←/→** - Move character
- **↓** - Stop character
- **P** - Pause/Resume
- **R** - Reset
- **ESC** - Exit

## 📊 Performance Metrics

The game calculates research metrics:
- **Precision** = TP / (TP + FP) × 100
- **Sensitivity** = TP / (TP + FN) × 100
- **Specificity** = TN / (TN + FP) × 100

## 🔧 Technical Details

- **Communication**: TCP/IP on localhost:8766
- **Frame Rate**: 60 FPS
- **Command Interval**: 1 second (research specification)
- **Physics**: Vector-based movement with acceleration
- **Difficulty**: Semirandom meteor spawning (max 5 concurrent)

## 🧪 Testing Status

✅ **Game Engine** - Working  
✅ **Character Movement** - Working  
✅ **Meteor System** - Working  
✅ **TCP Communication** - Working  
⏳ **EOG Integration** - In Progress  
⏳ **Performance Metrics** - In Progress  

---

**🎯 Goal**: Reproduce research results with Pygame implementation of EOG-controlled obstacle evasion game.
