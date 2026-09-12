"""Unit tests for memory recall/injection in the loop (feature 013, SL-1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.adapters.cli_sink import ListSink
from app.adapters.memory_memory import InMemoryMemoryStore
from app.adapters.mock_llm import MockLLMClient, text_turn
from app.core.loop import Agent
from app.core.session import MemoryNote, Session, derive_messages
from app.core.settings import AgentSettings
from app.core.types import MemoryFact
from app.tools.registry import ToolRegistry

SYSTEM = "You are a test assistant."


def _fact(customer: str, text: str, kind: str = "profile") -> MemoryFact:
    return MemoryFact(
        id=uuid4().hex[:12],
        customer_id=customer,
        kind=kind,
        text=text,
        created_at=datetime.now(UTC).isoformat(),
    )


def _agent(turns, memory=None) -> Agent:
    return Agent(
        llm=MockLLMClient(turns),
        tools=ToolRegistry(),
        settings=AgentSettings(max_turns=4),
        system_prompt=SYSTEM,
        memory=memory,
    )


async def test_recall_is_injected_once_and_logged():
    store = InMemoryMemoryStore()
    store.add(_fact("c1", "Wears size M"))
    agent = _agent([text_turn("ok"), text_turn("ok")], memory=store)
    session = Session(id="s1", customer_id="c1")

    await agent.stream_turn(session, "hi", ListSink())
    await agent.stream_turn(session, "hello again", ListSink())

    notes = [event for event in session.events if isinstance(event, MemoryNote)]
    assert len(notes) == 1  # injected once, not once per turn
    assert notes[0].facts == ["Wears size M"]

    # The fact is in the model context, derived from the log (SL-1).
    messages = agent.build_request(session)
    assert "Wears size M" in messages[0].content


async def test_no_memory_leaves_context_unchanged():
    agent = _agent([text_turn("ok")])
    session = Session(id="s2", customer_id="c2")
    baseline = derive_messages(session, SYSTEM)

    await agent.stream_turn(session, "hi", ListSink())

    assert not any(isinstance(event, MemoryNote) for event in session.events)
    assert agent.build_request(session)[0].content == baseline[0].content


async def test_extraction_stores_grounded_facts():
    store = InMemoryMemoryStore()
    agent = _agent([text_turn("ok")], memory=store)
    session = Session(id="s3", customer_id="c3")

    await agent.stream_turn(session, "I usually wear size M and I'm allergic to wool", ListSink())

    texts = {fact.text for fact in store.list("c3")}
    assert "Wears size M" in texts
    assert "Avoids wool" in texts


async def test_no_customer_runs_memory_disabled():
    store = InMemoryMemoryStore()
    store.add(_fact("c4", "Wears size M"))
    agent = _agent([text_turn("ok")], memory=store)
    session = Session(id="s4")  # no customer id

    await agent.stream_turn(session, "I like tents", ListSink())

    assert not any(isinstance(event, MemoryNote) for event in session.events)
    assert store.list("") == []
