"""The four research steps, shared by the CLI below and the Streamlit UI in app.py."""

import sys

from agents import (
    SEARCH_CHAR_BUDGET,
    SCRAPE_CHAR_BUDGET,
    build_reader_agent,
    build_search_agent,
    collect_source_urls,
    critic_chain,
    trim,
    writer_chain,
)

# key, number, title, description
STEPS = [
    ("search", "01", "Search Agent", "Gathers recent web information"),
    ("reader", "02", "Reader Agent", "Scrapes & extracts deep content"),
    ("writer", "03", "Writer Chain", "Drafts the full research report"),
    ("critic", "04", "Critic Chain", "Reviews & scores the report"),
]


def research_steps(topic):
    """Run the pipeline, yielding (key, output, state) as each step finishes."""
    topic = topic.strip()
    if not topic:
        raise ValueError("Topic must not be empty.")

    state = {"topic": topic, "sources": []}

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = search_result["messages"][-1].content
    # Take URLs from the tool output, not the agent's summary, which may drop or
    # invent them.
    state["sources"] = collect_source_urls(search_result)
    yield "search", state["search_results"], state

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{trim(state['search_results'], 800)}"
        )]
    })
    state["scraped_content"] = reader_result["messages"][-1].content
    for url in collect_source_urls(reader_result):
        if url not in state["sources"]:
            state["sources"].append(url)
    yield "reader", state["scraped_content"], state

    # Trim before sending: the untrimmed prompt went over Groq's 8000 tokens/min
    # cap and came back as a 413, which the SDK does not retry.
    research_combined = (
        f"SEARCH RESULTS:\n{trim(state['search_results'], SEARCH_CHAR_BUDGET)}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{trim(state['scraped_content'], SCRAPE_CHAR_BUDGET)}"
    )
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined,
        "sources": "\n".join(state["sources"]) or "(none captured)",
    })
    yield "writer", state["report"], state

    state["feedback"] = critic_chain.invoke({
        "report": trim(state["report"], SEARCH_CHAR_BUDGET + SCRAPE_CHAR_BUDGET),
    })
    yield "critic", state["feedback"], state


def run_research_pipeline(topic):
    """Run every step and return the final state."""
    state = {}
    for _, _, state in research_steps(topic):
        pass
    return state


if __name__ == "__main__":
    # Windows consoles use cp1252 and cannot encode characters the model often
    # emits (narrow no-break space, curly quotes), which crashes print().
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    topic = input("\n Enter a research topic : ")
    steps = research_steps(topic)

    try:
        # One pull per step, so the heading prints before the step runs.
        for key, num, title, desc in STEPS:
            print("\n" + "=" * 50)
            print(f"step {num} - {title} - {desc} ...")
            print("=" * 50)

            _, output, state = next(steps)
            print("\n" + output)

            if key == "search":
                print(f"\n sources found: {len(state['sources'])}")
    except Exception as e:
        print(f"\nPipeline failed: {type(e).__name__}: {e}")
        sys.exit(1)
