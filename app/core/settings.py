"""Configuration loading.

Settings come from ``config/settings.yaml`` and are overridden by environment
variables. Validation happens once at load; a bad value fails loud (PB-1).
"""

from __future__ import annotations

import os
from collections.abc import Callable
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
    # Fallback provider (feature 039, RD-1): empty disables the fallback.
    fallback_provider: Literal["", "deepseek", "openai", "anthropic", "mock"] = ""
    fallback_model: str = ""
    fallback_base_url: str = ""
    fallback_api_key: str = ""


class AgentSettings(BaseModel):
    max_tool_iterations: int = 8
    max_turns: int = 24


class EmbeddingSettings(BaseModel):
    # `hash` is the keyless default (P8); `openai` is the opt-in semantic upgrade.
    provider: Literal["hash", "openai", "ollama", "mock"] = "hash"
    model: str = "text-embedding-3-small"
    dimensions: int = 256
    base_url: str = ""
    api_key: str = ""
    # Vectors are cached by text so re-indexing a catalog (or re-running a
    # benchmark) does not pay for the same embedding twice.
    cache_path: str = "./data/embeddings.sqlite"


class VectorStoreSettings(BaseModel):
    provider: Literal["memory", "chroma"] = "memory"
    persist_directory: str = "./data/chroma"
    collection_name: str = "knowledge"


class RetrievalSettings(BaseModel):
    dense_top_k: int = 20
    sparse_top_k: int = 20
    fusion_top_k: int = 10
    rrf_k: int = 60
    # RRF weights (sparse, dense). Equal weights let the weaker retriever drag the
    # fused ranking down, so these are tuned on a held-out split of the rule set
    # (evals/tune_rrf.py) rather than guessed.
    sparse_weight: float = 1.0
    dense_weight: float = 1.0


class RerankSettings(BaseModel):
    enabled: bool = False
    provider: Literal["none", "cross_encoder", "llm"] = "none"
    top_k: int = 5


class EvaluationSettings(BaseModel):
    enabled: bool = False
    provider: Literal["custom", "ragas"] = "custom"
    metrics: list[str] = Field(default_factory=lambda: ["hit_rate", "mrr", "faithfulness"])
    # Real-model evaluation (feature 023): opt-in, budget-capped.
    seeds: int = Field(default=3, ge=1, le=20)
    pass_k: int = Field(default=3, ge=1, le=20)
    judge: bool = True
    judge_model: str = "deepseek-chat"
    max_cost_cny: float = Field(default=1.0, gt=0)


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
    seed_orders: bool = True


class CatalogSettings(BaseModel):
    """Local discovery retrieval (feature 046 step A).

    The live catalog is searched from a local index (``scripts/sync_catalog.py``).
    ``tfidf`` is keyless (P8); ``hybrid`` fuses it with a real embedding, which
    needs ``embedding.provider`` to be a real provider.
    """

    provider: Literal["tfidf", "hybrid"] = "tfidf"
    index_path: str = "./data/discovery/products.json"
    collection_name: str = "catalog"
    # Widen the retrieval window before mapping ids to live products, so a product
    # that has left the shop does not silently shrink the result set.
    overfetch: int = 4


class ShopifySettings(BaseModel):
    # Real post-purchase system of record (feature 045). Empty = keyless fixture.
    shop: str = ""  # e.g. my-store.myshopify.com
    access_token: str = ""
    api_version: str = "2025-07"


class SafetySettings(BaseModel):
    # Deterministic input guard before the model (feature 028, RW-1).
    input_guard: bool = True
    max_input_chars: int = Field(default=4000, gt=0)


class ResilienceSettings(BaseModel):
    # Graceful fallback per external dependency (feature 031, RD-1).
    fallback_enabled: bool = True


class DataSettings(BaseModel):
    # Boundary data quality (feature 027, RW-2): `repair` normalizes fixable
    # values and skips unusable rows; `strict` fails loud on an invalid row.
    quality: Literal["repair", "strict"] = "repair"


class ReturnsSettings(BaseModel):
    # The machine-readable return window; keep in sync with
    # config/knowledge/amazon-returns.md (feature 046, derived from config/policies/amazon.yaml).
    window_days: int = Field(default=30, gt=0)


class SkillsSettings(BaseModel):
    # Long-tail procedures in ``skills/<name>/SKILL.md`` (feature 019).
    enabled: bool = True
    path: str = "./skills"


class SessionSettings(BaseModel):
    store: Literal["memory", "sqlite"] = "sqlite"
    sqlite_path: str = "./data/db/sessions.sqlite"


class KnowledgeSettings(BaseModel):
    # `memory` is the keyless TF-IDF default; `dense` uses embeddings + vectors.
    provider: Literal["memory", "dense"] = "memory"
    path: str = "./config/knowledge"
    top_k: int = 3
    min_chars: int = 40


class ReviewsSettings(BaseModel):
    # Local real review store (feature 046, from Amazon Reviews'23).
    path: str = "./data/reviews/reviews.sqlite"


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
    catalog: CatalogSettings = Field(default_factory=CatalogSettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)
    reviews: ReviewsSettings = Field(default_factory=ReviewsSettings)
    returns: ReturnsSettings = Field(default_factory=ReturnsSettings)
    skills: SkillsSettings = Field(default_factory=SkillsSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    shopify: ShopifySettings = Field(default_factory=ShopifySettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    resilience: ResilienceSettings = Field(default_factory=ResilienceSettings)


def _to_bool(raw: str) -> bool:
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"expected a boolean, got {raw!r}")


# Environment variables that override the YAML file.
_ENV_OVERRIDES: dict[str, tuple[str, str, Callable[[str], object]]] = {
    "LLM_PROVIDER": ("llm", "provider", str),
    "LLM_MODEL": ("llm", "model", str),
    "LLM_BASE_URL": ("llm", "base_url", str),
    "LLM_API_KEY": ("llm", "api_key", str),
    "LLM_FALLBACK_PROVIDER": ("llm", "fallback_provider", str),
    "LLM_FALLBACK_MODEL": ("llm", "fallback_model", str),
    "LLM_FALLBACK_BASE_URL": ("llm", "fallback_base_url", str),
    "LLM_FALLBACK_API_KEY": ("llm", "fallback_api_key", str),
    "EMBEDDING_PROVIDER": ("embedding", "provider", str),
    "EMBEDDING_MODEL": ("embedding", "model", str),
    "EMBEDDING_BASE_URL": ("embedding", "base_url", str),
    "EMBEDDING_API_KEY": ("embedding", "api_key", str),
    "VECTOR_STORE_PROVIDER": ("vector_store", "provider", str),
    "LOG_LEVEL": ("observability", "log_level", str),
    "TRACE_FILE": ("observability", "trace_file", str),
    "WEB_HOST": ("web", "host", str),
    "WEB_PORT": ("web", "port", int),
    "STOREFRONT_PROVIDER": ("storefront", "provider", str),
    "STOREFRONT_SQLITE_PATH": ("storefront", "sqlite_path", str),
    "STOREFRONT_SEED_ORDERS": ("storefront", "seed_orders", _to_bool),
    "DATA_QUALITY": ("data", "quality", str),
    "SAFETY_INPUT_GUARD": ("safety", "input_guard", _to_bool),
    "SAFETY_MAX_INPUT_CHARS": ("safety", "max_input_chars", int),
    "RESILIENCE_FALLBACK_ENABLED": ("resilience", "fallback_enabled", _to_bool),
    "SHOPIFY_SHOP": ("shopify", "shop", str),
    "SHOPIFY_ACCESS_TOKEN": ("shopify", "access_token", str),
    "SHOPIFY_API_VERSION": ("shopify", "api_version", str),
    "RETURNS_WINDOW_DAYS": ("returns", "window_days", int),
    "SESSION_STORE": ("session", "store", str),
    "SESSION_SQLITE_PATH": ("session", "sqlite_path", str),
    "CATALOG_PROVIDER": ("catalog", "provider", str),
    "CATALOG_INDEX_PATH": ("catalog", "index_path", str),
    "KNOWLEDGE_PROVIDER": ("knowledge", "provider", str),
    "KNOWLEDGE_PATH": ("knowledge", "path", str),
    "REVIEWS_PATH": ("reviews", "path", str),
    "MEMORY_PROVIDER": ("memory", "provider", str),
    "MEMORY_SQLITE_PATH": ("memory", "sqlite_path", str),
    "SKILLS_ENABLED": ("skills", "enabled", _to_bool),
    "SKILLS_PATH": ("skills", "path", str),
    "EVAL_SEEDS": ("evaluation", "seeds", int),
    "EVAL_PASS_K": ("evaluation", "pass_k", int),
    "EVAL_JUDGE": ("evaluation", "judge", _to_bool),
    "EVAL_JUDGE_MODEL": ("evaluation", "judge_model", str),
    "EVAL_MAX_COST_CNY": ("evaluation", "max_cost_cny", float),
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
