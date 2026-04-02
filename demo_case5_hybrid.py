# =============================================================================
# DEMO CASE 5: Everything Else — Hybrid Routing + A2A + SSE + Gradio's Role
# Shows the hybrid agent pattern with visible routing decisions,
# plus explains A2A, SSE transport choice, and Gradio's MCP role.
#
# REQUIRES:
#   Terminal 1: python mcp_server.py        (sentiment tool on port 7860)
#   Terminal 2: python demo_case5_hybrid.py  (this file)
#   OPENAI_API_KEY must be set in your environment
#
# If no API key is available, the routing logic is demonstrated in mock mode.
# =============================================================================

import os
import gradio as gr

SERVER_URL = "http://127.0.0.1:7860/gradio_api/mcp/sse"

# ── Hybrid agent setup (requires OpenAI key + mcp_server.py running) ──────────

def build_agent():
    """Try to build the real agent. Returns (agent, model, tools) or None."""
    try:
        from smolagents import CodeAgent, MCPClient
        from smolagents.models import OpenAIServerModel
        if not os.getenv("OPENAI_API_KEY"):
            return None, None, None
        mcp_client = MCPClient({"url": SERVER_URL})
        tools = mcp_client.get_tools()
        model = OpenAIServerModel(model_id="gpt-4o")
        agent = CodeAgent(
            tools=tools,
            model=model,
            additional_authorized_imports=["json", "ast"]
        )
        return agent, model, mcp_client
    except Exception:
        return None, None, None


agent, model, mcp_client = build_agent()
LIVE_MODE = agent is not None

DECISION_PROMPT = """\
You are a smart AI assistant.

If the message is vague or conversational (e.g., "Can you help me?", "Hello"),
respond naturally in plain text.

If the message requires a tool, code, or calculation (e.g., "Analyze sentiment of...",
"What is the sentiment of..."), respond using:
<use_tools>
Thoughts: why you need tools
<code>
# Python code here
</code>

User message:
\"\"\"{message}\"\"\"
"""

def smart_agent(message):
    routing_log = []
    result = ""

    routing_log.append(f"Message received: \"{message}\"")
    routing_log.append("")
    routing_log.append("Step 1: Asking LLM — should I use tools?")

    if not LIVE_MODE:
        # ── Mock routing for demo without API key ──────────────
        keywords = ["sentiment", "analyze", "emotion", "feel", "mood", "positive", "negative"]
        needs_tool = any(k in message.lower() for k in keywords)

        if needs_tool:
            routing_log.append("         → LLM returned <use_tools> marker")
            routing_log.append("")
            routing_log.append("Step 2: Routing → TOOL PATH")
            routing_log.append("         → Would invoke CodeAgent + sentiment_analysis tool")
            routing_log.append("         → (Mock mode — no API key set)")
            result = "[Mock] Sentiment analysis would run here via MCP tool."
        else:
            routing_log.append("         → LLM returned plain text (no <use_tools>)")
            routing_log.append("")
            routing_log.append("Step 2: Routing → DIRECT REPLY PATH")
            routing_log.append("         → No tool invocation — saves latency + tokens")
            result = "[Mock] Hello! I'm here to help. What would you like to analyze?"
    else:
        # ── Live routing with real LLM + MCP tool ──────────────
        from smolagents.models import ChatMessage
        llm_reply = model.generate(
            messages=[ChatMessage(role="user", content=DECISION_PROMPT.format(message=message))]
        )
        content = llm_reply.content

        if "<use_tools>" in content and "<code>" in content:
            routing_log.append("         → LLM returned <use_tools> marker ✓")
            routing_log.append("")
            routing_log.append("Step 2: Routing → TOOL PATH")
            routing_log.append("         → Invoking CodeAgent + MCP sentiment_analysis tool")
            try:
                result = str(agent.run(message))
                routing_log.append("         ✓ Tool executed on server, result received")
            except Exception as e:
                result = f"Agent error: {e}"
        else:
            routing_log.append("         → LLM returned plain text (no <use_tools>)")
            routing_log.append("")
            routing_log.append("Step 2: Routing → DIRECT REPLY PATH")
            routing_log.append("         → No tool call — direct response returned")
            result = content.strip()

    routing_log.append("")
    routing_log.append("─" * 50)
    routing_log.append(f"Mode: {'LIVE (real LLM + MCP tool)' if LIVE_MODE else 'MOCK (keyword-based routing)'}")

    return "\n".join(routing_log), result


# ── Static explainer content ──────────────────────────────────────────────────

A2A_CONTENT = """\
A2A — What Comes After MCP
══════════════════════════════════════════════════

Today with MCP:
  Agent  ──MCP──→  Tool Server
  (agent talks to tools)

Future with A2A:
  Agent  ──A2A──→  Agent  ──MCP──→  Tool Server
  (agents delegate to other agents, which use tools)

A2A (Agent-to-Agent) solves:
  • Delegation  — "handle this sub-task for me"
  • Coordination — multiple agents on one problem
  • Specialization — each agent owns a domain

MCP is the foundation A2A builds on.
Tools remain decoupled. Agents become composable.

Your repo's mcp_client.py already hints at this:
  The CodeAgent acts as an orchestrator,
  delegating tool calls to the MCP server.
"""

SSE_CONTENT = """\
Why SSE? The Transport Choice Explained
══════════════════════════════════════════════════

             REST        WebSocket      SSE (MCP)
             ────        ─────────      ─────────
Direction    Pull        Bidirectional  Server pushes
Connection   Per-request Persistent    Persistent
Streaming    ✗           ✓             ✓
Simplicity   High        Medium        High
Reconnect    Manual      Manual        Auto (built-in)

SSE is the right fit for MCP because:
  • Client asks → server streams result back
  • One-way push is all that's needed
  • Simpler than WebSocket
  • Auto-reconnect on disconnect
  • Works through standard HTTP infrastructure

Endpoint in your repo:
  http://127.0.0.1:7860/gradio_api/mcp/sse
"""

GRADIO_CONTENT = """\
Gradio's Role — MCP Without Infrastructure
══════════════════════════════════════════════════

One line turns any Python function into an MCP tool:
  demo.launch(mcp_server=True)

What Gradio does automatically:
  ✓ Generates the tool manifest (name, description, params)
    from Python type hints and docstrings
  ✓ Starts the SSE server
  ✓ Routes tool calls to the correct function
  ✓ Serializes results back to JSON
  ✓ Provides a web UI for manual testing

What you don't have to write:
  ✗ SSE handler
  ✗ JSON schema for parameters
  ✗ Tool manifest authoring
  ✗ Request routing

Compare:
  Without Gradio → ~200 lines of SSE + routing boilerplate
  With Gradio    → 1 flag on demo.launch()
"""


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Case 5: Hybrid + Extras") as demo:
    mode_label = "LIVE MODE (real LLM + MCP)" if LIVE_MODE else "MOCK MODE (no API key / server — routing logic still shown)"
    gr.Markdown(f"""
# Case 5: Everything Else
### Hybrid Routing · A2A · SSE · Gradio's Role
> **Status: {mode_label}**
> To enable live mode: set `OPENAI_API_KEY` and run `mcp_server.py` on port 7860.
""")

    # ── Hybrid routing demo ───────────────────────────────────
    gr.Markdown("## 5a. Hybrid Routing — Agent Decides: Tool or Direct Reply?")
    gr.Markdown("""
The same agent takes two completely different paths based on the message:

| Message | Path | Why |
|---------|------|-----|
| `"Can you help me?"` | Direct reply | Vague — no tool needed |
| `"What is the sentiment of: I love this!"` | Tool path | Specific task → CodeAgent → MCP tool |
""")

    with gr.Row():
        with gr.Column(scale=3):
            msg_input = gr.Textbox(
                label="Your Message",
                placeholder="Try: 'Can you help me?' or 'What is the sentiment of: I love this!'",
                lines=2
            )
            send_btn = gr.Button("▶  Send to Agent", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("**Quick examples:**")
            ex1 = gr.Button("'Can you help me?'")
            ex2 = gr.Button("'What is the sentiment of: I love this!'")
            ex3 = gr.Button("'Hello!'")
            ex4 = gr.Button("'Analyze: This is terrible.'")

    with gr.Row():
        routing_log = gr.Textbox(label="Routing Decision Log", lines=14)
        agent_reply = gr.Textbox(label="Agent Reply", lines=14)

    send_btn.click(fn=smart_agent, inputs=msg_input, outputs=[routing_log, agent_reply])
    ex1.click(fn=lambda: "Can you help me?",                          outputs=msg_input)
    ex2.click(fn=lambda: "What is the sentiment of: I love this!",    outputs=msg_input)
    ex3.click(fn=lambda: "Hello!",                                    outputs=msg_input)
    ex4.click(fn=lambda: "Analyze: This is absolutely terrible.",     outputs=msg_input)

    gr.Markdown("---")

    # ── Three explainer tabs ──────────────────────────────────
    gr.Markdown("## 5b / 5c / 5d. More Context")
    with gr.Tabs():
        with gr.Tab("A2A — What's Next"):
            gr.Textbox(value=A2A_CONTENT, label="", lines=18, interactive=False)
        with gr.Tab("SSE Transport"):
            gr.Textbox(value=SSE_CONTENT, label="", lines=18, interactive=False)
        with gr.Tab("Gradio's Role"):
            gr.Textbox(value=GRADIO_CONTENT, label="", lines=18, interactive=False)


if __name__ == "__main__":
    demo.launch()
