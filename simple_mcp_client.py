import gradio as gr
from smolagents import MCPClient

# ------------------------------------------------------------
# CONNECT TO MCP SERVER
# ------------------------------------------------------------

client = MCPClient(
    {"url": "http://127.0.0.1:7860/gradio_api/mcp/sse"}
)

# ------------------------------------------------------------
# DISCOVER & NORMALIZE TOOLS
# ------------------------------------------------------------

raw_tools = client.get_tools()

# Normalize tools to dict[name -> tool]
if isinstance(raw_tools, dict):
    tools = raw_tools
else:
    tools = {tool.name: tool for tool in raw_tools}

tool_names = list(tools.keys())
print("✅ Tools discovered:", tool_names)

# ------------------------------------------------------------
# SAFE TOOL CALLER
# ------------------------------------------------------------

def call_tool(tool_name, url, top_n):
    if tool_name not in tools:
        return {
            "error": f"Tool '{tool_name}' not found",
            "available_tools": tool_names
        }

    tool = tools[tool_name]

    try:
        # Check tool signature to decide args
        params = tool.signature.parameters

        kwargs = {}
        if "url" in params:
            kwargs["url"] = url

        if "top_n" in params:
            kwargs["top_n"] = int(top_n)

        return tool(**kwargs)

    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# GRADIO UI
# ------------------------------------------------------------

with gr.Blocks(title="Simple MCP Client") as demo:

    gr.Markdown("## 🔌 Simple MCP Client")
    gr.Markdown("Select a tool, provide inputs, and run it.")

    tool_selector = gr.Dropdown(
        label="Select Tool",
        choices=tool_names,
        value=tool_names[0]
    )

    url_input = gr.Textbox(
        label="URL",
        placeholder="https://en.wikipedia.org/wiki/Andrew_Ng"
    )

    top_n_input = gr.Number(
        label="Top N Keywords (only if supported)",
        value=10,
        visible=False
    )

    output = gr.JSON(label="Result")

    # Show top_n only if tool supports it
    def toggle_top_n(tool_name):
        tool = tools.get(tool_name)
        if not tool:
            return gr.update(visible=False)
        return gr.update(visible=("top_n" in tool.signature.parameters))

    tool_selector.change(
        fn=toggle_top_n,
        inputs=tool_selector,
        outputs=top_n_input
    )

    run = gr.Button("Run")

    run.click(
        fn=call_tool,
        inputs=[tool_selector, url_input, top_n_input],
        outputs=output
    )

# ------------------------------------------------------------
# LAUNCH
# ------------------------------------------------------------

if __name__ == "__main__":
    demo.launch()
