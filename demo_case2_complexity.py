# =============================================================================
# DEMO CASE 2: Why MCP is Essential — Complexity Reduction
# Shows the M×N problem (tight coupling) vs M+N solution (MCP)
#
# STANDALONE — no server required
# =============================================================================

import gradio as gr

# ── Content blocks ────────────────────────────────────────────────────────────

WITHOUT_MCP = """\
WITHOUT MCP — The M×N Problem
══════════════════════════════════════════════════════

Every agent framework must reimplement every tool.

          LangChain  smolagents  AutoGen   CrewAI   YourAgent
          ─────────  ──────────  ───────   ──────   ─────────
WebSearch    ✍️           ✍️         ✍️        ✍️        ✍️
Sentiment    ✍️           ✍️         ✍️        ✍️        ✍️
Profile      ✍️           ✍️         ✍️        ✍️        ✍️
DB Query     ✍️           ✍️         ✍️        ✍️        ✍️

= 4 tools × 5 frameworks = 20 implementations
  All tightly coupled. All need maintaining separately.

What breaks at scale:
  ✗ New framework ships?    → rewrite every tool for it
  ✗ Tool API changes?       → update every agent that uses it
  ✗ Want to audit usage?    → no central point to log at
  ✗ Want to rate-limit?     → buried inside each agent
  ✗ Two teams?              → blocked on each other

In code (from simple_agent.py):
  llm.bind_tools([fetch_public_profile, read_text_input])
  ↑
  Tools are hardcoded INTO the agent file.
  Another agent needs them? Copy-paste.
"""

WITH_MCP = """\
WITH MCP — The M+N Solution (Write Once, Use Everywhere)
══════════════════════════════════════════════════════

Tools live on a server. Agents discover them at runtime.

  LangChain  smolagents  AutoGen   CrewAI   YourAgent
         ↘       ↓          ↙       ↙        ↙
              MCP Protocol  (SSE transport)
         ↗       ↑          ↖       ↖        ↖
  WebSearch  ✍️  (once)
  Sentiment  ✍️  (once)   ← any agent uses it
  Profile    ✍️  (once)
  DB Query   ✍️  (once)

= 4 implementations. Decoupled. Independently deployable.

Benefits:
  ✓ New agent?       → point it at the MCP endpoint, done
  ✓ Tool changes?    → update server only, clients auto-adapt
  ✓ Audit / log?     → one place: the MCP server
  ✓ Rate limits?     → enforced at server layer, all agents covered
  ✓ Two teams?       → tool team and agent team work independently

In code (from simple_mcp_client.py):
  client = MCPClient({"url": "http://127.0.0.1:7860/gradio_api/mcp/sse"})
  tools  = client.get_tools()   ← discovered, not hardcoded
"""

TIGHT_CODE = '''\
# ── simple_agent.py — TIGHT COUPLING ──────────────────
# Tools are defined INSIDE the agent file.

from langchain_core.tools import tool

@tool
def fetch_public_profile(url: str) -> str:
    """Fetch and return web content from a URL."""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()[:12000]

@tool
def read_text_input(text: str) -> str:
    """Return the text input directly."""
    return text

# Tools hardcoded into the LLM — lives in THIS file
llm_with_tools = llm.bind_tools([fetch_public_profile, read_text_input])
#                                 ↑
# Adding a new tool?   → modify this file
# Another agent needs it? → copy-paste into that file
# Tool changes?        → update every file that copied it
'''

LOOSE_CODE = '''\
# ── simple_mcp_server.py — LOOSE COUPLING (Server) ────
# Tools live here, fully independent of any agent.

def analyze_public_profile(url: str) -> dict:
    ...  # scrapes a page, extracts profile info

def summarize_page(url: str) -> dict:
    ...  # returns first 3 paragraphs

def extract_keywords(url: str, top_n: int = 10) -> dict:
    ...  # returns top-N frequency keywords

demo.launch(mcp_server=True)
# ↑ One flag → all functions are live MCP tools
# ─────────────────────────────────────────────────────
# ── simple_mcp_client.py — LOOSE COUPLING (Client) ───
# Client discovers tools at runtime — zero hardcoding.

client = MCPClient({"url": "http://127.0.0.1:7860/gradio_api/mcp/sse"})
tools  = client.get_tools()   # ← manifest comes from server

# Adding a new tool?      → update server only
# Another agent needs it? → point it at same endpoint
# Tool changes?           → server updates; clients auto-adapt
'''

def show_architecture(choice):
    return WITHOUT_MCP if "Without" in choice else WITH_MCP

def show_code(choice):
    return TIGHT_CODE if "Tight" in choice else LOOSE_CODE

def show_scale_impact(n_agents, n_tools):
    n_agents, n_tools = int(n_agents), int(n_tools)
    without = n_agents * n_tools
    with_mcp = n_agents + n_tools
    saved = without - with_mcp
    return (
        f"Without MCP: {n_agents} agents × {n_tools} tools = {without} implementations\n"
        f"With MCP:    {n_agents} agents + {n_tools} tools = {with_mcp} implementations\n"
        f"──────────────────────────────────────────────\n"
        f"Saved:  {saved} duplicate implementations  "
        f"({round((saved/without)*100)}% reduction)"
    )

# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Case 2: Why MCP is Essential") as demo:
    gr.Markdown("""
# Case 2: Why MCP is Essential — Complexity Reduction
### The M×N problem and how MCP solves it
> **Standalone demo — no server required.**
""")

    # ── Architecture toggle ───────────────────────────────────
    gr.Markdown("### Architecture Comparison")
    arch_toggle = gr.Radio(
        choices=["Without MCP (Tight Coupling)", "With MCP (Loose Coupling)"],
        value="Without MCP (Tight Coupling)",
        label="Select Scenario"
    )
    arch_output = gr.Textbox(label="Architecture", lines=20, value=WITHOUT_MCP)
    arch_toggle.change(fn=show_architecture, inputs=arch_toggle, outputs=arch_output)

    gr.Markdown("---")

    # ── Code comparison ───────────────────────────────────────
    gr.Markdown("### Code from This Repo")
    with gr.Row():
        code_toggle = gr.Radio(
            choices=["Tight (simple_agent.py)", "Loose (MCP server + client)"],
            value="Tight (simple_agent.py)",
            label="Show Code Example"
        )
    code_output = gr.Code(label="Code", language="python", lines=16)
    code_toggle.change(fn=show_code, inputs=code_toggle, outputs=code_output)
    demo.load(fn=show_code, inputs=code_toggle, outputs=code_output)

    gr.Markdown("---")

    # ── Scale calculator ──────────────────────────────────────
    gr.Markdown("### Scale Impact Calculator")
    with gr.Row():
        n_agents = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Number of Agent Frameworks")
        n_tools  = gr.Slider(minimum=1, maximum=20, value=4, step=1, label="Number of Tools")
    calc_output = gr.Textbox(label="Implementation Count", lines=4)
    calc_btn = gr.Button("Calculate", variant="primary")
    calc_btn.click(fn=show_scale_impact, inputs=[n_agents, n_tools], outputs=calc_output)
    demo.load(fn=show_scale_impact, inputs=[n_agents, n_tools], outputs=calc_output)


if __name__ == "__main__":
    demo.launch()
