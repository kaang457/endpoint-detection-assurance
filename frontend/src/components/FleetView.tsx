import NumberFlow from "@number-flow/react";
import { ChevronRight } from "lucide-react";
import type { Agent, State } from "../api";
import { STATUS, SUBNET } from "../labels";

interface Props {
  state: State;
  onOpen: (agent: Agent) => void;
}

function load(pct: number): string | undefined {
  if (pct >= 85) return "hot";
  if (pct >= 70) return "warn";
  return undefined;
}

function Tile({ agent, onOpen }: { agent: Agent; onOpen: (a: Agent) => void }) {
  const live = agent.status === "silent";
  return (
    <button
      className={`vm${agent.on_path ? " on-path" : ""}${live ? " live" : ""}`}
      data-sev={agent.status}
      onClick={() => onOpen(agent)}
      aria-label={`${agent.id}, ${STATUS[agent.status]}`}
    >
      <span className="vm-head">
        <span className="vm-dot" />
        <span className="vm-id">
          <b>{agent.id}</b>
          <small>
            {agent.role} · {agent.workload}
          </small>
        </span>
        {agent.status !== "nominal" && <span className="vm-state">{STATUS[agent.status]}</span>}
        <ChevronRight className="vm-chev" size={14} />
      </span>
      <span className="vm-stats">
        <span className="vm-ip mono">{agent.ip}</span>
        <span className="umeter-k">cpu</span>
        <span className="umeter" title={`CPU ${agent.cpu_pct}%`}>
          <i style={{ width: `${agent.cpu_pct}%` }} data-load={load(agent.cpu_pct)} />
        </span>
        <span className="umeter-k">mem</span>
        <span className="umeter" title={`Memory ${agent.mem_pct}%`}>
          <i style={{ width: `${agent.mem_pct}%` }} />
        </span>
      </span>
    </button>
  );
}

export function FleetView({ state, onOpen }: Props) {
  const counts = state.agents.reduce<Record<string, number>>((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="view">
      <div className="vhead">
        <div>
          <h2>Fleet</h2>
          <p>
            <b style={{ color: "var(--text)", fontWeight: 600 }}>{state.scenario.name}.</b>{" "}
            {state.scenario.description}
          </p>
        </div>
        <div className="vsum">
          <span>
            <b>{state.agents.length}</b> hosts
          </span>
          <span className="sil">
            <b>
              <NumberFlow value={counts.silent || 0} />
            </b>{" "}
            silent
          </span>
          <span className="alr">
            <b>
              <NumberFlow value={counts.alerting || 0} />
            </b>{" "}
            alerting
          </span>
          <span>
            <b>
              <NumberFlow value={counts.nominal || 0} />
            </b>{" "}
            nominal
          </span>
        </div>
      </div>

      {state.subnets.map((subnet) => {
        const hosts = state.agents.filter((a) => a.subnet === subnet);
        if (!hosts.length) return null;
        const hot = hosts.some((h) => h.on_path);
        const breached = hosts.filter((h) => h.status === "silent").length;
        const [sn, role] = SUBNET[subnet] ?? [subnet, ""];
        return (
          <div className={`band${hot ? " hot" : ""}`} key={subnet}>
            <div className="bandhead">
              <span className="sn">{sn}</span>
              <span className="role">{role}</span>
              <span className="tally">
                {hosts.length} hosts{breached ? ` · ${breached} breached` : ""}
              </span>
            </div>
            <div className="vmgrid">
              {hosts.map((a) => (
                <Tile key={a.id} agent={a} onOpen={onOpen} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
