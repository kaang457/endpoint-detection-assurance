"""The interactive console: fire one attack, watch for the alarm.

This is the page that makes the whole thesis tangible. The static dashboard in
`report.py` shows a finished run; this one lets you pull the trigger yourself on
each kill-chain step and see, in the same instant, the three facts the project
insists on keeping apart: what really happened (ground truth), which sensors saw
it (visibility), and whether a rule fired (detection).

Visual direction follows a security-operations threat-analysis console: a zinc
near-black surface, Inter for text and a monospace face for codes and metrics,
and an amber/orange alert accent. The three outcomes carry the severity palette
of a SOC — an alarm firing is the orange "a detection fired", a step seen with
no rule is the yellow caution, and an unseen step is the red critical, because
here an invisible attack is the real danger. The kill chain is drawn as a
severity timeline, since it really is a sequence.

One self-contained HTML string talks to the control plane's `/live/*` JSON
endpoints; no framework, because the point is the data, not the bundler.
"""

from __future__ import annotations


def render_console() -> str:
    return _PAGE


_CSS = """
:root{
  --bg:#09090b; --panel:#141417; --panel-2:#1b1b1f; --elev:#232327;
  --line:#27272a; --line-2:#3f3f46; --line-soft:#1d1d20;
  --text:#e4e4e7; --muted:#a1a1aa; --faint:#71717a;
  --orange:#f97316; --orange-2:#fb923c; --orange-bg:#271608; --orange-ln:#7c3f16;
  --red:#ef4444; --red-bg:#271113; --red-ln:#7f2a2d;
  --yellow:#eab308; --yellow-bg:#241f0b; --yellow-ln:#6f5e17;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#f4f4f5; --panel:#ffffff; --panel-2:#fafafa; --elev:#ffffff;
    --line:#e4e4e7; --line-2:#d4d4d8; --line-soft:#eeeeef;
    --text:#18181b; --muted:#52525b; --faint:#8a8a93;
    --orange:#ea580c; --orange-bg:#fdecd9; --orange-ln:#f3c89b;
    --red:#dc2626; --red-bg:#fbe3e3; --red-ln:#f1bcbc;
    --yellow:#a16207; --yellow-bg:#f6eecb; --yellow-ln:#e4d49a;
  }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  line-height:1.5;-webkit-font-smoothing:antialiased;font-size:15px}
.mono{font-family:var(--mono)}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
.lbl{font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);
  font-weight:600}

/* top rail */
.rail{position:sticky;top:0;z-index:40;background:color-mix(in srgb,var(--bg) 85%,transparent);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;align-items:center;gap:14px;height:60px}
.brand{display:flex;align-items:center;gap:10px;font-weight:600;letter-spacing:.14em;
  font-size:.82rem;text-transform:uppercase}
.brand svg{width:20px;height:20px;color:var(--orange)}
.brand .dim{color:var(--faint)}
.rail .grow{flex:1}
.rail nav{display:flex;gap:4px}
.rail nav a{color:var(--muted);font-size:.84rem;padding:7px 11px;border-radius:7px;text-decoration:none}
.rail nav a:hover{color:var(--text);background:var(--panel-2)}
.pill{font-family:var(--mono);font-size:.76rem;color:var(--muted);
  border:1px solid var(--line);border-radius:999px;padding:5px 12px;background:var(--panel)}
.pill b{color:var(--text);font-weight:600}
.pill .live{color:var(--orange)}

/* overview */
.hero{padding:30px 0 10px}
.hero .lbl{margin-bottom:12px}
.hero h1{font-size:clamp(1.7rem,3.6vw,2.45rem);line-height:1.05;margin:0 0 10px;
  font-weight:600;letter-spacing:-.022em;max-width:20ch}
.hero p{margin:0;max-width:66ch;color:var(--muted);font-size:1rem}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:20px}
button{font:inherit;cursor:pointer;border-radius:8px;border:1px solid var(--line-2);
  background:var(--panel-2);color:var(--text);padding:9px 15px;font-weight:500;
  transition:border-color .15s,background .15s,transform .04s}
button:hover{border-color:var(--faint)}
button:active{transform:translateY(1px)}
button.primary{background:var(--orange);border-color:var(--orange);color:#160a02;font-weight:600}
button.primary:hover{background:var(--orange-2);border-color:var(--orange-2)}
button:disabled{opacity:.45;cursor:default;transform:none}
.count{font-family:var(--mono);font-size:.8rem;color:var(--faint);margin-left:4px}

.overview{display:grid;grid-template-columns:1.7fr 1fr 1fr;gap:16px;margin:22px 0 26px}
@media(max-width:820px){.overview{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}
.panel > .lbl{display:block;margin-bottom:14px}
.meter{display:flex;height:14px;border-radius:8px;overflow:hidden;background:var(--line-soft);gap:2px}
.meter span{display:block;transition:flex-grow .5s cubic-bezier(.2,.7,.2,1)}
.meter .d{background:var(--orange)} .meter .v{background:var(--yellow)}
.meter .b{background:var(--red)} .meter .rest{background:var(--line-2)}
.legend{display:flex;flex-wrap:wrap;gap:20px;margin-top:16px}
.legend div{display:flex;flex-direction:column;gap:3px}
.legend .n{font-family:var(--mono);font-size:1.7rem;font-weight:600;line-height:1;letter-spacing:-.02em}
.legend .t{font-size:.78rem;color:var(--muted);display:flex;align-items:center;gap:6px}
.legend .t i{width:8px;height:8px;border-radius:2px}
.legend .cd .n{color:var(--orange)} .legend .cd i{background:var(--orange)}
.legend .cv .n{color:var(--yellow)} .legend .cv i{background:var(--yellow)}
.legend .cb .n{color:var(--red)} .legend .cb i{background:var(--red)}
.score{display:flex;align-items:flex-end;gap:12px}
.score .big{font-family:var(--mono);font-size:2.6rem;font-weight:600;line-height:.9;letter-spacing:-.03em}
.score .big.ok{color:var(--text)} .score .big.bad{color:var(--red)}
.score .sub{color:var(--muted);font-size:.82rem;padding-bottom:4px}

/* main grid */
.grid{display:grid;grid-template-columns:1fr 348px;gap:18px;padding-bottom:70px;align-items:start}
@media(max-width:960px){.grid{grid-template-columns:1fr}}
.panel-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.panel-head h2{font-size:1.05rem;font-weight:600;margin:0;letter-spacing:-.01em}
.panel-head .meta{font-family:var(--mono);font-size:.76rem;color:var(--faint)}
.lede{color:var(--muted);margin:0 0 18px;max-width:64ch;font-size:.9rem}

/* attack timeline */
.trace{position:relative}
.node{position:relative;display:grid;grid-template-columns:24px 1fr;gap:14px;padding-bottom:12px}
.node::before{content:"";position:absolute;left:11px;top:6px;bottom:0;width:2px;background:var(--line)}
.node:last-child::before{display:none}
.lamp{position:relative;z-index:2;width:16px;height:16px;margin:4px 0 0 3px;border-radius:50%;
  border:2px solid var(--faint);background:var(--panel);transition:all .25s}
.node.detected .lamp{background:var(--orange);border-color:var(--orange);box-shadow:0 0 0 4px var(--orange-bg)}
.node.visible_only .lamp{background:var(--yellow);border-color:var(--yellow);box-shadow:0 0 0 4px var(--yellow-bg)}
.node.blind .lamp{background:var(--red);border-color:var(--red);box-shadow:0 0 0 4px var(--red-bg)}
.body{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px;
  transition:border-color .2s}
.node.detected .body{border-color:var(--orange-ln)}
.node.visible_only .body{border-color:var(--yellow-ln)}
.node.blind .body{border-color:var(--red-ln)}
.head{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.idx{font-family:var(--mono);font-size:.76rem;color:var(--faint)}
.tactic{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--orange-2);font-weight:600}
.chip{display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:.74rem;
  padding:4px 11px;border-radius:999px;margin-left:auto;white-space:nowrap;border:1px solid transparent}
.chip::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.chip.detected{background:var(--orange-bg);color:var(--orange);border-color:var(--orange-ln)}
.chip.visible_only{background:var(--yellow-bg);color:var(--yellow);border-color:var(--yellow-ln)}
.chip.blind{background:var(--red-bg);color:var(--red);border-color:var(--red-ln)}
.chip.armed{background:var(--panel-2);color:var(--faint);border-color:var(--line-2)}
.chip.armed::before{background:var(--faint)}
.title{font-size:1.02rem;font-weight:500;margin:7px 0 0}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0 0}
.tag{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--panel-2);
  border:1px solid var(--line);border-radius:6px;padding:2px 8px}
.tag.host{color:var(--orange-2);border-color:var(--orange-ln)}
.narr{color:var(--muted);font-size:.86rem;margin:10px 0 0}
.result{margin:11px 0 0;padding:11px 0 0;border-top:1px solid var(--line-soft);
  display:flex;flex-wrap:wrap;gap:6px 18px}
.result .k{font-size:.82rem;color:var(--muted)}
.result .k b{color:var(--text);font-weight:600}
.alerts{margin:9px 0 0;display:flex;flex-direction:column;gap:5px}
.alert{font-size:.82rem;color:var(--orange-2);display:flex;gap:8px;align-items:baseline}
.alert .rid{font-family:var(--mono);font-weight:600;color:var(--orange)}
.alert .msg{color:var(--muted)}
.foot-actions{display:flex;justify-content:flex-end;margin-top:10px}

/* inspector */
.side{position:sticky;top:78px;display:flex;flex-direction:column;gap:16px}
.compare{display:grid;grid-template-columns:1fr auto auto;font-size:.84rem}
.compare .hd{color:var(--faint);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;
  padding:0 0 9px;border-bottom:1px solid var(--line)}
.compare .hd.r{text-align:right}
.compare .cell{padding:9px 0;border-bottom:1px solid var(--line-soft);display:flex;align-items:center}
.compare .cell.r{justify-content:flex-end;font-family:var(--mono)}
.compare .sensor{font-family:var(--mono);color:var(--text)}
.compare .status{color:var(--muted);padding-right:16px}
.compare .silent{color:var(--red);font-weight:600}
.compare .alive{color:var(--muted)}
.hint{font-size:.79rem;color:var(--faint);margin:12px 0 0}
.figrow{display:flex;justify-content:space-between;align-items:baseline;padding:9px 0;
  border-bottom:1px solid var(--line-soft)}
.figrow:last-child{border-bottom:0}
.figrow span{font-size:.85rem;color:var(--muted)}
.figrow b{font-family:var(--mono);font-size:1.1rem;font-weight:600}
.figrow.bad b{color:var(--red)}
.feed{list-style:none;margin:0;padding:0;max-height:290px;overflow:auto}
.feed li{display:flex;align-items:center;gap:10px;font-size:.84rem;padding:9px 0;
  border-bottom:1px solid var(--line-soft)}
.feed li:last-child{border-bottom:0}
.feed .dot{width:8px;height:8px;border-radius:50%;flex:none}
.feed .dot.detected{background:var(--orange)} .feed .dot.visible_only{background:var(--yellow)} .feed .dot.blind{background:var(--red)}
.feed .fid{font-family:var(--mono);color:var(--faint);font-size:.76rem}
.feed .fname{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.empty{color:var(--faint);font-size:.84rem}

footer{border-top:1px solid var(--line);padding:22px 0 60px;color:var(--muted);font-size:.84rem}
footer .wrap{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center}
footer a{color:var(--orange-2);text-decoration:none}
footer a:hover{text-decoration:underline}
footer .sep{color:var(--line-2)}
:focus-visible{outline:2px solid var(--orange);outline-offset:2px;border-radius:6px}
@media (prefers-reduced-motion: reduce){*{transition:none!important;scroll-behavior:auto}}
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDA — Attack Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head>
<body>
<div class="rail">
  <div class="wrap">
    <span class="brand">
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2 3 6v6c0 5 3.8 8.4 9 10 5.2-1.6 9-5 9-10V6l-9-4Z"
          stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        <path d="M8.4 12.2 11 14.8l4.6-5.2" stroke="currentColor" stroke-width="1.6"
          stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      EDA <span class="dim">Assurance</span>
    </span>
    <span class="grow"></span>
    <nav>
      <a href="#timeline">Timeline</a>
      <a href="/report.html">Report</a>
      <a href="/catalog">Weaknesses</a>
    </nav>
    <span class="pill"><span class="live">&#9679;</span> fleet <b id="fleetsize">&mdash;</b></span>
  </div>
</div>

<main class="wrap">
  <section class="hero">
    <span class="lbl">Live attack console</span>
    <h1>Fire an attack. See if the alarm fires.</h1>
    <p>Each step runs a real but benign action on one host in the fleet. You see
      three things at once: what happened, which sensors recorded it, and whether
      a rule fired. A sensor seeing an attack and a rule catching it are not the
      same measurement — the gap between them is where attackers live.</p>
    <div class="controls">
      <button class="primary" id="fire-all">Run the full kill chain</button>
      <button id="reset">Reset fleet</button>
      <span class="count" id="count"></span>
    </div>
  </section>

  <section class="overview">
    <div class="panel">
      <span class="lbl">Detection posture</span>
      <div class="meter" id="meter"></div>
      <div class="legend" id="legend"></div>
    </div>
    <div class="panel">
      <span class="lbl">False alarms</span>
      <div class="score"><span class="big ok" id="fp">0</span>
        <span class="sub">on <span id="benign">0</span><br>benign events</span></div>
    </div>
    <div class="panel">
      <span class="lbl">Reached C2</span>
      <div class="score"><span class="big bad" id="beacons">0</span>
        <span class="sub">beacons delivered,<br>detected or not</span></div>
    </div>
  </section>

  <section class="grid" id="timeline">
    <div class="panel">
      <div class="panel-head">
        <h2>Attack timeline</h2>
        <span class="meta" id="tracecount"></span>
      </div>
      <p class="lede">One intrusion walks from the web tier through a phished
        laptop to the database. Pull a trigger on any step. Order is kept: disable
        logging on the database (s11), then fire its beacon (s12) again to watch a
        detected action go dark.</p>
      <div class="trace" id="trace"></div>
    </div>

    <aside class="side">
      <div class="panel">
        <div class="panel-head"><h2>Silent failure</h2><span class="meta">H2</span></div>
        <div class="compare" id="h2">
          <div class="hd">Sensor</div><div class="hd r">Status</div><div class="hd r">Canary</div>
        </div>
        <p class="hint">A blinded sensor keeps reporting healthy. Only probing by
          result hears the silence.</p>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>App log is not detection</h2><span class="meta">H3</span></div>
        <div id="h3"></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>Evidence feed</h2></div>
        <ul class="feed" id="feed"></ul>
      </div>
    </aside>
  </section>
</main>

<footer>
  <div class="wrap">
    <span>Ground truth is known because this console runs every step itself.</span>
    <a href="/report.html">Static report</a><span class="sep">/</span>
    <a href="/report">JSON</a><span class="sep">/</span>
    <a href="/catalog">Planted weaknesses</a>
  </div>
</footer>

<script>
const VERDICT = {
  detected:     {chip: "Alarm raised"},
  visible_only: {chip: "Seen, no alarm"},
  blind:        {chip: "Unseen"},
  armed:        {chip: "Armed"},
};
const EFFECT = {
  process_spawn: "started a process",
  file_read: "read a file",
  network_connect: "opened a network connection",
  log_tamper: "cleared a log",
  app_request: "served a request",
};

async function api(path, method){
  const r = await fetch(path, {method: method || "GET"});
  if(!r.ok) throw new Error(path + " returned " + r.status);
  return r.json();
}
function el(tag, cls, html){
  const e = document.createElement(tag);
  if(cls) e.className = cls;
  if(html !== undefined) e.innerHTML = html;
  return e;
}
function esc(s){ return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }

function renderTop(s){
  document.getElementById("fleetsize").textContent = s.fleet.size;
  document.getElementById("count").textContent = s.fired + " of " + s.total + " steps fired";
  document.getElementById("tracecount").textContent = s.fired + " / " + s.total;
}

function renderMeter(s){
  const t = s.tally, rest = Math.max(0, s.total - s.fired);
  const meter = document.getElementById("meter");
  meter.innerHTML = "";
  for(const [cls, n] of [["d", t.detected], ["v", t.visible_only], ["b", t.blind], ["rest", rest]]){
    const span = el("span", cls);
    span.style.flexGrow = n;
    meter.appendChild(span);
  }
  document.getElementById("legend").innerHTML =
    '<div class="cd"><span class="n">' + t.detected + '</span><span class="t"><i></i>detected</span></div>' +
    '<div class="cv"><span class="n">' + t.visible_only + '</span><span class="t"><i></i>seen, no alarm</span></div>' +
    '<div class="cb"><span class="n">' + t.blind + '</span><span class="t"><i></i>blind</span></div>';
  const fp = document.getElementById("fp");
  fp.textContent = s.false_alarms;
  fp.className = "big " + (s.false_alarms ? "bad" : "ok");
  document.getElementById("benign").textContent = s.benign_events;
  document.getElementById("beacons").textContent = s.beacons_reached_c2;
}

function node(step){
  const n = el("div", "node " + step.outcome);
  n.appendChild(el("div", "lamp"));
  const body = el("div", "body");

  const head = el("div", "head");
  head.appendChild(el("span", "idx", esc(step.id)));
  head.appendChild(el("span", "tactic", esc(step.tactic)));
  head.appendChild(el("span", "chip " + step.outcome, esc(VERDICT[step.outcome].chip)));
  body.appendChild(head);

  body.appendChild(el("p", "title", esc(step.name)));

  const tags = el("div", "tags");
  tags.appendChild(el("span", "tag host", esc(step.agent)));
  tags.appendChild(el("span", "tag", esc(step.technique.split(" ")[0])));
  tags.appendChild(el("span", "tag", esc(step.owasp.split(" ")[0])));
  tags.appendChild(el("span", "tag", "sensors " + esc(step.sensors_present.join(" "))));
  body.appendChild(tags);

  body.appendChild(el("p", "narr", esc(step.narrative)));

  if(step.fired){
    const seen = step.seen_by.length ? step.seen_by.join(", ") : "nothing";
    const res = el("div", "result");
    res.appendChild(el("span", "k",
      "Ground truth: <b>" + esc(step.agent) + "</b> " + esc(EFFECT[step.effect_kind] || step.effect_kind)));
    res.appendChild(el("span", "k", "Saw the host effect: <b>" + esc(seen) + "</b>"));
    body.appendChild(res);
    if(step.alerts.length){
      const box = el("div", "alerts");
      for(const a of step.alerts){
        box.appendChild(el("div", "alert",
          '<span class="rid">' + esc(a.rule_id) + '</span><span class="msg">' + esc(a.message) + '</span>'));
      }
      body.appendChild(box);
    }
  }

  const foot = el("div", "foot-actions");
  const btn = el("button", "fire", step.fired ? "Fire again" : "Fire step");
  btn.onclick = () => fireStep(step.id, btn);
  foot.appendChild(btn);
  body.appendChild(foot);

  n.appendChild(body);
  return n;
}

function renderTrace(s){
  const box = document.getElementById("trace");
  box.innerHTML = "";
  for(const step of s.steps) box.appendChild(node(step));
}

function renderInspector(s){
  const sf = s.silent_failure_h2;
  const names = Array.from(new Set([...Object.keys(sf.status_check), ...Object.keys(sf.canary_probe)])).sort();
  const h2 = document.getElementById("h2");
  h2.querySelectorAll(".cell").forEach(e => e.remove());
  for(const name of names){
    const status = sf.status_check[name] || "—";
    const canary = sf.canary_probe[name] || "—";
    const silent = canary === "SILENT";
    h2.appendChild(el("div", "cell sensor", esc(name)));
    h2.appendChild(el("div", "cell r status", esc(status)));
    h2.appendChild(el("div", "cell r " + (silent ? "silent" : "alive"), esc(canary)));
  }

  const d = s.applog_blindness_h3;
  document.getElementById("h3").innerHTML =
    '<div class="figrow"><span>Requests the app logged</span><b>' + esc(d.requests_logged) + '</b></div>' +
    '<div class="figrow bad"><span>Host effects in the app log</span><b>' + esc(d.host_effects_in_app_log) + '</b></div>' +
    '<div class="figrow"><span>Beacons that reached C2</span><b>' + esc(s.beacons_reached_c2) + '</b></div>';

  const feed = document.getElementById("feed");
  const fired = s.steps.filter(x => x.fired);
  feed.innerHTML = "";
  if(!fired.length){ feed.appendChild(el("li", "empty", "No step fired yet. Pull a trigger on the left.")); return; }
  for(const step of fired.slice().reverse()){
    const li = el("li");
    li.innerHTML =
      '<span class="dot ' + step.outcome + '"></span>' +
      '<span class="fid">' + esc(step.id) + '</span>' +
      '<span class="fname">' + esc(VERDICT[step.outcome].chip) + ' — ' + esc(step.name) + '</span>';
    feed.appendChild(li);
  }
}

function render(s){ renderTop(s); renderMeter(s); renderTrace(s); renderInspector(s); }

async function fireStep(id, btn){
  btn.disabled = true;
  render(await api("/live/fire/" + id, "POST"));
}
async function reset(){ render(await api("/live/reset", "POST")); }
async function fireAll(){
  const btn = document.getElementById("fire-all");
  btn.disabled = true;
  render(await api("/live/fire-all", "POST"));
  btn.disabled = false;
}

document.getElementById("reset").onclick = reset;
document.getElementById("fire-all").onclick = fireAll;
api("/live/state").then(render).catch(err => {
  document.getElementById("trace").innerHTML =
    '<p class="empty">Could not load the campaign: ' + esc(err.message) + '</p>';
});
</script>
</body>
</html>
"""

_PAGE = _PAGE.replace("__CSS__", _CSS)
