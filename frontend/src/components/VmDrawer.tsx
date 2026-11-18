import { Drawer } from "vaul";
import type { Agent } from "../api";
import { OUTCOME, STATUS, uptime } from "../labels";

function load(pct: number): string | undefined {
  if (pct >= 85) return "hot";
  if (pct >= 70) return "warn";
  return undefined;
}

interface Props {
  agent: Agent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function VmDrawer({ agent, open, onOpenChange }: Props) {
  return (
    <Drawer.Root open={open} onOpenChange={onOpenChange}>
      <Drawer.Portal>
        <Drawer.Overlay className="drawer-overlay" />
        <Drawer.Content className="drawer" data-sev={agent?.status}>
          <div className="drawer-grip" />
          <div className="drawer-in">
            {agent && (
              <>
                <div className="did">
                  <span className="mono">{agent.subnet}</span>
                  <span className="st">{STATUS[agent.status]}</span>
                </div>
                <Drawer.Title asChild>
                  <h3 className="mono">{agent.id}</h3>
                </Drawer.Title>
                <Drawer.Description asChild>
                  <div className="meta">
                    <span className="hl">{agent.role}</span>
                    <span>{agent.workload}</span>
                    <span className="pw">
                      <i />
                      {agent.power}
                    </span>
                  </div>
                </Drawer.Description>

                <div className="sec-label">Virtual machine</div>
                <div className="vm-panel">
                  <div className="spec">
                    <span className="k">Guest OS</span>
                    <span className="v">{agent.os}</span>
                  </div>
                  <div className="spec">
                    <span className="k">Address</span>
                    <span className="v">{agent.ip}</span>
                  </div>
                  <div className="spec">
                    <span className="k">vCPU</span>
                    <span className="v">{agent.vcpu}</span>
                  </div>
                  <div className="spec">
                    <span className="k">Memory</span>
                    <span className="v">{agent.mem_gb} GB</span>
                  </div>
                  <div className="spec">
                    <span className="k">Disk</span>
                    <span className="v">{agent.disk_gb} GB</span>
                  </div>
                  <div className="spec">
                    <span className="k">Uptime</span>
                    <span className="v">{uptime(agent.uptime_s)}</span>
                  </div>
                  <div className="spec">
                    <span className="k">Pool</span>
                    <span className="v">{agent.pool}</span>
                  </div>
                  <div className="spec">
                    <span className="k">Subnet</span>
                    <span className="v">{agent.subnet}</span>
                  </div>
                </div>
                <div className="gauges">
                  <div className="gauge2">
                    <div className="lab">
                      <span>CPU</span>
                      <b>{agent.cpu_pct}%</b>
                    </div>
                    <div className="bar">
                      <i style={{ width: `${agent.cpu_pct}%` }} data-load={load(agent.cpu_pct)} />
                    </div>
                  </div>
                  <div className="gauge2">
                    <div className="lab">
                      <span>Memory</span>
                      <b>{agent.mem_pct}%</b>
                    </div>
                    <div className="bar">
                      <i style={{ width: `${agent.mem_pct}%` }} />
                    </div>
                  </div>
                </div>

                <div className="sec-label">Endpoint detection</div>
                <div className="meta">
                  {agent.sensors.map((s) => (
                    <span key={s}>{s}</span>
                  ))}
                </div>
                <div className="counts">
                  <span>
                    events <b>{agent.events}</b>
                  </span>
                  <span>
                    alerts <b>{agent.alerts}</b>
                  </span>
                </div>

                {agent.steps.length ? (
                  <div className="telemetry">
                    {agent.steps.map((st) => {
                      const seen = st.seen_by.length ? st.seen_by.join(", ") : "nothing";
                      return (
                        <div className="trow" key={st.id} style={{ alignItems: "center" }}>
                          <span className="k">
                            <span className="mono" style={{ color: "var(--faint)", marginRight: 8 }}>
                              {st.id}
                            </span>
                            {st.name}
                            {st.fired && (
                              <span style={{ display: "block", color: "var(--faint)", fontSize: ".78rem" }}>
                                recorded by {seen}
                              </span>
                            )}
                          </span>
                          <span className="otag" data-sev={st.outcome}>
                            {OUTCOME[st.outcome].tag}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="hint">No attack reached this host. Only benign activity.</p>
                )}
              </>
            )}
          </div>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  );
}
