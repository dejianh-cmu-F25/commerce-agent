# Tasks: Agent Core Loop

- [x] T001 Define provider-neutral types (`app/core/types.py`)
- [x] T002 Define agent events and `to_wire` (`app/core/events.py`)
- [x] T003 Implement the session log and `derive_messages` (`app/core/session.py`)
- [x] T004 Define the `LLMClient` port (`app/ports/llm.py`)
- [x] T005 Define the `EventSink` port (`app/ports/event_sink.py`)
- [x] T006 Implement the DeepSeek adapter (`app/adapters/deepseek_client.py`)
- [x] T007 Implement the mock adapter (`app/adapters/mock_llm.py`)
- [x] T008 Implement the tool registry and guarded execution (`app/tools/registry.py`)
- [x] T009 Implement `search_products` over the demo catalog (`app/tools/catalog.py`)
- [x] T010 Implement the loop with the SL-1 guard (`app/core/loop.py`)
- [x] T011 Implement the CLI and list sinks (`app/adapters/cli_sink.py`)
- [x] T012 Implement the web app with SSE and health checks (`web/main.py`)
- [x] T013 Implement the chat page and component registry (`web/static/`)
- [x] T014 Write unit tests for the loop (`tests/unit/test_loop.py`)
- [x] T015 Add Dockerfile, compose, CI, and the PR template
