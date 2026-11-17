"""The interactive console: fire one attack, watch for the alarm.

The static dashboard in `report.py` shows a finished run; this one lets you pull
the trigger yourself on each kill-chain step and see, in the same instant, the
three facts the project keeps apart: what happened (ground truth), which sensors
recorded it (visibility), and whether a rule fired (detection).

Layout is a security-operations console: a fixed left navigation rail and a main
area of titled sections built from translucent "glass" panels. Zinc near-black
surface, Inter for text and a monospace face for codes and metrics, an orange
alert accent. The three outcomes carry SOC severity semantics — an alarm firing
is orange, a step seen with no rule is yellow, an unseen step is red, because
here an invisible attack is the danger. The kill chain is a severity timeline,
since it really is a sequence.

One self-contained HTML string talks to the control plane's `/live/*` and
`/catalog` JSON; no framework, because the point is the data, not the bundler.
"""

from __future__ import annotations


def render_console() -> str:
    return _PAGE


_CSS = """
:root{
  --bg:#09090b; --sidebar:#0b0b0e; --panel:rgba(24,24,27,.6); --panel-solid:#18181b;
  --panel-2:#1b1b1f; --border:rgba(255,255,255,.08); --border-2:rgba(255,255,255,.14);
  --line-soft:rgba(255,255,255,.05);
  --text:#e4e4e7; --muted:#a1a1aa; --faint:#71717a;
  --orange:#f97316; --orange-2:#fb923c; --orange-bg:rgba(249,115,22,.12); --orange-ln:rgba(249,115,22,.4);
  --red:#ef4444; --red-bg:rgba(239,68,68,.12); --red-ln:rgba(239,68,68,.38);
  --yellow:#eab308; --yellow-bg:rgba(234,179,8,.12); --yellow-ln:rgba(234,179,8,.36);
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#f4f4f5; --sidebar:#ffffff; --panel:#ffffff; --panel-solid:#ffffff;
    --panel-2:#fafafa; --border:#e4e4e7; --border-2:#d4d4d8; --line-soft:#efeff1;
    --text:#18181b; --muted:#52525b; --faint:#8a8a93;
    --orange:#ea580c; --orange-bg:rgba(234,88,12,.1); --orange-ln:rgba(234,88,12,.35);
    --red:#dc2626; --red-bg:rgba(220,38,38,.1); --red-ln:rgba(220,38,38,.3);
    --yellow:#a16207; --yellow-bg:rgba(161,98,7,.12); --yellow-ln:rgba(161,98,7,.32);
  }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  line-height:1.5;-webkit-font-smoothing:antialiased;font-size:15px}
.mono{font-family:var(--mono)}

.app{display:grid;grid-template-columns:256px minmax(0,1fr);min-height:100vh}

/* sidebar */
.sidebar{position:sticky;top:0;height:100vh;display:flex;flex-direction:column;gap:18px;
  padding:22px 16px;background:var(--sidebar);border-right:1px solid var(--border)}
.brand{display:flex;align-items:center;gap:10px;padding:0 6px 2px;font-weight:600;
  letter-spacing:.14em;font-size:.82rem;text-transform:uppercase}
.brand svg{width:20px;height:20px;color:var(--orange)}
.brand .dim{color:var(--faint)}
.side-actions{display:flex;flex-direction:column;gap:8px}
button{font:inherit;cursor:pointer;border-radius:9px;border:1px solid var(--border-2);
  background:var(--panel-2);color:var(--text);padding:9px 14px;font-weight:500;
  transition:border-color .15s,background .15s,transform .04s,opacity .15s}
button:hover{border-color:var(--faint)}
button:active{transform:translateY(1px)}
button.primary{background:var(--orange);border-color:var(--orange);color:#160a02;font-weight:600;
  display:flex;align-items:center;justify-content:center;gap:8px}
button.primary:hover{background:var(--orange-2);border-color:var(--orange-2)}
button:disabled{opacity:.45;cursor:default;transform:none}
nav{display:flex;flex-direction:column;gap:2px}
nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:9px;
  color:var(--muted);text-decoration:none;font-size:.9rem;font-weight:500;
  border-left:2px solid transparent;transition:color .15s,background .15s}
nav a svg{width:17px;height:17px;flex:none;opacity:.8}
nav a:hover{color:var(--text);background:var(--panel-2)}
nav a.active{color:var(--text);background:var(--orange-bg);border-left-color:var(--orange)}
nav a.active svg{color:var(--orange);opacity:1}
.side-sp{flex:1}
.side-status{border:1px solid var(--border);border-radius:11px;padding:12px 13px;
  background:var(--panel-2)}
.side-status .r{display:flex;justify-content:space-between;align-items:baseline;font-size:.8rem;
  color:var(--muted);margin-bottom:7px}
.side-status .r b{font-family:var(--mono);color:var(--text);font-weight:600}
.minimeter{display:flex;height:6px;border-radius:4px;overflow:hidden;background:var(--line-soft);gap:2px;margin-top:2px}
.minimeter span{display:block;transition:flex-grow .5s}
.minimeter .d{background:var(--orange)} .minimeter .v{background:var(--yellow)}
.minimeter .b{background:var(--red)} .minimeter .rest{background:var(--border-2)}
.side-foot{font-size:.74rem;color:var(--faint);padding:0 6px;display:flex;flex-wrap:wrap;gap:4px 10px}
.side-foot a{color:var(--muted);text-decoration:none}
.side-foot a:hover{color:var(--orange-2)}

/* main */
main{min-width:0;padding:0 clamp(16px,2.6vw,34px) 70px}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;
  padding:18px 0 16px;margin-bottom:8px;
  background:linear-gradient(var(--bg) 70%,transparent);backdrop-filter:blur(2px)}
.topbar h1{font-size:1.18rem;font-weight:600;margin:0;letter-spacing:-.01em}
.topbar p{margin:2px 0 0;color:var(--muted);font-size:.84rem}
.topbar .grow{flex:1}
.pill{font-family:var(--mono);font-size:.76rem;color:var(--muted);
  border:1px solid var(--border);border-radius:999px;padding:6px 13px;background:var(--panel-2);white-space:nowrap}
.pill b{color:var(--text)} .pill .live{color:var(--orange)}
.menu-btn{display:none}

section.block{margin:26px 0 0;scroll-margin-top:84px}
.block-head{display:flex;align-items:baseline;gap:12px;margin:0 0 14px}
.block-head h2{font-size:1.02rem;font-weight:600;margin:0;letter-spacing:-.01em}
.block-head span{font-size:.82rem;color:var(--faint)}

.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.col-4{grid-column:span 4} .col-5{grid-column:span 5} .col-6{grid-column:span 6}
.col-7{grid-column:span 7} .col-8{grid-column:span 8} .col-12{grid-column:span 12}
@media(max-width:1040px){
  .col-4,.col-5,.col-6,.col-7,.col-8{grid-column:span 12}
}

.panel{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:20px;
  backdrop-filter:blur(12px)}
.panel.tight{padding:18px}
.plabel{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);
  font-weight:600;margin:0 0 14px;display:flex;align-items:center;justify-content:space-between}
.plabel .tag{font-family:var(--mono);letter-spacing:0;text-transform:none;color:var(--orange-2)}

/* posture */
.meter{display:flex;height:14px;border-radius:8px;overflow:hidden;background:var(--line-soft);gap:2px}
.meter span{display:block;transition:flex-grow .5s cubic-bezier(.2,.7,.2,1)}
.meter .d{background:var(--orange)} .meter .v{background:var(--yellow)}
.meter .b{background:var(--red)} .meter .rest{background:var(--border-2)}
.legend{display:flex;flex-wrap:wrap;gap:22px;margin-top:18px}
.legend div{display:flex;flex-direction:column;gap:4px}
.legend .n{font-family:var(--mono);font-size:1.8rem;font-weight:600;line-height:1;letter-spacing:-.02em}
.legend .t{font-size:.78rem;color:var(--muted);display:flex;align-items:center;gap:7px}
.legend .t i{width:8px;height:8px;border-radius:2px}
.legend .cd .n{color:var(--orange)} .legend .cd i{background:var(--orange)}
.legend .cv .n{color:var(--yellow)} .legend .cv i{background:var(--yellow)}
.legend .cb .n{color:var(--red)} .legend .cb i{background:var(--red)}
.score{display:flex;align-items:flex-end;gap:12px;height:100%}
.score .big{font-family:var(--mono);font-size:2.6rem;font-weight:600;line-height:.85;letter-spacing:-.03em}
.score .big.bad{color:var(--red)}
.score .sub{color:var(--muted);font-size:.8rem;padding-bottom:4px}
.tiles{display:flex;flex-direction:column;gap:16px;height:100%}
.tiles .panel{flex:1;display:flex;flex-direction:column}

/* attack timeline */
.trace{position:relative}
.node{position:relative;display:grid;grid-template-columns:24px 1fr;gap:14px;padding-bottom:12px}
.node::before{content:"";position:absolute;left:11px;top:6px;bottom:0;width:2px;background:var(--border)}
.node:last-child::before{display:none}
.lamp{position:relative;z-index:2;width:16px;height:16px;margin:4px 0 0 3px;border-radius:50%;
  border:2px solid var(--faint);background:var(--panel-solid);transition:all .25s}
.node.detected .lamp{background:var(--orange);border-color:var(--orange);box-shadow:0 0 0 4px var(--orange-bg)}
.node.visible_only .lamp{background:var(--yellow);border-color:var(--yellow);box-shadow:0 0 0 4px var(--yellow-bg)}
.node.blind .lamp{background:var(--red);border-color:var(--red);box-shadow:0 0 0 4px var(--red-bg)}
.body{background:var(--panel-2);border:1px solid var(--border);border-radius:12px;padding:13px 15px;
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
.chip.armed{background:var(--panel);color:var(--faint);border-color:var(--border-2)}
.chip.armed::before{background:var(--faint)}
.title{font-size:1.02rem;font-weight:500;margin:7px 0 0}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0 0}
.tag{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--panel);
  border:1px solid var(--border);border-radius:6px;padding:2px 8px}
.tag.host{color:var(--orange-2);border-color:var(--orange-ln)}
.narr{color:var(--muted);font-size:.86rem;margin:10px 0 0}
.result{margin:11px 0 0;padding:11px 0 0;border-top:1px solid var(--line-soft);
  display:flex;flex-wrap:wrap;gap:6px 18px}
.result .k{font-size:.82rem;color:var(--muted)}
.result .k b{color:var(--text);font-weight:600}
.alerts{margin:9px 0 0;display:flex;flex-direction:column;gap:5px}
.alert{font-size:.82rem;display:flex;gap:8px;align-items:baseline}
.alert .rid{font-family:var(--mono);font-weight:600;color:var(--orange)}
.alert .msg{color:var(--muted)}
.foot-actions{display:flex;justify-content:flex-end;margin-top:10px}

/* data tables */
.compare{display:grid;grid-template-columns:1fr auto auto;font-size:.85rem}
.compare .hd{color:var(--faint);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;
  padding:0 0 9px;border-bottom:1px solid var(--border)}
.compare .hd.r{text-align:right}
.compare .cell{padding:10px 0;border-bottom:1px solid var(--line-soft);display:flex;align-items:center}
.compare .cell.r{justify-content:flex-end;font-family:var(--mono)}
.compare .sensor{font-family:var(--mono);color:var(--text)}
.compare .status{color:var(--muted);padding-right:16px}
.compare .silent{color:var(--red);font-weight:600}
.hint{font-size:.79rem;color:var(--faint);margin:13px 0 0}
.figrow{display:flex;justify-content:space-between;align-items:baseline;padding:10px 0;
  border-bottom:1px solid var(--line-soft)}
.figrow:last-child{border-bottom:0}
.figrow span{font-size:.85rem;color:var(--muted)}
.figrow b{font-family:var(--mono);font-size:1.1rem;font-weight:600}
.figrow.bad b{color:var(--red)}

.matrix{width:100%;border-collapse:collapse;font-size:.82rem}
.matrix th,.matrix td{padding:9px 6px;border-bottom:1px solid var(--line-soft);text-align:center}
.matrix th{color:var(--faint);font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;font-weight:600}
.matrix th:first-child,.matrix td:first-child{text-align:left}
.matrix td.tech{font-family:var(--mono);color:var(--text)}
.matrix .y{color:var(--orange);font-weight:700}
.matrix .no{color:var(--faint)}

.cat{width:100%;border-collapse:collapse;font-size:.85rem}
.cat th,.cat td{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line-soft);vertical-align:top}
.cat th{color:var(--faint);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;font-weight:600}
.cat td.id{font-family:var(--mono);color:var(--orange-2)}
.cat td.code{font-family:var(--mono);color:var(--muted);white-space:nowrap}
.cat td.w{color:var(--text)}
.cat .sub{color:var(--faint);font-size:.8rem;margin-top:3px}

.feed{list-style:none;margin:0;padding:0;max-height:300px;overflow:auto}
.feed li{display:flex;align-items:center;gap:10px;font-size:.84rem;padding:10px 0;
  border-bottom:1px solid var(--line-soft)}
.feed li:last-child{border-bottom:0}
.feed .dot{width:8px;height:8px;border-radius:50%;flex:none}
.feed .dot.detected{background:var(--orange)} .feed .dot.visible_only{background:var(--yellow)} .feed .dot.blind{background:var(--red)}
.feed .fid{font-family:var(--mono);color:var(--faint);font-size:.76rem}
.feed .fname{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.empty{color:var(--faint);font-size:.84rem}

:focus-visible{outline:2px solid var(--orange);outline-offset:2px;border-radius:6px}
@media (prefers-reduced-motion: reduce){*{transition:none!important;scroll-behavior:auto}}

/* responsive: collapse the rail to a top bar */
@media(max-width:860px){
  .app{grid-template-columns:1fr}
  .sidebar{position:fixed;inset:0 auto 0 0;width:248px;z-index:60;transform:translateX(-100%);
    transition:transform .2s;box-shadow:0 0 0 100vmax rgba(0,0,0,0)}
  .sidebar.open{transform:translateX(0);box-shadow:0 0 0 100vmax rgba(0,0,0,.5)}
  .menu-btn{display:inline-flex;align-items:center;gap:8px}
  .topbar .desc{display:none}
}
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
<div class="app">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2 3 6v6c0 5 3.8 8.4 9 10 5.2-1.6 9-5 9-10V6l-9-4Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        <path d="M8.4 12.2 11 14.8l4.6-5.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      EDA <span class="dim">Assurance</span>
    </div>
    <div class="side-actions">
      <button class="primary" id="fire-all">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>
        Run kill chain
      </button>
      <button id="reset">Reset fleet</button>
    </div>
    <nav id="nav">
      <a href="#overview" data-sec="overview">
        <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="9" rx="1.5" stroke="currentColor" stroke-width="1.6"/><rect x="14" y="3" width="7" height="5" rx="1.5" stroke="currentColor" stroke-width="1.6"/><rect x="14" y="12" width="7" height="9" rx="1.5" stroke="currentColor" stroke-width="1.6"/><rect x="3" y="16" width="7" height="5" rx="1.5" stroke="currentColor" stroke-width="1.6"/></svg>
        Overview</a>
      <a href="#timeline" data-sec="timeline">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="8" cy="7" r="2" fill="var(--bg)" stroke="currentColor" stroke-width="1.6"/><circle cx="14" cy="12" r="2" fill="var(--bg)" stroke="currentColor" stroke-width="1.6"/><circle cx="10" cy="17" r="2" fill="var(--bg)" stroke="currentColor" stroke-width="1.6"/></svg>
        Attack timeline</a>
      <a href="#hypotheses" data-sec="hypotheses">
        <svg viewBox="0 0 24 24" fill="none"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
        Hypotheses</a>
      <a href="#weaknesses" data-sec="weaknesses">
        <svg viewBox="0 0 24 24" fill="none"><path d="M12 2 3 6v6c0 5 3.8 8.4 9 10 5.2-1.6 9-5 9-10V6l-9-4Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 8v4M12 15.5v.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
        Planted weaknesses</a>
    </nav>
    <div class="side-sp"></div>
    <div class="side-status">
      <div class="r"><span>Fleet</span><b id="s-fleet">—</b></div>
      <div class="r"><span>Steps fired</span><b id="s-fired">0 / 0</b></div>
      <div class="minimeter" id="minimeter"></div>
    </div>
    <div class="side-foot">
      <a href="/report.html">Report</a><a href="/report">JSON</a><a href="/catalog">Catalog</a>
    </div>
  </aside>

  <main>
    <div class="topbar">
      <button class="menu-btn" id="menu" aria-label="Toggle navigation">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      </button>
      <div>
        <h1>Attack console</h1>
        <p class="desc">Fire a step and watch whether the alarm fires.</p>
      </div>
      <span class="grow"></span>
      <span class="pill"><span class="live">&#9679;</span> <b id="count">0 / 0</b> fired</span>
    </div>

    <section class="block" id="overview">
      <div class="block-head"><h2>Overview</h2>
        <span>A sensor seeing an attack and a rule catching it are not the same measurement.</span></div>
      <div class="grid">
        <div class="panel col-8">
          <p class="plabel">Detection posture</p>
          <div class="meter" id="meter"></div>
          <div class="legend" id="legend"></div>
        </div>
        <div class="col-4 tiles">
          <div class="panel tight">
            <p class="plabel">False alarms</p>
            <div class="score"><span class="big" id="fp">0</span>
              <span class="sub">on <span id="benign">0</span><br>benign events</span></div>
          </div>
          <div class="panel tight">
            <p class="plabel">Reached C2</p>
            <div class="score"><span class="big bad" id="beacons">0</span>
              <span class="sub">beacons delivered,<br>detected or not</span></div>
          </div>
        </div>
      </div>
    </section>

    <section class="block" id="timeline">
      <div class="block-head"><h2>Attack timeline</h2>
        <span>Web tier &rarr; phished laptop &rarr; database. Order is kept.</span></div>
      <div class="grid">
        <div class="panel col-12">
          <p class="plabel">Kill chain<span class="tag" id="tracecount"></span></p>
          <div class="trace" id="trace"></div>
        </div>
      </div>
    </section>

    <section class="block" id="hypotheses">
      <div class="block-head"><h2>Hypotheses</h2>
        <span>Why visibility is not detection, in three measurements.</span></div>
      <div class="grid">
        <div class="panel col-8">
          <p class="plabel">Coverage differs by sensor<span class="tag">H1</span></p>
          <table class="matrix" id="h1"></table>
        </div>
        <div class="panel col-4">
          <p class="plabel">App log is not detection<span class="tag">H3</span></p>
          <div id="h3"></div>
        </div>
        <div class="panel col-5">
          <p class="plabel">Silent failure<span class="tag">H2</span></p>
          <div class="compare" id="h2">
            <div class="hd">Sensor</div><div class="hd r">Status</div><div class="hd r">Canary</div>
          </div>
          <p class="hint">A blinded sensor keeps reporting healthy. Only probing by result hears the silence.</p>
        </div>
        <div class="panel col-7">
          <p class="plabel">Evidence feed</p>
          <ul class="feed" id="feed"></ul>
        </div>
      </div>
    </section>

    <section class="block" id="weaknesses">
      <div class="block-head"><h2>Planted weaknesses</h2>
        <span>Each tagged with its OWASP:2025 category, ATT&amp;CK technique and lecture.</span></div>
      <div class="grid">
        <div class="panel col-12">
          <table class="cat" id="catalog"></table>
        </div>
      </div>
    </section>
  </main>
</div>

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

function fillMeter(node, t, rest){
  node.innerHTML = "";
  for(const [cls, n] of [["d", t.detected], ["v", t.visible_only], ["b", t.blind], ["rest", rest]]){
    const span = el("span", cls); span.style.flexGrow = n; node.appendChild(span);
  }
}

function renderTop(s){
  document.getElementById("s-fleet").textContent = s.fleet.size;
  document.getElementById("s-fired").textContent = s.fired + " / " + s.total;
  document.getElementById("count").textContent = s.fired + " / " + s.total;
  document.getElementById("tracecount").textContent = s.fired + " of " + s.total + " fired";
  fillMeter(document.getElementById("minimeter"), s.tally, Math.max(0, s.total - s.fired));
}

function renderOverview(s){
  const t = s.tally;
  fillMeter(document.getElementById("meter"), t, Math.max(0, s.total - s.fired));
  document.getElementById("legend").innerHTML =
    '<div class="cd"><span class="n">' + t.detected + '</span><span class="t"><i></i>detected</span></div>' +
    '<div class="cv"><span class="n">' + t.visible_only + '</span><span class="t"><i></i>seen, no alarm</span></div>' +
    '<div class="cb"><span class="n">' + t.blind + '</span><span class="t"><i></i>blind</span></div>';
  const fp = document.getElementById("fp");
  fp.textContent = s.false_alarms; fp.className = "big" + (s.false_alarms ? " bad" : "");
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
    res.appendChild(el("span", "k", "Ground truth: <b>" + esc(step.agent) + "</b> " + esc(EFFECT[step.effect_kind] || step.effect_kind)));
    res.appendChild(el("span", "k", "Saw the host effect: <b>" + esc(seen) + "</b>"));
    body.appendChild(res);
    if(step.alerts.length){
      const box = el("div", "alerts");
      for(const a of step.alerts){
        box.appendChild(el("div", "alert", '<span class="rid">' + esc(a.rule_id) + '</span><span class="msg">' + esc(a.message) + '</span>'));
      }
      body.appendChild(box);
    }
  }
  const foot = el("div", "foot-actions");
  const btn = el("button", "fire", step.fired ? "Fire again" : "Fire step");
  btn.onclick = () => fireStep(step.id, btn);
  foot.appendChild(btn); body.appendChild(foot);
  n.appendChild(body);
  return n;
}
function renderTrace(s){
  const box = document.getElementById("trace");
  box.innerHTML = "";
  for(const step of s.steps) box.appendChild(node(step));
}

function renderHypotheses(s){
  const m = s.capability_matrix_h1 || {};
  const techs = Object.keys(m);
  const sensors = techs.length ? Object.keys(m[techs[0]]) : [];
  const h1 = document.getElementById("h1");
  let head = "<thead><tr><th>Technique</th>" + sensors.map(x => "<th>" + esc(x) + "</th>").join("") + "</tr></thead><tbody>";
  let rows = "";
  for(const tech of techs){
    rows += "<tr><td class='tech'>" + esc(tech.split(" ")[0]) + "</td>" +
      sensors.map(x => m[tech][x] ? "<td class='y'>&#10003;</td>" : "<td class='no'>&middot;</td>").join("") + "</tr>";
  }
  h1.innerHTML = head + rows + "</tbody>";

  const sf = s.silent_failure_h2;
  const names = Array.from(new Set([...Object.keys(sf.status_check), ...Object.keys(sf.canary_probe)])).sort();
  const h2 = document.getElementById("h2");
  h2.querySelectorAll(".cell").forEach(e => e.remove());
  for(const name of names){
    const canary = sf.canary_probe[name] || "—";
    const silent = canary === "SILENT";
    h2.appendChild(el("div", "cell sensor", esc(name)));
    h2.appendChild(el("div", "cell r status", esc(sf.status_check[name] || "—")));
    h2.appendChild(el("div", "cell r " + (silent ? "silent" : ""), esc(canary)));
  }

  const d = s.applog_blindness_h3;
  document.getElementById("h3").innerHTML =
    '<div class="figrow"><span>Requests the app logged</span><b>' + esc(d.requests_logged) + '</b></div>' +
    '<div class="figrow bad"><span>Host effects in the app log</span><b>' + esc(d.host_effects_in_app_log) + '</b></div>' +
    '<div class="figrow"><span>Beacons that reached C2</span><b>' + esc(s.beacons_reached_c2) + '</b></div>';

  const feed = document.getElementById("feed");
  const fired = s.steps.filter(x => x.fired);
  feed.innerHTML = "";
  if(!fired.length){ feed.appendChild(el("li", "empty", "No step fired yet. Run the kill chain or fire a step.")); }
  else for(const step of fired.slice().reverse()){
    feed.appendChild(el("li", null,
      '<span class="dot ' + step.outcome + '"></span><span class="fid">' + esc(step.id) +
      '</span><span class="fname">' + esc(VERDICT[step.outcome].chip) + ' — ' + esc(step.name) + '</span>'));
  }
}

function render(s){ renderTop(s); renderOverview(s); renderTrace(s); renderHypotheses(s); }

async function renderCatalog(){
  try{
    const items = await api("/catalog");
    const t = document.getElementById("catalog");
    t.innerHTML = "<thead><tr><th>ID</th><th>Weakness</th><th>OWASP:2025</th><th>ATT&CK</th><th>Lecture</th></tr></thead><tbody>" +
      items.map(v =>
        "<tr><td class='id'>" + esc(v.id) + "</td>" +
        "<td class='w'>" + esc(v.name) + "<div class='sub'>" + esc(v.note) + "</div></td>" +
        "<td class='code'>" + esc(v.owasp_2025) + "</td>" +
        "<td class='code'>" + esc(v.attack) + "</td>" +
        "<td class='code'>" + esc(v.course) + "</td></tr>").join("") + "</tbody>";
  }catch(e){ document.getElementById("catalog").innerHTML = "<tbody><tr><td class='empty'>Catalog unavailable.</td></tr></tbody>"; }
}

async function fireStep(id, btn){ btn.disabled = true; render(await api("/live/fire/" + id, "POST")); }
async function reset(){ render(await api("/live/reset", "POST")); }
async function fireAll(){
  const btn = document.getElementById("fire-all"); btn.disabled = true;
  render(await api("/live/fire-all", "POST")); btn.disabled = false;
}
document.getElementById("reset").onclick = reset;
document.getElementById("fire-all").onclick = fireAll;

// mobile nav
const sidebar = document.getElementById("sidebar");
document.getElementById("menu").onclick = () => sidebar.classList.toggle("open");
document.getElementById("nav").addEventListener("click", () => sidebar.classList.remove("open"));

// scroll-spy
const links = Object.fromEntries([...document.querySelectorAll("#nav a")].map(a => [a.dataset.sec, a]));
const spy = new IntersectionObserver(entries => {
  entries.forEach(e => { if(e.isIntersecting){
    Object.values(links).forEach(a => a.classList.remove("active"));
    links[e.target.id]?.classList.add("active");
  }});
}, {rootMargin: "-45% 0px -50% 0px"});
document.querySelectorAll("section.block").forEach(s => spy.observe(s));

api("/live/state").then(render).catch(err => {
  document.getElementById("trace").innerHTML = '<p class="empty">Could not load the campaign: ' + esc(err.message) + '</p>';
});
renderCatalog();
</script>
</body>
</html>
"""

_PAGE = _PAGE.replace("__CSS__", _CSS)
