"""The interactive console: the fleet, its state, and the attacks against it.

The static dashboard in `report.py` shows a finished run; this one is the
operator's surface. Its home is the fleet: every simulated VM as a tile, grouped
by the trust boundary it sits behind, each one expandable to what the sensors on
it saw. The kill chain lights a path through the fleet, and the state that the
whole project is about — a host breached with no alarm — is the one the view is
built to make unmissable.

Look is a calm holographic operations surface: a deep field, thin cyan structure
that frames what is live, and motion that only answers an action (a tile opening)
or marks danger (a silent breach breathing). Severity stays load-bearing:
detection working is green, observed-with-no-rule amber, a silent breach red.

One self-contained HTML string talks to the control plane's `/live/*` and
`/catalog` JSON; no framework, because the point is the data, not the bundler.
"""

from __future__ import annotations


def render_console() -> str:
    return _PAGE


_CSS = """
:root{
  --bg:#070b11; --surface:#0c131b; --surface-2:#111a24; --raised:#16212d;
  --border:#1a2531; --border-2:#273644; --line:#121b24;
  --text:#dce7f1; --muted:#8193a4; --faint:#566978;
  --cyan:#22d3ee; --cyan-2:#67e8f9; --cyan-bg:rgba(34,211,238,.1); --cyan-ln:rgba(34,211,238,.4);
  --green:#34d399; --green-bg:rgba(52,211,153,.12); --green-ln:rgba(52,211,153,.42);
  --amber:#fbbf24; --amber-bg:rgba(251,191,36,.12); --amber-ln:rgba(251,191,36,.4);
  --red:#f87171; --red-bg:rgba(248,113,113,.13); --red-ln:rgba(248,113,113,.45);
  --r:7px; --r2:10px;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#eef2f6; --surface:#ffffff; --surface-2:#f2f5f8; --raised:#ffffff;
    --border:#dde3ea; --border-2:#c7d0d9; --line:#eaeef2;
    --text:#0f1b26; --muted:#4d5b6a; --faint:#8495a4;
    --cyan:#0891b2; --cyan-2:#0e7490; --cyan-bg:rgba(8,145,178,.1); --cyan-ln:rgba(8,145,178,.34);
    --green:#059669; --green-bg:rgba(5,150,105,.1); --green-ln:rgba(5,150,105,.3);
    --amber:#b45309; --amber-bg:rgba(180,83,9,.1); --amber-ln:rgba(180,83,9,.3);
    --red:#dc2626; --red-bg:rgba(220,38,38,.1); --red-ln:rgba(220,38,38,.3);
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased;
  background-image:
    radial-gradient(760px 420px at 14% -8%, rgba(34,211,238,.06), transparent 60%),
    linear-gradient(var(--line) 1px, transparent 1px),
    linear-gradient(90deg, var(--line) 1px, transparent 1px);
  background-size:auto, 44px 44px, 44px 44px;
  background-position:0 0, -1px -1px, -1px -1px;
  background-attachment:fixed;}
.mono{font-family:var(--mono)}
button{font:inherit;cursor:pointer;border-radius:var(--r);border:1px solid var(--border-2);
  background:var(--surface-2);color:var(--text);padding:7px 12px;font-weight:500;
  transition:border-color .14s,background .14s,color .14s}
button:hover{border-color:var(--cyan-ln)}
button:disabled{opacity:.5;cursor:default}
button.primary{background:var(--cyan);border-color:var(--cyan);color:#04212a;font-weight:600}
button.primary:hover{background:var(--cyan-2);border-color:var(--cyan-2)}
button.sm{padding:5px 10px;font-size:.85rem}
:focus-visible{outline:2px solid var(--cyan);outline-offset:1px;border-radius:var(--r)}

.app{display:grid;grid-template-columns:230px minmax(0,1fr);min-height:100vh}

/* sidebar */
.sidebar{position:sticky;top:0;height:100vh;display:flex;flex-direction:column;
  background:color-mix(in srgb,var(--surface) 82%,transparent);border-right:1px solid var(--border);
  padding:16px 12px;backdrop-filter:blur(6px)}
.brand{display:flex;align-items:center;gap:9px;padding:4px 8px 16px;font-weight:600;font-size:.95rem}
.brand svg{width:19px;height:19px;color:var(--cyan)}
.brand .dim{color:var(--faint);font-weight:400;letter-spacing:.04em}
nav{display:flex;flex-direction:column;gap:1px}
nav button{display:flex;align-items:center;gap:10px;padding:9px 10px;border:0;background:none;
  color:var(--muted);text-align:left;border-radius:var(--r);font-size:.9rem;font-weight:500;width:100%;
  border-left:2px solid transparent}
nav button svg{width:16px;height:16px;flex:none;opacity:.8}
nav button:hover{color:var(--text);background:var(--surface-2)}
nav button.active{color:var(--text);background:var(--cyan-bg);border-left-color:var(--cyan)}
nav button.active svg{color:var(--cyan);opacity:1}
.navcount{margin-left:auto;font-family:var(--mono);font-size:.74rem;color:var(--faint)}
.side-sp{flex:1}
.fleetbox{border-top:1px solid var(--border);padding:14px 8px 8px;margin-top:10px}
.fleetbox .r{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);margin-bottom:8px}
.fleetbox .r b{font-family:var(--mono);color:var(--text);font-weight:500}
.sidelinks{display:flex;gap:14px;padding:12px 8px 2px;font-size:.78rem}
.sidelinks a{color:var(--faint);text-decoration:none}
.sidelinks a:hover{color:var(--cyan-2)}

/* main */
main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:18px;
  padding:12px 20px;background:color-mix(in srgb,var(--surface) 86%,transparent);
  border-bottom:1px solid var(--border);flex-wrap:wrap;backdrop-filter:blur(8px)}
.posture{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.pstat{display:flex;align-items:baseline;gap:7px}
.pstat i{width:8px;height:8px;border-radius:2px;align-self:center}
.pstat .v{font-family:var(--mono);font-size:1.05rem;font-weight:600}
.pstat .k{font-size:.82rem;color:var(--muted)}
.pstat.det i{background:var(--green)} .pstat.det .v{color:var(--green)}
.pstat.obs i{background:var(--amber)} .pstat.obs .v{color:var(--amber)}
.pstat.bli i{background:var(--red)} .pstat.bli .v{color:var(--red)}
.pstat.c2 .v{color:var(--red)}
.pdiv{width:1px;height:26px;background:var(--border-2)}
.topbar .grow{flex:1}
.topbar .acts{display:flex;gap:8px}
.menu-btn{display:none}

.view{display:none;padding:18px 20px 64px;animation:fade .25s ease}
.view.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.vhead{margin:0 0 16px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
.vhead h2{font-size:1.1rem;font-weight:600;margin:0}
.vhead p{margin:3px 0 0;color:var(--muted);font-size:.86rem;max-width:66ch}
.vsum{display:flex;gap:16px;font-size:.82rem;color:var(--muted);white-space:nowrap}
.vsum b{font-family:var(--mono);color:var(--text);font-weight:600}
.vsum .sil{color:var(--red)} .vsum .alr{color:var(--green)}

/* fleet view */
.band{position:relative;margin:0 0 20px;padding-left:18px}
.band::before{content:"";position:absolute;left:0;top:6px;bottom:14px;width:2px;border-radius:2px;
  background:var(--border-2)}
.band.hot::before{background:linear-gradient(var(--cyan),transparent)}
.bandhead{display:flex;align-items:baseline;gap:10px;margin:0 0 11px}
.bandhead .sn{font-family:var(--mono);font-size:.82rem;color:var(--cyan-2);font-weight:600}
.bandhead .role{color:var(--muted);font-size:.84rem}
.bandhead .tally{margin-left:auto;font-size:.78rem;color:var(--faint);font-family:var(--mono)}
.vmgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(216px,1fr));gap:10px}
.vm{border:1px solid var(--border);border-radius:var(--r2);background:var(--surface);overflow:hidden;
  transition:border-color .18s,box-shadow .18s,transform .12s;position:relative}
.vm:hover{transform:translateY(-1px)}
.vm.on-path{border-color:var(--border-2)}
.vm.alerting{border-color:var(--green-ln)}
.vm.observed{border-color:var(--amber-ln)}
.vm.silent{border-color:var(--red-ln)}
.vm.silent{animation:breathe 2.6s ease-in-out infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 0 0 rgba(248,113,113,0)}50%{box-shadow:0 0 0 3px var(--red-bg)}}
.vm.open{border-color:var(--cyan-ln)}
/* holographic corner brackets on live hosts */
.vm.on-path::before,.vm.on-path::after{content:"";position:absolute;width:9px;height:9px;z-index:2;pointer-events:none}
.vm.on-path::before{top:6px;left:6px;border-top:1.5px solid var(--cyan);border-left:1.5px solid var(--cyan)}
.vm.on-path::after{bottom:6px;right:6px;border-bottom:1.5px solid var(--cyan);border-right:1.5px solid var(--cyan)}
.vm.silent::before,.vm.silent::after{border-color:var(--red)}
.vm.alerting::before,.vm.alerting::after{border-color:var(--green)}
.vm-head{display:flex;align-items:center;gap:10px;width:100%;border:0;background:none;color:var(--text);
  text-align:left;padding:12px 13px;border-radius:0}
.vm-dot{width:9px;height:9px;border-radius:50%;flex:none;background:var(--faint)}
.vm.alerting .vm-dot{background:var(--green)} .vm.observed .vm-dot{background:var(--amber)}
.vm.silent .vm-dot{background:var(--red)} .vm.targeted .vm-dot{background:var(--cyan)}
.vm-id{min-width:0;flex:1}
.vm-id b{font-family:var(--mono);font-weight:600;font-size:.86rem;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.vm-id small{color:var(--faint);font-size:.74rem}
.vm-state{font-size:.7rem;font-weight:600;letter-spacing:.02em;color:var(--faint)}
.vm.alerting .vm-state{color:var(--green)} .vm.observed .vm-state{color:var(--amber)}
.vm.silent .vm-state{color:var(--red)} .vm.targeted .vm-state{color:var(--cyan-2)}
.vm-chev{width:14px;height:14px;color:var(--faint);transition:transform .25s;flex:none}
.vm.open .vm-chev{transform:rotate(90deg)}
.vm-body{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s ease}
.vm.open .vm-body{grid-template-rows:1fr}
.vm-body > div{overflow:hidden;min-height:0}
.vm-inner{padding:0 13px 13px;border-top:1px solid var(--line)}
.vm-meta{display:flex;flex-wrap:wrap;gap:6px;margin:11px 0 0}
.vm-meta span{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--surface-2);
  border:1px solid var(--border);border-radius:5px;padding:2px 7px}
.vm-counts{display:flex;gap:18px;margin:11px 0 0;font-size:.8rem;color:var(--muted)}
.vm-counts b{font-family:var(--mono);color:var(--text)}
.vm-steps{margin:11px 0 0;display:flex;flex-direction:column;gap:6px}
.vm-step{display:flex;align-items:center;gap:9px;font-size:.82rem}
.vm-step .sid{font-family:var(--mono);color:var(--faint);font-size:.76rem}
.vm-step .sn{flex:1;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.vm-quiet{margin:11px 0 0;font-size:.82rem;color:var(--faint)}

/* shared status tag */
.otag{font-size:.72rem;font-weight:600;padding:2px 8px;border-radius:5px;text-align:center;
  border:1px solid transparent;white-space:nowrap}
.otag.detected{color:var(--green);background:var(--green-bg);border-color:var(--green-ln)}
.otag.visible_only{color:var(--amber);background:var(--amber-bg);border-color:var(--amber-ln)}
.otag.blind{color:var(--red);background:var(--red-bg);border-color:var(--red-ln)}
.otag.armed{color:var(--faint);background:var(--surface-2);border-color:var(--border-2)}

/* attack chain master-detail */
.workspace{display:grid;grid-template-columns:minmax(0,1fr) 384px;gap:16px;align-items:start}
@media(max-width:1060px){.workspace{grid-template-columns:1fr}}
.list{border:1px solid var(--border);border-radius:var(--r2);overflow:hidden;background:var(--surface)}
.listhead{display:grid;grid-template-columns:14px 30px 1fr 96px 80px;gap:12px;padding:9px 14px;
  border-bottom:1px solid var(--border);font-size:.72rem;color:var(--faint);background:var(--surface-2)}
.row{display:grid;grid-template-columns:14px 30px 1fr 96px 80px;gap:12px;align-items:center;width:100%;
  padding:11px 14px;border:0;border-bottom:1px solid var(--line);background:none;color:var(--text);
  text-align:left;border-left:2px solid transparent;border-radius:0}
.row:last-child{border-bottom:0}
.row:hover{background:var(--surface-2)}
.row.sel{background:var(--cyan-bg);border-left-color:var(--cyan)}
.row .lamp{width:9px;height:9px;border-radius:50%;background:var(--faint);justify-self:center}
.row.detected .lamp{background:var(--green)} .row.visible_only .lamp{background:var(--amber)}
.row.blind .lamp{background:var(--red)}
.row .rid{font-family:var(--mono);font-size:.8rem;color:var(--faint)}
.row .rname{min-width:0}
.row .rname b{font-weight:500;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .rname small{color:var(--faint);font-size:.74rem}
.row .rhost{font-family:var(--mono);font-size:.78rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:620px){
  .listhead,.row{grid-template-columns:14px 28px 1fr 74px}
  .listhead .h-host,.row .rhost{display:none}
}
.inspector{position:sticky;top:76px;border:1px solid var(--border);border-radius:var(--r2);
  background:var(--surface);padding:16px}
.insp-id{display:flex;align-items:center;gap:9px;font-size:.78rem;color:var(--faint)}
.insp-id .tactic{color:var(--cyan-2);font-weight:600}
.inspector h3{font-size:1.02rem;font-weight:600;margin:7px 0 0}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}
.meta span{font-family:var(--mono);font-size:.74rem;color:var(--muted);background:var(--surface-2);
  border:1px solid var(--border);border-radius:5px;padding:2px 7px}
.meta span.host{color:var(--cyan-2);border-color:var(--cyan-ln)}
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
.telemetry{margin:14px 0 0}
.trow{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);font-size:.85rem}
.trow:last-child{border-bottom:0}
.trow .k{color:var(--muted)} .trow .val{font-family:var(--mono);text-align:right;color:var(--text)}
.trow .val.none{color:var(--red)}
.alertline{font-size:.82rem;margin-top:9px;display:flex;gap:8px;align-items:baseline}
.alertline .rid{font-family:var(--mono);font-weight:600;color:var(--green)}
.alertline .msg{color:var(--muted)}
.insp-act{margin-top:16px}
.insp-act button{width:100%}
.insp-empty{color:var(--faint);font-size:.86rem;padding:30px 4px;text-align:center}

/* panels */
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.col-4{grid-column:span 4} .col-5{grid-column:span 5} .col-7{grid-column:span 7} .col-8{grid-column:span 8}
@media(max-width:1040px){.col-4,.col-5,.col-7,.col-8{grid-column:span 12}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r2);padding:16px}
.panel h3{font-size:.92rem;font-weight:600;margin:0 0 3px;display:flex;justify-content:space-between;align-items:baseline}
.panel h3 .tag{font-family:var(--mono);font-size:.72rem;color:var(--cyan-2);font-weight:500}
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
.cat td.id{font-family:var(--mono);color:var(--cyan-2)}
.cat td.code{font-family:var(--mono);color:var(--muted);white-space:nowrap;font-size:.8rem}
.cat td.w{color:var(--text)} .cat td{text-align:left!important}
.cat .csub{color:var(--faint);font-size:.8rem;margin-top:2px}

@media(max-width:860px){
  .app{grid-template-columns:1fr}
  .sidebar{position:fixed;inset:0 auto 0 0;width:234px;z-index:60;transform:translateX(-100%);transition:transform .2s}
  .sidebar.open{transform:translateX(0);box-shadow:0 0 0 100vmax rgba(0,0,0,.55)}
  .menu-btn{display:inline-flex}
}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDA — Fleet Console</title>
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
      <button data-view="fleet" class="active">
        <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="6" rx="1.5" stroke="currentColor" stroke-width="1.6"/><rect x="3" y="14" width="18" height="6" rx="1.5" stroke="currentColor" stroke-width="1.6"/><circle cx="7" cy="7" r="1" fill="currentColor"/><circle cx="7" cy="17" r="1" fill="currentColor"/></svg>
        Fleet<span class="navcount" id="nc-fleet"></span></button>
      <button data-view="chain">
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

    <section class="view active" id="view-fleet">
      <div class="vhead">
        <div><h2>Fleet</h2>
          <p>Fifty simulated hosts, grouped by the trust boundary they sit behind. The kill chain lights a path from the edge inward; a host breached with no alarm breathes red.</p></div>
        <div class="vsum" id="fleet-sum"></div>
      </div>
      <div id="bands"></div>
    </section>

    <section class="view" id="view-chain">
      <div class="vhead"><div><h2>Attack chain</h2>
        <p>Web tier &rarr; phished laptop &rarr; database. Select a step, fire it, read the verdict. Firing s11 blinds the database EDR, so fire s12 again after to watch a detected action go dark.</p></div></div>
      <div class="workspace">
        <div class="list">
          <div class="listhead"><span></span><span>#</span><span>Step</span><span class="h-host">Host</span><span>Verdict</span></div>
          <div id="rows"></div>
        </div>
        <div class="inspector" id="inspector"></div>
      </div>
    </section>

    <section class="view" id="view-hypotheses">
      <div class="vhead"><div><h2>Hypotheses</h2>
        <p>Why visibility is not detection, measured three ways.</p></div></div>
      <div class="grid">
        <div class="panel col-8"><h3>Coverage differs by sensor<span class="tag">H1</span></h3>
          <p class="sub">Which sensor type can even record each technique. The rows disagree.</p>
          <table class="tbl" id="h1"></table></div>
        <div class="panel col-4"><h3>App log is not detection<span class="tag">H3</span></h3>
          <p class="sub">The app logs requests, not host effects.</p><div id="h3"></div></div>
        <div class="panel col-5"><h3>Silent failure<span class="tag">H2</span></h3>
          <p class="sub">After logging is disabled on the database.</p>
          <table class="cmp" id="h2"></table>
          <p class="hint">A blinded sensor keeps reporting healthy. Only probing by result hears the silence.</p></div>
        <div class="panel col-7"><h3>Evidence feed</h3>
          <p class="sub">Every step you have fired, newest first.</p>
          <ul class="feed" id="feed"></ul></div>
      </div>
    </section>

    <section class="view" id="view-weaknesses">
      <div class="vhead"><div><h2>Planted weaknesses</h2>
        <p>Each tagged with its OWASP:2025 category, ATT&amp;CK technique and lecture.</p></div></div>
      <div class="panel"><table class="tbl cat" id="catalog"></table></div>
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
const STATUS = {
  nominal:  "Nominal",   targeted: "Targeted",
  observed: "Observed",  alerting: "Alerting",  silent: "Silent",
};
const SUBNET = {
  dmz:["dmz","internet edge"], corp:["corp","workstations"],
  "app-tier":["app-tier","application tier"], "data-tier":["data-tier","data tier"],
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

let STATE=null, SEL=null;
const FLEET_OPEN=new Set();

async function api(path, method){
  const r = await fetch(path, {method: method || "GET"});
  if(!r.ok) throw new Error(path + " returned " + r.status);
  return r.json();
}
function el(tag, cls, html){ const e=document.createElement(tag); if(cls)e.className=cls; if(html!==undefined)e.innerHTML=html; return e; }
function esc(s){ return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }

function renderPosture(s){
  const t=s.tally;
  p("p-det",t.detected); p("p-obs",t.visible_only); p("p-bli",t.blind);
  p("p-fp",s.false_alarms); p("p-c2",s.beacons_reached_c2);
  document.getElementById("s-fleet").textContent=s.fleet.size;
  document.getElementById("s-fired").textContent=s.fired+" / "+s.total;
  document.getElementById("nc-chain").textContent=s.fired+"/"+s.total;
  document.getElementById("nc-fleet").textContent=s.fleet.size;
}
function p(id,v){ document.getElementById(id).textContent=v; }

function vmTile(a){
  const open = FLEET_OPEN.has(a.id);
  const tile = el("div","vm "+a.status+(a.on_path?" on-path":"")+(open?" open":""));
  const head = el("button","vm-head");
  head.setAttribute("aria-expanded", open?"true":"false");
  const stateLabel = a.status === "nominal" ? "" : '<span class="vm-state">'+esc(STATUS[a.status])+'</span>';
  head.innerHTML =
    '<span class="vm-dot"></span>'+
    '<span class="vm-id"><b>'+esc(a.id)+'</b><small>'+esc(a.role)+' &middot; '+esc(a.workload)+'</small></span>'+
    stateLabel+
    '<svg class="vm-chev" viewBox="0 0 24 24" fill="none"><path d="m9 6 6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  head.onclick=()=>{ if(FLEET_OPEN.has(a.id))FLEET_OPEN.delete(a.id); else FLEET_OPEN.add(a.id); renderFleet(STATE); };
  tile.appendChild(head);

  let inner='<div class="vm-meta"><span>'+esc(a.subnet)+'</span>'+
    a.sensors.map(x=>'<span>'+esc(x)+'</span>').join("")+'</div>'+
    '<div class="vm-counts"><span>events <b>'+a.events+'</b></span><span>alerts <b>'+a.alerts+'</b></span></div>';
  if(a.steps.length){
    inner+='<div class="vm-steps">'+a.steps.map(st=>
      '<div class="vm-step"><span class="sid">'+esc(st.id)+'</span>'+
      '<span class="sn">'+esc(st.name)+'</span>'+
      '<span class="otag '+st.outcome+'">'+esc(OUT[st.outcome].tag)+'</span></div>').join("")+'</div>';
  }else{
    inner+='<p class="vm-quiet">No attack reached this host. Only benign activity.</p>';
  }
  const body=el("div","vm-body"); body.appendChild(el("div",null,'<div class="vm-inner">'+inner+'</div>'));
  tile.appendChild(body);
  return tile;
}

function renderFleet(s){
  STATE=s;
  const counts={}; for(const a of s.agents) counts[a.status]=(counts[a.status]||0)+1;
  document.getElementById("fleet-sum").innerHTML=
    '<span><b>'+s.agents.length+'</b> hosts</span>'+
    '<span class="sil"><b>'+(counts.silent||0)+'</b> silent</span>'+
    '<span class="alr"><b>'+(counts.alerting||0)+'</b> alerting</span>'+
    '<span><b>'+(counts.nominal||0)+'</b> nominal</span>';

  const bands=document.getElementById("bands"); bands.innerHTML="";
  for(const subnet of s.subnets){
    const hosts=s.agents.filter(a=>a.subnet===subnet);
    if(!hosts.length) continue;
    const hot=hosts.some(h=>h.on_path);
    const breached=hosts.filter(h=>h.status==="silent").length;
    const band=el("div","band"+(hot?" hot":""));
    const label=SUBNET[subnet]||[subnet,""];
    band.appendChild(el("div","bandhead",
      '<span class="sn">'+esc(label[0])+'</span><span class="role">'+esc(label[1])+'</span>'+
      '<span class="tally">'+hosts.length+' hosts'+(breached?' &middot; '+breached+' breached':'')+'</span>'));
    const grid=el("div","vmgrid");
    for(const a of hosts) grid.appendChild(vmTile(a));
    band.appendChild(grid);
    bands.appendChild(band);
  }
}

function renderList(s){
  const box=document.getElementById("rows"); box.innerHTML="";
  for(const step of s.steps){
    const row=el("button","row "+step.outcome+(step.id===SEL?" sel":""));
    row.innerHTML='<span class="lamp"></span><span class="rid">'+esc(step.id)+'</span>'+
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
  let html='<div class="insp-id"><span class="mono">'+esc(step.id)+'</span><span class="tactic">'+esc(step.tactic)+'</span></div>'+
    '<h3>'+esc(step.name)+'</h3>'+
    '<div class="meta"><span class="host">'+esc(step.agent)+'</span><span>'+esc(step.technique.split(" ")[0])+
      '</span><span>'+esc(step.owasp.split(" ")[0])+'</span><span>'+esc(step.course)+'</span></div>'+
    '<p class="narr">'+esc(step.narrative)+'</p>'+
    '<div class="verdict '+step.outcome+'"><svg class="ic" viewBox="0 0 24 24" fill="none">'+ICON[step.outcome]+'</svg>'+
      '<span><span class="vt">'+esc(o.vt)+'</span><span class="vs">'+esc(o.vs)+'</span></span></div>';
  if(step.fired){
    const seen=step.seen_by.length?step.seen_by.join(", "):"nothing";
    html+='<div class="telemetry">'+
      '<div class="trow"><span class="k">Host effect</span><span class="val">'+esc(EFFECT[step.effect_kind]||step.effect_kind)+'</span></div>'+
      '<div class="trow"><span class="k">Sensors on host</span><span class="val">'+esc(step.sensors_present.join(", "))+'</span></div>'+
      '<div class="trow"><span class="k">Recorded the effect</span><span class="val'+(step.seen_by.length?'':' none')+'">'+esc(seen)+'</span></div>'+
      '<div class="trow"><span class="k">Rules fired</span><span class="val'+(step.alerts.length?'':' none')+'">'+(step.alerts.length||"none")+'</span></div></div>';
    for(const a of step.alerts) html+='<p class="alertline"><span class="rid">'+esc(a.rule_id)+'</span><span class="msg">'+esc(a.message)+'</span></p>';
  }
  html+='<div class="insp-act"><button class="primary" id="insp-fire">'+(step.fired?"Fire again":"Fire step")+'</button></div>';
  insp.innerHTML=html;
  document.getElementById("insp-fire").onclick=(e)=>fireStep(step.id,e.target);
}

function renderHypotheses(s){
  const m=s.capability_matrix_h1||{}; const techs=Object.keys(m);
  const sensors=techs.length?Object.keys(m[techs[0]]):[];
  document.getElementById("h1").innerHTML="<thead><tr><th>Technique</th>"+sensors.map(x=>"<th>"+esc(x)+"</th>").join("")+
    "</tr></thead><tbody>"+techs.map(t=>"<tr><td class='tech'>"+esc(t.split(" ")[0])+"</td>"+
    sensors.map(x=>m[t][x]?"<td class='y'>&#10003;</td>":"<td class='no'>&middot;</td>").join("")+"</tr>").join("")+"</tbody>";
  const sf=s.silent_failure_h2;
  const names=Array.from(new Set([...Object.keys(sf.status_check),...Object.keys(sf.canary_probe)])).sort();
  document.getElementById("h2").innerHTML="<thead><tr><th>Sensor</th><th>Status</th><th>Canary</th></tr></thead><tbody>"+
    names.map(n=>{const c=sf.canary_probe[n]||"—";return "<tr><td class='sensor'>"+esc(n)+"</td><td class='status'>"+
    esc(sf.status_check[n]||"—")+"</td><td class='"+(c==="SILENT"?"silent":"")+"'>"+esc(c)+"</td></tr>";}).join("")+"</tbody>";
  const d=s.applog_blindness_h3;
  document.getElementById("h3").innerHTML=
    '<div class="figrow"><span>Requests the app logged</span><b>'+esc(d.requests_logged)+'</b></div>'+
    '<div class="figrow bad"><span>Host effects in the app log</span><b>'+esc(d.host_effects_in_app_log)+'</b></div>'+
    '<div class="figrow"><span>Beacons that reached C2</span><b>'+esc(s.beacons_reached_c2)+'</b></div>';
  const feed=document.getElementById("feed"); const fired=s.steps.filter(x=>x.fired);
  feed.innerHTML="";
  if(!fired.length) feed.appendChild(el("li","",'<span class="fname" style="color:var(--faint)">Nothing fired yet.</span>'));
  else for(const step of fired.slice().reverse())
    feed.appendChild(el("li",null,'<span class="dot '+step.outcome+'"></span><span class="fid">'+esc(step.id)+
      '</span><span class="fname">'+esc(OUT[step.outcome].tag)+' — '+esc(step.name)+'</span>'));
}

function render(s){ STATE=s; if(SEL===null&&s.steps.length)SEL=s.steps[0].id;
  renderPosture(s); renderFleet(s); renderList(s); renderInspector(s); renderHypotheses(s); }

async function renderCatalog(){
  try{
    const items=await api("/catalog");
    document.getElementById("nc-weak").textContent=items.length;
    document.getElementById("catalog").innerHTML="<thead><tr><th>ID</th><th>Weakness</th><th>OWASP:2025</th><th>ATT&CK</th><th>Lecture</th></tr></thead><tbody>"+
      items.map(v=>"<tr><td class='id'>"+esc(v.id)+"</td><td class='w'>"+esc(v.name)+"<div class='csub'>"+esc(v.note)+
      "</div></td><td class='code'>"+esc(v.owasp_2025)+"</td><td class='code'>"+esc(v.attack)+"</td><td class='code'>"+esc(v.course)+"</td></tr>").join("")+"</tbody>";
  }catch(e){ document.getElementById("catalog").innerHTML="<tbody><tr><td>Catalog unavailable.</td></tr></tbody>"; }
}

async function fireStep(id, btn){ if(btn)btn.disabled=true; SEL=id; render(await api("/live/fire/"+id,"POST")); }
async function reset(){ FLEET_OPEN.clear(); render(await api("/live/reset","POST")); }
async function fireAll(){ const b=document.getElementById("fire-all"); b.disabled=true; render(await api("/live/fire-all","POST")); b.disabled=false; }
document.getElementById("reset").onclick=reset;
document.getElementById("fire-all").onclick=fireAll;

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
  document.getElementById("bands").innerHTML='<p class="insp-empty">Could not load the fleet: '+esc(err.message)+'</p>';
});
renderCatalog();
</script>
</body>
</html>
"""

_PAGE = _PAGE.replace("__CSS__", _CSS)
