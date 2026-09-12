import {
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
import type { Source } from "@/lib/transport";

// Grounding sources (P4): rendered inside the AI Elements Sources container.
export function SourcesList({ items }: { items: Source[] }) {
  if (!items.length) return null;
  return (
    <Sources>
      <SourcesTrigger count={items.length} />
      <SourcesContent>
        {items.map((item) => (
          <div
            key={item.id}
            className="flex w-64 items-center justify-between gap-2 rounded-md border px-2 py-1 text-xs"
          >
            <span className="truncate text-foreground">{item.title}</span>
            <span className="shrink-0 text-muted-foreground tabular-nums">
              ${item.price.toFixed(2)}
              {!item.in_stock && " · out of stock"}
            </span>
          </div>
        ))}
      </SourcesContent>
    </Sources>
  );
}
