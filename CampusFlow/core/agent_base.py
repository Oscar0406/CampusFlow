"""
core/agent_base.py
Generic tool-calling agentic loop.
Every department agent is: make_agent(dept, system_prompt, trace_name)

The LLM decides which tools to call, calls them in sequence, inspects
results, and repeats up to MAX_TOOL_ROUNDS before producing a final reply.
"""
import json
from langsmith import traceable

from core.tools import get_tool_schemas, dispatch_tool
from models.session import Session

MAX_TOOL_ROUNDS = 6


def make_agent(department: str, system_prompt: str, trace_name: str):
    """
    Factory — returns an agent callable:
        agent_fn(extracted_data: dict, session: Session, llm: LLMService) -> dict
    """

    @traceable(name=trace_name)
    def agent_fn(extracted_data: dict, session: Session, llm) -> dict:
        # Merge session user_context into the request data so the LLM
        # knows facts gathered in previous turns (gender, student_id, etc.)
        merged = {**session.user_context, **extracted_data}

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(session.history_for_llm())
        messages.append({
            "role":    "user",
            "content": "Current request context:\n" + json.dumps(merged, indent=2),
        })

        tools = get_tool_schemas(department)
        tool_results: list[dict] = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = llm.complete_with_tools(messages, tools)

            if response.get("type") == "tool_use":
                # Append raw assistant message (required for Groq message history)
                messages.append(response["raw"])

                for call in response["tool_calls"]:
                    try:
                        result = dispatch_tool(call["name"], call["arguments"])
                    except Exception as e:
                        result = {"error": str(e)}

                    tool_results.append({
                        "tool":   call["name"],
                        "args":   call["arguments"],
                        "result": result,
                    })

                    messages.append({
                        "role":         "tool",
                        "tool_call_id": call["id"],
                        "content":      json.dumps(result),
                    })
            else:
                final_text = response.get("content", "")
                break
        else:
            final_text = (
                f"Sorry, I couldn't complete your {department} request after several attempts. "
                "Please try rephrasing or contact the office directly."
            )

        # Extract ticket_id from any WRITE tool result
        ticket_id = next(
            (tr["result"].get("ticket_id") for tr in tool_results if tr["result"].get("ticket_id")),
            None,
        )
        if ticket_id:
            session.tickets[department] = ticket_id

        return {
            "message":      final_text,
            "ticket_id":    ticket_id,
            "tool_results": tool_results,
        }

    agent_fn.__name__ = trace_name
    return agent_fn
