import type { State } from "../api";
import { OUTCOME, code } from "../labels";

export function HypothesesView({ state }: { state: State }) {
  const matrix = state.capability_matrix_h1;
  const techs = Object.keys(matrix);
  const sensors = techs.length ? Object.keys(matrix[techs[0]]) : [];
  const sf = state.silent_failure_h2;
  const sensorNames = Array.from(
    new Set([...Object.keys(sf.status_check), ...Object.keys(sf.canary_probe)]),
  ).sort();
  const h3 = state.applog_blindness_h3;
  const fired = state.steps.filter((s) => s.fired);

  return (
    <div className="view">
      <div className="vhead">
        <div>
          <h2>Hypotheses</h2>
          <p>Why visibility is not detection, measured three ways.</p>
        </div>
      </div>
      <div className="grid12">
        <div className="panel col-8">
          <h3>
            Coverage differs by sensor<span className="tag">H1</span>
          </h3>
          <p className="sub">Which sensor type can even record each technique. The rows disagree.</p>
          <table className="tbl">
            <thead>
              <tr>
                <th>Technique</th>
                {sensors.map((s) => (
                  <th key={s}>{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {techs.map((t) => (
                <tr key={t}>
                  <td className="tech">{code(t)}</td>
                  {sensors.map((s) => (
                    <td key={s} className={matrix[t][s] ? "y" : "no"}>
                      {matrix[t][s] ? "✓" : "·"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel col-4">
          <h3>
            App log is not detection<span className="tag">H3</span>
          </h3>
          <p className="sub">The app logs requests, not host effects.</p>
          <div className="figrow">
            <span>Requests the app logged</span>
            <b>{h3.requests_logged}</b>
          </div>
          <div className="figrow bad">
            <span>Host effects in the app log</span>
            <b>{h3.host_effects_in_app_log}</b>
          </div>
          <div className="figrow">
            <span>Beacons that reached C2</span>
            <b>{state.beacons_reached_c2}</b>
          </div>
        </div>

        <div className="panel col-5">
          <h3>
            Silent failure<span className="tag">H2</span>
          </h3>
          <p className="sub">After logging is disabled on the database.</p>
          <table className="tbl cmp">
            <thead>
              <tr>
                <th>Sensor</th>
                <th>Status</th>
                <th>Canary</th>
              </tr>
            </thead>
            <tbody>
              {sensorNames.map((n) => {
                const canary = sf.canary_probe[n] ?? "—";
                return (
                  <tr key={n}>
                    <td className="sensor">{n}</td>
                    <td className="status">{sf.status_check[n] ?? "—"}</td>
                    <td className={canary === "SILENT" ? "silent" : ""}>{canary}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="hint">
            A blinded sensor keeps reporting healthy. Only probing by result hears the silence.
          </p>
        </div>

        <div className="panel col-7">
          <h3>Evidence feed</h3>
          <p className="sub">Every step you have fired, newest first.</p>
          <ul className="feed">
            {fired.length === 0 && <li style={{ color: "var(--faint)" }}>Nothing fired yet.</li>}
            {fired
              .slice()
              .reverse()
              .map((s) => (
                <li key={s.id}>
                  <span className="dot" data-sev={s.outcome} />
                  <span className="fid">{s.id}</span>
                  <span className="fname">
                    {OUTCOME[s.outcome].tag} — {s.name}
                  </span>
                </li>
              ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
