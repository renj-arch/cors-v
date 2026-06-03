"""Bridges raw scene data from script_generator into animated SceneTimelines.

Auto-detects scene type and assembles the appropriate animated layers using
the animated_components building blocks. Falls back to static rendering
(visual_renderer) for complex diagram types not yet animated.
"""

from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from moviepy import VideoClip, ImageClip, CompositeVideoClip, AudioFileClip
import config
from src.timeline_engine import (
    W, H, COLORS,
    SceneTimeline, Layer,
    TextLayer, ShapeLayer, AnimType,
    build_standard_scene,
)
from src import animated_components as ac
from src import visual_renderer

FONT = config.get_font()


def compose_scene(
    scene: dict,
    duration: float,
) -> VideoClip:
    """Build a single animated scene from a scene dict.

    Auto-detects the diagram type and uses animated components when possible,
    falling back to static visual_renderer output with Ken Burns zoom.
    """
    scene_type = scene.get("type", "explain")
    heading = scene.get("heading", "")
    lines_raw = scene.get("bullets", "")
    dialogue = scene.get("dialogue", "")

    if isinstance(lines_raw, str):
        lines = [l.strip() for l in lines_raw.replace("•", "").split(",") if l.strip()]
    else:
        lines = list(lines_raw) if lines_raw else []
    if not lines:
        lines = [heading]

    combined = (heading + " " + " ".join(lines)).lower()

    if scene_type == "intro":
        return _build_intro_scene(heading, lines, dialogue, duration)
    elif scene_type == "hook":
        return _build_hook_scene(heading, lines, dialogue, duration)
    elif scene_type == "summary":
        return _build_summary_scene(heading, lines, duration)
    elif scene_type == "cta":
        return _build_cta_scene(heading, duration)
    elif any(w in combined for w in ["step", "process", "method", "how to", "procedure"]):
        if len(lines) <= 6:
            return _build_step_scene(heading, lines, duration)
        return _build_standard_animated(heading, lines, duration)
    elif any(w in combined for w in ["definition", "what is", "term", "meaning"]):
        return _build_definition_scene(heading, lines, duration)
    elif any(w in combined for w in ["formula", "equation", "="]):
        return _build_formula_scene(heading, lines, duration)
    elif any(w in combined for w in ["comparison", "vs ", "difference", "pros", "cons"]):
        return _build_standard_animated(heading, lines, duration)
    else:
        return _build_standard_animated(heading, lines, duration)


def _build_intro_scene(
    heading: str, lines: list[str], dialogue: str, duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_standard_background(tl)

    board = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.05), y=int(H * 0.08),
        w=int(W * 0.9), h=int(H * 0.78),
        fill=COLORS["board"], outline=(60, 70, 100),
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.0,
    )
    tl.add_layer(Layer(0, duration, board))

    ac.add_topic_intro(tl, heading, subtitle=lines[0] if lines else "")

    return tl.build_clip()


def _build_hook_scene(
    heading: str, lines: list[str], dialogue: str, duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_standard_background(tl)

    ac.add_fact_callout(tl, dialogue or heading, start_time=0.0, duration=duration)

    return tl.build_clip()


def _build_summary_scene(
    heading: str, lines: list[str], duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_board_background(tl)
    ac.add_animated_heading(tl, "Key Takeaways", y=120)
    ac.add_progressive_bullets(
        tl, lines,
        start_delay=0.3,
        item_interval=0.3,
    )
    return tl.build_clip()


def _build_cta_scene(heading: str, duration: float) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_standard_background(tl)
    ac.add_subscribe_card(tl, start_time=0.0, duration=duration)
    return tl.build_clip()


def _build_standard_animated(
    heading: str, lines: list[str], duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_board_background(tl)
    ac.add_animated_heading(tl, heading, y=120)
    ac.add_progressive_bullets(tl, lines, start_y=int(H * 0.28))
    return tl.build_clip()


def _build_step_scene(
    heading: str, lines: list[str], duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_board_background(tl)
    ac.add_animated_heading(tl, heading, y=100, font_size=32)
    ac.add_step_diagram(tl, heading, lines, start_y=160)
    return tl.build_clip()


def _build_definition_scene(
    heading: str, lines: list[str], duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_standard_background(tl)

    term = heading
    definition = " ".join(lines) if lines else heading

    board = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.05), y=int(H * 0.08),
        w=int(W * 0.9), h=int(H * 0.78),
        fill=COLORS["board"], outline=(60, 70, 100),
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.0,
    )
    tl.add_layer(Layer(0, duration, board))

    ac.add_definition_box(tl, term, definition, start_time=0.0, duration=duration)

    return tl.build_clip()


def _build_formula_scene(
    heading: str, lines: list[str], duration: float
) -> VideoClip:
    tl = SceneTimeline(duration)
    ac.add_standard_background(tl)

    board = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.05), y=int(H * 0.08),
        w=int(W * 0.9), h=int(H * 0.78),
        fill=COLORS["board"], outline=(60, 70, 100),
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.0,
    )
    tl.add_layer(Layer(0, duration, board))

    ac.add_formula_display(tl, heading, " ".join(lines[:2]), start_time=0.0, duration=duration)

    return tl.build_clip()


def build_scene_from_static(
    scene: dict,
    duration: float,
) -> ImageClip | VideoClip:
    """Fallback: render scene as static image using visual_renderer,
    then apply Ken Burns zoom for motion."""
    heading = scene.get("heading", "")
    lines_raw = scene.get("bullets", "")
    scene_type = scene.get("type", "explain")

    if isinstance(lines_raw, str):
        lines = [l.strip() for l in lines_raw.replace("•", "").split(",") if l.strip()]
    else:
        lines = list(lines_raw) if lines_raw else []
    if not lines:
        lines = [heading]

    if scene_type == "summary":
        canvas = visual_renderer.render_bullets("Key Takeaways", lines[:6])
    elif scene_type == "cta":
        canvas = visual_renderer.render_bullets(heading, lines[:4])
    else:
        canvas = visual_renderer.render_scene(scene_type, heading, lines)

    if canvas is None:
        canvas = visual_renderer._bg()

    arr = np.array(canvas)
    return _ken_burns_clip(arr, duration)


def _ken_burns_clip(arr: np.ndarray, dur: float, zoom_max: float = 0.08) -> VideoClip:
    """Slow Ken Burns zoom on a static image."""
    h, w = arr.shape[:2]
    import math

    def make_frame(t):
        p = t / dur if dur > 0 else 1
        scale = 1.0 + p * zoom_max
        cw, ch = int(w / scale), int(h / scale)
        ox = int((w - cw) * 0.5 * (1 - math.cos(p * math.pi)) * 0.3)
        oy = int((h - ch) * 0.5 * (1 - math.sin(p * math.pi * 0.5)) * 0.3)
        ox = max(0, min(ox, w - cw))
        oy = max(0, min(oy, h - ch))
        return arr[oy:oy + ch, ox:ox + cw].copy()

    return VideoClip(make_frame, duration=dur)
