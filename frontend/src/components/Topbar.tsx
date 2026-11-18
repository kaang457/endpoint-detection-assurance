import NumberFlow from "@number-flow/react";
import { Menu, Play, RotateCcw } from "lucide-react";
import type { State } from "../api";
import { ScenarioPicker } from "./ScenarioPicker";

interface Props {
  state: State;
  busy: boolean;
  onRun: () => void;
  onReset: () => void;
  onMenu: () => void;
  onScenario: (id: string) => void;
}

function Stat({ sev, value, label }: { sev?: string; value: number; label: string }) {
  return (
    <span className="pstat" data-sev={sev}>
      {sev && <i />}
      <span className="v">
        <NumberFlow value={value} />
      </span>
      <span className="k">{label}</span>
    </span>
  );
}

export function Topbar({ state, busy, onRun, onReset, onMenu, onScenario }: Props) {
  return (
    <div className="topbar">
      <button className="btn sm menu-btn" aria-label="Toggle navigation" onClick={onMenu}>
        <Menu size={16} />
      </button>
      <ScenarioPicker current={state.scenario} scenarios={state.scenarios} onPick={onScenario} />
      <div className="posture">
        <Stat sev="detected" value={state.tally.detected} label="detected" />
        <Stat sev="visible_only" value={state.tally.visible_only} label="observed" />
        <Stat sev="blind" value={state.tally.blind} label="blind" />
        <span className="pdiv" />
        <Stat value={state.false_alarms} label="false alarms" />
        <span className="pstat" data-sev="blind">
          <span className="v">
            <NumberFlow value={state.beacons_reached_c2} />
          </span>
          <span className="k">reached C2</span>
        </span>
      </div>
      <span className="grow" />
      <div className="acts">
        <button className="btn primary sm" onClick={onRun} disabled={busy}>
          <Play size={14} style={{ marginRight: 6, verticalAlign: "-2px" }} />
          Run kill chain
        </button>
        <button className="btn sm" onClick={onReset} disabled={busy}>
          <RotateCcw size={14} style={{ marginRight: 6, verticalAlign: "-2px" }} />
          Reset
        </button>
      </div>
    </div>
  );
}
