from ast import For  # Note: This import seems like a copy-paste error and isn't used; you can remove it if not needed.
import requests
from bs4 import BeautifulSoup

# Wrappers for chat models (e.g., ChatOpenAI for conversational models).
# Embeddings (for turning text into vectors, useful for search or similarity).
# Other OpenAI tools like DALL-E for image generation.

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage
)
from langchain.tools import tool

# SystemMessage: For system prompts (instructions to the AI).
# HumanMessage: For user inputs.
# ToolMessage: For responses from tools (functions the AI calls). We're using these to structure the conversation flow, as LangChain's tool-calling agents rely on message histories to track interactions.




# =================================================
# Tools : @tool: This decorator registers the function as a tool in LangChain. It allows the AI model to "call" this function during reasoning. We're using it to make two tools available to the agent.
# =================================================
@tool
def fetch_public_profile(url: str) -> str:
    """
    Fetches and cleans readable text from a public web page URL.
    Use this tool when the input is a URL.
    """
    response = requests.get(
        url,
        timeout=5,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    return text[:12_000]  # Increased limit for better analysis (from 50 to 12,000 to match original intent)


@tool
def read_text_input(text: str) -> str:
    """
    Accepts raw text input directly.
    Use this tool when the user already provides text.
    """
    return text[:12_000]  # Standardized limit for consistency



# =================================================
# LLM (tool-aware)
# =================================================
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
).bind_tools([fetch_public_profile, read_text_input])


# =================================================
# Agent (with show_think flag)
# =================================================
def run_agent(user_input: str, show_think: bool = False) -> str:
    system_prompt = (
        "You are a helpful AI agent specializing in professional profiles.\n"
        "Decide whether to fetch data from a URL or use provided text.\n"
        "Analyze the profile content and extract key details.\n"
        "Then, identify and list relevant people, such as:\n"
        "- Collaborators or co-founders mentioned\n"
        "- Similar experts in the same field\n"
        "- Influential figures or mentors referenced\n"
        "Provide a clear summary of the profile and a bulleted list of 3-5 relevant people with brief reasons why they are relevant.\n"
    )

    if show_think:
        system_prompt += (
            "\nWhen responding, include a section called "
            "'Reasoning Summary' explaining at a high level:\n"
            "- why you chose a tool (if any)\n"
            "- what you did\n"
            "- what you observed\n"
            "Do NOT reveal hidden chain-of-thought.\n"
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input),
    ]

    # First model call (may request a tool)
    assistant_msg = llm.invoke(messages)
    # assistant_msg = llm.invoke(messages): Calls the model with the messages. The model may respond directly or request a tool. We're using this to get the AI's initial response.



    # The if-elif for tool names is hardcoded—LangChain can automate this with Tool.from_function and AgentExecutor.

    if assistant_msg.tool_calls:
        tool_call = assistant_msg.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name == "fetch_public_profile":
            observation = fetch_public_profile.invoke(tool_args)
        elif tool_name == "read_text_input":
            observation = read_text_input.invoke(tool_args)
        else:
            observation = "ERROR: Unknown tool"

    # LangChain's tool-calling is inherently dynamic in that the model decides the tool (based on the prompt and input), but the code has to handle the invocation. The manual if-elif is just one way to do that—it's not leveraging LangChain's full dynamism for routing.


        # Protocol-correct flow
        messages.append(assistant_msg)
        messages.append(
            ToolMessage(
                content=observation,
                tool_call_id=tool_call["id"]
            )
        )

        final_msg = llm.invoke(messages)


        return final_msg.content

    return assistant_msg.content


# =================================================
# Demo
# =================================================
if __name__ == "__main__":
    # print("=== WITHOUT THINKING ===")
    # print(run_agent("https://en.wikipedia.org/wiki/Andrew_Ng"))

    # print("\n=== WITH THINKING ===")
    # print(run_agent("https://en.wikipedia.org/wiki/Andrew_Ng", show_think=True))

    print("\n=== WITH THINKING ===")
    print(run_agent("https://en.wikipedia.org/wiki/Andrew_Ng", show_think=True))

    # print(
    #     run_agent(
    #         """
    #         Rohit Jishtu is a Machine Learning Engineer working on 
    #         enterprise AI platforms and agentic AI systems.""",
    #         show_think=True
    #     )
    # )