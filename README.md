# 🔬 ResearchMind — Multi-Agent AI Research System

Give it a topic and four AI agents produce a sourced research report — then
critique their own work.

Built with **LangChain**, **Groq**, **Tavily** and **Streamlit**.

---

## How it works

| Step | Agent | What it does |
|:---:|---|---|
| 1 | 🔍 **Search Agent** | Searches the web with Tavily for recent sources |
| 2 | 📄 **Reader Agent** | Scrapes the most relevant page for deeper detail |
| 3 | ✍️ **Writer Chain** | Writes the report from everything gathered |
| 4 | 🧐 **Critic Chain** | Reviews the report and scores it out of 10 |

You get back an Introduction, Key Findings, Conclusion and Sources, plus a short
critique of the report's weaknesses.

---

## Setup

```bash
git clone https://github.com/mahim83/Multi-Agent-AI-Research-system.git
cd Multi-Agent-AI-Research-system

python -m venv .venv
.venv\Scripts\activate          # macOS / Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add two free API keys:

```
GROQ_API_KEY=your_key_here      # https://console.groq.com/keys
TAVILY_API_KEY=your_key_here    # https://app.tavily.com/home
```

`.env` is git-ignored, so your keys stay on your machine.

---

## Running it

```bash
streamlit run app.py      # web app
python pipeline.py        # command line
```

---

## Files

```
app.py          Streamlit interface
pipeline.py     The four research steps + the command-line version
agents.py       Model setup, the agents, and the writer/critic prompts
formatting.py   Cleans the model's markdown before it is shown
tools.py        Web search (Tavily) and page scraping (BeautifulSoup)
```

Both the web app and the CLI call `research_steps()` in `pipeline.py`, so the
pipeline exists in exactly one place.

---

## Notes

**Sources are real.** URLs are collected from what the search tool actually
returned, not from the model's summary, so the report cannot cite invented links.

**Prompts are trimmed to fit Groq's free tier** (8000 tokens per minute). If you
still hit the limit, wait a minute or lower `SEARCH_CHAR_BUDGET` and
`SCRAPE_CHAR_BUDGET` in `agents.py`.

**Markdown is cleaned before rendering.** `normalize_report()` in `formatting.py`
turns `<br>` into real line breaks and `•` into `-`, and unrolls tables with
paragraph-sized cells into readable sections.

**Change the model** by adding `GROQ_MODEL=openai/gpt-oss-20b` to `.env`. The
default is `openai/gpt-oss-120b`.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `TAVILY_API_KEY is not set` | Create `.env` from `.env.example` |
| `413 Request too large` | Lower the char budgets in `agents.py` |
| `429 rate_limit_exceeded` | Free-tier minute limit reached — wait and retry |

---

## Deploying

Host it free on [Streamlit Community Cloud](https://share.streamlit.io): point it
at this repo with main file `app.py`, then add both keys under
**Settings → Secrets**.

```toml
GROQ_API_KEY = "gsk_..."
TAVILY_API_KEY = "tvly-..."
```
