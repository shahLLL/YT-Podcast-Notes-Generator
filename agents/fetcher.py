import os
import logging
import yt_dlp
from state import PodcastState

# Configure Logger
logging.basicConfig(level=logging.INFO)

# Fetcher Agent
def fetcher_agent(state: PodcastState) -> PodcastState:
    """
    Input:  state["youtube_url"]
    Output: state["audio_path"], state["metadata"]
    """
    url = state["youtube_url"]
    logging.info(f"[Fetcher] Downloading audio from: {url}")

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        audio_path = os.path.join(output_dir, f"{video_id}.mp3")

        metadata = {
            "title": info.get("title", "Unknown Title"),
            "description": info.get("description", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "upload_date": info.get("upload_date", ""),
            "video_id": video_id,
        }

    logging.info(f"[Fetcher] ✅ Audio saved to: {audio_path}")
    logging.info(f"[Fetcher] ✅ Metadata: title='{metadata['title']}', duration={metadata['duration']}s")

    return {
        **state,
        "audio_path": audio_path,
        "metadata": metadata,
    }
