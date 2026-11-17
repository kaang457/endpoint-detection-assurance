import type { Outcome, AgentStatus } from "./api";

export const OUTCOME: Record<Outcome, { tag: string; verdict: string; detail: string }> = {
  detected: { tag: "Detected", verdict: "Alert fired", detail: "a detection rule matched this step" },
  visible_only: { tag: "Observed", verdict: "No alert — observed only", detail: "a sensor recorded it, but no rule matched" },
  blind: { tag: "Blind", verdict: "No alert — blind", detail: "no sensor recorded the host effect" },
  armed: { tag: "Armed", verdict: "Not fired yet", detail: "fire this step to measure it" },
};

export const STATUS: Record<AgentStatus, string> = {
  nominal: "Nominal",
  targeted: "Targeted",
  observed: "Observed",
  alerting: "Alerting",
  silent: "Silent",
};

export const SUBNET: Record<string, [string, string]> = {
  dmz: ["dmz", "internet edge"],
  corp: ["corp", "workstations"],
  "app-tier": ["app-tier", "application tier"],
  "data-tier": ["data-tier", "data tier"],
};

export const EFFECT: Record<string, string> = {
  process_spawn: "started a process",
  file_read: "read a file",
  network_connect: "opened a network connection",
  log_tamper: "cleared a log",
  app_request: "served a request",
};

export const code = (s: string) => s.split(" ")[0];
