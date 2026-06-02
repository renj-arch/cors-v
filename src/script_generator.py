"""Generates animated lecture scripts with scenes, teacher actions, and teaching flow."""

import config

SYSTEM_PROMPT = """You are an educational animated lecture script writer. Create engaging lecture scripts that teach concepts step-by-step with a friendly teacher character.

Each lecture should have:
1. INTRODUCTION — Hook the student, state what will be learned
2. EXPLAIN sections — Break down concepts one by one with clear explanations and examples
3. DIAGRAM descriptions — Describe visual aids that help understanding
4. SUMMARY — Recap key takeaways

Rules:
- Conversational, friendly tone like a real teacher
- Use simple language, explain jargon
- Include rhetorical questions
- Build concepts progressively
- End each section with a smooth transition to next
- Return ONLY the script text."""


def _generate_openai(prompt: str, temperature: float = 0.8, max_tokens: int = 2000, system: str = "") -> str:
    from openai import OpenAI
    base = config.OPENROUTER_BASE if config.LLM_PROVIDER == "openrouter" else None
    client = OpenAI(api_key=config.LLM_API_KEY, base_url=base, timeout=45)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    extra = {"max_tokens": max_tokens} if config.LLM_PROVIDER == "openrouter" else {}
    response = client.chat.completions.create(
        model=config.LLM_MODEL, messages=messages, max_tokens=max_tokens, temperature=temperature,
        extra_body=extra if config.LLM_PROVIDER == "openrouter" else None,
    )
    text = response.choices[0].message.content
    return text.strip() if text else ""


def _generate(prompt: str, temperature: float = 0.8, max_tokens: int = 2000, system: str = SYSTEM_PROMPT) -> str:
    return _generate_openai(prompt, temperature, max_tokens, system)


def generate_lecture_scenes(chapter_title: str, topic_keywords: str, concepts: list[dict]) -> list[dict]:
    """Generate lecture scenes. Falls back to template-based scenes if LLM unavailable."""
    names = " • ".join(c["title"] for c in concepts[:6])
    prompt = (
        f"Create an animated lecture script for: {chapter_title}\n"
        f"Topic keywords: {topic_keywords}\n"
        f"Concepts to cover: {names}\n\n"
        f"Write 6-8 scenes. Each scene should have:\n"
        f"---SCENE---\n"
        f"TYPE: intro / explain / diagram / summary\n"
        f"HEADING: short heading (max 8 words)\n"
        f"BULLETS: key points separated by commas\n"
        f"DIALOGUE: what the teacher says (2-3 sentences)\n"
        f"IMAGE: description for illustration\n\n"
        f"Start with an intro hook, explain each concept with examples, "
        f"include a diagram scene, end with summary."
    )

    try:
        raw = _generate(prompt, temperature=0.7, max_tokens=3000)
        scenes = _parse_scenes(raw)
        if scenes and len(scenes) >= 4:
            return scenes
    except:
        pass

    return _build_fallback_scenes(chapter_title, concepts)


def _parse_scenes(raw: str) -> list[dict]:
    scenes = []
    current = {}
    for line in raw.split("\n"):
        line = line.strip()
        if line == "---SCENE---":
            if current and current.get("heading"):
                scenes.append(current)
            current = {}
        elif line.upper().startswith("TYPE:"):
            current["type"] = line.split(":", 1)[-1].strip().lower()
        elif line.upper().startswith("HEADING:"):
            current["heading"] = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("BULLETS:"):
            current["bullets"] = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("DIALOGUE:"):
            current["dialogue"] = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("IMAGE:"):
            current["image_prompt"] = line.split(":", 1)[-1].strip()
    if current and current.get("heading"):
        scenes.append(current)
    return scenes


def _build_fallback_scenes(chapter_title: str, concepts: list[dict]) -> list[dict]:
    scenes = []
    scenes.append({
        "type": "intro",
        "heading": chapter_title[:60],
        "bullets": f"Let's learn about, {concepts[0]['title'] if concepts else 'this topic'}, Step by step explanation",
        "dialogue": f"Welcome students! Today we'll learn about {chapter_title}. Let's dive in!",
        "image_prompt": f"friendly teacher welcoming students, classroom, cartoon style, 16:9",
    })
    for c in concepts[:5]:
        scenes.append({
            "type": "explain",
            "heading": c["title"],
            "bullets": c["explanation"][:150],
            "dialogue": f"Let's understand {c['title']}. {c['explanation'][:150]}",
            "image_prompt": f"educational diagram explaining {c['title']}, cartoon style, teacher pointing, 16:9",
        })
    scenes.append({
        "type": "summary",
        "heading": "Key Takeaways",
        "bullets": " • ".join(c["title"] for c in concepts[:6]),
        "dialogue": "Let's recap what we learned today. " + ", ".join(c["title"] for c in concepts[:5]),
        "image_prompt": "teacher with summary board, classroom, warm lighting, 16:9",
    })
    return scenes


def generate_lecture_dialogue(scenes: list[dict]) -> str:
    parts = []
    for s in scenes:
        d = s.get("dialogue", "") or s.get("heading", "")
        if d:
            parts.append(d)
    return " ".join(parts)


def generate_video_title(chapter_title: str, topic: str) -> str:
    return f"{chapter_title} | Animated Lecture"[:100]
