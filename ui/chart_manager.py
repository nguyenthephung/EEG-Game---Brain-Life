import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import numpy as np

class ChartManager:
    def __init__(self, root):
        self.root = root
        self.fig, ((self.ax_af3_alpha, self.ax_af4_alpha), (self.ax_af3_beta, self.ax_af4_beta)) = plt.subplots(2, 2, figsize=(10, 8), sharex=True)
        self.canvas = None
        self.alpha_buffer = {"af3": deque(maxlen=100), "af4": deque(maxlen=100)}
        self.beta_buffer = {"af3": deque(maxlen=100), "af4": deque(maxlen=100)}
        self.af3_alpha_line, = self.ax_af3_alpha.plot([], [], color="blue")
        self.af4_alpha_line, = self.ax_af4_alpha.plot([], [], color="red")
        self.af3_beta_line, = self.ax_af3_beta.plot([], [], color="blue")
        self.af4_beta_line, = self.ax_af4_beta.plot([], [], color="red")

    def setup_charts(self, main_frame):
        chart_frame = tk.LabelFrame(main_frame, text="EEG Alpha and Beta Charts", font=("Arial", 10))
        chart_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack()

        self.ax_af3_alpha.set_title("AF3 Alpha Amplitude (\(10^{-6}\) V)")
        self.ax_af3_alpha.set_ylabel("Amplitude (\(10^{-6}\) V)")
        self.ax_af4_alpha.set_title("AF4 Alpha Amplitude (\(10^{-6}\) V)")
        self.ax_af4_alpha.set_ylabel("Amplitude (\(10^{-6}\) V)")
        self.ax_af3_beta.set_title("AF3 Beta Amplitude (\(10^{-6}\) V)")
        self.ax_af3_beta.set_ylabel("Amplitude (\(10^{-6}\) V)")
        self.ax_af4_beta.set_title("AF4 Beta Amplitude (\(10^{-6}\) V)")
        self.ax_af4_beta.set_xlabel("Time (samples)")
        self.ax_af4_beta.set_ylabel("Amplitude (\(10^{-6}\) V)")

    def update_chart(self, af3_alpha, af4_alpha, af3_beta, af4_beta):
        self.alpha_buffer["af3"].append(af3_alpha)
        self.alpha_buffer["af4"].append(af4_alpha)
        self.beta_buffer["af3"].append(af3_beta)
        self.beta_buffer["af4"].append(af4_beta)

        self.af3_alpha_line.set_data(range(len(self.alpha_buffer["af3"])), list(self.alpha_buffer["af3"]))
        self.ax_af3_alpha.relim()
        self.ax_af3_alpha.autoscale_view()

        self.af4_alpha_line.set_data(range(len(self.alpha_buffer["af4"])), list(self.alpha_buffer["af4"]))
        self.ax_af4_alpha.relim()
        self.ax_af4_alpha.autoscale_view()

        self.af3_beta_line.set_data(range(len(self.beta_buffer["af3"])), list(self.beta_buffer["af3"]))
        self.ax_af3_beta.relim()
        self.ax_af3_beta.autoscale_view()

        self.af4_beta_line.set_data(range(len(self.beta_buffer["af4"])), list(self.beta_buffer["af4"]))
        self.ax_af4_beta.relim()
        self.ax_af4_beta.autoscale_view()

        self.canvas.draw_idle()