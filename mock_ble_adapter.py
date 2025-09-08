#!/usr/bin/env python3
"""
🔌 Mock BLE Integration Adapter
Connects the EEG mock generator with existing BLE decoder infrastructure

This adapter:
1. Replaces real BLE connection with mock data
2. Maintains compatibility with existing decoder
3. Provides realistic packet timing and structure
4. Allows switching between mock and real device
"""

import asyncio
import threading
import time
import struct
from typing import Optional, Dict, List
import numpy as np
from mock_eeg_generator import MockBLEDevice

class MockBLEAdapter:
    """Adapter to integrate mock EEG data with existing BLE infrastructure"""
    
    def __init__(self, decoder, chart_manager=None, eog_processor=None):
        self.decoder = decoder
        self.chart_manager = chart_manager
        self.eog_processor = eog_processor
        
        # Mock device
        self.mock_device = MockBLEDevice()
        self.running = False
        self.integration_thread = None
        
        # Packet processing
        self.packets_processed = 0
        self.last_status_time = 0
        
        print("🔌 Mock BLE Adapter initialized")
        print("   Compatible with existing BLE decoder")

    def start_mock_streaming(self, mental_state: str = 'resting'):
        """Start mock data streaming with specified mental state"""
        if self.running:
            print("⚠️ Mock streaming already running")
            return
        
        # Set initial mental state
        self.mock_device.set_mental_state(mental_state)
        
        # Start mock device
        self.mock_device.start_streaming()
        
        # Start integration thread
        self.running = True
        self.integration_thread = threading.Thread(target=self._integration_loop, daemon=True)
        self.integration_thread.start()
        
        print(f"🚀 Mock streaming started with '{mental_state}' state")
        print("📊 Data will be fed to existing decoder and processors")

    def stop_mock_streaming(self):
        """Stop mock data streaming"""
        self.running = False
        self.mock_device.stop_streaming()
        
        if self.integration_thread:
            self.integration_thread.join(timeout=1.0)
        
        print("🛑 Mock streaming stopped")
    
    def stop_streaming(self):
        """Alias for stop_mock_streaming for compatibility"""
        self.stop_mock_streaming()

    def change_mental_state(self, state_name: str, **params):
        """Change mental state during streaming"""
        self.mock_device.set_mental_state(state_name, **params)
        print(f"🧠 Changed to '{state_name}' state")

    def _integration_loop(self):
        """Main loop to process mock packets and feed to decoder"""
        while self.running:
            try:
                # Get packet from mock device
                packet = self.mock_device.get_packet()
                
                if packet:
                    # Process packet through existing pipeline
                    self._process_mock_packet(packet)
                    self.packets_processed += 1
                    
                    # Status update every 5 seconds
                    current_time = time.time()
                    if current_time - self.last_status_time >= 5.0:
                        self._print_status()
                        self.last_status_time = current_time
                
                # Small delay to prevent busy waiting
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                print(f"❌ Integration loop error: {e}")
                time.sleep(0.1)

    def _process_mock_packet(self, packet: Dict):
        """Process mock packet through existing decoder infrastructure"""
        
        # Simulate BLE packet structure by converting to hex
        af3_hex = self._convert_to_ble_hex(packet['af3_data'], header=0x26)  # AF3 header
        af4_hex = self._convert_to_ble_hex(packet['af4_data'], header=0x24)  # AF4 header
        
        # Feed AF3 data to decoder
        try:
            result = self.decoder.decode_packet(af3_hex)
            if result:
                signal_type, value = result
                # Trigger processing if EOG processor available
                if self.eog_processor:
                    self._trigger_processing()
        except Exception as e:
            print(f"⚠️ AF3 decode error: {e}")
        
        # Small delay between AF3 and AF4 to simulate real BLE timing
        time.sleep(0.001)
        
        # Feed AF4 data to decoder  
        try:
            result = self.decoder.decode_packet(af4_hex)
            if result:
                signal_type, value = result
                # Trigger processing if EOG processor available
                if self.eog_processor:
                    self._trigger_processing()
        except Exception as e:
            print(f"⚠️ AF4 decode error: {e}")

    def _convert_to_ble_hex(self, samples: List[int], header: int) -> str:
        """Convert sample array to BLE hex packet format matching real decoder expectations"""
        
        # 🎯 CRITICAL: Decoder expects format: header + ASCII_value + 0x0A
        # Not binary data, but ASCII text!
        
        # Take first sample (simulate single value per packet like real device)
        sample = samples[0] if samples else 8388608
        
        # Ensure sample is in valid range
        sample = max(0, min(16777215, int(sample)))  # 24-bit range
        
        # Create packet: header + ASCII_digits + terminator
        packet_bytes = []
        
        # Add header
        packet_bytes.append(header & 0xFF)
        
        # Convert sample to ASCII string and add bytes
        sample_str = str(sample)
        for char in sample_str:
            packet_bytes.append(ord(char))
        
        # Add termination
        packet_bytes.append(0x0A)
        
        # Convert to hex string
        hex_string = ''.join([f'{byte:02x}' for byte in packet_bytes])
        
        return hex_string

    def _trigger_processing(self):
        """Trigger EOG/EEG processing if processors are available"""
        
        # Check if we have enough data for processing
        if (len(self.decoder.eeg_af3) >= 100 and 
            len(self.decoder.eeg_af4) >= 100 and 
            self.eog_processor):
            
            try:
                # Simulate UI labels for processing
                class MockLabel:
                    def __init__(self):
                        self.text = ""
                    def config(self, text=""):
                        self.text = text
                
                mental_label = MockLabel()
                direction_label = MockLabel()
                
                # Process through EOG processor
                self.eog_processor.process_eog_data(mental_label, direction_label)
                
            except Exception as e:
                print(f"⚠️ Processing error: {e}")

    def _print_status(self):
        """Print current status"""
        state = self.mock_device.generator.mental_state
        print(f"📊 Status: {self.packets_processed} packets | "
              f"Alert: {state['alertness']:.2f} | Focus: {state['focus']:.2f} | "
              f"AF3 buffer: {len(self.decoder.eeg_af3)} | AF4 buffer: {len(self.decoder.eeg_af4)}")

def create_demo_sequence():
    """Create a demo sequence with changing mental states"""
    return [
        ('resting', 10, "😌 Relaxed state - high alpha waves"),
        ('focused', 8, "🎯 Focused attention - high beta waves"), 
        ('stressed', 5, "😰 Stressed state - high beta + noise"),
        ('left_thinking', 6, "🧠 Left brain activity - language processing"),
        ('right_thinking', 6, "🎨 Right brain activity - spatial processing"),
        ('meditation', 8, "🧘 Meditation state - balanced alpha"),
        ('resting', 5, "😌 Back to resting state")
    ]

def main():
    """Demo the mock BLE integration"""
    print("🔌 Mock BLE Integration Demo")
    print("=" * 50)
    
    # Import existing components
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from ble.ble_decoder import BLEPacketDecoder
        from ui.chart_manager import EOGChartManager
        from signal_processing.eeg_processor import EOGProcessor
        
        # Create components
        decoder = BLEPacketDecoder()
        
        # Mock chart manager for demo
        class MockChartManager:
            def update_raw_signals(self, af3, af4):
                pass
            def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
                pass
        
        chart_manager = MockChartManager()
        eog_processor = EOGProcessor(decoder, chart_manager)
        
        # Create adapter
        adapter = MockBLEAdapter(decoder, chart_manager, eog_processor)
        
        print("✅ All components loaded successfully")
        
        # Run demo sequence
        demo_sequence = create_demo_sequence()
        
        print(f"\n🎬 Starting demo sequence ({len(demo_sequence)} states)")
        print("📊 Watch the console for EEG processing output")
        print("🛑 Press Ctrl+C to stop\n")
        
        try:
            for state_name, duration, description in demo_sequence:
                print(f"\n--- {description} ({duration}s) ---")
                
                if state_name == demo_sequence[0][0]:  # First state
                    adapter.start_mock_streaming(state_name)
                else:
                    adapter.change_mental_state(state_name)
                
                # Wait for duration
                time.sleep(duration)
        
        except KeyboardInterrupt:
            print(f"\n🛑 Demo interrupted by user")
        
        finally:
            adapter.stop_mock_streaming()
            print("✅ Demo completed")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
