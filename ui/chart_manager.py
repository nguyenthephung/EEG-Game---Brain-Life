import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import numpy as np

class EOGChartManager:
    def __init__(self, root):
        self.root = root
        # Create 2x3 subplot for comprehensive EOG analysis: Raw signals + Filtered EOG + Wavelet Scalograms
        self.fig, ((self.ax_raw_left, self.ax_raw_right), 
                   (self.ax_eog_left, self.ax_eog_right),
                   (self.ax_scalogram_y1, self.ax_scalogram_y2)) = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
        self.canvas = None
        
        # Buffers for EOG data
        self.raw_left_buffer = deque(maxlen=200)
        self.raw_right_buffer = deque(maxlen=200)
        self.eog_left_buffer = deque(maxlen=200)
        self.eog_right_buffer = deque(maxlen=200)
        self.y1_buffer = deque(maxlen=100)  # Y1 = Left - Right (horizontal)
        self.y2_buffer = deque(maxlen=100)  # Y2 = (Left + Right)/2 (vertical)
        
        # Scalogram data buffers
        self.scalogram_y1_buffer = None
        self.scalogram_y2_buffer = None
        
        # Plot lines
        self.raw_left_line, = self.ax_raw_left.plot([], [], color="blue", linewidth=1)
        self.raw_right_line, = self.ax_raw_right.plot([], [], color="red", linewidth=1)
        self.eog_left_line, = self.ax_eog_left.plot([], [], color="darkblue", linewidth=2)
        self.eog_right_line, = self.ax_eog_right.plot([], [], color="darkred", linewidth=2)
        
        # Configure plot styles
        plt.style.use('default')
        self.fig.patch.set_facecolor('white')

    def initialize_charts(self):
        # Setup chart layouts and labels for comprehensive EOG analysis with wavelet scalograms
        
        # Raw EEG signals (will extract EOG)
        self.ax_raw_left.set_title("Raw AF3 Signal (Left Eye)", fontsize=10, fontweight='bold')
        self.ax_raw_left.set_ylabel("Amplitude (μV)", fontsize=9)
        self.ax_raw_left.grid(True, alpha=0.3)
        self.ax_raw_left.set_ylim(-100, 100)
        
        self.ax_raw_right.set_title("Raw AF4 Signal (Right Eye)", fontsize=10, fontweight='bold')
        self.ax_raw_right.set_ylabel("Amplitude (μV)", fontsize=9)
        self.ax_raw_right.grid(True, alpha=0.3)
        self.ax_raw_right.set_ylim(-100, 100)
        
        # Filtered EOG signals
        self.ax_eog_left.set_title("Filtered EOG - Y1 (Horizontal)", fontsize=10, fontweight='bold')
        self.ax_eog_left.set_ylabel("EOG Amplitude (μV)", fontsize=9)
        self.ax_eog_left.grid(True, alpha=0.3)
        self.ax_eog_left.set_ylim(-50, 50)
        
        self.ax_eog_right.set_title("Filtered EOG - Y2 (Vertical)", fontsize=10, fontweight='bold')
        self.ax_eog_right.set_ylabel("EOG Amplitude (μV)", fontsize=9)
        self.ax_eog_right.grid(True, alpha=0.3)
        self.ax_eog_right.set_ylim(-50, 50)
        
        # Wavelet Scalograms
        self.ax_scalogram_y1.set_title("Wavelet Scalogram - Y1 (CWT with Haar)", fontsize=10, fontweight='bold')
        self.ax_scalogram_y1.set_ylabel("Scale (a)", fontsize=9)
        self.ax_scalogram_y1.set_xlabel("Time (samples)", fontsize=9)
        
        self.ax_scalogram_y2.set_title("Wavelet Scalogram - Y2 (CWT with Haar)", fontsize=10, fontweight='bold')
        self.ax_scalogram_y2.set_ylabel("Scale (a)", fontsize=9)
        self.ax_scalogram_y2.set_xlabel("Time (samples)", fontsize=9)
        
        # Apply tight layout
        plt.tight_layout(pad=2.0)
        
        # Create canvas if needed
        if self.canvas is None:
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Show the plot
        self.canvas.draw()

    def update_eog_data(self, af3_data, af4_data, eog_features=None, scalogram_data=None):
        """Update EOG charts with raw, processed data and wavelet scalograms"""
        try:
            # Add raw data to buffers
            if af3_data is not None:
                self.raw_left_buffer.append(af3_data)
            if af4_data is not None:
                self.raw_right_buffer.append(af4_data)
            
            # Process EOG if both channels have data
            if len(self.raw_left_buffer) > 0 and len(self.raw_right_buffer) > 0:
                # Calculate basic EOG features for visualization
                left_val = list(self.raw_left_buffer)[-1] if self.raw_left_buffer else 0
                right_val = list(self.raw_right_buffer)[-1] if self.raw_right_buffer else 0
                
                # Basic filtering simulation (would use proper EOG processor in real implementation)
                eog_left = left_val * 0.8  # Simulated filtered signal
                eog_right = right_val * 0.8
                
                self.eog_left_buffer.append(eog_left)
                self.eog_right_buffer.append(eog_right)
                
                # Calculate Y1 and Y2 features
                if eog_features:
                    self.y1_buffer.append(eog_features.get('y1', left_val - right_val))
                    self.y2_buffer.append(eog_features.get('y2', (left_val + right_val) / 2))
                else:
                    self.y1_buffer.append(left_val - right_val)  # Horizontal movement
                    self.y2_buffer.append((left_val + right_val) / 2)  # Vertical movement
                    
                # Update scalogram data if provided
                if scalogram_data:
                    self.scalogram_y1_buffer = scalogram_data.get('y1_scalogram')
                    self.scalogram_y2_buffer = scalogram_data.get('y2_scalogram')
            
            # Update plots
            self.update_plots()
            
        except Exception as e:
            print(f"Error updating EOG data: {e}")
    
    def update_plots(self):
        """Update all EOG visualization plots including wavelet scalograms"""
        try:
            # Update raw signal plots
            if len(self.raw_left_buffer) > 0:
                x_raw = range(len(self.raw_left_buffer))
                self.raw_left_line.set_data(x_raw, list(self.raw_left_buffer))
                self.ax_raw_left.set_xlim(0, max(len(self.raw_left_buffer), 1))
            
            if len(self.raw_right_buffer) > 0:
                x_raw = range(len(self.raw_right_buffer))
                self.raw_right_line.set_data(x_raw, list(self.raw_right_buffer))
                self.ax_raw_right.set_xlim(0, max(len(self.raw_right_buffer), 1))
            
            # Update filtered EOG plots
            if len(self.eog_left_buffer) > 0:
                x_eog = range(len(self.eog_left_buffer))
                self.eog_left_line.set_data(x_eog, list(self.eog_left_buffer))
                self.ax_eog_left.set_xlim(0, max(len(self.eog_left_buffer), 1))
            
            if len(self.eog_right_buffer) > 0:
                x_eog = range(len(self.eog_right_buffer))
                self.eog_right_line.set_data(x_eog, list(self.eog_right_buffer))
                self.ax_eog_right.set_xlim(0, max(len(self.eog_right_buffer), 1))
            
            # Update wavelet scalograms
            if self.scalogram_y1_buffer is not None:
                self.ax_scalogram_y1.clear()
                self.ax_scalogram_y1.imshow(self.scalogram_y1_buffer, aspect='auto', cmap='jet', 
                                           origin='lower', interpolation='bilinear')
                self.ax_scalogram_y1.set_title("Wavelet Scalogram - Y1 (CWT with Haar)", fontsize=10, fontweight='bold')
                self.ax_scalogram_y1.set_ylabel("Scale (a)", fontsize=9)
                
            if self.scalogram_y2_buffer is not None:
                self.ax_scalogram_y2.clear()
                self.ax_scalogram_y2.imshow(self.scalogram_y2_buffer, aspect='auto', cmap='jet',
                                           origin='lower', interpolation='bilinear')
                self.ax_scalogram_y2.set_title("Wavelet Scalogram - Y2 (CWT with Haar)", fontsize=10, fontweight='bold')
                self.ax_scalogram_y2.set_ylabel("Scale (a)", fontsize=9)
                self.ax_scalogram_y2.set_xlabel("Time (samples)", fontsize=9)
            
            # Refresh canvas
            if self.canvas:
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"Error updating plots: {e}")
    
    # Legacy method compatibility - redirect to EOG data update
    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        """Legacy compatibility method - converts old alpha/beta calls to EOG data"""
        # Use alpha values as raw EEG data for EOG processing
        self.update_eog_data(af3_alpha, af4_alpha)