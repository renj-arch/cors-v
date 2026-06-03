"""Upload educational video to YouTube via API v3 with SEO."""

import sys, os, json, pickle, random
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRET = "client_secret.json"
TOKEN_FILE = "token.pickle"

CATEGORIES = {
    "education": "27",
    "science_technology": "28",
}

DESCRIPTION_TEMPLATE = """📚 {title}

In this video, we explain {topic} concepts clearly and simply. Perfect for {exam} preparation.

⏱ TIMESTAMPS:
{timestamps}

📌 KEY CONCEPTS COVERED:
{concepts}

💡 Subscribe for more educational videos!
{channel_handle}
#education #{exam} #concept #explained #study"""


def get_service():
    creds = None
    if Path(TOKEN_FILE).exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def build_description(title: str, exam: str, slides: list[dict]) -> str:
    concepts = []
    timestamps = []
    for i, s in enumerate(slides):
        heading = s.get("heading", "")
        if heading:
            concepts.append(f"• {heading}")
            minutes = i // 2
            seconds = (i % 2) * 30
            timestamps.append(f"{minutes}:{seconds:02d} - {heading}")

    topic = slides[0].get("heading", "")[:60] if slides else title[:60]
    return DESCRIPTION_TEMPLATE.format(
        title=title,
        topic=topic,
        exam=exam.upper(),
        timestamps="\n".join(timestamps[:10]),
        concepts="\n".join(concepts[:10]),
        channel_handle="@vlymbooq",
    )


def generate_tags(exam: str, slides: list[dict]) -> list[str]:
    tags = [exam.upper(), "education", "concept", "explained", "study", "youtube education"]
    for s in slides[:5]:
        h = s.get("heading", "")
        if h:
            tags.append(h[:40])
    return tags


def upload(video_path: str, title: str = "", description: str = "",
           tags: list[str] = None, privacy: str = "public",
           made_for_kids: bool = False, exam: str = "neet",
           slides: list[dict] = None):
    youtube = get_service()

    if not description and slides:
        description = build_description(title, exam, slides)
    if not tags and slides:
        tags = generate_tags(exam, slides)
    if not title:
        title = "Concept Explained | Educational Video"
    if not description:
        description = f"Subscribe for more educational videos! @vlymbooq\n#education #{exam}"
    if not tags:
        tags = ["education", exam, "concept", "explained"]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    print(f"\n📤 Uploading: {title[:60]}...")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   {int(status.progress() * 100)}%")
    video_id = response["id"]
    print(f"✅ Uploaded! https://youtu.be/{video_id}")
    return video_id


if __name__ == "__main__":
    mp4s = sorted(Path("output").glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp4s:
        print("No MP4 files in output/")
        exit(1)
    video = str(mp4s[0])
    upload(
        video_path=video,
        title="Cell: The Unit of Life | NEET Biology Explained",
        description="Complete explanation of Cell Biology for NEET exam.\n#NEET #biology #cell",
        tags=["NEET", "biology", "cell", "education"],
        privacy="public",
    )
