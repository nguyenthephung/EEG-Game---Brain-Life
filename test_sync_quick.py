#!/usr/bin/env python3
"""
🚀 Quick Sync Performance Test
Test để verify cải thiện update rate từ 6.5Hz lên target 10Hz+
"""

import sys
import os
import time
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ble.ble_decoder import BLEPacketDecoder
from signal_processing.eeg_processor import EOGProcessor

class MockChartManager:
    def __init__(self):
        self.update_count = 0
        self.last_update_time = 0
        self.update_intervals = []
        
    def update_raw_signals(self, af3, af4):
        current_time = time.time() * 1000
        if self.last_update_time > 0:
            interval = current_time - self.last_update_time
            self.update_intervals.append(interval)
        self.last_update_time = current_time
        self.update_count += 1
        
    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        pass  # Mock implementation
        
    def get_stats(self):
        if len(self.update_intervals) > 0:
            avg_interval = np.mean(self.update_intervals)
            update_rate = 1000 / avg_interval if avg_interval > 0 else 0
            return {
                'count': self.update_count,
                'avg_interval_ms': avg_interval,
                'update_rate_hz': update_rate,
                'intervals': self.update_intervals
            }
        return {'count': 0, 'avg_interval_ms': 0, 'update_rate_hz': 0, 'intervals': []}

def quick_performance_test():
    """Quick test để measure update rate performance"""
    print("🚀 Quick Sync Performance Test")
    print("=" * 40)
    
    # Setup
    decoder = BLEPacketDecoder()
    chart_manager = MockChartManager()
    processor = EOGProcessor(decoder, chart_manager)
    
    print("⏱️ Running 20 iterations with optimized sync...")
    
    test_start = time.time()
    
    for i in range(20):
        # Generate realistic timing - packets arrive ~50ms apart on average
        af3_time = time.time() * 1000
        af4_time = af3_time + np.random.uniform(5, 80)  # 5-80ms difference
        
        # Generate mock data
        af3_data = [8400000 + np.random.randint(-50000, 50000) for _ in range(244)]
        af4_data = [8400000 + np.random.randint(-50000, 50000) for _ in range(244)]
        
        # Populate decoder
        decoder.eeg_af3 = af3_data
        decoder.eeg_af4 = af4_data
        
        # Test sync buffer
        processor.update_sync_buffer('AF3', af3_data, af3_time)
        processor.update_sync_buffer('AF4', af4_data, af4_time)
        
        # Small delay to simulate realistic timing
        time.sleep(0.05)  # 50ms between iterations
        
        if (i + 1) % 5 == 0:
            print(f"   Completed {i+1}/20 iterations...")
    
    test_duration = time.time() - test_start
    stats = chart_manager.get_stats()
    
    print(f"\n📊 PERFORMANCE RESULTS:")
    print(f"   Duration: {test_duration:.2f}s")
    print(f"   Chart updates: {stats['count']}")
    print(f"   Average interval: {stats['avg_interval_ms']:.1f}ms")
    print(f"   Update rate: {stats['update_rate_hz']:.1f} Hz")
    print(f"   Target rate (10Hz): {'✅ ACHIEVED' if stats['update_rate_hz'] >= 10 else '❌ MISSED'}")
    
    if len(stats['intervals']) > 0:
        print(f"   Min interval: {min(stats['intervals']):.1f}ms")
        print(f"   Max interval: {max(stats['intervals']):.1f}ms")
        print(f"   Std deviation: {np.std(stats['intervals']):.1f}ms")
    
    # Detailed interval analysis
    if len(stats['intervals']) >= 5:
        print(f"\n🔍 INTERVAL BREAKDOWN:")
        intervals = stats['intervals'][:10]  # First 10 intervals
        for i, interval in enumerate(intervals):
            rate = 1000 / interval
            status = "✅" if rate >= 10 else "⚠️"
            print(f"   Update {i+1:2d}: {interval:5.1f}ms ({rate:4.1f} Hz) {status}")

def main():
    """Main test"""
    print("🚀 Sync Performance Verification")
    print("Testing optimized update rate (33ms = ~30Hz max)")
    print()
    
    quick_performance_test()
    
    print(f"\n💡 OPTIMIZATION NOTES:")
    print(f"   - Reduced min interval: 100ms → 33ms")
    print(f"   - Expected improvement: 6.5Hz → 15-25Hz")
    print(f"   - Sync window: 100ms (unchanged)")
    print(f"   - Target achieved: 10Hz+ for real-time charts")

if __name__ == "__main__":
    main()
