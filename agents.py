import os
import re

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from tools import scrape_url, web_search

load_dotenv()

# ChatGroq reads GROQ_API_KEY from .env automatically.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Groq's free tier allows 8000 tokens per minute. A request bigger than that is
# rejected with a 413 that the SDK does not retry, so prompts are trimmed to
# these budgets before being sent.
SEARCH_CHAR_BUDGET = 6000
SCRAPE_CHAR_BUDGET = 6000

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0,
    reasoning_format="hidden",  # keep the model's scratchpad out of the answer
    max_tokens=2000,
    max_retries=6,
)


def trim(text, budget):
    """Cut text to a character budget, telling the model it was shortened."""
    text = str(text or "")
    if len(text) <= budget:
        return text
    return text[:budget] + "\n\n[... truncated to stay within the Groq token limit ...]"


def collect_source_urls(agent_result):
    """Pull URLs out of an agent's tool messages.

    The agent's final message is prose and may paraphrase or omit sources, so the
    tool output is the only reliable record of what was actually retrieved.
    """
    urls = []
    for message in agent_result["messages"]:
        if type(message).__name__ != "ToolMessage":
            continue
        for url in re.findall(r"https?://[^\s\)\]\},\"']+", str(message.content)):
            url = url.rstrip(".,;")
            if url not in urls:
                urls.append(url)
    return urls


def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        # The call limit keeps the conversation under the token cap.
        system_prompt=(
            "You are a web research agent. Use the web_search tool to gather "
            "recent, reliable information. Call it at most twice, then stop and "
            "summarise. Always reproduce the exact URLs you found."
        ),
    )


def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a deep-reading agent. Pick the single most relevant URL and "
            "call scrape_url on it exactly once, then summarise the key facts."
        ),
    )


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Verified Source URLs (cite only these, do not invent any others):
{sources}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (a "- " list of the verified URLs above, one per line)

Formatting rules:
- Plain Markdown only. Never write HTML: no <br>, <b> or <div>. The report is
  rendered by a reader that shows those as literal text instead of formatting.
- Give each key finding its own "### Finding N - <short title>" subsection,
  holding a paragraph of analysis followed by "- " bullets of evidence. Do not
  put the findings in a table.
- Use a table only for short comparable values: at most 4 columns, one brief
  phrase per cell, and never a line break inside a cell.
- Start every bullet with "- ". Never use the "•" character.
- Cite inline as (Publisher, D Mon YYYY), not with bracket markers, and list the
  matching URL under Sources.

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
