"""
Chatbot LLM Integration — Databricks GPT-5.5 with Tool Calling
===============================================================

Implements the tool-call loop for the ontology chatbot:
  1. Send user question + tool schemas to GPT-5.5 via Databricks AI Gateway
  2. If model requests tool calls, execute them against the rdflib graph
  3. Feed results back as tool-role messages
  4. Repeat until the model returns a final text answer (no more tool calls)

Uses the OpenAI-compatible chat/completions endpoint with the ``tools``
parameter.  Sequential tool calling only — parallel_tool_calls is disabled
per Databricks documentation.

SCOPE ASSUMPTION (POC):
    Operates on whatever rdflib Graph is currently in the Streamlit session.
    No cross-session persistence.  See chatbot_tools.py header for details.
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests
from rdflib import Graph

from chatbot_tools import (
    TOOL_SCHEMAS,
    find_entity,
    get_entity_details,
    get_relationships,
    get_results,
    compare_entities,
)
from vector_db import query_vector_db
from web_search import web_search


# ---------------------------------------------------------------------------
# System prompt — grounding instructions
# ---------------------------------------------------------------------------

CHATBOT_SYSTEM_PROMPT = """\
You are a research assistant that answers questions using up to three connected sources:
1. An ontology graph extracted from ingested scientific documents (structured entities/relationships).
2. A vector database over the same ingested documents (semantic text chunks).
3. The live web (for current external information).

RULES — follow these strictly:
1. ORCHESTRATION & TRUST HIERARCHY (check enabled sources in this priority order):
   - FIRST: For questions about entities, relationships, or quantitative results from the ingested documents, use the Graph tools (e.g., find_entity, get_relationships).
   - SECOND: If the Graph tools fail to find the requested entities or relationships, OR for questions about document nuance/methodology, fallback to use query_vector_db on the document text.
   - THIRD: For questions explicitly about current state, recent news, or something clearly outside the document scope, use web_search.
2. If the enabled sources are insufficient to answer, say so and name which additional source would help (e.g. "I can't answer this with only the Graph source enabled; enabling Web search would let me check for recent updates"). DO NOT fall through to a disabled source or hallucinate.
3. If sources genuinely conflict (e.g., the patent says Phase 1, but the web says Phase 3), surface BOTH claims explicitly and flag the discrepancy. Do NOT silently prefer one.
4. CITE YOUR SOURCES. Every factual claim must be traceable. Label each claim inline (e.g. "[Graph]", "[Vector DB, chunk_id]", "[Web, dated 2026-05-12]") based on the tool results.
5. If find_entity returns multiple candidates, present ALL of them to the user to disambiguate.
6. Only answer using information returned by your tool calls.
"""

# Maximum number of tool-call rounds before giving up
MAX_TOOL_ROUNDS = 8

# Timeout for Databricks API calls (seconds)
API_TIMEOUT = 120


# ---------------------------------------------------------------------------
# Databricks API call with tool support
# ---------------------------------------------------------------------------

def _call_databricks_chat_with_tools(
    host: str,
    token: str,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """
    Call the Databricks chat/completions endpoint with optional tools.

    Returns the raw parsed JSON response dict.  Tries multiple endpoint
    URL patterns (matching the fallback logic in app.py's
    call_databricks_chat).

    Raises RuntimeError on total failure.
    """
    host = host.rstrip("/")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Endpoint URL candidates + specific payload shapes
    payloads = [
        (
            f"{host}/serving-endpoints/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
        ),
        (
            f"{host}/serving-endpoints/{model}/invocations",
            {"messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
        ),
        (
            f"{host}/ai-gateway/openai/v1/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
        ),
        (
            f"{host}/ai-gateway/mlflow/v1/chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
        ),
    ]

    # Inject tool parameters into all payloads
    if tools:
        for _, p in payloads:
            p["tools"] = tools
            p["tool_choice"] = "auto"
            p["parallel_tool_calls"] = False
            # Required for GPT-5.5 tool calling on /chat/completions
            p["reasoning_effort"] = "none"

    last_error = "Unknown Databricks API error."
    for url, payload in payloads:
        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=API_TIMEOUT
            )
            if resp.status_code == 404:
                last_error = f"Endpoint not found: {url}"
                continue
            if not resp.ok:
                last_error = f"Databricks API {resp.status_code}: {resp.text[:500]}"
                continue
            return resp.json()
        except requests.RequestException as exc:
            last_error = f"Request to {url} failed: {exc}"

    raise RuntimeError(last_error)


def _parse_assistant_message(response: dict) -> dict[str, Any]:
    """
    Parse the assistant's message from a Databricks chat/completions response.

    Returns a dict with:
      - "content": str | None  (the text answer, if any)
      - "tool_calls": list[dict] | None  (requested tool calls, if any)
      - "raw_message": dict  (the full message object for conversation history)
    """
    choices = response.get("choices", [])
    if not choices:
        # Try alternative response shapes
        # Responses API shape
        output = response.get("output", [])
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict):
                    if item.get("type") == "message":
                        content_parts = item.get("content", [])
                        text = ""
                        for part in content_parts:
                            if isinstance(part, dict) and part.get("type") == "output_text":
                                text += part.get("text", "")
                        if text:
                            return {
                                "content": text,
                                "tool_calls": None,
                                "raw_message": {"role": "assistant", "content": text},
                            }
        return {
            "content": response.get("content", ""),
            "tool_calls": None,
            "raw_message": {"role": "assistant", "content": str(response)},
        }

    choice = choices[0]
    message = choice.get("message", {})

    content = message.get("content")
    if isinstance(content, list):
        # Handle structured content (list of parts)
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        content = "".join(text_parts) if text_parts else None

    tool_calls = message.get("tool_calls")

    return {
        "content": content if content and str(content).strip() else None,
        "tool_calls": tool_calls,
        "raw_message": message,
    }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def execute_tool_call(
    g: Graph, tool_name: str, arguments: dict[str, Any]
) -> Any:
    """
    Dispatch a tool call to the appropriate chatbot_tools function.

    Parameters
    ----------
    g : rdflib.Graph
        The session ontology graph.
    tool_name : str
        Name of the tool (must match one of the six defined tools).
    arguments : dict
        The arguments parsed from the model's tool_call.

    Returns
    -------
    Any
        JSON-serializable result from the tool function.
    """
    dispatch = {
        "find_entity": lambda: find_entity(g, arguments.get("name", "")),
        "get_entity_details": lambda: get_entity_details(g, arguments.get("uri", "")),
        "get_relationships": lambda: get_relationships(
            g, arguments.get("uri", ""), arguments.get("relation_type")
        ),
        "get_results": lambda: get_results(
            g,
            compound=arguments.get("compound"),
            target=arguments.get("target"),
            metric_type=arguments.get("metric_type"),
            max_value=arguments.get("max_value"),
            min_value=arguments.get("min_value"),
        ),
        "compare_entities": lambda: compare_entities(
            g, arguments.get("uri_a", ""), arguments.get("uri_b", "")
        ),
        "query_vector_db": lambda: query_vector_db(
            arguments.get("query", ""), arguments.get("top_k", 5)
        ),
        "web_search": lambda: web_search(arguments.get("query", "")),
    }

    func = dispatch.get(tool_name)
    if func is None:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return func()
    except Exception as exc:
        return {"error": f"Tool execution failed: {str(exc)}"}


# ---------------------------------------------------------------------------
# Main chatbot loop — streaming (generator) version
# ---------------------------------------------------------------------------

# Progress step descriptors yielded by the generator
STEP_SENDING   = "sending"     # Sending request to LLM
STEP_TOOL_REQ  = "tool_req"    # LLM requested a tool call
STEP_TOOL_EXEC = "tool_exec"   # Executing a tool
STEP_TOOL_DONE = "tool_done"   # Tool execution finished
STEP_FEEDING   = "feeding"     # Feeding tool result back to LLM
STEP_DONE      = "done"        # Final answer received
STEP_ERROR     = "error"       # Error occurred


def _summarize_result(result: Any) -> str:
    """One-line summary of a tool result for status display."""
    if isinstance(result, list):
        return f"{len(result)} result{'s' if len(result) != 1 else ''} returned"
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error'][:80]}"
        name = result.get("normalizedName", result.get("entity_class", ""))
        if name:
            return f"Found: {name}"
        return f"{len(result)} fields returned"
    return str(result)[:80]


def _format_args_short(arguments: dict) -> str:
    """Short human-readable summary of tool arguments."""
    parts = []
    for k, v in arguments.items():
        if v is not None and k != "_raw":
            parts.append(f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}")
    return ", ".join(parts) if parts else ""


def run_chatbot_loop_stream(
    host: str,
    token: str,
    model: str,
    graph: Graph,
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    enabled_tool_schemas: list[dict[str, Any]] | None = None,
):
    """
    Generator version of the chatbot tool-call loop.

    Yields progress tuples at each stage so the UI can show live updates:

        (step_type, label, detail, progress_frac, tool_trace_so_far)

    - step_type: one of STEP_* constants
    - label: short human-readable label for the current step
    - detail: longer detail string (tool name, arguments, result summary)
    - progress_frac: float 0.0–1.0 estimating overall progress
    - tool_trace_so_far: list of completed trace entries

    The final yield has step_type == STEP_DONE and detail == final_answer.
    """
    messages: list[dict] = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tool_trace: list[dict] = []

    for round_num in range(1, MAX_TOOL_ROUNDS + 1):
        # ── Progress: sending to LLM ──
        progress = min(0.05 + (round_num - 1) * 0.12, 0.90)
        yield (
            STEP_SENDING,
            f"Round {round_num}: Sending to GPT-5.5…",
            f"Sending {len(messages)} messages with {len(enabled_tool_schemas)} tool schemas",
            progress,
            list(tool_trace),
        )

        try:
            response = _call_databricks_chat_with_tools(
                host=host,
                token=token,
                model=model,
                messages=messages,
                tools=enabled_tool_schemas,
            )
        except RuntimeError as exc:
            yield (
                STEP_ERROR,
                "API Error",
                f"⚠️ Failed to reach Databricks API: {exc}",
                progress,
                list(tool_trace),
            )
            yield (
                STEP_DONE,
                "Error",
                f"⚠️ Failed to reach the Databricks API: {exc}",
                1.0,
                list(tool_trace),
            )
            return

        parsed = _parse_assistant_message(response)

        # ── Final answer (no tool calls) ──
        if parsed["tool_calls"] is None:
            final_answer = parsed["content"] or "(No response from model)"
            yield (
                STEP_DONE,
                "Answer received",
                final_answer,
                1.0,
                list(tool_trace),
            )
            return

        # ── Process tool calls ──
        messages.append(parsed["raw_message"])

        for tc in parsed["tool_calls"]:
            tool_call_id = tc.get("id", f"call_{round_num}")
            func_info = tc.get("function", {})
            tool_name = func_info.get("name", "unknown")
            args_raw = func_info.get("arguments", "{}")

            if isinstance(args_raw, str):
                try:
                    arguments = json.loads(args_raw)
                except json.JSONDecodeError:
                    arguments = {"_raw": args_raw}
            else:
                arguments = args_raw

            args_short = _format_args_short(arguments)

            # ── Progress: tool call requested ──
            yield (
                STEP_TOOL_REQ,
                f"Round {round_num}: Model requested `{tool_name}`",
                f"{tool_name}({args_short})",
                min(progress + 0.03, 0.92),
                list(tool_trace),
            )

            # ── Progress: executing tool ──
            yield (
                STEP_TOOL_EXEC,
                f"Round {round_num}: Executing `{tool_name}`…",
                f"Running {tool_name}({args_short}) against the graph",
                min(progress + 0.05, 0.93),
                list(tool_trace),
            )

            result = execute_tool_call(graph, tool_name, arguments)

            trace_entry = {
                "round": round_num,
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
            }
            tool_trace.append(trace_entry)

            # ── Progress: tool done ──
            summary = _summarize_result(result)
            yield (
                STEP_TOOL_DONE,
                f"Round {round_num}: `{tool_name}` → {summary}",
                summary,
                min(progress + 0.08, 0.94),
                list(tool_trace),
            )

            result_str = json.dumps(result, default=str)
            if len(result_str) > 12000:
                result_str = result_str[:12000] + '... (truncated)'

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result_str,
            })

            # ── Progress: feeding back ──
            yield (
                STEP_FEEDING,
                f"Round {round_num}: Returning results to GPT-5.5…",
                f"Feeding {len(result_str)} chars of tool output back",
                min(progress + 0.10, 0.95),
                list(tool_trace),
            )

    # Exhausted rounds
    yield (
        STEP_DONE,
        "Max rounds reached",
        "I ran out of tool-call rounds trying to answer this question. "
        "Please try rephrasing or asking a simpler question.",
        1.0,
        list(tool_trace),
    )


def run_chatbot_loop(
    host: str,
    token: str,
    model: str,
    graph: Graph,
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    enabled_tool_schemas: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Convenience wrapper: runs the streaming loop to completion and returns
    (final_answer, tool_trace).  Use run_chatbot_loop_stream() directly
    for real-time progress updates.
    """
    answer = "(No response)"
    trace: list[dict] = []
    gen = run_chatbot_loop_stream(
        host=host,
        token=token,
        model=model,
        graph=graph,
        user_message=user_message,
        history=history,
        enabled_tool_schemas=enabled_tool_schemas,
    )
    for step_type, label, detail, progress, current_trace in gen:
        trace = current_trace
        if step_type == STEP_DONE:
            answer = detail
    return answer, trace
