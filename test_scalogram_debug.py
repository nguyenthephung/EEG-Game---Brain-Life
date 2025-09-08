#!/usr/bin/env python3
"""
🧪 Test Scalogram Chart Generation
Debug specifically Y1 and Y2 scalogram charts
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signal_processing.eeg_processor import EOGProcessor
from ble.ble_decoder import BLEPacketDecoder
from ui.chart_manager import EOGChartManager
import tkinter as tk

def test_scalogram_generation():
    """Test if scalogram data is being generated correctly"""
    print("🧪 Testing Scalogram Generation")
    print("-" * 50)
    
    # Create components
    decoder = BLEPacketDecoder()
    root = tk.Tk()
    chart_manager = EOGChartManager(root)
    processor = EOGProcessor(decoder, chart_manager)
    
    # Create test signals
    t = np.linspace(0, 1, 244)  # 1 second at 244Hz
    
    # Simulate eye movement signals
    y1_signal = np.sin(2 * np.pi * 5 * t) + 0.5 * np.random.randn(len(t))  # 5Hz + noise
    y2_signal = np.cos(2 * np.pi * 3 * t) + 0.3 * np.random.randn(len(t))  # 3Hz + noise
    
    print(f"Y1 signal: {len(y1_signal)} samples, range: {y1_signal.min():.3f} to {y1_signal.max():.3f}")
    print(f"Y2 signal: {len(y2_signal)} samples, range: {y2_signal.min():.3f} to {y2_signal.max():.3f}")
    
    try:
        # Extract features (should generate scalogram)
        y1_features = processor.extract_wavelet_features(y1_signal)
        y2_features = processor.extract_wavelet_features(y2_signal)
        
        print(f"Y1 features keys: {list(y1_features.keys())}")
        print(f"Y2 features keys: {list(y2_features.keys())}")
        
        # Check if scalogram data exists
        y1_scalogram = y1_features.get('scalogram')
        y2_scalogram = y2_features.get('scalogram')
        
        if y1_scalogram is not None:
            print(f"✅ Y1 scalogram: {y1_scalogram.shape}, type: {type(y1_scalogram)}")
        else:
            print("❌ Y1 scalogram: None")
            
        if y2_scalogram is not None:
            print(f"✅ Y2 scalogram: {y2_scalogram.shape}, type: {type(y2_scalogram)}")
        else:
            print("❌ Y2 scalogram: None")
        
        # Test chart update
        print("\n📊 Testing Chart Update")
        eog_features = {
            'y1': np.mean(y1_signal),
            'y2': np.mean(y2_signal),
            'y1_features': y1_features,
            'y2_features': y2_features
        }
        
        # Check chart manager buffers before update
        print(f"Chart Y1 buffer before: {chart_manager.scalogram_y1_buffer is not None}")
        print(f"Chart Y2 buffer before: {chart_manager.scalogram_y2_buffer is not None}")
        
        # Update chart
        chart_manager.update_eog_data(np.mean(y1_signal), np.mean(y2_signal), eog_features)
        
        # Check chart manager buffers after update
        print(f"Chart Y1 buffer after: {chart_manager.scalogram_y1_buffer is not None}")
        print(f"Chart Y2 buffer after: {chart_manager.scalogram_y2_buffer is not None}")
        
        if chart_manager.scalogram_y1_buffer is not None:
            print(f"✅ Y1 buffer shape: {chart_manager.scalogram_y1_buffer.shape}")
        if chart_manager.scalogram_y2_buffer is not None:
            print(f"✅ Y2 buffer shape: {chart_manager.scalogram_y2_buffer.shape}")
        
        success = (y1_scalogram is not None and y2_scalogram is not None and
                  chart_manager.scalogram_y1_buffer is not None and 
                  chart_manager.scalogram_y2_buffer is not None)
        
        print(f"\n🎯 Scalogram test: {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error in scalogram test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

def test_wavelet_computation():
    """Test raw wavelet computation"""
    print("\n🌊 Testing Wavelet Computation")
    print("-" * 50)
    
    try:
        import pywt
        
        # Test signal
        t = np.linspace(0, 1, 244)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.random.randn(len(t))
        
        # Compute CWT
        scales = np.arange(1, 32)
        coefficients, frequencies = pywt.cwt(signal, scales, 'morl', sampling_period=1/244)
        
        print(f"Signal length: {len(signal)}")
        print(f"Coefficients shape: {coefficients.shape}")
        print(f"Scales: {len(scales)}")
        
        # Compute scalogram
        scalogram = np.abs(coefficients) ** 2
        print(f"Scalogram shape: {scalogram.shape}")
        print(f"Scalogram range: {scalogram.min():.3f} to {scalogram.max():.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Wavelet computation error: {e}")
        return False

def main():
    """Run all scalogram tests"""
    print("🧪 Scalogram Debug Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic wavelet computation
    results.append(test_wavelet_computation())
    
    # Test 2: Scalogram generation through processor
    results.append(test_scalogram_generation())
    
    # Summary
    print(f"\n📊 RESULTS: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All scalogram tests PASSED!")
        print("If Y1/Y2 charts still don't show, the issue is likely in:")
        print("  - Chart rendering/display")
        print("  - UI update timing")
        print("  - Chart axes configuration")
    else:
        print("❌ Some tests FAILED. Check the issues above.")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
