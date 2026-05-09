import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logging.info("Running")

# Load Environment Variables
load_dotenv()

from langgraph.graph import StateGraph, END
from state import PodcastState
from agents.fetcher import fetcher_agent
from agents.transcriber import transcriber_agent
from agents.extractor import extractor_agent
from agents.formatter import formatter_agent

def build_graph() -> StateGraph:
    """Build and compile the linear 4-agent LangGraph pipeline."""
    graph = StateGraph(PodcastState)

    # Register nodes (each node = one agent function)
    graph.add_node("fetcher", fetcher_agent)
    graph.add_node("transcriber", transcriber_agent)
    graph.add_node("extractor", extractor_agent)
    graph.add_node("formatter", formatter_agent)

    # Wire linear edges: fetcher → transcriber → extractor → formatter → END
    graph.set_entry_point("fetcher")
    graph.add_edge("fetcher", "transcriber")
    graph.add_edge("transcriber", "extractor")
    graph.add_edge("extractor", "formatter")
    graph.add_edge("formatter", END)

    return graph.compile()


def main():
    url = input("🎥Please Enter the URL of the YouTube Video: ")

    # Initial state — only youtube_url is set; all other fields start as None
    initial_state: PodcastState = {
        "youtube_url": url,
        "audio_path": None,
        "metadata": None,
        "transcript": None,
        "timestamps": None,
        "extracted": None,
        "show_notes": None,
        "output_path": None,
    }

    logging.info("\n🎙️  Podcast Show Notes Generator")
    logging.info("=" * 40)

    pipeline = build_graph()
    final_state = pipeline.invoke(initial_state)

    logging.info("\n" + "=" * 40)
    logging.info(f"✅ Done! Show notes saved to: {final_state['output_path']}")
    logging.info("=" * 40 + "\n")


if __name__ == "__main__":
    main()
