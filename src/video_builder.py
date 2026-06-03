"""Animated lecture-style video builder with transitions and visual effects."""

import io, random, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import requests as req
from moviepy import (
    VideoClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, ColorClip,
    CompositeAudioClip, concatenate_audioclips,
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
import config

FONT = config.get_font()
W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

COLORS = {
    "bg": (20, 25, 40),
    "bg_light": (35, 40, 60),
    "accent": (80, 200, 255),
    "accent2": (255, 210, 80),
    "accent3": (100, 255, 150),
    "text": (255, 255, 255),
    "text_sec": (200, 210, 230),
    "board": (30, 35, 50),
}




def gen_image(prompt: str, w: int = W, h: int = H) -> Image.Image | None:
    url = f"https://image.pollinations.ai/prompt/{req.utils.quote(prompt)}?width={w}&height={h}&nofeed=true&seed={random.randint(0,999999)}&model=flux"
    try:
        r = req.get(url, timeout=120)
        if r.status_code == 200 and len(r.content) > 500:
            return Image.open(io.BytesIO(r.content)).convert("RGB")
    except:
        pass
    return None


def upscale(img: Image.Image) -> Image.Image:
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.1)
    return img


def create_lecture_bg() -> Image.Image:
    canvas = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)
    for y in range(0, H, 4):
        shade = int(20 + 10 * math.sin(y / 80))
        draw.line([(0, y), (W, y)], fill=(shade, shade + 5, shade + 15))
    return canvas


def create_blackboard(bg: Image.Image | None, heading: str) -> Image.Image:
    if bg is None:
        bg = create_lecture_bg()
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)
    board_w, board_h = int(W * 0.85), int(H * 0.55)
    bx, by = (W - board_w) // 2, int(H * 0.08)
    draw.rounded_rectangle([bx, by, bx + board_w, by + board_h], radius=12,
                           fill=(15, 18, 28), outline=(60, 70, 100), width=2)

    try:
        font_h = ImageFont.truetype(FONT, 44)
        font_b = ImageFont.truetype(FONT, 32)
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()

    if heading:
        draw.text((bx + 40, by + 30), heading, font=font_h, fill=COLORS["accent2"])

    draw.rectangle([bx + 40, by + 85, bx + board_w - 40, by + 88], fill=COLORS["accent"])

    return canvas


def draw_on_board(canvas: Image.Image, lines: list[str], y_start: int = 150) -> Image.Image:
    img = canvas.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT, 28)
    except:
        font = ImageFont.load_default()

    board_w = int(W * 0.85)
    bx = (W - board_w) // 2
    by = int(H * 0.08)

    y = by + y_start
    for line in lines:
        chars_per_line = 45
        while len(line) > chars_per_line:
            split_at = line.rfind(" ", 0, chars_per_line)
            if split_at == -1:
                split_at = chars_per_line
            draw.text((bx + 40, y), line[:split_at], font=font, fill=COLORS["text"])
            line = line[split_at:].strip()
            y += 40
        draw.text((bx + 40, y), line, font=font, fill=COLORS["text"])
        y += 42
    return img


def create_teacher_scene(board_bg: Image.Image | None,
                         heading: str, bullet_lines: list[str]) -> Image.Image:
    canvas = create_blackboard(board_bg, heading)
    canvas = draw_on_board(canvas, bullet_lines)
    return canvas


def typewriter_effect(text: str, duration: float, start_time: float,
                      pos=("center", "center"), font_size: int = 36,
                      color: str = "white") -> list:
    chars = len(text)
    char_dur = duration / max(chars, 1)
    clips = []
    for i in range(1, chars + 1, 3):
        display = text[:i]
        t = TextClip(text=display, font=FONT, font_size=font_size, color=color,
                     stroke_color="black", stroke_width=2, method="label")
        t = t.with_position(pos).with_start(start_time + (i / max(chars, 1)) * duration * 0.8).with_duration(0.3)
        clips.append(t)
    return clips


def zoom_in_effect(clip: VideoClip, intensity: float = 0.1) -> VideoClip:
    def f(t):
        p = t / clip.duration if clip.duration > 0 else 1
        scale = 1.0 + p * intensity
        return np.array(clip.get_frame(t))
    return clip.transform(lambda frame: None)


def ken_burns_zoom(img: Image.Image, dur: float, zoom_max: float = 0.15) -> VideoClip:
    arr = np.array(img)
    h, w = arr.shape[:2]

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


def slide_transition(left_img: np.ndarray, right_img: np.ndarray, dur: float = 0.6) -> VideoClip:
    def make_frame(t):
        p = t / dur if dur > 0 else 1
        split = int(W * p)
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:, :W - split] = left_img[:, split:]
        frame[:, W - split:] = right_img[:, :split]
        return frame
    return VideoClip(make_frame, duration=dur)


def fade_transition(img: np.ndarray, dur: float = 0.3, fade_in: bool = True) -> VideoClip:
    arr = img.copy().astype(np.float32)
    def make_frame(t):
        p = t / dur if dur > 0 else 1
        if fade_in:
            return (arr * min(p, 1.0)).astype(np.uint8)
        else:
            return (arr * max(1.0 - p, 0)).astype(np.uint8)
    return VideoClip(make_frame, duration=dur)


def create_pointer_animation(duration: float, start_x: int, start_y: int, end_x: int, end_y: int,
                             start_time: float = 0) -> VideoClip:
    pointer_size = 20
    def make_frame(t):
        p = t / duration if duration > 0 else 1
        cx = int(start_x + (end_x - start_x) * p)
        cy = int(start_y + (end_y - start_y) * p)
        frame = np.zeros((H, W, 4), dtype=np.uint8)
        cv2 = None
        try:
            from PIL import ImageDraw
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([cx - pointer_size // 2, cy - pointer_size // 2,
                          cx + pointer_size // 2, cy + pointer_size // 2],
                         fill=(255, 50, 50, 200))
            draw.line([(cx, cy), (cx + 30, cy + 40)], fill=(255, 50, 50, 200), width=4)
            return np.array(img)
        except:
            return frame
    clip = VideoClip(make_frame, duration=duration)
    return clip.with_start(start_time)


def build_lecture_video(
    scenes: list[dict],
    audio_path: Path,
    output_path: Path,
    title: str = "",
    exam: str = "neet",
) -> Path:
    audio = AudioFileClip(str(audio_path))
    total_dur = audio.duration
    audio.close()

    scene_dur = total_dur / max(len(scenes), 1)

    print(f"\n  Generating {len(scenes)} lecture scenes...")

    scene_images = []
    for i, scene in enumerate(scenes):
        scene_type = scene.get("type", "explain")
        heading = scene.get("heading", "")
        lines = scene.get("bullets", "")
        if isinstance(lines, str):
            lines = [l.strip() for l in lines.replace("•", "").split(",") if l.strip()]
        if not lines:
            lines = [heading]

        img_prompt = scene.get("image_prompt", f"educational illustration: {heading}, infographic, 16:9")
        diag_img = gen_image(img_prompt)
        if diag_img:
            diag_img = upscale(diag_img)

        if scene_type == "hook" or scene_type == "intro":
            canvas = create_lecture_bg()
            canvas = create_blackboard(canvas, heading)
            canvas = draw_on_board(canvas, lines)
            scene_images.append(np.array(canvas))

        elif scene_type == "explain":
            canvas = create_teacher_scene(diag_img, heading, lines)
            scene_images.append(np.array(canvas))

        elif scene_type == "demo" or scene_type == "diagram":
            if diag_img:
                canvas = diag_img.copy()
                overlay = Image.new("RGBA", (W, int(H * 0.2)), (0, 0, 0, 160))
                canvas = Image.fromarray(canvas)
                canvas.paste(overlay, (0, 0), overlay)
                draw = ImageDraw.Draw(canvas)
                try:
                    f = ImageFont.truetype(FONT, 40)
                    draw.text((40, 20), heading, font=f, fill=COLORS["accent2"])
                except:
                    pass
                scene_images.append(np.array(canvas))
            else:
                canvas = create_teacher_scene(None, heading, lines)
                scene_images.append(np.array(canvas))

        elif scene_type == "summary":
            canvas = create_lecture_bg()
            canvas = create_blackboard(canvas, "📝 Key Takeaways")
            canvas = draw_on_board(canvas, lines[:6])
            scene_images.append(np.array(canvas))

        elif scene_type == "cta":
            canvas = create_lecture_bg()
            canvas = create_blackboard(canvas, heading)
            canvas = draw_on_board(canvas, lines)
            scene_images.append(np.array(canvas))

        else:
            canvas = create_teacher_scene(None, heading, lines)
            scene_images.append(np.array(canvas))

        print(f"    Scene {i+1}: {scene_type} — {heading[:40]}")

    print("  Assembling lecture...")
    clips = []

    for i, (scene_data, img_arr) in enumerate(zip(scenes, scene_images)):
        sd = scene_dur
        if i < len(scenes) - 1:
            sd = total_dur / len(scenes)
        else:
            sd = total_dur - (len(scenes) - 1) * (total_dur / len(scenes))

        if sd <= 0:
            sd = 0.5

        if sd > 1.5:
            main = ken_burns_zoom(img_arr, sd * 0.92, zoom_max=0.08)
            clips.append(main)
            if i < len(scenes) - 1:
                trans = fade_transition(img_arr, sd * 0.08, fade_in=False)
                clips.append(trans)
        else:
            main = ImageClip(img_arr, duration=sd)
            clips.append(main)

    if clips:
        bg = concatenate_videoclips(clips, method="compose")
    else:
        bg = ColorClip(color=COLORS["bg"], duration=max(total_dur, 1), size=config.VIDEO_SIZE)

    overlays = []

    ch_label = TextClip(text=f"{exam.upper()} Lecture", font=FONT, font_size=18,
                        color=COLORS["accent"], stroke_color="black", stroke_width=1,
                        method="label")
    ch_label = ch_label.with_position((20, 20)).with_duration(bg.duration).with_start(0)
    overlays.append(ch_label)

    from src.engagement import subscribe_end_card, comment_prompt
    overlays += comment_prompt(start_time=max(bg.duration * 0.6, 10.0), duration=3.0)
    end_card = subscribe_end_card(3.0).with_start(bg.duration)
    final_dur = bg.duration + 3.0

    final = CompositeVideoClip([bg] + overlays + [end_card], size=config.VIDEO_SIZE)
    final = final.with_duration(final_dur)

    audio_clip = AudioFileClip(str(audio_path))
    if final_dur > audio_clip.duration:
        silence = AudioFileClip(str(audio_path)).with_duration(final_dur - audio_clip.duration).with_volume_scaled(0)
        audio_clip = concatenate_audioclips([audio_clip, silence])

    music_paths = list(config.MUSIC_DIR.glob("*.mp3"))
    if music_paths:
        music = AudioFileClip(str(random.choice(music_paths)))
        music = music.with_duration(final_dur).with_volume_scaled(0.06)
        music = music.with_effects([AudioFadeIn(1.0), AudioFadeOut(2.0)])
        final = final.with_audio(CompositeAudioClip([audio_clip, music]))
    else:
        final = final.with_audio(audio_clip)

    print(f"  Rendering {final_dur:.1f}s animated lecture...")
    final.write_videofile(
        str(output_path),
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast",
        ffmpeg_params=["-movflags", "+faststart"],
        logger=None,
    )
    final.close()
    print(f"  Done: {output_path}")
    return output_path
