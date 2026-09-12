// Evaluation report client (feature 025).
export async function getReport(): Promise<string> {
  const response = await fetch("/report");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = (await response.json()) as { markdown: string };
  return data.markdown;
}
