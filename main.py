import tkinter as tk
from ui.app_ui import BLEApp

if __name__ == "__main__":
    root = tk.Tk()
    app = BLEApp(root)
    root.mainloop()