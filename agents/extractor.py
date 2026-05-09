import os
import json
import logging
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage
from state import PodcastState

# Configure Logger
logging.basicConfig(level=logging.INFO)

# Define Constants
CHUNK_SIZE = 4000     # characters per chunk
CHUNK_OVERLAP = 200   # overlap between chunks
MAX_QUOTES = 5        # cap on quotes kept after merging all chunks

# Helper Functions
def _build_model() -> ChatHuggingFace:
    api_key = os.environ.get("HUGGING_FACE_API_KEY")

    llm = HuggingFaceEndpoint(
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        task="text-generation",
        temperature=0.3,
        max_new_tokens=800,
        huggingfacehub_api_token=api_key,
    )
    return ChatHuggingFace(llm=llm)

def _chunk_transcript(transcript: str) -> list[str]:
    """Split transcript into overlapping chunks of CHUNK_SIZE characters."""
    chunks = []
    start = 0
    while start < len(transcript):
        end = start + CHUNK_SIZE
        chunks.append(transcript[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def _extract_from_chunk(model: ChatHuggingFace, chunk: str, chunk_num: int, total: int) -> dict:
    """Run extraction on a single chunk and return parsed dict."""
    logging.info(f"[Extractor] Processing chunk {chunk_num}/{total} ({len(chunk)} chars)...")
 
    prompt = f"""You are a podcast analyst. Given the transcript excerpt below, extract:
1. Key topics discussed (as a list of short phrases)
2. Guest names mentioned (list of names, or empty list if none)
3. Notable quotes (up to 3 verbatim quotes from this excerpt)
 
Respond ONLY with valid JSON in this exact format, no preamble, no markdown fences:
{{
  "topics": ["topic 1", "topic 2"],
  "guests": ["Guest Name"],
  "quotes": ["Quote one.", "Quote two."]
}}
 
Transcript excerpt:
{chunk}"""
 
    response = model.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
 
    try:
        clean = raw.strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logging.info(f"[Extractor] ⚠️  Could not parse JSON for chunk {chunk_num}. Raw output:\n{raw}")
        return {"topics": [], "guests": [], "quotes": []}

def _merge_results(results: list[dict]) -> dict:
    """
    Merge extraction results from all chunks.
    - Topics and guests: deduplicated by lowercased value
    - Quotes: deduplicated, capped at MAX_QUOTES
    """
    seen_topics = set()
    seen_guests = set()
    seen_quotes = set()
 
    merged_topics = []
    merged_guests = []
    merged_quotes = []
 
    for result in results:
        for topic in result.get("topics", []):
            key = topic.lower().strip()
            if key and key not in seen_topics:
                seen_topics.add(key)
                merged_topics.append(topic)
 
        for guest in result.get("guests", []):
            key = guest.lower().strip()
            if key and key not in seen_guests:
                seen_guests.add(key)
                merged_guests.append(guest)
 
        for quote in result.get("quotes", []):
            key = quote.lower().strip()
            if key and key not in seen_quotes and len(merged_quotes) < MAX_QUOTES:
                seen_quotes.add(key)
                merged_quotes.append(quote)
 
    return {
        "topics": merged_topics,
        "guests": merged_guests,
        "quotes": merged_quotes,
    }

# Extractor Agent
def extractor_agent(state: PodcastState) -> PodcastState:
    """
    Input:  state["transcript"]
    Output: state["extracted"] — { topics, guests, quotes }
    """
    transcript = state["transcript"]
    chunks = _chunk_transcript(transcript)
    total = len(chunks)
 
    logging.info(f"[Extractor] Transcript split into {total} chunk(s) of ~{CHUNK_SIZE} chars each.")
 
    model = _build_model()
 
    chunk_results = [
        _extract_from_chunk(model, chunk, i + 1, total)
        for i, chunk in enumerate(chunks)
    ]
 
    extracted = _merge_results(chunk_results)
 
    logging.info(f"[Extractor] ✅ Topics: {extracted['topics']}")
    logging.info(f"[Extractor] ✅ Guests: {extracted['guests']}")
    logging.info(f"[Extractor] ✅ Quotes: {len(extracted['quotes'])} found across {total} chunk(s)")
 
    return {
        **state,
        "extracted": extracted,
    }
