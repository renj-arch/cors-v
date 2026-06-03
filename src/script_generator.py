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
        "You are an expert exam teacher creating an educational animation video for competitive exam preparation. "
        "Generate a structured lecture as a JSON array of scenes. "
        "Each scene is an object with keys: type, heading, bullets, dialogue, image_prompt. "
        "Types: hook (attention-grabbing opener), intro (topic overview), explain (teach a concept), demo (interesting fact/demonstration), summary (recap), cta (call to action). "
        "bullets is a comma-separated string of 2-4 key points. "
        "dialogue is the spoken narration (~40-80 words per scene, conversational, engaging, exam-focused). "
        "image_prompt is a short description for generating an illustration (~10 words, no teacher/character, use diagrams, icons, infographics, animations, visual examples). "
        "Return ONLY valid JSON, no markdown wrapping."
    )

    concepts_text = "\n".join(
        f"- {c['title']}: {c['explanation'][:200]}"
        for c in concepts
    )

    prompt = (
        f"Create an educational animation video for '{chapter_title}' ({topic_keywords}). "
        f"The video should be 8-12 minutes long.\n\n"
        f"Source concepts:\n{concepts_text}\n\n"
        "Structure the video as follows:\n"
        "1. HOOK (0-10s): Start with a surprising question or interesting fact that grabs attention. example: 'What if I told you your brain uses enough electricity to power a light bulb?'\n"
        "2. INTRO (10-20s): Explain what viewers will learn. Keep it simple and exciting.\n"
        "3. MAIN EXPLANATION (20s-3min+): Break the topic into small sections. Use visual examples, animated diagrams, icons, and step-by-step explanations.\n"
        "4. DEMO: Add a memorable example, interesting fact, or demonstration that keeps attention high.\n"
        "5. SUMMARY: Quick recap of key points in 2-3 sentences.\n"
        "6. CTA: Ask viewers to subscribe, comment, or watch another video.\n\n"
        "Style guidelines:\n"
        "- Clear 2D animated visuals with colorful graphics and animated text\n"
        "- Friendly teacher voice, military-themed educational design for Agniveer\n"
        "- Clean infographics, smooth transitions, highlighted key points\n"
        "- Step-by-step solving methods with exam-style examples\n"
        "- Common mistakes students make\n"
        "- Tricks and shortcuts for solving questions quickly\n"
        "- Engaging pacing suitable for beginners\n"
        "- Include practice questions with detailed solutions\n"
        "- NO visible teacher character on screen — use diagrams, icons, infographics only"
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
        "bullets": "Surprising fact, Why it matters, Stay tuned",
        "dialogue": (
            f"Did you know that mastering {chapter_title} can boost your exam score by up to 15%? "
            f"In this video, we will break down everything you need to know step by step."
        ),
        "image_prompt": "animated question mark with glowing brain, infographic, colorful, 16:9",
    })
    scenes.append({
        "type": "intro",
        "heading": chapter_title[:60],
        "bullets": "What we will cover, Key concepts, Exam tips",
        "dialogue": (
            f"Welcome to this lesson on {chapter_title}. "
            f"This is a frequently tested topic in competitive exams. "
            f"We will cover the fundamentals, solving techniques, and practice questions. "
            f"Let's dive in!"
        ),
        "image_prompt": "animated topic title with icons, colorful infographic, exam preparation theme",
    })
    for c in concepts:
        expl = c["explanation"][:300]
        scenes.append({
            "type": "explain",
            "heading": c["title"][:40],
            "bullets": expl[:150],
            "dialogue": (
                f"Let's understand {c['title']}. "
                f"{expl[:250]} "
                f"This concept is important for your exam preparation."
            ),
            "image_prompt": f"animated diagram showing {c['title']}, infographic, icons, visual explanation, 16:9",
        })
    scenes.append({
        "type": "demo",
        "heading": "Pro Tip",
        "bullets": "Common mistake, How to avoid, Shortcut method",
        "dialogue": (
            "Here is a pro tip: many students make mistakes in this topic by rushing. "
            "Take your time to understand each step. Practice with timer-based questions to improve speed."
        ),
        "image_prompt": "animated light bulb with tips, infographic, exam preparation theme",
    })
    scenes.append({
        "type": "summary",
        "heading": "Quick Recap",
        "bullets": ", ".join(c["title"] for c in concepts[:4]),
        "dialogue": (
            "Let's quickly recap what we learned: " +
            ", ".join(c["title"] for c in concepts[:3]) +
            f", and more. Review these topics regularly and practice questions. "
            f"Consistent practice is the key to success!"
        ),
        "image_prompt": "animated summary board with key points, infographic, icons, 16:9",
    })
    scenes.append({
        "type": "cta",
        "heading": "Subscribe for More",
        "bullets": "Like, Share, Subscribe, Comment",
        "dialogue": (
            "If you found this helpful, please like and subscribe for more exam preparation videos. "
            "Comment below which topic you want us to cover next. "
            "Keep studying and keep learning!"
        ),
        "image_prompt": "animated subscribe button with bell icon, colorful, call to action, 16:9",
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
