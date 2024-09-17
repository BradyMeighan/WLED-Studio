# main.py

import customtkinter as ctk
import logging
from src.gui.main_gui import StreamingApp
from src.gui.loading_screen import LoadingScreen  # Added import for LoadingScreen
from src.utils.logger_handler import logger_handler

def main():
    # Configure the root logger with default INFO level
    logging.basicConfig(
        level=logging.INFO,  # Default to INFO; will be toggled to DEBUG if debug mode is enabled
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",  # Fixed format specifier
        handlers=[logger_handler()]
    )

    root = ctk.CTk()
    app = StreamingApp(root)

    # Show loading screen
    loading = LoadingScreen(root, app.populate_devices)

    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
