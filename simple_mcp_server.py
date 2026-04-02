# --- Imports ---
import json
import requests
import gradio as gr
from bs4 import BeautifulSoup
import re
from collections import Counter

# ------------------------------------------------------------
# TOOL 1: Analyze Public Profile
# ------------------------------------------------------------

def analyze_public_profile(url: str) -> dict:
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "comment"]):
            tag.decompose()

        person = "Not found"
        if soup.find("h1"):
            person = soup.find("h1").get_text(strip=True)
        elif soup.title:
            person = soup.title.get_text(strip=True)

        achievements = []
        infobox = soup.find("table", class_="infobox")
        if infobox:
            for row in infobox.find_all("tr"):
                th, td = row.find("th"), row.find("td")
                if th and td and "known" in th.get_text().lower():
                    achievements.append(td.get_text(" ", strip=True))

        if not achievements:
            achievements = ["Not found"]

        ai_contributions = []
        for p in soup.find_all("p"):
            if "machine learning" in p.get_text().lower():
                ai_contributions.append(p.get_text(strip=True))
                break

        if not ai_contributions:
            ai_contributions = ["Not found"]

        return {
            "who_is_the_person": person,
            "notable_achievements": achievements,
            "contributions_in_ai": ai_contributions,
        }

    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# TOOL 2: Summarize Page
# ------------------------------------------------------------

def summarize_page(url: str) -> dict:
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        summary = " ".join(p.get_text(" ", strip=True) for p in paragraphs[:3])[:500]

        return {"summary": summary or "No summary available"}

    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# TOOL 3: Extract Keywords
# ------------------------------------------------------------

def extract_keywords(url: str, top_n: int = 10) -> dict:
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True).lower()
        words = re.findall(r'\b\w+\b', text)
        freq = Counter(words)

        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "is", "are", "was", "were"
        }

        keywords = [
            word for word, _ in freq.most_common(top_n * 2)
            if word not in stop_words
        ][:top_n]

        return {"keywords": keywords}

    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# MCP SERVER (NO DISPATCHER)
# ------------------------------------------------------------

demo = gr.Blocks()

with demo:
    gr.Markdown("## 🧰 MCP Tool Server")

    gr.Interface(
        fn=analyze_public_profile,
        inputs=gr.Textbox(label="URL"),
        outputs=gr.JSON(),
        title="analyze_public_profile"
    )

    gr.Interface(
        fn=summarize_page,
        inputs=gr.Textbox(label="URL"),
        outputs=gr.JSON(),
        title="summarize_page"
    )

    gr.Interface(
        fn=extract_keywords,
        inputs=[
            gr.Textbox(label="URL"),
            gr.Number(label="Top N", value=10)
        ],
        outputs=gr.JSON(),
        title="extract_keywords"
    )

# ------------------------------------------------------------
# LAUNCH
# ------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(mcp_server=True)
