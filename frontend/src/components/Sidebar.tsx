import * as Tabs from "@radix-ui/react-tabs";
import { LayoutGrid, ListTree, FlaskConical, Shield, ShieldCheck } from "lucide-react";
import type { State } from "../api";

interface Props {
  state: State;
  catalogCount: number;
  open: boolean;
  onNavigate: () => void;
  onOpenPalette: () => void;
}

export function Sidebar({ state, catalogCount, open, onNavigate, onOpenPalette }: Props) {
  return (
    <aside className={`sidebar${open ? " open" : ""}`}>
      <div className="brand">
        <ShieldCheck size={19} />
        EDA <span className="dim">Assurance</span>
      </div>
      <Tabs.List className="nav" aria-label="Views">
        <Tabs.Trigger value="fleet" onClick={onNavigate}>
          <LayoutGrid size={16} /> Fleet
          <span className="navcount">{state.fleet.size}</span>
        </Tabs.Trigger>
        <Tabs.Trigger value="chain" onClick={onNavigate}>
          <ListTree size={16} /> Attack chain
          <span className="navcount">
            {state.fired}/{state.total}
          </span>
        </Tabs.Trigger>
        <Tabs.Trigger value="hypotheses" onClick={onNavigate}>
          <FlaskConical size={16} /> Hypotheses
        </Tabs.Trigger>
        <Tabs.Trigger value="weaknesses" onClick={onNavigate}>
          <Shield size={16} /> Weaknesses
          <span className="navcount">{catalogCount || ""}</span>
        </Tabs.Trigger>
      </Tabs.List>

      <button className="kbd" onClick={onOpenPalette} style={{ background: "none", border: 0, cursor: "pointer" }}>
        <kbd>Ctrl</kbd>
        <kbd>K</kbd>
        <span>command menu</span>
      </button>

      <div className="side-sp" />
      <div className="fleetbox">
        <div className="r">
          <span>Fleet</span>
          <b>{state.fleet.size}</b>
        </div>
        <div className="r">
          <span>Steps fired</span>
          <b>
            {state.fired} / {state.total}
          </b>
        </div>
        <div className="sidelinks">
          <a href="/report.html">Report</a>
          <a href="/report">JSON</a>
          <a href="/catalog">Catalog</a>
        </div>
      </div>
    </aside>
  );
}
