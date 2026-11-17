import { Check, CircleAlert, CircleSlash, Circle } from "lucide-react";
import type { State, Step } from "../api";
import { EFFECT, OUTCOME, code } from "../labels";

interface Props {
  state: State;
  sel: string | null;
  onSelect: (id: string) => void;
  onFire: (id: string) => void;
}

function VerdictIcon({ outcome }: { outcome: Step["outcome"] }) {
  const size = 22;
  if (outcome === "detected") return <Check size={size} />;
  if (outcome === "visible_only") return <CircleAlert size={size} />;
  if (outcome === "blind") return <CircleSlash size={size} />;
  return <Circle size={size} />;
}

function Inspector({ step, onFire }: { step: Step | undefined; onFire: (id: string) => void }) {
  if (!step) return <p className="insp-empty">Select a step to inspect it.</p>;
  const o = OUTCOME[step.outcome];
  const seen = step.seen_by.length ? step.seen_by.join(", ") : "nothing";
  return (
    <>
      <div className="insp-id">
        <span className="mono">{step.id}</span>
        <span className="tactic">{step.tactic}</span>
      </div>
      <h3>{step.name}</h3>
      <div className="meta">
        <span className="hl">{step.agent}</span>
        <span>{code(step.technique)}</span>
        <span>{code(step.owasp)}</span>
        <span>{step.course}</span>
      </div>
      <p className="narr">{step.narrative}</p>
      <div className={`verdict${step.outcome === "armed" ? " armed" : ""}`} data-sev={step.outcome}>
        <VerdictIcon outcome={step.outcome} />
        <span>
          <span className="vt">{o.verdict}</span>
          <span className="vs">{o.detail}</span>
        </span>
      </div>
      {step.fired && (
        <>
          <div className="telemetry">
            <div className="trow">
              <span className="k">Host effect</span>
              <span className="val">{EFFECT[step.effect_kind] ?? step.effect_kind}</span>
            </div>
            <div className="trow">
              <span className="k">Sensors on host</span>
              <span className="val">{step.sensors_present.join(", ")}</span>
            </div>
            <div className="trow">
              <span className="k">Recorded the effect</span>
              <span className={`val${step.seen_by.length ? "" : " none"}`}>{seen}</span>
            </div>
            <div className="trow">
              <span className="k">Rules fired</span>
              <span className={`val${step.alerts.length ? "" : " none"}`}>{step.alerts.length || "none"}</span>
            </div>
          </div>
          {step.alerts.map((a) => (
            <p className="alertline" key={a.rule_id}>
              <span className="rid">{a.rule_id}</span>
              <span className="msg">{a.message}</span>
            </p>
          ))}
        </>
      )}
      <div style={{ marginTop: 16 }}>
        <button className="btn primary" style={{ width: "100%" }} onClick={() => onFire(step.id)}>
          {step.fired ? "Fire again" : "Fire step"}
        </button>
      </div>
    </>
  );
}

export function ChainView({ state, sel, onSelect, onFire }: Props) {
  const step = state.steps.find((s) => s.id === sel);
  return (
    <div className="view">
      <div className="vhead">
        <div>
          <h2>Attack chain</h2>
          <p>
            Web tier → phished laptop → database. Select a step, fire it, read the verdict. Firing s11
            blinds the database EDR, so fire s12 again after to watch a detected action go dark.
          </p>
        </div>
      </div>
      <div className="workspace">
        <div className="list">
          <div className="listhead">
            <span />
            <span>#</span>
            <span>Step</span>
            <span className="h-host">Host</span>
            <span>Verdict</span>
          </div>
          {state.steps.map((s) => (
            <button
              key={s.id}
              className={`row${s.id === sel ? " sel" : ""}`}
              data-sev={s.outcome}
              onClick={() => onSelect(s.id)}
            >
              <span className="lamp" />
              <span className="rid">{s.id}</span>
              <span className="rname">
                <b>{s.name}</b>
                <small>{s.tactic}</small>
              </span>
              <span className="rhost">{s.agent}</span>
              <span className="otag" data-sev={s.outcome}>
                {OUTCOME[s.outcome].tag}
              </span>
            </button>
          ))}
        </div>
        <div className="inspector">
          <Inspector step={step} onFire={onFire} />
        </div>
      </div>
    </div>
  );
}
