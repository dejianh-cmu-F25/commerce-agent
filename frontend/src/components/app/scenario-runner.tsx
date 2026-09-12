import { useCallback, useEffect, useState } from "react";
import { PlayIcon, RefreshCwIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getScenarios,
  runScenarios,
  type ScenarioInfo,
  type ScenarioResult,
} from "@/lib/scenarios";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

// The Scenario Runner (WV-4): run the keyless gold scenarios and see pass/fail.
export function ScenarioRunner() {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [results, setResults] = useState<Record<string, ScenarioResult>>({});
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      getScenarios()
        .then((items) => {
          setScenarios(items);
          setError(null);
        })
        .catch((err) => setError(err instanceof Error ? err.message : "Failed to load scenarios"))
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

  const run = useCallback(() => {
    setRunning(true);
    setError(null);
    runScenarios()
      .then((items) => setResults(Object.fromEntries(items.map((item) => [item.name, item]))))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to run scenarios"))
      .finally(() => setRunning(false));
  }, []);

  const total = Object.keys(results).length;
  const passed = Object.values(results).filter((result) => result.ok).length;

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4")}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h2 className="text-sm font-semibold">Scenarios</h2>
        <span className="text-xs text-muted-foreground">
          Keyless gold cases over the real loop
        </span>
        <div className="ml-auto flex items-center gap-2">
          {total > 0 ? (
            <span className="text-xs text-muted-foreground tabular-nums" aria-live="polite">
              {passed}/{total} passed
            </span>
          ) : null}
          <button
            type="button"
            onClick={refresh}
            className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <RefreshCwIcon className="size-3" /> Refresh
          </button>
          <button
            type="button"
            onClick={run}
            disabled={running || loading || scenarios.length === 0}
            className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
          >
            <PlayIcon className="size-3" /> {running ? "Running…" : "Run all"}
          </button>
        </div>
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
      ) : scenarios.length === 0 ? (
        <p className="text-sm text-muted-foreground">No scenarios.</p>
      ) : (
        <ul className="flex flex-col gap-2" aria-live="polite">
          {scenarios.map((scenario) => {
            const result = results[scenario.name];
            const tools = result?.tools ?? scenario.expect_tools;
            const components = result?.components ?? scenario.expect_components;
            return (
              <li key={scenario.name} className="rounded-md border px-3 py-2 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{scenario.name}</span>
                  {result ? (
                    <span
                      className={cn(
                        "rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide",
                        result.ok ? "text-muted-foreground" : "text-destructive",
                      )}
                    >
                      {result.ok ? "Pass" : "Fail"}
                    </span>
                  ) : null}
                  <span className="text-muted-foreground">{scenario.user_text}</span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                  <span>tools:</span>
                  {tools.length === 0 ? (
                    <em>none</em>
                  ) : (
                    tools.map((tool) => (
                      <code key={tool} className="rounded border px-1">
                        {tool}
                      </code>
                    ))
                  )}
                  <span className="ml-2">components:</span>
                  {components.length === 0 ? (
                    <em>none</em>
                  ) : (
                    components.map((component) => (
                      <code key={component} className="rounded border px-1">
                        {component}
                      </code>
                    ))
                  )}
                </div>
                {result && !result.ok ? (
                  <ul className="mt-1 list-disc pl-5 text-xs text-destructive">
                    {result.failures.map((failure) => (
                      <li key={failure}>{failure}</li>
                    ))}
                  </ul>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
