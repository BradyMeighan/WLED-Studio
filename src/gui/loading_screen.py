# src/gui/loading_screen.py

import threading
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from tkinter import messagebox
import customtkinter as ctk
from tkinter import ttk
from src.utils.logger_handler import logger_handler

WLED_JSON_ENDPOINT = "/json"
SCAN_TIMEOUT = 0.2  # seconds per request

class LoadingScreen(ctk.CTkToplevel):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.title("Loading...")
        self.geometry("400x200")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.disable_event)

        self.label = ctk.CTkLabel(self, text="Scanning for WLED devices...", font=("Roboto", 16))
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(expand=True, fill='x', padx=50, pady=20)
        self.progress.start(10)

        self.status_label = ctk.CTkLabel(self, text="Please wait...", font=("Roboto", 12))
        self.status_label.pack(pady=10)

        self.on_complete = on_complete

        self.logger = logging.getLogger("LoadingScreen")

        # Start scanning in a separate thread
        threading.Thread(target=self.scan_network, daemon=True).start()

    def disable_event(self):
        pass  # Prevent closing the loading screen

    def scan_network(self):
        self.logger.debug("Starting network scan for WLED devices")
        devices = self.find_wled_devices()
        self.after(0, self.on_complete, devices)
        self.after(0, self.destroy)

    def find_wled_devices(self):
        devices = []
        try:
            # Get the local IP and subnet
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.logger.debug(f"Local IP address detected: {local_ip}")
            ip = ipaddress.ip_address(local_ip)
            network = ipaddress.ip_network(f"{ip}/24", strict=False)

            self.status_label.configure(text="Scanning the network...")

            # Generate all possible IP addresses in the subnet
            all_ips = [str(potential_ip) for potential_ip in network.hosts()]

            # Define a maximum number of threads
            max_threads = 100  # Adjust based on your system's capabilities

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                future_to_ip = {executor.submit(self.scan_ip, ip_str): ip_str for ip_str in all_ips}
                for future in as_completed(future_to_ip):
                    ip_str = future_to_ip[future]
                    try:
                        device = future.result()
                        if device:
                            devices.append(device)
                            self.status_label.configure(text=f"Found device at {device['ip']}")
                            self.logger.info(f"Found WLED device: {device}")
                            executor.shutdown(wait=False)  # Stop further scanning
                            break  # Exit after finding the first device
                    except Exception as e:
                        self.logger.error(f"Error scanning IP {ip_str}: {e}")
                        continue  # Continue scanning other IPs

        except Exception as e:
            self.logger.error(f"Error during network scan: {e}")
            self.status_label.configure(text=f"Error during scan: {e}")

        self.logger.debug(f"Scan completed with devices: {devices}")
        return devices

    def scan_ip(self, ip_str: str):
        try:
            url = f"http://{ip_str}{WLED_JSON_ENDPOINT}"
            response = requests.get(url, timeout=SCAN_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                # Verify if it's a WLED device by checking for specific keys
                if "info" in data and "leds" in data["info"] and "matrix" in data["info"]["leds"]:
                    # Fetch width and height from matrix
                    matrix = data["info"]["leds"]["matrix"]
                    width = matrix.get("w", 0)
                    height = matrix.get("h", 0)
                    device_ip = data["info"].get("ip", ip_str)
                    return {
                        "ip": device_ip,
                        "width": width,
                        "height": height
                    }
        except requests.RequestException:
            pass  # Ignore connection errors
        except ValueError:
            pass  # Ignore JSON decoding errors
        return None
