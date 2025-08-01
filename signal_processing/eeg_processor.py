import numpy as np
from collections import deque
import pandas as pd
from scipy.signal import butter, lfilter

class EEGProcessor:
    def __init__(self, decoder, chart_manager):
        self.decoder = decoder
        self.chart_manager = chart_manager
        self.directions = deque(maxlen=10)
        self.mental_state = "Unknown"
        self.update_count = 0
        self.beta_diff_buffer = deque(maxlen=50)
        self.beta_diff_history = deque(maxlen=50)

    def convert_to_uV(self, data):
        return (1_000_000 * (np.array(data) - 8388608) * 1.6 / 8388608 / 2).astype(np.int16)

    def extract_features(self, data, ch_name="EEG", sample_rate=244):
        if len(data) < 2:
            return {"alpha": 0, "beta": 0, "alpha_ratio": 0, "beta_ratio": 0, "beta_signal": np.array([]), "alpha_signal": np.array([])}

        def butter_bandpass(lowcut, highcut, fs, order=2):
            nyquist = 0.5 * fs
            low = lowcut / nyquist
            high = highcut / nyquist
            b, a = butter(order, [low, high], btype='band')
            return b, a

        def bandpass_filter(data, lowcut, highcut, fs, order=2):
            b, a = butter_bandpass(lowcut, highcut, fs, order)
            return lfilter(b, a, data)

        filtered_alpha = bandpass_filter(data, 8, 13, sample_rate)
        filtered_beta = bandpass_filter(data, 13, 30, sample_rate)
        alpha_amplitude = np.sqrt(np.mean(filtered_alpha ** 2))
        beta_amplitude = np.sqrt(np.mean(filtered_beta ** 2))
        total_amplitude = alpha_amplitude + beta_amplitude
        alpha_ratio = alpha_amplitude / total_amplitude if total_amplitude > 0 else 0
        beta_ratio = beta_amplitude / total_amplitude if total_amplitude > 0 else 0

        print(f"[DEBUG] {ch_name}: alpha_amplitude={alpha_amplitude:.2f} µV, beta_amplitude={beta_amplitude:.2f} µV, "
              f"alpha_ratio={alpha_ratio:.2f}, beta_ratio={beta_ratio:.2f}")
        return {"alpha": alpha_amplitude, "beta": beta_amplitude, "alpha_ratio": alpha_ratio, "beta_ratio": beta_ratio,
                "beta_signal": filtered_beta, "alpha_signal": filtered_alpha}

    def classify_direction(self, af3_features, af4_features):
        alpha_af3 = af3_features["alpha_ratio"]
        beta_af3 = af3_features["beta_ratio"]
        alpha_af4 = af4_features["alpha_ratio"]
        beta_af4 = af4_features["beta_ratio"]
        beta_diff = beta_af4 - beta_af3
        alpha_diff = alpha_af4 - alpha_af3

        self.beta_diff_history.append(beta_diff)
        std_beta_diff = np.std(list(self.beta_diff_history)) if len(self.beta_diff_history) > 10 else 0.1
        dynamic_threshold = max(0.02, std_beta_diff)

        print(f"[DEBUG] AF3: alpha={alpha_af3}, beta={beta_af3}, AF4: alpha={alpha_af4}, beta={beta_af4}, beta_diff={beta_diff}, threshold={dynamic_threshold}")

        if alpha_af3 < 0.1 and alpha_af4 < 0.1 and beta_af4 < 0.3:
            return "none"
        elif beta_diff > dynamic_threshold and beta_af4 > 0.05:
            return "right"
        elif beta_diff < -dynamic_threshold and beta_af3 > 0.05:
            return "left"
        elif (alpha_af3 + alpha_af4) > 1.0 and abs(alpha_diff) < 0.2:
            return "up"
        else:
            return "down"

    def calculate_speed(self):
        ppg_data = np.array([x for x in self.decoder.ppg if x < 1000000])
        if len(ppg_data) == 0:
            return 0.05
        stress_level = np.std(ppg_data) / 10000
        return min(max(1 - stress_level * 0.2, 0.05), 0.5)

    def process_eeg_data(self, mental_label, direction_label):
        af3_data = self.convert_to_uV(self.decoder.eeg_af3)
        af4_data = self.convert_to_uV(self.decoder.eeg_af4) if len(self.decoder.eeg_af4) > 0 else np.zeros_like(af3_data)
        af3_features = self.extract_features(af3_data, ch_name="AF3")
        af4_features = self.extract_features(af4_data, ch_name="AF4")
        ppg_data = np.array(self.decoder.ppg)

        window_size = 300
        if len(af4_data) >= window_size:
            af4_beta_smooth = np.mean([self.extract_features(af4_data[i:i+window_size], ch_name="AF4")["beta"] 
                                      for i in range(0, len(af4_data) - window_size + 1, window_size)][-1])
        else:
            af4_beta_smooth = af4_features["beta"]

        signal_quality = np.mean(np.abs(af3_data)) + np.mean(np.abs(af4_data))
        print(f"[DEBUG] Signal quality: {signal_quality}, AF4 beta smooth: {af4_beta_smooth}")

        if signal_quality < 0.5 or len(self.decoder.eeg_af4) < 100:
            direction = "none"
        elif af4_beta_smooth > 0.3:
            direction = self.classify_direction(af3_features, af4_features)
            beta_diff = af4_features["beta_ratio"] - af3_features["beta_ratio"]
            self.beta_diff_buffer.append(beta_diff)
            smoothed_beta_diff = np.mean(self.beta_diff_buffer) if self.beta_diff_buffer else beta_diff
            if len(self.directions) > 2 and self.directions[-1] == self.directions[-2]:
                self.directions.append(direction)
            else:
                self.directions.append("none")
        else:
            direction = "none"

        stress_level = np.std(ppg_data) / 10000 if len(ppg_data) > 0 else 0.5
        self.mental_state = "Stressed" if stress_level > 0.1 else "Calm"
        mental_label.config(text=f"Mental State: {self.mental_state}")
        direction_label.config(text=f"Direction: {direction if direction != 'none' else 'Stopped'}")
        print(f"[DEBUG] Predicted direction: {direction}")

        self.update_count += 1
        if self.update_count % 2 == 0:
            self.chart_manager.update_chart(af3_features["alpha"], af4_features["alpha"], 
                                           af3_features["beta"], af4_features["beta"])

    def calibrate(self):
        print("🧠 Starting calibration...")
        directions = ["up", "down", "left", "right", "none"]
        self.calibration_data = []
        self.current_direction_index = 0

        def collect_data(direction, duration=5000):
            print(f"Imagine '{direction}' for {duration/1000}s.")
            self.calibration_data.append({
                "AF3": list(self.decoder.eeg_af3),
                "AF4": list(self.decoder.eeg_af4),
                "PPG": list(self.decoder.ppg),
                "label": direction
            })
            self.root.after(duration, next_direction)

        def next_direction():
            self.current_direction_index += 1
            if self.current_direction_index < len(directions):
                collect_data(directions[self.current_direction_index])
            else:
                self.finish_calibration()

        collect_data(directions[self.current_direction_index])

    def finish_calibration(self):
        print("✅ Calibration completed.")
        data = []
        for entry in self.calibration_data:
            for i in range(min(len(entry["AF3"]), len(entry["AF4"]), len(entry["PPG"]))):
                data.append({
                    "AF3": entry["AF3"][i],
                    "AF4": entry["AF4"][i],
                    "PPG": entry["PPG"][i],
                    "label": entry["label"]
                })
        pd.DataFrame(data).to_csv("calibration_data.csv", index=False)
        delattr(self, 'calibration_data')