# 🧠 Advanced EOG Detection with Continuous Wavelet Transform

## 📊 Research Implementation

This project implements advanced EOG (Electrooculography) detection based on recent research using **Continuous Wavelet Transform (CWT)** and **Wavelet Scalogram** analysis for real-time eye movement classification.

## 🔬 Research Methodology

### 1. Continuous Wavelet Transform (CWT)
```
Ca,b(ω) = Ca,b = ∫ EEG(t) ψa,b(t) dt
```
Where:
- `ψa,b(t) = 1/√|a| ψ*((t-b)/a)` (Haar wavelet function)
- `a` = scale parameter (positive, defines frequency content)
- `b` = position parameter (real number, defines time shift)
- `Ca,b` = wavelet coefficients

### 2. Wavelet Scalogram
```
S = |coefs * coefs|
E = ΣS(t)
```
Where:
- `S` = energy for each wavelet coefficient
- `E` = total energy over 1-second window

### 3. Feature Extraction (4 Key Features)
1. **Maximum Wavelet Coefficient** - Peak energy in scalogram
2. **Area Under Curve** - 200ms window using trapezoidal method
3. **Amplitude** - Peak-to-peak signal variation
4. **Velocity** - Signal change rate (derivative approximation)

### 4. Hierarchical Classification
Fixed thresholds for binary outputs:
- Convert features to binary vectors
- Discriminate between 6 classes: `blink`, `center`, `right`, `left`, `up`, `down`
- Use Y1 (horizontal) and Y2 (vertical) signal analysis

## 🚀 Implementation Features

### Signal Processing Pipeline
1. **8th-order Butterworth Filter** [0.5-100 Hz]
2. **4th-order Notch Filter** [48-52 Hz] for power-line noise
3. **Frequency Band Separation** [0.5-10 Hz] for EOG extraction
4. **Baseline Correction** using smoothed signal mean
5. **CWT with Haar Wavelet** for time-frequency analysis

### Real-time Visualization
- **3x2 Chart Layout:**
  - Raw AF3/AF4 signals (Left/Right eye)
  - Filtered EOG Y1/Y2 (Horizontal/Vertical)
  - Wavelet Scalograms with color-coded energy maps

### Classification System
```python
# Hierarchical decision tree
if blink_detected:
    return "blink"
elif low_activity:
    return "center"
elif Y1_dominant:
    return "left" or "right"
elif Y2_dominant:
    return "up" or "down"
```

## 📈 Performance Enhancements

### Advanced Features
- **Wavelet-Enhanced Detection** - Higher accuracy than simple threshold methods
- **Energy-Based Quality Assessment** - Signal quality using scalogram energy
- **200ms Window Analysis** - Optimal detection window as per research
- **Binary Feature Vectors** - Robust classification outputs

### Real-time Processing
- **244 Hz Sampling Rate** - High temporal resolution
- **Sliding Window Analysis** - Continuous real-time detection
- **Minimum Detection Interval** - Prevents false triggers
- **Movement History Buffer** - Smooth detection transitions

## 🔧 Technical Configuration

### Wavelet Parameters
```python
wavelet_name = 'haar'           # Haar wavelet (research specified)
scales = np.arange(1, 32)       # Scale range for CWT
window_ms = 200                 # Feature extraction window
sampling_rate = 244             # Device sampling frequency
```

### Classification Thresholds
```python
thresholds = {
    'max_wavelet_coeff': 0.1,   # Wavelet energy threshold
    'area_under_curve': 0.05,   # Signal area threshold  
    'amplitude': 50.0,          # Peak-to-peak threshold
    'velocity': 100.0           # Change rate threshold
}
```

## 📊 Chart Visualization

### Scalogram Display
- **Colormap**: Jet colormap for energy visualization
- **Axes**: Scale (a) vs Time (samples)
- **Real-time Updates**: Dynamic scalogram refresh
- **Interpolation**: Bilinear for smooth visualization

### Signal Quality Indicators
- **Good Signal**: Wavelet Enhanced (>1000)
- **Moderate Signal**: Standard Processing (500-1000)
- **Weak Signal**: Basic Detection (<500)

## 🎯 Eye Movement Classes

1. **Blink** - High energy in both Y1 and Y2
2. **Center** - Low overall scalogram energy
3. **Right** - Positive Y1 dominant with high wavelet energy
4. **Left** - Negative Y1 dominant with high wavelet energy
5. **Up** - Positive Y2 with high velocity
6. **Down** - Negative Y2 with high velocity

## 🔬 Research Validation

This implementation follows the methodology described in:
- **Offline Algorithm**: 4-direction classification using area under curve
- **Online Algorithm**: 6-class discrimination with wavelet features
- **Fixed Thresholds**: Based on mean and standard deviation from previous studies
- **Binary Output Vectors**: For cursor control and game interaction

## 🌐 Integration

### WebSocket Server
Real-time data streaming for external applications:
```json
{
    "direction": "right",
    "mental_state": "focused", 
    "speed": 0.8,
    "stress_level": 0.3,
    "wavelet_energy": 1250.5
}
```

### BLE Connectivity
- **Device**: BrainLife Focus+ EEG headset
- **Channels**: AF3, AF4 (frontal electrodes)
- **Real-time**: 244 Hz continuous streaming
- **Protocol**: Custom BLE packet decoding

## 🚀 Usage

1. **Start Application**: `python main.py`
2. **Scan & Connect**: Find BrainLife device via BLE
3. **Begin Tracking**: Click "Start Tracking" for real-time EOG
4. **Calibrate**: Use "Calibrate EOG" for optimal thresholds
5. **Monitor**: View real-time wavelet scalograms and movement detection

---

**🧠 Advanced Brain-Computer Interface with Research-Grade Signal Processing**
