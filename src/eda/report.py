"""Render a run into report.json and a self-contained dashboard.

The dashboard's job is to make one thing unmissable: the column where an attack
step left a trace but raised no alarm. Everything else on the page is in service
of reading that gap at a glance.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

_OUTCOME_LABEL = {
    "detected": "DETECTED",
    "visible_only": "VISIBLE, NO ALARM",
    "blind": "BLIND",
}


def render(report: dict, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    page = out_dir / "index.html"
    page.write_text(render_html(report), encoding="utf-8")
    return page


def render_html(report: dict) -> str:
    tally = report["tally"]
    fleet = report["fleet"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Endpoint Detection Assurance</title>
<style>{_CSS}</style>
</head>
<body>
<main>
  <header>
    <p class="kicker">Endpoint Detection Assurance &middot; BİL 420/520</p>
    <h1>What the sensors actually saw</h1>
    <p class="thesis">A trace in the logs is <b>visibility</b>. A rule firing is
      <b>detection</b>. They are measured separately here, because the gap
      between them is where the attack survives.</p>
  </header>

  <section class="strip">
    {_stat(fleet["size"], "agents in fleet")}
    {_stat(tally["detected"], "detected", "ok")}
    {_stat(tally["visible_only"], "visible, no alarm", "warn")}
    {_stat(tally["blind"], "blind", "bad")}
    {_stat(report["false_alarms"], "false alarms", "ok" if report["false_alarms"] == 0 else "warn")}
  </section>

  <section>
    <h2>The kill chain, step by step</h2>
    <p class="lede">One intrusion walked from the web tier to the database. Each
      row is one step, with what ground truth says happened and what the fleet's
      sensors made of it.</p>
    {_steps_table(report["steps"])}
  </section>

  <section class="grid">
    <div class="panel">
      <h3>H1 &middot; Coverage differs by sensor</h3>
      <p class="note">Which sensor type could even see each technique. The rows
        disagree, so no single sensor's coverage speaks for the fleet.</p>
      {_matrix_table(report["capability_matrix_h1"])}
    </div>
    <div class="panel">
      <h3>H2 &middot; Silent failure beats the status check</h3>
      <p class="note">After logging was disabled on the database, the health
        check still trusted the EDR. Only the canary noticed the silence.</p>
      {_silent_failure(report["silent_failure_h2"])}
    </div>
    <div class="panel">
      <h3>H3 &middot; The app log is not detection</h3>
      <p class="note">The application logged its requests and none of the host
        effects the attack caused. Logging without the right events is not
        visibility.</p>
      {_h3(report["applog_blindness_h3"], report["beacons_reached_c2"])}
    </div>
  </section>

  <footer>
    <p>Ground truth is known because the harness runs every step. Normal
    activity is scripted; its {report["benign_events"]} benign events raised
    {report["false_alarms"]} alarms. Mapping of each step to its lecture lives in
    <code>docs/course-mapping.md</code>.</p>
  </footer>
</main>
</body>
</html>
"""


def _stat(value: object, label: str, tone: str = "") -> str:
    return (
        f'<div class="stat {tone}"><span class="num">{html.escape(str(value))}</span>'
        f'<span class="lbl">{html.escape(label)}</span></div>'
    )


def _steps_table(steps: list[dict]) -> str:
    rows = []
    for step in steps:
        outcome = step["outcome"]
        seen = ", ".join(step["seen_by"]) or "&mdash;"
        alerts = ", ".join(a["rule_id"] for a in step["alerts"]) or "&mdash;"
        rows.append(
            f"""<tr class="o-{outcome}">
  <td class="mono">{html.escape(step["id"])}</td>
  <td>{html.escape(step["tactic"])}<br><span class="sub">{html.escape(step["name"])}</span></td>
  <td class="mono">{html.escape(step["agent"])}</td>
  <td class="mono">{html.escape(step["technique"])}<br><span class="sub">{html.escape(step["owasp"])}</span></td>
  <td>{seen}</td>
  <td class="mono">{alerts}</td>
  <td><span class="badge b-{outcome}">{_OUTCOME_LABEL[outcome]}</span></td>
</tr>"""
        )
    body = "\n".join(rows)
    return f"""<table class="steps">
<thead><tr>
  <th>#</th><th>Tactic / step</th><th>Host</th><th>Technique / OWASP</th>
  <th>Saw the host effect</th><th>Rule fired</th><th>Outcome</th>
</tr></thead>
<tbody>{body}</tbody>
</table>"""


def _matrix_table(matrix: dict[str, dict[str, bool]]) -> str:
    sensors = list(next(iter(matrix.values())).keys()) if matrix else []
    head = "".join(f"<th class='mono'>{html.escape(s)}</th>" for s in sensors)
    rows = []
    for technique, cells in matrix.items():
        tds = "".join(
            f"<td class='{'yes' if cells[s] else 'no'}'>{'&check;' if cells[s] else ''}</td>"
            for s in sensors
        )
        rows.append(f"<tr><td class='mono tech'>{html.escape(technique)}</td>{tds}</tr>")
    return f"<table class='matrix'><thead><tr><th>Technique</th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _silent_failure(data: dict) -> str:
    status = data["status_check"]
    canary = data["canary_probe"]
    rows = []
    for sensor in sorted(set(status) | set(canary)):
        s = status.get(sensor, "&mdash;")
        c = canary.get(sensor, "&mdash;")
        bad = c == "SILENT"
        rows.append(
            f"<tr class='{'row-bad' if bad else ''}'><td class='mono'>{html.escape(sensor)}</td>"
            f"<td>{html.escape(str(s))}</td><td class='mono'>{html.escape(str(c))}</td></tr>"
        )
    return (
        "<table class='mini'><thead><tr><th>Sensor</th><th>Status check</th>"
        f"<th>Canary</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _h3(data: dict, beacons: int) -> str:
    return f"""<table class="mini">
<tbody>
<tr><td>Requests the app logged</td><td class="mono">{data["requests_logged"]}</td></tr>
<tr class="row-bad"><td>Host effects visible in the app log</td><td class="mono">{data["host_effects_in_app_log"]}</td></tr>
<tr><td>Beacons that reached C2</td><td class="mono">{beacons}</td></tr>
</tbody></table>"""


_CSS = """
:root{
  --paper:#f7f4ee; --ink:#1b1b1a; --muted:#6b6760; --line:#ddd6ca;
  --card:#fffdf8; --accent:#0f6e6e;
  --ok:#2f6f4f; --warn:#9a6b00; --bad:#8f2d2d;
  --ok-bg:#e7f0ea; --warn-bg:#f4ecd8; --bad-bg:#f3e0dd;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#14161a; --ink:#ece7df; --muted:#9a948a; --line:#2b2f36;
    --card:#191c21; --accent:#54b3b0;
    --ok:#7fc29b; --warn:#d6ad5c; --bad:#dc8a82;
    --ok-bg:#1b2822; --warn-bg:#2a2518; --bad-bg:#2c1d1b;
  }
}
:root[data-theme="dark"]{
  --paper:#14161a; --ink:#ece7df; --muted:#9a948a; --line:#2b2f36;
  --card:#191c21; --accent:#54b3b0;
  --ok:#7fc29b; --warn:#d6ad5c; --bad:#dc8a82;
  --ok-bg:#1b2822; --warn-bg:#2a2518; --bad-bg:#2c1d1b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  font-size:.86em}
main{max-width:1060px;margin:0 auto;padding:48px 16px 80px}
header{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:28px}
.kicker{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.76rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
h1{font-size:clamp(1.9rem,4.5vw,3rem);line-height:1.05;margin:0 0 14px;
  letter-spacing:-.02em;font-weight:800}
.thesis{max-width:60ch;font-size:1.06rem;color:var(--ink);margin:0}
.thesis b{color:var(--accent);font-weight:700}
.lede,.note{color:var(--muted);max-width:66ch}
section{margin:38px 0}
h2{font-size:1.4rem;letter-spacing:-.01em;margin:0 0 6px}
h3{font-size:1.02rem;margin:0 0 4px}
.strip{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}
.stat{flex:1 1 120px;background:var(--card);border:1px solid var(--line);
  border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;gap:2px}
.stat .num{font-size:2rem;font-weight:800;letter-spacing:-.03em;line-height:1}
.stat .lbl{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.stat.ok .num{color:var(--ok)} .stat.warn .num{color:var(--warn)} .stat.bad .num{color:var(--bad)}
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:.93rem}
.steps th,.steps td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);
  vertical-align:top}
.steps thead th{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;
  color:var(--muted);border-bottom:1.5px solid var(--ink)}
.steps .sub{color:var(--muted);font-size:.82em}
.steps tr.o-blind td, .steps tr.o-visible_only td{background:transparent}
.badge{display:inline-block;padding:3px 8px;border-radius:999px;font-size:.72rem;
  font-weight:700;letter-spacing:.03em;white-space:nowrap}
.b-detected{background:var(--ok-bg);color:var(--ok)}
.b-visible_only{background:var(--warn-bg);color:var(--warn)}
.b-blind{background:var(--bad-bg);color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px}
.matrix td,.matrix th,.mini td,.mini th{padding:7px 9px;border-bottom:1px solid var(--line);
  text-align:center}
.matrix th:first-child,.matrix td:first-child,.mini td:first-child{text-align:left}
.matrix .tech{font-size:.76rem}
.matrix td.yes{color:var(--ok);font-weight:800}
.matrix td.no{color:var(--line)}
.mini th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);text-align:left}
tr.row-bad td, tr.row-bad td.mono{color:var(--bad)}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--muted);font-size:.88rem}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.86em;
  background:var(--card);padding:1px 5px;border-radius:4px;border:1px solid var(--line)}
@media(max-width:640px){
  .steps thead{display:none}
  .steps td{display:block;border:none;padding:4px 0}
  .steps tr{display:block;border-bottom:1.5px solid var(--line);padding:12px 0}
}
"""
