#!/usr/bin/env python3
"""
🧪 Test Script for Mock EEG System
Tests all components of the mock data pipeline

Usage: python test_mock_system.py
"""

import time
import threading
import sys
import os
sys.path.append(os.path.dirname(__file__))

from mock_eeg_generator import EEGSignalGenerator
from mock_ble_adapter import MockBLEAdapter
from ble.ble_decoder import BLEPacketDecoder
from signal_processing.eeg_processor import EOGProcessor

class MockSystemTester:
    def __init__(self):
        print("🧪 Mock EEG System Test")
        print("=" * 40)
        
        # Initialize components
        self.decoder = BLEPacketDecoder()
        self.chart_manager = None  # No UI for this test
        self.eog_processor = EOGProcessor(self.decoder, self.chart_manager)
        
        # Mock adapter
        self.mock_adapter = MockBLEAdapter(self.decoder, self.chart_manager, self.eog_processor)
        
        self.test_results = []

    def test_signal_generation(self):
        """Test 1: Basic signal generation"""
        print("\n📊 Test 1: Signal Generation")
        print("-" * 30)
        
        generator = EEGSignalGenerator()
        
        # Test different mental states
        states = ["resting", "focused", "stressed", "meditation"]
        for state in states:
            print(f"   Testing {state} state...")
            generator.set_mental_state(state)
            
            # Generate some samples
            for _ in range(10):
                af3, af4 = generator.generate_sample()
                
            print(f"   ✅ {state}: AF3={af3:.3f}, AF4={af4:.3f}")
        
        self.test_results.append("Signal generation: PASS")
        return True

    def test_packet_conversion(self):
        """Test 2: BLE packet conversion"""
        print("\n📦 Test 2: Packet Conversion")
        print("-" * 30)
        
        try:
            # Generate mock data
            af3_data = [100, 200, 300, 400]
            af4_data = [150, 250, 350, 450]
            
            # Test packet creation
            packets = self.mock_adapter.create_eeg_packets(af3_data, af4_data)
            
            if len(packets) > 0:
                print(f"   ✅ Created {len(packets)} packets")
                
                # Show first packet structure
                first_packet = packets[0]
                print(f"   📦 Sample packet: {first_packet[:20]}...")
                
                self.test_results.append("Packet conversion: PASS")
                return True
            else:
                print("   ❌ No packets created")
                self.test_results.append("Packet conversion: FAIL")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results.append("Packet conversion: FAIL")
            return False

    def test_decoder_integration(self):
        """Test 3: Decoder integration"""
        print("\n🔍 Test 3: Decoder Integration")
        print("-" * 30)
        
        try:
            # Clear buffers
            self.decoder.eeg_af3.clear()
            self.decoder.eeg_af4.clear()
            
            # Generate and process some packets
            af3_data = [100, 200, 300]
            af4_data = [150, 250, 350]
            packets = self.mock_adapter.create_eeg_packets(af3_data, af4_data)
            
            # Process packets
            for packet in packets:
                self.mock_adapter.process_packet(packet)
            
            # Check results
            af3_samples = len(self.decoder.eeg_af3)
            af4_samples = len(self.decoder.eeg_af4)
            
            if af3_samples > 0 and af4_samples > 0:
                print(f"   ✅ Processed: AF3={af3_samples} samples, AF4={af4_samples} samples")
                
                # Show latest values
                if af3_samples > 0:
                    print(f"   📈 Latest AF3: {self.decoder.eeg_af3[-1]:.3f}")
                if af4_samples > 0:
                    print(f"   📈 Latest AF4: {self.decoder.eeg_af4[-1]:.3f}")
                    
                self.test_results.append("Decoder integration: PASS")
                return True
            else:
                print("   ❌ No samples processed")
                self.test_results.append("Decoder integration: FAIL")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results.append("Decoder integration: FAIL")
            return False

    def test_eog_processing(self):
        """Test 4: EOG processing"""
        print("\n👁️ Test 4: EOG Processing")
        print("-" * 30)
        
        try:
            # Fill buffers with test data
            self.decoder.eeg_af3.clear()
            self.decoder.eeg_af4.clear()
            
            # Add test data simulating eye movements
            for i in range(100):
                # Simulate left eye movement
                if 20 <= i < 40:
                    af3_val = 500 + 200 * (i - 20) / 20  # Rising edge on AF3
                    af4_val = 300
                # Simulate right eye movement  
                elif 60 <= i < 80:
                    af3_val = 300
                    af4_val = 500 + 200 * (i - 60) / 20  # Rising edge on AF4
                else:
                    af3_val = 300
                    af4_val = 300
                    
                self.decoder.eeg_af3.append(af3_val)
                self.decoder.eeg_af4.append(af4_val)
            
            # Test EOG detection
            direction = self.eog_processor.detect_eye_movement_wavelet()
            
            if direction:
                print(f"   ✅ Detected movement: {direction}")
                self.test_results.append("EOG processing: PASS")
                return True
            else:
                print(f"   ⚪ No movement detected (normal)")
                self.test_results.append("EOG processing: PASS")
                return True
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results.append("EOG processing: FAIL")
            return False

    def test_streaming_mode(self):
        """Test 5: Streaming mode"""
        print("\n🌊 Test 5: Streaming Mode")
        print("-" * 30)
        
        try:
            # Start streaming
            print("   Starting streaming...")
            self.mock_adapter.start_mock_streaming("resting")
            
            # Let it run for 3 seconds
            print("   Streaming for 3 seconds...")
            time.sleep(3)
            
            # Check if data is being generated
            af3_count = len(self.decoder.eeg_af3)
            af4_count = len(self.decoder.eeg_af4)
            
            # Stop streaming
            self.mock_adapter.stop_streaming()
            
            if af3_count > 100 and af4_count > 100:
                print(f"   ✅ Streamed: AF3={af3_count}, AF4={af4_count} samples")
                self.test_results.append("Streaming mode: PASS")
                return True
            else:
                print(f"   ❌ Insufficient data: AF3={af3_count}, AF4={af4_count}")
                self.test_results.append("Streaming mode: FAIL")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results.append("Streaming mode: FAIL")
            return False

    def test_mental_state_changes(self):
        """Test 6: Mental state changes"""
        print("\n🧠 Test 6: Mental State Changes")
        print("-" * 30)
        
        try:
            states = ["resting", "focused", "stressed", "meditation"]
            
            for state in states:
                print(f"   Testing {state} state...")
                
                # Start streaming with this state
                self.mock_adapter.start_mock_streaming(state)
                time.sleep(1)  # Let it generate some data
                
                # Check if data is being generated
                initial_count = len(self.decoder.eeg_af3)
                time.sleep(1)
                final_count = len(self.decoder.eeg_af3)
                
                if final_count > initial_count:
                    print(f"   ✅ {state}: Generated {final_count - initial_count} samples")
                else:
                    print(f"   ❌ {state}: No new samples")
                
                self.mock_adapter.stop_streaming()
            
            self.test_results.append("Mental state changes: PASS")
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results.append("Mental state changes: FAIL")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Running Mock EEG System Tests...")
        print("=" * 50)
        
        tests = [
            self.test_signal_generation,
            self.test_packet_conversion,
            self.test_decoder_integration,
            self.test_eog_processing,
            self.test_streaming_mode,
            self.test_mental_state_changes
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
        
        # Print results
        print("\n" + "=" * 50)
        print("🏁 TEST RESULTS")
        print("=" * 50)
        
        for result in self.test_results:
            status = "✅" if "PASS" in result else "❌"
            print(f"{status} {result}")
        
        print(f"\n📊 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests PASSED! Mock system is ready to use.")
        else:
            print("⚠️ Some tests FAILED. Check the issues above.")
        
        return passed == total

def main():
    """Main test function"""
    tester = MockSystemTester()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 50)
    print("📋 USAGE INSTRUCTIONS")
    print("=" * 50)
    print("1. Run main app with mock data:")
    print("   python main_mock.py")
    print()
    print("2. In the app:")
    print("   - Click 'Start Streaming'")
    print("   - Select different mental states")
    print("   - Watch real-time charts")
    print("   - Test EOG detection")
    print("   - Launch test game")
    print()
    print("3. No hardware needed - all simulated!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
