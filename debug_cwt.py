#!/usr/bin/env python3
"""
🔧 Quick PyWavelets CWT Debug
"""

import numpy as np
import pywt

def test_cwt_wavelets():
    """Test different wavelets with pywt.cwt"""
    print("🌊 Testing PyWavelets CWT")
    print("-" * 40)
    
    # Test signal
    t = np.linspace(0, 1, 244)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.random.randn(len(t))
    scales = np.arange(1, 32)
    sampling_rate = 244
    
    wavelets_to_test = ['haar', 'morl', 'cmor', 'mexh']
    
    for wavelet_name in wavelets_to_test:
        try:
            print(f"\n🔧 Testing wavelet: {wavelet_name}")
            
            # Test basic CWT
            coefs, frequencies = pywt.cwt(signal, scales, wavelet_name, 
                                        sampling_period=1/sampling_rate)
            
            print(f"  ✅ CWT success: coefs shape {coefs.shape}")
            print(f"  Frequencies shape: {frequencies.shape}")
            print(f"  Coefs dtype: {coefs.dtype}")
            
            # Test if it's complex
            if np.iscomplexobj(coefs):
                print(f"  ⚠️ Complex coefficients detected")
            else:
                print(f"  ✅ Real coefficients")
                
        except Exception as e:
            print(f"  ❌ Error with {wavelet_name}: {e}")
            
def test_wavelets_available():
    """List available wavelets"""
    print("\n📋 Available Wavelets:")
    print("-" * 40)
    
    families = pywt.families()
    for family in families:
        wavelets = pywt.wavelist(family)
        print(f"{family}: {wavelets}")

if __name__ == "__main__":
    test_wavelets_available()
    test_cwt_wavelets()
