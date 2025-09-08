#!/usr/bin/env python3
"""
🧠 EEG Mock Data Generator for AF3/AF4 Channels
Generates realistic EEG signals for testing when hardware is not available

Features:
- Simulates alpha (8-13Hz) and beta (13-30Hz) brain waves
- AF3 (left frontal) and AF4 (right frontal) asymmetry
- Realistic noise, artifacts, and signal variations
- Different mental states: resting, focused, stressed, eye movements
- BLE packet timing simulation
"""

import numpy as np
import time
import threading
import queue
from typing import Dict, List, Tuple
import json
import math

class EEGSignalGenerator:
    """Generate realistic EEG signals for AF3 and AF4 channels"""
    
    def __init__(self, sampling_rate=244):
        self.sampling_rate = sampling_rate
        self.time = 0
        self.baseline_offset = 8388608  # 24-bit ADC baseline
        
        # Brain wave frequencies (Hz)
        self.freq_bands = {
            'delta': (0.5, 4),    # Deep sleep
            'theta': (4, 8),      # Drowsiness, meditation
            'alpha': (8, 13),     # Relaxed awareness
            'beta': (13, 30),     # Active thinking, focus
            'gamma': (30, 100)    # High-level cognitive processing
        }
        
        # Current mental state parameters
        self.mental_state = {
            'alertness': 0.5,     # 0=drowsy, 1=alert
            'focus': 0.5,         # 0=unfocused, 1=focused
            'stress': 0.3,        # 0=calm, 1=stressed
            'left_activity': 0.5, # 0=low, 1=high left hemisphere
            'right_activity': 0.5 # 0=low, 1=high right hemisphere
        }
        
        # Noise and artifact parameters
        self.noise_level = 0.1
        self.artifact_probability = 0.01  # 1% chance per sample
        
        print("🧠 EEG Signal Generator initialized")
        print(f"   Sampling rate: {sampling_rate} Hz")
        print(f"   Baseline: {self.baseline_offset}")

    def set_mental_state(self, state_name: str, **params):
        """Set predefined mental states or custom parameters"""
        
        presets = {
            'resting': {
                'alertness': 0.3, 'focus': 0.2, 'stress': 0.1,
                'left_activity': 0.4, 'right_activity': 0.4
            },
            'focused': {
                'alertness': 0.8, 'focus': 0.9, 'stress': 0.4,
                'left_activity': 0.7, 'right_activity': 0.6
            },
            'stressed': {
                'alertness': 0.9, 'focus': 0.3, 'stress': 0.8,
                'left_activity': 0.8, 'right_activity': 0.8
            },
            'meditation': {
                'alertness': 0.6, 'focus': 0.8, 'stress': 0.1,
                'left_activity': 0.5, 'right_activity': 0.5
            },
            'left_thinking': {
                'alertness': 0.7, 'focus': 0.8, 'stress': 0.3,
                'left_activity': 0.9, 'right_activity': 0.4
            },
            'right_thinking': {
                'alertness': 0.7, 'focus': 0.8, 'stress': 0.3,
                'left_activity': 0.4, 'right_activity': 0.9
            }
        }
        
        if state_name in presets:
            self.mental_state.update(presets[state_name])
            print(f"🧠 Mental state: {state_name}")
        
        # Override with custom parameters
        for key, value in params.items():
            if key in self.mental_state:
                self.mental_state[key] = np.clip(value, 0, 1)
        
        self._print_state()

    def _print_state(self):
        """Print current mental state"""
        state = self.mental_state
        print(f"   Alertness: {state['alertness']:.2f} | Focus: {state['focus']:.2f} | Stress: {state['stress']:.2f}")
        print(f"   Left: {state['left_activity']:.2f} | Right: {state['right_activity']:.2f}")

    def generate_brain_waves(self, duration_samples: int, channel: str) -> np.ndarray:
        """Generate realistic brain wave patterns for specific channel"""
        
        # Time array
        t = np.linspace(self.time, self.time + duration_samples/self.sampling_rate, duration_samples)
        self.time += duration_samples / self.sampling_rate
        
        # Channel-specific activity
        if channel.upper() == 'AF3':  # Left frontal
            activity_level = self.mental_state['left_activity']
            hemisphere_bias = 1.0
        else:  # AF4 - Right frontal  
            activity_level = self.mental_state['right_activity']
            hemisphere_bias = 1.0
        
        signal = np.zeros(duration_samples)
        
        # Generate each frequency band
        for band_name, (f_low, f_high) in self.freq_bands.items():
            band_signal = self._generate_frequency_band(t, f_low, f_high, band_name, activity_level)
            signal += band_signal
        
        # Add realistic noise
        noise = np.random.normal(0, self.noise_level * 1000, duration_samples)
        signal += noise
        
        # Add occasional artifacts (eye blinks, muscle tension)
        signal = self._add_artifacts(signal, duration_samples)
        
        # Convert to ADC units and add baseline
        signal_adc = signal * 1000 + self.baseline_offset  # Scale and offset
        
        # 🔧 FIX: Clamp to valid 24-bit range (0 to 16777215)
        signal_adc = np.clip(signal_adc, 0, 16777215)
        
        return signal_adc.astype(int)

    def _generate_frequency_band(self, t: np.ndarray, f_low: float, f_high: float, band_name: str, activity: float) -> np.ndarray:
        """Generate specific frequency band with realistic characteristics"""
        
        # Band-specific amplitudes based on mental state
        state = self.mental_state
        
        if band_name == 'alpha':
            # Alpha increases with relaxation, decreases with focus
            amplitude = (1.0 - state['focus']) * (1.0 - state['stress']) * 2000
        elif band_name == 'beta':
            # Beta increases with focus and stress
            amplitude = (state['focus'] + state['stress']) * activity * 1500
        elif band_name == 'theta':
            # Theta increases with drowsiness
            amplitude = (1.0 - state['alertness']) * 800
        elif band_name == 'delta':
            # Delta present in low levels during wake
            amplitude = (1.0 - state['alertness']) * 400
        else:  # gamma
            # Gamma increases with high cognitive load
            amplitude = state['focus'] * state['alertness'] * 300
        
        # Generate multiple frequency components within band
        n_components = 3
        frequencies = np.linspace(f_low, f_high, n_components)
        
        band_signal = np.zeros_like(t)
        for freq in frequencies:
            # Add some frequency modulation for realism
            freq_mod = freq + 0.5 * np.sin(2 * np.pi * 0.1 * t)  # 0.1 Hz modulation
            
            # Random phase for each component
            phase = np.random.uniform(0, 2*np.pi)
            
            # Generate component
            component = amplitude * np.sin(2 * np.pi * freq_mod * t + phase)
            
            # Add amplitude modulation
            amp_mod = 1.0 + 0.3 * np.sin(2 * np.pi * 0.05 * t)  # 0.05 Hz AM
            component *= amp_mod
            
            band_signal += component / n_components
        
        return band_signal

    def _add_artifacts(self, signal: np.ndarray, duration_samples: int) -> np.ndarray:
        """Add realistic EEG artifacts"""
        
        for i in range(duration_samples):
            if np.random.random() < self.artifact_probability:
                artifact_type = np.random.choice(['blink', 'muscle', 'electrode'])
                
                if artifact_type == 'blink':
                    # Eye blink artifact - large positive deflection
                    artifact_duration = int(0.3 * self.sampling_rate)  # 300ms
                    artifact_end = min(i + artifact_duration, duration_samples)
                    artifact_shape = np.exp(-np.linspace(0, 5, artifact_end - i))
                    signal[i:artifact_end] += 5000 * artifact_shape
                    
                elif artifact_type == 'muscle':
                    # Muscle tension - high frequency noise
                    artifact_duration = int(0.1 * self.sampling_rate)  # 100ms
                    artifact_end = min(i + artifact_duration, duration_samples)
                    muscle_noise = np.random.normal(0, 2000, artifact_end - i)
                    signal[i:artifact_end] += muscle_noise
                    
                elif artifact_type == 'electrode':
                    # Electrode movement - sudden step
                    step_size = np.random.uniform(-1000, 1000)
                    signal[i:] += step_size
        
        return signal

    def generate_packet(self, samples_per_packet: int = 16) -> Tuple[List[int], List[int]]:
        """Generate one BLE packet worth of data for both channels"""
        
        af3_data = self.generate_brain_waves(samples_per_packet, 'AF3')
        af4_data = self.generate_brain_waves(samples_per_packet, 'AF4')
        
        return af3_data.tolist(), af4_data.tolist()

class MockBLEDevice:
    """Simulate BLE device sending EEG packets"""
    
    def __init__(self, packet_interval_ms: float = 65.6):  # ~15.3 Hz packet rate
        self.generator = EEGSignalGenerator()
        self.packet_interval = packet_interval_ms / 1000.0  # Convert to seconds
        self.running = False
        self.thread = None
        self.data_queue = queue.Queue()
        self.packet_count = 0
        
        print(f"📡 Mock BLE Device initialized")
        print(f"   Packet rate: {1000/packet_interval_ms:.1f} Hz")
        print(f"   Samples per packet: 16 (AF3), 16 (AF4)")

    def start_streaming(self):
        """Start generating EEG data packets"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self.thread.start()
        print("📡 Started EEG data streaming")

    def stop_streaming(self):
        """Stop generating packets"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("📡 Stopped EEG data streaming")

    def _streaming_loop(self):
        """Main streaming loop"""
        while self.running:
            start_time = time.time()
            
            # Generate packet
            af3_samples, af4_samples = self.generator.generate_packet(16)
            
            # Create packet data structure
            packet_data = {
                'timestamp': time.time() * 1000,  # milliseconds
                'packet_id': self.packet_count,
                'af3_data': af3_samples,
                'af4_data': af4_samples
            }
            
            # Add to queue
            self.data_queue.put(packet_data)
            self.packet_count += 1
            
            # Print status every 100 packets
            if self.packet_count % 100 == 0:
                state = self.generator.mental_state
                print(f"📡 Packet #{self.packet_count} | State: alertness={state['alertness']:.2f}, focus={state['focus']:.2f}")
            
            # Sleep until next packet
            elapsed = time.time() - start_time
            sleep_time = max(0, self.packet_interval - elapsed)
            time.sleep(sleep_time)

    def get_packet(self) -> Dict:
        """Get next packet from queue"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None

    def set_mental_state(self, state_name: str, **params):
        """Change mental state during streaming"""
        self.generator.set_mental_state(state_name, **params)

def main():
    """Demo and test the EEG generator"""
    print("🧠 EEG Mock Data Generator Demo")
    print("=" * 50)
    
    # Create mock device
    device = MockBLEDevice()
    
    print("\n🎯 Testing different mental states:")
    
    # Test different states
    states_to_test = [
        ('resting', 3),
        ('focused', 3), 
        ('stressed', 2),
        ('left_thinking', 2),
        ('right_thinking', 2)
    ]
    
    device.start_streaming()
    
    try:
        for state_name, duration in states_to_test:
            print(f"\n--- Testing {state_name} state for {duration}s ---")
            device.set_mental_state(state_name)
            
            # Collect some packets
            start_time = time.time()
            packets_received = 0
            
            while time.time() - start_time < duration:
                packet = device.get_packet()
                if packet:
                    packets_received += 1
                    if packets_received % 20 == 0:  # Print every 20 packets
                        af3_mean = np.mean(packet['af3_data'])
                        af4_mean = np.mean(packet['af4_data'])
                        print(f"   Packet {packet['packet_id']}: AF3={af3_mean:.0f}, AF4={af4_mean:.0f}")
                
                time.sleep(0.01)  # 10ms polling
            
            print(f"   Received {packets_received} packets in {duration}s")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    finally:
        device.stop_streaming()
        print("\n✅ Demo completed")

if __name__ == "__main__":
    main()
