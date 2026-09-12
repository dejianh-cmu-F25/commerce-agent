// Metrics API client (feature 017).
export type SpanStat = {
  name: string;
  count: number;
  errors: number;
  avg_ms: number;
  p95_ms: number;
};

export type Metrics = {
  window: { spans: number; limit: number };
  spans: SpanStat[];
  tokens: { prompt: number; completion: number; cache_hit: number; cache_miss: number };
  cost_cny: number;
  tools: { ok: number; error: number };
  budget: { currency: string; spent: number; limit: number; remaining: number };
};

export async function getMetrics(): Promise<Metrics> {
  const response = await fetch("/metrics");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as Metrics;
}
