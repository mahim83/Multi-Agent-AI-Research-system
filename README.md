# 🔬 ResearchMind — Multi-Agent AI Research System

Give it a topic, and four AI agents work together to produce a sourced research
report — then critique their own work.

Built with **LangChain**, **Groq**, **Tavily** and **Streamlit**.

---

## How it works

The pipeline runs in four steps:

| Step | Agent | What it does |
|:---:|---|---|
| 1 | 🔍 **Search Agent** | Searches the web with Tavily for recent sources |
| 2 | 📄 **Reader Agent** | Scrapes the most relevant page for deeper detail |
| 3 | ✍️ **Writer Chain** | Writes the report from everything gathered |
| 4 | 🧐 **Critic Chain** | Reviews the report and scores it out of 10 |

You get back a report with an Introduction, Key Findings, Conclusion and Sources,
plus a short critique of its weaknesses.

---

## Setup

**1. Clone and install**

```bash
git clone https://github.com/mahim83/Multi-Agent-AI-Research-system.git
cd Multi-Agent-AI-Research-system

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

**2. Add your API keys**

Copy the template:

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
```

Then open `.env` and paste in your keys:

```
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

Both are free to get:

- Groq → https://console.groq.com/keys
- Tavily → https://app.tavily.com/home

> `.env` is ignored by git, so your keys stay on your machine.

---

## Running it

**Web app:**

```bash
streamlit run app.py
```

**Command line:**

```bash
python pipeline.py
```

---

## Files

```
app.py          Streamlit web interface
pipeline.py     The four research steps + command-line version
agents.py       Groq model setup, the agents and the writer/critic prompts
tools.py        Web search (Tavily) and page scraping (BeautifulSoup)
.env.example    Template for your API keys
```

The four steps live in one place — `research_steps()` in `pipeline.py` — and both
the web app and the command line use it, so the logic isn't duplicated.

---

## Good to know

**Sources are real.** URLs are collected from what the search tool actually
returned, not from the model's summary. This stops the report from citing
made-up links.

**Groq's free tier allows 8000 tokens per minute.** Long prompts are trimmed
before being sent so they fit. If you hit the limit anyway, wait a minute or
lower `SEARCH_CHAR_BUDGET` and `SCRAPE_CHAR_BUDGET` in `agents.py`.

**Changing the model.** The default is `openai/gpt-oss-120b`. To use a different
one, add this to `.env`:

```
GROQ_MODEL=openai/gpt-oss-20b
```

---

## Common problems

| Problem | Fix |
|---|---|
| `TAVILY_API_KEY is not set` | You haven't created `.env` yet — copy `.env.example` |
| `413 Request too large` | A prompt was over the token limit; lower the budgets in `agents.py` |
| `429 rate_limit_exceeded` | You've used your 8000 tokens for this minute — wait and retry |
| `UnicodeEncodeError` | Windows terminal encoding; `pipeline.py` already handles this |

---

## Deploying

You can host the web app free on [Streamlit Community Cloud](https://share.streamlit.io).
Point it at this repo, branch `main`, main file `app.py`.

Since there's no `.env` on the server, add your keys under **Settings → Secrets**:

```toml
GROQ_API_KEY = "gsk_..."
TAVILY_API_KEY = "tvly-..."
```
