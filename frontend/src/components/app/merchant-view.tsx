import { useCallback, useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  applyChange,
  getChanges,
  getInventory,
  type InventoryItem,
  type MerchantChange,
} from "@/lib/merchant";

const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

// The operator face: inventory + staged changes with human approval (P3).
export function MerchantView() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [changes, setChanges] = useState<MerchantChange[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apply = useCallback((data: { inventory: InventoryItem[]; changes: MerchantChange[] }) => {
    setInventory(data.inventory);
    setChanges(data.changes);
    setError(null);
  }, []);

  const reportError = useCallback((err: unknown) => {
    setError(err instanceof Error ? err.message : "Failed to load merchant data");
  }, []);

  const load = useCallback(
    () =>
      Promise.all([getInventory(), getChanges()])
        .then(([items, staged]) => apply({ inventory: items, changes: staged }))
        .catch(reportError)
        .finally(() => setLoading(false)),
    [apply, reportError],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  const approve = useCallback(
    (id: string) => {
      applyChange(id)
        .then(() => load())
        .catch(reportError);
    },
    [load, reportError],
  );

  return (
    <div className={cn(CONTAINER, "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4")}>
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold">Merchant</h2>
        <button
          type="button"
          onClick={refresh}
          className="ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <RefreshCwIcon className="size-3" /> Refresh
        </button>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {loading ? <p className="text-sm text-muted-foreground">Loading…</p> : null}

      <section className="flex flex-col gap-1">
        <h3 className="text-xs font-semibold text-muted-foreground">Pending changes</h3>
        {!loading && changes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No pending changes.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {changes.map((change) => (
              <li
                key={change.id}
                className="flex items-center gap-3 rounded-md border px-3 py-2 text-xs"
              >
                <span className="font-mono">{change.product_id}</span>
                <span>{change.kind}</span>
                <span className="text-muted-foreground tabular-nums">
                  {change.old_value.toFixed(2)} → {change.new_value.toFixed(2)}
                </span>
                <button
                  type="button"
                  onClick={() => approve(change.id)}
                  className="ml-auto rounded-md border px-2 py-1 hover:bg-accent"
                >
                  Approve
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-1">
        <h3 className="text-xs font-semibold text-muted-foreground">Inventory</h3>
        <div className="overflow-hidden rounded-md border text-xs">
          {inventory.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 border-b px-3 py-2 last:border-b-0"
            >
              <span className="font-mono">{item.id}</span>
              <span className="truncate">{item.title}</span>
              <span className="ml-auto tabular-nums">${item.price.toFixed(2)}</span>
              <span
                className={cn(
                  "w-16 text-right tabular-nums",
                  item.stock === 0 ? "text-destructive" : "text-muted-foreground",
                )}
              >
                stock {item.stock}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
