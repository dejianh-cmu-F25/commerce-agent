// Opaque customer id for cross-session memory (feature 013). Generated once and
// kept in browser storage; it is not authentication. Falls back to a per-tab id
// when storage is unavailable.
const CUSTOMER_KEY = "commerce-agent.customer";

let fallback = "";

export function getCustomerId(): string {
  try {
    const existing = window.localStorage.getItem(CUSTOMER_KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    window.localStorage.setItem(CUSTOMER_KEY, id);
    return id;
  } catch {
    if (!fallback) fallback = crypto.randomUUID();
    return fallback;
  }
}
