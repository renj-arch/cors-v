"""Programmatic diagram rendering for lecture videos — flowcharts, comparisons, step-by-step, classification trees."""

import math
from PIL import Image, ImageDraw, ImageFont
import config

FONT = config.get_font()
W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

C = {
    "bg": (20, 25, 40),
    "board": (15, 18, 28),
    "board_outline": (60, 70, 100),
    "accent": (80, 200, 255),
    "accent2": (255, 210, 80),
    "accent3": (100, 255, 150),
    "accent4": (200, 130, 255),
    "text": (255, 255, 255),
    "text_sec": (200, 210, 230),
    "box1": (40, 50, 80),
    "box2": (60, 80, 120),
    "box3": (80, 60, 100),
    "box4": (40, 80, 60),
    "arrow": (255, 200, 80),
    "highlight": (255, 100, 80),
}

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


def _bg():
    img = Image.new("RGB", (W, H), C["bg"])
    draw = ImageDraw.Draw(img)
    for y in range(0, H, 4):
        shade = int(20 + 10 * math.sin(y / 80))
        draw.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
    return img


def _board(draw, bx, by, bw, bh):
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=12,
                           fill=C["board"], outline=C["board_outline"], width=2)


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


def _arrow(draw, x1, y1, x2, y2, color=None, width=3):
    c = color or C["arrow"]
    draw.line([(x1, y1), (x2, y2)], fill=c, width=width)
    dx, dy = x2 - x1, y2 - y1
    angle = math.atan2(dy, dx)
    head_len = 12
    ax = x2 - head_len * math.cos(angle - 0.4)
    ay = y2 - head_len * math.sin(angle - 0.4)
    bx = x2 - head_len * math.cos(angle + 0.4)
    by = y2 - head_len * math.sin(angle + 0.4)
    draw.polygon([(x2, y2), (ax, ay), (bx, by)], fill=c)


def _box(draw, x, y, w, h, text, fill=C["box1"], text_color=C["text"], font_size=24):
    f = _font(font_size)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=fill, outline=C["board_outline"], width=2)
    inner_w = max(w - 16, 10)
    lines = _wrap(text, inner_w, f)
    lh = font_size + 4
    total_h = len(lines) * lh
    sy = y + max((h - total_h) // 2, 4)
    for i, line in enumerate(lines):
        tw = _tw(f, line)
        tx = max(x + (w - tw) // 2, x + 8)
        draw.text((tx, sy + i * lh), line, font=f, fill=text_color)


def _draw_heading(draw, bx, by, bw, heading):
    f = _font(32)
    max_w = bw - 60
    display = heading
    while _tw(f, display) > max_w and len(display) > 5:
        display = display[:-1]
    if display != heading and len(display) > 3:
        display = display[:-3] + "..."
    draw.text((bx + 30, by + 20), display, font=f, fill=C["accent2"])
    underline_y = by + 62
    line_w = min(_tw(f, display), max_w)
    draw.rectangle([bx + 30, underline_y, bx + 30 + line_w, underline_y + 3], fill=C["accent"])


def render_flowchart(heading, lines):
    """Vertical stacked flowchart with arrows between boxes. Handles 1-8 items."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    n = min(len(items), 8)
    usable_h = bh - 140
    usable_w = bw - 100
    box_h = min(70, int(usable_h / n) - 6)
    box_h = max(box_h, 40)
    gap = 8
    total_h = n * box_h + (n - 1) * gap
    start_y = by + (bh - total_h) // 2 + 30

    f_b = _font(18)
    for i, item in enumerate(items[:n]):
        y = start_y + i * (box_h + gap)
        colors = [C["box1"], C["box2"], C["box3"], C["box4"]]
        label = f"{i+1}. {item}"
        _box(draw, bx + 50, y, usable_w, box_h, label, fill=colors[i % 4], font_size=18)
        if i < n - 1:
            _arrow(draw, bx + 50 + usable_w // 2, y + box_h + 1,
                   bx + 50 + usable_w // 2, y + box_h + gap - 1,
                   color=C["accent3"], width=2)

    return img


def render_steps(heading, lines):
    """Numbered vertical circles with step descriptions."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    n = min(len(items), 6)
    usable_h = bh - 140
    usable_w = bw - 180
    box_h = min(int(usable_h / n) - 10, 70)
    box_h = max(box_h, 36)
    gap = 10
    total_h = n * box_h + (n - 1) * gap
    start_y = by + (bh - total_h) // 2 + 30

    f_text = _font(22)
    for i, item in enumerate(items[:n]):
        y = start_y + i * (box_h + gap)
        num_r = 16
        cx = bx + 55
        cy = y + box_h // 2
        draw.ellipse([cx - num_r, cy - num_r, cx + num_r, cy + num_r], fill=C["accent2"])
        fn = _font(16)
        num_tw = _tw(fn, str(i + 1))
        draw.text((cx - num_tw // 2, cy - 8), str(i + 1), font=fn, fill=(0, 0, 0))
        tx = cx + num_r + 16
        _draw_wrapped(draw, tx, y + 4, item, f_text, C["text"], usable_w, line_spacing=26)
        if i < n - 1:
            _arrow(draw, cx, cy + num_r + 2, cx, cy + num_r + gap - 2,
                   color=C["accent3"], width=2)

    return img


def render_comparison(heading, lines):
    """Two-column comparison chart."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    col_w = (bw - 120) // 2
    y = by + 110
    col_h = bh - 140
    mid_x = bx + bw // 2

    draw.line([(mid_x, y), (mid_x, y + col_h)], fill=C["board_outline"], width=2)

    mid = len(items) // 2
    left_items = items[:mid] if mid else items[:1]
    right_items = items[mid:] if mid else []

    f = _font(22)
    for i, item in enumerate(left_items):
        iy = y + 12 + i * 38
        _draw_wrapped(draw, bx + 45, iy, item, f, C["accent3"], col_w - 20, line_spacing=28)

    for i, item in enumerate(right_items):
        iy = y + 12 + i * 38
        _draw_wrapped(draw, mid_x + 45, iy, item, f, C["accent4"], col_w - 20, line_spacing=28)

    return img


def render_classification(heading, lines):
    """Tree diagram: root heading at top, child categories below."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    root_y = by + 100
    root_w = min(400, bw - 80)
    root_h = 50
    root_x = bx + (bw - root_w) // 2
    _box(draw, root_x, root_y, root_w, root_h, heading[:40], fill=C["box2"], font_size=22)

    n = min(len(items), 6)
    child_w = min(200, (bw - 100) // n)
    child_h = 70
    child_y = root_y + root_h + 50
    gap = (bw - 80 - n * child_w) // max(n - 1, 1)
    if gap < 8:
        gap = 8
        child_w = (bw - 80 - (n - 1) * gap) // n
    child_w = max(child_w, 60)
    start_x = bx + 40

    for i, item in enumerate(items[:n]):
        cx = start_x + i * (child_w + gap)
        _box(draw, cx, child_y, child_w, child_h, item, fill=C["box3" if i % 2 else "box1"], font_size=16)
        _arrow(draw, root_x + root_w // 2, root_y + root_h,
               cx + child_w // 2, child_y, width=2)

    return img


def render_concept(heading, lines):
    """Radial mind map: center concept with orbiting nodes."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    cx, cy = W // 2, by + bh // 2 - 20
    center_r = 60
    draw.ellipse([cx - center_r, cy - center_r, cx + center_r, cy + center_r],
                 fill=C["accent2"], outline=C["board_outline"], width=3)
    fn = _font(16)
    hw = _tw(fn, heading[:18])
    draw.text((cx - hw // 2, cy - 8), heading[:18], font=fn, fill=(0, 0, 0))

    n = min(len(items), 6)
    node_r = 55
    radius = 180
    angle_step = 2 * math.pi / n if n else 1
    for i, item in enumerate(items[:n]):
        angle = angle_step * i - math.pi / 2
        nx = cx + int(radius * math.cos(angle))
        ny = cy + int(radius * math.sin(angle))
        draw.line([(cx, cy), (nx, ny)], fill=C["accent"], width=2)
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r],
                     fill=C["box1"], outline=C["accent"], width=2)
        f = _font(14)
        inner_w = node_r * 2 - 16
        _draw_wrapped(draw, nx - node_r + 8, ny - 12, item[:40], f, C["text"], inner_w, line_spacing=16)

    return img


def render_bullets(heading, lines):
    """Styled bullet list with colored dots and wrapping."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _draw_heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    f = _font(24)
    max_w = bw - 130
    y = by + 110
    colors = [C["accent"], C["accent2"], C["accent3"], C["accent4"], C["highlight"]]
    for i, item in enumerate(items[:10]):
        dot_color = colors[i % len(colors)]
        draw.ellipse([bx + 50, y + 6, bx + 64, y + 20], fill=dot_color)
        y = _draw_wrapped(draw, bx + 78, y, item, f, C["text"], max_w, line_spacing=30)
        y += 8

    return img


def render_scene(scene_type, heading, lines):
    """Auto-detect best diagram type and render. Always returns an Image."""
    h = heading.lower()
    combined = " ".join(lines).lower()

    if scene_type == "summary":
        return render_bullets("Key Takeaways", lines)

    if any(w in combined or w in h for w in ["comparison", "vs ", "difference", "pros", "cons", "advantage", "disadvantage"]):
        return render_comparison(heading, lines)

    if any(w in combined or w in h for w in ["type", "category", "classification", "kind", "branch"]):
        return render_classification(heading, lines)

    if any(w in combined or w in h for w in ["step", "process", "method", "technique", "approach", "procedure", "how to"]):
        if len(lines) <= 6:
            return render_steps(heading, lines)
        return render_flowchart(heading, lines)

    if any(w in combined or w in h for w in ["concept", "overview", "introduction", "what is", "definition"]):
        return render_concept(heading, lines)

    if scene_type == "hook":
        return render_concept(heading, lines)

    if len(lines) <= 3:
        return render_steps(heading, lines)
    if len(lines) <= 6:
        return render_flowchart(heading, lines)

    return render_bullets(heading, lines)
