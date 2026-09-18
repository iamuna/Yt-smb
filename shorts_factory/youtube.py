from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .config import DATA_DIR

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
TOKEN_FILE = DATA_DIR / "youtube_token.json"


def _credentials(client_secrets_file: Path) -> Credentials:
    if not client_secrets_file.exists():
        raise RuntimeError("YouTube OAuth client secrets JSON file was not found.")

    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_file),
            SCOPES,
        )
        credentials = flow.run_local_server(port=0)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str,
    client_secrets_file: Path,
) -> str:
    if not video_path.exists():
        raise RuntimeError("Queued video file no longer exists.")

    credentials = _credentials(client_secrets_file)
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags[:15],
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            str(video_path),
            chunksize=8 * 1024 * 1024,
            resumable=True,
        ),
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = str(response.get("id") or "")
    if not video_id:
        raise RuntimeError("YouTube upload completed without a video ID.")
    return video_id
