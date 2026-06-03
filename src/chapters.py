"""Read chapter content from the study project for video generation."""

from pathlib import Path
import re
import config
from bs4 import BeautifulSoup


EXAM_DIRS = {
    "neet": config.STUDY_PROJECT / "neet" / "chapters",
    "upsc": config.STUDY_PROJECT / "upsc" / "chapters",
    "jee": config.STUDY_PROJECT / "jee" / "chapters",
    "gate": config.STUDY_PROJECT / "gate" / "chapters",
    "ssc-gd": config.STUDY_PROJECT / "ssc-gd" / "chapters",
    "cgl": config.STUDY_PROJECT / "cgl" / "chapters",
    "ibps-po": config.STUDY_PROJECT / "ibps-po" / "chapters",
    "sbi-clerk": config.STUDY_PROJECT / "sbi-clerk" / "chapters",
    "rbi": config.STUDY_PROJECT / "rbi" / "chapters",
    "ctet": config.STUDY_PROJECT / "ctet" / "chapters",
    "agniveer": config.STUDY_PROJECT / "agniveer" / "chapters",
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
        # Strip leading "Chapter N: " prefix for matching with dropdown titles
        clean = re.sub(r'^Chapter\s+\d+[:\-.]\s*', '', clean).strip()
        return clean.strip()
    return html_path.stem.replace("-", " ").title()


def _clean_html_text(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def _parse_lesson_questions(soup: BeautifulSoup) -> list[dict]:
    """Parse questions from lesson page HTML (q-card elements)."""
    questions = []
    for card in soup.select(".q-card"):
        qid = len(questions)
        q_text_el = card.select_one(".q-text")
        q_text = _clean_html_text(q_text_el.get_text()) if q_text_el else ""

        topic_el = card.select_one(".q-topic")
        topic = _clean_html_text(topic_el.get_text()) if topic_el else ""

        sol_el = card.select_one(".q-soln")
        sol = _clean_html_text(sol_el.get_text()) if sol_el else ""
        sol = re.sub(r'^Answer[:\s]*', '', sol, flags=re.IGNORECASE).strip()

        options = []
        for opt in card.select(".q-opt"):
            label_el = opt.select_one(".opt-letter")
            label = _clean_html_text(label_el.get_text()) if label_el else ""
            text_el = opt.select_one(".opt-text")
            opt_text = _clean_html_text(text_el.get_text()) if text_el else ""
            correct = opt.get("data-correct") == "1"
            options.append({"label": label, "text": opt_text, "correct": correct})

        questions.append({
            "id": qid,
            "text": q_text,
            "topic": topic,
            "options": options,
            "solution": sol,
        })
    return questions


def _parse_json_questions(text: str) -> list[dict]:
    """Parse questions from old JSON format (var questions = [...] or var qs = [...])."""
    questions = []
    start = text.find("var questions = ")
    if start < 0:
        start = text.find("var qs = ")
    if start < 0:
        return questions

    start = text.index("[", start)
    depth = 0
    objs = []
    cur_start = None
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            if depth == 0:
                cur_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and cur_start is not None:
                objs.append(text[cur_start:i + 1])
                cur_start = None
        elif ch == "]" and depth == 0:
            break

    esc = r'(?:[^"\\]|\\.)*'

    for obj in objs:
        m = re.search(
            r'"id":\s*(\d+)\s*,'
            r'.*?"text":"(' + esc + r')",'
            r'.*?"topic":"(' + esc + r')",'
            r'.*?"(?:opts|options)":\s*\[(.*?)\]\s*,'
            r'.*?"sol":"(' + esc + r')"',
            obj, re.DOTALL
        )
        swapped = False
        if not m:
            m = re.search(
                r'"id":\s*(\d+)\s*,'
                r'.*?"topic":"(' + esc + r')",'
                r'.*?"text":"(' + esc + r')",'
                r'.*?"(?:opts|options)":\s*\[(.*?)\]\s*,'
                r'.*?"sol":"(' + esc + r')"',
                obj, re.DOTALL
            )
            swapped = True
        if not m:
            continue

        def _esc_clean(s):
            return s.replace("\\u0026", "&").replace("\\n", " ").replace('\\"', '"')

        qid = int(m.group(1))
        qtext_val = _esc_clean(m.group(3 if swapped else 2))
        topic = _esc_clean(m.group(2 if swapped else 3))
        opts_raw = m.group(4)
        sol = _esc_clean(m.group(5))

        options = []
        opt_pattern = re.compile(r'\{"l":"([^"]*)","t":"((?:[^"\\]|\\.)*)"(,"c":(?:true|false))?\}')
        for om in opt_pattern.finditer(f"[{opts_raw}]"):
            options.append({
                "label": om.group(1),
                "text": _esc_clean(om.group(2)),
                "correct": "true" in (om.group(3) or ""),
            })

        questions.append({
            "id": qid,
            "text": qtext_val,
            "topic": topic,
            "options": options,
            "solution": sol,
        })
    return questions


def get_chapter_questions(html_path: Path) -> list[dict]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    questions = _parse_lesson_questions(soup)
    if questions:
        return questions
    return _parse_json_questions(text)


def extract_concepts(html_path: Path) -> list[dict]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    concepts = []

    # Try lesson page format: sections → concepts
    sections = soup.select(".lesson-section")
    if sections:
        for sec in sections:
            h2 = sec.select_one(".lesson-h2")
            body = sec.select_one(".lesson-body")
            title = _clean_html_text(h2.get_text()) if h2 else ""
            explanation = _clean_html_text(body.get_text()) if body else ""
            if title and explanation:
                concepts.append({"title": title, "explanation": explanation, "example": ""})

        # Add examples as additional concepts
        for ex in soup.select(".ex-card"):
            q_el = ex.select_one(".ex-q")
            sol_el = ex.select_one(".ex-sol")
            if q_el and sol_el:
                q_text = _clean_html_text(q_el.get_text())
                sol_text = _clean_html_text(sol_el.get_text())
                title = re.sub(r'^(Example\s*\d*[:.]?\s*|Solution[:.]?\s*)', '', q_text, flags=re.IGNORECASE).strip()[:60]
                concepts.append({"title": f"Example: {title}", "explanation": sol_text, "example": q_text})

        # Add key points as one concept
        kp = soup.select_one(".key-points")
        if kp:
            points = [li.get_text(strip=True) for li in kp.select("li")]
            concepts.append({
                "title": "Key Points",
                "explanation": " ".join(points),
                "example": "",
            })

        return concepts

    # Fallback: extract from questions (old format)
    questions = get_chapter_questions(html_path)
    topics_seen = set()
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


def get_chapter_info(exam: str = "neet", chapter_number: int = 1, title: str = "") -> dict | None:
    chapters = list_chapters(exam)

    # If title is provided, match by title
    if title:
        def _normalize(s):
            return re.sub(r'\s+', ' ', s).lower().strip().replace('-', ' ').replace('\u2014', ' ').replace('–', ' ')
        target = _normalize(title)
        for ch in chapters:
            ch_norm = _normalize(ch["title"])
            if ch_norm == target or ch_norm.startswith(target) or target.startswith(ch_norm):
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
        # Fallback: try matching against filename stem
        for ch in chapters:
            fn_norm = ch["filename"].lower().replace('-', ' ').replace('_', ' ')
            if target in fn_norm or fn_norm in target:
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
        print(f"  Chapter '{title}' not found via title or filename match.")
        print(f"  Available chapters: {[ch['title'] for ch in chapters]}")
        return None

    # Try numeric filename match first (neet)
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
    # Fallback: use 1-based index (upsc/jee)
    if 1 <= chapter_number <= len(chapters):
        ch = chapters[chapter_number - 1]
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
