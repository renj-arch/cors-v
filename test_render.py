"""Render a short animated test with frame caching."""
import sys, time
sys.path.insert(0, '.')
from src.scene_composer import compose_scene
from src.timeline_engine import SceneTimeline
from src import animated_components as ac
from moviepy import concatenate_videoclips
import config

scenes_data = [
    {"type": "intro", "heading": "Cell: The Unit of Life", "bullets": "Complete guide for NEET Biology", "dialogue": "Welcome."},
    {"type": "explain", "heading": "Cell Theory", "bullets": "All living things are made of cells,Cell is the basic unit of life,All cells arise from pre-existing cells", "dialogue": "Cell theory is the foundation."},
    {"type": "explain", "heading": "Types of Cells", "bullets": "Prokaryotic cells have no nucleus,Eukaryotic cells have a nucleus,Bacteria are prokaryotes", "dialogue": "Two main types of cells."},
    {"type": "summary", "heading": "Quick Recap", "bullets": "Cell theory fundamentals,Prokaryotic vs Eukaryotic,Key differences", "dialogue": "Let us recap."},
]

clips = []
for i, s in enumerate(scenes_data):
    print(f"Scene {i+1}: {s['type']} ({3.0}s)")
    t0 = time.time()
    clip = compose_scene(s, 3.0)
    elapsed = time.time() - t0
    print(f"  Composed in {elapsed:.1f}s")
    clips.append(clip)

final = concatenate_videoclips(clips, method="compose")
print(f"\nTotal duration: {final.duration:.1f}s")

out_path = config.OUTPUT_DIR / "test_cache.mp4"
print(f"Rendering to {out_path}...")
t0 = time.time()
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
render_time = time.time() - t0
final.close()
file_size = out_path.stat().st_size / 1024
print(f"\nDone! {file_size:.0f} KB, rendered in {render_time:.1f}s")
print(f"Avg: {render_time/final.duration:.1f}s per second of video")
