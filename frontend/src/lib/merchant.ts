export type InventoryItem = {
  id: string;
  title: string;
  price: number;
  stock: number;
  in_stock: boolean;
};

export type MerchantChange = {
  id: string;
  product_id: string;
  kind: "price" | "stock";
  old_value: number;
  new_value: number;
  status: string;
  created_at: string;
};

export async function getInventory(): Promise<InventoryItem[]> {
  const response = await fetch("/merchant/inventory");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return ((await response.json()) as { items: InventoryItem[] }).items;
}

export async function getChanges(): Promise<MerchantChange[]> {
  const response = await fetch("/merchant/changes");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return ((await response.json()) as { changes: MerchantChange[] }).changes;
}

export async function applyChange(id: string): Promise<MerchantChange> {
  const response = await fetch(`/merchant/changes/${id}/apply`, { method: "POST" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return ((await response.json()) as { change: MerchantChange }).change;
}
