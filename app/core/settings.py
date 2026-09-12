"""Configuration loading.

Settings come from ``config/settings.yaml`` and are overridden by environment
variables. Validation happens once at load; a bad value fails loud (PB-1).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

DEFAULT_CONFIG_PATH = "config/settings.yaml"


class LLMSettings(BaseModel):
    provider: Literal["deepseek", "openai", "anthropic", "mock"] = "deepseek"
    model: str = "deepseek-chat"
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.0
    max_tokens: int = 4096


class AgentSettings(BaseModel):
    max_tool_iterations: int = 8
    max_turns: int = 24


class EmbeddingSettings(BaseModel):
    provider: Literal["openai", "ollama", "mock"] = "openai"
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    base_url: str = ""
    api_key: str = ""


class VectorStoreSettings(BaseModel):
    provider: Literal["chroma", "memory"] = "chroma"
    persist_directory: str = "./data/chroma"
    collection_name: str = "knowledge"


class RetrievalSettings(BaseModel):
    dense_top_k: int = 20
    sparse_top_k: int = 20
    fusion_top_k: int = 10
    rrf_k: int = 60


class RerankSettings(BaseModel):
    enabled: bool = False
    provider: Literal["none", "cross_encoder", "llm"] = "none"
    top_k: int = 5


class EvaluationSettings(BaseModel):
    enabled: bool = False
    provider: Literal["custom", "ragas"] = "custom"
    metrics: list[str] = Field(default_factory=lambda: ["hit_rate", "mrr", "faithfulness"])


class ObservabilitySettings(BaseModel):
    log_level: str = "INFO"
    trace_enabled: bool = True
    trace_file: str = "./logs/traces.jsonl"
    trace_max_attr_len: int = 500


class ChunkRefinerSettings(BaseModel):
    use_llm: bool = False


class MetadataEnricherSettings(BaseModel):
    use_llm: bool = False


class IngestionSettings(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    splitter: Literal["recursive", "semantic", "fixed"] = "recursive"
    chunk_refiner: ChunkRefinerSettings = Field(default_factory=ChunkRefinerSettings)
    metadata_enricher: MetadataEnricherSettings = Field(default_factory=MetadataEnricherSettings)


class MemorySettings(BaseModel):
    provider: Literal["memory", "sqlite"] = "sqlite"
    sqlite_path: str = "./data/db/memory.sqlite"
    extraction: Literal["deterministic"] = "deterministic"
    retention_days: int = 365


class BudgetSettings(BaseModel):
    enabled: bool = True
    currency: str = "CNY"
    total_limit: float = 10.0
    usd_to_cny: float = 7.25
    input_cache_miss_per_1m: float = 0.30
    input_cache_hit_per_1m: float = 0.006
    output_per_1m: float = 1.20
    state_file: str = "./data/budget.json"


class WebSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class StorefrontSettings(BaseModel):
    provider: Literal["memory", "sqlite"] = "sqlite"
    sqlite_path: str = "./data/db/storefront.sqlite"


class SessionSettings(BaseModel):
    store: Literal["memory", "sqlite"] = "sqlite"
    sqlite_path: str = "./data/db/sessions.sqlite"


class KnowledgeSettings(BaseModel):
    provider: Literal["memory"] = "memory"
    path: str = "./config/knowledge"
    top_k: int = 3
    min_chars: int = 40


class Settings(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    rerank: RerankSettings = Field(default_factory=RerankSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    ingestion: IngestionSettings = Field(default_factory=IngestionSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)
    web: WebSettings = Field(default_factory=WebSettings)
    storefront: StorefrontSettings = Field(default_factory=StorefrontSettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)


# Environment variables that override the YAML file.
_ENV_OVERRIDES: dict[str, tuple[str, str, type]] = {
    "LLM_PROVIDER": ("llm", "provider", str),
    "LLM_MODEL": ("llm", "model", str),
    "LLM_BASE_URL": ("llm", "base_url", str),
    "LLM_API_KEY": ("llm", "api_key", str),
    "EMBEDDING_PROVIDER": ("embedding", "provider", str),
    "EMBEDDING_MODEL": ("embedding", "model", str),
    "EMBEDDING_BASE_URL": ("embedding", "base_url", str),
    "EMBEDDING_API_KEY": ("embedding", "api_key", str),
    "LOG_LEVEL": ("observability", "log_level", str),
    "TRACE_FILE": ("observability", "trace_file", str),
    "WEB_HOST": ("web", "host", str),
    "WEB_PORT": ("web", "port", int),
    "STOREFRONT_PROVIDER": ("storefront", "provider", str),
    "STOREFRONT_SQLITE_PATH": ("storefront", "sqlite_path", str),
    "SESSION_STORE": ("session", "store", str),
    "SESSION_SQLITE_PATH": ("session", "sqlite_path", str),
    "KNOWLEDGE_PROVIDER": ("knowledge", "provider", str),
    "KNOWLEDGE_PATH": ("knowledge", "path", str),
    "MEMORY_PROVIDER": ("memory", "provider", str),
    "MEMORY_SQLITE_PATH": ("memory", "sqlite_path", str),
}


class SettingsError(RuntimeError):
    """Raised when configuration is missing or invalid."""


def _apply_env_overrides(data: dict) -> None:
    for env_name, (section, key, caster) in _ENV_OVERRIDES.items():
        raw = os.environ.get(env_name)
        if raw is None or raw == "":
            continue
        try:
            value = caster(raw)
        except (TypeError, ValueError) as exc:
            raise SettingsError(f"Invalid {env_name}={raw!r}: {exc}") from exc
        data.setdefault(section, {})[key] = value


def load_settings(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load and validate settings, applying environment overrides."""
    config_path = Path(path)
    if not config_path.exists():
        raise SettingsError(f"Config file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise SettingsError(f"Invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SettingsError(f"Config root must be a mapping in {config_path}")

    _apply_env_overrides(raw)

    try:
        return Settings.model_validate(raw)
    except ValidationError as exc:
        raise SettingsError(f"Invalid configuration:\n{exc}") from exc
