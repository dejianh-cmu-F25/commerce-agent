export type TraceSummary = {
  trace_id: string;
  start_ms: number;
  duration_ms: number;
  span_count: number;
  status: string;
};

export type Span = {
  trace_id: string;
  span_id: string;
  parent_id: string | null;
  name: string;
  start_ms: number;
  end_ms: number;
  status: string;
  attributes: Record<string, unknown>;
};

export type SpanNode = { span: Span; depth: number; children: SpanNode[] };

export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

// Order spans by start time and nest by parent_id. A span whose parent is
// missing is treated as a root (never dropped).
export function buildSpanTree(spans: Span[]): SpanNode[] {
  const byId = new Map<string, SpanNode>();
  for (const span of spans) byId.set(span.span_id, { span, depth: 0, children: [] });

  const roots: SpanNode[] = [];
  for (const node of byId.values()) {
    const parent = node.span.parent_id ? byId.get(node.span.parent_id) : undefined;
    if (parent) parent.children.push(node);
    else roots.push(node);
  }

  const sort = (nodes: SpanNode[], depth: number): void => {
    nodes.sort((a, b) => a.span.start_ms - b.span.start_ms);
    for (const node of nodes) {
      node.depth = depth;
      sort(node.children, depth + 1);
    }
  };
  sort(roots, 0);
  return roots;
}

export async function listTraces(limit = 50): Promise<TraceSummary[]> {
  const response = await fetch(`/traces?limit=${limit}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const body = (await response.json()) as { traces: TraceSummary[] };
  return body.traces;
}

export async function getTrace(traceId: string): Promise<Span[]> {
  const response = await fetch(`/traces/${traceId}`);
  if (response.status === 404) throw new Error("Trace not found");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const body = (await response.json()) as { spans: Span[] };
  return body.spans;
}
