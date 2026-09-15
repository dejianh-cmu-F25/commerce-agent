import { cn } from "@/lib/utils";

export type Budget = { spent_cny: number; limit_cny: number; remaining_cny: number };

export function BudgetMeter({ budget }: { budget: Budget | null }) {
  const spent = budget?.spent_cny ?? 0;
  const limit = budget?.limit_cny ?? 0;
  const pct = limit > 0 ? Math.min(100, (spent / limit) * 100) : 0;
  const over = pct >= 100;

  return (
    <div
      className="flex items-center gap-2 text-xs text-muted-foreground tabular-nums"
      title={limit > 0 ? "Spend against the configured budget" : "Model spend so far"}
    >
      <span>
        {budget
          ? limit > 0
            ? `budget: ¥${spent.toFixed(4)} / ¥${limit.toFixed(2)}`
            : `spend: ¥${spent.toFixed(4)}`
          : "spend: —"}
      </span>
      {limit > 0 ? (
        <span
          className="h-1.5 w-20 overflow-hidden rounded-full bg-border sm:w-28"
          role="progressbar"
          aria-label="Budget used"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(pct)}
        >
          <span
            className={cn(
              "block h-full transition-[width] duration-150",
              over ? "bg-destructive" : "bg-primary",
            )}
            style={{ width: `${pct}%` }}
          />
        </span>
      ) : null}
    </div>
  );
}
