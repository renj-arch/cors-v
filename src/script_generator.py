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
    hook_variations = [
        f"Aaj hum padhenge {chapter_title}. Yeh topic exams ke liye bahut important hai. Chaliye shuru karte hain!",
        f"Lagta hai {chapter_title} mushkil hai? Bilkul nahi! Main aaj aapko itna simple tarike se samjhaunga ki aapko yeh topic hamesha yaad rahega.",
        f"Kya aap jaante hain ki {chapter_title} se har saal 2-3 sawaal aate hain? Is video mein main aapko har concept ko example ke saath samjhaunga.",
    ]
    import random
    hook = random.choice(hook_variations)
    scenes.append({
        "type": "hook",
        "heading": "Aaj Kya Seekhenge?",
        "bullets": "Important topic for exam, Easy explanation with examples, Step by step learning",
        "dialogue": hook,
        "image_prompt": "animated intro with topic title, colorful educational icons, 16:9",
    })
    scenes.append({
        "type": "intro",
        "heading": chapter_title[:60],
        "bullets": "What we will cover, Why it matters, Real life connection",
        "dialogue": (
            f"Chaliye samajhte hain {chapter_title} ko detail mein. "
            f"Main har concept ko tod-tod ke samjhaunga - pehle basic definition, "
            f"phir ek simple example, phir exam mein kaise aata hai. "
            f"Beech mein main kuch common mistakes bhi bataunga jo students karte hain. "
            f"Dhyan se suniye aur mere saath chaliye!"
        ),
        "image_prompt": "animated chapter roadmap with numbered steps, infographic style, 16:9",
    })
    explanations = [
        "Samajhiye, {title} ka matlab hai {explanation[:200]}. Isko aise samjho jaise aap roz apni zindagi mein karte hain. Jab aap {example}, tab aap asal mein {title} ka use kar rahe hote hain. Exam mein yeh sawaal aata hai toh aapko bas {title} ka concept apply karna hai. Simple hai na?",
        "{title} ko samajhne ke liye pehle iska basic samajhte hain. {explanation[:200]}. Ab main aapko ek real life example deta hoon. Maan lijiye aap {example} - yahi hai {title}. Exam mein yeh concept kaise aata hai? Aksar woh aise sawaal puchte hain jahan aapko {title} identify karke answer dena hota hai. Ekdum simple!",
        "Beta, {title} sunke aapko mushkil lagega, lekin main aapko itna simple bana dunga ki kabhi nahi bhoolenge. {explanation[:200]}. Real life mein iska matlab hai {example}. Exam mein yeh concept usually 2-3 marks ka aata hai. Bas itna yaad rakhein: {title} ka matlab {example} jaisa situation hota hai.",
        "{title}: Yeh concept thoda tricky hai, isliye main dhyaan se samjhaunga. {explanation[:200]}. Iska sabse simple example hai - {example}. Jaise aap yeh roz karte hain, waise hi exam mein bhi apply karna hai. Meri trick: is concept ko apni favourite cheez se relate karein, phir kabhi nahi bhoolenge!",
        "Aaj ka pehla concept hai {title}. Yeh kya hai? {explanation[:200]}. Chaliye ek example lete hain: {example}. Dekha kitna simple hai? Exam mein jab bhi aisa sawaal aaye, aapko bas {title} ka rule yaad rakhna hai. Main aapko shortcut batata hoon: {title} ko do minute mein yaad karne ka tareeka hai - bas isko {example} se relate karein!",
    ]
    for i, c in enumerate(concepts):
        expl = c["explanation"][:400]
        example = c.get("example", "") or expl[:100]
        dia = explanations[i % len(explanations)].format(title=c["title"][:40], explanation=expl, example=example[:100])
        scenes.append({
            "type": "explain",
            "heading": c["title"][:50],
            "bullets": f"Simple definition, Real life example, Exam trick",
            "dialogue": dia,
            "image_prompt": f"animated diagram explaining {c['title'][:30]}, colorful icons, step by step infographic, 16:9",
        })
    scenes.append({
        "type": "demo",
        "heading": "Ab Aapki Baari! Exam Question",
        "bullets": "Sawaal, Sochiye aur jawab dijiye, Step by step solution",
        "dialogue": (
            "Ab main aapko ek exam-style question dunga. Pehle aap khud sochiye, phir main solution bataunga. "
            "Sawaal yeh hai: inn concepts mein se kaunsa sahi hai? Rukein, sochiye... "
            "Sahi jawab hai - jo concept humne abhi padha, wahi yahan apply hoga. "
            "Dekha? Agar aapne concepts acche se samajh liye, toh exam ke sawaal bahut easy lagte hain. "
            "Bas practice karte rahiye!"
        ),
        "image_prompt": "animated question and answer board with check marks, exam practice theme, 16:9",
    })
    concept_names = [c["title"][:30] for c in concepts[:4]]
    scenes.append({
        "type": "summary",
        "heading": "Aaj Humne Kya Seekha?",
        "bullets": ", ".join(concept_names) if concept_names else "Quick revision, Key points",
        "dialogue": (
            "Chaliye jaldi se repeat karte hain aaj ka poora lesson. "
            + "Humne seekha: " + ", ".join(concept_names) + ". "
            "Yaad rakhiye - har concept ko real life se jodkar padhenge toh kabhi nahi bhoolenge. "
            "Jo maine aapko tricks batayi hain, woh exam mein bahut kaam aayengi. "
            "Agar koi doubt ho toh comment mein zaroor bataiye. "
            "Main har comment padhta hoon aur naye videos banata hoon aapke sawaalon ke hisaab se!"
        ),
        "image_prompt": "animated revision board with bullet points, summary chart with icons, 16:9",
    })
    scenes.append({
        "type": "cta",
        "heading": "Subscribe Karna Mat Bhoolna!",
        "bullets": "Subscribe to channel, Share with friends, Comment your topic request",
        "dialogue": (
            "Agar aaj ka video aapko helpful laga toh LIKE karein aur channel ko SUBSCRIBE karein. "
            "Yeh bahut chhoti si cheez hai jo mujhe aur achhe videos banane ke liye motivate karti hai. "
            "Apne doston ke saath bhi share karein jo exam ki tayyari kar rahe hain. "
            "Aur haan, comments mein batao ki aapkaunsa topic next chahate hain. "
            "Main har request padhta hoon aur usi hisaab se videos banata hoon. "
            "Thank you for watching! Keep learning, keep growing! Jai Hind!"
        ),
        "image_prompt": "animated subscribe button with bell icon and subscriber count, colorful call to action, 16:9",
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
