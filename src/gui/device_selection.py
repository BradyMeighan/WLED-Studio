# src/gui/device_selection.py

import customtkinter as ctk
from tkinter import messagebox
import logging
from src.utils.logger_handler import logger_handler

class DeviceSelectionWindow(ctk.CTkToplevel):
    def __init__(self, parent, devices: list, callback):
        super().__init__(parent)
        self.title("Select WLED Device")
        self.geometry("500x350")
        self.resizable(False, False)
        self.callback = callback

        self.logger = logging.getLogger("DeviceSelectionWindow")
        self.logger.debug("Initializing DeviceSelectionWindow")

        label = ctk.CTkLabel(
            self,
            text="Multiple WLED devices found. Please select one:",
            font=("Roboto", 14)
        )
        label.pack(pady=10)

        # Creating a Listbox to show devices
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical")
        scrollbar.pack(side="right", fill="y")

        self.listbox = ctk.CTkListbox(list_frame, yscrollcommand=scrollbar.set, selectmode="single")
        for d in devices:
            display_text = f"IP: {d['ip']} | Width: {d['width']} | Height: {d['height']}"
            self.listbox.insert(ctk.END, display_text)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.listbox.yview)

        select_button = ctk.CTkButton(self, text="Select", command=self.select_device)
        select_button.pack(pady=20)

    def select_device(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Selection Error", "Please select a device from the list.")
            self.logger.error("No device selected in DeviceSelectionWindow")
            return
        selected_index = selected_indices[0]
        selected_text = self.listbox.get(selected_index)
        # Extract IP, width, and height from the selected text
        try:
            parts = selected_text.split("|")
            ip_part = parts[0].strip().split(": ")[1]
            width_part = parts[1].strip().split(": ")[1]
            height_part = parts[2].strip().split(": ")[1]
            device = {
                "ip": ip_part,
                "width": int(width_part),
                "height": int(height_part)
            }
            self.logger.debug(f"Device selected: {device}")
            self.callback(device)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Parsing Error", f"Failed to parse selected device information: {e}")
            self.logger.exception("Failed to parse device information")
