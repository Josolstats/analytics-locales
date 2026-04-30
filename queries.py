import pymysql
from datetime import date
import calendar

DB_HOST = "nouesmalt.duckdns.org"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "fran06"

# tipo "maxx"   -> BD barras separada, cocktails = tickets_sorteo*5
# tipo "kixx"   -> BD barras separada, cocktails = precio directo, solo barra1
# tipo "luna"   -> BD barras separada, cocktails = tickets_sorteo*5, solo barra1
# tipo "interno"-> barra_tickets integrada en misma BD, sin cocktails

LOCALES = {
    "sala_maxx":   {"nombre":"Sala Maxx",       "tipo":"maxx",    "db_rec":"bs2026",        "db_bar":"barrabs2026",   "num_barras":5},
    "sala_kixx":   {"nombre":"Sala Kixx",        "tipo":"kixx",    "db_rec":"kixx2026",      "db_bar":"barrakixx2026", "num_barras":1},
    "luna_azul":   {"nombre":"Luna Azul",        "tipo":"luna",    "db_rec":"lunaxilxes2026","db_bar":"barraluna2026", "num_barras":1},
    "mb_ibiza":    {"nombre":"MB Ibiza",         "tipo":"interno", "db_rec":"mbi2026",       "db_bar":None,            "num_barras":0},
    "maxxage_mad": {"nombre":"Maxxage Madrid",   "tipo":"interno", "db_rec":"maxxmad2026",   "db_bar":None,            "num_barras":0},
    "maxxage_vlc": {"nombre":"Maxxage Valencia", "tipo":"interno", "db_rec":"maxxvlc2026",   "db_bar":None,            "num_barras":0},
    "mb_marbella": {"nombre":"MB Marbella",      "tipo":"interno", "db_rec":"mbm2026",       "db_bar":None,            "num_barras":0},
}

LOCALES_2025 = {
    "sala_maxx":   {"db_rec":"bs2025",         "db_bar":"barrabs2025"},
    "sala_kixx":   {"db_rec":"kixx2025",       "db_bar":"barrakixx2025"},
    "luna_azul":   {"db_rec":"lunaxilxes2025", "db_bar":"barraluna2025"},
    "mb_ibiza":    {"db_rec":"mbi2025",        "db_bar":None},
    "maxxage_mad": {"db_rec":"maxxmad2025",    "db_bar":None},
    "maxxage_vlc": {"db_rec":"maxxvlc2025",    "db_bar":None},
    "mb_marbella": {"db_rec":"mbm2025",        "db_bar":None},
}

def get_conn():
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, connect_timeout=10)

def calcular_recepcion(conn, db_rec, lote):
    cur = conn.cursor()
    cur.execute(f"SELECT SUM(importe) FROM {db_rec}.cobros WHERE codlot={lote}")
    total_cobros = float(cur.fetchone()[0] or 0)
    cur.execute(f"SELECT SUM(l.precio*l.cantidad) FROM {db_rec}.tickets t, {db_rec}.lineasticket l WHERE t.codlot={lote} AND t.codtic=l.codtic AND l.codart<100000")
    alq = float(cur.fetchone()[0] or 0)
    pen = total_cobros - alq
    return round(pen), round(alq)

def calcular_gastos(conn, db_rec, lote):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT SUM(g.importe) FROM {db_rec}.gastos g WHERE g.codlot={lote} AND g.estado<>2 AND g.codcon NOT IN (23,30)")
        return float(cur.fetchone()[0] or 0)
    except Exception:
        return 0

def calcular_dia_maxx(conn, db_rec, db_bar, num_barras, lote, fecha, anyo):
    cur = conn.cursor()
    d, m, y = fecha.day, fecha.month, fecha.year
    pen, alq = calcular_recepcion(conn, db_rec, lote)

    bar = 0
    for b in range(1, num_barras + 1):
        try:
            cur.execute(f"SELECT SUM(l.cantidad*l.precio) FROM {db_bar}.lotes{b} lo, {db_bar}.lineasticket{b} l, {db_bar}.tickets{b} t WHERE lo.codlot=t.codlot AND l.codtic=t.codtic AND (t.estado=1 OR t.estado=2) AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
            bar += float(cur.fetchone()[0] or 0)
        except Exception:
            pass

    ent = 0
    try:
        cur.execute(f"SELECT SUM(v.precio) FROM {db_bar}.lotes_entradas lo, {db_bar}.entradas e, {db_bar}.var_entradas v WHERE lo.codlotent=e.codlot AND v.tipo=e.tipo AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        ent = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    coc = 0
    for b in range(1, num_barras + 1):
        try:
            cur.execute(f"SELECT SUM(c.tickets_sorteo*5) FROM {db_bar}.cocktails c, {db_bar}.lotes{b} lo WHERE lo.codlot=c.lote AND c.barra={b} AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
            coc += float(cur.fetchone()[0] or 0)
        except Exception:
            pass

    gas = calcular_gastos(conn, db_rec, lote)
    ing = pen + alq + bar + ent - coc
    dis = ing - gas
    return {"pen":round(pen),"alq":round(alq),"bar":round(bar),"ent":round(ent),"coc":round(coc),"ing":round(ing),"gas":round(gas),"dis":round(dis)}

def calcular_dia_kixx(conn, db_rec, db_bar, lote, fecha, anyo):
    cur = conn.cursor()
    d, m, y = fecha.day, fecha.month, fecha.year
    pen, alq = calcular_recepcion(conn, db_rec, lote)

    # Solo barra1
    bar = 0
    try:
        cur.execute(f"SELECT SUM(l.cantidad*l.precio) FROM {db_bar}.lotes1 lo, {db_bar}.lineasticket1 l, {db_bar}.tickets1 t WHERE lo.codlot=t.codlot AND l.codtic=t.codtic AND (t.estado=1 OR t.estado=2) AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        bar = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    ent = 0
    try:
        cur.execute(f"SELECT SUM(v.precio) FROM {db_bar}.lotes_entradas lo, {db_bar}.entradas e, {db_bar}.var_entradas v WHERE lo.codlotent=e.codlot AND v.tipo=e.tipo AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        ent = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    # Cocktails kixx usa precio directo
    coc = 0
    try:
        cur.execute(f"SELECT SUM(c.precio) FROM {db_bar}.cocktails c, {db_bar}.lotes1 lo WHERE lo.codlot=c.lote AND c.barra='1' AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        coc = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    gas = calcular_gastos(conn, db_rec, lote)
    ing = pen + alq + bar + ent - coc
    dis = ing - gas
    return {"pen":round(pen),"alq":round(alq),"bar":round(bar),"ent":round(ent),"coc":round(coc),"ing":round(ing),"gas":round(gas),"dis":round(dis)}

def calcular_dia_luna(conn, db_rec, db_bar, lote, fecha, anyo):
    cur = conn.cursor()
    d, m, y = fecha.day, fecha.month, fecha.year
    pen, alq = calcular_recepcion(conn, db_rec, lote)

    bar = 0
    try:
        cur.execute(f"SELECT SUM(l.cantidad*l.precio) FROM {db_bar}.lotes1 lo, {db_bar}.lineasticket1 l, {db_bar}.tickets1 t WHERE lo.codlot=t.codlot AND l.codtic=t.codtic AND (t.estado=1 OR t.estado=2) AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        bar = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    ent = 0
    try:
        cur.execute(f"SELECT SUM(v.precio) FROM {db_bar}.lotes_entradas lo, {db_bar}.entradas e, {db_bar}.var_entradas v WHERE lo.codlotent=e.codlot AND v.tipo=e.tipo AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        ent = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    coc = 0
    try:
        cur.execute(f"SELECT SUM(c.tickets_sorteo*5) FROM {db_bar}.cocktails c, {db_bar}.lotes1 lo WHERE lo.codlot=c.lote AND c.barra='1' AND DAY(lo.fecha)={d} AND MONTH(lo.fecha)={m} AND YEAR(lo.fecha)={y}")
        coc = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    gas = calcular_gastos(conn, db_rec, lote)
    ing = pen + alq + bar + ent - coc
    dis = ing - gas
    return {"pen":round(pen),"alq":round(alq),"bar":round(bar),"ent":round(ent),"coc":round(coc),"ing":round(ing),"gas":round(gas),"dis":round(dis)}

def calcular_dia_interno(conn, db_rec, lote, anyo):
    pen, alq = calcular_recepcion(conn, db_rec, lote)
    cur = conn.cursor()

    bar = 0
    try:
        cur.execute(f"SELECT SUM(l.precio*l.cantidad) FROM {db_rec}.barra_tickets t, {db_rec}.barra_lineasticket l WHERE t.codlot={lote} AND t.codtic=l.codtic")
        bar = float(cur.fetchone()[0] or 0)
    except Exception:
        pass

    gas = calcular_gastos(conn, db_rec, lote)
    ing = pen + alq + bar
    dis = ing - gas
    return {"pen":round(pen),"alq":round(alq),"bar":round(bar),"ent":0,"coc":0,"ing":round(ing),"gas":round(gas),"dis":round(dis)}

def get_totales_rango(local_key, anyo, fecha_ini, fecha_fin, incluir_dias=False):
    cfg = LOCALES[local_key]
    if anyo == 2025:
        db_rec = LOCALES_2025[local_key]["db_rec"]
        db_bar = LOCALES_2025[local_key]["db_bar"]
    else:
        db_rec = cfg["db_rec"]
        db_bar = cfg["db_bar"]

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT codlot, fecha FROM {db_rec}.lotes WHERE fecha>='{fecha_ini}' AND fecha<='{fecha_fin}' ORDER BY fecha")
        lotes = cur.fetchall()
        tot = {"pen":0,"alq":0,"bar":0,"ent":0,"coc":0,"ing":0,"gas":0,"dis":0,"dias":len(lotes)}
        dias_list = []

        for lote, fecha in lotes:
            tipo = cfg["tipo"]
            if tipo == "maxx":
                d = calcular_dia_maxx(conn, db_rec, db_bar, cfg["num_barras"], lote, fecha, anyo)
            elif tipo == "kixx":
                d = calcular_dia_kixx(conn, db_rec, db_bar, lote, fecha, anyo)
            elif tipo == "luna":
                d = calcular_dia_luna(conn, db_rec, db_bar, lote, fecha, anyo)
            else:
                d = calcular_dia_interno(conn, db_rec, lote, anyo)

            for k in ["pen","alq","bar","ent","coc","ing","gas","dis"]:
                tot[k] += d[k]
            if incluir_dias:
                dias_list.append({"fecha": fecha.strftime("%d/%m"), "dia": fecha.day, **d})

        tot = {k: round(v) for k, v in tot.items()}
        if incluir_dias:
            return tot, dias_list
        return tot
    finally:
        conn.close()

def get_mes(local_key, mes, hasta_dia=None):
    hoy = date.today()
    if hasta_dia is None:
        hasta_dia = hoy.day if mes == hoy.month else calendar.monthrange(2026, mes)[1]
    fi26 = f"2026-{mes:02d}-01"
    ff26 = f"2026-{mes:02d}-{hasta_dia:02d} 23:59:59"
    fi25 = f"2025-{mes:02d}-01"
    ff25 = f"2025-{mes:02d}-{hasta_dia:02d} 23:59:59"
    t26 = get_totales_rango(local_key, 2026, fi26, ff26)
    t25 = get_totales_rango(local_key, 2025, fi25, ff25)
    return {"y2025": t25, "y2026": t26, "hasta_dia": hasta_dia}

def get_mes_con_dias(local_key, mes, hasta_dia=None):
    hoy = date.today()
    if hasta_dia is None:
        hasta_dia = hoy.day if mes == hoy.month else calendar.monthrange(2026, mes)[1]
    fi26 = f"2026-{mes:02d}-01"
    ff26 = f"2026-{mes:02d}-{hasta_dia:02d} 23:59:59"
    fi25 = f"2025-{mes:02d}-01"
    ff25 = f"2025-{mes:02d}-{hasta_dia:02d} 23:59:59"
    t26, dias26 = get_totales_rango(local_key, 2026, fi26, ff26, incluir_dias=True)
    t25, dias25 = get_totales_rango(local_key, 2025, fi25, ff25, incluir_dias=True)
    return {"y2025": t25, "y2026": t26, "dias2025": dias25, "dias2026": dias26, "hasta_dia": hasta_dia}

def get_acumulado(local_key):
    hoy = date.today()
    fi26 = "2026-01-01"
    ff26 = f"2026-{hoy.month:02d}-{hoy.day:02d} 23:59:59"
    fi25 = "2025-01-01"
    ff25 = f"2025-{hoy.month:02d}-{hoy.day:02d} 23:59:59"
    t26 = get_totales_rango(local_key, 2026, fi26, ff26)
    t25 = get_totales_rango(local_key, 2025, fi25, ff25)
    meses26, meses25 = [], []
    for m in range(1, hoy.month + 1):
        ultimo = hoy.day if m == hoy.month else calendar.monthrange(2026, m)[1]
        m26 = get_totales_rango(local_key, 2026, f"2026-{m:02d}-01", f"2026-{m:02d}-{ultimo:02d} 23:59:59")
        m25 = get_totales_rango(local_key, 2025, f"2025-{m:02d}-01", f"2025-{m:02d}-{ultimo:02d} 23:59:59")
        meses26.append(m26["ing"])
        meses25.append(m25["ing"])
    return {"y2025": t25, "y2026": t26, "meses2025": meses25, "meses2026": meses26}
