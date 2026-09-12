import { useCallback, useEffect, useState } from "react";
import { RefreshCwIcon, Trash2Icon } from "lucide-react";
import { cn } from "@/lib/utils";
import { getCustomerId } from "@/lib/identity";
import { forgetAll, forgetFact, getFacts, type MemoryFact } from "@/lib/memory";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

const KIND_LABEL: Record<string, string> = {
  preference: "Preference",
  constraint: "Constraint",
  profile: "Profile",
};

function formatLearned(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString();
}

// The customer face of memory: what the agent remembers, and a way to forget it.
export function MemoryView() {
  const [facts, setFacts] = useState<MemoryFact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const reportError = useCallback((err: unknown) => {
    setError(err instanceof Error ? err.message : "Failed to load memory");
  }, []);

  const load = useCallback(
    () =>
      getFacts(getCustomerId())
        .then((items) => {
          setFacts(items);
          setError(null);
        })
        .catch(reportError)
        .finally(() => setLoading(false)),
    [reportError],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  const forget = useCallback(
    (id: string) => {
      setBusyId(id);
      forgetFact(getCustomerId(), id)
        .then(() => setFacts((prev) => prev.filter((fact) => fact.id !== id)))
        .catch(reportError)
        .finally(() => setBusyId(null));
    },
    [reportError],
  );

  const clear = useCallback(() => {
    forgetAll(getCustomerId())
      .then(() => setFacts([]))
      .catch(reportError);
  }, [reportError]);

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4")}>
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold">Memory</h2>
        <span className="text-xs text-muted-foreground">What the agent remembers about you</span>
        <button
          type="button"
          onClick={refresh}
          className="ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <RefreshCwIcon className="size-3" /> Refresh
        </button>
        {facts.length > 1 ? (
          <button
            type="button"
            onClick={clear}
            className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <Trash2Icon className="size-3" /> Forget all
          </button>
        ) : null}
      </div>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}{" "}
          <button type="button" onClick={refresh} className="underline">
            Retry
          </button>
        </p>
      ) : null}

      <section className="flex flex-col gap-1" aria-live="polite">
        <h3 className="text-xs font-semibold text-muted-foreground">Remembered facts</h3>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : facts.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nothing is remembered yet. Tell the agent something durable — a size, a preference, a
            budget — and it will remember it in future chats.
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {facts.map((fact) => (
              <li
                key={fact.id}
                className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm"
              >
                <span className="shrink-0 rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {KIND_LABEL[fact.kind] ?? fact.kind}
                </span>
                <span className="min-w-0 flex-1 break-words">{fact.text}</span>
                <span className="hidden shrink-0 text-xs text-muted-foreground tabular-nums sm:inline">
                  {formatLearned(fact.created_at)}
                </span>
                <button
                  type="button"
                  onClick={() => forget(fact.id)}
                  disabled={busyId === fact.id}
                  aria-label={`Forget: ${fact.text}`}
                  className="shrink-0 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
                >
                  Forget
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
