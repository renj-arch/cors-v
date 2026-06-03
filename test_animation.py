"""Quick test: render a short animated lecture video with the new timeline engine."""

import sys
sys.path.insert(0, '.')
from pathlib import Path
from src.scene_composer import compose_scene
from moviepy import concatenate_videoclips
import config

print("Building animated test video...")

scenes_data = [
    {
        "type": "intro",
        "heading": "Cell: The Unit of Life",
        "bullets": "Complete guide for NEET Biology",
        "dialogue": "Welcome to this lesson on Cell Biology.",
    },
    {
        "type": "explain",
        "heading": "Cell Theory",
        "bullets": "All living things are made of cells,Cell is the basic unit of life,All cells arise from pre-existing cells",
        "dialogue": "Cell theory is the foundation of modern biology.",
    },
    {
        "type": "explain",
        "heading": "Types of Cells",
        "bullets": "Prokaryotic cells have no nucleus,Eukaryotic cells have a nucleus,Bacteria are prokaryotes,Plants and animals are eukaryotes",
        "dialogue": "There are two main types of cells.",
    },
    {
        "type": "summary",
        "heading": "Quick Recap",
        "bullets": "Cell theory fundamentals,Prokaryotic vs Eukaryotic,Key differences",
        "dialogue": "Let us recap what we learned.",
    },
]

clips = []
for i, s in enumerate(scenes_data):
    print(f"  Scene {i+1}: {s['type']}...")
    clip = compose_scene(s, 3.0)
    clips.append(clip)

final = concatenate_videoclips(clips, method="compose")
print(f"  Total duration: {final.duration:.1f}s")

out_dir = config.OUTPUT_DIR
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "test_animated_lecture.mp4"

final.write_videofile(
    str(out_path),
    fps=config.VIDEO_FPS,
    codec="libx264",
    audio_codec="aac",
    threads=4,
    preset="ultrafast",
    ffmpeg_params=["-movflags", "+faststart"],
    logger=None,
)
final.close()
print(f"  Done! Output: {out_path}")
print(f"  File size: {out_path.stat().st_size / 1024:.0f} KB")
