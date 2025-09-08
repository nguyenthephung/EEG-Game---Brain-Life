#!/usr/bin/env python3
"""
📊 Test AF3/AF4 Chart Synchronization
Kiểm tra việc sync chart giữa AF3 và AF4 channels

Test này kiểm tra:
1. Chart sync buffer hoạt động đúng
2. AF3/AF4 được update cùng lúc
3. Timing synchronization với tolerance window
"""

import sys
import os
import numpy as np
import time
from collections import deque

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ble.ble_decoder import BLEPacketDecoder
from signal_processing.eeg_processor import EOGProcessor

class MockChartManager:
    """Mock chart manager để test sync functionality"""
    
    def __init__(self):
        self.raw_update_count = 0
        self.chart_update_count = 0
        self.last_raw_update = None
        self.last_chart_update = None
        self.sync_logs = []
        
    def update_raw_signals(self, af3_value, af4_value):
        """Mock raw signal update"""
        current_time = time.time() * 1000
        self.raw_update_count += 1
        self.last_raw_update = (af3_value, af4_value, current_time)
        
        print(f"📊 [RAW UPDATE {self.raw_update_count:3d}] AF3: {af3_value:8.1f} | AF4: {af4_value:8.1f} | Time: {current_time:.0f}")
        
        # Log for sync analysis
        self.sync_logs.append({
            'type': 'raw',
            'count': self.raw_update_count,
            'af3': af3_value,
            'af4': af4_value,
            'timestamp': current_time
        })
    
    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        """Mock alpha/beta chart update"""
        current_time = time.time() * 1000
        self.chart_update_count += 1
        self.last_chart_update = (af3_alpha, af4_alpha, af3_beta, af4_beta, current_time)
        
        print(f"🧠 [CHART UPDATE {self.chart_update_count:2d}] AF3: α={af3_alpha:.3f}, β={af3_beta:.3f} | "
              f"AF4: α={af4_alpha:.3f}, β={af4_beta:.3f} | Time: {current_time:.0f}")
        
        # Log for sync analysis
        self.sync_logs.append({
            'type': 'chart',
            'count': self.chart_update_count,
            'af3_alpha': af3_alpha,
            'af4_alpha': af4_alpha,
            'af3_beta': af3_beta,
            'af4_beta': af4_beta,
            'timestamp': current_time
        })
    
    def get_stats(self):
        """Get update statistics"""
        return {
            'raw_updates': self.raw_update_count,
            'chart_updates': self.chart_update_count,
            'total_logs': len(self.sync_logs)
        }

def simulate_asynchronous_packets():
    """Simulate realistic AF3/AF4 packet timing (asynchronous arrival)"""
    print("🔧 Testing Asynchronous Packet Simulation")
    print("=" * 50)
    
    # Initialize components
    decoder = BLEPacketDecoder()
    chart_manager = MockChartManager()
    processor = EOGProcessor(decoder, chart_manager)
    
    print("📡 Simulating realistic BLE packet timing...")
    print("   AF3 and AF4 packets arrive at different times")
    print("   Testing sync buffer behavior\n")
    
    # Generate test patterns
    base_time = time.time() * 1000
    
    for i in range(10):  # 10 iterations
        print(f"\n--- Iteration {i+1} ---")
        
        # Generate mock EEG data with different patterns
        af3_samples = np.random.normal(8388608, 30000, 244).astype(int)
        af4_samples = np.random.normal(8388608, 25000, 244).astype(int)
        
        # Simulate different packet arrival timing
        af3_arrival_time = base_time + i * 200 + np.random.uniform(0, 50)  # Random delay 0-50ms
        af4_arrival_time = base_time + i * 200 + np.random.uniform(20, 80) # Random delay 20-80ms
        
        print(f"⏰ AF3 packet arrival: {af3_arrival_time:.1f}ms")
        print(f"⏰ AF4 packet arrival: {af4_arrival_time:.1f}ms")
        print(f"🔄 Time difference: {abs(af3_arrival_time - af4_arrival_time):.1f}ms")
        
        # Simulate AF3 packet arrival first
        decoder.eeg_af3 = af3_samples.tolist()
        decoder.eeg_af4 = []  # AF4 not yet arrived
        processor.update_sync_buffer('AF3', af3_samples, af3_arrival_time)
        
        time.sleep(0.05)  # Small delay to simulate real timing
        
        # Simulate AF4 packet arrival
        decoder.eeg_af4 = af4_samples.tolist()
        processor.update_sync_buffer('AF4', af4_samples, af4_arrival_time)
        
        time.sleep(0.1)  # Wait between iterations
    
    # Print final statistics
    stats = chart_manager.get_stats()
    print(f"\n📊 SYNCHRONIZATION TEST RESULTS:")
    print(f"   Raw signal updates: {stats['raw_updates']}")
    print(f"   Chart updates: {stats['chart_updates']}")
    print(f"   Total logged events: {stats['total_logs']}")
    
    # Analyze sync behavior
    analyze_sync_performance(chart_manager.sync_logs)

def analyze_sync_performance(sync_logs):
    """Analyze synchronization performance from logs"""
    print(f"\n🔍 SYNC PERFORMANCE ANALYSIS:")
    print("-" * 30)
    
    raw_updates = [log for log in sync_logs if log['type'] == 'raw']
    chart_updates = [log for log in sync_logs if log['type'] == 'chart']
    
    print(f"📊 Raw updates: {len(raw_updates)}")
    print(f"🧠 Chart updates: {len(chart_updates)}")
    
    if len(chart_updates) > 1:
        # Calculate update intervals
        intervals = []
        for i in range(1, len(chart_updates)):
            interval = chart_updates[i]['timestamp'] - chart_updates[i-1]['timestamp']
            intervals.append(interval)
        
        avg_interval = np.mean(intervals)
        update_rate = 1000 / avg_interval if avg_interval > 0 else 0
        
        print(f"⏰ Average update interval: {avg_interval:.1f}ms")
        print(f"🔄 Effective update rate: {update_rate:.1f} Hz")
        print(f"✅ Target rate (10Hz): {'ACHIEVED' if 8 <= update_rate <= 12 else 'MISSED'}")
    
    # Check if sync buffer is working (should have fewer chart updates than raw)
    sync_ratio = len(chart_updates) / max(len(raw_updates), 1)
    print(f"📈 Sync efficiency: {sync_ratio:.2f} (lower is better - means sync is working)")

def test_sync_timing_edge_cases():
    """Test edge cases for sync timing"""
    print(f"\n🧪 TESTING SYNC EDGE CASES")
    print("=" * 40)
    
    decoder = BLEPacketDecoder()
    chart_manager = MockChartManager()
    processor = EOGProcessor(decoder, chart_manager)
    
    test_cases = [
        ("Normal sync", 50, 60),      # 10ms difference
        ("Edge of window", 95, 105),  # 10ms difference at edge
        ("Beyond window", 50, 200),   # 150ms difference (should not sync)
        ("Reverse order", 100, 50),   # AF4 arrives before AF3
        ("Simultaneous", 50, 50),     # Same timestamp
    ]
    
    for case_name, af3_time, af4_time in test_cases:
        print(f"\n🔬 Testing: {case_name}")
        print(f"   AF3 time: {af3_time}ms, AF4 time: {af4_time}ms")
        print(f"   Time diff: {abs(af3_time - af4_time)}ms")
        
        # Generate test data
        af3_data = np.random.normal(8388608, 20000, 100).astype(int)
        af4_data = np.random.normal(8388608, 20000, 100).astype(int)
        
        # Clear previous data
        processor.sync_buffer['af3_data'] = None
        processor.sync_buffer['af4_data'] = None
        
        before_updates = chart_manager.chart_update_count
        
        # Test sync timing
        processor.update_sync_buffer('AF3', af3_data, af3_time)
        processor.update_sync_buffer('AF4', af4_data, af4_time)
        
        after_updates = chart_manager.chart_update_count
        sync_occurred = after_updates > before_updates
        
        expected_sync = abs(af3_time - af4_time) <= 100  # Within 100ms window
        result = "✅ PASS" if sync_occurred == expected_sync else "❌ FAIL"
        
        print(f"   Expected sync: {expected_sync}")
        print(f"   Actual sync: {sync_occurred}")
        print(f"   Result: {result}")

def main():
    """Main test function"""
    print("📊 AF3/AF4 Chart Synchronization Test Suite")
    print("=" * 50)
    
    choice = input("""
Choose test mode:
1. 🔄 Asynchronous Packet Simulation
2. 🧪 Sync Timing Edge Cases
3. 📋 Both Tests

Enter choice (1-3): """).strip()
    
    if choice == "1":
        simulate_asynchronous_packets()
    elif choice == "2":
        test_sync_timing_edge_cases()
    elif choice == "3":
        simulate_asynchronous_packets()
        test_sync_timing_edge_cases()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
