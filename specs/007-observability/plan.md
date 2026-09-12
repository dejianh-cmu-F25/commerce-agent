# Implementation Plan: Observability (Structured Traces)

**Branch**: `007-observability` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-observability/spec.md`

## Summary

Add a `Tracer` port with a JSONL adapter; instrument the loop to emit `turn`,
`llm`, and `tool` spans sharing a `trace_id`, with redacted inputs/outputs,
durations, tokens, and cost. Expose `GET /traces` and `GET /traces/{trace_id}`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib `json`, `time`, `threading`; no new packages

**Storage**: append-only JSONL at `observability.trace_file`

**Testing**: `pytest` — unit (tracer), integration (instrumented turn), API

**Target Platform**: server

**Project Type**: web service (observability)

**Performance Goals**: one small append per span; negligible

**Constraints**: never change chat behavior; tolerate a missing/corrupt file

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SL-2 structured traces | `trace_id` spans for turn/llm/tool to `logs/traces.jsonl` | PASS |
| OB-1 trace_id | shared id across spans | PASS |
| OB-2 structured logs only | JSON objects, no prints | PASS |
| OB-3 metrics | latency, tokens, cost, tool status as attributes | PASS |
| OB-5 redacted inputs/outputs | truncation before writing | PASS |
| PB-1 config as contract | `observability` settings validated | PASS |
| PB-2 capability seam | Tracer port + Jsonl/Null providers + loop consumer | PASS |
| P5 contract first | port defined before adapter; injected | PASS |
| P8 reproducible | NullTracer / disabled path | PASS |

OB-4 (web Trace Viewer) is explicitly deferred.

## Project Structure

### Documentation (this feature)

```text
specs/007-observability/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/tracer.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
app/
├── core/
│   ├── types.py             # + Span
│   └── loop.py              # instrument turn/llm/tool spans
├── ports/tracer.py          # NEW: Tracer protocol
└── adapters/tracer_jsonl.py # NEW: JsonlTracer + NullTracer
web/main.py                  # build_tracer; GET /traces, GET /traces/{id}
tests/
├── unit/test_tracer_jsonl.py
└── integration/test_traces_api.py
```

## Complexity Tracking

> No constitution violations; nothing to justify.
