"""Pipeline: generate animated lecture → upload to YouTube."""

import sys
import course_video
from upload_youtube import upload


def run():
    exam = sys.argv[1] if len(sys.argv) > 1 else "neet"
    chapter = sys.argv[2] if len(sys.argv) > 2 else "1"

    print("=" * 55)
    print(f"  COURSEVI PIPELINE — {exam.upper()} Chapter {chapter}")
    print("=" * 55)

    sys.argv = [sys.argv[0], exam, chapter]
    result = course_video.main()

    if result:
        out_path, data = result
        print("\n" + "=" * 55)
        print("  UPLOADING TO YOUTUBE")
        print("=" * 55)
        try:
            upload(
                video_path=str(out_path),
                title=data.get("title", "Animated Lecture"),
                exam=data.get("exam", "neet"),
                slides=data.get("scenes", []),
            )
        except Exception as e:
            print(f"  Upload skipped: {e}")
        print(f"\n  Pipeline complete!")
    else:
        print("  Pipeline failed — no video generated.")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"PIPELINE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
