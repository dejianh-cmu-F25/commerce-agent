import { useCallback, useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { getMetrics, type Metrics } from "@/lib/metrics";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-[8rem] flex-1 rounded-md border px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-lg tabular-nums">{value}</div>
    </div>
  );
}

// Harness metrics over the recent traces (OB-3). Read-only.
export function MetricsView() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      getMetrics()
        .then((data) => {
          setMetrics(data);
          setError(null);
        })
        .catch((err) => setError(err instanceof Error ? err.message : "Failed to load metrics"))
        .finally(() => setLoading(false)),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  const empty = metrics !== null && metrics.window.spans === 0;

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4")}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h2 className="text-sm font-semibold">Metrics</h2>
        <span className="text-xs text-muted-foreground">
          Latency, tokens, cost, and tools over recent traces
        </span>
        <button
          type="button"
          onClick={refresh}
          className="ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <RefreshCwIcon className="size-3" /> Refresh
        </button>
      </div>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}{" "}
          <button type="button" onClick={refresh} className="underline">
            Retry
          </button>
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : empty ? (
        <p className="text-sm text-muted-foreground">
          No activity yet. Send a message or run a scenario, then refresh.
        </p>
      ) : metrics ? (
        <div className="flex flex-col gap-4" aria-live="polite">
          <div className="flex flex-wrap gap-2">
            <Tile label="Spans (window)" value={String(metrics.window.spans)} />
            <Tile label="Prompt tokens" value={metrics.tokens.prompt.toLocaleString()} />
            <Tile label="Completion tokens" value={metrics.tokens.completion.toLocaleString()} />
            <Tile
              label="Cache hits"
              value={`${metrics.tokens.cache_hit.toLocaleString()} / ${(
                metrics.tokens.cache_hit + metrics.tokens.cache_miss
              ).toLocaleString()}`}
            />
            <Tile label="Cost (window)" value={`¥${metrics.cost_cny.toFixed(4)}`} />
            <Tile label="Tools ok / error" value={`${metrics.tools.ok} / ${metrics.tools.error}`} />
            <Tile
              label={`Budget (${metrics.budget.currency})`}
              value={`¥${metrics.budget.spent.toFixed(2)} / ¥${metrics.budget.limit.toFixed(2)}`}
            />
          </div>

          <section className="flex flex-col gap-1">
            <h3 className="text-xs font-semibold text-muted-foreground">Latency by span</h3>
            <div className="overflow-x-auto rounded-md border text-xs">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="px-3 py-1.5 font-medium">Span</th>
                    <th className="px-3 py-1.5 text-right font-medium">Count</th>
                    <th className="px-3 py-1.5 text-right font-medium">Errors</th>
                    <th className="px-3 py-1.5 text-right font-medium">Avg ms</th>
                    <th className="px-3 py-1.5 text-right font-medium">p95 ms</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.spans.map((span) => (
                    <tr key={span.name} className="border-b last:border-b-0">
                      <td className="px-3 py-1.5 font-mono">{span.name}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">{span.count}</td>
                      <td
                        className={cn(
                          "px-3 py-1.5 text-right tabular-nums",
                          span.errors > 0 && "text-destructive",
                        )}
                      >
                        {span.errors}
                      </td>
                      <td className="px-3 py-1.5 text-right tabular-nums">
                        {span.avg_ms.toFixed(1)}
                      </td>
                      <td className="px-3 py-1.5 text-right tabular-nums">
                        {span.p95_ms.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
