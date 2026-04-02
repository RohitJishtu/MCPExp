# =============================================================================
# DEMO CASE 1: How Does MCP Work?
# Shows the live flow: Connect → Discover → Inspect → Call → Receive
#
# REQUIRES: simple_mcp_server.py running on port 7860
#   Terminal 1: python simple_mcp_server.py
#   Terminal 2: python demo_case1_how_it_works.py
# =============================================================================

import gradio as gr
from smolagents import MCPClient

SERVER_URL = "http://127.0.0.1:7860/gradio_api/mcp/sse"

def run_mcp_flow(tool_choice, url_input, top_n):
    log = []
    result = None

    def sep():
        log.append("─" * 55)

    def step(n, title):
        log.append("")
        log.append(f"[STEP {n}]  {title}")

    sep()
    log.append("  MCP LIVE FLOW DEMO")
    sep()

    # ── STEP 1: Connect ───────────────────────────────────────
    step(1, "Connecting to MCP Server via SSE...")
    log.append(f"          Endpoint → {SERVER_URL}")
    try:
        client = MCPClient({"url": SERVER_URL})
        log.append("          ✓ Connected! (persistent SSE stream open)")
    except Exception as e:
        log.append(f"          ✗ Connection failed: {e}")
        log.append("\n  Is simple_mcp_server.py running on port 7860?")
        return "\n".join(log), None

    # ── STEP 2: Discover ──────────────────────────────────────
    step(2, "Discovering tools from server manifest...")
    raw_tools = client.get_tools()
    tools = raw_tools if isinstance(raw_tools, dict) else {t.name: t for t in raw_tools}
    tool_names = list(tools.keys())
    log.append(f"          ✓ Server returned {len(tool_names)} tool(s):")
    for name in tool_names:
        log.append(f"               • {name}")
    log.append("          (No hardcoding — manifest came from the server)")

    # ── STEP 3: Inspect signature ─────────────────────────────
    step(3, f"Inspecting signature for '{tool_choice}'...")
    tool = tools.get(tool_choice)
    if not tool:
        log.append(f"          ✗ Tool '{tool_choice}' not found in manifest")
        client.disconnect()
        return "\n".join(log), None

    params = list(tool.signature.parameters.keys())
    log.append(f"          ✓ Parameters declared by server: {params}")
    for pname, pobj in tool.signature.parameters.items():
        default = pobj.default
        annotation = pobj.annotation
        default_str = f"  (default={default})" if default is not pobj.empty else ""
        log.append(f"               → {pname}: {annotation}{default_str}")

    # ── STEP 4: Build kwargs ──────────────────────────────────
    step(4, "Building kwargs from discovered signature...")
    kwargs = {}
    if "url" in tool.signature.parameters:
        kwargs["url"] = url_input
        log.append(f"          → url   = '{url_input}'")
    if "top_n" in tool.signature.parameters:
        kwargs["top_n"] = int(top_n)
        log.append(f"          → top_n = {int(top_n)}")
    log.append("          (Client only passes what the server declared)")

    # ── STEP 5: Call & receive ────────────────────────────────
    step(5, "Sending call to server (tool runs remotely)...")
    try:
        result = tool(**kwargs)
        log.append("          ✓ Result received over SSE stream!")
    except Exception as e:
        log.append(f"          ✗ Call failed: {e}")
        client.disconnect()
        return "\n".join(log), None

    # ── Summary ───────────────────────────────────────────────
    log.append("")
    sep()
    log.append("  SUMMARY")
    sep()
    log.append("  The CLIENT sent:  tool name + kwargs")
    log.append("  The SERVER ran:   the actual Python function")
    log.append("  Transport used:   SSE (Server-Sent Events)")
    log.append("  Discovery:        runtime — no hardcoded tool list")
    sep()

    client.disconnect()
    return "\n".join(log), result


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Case 1: How MCP Works") as demo:
    gr.Markdown("""
# Case 1: How MCP Works
### Live flow: Connect → Discover → Inspect → Call → Receive
> **Setup:** Run `python simple_mcp_server.py` in another terminal first.
""")

    with gr.Row():
        tool_choice = gr.Dropdown(
            label="Tool to Demo",
            choices=["analyze_public_profile", "summarize_page", "extract_keywords"],
            value="summarize_page"
        )
        url_input = gr.Textbox(
            label="URL",
            value="https://en.wikipedia.org/wiki/Andrew_Ng"
        )
        top_n = gr.Number(label="Top N  (only used by extract_keywords)", value=5)

    run_btn = gr.Button("▶  Run MCP Flow Step-by-Step", variant="primary", size="lg")

    with gr.Row():
        log_output = gr.Textbox(label="Live Flow Log", lines=22, max_lines=30)
        result_output = gr.JSON(label="Tool Result  (returned from server)")

    run_btn.click(
        fn=run_mcp_flow,
        inputs=[tool_choice, url_input, top_n],
        outputs=[log_output, result_output]
    )


if __name__ == "__main__":
    demo.launch()
