import html
import re
import time

import streamlit as st

from pipeline import STEPS, research_steps

st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #e8e4dc; }

.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,140,50,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,80,30,0.08) 0%, transparent 55%);
    background-attachment: fixed;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1200px; }

.hero { text-align: center; padding: 3.5rem 0 2.5rem; }
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #ff8c32;
    margin-bottom: 1rem;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.03em;
    color: #f0ebe0;
    margin: 0 0 1rem;
}
.hero h1 span { color: #ff8c32; }
.hero-sub {
    font-size: 1.05rem;
    font-weight: 300;
    color: #a09890;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.65;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,140,50,0.3), transparent);
    margin: 2rem 0;
}

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,140,50,0.25) !important;
    border-radius: 10px !important;
    color: #f0ebe0 !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff8c32 !important;
    box-shadow: 0 0 0 3px rgba(255,140,50,0.12) !important;
}
.stTextInput label, .stTextInput label p {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #ff8c32 !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff8c32 0%, #ff5a1a 100%) !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 2.2rem !important;
    box-shadow: 0 4px 20px rgba(255,140,50,0.3) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(255,140,50,0.4) !important;
}

.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #a09890 !important;
    font-size: 0.75rem !important;
    padding: 0.3rem 0.6rem !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(255,140,50,0.4) !important;
    color: #ff8c32 !important;
}

.step-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, background 0.3s;
}
.step-card.active { border-color: rgba(255,140,50,0.4); background: rgba(255,140,50,0.04); }
.step-card.done   { border-color: rgba(80,200,120,0.3); background: rgba(80,200,120,0.03); }
.step-card.failed { border-color: rgba(255,80,80,0.4);  background: rgba(255,80,80,0.04); }
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: rgba(255,255,255,0.05);
}
.step-card.active::before { background: #ff8c32; }
.step-card.done::before   { background: #50c878; }
.step-card.failed::before { background: #ff5050; }

.step-header { display: flex; align-items: center; gap: 0.8rem; }
.step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    color: #ff8c32;
    opacity: 0.7;
}
.step-title { font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; color: #f0ebe0; }
.step-status {
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    white-space: nowrap;
}
.status-waiting { color: #555; }
.status-running { color: #ff8c32; }
.status-done    { color: #50c878; }
.status-failed  { color: #ff5050; }
.step-desc { font-size: 0.8rem; color: #706860; margin-top: 0.35rem; }

@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }
.pulse { animation: pulse 1.2s ease-in-out infinite; }

.score-wrap { display: flex; align-items: baseline; gap: 0.6rem; margin-bottom: 1rem; }
.score-val { font-family: 'Syne', sans-serif; font-size: 2.6rem; font-weight: 800; color: #50c878; }
.score-max { font-family: 'DM Mono', monospace; font-size: 0.85rem; color: #706860; }

.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #f0ebe0;
    margin: 2rem 0 1rem;
}
.panel-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    padding-bottom: 0.6rem;
}
.panel-label.orange { color: #ff8c32; border-bottom: 1px solid rgba(255,140,50,0.15); }
.panel-label.green  { color: #50c878; border-bottom: 1px solid rgba(80,200,120,0.15); }

.result-content {
    font-size: 0.88rem;
    line-height: 1.75;
    color: #cdc8bf;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 420px;
    overflow-y: auto;
}

.src-item {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    word-break: break-all;
}
.src-item a { color: #ff8c32; text-decoration: none; }
.src-item a:hover { text-decoration: underline; }

.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; border-bottom: 1px solid rgba(255,255,255,0.07); }
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase;
    color: #a09890 !important;
}
.stTabs [aria-selected="true"] { color: #ff8c32 !important; }

details summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: #a09890 !important;
}

.notice {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #605850;
    text-align: center;
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

STATUS = {
    "waiting": ("WAITING", "status-waiting", ""),
    "running": ("<span class='pulse'>● RUNNING</span>", "status-running", "active"),
    "done": ("✓ DONE", "status-done", "done"),
    "failed": ("✕ FAILED", "status-failed", "failed"),
}

ICON = {"search": "🔍", "reader": "📄", "writer": "✍️", "critic": "🧐"}

defaults = {"results": {}, "sources": [], "running": False, "done": False, "error": None}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def use_example(text):
    # A widget's session_state key can only be set from a callback, so the chips
    # use on_click instead of their return value.
    st.session_state.topic_input = text


st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Multi-Agent AI System</div>
    <h1>Research<span>Mind</span></h1>
    <p class="hero-sub">
        Four specialized AI agents collaborate — searching, scraping, writing,
        and critiquing — to deliver a polished research report on any topic.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

col_input, _, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. Quantum computing breakthroughs in 2026",
        key="topic_input",
        disabled=st.session_state.running,
    )
    run_btn = st.button(
        "⚡  Run Research Pipeline",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.running,
    )

    st.markdown(
        "<div style=\"font-family:'DM Mono',monospace;font-size:0.68rem;"
        "color:#605850;letter-spacing:0.1em;margin:1rem 0 0.4rem;\">TRY →</div>",
        unsafe_allow_html=True,
    )
    examples = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]
    for column, example in zip(st.columns(len(examples)), examples):
        column.button(
            example,
            key=f"ex_{example}",
            on_click=use_example,
            args=(example,),
            use_container_width=True,
            disabled=st.session_state.running,
        )

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)
    # Placeholders, so each card can be repainted while the pipeline runs.
    slots = [st.empty() for _ in STEPS]


def paint(done_count, running=False, failed=False):
    """Repaint the four cards, given how many steps have finished."""
    for i, (slot, step) in enumerate(zip(slots, STEPS)):
        _, num, title, desc = step
        if i < done_count:
            state = "done"
        elif i == done_count and failed:
            state = "failed"
        elif i == done_count and running:
            state = "running"
        else:
            state = "waiting"
        label, css, card = STATUS[state]
        slot.markdown(f"""
        <div class="step-card {card}">
            <div class="step-header">
                <span class="step-num">{num}</span>
                <span class="step-title">{title}</span>
                <span class="step-status {css}">{label}</span>
            </div>
            <div class="step-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)


if not st.session_state.running:
    paint(len(st.session_state.results), failed=bool(st.session_state.error))

if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.update(results={}, sources=[], running=True, done=False, error=None)
        st.rerun()

if st.session_state.running and not st.session_state.done:
    results = {}
    status = st.empty()
    steps = research_steps(st.session_state.topic_input)

    try:
        # Mark a step running, then pull it: the generator only yields once the
        # step has finished.
        for i, (key, num, title, desc) in enumerate(STEPS):
            paint(i, running=True)
            status.markdown(f"{ICON[key]}  **{title}** — {desc.lower()}…")

            _, output, state = next(steps)
            results[key] = output
            st.session_state.results = dict(results)
            st.session_state.sources = list(state["sources"])

        paint(len(STEPS))
        status.empty()
    except Exception as e:
        st.session_state.error = f"{type(e).__name__}: {e}"
        paint(len(results), failed=True)
        status.empty()
    finally:
        # Resetting here matters: if an error left running=True, the app would
        # relaunch the pipeline on every rerun.
        steps.close()
        st.session_state.running = False
        st.session_state.done = True

    st.rerun()

if st.session_state.error:
    st.error(f"Pipeline stopped: {st.session_state.error}")
    if "rate_limit" in st.session_state.error or "413" in st.session_state.error:
        st.caption("Groq's free tier allows 8000 tokens per minute. Wait a minute and retry.")

results = st.session_state.results

if results:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Results</div>', unsafe_allow_html=True)

    tab_report, tab_critic, tab_sources, tab_raw = st.tabs(
        ["Report", "Critique", "Sources", "Raw output"]
    )

    with tab_report:
        if "writer" in results:
            st.markdown('<div class="panel-label orange">📝 Final Research Report</div>',
                        unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(results["writer"])
            st.download_button(
                "⬇  Download Report (.md)",
                data=results["writer"],
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
            )
        else:
            st.info("The report was not produced.")

    with tab_critic:
        if "critic" in results:
            st.markdown('<div class="panel-label green">🧐 Critic Feedback</div>',
                        unsafe_allow_html=True)
            score = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", results["critic"])
            if score:
                st.markdown(
                    f'<div class="score-wrap"><span class="score-val">{score.group(1)}</span>'
                    f'<span class="score-max">/ 10</span></div>',
                    unsafe_allow_html=True,
                )
            with st.container(border=True):
                st.markdown(results["critic"])
        else:
            st.info("No critique available.")

    with tab_sources:
        sources = st.session_state.sources
        if sources:
            st.markdown(f'<div class="panel-label orange">🔗 {len(sources)} verified sources</div>',
                        unsafe_allow_html=True)
            st.markdown("".join(
                f'<div class="src-item"><a href="{html.escape(url, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">{html.escape(url)}</a></div>'
                for url in sources
            ), unsafe_allow_html=True)
        else:
            st.info("No source URLs were captured.")

    with tab_raw:
        # html.escape is required: this is model output going into an
        # unsafe_allow_html block, and a stray '<' would break the layout.
        for key, label in [("search", "🔍 Search Agent output"), ("reader", "📄 Reader Agent output")]:
            if key in results:
                with st.expander(label):
                    st.markdown(f'<div class="result-content">{html.escape(results[key])}</div>',
                                unsafe_allow_html=True)

st.markdown("""
<div class="notice">
    ResearchMind · Powered by LangChain multi-agent pipeline · Built with Streamlit
</div>
""", unsafe_allow_html=True)
