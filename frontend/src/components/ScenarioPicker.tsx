import { useEffect, useRef, useState } from "react";
import { ChevronDown, Shuffle } from "lucide-react";
import type { Scenario } from "../api";

interface Props {
  current: Scenario;
  scenarios: Scenario[];
  onPick: (id: string) => void;
}

export function ScenarioPicker({ current, scenarios, onPick }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const pick = (id: string) => {
    setOpen(false);
    onPick(id);
  };

  return (
    <div className="spick" ref={ref}>
      <button className="spick-btn" onClick={() => setOpen((o) => !o)}>
        <span className="spick-lab">scenario</span>
        <span className="spick-name">{current.name}</span>
        <ChevronDown size={14} />
      </button>
      {open && (
        <div className="spick-menu">
          {scenarios.map((s) => (
            <button key={s.id} className={`spick-item${s.id === current.id ? " on" : ""}`} onClick={() => pick(s.id)}>
              <span className="nm">{s.name}</span>
              <span className="ds">{s.description}</span>
            </button>
          ))}
          <button className="spick-item rnd" onClick={() => pick("random")}>
            <span className="nm">
              <Shuffle size={13} /> Random
            </span>
            <span className="ds">Pick a scenario at random, on a fresh fleet.</span>
          </button>
        </div>
      )}
    </div>
  );
}
