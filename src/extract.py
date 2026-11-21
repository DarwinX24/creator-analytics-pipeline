import json
import os
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")


def fetch_channel_videos(max_results=50):
    if not API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY in .env file.")
    if not CHANNEL_ID:
        raise ValueError("Missing CHANNEL_ID in .env file.")

    youtube = build("youtube", "v3", developerKey=API_KEY)

    # 1. Get the 'Uploads' playlist ID for the channel
    channel_res = (
        youtube.channels().list(part="contentDetails", id=CHANNEL_ID).execute()
    )
    items = channel_res.get("items", [])
    if not items:
        raise RuntimeError(f"No channel found for CHANNEL_ID={CHANNEL_ID}")

    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"][
        "uploads"
    ]

    # 2. Fetch recent video IDs from the uploads playlist
    playlist_res = (
        youtube.playlistItems()
        .list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=max_results,
        )
        .execute()
    )
    video_ids = [
        item["snippet"]["resourceId"]["videoId"]
        for item in playlist_res.get("items", [])
    ]

    if not video_ids:
        raise RuntimeError("No videos found in the uploads playlist.")

    # 3. Fetch detailed statistics for each video
    stats_res = (
        youtube.videos()
        .list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
        .execute()
    )

    # 4. Save raw JSON with timestamp
    os.makedirs("data/raw", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"data/raw/videos_{timestamp}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stats_res.get("items", []), f, indent=2)

    print(f"Extracted {len(stats_res.get('items', []))} videos to {filepath}")


if __name__ == "__main__":
    fetch_channel_videos()
