import { cn } from "@/lib/utils";
import type {
  OrderDetail,
  OrderSummary,
  ReturnableItem,
  ReturnData,
  ReturnDecisionData,
  ReviewItem,
} from "@/lib/transport";

const STATUS_LABEL: Record<string, string> = {
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
  requested: "Requested",
};

function label(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString();
}

// The customer's orders (feature 014). Read-only.
export function OrdersCard({ items }: { items: OrderSummary[] }) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="border-b px-3 py-2 font-medium">Your orders</div>
      <ul>
        {items.map((order) => (
          <li
            key={order.id}
            className="flex items-center gap-3 border-b px-3 py-1.5 last:border-b-0"
          >
            <span className="font-mono">{order.id}</span>
            <span className="rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
              {label(order.status)}
            </span>
            <span className="truncate text-muted-foreground">
              {order.item_count} item{order.item_count === 1 ? "" : "s"} · {formatDate(order.placed_at)}
            </span>
            <span className="ml-auto shrink-0 tabular-nums">${order.total.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// One order's detail: status, items, dates (feature 014). Read-only.
export function OrderCard({ order }: { order: OrderDetail }) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="flex items-center justify-between gap-3 border-b px-3 py-2 font-medium">
        <span className="font-mono">{order.id}</span>
        <span className="rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
          {label(order.status)}
        </span>
      </div>
      <ul>
        {order.items.map((item) => (
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
      <div className="border-t px-3 py-2 text-muted-foreground">
        Placed {formatDate(order.placed_at)} · Delivered {formatDate(order.delivered_at)} · Returns
        within {order.window_days} days
      </div>
    </div>
  );
}

// A recorded return request — never a refund (P3).
export function ReturnCard({ data }: { data: ReturnData }) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="border-b px-3 py-2 font-medium">Return requested</div>
      <div className="flex items-center justify-between gap-3 px-3 py-1.5">
        <span className="truncate">{data.title}</span>
        <span className="shrink-0 text-muted-foreground">×{data.quantity}</span>
      </div>
      <p className="border-t px-3 py-2 text-muted-foreground">
        Order <span className="font-mono">{data.order_id}</span> · within the {data.window_days}-day
        window. No refund is issued yet — support will confirm by email.
      </p>
    </div>
  );
}

// The return proposal and the harness's verdict on it (feature 046). The model
// proposes; the PolicyGate disposes, so this card is where a customer sees both the
// decision and - when the harness refused it - why.
export function ReturnDecisionCard({ data }: { data: ReturnDecisionData }) {
  if (data.accessible === false) {
    return (
      <div className="not-prose mt-2 w-full max-w-md rounded-md border border-dashed text-xs">
        <div className="border-b px-3 py-2 font-medium">Order not available</div>
        <p className="px-3 py-2 text-muted-foreground">
          {data.guidance ?? "You can only see your own orders."}
        </p>
      </div>
    );
  }
  const refused = data.validated === false;
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="flex items-center justify-between gap-3 border-b px-3 py-2 font-medium">
        <span>Return decision</span>
        <span className="rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
          {data.decision ?? "unknown"}
        </span>
      </div>
      <dl className="grid gap-1 px-3 py-2">
        <div className="flex gap-2">
          <dt className="text-muted-foreground">Order</dt>
          <dd className="font-mono">{data.order_id}</dd>
        </div>
        {data.cited_clauses && data.cited_clauses.length > 0 ? (
          <div className="flex gap-2">
            <dt className="text-muted-foreground">Policy</dt>
            <dd className="font-mono">{data.cited_clauses.join(", ")}</dd>
          </div>
        ) : null}
      </dl>
      <p
        className={cn(
          "border-t px-3 py-2",
          refused ? "text-destructive" : "text-muted-foreground",
        )}
      >
        {refused
          ? `The harness rejected this proposal — it is not recorded. ${data.policy ?? ""}`
          : "Proposed only: nothing is approved or refunded here."}
      </p>
    </div>
  );
}

// The order's returnable items, with the refs the model uses (feature 046).
export function ReturnableItemsCard({ items }: { items: ReturnableItem[] }) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="border-b px-3 py-2 font-medium">Returnable items</div>
      <ul>
        {items.map((item, index) => (
          <li
            key={item.fulfillment_line_item_id}
            className="flex items-center gap-3 border-b px-3 py-1.5 last:border-b-0"
          >
            <span className="font-mono text-muted-foreground">ref {index + 1}</span>
            <span className="truncate">{item.title}</span>
            <span className="ml-auto shrink-0 tabular-nums">x{item.quantity}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// The reviews the model actually read: the evidence behind any "customers say" claim.
export function ReviewsCard({ items }: { items: ReviewItem[] }) {
  return (
    <div className="not-prose mt-2 w-full max-w-md rounded-md border text-xs">
      <div className="border-b px-3 py-2 font-medium">Customer reviews</div>
      <ul>
        {items.map((review, index) => (
          <li key={index} className="border-b px-3 py-2 last:border-b-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{review.rating.toFixed(1)}★</span>
              <span className="truncate">{review.title}</span>
              {review.verified ? (
                <span className="ml-auto shrink-0 text-[10px] uppercase tracking-wide text-muted-foreground">
                  verified
                </span>
              ) : null}
            </div>
            <p className="mt-1 text-muted-foreground">{review.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
