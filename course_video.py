"""Animated lecture video generator — teacher character explains concepts from study chapters."""

import sys, time
from pathlib import Path
import config
from src.chapters import get_chapter_info
from src.script_generator import generate_lecture_scenes, generate_lecture_dialogue, generate_video_title
from src.text_to_speech import generate_tts
from src.video_builder import build_lecture_video


EXAMS = ["neet", "upsc", "jee", "gate", "ssc-gd", "cgl", "ibps-po", "sbi-clerk", "rbi", "ctet"]


def main():
    print("=" * 55)
    print("  COURSEVI — ANIMATED LECTURE GENERATOR")
    print("=" * 55)

    exam = "neet"
    chapter_num = 1
    if len(sys.argv) > 1:
        exam = sys.argv[1].lower()
        if exam not in EXAMS:
            print(f"  Unknown exam: {exam}. Using neet.")
            exam = "neet"
    if len(sys.argv) > 2:
        try:
            chapter_num = int(sys.argv[2])
        except ValueError:
            print(f"  Invalid chapter number: {sys.argv[2]}. Using 1.")

    ch_info = get_chapter_info(exam, chapter_num)
    if not ch_info:
        print(f"  No chapter {chapter_num} found for {exam}.")
        return

    print(f"\n  Exam: {exam.upper()}")
    print(f"  Chapter: {ch_info['title']}")
    print(f"  Concepts: {len(ch_info['concepts'])}")

    if not ch_info["concepts"]:
        print("  No concepts found. Using chapter title as topic.")
        ch_info["concepts"] = [{"title": ch_info["title"], "explanation": f"Learning about {ch_info['title']}"}]

    temp_dir = config.TEMP_DIR / f"{exam}_{ch_info['filename']}"
    temp_dir.mkdir(exist_ok=True)

    print(f"\n[1/4] Creating lecture scenes...")
    topic_keywords = ch_info["filename"].replace("biology-chapter-", "").replace("-", " ")
    scenes = generate_lecture_scenes(ch_info["title"], topic_keywords, ch_info["concepts"])
    print(f"  {len(scenes)} lecture scenes created")

    dialogue = generate_lecture_dialogue(scenes)
    if not dialogue or len(dialogue) < 50:
        for s in scenes:
            s["dialogue"] = f"Let's understand {s['heading']}. This is an important concept."
        dialogue = generate_lecture_dialogue(scenes)

    title = generate_video_title(ch_info["title"], topic_keywords)

    print(f"\n[2/4] Generating voiceover ({len(dialogue)} chars)...")
    print(f"  Title: {title}")
    tts_path = temp_dir / "narration.mp3"
    try:
        generate_tts(dialogue, tts_path)
    except Exception as e:
        print(f"  TTS failed: {e}. Trying fallback...")
        try:
            fallback = ". ".join(s.get("heading", "") for s in scenes if s.get("heading"))
            if fallback:
                generate_tts(fallback, tts_path)
            else:
                print("  No fallback text.")
                return
        except Exception as e2:
            print(f"  TTS fallback failed: {e2}")
            return
    print(f"  Voiceover saved ({tts_path.stat().st_size / 1024:.0f} KB)")

    print(f"\n[3/4] Building animated lecture video...")
    safe_title = title.lower().replace(" ", "_").replace("?", "").replace("!", "").replace("'", "").replace(".","").replace(",","").replace(":","").replace("|","")[:60]
    out_path = config.OUTPUT_DIR / f"{exam}_{safe_title}.mp4"
    out_path.unlink(missing_ok=True)

    build_lecture_video(scenes, tts_path, out_path, title=title, exam=exam)

    print(f"\n[4/4] Video ready!")
    print(f"  Output: {out_path}")

    return out_path, {"title": title, "exam": exam, "chapter": ch_info["title"], "scenes": scenes}


if __name__ == "__main__":
    t0 = time.time()
    try:
        main()
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print(f"\n  Total time: {time.time() - t0:.0f}s")
