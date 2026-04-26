import requests, urllib3, re, time
from datetime import datetime
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL          = "http://www.xarovtrade21.com/stats"
LOGIN_URL         = f"{BASE_URL}/login.php"
USERNAME          = "jose"
PASSWORD          = "Jsnou6"
LOCALES_EXCLUIDOS = ["sala luxx", "luxx", "cantue", "cafeteria via"]
DIAS_ES           = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
LOCAL_COLORS      = {"MAD": "#3ecfb2", "VLC": "#7c6af5", "MBM": "#5ecf7a"}

def get_color(name):
    for k, v in LOCAL_COLORS.items():
        if k.upper() in name.upper():
            return v
    return "#3ecfb2"

def login_and_get_session():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        driver.get(LOGIN_URL)
        time.sleep(2)
        driver.find_element(By.NAME, "form-username").send_keys(USERNAME)
        driver.find_element(By.NAME, "form-password").send_keys(PASSWORD)
        try:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except:
            try:
                driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            except:
                driver.find_element(By.CSS_SELECTOR, ".btn").click()
        time.sleep(3)
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/5.0"
        for cookie in driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])
        admin_html = driver.page_source
        return session, admin_html
    finally:
        driver.quit()

def discover_locals(admin_html):
    soup = BeautifulSoup(admin_html, "html.parser")
    links = {}
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if href in seen or not text: continue
        seen.add(href)
        if "codloc=" not in href: continue
        if any(ex in text.lower() for ex in LOCALES_EXCLUIDOS): continue
        if href.startswith("http"):
            url = href
        elif href.startswith("/"):
            url = "http://www.xarovtrade21.com" + href
        else:
            url = "http://www.xarovtrade21.com/stats/" + href.lstrip("/")
        links[text] = url
    return links

def discover_months(session, local_url):
    r = session.get(local_url, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    meses = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href in seen: continue
        seen.add(href)
        if "menu=1" in href and "mes=" in href and "mesgas" not in href:
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = "http://www.xarovtrade21.com" + href
            else:
                url = "http://www.xarovtrade21.com/stats/" + href.lstrip("/")
            mes_num = re.search(r'[&?]mes=(\d+)', href)
            order = int(mes_num.group(1)) if mes_num else 99
            meses.append({"nombre": f"Mes {order}", "url": url, "order": order})
    meses.sort(key=lambda x: x["order"])
    return meses

def parse_amount(text):
    if not text: return 0.0
    text = text.replace("€", "").strip()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try: return float(text)
    except: return 0.0

def extract_table(session, url, nombre):
    r = session.get(url, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = None
    for t in soup.find_all("table"):
        if "fecha" in t.get_text().lower() and "ingresos" in t.get_text().lower():
            table = t; break
    if not table: return []

    rows_el = table.find_all("tr")
    if not rows_el: return []
    headers = [th.get_text(strip=True).lower() for th in rows_el[0].find_all(["th","td"])]

    col = {}
    for i, h in enumerate(headers):
        if "fecha" in h:                       col["fecha"] = i
        elif "cliente" in h:                   col["clientes"] = i
        elif "alquiler" in h:                  col["alquileres"] = i
        elif "barra" in h and "visa" not in h: col["barras"] = i
        elif "ingreso" in h:                   col["ingresos"] = i
        elif "gasto" in h:                     col["gastos"] = i

    def gv(cells, key):
        idx = col.get(key)
        if idx is None or idx >= len(cells): return "0"
        return cells[idx].get_text(strip=True)

    data = []
    for tr in rows_el[1:]:
        cells = tr.find_all(["td","th"])
        if not cells: continue
        if "total" in tr.get_text().lower()[:30]: continue
        fecha_str = gv(cells, "fecha")
        if not fecha_str or not re.search(r'\d{2}[/\-]\d{2}', fecha_str): continue
        try:
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try: dt = datetime.strptime(fecha_str, fmt); break
                except: continue
            else: continue
        except: continue

        data.append({
            "dia": dt.day, "mes": dt.month, "anyo": dt.year,
            "fecha": dt.strftime("%d/%m/%Y"),
            "dow": DIAS_ES[dt.weekday()], "dow_idx": dt.weekday(),
            "clientes":   parse_amount(gv(cells, "clientes")),
            "ingresos":   parse_amount(gv(cells, "ingresos")),
            "gastos":     parse_amount(gv(cells, "gastos")),
            "alquileres": parse_amount(gv(cells, "alquileres")),
            "barras":     parse_amount(gv(cells, "barras")),
        })
    return data

def calc_historical_avg(all_months_data, current_order):
    dow_vals = defaultdict(list)
    for order, nombre, rows in all_months_data:
        if order >= current_order: continue
        for row in rows:
            if row["ingresos"] > 0:
                dow_vals[row["dow"]].append(row["ingresos"])
    return {d: (sum(v)/len(v) if v else 0.0) for d in DIAS_ES for v in [dow_vals[d]]}

def run_scraper(modo="completo"):
    """
    modo='rapido'   -> solo los 2 ultimos meses
    modo='completo' -> todos los meses
    """
    session, admin_html = login_and_get_session()
    locals_map = discover_locals(admin_html)
    resultados = {}

    for local_name, local_url in locals_map.items():
        meses = discover_months(session, local_url)
        if not meses: continue

        # Modo rapido: solo los 2 ultimos meses
        if modo == "rapido":
            meses = meses[-2:] if len(meses) >= 2 else meses

        meses_data = []
        for mes in meses:
            try:
                rows = extract_table(session, mes["url"], mes["nombre"])
                meses_data.append((mes["order"], mes["nombre"], rows))
            except Exception as e:
                print(f"Error {local_name} {mes['nombre']}: {e}")

        if meses_data:
            resultados[local_name] = meses_data

    return resultados
