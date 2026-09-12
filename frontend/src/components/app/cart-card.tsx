import type { CartItem } from "@/lib/transport";

// Renders the cart and checkout payloads (feature 009). Checkout is a render,
// never a charge (P3).
export function CartCard({
  title,
  items,
  total,
  note,
}: {
  title: string;
  items: CartItem[];
  total: number;
  note?: string;
}) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="flex items-center justify-between border-b px-3 py-2 font-medium">
        <span>{title}</span>
        <span className="tabular-nums">${total.toFixed(2)}</span>
      </div>
      {items.length === 0 ? (
        <p className="px-3 py-2 text-muted-foreground">Your cart is empty.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li
              key={item.product_id}
              className="flex items-center justify-between gap-3 border-b px-3 py-1.5 last:border-b-0"
            >
              <span className="truncate">{item.title}</span>
              <span className="shrink-0 text-muted-foreground">×{item.quantity}</span>
              <span className="shrink-0 tabular-nums">${item.line_total.toFixed(2)}</span>
            </li>
          ))}
        </ul>
      )}
      {note ? <p className="border-t px-3 py-2 text-muted-foreground">{note}</p> : null}
    </div>
  );
}
