import { useCallback, useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { MessageResponse } from "@/components/ai-elements/message";
import { getReport } from "@/lib/report";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

// The committed evaluation report, rendered read-only (feature 025).
export function ReportView() {
  const [markdown, setMarkdown] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      getReport()
        .then((text) => {
          setMarkdown(text);
          setError(null);
        })
        .catch((err) => setError(err instanceof Error ? err.message : "Failed to load the report"))
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

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4")}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h2 className="text-sm font-semibold">Evaluation report</h2>
        <span className="text-xs text-muted-foreground">
          Retrieval, ablation, reliability, cost, judge
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
      ) : loading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : markdown.trim() === "" ? (
        <p className="text-sm text-muted-foreground">
          No report yet. Generate one with{" "}
          <code className="rounded border px-1">uv run python evals/report.py --write</code>.
        </p>
      ) : (
        <div className="min-w-0 overflow-x-auto text-sm" aria-live="polite">
          <MessageResponse>{markdown}</MessageResponse>
        </div>
      )}
    </div>
  );
}
