import os
import logging
from datetime import datetime
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage
from state import PodcastState

# Configure Logger
logging.basicConfig(level=logging.INFO)

# Helper Functions
def _build_model() -> ChatHuggingFace:
    api_key = os.environ.get("HUGGING_FACE_API_KEY")

    llm = HuggingFaceEndpoint(
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        task="text-generation",
        temperature=0.5,
        max_new_tokens=1024,
        huggingfacehub_api_token=api_key,
    )
    return ChatHuggingFace(llm=llm)


def _build_chapter_markers(timestamps: list) -> str:
    """Convert Whisper segments into timestamped chapter markers every ~5 minutes."""
    if not timestamps:
        return "_No timestamps available._"

    markers = []
    last_added = -300

    for seg in timestamps:
        start = seg["start"]
        if start - last_added >= 300:
            minutes = int(start // 60)
            seconds = int(start % 60)
            markers.append(f"- `{minutes:02d}:{seconds:02d}` — {seg['text'][:80]}...")
            last_added = start

    return "\n".join(markers) if markers else "_No chapter markers generated._"

# Formatter Agent
def formatter_agent(state: PodcastState) -> PodcastState:
    """
    Input:  state["metadata"], state["transcript"], state["timestamps"], state["extracted"]
    Output: state["show_notes"], state["output_path"]
    """
    metadata = state["metadata"]
    transcript = state["transcript"]
    extracted = state["extracted"]
    timestamps = state.get("timestamps", [])

    logging.info("[Formatter] Calling Hugging Face API to write show notes...")

    topics_str = ", ".join(extracted.get("topics", [])) or "N/A"
    guests_str = ", ".join(extracted.get("guests", [])) or "None mentioned"
    quotes_str = "\n".join(f'- "{q}"' for q in extracted.get("quotes", [])) or "N/A"
    transcript_snippet = transcript[:3000]

    model = _build_model()

    prompt = f"""You are a professional podcast editor. Write a polished 2-3 sentence episode summary for the following podcast episode.

Episode title: {metadata['title']}
Host/Uploader: {metadata['uploader']}
Topics covered: {topics_str}
Guests: {guests_str}

Transcript excerpt:
{transcript_snippet}

Write ONLY the summary paragraph. No preamble, no labels."""

    response = model.invoke([HumanMessage(content=prompt)])
    summary = response.content.strip()

    # Build chapter markers from timestamps
    chapter_markers = _build_chapter_markers(timestamps)

    # Format upload date nicely
    raw_date = metadata.get("upload_date", "")
    try:
        upload_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%B %d, %Y")
    except ValueError:
        upload_date = raw_date or "Unknown"

    # Duration formatting
    duration_sec = metadata.get("duration", 0)
    duration_fmt = f"{duration_sec // 3600}h {(duration_sec % 3600) // 60}m" if duration_sec >= 3600 else f"{duration_sec // 60}m {duration_sec % 60}s"

    # Assemble final Markdown
    guests_section = ""
    if extracted.get("guests"):
        guest_lines = "\n".join(f"- **{g}**" for g in extracted["guests"])
        guests_section = f"\n## 👤 Guests\n{guest_lines}\n"

    show_notes = f"""# {metadata['title']}

> **Uploader:** {metadata['uploader']}  
> **Published:** {upload_date}  
> **Duration:** {duration_fmt}

---

## 📝 Episode Summary

{summary}

---

## 🗂️ Key Topics
{chr(10).join(f'- {t}' for t in extracted.get('topics', ['No topics extracted.']))}
{guests_section}
---

## 💬 Notable Quotes
{quotes_str}

---

## ⏱️ Chapter Markers
{chapter_markers}

---

*Show notes generated automatically by 🎥YT-Podcast-Notes-Generator (https://github.com/shahLLL/YT-Podcast-Notes-Generator#yt-podcast-notes-generator)*
"""

    # Write to disk
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    video_id = metadata.get("video_id", "episode")
    output_path = os.path.join(output_dir, f"{video_id}_shownotes.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(show_notes)

    logging.info(f"[Formatter] ✅ Show notes written to: {output_path}")

    return {
        **state,
        "show_notes": show_notes,
        "output_path": output_path,
    }
