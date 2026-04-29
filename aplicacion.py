import os
import threading
from flask import Flask, jsonify, render_template_string
from queries import get_mes, get_mes_con_dias, get_acumulado, LOCALES
from datetime import date

app = Flask(__name__)

estado_tareas = {}

HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maxxage Analytics</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
:root{--bg:#0a0a0f;--sur:#111118;--bor:#1e1e2e;--bor2:#2a2a3e;--txt:#e8e8f0;--mu:#5a5a7a;--ok:#3ecfb2;--err:#ff4d6d;--warn:#f5a623;--blu:#5b8dee}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'DM Mono',monospace;min-height:100vh;padding:2rem 1rem}
.logo{font-family:'Syne',sans-serif;font-weight:800;font-size:clamp(1.8rem,5vw,3rem);letter-spacing:-.03em;text-align:center;margin-bottom:.4rem}
.logo span{color:var(--ok)}
.sub{font-size:.65rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mu);text-align:center;margin-bottom:2rem}
.card{background:var(--sur);border:1px solid var(--bor);border-radius:8px;padding:1.5rem;margin-bottom:1rem}
.section-title{font-size:.6rem;letter-spacing:.15em;text-transform:uppercase;color:var(--mu);margin-bottom:1rem}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem}
.grid-auto{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem}
select,button{font-family:'DM Mono',monospace;font-size:.75rem;background:var(--bg);color:var(--txt);border:1px solid var(--bor2);border-radius:4px;padding:.5rem .75rem;cursor:pointer;transition:all .2s}
select:hover,button:hover{border-color:var(--ok)}
button.active,button.primary{border-color:var(--ok);color:var(--ok)}
button:disabled{opacity:.4;cursor:not-allowed}
.tabs{display:flex;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap}
.tab{padding:.5rem 1.2rem;border:1px solid var(--bor2);border-radius:4px;cursor:pointer;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:var(--mu);transition:all .2s}
.tab.active{border-color:var(--ok);color:var(--ok);background:rgba(62,207,178,.07)}
.metric{background:var(--bg);border:1px solid var(--bor);border-radius:6px;padding:1rem}
.metric-label{font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mu);margin-bottom:.4rem}
.metric-val{font-size:1.4rem;font-weight:500;font-family:'Syne',sans-serif}
.metric-dif{font-size:.65rem;margin-top:.3rem}
.up{color:var(--ok)}
.dn{color:var(--err)}
.neu{color:var(--mu)}
table{width:100%;border-collapse:collapse;font-size:.7rem}
thead th{color:var(--mu);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;padding:.6rem .75rem;text-align:right;border-bottom:1px solid var(--bor)}
thead th:first-child{text-align:left}
tbody td{padding:.6rem .75rem;text-align:right;border-bottom:1px solid var(--bor)}
tbody td:first-child{text-align:left;color:var(--mu)}
tbody tr:hover{background:rgba(255,255,255,.02)}
tbody tr:last-child td{border-bottom:none;font-weight:500}
tfoot td{padding:.6rem .75rem;text-align:right;border-top:1px solid var(--bor2);color:var(--ok);font-weight:500}
tfoot td:first-child{text-align:left}
.tbl-wrap{overflow-x:auto}
.spinner{display:inline-block;width:10px;height:10px;border:2px solid var(--mu);border-top-color:var(--ok);border-radius:50%;animation:spin .8s linear infinite;margin-right:.4rem;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.progress-wrap{background:var(--bor);border-radius:4px;height:3px;margin-top:.75rem;overflow:hidden}
.progress-fill{height:100%;background:var(--ok);border-radius:4px;transition:width .4s}
.chart-wrap{position:relative;width:100%;height:200px;margin-top:1rem}
.local-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.75rem;margin-bottom:1.5rem}
.local-btn{background:var(--bg);border:1px solid var(--bor);border-radius:6px;padding:1rem;cursor:pointer;transition:all .2s;text-align:left}
.local-btn:hover{border-color:var(--ok);background:rgba(62,207,178,.04)}
.local-btn.active{border-color:var(--ok);background:rgba(62,207,178,.08)}
.local-nombre{font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;margin-bottom:.25rem;color:var(--ok)}
.local-sub{font-size:.6rem;color:var(--mu)}
.controles{display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;margin-bottom:1.5rem}
.badge{font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;padding:.25rem .6rem;border-radius:3px;background:rgba(62,207,178,.1);color:var(--ok);border:1px solid rgba(62,207,178,.2)}
.empty{text-align:center;padding:3rem;color:var(--mu);font-size:.75rem}
#vista-detalle{display:none}
</style>
</head>
<body>
<div class="logo">Maxxage <span>Analytics</span></div>
<div class="sub">Comparativa 2025 vs 2026 · Datos en tiempo real</div>

<div class="card">
  <div class="section-title">Selecciona local</div>
  <div class="local-grid" id="local-grid"></div>

  <div class="tabs" id="tabs">
    <button class="tab active" onclick="setVista('mes',this)">Por mes</button>
    <button class="tab" onclick="setVista('acum',this)">Acumulado año</button>
  </div>

  <!-- VISTA MES -->
  <div id="vista-mes">
    <div class="controles">
      <select id="sel-mes" onchange="cambiarMes()">
        <option value="1">Enero</option>
        <option value="2">Febrero</option>
        <option value="3">Marzo</option>
        <option value="4" selected>Abril</option>
      </select>
      <button id="btn-detalle" onclick="toggleDetalle()">📅 Ver detalle por días</button>
      <span class="badge" id="badge-hasta"></span>
    </div>

    <div id="loading-mes" style="display:none">
      <div style="font-size:.7rem;color:var(--mu)"><span class="spinner"></span><span id="loading-txt">Calculando...</span></div>
      <div class="progress-wrap"><div class="progress-fill" id="progress" style="width:0%"></div></div>
      <div style="font-size:.6rem;color:var(--mu);margin-top:.4rem" id="loading-eta">Esto puede tardar 2-3 minutos</div>
    </div>

    <div id="contenido-mes">
      <div class="grid-auto" id="metrics-mes" style="margin-bottom:1rem"></div>
      <div class="tbl-wrap"><table id="tbl-mes">
        <thead><tr><th>Concepto</th><th>2025</th><th>2026</th><th>Dif €</th><th>%</th></tr></thead>
        <tbody id="tbody-mes"></tbody>
      </table></div>
      <div class="chart-wrap"><canvas id="chart-mes" role="img" aria-label="Comparativa ingresos 2025 vs 2026"></canvas></div>
    </div>

    <!-- Detalle por días -->
    <div id="vista-detalle">
      <div style="margin-top:1.5rem;margin-bottom:1rem;display:flex;align-items:center;gap:.75rem">
        <span style="font-size:.7rem;color:var(--mu)">Detalle día a día</span>
        <span class="badge" id="badge-detalle"></span>
      </div>
      <div id="loading-detalle" style="display:none">
        <div style="font-size:.7rem;color:var(--mu)"><span class="spinner"></span><span id="det-txt">Calculando días...</span></div>
        <div class="progress-wrap"><div class="progress-fill" id="progress-det" style="width:0%"></div></div>
        <div style="font-size:.6rem;color:var(--mu);margin-top:.4rem">Esto puede tardar 2-3 minutos</div>
      </div>
      <div id="contenido-detalle">
        <div class="chart-wrap" style="height:220px"><canvas id="chart-diario" role="img" aria-label="Ingresos diarios 2025 vs 2026"></canvas></div>
        <div class="tbl-wrap" style="margin-top:1rem"><table>
          <thead><tr><th>Día</th><th>Ing 25</th><th>Ing 26</th><th>Dif €</th><th>%</th><th>Bar 25</th><th>Bar 26</th><th>Ent 25</th><th>Ent 26</th></tr></thead>
          <tbody id="tbody-diario"></tbody>
          <tfoot id="tfoot-diario"></tfoot>
        </table></div>
      </div>
    </div>
  </div>

  <!-- VISTA ACUMULADO -->
  <div id="vista-acum" style="display:none">
    <div id="loading-acum" style="display:none">
      <div style="font-size:.7rem;color:var(--mu)"><span class="spinner"></span>Calculando acumulado...</div>
      <div class="progress-wrap"><div class="progress-fill" id="progress-acum" style="width:0%"></div></div>
    </div>
    <div id="contenido-acum">
      <div class="grid-auto" id="metrics-acum" style="margin-bottom:1rem"></div>
      <div class="tbl-wrap"><table>
        <thead><tr><th>Concepto</th><th>2025 (ene-hoy)</th><th>2026 (ene-hoy)</th><th>Dif €</th><th>%</th></tr></thead>
        <tbody id="tbody-acum"></tbody>
      </table></div>
      <div class="chart-wrap"><canvas id="chart-acum" role="img" aria-label="Evolución acumulada 2025 vs 2026"></canvas></div>
    </div>
  </div>
</div>

<script>
const LOCALES = {{ locales_json|safe }};
const CONCEPTOS = [
  {k:'pen',l:'Pensiones'},{k:'alq',l:'Alquileres'},{k:'bar',l:'Barras'},
  {k:'ent',l:'Entradas'},{k:'coc',l:'Cocktails',resta:true},{k:'ing',l:'Ingresos',bold:true}
];
const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

let localActual = null, vistaActual = 'mes', detalleVisible = false;
let chartMes=null, chartDiario=null, chartAcum=null;
let cacheData = {};

const fmt = v => Math.round(v).toLocaleString('es-ES') + '€';
const pct = (a,b) => a===0 ? 0 : ((b-a)/a*100);

// Inicializar locales
function initLocales() {
  const grid = document.getElementById('local-grid');
  grid.innerHTML = '';
  for (const [key, cfg] of Object.entries(LOCALES)) {
    const d = document.createElement('div');
    d.className = 'local-btn';
    d.id = 'local-' + key;
    d.innerHTML = `<div class="local-nombre">${cfg.nombre}</div><div class="local-sub">Click para ver</div>`;
    d.onclick = () => selectLocal(key);
    grid.appendChild(d);
  }
}

function selectLocal(key) {
  document.querySelectorAll('.local-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('local-' + key).classList.add('active');
  localActual = key;
  cacheData = {};
  if (vistaActual === 'mes') cargarMes();
  else cargarAcum();
}

function setVista(v, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  vistaActual = v;
  document.getElementById('vista-mes').style.display = v==='mes' ? 'block' : 'none';
  document.getElementById('vista-acum').style.display = v==='acum' ? 'block' : 'none';
  if (!localActual) return;
  if (v === 'acum') cargarAcum();
  else cargarMes();
}

function cambiarMes() {
  cacheData = {};
  detalleVisible = false;
  document.getElementById('vista-detalle').style.display = 'none';
  document.getElementById('btn-detalle').textContent = '📅 Ver detalle por días';
  if (localActual) cargarMes();
}

function cargarMes() {
  const mes = parseInt(document.getElementById('sel-mes').value);
  const cKey = `mes_${mes}`;
  if (cacheData[cKey]) { renderMes(cacheData[cKey]); return; }

  document.getElementById('loading-mes').style.display = 'block';
  document.getElementById('contenido-mes').style.opacity = '0.3';
  let prog = 0;
  const msgs = ['Consultando lotes...','Calculando pensiones...','Calculando barras...','Calculando entradas...','Finalizando...'];
  let idx = 0;
  const iv = setInterval(() => {
    prog = Math.min(prog + Math.random()*15, 90);
    document.getElementById('progress').style.width = prog + '%';
    if (idx < msgs.length) document.getElementById('loading-txt').textContent = msgs[idx++];
    const s = Math.round((100-prog)*1.2);
    document.getElementById('loading-eta').textContent = `Tiempo estimado: ~${s} segundos`;
  }, 500);

  fetch(`/api/mes/${localActual}/${mes}`)
    .then(r => r.json())
    .then(data => {
      clearInterval(iv);
      document.getElementById('progress').style.width = '100%';
      setTimeout(() => {
        document.getElementById('loading-mes').style.display = 'none';
        document.getElementById('contenido-mes').style.opacity = '1';
        cacheData[cKey] = data;
        renderMes(data);
      }, 300);
    })
    .catch(e => {
      clearInterval(iv);
      document.getElementById('loading-mes').style.display = 'none';
      document.getElementById('contenido-mes').style.opacity = '1';
      alert('Error: ' + e);
    });
}

function renderMes(data) {
  const mes = parseInt(document.getElementById('sel-mes').value);
  const {y2025:t25, y2026:t26, hasta_dia} = data;
  const nomMes = MESES[mes-1];
  document.getElementById('badge-hasta').textContent = `${nomMes} hasta día ${hasta_dia}`;

  const dif = t26.ing - t25.ing, p = pct(t25.ing, t26.ing);
  document.getElementById('metrics-mes').innerHTML = `
    <div class="metric"><div class="metric-label">Ingresos 2025</div><div class="metric-val">${fmt(t25.ing)}</div></div>
    <div class="metric"><div class="metric-label">Ingresos 2026</div><div class="metric-val">${fmt(t26.ing)}</div></div>
    <div class="metric"><div class="metric-label">Diferencia</div><div class="metric-val ${dif>=0?'up':'dn'}">${dif>=0?'+':''}${fmt(dif)}</div><div class="metric-dif ${dif>=0?'up':'dn'}">${dif>=0?'▲':'▼'} ${Math.abs(p).toFixed(1)}%</div></div>
    <div class="metric"><div class="metric-label">Cocktails 2026</div><div class="metric-val dn">-${fmt(t26.coc)}</div></div>
  `;

  document.getElementById('tbody-mes').innerHTML = CONCEPTOS.map(c => {
    const v25 = c.resta ? -t25[c.k] : t25[c.k];
    const v26 = c.resta ? -t26[c.k] : t26[c.k];
    const df = v26-v25, pp = pct(Math.abs(v25), Math.abs(v26));
    const cls = df>=0?'up':'dn';
    return `<tr style="${c.bold?'border-top:1px solid var(--bor2)':''}">
      <td>${c.l}</td><td>${fmt(Math.abs(v25))}</td><td>${fmt(Math.abs(v26))}</td>
      <td class="${cls}">${df>=0?'+':''}${fmt(df)}</td>
      <td class="${cls}">${df>=0?'▲':'▼'}${Math.abs(pp).toFixed(1)}%</td>
    </tr>`;
  }).join('');

  // Chart barras por mes
  const ing25all = data.todos_meses ? data.todos_meses.map(m=>m.y2025.ing) : [1,2,3,4].map(m=>0);
  if (chartMes) chartMes.destroy();
  chartMes = new Chart(document.getElementById('chart-mes'), {
    type:'bar',
    data:{
      labels: MESES.slice(0,4),
      datasets:[
        {label:'2025',data:[t25.ing,0,0,0],backgroundColor:'rgba(91,141,238,0.6)',borderRadius:3},
        {label:'2026',data:[t26.ing,0,0,0],backgroundColor:'rgba(62,207,178,0.7)',borderRadius:3},
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{ticks:{color:'#5a5a7a',font:{size:10}},grid:{color:'rgba(255,255,255,.04)'}},
              y:{ticks:{color:'#5a5a7a',font:{size:10},callback:v=>(v/1000).toFixed(0)+'k€'},grid:{color:'rgba(255,255,255,.04)'}}}}
  });
}

function toggleDetalle() {
  if (!localActual) return;
  if (detalleVisible) {
    document.getElementById('vista-detalle').style.display = 'none';
    document.getElementById('btn-detalle').textContent = '📅 Ver detalle por días';
    detalleVisible = false;
    return;
  }
  const mes = parseInt(document.getElementById('sel-mes').value);
  const cKey = `det_${mes}`;
  document.getElementById('vista-detalle').style.display = 'block';
  document.getElementById('btn-detalle').textContent = '📅 Ocultar detalle';
  detalleVisible = true;

  if (cacheData[cKey]) { renderDetalle(cacheData[cKey]); return; }

  document.getElementById('loading-detalle').style.display = 'block';
  document.getElementById('contenido-detalle').style.opacity = '0.2';
  let prog = 0;
  const iv = setInterval(() => {
    prog = Math.min(prog + Math.random()*12, 90);
    document.getElementById('progress-det').style.width = prog + '%';
    const s = Math.round((100-prog)*1.5);
    document.getElementById('det-txt').textContent = `Calculando días... ~${s}s restantes`;
  }, 600);

  fetch(`/api/mes_dias/${localActual}/${mes}`)
    .then(r => r.json())
    .then(data => {
      clearInterval(iv);
      document.getElementById('progress-det').style.width = '100%';
      setTimeout(() => {
        document.getElementById('loading-detalle').style.display = 'none';
        document.getElementById('contenido-detalle').style.opacity = '1';
        cacheData[cKey] = data;
        renderDetalle(data);
      }, 300);
    });
}

function renderDetalle(data) {
  const mes = parseInt(document.getElementById('sel-mes').value);
  const {dias2025:d25, dias2026:d26} = data;
  document.getElementById('badge-detalle').textContent = `${d26.length} días disponibles`;

  if (chartDiario) chartDiario.destroy();
  chartDiario = new Chart(document.getElementById('chart-diario'), {
    type:'bar',
    data:{
      labels: d26.map(r=>r.fecha),
      datasets:[
        {label:'2025',data:d25.map(r=>r.ing),backgroundColor:'rgba(91,141,238,0.5)',borderRadius:2},
        {label:'2026',data:d26.map(r=>r.ing),backgroundColor:'rgba(62,207,178,0.7)',borderRadius:2},
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{ticks:{color:'#5a5a7a',font:{size:9},maxRotation:0,autoSkip:true,maxTicksLimit:15},grid:{display:false}},
              y:{ticks:{color:'#5a5a7a',font:{size:9},callback:v=>(v/1000).toFixed(0)+'k€'},grid:{color:'rgba(255,255,255,.04)'}}}}
  });

  let tot25={ing:0,bar:0,ent:0}, tot26={ing:0,bar:0,ent:0};
  const rows = d26.map((r,i) => {
    const r25 = d25[i] || {ing:0,bar:0,ent:0};
    const df = r.ing-r25.ing, pp = pct(r25.ing, r.ing);
    const cls = df>=0?'up':'dn';
    tot25.ing+=r25.ing; tot25.bar+=r25.bar; tot25.ent+=r25.ent;
    tot26.ing+=r.ing; tot26.bar+=r.bar; tot26.ent+=r.ent;
    return `<tr>
      <td>${r.fecha}</td>
      <td>${fmt(r25.ing)}</td><td>${fmt(r.ing)}</td>
      <td class="${cls}">${df>=0?'+':''}${fmt(df)}</td>
      <td class="${cls}">${df>=0?'▲':'▼'}${Math.abs(pp).toFixed(1)}%</td>
      <td>${fmt(r25.bar)}</td><td>${fmt(r.bar)}</td>
      <td>${fmt(r25.ent)}</td><td>${fmt(r.ent)}</td>
    </tr>`;
  });
  document.getElementById('tbody-diario').innerHTML = rows.join('');
  const df_tot = tot26.ing-tot25.ing, pp_tot = pct(tot25.ing, tot26.ing);
  document.getElementById('tfoot-diario').innerHTML = `<tr>
    <td>Total</td>
    <td>${fmt(tot25.ing)}</td><td>${fmt(tot26.ing)}</td>
    <td class="${df_tot>=0?'up':'dn'}">${df_tot>=0?'+':''}${fmt(df_tot)}</td>
    <td class="${df_tot>=0?'up':'dn'}">${df_tot>=0?'▲':'▼'}${Math.abs(pp_tot).toFixed(1)}%</td>
    <td>${fmt(tot25.bar)}</td><td>${fmt(tot26.bar)}</td>
    <td>${fmt(tot25.ent)}</td><td>${fmt(tot26.ent)}</td>
  </tr>`;
}

function cargarAcum() {
  if (cacheData['acum']) { renderAcum(cacheData['acum']); return; }
  document.getElementById('loading-acum').style.display = 'block';
  document.getElementById('contenido-acum').style.opacity = '0.3';
  let prog = 0;
  const iv = setInterval(() => {
    prog = Math.min(prog + Math.random()*10, 90);
    document.getElementById('progress-acum').style.width = prog + '%';
  }, 600);

  fetch(`/api/acumulado/${localActual}`)
    .then(r => r.json())
    .then(data => {
      clearInterval(iv);
      setTimeout(() => {
        document.getElementById('loading-acum').style.display = 'none';
        document.getElementById('contenido-acum').style.opacity = '1';
        cacheData['acum'] = data;
        renderAcum(data);
      }, 300);
    });
}

function renderAcum(data) {
  const {y2025:t25, y2026:t26, meses2025, meses2026} = data;
  const dif = t26.ing-t25.ing, p = pct(t25.ing, t26.ing);
  document.getElementById('metrics-acum').innerHTML = `
    <div class="metric"><div class="metric-label">Acum 2025</div><div class="metric-val">${fmt(t25.ing)}</div></div>
    <div class="metric"><div class="metric-label">Acum 2026</div><div class="metric-val">${fmt(t26.ing)}</div></div>
    <div class="metric"><div class="metric-label">Diferencia</div><div class="metric-val up">+${fmt(dif)}</div><div class="metric-dif up">▲ ${p.toFixed(1)}%</div></div>
    <div class="metric"><div class="metric-label">Crecimiento</div><div class="metric-val up">+${p.toFixed(1)}%</div></div>
  `;

  document.getElementById('tbody-acum').innerHTML = CONCEPTOS.map(c => {
    const v25=c.resta?-t25[c.k]:t25[c.k], v26=c.resta?-t26[c.k]:t26[c.k];
    const df=v26-v25, pp=pct(Math.abs(v25),Math.abs(v26));
    const cls=df>=0?'up':'dn';
    return `<tr style="${c.bold?'border-top:1px solid var(--bor2)':''}">
      <td>${c.l}</td><td>${fmt(Math.abs(v25))}</td><td>${fmt(Math.abs(v26))}</td>
      <td class="${cls}">${df>=0?'+':''}${fmt(df)}</td>
      <td class="${cls}">${df>=0?'▲':'▼'}${Math.abs(pp).toFixed(1)}%</td>
    </tr>`;
  }).join('');

  // Acumulado mes a mes
  const labels = MESES.slice(0, meses2026.length);
  let s25=0, s26=0;
  const acum25=meses2025.map(v=>{s25+=v;return s25});
  const acum26=meses2026.map(v=>{s26+=v;return s26});
  if (chartAcum) chartAcum.destroy();
  chartAcum = new Chart(document.getElementById('chart-acum'), {
    type:'line',
    data:{labels,datasets:[
      {label:'2025',data:acum25,borderColor:'#5b8dee',backgroundColor:'rgba(91,141,238,0.07)',fill:true,tension:0.3,pointRadius:4,pointBackgroundColor:'#5b8dee'},
      {label:'2026',data:acum26,borderColor:'#3ecfb2',backgroundColor:'rgba(62,207,178,0.07)',fill:true,tension:0.3,pointRadius:4,pointBackgroundColor:'#3ecfb2'},
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:{ticks:{color:'#5a5a7a',font:{size:10}},grid:{color:'rgba(255,255,255,.04)'}},
              y:{ticks:{color:'#5a5a7a',font:{size:10},callback:v=>(v/1000).toFixed(0)+'k€'},grid:{color:'rgba(255,255,255,.04)'}}}}
  });
}

initLocales();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    import json
    locales_json = json.dumps({k: {"nombre": v["nombre"]} for k,v in LOCALES.items()})
    return render_template_string(HTML, locales_json=locales_json)

@app.route("/api/mes/<local_key>/<int:mes>")
def api_mes(local_key, mes):
    if local_key not in LOCALES:
        return jsonify({"error": "Local no encontrado"}), 404
    try:
        data = get_mes(local_key, mes)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mes_dias/<local_key>/<int:mes>")
def api_mes_dias(local_key, mes):
    if local_key not in LOCALES:
        return jsonify({"error": "Local no encontrado"}), 404
    try:
        data = get_mes_con_dias(local_key, mes)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/acumulado/<local_key>")
def api_acumulado(local_key):
    if local_key not in LOCALES:
        return jsonify({"error": "Local no encontrado"}), 404
    try:
        data = get_acumulado(local_key)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
