#!/usr/bin/env python3
"""
🧪 Mock EEG Integration Test Suite
Tests the mock EEG generator integration with existing BLE infrastructure

Tests:
1. Mock signal generation
2. BLE packet conversion  
3. Decoder integration
4. EOG processor compatibility
5. Chart system integration
"""

import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mock_eeg_generator import EEGSignalGenerator, MockBLEDevice
from mock_ble_adapter import MockBLEAdapter
from ble.ble_decoder import BLEPacketDecoder
from signal_processing.eeg_processor import EOGProcessor

class MockChartManager:
    """Minimal chart manager for testing"""
    def __init__(self):
        self.update_count = 0
        
    def update_raw_signals(self, af3, af4):
        self.update_count += 1
        print(f"📊 Chart update #{self.update_count}: AF3={af3:.0f}, AF4={af4:.0f}")
        
    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        print(f"🧠 Alpha/Beta: AF3(α={af3_alpha:.0f}, β={af3_beta:.0f}) AF4(α={af4_alpha:.0f}, β={af4_beta:.0f})")

def test_signal_generation():
    """Test basic signal generation"""
    print("🔄 Testing signal generation...")
    
    generator = EEGSignalGenerator()
    
    try:
        # Test AF3 signal
        af3_signal = generator.generate_af3_signal(0.1)  # 100ms
        if len(af3_signal) > 0:
            print(f"   ✅ AF3: Generated {len(af3_signal)} samples")
            print(f"   📊 Range: {min(af3_signal)} - {max(af3_signal)}")
            
            # Check 24-bit range
            if all(0 <= s <= 16777215 for s in af3_signal):
                print(f"   ✅ All samples in valid 24-bit range")
                return True
            else:
                print(f"   ❌ Some samples out of 24-bit range")
                return False
        else:
            print(f"   ❌ No AF3 samples generated")
            return False
            
    except Exception as e:
        print(f"   ❌ Signal generation error: {e}")
        return False

def test_packet_conversion():
    """Test BLE packet conversion"""
    print("🔄 Testing packet conversion...")
    
    try:
        decoder = BLEPacketDecoder()
        generator = EEGSignalGenerator()
        adapter = MockBLEAdapter(decoder)
        
        # Generate simple test samples
        test_samples = [8400000, 8350000, 8450000, 8380000]  # Valid 24-bit values
        hex_packet = adapter._convert_to_ble_hex(test_samples, header=0x26)
        
        print(f"   ✅ Converted {len(test_samples)} samples")
        print(f"   📦 Packet length: {len(hex_packet)} hex chars")
        print(f"   🔍 Sample packet: {hex_packet[:20]}...")
        
        # Test decoder
        result = decoder.decode_packet(hex_packet)
        if result:
            signal_type, value = result
            print(f"   ✅ Decoder success: {signal_type}")
            return True
        else:
            print(f"   ⚠️ Decoder returned None")
            return False
            
    except Exception as e:
        print(f"   ❌ Packet conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_adapter_integration():
    """Test full adapter integration"""
    print("🔄 Testing adapter integration...")
    
    try:
        decoder = BLEPacketDecoder()
        chart_manager = MockChartManager()
        eog_processor = EOGProcessor(decoder, chart_manager)
        adapter = MockBLEAdapter(decoder, chart_manager, eog_processor)
        
        print("   📡 Starting mock streaming...")
        adapter.start_mock_streaming('resting')
        
        # Let it run for 2 seconds
        time.sleep(2)
        
        print("   🛑 Stopping mock streaming...")
        adapter.stop_streaming()
        
        # Check if we got chart updates
        if chart_manager.update_count > 0:
            print(f"   ✅ Got {chart_manager.update_count} chart updates")
            return True
        else:
            print(f"   ❌ No chart updates received")
            return False
            
    except Exception as e:
        print(f"   ❌ Adapter integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mental_state_changes():
    """Test mental state switching"""
    print("🔄 Testing mental state changes...")
    
    try:
        device = MockBLEDevice()
        device.start_streaming()
        
        states_to_test = ['resting', 'focused', 'stressed']
        
        for state in states_to_test:
            device.set_mental_state(state)
            packet = device.get_packet()
            
            if packet and 'af3_data' in packet and 'af4_data' in packet:
                print(f"   ✅ {state}: Generated AF3={len(packet['af3_data'])}, AF4={len(packet['af4_data'])} samples")
            else:
                print(f"   ❌ {state}: Failed to generate packet")
                device.stop_streaming()
                return False
        
        device.stop_streaming()
        print(f"   ✅ All mental states working")
        return True
        
    except Exception as e:
        print(f"   ❌ Mental state test error: {e}")
        return False

def run_integration_test():
    """Run complete integration test suite"""
    print("🧪 Mock EEG Integration Test Suite")
    print("=" * 50)
    
    test_results = {
        'signal_generation': False,
        'packet_conversion': False, 
        'adapter_integration': False,
        'mental_state_changes': False
    }
    
    # Run tests
    test_results['signal_generation'] = test_signal_generation()
    print()
    
    test_results['packet_conversion'] = test_packet_conversion()
    print()
    
    test_results['adapter_integration'] = test_adapter_integration()
    print()
    
    test_results['mental_state_changes'] = test_mental_state_changes()
    print()
    
    # Summary
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print("=" * 50)
    print("🏁 TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests PASSED! Mock system ready to use.")
        print("\n📋 Next steps:")
        print("1. Run: python main_mock.py")
        print("2. Test real-time charts and EOG detection")
        print("3. Launch game integration test")
    else:
        print("⚠️ Some tests FAILED. Check the issues above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_integration_test()
    exit(0 if success else 1)
