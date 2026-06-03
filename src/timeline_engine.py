"""Timeline-based scene composition engine for animated lecture videos.

Each scene is composed of timed layers with individual animations.
Layers are composited per-frame onto a background, enabling
progressive reveals, synchronized text, and multi-element motion.

Performance: each layer is pre-rendered to a RGBA numpy array once.
Per-frame compositing uses numpy alpha blending (no PIL in the loop).
"""

from __future__ import annotations
import math, random, hashlib, threading
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
    shape_type: str
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

    Each layer is pre-rendered to a RGBA numpy array once.
    Per-frame compositing is pure numpy alpha blending — no PIL in the loop.
    """

    def __init__(self, duration: float):
        self.duration = duration
        self.layers: list[Layer] = []
        self.bg_image: Image.Image | None = None
        self._bg_np: np.ndarray | None = None
        self._prepped: list[_PrepLayer] | None = None

    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    def set_background(self, bg: Image.Image):
        self.bg_image = bg
        self._bg_np = None

    def _get_bg(self) -> np.ndarray:
        if self._bg_np is not None:
            return self._bg_np
        if self.bg_image:
            pil = self.bg_image.copy().resize((W, H), Image.LANCZOS)
        else:
            pil = Image.new("RGB", (W, H), COLORS["bg"])
            draw = ImageDraw.Draw(pil)
            for y in range(0, H, 4):
                shade = int(20 + 10 * math.sin(y / 80))
                draw.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
        self._bg_np = np.array(pil)
        return self._bg_np


class _PrepLayer:
    """A layer with its element pre-rendered to RGBA numpy."""

    def __init__(self, layer: Layer):
        self.start_time = layer.start_time
        self.duration = layer.duration
        self.elem = layer.element
        self.is_text = isinstance(layer.element, TextLayer)
        self.is_shape = isinstance(layer.element, ShapeLayer)
        self.is_arrow = isinstance(layer.element, ArrowLayer)

        anim = getattr(layer.element, "animation", AnimType.FADE_IN)
        self.anim_type = anim

        self.rgba: np.ndarray | None = None
        self.base_x: int = 0
        self.base_y: int = 0
        self.w: int = 0
        self.h: int = 0

        if self.is_text:
            self._prep_text()
        elif self.is_shape:
            self._prep_shape()
        elif self.is_arrow:
            self._prep_arrow()

    def _prep_text(self):
        e = self.elem
        try:
            font = ImageFont.truetype(FONT, e.font_size)
        except Exception:
            font = ImageFont.load_default()
        try:
            bbox = font.getbbox(e.text)
            self.w = bbox[2] - bbox[0] + 4
            self.h = bbox[3] - bbox[1] + 4
        except Exception:
            self.w = len(e.text) * e.font_size
            self.h = e.font_size + 4

        if self.w < 1 or self.h < 1:
            self.w, self.h = 10, 10

        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), e.text, font=font, fill=(*e.color, 255))
        self.rgba = np.array(img)
        self.base_x = e.x
        self.base_y = e.y

    def _prep_shape(self):
        e = self.elem
        self.w, self.h = max(e.w, 1), max(e.h, 1)
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill_rgba = (*e.fill, 255)
        outline_rgba = (*e.outline, 255) if e.outline else None

        if e.shape_type in ("rect", "rounded_rect"):
            if e.shape_type == "rounded_rect":
                draw.rounded_rectangle([0, 0, self.w, self.h], radius=e.radius,
                                       fill=fill_rgba, outline=outline_rgba, width=2)
            else:
                draw.rectangle([0, 0, self.w, self.h],
                               fill=fill_rgba, outline=outline_rgba, width=2)
        elif e.shape_type == "circle":
            draw.ellipse([0, 0, self.w, self.h],
                         fill=fill_rgba, outline=outline_rgba, width=2)

        self.rgba = np.array(img)
        self.base_x = e.x
        self.base_y = e.y

    def _prep_arrow(self):
        e = self.elem
        self.w = abs(e.x2 - e.x1) + 20
        self.h = abs(e.y2 - e.y1) + 20
        if self.w < 1:
            self.w = 10
        if self.h < 1:
            self.h = 10
        self.base_x = min(e.x1, e.x2) - 10
        self.base_y = min(e.y1, e.y2) - 10
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        ax = e.x1 - self.base_x
        ay = e.y1 - self.base_y
        bx = e.x2 - self.base_x
        by = e.y2 - self.base_y
        draw.line([(ax, ay), (bx, by)], fill=(*e.color, 255), width=e.width)
        dx, dy = bx - ax, by - ay
        angle = math.atan2(dy, dx)
        head_len = 12
        hx1 = bx - head_len * math.cos(angle - 0.4)
        hy1 = by - head_len * math.sin(angle - 0.4)
        hx2 = bx - head_len * math.cos(angle + 0.4)
        hy2 = by - head_len * math.sin(angle + 0.4)
        draw.polygon([(bx, by), (int(hx1), int(hy1)), (int(hx2), int(hy2))], fill=(*e.color, 255))
        self.rgba = np.array(img)

    def get_alpha(self, progress: float) -> float:
        if self.anim_type == AnimType.NONE:
            return 1.0
        return float(np.clip(progress * 1.5, 0.0, 1.0))

    def get_offset(self, progress: float) -> tuple[int, int]:
        ox, oy = 0, 0
        t = self.anim_type
        if t == AnimType.SLIDE_LEFT:
            ox = -int((1 - progress) * 80)
        elif t == AnimType.SLIDE_RIGHT:
            ox = int((1 - progress) * 80)
        elif t == AnimType.SLIDE_UP:
            oy = -int((1 - progress) * 80)
        elif t == AnimType.SLIDE_DOWN:
            oy = int((1 - progress) * 80)
        return ox, oy

    def get_char_count(self, progress: float) -> int | None:
        if self.anim_type == AnimType.TYPEWRITER and self.is_text:
            return max(1, int(len(self.elem.text) * progress))
        return None

    def get_scale(self, progress: float) -> float | None:
        if self.anim_type == AnimType.POP and self.is_text:
            s = min(progress * 2.0, 1.0)
            if s < 0.01:
                return 0.0
            return s
        return None


def _alpha_blend(bg: np.ndarray, fg: np.ndarray, x: int, y: int, alpha: float):
    """Alpha-blend fg (RGBA) onto bg (RGB) at position (x,y) with global alpha."""
    h, w = fg.shape[:2]
    if h <= 0 or w <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(bg.shape[1], x + w)
    y1 = min(bg.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return

    fx0 = x0 - x
    fy0 = y0 - y
    fx1 = fx0 + (x1 - x0)
    fy1 = fy0 + (y1 - y0)

    fg_slice = fg[fy0:fy1, fx0:fx1]
    bg_slice = bg[y0:y1, x0:x1]

    if alpha < 1.0:
        a = (fg_slice[:, :, 3].astype(np.float32) / 255.0) * alpha
    else:
        a = fg_slice[:, :, 3].astype(np.float32) / 255.0

    a = a[:, :, np.newaxis]
    bg[y0:y1, x0:x1] = (bg_slice.astype(np.float32) * (1 - a) + fg_slice[:, :, :3].astype(np.float32) * a).astype(np.uint8)


def _composite_frame(
    bg_np: np.ndarray,
    prepped: list[_PrepLayer],
    t: float,
) -> np.ndarray:
    """Composite all visible layers at time t onto background copy."""
    frame = bg_np.copy()

    for pl in prepped:
        if t < pl.start_time or t > pl.start_time + pl.duration:
            continue

        progress = 0.0
        local_t = t - pl.start_time
        anim_dur = pl.elem.animation_duration if hasattr(pl.elem, "animation_duration") else 0.3
        if anim_dur > 0:
            progress = min(local_t / anim_dur, 1.0)

        alpha = pl.get_alpha(progress)
        if alpha <= 0:
            continue

        ox, oy = pl.get_offset(progress)
        x = pl.base_x + ox
        y = pl.base_y + oy

        if pl.anim_type == AnimType.TYPEWRITER and pl.is_text:
            char_count = max(1, int(len(pl.elem.text) * progress))
            e = pl.elem
            try:
                font = ImageFont.truetype(FONT, e.font_size)
            except Exception:
                font = ImageFont.load_default()
            visible_text = e.text[:char_count]
            try:
                bbox = font.getbbox(visible_text)
                tw = bbox[2] - bbox[0] + 4
                th = bbox[3] - bbox[1] + 4
            except Exception:
                tw, th = 10, e.font_size + 4
            if tw < 1 or th < 1:
                continue
            img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 2), visible_text, font=font, fill=(*e.color, 255))
            text_rgba = np.array(img)
            _alpha_blend(frame, text_rgba, x, y, alpha)
            continue

        if pl.anim_type == AnimType.POP and pl.is_text:
            scale = min(progress * 2.0, 1.0)
            if scale < 0.01:
                continue
            e = pl.elem
            scaled_size = max(int(e.font_size * scale), 8)
            try:
                font = ImageFont.truetype(FONT, scaled_size)
            except Exception:
                font = ImageFont.load_default()
            try:
                bbox = font.getbbox(e.text)
                tw = bbox[2] - bbox[0] + 4
                th = bbox[3] - bbox[1] + 4
            except Exception:
                tw, th = 10, scaled_size + 4
            if tw < 1 or th < 1:
                continue
            img = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2, 2), e.text, font=font, fill=(*e.color, 255))
            text_rgba = np.array(img)
            cx = x + (pl.w // 2) - (tw // 2)
            cy = y + (pl.h // 2) - (th // 2)
            _alpha_blend(frame, text_rgba, cx, cy, alpha)
            continue

        if pl.is_arrow:
            arr_elem = pl.elem
            if progress < 0.1:
                continue
            end_progress = min(progress * 1.2, 1.0)
            ex = arr_elem.x1 + (arr_elem.x2 - arr_elem.x1) * end_progress
            ey = arr_elem.y1 + (arr_elem.y2 - arr_elem.y1) * end_progress
            ax, ay = min(arr_elem.x1, int(ex)) - 10, min(arr_elem.y1, int(ey)) - 10
            aw = abs(arr_elem.x1 - int(ex)) + 20
            ah = abs(arr_elem.y1 - int(ey)) + 20
            if aw < 1 or ah < 1:
                continue
            arrow_img = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
            draw = ImageDraw.Draw(arrow_img)
            draw.line([(arr_elem.x1 - ax, arr_elem.y1 - ay), (int(ex) - ax, int(ey) - ay)],
                      fill=(*arr_elem.color, 255), width=arr_elem.width)
            if progress >= 0.8:
                dx, dy = arr_elem.x2 - arr_elem.x1, arr_elem.y2 - arr_elem.y1
                angle = math.atan2(dy, dx)
                head_len = 12
                hx1 = arr_elem.x2 - head_len * math.cos(angle - 0.4)
                hy1 = arr_elem.y2 - head_len * math.sin(angle - 0.4)
                hx2 = arr_elem.x2 - head_len * math.cos(angle + 0.4)
                hy2 = arr_elem.y2 - head_len * math.sin(angle + 0.4)
                draw.polygon([(arr_elem.x2, arr_elem.y2), (int(hx1), int(hy1)), (int(hx2), int(hy2))],
                             fill=(*arr_elem.color, 255))
            arrow_rgba = np.array(arrow_img)
            _alpha_blend(frame, arrow_rgba, ax, ay, alpha)
            continue

        if pl.rgba is not None:
            _alpha_blend(frame, pl.rgba, x, y, alpha)

    return frame


class _CachedSceneClip(VideoClip):
    """A VideoClip backed by a pre-rendered frame cache."""

    def __init__(self, cache: list[np.ndarray], fps: int, duration: float):
        self._cache = cache
        self._fps = fps
        self._clip_duration = duration
        super().__init__(frame_function=self._make_frame)
        self.duration = duration
        self.end = duration

    def _make_frame(self, t):
        dur = self._clip_duration
        if dur is not None and t >= dur:
            t = dur - 0.001
        fi = min(int(t * self._fps), len(self._cache) - 1)
        return self._cache[fi]


def build_clip(self, fps: int = config.VIDEO_FPS) -> VideoClip:
    """Build a VideoClip with pre-rendered frame cache."""
    prepped = [_PrepLayer(l) for l in self.layers]
    bg_np = self._get_bg()

    total_frames = max(1, int(self.duration * fps))
    print(f"    Rendering {total_frames} frames ({len(prepped)} layers)...")

    cache = [None] * total_frames
    for fi in range(total_frames):
        t = fi / fps
        if t >= self.duration:
            t = self.duration - 0.001
        cache[fi] = _composite_frame(bg_np, prepped, t)

    print(f"    Done — {len(cache)} frames cached")
    return _CachedSceneClip(cache, fps, self.duration)


SceneTimeline.build_clip = build_clip


def build_standard_scene(
    duration: float,
    heading: str,
    bullet_lines: list[str],
    scene_type: str = "explain",
    bg_image: Image.Image | None = None,
) -> SceneTimeline:
    """Build a SceneTimeline with standard lecture layout."""
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
            animation_duration=0.4,
            delay=delay,
        )
        tl.add_layer(Layer(delay, duration - delay, bullet_layer))

    return tl
