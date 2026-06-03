"""Reusable animated visual components for lecture scenes.

Provides pre-built animated elements that can be composed into
a SceneTimeline: progressive bullet lists, animated headings,
highlight boxes, typing text, diagrams, and call-to-action cards.
"""

from __future__ import annotations
import math
from PIL import Image, ImageDraw, ImageFont
import config
from src.timeline_engine import (
    W, H, FONT, COLORS,
    Layer, SceneTimeline,
    TextLayer, ShapeLayer, ArrowLayer, ImageLayer,
    AnimType,
)

FONT_CACHE = {}


def _font(size=28):
    if size in FONT_CACHE:
        return FONT_CACHE[size]
    f = None
    try:
        f = ImageFont.truetype(FONT, size)
    except Exception:
        try:
            f = ImageFont.load_default().font_variant(size=size)
        except Exception:
            f = ImageFont.load_default()
    FONT_CACHE[size] = f
    return f


def _tw(font, text):
    bbox = font.getbbox(text)
    if bbox:
        return bbox[2] - bbox[0]
    return len(text) * 8


def _wrap(text, max_w, font):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + " " + w if cur else w
        if _tw(font, test) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if not lines:
        fallback_len = max(int(max_w / max(_tw(font, "W"), 1)), 1)
        return [text[:fallback_len]]
    return lines


def _draw_wrapped(draw, x, y, text, font, fill, max_w, line_spacing=None):
    if line_spacing is None:
        line_spacing = font.size + 6
    lines = _wrap(text, max_w, font)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_spacing
    return y


def add_standard_background(tl: SceneTimeline):
    """Add the dark gradient background to a timeline."""
    canvas = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)
    for y in range(0, H, 4):
        shade = int(20 + 10 * math.sin(y / 80))
        draw.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
    tl.set_background(canvas)


def add_board_background(tl: SceneTimeline):
    """Add gradient background + a rounded board rectangle."""
    add_standard_background(tl)
    board = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.05), y=int(H * 0.08),
        w=int(W * 0.9), h=int(H * 0.78),
        fill=COLORS["board"], outline=(60, 70, 100),
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
    )
    tl.add_layer(Layer(0, tl.duration, board))


def add_animated_heading(
    tl: SceneTimeline,
    text: str,
    x: int | None = None,
    y: int = 120,
    font_size: int = 38,
    color: tuple[int, int, int] = COLORS["accent2"],
    start_time: float = 0.1,
    duration: float | None = None,
    with_underline: bool = True,
):
    """Add a heading that slides in from top with underline."""
    if x is None:
        x = int(W * 0.08)
    if duration is None:
        duration = tl.duration - start_time

    heading = TextLayer(
        text=text,
        x=x, y=y,
        font_size=font_size,
        color=color,
        animation=AnimType.SLIDE_DOWN,
        animation_duration=0.5, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, heading))

    if with_underline:
        underline = ShapeLayer(
            shape_type="rect",
            x=x, y=y + font_size + 8,
            w=min(len(text) * (font_size // 2), int(W * 0.8)), h=3,
            fill=COLORS["accent"],
            animation=AnimType.FADE_IN, animation_duration=0.3, delay=start_time + 0.3,
        )
        tl.add_layer(Layer(start_time + 0.3, duration - 0.3, underline))


def add_progressive_bullets(
    tl: SceneTimeline,
    lines: list[str],
    start_x: int = int(W * 0.08),
    start_y: int = int(H * 0.28),
    font_size: int = 26,
    gap: int = 48,
    start_delay: float = 0.5,
    item_interval: float = 0.35,
    color: tuple[int, int, int] = COLORS["text"],
    max_items: int = 7,
):
    """Add bullet points that reveal one by one with slide/fade animation."""
    for i, line in enumerate(lines[:max_items]):
        delay = start_delay + i * item_interval
        anim = AnimType.SLIDE_LEFT if i % 2 == 0 else AnimType.FADE_IN
        dot_colors = [COLORS["accent"], COLORS["accent2"], COLORS["accent3"], COLORS["accent4"], COLORS["highlight"]]

        dot = ShapeLayer(
            shape_type="circle",
            x=start_x, y=start_y + i * gap + 4,
            w=14, h=14,
            fill=dot_colors[i % 5],
            animation=AnimType.POP,
            animation_duration=0.25, delay=delay,
        )
        tl.add_layer(Layer(delay, tl.duration - delay, dot))

        bullet = TextLayer(
            text=line,
            x=start_x + 24, y=start_y + i * gap,
            font_size=font_size,
            color=color,
            animation=anim,
            animation_duration=0.4, delay=delay,
            max_width=int(W * 0.75),
        )
        tl.add_layer(Layer(delay, tl.duration - delay, bullet))


def add_highlight_box(
    tl: SceneTimeline,
    text: str,
    x: int,
    y: int,
    w: int,
    h: int,
    start_time: float,
    duration: float = 3.0,
    font_size: int = 28,
    fill: tuple = (255, 100, 80, 60),
    text_color: tuple = COLORS["accent2"],
):
    """Add a highlight box that pulses/fades in over a region, with optional label."""
    box = ShapeLayer(
        shape_type="rounded_rect",
        x=x, y=y, w=w, h=h,
        fill=fill[:3] if len(fill) == 3 else fill,
        outline=COLORS["accent2"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, box))

    if text:
        heading = TextLayer(
            text=text,
            x=x + 12, y=y + 8,
            font_size=font_size,
            color=text_color,
            animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
        )
        tl.add_layer(Layer(start_time + 0.15, duration - 0.15, heading))


def add_fact_callout(
    tl: SceneTimeline,
    fact_text: str,
    start_time: float,
    duration: float = 4.0,
):
    """Add a 'Did You Know?' callout with icon-like circle and text."""
    cx, cy = W // 2, H // 2 - 60

    circle = ShapeLayer(
        shape_type="circle",
        x=cx - 80, y=cy - 80, w=160, h=160,
        fill=COLORS["accent"],
        animation=AnimType.POP, animation_duration=0.4, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, circle))

    icon_text = TextLayer(
        text="💡",
        x=cx - 20, y=cy - 25,
        font_size=40,
        color=(255, 255, 255),
        animation=AnimType.POP, animation_duration=0.3, delay=0.1,
    )
    tl.add_layer(Layer(start_time + 0.1, duration - 0.1, icon_text))

    label = TextLayer(
        text="DID YOU KNOW?",
        x=cx - 80, y=cy + 50,
        font_size=22,
        color=COLORS["accent2"],
        animation=AnimType.SLIDE_UP, animation_duration=0.3, delay=0.2,
    )
    tl.add_layer(Layer(start_time + 0.2, duration - 0.2, label))

    text = TextLayer(
        text=fact_text,
        x=int(W * 0.12), y=cy + 110,
        font_size=26,
        color=COLORS["text"],
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.5,
        max_width=int(W * 0.76),
    )
    tl.add_layer(Layer(start_time + 0.5, duration - 0.5, text))


def add_definition_box(
    tl: SceneTimeline,
    term: str,
    definition: str,
    start_time: float,
    duration: float = 5.0,
):
    """Add a term + definition display. Term on left, definition on right."""
    bx, by = int(W * 0.05) + 30, int(H * 0.3)
    bw, bh = int(W * 0.9) - 60, 160

    box = ShapeLayer(
        shape_type="rounded_rect",
        x=bx, y=by, w=bw, h=bh,
        fill=(40, 50, 80),
        outline=COLORS["accent"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, box))

    term_text = TextLayer(
        text=term,
        x=bx + 30, y=by + 20,
        font_size=30,
        color=COLORS["accent2"],
        animation=AnimType.SLIDE_LEFT, animation_duration=0.3, delay=0.1,
    )
    tl.add_layer(Layer(start_time + 0.1, duration - 0.1, term_text))

    def_text = TextLayer(
        text=definition,
        x=bx + 30, y=by + 65,
        font_size=24,
        color=COLORS["text"],
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.4,
        max_width=bw - 60,
    )
    tl.add_layer(Layer(start_time + 0.4, duration - 0.4, def_text))


def add_formula_display(
    tl: SceneTimeline,
    formula: str,
    explanation: str,
    start_time: float,
    duration: float = 5.0,
):
    """Display a formula prominently with explanation below."""
    cx = W // 2

    formula_box = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.15), y=int(H * 0.25),
        w=int(W * 0.7), h=100,
        fill=(40, 35, 60),
        outline=COLORS["accent2"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, formula_box))

    formula_text = TextLayer(
        text=formula,
        x=cx - int(_tw(_font(36), formula) / 2), y=int(H * 0.25) + 25,
        font_size=36,
        color=COLORS["accent2"],
        animation=AnimType.POP, animation_duration=0.4, delay=0.15,
    )
    tl.add_layer(Layer(start_time + 0.15, duration - 0.15, formula_text))

    if explanation:
        expl_text = TextLayer(
            text=explanation,
            x=int(W * 0.12), y=int(H * 0.25) + 130,
            font_size=24,
            color=COLORS["text_sec"],
            animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.6,
            max_width=int(W * 0.76),
        )
        tl.add_layer(Layer(start_time + 0.6, duration - 0.6, expl_text))


def add_subscribe_card(tl: SceneTimeline, start_time: float, duration: float = 3.0):
    """Add an end-card subscribe prompt."""
    cx = W // 2
    box = ShapeLayer(
        shape_type="rounded_rect",
        x=int(W * 0.15), y=int(H * 0.3),
        w=int(W * 0.7), h=200,
        fill=(25, 25, 40),
        outline=COLORS["accent2"],
        animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.0,
    )
    tl.add_layer(Layer(start_time, duration, box))

    txt1 = TextLayer(
        text="SUBSCRIBE 🔔",
        x=cx - 140, y=int(H * 0.3) + 40,
        font_size=48,
        color=COLORS["accent2"],
        animation=AnimType.POP, animation_duration=0.4, delay=0.2,
    )
    tl.add_layer(Layer(start_time + 0.2, duration - 0.2, txt1))

    txt2 = TextLayer(
        text="FOR MORE ANIMATED LECTURES",
        x=cx - 180, y=int(H * 0.3) + 105,
        font_size=28,
        color=COLORS["text"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.6,
    )
    tl.add_layer(Layer(start_time + 0.6, duration - 0.6, txt2))

    txt3 = TextLayer(
        text="@vlymbooq",
        x=cx - 70, y=int(H * 0.3) + 145,
        font_size=24,
        color=COLORS["accent"],
        animation=AnimType.FADE_IN, animation_duration=0.3, delay=0.9,
    )
    tl.add_layer(Layer(start_time + 0.9, duration - 0.9, txt3))


def add_topic_intro(
    tl: SceneTimeline,
    topic: str,
    subtitle: str = "",
):
    """Full-screen topic intro with animated title."""
    cx = W // 2
    cy = H // 2 - 60

    circle = ShapeLayer(
        shape_type="circle",
        x=cx - 100, y=cy - 100, w=200, h=200,
        fill=COLORS["accent"],
        animation=AnimType.POP, animation_duration=0.5, delay=0.0,
    )
    tl.add_layer(Layer(0, tl.duration, circle))

    topic_text = TextLayer(
        text=topic,
        x=cx - int(_tw(_font(42), topic) / 2), y=cy - 20,
        font_size=42,
        color=(255, 255, 255),
        animation=AnimType.TYPEWRITER, animation_duration=0.8, delay=0.2,
    )
    tl.add_layer(Layer(0.2, tl.duration - 0.2, topic_text))

    if subtitle:
        sub_text = TextLayer(
            text=subtitle,
            x=cx - int(_tw(_font(24), subtitle) / 2), y=cy + 50,
            font_size=24,
            color=COLORS["text_sec"],
            animation=AnimType.FADE_IN, animation_duration=0.4, delay=0.8,
        )
        tl.add_layer(Layer(0.8, tl.duration - 0.8, sub_text))


def add_step_diagram(
    tl: SceneTimeline,
    heading: str,
    steps: list[str],
    start_y: int = 200,
):
    """Animated step diagram with numbered circles and connecting arrows."""
    bx = int(W * 0.1)
    bw = int(W * 0.8)

    n = min(len(steps), 6)
    usable_h = int(H * 0.65)
    step_h = min(65, (usable_h - (n - 1) * 12) // n)
    step_h = max(step_h, 36)
    gap = 12
    total_h = n * step_h + (n - 1) * gap
    start_y = int(H * 0.08) + (int(H * 0.78) - total_h) // 2 + 40

    for i, step in enumerate(steps[:n]):
        delay = 0.3 + i * 0.3
        y = start_y + i * (step_h + gap)

        num_circle = ShapeLayer(
            shape_type="circle",
            x=bx + 20, y=y + (step_h - 32) // 2, w=32, h=32,
            fill=COLORS["accent2"],
            animation=AnimType.POP, animation_duration=0.25, delay=delay,
        )
        tl.add_layer(Layer(delay, tl.duration - delay, num_circle))

        num_text = TextLayer(
            text=str(i + 1),
            x=bx + 28, y=y + (step_h - 32) // 2 + 4,
            font_size=18,
            color=(0, 0, 0),
            animation=AnimType.FADE_IN, animation_duration=0.15, delay=delay + 0.1,
        )
        tl.add_layer(Layer(delay + 0.1, tl.duration - delay - 0.1, num_text))

        step_text = TextLayer(
            text=step,
            x=bx + 70, y=y + 4,
            font_size=22,
            color=COLORS["text"],
            animation=AnimType.SLIDE_LEFT, animation_duration=0.35, delay=delay + 0.1,
            max_width=bw - 90,
        )
        tl.add_layer(Layer(delay + 0.1, tl.duration - delay - 0.1, step_text))

        if i < n - 1:
            arrow = ArrowLayer(
                x1=bx + 36, y1=y + step_h,
                x2=bx + 36, y2=y + step_h + gap,
                color=COLORS["accent3"], width=2,
                animation=AnimType.FADE_IN, animation_duration=0.2, delay=delay + 0.3,
            )
            tl.add_layer(Layer(delay + 0.3, tl.duration - delay - 0.3, arrow))
