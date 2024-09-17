# src/gui/main_gui.py

# src/gui/main_gui.py

import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
import cv2
import numpy as np
import time
import threading
from PIL import Image, ImageTk, ImageGrab
from typing import List, Optional, Tuple  # Added List here

from src.capture.video_capture import VideoCapture
from src.capture.video_file_capture import VideoFileCapture
from src.capture.image_capture import ImageCapture
from src.capture.gif_capture import GIFCapture
from src.capture.text_animator import TextAnimator
from src.managers.streamer_manager import StreamerManager
from src.gui.loading_screen import LoadingScreen
from src.gui.device_selection import DeviceSelectionWindow
from src.utils.logger_handler import logger_handler
from src.capture.display_capture import DisplayCapture  # Add this import



class StreamingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Video Wall Streamer")
        self.root.geometry("850x1150")  # Set a reasonable default size
        self.root.minsize(800, 600)  # Set a minimum size to prevent extreme shrinking

        # Initialize logger
        self.logger = logging.getLogger("StreamingApp")
        self.logger.debug("Initializing StreamingApp")

        # Initialize variables
        self.source_type = ctk.StringVar(value="camera")
        self.camera_source = ctk.StringVar(value="0")  # For Camera source input
        self.youtube_url = ctk.StringVar()  # For YouTube source input
        self.image_path = ctk.StringVar()
        self.video_path = ctk.StringVar()  # New variable for video files
        self.text_input = ctk.StringVar()
        self.text_color = ctk.StringVar(value="255,255,255")
        self.text_speed = ctk.StringVar(value="50")  # Pixels per second
        self.text_direction = ctk.StringVar(value="left")
        self.host = ctk.StringVar()
        self.port = ctk.IntVar(value=21324)
        self.serial = ctk.StringVar(value="")
        self.baudrate = ctk.IntVar(value=115200)
        self.width = ctk.IntVar(value=0)
        self.height = ctk.IntVar(value=0)
        self.crop = ctk.StringVar(value="0,0,0,0")
        self.scale = ctk.StringVar(value="fill")
        self.interpolation = ctk.StringVar(value="smooth")
        self.gamma = ctk.DoubleVar(value=0.5)
        self.loop = ctk.BooleanVar(value=False)  # Loop variable
        self.debug = ctk.BooleanVar(value=False)
        self.fps = ctk.IntVar(value=15)

        # Text Options Variables
        self.font_path = ctk.StringVar()
        self.font_size = ctk.IntVar(value=48)  # Default font size
        self.font_bold = ctk.BooleanVar(value=False)
        self.font_italic = ctk.BooleanVar(value=False)
        self.bg_color = ctk.StringVar()
        self.opacity = ctk.DoubleVar(value=1.0)
        self.effect = ctk.StringVar(value="None")
        self.alignment = ctk.StringVar(value="left")
        self.shadow = ctk.BooleanVar(value=False)
        self.shadow_color = ctk.StringVar(value="0,0,0")
        self.shadow_offset = ctk.StringVar(value="2,2")

        # Initialize preview image holder
        self.preview_image = None

        # Initialize streamer manager
        self.streamer_manager = None

        # Initialize player
        self.player = None

        # Streaming control
        self.streaming = False
        self.thread = None
        self.stop_event = threading.Event()  # Event to signal the streaming thread to stop

        # Build UI
        self.build_ui()

    def show_source_options(self, selected):
        """
        Displays the source options based on the selected source type.
        """
        # Hide all dynamic options
        for frame in self.source_options.values():
            frame.grid_remove()

        # Show the relevant source options if they exist
        if selected in self.source_options:
            self.source_options[selected].grid()

    def rescan_network(self):
        if self.streaming:
            messagebox.showwarning("Streaming Active", "Cannot rescan network while streaming is active.")
            self.logger.warning("Attempted to rescan network while streaming is active.")
            return

        self.logger.debug("Initiating network rescan.")
        # Show the LoadingScreen for rescan
        loading = LoadingScreen(self.root, self.populate_devices)

    def build_ui(self):
        # Main container frame with grid layout
        container = ctk.CTkFrame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create a scrollable frame for content
        content_scrollable_frame = ctk.CTkScrollableFrame(container)
        content_scrollable_frame.grid(row=0, column=0, sticky="nsew")
        content_scrollable_frame.grid_rowconfigure(0, weight=1)
        content_scrollable_frame.grid_columnconfigure(0, weight=1)

        # Content Frame Layout within the scrollable frame
        # Source Selection Section
        source_frame = ctk.CTkFrame(content_scrollable_frame, corner_radius=10)
        source_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        source_frame.grid_columnconfigure(0, weight=1)

        # Source Selection Label
        source_label = ctk.CTkLabel(source_frame, text="Source Selection", font=("Roboto", 16))
        source_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(10, 5), padx=10)

        # Radio Buttons for Source Selection
        sources = [
            ("Camera", "camera"),
            ("YouTube", "youtube"),  # Added YouTube option
            ("Display", "display"),
            ("Image / Gif", "image"),
            ("Video File", "video"),  # New Video File option
            ("Text", "text")
        ]

        sources_frame = ctk.CTkFrame(source_frame)
        sources_frame.grid(row=1, column=0, sticky="w", pady=5, padx=10)
        sources_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        for idx, (text, mode) in enumerate(sources):
            rb = ctk.CTkRadioButton(
                sources_frame,
                text=text,
                variable=self.source_type,
                value=mode,
                command=self.on_source_change
            )
            rb.grid(row=0, column=idx, padx=5, pady=5, sticky="w")

        # Dynamic Source Options
        dynamic_frame = ctk.CTkFrame(content_scrollable_frame)
        dynamic_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        dynamic_frame.grid_columnconfigure(0, weight=1)

        self.source_options = {}

        # Image Options
        self.source_options["image"] = self.create_image_options(dynamic_frame)

        # Video File Options
        self.source_options["video"] = self.create_video_options(dynamic_frame)  # New video options

        # Text Options
        self.source_options["text"] = self.create_text_options(dynamic_frame)

        # Camera Options
        self.source_options["camera"] = self.create_camera_options(dynamic_frame)

        # YouTube Options (New)
        self.source_options["youtube"] = self.create_youtube_options(dynamic_frame)

        # Initially show camera options
        self.show_source_options("camera")

        # Live Preview Section
        preview_frame = ctk.CTkFrame(content_scrollable_frame, corner_radius=10)
        preview_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        preview_frame.grid_columnconfigure(0, weight=1)

        # Live Preview Label
        preview_label = ctk.CTkLabel(preview_frame, text="Live Preview", font=("Roboto", 16))
        preview_label.grid(row=0, column=0, sticky="w", pady=(10, 5), padx=10)

        # Preview Image Label
        self.preview = ctk.CTkLabel(preview_frame, text="", width=400, height=300)
        self.preview.grid(row=1, column=0, pady=10, padx=10, sticky="n")

        # Streamer Settings Section
        streamer_frame = ctk.CTkFrame(content_scrollable_frame, corner_radius=10)
        streamer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        streamer_frame.grid_columnconfigure(1, weight=1)

        # Streamer Settings Label
        streamer_label = ctk.CTkLabel(streamer_frame, text="Streamer Settings", font=("Roboto", 16))
        streamer_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(10, 5), padx=10)

        # Define labels and entries in a grid for cleaner code
        settings = [
            ("Host:", self.host),
            ("Port:", self.port),
            ("Width:", self.width),
            ("Height:", self.height),
            ("Crop (L,T,R,B):", self.crop),
            ("Scale:", self.scale),
            ("Interpolation:", self.interpolation),
            ("Gamma:", self.gamma),
            ("FPS:", self.fps),
        ]

        for i, (label_text, var) in enumerate(settings, start=1):
            label = ctk.CTkLabel(streamer_frame, text=label_text)
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            if label_text in ["Scale:", "Interpolation:"]:
                if label_text == "Scale:":
                    options = ["stretch", "fill", "fit", "crop"]
                else:
                    options = ["hard", "smooth"]
                combobox = ctk.CTkOptionMenu(
                    streamer_frame, 
                    variable=var, 
                    values=options
                )
                combobox.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            else:
                entry = ctk.CTkEntry(streamer_frame, textvariable=var)
                entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5)

            # Add specific buttons for certain fields
            if label_text == "Crop (L,T,R,B):":
                capture_button = ctk.CTkButton(
                    streamer_frame, 
                    text="Capture Crop", 
                    command=self.capture_crop_area
                )
                capture_button.grid(row=i, column=2, sticky="w", padx=5, pady=5)
            elif label_text == "Host:":
                rescan_button = ctk.CTkButton(
                    streamer_frame, 
                    text="Rescan Network", 
                    command=self.rescan_network
                )
                rescan_button.grid(row=i, column=2, sticky="w", padx=5, pady=5)

        # Streamer Settings Frame Configuration
        for i in range(len(settings) + 1):
            streamer_frame.grid_rowconfigure(i, weight=0)
        streamer_frame.grid_columnconfigure(1, weight=1)

        # Add a status label at the bottom or any preferred location
        self.status_label = ctk.CTkLabel(self.root, text="Ready", anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # Serial Settings Section
        serial_frame = ctk.CTkFrame(content_scrollable_frame, corner_radius=10)
        serial_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        serial_frame.grid_columnconfigure(1, weight=1)

        # Serial Settings Label
        serial_label = ctk.CTkLabel(serial_frame, text="Serial Settings", font=("Roboto", 16))
        serial_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=10)

        serial_settings = [
            ("Serial Port:", self.serial),
            ("Baud Rate:", self.baudrate),
        ]

        for i, (label_text, var) in enumerate(serial_settings, start=1):
            label = ctk.CTkLabel(serial_frame, text=label_text)
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ctk.CTkEntry(serial_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5)

        # Configure row and column weights in serial_frame
        for i in range(len(serial_settings) + 1):
            serial_frame.grid_rowconfigure(i, weight=0)
        serial_frame.grid_columnconfigure(1, weight=1)

        # Bottom Frame Layout (Control Buttons and Checkboxes)
        # This frame remains fixed at the bottom
        bottom_frame = ctk.CTkFrame(container)
        bottom_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.grid_columnconfigure((0, 1, 2), weight=1)

        control_frame = ctk.CTkFrame(bottom_frame)
        control_frame.pack(fill="x", pady=10)

        # Control Buttons
        self.start_button = ctk.CTkButton(
            control_frame, 
            text="Start Streaming", 
            command=self.start_streaming, 
            fg_color="green"
        )
        self.start_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.stop_button = ctk.CTkButton(
            control_frame, 
            text="Stop Streaming", 
            command=self.stop_streaming, 
            fg_color="red", 
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.quit_button = ctk.CTkButton(
            control_frame, 
            text="Quit", 
            command=self.on_closing
        )
        self.quit_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Debug and Loop Mode Checkboxes
        checkbox_frame = ctk.CTkFrame(bottom_frame)
        checkbox_frame.pack(fill="x", pady=(0, 10))
        checkbox_frame.grid_columnconfigure((0, 1), weight=1)

        debug_checkbox = ctk.CTkCheckBox(
            checkbox_frame, 
            text="Enable Debug Mode", 
            variable=self.debug, 
            command=self.toggle_debug_mode
        )
        debug_checkbox.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        loop_checkbox = ctk.CTkCheckBox(
            checkbox_frame, 
            text="Loop Source", 
            variable=self.loop
        )
        loop_checkbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Ensure all columns expand equally in the control_frame
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)

    def create_image_options(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")

        image_label = ctk.CTkLabel(frame, text="Image Path:")
        image_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        image_entry = ctk.CTkEntry(frame, textvariable=self.image_path, width=250)
        image_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        browse_button = ctk.CTkButton(frame, text="Browse", command=self.browse_image)
        browse_button.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        return frame

    def create_video_options(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")

        video_label = ctk.CTkLabel(frame, text="Video Path:")
        video_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        video_entry = ctk.CTkEntry(frame, textvariable=self.video_path, width=250)
        video_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        browse_button = ctk.CTkButton(frame, text="Browse", command=self.browse_video)
        browse_button.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        return frame

    def create_text_options(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")

        # Existing Text Input
        text_label = ctk.CTkLabel(frame, text="Text:")
        text_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        text_entry = ctk.CTkEntry(frame, textvariable=self.text_input, width=250)
        text_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Text Color
        color_label = ctk.CTkLabel(frame, text="Text Color (R,G,B):")
        color_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        color_entry = ctk.CTkEntry(frame, textvariable=self.text_color, width=250)
        color_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Text Speed
        speed_label = ctk.CTkLabel(frame, text="Text Speed (pixels/sec):")
        speed_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        speed_entry = ctk.CTkEntry(frame, textvariable=self.text_speed, width=250)
        speed_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Text Direction
        direction_label = ctk.CTkLabel(frame, text="Text Direction:")
        direction_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
        direction_combobox = ctk.CTkOptionMenu(
            frame, 
            variable=self.text_direction, 
            values=["left", "right", "up", "down"]
        )
        direction_combobox.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # New: Font Selection
        font_label = ctk.CTkLabel(frame, text="Font:")
        font_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
        font_entry = ctk.CTkEntry(frame, textvariable=self.font_path, width=250)
        font_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        font_browse_button = ctk.CTkButton(frame, text="Browse", command=self.browse_font)
        font_browse_button.grid(row=4, column=2, sticky="w", padx=5, pady=5)

        # New: Font Size
        font_size_label = ctk.CTkLabel(frame, text="Font Size:")
        font_size_label.grid(row=5, column=0, sticky="e", padx=5, pady=5)
        font_size_entry = ctk.CTkEntry(frame, textvariable=self.font_size, width=250)
        font_size_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        # New: Font Style
        font_style_label = ctk.CTkLabel(frame, text="Font Style:")
        font_style_label.grid(row=6, column=0, sticky="e", padx=5, pady=5)
        font_style_frame = ctk.CTkFrame(frame)
        font_style_frame.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        font_bold_checkbox = ctk.CTkCheckBox(font_style_frame, text="Bold", variable=self.font_bold)
        font_bold_checkbox.pack(side="left", padx=5)
        font_italic_checkbox = ctk.CTkCheckBox(font_style_frame, text="Italic", variable=self.font_italic)
        font_italic_checkbox.pack(side="left", padx=5)

        # New: Background Color
        bg_color_label = ctk.CTkLabel(frame, text="Background Color (R,G,B):")
        bg_color_label.grid(row=7, column=0, sticky="e", padx=5, pady=5)
        bg_color_entry = ctk.CTkEntry(frame, textvariable=self.bg_color, width=250)
        bg_color_entry.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        # New: Opacity
        opacity_label = ctk.CTkLabel(frame, text="Opacity (0.0 - 1.0):")
        opacity_label.grid(row=8, column=0, sticky="e", padx=5, pady=5)
        opacity_slider = ctk.CTkSlider(frame, from_=0.0, to=1.0, variable=self.opacity)
        opacity_slider.grid(row=8, column=1, sticky="w", padx=5, pady=5)

        # New: Effects
        effect_label = ctk.CTkLabel(frame, text="Effect:")
        effect_label.grid(row=9, column=0, sticky="e", padx=5, pady=5)
        effect_combobox = ctk.CTkOptionMenu(
            frame,
            variable=self.effect,
            values=["None", "Fade", "Blink", "Color Cycle"]
        )
        effect_combobox.grid(row=9, column=1, sticky="w", padx=5, pady=5)

        # New: Alignment
        alignment_label = ctk.CTkLabel(frame, text="Alignment:")
        alignment_label.grid(row=10, column=0, sticky="e", padx=5, pady=5)
        alignment_combobox = ctk.CTkOptionMenu(
            frame,
            variable=self.alignment,
            values=["left", "center", "right"]
        )
        alignment_combobox.grid(row=10, column=1, sticky="w", padx=5, pady=5)

        # New: Shadow
        shadow_label = ctk.CTkLabel(frame, text="Shadow:")
        shadow_label.grid(row=11, column=0, sticky="e", padx=5, pady=5)
        shadow_checkbox = ctk.CTkCheckBox(frame, text="Enable Shadow", variable=self.shadow)
        shadow_checkbox.grid(row=11, column=1, sticky="w", padx=5, pady=5)

        # New: Shadow Color and Offset
        shadow_color_label = ctk.CTkLabel(frame, text="Shadow Color (R,G,B):")
        shadow_color_label.grid(row=12, column=0, sticky="e", padx=5, pady=5)
        shadow_color_entry = ctk.CTkEntry(frame, textvariable=self.shadow_color, width=250)
        shadow_color_entry.grid(row=12, column=1, sticky="w", padx=5, pady=5)

        shadow_offset_label = ctk.CTkLabel(frame, text="Shadow Offset (X,Y):")
        shadow_offset_label.grid(row=13, column=0, sticky="e", padx=5, pady=5)
        shadow_offset_entry = ctk.CTkEntry(frame, textvariable=self.shadow_offset, width=250)
        shadow_offset_entry.grid(row=13, column=1, sticky="w", padx=5, pady=5)

        return frame

    def browse_font(self):
        file_path = filedialog.askopenfilename(
            title="Select Font File",
            filetypes=[("TrueType Font", "*.ttf"), ("OpenType Font", "*.otf")]
        )
        if file_path:
            self.font_path.set(file_path)

    def create_camera_options(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")

        source_label = ctk.CTkLabel(frame, text="Camera Source (index):")
        source_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        source_entry = ctk.CTkEntry(frame, textvariable=self.camera_source, width=250)
        source_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        return frame

    def create_youtube_options(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")

        url_label = ctk.CTkLabel(frame, text="YouTube URL:")
        url_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        url_entry = ctk.CTkEntry(frame, textvariable=self.youtube_url, width=250)
        url_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Optional: Implement a button to validate URL
        validate_button = ctk.CTkButton(
            frame, 
            text="Validate", 
            command=self.validate_youtube_url
        )
        validate_button.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        return frame

    def on_source_change(self):
        selected = self.source_type.get()
        self.show_source_options(selected)

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image or GIF",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            self.image_path.set(file_path)

    def browse_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")]
        )
        if file_path:
            self.video_path.set(file_path)

    def validate_youtube_url(self):
        url = self.youtube_url.get()
        if "youtube.com/watch?v=" in url or "youtu.be/" in url:
            messagebox.showinfo("Valid URL", "YouTube URL is valid.")
        else:
            messagebox.showerror("Invalid URL", "Please enter a valid YouTube URL.")

    def parse_crop(self, crop_str: str) -> List[int]:
        try:
            parts = [int(x.strip()) for x in crop_str.split(",")]
            if len(parts) == 1:
                return parts * 4
            elif len(parts) == 2:
                return parts * 2
            elif len(parts) == 4:
                return parts
            else:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid Crop", "Crop must be in format L,T,R,B with integer values.")
            return [0, 0, 0, 0]

    def toggle_debug_mode(self):
        if self.debug.get():
            # Set logger to DEBUG level
            logging.getLogger().setLevel(logging.DEBUG)
            self.logger.info("Debug mode enabled.")
        else:
            # Set logger to INFO level
            logging.getLogger().setLevel(logging.INFO)
            self.logger.info("Debug mode disabled.")
    
    def start_streaming(self):
        if self.streaming:
            self.logger.warning("Streaming already in progress")
            messagebox.showwarning("Streaming Active", "A streaming session is already active.")
            return

        # Validate and prepare settings
        source_type = self.source_type.get()
        player = None
        frame_rate = self.fps.get()

        if frame_rate <= 0:
            messagebox.showerror("Error", "Invalid FPS. Please enter a positive integer.")
            self.logger.error("Invalid FPS value")
            return

        self.logger.debug(f"Starting streaming with source_type={source_type}, frame_rate={frame_rate}")

        try:
            if source_type == "image":
                image_path = self.image_path.get()
                if not image_path:
                    raise ValueError("Image path is not specified.")

                # Detect if the selected file is a GIF
                if image_path.lower().endswith('.gif'):
                    self.logger.debug(f"Selected file is a GIF: {image_path}")
                    player = GIFCapture(gif_path=image_path, fps=frame_rate)
                else:
                    self.logger.debug(f"Selected file is a static image: {image_path}")
                    player = ImageCapture(image_path=image_path)

            elif source_type == "video":
                video_path = self.video_path.get()
                if not video_path:
                    raise ValueError("Video path is not specified.")
                player = VideoFileCapture(video_path=video_path, loop=self.loop.get())

            elif source_type == "display":
                player = DisplayCapture()

            elif source_type == "camera":
                camera_index = int(self.camera_source.get())
                player = VideoCapture(source=camera_index, loop=self.loop.get())

            elif source_type == "youtube":
                youtube_url = self.youtube_url.get()
                if not youtube_url:
                    raise ValueError("YouTube URL is not specified.")
                player = VideoCapture(source=youtube_url, loop=self.loop.get())

            elif source_type == "text":
                text = self.text_input.get()
                if not text:
                    raise ValueError("Text input is empty.")

                # Parse text color
                color_str = self.text_color.get()
                try:
                    color = tuple(map(int, color_str.split(',')))
                    if len(color) != 3:
                        raise ValueError
                except:
                    raise ValueError("Text color must be in format R,G,B with integer values.")

                # Parse shadow offset
                shadow_offset = self.parse_shadow_offset(self.shadow_offset.get())

                # Parse background color
                bg_color_str = self.bg_color.get()
                try:
                    bg_color = tuple(map(int, bg_color_str.split(','))) if bg_color_str else None
                    if bg_color and len(bg_color) != 3:
                        raise ValueError
                except:
                    raise ValueError("Background color must be in format R,G,B with integer values.")

                # Parse text speed
                speed = float(self.text_speed.get())
                direction = self.text_direction.get()
                alignment = self.alignment.get()
                opacity = float(self.opacity.get())
                effect = self.effect.get().lower() if self.effect.get() != "None" else None
                font_path = self.font_path.get() or None
                font_size = int(self.font_size.get()) if self.font_size.get() else None
                font_bold = self.font_bold.get()
                font_italic = self.font_italic.get()

                # Initialize TextAnimator with enhanced options
                player = TextAnimator(
                    text=text,
                    width=self.width.get(),
                    height=self.height.get(),
                    speed=speed,
                    direction=direction,
                    color=color,
                    fps=frame_rate,
                    font_path=font_path,
                    font_size=font_size,
                    font_bold=font_bold,
                    font_italic=font_italic,
                    bg_color=bg_color,
                    opacity=opacity,
                    effect=effect,
                    alignment=alignment,
                    shadow=self.shadow.get(),
                    shadow_color=self.parse_color(self.shadow_color.get()),
                    shadow_offset=shadow_offset,
                )

            else:
                messagebox.showerror("Error", "Unknown source type selected.")
                self.logger.error(f"Unknown source type selected: {source_type}")
                return

            # Assign player to self.player for proper stopping
            self.player = player

            # Initialize streamer manager with GUI settings
            stream_configs = self.build_streamer_configs()

            if not stream_configs:
                messagebox.showerror("Error", "No streamer configurations available.")
                self.logger.error("No streamer configurations found")
                return

            self.streamer_manager = StreamerManager(stream_configs, logger=self.logger)

            # Start streaming thread
            self.streaming = True
            self.stop_event.clear()  # Ensure the stop_event is cleared
            self.thread = threading.Thread(target=self.streaming_loop, args=(player, frame_rate), daemon=True)
            self.thread.start()

            self.logger.info("Streaming started successfully")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        except Exception as e:
            self.logger.exception("Error starting streaming")
            messagebox.showerror("Error", f"An error occurred: {e}")
            return


    def parse_shadow_offset(self, offset_str: str) -> Tuple[int, int]:
        try:
            parts = [int(x.strip()) for x in offset_str.split(",")]
            if len(parts) == 1:
                return (parts[0], parts[0])
            elif len(parts) == 2:
                return (parts[0], parts[1])
            else:
                raise ValueError
        except:
            messagebox.showerror("Invalid Shadow Offset", "Shadow offset must be in format X,Y with integer values.")
            return (2, 2)  # Default shadow offset

    def parse_color(self, color_str: str) -> Tuple[int, int, int]:
        try:
            parts = [int(x.strip()) for x in color_str.split(",")]
            if len(parts) != 3:
                raise ValueError
            return tuple(parts)
        except:
            messagebox.showerror("Invalid Color", "Color must be in format R,G,B with integer values.")
            return (0, 0, 0)  # Default color

    def build_streamer_configs(self):
        # Function implementation
        # Collect streamer settings from GUI variables
        config = {
            "host": self.host.get(),
            "port": self.port.get(),
            "serialport": self.serial.get(),
            "baudrate": self.baudrate.get(),
            "width": self.width.get(),
            "height": self.height.get(),
            "crop": self.parse_crop(self.crop.get()),
            "scale": self.scale.get(),
            "interpolation": self.interpolation.get(),
            "gamma": self.gamma.get(),
            # "loop": self.loop.get(),       # Exclude 'loop'
            # "fps": self.fps.get(),         # Exclude 'fps' if not supported by streamer
        }

        # Determine streamer type based on serial port
        stream_configs = []
        if config["serialport"]:
            streamer_config = {
                "serialport": config["serialport"],
                "baudrate": config["baudrate"],
                "width": config["width"],
                "height": config["height"],
                "crop": config["crop"],
                "scale": config["scale"],
                "interpolation": config["interpolation"],
                "gamma": config["gamma"],
            }
            stream_configs.append(streamer_config)
            self.logger.debug(f"Added SerialWLEDStreamer config: {streamer_config}")
        else:
            # Assume UDP streamer
            streamer_config = {
                "host": config["host"],
                "port": config["port"],
                "width": config["width"],
                "height": config["height"],
                "crop": config["crop"],
                "scale": config["scale"],
                "interpolation": config["interpolation"],
                "gamma": config["gamma"],
            }
            stream_configs.append(streamer_config)
            self.logger.debug(f"Added UDPWLEDStreamer config: {streamer_config}")

        return stream_configs

    def get_text_animator_args(self):
        args = argparse.Namespace()
        args.text = self.text_input.get()
        args.text_color = self.text_color.get()
        args.text_speed = self.text_speed.get()
        args.text_direction = self.text_direction.get()
        args.host = self.host.get()
        args.port = self.port.get()
        args.serial = self.serial.get()
        args.baudrate = self.baudrate.get()
        args.width = self.width.get()
        args.height = self.height.get()
        args.crop = self.parse_crop(self.crop.get())
        args.scale = self.scale.get()
        args.interpolation = self.interpolation.get()
        args.gamma = self.gamma.get()
        args.loop = self.loop.get()
        args.debug = self.debug.get()
        args.fps = self.fps.get()
        return args

    def streaming_loop(self, player, frame_rate):
        self.logger.debug("Streaming loop started")
        frame_interval = 1.0 / frame_rate

        if player is None:
            self.logger.error("Player is not initialized.")
            self.root.after(0, lambda: messagebox.showerror("Streaming Error", "Player is not initialized."))
            return

        try:
            while not self.stop_event.is_set():
                start_time = time.perf_counter()

                # Read and process frame
                frame = player.read()
                if frame is None:
                    self.logger.warning("Received None frame, stopping streaming")
                    break

                # Update live preview
                self.update_preview(frame)

                # Process and send frame
                self.streamer_manager.process_and_send_frame(frame, debug=False)  # Debug handled via logger

                # Measure elapsed time
                elapsed_time = time.perf_counter() - start_time
                time_to_wait = frame_interval - elapsed_time
                if time_to_wait > 0:
                    time.sleep(time_to_wait)
                else:
                    self.logger.debug(f"Processing took longer than frame interval: {elapsed_time:.6f} seconds")

                # Log total time per frame
                total_time = time.perf_counter() - start_time
                self.logger.debug(f"Total time per frame: {total_time:.6f} seconds")

        except Exception as e:
            self.logger.exception("Error in streaming loop")
            # Capture 'e' as a default parameter to avoid scoping issues
            self.root.after(0, lambda e=e: messagebox.showerror("Streaming Error", f"An error occurred during streaming: {e}"))
        finally:
            self.logger.debug("Streaming loop terminating")
            # Perform cleanup
            if self.player:
                self.player.stop()
                self.player = None  # Release the player reference
            if self.streamer_manager:
                self.streamer_manager.close_all()
            cv2.destroyAllWindows()
            self.logger.debug("OpenCV windows destroyed")
            # Update streaming state and buttons
            self.streaming = False
            self.thread = None  # Release the thread reference
            self.root.after(0, self.update_buttons_after_stop)

    def update_buttons_after_stop(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.logger.info("Streaming stopped")

    def stop_streaming(self):
        if not self.streaming:
            self.logger.warning("Stop Streaming called, but streaming was not active")
            return

        self.logger.debug("Stopping streaming")
        self.stop_event.set()  # Signal the streaming thread to stop
        self.streaming = False  # Update the streaming flag
        self.logger.debug("Streaming flag set to False")

        # Start a non-blocking wait for the thread to join
        self.check_thread_stop()

    def check_thread_stop(self):
        if self.thread and self.thread.is_alive():
            self.logger.debug("Waiting for streaming thread to terminate")
            # Schedule another check in 100ms
            self.root.after(100, self.check_thread_stop)
        else:
            if self.streaming:
                self.logger.debug("Streaming thread has stopped")
                self.streaming = False
                self.thread = None  # Ensure thread reference is cleared
                self.update_buttons_after_stop()
                self.logger.info("Streaming stopped")

    def on_closing(self):
        self.logger.debug("Application closing initiated")
        if self.streaming:
            self.logger.debug("Application closing while streaming is active")
            self.stop_streaming()
        self.root.destroy()


    def populate_devices(self, devices: List[dict]):
        if not devices:
            # Update the status label instead of showing a dialog box
            self.status_label.configure(text="No WLED devices found. Please enter the IP address manually.")
            self.logger.info("No WLED devices found during network scan")
            return

        elif len(devices) == 1:
            device = devices[0]
            self.logger.info(f"Auto-populating with single found device: {device}")
            self.host.set(device["ip"])
            if device["width"]:
                self.width.set(device["width"])
            if device["height"]:
                self.height.set(device["height"])
            self.status_label.configure(text=f"Connected to device at {device['ip']}")

        else:
            # Multiple devices found, let user select
            self.logger.info(f"Multiple WLED devices found: {devices}")
            selection_window = DeviceSelectionWindow(self.root, devices, self.apply_device_selection)
            self.root.wait_window(selection_window)
            if self.host.get():
                self.status_label.configure(text=f"Connected to device at {self.host.get()}")


    def apply_device_selection(self, device: dict):
        self.host.set(device["ip"])
        if device["width"]:
            self.width.set(device["width"])
        if device["height"]:
            self.height.set(device["height"])
        self.logger.info(f"Device selected: {device}")

    def capture_crop_area(self):
        """
        Captures a screenshot, allows the user to select a crop area, and updates the crop coordinates.
        """
        self.logger.debug("Starting crop capture tool")

        try:
            # Capture the screenshot
            screenshot = ImageGrab.grab()
            screen_width, screen_height = screenshot.size
            self.logger.debug(f"Screenshot captured: width={screen_width}, height={screen_height}")

            # Convert the screenshot to a format compatible with OpenCV
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Display the screenshot and let the user select ROI
            self.logger.debug("Displaying screenshot for ROI selection")
            roi = cv2.selectROI("Select Crop Area and press Enter or Space", screenshot_cv, fromCenter=False, showCrosshair=True)
            cv2.destroyWindow("Select Crop Area and press Enter or Space")

            x, y, w, h = roi
            self.logger.debug(f"ROI selected: x={x}, y={y}, w={w}, h={h}")

            if w and h:
                # Calculate margins: left, top, right, bottom
                left = x
                top = y
                right = screen_width - (x + w)
                bottom = screen_height - (y + h)

                # Update the crop variable
                self.crop.set(f"{left},{top},{right},{bottom}")
                self.logger.info(f"Crop coordinates set to: L={left}, T={top}, R={right}, B={bottom}")

                # Inform the user
                messagebox.showinfo("Crop Captured", f"Crop area set to:\nLeft: {left}\nTop: {top}\nRight: {right}\nBottom: {bottom}")
            else:
                self.logger.warning("No ROI selected")
                messagebox.showwarning("No Crop Selected", "No crop area was selected.")

        except Exception as e:
            self.logger.exception("Failed to capture crop area")
            messagebox.showerror("Error", f"Failed to capture crop area: {e}")

    def update_preview(self, frame):
        """
        Updates the live preview area with the given frame in a thread-safe manner.
        """
        def update_image():
            try:
                # Convert the frame from BGR (OpenCV) to RGB (PIL)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # Resize the image to fit the preview area if necessary
                pil_image = pil_image.resize((400, 300), Image.Resampling.LANCZOS)

                # Convert to ImageTk
                imgtk = ImageTk.PhotoImage(image=pil_image)

                # Update the preview label
                self.preview.configure(image=imgtk)
                self.preview.image = imgtk  # Keep a reference to prevent garbage collection

            except Exception as e:
                self.logger.exception("Failed to update live preview")

        # Schedule the update in the main thread
        self.root.after(0, update_image)
