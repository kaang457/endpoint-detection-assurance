import type { CSSProperties } from "react";
import { Dialog } from "@base-ui-components/react/dialog";
import { Command } from "cmdk";
import { LayoutGrid, ListTree, FlaskConical, Shield, Play, RotateCcw, Crosshair, Clapperboard, Shuffle } from "lucide-react";
import type { State } from "../api";
import type { ViewKey } from "../App";
import { OUTCOME } from "../labels";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  state: State;
  onView: (v: ViewKey) => void;
  onFire: (id: string) => void;
  onRunAll: () => void;
  onReset: () => void;
  onScenario: (id: string) => void;
}

const srOnly: CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
};

export function CommandPalette({ open, onOpenChange, state, onView, onFire, onRunAll, onReset, onScenario }: Props) {
  const run = (fn: () => void) => {
    onOpenChange(false);
    fn();
  };
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Backdrop className="cmd-backdrop" />
        <Dialog.Popup className="cmd">
          <Dialog.Title style={srOnly}>Command menu</Dialog.Title>
          <Command label="Command menu">
            <Command.Input placeholder="Jump to a view, or fire a step…" autoFocus />
            <Command.List>
              <Command.Empty>No matches.</Command.Empty>
              <Command.Group heading="Go to">
                <Command.Item onSelect={() => run(() => onView("fleet"))}>
                  <LayoutGrid size={15} /> Fleet
                </Command.Item>
                <Command.Item onSelect={() => run(() => onView("chain"))}>
                  <ListTree size={15} /> Attack chain
                </Command.Item>
                <Command.Item onSelect={() => run(() => onView("hypotheses"))}>
                  <FlaskConical size={15} /> Hypotheses
                </Command.Item>
                <Command.Item onSelect={() => run(() => onView("weaknesses"))}>
                  <Shield size={15} /> Weaknesses
                </Command.Item>
              </Command.Group>
              <Command.Group heading="Campaign">
                <Command.Item onSelect={() => run(onRunAll)}>
                  <Play size={15} /> Run the whole kill chain
                </Command.Item>
                <Command.Item onSelect={() => run(onReset)}>
                  <RotateCcw size={15} /> Reset the fleet
                </Command.Item>
              </Command.Group>
              <Command.Group heading="Scenario">
                <Command.Item value="scenario random surprise" onSelect={() => run(() => onScenario("random"))}>
                  <Shuffle size={15} /> Random scenario
                </Command.Item>
                {state.scenarios.map((s) => (
                  <Command.Item
                    key={s.id}
                    value={`scenario ${s.id} ${s.name}`}
                    onSelect={() => run(() => onScenario(s.id))}
                  >
                    <Clapperboard size={15} />
                    {s.name}
                    {s.id === state.scenario.id && <span className="mono">current</span>}
                  </Command.Item>
                ))}
              </Command.Group>
              <Command.Group heading="Fire a step">
                {state.steps.map((s) => (
                  <Command.Item
                    key={s.id}
                    value={`fire ${s.id} ${s.name} ${s.tactic}`}
                    onSelect={() => run(() => onFire(s.id))}
                  >
                    <Crosshair size={15} />
                    <span>
                      <span className="mono" style={{ color: "var(--faint)", marginRight: 8 }}>
                        {s.id}
                      </span>
                      {s.name}
                    </span>
                    <span className="mono">{OUTCOME[s.outcome].tag}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            </Command.List>
          </Command>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
