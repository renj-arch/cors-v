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
                "max_tokens": 8192,
            },
            timeout=180,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"  LLM API error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  LLM call failed: {e}")
    return ""


def generate_lecture_scenes(chapter_title: str, topic_keywords: str, concepts: list[dict]) -> list[dict]:
    system = (
        "You are India's best exam teacher. Students love you because you make "
        "difficult topics feel like a fun conversation. "
        "Generate a lecture as a JSON array of scenes. "
        "Each scene: {type, heading, bullets, dialogue, image_prompt}. "
        "Types: hook, intro, explain, example, demo, summary, cta. "
        "bullets: 2-4 key points as comma-separated string. "
        "dialogue: 60-100 words of conversational Hinglish teaching. "
        "NEVER use generic sentences like 'Let me explain' or 'This is important'. "
        "Instead, teach the actual content with specific examples and analogies. "
        "image_prompt: short visual description (no teacher, use diagrams/icons). "
        "Return ONLY valid JSON array, no markdown."
    )

    concepts_text = "\n".join(
        f"- {c['title']}: {c['explanation'][:400]}"
        for c in concepts
    )

    prompt = (
        f"Create an animated lecture for '{chapter_title}'.\n\n"
        f"Teach these concepts:\n{concepts_text}\n\n"
        "RULES:\n"
        "- Each explain scene must teach ONE concept with real example + exam trick\n"
        "- Dialogues must be UNIQUE for each concept — never repeat phrases\n"
        "- Use Hinglish: mix Hindi and English naturally\n"
        "- Teach like a friendly Indian teacher: 'Beta dekho', 'Yaad rakho', 'Simple hai na'\n"
        "- Include common student mistakes and how to avoid them\n"
        "- Give memory tricks specific to each concept\n\n"
        "Structure (5-7 scenes total):\n"
        "1. HOOK: A 'sochiye' question or surprising fact\n"
        "2. INTRO: What we'll learn, why it matters\n"
        "3. EXPLAIN (one scene per concept): teach with example + trick\n"
        "4. SUMMARY: quick recap of all concepts\n"
        "5. CTA: subscribe, comment what to cover next\n\n"
        "IMPORTANT: Every dialogue must teach REAL content, not generic filler."
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
        "type": "hook",
        "heading": "Did You Know?",
        "bullets": "Interesting fact, Why it matters for exam, What we will learn today",
        "dialogue": (
            f"Hello students! Do you know that {chapter_title} is one of the most important topics "
            f"for your exam? Every year, 2-3 questions come from this topic. "
            f"In this video, I will explain everything step by step in simple words. "
            f"By the end, you will understand this topic completely. Let's start!"
        ),
        "image_prompt": "animated brain with question mark, colorful infographic icons, 16:9",
    })
    scenes.append({
        "type": "intro",
        "heading": chapter_title[:60],
        "bullets": "What is this topic, Why it is important, What we will cover",
        "dialogue": (
            f"Today we are going to learn about {chapter_title}. "
            f"This topic is very important for competitive exams. "
            f"First, we will understand the basic concepts. "
            f"Then we will see examples from daily life. "
            f"After that, I will show you some exam-style questions. "
            f"And finally, we will do a quick revision. "
            f"Are you ready? Let's begin!"
        ),
        "image_prompt": "animated topic banner with icons, school classroom theme, infographic, 16:9",
    })
    for c in concepts:
        expl = c["explanation"].strip()
        example_text = c.get("example", "").strip()
        dialogue_parts = [f"Let us understand {c['title']}."]
        if expl:
            dialogue_parts.append(expl)
        if example_text and example_text != expl:
            dialogue_parts.append(f"For example: {example_text}")
        dialogue_parts.append("This concept is important for your exam. Make sure you remember it well.")
        dialogue = " ".join(dialogue_parts)
        scenes.append({
            "type": "explain",
            "heading": c["title"][:50],
            "bullets": f"Definition, Example, Key point",
            "dialogue": dialogue,
            "image_prompt": f"animated infographic explaining {c['title'][:30]}, colorful diagram with icons, 16:9",
        })
    concept_summary = ", ".join(c["title"][:30] for c in concepts[:5])
    scenes.append({
        "type": "summary",
        "heading": "Quick Revision",
        "bullets": concept_summary if concept_summary else "Key points, Important concepts",
        "dialogue": (
            "Let's quickly revise what we learned today. "
            + ("We covered: " + concept_summary + ". " if concept_summary else "")
            + "Please review these concepts regularly to keep them fresh in your memory. "
            "If you have any doubts, feel free to ask in the comments section. "
            "Keep studying hard and you will definitely succeed!"
        ),
        "image_prompt": "animated summary board with bullet points, revision chart, colorful icons, 16:9",
    })
    scenes.append({
        "type": "cta",
        "heading": "Subscribe for More",
        "bullets": "Subscribe, Share with friends, Comment your doubt",
        "dialogue": (
            "I hope this lesson helped you understand the topic better. "
            "If you found this useful, please like and subscribe to the channel. "
            "Share this video with your friends who are also preparing for exams. "
            "Let me know in the comments which topic you want me to cover next. "
            "Thank you for watching! Keep learning, keep growing!"
        ),
        "image_prompt": "animated subscribe button with bell icon, colorful call to action, 16:9",
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
