# =============================================================================
# DEMO CASE 3: How MCP Handles Security
# Shows 3 security layers: Transport, Parameter Contract, Input Validation
# Runs 5 live security tests against the server
#
# REQUIRES: simple_mcp_server.py running on port 7860
#   Terminal 1: python simple_mcp_server.py
#   Terminal 2: python demo_case3_security.py
# =============================================================================

import gradio as gr
from smolagents import MCPClient

SERVER_URL = "http://127.0.0.1:7860/gradio_api/mcp/sse"

# ── Security architecture explanation ─────────────────────────────────────────

SECURITY_LAYERS = """\
MCP Security Architecture — 3 Layers
══════════════════════════════════════════════════════

Layer 1 — Transport (SSE)
  • Server binds to 127.0.0.1 by default → localhost only
  • Not reachable from the internet without explicit config
  • External access requires adding auth headers at the SSE layer
  • Endpoint: http://127.0.0.1:7860/gradio_api/mcp/sse

Layer 2 — Parameter Contract (Tool Signature)
  • Every tool declares its inputs via Python type hints
  • Client CANNOT pass undeclared parameters — signature is enforced
  • Example:
      def extract_keywords(url: str, top_n: int = 10) -> dict
      → only url and top_n are accepted, nothing else
  • Malicious extra params are silently ignored or rejected

Layer 3 — Input Validation (Server-Side Guards)
  • URL validated with regex BEFORE any network call:
      re.match(r'^https?://', url.strip())
  • Empty string check before execution
  • All errors returned as clean JSON — server never crashes
  • Each tool is a controlled, bounded operation

Layer 4 — Governance (The MCP Advantage)
  • Server decides WHICH tools are visible to which agents
  • Central point for rate limiting, logging, audit
  • One compromised agent cannot affect other agents' tools
  • Tools can be versioned and updated independently
"""

# ── Test case definitions ─────────────────────────────────────────────────────

TESTS = {
    "T1 — Valid URL (happy path)": {
        "tool": "summarize_page",
        "url": "https://en.wikipedia.org/wiki/Geoffrey_Hinton",
        "top_n": 5,
        "expect": "success",
        "why": "Normal valid request — should execute and return a summary."
    },
    "T2 — Invalid URL (no http scheme)": {
        "tool": "summarize_page",
        "url": "not-a-url",
        "top_n": 5,
        "expect": "error",
        "why": "Server regex guard fires: re.match(r'^https?://', ...) fails."
    },
    "T3 — Empty URL": {
        "tool": "analyze_public_profile",
        "url": "",
        "top_n": 5,
        "expect": "error",
        "why": "Empty input check: 'if not url' returns error before touching network."
    },
    "T4 — Non-HTTP scheme (javascript:)": {
        "tool": "summarize_page",
        "url": "javascript:alert('xss')",
        "top_n": 5,
        "expect": "error",
        "why": "Scheme is not http/https — regex guard blocks it cleanly."
    },
    "T5 — Valid keywords call with top_n": {
        "tool": "extract_keywords",
        "url": "https://en.wikipedia.org/wiki/GPT-4",
        "top_n": 7,
        "expect": "success",
        "why": "Optional parameter top_n passed — only valid because server declared it."
    },
}

def run_test(test_name):
    test = TESTS[test_name]
    log = []

    def sep(): log.append("─" * 55)

    sep()
    log.append(f"  TEST: {test_name}")
    sep()
    log.append(f"  Tool    : {test['tool']}")
    log.append(f"  URL     : '{test['url']}'")
    log.append(f"  top_n   : {test['top_n']}")
    log.append(f"  Why     : {test['why']}")
    log.append(f"  Expect  : {test['expect'].upper()}")
    log.append("")

    result = None
    try:
        client = MCPClient({"url": SERVER_URL})
        tools = client.get_tools()
        tools = tools if isinstance(tools, dict) else {t.name: t for t in tools}

        tool = tools.get(test["tool"])
        if not tool:
            log.append(f"  ✗ Tool '{test['tool']}' not found on server")
            return "\n".join(log), None

        kwargs = {"url": test["url"]}
        if "top_n" in tool.signature.parameters:
            kwargs["top_n"] = int(test["top_n"])

        log.append("  Calling tool on server...")
        result = tool(**kwargs)

        if isinstance(result, dict) and "error" in result:
            log.append(f"\n  [SECURITY]  Server rejected the request")
            log.append(f"              Error → {result['error']}")
            if test["expect"] == "error":
                log.append(f"\n  ✓ PASS — validation worked as expected")
            else:
                log.append(f"\n  ✗ UNEXPECTED — expected success but got error")
        else:
            if test["expect"] == "success":
                log.append(f"\n  ✓ PASS — valid request processed successfully")
            else:
                log.append(f"\n  ✗ UNEXPECTED — expected rejection but got result")

        client.disconnect()

    except Exception as e:
        log.append(f"\n  ✗ Exception: {e}")
        log.append("    Is simple_mcp_server.py running on port 7860?")

    sep()
    return "\n".join(log), result

def run_all_tests():
    all_logs = []
    all_results = {}
    for name in TESTS:
        log, result = run_test(name)
        all_logs.append(log)
        all_results[name] = result
    return "\n\n".join(all_logs), all_results

# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Case 3: MCP Security") as demo:
    gr.Markdown("""
# Case 3: How MCP Handles Security
### Transport → Parameter Contract → Input Validation → Governance
> **Setup:** Run `python simple_mcp_server.py` in another terminal first.
""")

    with gr.Row():
        # ── Architecture panel ────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### Security Architecture")
            arch_btn = gr.Button("Show Security Layers", variant="secondary")
            arch_output = gr.Textbox(label="", lines=28, value=SECURITY_LAYERS)
            arch_btn.click(fn=lambda: SECURITY_LAYERS, outputs=arch_output)

        # ── Live tests panel ──────────────────────────────────
        with gr.Column(scale=2):
            gr.Markdown("### Live Security Tests")

            test_choice = gr.Radio(
                choices=list(TESTS.keys()),
                value=list(TESTS.keys())[0],
                label="Select Test"
            )

            with gr.Row():
                run_one_btn = gr.Button("▶  Run Selected Test", variant="primary")
                run_all_btn = gr.Button("▶▶  Run All Tests", variant="secondary")

            log_output    = gr.Textbox(label="Test Log", lines=16)
            result_output = gr.JSON(label="Server Response")

            run_one_btn.click(
                fn=run_test,
                inputs=test_choice,
                outputs=[log_output, result_output]
            )
            run_all_btn.click(
                fn=run_all_tests,
                outputs=[log_output, result_output]
            )


if __name__ == "__main__":
    demo.launch()
