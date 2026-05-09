from typing import TypedDict, Optional


class PodcastState(TypedDict):
    # --- Input ---
    youtube_url: str                  # The YouTube URL provided by the user

    # --- Agent 1: Fetcher ---
    audio_path: Optional[str]         # Local path to downloaded audio file
    metadata: Optional[dict]          # { title, description, duration, uploader, upload_date }

    # --- Agent 2: Transcriber ---
    transcript: Optional[str]         # Full transcript text from Whisper
    timestamps: Optional[list]        # List of Whisper segment dicts: { start, end, text }

    # --- Agent 3: Extractor ---
    extracted: Optional[dict]         # { topics: [...], guests: [...], quotes: [...] }

    # --- Agent 4: Formatter ---
    show_notes: Optional[str]         # Final Markdown-formatted show notes
    output_path: Optional[str]        # Path where the .md file was saved
