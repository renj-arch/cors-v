"""Timeline-based scene composition engine for animated lecture videos.

Each scene is composed of timed layers with individual animations.
Layers are composited per-frame onto a background, enabling
progressive reveals, synchronized text, and multi-element motion.
"""

from __future__ import annotations
import math, random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import (
    VideoClip, ImageClip, TextClip, CompositeVideoClip, ColorClip,
)
import config

W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
FONT = config.get_font()

COLORS = {
    "bg": (20, 25, 40),
    "accent": (80, 200, 255),
    "accent2": (255, 210, 80),
    "accent3": (100, 255, 150),
    "accent4": (200, 130, 255),
    "text": (255, 255, 255),
    "text_sec": (200, 210, 230),
    "highlight": (255, 100, 80),
    "board": (15, 18, 28),
}


class AnimType(Enum):
    FADE_IN = auto()
    SLIDE_LEFT = auto()
    SLIDE_RIGHT = auto()
    SLIDE_UP = auto()
    SLIDE_DOWN = auto()
    POP = auto()
    TYPEWRITER = auto()
    HIGHLIGHT = auto()
    NONE = auto()


@dataclass
class TextLayer:
    text: str
    x: int
    y: int
    font_size: int = 28
    color: tuple[int, int, int] = COLORS["text"]
    max_width: int = 800
    animation: AnimType = AnimType.FADE_IN
    animation_duration: float = 0.4
    delay: float = 0.0
    highlight_color: tuple[int, int, int] | None = None


@dataclass
class ShapeLayer:
    shape_type: str  # "rect", "rounded_rect", "circle", "line"
    x: int
    y: int
    w: int
    h: int
    fill: tuple[int, int, int] = COLORS["board"]
    outline: tuple[int, int, int] | None = None
    animation: AnimType = AnimType.FADE_IN
    animation_duration: float = 0.3
    delay: float = 0.0
    radius: int = 8


@dataclass
class ImageLayer:
    pil_image: Image.Image
    x: int
    y: int
    w: int | None = None
    h: int | None = None
    animation: AnimType = AnimType.FADE_IN
    animation_duration: float = 0.4
    delay: float = 0.0


@dataclass
class ArrowLayer:
    x1: int
    y1: int
    x2: int
    y2: int
    color: tuple[int, int, int] = COLORS["accent3"]
    width: int = 3
    animation: AnimType = AnimType.FADE_IN
    animation_duration: float = 0.3
    delay: float = 0.0


class Layer:
    """A single timed element in a scene."""

    def __init__(
        self,
        start_time: float,
        duration: float,
        element: TextLayer | ShapeLayer | ImageLayer | ArrowLayer,
    ):
        self.start_time = start_time
        self.duration = duration
        self.element = element

    def end_time(self) -> float:
        return self.start_time + self.duration


class SceneTimeline:
    """Timeline of layers composing one scene.

    Renders to a (duration, height, width, 3) numpy array clip
    with all layers composited per frame.
    """

    def __init__(self, duration: float):
        self.duration = duration
        self.layers: list[Layer] = []
        self.bg_image: Image.Image | None = None

    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    def set_background(self, bg: Image.Image):
        self.bg_image = bg

    def _render_bg(self) -> Image.Image:
        if self.bg_image:
            return self.bg_image.copy().resize((W, H), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), COLORS["bg"])
        draw = ImageDraw.Draw(canvas)
        for y in range(0, H, 4):
            shade = int(20 + 10 * math.sin(y / 80))
            draw.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
        return canvas

    def build_clip(self, fps: int = config.VIDEO_FPS) -> VideoClip:
        layers_sorted = sorted(self.layers, key=lambda l: l.start_time)

        def make_frame(t):
            if t >= self.duration:
                t = self.duration - 0.01
            bg = self._render_bg()
            composite = bg.copy()
            draw = ImageDraw.Draw(composite, "RGBA")

            for layer in layers_sorted:
                if t < layer.start_time or t > layer.end_time():
                    continue
                local_t = t - layer.start_time
                elem = layer.element
                anim_dur = self._resolve_anim_duration(elem)
                progress = min(local_t / anim_dur, 1.0) if anim_dur > 0 else 1.0

                self._draw_element(composite, draw, elem, progress, local_t)

            return np.array(composite)

        return VideoClip(make_frame, duration=self.duration)

    def _resolve_anim_duration(
        self, elem: TextLayer | ShapeLayer | ImageLayer | ArrowLayer
    ) -> float:
        if hasattr(elem, "animation_duration") and elem.animation_duration:
            return elem.animation_duration
        return 0.3

    def _draw_element(
        self,
        composite: Image.Image,
        draw: ImageDraw.ImageDraw,
        elem: TextLayer | ShapeLayer | ImageLayer | ArrowLayer,
        progress: float,
        local_t: float,
    ):
        alpha = self._alpha_from_progress(elem, progress)
        if alpha <= 0:
            return

        if isinstance(elem, TextLayer):
            self._draw_text_layer(composite, draw, elem, progress, alpha)
        elif isinstance(elem, ShapeLayer):
            self._draw_shape_layer(draw, elem, progress, alpha)
        elif isinstance(elem, ImageLayer):
            self._draw_image_layer(composite, elem, progress, alpha)
        elif isinstance(elem, ArrowLayer):
            self._draw_arrow_layer(draw, elem, progress, alpha)

    def _alpha_from_progress(
        self, elem, progress: float
    ) -> float:
        anim = getattr(elem, "animation", AnimType.FADE_IN)
        if anim == AnimType.NONE:
            return 1.0
        return min(progress * 1.5, 1.0)

    def _draw_text_layer(
        self,
        composite: Image.Image,
        draw: ImageDraw.ImageDraw,
        elem: TextLayer,
        progress: float,
        alpha: float,
    ):
        try:
            font = ImageFont.truetype(FONT, elem.font_size)
        except Exception:
            font = ImageFont.load_default()

        text = elem.text
        anim = elem.animation
        x, y = elem.x, elem.y

        if anim == AnimType.TYPEWRITER:
            visible_chars = max(1, int(len(text) * progress))
            text = text[:visible_chars]
        elif anim == AnimType.SLIDE_LEFT:
            offset = int((1 - progress) * 80)
            x -= offset
        elif anim == AnimType.SLIDE_RIGHT:
            offset = int((1 - progress) * 80)
            x += offset
        elif anim == AnimType.SLIDE_UP:
            offset = int((1 - progress) * 60)
            y += offset
        elif anim == AnimType.SLIDE_DOWN:
            offset = int((1 - progress) * 60)
            y -= offset
        elif anim == AnimType.POP:
            scale = min(progress * 2, 1.0)
            if scale < 0.01:
                return
            try:
                scaled_size = max(int(elem.font_size * scale), 8)
                font = ImageFont.truetype(FONT, scaled_size)
            except Exception:
                font = ImageFont.load_default()

        text_color = elem.color
        if elem.highlight_color and progress > 0.5:
            text_color = elem.highlight_color

        try:
            bbox = font.getbbox(text)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            tw, th = len(text) * elem.font_size // 2, elem.font_size

        composite_rgba = composite.convert("RGBA")
        txt_img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((2, 2), text, font=font, fill=(*text_color, int(255 * alpha)))
        composite_rgba.paste(txt_img, (x, y), txt_img)
        composite.paste(composite_rgba.convert("RGB"))

    def _draw_shape_layer(
        self,
        draw: ImageDraw.ImageDraw,
        elem: ShapeLayer,
        progress: float,
        alpha: int,
    ):
        fill = (*elem.fill, int(255 * alpha))
        outline = elem.outline
        outline_rgba = (*outline, int(255 * alpha)) if outline else None

        if elem.shape_type in ("rect", "rounded_rect"):
            if elem.shape_type == "rounded_rect":
                draw.rounded_rectangle(
                    [elem.x, elem.y, elem.x + elem.w, elem.y + elem.h],
                    radius=elem.radius, fill=fill, outline=outline_rgba, width=2,
                )
            else:
                draw.rectangle(
                    [elem.x, elem.y, elem.x + elem.w, elem.y + elem.h],
                    fill=fill, outline=outline_rgba, width=2,
                )
        elif elem.shape_type == "circle":
            draw.ellipse(
                [elem.x, elem.y, elem.x + elem.w, elem.y + elem.h],
                fill=fill, outline=outline_rgba, width=2,
            )

    def _draw_image_layer(
        self,
        composite: Image.Image,
        elem: ImageLayer,
        progress: float,
        alpha: float,
    ):
        img = elem.pil_image
        w = elem.w or img.width
        h = elem.h or img.height
        img_resized = img.copy().resize((w, h), Image.LANCZOS)
        if alpha < 1.0:
            img_resized = img_resized.convert("RGBA")
            r, g, b, a = img_resized.split()
            a = a.point(lambda x: int(x * alpha))
            img_resized = Image.merge("RGBA", (r, g, b, a))
        composite_rgba = composite.convert("RGBA")
        composite_rgba.paste(img_resized, (elem.x, elem.y), img_resized)
        composite.paste(composite_rgba.convert("RGB"))

    def _draw_arrow_layer(
        self,
        draw: ImageDraw.ImageDraw,
        elem: ArrowLayer,
        progress: float,
        alpha: float,
    ):
        if progress < 0.1:
            return
        end_x = elem.x1 + (elem.x2 - elem.x1) * min(progress * 1.2, 1.0)
        end_y = elem.y1 + (elem.y2 - elem.y1) * min(progress * 1.2, 1.0)
        color = (*elem.color, int(255 * alpha))
        draw.line([(elem.x1, elem.y1), (int(end_x), int(end_y))], fill=color, width=elem.width)
        if progress >= 0.8:
            dx, dy = elem.x2 - elem.x1, elem.y2 - elem.y1
            angle = math.atan2(dy, dx)
            head_len = 12
            ax = elem.x2 - head_len * math.cos(angle - 0.4)
            ay = elem.y2 - head_len * math.sin(angle - 0.4)
            bx = elem.x2 - head_len * math.cos(angle + 0.4)
            by = elem.y2 - head_len * math.sin(angle + 0.4)
            draw.polygon([(elem.x2, elem.y2), (int(ax), int(ay)), (int(bx), int(by))], fill=color)


def build_standard_scene(
    duration: float,
    heading: str,
    bullet_lines: list[str],
    scene_type: str = "explain",
    bg_image: Image.Image | None = None,
) -> SceneTimeline:
    """Build a SceneTimeline with standard lecture layout:
    - Heading slides in at top
    - Bullet points fade/slide in one by one
    """
    tl = SceneTimeline(duration)

    if bg_image:
        tl.set_background(bg_image)
    else:
        base = Image.new("RGB", (W, H), COLORS["bg"])
        d = ImageDraw.Draw(base)
        for y in range(0, H, 4):
            shade = int(20 + 10 * math.sin(y / 80))
            d.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
        tl.set_background(base)

    board_layer = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.05), y=int(H * 0.08),
        w=int(W * 0.9), h=int(H * 0.72),
        fill=COLORS["board"], outline=(60, 70, 100),
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
    )
    tl.add_layer(Layer(0, duration, board_layer))

    heading_layer = TextLayer(
        text=heading,
        x=int(W * 0.08), y=int(H * 0.12),
        font_size=38,
        color=COLORS["accent2"],
        animation=AnimType.SLIDE_DOWN,
        animation_duration=0.5, delay=0.0,
    )
    tl.add_layer(Layer(0.1, duration, heading_layer))

    underline = ShapeLayer(
        shape_type="rect",
        x=int(W * 0.08), y=int(H * 0.19),
        w=min(len(heading) * 20, int(W * 0.8)), h=3,
        fill=COLORS["accent"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.3,
    )
    tl.add_layer(Layer(0.3, duration, underline))

    bullet_start_y = int(H * 0.24)
    bullet_gap = 48
    max_bullets = min(len(bullet_lines), 7)

    for i, line in enumerate(bullet_lines[:max_bullets]):
        delay = 0.5 + i * 0.35
        anim = AnimType.SLIDE_LEFT if i % 2 == 0 else AnimType.FADE_IN
        dot_color = [COLORS["accent"], COLORS["accent2"], COLORS["accent3"], COLORS["accent4"], COLORS["highlight"]][i % 5]

        dot = ShapeLayer(
            shape_type="circle",
            x=int(W * 0.08), y=bullet_start_y + i * bullet_gap + 4,
            w=14, h=14,
            fill=dot_color,
            animation=AnimType.POP,
            animation_duration=0.25, delay=delay,
        )
        tl.add_layer(Layer(delay, duration - delay, dot))

        bullet_layer = TextLayer(
            text=line,
            x=int(W * 0.12), y=bullet_start_y + i * bullet_gap,
            font_size=26,
            color=COLORS["text"],
            animation=anim,
            animation_duration=0.4, delay=delay,
        )
        tl.add_layer(Layer(delay, duration - delay, bullet_layer))

    return tl
