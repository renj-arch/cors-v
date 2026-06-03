"""Generate full-course lesson HTML pages with theory + practice questions using LLM."""

import sys, json, time, os, re
from pathlib import Path
import requests as req

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

STUDY = config.STUDY_PROJECT
DOLLAR = "$"

def llm(prompt, system=""):
    if not config.LLM_API_KEY:
        print("  No API key")
        return ""
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/renj-arch/cors-v",
        "X-Title": "Coursevi",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        r = req.post(
            f"{config.OPENROUTER_BASE}/chat/completions",
            headers=headers,
            json={"model": config.LLM_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 8192},
            timeout=180,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"  API error {r.status_code}")
    except Exception as e:
        print(f"  LLM error: {e}")
    return ""


COURSES = {
    "agniveer-reasoning": {
        "exam": "agniveer",
        "dir": "agniveer/chapters",
        "title": "Agniveer Reasoning",
        "badge": "Agniveer &middot; Reasoning",
        "chapters": [
            "Analogies - Verbal and Non-verbal",
            "Number Series, Letter Series & Alpha-Numeric Series",
            "Classification and Odd One Out",
            "Coding-Decoding",
            "Blood Relations and Family Trees",
            "Direction Sense and Distance",
            "Puzzles and Seating Arrangements",
            "Syllogisms and Statements",
        ],
    },
    "agniveer-mathematics": {
        "exam": "agniveer",
        "dir": "agniveer/chapters",
        "title": "Agniveer Mathematics",
        "badge": "Agniveer &middot; Mathematics",
        "chapters": [
            "Number System, LCM and HCF",
            "Percentage, Average and Ratio-Proportion",
            "Profit, Loss, Discount and Simple Interest",
            "Time, Work, Speed and Distance",
            "Algebra, Geometry and Mensuration",
            "Data Interpretation and Statistics",
        ],
    },
    "agniveer-science": {
        "exam": "agniveer",
        "dir": "agniveer/chapters",
        "title": "Agniveer Science",
        "badge": "Agniveer &middot; Science",
        "chapters": [
            "Physics - Motion, Force and Newton's Laws",
            "Physics - Work, Energy and Power",
            "Physics - Light, Sound and Electricity",
            "Chemistry - Atoms, Elements and Compounds",
            "Chemistry - Acids, Bases, Salts and Metals",
            "Biology - Cell, Tissues and Human Body Systems",
            "Biology - Nutrition, Health and Diseases",
            "Environmental Science and Ecology",
        ],
    },
    "agniveer-general-knowledge": {
        "exam": "agniveer",
        "dir": "agniveer/chapters",
        "title": "Agniveer General Knowledge",
        "badge": "Agniveer &middot; General Knowledge",
        "chapters": [
            "Indian History - Ancient and Medieval Periods",
            "Indian History - Modern India and Freedom Struggle",
            "Indian Geography - Physical Features",
            "Indian Geography - Economic and Social Geography",
            "Indian Polity - Constitution and Governance",
            "Indian Economy - Basics and Development",
            "Science and Technology Developments",
            "Sports, Awards, Honors and Current Affairs",
        ],
    },
}

def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:40]

def self_extract_json(text):
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None

def gen_chapter_html(course_key, course, ch_idx, ch_title, content):
    exam = course["exam"]
    chapters = course["chapters"]
    ch_num = ch_idx + 1
    prefix = f"{exam}-{course_key.split('-')[1]}"
    filename = f"{prefix}-chapter-{ch_num}-{_slug(ch_title)}.html"

    def ch_fn(i):
        return f"{prefix}-chapter-{i+1}-{_slug(chapters[i])}.html"

    ch_links = ""
    for i, ch in enumerate(chapters):
        active = "active" if i == ch_idx else ""
        ch_links += f'<a href="{ch_fn(i)}" class="{active}">Ch {i+1}</a>\n'

    desc = content.get("description", f"Complete lesson on {ch_title} with detailed theory, examples, and practice questions for Agniveer exam.")
    sections_html = ""
    for sec in content.get("sections", []):
        sections_html += f"""
            <div class="lesson-section">
                <h2 class="lesson-h2">{sec.get("heading", "")}</h2>
                <div class="lesson-body">{sec.get("body", "")}</div>
            </div>"""

    key_points = content.get("key_points", [])
    key_html = ""
    if key_points:
        key_html = """
            <div class="lesson-box key-points">
                <h3>Key Points to Remember</h3>
                <ul>""" + "".join(f"<li>{p}</li>" for p in key_points) + "</ul></div>"

    examples = content.get("examples", [])
    ex_html = ""
    if examples:
        ex_html = """
            <div class="lesson-box examples">
                <h3>Solved Examples</h3>""" + "".join(f'<div class="ex-card"><p class="ex-q"><strong>Example {i+1}:</strong> {ex.get("q","")}</p><p class="ex-sol"><strong>Solution:</strong> {ex.get("sol","")}</p></div>' for i, ex in enumerate(examples)) + "</div>"

    q_html = ""
    for qi, q in enumerate(content.get("questions", [])):
        opts_html = ""
        for oi, opt in enumerate(q.get("options", [])):
            letter = chr(65 + oi)
            correct_attr = ' data-correct="1"' if opt.get("correct") else ""
            opts_html += f'<div class="q-opt"{correct_attr} onclick="checkOpt(this,\'{letter}\')"><span class="opt-letter">{letter}.</span> <span class="opt-text">{opt.get("t","")}</span></div>\n'
        q_html += f"""
            <div class="q-card" data-q="{qi}">
                <div class="q-num"><span>Question {qi + 1}</span><span class="q-topic">{q.get("topic","")}</span></div>
                <div class="q-text">{q.get("text","")}</div>
                <div class="q-opts">{opts_html}</div>
                <div class="q-soln"><strong>Answer: {q.get("answer","")}</strong><br>{q.get("sol","")}</div>
            </div>"""

    prev_fn = ch_fn(ch_idx - 1) if ch_idx > 0 else ""
    next_fn = ch_fn(ch_idx + 1) if ch_idx < len(chapters) - 1 else ""

    nav_links = f'<a href="../../{exam}/index.html">Home</a><a href="../../dashboard.html">Dashboard</a><a href="../../{exam}/course/index.html" class="active">{course["title"]}</a>'

    h = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>{ch_title} — {course["title"]}</title>
    <meta name="description" content="{desc[:200]}">
    <link rel="icon" type="image/svg+xml" href="../../favicon.svg">
    <link rel="icon" type="image/png" href="../../logo.png">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:Inter,sans-serif;background:#09090b;color:#fafafa;min-height:100vh}}
        a{{color:#a78bfa;text-decoration:none}}
        .nav{{position:sticky;top:0;z-index:100;padding:14px 24px;background:rgba(9,9,11,.85);backdrop-filter:blur(16px);border-bottom:1px solid rgba(255,255,255,.06)}}
        .nav-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:16px}}
        .brand{{display:flex;align-items:center;gap:8px}}
        .brand-text{{font-weight:800;font-size:1.05em;background:linear-gradient(135deg,#a78bfa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
        .nav-links{{display:flex;gap:2px;flex-wrap:wrap}}
        .nav-links a{{padding:7px 14px;border-radius:100px;font-size:.82em;font-weight:500;color:#a1a1aa;transition:all .2s;white-space:nowrap}}
        .nav-links a:hover,.nav-links a.active{{color:#fafafa;background:rgba(255,255,255,.06)}}
        .container{{max-width:920px;margin:0 auto;padding:24px}}
        .ch-list{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px}}
        .ch-list a{{padding:6px 14px;border-radius:100px;font-size:.8em;border:1px solid rgba(255,255,255,.06);color:#a1a1aa;transition:all .2s}}
        .ch-list a:hover,.ch-list a.active{{border-color:#a78bfa;color:#a78bfa;background:rgba(167,139,250,.1)}}
        .header{{padding:20px 0;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:24px}}
        .header .badge{{display:inline-flex;padding:4px 12px;border-radius:100px;background:rgba(167,139,250,.12);color:#a78bfa;font-size:.75em;font-weight:600;margin-bottom:8px}}
        .header h1{{font-size:1.6em;font-weight:900;margin-bottom:6px;line-height:1.2}}
        .header .sub{{color:#a1a1aa;font-size:.9em;line-height:1.6}}
        .lesson-section{{margin-bottom:28px}}
        .lesson-h2{{font-size:1.2em;font-weight:700;color:#a78bfa;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,.06)}}
        .lesson-body{{font-size:.92em;line-height:1.8;color:#d4d4d8}}
        .lesson-body p{{margin-bottom:12px}}
        .lesson-body ul,.lesson-body ol{{margin:8px 0 12px 20px}}
        .lesson-body li{{margin-bottom:6px}}
        .lesson-box{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px;margin-bottom:24px}}
        .lesson-box h3{{font-size:1em;font-weight:700;color:#34d399;margin-bottom:10px}}
        .lesson-box ul{{list-style:none;padding:0}}
        .lesson-box ul li{{padding:6px 0;padding-left:20px;position:relative;font-size:.88em;color:#d4d4d8}}
        .lesson-box ul li::before{{content:"\\25B8";position:absolute;left:0;color:#34d399}}
        .ex-card{{background:rgba(255,255,255,.03);border-radius:8px;padding:14px;margin-bottom:10px}}
        .ex-q{{font-size:.9em;margin-bottom:6px;color:#fafafa}}
        .ex-sol{{font-size:.85em;color:#a1a1aa;line-height:1.5}}
        .q-card{{background:#111113;border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px;margin-bottom:12px}}
        .q-card .q-num{{font-size:.78em;color:#52525b;margin-bottom:4px;display:flex;justify-content:space-between}}
        .q-card .q-topic{{font-size:.7em;padding:2px 8px;border-radius:100px;background:rgba(167,139,250,.1);color:#a78bfa}}
        .q-card .q-text{{font-size:.93em;margin-bottom:10px;line-height:1.6;font-weight:500}}
        .q-card .q-opts{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
        @media(max-width:500px){{.q-card .q-opts{{grid-template-columns:1fr}}}}
        .q-card .q-opt{{padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.06);cursor:pointer;font-size:.82em;transition:all .15s;display:flex;align-items:center;gap:6px}}
        .q-card .q-opt:hover{{border-color:rgba(255,255,255,.15)}}
        .q-card .q-opt.correct{{border-color:#34d399;background:rgba(52,211,153,.1)}}
        .q-card .q-opt.wrong{{border-color:#ef4444;background:rgba(239,68,68,.1);color:#ef4444}}
        .q-card .q-opt .opt-letter{{color:#52525b;font-weight:600;min-width:16px}}
        .q-card .q-soln{{display:none;margin-top:10px;padding:10px;background:rgba(139,92,246,.06);border-radius:8px;font-size:.82em;color:#a1a1aa;line-height:1.5}}
        .q-card .q-soln.show{{display:block}}
        .q-card .q-soln strong{{color:#34d399}}
        .pn-links{{display:flex;justify-content:space-between;margin:24px 0;gap:12px}}
        .pn-links a{{padding:10px 20px;border-radius:100px;border:1px solid rgba(255,255,255,.06);font-size:.85em;transition:all .2s}}
        .pn-links a:hover{{border-color:#a78bfa;color:#a78bfa}}
        h3{{font-size:1.05em;font-weight:700;color:#fafafa;margin:20px 0 10px}}
        table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:.88em}}
        th,td{{padding:8px 12px;border:1px solid rgba(255,255,255,.06);text-align:left}}
        th{{background:rgba(167,139,250,.1);color:#a78bfa;font-weight:600}}
        td{{color:#d4d4d8}}
        code{{background:rgba(255,255,255,.04);padding:2px 6px;border-radius:4px;font-size:.9em;color:#34d399}}
    </style>
</head>
<body>
    <nav class="nav"><div class="nav-inner"><a href="../../index.html" class="brand"><span class="brand-text">vlymbooq</span></a><div class="nav-links">{nav_links}</div></div></nav>
    <div class="container">
        <div class="ch-list">{ch_links}</div>
        <div class="header">
            <div class="badge">{course["badge"]}</div>
            <h1>Chapter {ch_num}: {ch_title}</h1>
            <div class="sub">{desc}</div>
        </div>
        {sections_html}
        {key_html}
        {ex_html}
        <h3>Practice Questions</h3>
        {q_html}
        <div class="pn-links">
            {f'<a href="{prev_fn}">&larr; Previous</a>' if prev_fn else '<span></span>'}
            {f'<a href="{next_fn}">Next &rarr;</a>' if next_fn else '<span></span>'}
        </div>
    </div>
    <script>
    function checkOpt(el,ltr){{var p=el.closest('.q-card');if(p.dataset.locked)return;p.dataset.locked=1;var sol=p.querySelector('.q-soln');sol.classList.add('show');var opts=p.querySelectorAll('.q-opt');opts.forEach(function(o){{o.style.pointerEvents='none'}});if(el.dataset.correct){{el.classList.add('correct')}}else{{el.classList.add('wrong');opts.forEach(function(o){{if(o.dataset.correct)o.classList.add('correct')}})}}}}
    </script>
</body>
</html>"""
    return filename, h


def generate_course(course_key, course):
    chapters = course["chapters"]
    exam_dir = STUDY / course["dir"]
    exam_dir.mkdir(parents=True, exist_ok=True)

    for i, ch_title in enumerate(chapters):
        print(f"\n{'='*50}")
        print(f"  {course_key}: Chapter {i+1}/{len(chapters)} — {ch_title}")
        print(f"{'='*50}")

        sys_prompt = (
            "You are an expert exam teacher creating detailed lesson content for Agniveer (Indian Army) exam preparation. "
            "Generate comprehensive, accurate, and exam-focused content. "
            "Return ONLY valid JSON with no markdown wrapping."
        )

        title_trunc = ch_title[:30]
        prompt = (
            'Generate a complete lesson for Agniveer exam on the topic: "' + ch_title + '"\n\n'
            'Return JSON with this exact structure:\n'
            '{\n'
            '  "description": "2-3 sentence description of what this chapter covers",\n'
            '  "sections": [\n'
            '    {"heading": "Introduction", "body": "<p>intro paragraph here</p>"},\n'
            '    {"heading": "Section heading 1", "body": "<p>explanation with <strong>key terms</strong>. Use <ul><li>points</li></ul> where appropriate. Include formulas with <code>formula here</code>.</p>"},\n'
            '    {"heading": "Section heading 2", "body": "<p>more content</p>"}\n'
            '  ],\n'
            '  "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],\n'
            '  "examples": [\n'
            '    {"q": "Example question text", "sol": "Step by step solution explanation"},\n'
            '    {"q": "Another example", "sol": "Solution"}\n'
            '  ],\n'
            '  "questions": [\n'
            '    {"text": "MCQ question text", "options": [{"t": "Option A", "correct": false}, {"t": "Option B", "correct": true}], "answer": "B", "sol": "Explanation", "topic": "' + title_trunc + '"}\n'
            '  ]\n'
            '}\n\n'
            'Requirements:\n'
            '- 4-5 sections with detailed theory content\n'
            '- 5 key points\n'
            '- 3 solved examples with step-by-step solutions\n'
            '- 8-10 practice MCQs with 4 options each\n'
            '- Use simple HTML in body text (<p>, <ul>, <li>, <strong>, <code>, <table>)\n'
            '- Indian curriculum context\n'
            '- Exam-focused content'
        )

        raw = llm(prompt, sys_prompt)
        if not raw:
            print(f"  Failed to generate content for {ch_title}")
            continue

        content = self_extract_json(raw)
        if content is None:
            print(f"  JSON parse failed for {ch_title}, retrying...")
            raw2 = llm(prompt, sys_prompt)
            if raw2:
                content = self_extract_json(raw2)
            if content is None:
                print(f"  Skipping {ch_title}")
                continue

        filename, html = gen_chapter_html(course_key, course, i, ch_title, content)
        output_path = exam_dir / filename
        output_path.write_text(html, encoding="utf-8")
        print(f"  Written: {output_path.name}")

    print(f"\n  Course complete: {course_key} ({len(chapters)} chapters)")


if __name__ == "__main__":
    keys = list(COURSES.keys())
    if len(sys.argv) > 1:
        key = sys.argv[1]
        if key in COURSES:
            generate_course(key, COURSES[key])
        else:
            print(f"Unknown course. Options: {', '.join(keys)}")
    else:
        for key, course in COURSES.items():
            generate_course(key, course)
