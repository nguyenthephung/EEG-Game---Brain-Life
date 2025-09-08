import numpy as np
from collections import deque
import pandas as pd
from scipy.signal import butter, lfilter, savgol_filter
from scipy import signal
import pywt  # For wavelet transforms
import time

class EOGProcessor:
    def __init__(self, decoder, chart_manager):
        self.decoder = decoder
        self.chart_manager = chart_manager
        
        # EOG processing parameters based on research
        self.sampling_rate = 244  # Hz (from your device)
        self.window_size = 244  # 1 second blocks
        self.detection_threshold = 0.5
        
        # Buffers for real-time processing
        self.left_buffer = deque(maxlen=self.window_size)
        self.right_buffer = deque(maxlen=self.window_size)
        
        # Movement detection states
        self.last_detection_time = 0
        self.min_detection_interval = 0.5  # seconds
        
        # Current eye movement state
        self.current_movement = "center"
        self.movement_history = deque(maxlen=5)
        
        # Wavelet transform parameters
        self.wavelet_name = 'morl'  # Morlet wavelet (Haar has compatibility issues in PyWavelets 1.8.0)
        self.scales = np.arange(1, 32)  # Scale parameter 'a' range
        self.wavelet_window_ms = 200  # 200ms window for area calculation
        self.wavelet_window_samples = int(self.wavelet_window_ms * self.sampling_rate / 1000)
        
        # Feature thresholds (to be set from previous studies)
        self.thresholds = {
            'max_wavelet_coeff': 0.1,
            'area_under_curve': 0.05,
            'amplitude': 50.0,
            'velocity': 100.0
        }
        
        # TCP server for game communication
        self.tcp_server = None
        self.game_connected = False
        
        # 📊 AF3/AF4 Chart Synchronization Buffer
        self.sync_buffer = {
            'af3_data': None,
            'af4_data': None,
            'af3_timestamp': None,
            'af4_timestamp': None,
            'sync_window_ms': 100,  # 100ms sync window
            'last_chart_update': 0
        }
        
        # 🧠 Alpha/Beta band processing (from legacy EEG code)
        self.directions = deque(maxlen=10)
        self.mental_state = "Unknown"
        self.update_count = 0
        self.beta_diff_buffer = deque(maxlen=50)
        self.beta_diff_history = deque(maxlen=50)
        
        print("🔧 EOG Processor initialized for eye movement detection")
        print("🧠 Alpha/Beta band processing enabled")

    def update_sync_buffer(self, channel, data, timestamp):
        """Update sync buffer and trigger chart update when both channels ready"""
        if channel == 'AF3':
            self.sync_buffer['af3_data'] = data
            self.sync_buffer['af3_timestamp'] = timestamp
        elif channel == 'AF4':
            self.sync_buffer['af4_data'] = data
            self.sync_buffer['af4_timestamp'] = timestamp
        
        # Check if both channels have recent data
        self.check_and_update_charts()

    def check_and_update_charts(self):
        """Update charts only when both AF3 and AF4 have synchronized data"""
        current_time = time.time() * 1000  # milliseconds
        
        af3_data = self.sync_buffer['af3_data']
        af4_data = self.sync_buffer['af4_data']
        af3_time = self.sync_buffer['af3_timestamp']
        af4_time = self.sync_buffer['af4_timestamp']
        
        # Check if both channels have data
        if af3_data is None or af4_data is None:
            return False
        
        # Check if timestamps are within sync window
        if af3_time is None or af4_time is None:
            return False
            
        time_diff = abs(af3_time - af4_time)
        if time_diff > self.sync_buffer['sync_window_ms']:
            return False  # Too much time difference, wait for newer data
        
        # � IMPROVED: Dynamic rate limiting based on data availability
        time_since_last = current_time - self.sync_buffer['last_chart_update']
        
        # Adaptive rate limiting:
        # - Fast updates when data changes significantly
        # - Slower updates when data is stable  
        min_interval = 33  # 33ms = ~30Hz max (better than 10Hz target)
        
        if time_since_last < min_interval:
            return False
        
        # 📊 UPDATE CHARTS SYNCHRONOUSLY
        try:
            # Raw signals
            if self.chart_manager and hasattr(self.chart_manager, 'update_raw_signals'):
                latest_af3 = af3_data[-1] if len(af3_data) > 0 else 0
                latest_af4 = af4_data[-1] if len(af4_data) > 0 else 0
                self.chart_manager.update_raw_signals(latest_af3, latest_af4)
                print(f"📊 [SYNC RAW] AF3: {latest_af3:.1f} | AF4: {latest_af4:.1f} | Δt: {time_diff:.1f}ms")
            
            # Alpha/Beta features
            af3_features = self.extract_features(af3_data, ch_name="AF3")
            af4_features = self.extract_features(af4_data, ch_name="AF4")
            
            if self.chart_manager and hasattr(self.chart_manager, 'update_chart'):
                self.chart_manager.update_chart(
                    af3_features["alpha"], af4_features["alpha"],
                    af3_features["beta"], af4_features["beta"]
                )
                print(f"🧠 [SYNC ALPHA/BETA] AF3: α={af3_features['alpha']:.1f}, β={af3_features['beta']:.1f} | "
                      f"AF4: α={af4_features['alpha']:.1f}, β={af4_features['beta']:.1f}")
            
            # Update timestamp
            self.sync_buffer['last_chart_update'] = current_time
            
            # Clear buffer after successful update
            self.sync_buffer['af3_data'] = None
            self.sync_buffer['af4_data'] = None
            
            return True
            
        except Exception as e:
            print(f"❌ Chart sync update error: {e}")
            return False

    def preprocess_eog_signal(self, signal):
        """Apply preprocessing filters according to research"""
        if len(signal) < 10:
            return signal
            
        # 8th-order Butterworth band-pass filter [0.5-100 Hz]
        nyquist = self.sampling_rate / 2
        low_cutoff = 0.5 / nyquist
        high_cutoff = min(100, nyquist * 0.95) / nyquist
        
        try:
            b, a = butter(4, [low_cutoff, high_cutoff], btype='band')  # Reduced to 4th order
            filtered_signal = lfilter(b, a, signal)
            
            # 4th-order notch filter [48-52 Hz] for power-line noise
            notch_freq = 50 / nyquist
            notch_width = 2 / nyquist
            if notch_freq - notch_width/2 > 0 and notch_freq + notch_width/2 < 1:
                b_notch, a_notch = butter(2, [notch_freq - notch_width/2, notch_freq + notch_width/2], btype='bandstop')
                filtered_signal = lfilter(b_notch, a_notch, filtered_signal)
            
            return filtered_signal
        except:
            return signal

    def separate_frequency_bands(self, signal):
        """Separate into low [0.5-10 Hz] EOG and high [10-100 Hz] EEG"""
        if len(signal) < 10:
            return signal, signal
            
        nyquist = self.sampling_rate / 2
        
        try:
            # Low frequency band [0.5-10 Hz] - contains EOG
            low_cutoff = 10 / nyquist
            b_low, a_low = butter(2, low_cutoff, btype='low')
            eog_signal = lfilter(b_low, a_low, signal)
            
            # High frequency band [10-100 Hz] - contains brain activity
            high_cutoff = 10 / nyquist
            b_high, a_high = butter(2, high_cutoff, btype='high')
            eeg_signal = lfilter(b_high, a_high, signal)
            
            return eog_signal, eeg_signal
        except:
            return signal, signal

    def baseline_correction(self, signal):
        """Baseline artifact correction by subtracting smoothed signal mean"""
        if len(signal) < 5:
            return signal
            
        try:
            # Smooth signal using simple moving average
            window_len = min(21, len(signal)//3)
            if window_len >= 3:
                smoothed = np.convolve(signal, np.ones(window_len)/window_len, mode='same')
                baseline_corrected = signal - (smoothed - np.mean(smoothed))
                return baseline_corrected
        except:
            pass
        return signal

    def calculate_eog_features(self, left_signal, right_signal):
        """Calculate Y1 and Y2 features according to research"""
        if len(left_signal) == 0 or len(right_signal) == 0:
            return 0, 0
            
        # Y1: maximizes margin between left and right classes
        Y1 = np.mean(left_signal) - np.mean(right_signal)
        
        # Y2: distinguishes between up and down using smoothed sum
        smoothed_sum = np.mean(left_signal) + np.mean(right_signal)
        Y2 = smoothed_sum
        
        return Y1, Y2

    def continuous_wavelet_transform(self, signal, wavelet='morl'):
        """
        Apply Continuous Wavelet Transform according to research formula:
        Ca,b(ω) = Ca,b = ∫ EEG(t) ψa,b(t) dt
        where ψa,b(t) = 1/√|a| ψ*((t-b)/a)
        """
        if len(signal) < 10:
            return None, None
            
        try:
            # 🔧 Fix PyWavelets compatibility issue
            # Use correct CWT method
            coefs, frequencies = pywt.cwt(signal, self.scales, wavelet, sampling_period=1/self.sampling_rate)
            
            # coefs shape: (scales, time_samples)
            return coefs, frequencies
        except Exception as e:
            print(f"CWT Error: {e}")
            # Fallback to basic wavelet
            try:
                coefs, frequencies = pywt.cwt(signal, self.scales, 'morl')
                return coefs, frequencies
            except Exception as e2:
                print(f"CWT Fallback Error: {e2}")
                return None, None
    
    def compute_wavelet_scalogram(self, coefs):
        """
        Compute wavelet scalogram: S = |coefs * coefs|
        E = ΣS(t) for energy calculation over 1 second
        """
        if coefs is None:
            return None, 0
            
        try:
            # S = |coefs|^2 (energy for each wavelet coefficient)
            scalogram = np.abs(coefs) ** 2
            
            # E = total energy over 1 second window
            total_energy = np.sum(scalogram)
            
            return scalogram, total_energy
        except Exception as e:
            print(f"Scalogram Error: {e}")
            return None, 0
    
    def extract_wavelet_features(self, signal):
        """
        Extract features from wavelet analysis:
        1. Maximum wavelet coefficient
        2. Area under curve (200ms window)
        3. Amplitude 
        4. Velocity
        """
        if len(signal) < self.wavelet_window_samples:
            return self._default_features()
        
        # Apply CWT
        coefs, frequencies = self.continuous_wavelet_transform(signal)
        if coefs is None:
            return self._default_features()
        
        # Compute scalogram
        scalogram, total_energy = self.compute_wavelet_scalogram(coefs)
        if scalogram is None:
            return self._default_features()
        
        try:
            # 1. Maximum wavelet coefficient
            max_coeff_idx = np.unravel_index(np.argmax(np.abs(coefs)), coefs.shape)
            max_wavelet_coeff = np.abs(coefs[max_coeff_idx])
            
            # 2. Area under curve (200ms window centered on max coefficient)
            time_idx = max_coeff_idx[1]
            half_window = self.wavelet_window_samples // 2
            start_idx = max(0, time_idx - half_window)
            end_idx = min(len(signal), time_idx + half_window)
            
            # Use trapezoidal method for area calculation
            window_signal = signal[start_idx:end_idx]
            if len(window_signal) > 1:
                # Separate positive and negative peaks
                positive_area = np.trapz(np.maximum(window_signal, 0))
                negative_area = np.trapz(np.minimum(window_signal, 0))
                area_under_curve = abs(positive_area) + abs(negative_area)
            else:
                area_under_curve = 0
            
            # 3. Amplitude (peak-to-peak in the window)
            amplitude = np.ptp(window_signal) if len(window_signal) > 0 else 0
            
            # 4. Velocity (approximate derivative)
            if len(window_signal) > 1:
                velocity = np.max(np.abs(np.diff(window_signal))) * self.sampling_rate
            else:
                velocity = 0
            
            return {
                'max_wavelet_coeff': max_wavelet_coeff,
                'area_under_curve': area_under_curve,
                'amplitude': amplitude,
                'velocity': velocity,
                'scalogram_energy': total_energy,
                'coefs': coefs,
                'scalogram': scalogram
            }
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return self._default_features()
    
    def _default_features(self):
        """Return default feature values"""
        return {
            'max_wavelet_coeff': 0,
            'area_under_curve': 0,
            'amplitude': 0,
            'velocity': 0,
            'scalogram_energy': 0
        }

    def detect_eye_movement_wavelet(self, Y1_signal, Y2_signal=None):
        """
        Hierarchical classification using wavelet features for 6-class detection
        Based on research: fixed thresholds for 4 features with binary outputs
        
        Args:
            Y1_signal: Either Y1 signal array OR dict {'AF3': af3_data, 'AF4': af4_data}
            Y2_signal: Y2 signal array (if Y1_signal is not dict)
        """
        current_time = time.time()
        
        # Prevent too frequent detections
        if current_time - self.last_detection_time < self.min_detection_interval:
            return self.current_movement
        
        # Handle different input formats
        if isinstance(Y1_signal, dict):
            # Called with dict format: {'AF3': data, 'AF4': data}
            af3_data = Y1_signal.get('AF3', [])
            af4_data = Y1_signal.get('AF4', [])
            
            if len(af3_data) == 0 or len(af4_data) == 0:
                return self.current_movement
                
            # Calculate Y1 (horizontal) and Y2 (vertical) from AF3/AF4
            Y1_calculated = np.array(af3_data) - np.array(af4_data)  # Horizontal: left-right
            Y2_calculated = (np.array(af3_data) + np.array(af4_data)) / 2  # Vertical: average
            
            y1_signal_to_use = Y1_calculated
            y2_signal_to_use = Y2_calculated
            
        else:
            # Called with separate Y1, Y2 arrays
            y1_signal_to_use = Y1_signal
            y2_signal_to_use = Y2_signal if Y2_signal is not None else Y1_signal
        
        # Extract wavelet features for both Y1 and Y2 signals
        y1_features = self.extract_wavelet_features(y1_signal_to_use)
        y2_features = self.extract_wavelet_features(y2_signal_to_use)
        
        # 🔧 Update EOG charts with scalogram data
        if self.chart_manager and hasattr(self.chart_manager, 'update_eog_data'):
            try:
                # Calculate Y1 and Y2 values for chart
                current_y1 = np.mean(y1_signal_to_use[-10:]) if len(y1_signal_to_use) > 10 else 0
                current_y2 = np.mean(y2_signal_to_use[-10:]) if len(y2_signal_to_use) > 10 else 0
                
                # Create features dict with scalogram data
                eog_features = {
                    'y1': current_y1,
                    'y2': current_y2,
                    'y1_features': y1_features,  # Contains scalogram data
                    'y2_features': y2_features   # Contains scalogram data
                }
                
                # Update charts with scalogram
                self.chart_manager.update_eog_data(current_y1, current_y2, eog_features)
                
            except Exception as e:
                print(f"⚠️ Error updating EOG charts: {e}")
        
        # Hierarchical classification with fixed thresholds
        movement = self.hierarchical_classifier(y1_features, y2_features)
        
        # Update movement history and current state
        self.movement_history.append(movement)
        self.last_detection_time = current_time
        self.current_movement = movement
        
        return movement
    
    def hierarchical_classifier(self, y1_features, y2_features):
        """
        Hierarchical classification using binary outputs from thresholds
        Convert classification results to vectors for binary outputs
        """
        
        # Binary feature vectors for Y1 and Y2
        y1_binary = self.extract_binary_features(y1_features)
        y2_binary = self.extract_binary_features(y2_features)
        
        # Step 1: Blink detection (high energy in both channels)
        if (y1_features['max_wavelet_coeff'] > self.thresholds['max_wavelet_coeff'] * 3 and
            y2_features['max_wavelet_coeff'] > self.thresholds['max_wavelet_coeff'] * 3 and
            y1_features['amplitude'] > self.thresholds['amplitude'] * 2):
            return "blink"
        
        # Step 2: Movement vs. Center classification
        total_activity = (y1_features['scalogram_energy'] + y2_features['scalogram_energy'])
        if total_activity < self.thresholds['max_wavelet_coeff'] * 0.5:
            return "center"
        
        # Step 3: Horizontal movement (Y1 dominant)
        if (y1_features['max_wavelet_coeff'] > self.thresholds['max_wavelet_coeff'] and
            y1_features['area_under_curve'] > self.thresholds['area_under_curve']):
            
            # Determine left vs right based on Y1 signal characteristics
            if y1_features['amplitude'] > 0:  # Positive Y1 indicates right movement
                return "right"
            else:  # Negative Y1 indicates left movement  
                return "left"
        
        # Step 4: Vertical movement (Y2 dominant)
        if (y2_features['max_wavelet_coeff'] > self.thresholds['max_wavelet_coeff'] and
            y2_features['area_under_curve'] > self.thresholds['area_under_curve']):
            
            # Determine up vs down based on Y2 signal characteristics
            if y2_features['velocity'] > self.thresholds['velocity']:
                return "up" if y2_features['amplitude'] > 0 else "down"
        
        return "center"
    
    def extract_binary_features(self, features):
        """Convert features to binary outputs using fixed thresholds"""
        binary_vector = {
            'max_coeff_binary': 1 if features['max_wavelet_coeff'] > self.thresholds['max_wavelet_coeff'] else 0,
            'area_binary': 1 if features['area_under_curve'] > self.thresholds['area_under_curve'] else 0,
            'amplitude_binary': 1 if features['amplitude'] > self.thresholds['amplitude'] else 0,
            'velocity_binary': 1 if features['velocity'] > self.thresholds['velocity'] else 0,
        }
        return binary_vector

    def detect_eye_movement(self, Y1, Y2):
        """Legacy method - simplified detection for backward compatibility"""
        current_time = time.time()
        
        # Prevent too frequent detections
        if current_time - self.last_detection_time < self.min_detection_interval:
            return self.current_movement
        
        # Normalize Y1 and Y2
        Y1_normalized = Y1 / (abs(Y1) + abs(Y2) + 1e-6)
        Y2_normalized = Y2 / (abs(Y1) + abs(Y2) + 1e-6)
        
        # Detection logic
        movement = "center"
        
        # Blink detection (high amplitude in both channels)
        if abs(Y1) > self.detection_threshold * 2 and abs(Y2) > self.detection_threshold * 2:
            movement = "blink"
            self.last_detection_time = current_time
        # Horizontal movement detection
        elif abs(Y1_normalized) > 0.3:
            if Y1_normalized > 0:
                movement = "right"
            else:
                movement = "left"
            self.last_detection_time = current_time
        # Vertical movement detection
        elif abs(Y2_normalized) > 0.3:
            if Y2_normalized > 0:
                movement = "up"
            else:
                movement = "down"
            self.last_detection_time = current_time
        
        self.current_movement = movement
        self.movement_history.append(movement)
        return movement

    def convert_to_uV(self, data):
        """Convert raw EEG data to microvolts"""
        return (1_000_000 * (np.array(data) - 8388608) * 1.6 / 8388608 / 2).astype(np.int16)

    def process_eog_data(self, mental_label, direction_label):
        """Main EOG processing function with synchronized chart updates"""
        current_time = time.time() * 1000  # milliseconds
        
        # Get raw data and convert to microvolts
        af3_data = self.convert_to_uV(self.decoder.eeg_af3)
        af4_data = self.convert_to_uV(self.decoder.eeg_af4) if len(self.decoder.eeg_af4) > 0 else np.zeros_like(af3_data)
        
        if len(af3_data) < 50 or len(af4_data) < 50:
            direction_label.config(text="Eye Movement: Insufficient Data")
            mental_label.config(text="EOG Status: Waiting...")
            return
        
        # � SYNCHRONIZED CHART UPDATES (replaces old immediate updates)
        # Buffer data for synchronized chart updates
        self.update_sync_buffer('AF3', af3_data, current_time)
        self.update_sync_buffer('AF4', af4_data, current_time + 1)  # Slight offset for AF4
        
        # Preprocess signals for EOG detection
        af3_filtered = self.preprocess_eog_signal(af3_data)
        af4_filtered = self.preprocess_eog_signal(af4_data)
        
        # Separate frequency bands to extract EOG
        af3_eog, af3_eeg = self.separate_frequency_bands(af3_filtered)
        af4_eog, af4_eeg = self.separate_frequency_bands(af4_filtered)
        
        # Apply baseline correction
        af3_eog_corrected = self.baseline_correction(af3_eog)
        af4_eog_corrected = self.baseline_correction(af4_eog)
        
        # Calculate EOG features Y1 and Y2
        Y1, Y2 = self.calculate_eog_features(af3_eog_corrected, af4_eog_corrected)
        
        # Advanced wavelet-based detection for better accuracy
        if len(af3_eog_corrected) >= self.wavelet_window_samples and len(af4_eog_corrected) >= self.wavelet_window_samples:
            # Use wavelet-based detection for higher accuracy
            eye_movement = self.detect_eye_movement_wavelet(af3_eog_corrected, af4_eog_corrected)
        else:
            # Fallback to simple detection
            eye_movement = self.detect_eye_movement(Y1, Y2)
        
        # 🎮 Send command to game (IMPORTANT!)
        self.send_command_to_game(eye_movement)
        
        # Update UI labels
        direction_label.config(text=f"Eye Movement: {eye_movement.upper()}")
        
        # Calculate signal quality with wavelet energy
        base_quality = np.mean(np.abs(af3_data)) + np.mean(np.abs(af4_data))
        
        # Add wavelet energy for quality assessment
        if len(af3_eog_corrected) >= self.wavelet_window_samples:
            y1_features = self.extract_wavelet_features(af3_eog_corrected)
            y2_features = self.extract_wavelet_features(af4_eog_corrected)
            wavelet_quality = (y1_features['scalogram_energy'] + y2_features['scalogram_energy']) / 1000
            signal_quality = base_quality + wavelet_quality
        else:
            signal_quality = base_quality
            
        if signal_quality > 1000:
            mental_label.config(text="EOG Status: Good Signal (Wavelet Enhanced)")
        elif signal_quality > 500:
            mental_label.config(text="EOG Status: Moderate Signal")
        else:
            mental_label.config(text="EOG Status: Weak Signal")
        
        # Debug output with wavelet info
        print(f"[EOG WAVELET] Y1={Y1:.3f}, Y2={Y2:.3f}, Movement={eye_movement}, Quality={signal_quality:.1f}")
        
        # Update charts with EOG data
        if hasattr(self.chart_manager, 'update_chart'):
            try:
                self.chart_manager.update_chart(
                    np.mean(af3_eog_corrected[-50:]) if len(af3_eog_corrected) > 50 else 0,
                    np.mean(af4_eog_corrected[-50:]) if len(af4_eog_corrected) > 50 else 0,
                    Y1, Y2
                )
            except:
                pass

    def calibrate(self):
        """Calibrate EOG system for different eye movements"""
        print("👁️ Starting EOG calibration...")
        movements = ["center", "left", "right", "up", "down", "blink"]
        self.calibration_data = {}
        self.current_movement_index = 0

        def collect_movement_data(movement, duration=3000):
            print(f"Please look {movement} for {duration/1000}s...")
            # Store current data for this movement
            af3_data = list(self.decoder.eeg_af3)[-100:] if len(self.decoder.eeg_af3) >= 100 else list(self.decoder.eeg_af3)
            af4_data = list(self.decoder.eeg_af4)[-100:] if len(self.decoder.eeg_af4) >= 100 else list(self.decoder.eeg_af4)
            
            self.calibration_data[movement] = {
                "AF3": af3_data,
                "AF4": af4_data,
            }
            
            # Schedule next movement
            if hasattr(self.chart_manager, 'parent_widget'):
                self.chart_manager.parent_widget.after(duration, next_movement)

        def next_movement():
            self.current_movement_index += 1
            if self.current_movement_index < len(movements):
                collect_movement_data(movements[self.current_movement_index])
            else:
                self.finish_calibration()

        # Start calibration
        collect_movement_data(movements[self.current_movement_index])

    def finish_calibration(self):
        """Complete EOG calibration and save data"""
        print("✅ EOG Calibration completed.")
        
        # Calculate thresholds based on calibration data
        try:
            # Analyze calibration data to set better thresholds
            if 'left' in self.calibration_data and 'right' in self.calibration_data:
                left_data = self.convert_to_uV(self.calibration_data['left']['AF3'])
                right_data = self.convert_to_uV(self.calibration_data['right']['AF4'])
                
                if len(left_data) > 0 and len(right_data) > 0:
                    # Update threshold based on calibration
                    self.detection_threshold = (np.std(left_data) + np.std(right_data)) / 4
                    print(f"📊 Updated detection threshold: {self.detection_threshold:.3f}")
            
            # Save calibration data
            data = []
            for movement, signals in self.calibration_data.items():
                for i in range(min(len(signals["AF3"]), len(signals["AF4"]))):
                    data.append({
                        "AF3": signals["AF3"][i],
                        "AF4": signals["AF4"][i],
                        "movement": movement
                    })
            
            pd.DataFrame(data).to_csv("eog_calibration_data.csv", index=False)
            print("💾 EOG calibration data saved to eog_calibration_data.csv")
            
        except Exception as e:
            print(f"⚠️ Calibration analysis failed: {e}")
        
        if hasattr(self, 'calibration_data'):
            delattr(self, 'calibration_data')
    
    def start_game_server(self):
        """Start TCP server for game communication"""
        try:
            # Import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'game'))
            from eog_tcp_server import EOGTCPServer
            
            self.tcp_server = EOGTCPServer(self)
            
            # Start server in separate thread
            import threading
            server_thread = threading.Thread(target=self.tcp_server.start, daemon=True)
            server_thread.start()
            
            self.game_connected = True
            print("🎮 Game TCP Server started - Ready for game connection")
            
        except Exception as e:
            print(f"❌ Failed to start game server: {e}")
            self.game_connected = False
    
    def send_command_to_game(self, command: str):
        """Send EOG command to connected game"""
        if self.tcp_server and self.game_connected:
            try:
                self.tcp_server.send_command(command)
                print(f"🎮 Sent to game: {command}")
            except Exception as e:
                print(f"❌ Failed to send command to game: {e}")
        # else:
        #     print(f"🎮 Game not connected - Command: {command}")
    
    def stop_game_server(self):
        """Stop the game TCP server"""
        if self.tcp_server:
            self.tcp_server.stop()
            self.tcp_server = None
            self.game_connected = False
            print("🎮 Game TCP Server stopped")
    
    # 🧠 ===== ALPHA/BETA BAND PROCESSING METHODS (Legacy EEG) =====
    
    def convert_to_uV(self, data):
        """Convert raw EEG data to microvolts"""
        return (1_000_000 * (np.array(data) - 8388608) * 1.6 / 8388608 / 2).astype(np.int16)

    def extract_features(self, data, ch_name="EEG", sample_rate=244):
        """Extract alpha and beta band features from EEG signal"""
        if len(data) < 2:
            return {
                "alpha": 0, "beta": 0, "alpha_ratio": 0, "beta_ratio": 0, 
                "beta_signal": np.array([]), "alpha_signal": np.array([])
            }

        def butter_bandpass(lowcut, highcut, fs, order=2):
            nyquist = 0.5 * fs
            low = lowcut / nyquist
            high = highcut / nyquist
            b, a = butter(order, [low, high], btype='band')
            return b, a

        def bandpass_filter(data, lowcut, highcut, fs, order=2):
            b, a = butter_bandpass(lowcut, highcut, fs, order)
            return lfilter(b, a, data)

        # Extract frequency bands
        filtered_alpha = bandpass_filter(data, 8, 13, sample_rate)  # Alpha: 8-13 Hz
        filtered_beta = bandpass_filter(data, 13, 30, sample_rate)  # Beta: 13-30 Hz
        
        # Calculate amplitudes (RMS)
        alpha_amplitude = np.sqrt(np.mean(filtered_alpha ** 2))
        beta_amplitude = np.sqrt(np.mean(filtered_beta ** 2))
        
        # Calculate ratios
        total_amplitude = alpha_amplitude + beta_amplitude
        alpha_ratio = alpha_amplitude / total_amplitude if total_amplitude > 0 else 0
        beta_ratio = beta_amplitude / total_amplitude if total_amplitude > 0 else 0

        print(f"[DEBUG] {ch_name}: alpha_amplitude={alpha_amplitude:.2f} µV, beta_amplitude={beta_amplitude:.2f} µV, "
              f"alpha_ratio={alpha_ratio:.2f}, beta_ratio={beta_ratio:.2f}")
        
        return {
            "alpha": alpha_amplitude, 
            "beta": beta_amplitude, 
            "alpha_ratio": alpha_ratio, 
            "beta_ratio": beta_ratio,
            "beta_signal": filtered_beta, 
            "alpha_signal": filtered_alpha
        }

    def classify_direction_legacy(self, af3_features, af4_features):
        """Legacy EEG-based direction classification using alpha/beta bands"""
        alpha_af3 = af3_features["alpha_ratio"]
        beta_af3 = af3_features["beta_ratio"]
        alpha_af4 = af4_features["alpha_ratio"]
        beta_af4 = af4_features["beta_ratio"]
        
        beta_diff = beta_af4 - beta_af3
        alpha_diff = alpha_af4 - alpha_af3

        self.beta_diff_history.append(beta_diff)
        std_beta_diff = np.std(list(self.beta_diff_history)) if len(self.beta_diff_history) > 10 else 0.1
        dynamic_threshold = max(0.02, std_beta_diff)

        print(f"[DEBUG] AF3: alpha={alpha_af3:.3f}, beta={beta_af3:.3f}, AF4: alpha={alpha_af4:.3f}, beta={beta_af4:.3f}, "
              f"beta_diff={beta_diff:.3f}, threshold={dynamic_threshold:.3f}")

        # Classification logic from legacy code
        if alpha_af3 < 0.1 and alpha_af4 < 0.1 and beta_af4 < 0.3:
            return "center"  # No significant activity
        elif beta_diff > dynamic_threshold and beta_af4 > 0.05:
            return "right"  # Right hemisphere activity
        elif beta_diff < -dynamic_threshold and beta_af3 > 0.05:
            return "left"   # Left hemisphere activity
        elif (alpha_af3 + alpha_af4) > 1.0 and abs(alpha_diff) < 0.2:
            return "up"     # Balanced high alpha
        else:
            return "down"   # Default

    def calculate_stress_level(self):
        """Calculate stress level from PPG data"""
        ppg_data = np.array([x for x in self.decoder.ppg if x < 1000000])
        if len(ppg_data) == 0:
            return 0.05
        stress_level = np.std(ppg_data) / 10000
        return min(max(1 - stress_level * 0.2, 0.05), 0.5)

    def process_eeg_legacy(self, mental_label=None, direction_label=None):
        """
        Legacy EEG processing with alpha/beta band analysis
        Can be used alongside or instead of EOG detection
        """
        # Convert raw data to microvolts
        af3_data = self.convert_to_uV(self.decoder.eeg_af3)
        af4_data = self.convert_to_uV(self.decoder.eeg_af4) if len(self.decoder.eeg_af4) > 0 else np.zeros_like(af3_data)
        
        # Extract alpha/beta features
        af3_features = self.extract_features(af3_data, ch_name="AF3")
        af4_features = self.extract_features(af4_data, ch_name="AF4")
        ppg_data = np.array(self.decoder.ppg)

        # Smoothing for AF4 beta
        window_size = 300
        if len(af4_data) >= window_size:
            af4_beta_smooth = np.mean([
                self.extract_features(af4_data[i:i+window_size], ch_name="AF4")["beta"] 
                for i in range(0, len(af4_data) - window_size + 1, window_size)
            ][-1:])  # Take last window
        else:
            af4_beta_smooth = af4_features["beta"]

        # Signal quality check
        signal_quality = np.mean(np.abs(af3_data)) + np.mean(np.abs(af4_data))
        print(f"[DEBUG] Signal quality: {signal_quality:.2f}, AF4 beta smooth: {af4_beta_smooth:.3f}")

        # Direction classification
        if signal_quality < 0.5 or len(self.decoder.eeg_af4) < 100:
            direction = "center"
        elif af4_beta_smooth > 0.3:
            direction = self.classify_direction_legacy(af3_features, af4_features)
            beta_diff = af4_features["beta_ratio"] - af3_features["beta_ratio"]
            self.beta_diff_buffer.append(beta_diff)
            
            # Stability check
            if len(self.directions) > 2 and self.directions[-1] == self.directions[-2]:
                self.directions.append(direction)
            else:
                self.directions.append("center")
        else:
            direction = "center"

        # Mental state from PPG
        stress_level = np.std(ppg_data) / 10000 if len(ppg_data) > 0 else 0.5
        self.mental_state = "Stressed" if stress_level > 0.1 else "Calm"
        
        # Update UI labels if provided
        if mental_label:
            mental_label.config(text=f"Mental State: {self.mental_state}")
        if direction_label:
            direction_label.config(text=f"Direction: {direction if direction != 'center' else 'Stopped'}")
        
        print(f"[DEBUG] Legacy EEG Direction: {direction}")

        # Update charts
        self.update_count += 1
        if self.update_count % 2 == 0 and self.chart_manager:
            self.chart_manager.update_chart(
                af3_features["alpha"], af4_features["alpha"], 
                af3_features["beta"], af4_features["beta"]
            )
        
        return direction

    def hybrid_detection(self, use_eeg=True, use_eog=True):
        """
        Hybrid detection combining both EEG (alpha/beta) and EOG (eye movement)
        Returns the most confident detection
        """
        results = {}
        
        if use_eeg and len(self.decoder.eeg_af3) > 100:
            eeg_direction = self.process_eeg_legacy()
            results['eeg'] = eeg_direction
        
        if use_eog and len(self.decoder.eeg_af3) > self.window_size:
            # Use standard EOG detection
            af3_data = self.convert_to_uV(self.decoder.eeg_af3)
            af4_data = self.convert_to_uV(self.decoder.eeg_af4) if len(self.decoder.eeg_af4) > 0 else af3_data
            
            eog_direction = self.detect_eye_movement_wavelet({
                'AF3': af3_data[-self.window_size:],
                'AF4': af4_data[-self.window_size:]
            })
            results['eog'] = eog_direction
        
        # Combine results (EOG takes priority for eye movements, EEG for mental states)
        if 'eog' in results and results['eog'] in ['left', 'right', 'up', 'down', 'blink']:
            final_direction = results['eog']
        elif 'eeg' in results:
            final_direction = results['eeg']
        else:
            final_direction = 'center'
        
        print(f"[HYBRID] EEG: {results.get('eeg', 'N/A')}, EOG: {results.get('eog', 'N/A')} → Final: {final_direction}")
        return final_direction