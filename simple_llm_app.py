from typing import Final

import requests
from bs4 import BeautifulSoup
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


# =================================================
# Tool: Fetch readable text from public web page
# =================================================
DEFAULT_URL: Final[str] = "https://en.wikipedia.org/wiki/Mariah_Carey"
REQUEST_TIMEOUT_SECONDS: Final[int] = 5
MAX_PROFILE_CHARS: Final[int] = 12_000
REQUEST_HEADERS: Final[dict[str, str]] = {"User-Agent": "Mozilla/5.0"}


# =================================================
# Prompt (Profile Analysis)
# =================================================
PROFILE_ANALYSIS_TEMPLATE: Final[str] = """
You are an AI agent analyzing a public professional profile.

From the content below, extract:
- Short professional summary
- Key roles and expertise
- Notable achievements
- Who this profile would be relevant for

Profile Content:
{content}
"""


def extract_readable_text(html: str) -> str:
    """Strip non-readable tags and return trimmed page text."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return " ".join(soup.stripped_strings)[:MAX_PROFILE_CHARS]


def fetch_public_profile(url: str) -> str:
    """Fetch and clean text from a public web page for profile analysis."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=REQUEST_HEADERS,
        )
        response.raise_for_status()
        return extract_readable_text(response.text)
    except Exception as exc:
        return f"ERROR: Failed to fetch profile: {exc}"


# =================================================
# LLM
# =================================================
def build_profile_chain():
    """Create the prompt -> model -> parser pipeline."""
    prompt = PromptTemplate.from_template(PROFILE_ANALYSIS_TEMPLATE)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return prompt | llm | StrOutputParser()


# =================================================
# Agent Orchestration
# =================================================
def analyze_profile_from_web(url: str) -> str:
    """Fetch a public profile page and return the LLM's analysis."""
    content = fetch_public_profile(url)
    if content.startswith("ERROR"):
        return content

    profile_chain = build_profile_chain()
    return profile_chain.invoke({"content": content})


# =================================================
# Demo Run
# =================================================
def main() -> None:
    """Run the demo against a default public profile."""
    #Public, safe, reliable profile
    # url = "https://en.wikipedia.org/wiki/Andrew_Ng"
    print(analyze_profile_from_web(DEFAULT_URL))


if __name__ == "__main__":
    main()


# Problems:
# Tool must live in the same codebase
# Every consumer must re-implement the tool
# Tight coupling
# Scaling problem (M × N)
# Ownership & governance
# enforce policies
