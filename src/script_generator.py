"""Generates detailed lecture scripts from chapter concepts using LLM."""

import json
import requests as req
import config


def _llm_complete(prompt: str, system: str = "") -> str:
    if not config.LLM_API_KEY:
        print("  No LLM API key configured")
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
            json={
                "model": config.LLM_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"  LLM API error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  LLM call failed: {e}")
    return ""


def generate_lecture_scenes(chapter_title: str, topic_keywords: str, concepts: list[dict]) -> list[dict]:
    system = (
        "You are an expert exam teacher creating an animated lecture video. "
        "Generate a structured lecture as a JSON array of scenes. "
        "Each scene is an object with keys: type, heading, bullets, dialogue, image_prompt. "
        "Types: intro (welcome + overview), explain (teach a concept), summary (recap). "
        "bullets is a comma-separated string of 2-4 key points. "
        "dialogue is natural spoken teaching (~40-80 words per scene, conversational, engaging). "
        "image_prompt is a short description for generating an illustration (~10 words, cartoon style, classroom). "
        "Return ONLY valid JSON, no markdown wrapping."
    )

    concepts_text = "\n".join(
        f"- {c['title']}: {c['explanation'][:200]}"
        for c in concepts
    )

    prompt = (
        f"Create an animated lecture for: {chapter_title}\n"
        f"Exam context keywords: {topic_keywords}\n\n"
        f"Concepts to cover:\n{concepts_text}\n\n"
        "Generate scenes: intro (welcome + what we'll learn), "
        f"one explain scene per concept ({len(concepts)} concepts), "
        "and a summary (key takeaways). "
        "Make the dialogue sound like a real teacher explaining clearly with examples."
    )

    raw = _llm_complete(prompt, system)
    if not raw:
        return _fallback_scenes(chapter_title, concepts)

    try:
        scenes = json.loads(raw)
        if isinstance(scenes, list) and len(scenes) > 1:
            return scenes
    except json.JSONDecodeError:
        pass

    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        scenes = json.loads(raw[start:end])
        if isinstance(scenes, list) and len(scenes) > 1:
            return scenes
    except (json.JSONDecodeError, ValueError):
        pass

    return _fallback_scenes(chapter_title, concepts)


def _fallback_scenes(chapter_title: str, concepts: list[dict]) -> list[dict]:
    scenes = []
    scenes.append({
        "type": "intro",
        "heading": chapter_title[:60],
        "bullets": "Welcome, What we'll learn today, Key concepts, Exam preparation",
        "dialogue": (
            f"Hello students! Welcome to this animated lecture on {chapter_title}. "
            f"This is an important topic for your exams. "
            f"We will go through each concept step by step with clear explanations. "
            f"Let's begin our learning journey!"
        ),
        "image_prompt": "friendly teacher at blackboard welcoming students, classroom, warm lighting, cartoon style",
    })
    for c in concepts:
        expl = c["explanation"][:300]
        scenes.append({
            "type": "explain",
            "heading": c["title"][:40],
            "bullets": expl[:150],
            "dialogue": (
                f"Now let's understand {c['title']}. "
                f"{expl[:250]} "
                f"Make sure you understand this concept well for your exam."
            ),
            "image_prompt": f"teacher explaining {c['title']}, educational diagram, classroom, cartoon style",
        })
    scenes.append({
        "type": "summary",
        "heading": "Key Takeaways",
        "bullets": ", ".join(c["title"] for c in concepts[:6]),
        "dialogue": (
            "Great work today! We covered " +
            ", ".join(c["title"] for c in concepts[:4]) +
            ", along with other important concepts. "
            "Review these topics regularly and practice questions to strengthen your understanding. "
            "Keep studying and keep learning!"
        ),
        "image_prompt": "teacher with summary board, classroom, encouraging smile, cartoon style",
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
    system = "Generate a short, engaging YouTube video title (max 80 chars). Return ONLY the title."
    prompt = (
        f"Create a YouTube title for an animated lecture about: {chapter_title}. "
        f"Topic keywords: {topic}. "
        f"Make it exam-focused and engaging."
    )
    raw = _llm_complete(prompt, system)
    if raw and len(raw) < 100:
        return raw
    clean = chapter_title.replace(" - MCQ with Answers", "").replace("&mdash;", "-")
    return f"{clean} | Complete Animated Lecture"[:100]
