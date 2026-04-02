# =============================================================================
# DEMO CASE 4: How MCP Does Discovery
# Shows dynamic tool discovery — client adapts when server adds a new tool,
# with ZERO changes to client code.
#
# DEMO STEPS:
#   Step A — Run V1 server (3 tools):
#     Terminal 1: python demo_case4_server_v1.py
#     Terminal 2: python demo_case4_discovery.py
#     → Click "Refresh & Discover Tools" — shows 3 tools
#
#   Step B — Swap to V2 server (4 tools, adds word_count):
#     Stop Terminal 1, then: python demo_case4_server_v2.py
#     → Click "Refresh & Discover Tools" again — shows 4 tools automatically
#     → No change to this client file at all
# =============================================================================

import gradio as gr
from smolagents import MCPClient

SERVER_URL = "http://127.0.0.1:7860/gradio_api/mcp/sse"

DISCOVERY_EXPLAINER = """\
How MCP Discovery Works
══════════════════════════════════════════════════

1. Client connects to the SSE endpoint
       http://127.0.0.1:7860/gradio_api/mcp/sse

2. Server sends a tool manifest over the stream
       [{name, description, parameters, types}, ...]

3. Client builds its UI from the manifest — no hardcoding

4. Each tool's signature is inspected at call time
       params = tool.signature.parameters
       → only pass what the server declared

KEY POINT:
  When the server adds a new tool (e.g. word_count),
  the client discovers it on next connection.
  No client code change required.

Compare to tight coupling:
  llm.bind_tools([fetch_public_profile, read_text_input])
  ↑ hardcoded list — adding a tool = modify the agent
"""

# ── State shared across callbacks ─────────────────────────────────────────────
_tools = {}

def discover_tools():
    """Connect to server and return discovered tool info."""
    log = []
    manifest_rows = []

    try:
        log.append("Connecting to MCP server...")
        client = MCPClient({"url": SERVER_URL})

        raw = client.get_tools()
        _tools.clear()
        _tools.update(raw if isinstance(raw, dict) else {t.name: t for t in raw})

        log.append(f"✓ Connected! Found {len(_tools)} tool(s):\n")
        for name, tool in _tools.items():
            params = list(tool.signature.parameters.keys())
            defaults = {
                k: v.default
                for k, v in tool.signature.parameters.items()
                if v.default is not v.empty
            }
            log.append(f"  • {name}")
            log.append(f"      params   : {params}")
            if defaults:
                log.append(f"      defaults : {defaults}")
            log.append("")
            manifest_rows.append([name, str(params), str(defaults)])

        client.disconnect()

    except Exception as e:
        log.append(f"✗ Could not connect: {e}")
        log.append("  Is the server running on port 7860?")

    tool_names = list(_tools.keys())
    dropdown_update = gr.update(choices=tool_names, value=tool_names[0] if tool_names else None)
    return "\n".join(log), manifest_rows, dropdown_update


def call_selected_tool(tool_name, url_input, top_n):
    if not _tools:
        return "Run discovery first.", None

    tool = _tools.get(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not in discovered list.", None

    kwargs = {}
    if "url" in tool.signature.parameters:
        kwargs["url"] = url_input
    if "top_n" in tool.signature.parameters:
        kwargs["top_n"] = int(top_n)

    try:
        result = tool(**kwargs)
        log = (
            f"Called: {tool_name}\n"
            f"Args:   {kwargs}\n"
            f"Result: see JSON panel →"
        )
        return log, result
    except Exception as e:
        return f"Error: {e}", None


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Case 4: MCP Discovery") as demo:
    gr.Markdown("""
# Case 4: How MCP Does Discovery
### No hardcoding — client adapts automatically when server changes
> **Demo:** Start with `demo_case4_server_v1.py` (3 tools), discover.
> Then swap to `demo_case4_server_v2.py` (4 tools), discover again — client picks up `word_count` automatically.
""")

    with gr.Row():
        # ── Explainer ─────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### How It Works")
            gr.Textbox(value=DISCOVERY_EXPLAINER, label="", lines=22, interactive=False)

        # ── Discovery panel ───────────────────────────────────
        with gr.Column(scale=2):
            gr.Markdown("### Live Discovery")
            discover_btn = gr.Button("🔍  Refresh & Discover Tools", variant="primary", size="lg")

            discovery_log = gr.Textbox(label="Discovery Log", lines=12)
            manifest_table = gr.Dataframe(
                headers=["Tool Name", "Parameters", "Defaults"],
                label="Discovered Tool Manifest",
                interactive=False
            )

            gr.Markdown("---")
            gr.Markdown("### Call a Discovered Tool")

            tool_dropdown = gr.Dropdown(label="Select Tool", choices=[], interactive=True)
            url_input     = gr.Textbox(label="URL", value="https://en.wikipedia.org/wiki/Andrew_Ng")
            top_n_input   = gr.Number(label="Top N  (for extract_keywords)", value=5)
            call_btn      = gr.Button("▶  Call Tool", variant="secondary")

            call_log    = gr.Textbox(label="Call Log", lines=4)
            call_result = gr.JSON(label="Result")

    discover_btn.click(
        fn=discover_tools,
        outputs=[discovery_log, manifest_table, tool_dropdown]
    )

    call_btn.click(
        fn=call_selected_tool,
        inputs=[tool_dropdown, url_input, top_n_input],
        outputs=[call_log, call_result]
    )


if __name__ == "__main__":
    demo.launch()
