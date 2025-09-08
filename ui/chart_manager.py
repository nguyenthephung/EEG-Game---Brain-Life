import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import numpy as np

class EOGChartManager:
    def __init__(self, root):
        self.root = root
        # Create 3x2 subplot layout: Raw signals + Alpha/Beta bands + Wavelet Scalograms
        self.fig, ((self.ax_raw_left, self.ax_raw_right), 
                   (self.ax_alpha_beta_af3, self.ax_alpha_beta_af4),
                   (self.ax_scalogram_y1, self.ax_scalogram_y2)) = plt.subplots(3, 2, figsize=(14, 12), sharex=True)
        self.canvas = None
        
        # Buffers for EOG data
        self.raw_left_buffer = deque(maxlen=200)
        self.raw_right_buffer = deque(maxlen=200)
        self.eog_left_buffer = deque(maxlen=200)
        self.eog_right_buffer = deque(maxlen=200)
        self.y1_buffer = deque(maxlen=100)  # Y1 = Left - Right (horizontal)
        self.y2_buffer = deque(maxlen=100)  # Y2 = (Left + Right)/2 (vertical)
        
        # 🧠 Alpha/Beta buffers for AF3 and AF4
        self.af3_alpha_buffer = deque(maxlen=100)
        self.af3_beta_buffer = deque(maxlen=100)
        self.af4_alpha_buffer = deque(maxlen=100)
        self.af4_beta_buffer = deque(maxlen=100)
        
        # Scalogram data buffers
        self.scalogram_y1_buffer = None
        self.scalogram_y2_buffer = None
        
        # Plot lines
        self.raw_left_line, = self.ax_raw_left.plot([], [], color="blue", linewidth=1)
        self.raw_right_line, = self.ax_raw_right.plot([], [], color="red", linewidth=1)
        
        # 🔧 Add missing EOG plot lines (for filtered signals)
        self.eog_left_line, = self.ax_raw_left.plot([], [], color="cyan", linewidth=1, alpha=0.7, label="Filtered")
        self.eog_right_line, = self.ax_raw_right.plot([], [], color="magenta", linewidth=1, alpha=0.7, label="Filtered")
        
        # 🧠 Alpha/Beta plot lines
        self.af3_alpha_line, = self.ax_alpha_beta_af3.plot([], [], color="green", linewidth=2, label="Alpha (8-13Hz)")
        self.af3_beta_line, = self.ax_alpha_beta_af3.plot([], [], color="orange", linewidth=2, label="Beta (13-30Hz)")
        self.af4_alpha_line, = self.ax_alpha_beta_af4.plot([], [], color="green", linewidth=2, label="Alpha (8-13Hz)")
        self.af4_beta_line, = self.ax_alpha_beta_af4.plot([], [], color="orange", linewidth=2, label="Beta (13-30Hz)")
        
        # Configure plot styles
        plt.style.use('default')
        self.fig.patch.set_facecolor('white')

    def initialize_charts(self):
        # Setup chart layouts and labels for comprehensive EEG/EOG analysis
        
        # Raw EEG signals (AF3/AF4)
        self.ax_raw_left.set_title("Raw AF3 Signal", fontsize=10, fontweight='bold')
        self.ax_raw_left.set_ylabel("Amplitude (μV)", fontsize=9)
        self.ax_raw_left.grid(True, alpha=0.3)
        self.ax_raw_left.set_ylim(-100, 100)
        
        self.ax_raw_right.set_title("Raw AF4 Signal", fontsize=10, fontweight='bold')
        self.ax_raw_right.set_ylabel("Amplitude (μV)", fontsize=9)
        self.ax_raw_right.grid(True, alpha=0.3)
        self.ax_raw_right.set_ylim(-100, 100)
        
        # 🧠 Alpha/Beta band analysis
        self.ax_alpha_beta_af3.set_title("AF3 Alpha/Beta Bands", fontsize=10, fontweight='bold')
        self.ax_alpha_beta_af3.set_ylabel("Power (μV²)", fontsize=9)
        self.ax_alpha_beta_af3.grid(True, alpha=0.3)
        self.ax_alpha_beta_af3.set_ylim(0, 50)
        self.ax_alpha_beta_af3.legend(loc='upper right', fontsize=8)
        
        self.ax_alpha_beta_af4.set_title("AF4 Alpha/Beta Bands", fontsize=10, fontweight='bold')
        self.ax_alpha_beta_af4.set_ylabel("Power (μV²)", fontsize=9)
        self.ax_alpha_beta_af4.grid(True, alpha=0.3)
        self.ax_alpha_beta_af4.set_ylim(0, 50)
        self.ax_alpha_beta_af4.legend(loc='upper right', fontsize=8)
        
        
        # Wavelet Scalograms (EOG Analysis)
        self.ax_scalogram_y1.set_title("Wavelet Scalogram - Y1 (Horizontal EOG)", fontsize=10, fontweight='bold')
        self.ax_scalogram_y1.set_ylabel("Scale (a)", fontsize=9)
        self.ax_scalogram_y1.set_xlabel("Time (samples)", fontsize=9)
        
        self.ax_scalogram_y2.set_title("Wavelet Scalogram - Y2 (Vertical EOG)", fontsize=10, fontweight='bold')
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

    def update_eog_data(self, left_val, right_val, eog_features=None, scalogram_data=None):
        """
        Update EOG data buffers and plots with real-time wavelet analysis
        """
        try:
            # Add to buffers
            if left_val is not None and right_val is not None:
                self.raw_left_buffer.append(left_val)
                self.raw_right_buffer.append(right_val)
                
                # Basic filtering simulation (would use proper EOG processor in real implementation)
                eog_left = left_val * 0.8  # Simulated filtered signal
                eog_right = right_val * 0.8
                
                self.eog_left_buffer.append(eog_left)
                self.eog_right_buffer.append(eog_right)
                
                # Calculate Y1 and Y2 features
                if eog_features:
                    self.y1_buffer.append(eog_features.get('y1', left_val - right_val))
                    self.y2_buffer.append(eog_features.get('y2', (left_val + right_val) / 2))
                    
                    # 🔧 Extract scalogram data from features if available
                    if 'y1_features' in eog_features and 'y2_features' in eog_features:
                        y1_scalogram = eog_features['y1_features'].get('scalogram')
                        y2_scalogram = eog_features['y2_features'].get('scalogram')
                        
                        if y1_scalogram is not None:
                            self.scalogram_y1_buffer = y1_scalogram
                        if y2_scalogram is not None:
                            self.scalogram_y2_buffer = y2_scalogram
                            
                else:
                    self.y1_buffer.append(left_val - right_val)  # Horizontal movement
                    self.y2_buffer.append((left_val + right_val) / 2)  # Vertical movement
                    
                # Update scalogram data if provided explicitly
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
                self.ax_raw_left.set_xlim(0, max(len(self.eog_left_buffer), 1))
            
            if len(self.eog_right_buffer) > 0:
                x_eog = range(len(self.eog_right_buffer))
                self.eog_right_line.set_data(x_eog, list(self.eog_right_buffer))
                self.ax_raw_right.set_xlim(0, max(len(self.eog_right_buffer), 1))
            
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
    
    # 🧠 Alpha/Beta chart update method
    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        """Update alpha/beta band charts for AF3 and AF4 channels"""
        try:
            # Add data to buffers
            self.af3_alpha_buffer.append(af3_alpha)
            self.af3_beta_buffer.append(af3_beta)
            self.af4_alpha_buffer.append(af4_alpha)
            self.af4_beta_buffer.append(af4_beta)
            
            # Update AF3 alpha/beta plot
            if len(self.af3_alpha_buffer) > 0:
                x_data = range(len(self.af3_alpha_buffer))
                self.af3_alpha_line.set_data(x_data, list(self.af3_alpha_buffer))
                self.af3_beta_line.set_data(x_data, list(self.af3_beta_buffer))
                self.ax_alpha_beta_af3.set_xlim(0, max(len(self.af3_alpha_buffer), 1))
                
                # Auto-scale y-axis based on data range
                all_af3_data = list(self.af3_alpha_buffer) + list(self.af3_beta_buffer)
                if all_af3_data:
                    y_max = max(max(all_af3_data), 10)  # Minimum 10 for visibility
                    self.ax_alpha_beta_af3.set_ylim(0, y_max * 1.1)
            
            # Update AF4 alpha/beta plot
            if len(self.af4_alpha_buffer) > 0:
                x_data = range(len(self.af4_alpha_buffer))
                self.af4_alpha_line.set_data(x_data, list(self.af4_alpha_buffer))
                self.af4_beta_line.set_data(x_data, list(self.af4_beta_buffer))
                self.ax_alpha_beta_af4.set_xlim(0, max(len(self.af4_alpha_buffer), 1))
                
                # Auto-scale y-axis based on data range
                all_af4_data = list(self.af4_alpha_buffer) + list(self.af4_beta_buffer)
                if all_af4_data:
                    y_max = max(max(all_af4_data), 10)  # Minimum 10 for visibility
                    self.ax_alpha_beta_af4.set_ylim(0, y_max * 1.1)
            
            # Update canvas
            if self.canvas:
                self.canvas.draw_idle()
                
            # Print debug info
            print(f"📊 Charts Updated - AF3: α={af3_alpha:.2f}, β={af3_beta:.2f} | AF4: α={af4_alpha:.2f}, β={af4_beta:.2f}")
                
        except Exception as e:
            print(f"❌ Error updating alpha/beta charts: {e}")
    
    def update_raw_signals(self, af3_raw, af4_raw):
        """Update raw signal displays"""
        try:
            # Add to raw signal buffers
            self.raw_left_buffer.append(af3_raw)
            self.raw_right_buffer.append(af4_raw)
            
            # Update raw signal plots
            if len(self.raw_left_buffer) > 0:
                x_data = range(len(self.raw_left_buffer))
                self.raw_left_line.set_data(x_data, list(self.raw_left_buffer))
                self.ax_raw_left.set_xlim(0, max(len(self.raw_left_buffer), 1))
            
            if len(self.raw_right_buffer) > 0:
                x_data = range(len(self.raw_right_buffer))
                self.raw_right_line.set_data(x_data, list(self.raw_right_buffer))
                self.ax_raw_right.set_xlim(0, max(len(self.raw_right_buffer), 1))
            
            # Update canvas
            if self.canvas:
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"❌ Error updating raw signals: {e}")