# src/capture/text_animator.py

import cv2
import numpy as np
import time
import logging
from PIL import Image, ImageDraw, ImageTk, ImageFont
from typing import Optional, Tuple
from ..utils.logger_handler import logger_handler

class TextAnimator:
    def __init__(
        self,
        text: str,
        width: int,
        height: int,
        speed: float,
        direction: str,
        color: Tuple[int, int, int],
        fps: int,
        font_path: Optional[str] = None,
        font_size: Optional[int] = None,
        font_bold: bool = False,
        font_italic: bool = False,
        bg_color: Optional[Tuple[int, int, int]] = None,
        opacity: float = 1.0,
        effect: Optional[str] = None,
        alignment: str = "left",
        shadow: bool = False,
        shadow_color: Tuple[int, int, int] = (0, 0, 0),
        shadow_offset: Tuple[int, int] = (2, 2),
    ):
        """
        Enhanced TextAnimator with additional customization options and effects.

        :param text: The text to animate.
        :param width: Width of the output frame.
        :param height: Height of the output frame.
        :param speed: Speed of the text in pixels per second.
        :param direction: Direction of scrolling ('left', 'right', 'up', 'down').
        :param color: Text color as a tuple (B, G, R).
        :param fps: Frames per second.
        :param font_path: Path to the TrueType font file. If None, default font is used.
        :param font_size: Size of the font. If None, calculated based on height.
        :param font_bold: Whether the font is bold.
        :param font_italic: Whether the font is italic.
        :param bg_color: Background color as a tuple (B, G, R). If None, transparent.
        :param opacity: Opacity of the text (0.0 to 1.0).
        :param effect: Additional text effect ('fade', 'blink', 'color_cycle', etc.).
        :param alignment: Text alignment ('left', 'center', 'right').
        :param shadow: Whether to render a shadow behind the text.
        :param shadow_color: Color of the shadow.
        :param shadow_offset: Offset of the shadow (x, y).
        """
        self.logger = logging.getLogger("TextAnimator")
        self.text = text
        self.width = width
        self.height = height
        self.speed = speed  # Pixels per second
        self.direction = direction.lower()
        self.color = color  # (B, G, R)
        self.fps = fps
        self.font_path = font_path
        self.font_size = font_size or int(height * 0.5)
        self.font_bold = font_bold
        self.font_italic = font_italic
        self.bg_color = bg_color
        self.opacity = opacity
        self.effect = effect
        self.alignment = alignment.lower()
        self.shadow = shadow
        self.shadow_color = shadow_color
        self.shadow_offset = shadow_offset

        # Initialize font using PIL
        try:
            if self.font_path:
                self.font = ImageFont.truetype(self.font_path, self.font_size)
            else:
                self.font = ImageFont.load_default()
        except Exception as e:
            self.logger.error(f"Failed to load font: {e}")
            self.font = ImageFont.load_default()

        # Initialize text image
        self.logger.debug("Initializing TextAnimator")
        self.text_image = self.create_text_image()

        # Initialize scrolling positions based on direction
        self.initialize_scrolling()

        # Initialize effect parameters
        self.effect_params = self.init_effect_params()

        self.last_frame_time = time.perf_counter()


    def create_text_image(self) -> Image.Image:
        """
        Creates an image of the text with optional effects.
        """
        # Calculate text size using draw.textbbox
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), self.text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Determine canvas size based on direction
        if self.direction in ["left", "right"]:
            canvas_width = text_width + self.width
            canvas_height = self.height
        elif self.direction in ["up", "down"]:
            canvas_width = self.width
            canvas_height = text_height + self.height
        else:
            self.logger.warning(f"Unknown direction '{self.direction}'. Defaulting to 'left'.")
            self.direction = "left"
            canvas_width = text_width + self.width
            canvas_height = self.height

        # Create text image with transparency
        if self.bg_color:
            text_image = Image.new("RGBA", (canvas_width, canvas_height), self.bg_color + (255,))
        else:
            text_image = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        draw = ImageDraw.Draw(text_image)

        # Calculate text position based on alignment
        if self.direction in ["left", "right"]:
            if self.alignment == "left":
                x = 0
            elif self.alignment == "center":
                x = (self.width - text_width) // 2
            elif self.alignment == "right":
                x = self.width - text_width
            else:
                x = 0  # Default to left
            y = (self.height - text_height) // 2
        elif self.direction in ["up", "down"]:
            x = (self.width - text_width) // 2
            if self.alignment == "left":
                y = 0
            elif self.alignment == "center":
                y = (self.height - text_height) // 2
            elif self.alignment == "right":
                y = self.height - text_height
            else:
                y = 0  # Default to top
        else:
            x, y = 0, 0

        # Draw shadow if enabled
        if self.shadow:
            shadow_x, shadow_y = self.shadow_offset
            draw.text(
                (x + shadow_x, y + shadow_y),
                self.text,
                font=self.font,
                fill=self.shadow_color + (int(255 * self.opacity),)
            )

        # Draw text
        draw.text(
            (x, y),
            self.text,
            font=self.font,
            fill=self.color + (int(255 * self.opacity),)
        )

        return text_image

    def initialize_scrolling(self):
        # Corrected delta signs
        if self.direction == "left":
            self.x_pos = self.width
            self.y_pos = 0
            self.delta_x = -self.speed / self.fps
            self.delta_y = 0
        elif self.direction == "right":
            self.x_pos = -self.text_image.width
            self.y_pos = 0
            self.delta_x = self.speed / self.fps
            self.delta_y = 0
        elif self.direction == "up":
            self.x_pos = 0
            self.y_pos = self.height
            self.delta_x = 0
            self.delta_y = -self.speed / self.fps
        elif self.direction == "down":
            self.x_pos = 0
            self.y_pos = -self.text_image.height
            self.delta_x = 0
            self.delta_y = self.speed / self.fps
        else:
            self.x_pos = self.width
            self.y_pos = 0
            self.delta_x = -self.speed / self.fps
            self.delta_y = 0

    def init_effect_params(self):
        """
        Initializes parameters for text effects.
        """
        params = {}
        if self.effect == "fade":
            params["fade_in"] = True
            params["fade_out"] = True
            params["fade_step"] = 5  # Opacity change per frame
            params["current_opacity"] = 0
        elif self.effect == "blink":
            params["blink"] = True
            params["blink_interval"] = self.fps  # Blink every second
            params["blink_counter"] = 0
            params["visible"] = True
        elif self.effect == "color_cycle":
            # Define a list of colors to cycle through
            params["color_cycle"] = [
                (255, 0, 0),    # Red
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Cyan
            ]
            params["current_color_index"] = 0
            params["color_change_interval"] = self.fps * 2  # Change color every 2 seconds
            params["color_change_counter"] = 0
        return params

    def apply_effects(self):
        """
        Applies text effects based on the current frame.
        """
        if not self.effect:
            return

        if self.effect == "fade":
            if self.effect_params.get("fade_in"):
                if self.effect_params["current_opacity"] < 255 * self.opacity:
                    self.effect_params["current_opacity"] += self.effect_params["fade_step"]
                    if self.effect_params["current_opacity"] >= 255 * self.opacity:
                        self.effect_params["current_opacity"] = int(255 * self.opacity)
                        self.effect_params["fade_in"] = False
            elif self.effect_params.get("fade_out"):
                if self.effect_params["current_opacity"] > 0:
                    self.effect_params["current_opacity"] -= self.effect_params["fade_step"]
                    if self.effect_params["current_opacity"] <= 0:
                        self.effect_params["current_opacity"] = 0
                        self.effect_params["fade_out"] = False
            # Update text_image opacity
            alpha = self.effect_params.get("current_opacity", int(255 * self.opacity))
            text_with_alpha = self.text_image.copy()
            text_with_alpha.putalpha(alpha)
            self.text_image = text_with_alpha

        elif self.effect == "blink":
            self.effect_params["blink_counter"] += 1
            if self.effect_params["blink_counter"] >= self.effect_params["blink_interval"]:
                self.effect_params["blink_counter"] = 0
                self.effect_params["visible"] = not self.effect_params["visible"]
            if not self.effect_params["visible"]:
                # Make text transparent
                text_with_alpha = self.text_image.copy()
                transparent = Image.new("RGBA", self.text_image.size, (0, 0, 0, 0))
                self.text_image = transparent
            else:
                # Restore text
                self.text_image = self.create_text_image()

        elif self.effect == "color_cycle":
            self.effect_params["color_change_counter"] += 1
            if self.effect_params["color_change_counter"] >= self.effect_params["color_change_interval"]:
                self.effect_params["color_change_counter"] = 0
                self.effect_params["current_color_index"] = (self.effect_params["current_color_index"] + 1) % len(
                    self.effect_params["color_cycle"]
                )
                # Update text color
                new_color = self.effect_params["color_cycle"][self.effect_params["current_color_index"]]
                self.color = new_color
                self.text_image = self.create_text_image()

    def read(self) -> Optional[np.ndarray]:
        current_time = time.perf_counter()
        elapsed_time = current_time - self.last_frame_time

        if elapsed_time >= 1.0 / self.fps:
            self.last_frame_time = current_time

            if self.direction in ["left", "right"]:
                self.x_pos += self.delta_x
                if self.direction == "left" and self.x_pos <= -self.text_image.width:
                    self.x_pos = self.width
                elif self.direction == "right" and self.x_pos >= self.width:
                    self.x_pos = -self.text_image.width
            elif self.direction in ["up", "down"]:
                self.y_pos += self.delta_y
                if self.direction == "up" and self.y_pos <= -self.text_image.height:
                    self.y_pos = self.height
                elif self.direction == "down" and self.y_pos >= self.height:
                    self.y_pos = -self.text_image.height

        # Apply effects
        self.apply_effects()

        # Create a blank frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Convert PIL image to OpenCV image with alpha channel
        frame_pil = self.text_image.copy()
        frame_cv = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGBA2BGRA)

        x = int(self.x_pos)
        y = int(self.y_pos)

        # Create an overlay
        overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)  # BGRA

        # Determine the area where the text will be placed
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(self.width, x + frame_cv.shape[1])
        y_end = min(self.height, y + frame_cv.shape[0])

        text_x_start = max(0, -x)
        text_y_start = max(0, -y)
        text_x_end = text_x_start + (x_end - x_start)
        text_y_end = text_y_start + (y_end - y_start)

        if x_start < x_end and y_start < y_end:
            overlay[y_start:y_end, x_start:x_end] = frame_cv[text_y_start:text_y_end, text_x_start:text_x_end]

        # Convert frame to BGRA
        frame_bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

        # Combine frame and overlay
        combined = cv2.add(frame_bgra, overlay)

        # Convert back to BGR
        final_frame = cv2.cvtColor(combined, cv2.COLOR_BGRA2BGR)

        self.current_frame = final_frame
        return self.current_frame

            
    def stop(self):
        """
        Stops the text animator.
        """
        self.logger.debug("Stopping TextAnimator")
        # Any cleanup if necessary
        pass
