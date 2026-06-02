"""Branding, hook, end-card, and engagement overlays for YouTube educational videos."""

import random
from pathlib import Path
import numpy as np
from PIL import Image
from moviepy import VideoClip, TextClip, ImageClip, CompositeVideoClip
import config

FONT = config.get_font()
W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
CHANNEL_NAME = "Dingdong"
CHANNEL_HANDLE = "@dingdong"

LOGO_PATH = Path(__file__).resolve().parent.parent / "dingdong_logo.png"


def fast_zoom(img_array, dur: float, zoom_in: bool = True, intensity: float = 0.15) -> VideoClip:
    from PIL import Image
    if isinstance(img_array, Image.Image):
        w, h = img_array.size
    else:
        h, w = img_array.shape[:2]

    def f(t):
        p = t / dur if dur > 0 else 1
        scale = 1.0 + p * intensity if zoom_in else 1.0 + (1 - p) * intensity
        cw, ch = int(w / scale), int(h / scale)
        ox = max(0, (w - cw) // 2)
        oy = max(0, (h - ch) // 2)
        arr = img_array if isinstance(img_array, np.ndarray) else np.array(img_array)
        return arr[oy:oy + ch, ox:ox + cw].copy()
    return VideoClip(f, duration=dur)


def slide_transition(left_img, right_img, dur: float = 0.5) -> VideoClip:
    from PIL import Image
    l_arr = np.array(left_img) if isinstance(left_img, Image.Image) else left_img
    r_arr = np.array(right_img) if isinstance(right_img, Image.Image) else right_img

    def f(t):
        p = t / dur if dur > 0 else 1
        split = int(W * p)
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:, :W - split] = l_arr[:, split:]
        frame[:, W - split:] = r_arr[:, :split]
        return frame
    return VideoClip(f, duration=dur)


def fade_transition(img, dur: float = 0.3) -> VideoClip:
    arr = np.array(img) if not isinstance(img, np.ndarray) else img

    def f(t):
        p = t / dur if dur > 0 else 1
        return (arr * p).astype(np.uint8)
    return VideoClip(f, duration=dur)


def hook_overlay(duration: float = 3.0) -> list:
    hooks = [
        ("🎯 CONCEPT CLEAR IN 5 MINUTES", "#00FF88"),
        ("📚 MASTER THIS TOPIC FAST", "#FFCC00"),
        ("🧠 UNDERSTAND IN SECONDS", "#FF6600"),
        ("⚡ EXAM READY IN NO TIME", "#FF00FF"),
        ("🔥 TOP SCORING SECRET", "#FF4444"),
    ]
    text, color = random.choice(hooks)
    main = TextClip(text=text, font=FONT, font_size=48, color=color,
                    stroke_color="black", stroke_width=3, method="label")
    main = main.with_position(("center", H // 2 - 60)).with_duration(duration).with_start(0.0)
    sub = TextClip(text="subscribe for more 📖", font=FONT, font_size=28, color="white",
                   stroke_color="black", stroke_width=2, method="label")
    sub = sub.with_position(("center", H // 2 + 10)).with_duration(duration).with_start(0.0)
    return [main, sub]


def branding_overlays(duration: float) -> list:
    logo_path = LOGO_PATH
    overlays = []
    if logo_path.exists():
        logo = ImageClip(str(logo_path), duration=duration, is_mask=False)
        logo = logo.resized(height=60).with_position((W - 80, 20)).with_duration(duration).with_start(0.0)
        overlays.append(logo)
    name = TextClip(text=CHANNEL_HANDLE, font=FONT, font_size=16, color="#FFCC00",
                    stroke_color="black", stroke_width=1, method="label")
    name = name.with_position((W - 75, 85)).with_duration(duration).with_start(0.0)
    overlays.append(name)
    return overlays


def subscribe_end_card(duration: float = 3.0) -> VideoClip:
    bg_arr = np.zeros((H, W, 3), dtype=np.uint8)
    bg_arr[:] = [20, 20, 30]
    bg = ImageClip(bg_arr, duration=duration)

    txt1 = TextClip(text="SUBSCRIBE 🔔", font=FONT, font_size=64, color="#FFCC00",
                    stroke_color="black", stroke_width=3, method="label")
    txt1 = txt1.with_position(("center", H // 2 - 80)).with_duration(duration)

    txt2 = TextClip(text="FOR MORE ANIMATED LECTURES", font=FONT, font_size=32, color="white",
                    stroke_color="black", stroke_width=2, method="label")
    txt2 = txt2.with_position(("center", H // 2)).with_duration(duration)

    txt3 = TextClip(text=CHANNEL_HANDLE, font=FONT, font_size=28, color="#FFCC00",
                    stroke_color="black", stroke_width=2, method="label")
    txt3 = txt3.with_position(("center", H // 2 + 60)).with_duration(duration)

    return CompositeVideoClip([bg, txt1, txt2, txt3], size=config.VIDEO_SIZE)


def comment_prompt(start_time: float, duration: float = 3.0) -> list:
    prompts = [
        "Which concept was hardest? Comment below 👇",
        "Did this help? Drop a 🧠 in comments",
        "Share this with a friend who needs it 💪",
        "How many marks in this topic? Tell us! 📊",
        "Which exam are you preparing for? ⬇️",
    ]
    text = random.choice(prompts)
    txt = TextClip(text=text, font=FONT, font_size=28, color="white",
                   stroke_color="black", stroke_width=2, method="label")
    txt = txt.with_position(("center", H - 100)).with_duration(duration).with_start(start_time)
    return [txt]
