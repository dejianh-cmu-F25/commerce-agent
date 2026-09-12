# Contract: LLMClient

A **capability seam** (PB-2): Service Definition + Service Provider + Consumer.

- **Definition**: `app/ports/llm.py` — `LLMClient.stream(messages, tools)`
- **Providers**: `app/adapters/deepseek_client.py`, `app/adapters/mock_llm.py`
- **Consumer**: `app/core/loop.py`

## Interface

```python
def stream(
    messages: Sequence[Message],
    tools: Sequence[ToolSpec] = (),
) -> AsyncIterator[TextDelta | ToolCallComplete | Finish]: ...
```

## Guarantees

- Yields zero or more `TextDelta`, then zero or more `ToolCallComplete`, then one
  `Finish`. A provider MUST end with `Finish`.
- Tool call `arguments` are a raw JSON string; the loop parses them defensively.
- A provider MUST NOT raise on a normal completion; transport errors propagate to
  the loop, which ends the turn with an error event.
- The provider MUST NOT know about sessions, tools, or surfaces.
