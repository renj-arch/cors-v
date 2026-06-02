"""Read chapter content from the study project for video generation."""

from pathlib import Path
import re
import config


EXAM_DIRS = {
    "neet": config.STUDY_PROJECT / "neet" / "chapters",
    "upsc": config.STUDY_PROJECT / "upsc" / "chapters",
    "jee": config.STUDY_PROJECT / "jee" / "chapters",
}


def list_chapters(exam: str = "neet") -> list[dict]:
    ch_dir = EXAM_DIRS.get(exam)
    if not ch_dir or not ch_dir.exists():
        return []
    chapters = []
    for f in sorted(ch_dir.glob("*.html")):
        title = _extract_title(f)
        if title:
            chapters.append({
                "exam": exam,
                "file": str(f),
                "title": title,
                "filename": f.stem,
            })
    return chapters


def _extract_title(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<h1>(.*?)</h1>", text, re.DOTALL)
    if m:
        clean = re.sub(r"<[^>]+>", "", m.group(1))
        clean = clean.replace("&mdash;", "-").replace("&amp;", "&")
        return clean.strip()
    return html_path.stem.replace("-", " ").title()


def get_chapter_questions(html_path: Path) -> list[dict]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    questions = []

    esc = r'(?:[^"\\]|\\.)*'

    pattern = re.compile(
        r'"id":(\d+),'
        r'"text":"(' + esc + r')",'
        r'"topic":"(' + esc + r')",'
        r'"opts":\[(.*?)\],'
        r'"sol":"(' + esc + r')"'
    )
    for m in pattern.finditer(text):
        def clean(s):
            return s.replace("\\u0026", "&").replace("\\n", " ").replace('\\"', '"')

        qid = int(m.group(1))
        qtext = clean(m.group(2))
        topic = clean(m.group(3))
        opts_raw = m.group(4)
        sol = clean(m.group(5))

        options = []
        opt_pattern = re.compile(r'\{"l":"([^"]*)","t":"((?:[^"\\]|\\.)*)"(,"c":true)?\}')
        for om in opt_pattern.finditer(f"[{opts_raw}]"):
            options.append({
                "label": om.group(1),
                "text": clean(om.group(2)),
                "correct": bool(om.group(3)),
            })
        questions.append({
            "id": qid,
            "text": qtext,
            "topic": topic,
            "options": options,
            "solution": sol,
        })
    return questions


def extract_concepts(html_path: Path) -> list[dict]:
    questions = get_chapter_questions(html_path)
    topics_seen = set()
    concepts = []
    for q in questions:
        topic = q["topic"]
        if topic and topic not in topics_seen:
            topics_seen.add(topic)
            correct_answer = next((o["text"] for o in q["options"] if o["correct"]), "")
            concepts.append({
                "title": topic,
                "explanation": q["solution"],
                "example": correct_answer,
            })
    return concepts


def _extract_chapter_number(filename: str) -> int:
    m = re.search(r'chapter[_-](\d+)', filename)
    return int(m.group(1)) if m else 0


def _extract_description(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<div class="sub">(.*?)</div>', text, re.DOTALL)
    if m:
        clean = re.sub(r"<[^>]+>", "", m.group(1))
        return clean.strip()
    return ""


def get_chapter_info(exam: str = "neet", chapter_number: int = 1) -> dict | None:
    chapters = list_chapters(exam)
    for ch in chapters:
        if _extract_chapter_number(ch["filename"]) == chapter_number:
            html_path = Path(ch["file"])
            concepts = extract_concepts(html_path)
            return {
                "exam": exam,
                "title": ch["title"],
                "filename": ch["filename"],
                "concepts": concepts,
                "description": _extract_description(html_path),
                "question_count": len(get_chapter_questions(html_path)),
            }
    return None
