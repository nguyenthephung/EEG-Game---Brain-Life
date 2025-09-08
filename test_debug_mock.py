#!/usr/bin/env python3
"""
🔧 Quick Debug Script cho Mock EEG System
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mock_eeg_generator import EEGSignalGenerator, MockBLEDevice
from mock_ble_adapter import MockBLEAdapter
from ble.ble_decoder import BLEPacketDecoder

def test_basic_generation():
    """Test basic signal generation"""
    print("🧠 Testing EEG Signal Generation")
    print("-" * 40)
    
    generator = EEGSignalGenerator()
    generator.set_mental_state('resting')
    
    # Generate samples
    af3_samples, af4_samples = generator.generate_packet(samples_per_packet=16)
    
    print(f"AF3 samples: {len(af3_samples)}")
    print(f"AF4 samples: {len(af4_samples)}")
    print(f"AF3 range: {min(af3_samples)} - {max(af3_samples)}")
    print(f"AF4 range: {min(af4_samples)} - {max(af4_samples)}")
    
    # Check if in valid range
    valid_af3 = all(0 <= s <= 16777215 for s in af3_samples)
    valid_af4 = all(0 <= s <= 16777215 for s in af4_samples)
    
    print(f"AF3 valid range: {'✅' if valid_af3 else '❌'}")
    print(f"AF4 valid range: {'✅' if valid_af4 else '❌'}")
    
    return valid_af3 and valid_af4

def test_packet_conversion():
    """Test packet conversion to hex"""
    print("\n📦 Testing Packet Conversion")
    print("-" * 40)
    
    # Create decoder and adapter
    decoder = BLEPacketDecoder()
    adapter = MockBLEAdapter(decoder)
    
    # Test sample data (known good values)
    test_samples = [8388608 + i * 1000 for i in range(16)]  # Around baseline
    
    try:
        hex_packet = adapter._convert_to_ble_hex(test_samples, header=0x26)
        print(f"Generated hex packet: {hex_packet[:50]}...")
        print(f"Packet length: {len(hex_packet)} chars")
        
        # Test if it's valid hex
        try:
            bytes.fromhex(hex_packet)
            print("✅ Valid hex format")
            hex_valid = True
        except ValueError as e:
            print(f"❌ Invalid hex format: {e}")
            hex_valid = False
            
        # Test decoder
        try:
            result = decoder.decode_packet(hex_packet)
            if result:
                signal_type, value = result
                print(f"✅ Decoder success: {signal_type} = {value}")
                decode_success = True
            else:
                print("⚠️ Decoder returned None")
                decode_success = False
        except Exception as e:
            print(f"❌ Decoder error: {e}")
            decode_success = False
            
        return hex_valid and decode_success
        
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return False

def test_mock_device():
    """Test mock device packet generation"""
    print("\n📱 Testing Mock Device")
    print("-" * 40)
    
    device = MockBLEDevice()
    device.set_mental_state('focused')
    device.start_streaming()
    
    try:
        # Wait a bit for packets to generate
        time.sleep(0.5)
        
        # Get a few packets
        packets = []
        for i in range(3):
            packet = device.get_packet()
            if packet:
                packets.append(packet)
                print(f"Packet {i+1}: AF3={len(packet['af3_data'])}, AF4={len(packet['af4_data'])}")
            else:
                print(f"⚠️ Packet {i+1}: No data available")
                time.sleep(0.1)  # Wait a bit more
        
        device.stop_streaming()
        
        success = len(packets) > 0
        print(f"Device generation: {'✅' if success else '❌'}")
        return success
        
    except Exception as e:
        print(f"❌ Device error: {e}")
        device.stop_streaming()
        return False

def main():
    """Run all tests"""
    print("🧪 Mock EEG Debug Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic generation
    results.append(test_basic_generation())
    
    # Test 2: Packet conversion
    results.append(test_packet_conversion())
    
    # Test 3: Mock device
    results.append(test_mock_device())
    
    # Summary
    print(f"\n📊 RESULTS: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests PASSED! Mock system should work.")
    else:
        print("❌ Some tests FAILED. Check the issues above.")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
