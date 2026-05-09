import whisper
import logging
from state import PodcastState

# Configure Logger
logging.basicConfig(level=logging.INFO)

# Transcriber Agent
def transcriber_agent(state: PodcastState) -> PodcastState:
    """
    Input:  state["audio_path"]
    Output: state["transcript"], state["timestamps"]
    """
    audio_path = state["audio_path"]
    logging.info(f"[Transcriber] Transcribing: {audio_path}")
    logging.info("[Transcriber] Loading Whisper model (base)... this may take a moment.")

    model = whisper.load_model("base")

    result = model.transcribe(audio_path, verbose=False)

    transcript = result["text"].strip()
    timestamps = [
        {
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        }
        for seg in result["segments"]
    ]

    logging.info(f"[Transcriber] ✅ Transcript length: {len(transcript)} characters")
    logging.info(f"[Transcriber] ✅ Segments: {len(timestamps)}")

    return {
        **state,
        "transcript": transcript,
        "timestamps": timestamps,
    }
