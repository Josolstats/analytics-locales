import os
import threading
from flask import Flask, render_template_string, jsonify
from scraper import run_scraper
from generator import gen_local_html

app = Flask(__name__)

# Estado global del proceso
estado = {"corriendo": False, "progreso": "", "resultados": {}, "modo": ""}

HOME_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maxxage Analytics</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0a0a0f;--sur:#111118;--bor:#1e1e2e;--txt:#e8e8f0;--mu:#5a5a7a;--ok:#3ecfb2;--err:#ff4d6d;--warn:#f5a623}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'DM Mono',monospace;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem}
.logo{font-family:'Syne',sans-serif;font-weight:800;font-size:clamp(2rem,6vw,4rem);letter-spacing:-.03em;margin-bottom:.5rem;text-align:center}
.logo span{color:var(--ok)}
.sub{font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mu);margin-bottom:3rem;text-align:center}
.btns{display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-bottom:2rem}
.btn{font-family:'DM Mono',monospace;font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;padding:1rem 2rem;border:1px solid;cursor:pointer;border-radius:3px;transition:all .2s;background:transparent}
.btn-rapido{border-color:var(--warn);color:var(--warn)}
.btn-rapido:hover{background:var(--warn);color:var(--bg)}
.btn-completo{border-color:var(--ok);color:var(--ok)}
.btn-completo:hover{background:var(--ok);color:var(--bg)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.estado{text-align:center;font-size:.7rem;color:var(--mu);min-height:2rem;margin-bottom:2rem}
.estado.activo{color:var(--warn)}
.locales{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;background:var(--bor);border:1px solid var(--bor);width:100%;max-width:900px}
.local-btn{background:var(--sur);padding:1.2rem;cursor:pointer;border:none;color:var(--txt);font-family:'DM Mono',monospace;font-size:.7rem;text-align:left;transition:background .2s}
.local-btn:hover{background:#1e1e2e}
.local-nombre{font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;margin-bottom:.3rem}
.local-info{font-size:.6rem;color:var(--mu)}
.spinner{display:inline-block;width:12px;height:12px;border:2px solid var(--mu);border-top-color:var(--warn);border-radius:50%;animation:spin .8s linear infinite;margin-right:.5rem;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.info-box{border:1px solid var(--bor);padding:1rem 1.5rem;font-size:.65rem;color:var(--mu);max-width:900px;width:100%;margin-bottom:2rem;line-height:1.8}
.info-box span{color:var(--warn)}
</style>
</head>
<body>
<div class="logo">Maxxage <span>Analytics</span></div>
<div class="sub">Panel de informes · Actualizado en tiempo real</div>

<div class="info-box">
  <span>Rapido</span> — Compara el mes actual con el anterior · ~2-3 min &nbsp;|&nbsp;
  <span>Completo</span> — Todos los meses con semaforo historico · ~8 min
</div>

<div class="btns">
  <button class="btn btn-rapido" onclick="lanzar('rapido')" id="btn-rapido">⚡ Rapido</button>
  <button class="btn btn-completo" onclick="lanzar('completo')" id="btn-completo">📊 Completo</button>
</div>

<div class="estado" id="estado">Listo para generar informes</div>

<div class="locales" id="locales" style="display:none"></div>

<script>
let intervalo = null;

function lanzar(modo) {
  document.getElementById('btn-rapido').disabled = true;
  document.getElementById('btn-completo').disabled = true;
  document.getElementById('locales').style.display = 'none';
  document.getElementById('estado').className = 'estado activo';
  document.getElementById('estado').innerHTML = '<span class="spinner"></span> Iniciando...';

  fetch('/lanzar/' + modo, {method: 'POST'})
    .then(() => {
      intervalo = setInterval(checkEstado, 3000);
    });
}

function checkEstado() {
  fetch('/estado')
    .then(r => r.json())
    .then(data => {
      document.getElementById('estado').innerHTML = data.corriendo
        ? '<span class="spinner"></span> ' + data.progreso
        : data.progreso;

      if (!data.corriendo) {
        clearInterval(intervalo);
        document.getElementById('btn-rapido').disabled = false;
        document.getElementById('btn-completo').disabled = false;
        document.getElementById('estado').className = 'estado';

        if (Object.keys(data.resultados).length > 0) {
          mostrarLocales(data.resultados);
        }
      }
    });
}

function mostrarLocales(resultados) {
  const colores = {MAD: '#3ecfb2', VLC: '#7c6af5', MBM: '#5ecf7a'};
  function getColor(name) {
    for (const [k, v] of Object.entries(colores)) {
      if (name.toUpperCase().includes(k)) return v;
    }
    return '#3ecfb2';
  }

  const container = document.getElementById('locales');
  container.innerHTML = '';
  for (const [nombre, info] of Object.entries(resultados)) {
    const color = getColor(nombre);
    const btn = document.createElement('div');
    btn.className = 'local-btn';
    btn.innerHTML = `<div class="local-nombre" style="color:${color}">${nombre}</div><div class="local-info">${info.meses} meses · ${info.total_ing}</div>`;
    btn.onclick = () => window.open('/informe/' + encodeURIComponent(nombre), '_blank');
    container.appendChild(btn);
  }
  container.style.display = 'grid';
}
</script>
</body>
</html>
"""

def ejecutar_scraper(modo):
    global estado
    try:
        estado["progreso"] = "Haciendo login..."
        resultados_raw = run_scraper(modo)
        
        resumen = {}
        for local_name, meses_data in resultados_raw.items():
            total_ing = sum(
                sum(r["ingresos"] for r in rows)
                for _, _, rows in meses_data
            )
            resumen[local_name] = {
                "meses": len(meses_data),
                "total_ing": f"{total_ing:,.0f}€"
            }
            estado["progreso"] = f"Procesando {local_name}..."

        estado["resultados_raw"] = resultados_raw
        estado["resultados"] = resumen
        estado["corriendo"] = False
        estado["progreso"] = f"✓ Completado — {len(resumen)} locales generados"
    except Exception as e:
        estado["corriendo"] = False
        estado["progreso"] = f"Error: {str(e)}"

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/lanzar/<modo>", methods=["POST"])
def lanzar(modo):
    global estado
    if estado["corriendo"]:
        return jsonify({"ok": False, "msg": "Ya hay un proceso en marcha"})
    estado = {"corriendo": True, "progreso": "Iniciando...", "resultados": {}, "resultados_raw": {}, "modo": modo}
    t = threading.Thread(target=ejecutar_scraper, args=(modo,))
    t.daemon = True
    t.start()
    return jsonify({"ok": True})

@app.route("/estado")
def get_estado():
    return jsonify({
        "corriendo": estado["corriendo"],
        "progreso": estado["progreso"],
        "resultados": estado["resultados"]
    })

@app.route("/informe/<nombre>")
def informe(nombre):
    resultados_raw = estado.get("resultados_raw", {})
    if nombre not in resultados_raw:
        return "Informe no disponible. Genera los informes primero.", 404
    meses_data = resultados_raw[nombre]
    html = gen_local_html(nombre, meses_data)
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
