import { Drawer } from "vaul";
import type { Agent } from "../api";
import { OUTCOME, STATUS } from "../labels";

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
                    {agent.sensors.map((s) => (
                      <span key={s}>{s}</span>
                    ))}
                  </div>
                </Drawer.Description>
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
