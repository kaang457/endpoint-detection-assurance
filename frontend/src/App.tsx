import { useCallback, useEffect, useMemo, useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { toast } from "sonner";
import type { Agent, State, Vulnerability } from "./api";
import { api } from "./api";
import { OUTCOME } from "./labels";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { FleetView } from "./components/FleetView";
import { ChainView } from "./components/ChainView";
import { HypothesesView } from "./components/HypothesesView";
import { WeaknessesView } from "./components/WeaknessesView";
import { VmDrawer } from "./components/VmDrawer";
import { CommandPalette } from "./components/CommandPalette";

export type ViewKey = "fleet" | "chain" | "hypotheses" | "weaknesses";

function fireToast(id: string, outcome: Agent["steps"][number]["outcome"]) {
  const label = `${id} · ${OUTCOME[outcome].tag}`;
  if (outcome === "detected") toast.success(label, { description: "A detection rule fired." });
  else if (outcome === "blind") toast.error(label, { description: "No sensor saw it. Silent." });
  else toast(label, { description: OUTCOME[outcome].detail });
}

export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [catalog, setCatalog] = useState<Vulnerability[]>([]);
  const [view, setView] = useState<ViewKey>("fleet");
  const [sel, setSel] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<Agent | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.state().then(setState).catch((e) => setError(String(e.message)));
    api.catalog().then(setCatalog).catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // keep the drawer bound to fresh data after a fire
  const freshDrawer = useMemo(
    () => (drawer && state ? state.agents.find((a) => a.id === drawer.id) ?? null : null),
    [drawer, state],
  );

  const fire = useCallback(async (id: string) => {
    setBusy(true);
    try {
      const next = await api.fire(id);
      setState(next);
      setSel(id);
      const step = next.steps.find((s) => s.id === id);
      if (step) fireToast(step.id, step.outcome);
    } finally {
      setBusy(false);
    }
  }, []);

  const runAll = useCallback(async () => {
    setBusy(true);
    try {
      const next = await api.fireAll();
      setState(next);
      const breached = next.agents.filter((a) => a.status === "silent").length;
      toast(`Kill chain complete — ${next.tally.detected} detected, ${next.tally.blind} blind`, {
        description: `${breached} host${breached === 1 ? "" : "s"} silently breached, ${next.beacons_reached_c2} beacons reached C2.`,
      });
    } finally {
      setBusy(false);
    }
  }, []);

  const reset = useCallback(async () => {
    setBusy(true);
    try {
      setState(await api.reset());
      setDrawer(null);
      toast("Fleet reset", { description: "Fresh hosts, nothing fired." });
    } finally {
      setBusy(false);
    }
  }, []);

  if (error) {
    return <div className="insp-empty">Could not reach the control plane: {error}</div>;
  }
  if (!state) {
    return <div className="insp-empty">Loading the fleet…</div>;
  }

  return (
    <>
      <Tabs.Root
        className="app"
        orientation="vertical"
        value={view}
        onValueChange={(v) => setView(v as ViewKey)}
      >
        <Sidebar
          state={state}
          catalogCount={catalog.length}
          open={menuOpen}
          onNavigate={() => setMenuOpen(false)}
          onOpenPalette={() => setPaletteOpen(true)}
        />
        <main className="main">
          <Topbar state={state} busy={busy} onRun={runAll} onReset={reset} onMenu={() => setMenuOpen((o) => !o)} />
          <Tabs.Content value="fleet">
            <FleetView state={state} onOpen={setDrawer} />
          </Tabs.Content>
          <Tabs.Content value="chain">
            <ChainView state={state} sel={sel} onSelect={setSel} onFire={fire} />
          </Tabs.Content>
          <Tabs.Content value="hypotheses">
            <HypothesesView state={state} />
          </Tabs.Content>
          <Tabs.Content value="weaknesses">
            <WeaknessesView items={catalog} />
          </Tabs.Content>
        </main>
      </Tabs.Root>

      <VmDrawer agent={freshDrawer} open={drawer !== null} onOpenChange={(o) => !o && setDrawer(null)} />
      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        state={state}
        onView={setView}
        onFire={fire}
        onRunAll={runAll}
        onReset={reset}
      />
    </>
  );
}
