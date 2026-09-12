// Customer memory API client (feature 013).
export type MemoryFact = {
  id: string;
  kind: string;
  text: string;
  created_at: string;
};

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as T;
}

export async function getFacts(customerId: string): Promise<MemoryFact[]> {
  const response = await fetch(`/memory/${encodeURIComponent(customerId)}`);
  const data = await readJson<{ facts: MemoryFact[] }>(response);
  return data.facts;
}

export async function forgetFact(customerId: string, factId: string): Promise<void> {
  const response = await fetch(
    `/memory/${encodeURIComponent(customerId)}/facts/${encodeURIComponent(factId)}`,
    { method: "DELETE" },
  );
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
}

export async function forgetAll(customerId: string): Promise<number> {
  const response = await fetch(`/memory/${encodeURIComponent(customerId)}`, {
    method: "DELETE",
  });
  const data = await readJson<{ removed: number }>(response);
  return data.removed;
}
