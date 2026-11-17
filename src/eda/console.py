"""The interactive console: fire one attack, read the detection verdict.

The static dashboard in `report.py` shows a finished run; this one is the
workbench. It follows the blue-team workflow directly: read the current
posture, pick an attack step, fire it, see what the sensors recorded, and read
whether a rule fired — detected, observed-but-not-detected, or blind.

The layout is a master-detail workspace, the way Elastic Security, Defender and
Splunk present events: a dense list of steps on the left, an inspector on the
right. Surfaces are flat, not glass. One interactive accent (steel blue) is kept
separate from the severity colors, which are load-bearing: detection working is
green, observed-with-no-rule is amber, and an unseen step is red, because an
invisible attack is the danger here.

One self-contained HTML string talks to the control plane's `/live/*` and
`/catalog` JSON; no framework, because the point is the data, not the bundler.
"""

from __future__ import annotations


def render_console() -> str:
    return _PAGE


_CSS = """
:root{
  --bg:#0b0d10; --surface:#111418; --surface-2:#161a20; --raised:#1b2027;
  --border:#20262d; --border-2:#2b333c; --line:#191e24;
  --text:#dce3ea; --muted:#8a95a3; --faint:#5f6b78;
  --accent:#4c8dff; --accent-2:#6ba1ff; --accent-bg:rgba(76,141,255,.14); --accent-ln:rgba(76,141,255,.45);
  --green:#3fb950; --green-bg:rgba(63,185,80,.13); --green-ln:rgba(63,185,80,.4);
  --amber:#d29922; --amber-bg:rgba(210,153,34,.13); --amber-ln:rgba(210,153,34,.4);
  --red:#f85149; --red-bg:rgba(248,81,73,.13); --red-ln:rgba(248,81,73,.42);
  --r:6px; --r2:8px;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#f6f7f9; --surface:#ffffff; --surface-2:#f1f3f6; --raised:#ffffff;
    --border:#dfe3e8; --border-2:#cdd3da; --line:#eceff2;
    --text:#161b22; --muted:#56606c; --faint:#8993a0;
    --accent:#2563eb; --accent-bg:rgba(37,99,235,.1); --accent-ln:rgba(37,99,235,.35);
    --green:#1a7f37; --green-bg:rgba(26,127,55,.1); --green-ln:rgba(26,127,55,.3);
    --amber:#9a6700; --amber-bg:rgba(154,103,0,.1); --amber-ln:rgba(154,103,0,.3);
    --red:#cf222e; --red-bg:rgba(207,34,46,.1); --red-ln:rgba(207,34,46,.3);
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
.mono{font-family:var(--mono)}
button{font:inherit;cursor:pointer;border-radius:var(--r);border:1px solid var(--border-2);
  background:var(--surface-2);color:var(--text);padding:7px 12px;font-weight:500;
  transition:border-color .12s,background .12s}
button:hover{border-color:var(--faint)}
button:disabled{opacity:.5;cursor:default}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
button.primary:hover{background:var(--accent-2);border-color:var(--accent-2)}
button.sm{padding:5px 10px;font-size:.85rem}
:focus-visible{outline:2px solid var(--accent);outline-offset:1px;border-radius:var(--r)}

.app{display:grid;grid-template-columns:232px minmax(0,1fr);min-height:100vh}

/* sidebar */
.sidebar{position:sticky;top:0;height:100vh;display:flex;flex-direction:column;
  background:var(--surface);border-right:1px solid var(--border);padding:16px 12px}
.brand{display:flex;align-items:center;gap:9px;padding:4px 8px 16px;font-weight:600;
  letter-spacing:.02em;font-size:.95rem}
.brand svg{width:19px;height:19px;color:var(--accent)}
.brand .dim{color:var(--faint);font-weight:400}
nav{display:flex;flex-direction:column;gap:1px}
nav button{display:flex;align-items:center;gap:10px;padding:8px 10px;border:0;background:none;
  color:var(--muted);text-align:left;border-radius:var(--r);font-size:.9rem;font-weight:500;width:100%}
nav button svg{width:16px;height:16px;flex:none;opacity:.85}
nav button:hover{color:var(--text);background:var(--surface-2)}
nav button.active{color:var(--text);background:var(--accent-bg)}
nav button.active svg{color:var(--accent);opacity:1}
.navcount{margin-left:auto;font-family:var(--mono);font-size:.74rem;color:var(--faint)}
.side-sp{flex:1}
.fleetbox{border-top:1px solid var(--border);padding:14px 8px 8px;margin-top:10px}
.fleetbox .r{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);margin-bottom:8px}
.fleetbox .r b{font-family:var(--mono);color:var(--text);font-weight:500}
.sidelinks{display:flex;gap:14px;padding:12px 8px 2px;font-size:.78rem}
.sidelinks a{color:var(--faint);text-decoration:none}
.sidelinks a:hover{color:var(--accent-2)}

/* main */
main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:18px;
  padding:12px 20px;background:var(--surface);border-bottom:1px solid var(--border);flex-wrap:wrap}
.posture{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.pstat{display:flex;align-items:baseline;gap:7px}
.pstat i{width:8px;height:8px;border-radius:2px;align-self:center}
.pstat .v{font-family:var(--mono);font-size:1.05rem;font-weight:600}
.pstat .k{font-size:.82rem;color:var(--muted)}
.pstat.det i{background:var(--green)} .pstat.det .v{color:var(--green)}
.pstat.obs i{background:var(--amber)} .pstat.obs .v{color:var(--amber)}
.pstat.bli i{background:var(--red)} .pstat.bli .v{color:var(--red)}
.pstat.c2 .v{color:var(--red)}
.pdiv{width:1px;height:26px;background:var(--border)}
.topbar .grow{flex:1}
.topbar .acts{display:flex;gap:8px}
.menu-btn{display:none}

.view{display:none;padding:18px 20px 60px}
.view.active{display:block}
.vhead{margin:0 0 14px}
.vhead h2{font-size:1.05rem;font-weight:600;margin:0}
.vhead p{margin:3px 0 0;color:var(--muted);font-size:.86rem}

/* master-detail */
.workspace{display:grid;grid-template-columns:minmax(0,1fr) 384px;gap:16px;align-items:start}
@media(max-width:1060px){.workspace{grid-template-columns:1fr}}
.list{border:1px solid var(--border);border-radius:var(--r2);overflow:hidden;background:var(--surface)}
.listhead{display:grid;grid-template-columns:14px 30px 1fr 96px 80px;gap:12px;
  padding:9px 14px;border-bottom:1px solid var(--border);font-size:.72rem;color:var(--faint);
  background:var(--surface-2)}
.row{display:grid;grid-template-columns:14px 30px 1fr 96px 80px;gap:12px;align-items:center;
  width:100%;padding:11px 14px;border:0;border-bottom:1px solid var(--line);background:none;
  color:var(--text);text-align:left;border-left:2px solid transparent;border-radius:0}
.row:last-child{border-bottom:0}
.row:hover{background:var(--surface-2)}
.row.sel{background:var(--accent-bg);border-left-color:var(--accent)}
.row .lamp{width:9px;height:9px;border-radius:50%;background:var(--faint);justify-self:center}
.row.detected .lamp{background:var(--green)} .row.visible_only .lamp{background:var(--amber)}
.row.blind .lamp{background:var(--red)}
.row .rid{font-family:var(--mono);font-size:.8rem;color:var(--faint)}
.row .rname{min-width:0}
.row .rname b{font-weight:500;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .rname small{color:var(--faint);font-size:.74rem}
.row .rhost{font-family:var(--mono);font-size:.78rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .otag{font-size:.74rem;font-weight:600;padding:2px 8px;border-radius:4px;text-align:center;
  border:1px solid transparent;white-space:nowrap}
.otag.detected{color:var(--green);background:var(--green-bg);border-color:var(--green-ln)}
.otag.visible_only{color:var(--amber);background:var(--amber-bg);border-color:var(--amber-ln)}
.otag.blind{color:var(--red);background:var(--red-bg);border-color:var(--red-ln)}
.otag.armed{color:var(--faint);background:var(--surface-2);border-color:var(--border-2)}
@media(max-width:620px){
  .listhead,.row{grid-template-columns:14px 28px 1fr 74px}
  .listhead .h-host,.row .rhost{display:none}
}

/* inspector */
.inspector{position:sticky;top:76px;border:1px solid var(--border);border-radius:var(--r2);
  background:var(--surface);padding:16px}
.insp-id{display:flex;align-items:center;gap:9px;font-size:.78rem;color:var(--faint)}
.insp-id .tactic{color:var(--accent-2);font-weight:600}
.inspector h3{font-size:1.02rem;font-weight:600;margin:7px 0 0}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}
.meta span{font-family:var(--mono);font-size:.74rem;color:var(--muted);background:var(--surface-2);
  border:1px solid var(--border);border-radius:4px;padding:2px 7px}
.meta span.host{color:var(--accent-2);border-color:var(--accent-ln)}
.narr{color:var(--muted);font-size:.86rem;margin:13px 0 0}
.verdict{display:flex;align-items:center;gap:10px;margin:16px 0 0;padding:12px 14px;border-radius:var(--r);
  border:1px solid var(--border-2);background:var(--surface-2)}
.verdict .ic{width:22px;height:22px;flex:none}
.verdict .vt{font-weight:600}
.verdict .vs{display:block;font-weight:400;color:var(--muted);font-size:.82rem}
.verdict.detected{background:var(--green-bg);border-color:var(--green-ln);color:var(--green)}
.verdict.visible_only{background:var(--amber-bg);border-color:var(--amber-ln);color:var(--amber)}
.verdict.blind{background:var(--red-bg);border-color:var(--red-ln);color:var(--red)}
.verdict.armed{color:var(--muted)}
.telemetry{margin:14px 0 0;display:flex;flex-direction:column;gap:0}
.trow{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);font-size:.85rem}
.trow:last-child{border-bottom:0}
.trow .k{color:var(--muted)} .trow .val{font-family:var(--mono);text-align:right;color:var(--text)}
.trow .val.none{color:var(--red)}
.alertline{font-size:.82rem;margin-top:9px;display:flex;gap:8px;align-items:baseline}
.alertline .rid{font-family:var(--mono);font-weight:600;color:var(--green)}
.alertline .msg{color:var(--muted)}
.insp-act{margin-top:16px;display:flex;gap:8px}
.insp-act button{flex:1}
.insp-empty{color:var(--faint);font-size:.86rem;padding:30px 4px;text-align:center}

/* panels (hypotheses, weaknesses) */
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.col-4{grid-column:span 4} .col-5{grid-column:span 5} .col-6{grid-column:span 6}
.col-7{grid-column:span 7} .col-8{grid-column:span 8} .col-12{grid-column:span 12}
@media(max-width:1040px){.col-4,.col-5,.col-6,.col-7,.col-8{grid-column:span 12}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r2);padding:16px}
.panel h3{font-size:.92rem;font-weight:600;margin:0 0 3px;display:flex;justify-content:space-between;align-items:baseline}
.panel h3 .tag{font-family:var(--mono);font-size:.72rem;color:var(--accent-2);font-weight:500}
.panel .sub{color:var(--faint);font-size:.8rem;margin:0 0 14px}

.tbl{width:100%;border-collapse:collapse;font-size:.84rem}
.tbl th,.tbl td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.tbl th{color:var(--faint);font-size:.72rem;font-weight:600}
.tbl th:not(:first-child),.tbl td:not(:first-child){text-align:center}
.tbl td.tech{font-family:var(--mono);text-align:left;color:var(--text)}
.tbl .y{color:var(--green);font-weight:700}
.tbl .no{color:var(--faint)}
.cmp{width:100%;border-collapse:collapse;font-size:.85rem}
.cmp th,.cmp td{padding:9px 6px;border-bottom:1px solid var(--line)}
.cmp th{color:var(--faint);font-size:.72rem;text-align:left}
.cmp th:not(:first-child),.cmp td:not(:first-child){text-align:right;font-family:var(--mono)}
.cmp td.sensor{font-family:var(--mono);color:var(--text)}
.cmp td.silent{color:var(--red);font-weight:600}
.cmp td.status{color:var(--muted)}
.figrow{display:flex;justify-content:space-between;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--line)}
.figrow:last-child{border-bottom:0}
.figrow span{color:var(--muted)} .figrow b{font-family:var(--mono);font-size:1.05rem;font-weight:600}
.figrow.bad b{color:var(--red)}
.hint{font-size:.79rem;color:var(--faint);margin:12px 0 0}
.feed{list-style:none;margin:0;padding:0;max-height:260px;overflow:auto}
.feed li{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--line);font-size:.84rem}
.feed li:last-child{border-bottom:0}
.feed .dot{width:8px;height:8px;border-radius:50%;flex:none}
.feed .dot.detected{background:var(--green)} .feed .dot.visible_only{background:var(--amber)} .feed .dot.blind{background:var(--red)}
.feed .fid{font-family:var(--mono);color:var(--faint);font-size:.76rem}
.feed .fname{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat td.id{font-family:var(--mono);color:var(--accent-2)}
.cat td.code{font-family:var(--mono);color:var(--muted);white-space:nowrap;font-size:.8rem}
.cat td.w{color:var(--text)} .cat td{text-align:left!important}
.cat .csub{color:var(--faint);font-size:.8rem;margin-top:2px}

@media(max-width:860px){
  .app{grid-template-columns:1fr}
  .sidebar{position:fixed;inset:0 auto 0 0;width:236px;z-index:60;transform:translateX(-100%);transition:transform .2s}
  .sidebar.open{transform:translateX(0);box-shadow:0 0 0 100vmax rgba(0,0,0,.55)}
  .menu-btn{display:inline-flex}
}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
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
    <nav id="nav">
      <button data-view="chain" class="active">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="8" cy="7" r="1.9" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/><circle cx="14" cy="12" r="1.9" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/><circle cx="10" cy="17" r="1.9" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/></svg>
        Attack chain<span class="navcount" id="nc-chain"></span></button>
      <button data-view="hypotheses">
        <svg viewBox="0 0 24 24" fill="none"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
        Hypotheses</button>
      <button data-view="weaknesses">
        <svg viewBox="0 0 24 24" fill="none"><path d="M12 2 3 6v6c0 5 3.8 8.4 9 10 5.2-1.6 9-5 9-10V6l-9-4Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 8v4M12 15.5v.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
        Weaknesses<span class="navcount" id="nc-weak"></span></button>
    </nav>
    <div class="side-sp"></div>
    <div class="fleetbox">
      <div class="r"><span>Fleet</span><b id="s-fleet">—</b></div>
      <div class="r"><span>Steps fired</span><b id="s-fired">0 / 0</b></div>
      <div class="sidelinks">
        <a href="/report.html">Report</a><a href="/report">JSON</a><a href="/catalog">Catalog</a>
      </div>
    </div>
  </aside>

  <main>
    <div class="topbar">
      <button class="menu-btn sm" id="menu" aria-label="Toggle navigation">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      </button>
      <div class="posture">
        <span class="pstat det"><i></i><span class="v" id="p-det">0</span><span class="k">detected</span></span>
        <span class="pstat obs"><i></i><span class="v" id="p-obs">0</span><span class="k">observed</span></span>
        <span class="pstat bli"><i></i><span class="v" id="p-bli">0</span><span class="k">blind</span></span>
        <span class="pdiv"></span>
        <span class="pstat"><span class="v" id="p-fp">0</span><span class="k">false alarms</span></span>
        <span class="pstat c2"><span class="v" id="p-c2">0</span><span class="k">reached C2</span></span>
      </div>
      <span class="grow"></span>
      <div class="acts">
        <button class="primary sm" id="fire-all">Run kill chain</button>
        <button class="sm" id="reset">Reset</button>
      </div>
    </div>

    <section class="view active" id="view-chain">
      <div class="vhead"><h2>Attack chain</h2>
        <p>Web tier &rarr; phished laptop &rarr; database. Select a step, fire it, read the verdict. Firing s11 blinds the database EDR, so fire s12 again after to watch a detected action go dark.</p></div>
      <div class="workspace">
        <div class="list">
          <div class="listhead"><span></span><span>#</span><span>Step</span><span class="h-host">Host</span><span>Verdict</span></div>
          <div id="rows"></div>
        </div>
        <div class="inspector" id="inspector"></div>
      </div>
    </section>

    <section class="view" id="view-hypotheses">
      <div class="vhead"><h2>Hypotheses</h2>
        <p>Why visibility is not detection, measured three ways.</p></div>
      <div class="grid">
        <div class="panel col-8">
          <h3>Coverage differs by sensor<span class="tag">H1</span></h3>
          <p class="sub">Which sensor type can even record each technique. The rows disagree.</p>
          <table class="tbl" id="h1"></table>
        </div>
        <div class="panel col-4">
          <h3>App log is not detection<span class="tag">H3</span></h3>
          <p class="sub">The app logs requests, not host effects.</p>
          <div id="h3"></div>
        </div>
        <div class="panel col-5">
          <h3>Silent failure<span class="tag">H2</span></h3>
          <p class="sub">After logging is disabled on the database.</p>
          <table class="cmp" id="h2"></table>
          <p class="hint">A blinded sensor keeps reporting healthy. Only probing by result hears the silence.</p>
        </div>
        <div class="panel col-7">
          <h3>Evidence feed</h3>
          <p class="sub">Every step you have fired, newest first.</p>
          <ul class="feed" id="feed"></ul>
        </div>
      </div>
    </section>

    <section class="view" id="view-weaknesses">
      <div class="vhead"><h2>Planted weaknesses</h2>
        <p>Each tagged with its OWASP:2025 category, ATT&amp;CK technique and lecture.</p></div>
      <div class="panel">
        <table class="tbl cat" id="catalog"></table>
      </div>
    </section>
  </main>
</div>

<script>
const OUT = {
  detected:     {tag:"Detected", vt:"Alert fired",             vs:"a detection rule matched this step"},
  visible_only: {tag:"Observed", vt:"No alert \\u2014 observed only", vs:"a sensor recorded it, but no rule matched"},
  blind:        {tag:"Blind",    vt:"No alert \\u2014 blind",          vs:"no sensor recorded the host effect"},
  armed:        {tag:"Armed",    vt:"Not fired yet",            vs:"fire this step to measure it"},
};
const EFFECT = {
  process_spawn:"started a process", file_read:"read a file",
  network_connect:"opened a network connection", log_tamper:"cleared a log", app_request:"served a request",
};
const ICON = {
  detected:'<path d="M20 6 9 17l-5-5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
  visible_only:'<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M12 8v5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16.4" r="1.2" fill="currentColor"/>',
  blind:'<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M8 8l8 8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
  armed:'<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/>',
};

let STATE = null, SEL = null;

async function api(path, method){
  const r = await fetch(path, {method: method || "GET"});
  if(!r.ok) throw new Error(path + " returned " + r.status);
  return r.json();
}
function el(tag, cls, html){ const e=document.createElement(tag); if(cls)e.className=cls; if(html!==undefined)e.innerHTML=html; return e; }
function esc(s){ return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }

function renderPosture(s){
  const t=s.tally;
  document.getElementById("p-det").textContent=t.detected;
  document.getElementById("p-obs").textContent=t.visible_only;
  document.getElementById("p-bli").textContent=t.blind;
  document.getElementById("p-fp").textContent=s.false_alarms;
  document.getElementById("p-c2").textContent=s.beacons_reached_c2;
  document.getElementById("s-fleet").textContent=s.fleet.size;
  document.getElementById("s-fired").textContent=s.fired+" / "+s.total;
  document.getElementById("nc-chain").textContent=s.fired+"/"+s.total;
}

function renderList(s){
  const box=document.getElementById("rows"); box.innerHTML="";
  for(const step of s.steps){
    const row=el("button","row "+step.outcome+(step.id===SEL?" sel":""));
    row.setAttribute("aria-current", step.id===SEL ? "true":"false");
    row.innerHTML=
      '<span class="lamp"></span>'+
      '<span class="rid">'+esc(step.id)+'</span>'+
      '<span class="rname"><b>'+esc(step.name)+'</b><small>'+esc(step.tactic)+'</small></span>'+
      '<span class="rhost">'+esc(step.agent)+'</span>'+
      '<span class="otag '+step.outcome+'">'+esc(OUT[step.outcome].tag)+'</span>';
    row.onclick=()=>{ SEL=step.id; renderList(STATE); renderInspector(STATE); };
    box.appendChild(row);
  }
}

function renderInspector(s){
  const insp=document.getElementById("inspector");
  const step=s.steps.find(x=>x.id===SEL);
  if(!step){ insp.innerHTML='<p class="insp-empty">Select a step to inspect it.</p>'; return; }
  const o=OUT[step.outcome];
  let html=
    '<div class="insp-id"><span class="mono">'+esc(step.id)+'</span><span class="tactic">'+esc(step.tactic)+'</span></div>'+
    '<h3>'+esc(step.name)+'</h3>'+
    '<div class="meta"><span class="host">'+esc(step.agent)+'</span>'+
      '<span>'+esc(step.technique.split(" ")[0])+'</span>'+
      '<span>'+esc(step.owasp.split(" ")[0])+'</span>'+
      '<span>'+esc(step.course)+'</span></div>'+
    '<p class="narr">'+esc(step.narrative)+'</p>'+
    '<div class="verdict '+step.outcome+'"><svg class="ic" viewBox="0 0 24 24" fill="none">'+ICON[step.outcome]+'</svg>'+
      '<span><span class="vt">'+esc(o.vt)+'</span><span class="vs">'+esc(o.vs)+'</span></span></div>';
  if(step.fired){
    const seen=step.seen_by.length?step.seen_by.join(", "):"nothing";
    html+='<div class="telemetry">'+
      '<div class="trow"><span class="k">Host effect</span><span class="val">'+esc(EFFECT[step.effect_kind]||step.effect_kind)+'</span></div>'+
      '<div class="trow"><span class="k">Sensors on host</span><span class="val">'+esc(step.sensors_present.join(", "))+'</span></div>'+
      '<div class="trow"><span class="k">Recorded the effect</span><span class="val'+(step.seen_by.length?'':' none')+'">'+esc(seen)+'</span></div>'+
      '<div class="trow"><span class="k">Rules fired</span><span class="val'+(step.alerts.length?'':' none')+'">'+(step.alerts.length?step.alerts.length:"none")+'</span></div>'+
      '</div>';
    for(const a of step.alerts){
      html+='<p class="alertline"><span class="rid">'+esc(a.rule_id)+'</span><span class="msg">'+esc(a.message)+'</span></p>';
    }
  }
  html+='<div class="insp-act"><button class="primary" id="insp-fire">'+(step.fired?"Fire again":"Fire step")+'</button></div>';
  insp.innerHTML=html;
  document.getElementById("insp-fire").onclick=(e)=>fireStep(step.id,e.target);
}

function renderHypotheses(s){
  const m=s.capability_matrix_h1||{}; const techs=Object.keys(m);
  const sensors=techs.length?Object.keys(m[techs[0]]):[];
  document.getElementById("h1").innerHTML=
    "<thead><tr><th>Technique</th>"+sensors.map(x=>"<th>"+esc(x)+"</th>").join("")+"</tr></thead><tbody>"+
    techs.map(tech=>"<tr><td class='tech'>"+esc(tech.split(" ")[0])+"</td>"+
      sensors.map(x=>m[tech][x]?"<td class='y'>&#10003;</td>":"<td class='no'>&middot;</td>").join("")+"</tr>").join("")+"</tbody>";

  const sf=s.silent_failure_h2;
  const names=Array.from(new Set([...Object.keys(sf.status_check),...Object.keys(sf.canary_probe)])).sort();
  document.getElementById("h2").innerHTML=
    "<thead><tr><th>Sensor</th><th>Status</th><th>Canary</th></tr></thead><tbody>"+
    names.map(n=>{const c=sf.canary_probe[n]||"—";const sil=c==="SILENT";
      return "<tr><td class='sensor'>"+esc(n)+"</td><td class='status'>"+esc(sf.status_check[n]||"—")+
        "</td><td class='"+(sil?"silent":"")+"'>"+esc(c)+"</td></tr>";}).join("")+"</tbody>";

  const d=s.applog_blindness_h3;
  document.getElementById("h3").innerHTML=
    '<div class="figrow"><span>Requests the app logged</span><b>'+esc(d.requests_logged)+'</b></div>'+
    '<div class="figrow bad"><span>Host effects in the app log</span><b>'+esc(d.host_effects_in_app_log)+'</b></div>'+
    '<div class="figrow"><span>Beacons that reached C2</span><b>'+esc(s.beacons_reached_c2)+'</b></div>';

  const feed=document.getElementById("feed"); const fired=s.steps.filter(x=>x.fired);
  feed.innerHTML="";
  if(!fired.length){ feed.appendChild(el("li","", '<span class="fname" style="color:var(--faint)">Nothing fired yet.</span>')); }
  else for(const step of fired.slice().reverse()){
    feed.appendChild(el("li",null,'<span class="dot '+step.outcome+'"></span><span class="fid">'+esc(step.id)+
      '</span><span class="fname">'+esc(OUT[step.outcome].tag)+' — '+esc(step.name)+'</span>'));
  }
}

function render(s){ STATE=s; if(SEL===null&&s.steps.length)SEL=s.steps[0].id; renderPosture(s); renderList(s); renderInspector(s); renderHypotheses(s); }

async function renderCatalog(){
  try{
    const items=await api("/catalog");
    document.getElementById("nc-weak").textContent=items.length;
    document.getElementById("catalog").innerHTML=
      "<thead><tr><th>ID</th><th>Weakness</th><th>OWASP:2025</th><th>ATT&CK</th><th>Lecture</th></tr></thead><tbody>"+
      items.map(v=>"<tr><td class='id'>"+esc(v.id)+"</td><td class='w'>"+esc(v.name)+
        "<div class='csub'>"+esc(v.note)+"</div></td><td class='code'>"+esc(v.owasp_2025)+
        "</td><td class='code'>"+esc(v.attack)+"</td><td class='code'>"+esc(v.course)+"</td></tr>").join("")+"</tbody>";
  }catch(e){ document.getElementById("catalog").innerHTML="<tbody><tr><td>Catalog unavailable.</td></tr></tbody>"; }
}

async function fireStep(id, btn){ if(btn)btn.disabled=true; SEL=id; render(await api("/live/fire/"+id,"POST")); }
async function reset(){ render(await api("/live/reset","POST")); }
async function fireAll(){ const b=document.getElementById("fire-all"); b.disabled=true; render(await api("/live/fire-all","POST")); b.disabled=false; }
document.getElementById("reset").onclick=reset;
document.getElementById("fire-all").onclick=fireAll;

// view switch
const sidebar=document.getElementById("sidebar");
document.getElementById("menu").onclick=()=>sidebar.classList.toggle("open");
document.querySelectorAll("#nav button").forEach(btn=>{
  btn.onclick=()=>{
    document.querySelectorAll("#nav button").forEach(b=>b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(v=>v.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-"+btn.dataset.view).classList.add("active");
    sidebar.classList.remove("open");
  };
});

api("/live/state").then(render).catch(err=>{
  document.getElementById("rows").innerHTML='<p class="insp-empty">Could not load the campaign: '+esc(err.message)+'</p>';
});
renderCatalog();
</script>
</body>
</html>
"""

_PAGE = _PAGE.replace("__CSS__", _CSS)
