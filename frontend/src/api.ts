// The shape of the control plane's /live/* responses, typed once at the
// boundary so the rest of the app works with trusted data.

export type Outcome = "detected" | "visible_only" | "blind" | "armed";
export type AgentStatus = "nominal" | "targeted" | "observed" | "alerting" | "silent";

export interface Alert {
  rule_id: string;
  technique: string;
  message: string;
}

export interface Step {
  id: string;
  tactic: string;
  name: string;
  agent: string;
  role: string;
  subnet: string;
  technique: string;
  owasp: string;
  course: string;
  effect_kind: string;
  sensors_present: string[];
  narrative: string;
  fired: boolean;
  outcome: Outcome;
  seen_by: string[];
  alerts: Alert[];
}

export interface Agent {
  id: string;
  role: string;
  subnet: string;
  workload: string;
  sensors: string[];
  events: number;
  alerts: number;
  on_path: boolean;
  status: AgentStatus;
  steps: Step[];
  // management-plane facts, the way a VM console presents a host
  os: string;
  ip: string;
  vcpu: number;
  mem_gb: number;
  disk_gb: number;
  power: string;
  uptime_s: number;
  pool: string;
  cpu_pct: number;
  mem_pct: number;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export interface State {
  source: string;
  scenario: Scenario;
  scenarios: Scenario[];
  fleet: { size: number; by_role: Record<string, number> };
  subnets: string[];
  agents: Agent[];
  steps: Step[];
  tally: { detected: number; visible_only: number; blind: number };
  fired: number;
  total: number;
  false_alarms: number;
  benign_events: number;
  beacons_reached_c2: number;
  silent_failure_h2: {
    status_check: Record<string, string>;
    canary_probe: Record<string, string>;
  };
  applog_blindness_h3: { requests_logged: number; host_effects_in_app_log: number };
  capability_matrix_h1: Record<string, Record<string, boolean>>;
}

export interface Vulnerability {
  id: string;
  name: string;
  owasp_2025: string;
  attack: string;
  course: string;
  where: string;
  note: string;
}

async function call<T>(path: string, method: "GET" | "POST" = "GET"): Promise<T> {
  const res = await fetch(path, { method });
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  state: () => call<State>("/live/state"),
  fire: (id: string) => call<State>(`/live/fire/${id}`, "POST"),
  fireAll: () => call<State>("/live/fire-all", "POST"),
  reset: () => call<State>("/live/reset", "POST"),
  scenario: (id: string) => call<State>(`/live/scenario/${id}`, "POST"),
  catalog: () => call<Vulnerability[]>("/catalog"),
};
