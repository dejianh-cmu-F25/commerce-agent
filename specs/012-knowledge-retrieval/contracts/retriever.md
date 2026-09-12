# Contract: Knowledge retrieval

## Port (`app/ports/retriever.py`)

```python
class Retriever(Protocol):
    def retrieve(self, query: str, k: int = 3) -> list[Chunk]: ...
```

- Returns at most `k` chunks with `score > 0`, highest first.
- An empty query or no matches returns `[]`.

## Provider (`app/adapters/retriever_memory.py`)

```python
class InMemoryRetriever:
    def add(self, chunks: list[Chunk]) -> None: ...  # idempotent by chunk id
    def retrieve(self, query: str, k: int = 3) -> list[Chunk]: ...
    def size(self) -> int: ...
```

- TF-IDF over `[a-z0-9]+` tokens; cosine normalization.
- Adding a chunk id that already exists is a no-op (RD-2).

## Ingestion (`app/knowledge/ingest.py`)

```python
def load_chunks(path: str, min_chars: int = 40) -> list[Chunk]: ...
```

- Reads `*.md`; splits on blank lines; ids `"{source}#{index}"`.

## Tool (`app/tools/knowledge.py`)

`search_knowledge(query, k)` → a text result listing `[source] snippet` for the
top chunks, or "No relevant knowledge found."

## Wiring

`build_retriever(settings)` (web) loads `knowledge.path` into an
`InMemoryRetriever`; `register_knowledge_tools(registry, retriever)` registers the
tool.
