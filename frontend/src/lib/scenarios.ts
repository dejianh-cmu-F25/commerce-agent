// Scenario Runner API client (feature 016).
export type ScenarioInfo = {
  name: string;
  user_text: string;
  expect_tools: string[];
  expect_components: string[];
};

export type ScenarioResult = {
  name: string;
  ok: boolean;
  failures: string[];
  tools: string[];
  components: string[];
};

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as T;
}

export async function getScenarios(): Promise<ScenarioInfo[]> {
  const response = await fetch("/scenarios");
  const data = await readJson<{ scenarios: ScenarioInfo[] }>(response);
  return data.scenarios;
}

export async function runScenarios(): Promise<ScenarioResult[]> {
  const response = await fetch("/scenarios/run", { method: "POST" });
  const data = await readJson<{ results: ScenarioResult[] }>(response);
  return data.results;
}
