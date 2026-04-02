# =============================================================================
# DEMO CASE 4 — Server V1  (3 tools)
# Used in the first half of the discovery demo.
# Run this first, then show discovery on the client.
# Then stop this and start demo_case4_server_v2.py to add a 4th tool.
#
# Run: python demo_case4_server_v1.py
# =============================================================================

import re
import requests
import gradio as gr
from bs4 import BeautifulSoup
from collections import Counter


def analyze_public_profile(url: str) -> dict:
    """Analyze a public profile page. Extracts name, achievements, and AI contributions."""
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}
    try:
        soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        person = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Not found"
        infobox = soup.find("table", class_="infobox")
        achievements = []
        if infobox:
            for row in infobox.find_all("tr"):
                th, td = row.find("th"), row.find("td")
                if th and td and "known" in th.get_text().lower():
                    achievements.append(td.get_text(" ", strip=True))
        ai = []
        for p in soup.find_all("p"):
            if "machine learning" in p.get_text().lower():
                ai.append(p.get_text(strip=True))
                break
        return {
            "who_is_the_person": person,
            "notable_achievements": achievements or ["Not found"],
            "contributions_in_ai": ai or ["Not found"],
        }
    except Exception as e:
        return {"error": str(e)}


def summarize_page(url: str) -> dict:
    """Summarize a web page by returning its first three paragraphs (max 500 chars)."""
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}
    try:
        soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        summary = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")[:3])[:500]
        return {"summary": summary or "No summary available"}
    except Exception as e:
        return {"error": str(e)}


def extract_keywords(url: str, top_n: int = 10) -> dict:
    """Extract the top N keywords from a web page based on word frequency."""
    if not url or not re.match(r'^https?://', url.strip()):
        return {"error": "Invalid URL"}
    try:
        soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        words = re.findall(r'\b\w+\b', soup.get_text(" ", strip=True).lower())
        stop = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","is","are","was","were"}
        keywords = [w for w, _ in Counter(words).most_common(top_n * 2) if w not in stop][:top_n]
        return {"keywords": keywords}
    except Exception as e:
        return {"error": str(e)}


# ── Server ────────────────────────────────────────────────────────────────────

demo = gr.Blocks()

with demo:
    gr.Markdown("## MCP Tool Server — V1  (3 tools)")
    gr.Interface(fn=analyze_public_profile, inputs=gr.Textbox(label="URL"), outputs=gr.JSON(), title="analyze_public_profile")
    gr.Interface(fn=summarize_page,         inputs=gr.Textbox(label="URL"), outputs=gr.JSON(), title="summarize_page")
    gr.Interface(fn=extract_keywords,       inputs=[gr.Textbox(label="URL"), gr.Number(label="Top N", value=10)], outputs=gr.JSON(), title="extract_keywords")

if __name__ == "__main__":
    print("\n[V1] Server starting with 3 tools: analyze_public_profile, summarize_page, extract_keywords")
    print("[V1] MCP endpoint → http://127.0.0.1:7860/gradio_api/mcp/sse\n")
    demo.launch(mcp_server=True)
