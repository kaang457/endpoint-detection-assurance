"""The interactive console: fire one attack, watch for the alarm.

This is the page that makes the whole thesis tangible. The static dashboard in
`report.py` shows a finished run; this one lets you pull the trigger yourself on
each kill-chain step and see, in the same instant, the three facts the project
insists on keeping apart: what really happened (ground truth), which sensors saw
it (visibility), and whether a rule fired (detection).

The page is one self-contained HTML string; it talks to the control plane's
`/live/*` JSON endpoints. No build step, no framework — the point is the data,
not the bundler.
"""

from __future__ import annotations


def render_console() -> str:
    return _PAGE


_CSS = """
:root{
  --paper:#f7f4ee; --ink:#1b1b1a; --muted:#6b6760; --line:#ddd6ca;
  --card:#fffdf8; --accent:#0f6e6e; --accent-ink:#0b4f4f;
  --ok:#2f6f4f; --warn:#9a6b00; --bad:#8f2d2d;
  --ok-bg:#e7f0ea; --warn-bg:#f4ecd8; --bad-bg:#f3e0dd;
  --armed:#514c44; --armed-bg:#efeadf;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#14161a; --ink:#ece7df; --muted:#9a948a; --line:#2b2f36;
    --card:#191c21; --accent:#54b3b0; --accent-ink:#8fd6d3;
    --ok:#7fc29b; --warn:#d6ad5c; --bad:#dc8a82;
    --ok-bg:#1b2822; --warn-bg:#2a2518; --bad-bg:#2c1d1b;
    --armed:#9a948a; --armed-bg:#20242b;
  }
}
:root[data-theme="dark"]{
  --paper:#14161a; --ink:#ece7df; --muted:#9a948a; --line:#2b2f36;
  --card:#191c21; --accent:#54b3b0; --accent-ink:#8fd6d3;
  --ok:#7fc29b; --warn:#d6ad5c; --bad:#dc8a82;
  --ok-bg:#1b2822; --warn-bg:#2a2518; --bad-bg:#2c1d1b;
  --armed:#9a948a; --armed-bg:#20242b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
main{max-width:1180px;margin:0 auto;padding:40px 16px 90px}
header{border-bottom:2px solid var(--ink);padding-bottom:20px;margin-bottom:22px}
.kicker{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.76rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
h1{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.04;margin:0 0 12px;
  letter-spacing:-.02em;font-weight:800}
.thesis{max-width:66ch;font-size:1.04rem;margin:0}
.thesis b{color:var(--accent);font-weight:700}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:20px 0 6px}
button{font:inherit;cursor:pointer;border-radius:8px;border:1px solid var(--line);
  background:var(--card);color:var(--ink);padding:9px 14px;font-weight:600;
  transition:transform .05s ease, border-color .15s ease}
button:hover{border-color:var(--accent)}
button:active{transform:translateY(1px)}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button:disabled{opacity:.5;cursor:default;transform:none}
.spacer{flex:1}
.counter{font-size:.85rem;color:var(--muted)}
.strip{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 26px}
.stat{flex:1 1 120px;background:var(--card);border:1px solid var(--line);
  border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:2px}
.stat .num{font-size:1.8rem;font-weight:800;letter-spacing:-.03em;line-height:1}
.stat .lbl{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.stat.ok .num{color:var(--ok)} .stat.warn .num{color:var(--warn)} .stat.bad .num{color:var(--bad)}
.layout{display:grid;grid-template-columns:1fr 320px;gap:22px;align-items:start}
@media(max-width:860px){.layout{grid-template-columns:1fr}}
h2{font-size:1.25rem;letter-spacing:-.01em;margin:0 0 4px}
.lede{color:var(--muted);max-width:60ch;margin:0 0 16px}
.step{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;margin-bottom:12px;border-left:4px solid var(--armed)}
.step.detected{border-left-color:var(--ok)}
.step.visible_only{border-left-color:var(--warn)}
.step.blind{border-left-color:var(--bad)}
.step-top{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.sid{font-size:.76rem;font-weight:700;color:var(--muted)}
.step h3{font-size:1.02rem;margin:0;font-weight:700}
.tactic{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--accent);
  font-weight:700}
.meta{font-size:.82rem;color:var(--muted);margin:6px 0 0}
.meta .tag{display:inline-block;background:var(--armed-bg);border:1px solid var(--line);
  border-radius:5px;padding:1px 7px;margin:2px 6px 0 0;font-size:.76rem}
.narr{font-size:.9rem;margin:10px 0 0;color:var(--ink)}
.row{display:flex;align-items:center;gap:12px;margin-top:12px;flex-wrap:wrap}
.verdict{display:inline-flex;align-items:center;gap:8px;font-weight:800;font-size:.84rem;
  padding:6px 12px;border-radius:999px;letter-spacing:.02em;white-space:nowrap}
.verdict.detected{background:var(--ok-bg);color:var(--ok)}
.verdict.visible_only{background:var(--warn-bg);color:var(--warn)}
.verdict.blind{background:var(--bad-bg);color:var(--bad)}
.verdict.armed{background:var(--armed-bg);color:var(--armed)}
.dot{width:8px;height:8px;border-radius:50%;background:currentColor;display:inline-block}
.detail{font-size:.84rem;color:var(--muted)}
.detail b{color:var(--ink)}
.alert-line{font-size:.82rem;margin-top:8px;color:var(--ok)}
.alert-line .mono{font-weight:700}
.fire{margin-left:auto}
.side{position:sticky;top:18px;display:flex;flex-direction:column;gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.panel h4{margin:0 0 4px;font-size:.95rem}
.panel .note{font-size:.8rem;color:var(--muted);margin:0 0 10px}
.mini{width:100%;border-collapse:collapse;font-size:.82rem}
.mini td,.mini th{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
.mini th{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
tr.row-bad td{color:var(--bad);font-weight:600}
.feed{list-style:none;margin:0;padding:0;max-height:260px;overflow:auto}
.feed li{font-size:.82rem;padding:7px 0;border-bottom:1px solid var(--line);display:flex;gap:8px}
.feed .mono{font-size:.78rem}
.feed .v{font-weight:700}
.feed .v.detected{color:var(--ok)} .feed .v.visible_only{color:var(--warn)} .feed .v.blind{color:var(--bad)}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);
  color:var(--muted);font-size:.86rem}
a{color:var(--accent)}
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDA — Live Attack Console</title>
<style>__CSS__</style>
</head>
<body>
<main>
  <header>
    <p class="kicker">Endpoint Detection Assurance &middot; Live Console</p>
    <h1>Fire an attack. Watch for the alarm.</h1>
    <p class="thesis">Each step runs a <b>real but benign</b> host action on one
      agent in the fleet. You see three things at once: what happened, which
      sensors <b>saw</b> it (visibility), and whether a rule <b>fired</b>
      (detection). The gap between the last two is the whole point.</p>
  </header>

  <div class="bar">
    <button id="fire-all" class="primary">Run the whole kill chain</button>
    <button id="reset">Reset fleet</button>
    <span class="spacer"></span>
    <span class="counter" id="counter"></span>
  </div>

  <div class="strip" id="strip"></div>

  <div class="layout">
    <section>
      <h2>The kill chain</h2>
      <p class="lede">One intrusion walks from the web tier through a phished
        laptop to the database. Fire a step to pull its trigger. Order matters:
        disable logging (s11), then fire the beacon (s12) again to watch a
        detected action go silent.</p>
      <div id="steps"></div>
    </section>

    <aside class="side">
      <div class="panel">
        <h4>Evidence feed</h4>
        <p class="note">Newest fired step first.</p>
        <ul class="feed" id="feed"></ul>
      </div>
      <div class="panel" id="h2panel">
        <h4>H2 &middot; Silent failure</h4>
        <p class="note">After logging is disabled on the database, does the
          health check still trust the EDR while the canary hears silence?</p>
        <table class="mini" id="h2"><tbody></tbody></table>
      </div>
      <div class="panel" id="h3panel">
        <h4>H3 &middot; The app log is not detection</h4>
        <table class="mini" id="h3"><tbody></tbody></table>
      </div>
    </aside>
  </div>

  <footer>
    Ground truth is known because this console runs every step itself. The full
    non-interactive run is at <a href="/report">/report</a>; the planted
    weaknesses at <a href="/catalog">/catalog</a>. Visibility is a sensor
    recording a trace; detection is a rule firing. They are measured apart.
  </footer>
</main>

<script>
const VERDICT = {
  detected:     {label: "ALARM RAISED",        hint: "a rule fired"},
  visible_only: {label: "NO ALARM \\u00b7 but seen", hint: "a sensor saw it, no rule matched"},
  blind:        {label: "NO ALARM \\u00b7 unseen",   hint: "no sensor saw it"},
  armed:        {label: "armed",               hint: "not fired yet"},
};
const EFFECT = {
  process_spawn: "spawned a process",
  file_read: "read a file",
  network_connect: "opened a network connection",
  log_tamper: "cleared a log",
  app_request: "served a request",
};

async function api(path, method) {
  const r = await fetch(path, {method: method || "GET"});
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}

function esc(s) {
  return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
}

function renderStrip(s) {
  const strip = document.getElementById("strip");
  const t = s.tally;
  const cells = [
    [s.fleet.size, "agents in fleet", ""],
    [t.detected, "detected", "ok"],
    [t.visible_only, "visible, no alarm", "warn"],
    [t.blind, "blind", "bad"],
    [s.false_alarms, "false alarms", s.false_alarms ? "warn" : "ok"],
    [s.beacons_reached_c2, "beacons reached C2", s.beacons_reached_c2 ? "bad" : "ok"],
  ];
  strip.innerHTML = "";
  for (const [num, lbl, tone] of cells) {
    const d = el("div", "stat " + tone);
    d.appendChild(el("span", "num", esc(num)));
    d.appendChild(el("span", "lbl", esc(lbl)));
    strip.appendChild(d);
  }
  document.getElementById("counter").textContent = s.fired + " / " + s.total + " steps fired";
}

function stepCard(step) {
  const card = el("div", "step " + step.outcome);
  const top = el("div", "step-top");
  top.appendChild(el("span", "sid mono", esc(step.id)));
  top.appendChild(el("span", "tactic", esc(step.tactic)));
  top.appendChild(el("h3", null, esc(step.name)));
  card.appendChild(top);

  const meta = el("div", "meta");
  meta.innerHTML =
    '<span class="tag mono">' + esc(step.agent) + '</span>' +
    '<span class="tag">' + esc(step.technique) + '</span>' +
    '<span class="tag">' + esc(step.owasp) + '</span>' +
    '<span class="tag">sensors: ' + esc(step.sensors_present.join(", ")) + '</span>';
  card.appendChild(meta);

  card.appendChild(el("p", "narr", esc(step.narrative)));

  const row = el("div", "row");
  const v = VERDICT[step.outcome];
  const verdict = el("span", "verdict " + step.outcome,
    '<span class="dot"></span>' + v.label);
  row.appendChild(verdict);

  if (step.fired) {
    const seen = step.seen_by.length ? step.seen_by.join(", ") : "nothing";
    row.appendChild(el("span", "detail",
      'ground truth: <b>' + esc(step.agent) + '</b> ' + esc(EFFECT[step.effect_kind] || step.effect_kind) +
      ' &middot; saw the host effect: <b>' + esc(seen) + '</b>'));
  } else {
    row.appendChild(el("span", "detail", esc(v.hint)));
  }

  const btn = el("button", "fire", step.fired ? "Fire again" : "Fire");
  btn.onclick = () => fireStep(step.id, btn);
  row.appendChild(btn);
  card.appendChild(row);

  if (step.fired && step.alerts.length) {
    for (const a of step.alerts) {
      card.appendChild(el("p", "alert-line",
        '&#9873; alert <span class="mono">' + esc(a.rule_id) + '</span> (' +
        esc(a.technique) + '): ' + esc(a.message)));
    }
  }
  return card;
}

function renderSteps(s) {
  const box = document.getElementById("steps");
  box.innerHTML = "";
  for (const step of s.steps) box.appendChild(stepCard(step));
}

function renderFeed(s) {
  const feed = document.getElementById("feed");
  const fired = s.steps.filter(x => x.fired);
  feed.innerHTML = "";
  if (!fired.length) {
    feed.appendChild(el("li", null, '<span class="detail">No step fired yet.</span>'));
    return;
  }
  for (const step of fired.slice().reverse()) {
    const li = el("li");
    li.innerHTML =
      '<span class="mono">' + esc(step.id) + '</span>' +
      '<span class="v ' + step.outcome + '">' + VERDICT[step.outcome].label + '</span>' +
      '<span class="detail">' + esc(step.name) + '</span>';
    feed.appendChild(li);
  }
}

function renderPanels(s) {
  const h2 = document.querySelector("#h2 tbody");
  const sf = s.silent_failure_h2;
  const names = Array.from(new Set([
    ...Object.keys(sf.status_check), ...Object.keys(sf.canary_probe),
  ])).sort();
  h2.innerHTML = '<tr><th>Sensor</th><th>Status</th><th>Canary</th></tr>';
  for (const n of names) {
    const status = sf.status_check[n] || "\\u2014";
    const canary = sf.canary_probe[n] || "\\u2014";
    const bad = canary === "SILENT";
    h2.insertAdjacentHTML("beforeend",
      '<tr class="' + (bad ? "row-bad" : "") + '"><td class="mono">' + esc(n) +
      '</td><td>' + esc(status) + '</td><td class="mono">' + esc(canary) + '</td></tr>');
  }

  const h3 = document.querySelector("#h3 tbody");
  const d = s.applog_blindness_h3;
  h3.innerHTML =
    '<tr><td>Requests the app logged</td><td class="mono">' + esc(d.requests_logged) + '</td></tr>' +
    '<tr class="row-bad"><td>Host effects in the app log</td><td class="mono">' + esc(d.host_effects_in_app_log) + '</td></tr>' +
    '<tr><td>Beacons that reached C2</td><td class="mono">' + esc(s.beacons_reached_c2) + '</td></tr>';
}

function render(s) {
  renderStrip(s);
  renderSteps(s);
  renderFeed(s);
  renderPanels(s);
}

async function fireStep(id, btn) {
  btn.disabled = true;
  await api("/live/fire/" + id, "POST");
  render(await api("/live/state"));
}

async function reset() {
  render(await api("/live/reset", "POST"));
}

async function fireAll() {
  const btn = document.getElementById("fire-all");
  btn.disabled = true;
  await api("/live/fire-all", "POST");
  render(await api("/live/state"));
  btn.disabled = false;
}

document.getElementById("reset").onclick = reset;
document.getElementById("fire-all").onclick = fireAll;

api("/live/state").then(render).catch(err => {
  document.getElementById("steps").innerHTML =
    '<p class="detail">Could not load the campaign: ' + esc(err.message) + '</p>';
});
</script>
</body>
</html>
"""

_PAGE = _PAGE.replace("__CSS__", _CSS)
