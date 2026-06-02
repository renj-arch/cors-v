"""Generates detailed lecture scripts from chapter concepts — no LLM required."""

import config


def generate_lecture_scenes(chapter_title: str, topic_keywords: str, concepts: list[dict]) -> list[dict]:
    return _build_detailed_lecture(chapter_title, concepts)


def _build_detailed_lecture(chapter_title: str, concepts: list[dict]) -> list[dict]:
    scenes = []

    title_clean = chapter_title.replace(" - MCQ with Answers", "").replace("&mdash;", "-")
    scenes.append({
        "type": "intro",
        "heading": title_clean[:60],
        "bullets": "Welcome, What we'll learn today, Step by step explanation, Exam-focused",
        "dialogue": (
            f"Hello students, and welcome to this animated lecture. "
            f"Today we're going to learn about {title_clean}. "
            f"This is one of the most important topics for your exam preparation. "
            f"We'll cover everything step by step, from the basics to the key details you need to remember. "
            f"By the end of this video, you'll have a clear understanding of all the key concepts. "
            f"Let's begin!"
        ),
        "image_prompt": "friendly teacher at blackboard welcoming students, classroom, warm lighting, 16:9, cartoon style",
    })

    groups = _group_concepts(concepts)

    for group_name, group_concepts in groups:
        if not group_concepts:
            continue

        if group_name != "default":
            names = ", ".join(c["title"] for c in group_concepts)
            scenes.append({
                "type": "explain",
                "heading": group_name[:50],
                "bullets": names,
                "dialogue": f"Now let's move on to {group_name}. We'll cover {names}. Pay close attention to these concepts.",
                "image_prompt": f"teacher pointing at board with {group_name} diagram, educational, 16:9, cartoon style",
            })

        for c in group_concepts:
            title = c["title"]
            expl = c["explanation"][:300].replace('"', "").replace("'", "")
            example = c.get("example", "")
            if example:
                example = example.replace('"', "").replace("'", "")

            dialogue = _build_concept_dialogue(title, expl, example, group_name)
            bullet = expl if len(expl) < 150 else expl[:147] + "..."

            scenes.append({
                "type": "explain",
                "heading": title[:40],
                "bullets": bullet,
                "dialogue": dialogue,
                "image_prompt": f"educational diagram explaining {title}, teacher pointing, cartoon style, classroom board, 16:9",
            })

    concept_names = " • ".join(c["title"] for c in concepts[:8])
    scenes.append({
        "type": "summary",
        "heading": "Key Takeaways",
        "bullets": concept_names,
        "dialogue": (
            "Great work, students! Let's quickly recap what we learned today. "
            + "We covered " + ", ".join(c["title"] for c in concepts[:5]) + ", "
            + "and several other important concepts. "
            + "Remember to review these topics regularly for your exams. "
            + "If you found this helpful, please subscribe for more animated lectures. "
            + "Keep studying and keep learning!"
        ),
        "image_prompt": "teacher with summary board listing key points, classroom, warm encouraging smile, 16:9, cartoon style",
    })

    return scenes


def _group_concepts(concepts: list[dict]) -> list[tuple[str, list[dict]]]:
    groups = []

    cell_theory = [c for c in concepts if "theory" in c["title"].lower()]
    if cell_theory:
        groups.append(("Cell Theory - The Foundation", cell_theory))

    prokaryotic = [c for c in concepts if "prokary" in c["title"].lower()]
    if prokaryotic:
        groups.append(("Prokaryotic vs Eukaryotic Cells", prokaryotic))

    membrane_organelles_titles = {"Nucleus", "Mitochondria", "Chloroplast", "ER", "Golgi", "Lysosomes", "Peroxisomes"}
    membrane = [c for c in concepts if c["title"] in membrane_organelles_titles]
    if membrane:
        groups.append(("Membrane-Bound Organelles", membrane))

    non_membrane_titles = {"Ribosomes", "Centrosome", "Cilia/Flagella", "Cytoskeleton"}
    non_membrane = [c for c in concepts if c["title"] in non_membrane_titles]
    if non_membrane:
        groups.append(("Non-Membrane Structures", non_membrane))

    plant_titles = {"Cell Wall", "Vacuole"}
    plant = [c for c in concepts if c["title"] in plant_titles]
    if plant:
        groups.append(("Plant Cell Special Features", plant))

    used = set()
    for _, gc in groups:
        for c in gc:
            used.add(c["title"])

    remaining = [c for c in concepts if c["title"] not in used]
    if remaining:
        groups.append(("default", remaining))

    return groups


def _build_concept_dialogue(title: str, explanation: str, example: str, group: str) -> str:
    parts = [f"Now let's understand {title} in detail."]

    if explanation:
        parts.append(explanation)

    extras = {
        "cell theory": [
            "This is the fundamental concept of biology. Every living organism is made of one or more cells.",
            "The cell is the basic structural and functional unit of life. All cells arise from pre-existing cells.",
            "This theory was developed by Schleiden, Schwann, and later Virchow. It forms the foundation of modern biology.",
        ],
        "prokary": [
            "Prokaryotic cells are simpler and smaller in size. They lack a true nucleus and membrane-bound organelles.",
            "Examples include bacteria and archaea. Their DNA floats freely in the cytoplasm in a region called the nucleoid.",
            "Eukaryotic cells on the other hand are larger and more complex. They have a true nucleus enclosed by a nuclear membrane.",
            "Eukaryotes include plants, animals, fungi, and protists. This is a key difference you must remember for your exams.",
        ],
        "nucleus": [
            "Think of the nucleus as the brain or control center of the cell. It stores all the genetic material in the form of DNA.",
            "The nucleus is enclosed by a double membrane called the nuclear envelope. This envelope has pores that allow material to move in and out.",
            "Inside the nucleus you will find the nucleolus which is responsible for making ribosomes. The nucleus also contains chromatin which condenses into chromosomes during cell division.",
        ],
        "mitochondria": [
            "Mitochondria are called the powerhouse of the cell. Their main job is to produce energy in the form of ATP through a process called cellular respiration.",
            "They have a double membrane structure. The inner membrane folds into structures called cristae which increase surface area for energy production.",
            "Interestingly mitochondria have their own DNA and ribosomes. This suggests they once lived independently before being engulfed by larger cells. This is called the endosymbiotic theory.",
        ],
        "chloroplast": [
            "Chloroplasts are found only in plant cells and some algae. They are responsible for photosynthesis which is how plants make their food.",
            "Like mitochondria they also have a double membrane. Inside they have stacks of disc-like structures called thylakoids which contain the green pigment chlorophyll.",
            "Chloroplasts capture sunlight and convert it into chemical energy in the form of glucose. This process releases oxygen as a byproduct which is essential for all life on Earth.",
        ],
        "er": [
            "The endoplasmic reticulum or ER is a network of membranes throughout the cytoplasm. It comes in two types: Rough ER and Smooth ER.",
            "Rough ER has ribosomes attached to its surface making it look bumpy. It is involved in protein synthesis and processing. The ribosomes on rough ER make proteins that are either secreted from the cell or incorporated into membranes.",
            "Smooth ER does not have ribosomes. It is involved in lipid synthesis including steroids and phospholipids. It also helps in detoxification of drugs and toxins.",
        ],
        "golgi": [
            "The Golgi apparatus is named after the scientist Camillo Golgi. Think of it as the packaging and shipping center of the cell.",
            "It consists of stacked membrane-bound sacs called cisternae. Proteins from the ER arrive at the Golgi where they are modified sorted and packaged.",
            "The Golgi apparatus also forms lysosomes and is involved in the secretion of substances like hormones and enzymes out of the cell.",
        ],
        "lysosome": [
            "Lysosomes are the recycling and waste disposal system of the cell. They contain powerful digestive enzymes called acid hydrolases.",
            "These enzymes break down worn out organelles bacteria and other foreign materials. They work best in acidic conditions which the lysosome maintains.",
            "If a lysosome bursts it can digest the entire cell. This is why they are sometimes called the suicide bags of the cell. They also play a role in programmed cell death or apoptosis.",
        ],
        "ribosome": [
            "Ribosomes are the protein factories of the cell. They are made of ribosomal RNA or rRNA and proteins.",
            "Ribosomes can be found floating freely in the cytoplasm or attached to the rough endoplasmic reticulum. Free ribosomes make proteins for use inside the cell while bound ribosomes make proteins for export.",
            "Ribosomes read the genetic instructions from messenger RNA and link amino acids together to form proteins. This process is called translation.",
        ],
        "centro": [
            "Centrosomes are important for cell division. Each centrosome contains two centrioles arranged perpendicular to each other.",
            "Centrioles have a unique structure with nine triplets of microtubules arranged in a cylindrical pattern. This is called the 9 plus 0 arrangement.",
            "During cell division centrosomes move to opposite poles of the cell and help form the spindle fibers. These spindle fibers attach to chromosomes and pull them apart.",
        ],
        "cilia": [
            "Cilia and flagella are hair like projections from the cell surface that help in movement. Cilia are short and numerous while flagella are long and usually just one or two per cell.",
            "Both have the same internal structure called the 9 plus 2 arrangement. This means nine pairs of microtubules around the outside and two single microtubules in the center.",
            "Cilia can be found in the respiratory tract where they sweep mucus and trapped particles upward. Flagella are found in sperm cells where they help the sperm swim toward the egg.",
        ],
        "cytoskeleton": [
            "The cytoskeleton is the structural framework of the cell. It gives the cell its shape and provides mechanical support.",
            "It is made of three types of fibers: microfilaments made of actin, intermediate filaments, and microtubules made of tubulin.",
            "The cytoskeleton is also involved in cell movement and the transport of materials within the cell. For example during muscle contraction microfilaments slide past each other to shorten the muscle cell.",
        ],
        "wall": [
            "The cell wall is a rigid layer found outside the cell membrane in plant cells. It provides structural support and protection.",
            "Plant cell walls are made primarily of cellulose which is a polysaccharide. This makes them strong yet flexible.",
            "The middle lamella is the outermost layer of the cell wall. It is made of pectin and helps cement adjacent plant cells together. This is how plants maintain their structure without a skeleton.",
        ],
        "vacuole": [
            "Vacuoles are storage sacs within cells. Plant cells have a large central vacuole that takes up most of the cell volume.",
            "The vacuole is surrounded by a membrane called the tonoplast. It stores water nutrients and waste products.",
            "The central vacuole also maintains turgor pressure which keeps the plant cell firm. When a plant does not get enough water the vacuole shrinks and the plant wilts.",
        ],
        "peroxi": [
            "Peroxisomes are small membrane-bound organelles that contain enzymes for various metabolic reactions.",
            "They are particularly important for breaking down fatty acids and detoxifying harmful substances. The enzyme catalase breaks down hydrogen peroxide into water and oxygen.",
            "In plant cells peroxisomes are also involved in photorespiration which is a process that occurs during photosynthesis.",
        ],
    }

    for key, sentences in extras.items():
        if key in title.lower():
            parts.extend(sentences)
            break

    if not any(key in title.lower() for key in extras):
        parts.append("Make sure you understand this concept well as it is frequently asked in exams.")

    if example and example not in explanation:
        parts.append(f"A key example to remember is {example}.")
    else:
        parts.append("Remember this concept and practice related questions to strengthen your understanding.")

    return " ".join(parts)


def generate_lecture_dialogue(scenes: list[dict]) -> str:
    parts = []
    for s in scenes:
        d = s.get("dialogue", "") or s.get("heading", "")
        if d:
            parts.append(d)
    return " ".join(parts)


def generate_video_title(chapter_title: str, topic: str) -> str:
    clean = chapter_title.replace(" - MCQ with Answers", "").replace("&mdash;", "-")
    return f"{clean} | Complete Animated Lecture"[:100]
