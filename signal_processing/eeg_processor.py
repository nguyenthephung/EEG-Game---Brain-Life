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
        self.wavelet_name = 'haar'  # Haar wavelet as specified in research
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
        
        print("🔧 EOG Processor initialized for eye movement detection")

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

    def continuous_wavelet_transform(self, signal, wavelet='haar'):
        """
        Apply Continuous Wavelet Transform according to research formula:
        Ca,b(ω) = Ca,b = ∫ EEG(t) ψa,b(t) dt
        where ψa,b(t) = 1/√|a| ψ*((t-b)/a)
        """
        if len(signal) < 10:
            return None, None
            
        try:
            # Apply CWT with Haar wavelet
            coefs, frequencies = pywt.cwt(signal, self.scales, wavelet, 1/self.sampling_rate)
            
            # coefs shape: (scales, time_samples)
            return coefs, frequencies
        except Exception as e:
            print(f"CWT Error: {e}")
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

    def detect_eye_movement_wavelet(self, Y1_signal, Y2_signal):
        """
        Hierarchical classification using wavelet features for 6-class detection
        Based on research: fixed thresholds for 4 features with binary outputs
        """
        current_time = time.time()
        
        # Prevent too frequent detections
        if current_time - self.last_detection_time < self.min_detection_interval:
            return self.current_movement
        
        # Extract wavelet features for both Y1 and Y2 signals
        y1_features = self.extract_wavelet_features(Y1_signal)
        y2_features = self.extract_wavelet_features(Y2_signal)
        
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
        """Main EOG processing function - replaces process_eeg_data"""
        # Get raw data and convert to microvolts
        af3_data = self.convert_to_uV(self.decoder.eeg_af3)
        af4_data = self.convert_to_uV(self.decoder.eeg_af4) if len(self.decoder.eeg_af4) > 0 else np.zeros_like(af3_data)
        
        if len(af3_data) < 50 or len(af4_data) < 50:
            direction_label.config(text="Eye Movement: Insufficient Data")
            mental_label.config(text="EOG Status: Waiting...")
            return
        
        # Preprocess signals
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