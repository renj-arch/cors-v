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


def _font(size=28):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


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


def _heading(draw, bx, by, bw, text):
    f = _font(36)
    draw.text((bx + 30, by + 20), text, font=f, fill=C["accent2"])
    draw.rectangle([bx + 30, by + 72, bx + bw - 30, by + 75], fill=C["accent"])


def _wrap(text, max_w, font):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + " " + w if cur else w
        if font.getbbox(test)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


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
    lines = _wrap(text, w - 20, f)
    line_h = font_size + 4
    total_h = len(lines) * line_h
    sy = y + (h - total_h) // 2
    for i, line in enumerate(lines):
        tw = f.getbbox(line)[2]
        draw.text((x + (w - tw) // 2, sy + i * line_h), line, font=f, fill=text_color)


def render_flowchart(heading, lines):
    """Step-by-step flowchart with boxes and arrows."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    n = min(len(items), 6)
    box_w = min(220, (bw - 80) // n)
    box_h = 80
    gap = (bw - 80 - n * box_w) // max(n - 1, 1)
    start_x = bx + 40
    y = by + 110

    for i, item in enumerate(items[:n]):
        x = start_x + i * (box_w + gap)
        colors = [C["box1"], C["box2"], C["box3"], C["box4"]]
        _box(draw, x, y, box_w, box_h, f"{i+1}. {item}", fill=colors[i % 4], font_size=22)
        if i < n - 1:
            ax = x + box_w
            ay2 = y + box_h // 2
            _arrow(draw, ax + 2, ay2, x + box_w + gap - 2, ay2)

    return img


def render_steps(heading, lines):
    """Vertical numbered steps with connecting arrows."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    n = min(len(items), 6)
    box_h = 55
    gap = 20
    total_h = n * box_h + (n - 1) * gap
    start_y = by + (bh - total_h) // 2 + 40

    for i, item in enumerate(items[:n]):
        y = start_y + i * (box_h + gap)
        num_w = 40
        cx = bx + 50
        draw.ellipse([cx, y + 5, cx + num_w, y + box_h - 5], fill=C["accent2"])
        fn = _font(20)
        draw.text((cx + 12, y + 14), str(i + 1), font=fn, fill=(0, 0, 0))
        tx = cx + num_w + 20
        tw = bw - (tx - bx) - 40
        f = _font(24)
        draw.text((tx, y + 12), item, font=f, fill=C["text"])
        if i < n - 1:
            _arrow(draw, cx + 20, y + box_h + 2, cx + 20, y + box_h + gap - 2,
                   color=C["accent3"], width=2)

    return img


def render_comparison(heading, lines):
    """Side-by-side comparison columns."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    col_w = (bw - 100) // 2
    col_h = bh - 130
    y = by + 110

    mid_x = bx + bw // 2
    draw.line([(mid_x, y), (mid_x, y + col_h)], fill=C["board_outline"], width=2)

    left_text = items[:len(items)//2] if len(items) > 1 else items[:1]
    right_text = items[len(items)//2:] if len(items) > 1 else []

    f = _font(24)
    for i, item in enumerate(left_text):
        iy = y + 20 + i * 40
        draw.text((bx + 50, iy), f"{i+1}. {item[:50]}", font=f, fill=C["accent3"])

    for i, item in enumerate(right_text):
        iy = y + 20 + i * 40
        draw.text((mid_x + 50, iy), f"{i+1}. {item[:50]}", font=f, fill=C["accent4"])

    return img


def render_classification(heading, lines):
    """Hierarchical tree / classification diagram."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    root_y = by + 100
    root_w = 300
    root_h = 50
    root_x = bx + (bw - root_w) // 2
    _box(draw, root_x, root_y, root_w, root_h, heading[:35], fill=C["box2"], font_size=24)

    n = min(len(items), 4)
    child_w = min(200, (bw - 100) // n)
    child_h = 70
    child_y = root_y + root_h + 60
    gap = (bw - 80 - n * child_w) // max(n - 1, 1)
    start_x = bx + 40

    for i, item in enumerate(items[:n]):
        cx = start_x + i * (child_w + gap)
        _box(draw, cx, child_y, child_w, child_h, item, fill=C["box3" if i % 2 else "box1"], font_size=20)
        arrow_top_x = root_x + root_w // 2
        arrow_top_y = root_y + root_h
        arrow_bot_x = cx + child_w // 2
        arrow_bot_y = child_y
        if i == 0:
            _arrow(draw, arrow_top_x, arrow_top_y, arrow_bot_x, arrow_bot_y, width=2)
        else:
            _arrow(draw, arrow_top_x, arrow_top_y, arrow_bot_x, arrow_bot_y, width=2)

    return img


def render_concept(heading, lines):
    """Central concept with surrounding detail nodes connected by lines."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    cx, cy = W // 2, by + bh // 2 - 20
    center_r = 60
    draw.ellipse([cx - center_r, cy - center_r, cx + center_r, cy + center_r],
                 fill=C["accent2"], outline=C["board_outline"], width=3)
    fn = _font(18)
    tw = fn.getbbox(heading[:20])[2]
    draw.text((cx - tw // 2, cy - 8), heading[:20], font=fn, fill=(0, 0, 0))

    n = min(len(items), 6)
    node_r = 50
    angle_step = 2 * math.pi / n
    for i, item in enumerate(items[:n]):
        angle = angle_step * i - math.pi / 2
        nx = cx + int(200 * math.cos(angle))
        ny = cy + int(200 * math.sin(angle))
        draw.line([(cx, cy), (nx, ny)], fill=C["accent"], width=2)
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r],
                     fill=C["box1"], outline=C["accent"], width=2)
        f = _font(16)
        lines_wrapped = _wrap(item[:35], node_r * 2 - 10, f)
        for li, lw in enumerate(lines_wrapped[:2]):
            lw_tw = f.getbbox(lw)[2]
            draw.text((nx - lw_tw // 2, ny - 8 + li * 18), lw, font=f, fill=C["text"])

    return img


def render_bullets(heading, lines):
    """Styled bullet list with icons."""
    img = _bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 60, 60, W - 120, H - 120
    _board(draw, bx, by, bw, bh)
    _heading(draw, bx, by, bw, heading)

    items = [l for l in lines if l]
    if not items:
        return img

    f = _font(26)
    y = by + 120
    colors = [C["accent"], C["accent2"], C["accent3"], C["accent4"], C["highlight"]]
    for i, item in enumerate(items[:8]):
        dot_color = colors[i % len(colors)]
        draw.ellipse([bx + 60, y + 8, bx + 76, y + 24], fill=dot_color)
        draw.text((bx + 90, y + 4), item[:70], font=f, fill=C["text"])
        y += 44

    return img


def render_scene(scene_type, heading, lines):
    """Auto-detect best diagram type and render."""
    h = heading.lower()
    combined = " ".join(lines).lower()

    if scene_type == "summary":
        return render_bullets("Key Takeaways", lines)

    if any(w in combined or w in h for w in ["comparison", "vs ", "difference", "pros", "cons", "advantage"]):
        return render_comparison(heading, lines)

    if any(w in combined or w in h for w in ["type", "category", "classification", "kind", "branch"]):
        return render_classification(heading, lines)

    if any(w in combined or w in h for w in ["step", "process", "method", "technique", "approach", "procedure"]):
        if len(lines) <= 4:
            return render_steps(heading, lines)
        return render_flowchart(heading, lines)

    if any(w in combined or w in h for w in ["concept", "overview", "introduction", "what is", "definition"]):
        return render_concept(heading, lines)

    if scene_type == "hook":
        return render_concept(heading, lines)

    if len(lines) <= 3:
        return render_steps(heading, lines)
    if len(lines) <= 5:
        return render_flowchart(heading, lines)

    return render_bullets(heading, lines)
