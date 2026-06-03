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
        "You are the best exam teacher in India. You explain complex topics "
        "in simple words so even a beginner can understand. "
        "Generate a structured lecture as a JSON array of scenes. "
        "Each scene is an object with keys: type, heading, bullets, dialogue, image_prompt. "
        "Types: hook, intro, explain, example, demo, summary, cta. "
        "bullets is a comma-separated string of 2-4 key points. "
        "dialogue is spoken narration (60-120 words per scene). "
        "Write dialogue like a friendly teacher talking to a student. "
        "image_prompt is a short description for visual (no teacher character, use diagrams, icons). "
        "Return ONLY valid JSON, no markdown wrapping."
    )

    concepts_text = "\n".join(
        f"- {c['title']}: {c['explanation'][:400]}"
        for c in concepts
    )

    prompt = (
        f"Create a detailed animated lecture for '{chapter_title}' ({topic_keywords}).\n\n"
        f"Source concepts:\n{concepts_text}\n\n"
        "IMPORTANT GUIDELINES:\n"
        "- Explain like the student knows NOTHING about the topic\n"
        "- Use simple everyday examples and analogies\n"
        "- Break each concept into small, easy steps\n"
        "- Include real-life examples students can relate to\n"
        "- Point out common mistakes students make\n"
        "- Give memory tricks and shortcuts for exams\n"
        "- Each concept should have its own explain scene (6-12 scenes total)\n\n"
        "Structure:\n"
        "1. HOOK: Start with a 'imagine this' or 'did you know' question that grabs attention. Make it relatable.\n"
        "2. INTRO: What will we learn today? Why is this important for exams? Keep it exciting.\n"
        "3. EXPLAIN scenes (one per concept): Teach like a classroom teacher - step by step.\n"
        "   - First explain WHAT it is in simple words\n"
        "   - Then give an EXAMPLE from daily life\n"
        "   - Then explain WHY it works that way\n"
        "   - Finally give a MEMORY TRICK for exams\n"
        "4. DEMO or EXAMPLE: Show a practice question with step-by-step solution\n"
        "5. SUMMARY: Quick recap of everything learned in 3-4 simple points\n"
        "6. CTA: Subscribe for more. Ask what topic they want next.\n\n"
        "Style:\n"
        "- Use Hinglish (Hindi + English mix) for Indian students if helpful\n"
        "- Friendly, encouraging tone like 'Beta, yeh concept samajhna bahut easy hai'\n"
        "- Dialogue must be CONVERSATIONAL, not textbook-like\n"
        "- Each dialogue should be 60-120 words, complete sentences\n"
        "- Image prompts should describe simple infographic visuals\n"
        "- NO teacher character visible - use diagrams, icons, charts only"
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
        expl = c["explanation"][:400]
        scenes.append({
            "type": "explain",
            "heading": c["title"][:50],
            "bullets": f"Simple definition, Easy example, Key point to remember",
            "dialogue": (
                f"Let me explain {c['title']} in simple words. "
                f"{expl[:300]} "
                f"Let me give you an example from daily life to make it clear. "
                f"Think about it like this: {c['title']} is similar to something you already know. "
                f"This is a very important concept for your exam. "
                f"Remember this well because many questions are asked from here."
            ),
            "image_prompt": f"animated infographic explaining {c['title']}, colorful diagram with icons, step by step, 16:9",
        })
        scenes.append({
            "type": "example",
            "heading": f"Example: {c['title'][:35]}",
            "bullets": "Real life example, Step by step solution, Why this works",
            "dialogue": (
                f"Now let me show you an example to understand {c['title']} better. "
                f"Suppose you have a situation where this concept applies. "
                f"First, we identify what the question is asking. "
                f"Then we apply the rule step by step. "
                f"See how simple it is? Once you understand the basic idea, "
                f"you can solve any question on this topic. "
                f"Practice this concept with different examples to become perfect."
            ),
            "image_prompt": f"animated example problem with step by step solution, {c['title']}, educational diagram, 16:9",
        })
    scenes.append({
        "type": "demo",
        "heading": "Exam Practice Question",
        "bullets": "Question, Step by step solution, Answer with explanation",
        "dialogue": (
            "Now let's solve an exam-style question together. "
            "I will read the question, and you try to think of the answer. "
            "First, understand what the question is asking. "
            "Then apply the concept we just learned. "
            "Let me show you the step-by-step solution. "
            "See how easy it is when you break it down? "
            "This is exactly how questions appear in your exam. "
            "Practice more questions like this to improve your speed."
        ),
        "image_prompt": "animated question paper with pen and check marks, exam preparation theme, 16:9",
    })
    scenes.append({
        "type": "summary",
        "heading": "Quick Revision",
        "bullets": ", ".join(c["title"][:30] for c in concepts[:4]),
        "dialogue": (
            "Let's quickly revise what we learned today. "
            + "We understood: " + ", ".join(c["title"] for c in concepts[:3]) +
            ". " +
            "Remember the key points I taught you. "
            "Practice these concepts regularly. "
            "If you have any doubts, write in the comments. "
            "I will answer all your questions. "
            "Keep studying hard and you will definitely succeed!"
        ),
        "image_prompt": "animated summary board with bullet points, revision chart, colorful icons, 16:9",
    })
    scenes.append({
        "type": "cta",
        "heading": "Subscribe for More",
        "bullets": "Subscribe, Share with friends, Comment your doubt",
        "dialogue": (
            "I hope you enjoyed this lesson and learned something new. "
            "If this video helped you, please like and subscribe to our channel. "
            "Share this video with your friends who are also preparing for exams. "
            "Tell me in the comments which topic you want me to explain next. "
            "I read every comment and make videos based on your requests. "
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
