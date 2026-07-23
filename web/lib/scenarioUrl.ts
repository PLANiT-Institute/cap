export type ScenarioQuery = {
  firm?: string;
  mode?: string;
  intervention?: string;
  route?: string;
};

const KEYS = ["firm", "mode", "intervention", "route"] as const;

export function readScenarioQuery(): ScenarioQuery {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  return Object.fromEntries(
    KEYS.map((key) => [key, params.get(key) ?? undefined]).filter(([, value]) => value),
  );
}

export function scenarioHref(pathname: string, values: ScenarioQuery) {
  const params = new URLSearchParams();
  KEYS.forEach((key) => {
    const value = values[key];
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

export function replaceScenarioQuery(values: ScenarioQuery) {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  KEYS.forEach((key) => {
    const value = values[key];
    if (value) params.set(key, value);
    else params.delete(key);
  });
  const query = params.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`);
}
