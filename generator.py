from datetime import datetime
from collections import defaultdict
from scraper import get_color, calc_historical_avg, DIAS_ES

COMMON_CSS = """
:root{--bg:#0a0a0f;--sur:#111118;--bor:#1e1e2e;--txt:#e8e8f0;--mu:#5a5a7a;--ok:#3ecfb2;--err:#ff4d6d;--warn:#f5a623}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'DM Mono',monospace}
header{padding:2rem 2rem 1.5rem;border-bottom:1px solid var(--bor);display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:1rem}
.brand{font-family:'Syne',sans-serif;font-weight:800;font-size:clamp(1.5rem,4vw,2.6rem);letter-spacing:-.03em}
.badge{font-size:.62rem;letter-spacing:.15em;text-transform:uppercase;color:var(--mu);border:1px solid var(--bor);padding:.3rem .65rem}
.wrap{max-width:1150px;margin:0 auto;padding:0 1.2rem 4rem}
.tabs-nav{display:flex;gap:2px;padding:1rem 0;flex-wrap:wrap;position:sticky;top:0;background:var(--bg);z-index:10;border-bottom:1px solid var(--bor);margin-bottom:1.5rem}
.tab-btn{background:var(--sur);border:1px solid var(--bor);color:var(--mu);font-family:'DM Mono',monospace;font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;padding:.5rem 1rem;cursor:pointer;border-radius:2px;transition:all .2s}
.tab-btn:hover{color:var(--txt);border-color:var(--txt)}
.tab-panel{display:none} .tab-panel.active{display:block}
.sec{font-family:'Syne',sans-serif;font-size:.68rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--mu);margin:2rem 0 .9rem;padding-bottom:.45rem;border-bottom:1px solid var(--bor)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--bor);border:1px solid var(--bor);margin-bottom:1.5rem}
.kpi{background:var(--sur);padding:1.1rem;position:relative}
.kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.kl{font-size:.57rem;letter-spacing:.1em;text-transform:uppercase;color:var(--mu);margin-bottom:.35rem}
.kv{font-family:'DM Serif Display',serif;font-size:1.55rem;line-height:1;margin-bottom:.15rem}
.ks{font-size:.58rem;color:var(--mu)}
.prog-wrap{margin:1rem 0 1.5rem}
.prog-label{display:flex;justify-content:space-between;font-size:.6rem;color:var(--mu);margin-bottom:.4rem}
.prog-bar{height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden}
.prog-fill{height:100%;border-radius:3px}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(105px,1fr));gap:6px;margin-bottom:1.5rem}
.scard{background:var(--sur);border:1px solid var(--bor);border-radius:4px;padding:.8rem .6rem;text-align:center;position:relative}
.scard.ok{border-color:rgba(62,207,178,.35);background:rgba(62,207,178,.04)}
.scard.err{border-color:rgba(255,77,109,.35);background:rgba(255,77,109,.04)}
.scard-dot{position:absolute;top:5px;right:5px;width:7px;height:7px;border-radius:50%}
.scard.ok .scard-dot{background:var(--ok)} .scard.err .scard-dot{background:var(--err)}
.scard-dia{font-size:.54rem;color:var(--mu);margin-bottom:.1rem}
.scard-dow{font-size:.52rem;color:var(--mu);margin-bottom:.3rem}
.scard-ing{font-family:'DM Serif Display',serif;font-size:.95rem;margin-bottom:.1rem}
.scard.ok .scard-ing{color:var(--ok)} .scard.err .scard-ing{color:var(--err)}
.scard-pct{font-size:.6rem;font-weight:600}
.scard.ok .scard-pct{color:var(--ok)} .scard.err .scard-pct{color:var(--err)}
.scard-esp{font-size:.48rem;color:var(--mu);margin-top:.06rem}
.tw{overflow-x:auto;margin-bottom:1.5rem}
table.main{width:100%;border-collapse:collapse;font-size:.64rem}
table.main thead tr{border-bottom:1px solid var(--bor)}
table.main th{font-size:.52rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mu);padding:.4rem .5rem;text-align:right;white-space:nowrap}
table.main th:first-child,table.main th:nth-child(2){text-align:left}
table.main tbody tr{border-bottom:1px solid rgba(255,255,255,.025)}
table.main tbody tr:hover{background:rgba(255,255,255,.015)}
table.main td{padding:.45rem .5rem;text-align:right;vertical-align:middle}
table.main td:first-child,table.main td:nth-child(2){text-align:left;color:var(--mu)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--bor);border:1px solid var(--bor);margin-bottom:1.5rem}
.tc{background:var(--sur);padding:1rem}
.tc-title{font-family:'Syne',sans-serif;font-size:.6rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--mu);margin-bottom:.7rem}
.rt{width:100%;border-collapse:collapse;font-size:.63rem}
.rt td{padding:.28rem .35rem;border-bottom:1px solid rgba(255,255,255,.03)}
.gd{font-size:.56rem;color:var(--mu);text-align:right;margin-top:1.5rem}
@media(max-width:600px){.sgrid{grid-template-columns:repeat(3,1fr)}.two{grid-template-columns:1fr}}
"""

def gen_local_html(local_name, meses_data):
    color = get_color(local_name)
    tabs_nav = ""
    tabs_content = ""

    for idx, (order, nombre, rows) in enumerate(meses_data):
        tab_id = f"tab_{idx}"
        active = "active" if idx == len(meses_data) - 1 else ""
        tabs_nav += f'<button class="tab-btn {active}" onclick="showTab(\'{tab_id}\')" id="btn_{tab_id}">{nombre}</button>'

        days_map   = {r["dia"]: r for r in rows}
        total_ing  = sum(r["ingresos"] for r in days_map.values())
        total_cli  = sum(r["clientes"] for r in days_map.values())
        total_alq  = sum(r["alquileres"] for r in days_map.values())
        total_gas  = sum(r["gastos"] for r in days_map.values())
        media_real = total_ing / len(days_map) if days_map else 0
        tkt        = total_ing / total_cli if total_cli else 0

        hist_avg   = calc_historical_avg(meses_data, order)
        total_esp  = sum(hist_avg.get(r["dow"], 0) for r in days_map.values())
        var_hist   = ((total_ing - total_esp) / total_esp * 100) if total_esp else 0
        dias_sobre = sum(1 for r in days_map.values() if r["ingresos"] >= hist_avg.get(r["dow"], 0))
        dias_bajo  = len(days_map) - dias_sobre

        dias_restantes = max(0, 30 - len(days_map))
        proy_extra = 0
        if days_map:
            last = days_map[max(days_map.keys())]
            for i in range(1, dias_restantes + 1):
                proy_extra += hist_avg.get(DIAS_ES[(last["dow_idx"] + i) % 7], media_real)
        proy_total = total_ing + proy_extra

        comp_section = ""
        if idx > 0:
            prev_order, prev_nombre, prev_rows = meses_data[idx - 1]
            map_prev = {r["dia"]: r for r in prev_rows if r["dia"] <= 23}
            map_curr = {r["dia"]: r for r in rows if r["dia"] <= 23}
            tot_prev = sum(r["ingresos"] for r in map_prev.values())
            tot_curr = sum(r["ingresos"] for r in map_curr.values())
            var_comp = ((tot_curr - tot_prev) / tot_prev * 100) if tot_prev else 0
            vc = "var(--ok)" if var_comp >= 0 else "var(--err)"
            filas_comp = ""
            for d in range(1, 24):
                rp = map_prev.get(d); rc = map_curr.get(d)
                ip = rp["ingresos"] if rp else 0
                ic = rc["ingresos"] if rc else 0
                diff = ic - ip
                pct  = f"{diff/ip*100:+.1f}%" if ip else "?"
                cd   = "var(--ok)" if diff >= 0 else "var(--err)"
                dp   = rp["dow"] if rp else "?"; dc_ = rc["dow"] if rc else "?"
                filas_comp += f'<tr><td>Dia {d}</td><td>{dp}/{dc_}</td><td style="color:var(--mu)">{ip:,.0f}€</td><td style="color:{color}">{ic:,.0f}€</td><td style="color:{cd}">{diff:+,.0f}€</td><td style="color:{cd}">{pct}</td></tr>'
            comp_section = f"""
            <div class="sec">Comparativa {prev_nombre} vs {nombre} · dias 1-23</div>
            <div class="kpis" style="margin-bottom:1rem">
              <div class="kpi"><div class="kl">{prev_nombre}</div><div class="kv" style="color:var(--mu)">{tot_prev:,.0f}€</div></div>
              <div class="kpi"><div class="kl">{nombre}</div><div class="kv" style="color:{color}">{tot_curr:,.0f}€</div></div>
              <div class="kpi"><div class="kl">Variacion</div><div class="kv" style="color:{vc}">{var_comp:+.1f}%</div><div class="ks">{tot_curr-tot_prev:+,.0f}€</div></div>
            </div>
            <div class="tw"><table class="main">
              <thead><tr><th>Dia</th><th>Sem.</th><th>{prev_nombre}</th><th>{nombre}</th><th>Dif.</th><th>Var%</th></tr></thead>
              <tbody>{filas_comp}</tbody>
            </table></div>"""

        cards = ""
        for r in sorted(days_map.values(), key=lambda x: x["dia"]):
            esp  = hist_avg.get(r["dow"], 0)
            diff = r["ingresos"] - esp
            pct  = (diff / esp * 100) if esp else 0
            ok   = r["ingresos"] >= esp
            cards += f"""<div class="scard {'ok' if ok else 'err'}">
              <div class="scard-dot"></div>
              <div class="scard-dia">Dia {r['dia']}</div>
              <div class="scard-dow">{r['dow']}</div>
              <div class="scard-ing">{r['ingresos']:,.0f}€</div>
              <div class="scard-pct">{'▲' if ok else '▼'} {pct:+.1f}%</div>
              <div class="scard-esp">esp. {esp:,.0f}€</div>
            </div>"""

        filas_det = ""
        for r in sorted(days_map.values(), key=lambda x: x["dia"]):
            esp  = hist_avg.get(r["dow"], 0)
            diff = r["ingresos"] - esp
            pct  = (diff / esp * 100) if esp else 0
            ok   = r["ingresos"] >= esp
            dc   = "#3ecfb2" if ok else "#ff4d6d"
            sym  = "▲" if ok else "▼"
            filas_det += f'<tr><td>{r["fecha"]}</td><td>{r["dow"]}</td><td style="color:{color}">{r["ingresos"]:,.0f}€</td><td style="color:var(--mu)">{esp:,.0f}€</td><td style="color:{dc}">{sym} {pct:+.1f}%</td><td style="color:{dc}">{diff:+,.0f}€</td><td style="color:var(--mu)">{int(r["clientes"])}</td><td style="color:{color}">{r["alquileres"]:,.0f}€</td></tr>'

        dow_ref = "".join(f"<tr><td style='color:var(--mu)'>{d}</td><td style='color:{color};text-align:right'>{hist_avg.get(d,0):,.0f}€</td></tr>" for d in DIAS_ES)
        has_hist = any(v > 0 for v in hist_avg.values())
        sem_section = ""
        if has_hist:
            sem_section = f"""
            <div class="sec">Semaforo vs media historica</div>
            <div class="kpis" style="margin-bottom:1rem">
              <div class="kpi"><div class="kl">Ingresos acumulados</div><div class="kv" style="color:{color}">{total_ing:,.0f}€</div><div class="ks">{len(days_map)} dias</div></div>
              <div class="kpi"><div class="kl">Esperado historico</div><div class="kv" style="color:var(--mu)">{total_esp:,.0f}€</div></div>
              <div class="kpi"><div class="kl">Desviacion</div><div class="kv" style="color:{'var(--ok)' if var_hist>=0 else 'var(--err)'}">{var_hist:+.1f}%</div></div>
              <div class="kpi"><div class="kl">Media diaria</div><div class="kv" style="color:{color}">{media_real:,.0f}€</div></div>
              <div class="kpi"><div class="kl">Dias en verde</div><div class="kv" style="color:var(--ok)">{dias_sobre}</div></div>
              <div class="kpi"><div class="kl">Dias en rojo</div><div class="kv" style="color:var(--err)">{dias_bajo}</div></div>
              <div class="kpi"><div class="kl">Proyeccion fin mes</div><div class="kv" style="color:var(--warn)">{proy_total:,.0f}€</div></div>
            </div>
            <div class="prog-wrap">
              <div class="prog-label"><span>{len(days_map)} dias registrados</span><span>{30-len(days_map)} dias restantes</span></div>
              <div class="prog-bar"><div class="prog-fill" style="width:{min(100,len(days_map)/30*100):.1f}%;background:{color}"></div></div>
            </div>
            <div class="sgrid">{cards}</div>"""

        tabs_content += f"""
        <div id="{tab_id}" class="tab-panel {'active' if active else ''}">
          <div class="sec">Resumen {nombre}</div>
          <div class="kpis">
            <div class="kpi"><div class="kl">Ingresos totales</div><div class="kv" style="color:{color}">{total_ing:,.0f}€</div></div>
            <div class="kpi"><div class="kl">Media diaria</div><div class="kv" style="color:{color}">{media_real:,.0f}€</div></div>
            <div class="kpi"><div class="kl">Alquileres</div><div class="kv" style="color:{color}">{total_alq:,.0f}€</div></div>
            <div class="kpi"><div class="kl">Gastos</div><div class="kv" style="color:var(--err)">{total_gas:,.0f}€</div></div>
          </div>
          {comp_section}
          {sem_section}
          <div class="sec">Detalle diario</div>
          <div class="tw"><table class="main">
            <thead><tr><th>Fecha</th><th>Dia</th><th>Ingresos</th><th>Media hist.</th><th>Desv.</th><th>Dif.</th><th>Clientes</th><th>Alquileres</th></tr></thead>
            <tbody>{filas_det}</tbody>
          </table></div>
          <div class="two">
            <div class="tc"><div class="tc-title">Media historica por dia</div><table class="rt"><tbody>{dow_ref}</tbody></table></div>
          </div>
        </div>"""

    tab_css = f".tab-btn.active{{background:{color}18;border-color:{color};color:{color}}}"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{local_name}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<style>{COMMON_CSS}{tab_css}</style>
</head>
<body>
<header>
  <div class="brand"><span style="color:{color}">{local_name}</span></div>
  <div class="badge">Generado {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
</header>
<div class="wrap">
  <div class="tabs-nav">{tabs_nav}</div>
  {tabs_content}
  <div class="gd">Maxxage Analytics · {datetime.now().strftime("%d/%m/%Y")}</div>
</div>
<script>
function showTab(id) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.getElementById('btn_' + id).classList.add('active');
}}
</script>
</body></html>"""
