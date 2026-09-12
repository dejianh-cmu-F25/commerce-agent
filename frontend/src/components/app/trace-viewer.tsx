import { Fragment, useCallback, useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  buildSpanTree,
  formatDuration,
  getTrace,
  listTraces,
  type Span,
  type SpanNode,
  type TraceSummary,
} from "@/lib/traces";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

function flatten(nodes: SpanNode[]): SpanNode[] {
  const out: SpanNode[] = [];
  const walk = (items: SpanNode[]): void => {
    for (const node of items) {
      out.push(node);
      walk(node.children);
    }
  };
  walk(nodes);
  return out;
}

function statusClass(status: string): string {
  return status === "error" ? "text-destructive" : "text-muted-foreground";
}

function SpanRow({ node }: { node: SpanNode }) {
  const { span, depth } = node;
  const attributes = Object.entries(span.attributes);
  return (
    <div className="rounded-md border px-3 py-2 text-xs" style={{ marginLeft: depth * 16 }}>
      <div className="flex items-center gap-3">
        <span className="font-medium">{span.name}</span>
        <span className="text-muted-foreground tabular-nums">
          {formatDuration(span.end_ms - span.start_ms)}
        </span>
        <span className={cn("ml-auto rounded-full border px-2", statusClass(span.status))}>
          {span.status}
        </span>
      </div>
      {attributes.length > 0 ? (
        <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-muted-foreground">
          {attributes.map(([key, value]) => (
            <Fragment key={key}>
              <dt className="font-mono">{key}</dt>
              <dd className="truncate">{String(value)}</dd>
            </Fragment>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

export function TraceViewer() {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyTraces = useCallback((list: TraceSummary[]) => {
    setTraces(list);
    if (list.length === 0) {
      setSelected(null);
      setSpans([]);
    }
    setError(null);
  }, []);

  const reportError = useCallback((err: unknown) => {
    setError(err instanceof Error ? err.message : "Failed to load traces");
  }, []);

  useEffect(() => {
    let cancelled = false;
    listTraces()
      .then((list) => {
        if (!cancelled) applyTraces(list);
      })
      .catch((err) => {
        if (!cancelled) reportError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [applyTraces, reportError]);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    listTraces().then(applyTraces).catch(reportError).finally(() => setLoading(false));
  }, [applyTraces, reportError]);

  const select = useCallback(async (traceId: string) => {
    setSelected(traceId);
    setSpans([]);
    setError(null);
    try {
      setSpans(await getTrace(traceId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trace");
    }
  }, []);

  const tree = buildSpanTree(spans);

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4")}>
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold">Traces</h2>
        <button
          type="button"
          onClick={() => void refresh()}
          className="ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <RefreshCwIcon className="size-3" /> Refresh
        </button>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {loading ? <p className="text-sm text-muted-foreground">Loading traces…</p> : null}

      {!loading && !error && traces.length === 0 ? (
        <p className="text-sm text-muted-foreground">No traces yet — send a message in Chat.</p>
      ) : null}

      {traces.length > 0 ? (
        <ul className="flex flex-col gap-1">
          {traces.map((trace) => (
            <li key={trace.trace_id}>
              <button
                type="button"
                onClick={() => void select(trace.trace_id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md border px-3 py-2 text-left text-xs",
                  selected === trace.trace_id ? "border-primary bg-accent" : "hover:bg-accent",
                )}
              >
                <span className="font-mono">{trace.trace_id.slice(0, 8)}</span>
                <span className="text-muted-foreground tabular-nums">
                  {formatDuration(trace.duration_ms)}
                </span>
                <span className="text-muted-foreground">{trace.span_count} spans</span>
                <span className={cn("ml-auto rounded-full border px-2", statusClass(trace.status))}>
                  {trace.status}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {selected ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-semibold text-muted-foreground">
            Timeline · {selected.slice(0, 8)}
          </h3>
          {spans.length === 0 && !error ? (
            <p className="text-sm text-muted-foreground">Loading spans…</p>
          ) : null}
          <div className="flex flex-col gap-1">
            {flatten(tree).map((node) => (
              <SpanRow key={node.span.span_id} node={node} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
