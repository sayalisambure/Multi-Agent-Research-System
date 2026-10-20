import time

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
load_dotenv()

# Free tier = 5 requests/minute per model. If every model is rate limited,
# we wait and try again instead of failing.
MODEL_POOL = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
]

WAIT_SECONDS = 35   # pause between retry rounds
MAX_ROUNDS = 4      # how many times to retry after rate limits


def make_llm(model_name: str):
    return ChatGoogleGenerativeAI(
        model=model_name, temperature=0, max_retries=0, timeout=90
    )


def rotated(start: int):
    return MODEL_POOL[start:] + MODEL_POOL[:start]


def is_rate_limit(e: Exception) -> bool:
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def is_daily_limit(e: Exception) -> bool:
    return "PerDay" in str(e)


def run_with_wait(call):
    """Run call(); on per-minute rate limits, wait and retry. Daily limits fail fast."""
    last = None
    for round_no in range(MAX_ROUNDS):
        try:
            return call()
        except Exception as e:
            last = e
            if is_rate_limit(e) and not is_daily_limit(e) and round_no < MAX_ROUNDS - 1:
                print(f"[wait] rate limited, waiting {WAIT_SECONDS}s (round {round_no + 1}/{MAX_ROUNDS})")
                time.sleep(WAIT_SECONDS)
                continue
            raise
    raise last


# ── Agent: tries each model, then waits and retries if all are rate limited ───
class FallbackAgent:
    def __init__(self, tools, models):
        self.models = models
        self.agents = [create_agent(model=make_llm(m), tools=tools) for m in models]

    def _try_all(self, inputs, *args, **kwargs):
        last = None
        for name, agent in zip(self.models, self.agents):
            try:
                return agent.invoke(inputs, *args, **kwargs)
            except Exception as e:
                print(f"[fallback] {name} failed: {repr(e)[:160]}")
                last = e
        raise last

    def invoke(self, inputs, *args, **kwargs):
        return run_with_wait(lambda: self._try_all(inputs, *args, **kwargs))


def build_search_agent():
    return FallbackAgent([web_search], rotated(0))


def build_reader_agent():
    return FallbackAgent([scrape_url], rotated(1))


# ── Chains: model fallback + wait and retry ───────────────────────────────────
class WaitingChain:
    def __init__(self, chain):
        self.chain = chain

    def invoke(self, inputs, *args, **kwargs):
        return run_with_wait(lambda: self.chain.invoke(inputs, *args, **kwargs))


def llm_with_fallback(start: int):
    names = rotated(start)
    return make_llm(names[0]).with_fallbacks([make_llm(n) for n in names[1:]])


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = WaitingChain(writer_prompt | llm_with_fallback(2) | StrOutputParser())

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

critic_chain = WaitingChain(critic_prompt | llm_with_fallback(3) | StrOutputParser())