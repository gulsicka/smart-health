import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.tools import TOOLS, TOOLS_BY_NAME

MAX_TOOL_ITERATIONS = 5 


async def _run_agent_events(llm, system_prompt: str, query: str):
    llm_with_tools = llm.bind_tools(TOOLS)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]

    for _ in range(MAX_TOOL_ITERATIONS):
        full = None
        async for chunk in llm_with_tools.astream(messages):
            full = chunk if full is None else full + chunk
            if chunk.content:
                yield ("content", chunk.content)

        messages.append(full)

        if not full.tool_calls:
            return

        seen_calls = {}
        for call in full.tool_calls:
            key = (call["name"], json.dumps(call["args"], sort_keys=True))
            if key not in seen_calls:
                yield ("status", f"[calling {call['name']}...]")
                tool_fn = TOOLS_BY_NAME[call["name"]]
                try:
                    result = await tool_fn.ainvoke(call["args"])
                except Exception as e:
                    result = f"Error calling {call['name']}: {e}"
                seen_calls[key] = result if isinstance(result, str) else json.dumps(result, default=str)
            messages.append(ToolMessage(content=seen_calls[key], tool_call_id=call["id"]))
    else:
        yield ("content", "I wasn't able to fully answer that within the allowed number of lookups — try rephrasing or narrowing your question.")


async def run_agent(llm, system_prompt: str, query: str) -> str:
    parts = []
    async for kind, text in _run_agent_events(llm, system_prompt, query):
        if kind == "content":
            parts.append(text)
    return "".join(parts)


async def stream_agent(llm, system_prompt: str, query: str):
    yield ": connected\n\n"
    async for _, text in _run_agent_events(llm, system_prompt, query):
        yield f"data: {text}\n\n"
