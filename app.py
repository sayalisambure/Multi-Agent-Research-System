import html
import time

import streamlit as st

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8e4dc;
}

.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,140,50,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,80,30,0.08) 0%, transparent 55%);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1200px; }

/* ── Hero ── */
.hero { text-align: center; padding: 3.5rem 0 2.5rem; position: relative; }
.hero-eyebrow {
    font-family: 'DM Mono', monospace; font-size: 0.7rem; font-weight: 500;
    letter-spacing: 0.25em; text-transform: uppercase; color: #ff8c32;
    margin-bottom: 1rem; opacity: 0.9;
}
.hero h1 {
    font-family: 'Syne', sans-serif; font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 800; line-height: 1.0; letter-spacing: -0.03em;
    color: #f0ebe0; margin: 0 0 1rem;
}
.hero h1 span { color: #ff8c32; }
.hero-sub {
    font-size: 1.05rem; font-weight: 300; color: #a09890;
    max-width: 520px; margin: 0 auto; line-height: 1.65;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,140,50,0.3), transparent);
    margin: 2rem 0;
}

/* ── Bordered containers (input / report / feedback) ── */
[class*="st-key-input_card"],
[class*="st-key-report_card"],
[class*="st-key-feedback_card"] {
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    padding: 0.5rem 0.8rem;
}
[class*="st-key-input_card"]    { border: 1px solid rgba(255,140,50,0.15); }
[class*="st-key-report_card"]   { border: 1px solid rgba(255,140,50,0.2); }
[class*="st-key-feedback_card"] { border: 1px solid rgba(80,200,120,0.2); margin-top: 1.2rem; }

/* ── Text input ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,140,50,0.25) !important;
    border-radius: 10px !important;
    color: #f0ebe0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff8c32 !important;
    box-shadow: 0 0 0 3px rgba(255,140,50,0.12) !important;
}
.stTextInput > label {
    font-family: 'DM Mono', monospace !important; font-size: 0.72rem !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    color: #ff8c32 !important; font-weight: 500 !important;
}

/* ── Primary button ── */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #ff8c32 0%, #ff5a1a 100%) !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.7rem 2.2rem !important;
    box-shadow: 0 4px 20px rgba(255,140,50,0.3) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(255,140,50,0.4) !important;
}
.stButton > button:disabled { opacity: 0.45 !important; transform: none !important; }

/* ── Example chips (small, quiet buttons) ── */
[class*="st-key-chips"] .stButton > button {
    background: rgba(255,255,255,0.04) !important;
    color: #a09890 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 400 !important; font-size: 0.75rem !important;
    letter-spacing: 0 !important;
    padding: 0.25rem 0.7rem !important;
    box-shadow: none !important;
}
[class*="st-key-chips"] .stButton > button:hover {
    border-color: rgba(255,140,50,0.4) !important;
    color: #f0ebe0 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Pipeline step cards ── */
.step-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.2rem 1.6rem; margin-bottom: 1rem;
    position: relative; overflow: hidden; transition: border-color 0.3s;
}
.step-card.active { border-color: rgba(255,140,50,0.4); background: rgba(255,140,50,0.04); }
.step-card.done   { border-color: rgba(80,200,120,0.3); background: rgba(80,200,120,0.03); }
.step-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    border-radius: 14px 0 0 14px; background: rgba(255,255,255,0.05);
}
.step-card.active::before { background: #ff8c32; }
.step-card.done::before   { background: #50c878; }

.step-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.3rem; }
.step-num { font-family: 'DM Mono', monospace; font-size: 0.68rem; letter-spacing: 0.15em; color: #ff8c32; opacity: 0.7; }
.step-title { font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; color: #f0ebe0; }
.step-status { margin-left: auto; font-family: 'DM Mono', monospace; font-size: 0.68rem; letter-spacing: 0.1em; }
.status-waiting { color: #555; }
.status-running { color: #ff8c32; }
.status-done    { color: #50c878; }

/* ── Raw result panels ── */
.result-panel {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1.4rem 1.6rem; margin: 0.5rem 0 1rem;
}
.result-panel-title {
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.2em;
    text-transform: uppercase; color: #ff8c32; margin-bottom: 1rem;
    padding-bottom: 0.7rem; border-bottom: 1px solid rgba(255,140,50,0.15);
}
.result-content {
    font-size: 0.9rem; line-height: 1.75; color: #cdc8bf;
    white-space: pre-wrap; word-break: break-word;
}

.panel-label {
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.2em;
    text-transform: uppercase; margin: 0.6rem 0 1rem; padding-bottom: 0.7rem;
}
.panel-label.orange { color: #ff8c32; border-bottom: 1px solid rgba(255,140,50,0.15); }
.panel-label.green  { color: #50c878; border-bottom: 1px solid rgba(80,200,120,0.15); }

.stSpinner > div { color: #ff8c32 !important; }

details summary {
    font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important;
    color: #a09890 !important; letter-spacing: 0.1em !important;
}

.section-heading {
    font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700;
    color: #f0ebe0; margin: 0 0 1rem;
}
.notice {
    font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #605850;
    text-align: center; margin-top: 3rem; letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def to_text(content) -> str:
    """Model output can be a str or a list of content blocks (e.g. Gemini)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    return str(content)


def step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done": ("✓ DONE", "status-done"),
    }
    label, cls = status_map.get(state, ("", ""))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    desc_html = (
        f"<div style='font-size:0.82rem;color:#706860;margin-top:0.3rem;'>{desc}</div>"
        if desc else ""
    )
    st.markdown(
        f"""
        <div class="step-card {card_cls}">
            <div class="step-header">
                <span class="step-num">{num}</span>
                <span class="step-title">{title}</span>
                <span class="step-status {cls}">{label}</span>
            </div>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def set_example(text: str):
    st.session_state["topic_input"] = text


# ── Session state ─────────────────────────────────────────────────────────────
st.session_state.setdefault("results", {})
st.session_state.setdefault("running", False)
st.session_state.setdefault("done", False)
st.session_state.setdefault("topic_input", "")

STEPS = [
    ("search", "01", "Search Agent", "Gathers recent web information"),
    ("reader", "02", "Reader Agent", "Scrapes & extracts deep content"),
    ("writer", "03", "Writer Chain", "Drafts the full research report"),
    ("critic", "04", "Critic Chain", "Reviews & scores the report"),
]

# ── Hero ──────────────────────────────────────────────────────────────────────
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

# ── Layout: input left, pipeline right ────────────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    with st.container(border=True, key="input_card"):
        topic = st.text_input(
            "Research Topic",
            placeholder="e.g. Quantum computing breakthroughs in 2025",
            key="topic_input",
        )
        run_btn = st.button(
            "⚡  Run Research Pipeline",
            use_container_width=True,
            disabled=st.session_state.running,
        )

    st.caption("Try an example:")
    with st.container(key="chips"):
        chip_cols = st.columns(3)
        for col, ex in zip(chip_cols, ["LLM agents 2025", "CRISPR gene editing", "Fusion energy progress"]):
            col.button(
                ex,
                key=f"chip_{ex}",
                on_click=set_example,
                args=(ex,),
                use_container_width=True,
                disabled=st.session_state.running,
            )

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)
    slots = {key: st.empty() for key, *_ in STEPS}


def draw_steps(current=None):
    for key, num, title, desc in STEPS:
        if key in st.session_state.results:
            state = "done"
        elif key == current:
            state = "running"
        else:
            state = "waiting"
        with slots[key]:
            step_card(num, title, state, desc)


draw_steps()

# ── Start a run ───────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()

# ── Run pipeline ──────────────────────────────────────────────────────────────
if st.session_state.running and not st.session_state.done:
    results = {}
    topic_val = st.session_state.topic_input.strip()

    try:
        # Step 1: Search
        draw_steps("search")
        with st.spinner("🔍  Search Agent is working…"):
            sr = build_search_agent().invoke({
                "messages": [("user", f"Find recent, reliable and detailed information about: {topic_val}")]
            })
            results["search"] = to_text(sr["messages"][-1].content)
            st.session_state.results = dict(results)

        # Step 2: Reader
        draw_steps("reader")
        with st.spinner("📄  Reader Agent is scraping top resources…"):
            rr = build_reader_agent().invoke({
                "messages": [("user",
                    f"Based on the following search results about '{topic_val}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{results['search'][:800]}"
                )]
            })
            results["reader"] = to_text(rr["messages"][-1].content)
            st.session_state.results = dict(results)

        # Step 3: Writer
        draw_steps("writer")
        with st.spinner("✍️  Writer is drafting the report…"):
            research_combined = (
                f"SEARCH RESULTS:\n{results['search']}\n\n"
                f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
            )
            results["writer"] = to_text(
                writer_chain.invoke({"topic": topic_val, "research": research_combined})
            )
            st.session_state.results = dict(results)

        # Step 4: Critic
        draw_steps("critic")
        with st.spinner("🧐  Critic is reviewing the report…"):
            results["critic"] = to_text(critic_chain.invoke({"report": results["writer"]}))
            st.session_state.results = dict(results)

        st.session_state.done = True

    except Exception as e:
        st.error(f"The pipeline stopped: {e}")
    finally:
        # Always release the lock so a failure can't re-trigger the run
        st.session_state.running = False

    if st.session_state.done:
        st.rerun()

# ── Results display ───────────────────────────────────────────────────────────
r = st.session_state.results

if r:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Results</div>', unsafe_allow_html=True)

    if "search" in r:
        with st.expander("🔍 Search Results (raw)", expanded=False):
            st.markdown(
                f'<div class="result-panel"><div class="result-panel-title">Search Agent Output</div>'
                f'<div class="result-content">{html.escape(r["search"])}</div></div>',
                unsafe_allow_html=True,
            )

    if "reader" in r:
        with st.expander("📄 Scraped Content (raw)", expanded=False):
            st.markdown(
                f'<div class="result-panel"><div class="result-panel-title">Reader Agent Output</div>'
                f'<div class="result-content">{html.escape(r["reader"])}</div></div>',
                unsafe_allow_html=True,
            )

    if "writer" in r:
        with st.container(border=True, key="report_card"):
            st.markdown('<div class="panel-label orange">📝 Final Research Report</div>', unsafe_allow_html=True)
            st.markdown(r["writer"])
            st.download_button(
                label="⬇  Download Report (.md)",
                data=r["writer"],
                file_name="research_report.md",
                mime="text/markdown",
            )

    if "critic" in r:
        with st.container(border=True, key="feedback_card"):
            st.markdown('<div class="panel-label green">🧐 Critic Feedback</div>', unsafe_allow_html=True)
            st.markdown(r["critic"])

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="notice">
    ResearchMind · Powered by LangChain multi-agent pipeline · Built with Streamlit
</div>
""", unsafe_allow_html=True)