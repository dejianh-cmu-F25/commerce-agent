"""DeepSeek LLM adapter (OpenAI-compatible chat completions).

Service Provider for :class:`app.ports.llm.LLMClient`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from openai import AsyncOpenAI

from app.core.settings import LLMSettings
from app.core.types import (
    Finish,
    LLMEvent,
    Message,
    TextDelta,
    ToolCall,
    ToolCallComplete,
    ToolSpec,
    Usage,
)


def _to_openai_messages(messages: Sequence[Message]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m.role == "assistant" and m.tool_calls:
            out.append(
                {
                    "role": "assistant",
                    "content": m.content or None,
                    "tool_calls": [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {"name": c.name, "arguments": c.arguments},
                        }
                        for c in m.tool_calls
                    ],
                }
            )
        elif m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        else:
            out.append({"role": m.role, "content": m.content})
    return out


def _to_openai_tools(tools: Sequence[ToolSpec]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


class DeepSeekClient:
    """Streams completions from a DeepSeek (OpenAI-compatible) endpoint."""

    def __init__(self, settings: LLMSettings) -> None:
        if not settings.api_key:
            raise ValueError("LLM api_key is empty; set LLM_API_KEY in .env")
        self._client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url or None,
        )
        self._model = settings.model
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens

    async def stream(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
    ) -> AsyncIterator[LLMEvent]:
        kwargs: dict = {
            "model": self._model,
            "messages": _to_openai_messages(messages),
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = _to_openai_tools(tools)

        tool_buffers: dict[int, dict[str, str]] = {}
        finish_reason = "stop"
        usage = None

        response = await self._client.chat.completions.create(**kwargs)
        async for chunk in response:
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta
            if delta and delta.content:
                yield TextDelta(delta.content)
            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    buf = tool_buffers.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        buf["id"] = tc.id
                    if tc.function and tc.function.name:
                        buf["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        buf["args"] += tc.function.arguments
            if choice.finish_reason:
                finish_reason = choice.finish_reason

        for index in sorted(tool_buffers):
            buf = tool_buffers[index]
            if not buf["name"]:
                continue
            yield ToolCallComplete(
                ToolCall(
                    id=buf["id"] or f"call_{index}",
                    name=buf["name"],
                    arguments=buf["args"] or "{}",
                )
            )
        if usage is not None:
            yield Usage(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                cache_hit_tokens=getattr(usage, "prompt_cache_hit_tokens", 0) or 0,
                cache_miss_tokens=getattr(usage, "prompt_cache_miss_tokens", 0) or 0,
            )
        yield Finish(finish_reason)
