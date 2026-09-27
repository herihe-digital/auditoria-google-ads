"""auditor.py — el motor de decisión del skill auditor-google-ads (v3).

La IA clasifica y conversa; este archivo lee, calcula, decide y escribe las cifras. Sólo usa la biblioteca
estándar de Python 3.9+, no se conecta a internet y no toca la cuenta.

Uso (en la carpeta donde está el informe):
  python3 auditor.py leer INFORME            turno 1: resumen + términos para buscar nombres
  python3 auditor.py turno1 INFORME          turno 1: el mensaje completo (lee nombres.txt)
  python3 auditor.py ficha INFORME           turno 2: valida ficha.json contra respuestas.txt
  python3 auditor.py etiquetar INFORME       turno 2: los términos a etiquetar (--compra: 2.ª pregunta)
  python3 auditor.py auditar INFORME         turno 2: decide y escribe el informe (lee etiquetas.csv, compra.csv)
Desde Python: import auditor; auditor.main(["leer", "informe.csv"])
"""
import csv
import json
import math
import re
import statistics
import sys
import unicodedata
from datetime import date
from pathlib import Path

VERSION = "3.0.0"

# ───────────────────────────── texto ─────────────────────────────


def norm(s):
    """minúsculas, sin tildes, sólo letras y dígitos separados por un espacio"""
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w]+", " ", s).replace("_", " ").split())


def toks(s):
    return tuple(norm(s).split())


def contiene(term_toks, frase_toks):
    """¿la frase está dentro del término, palabra por palabra y en orden? (como la negativa de frase)"""
    n = len(frase_toks)
    return n > 0 and any(term_toks[i:i + n] == frase_toks for i in range(len(term_toks) - n + 1))


STOP = {"de", "en", "el", "la", "los", "las", "para", "por", "con", "y", "del", "al", "un", "una", "a", "o", "e",
        "que", "mi", "tu", "su", "se", "me", "es", "lo", "le", "sin", "the", "of", "for", "and", "to", "in"}
COMPRADOR = {"precio", "precios", "cuanto", "cuesta", "cuestan", "valor", "valores", "cotizacion", "cotizar",
             "barato", "barata", "baratos", "tarifa", "tarifas", "costo", "costos", "chile", "servicio",
             "servicios", "empresa", "empresas", "venta", "comprar", "contratar", "mejor", "cerca"}
GENERICO_GRUPO = {"ag", "grupo", "adgroup", "ad", "group", "search", "busqueda", "campana", "general", "otros"}

# ───────────────────────────── números y formato ─────────────────────────────


def fnum(x, dec=2):
    """número chileno: 1.234 · 0,59 · 11,89"""
    if x is None:
        return "—"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    s = f"{x:,.{dec}f}".rstrip("0").rstrip(".")
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def fmoney(x):
    return "—" if x is None else "$" + f"{int(round(x)):,}".replace(",", ".")


def fpct(x):
    return "—" if x is None else f"{x:.1f}".replace(".", ",") + " %"


def fclics(x):
    return fnum(x) + (" clic" if x == 1 else " clics")


def fpct2(x):
    """porcentaje con dos decimales, para que la multiplicación que se muestra cuadre"""
    return "—" if x is None else f"{x:.2f}".replace(".", ",") + " %"


def fconv(x):
    return fnum(x, 2) + (" conv" if x is not None else "")


DESCONOCIDO = {"", "--", "—", "-", "n/a", "na", "null", "none"}
RX_ES = re.compile(r"-?\d{1,3}(\.\d{3})+(,\d+)?|-?\d+,\d{1,2}")
RX_EN = re.compile(r"-?\d{1,3}(,\d{3})+(\.\d+)?|-?\d+\.\d{1,2}")


def _limpia_num(s):
    s = (s or "").strip().strip('"').strip()
    s = re.sub(r"(?i)\b(clp|usd|ars|mxn|cop|pen|eur|uyu|brl)\b", "", s)
    return s.replace("$", "").replace("%", "").replace(" ", "").replace(" ", "")


def detectar_locale(valores):
    es = en = 0
    for v in valores:
        v = _limpia_num(v)
        if RX_ES.fullmatch(v):
            es += 1
        elif RX_EN.fullmatch(v):
            en += 1
    return "es" if es > en else "en"


def num(s, loc):
    """'97,904' → 97904 · '0,50' (es) → 0.5 · '--' → None (desconocido, jamás cero)"""
    s = _limpia_num(s)
    if s.lower() in DESCONOCIDO:
        return None
    s = s.replace(".", "").replace(",", ".") if loc == "es" else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

# ───────────────────────────── lectura del informe ─────────────────────────────


COLS = {
    "termino": ["termino de busqueda", "terminos de busqueda", "search term", "search terms", "consulta de busqueda",
                "palabra clave", "palabras clave", "keyword", "keywords"],
    "concordancia": ["tipo de concordancia", "concordancia", "match type", "search term match type",
                     "concordancia del termino de busqueda", "tipo de concordancia de palabra clave"],
    "campana": ["campana", "campaign", "nombre de la campana", "campaign name"],
    "grupo": ["grupo de anuncios", "ad group", "nombre del grupo de anuncios", "ad group name"],
    "clics": ["clics", "clicks", "clic"],
    "impr": ["impr", "impresiones", "impressions", "impr s"],
    "costo": ["costo", "coste", "cost", "costo total", "importe"],
    "conv": ["conversiones", "conversions", "conv"],
    "todas": ["todas las conv", "todas las conversiones", "all conv", "all conversions"],
    "valor": ["valor de conv", "valor de conversion", "valor de las conversiones", "valor conv", "conv value",
              "conversion value", "valor de conversiones"],
    "tipo_campana": ["tipo de campana", "campaign type"],
}
NUMERICAS = ("clics", "impr", "costo", "conv", "todas", "valor")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "set": 9,
         "oct": 10, "nov": 11, "dic": 12, "jan": 1, "apr": 4, "aug": 8, "dec": 12}


def _decodificar(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16"), "UTF-16"
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8"), "UTF-8"
    if raw.count(b"\x00") > len(raw) // 4:
        for enc in ("utf-16-le", "utf-16-be"):
            try:
                return raw.decode(enc), "UTF-16"
            except UnicodeDecodeError:
                pass
    try:
        return raw.decode("utf-8"), "UTF-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "Windows-1252"


def _partir(linea, delim):
    if delim == "|":
        s = linea.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]
    return next(csv.reader([linea], delimiter=delim))


BUSQUEDA = ("termino de busqueda", "terminos de busqueda", "search term", "search terms", "consulta de busqueda")


def _mapear(celdas):
    m = {}
    for i, c in enumerate(celdas):
        n = norm(c)
        for k, alias in COLS.items():
            if k not in m and n in alias:
                m[k] = i
                break
    # un informe de términos puede traer también la columna «Palabra clave»: manda el término de búsqueda
    busq = next((i for i, c in enumerate(celdas) if norm(c) in BUSQUEDA), None)
    if busq is not None:
        m["termino"] = busq
    return m


def _fechas(s, mes_primero=False):
    out = []
    for m in re.finditer(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        out.append(date(int(m[1]), int(m[2]), int(m[3])))
    if not out:
        for m in re.finditer(r"(\d{1,2})(?:\s+de)?\s+([a-záé]{3,})\.?(?:\s+de)?\s+(\d{4})", s, re.I):
            mes = MESES.get(norm(m[2])[:3])
            if mes:
                out.append(date(int(m[3]), mes, int(m[1])))
    if not out:
        for m in re.finditer(r"([a-z]{3,})\.?\s+(\d{1,2}),\s*(\d{4})", s, re.I):
            mes = MESES.get(norm(m[1])[:3])
            if mes:
                out.append(date(int(m[3]), mes, int(m[2])))
    if not out:
        pares = [(int(m[1]), int(m[2]), int(m[3])) for m in re.finditer(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)][:2]
        ordenes = ((1, 0), (0, 1)) if mes_primero else ((0, 1), (1, 0))
        for orden in ordenes:   # día/mes (Chile) o mes/día (interfaz en inglés): primero el del idioma del informe
            try:
                fs = [date(a[2], a[orden[1]], a[orden[0]]) for a in pares]
            except ValueError:
                continue
            if len(fs) == 2 and 0 <= (fs[1] - fs[0]).days <= 400:
                return fs
        return []
    return out[:2]


def leer_informe(path):
    """Lee el export de la interfaz (UTF-16/UTF-8, tabulador/coma/punto y coma) o una tabla pegada con «|»."""
    raw = Path(path).read_bytes()
    txt, enc = _decodificar(raw)
    lineas = [ln for ln in txt.splitlines() if ln.strip() and not re.fullmatch(r"[\s|:\-]+", ln)]
    mejor = None
    for delim in ("\t", ",", ";", "|"):
        for i, ln in enumerate(lineas[:40]):
            if ln.count(delim) < 2:
                continue
            try:
                m = _mapear(_partir(ln, delim))
            except (csv.Error, StopIteration):
                continue
            if "termino" in m and len(m) >= 3 and (mejor is None or len(m) > len(mejor[2])):
                mejor = (delim, i, m)
    if mejor is None:
        raise SystemExit("ERROR: no encontré el encabezado (una fila con «Término de búsqueda» o «Palabra clave» "
                         "y columnas de clics/costo). ¿El archivo se leyó en una sola columna? No es «no hay nada».")
    delim, hi, m = mejor
    faltan = [n for k, n in (("costo", "Costo"), ("clics", "Clics")) if k not in m]
    if faltan:
        raise SystemExit(f"ERROR: al informe le falta la columna {' y '.join('«' + x + '»' for x in faltan)}. "
                         "Descárgalo de nuevo con esa columna: sin ella no hay nada que auditar.")
    n_enc = len(_partir(lineas[hi], delim))
    preambulo = lineas[:hi]
    filas_crudas = []
    for ln in lineas[hi + 1:]:
        try:
            filas_crudas.append(_partir(ln, delim))
        except csv.Error:
            continue
    valores = [f[m[k]] for f in filas_crudas for k in NUMERICAS if k in m and m[k] < len(f)]
    loc = detectar_locale(valores)
    terminos, totales, desfasadas = [], {}, 0
    for f in filas_crudas:
        corrida = False
        if delim != "|" and len(f) != n_enc and any(x.strip() for x in f):
            desfasadas += 1
            corrida = not any(re.match(r"\s*total\s*:", c, re.I) for c in f)
        f = f + [""] * (max(m.values()) + 1 - len(f))
        etiqueta_total = next((c.strip() for c in f if re.match(r"\s*total\s*:", c, re.I)), None)
        # una fila con las columnas corridas no aporta cifras (serían de otra columna), pero su búsqueda existe:
        # entra sin números, en duda, para que ninguna negativa la bloquee a ciegas
        vals = {k: (None if corrida else num(f[m[k]], loc)) for k in NUMERICAS if k in m}
        if etiqueta_total:
            totales[etiqueta_total] = vals
            continue
        texto = f[m["termino"]].strip().strip('"').strip("[]").strip('"').strip()
        if not texto:
            continue
        t = {"texto": texto, "n": norm(texto), "toks": toks(texto),
             "campana": f[m["campana"]].strip() if "campana" in m else "",
             "grupo": f[m["grupo"]].strip() if "grupo" in m else "",
             "conc": f[m["concordancia"]].strip() if "concordancia" in m else "", **vals}
        for k in ("clics", "costo", "conv", "todas", "impr", "valor"):
            t.setdefault(k, None)
        t["artefacto"] = t["clics"] is not None and t["impr"] is not None and t["clics"] > t["impr"]
        t["corrida"] = corrida
        terminos.append(t)
    if terminos and desfasadas > max(2, 0.02 * len(terminos)):
        raise SystemExit(f"ERROR: {desfasadas} filas no tienen el mismo número de columnas que el encabezado (suele "
                         "pasar si el separador es coma y los decimales también). Descarga el informe de nuevo, sin "
                         "abrirlo en Excel, o pégalo como tabla.")
    vistos, duplicadas = set(), 0
    for t in terminos:
        # dos informes pegados = filas idénticas CON costo (las de costo cero se repiten normalmente: una por
        # palabra clave que activó la búsqueda)
        if not t["costo"]:
            continue
        clave = (t["n"], t["campana"], t["grupo"], t["conc"], t["clics"], t["impr"], t["costo"], t["conv"])
        duplicadas += clave in vistos
        vistos.add(clave)
    # un mismo nombre de grupo en dos campañas son dos grupos distintos
    camp_de = {}
    for t in terminos:
        camp_de.setdefault(t["grupo"], set()).add(t["campana"])
    for t in terminos:
        t["gkey"] = f"{t['grupo']} ({t['campana']})" if t["grupo"] and len(camp_de[t["grupo"]]) > 1 else t["grupo"]
    titulo = preambulo[0].strip() if preambulo else ""
    en_ingles = bool(re.search(r"(?i)\breport\b|\bsearch terms?\b|\bkeyword", titulo))
    periodo_txt = next((p.strip() for p in preambulo[1:3] if _fechas(p, en_ingles)), "")
    f = _fechas(periodo_txt, en_ingles)
    dias = (f[1] - f[0]).days + 1 if len(f) == 2 else None
    if dias is None:
        m_d = re.search(r"(?:[úu]ltimos|last)\s+(\d{1,3})\s+(?:d[ií]as|days)", " ".join(preambulo), re.I)
        if m_d:
            dias, periodo_txt = int(m_d[1]), f"últimos {m_d[1]} días"
    col_termino = norm(_partir(lineas[hi], delim)[m["termino"]])
    nt = norm(titulo)
    if "search term" in nt or "terminos de busqueda" in nt:
        tipo = "terminos"
    elif "keyword" in nt or "palabra" in nt or col_termino in ("palabra clave", "palabras clave", "keyword",
                                                                "keywords"):
        tipo = "palabras_clave"
    else:
        tipo = "terminos"
    return {"archivo": str(path), "encoding": enc, "delim": {"\t": "tabulador", ",": "coma", ";": "punto y coma",
            "|": "tabla pegada"}[delim], "locale": loc, "titulo": titulo, "periodo": periodo_txt, "dias": dias,
            "tipo": tipo, "columnas": sorted(m), "terminos": terminos, "totales": totales,
            "desfasadas": desfasadas, "duplicadas": duplicadas}


def _total(inf, *nombres):
    for k, v in inf["totales"].items():
        if norm(k).replace("total ", "", 1) in nombres:
            return v
    return None

# ───────────────────────────── agregados ─────────────────────────────


def suma(filas, k):
    return sum((t.get(k) or 0) for t in filas)


def conv_max(t):
    return max(t.get("conv") or 0, t.get("todas") or 0)


def unicos(inf):
    """Un registro por búsqueda (texto normalizado), sumando campañas; id estable por costo."""
    d = {}
    for t in inf["terminos"]:
        u = d.setdefault(t["n"], {"n": t["n"], "texto": t["texto"], "toks": t["toks"], "filas": [], "grupos": []})
        u["filas"].append(t)
        if t["gkey"] and t["gkey"] not in u["grupos"]:
            u["grupos"].append(t["gkey"])
    us = list(d.values())
    cols = set(inf["columnas"])
    for u in us:
        for k in ("clics", "costo", "conv", "todas", "impr", "valor"):
            u[k] = suma(u["filas"], k)
        u["cmax"] = max(u["conv"], u["todas"])
        # «--» es desconocido: una búsqueda sin dato de conversiones nunca se puede dar por «cero conversiones»
        u["conv_desc"] = not ({"conv", "todas"} & cols) or any(
            (k in cols and t.get(k) is None) for t in u["filas"] for k in ("conv", "todas"))
    us.sort(key=lambda u: (-u["costo"], -u["clics"], u["n"]))
    for i, u in enumerate(us, 1):
        u["id"] = f"k{i:03d}"
    return us

# ───────────────────────────── temas (P1b) ─────────────────────────────


SEMILLAS = {
    "empleo": ("Empleo", ["trabajo", "trabajos", "empleo", "empleos", "sueldo", "sueldos", "salario", "salarios",
                          "postular", "postulacion", "vacante", "vacantes", "practica profesional", "freelance",
                          "se busca", "busco trabajo", "ofertas laborales", "oferta laboral", "remuneracion"]),
    "gratis": ("Gratis", ["gratis", "gratuito", "gratuita", "gratuitos", "gratuitas", "free"]),
    "formacion": ("Cursos y tutoriales", ["curso", "cursos", "capacitacion", "capacitaciones", "diplomado",
                                          "certificacion", "tutorial", "tutoriales", "pdf", "plantilla",
                                          "plantillas", "que es", "que significa", "definicion", "ejemplos"]),
    "hazlo_tu_mismo": ("Hazlo tú mismo y «cómo…»", ["casero", "casera", "caseros", "paso a paso"]),
    "tercero": ("Plataformas de terceros", ["mercadolibre", "mercado libre", "falabella", "ripley", "aliexpress",
                                            "amazon", "temu", "yapo", "login", "iniciar sesion"]),
    "usados": ("Usados", ["usado", "usados", "usada", "usadas", "segunda mano", "remate"]),
}
# semillas que chocan con servicios de verdad («trabajos de poda», «contratar freelance», «bird free»): junto a una
# palabra de lo que el dueño vende nunca bastan solas
SEMILLAS_DEBILES = {"trabajo", "trabajos", "freelance", "free"}
# «gratis» que es de comprador: no se propone
GRATIS_COMPRADOR = {"cotizacion", "evaluacion", "despacho", "envio", "diagnostico", "presupuesto", "visita",
                    "asesoria", "prueba", "demo", "instalacion", "retiro", "inspeccion"}


def semillas_de(u):
    """categorías cuya semilla aparece en la búsqueda, con frontera de palabra (temu ≠ temuco)"""
    out = {}
    tk = u["toks"]
    for cat, (_, semillas) in SEMILLAS.items():
        for s in semillas:
            st = tuple(s.split())
            if contiene(tk, st):
                if cat == "gratis" and any(w in GRATIS_COMPRADOR for w in tk):
                    continue
                out.setdefault(cat, []).append(s)
    if len(tk) >= 2 and "como" in tk:
        i = tk.index("como")
        if i + 1 < len(tk) and re.search(r"(ar|er|ir)$", tk[i + 1]) and tk[i + 1] not in ("cotizar", "contratar",
                                                                                           "comprar", "elegir"):
            out.setdefault("hazlo_tu_mismo", []).append("como " + tk[i + 1])
    return out


def temas(inf, us=None):
    """Temas fijos (determinísticos): grupos de anuncios por costo + categorías-semilla con costo.
    Sin columna de grupo: con ≤ 8 búsquedas con costo, cada una es un tema; si no, las palabras que más cuestan."""
    us = us or unicos(inf)
    con_costo = [u for u in us if u["costo"] > 0]
    out = []
    if "grupo" in inf["columnas"]:
        g = {}
        for t in inf["terminos"]:
            e = g.setdefault(t["gkey"] or "(sin grupo)", {"costo": 0, "conv": 0, "clics": 0})
            e["costo"] += t["costo"] or 0
            e["conv"] += t["conv"] or 0
            e["clics"] += t["clics"] or 0
        orden = sorted((k for k in g if g[k]["costo"] > 0), key=lambda k: (-g[k]["costo"], k))
        for k in orden:
            out.append({"nombre": k, "regla": {"grupo": k}})
    elif len(con_costo) <= 8:
        for u in con_costo:
            out.append({"nombre": u["texto"], "regla": {"termino": u["n"]}})
    else:
        restantes = list(con_costo)
        while restantes and len(out) < 6:
            peso = {}
            for u in restantes:
                for w in set(u["toks"]):
                    if w not in STOP and w not in COMPRADOR and len(w) > 2:
                        peso[w] = peso.get(w, 0) + u["costo"]
            if not peso:
                break
            w = sorted(peso, key=lambda x: (-peso[x], x))[0]
            out.append({"nombre": w, "regla": {"contiene": [w]}})
            restantes = [u for u in restantes if w not in u["toks"]]
    cats = {}
    for u in con_costo:
        for cat, ss in semillas_de(u).items():
            e = cats.setdefault(cat, [])
            for s in ss:
                if s not in e:
                    e.append(s)
    for cat in sorted(cats, key=lambda c: -sum(u["costo"] for u in con_costo if c in semillas_de(u))):
        out.append({"nombre": SEMILLAS[cat][0] if cat in SEMILLAS else cat, "regla": {"contiene": cats[cat]},
                    "categoria": cat})
    letras = "abcdefghijklmnopqrstuvwxyz"
    for i, tm in enumerate(out):
        tm["id"] = letras[i] if i < 26 else f"t{i}"
        tm["miembros"] = [u for u in us if cumple(u, tm["regla"])]
    return out


def cumple(u, regla):
    if "grupo" in regla:
        return regla["grupo"] in u["grupos"] or (regla["grupo"] == "(sin grupo)" and not u["grupos"])
    if "termino" in regla:
        return u["n"] == regla["termino"]
    if "contiene" in regla:
        return any(contiene(u["toks"], tuple(v.split())) for w in regla["contiene"] for v in variantes(w))
    return False


def filas_tema(inf, regla):
    """las filas del informe que caen en el tema (por grupo: sólo las de ese grupo)"""
    if "grupo" in regla:
        return [t for t in inf["terminos"] if (t["gkey"] or "(sin grupo)") == regla["grupo"]]
    if "termino" in regla:
        return [t for t in inf["terminos"] if t["n"] == regla["termino"]]
    return [t for t in inf["terminos"] if any(contiene(t["toks"], tuple(v.split())) for w in regla.get("contiene", [])
                                              for v in variantes(w))]


def fmt_regla(r):
    if "grupo" in r:
        return f"grupo «{r['grupo']}»"
    if "termino" in r:
        return "sólo esa fila"
    return "contiene " + " / ".join(f"«{w}»" for w in r["contiene"])

# ───────────────────────────── cobertura, medición ─────────────────────────────


def cobertura(inf):
    visible = suma(inf["terminos"], "costo")
    cuenta = _total(inf, "cuenta", "account")
    busq = _total(inf, "busqueda", "search")
    out = {"visible": visible, "cuenta": cuenta["costo"] if cuenta else None, "solo_busqueda": None, "pct": None}
    out["excede"] = False
    if cuenta and cuenta.get("costo"):
        out["pct"] = 100 * visible / cuenta["costo"]
        if out["pct"] > 100.5:      # suma más que la cuenta: filas repetidas o dos informes pegados
            out["pct"], out["excede"] = None, True
        if busq and busq.get("costo") is not None:
            out["solo_busqueda"] = abs(busq["costo"] - cuenta["costo"]) < 1
    return out


def _conv_total(inf, k):
    """(valor, fuente) de una columna de conversión; None si la columna falta o no trae ningún dato"""
    if k not in inf["columnas"]:
        return None, None
    cuenta = _total(inf, "cuenta", "account")
    if cuenta and cuenta.get(k) is not None:
        return cuenta[k], "fila «Total: Cuenta»"
    if any(t.get(k) is None for t in inf["terminos"]):      # una suma con huecos no es un total
        return None, None
    return sum(t[k] for t in inf["terminos"]), "suma de los términos"


def medicion(inf):
    c, fc = _conv_total(inf, "conv")
    a, fa = _conv_total(inf, "todas")
    out = {"conv": c, "todas": a, "estado": "falta «Todas las conv.»", "factor": None, "fuente": fc or fa or "—"}
    if c is None and a is None:
        out["estado"] = "sin columnas de conversión con datos: no puedo medir"
    elif c is None:
        out["estado"] = "falta «Conversiones»"
    elif a is not None:
        if max(c, a) == 0:
            out["estado"] = "ninguna conversión"
        elif min(c, a) == 0:
            out["estado"], out["factor"] = "una de las columnas en cero", math.inf
        else:
            f = max(c, a) / min(c, a)
            out["factor"] = f
            out["estado"] = "iguales" if f < 1.05 else f"divergen {fnum(f, 1)}×"
    return out

# ───────────────────────────── detector de marca y nombres ─────────────────────────────


def detector_marca(inf, us, excluir=()):
    """candidatos a marca por CTR; nunca palabras de los nombres de grupo o campaña ni los lugares ya anotados"""
    if "impr" not in inf["columnas"]:
        return None
    fuera = {f for t in inf["terminos"] for x in (t["grupo"], t["campana"]) for w in toks(x) for f in formas(w)} | \
        {f for x in excluir for w in toks(x) for f in formas(w)}
    filas = [u for u in us if u["impr"]]
    impr, clics = suma(filas, "impr"), suma(filas, "clics")
    if not impr:
        return []
    ctr = clics / impr
    for factor in (2.5,):       # a 1,5× trae las palabras de la categoría («agencias», «redes»): ruido, no marca
        tok = {}
        for u in filas:
            for w in set(u["toks"]):
                if len(w) >= 4 and w not in STOP and w not in COMPRADOR and w not in fuera:
                    e = tok.setdefault(w, [0, 0, 0, 0.0])
                    e[0] += 1
                    e[1] += u["impr"]
                    e[2] += u["clics"]
                    e[3] += u["costo"]
        cands = [(w, e) for w, e in tok.items() if e[0] >= 2 and e[1] >= 20 and ctr and e[2] / e[1] >= factor * ctr]
        if cands:
            cands.sort(key=lambda x: -x[1][3])
            return [{"token": w, "ctr_x": (e[2] / e[1]) / ctr, "costo": e[3], "terminos": e[0]} for w, e in cands[:10]]
    return []


def leer_nombres(path):
    lugares, nombres = [], []
    if not Path(path).exists():
        return lugares, nombres
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip().strip("-•*").strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"(?i)lugar\s*:\s*(.+)", ln)
        (lugares if m else nombres).append((m[1] if m else ln).strip().strip("«»\"'"))
    return lugares, nombres


def cifras_de(us, frase):
    ft = toks(frase)
    ms = [u for u in us if contiene(u["toks"], ft)]
    return {"frase": frase, "terminos": len(ms), "costo": suma(ms, "costo"), "clics": suma(ms, "clics"),
            "conv": suma(ms, "conv"), "cmax": sum(u["cmax"] for u in ms), "miembros": ms}

# ───────────────────────────── turno 1 ─────────────────────────────


def resumen(inf, us):
    con_costo = [u for u in us if u["costo"] > 0]
    cob, med = cobertura(inf), medicion(inf)
    L = []
    tipo = "Informe de palabras clave" if inf["tipo"] == "palabras_clave" else "Informe de términos de búsqueda"
    per = inf["periodo"] or "período no indicado"
    dias = f" ({inf['dias']} días)" if inf["dias"] and "días" not in per else ""
    nombre_u = "palabras clave" if inf["tipo"] == "palabras_clave" else "términos"
    filas_n = f"; {len(inf['terminos'])} filas" if len(inf["terminos"]) != len(us) else ""
    de = f" (de {len(us)} distintos{filas_n})" if len(us) != len(con_costo) else ""
    L.append(f"- {tipo} · {per}{dias} · {len(con_costo)} {nombre_u} con costo{de} · "
             f"{fnum(suma(inf['terminos'], 'clics'))} clics · {fmoney(cob['visible'])} · "
             f"{fconv(suma(inf['terminos'], 'conv'))}")
    faltan = []
    if "grupo" not in inf["columnas"]:
        faltan.append("Grupo de anuncios → no puedo revisar la salud de cada grupo")
    if "concordancia" not in inf["columnas"] and inf["tipo"] == "terminos":
        faltan.append("Tipo de concordancia → no puedo comparar concordancias")
    if "todas" not in inf["columnas"]:
        faltan.append("Todas las conv. → no sé si tu columna de conversión mide lo que cierra")
    if "valor" not in inf["columnas"]:
        faltan.append("Valor de conversión → cuento conversiones, no pesos")
    if "impr" not in inf["columnas"]:
        faltan.append("Impresiones → no corre el detector de marca")
    if "conv" not in inf["columnas"]:
        faltan.insert(0, "Conversiones → sin ella no juzgo rendimiento ni puedo probar que una búsqueda no convirtió")
    if faltan:
        L.append("- Columnas que faltan: " + " · ".join(faltan))
    if inf.get("desfasadas"):
        L.append(f"- Ojo: {inf['desfasadas']} fila(s) con las columnas corridas (¿coma decimal sin comillas?): no leí "
                 "sus cifras, no están en ningún total y ninguna negativa las toca. Descarga el informe de nuevo sin "
                 "abrirlo en Excel.")
    if inf.get("duplicadas"):
        L.append(f"- Ojo: {inf['duplicadas']} filas repetidas (misma búsqueda, campaña, grupo y concordancia). "
                 "¿Pegaste dos informes? Las sumé tal como vienen.")
    if cob.get("excede"):
        L.append(f"- Cobertura: NO la calculo: los términos suman {fmoney(cob['visible'])}, más que la fila «Total: "
                 f"Cuenta» ({fmoney(cob['cuenta'])}). ¿Filas repetidas o dos informes pegados? Revisa el archivo.")
    elif cob["pct"] is not None:
        extra = " «Total: Cuenta» es igual a «Total: Búsqueda»: el informe está limitado a Búsqueda." \
            if cob["solo_busqueda"] else ""
        L.append(f"- Cobertura: este archivo ve el {fpct(cob['pct'])} del costo de la cuenta "
                 f"({fmoney(cob['visible'])} de {fmoney(cob['cuenta'])}, fila «Total: Cuenta»).{extra}")
    else:
        L.append("- Cobertura: desconocida (el archivo no trae la fila «Total: Cuenta»); no sé cuánto de tu gasto "
                 "queda fuera de este informe.")
    if med["conv"] is None or med["todas"] is None:
        L.append(f"- Medición: «Conversiones» {fnum(med['conv'])} · «Todas las conv.» {fnum(med['todas'])} → "
                 f"{med['estado']}")
    else:
        L.append(f"- Medición: «Conversiones» {fnum(med['conv'])} · «Todas las conv.» {fnum(med['todas'])} "
                 f"→ {med['estado']} ({med['fuente']})")
    return L


def cmd_leer(inf, args):
    us = unicos(inf)
    print(f"auditor.py {VERSION} · {inf['encoding']} · separador: {inf['delim']} · números: {inf['locale']}")
    print("\n".join(resumen(inf, us)))
    G = geo_de(args)
    if G:
        print(resumen_geo(G))
    tm = temas(inf, us)
    print("\nTemas (fijos; el turno 2 usa las mismas reglas):")
    for t in tm:
        fs = filas_tema(inf, t["regla"])
        print(f"  {t['id']}) {t['nombre']} [{fmt_regla(t['regla'])}] · {len(t['miembros'])} búsquedas · "
              f"{fmoney(suma(fs, 'costo'))} · {fconv(suma(fs, 'conv'))}")
    dm = detector_marca(inf, us)
    if dm:
        print("\nDetector de marca (candidatos, no decide): " +
              " · ".join(f"«{d['token']}» CTR {fnum(d['ctr_x'], 1)}× la cuenta" for d in dm))
    con_costo = [u for u in us if u["costo"] > 0]
    total = suma(con_costo, "costo") or 1
    acum, lista = 0, []
    for u in con_costo:
        if len(con_costo) > 400 and (acum / total >= 0.95 or len(lista) >= 400):
            break
        lista.append(u)
        acum += u["costo"]
    print(f"\nBúsquedas con costo para encontrar NOMBRES PROPIOS ({len(lista)} de {len(con_costo)}, "
          f"{fpct(100 * acum / total)} del costo):")
    for u in lista:
        print(f"  {u['texto']}")
    print("\nSiguiente paso: escribe en nombres.txt cada nombre propio que aparece arriba —empresa, marca, persona, "
          "herramienta o producto de otra empresa— uno por línea, tal como aparece en la búsqueda; los lugares, "
          "con «lugar: » delante. Después: python3 auditor.py turno1 " + Path(inf["archivo"]).name)


def cmd_turno1(inf, args):
    us = unicos(inf)
    lugares, nombres = leer_nombres(args.get("nombres", "nombres.txt"))
    G = geo_de(args)
    L = ["**Lo que leí en tu archivo**"] + resumen(inf, us) + ([resumen_geo(G)] if G else [])
    L += ["", "**Antes de auditar, necesito tu contexto** (una línea por pregunta basta)", ""]
    zona = ""
    if G and lugares_top(G):
        zona = " En tu informe de ubicaciones aparecen con costo: " + ", ".join(
            f"{k} ({fmoney(v)})" for k, v in lugares_top(G)) + ": dime dónde atiendes de verdad."
    elif lugares:
        cs = [cifras_de(us, ln) for ln in lugares]
        cs = [c for c in cs if c["costo"] > 0]
        if cs:
            zona = " En el archivo aparecen con costo: " + ", ".join(
                f"{c['frase']} ({fmoney(c['costo'])})" for c in sorted(cs, key=lambda c: -c["costo"])) + \
                ": dime cuáles son tuyas de verdad."
    L.append("**P1 — negocio y zona.** En una frase, como lo diría tu cliente: ¿qué vendes, a quién y en qué "
             "comunas, ciudades o países atiendes de verdad? ¿Qué NO vendes, pero te confunden con eso?" + zona)
    L += ["", "**P1b — tu servicio principal.** Marca cada tema: 1 = servicio principal · 2 = lo vendo, pero es "
          "secundario · 3 = no lo vendo. Si un tema mezcla cosas, pártelo (por ejemplo: «c) X 3, lo demás 2»)."]
    for t in temas(inf, us):
        fs = sorted((f for f in filas_tema(inf, t["regla"]) if (f["costo"] or 0) > 0),
                    key=lambda f: (-f["costo"], f["n"]))
        ms = [u for u in t["miembros"] if u["costo"] > 0]
        ej = " · ".join(f"«{f['texto']}» {fmoney(f['costo'])}" + (f" ({fconv(f['conv'])})" if f["conv"] else "")
                        for f in fs[:3])
        dentro = ""
        if t.get("categoria") and "grupo" in inf["columnas"]:
            gs = sorted({g for u in ms for g in u["grupos"]})
            dentro = f" (ya está dentro de {', '.join('«' + g + '»' for g in gs)}: no lo sumes aparte)" if gs else ""
        if "termino" in t["regla"]:
            L.append(f" {t['id']}) **{t['nombre']}** · {fmoney(suma(fs, 'costo'))} · {fclics(suma(fs, 'clics'))} · "
                     f"{fconv(suma(fs, 'conv'))} → 1 / 2 / 3")
            continue
        regla = "" if "grupo" in t["regla"] else f" [{fmt_regla(t['regla'])}]"
        L.append(f" {t['id']}) **{t['nombre']}**{regla}{dentro} — {ej} · total "
                 f"{fmoney(suma(fs, 'costo'))} · {fconv(suma(fs, 'conv'))} → 1 / 2 / 3")
    dm = detector_marca(inf, us, excluir=lugares)
    if dm:
        p2 = " Candidatos del archivo (CTR alto; puede ser tu marca, un competidor o una comuna): " + \
             ", ".join(f"«{d['token']}»" for d in dm[:5]) + "."
    elif dm is not None:
        p2 = " En el archivo no aparece ninguna búsqueda con el CTR típico de una marca."
    else:
        p2 = ""
    L += ["", f"**P2 — tu marca.** ¿Cómo se llama tu marca y cómo la escriben mal?{p2}"]
    propias = {w for t in inf["terminos"] for x in (t["grupo"], t["campana"]) for w in toks(x)}
    nombres = [n for n in nombres if not set(toks(n)) <= propias]
    cs = sorted((c for c in (cifras_de(us, n) for n in nombres) if c["costo"] > 0), key=lambda c: -c["costo"])
    if cs:
        L += ["", "**P3 — los nombres de tu archivo.** Para cada uno: (a) mi marca · (b) un competidor · (c) mi "
              "ciudad o comuna · (d) otro negocio, parecido, pero no competimos · (e) no sé qué es. Si es "
              "competidor: ¿quieres aparecer cuando lo buscan? sí / no / no sé"]
        for c in cs:
            L.append(f" - «{c['frase']}» · {fmoney(c['costo'])} · {fclics(c['clics'])} · {fconv(c['conv'])}")
    clics = suma(inf["terminos"], "clics")
    L += ["", f"**P4 — cómo se cierra la venta.** ¿Cómo llega el cliente que compra: formulario, WhatsApp, "
          f"teléfono, tienda o local, compra en la web? Tu archivo muestra {fnum(suma(inf['terminos'], 'conv'))} "
          f"conversiones en {fclics(clics)}: ¿se parece a los contactos o ventas reales que recibiste?",
          "", "**P5 (opcional).** ¿Cambiaste sitio, formulario, teléfono, WhatsApp o etiqueta de conversión en el "
          "período de este informe?",
          "", "**P6 (opcional).** ¿Cuánto puedes pagar por un cliente, o cuánto vale una venta promedio?",
          "", "Responde lo que sepas; lo que no sepas, dilo y sigo con eso. Si prefieres que audite sin tus "
          "respuestas, escribe «sigue sin mis respuestas» y declaro los supuestos."]
    print("===== MENSAJE PARA EL DUEÑO: cópialo entero, de la línea siguiente a la marca de fin =====")
    print("\n".join(L))
    print("===== FIN DEL MENSAJE =====")

# ───────────────────────────── ficha ─────────────────────────────


def _lit(s):
    return " ".join(norm(s).split())


def cargar_ficha(inf, args, estricta=True):
    """Valida ficha.json. Todo texto tiene que ser un trozo literal de respuestas.txt; toda decisión (el número de
    un tema, un competidor, otro negocio) lleva la frase del dueño que la sostiene."""
    fp = Path(args.get("ficha", "ficha.json"))
    if not fp.exists():
        raise SystemExit("ERROR: falta ficha.json (ver el formato en el SKILL.md).")
    try:
        fi = json.loads(fp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: ficha.json no es JSON válido: {e}")
    rp = Path(args.get("respuestas", "respuestas.txt"))
    resp = _lit(rp.read_text(encoding="utf-8")) if rp.exists() else ""
    sin_resp = bool(fi.get("sin_respuestas"))
    errores = []
    # estructura (siempre)
    ids = {t["id"] for t in temas(inf)}
    en_archivo = lambda x: any(contiene(t["toks"], toks(x)) for t in inf["terminos"])  # noqa: E731
    for t in fi.get("temas", []):
        if t.get("id") not in ids:
            errores.append(f"temas: el id «{t.get('id')}» no existe (temas: {', '.join(sorted(ids))})")
        if t.get("valor") not in (1, 2, 3, None):
            errores.append(f"temas.{t.get('id')}: valor debe ser 1, 2, 3 o null (sin respuesta)")
        for p in t.get("partes", []):
            if p.get("valor") not in (1, 2, 3):
                errores.append(f"temas.{t.get('id')}.partes: valor debe ser 1, 2 o 3")
    for n in fi.get("nombres", []):
        if n.get("tipo") not in ("a", "b", "c", "d", "e"):
            errores.append(f"nombres «{n.get('nombre')}»: tipo debe ser a, b, c, d o e")
        if n.get("aparecer") not in (None, "si", "no", "no_se"):
            errores.append(f"nombres «{n.get('nombre')}»: aparecer debe ser si, no, no_se o null")
        if not en_archivo(n.get("nombre", "")):
            errores.append(f"nombres: «{n.get('nombre')}» no aparece en ninguna búsqueda del archivo")
    if sin_resp:
        if any(t.get("valor") is not None or t.get("partes") for t in fi.get("temas", [])) or fi.get("nombres") \
                or fi.get("no_vende"):
            errores.append("sin respuestas del dueño no hay temas marcados, nombres, zonas ni «no vende»: déjalos "
                           "vacíos (el programa protege todo y entrega candidatas)")
    else:
        if not resp:
            errores.append("falta respuestas.txt con la respuesta del dueño, copiada tal cual")

        def chk(campo, s_, obligatorio=False, debe_nombrar=()):
            q = _lit(s_ or "")
            if obligatorio and len(q.split()) < 2:
                errores.append(f"{campo}: falta la frase del dueño que lo sostiene (cópiala literal, completa)")
            elif q and f" {q} " not in f" {resp} ":
                errores.append(f"{campo}: «{s_}» no está en las palabras del dueño (cópialo literal o déjalo vacío)")
            elif q and debe_nombrar and not any(set(toks(x)) & set(q.split()) - STOP - GENERICO_GRUPO
                                                for x in debe_nombrar[:1] if x) and not (
                    len(debe_nombrar) > 1
                    and re.search(rf"(?i)(^|[^\w]){re.escape(debe_nombrar[1])}\s*([\):=→-]|\s[123]\b)", s_ or "")):
                errores.append(f"{campo}: la frase «{s_}» no nombra a «{debe_nombrar[0]}»: copia la frase donde el "
                               "dueño habla de eso")
        for c in ("negocio", "zona", "cierre", "cpa", "cambios"):
            chk(c, fi.get(c, ""))
        for m in fi.get("marca", []):
            chk("marca", m)
        tms = {t["id"]: t for t in temas(inf)}
        for t in fi.get("temas", []):
            base = tms.get(t.get("id"), {"nombre": ""})
            con_valor = t.get("valor") is not None
            chk(f"temas.{t.get('id')}.palabras_del_dueno", t.get("palabras_del_dueno", ""),
                obligatorio=con_valor, debe_nombrar=(base["nombre"], t.get("id", "")) if con_valor else ())
            for p in t.get("partes", []):
                chk(f"temas.{t.get('id')}.partes.palabras_del_dueno", p.get("palabras_del_dueno", ""), obligatorio=True)
        for nv in fi.get("no_vende", []):
            chk("no_vende", nv.get("texto", ""), obligatorio=True)
        for n in fi.get("nombres", []):
            qn = " " + _lit(n.get("palabras_del_dueno", "")) + " "
            duda_txt = re.search(r" no (lo )?se | ni idea | no conozco | no se quien", qn)
            if n.get("aparecer") == "no" and (not set(qn.split()) & NEGACION or duda_txt):
                errores.append(f"nombres «{n.get('nombre')}»: «aparecer: no» exige una frase del dueño que lo diga "
                               "(«no quiero aparecer…»); si dijo «no sé», va aparecer: no_se")
            if n.get("tipo") in ("b", "d") and duda_txt and not re.search(r" competencia | competidor", qn):
                errores.append(f"nombres «{n.get('nombre')}»: la frase del dueño dice que no sabe qué es: va tipo e")
            chk(f"nombres «{n.get('nombre')}».palabras_del_dueno", n.get("palabras_del_dueno", ""),
                obligatorio=n.get("tipo") in ("b", "d") or n.get("aparecer") == "no",
                debe_nombrar=(n.get("nombre", ""),))
    if not sin_resp and rp.exists():
        errores += no_vende_sin_regla(inf, fi, rp.read_text(encoding="utf-8"))
        errores += si_vende_sin_parte(fi, rp.read_text(encoding="utf-8"))
        errores += valor_de_tema_partido(fi, {t["id"]: t for t in temas(inf)})
    if errores and estricta:
        raise SystemExit("ERROR en ficha.json:\n  - " + "\n  - ".join(errores))
    return fi


RX_NO_VENDE = re.compile(r"\b(?:no|ni|tampoco)\s+(?:vendemos|vendo|hacemos|hago|ofrecemos|ofrezco|damos|doy|"
                         r"trabajamos(?:\s+con)?|trabajo(?:\s+con)?)\s+([^.,;:()«»\"\n]{3,80})", re.I)


RX_SI_VENDE = re.compile(r"([^.;:·\n]{3,90}?)\s+s[ií]\s+(?:la|lo|las|los)?\s*(?:vendemos|vendo|hacemos|hago|"
                         r"ofrecemos|ofrezco)\b", re.I)


RX_RESTO = re.compile(r"\b(?:lo|los|las|todo lo|todos los|todas las) (?:demas|otro|otros|otras)\b|\bel resto\b")


def valor_de_tema_partido(fi, tms):
    """Tema con partes: su `valor` es lo que el dueño dijo del RESTO del tema. La frase tiene que decirlo («lo demás 2»,
    «c) 2, menos email»); si sólo habla de una parte, el valor es null (eval6: «la automatización… sí la vendemos (2)»
    subió a 2 el tema entero y protegió «funnel marketing», que el dueño no había contestado)."""
    out = []
    for t in fi.get("temas", []):
        if not t.get("partes") or t.get("valor") is None:
            continue
        q = _lit(t.get("palabras_del_dueno", ""))
        de_partes = {w for p_ in t["partes"] for x in p_.get("contiene", []) for w in toks(x)}
        rotulos = ({w for w in toks(tms.get(t.get("id"), {}).get("nombre", ""))} - STOP - GENERICO_GRUPO - de_partes) \
            | {norm(t.get("id", ""))}
        ws = q.split()
        dice_el_tema = any(w in rotulos and ws[i + 1] == str(t["valor"]) for i, w in enumerate(ws[:-1]))
        if not (RX_RESTO.search(q) or dice_el_tema):
            out.append(f"temas.{t.get('id')}: tiene partes y valor {t['valor']}, pero «{t.get('palabras_del_dueno', '')}» "
                       "habla de una parte, no del resto del tema. Si el dueño no dijo qué pasa con el resto («lo demás "
                       "2», «c) 2, menos email»), el valor del tema es null: el programa deja el resto en duda.")
    return out


def si_vende_sin_parte(fi, respuestas):
    """«X sí la vendemos» dentro de un tema partido tiene que quedar como parte vendida (1 o 2) en la ficha (eval5: la
    parte «automatización con chatbots… sí la vendemos» se perdió y el programa no lo notó). La frase de un tema que
    ya tiene partes no la cubre: en ese tema, lo que se vende por separado es una parte (eval6)."""
    citas = [_lit(t.get("palabras_del_dueno", "")) for t in fi.get("temas", [])
             if t.get("valor") in (1, 2) and not t.get("partes")]
    citas += [_lit(p_.get("palabras_del_dueno", "")) for t in fi.get("temas", []) for p_ in t.get("partes", [])
              if p_.get("valor") in (1, 2)]
    out = []
    for m in RX_SI_VENDE.finditer(respuestas):
        x = _lit(m.group(1))
        nucleo = {w for w in x.split() if w not in STOP}
        if not nucleo or any(nucleo <= set(c.split()) for c in citas if c):
            continue
        frase = m.group(0).strip()
        out.append(f"el dueño dijo «{frase}» y la ficha no lo recoge: va como parte (valor 1 o 2) del tema donde lo "
                   f'dijo, {{"contiene": ["<palabras con que se busca>"], "valor": 2, '
                   f'"palabras_del_dueno": "{frase}"}}')
    return out


def no_vende_sin_regla(inf, fi, respuestas):
    """«no vendemos X» dicho por el dueño tiene que quedar en la ficha: en «no vende» o en una regla marcada 3.
    Si no, esas búsquedas terminan protegidas como si las vendiera (eval 27-set: «community manager»)."""
    R = reglas_de_ficha(inf, fi)
    textos_nv = [norm(nv.get("texto", "")) for nv in fi.get("no_vende", [])]
    out = []
    verbos = r"(vendemos|vendo|hacemos|hago|ofrecemos|ofrezco|damos|doy|trabajamos|trabajo)"
    texto = re.sub(rf"(?i)\s+(?:ni|y tampoco)\s+{verbos}\b", r". no \1", respuestas)   # «…ni vendemos X» = otra frase
    for m in RX_NO_VENDE.finditer(texto):
        resto = re.split(r"\s(?:ni|y|o|pero|sino|que|porque|aunque|si)\s", " " + norm(m.group(1)) + " ")[0]
        x = " ".join([w for w in resto.split() if w not in STOP][:4])
        if not x or x in ("eso", "esto", "nada", "mas"):
            continue
        prueba = {"n": x, "toks": tuple(x.split()), "grupos": []}
        en_texto = any(x in t for t in textos_nv)
        en_regla = any(v == 3 and "grupo" not in r and cumple(prueba, r) for r, v, _, _ in R)
        if not (en_texto or en_regla):
            # la frase sugerida sale del texto ORIGINAL del dueño (literal), no del texto preparado
            orig = re.search(rf"(?i)\b(?:no|ni|tampoco)\s+{verbos}\s+{re.escape(m.group(1).strip())}", respuestas)
            frase = (orig.group(0) if orig else m.group(0)).strip()
            out.append(f"el dueño dijo «{frase}» y la ficha no lo recoge: agrega a no_vende "
                       f'{{"texto": "{frase}", "contiene": ["<palabras con que se busca {x}>"]}}')
    return out


def render_ficha(inf, fi):
    tm = {t["id"]: t for t in temas(inf)}
    hoy = date.today().isoformat()
    L = [f"FICHA DEL NEGOCIO — {hoy} (auditor-google-ads {VERSION})"]
    if fi.get("sin_respuestas"):
        L.append("Sin respuestas del dueño: todo lo de abajo es supuesto.")
    L.append(f"Negocio (P1): {fi.get('negocio') or 'no declarado'}")
    L.append(f"Zona (P1): {fi.get('zona') or 'no declarada'}")
    L.append("Temas (P1b):")
    supuestos = list(fi.get("supuestos", []))
    no_vende = []
    for t in fi.get("temas", []):
        base = tm.get(t["id"])
        if not base:
            continue
        v = t.get("valor")
        nota = f" «{t['palabras_del_dueno']}»" if t.get("palabras_del_dueno") else ""
        L.append(f"  {t['id']}) {base['nombre']} [{fmt_regla(base['regla'])}] → {v if v else 'sin respuesta'}{nota}")
        if v == 3:
            no_vende.append(base["nombre"])
        for p in t.get("partes", []):
            L.append(f"     parte «{p.get('palabras_del_dueno', '')}» [contiene "
                     f"{' / '.join('«' + w + '»' for w in p.get('contiene', []))}] → {p['valor']}")
            if p["valor"] == 3:
                no_vende.append(p.get("palabras_del_dueno") or "/".join(p.get("contiene", [])))
            lit = _lit(p.get("palabras_del_dueno", ""))
            extra = [w for w in p.get("contiene", []) if _lit(w) not in lit]
            if extra:
                supuestos.append(f"cuento {' y '.join('«' + w + '»' for w in extra)} como parte de "
                                 f"«{p.get('palabras_del_dueno', '')}»")
    for nv in fi.get("no_vende", []):
        no_vende.append(nv["texto"])
        extra = [w for w in nv.get("contiene", []) if _lit(w) not in _lit(nv["texto"])]
        if extra:
            supuestos.append(f"cuento {' y '.join('«' + w + '»' for w in extra)} como «{nv['texto']}»")
    L.append("No vende: " + (" · ".join(dict.fromkeys(no_vende)) if no_vende else "nada declarado"))
    L.append("Marca y variantes (P2): " + (" · ".join(fi.get("marca", [])) or "no declarada"))
    if fi.get("nombres"):
        tipos = {"a": "mi marca", "b": "competidor", "c": "mi ciudad o comuna", "d": "otro negocio", "e": "no sé"}
        L.append("Nombres (P3): " + " · ".join(
            f"«{n.get('nombre')}» → {tipos.get(n.get('tipo'), '?')}"
            + (f", ¿aparecer? {n['aparecer'].replace('_', ' ')}" if n.get("tipo") == "b" and n.get("aparecer") else "")
            for n in fi["nombres"]))
    L.append(f"Cómo se cierra la venta (P4): {fi.get('cierre') or 'no declarado'}")
    L.append(f"CPA o ticket (P6): {fi.get('cpa') or 'no declarado'}")
    L.append("Supuestos (míos, no del dueño): " + ("; ".join(dict.fromkeys(supuestos)) if supuestos else "ninguno"))
    return "\n".join(L)


def cmd_ficha(inf, args):
    fi = cargar_ficha(inf, args)
    print("ficha.json: OK (cada texto es literal del dueño)\n")
    print(render_ficha(inf, fi))

# ───────────────────────────── estado de cada búsqueda ─────────────────────────────


ETIQUETAS = ("nucleo", "secundario", "marca", "competidor", "empleo", "gratis", "formacion", "hazlo_tu_mismo",
             "otra_zona", "otro_negocio", "tercero", "no_se")
AJENAS = ("empleo", "gratis", "formacion", "hazlo_tu_mismo", "otra_zona", "otro_negocio", "tercero")
LISTA = {"empleo": "Empleo", "gratis": "Gratis", "formacion": "Formación", "hazlo_tu_mismo": "Hazlo tú mismo",
         "otra_zona": "Otras zonas", "otro_negocio": "Otros negocios", "tercero": "Herramientas y plataformas de "
         "terceros", "competidor": "Competidores", "usados": "Otros negocios"}


def reglas_de_ficha(inf, fi):
    """(regla, valor, fuente, es_de_palabra) de la ficha: las de palabra son más específicas que las de grupo."""
    tm = {t["id"]: t for t in temas(inf)}
    R = []
    for t in fi.get("temas", []):
        base = tm.get(t.get("id"))
        if not base:
            continue
        if t.get("valor") in (1, 2, 3):
            R.append((base["regla"], t["valor"], f"tema {t['id']}", "grupo" not in base["regla"]))
        for p in t.get("partes", []):
            if p.get("contiene"):
                R.append(({"contiene": p["contiene"]}, p["valor"], f"tema {t['id']} (parte)", True))
    for nv in fi.get("no_vende", []):
        ws = nv.get("contiene") or [nv["texto"]]
        R.append(({"contiene": ws}, 3, "no vende (P1)", True))
    return R


def formas(w):
    """singular y plural posibles de una palabra, sólo para PROTEGER (comparar de más aquí es seguro: deja una
    duda, no corta nada). dulce/dulces · tapiz/tapices · mueble/muebles · pais/paises"""
    f = {w, w + "s", w + "es"}
    if w.endswith("s"):
        f.add(w[:-1])
    if w.endswith("es"):
        f.add(w[:-2])
    if w.endswith("ces"):
        f.add(w[:-3] + "z")
    if w.endswith("z"):
        f.add(w[:-1] + "ces")
    return f


def palabra_regla_3(u, R):
    """la palabra de la regla «no lo vendo» del dueño que aparece en la búsqueda (para la negativa de frase)"""
    for r, v, _, de_pal in R:
        if v == 3 and de_pal and "contiene" in r:
            for w in r["contiene"]:
                if any(contiene(u["toks"], tuple(x.split())) for x in variantes(w)):
                    return w
    return ""


def palabras_protegidas(inf, fi):
    """raíces de las palabras que nombran lo que el dueño vende (temas 1 y 2) y su marca"""
    tm = {t["id"]: t for t in temas(inf)}
    fuentes = []
    if fi.get("sin_respuestas"):
        fuentes += [t["regla"]["grupo"] for t in tm.values() if "grupo" in t["regla"]]
    for t in fi.get("temas", []):
        base = tm.get(t.get("id"))
        if not base:
            continue
        if t.get("valor") in (1, 2):
            fuentes.append(base["regla"].get("grupo") or base["regla"].get("termino")
                           or " ".join(base["regla"].get("contiene", [])))
        for p in t.get("partes", []):
            if p.get("valor") in (1, 2):
                fuentes += list(p.get("contiene", []))
    P = {x for f in fuentes for w in toks(f) if w not in STOP and w not in GENERICO_GRUPO
         and w not in COMPRADOR and len(w) > 2 and not re.fullmatch(r"[a-z]{0,3}\d+", w) for x in formas(w)}
    return P | {x for m in fi.get("marca", []) for w in toks(m) if len(w) > 1 for x in formas(w)}


NEGACION = {"no", "ni", "tampoco", "nunca", "jamas"}


def frases_de_marca(fi):
    """la marca se reconoce por frase: la de P2 y los nombres que el dueño marcó (a) en P3"""
    fs = [toks(m) for m in fi.get("marca", [])] + [toks(n["nombre"]) for n in fi.get("nombres", [])
                                                   if n.get("tipo") == "a"]
    return [f for f in fs if f]


def leer_etiquetas(path, us):
    ids = {u["id"] for u in us}
    E = {}
    p = Path(path)
    if not p.exists():
        return E
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.lower().startswith("id"):
            continue
        partes = [x.strip() for x in re.split(r"[;\t|]", ln)]
        if len(partes) < 2 or partes[0] not in ids:
            continue
        et = norm(partes[1]).replace(" ", "_")
        et = {"no_sé": "no_se", "nose": "no_se", "diy": "hazlo_tu_mismo", "formación": "formacion"}.get(et, et)
        if et not in ETIQUETAS:
            et = "no_se"
        E[partes[0]] = {"etiqueta": et, "palabra": partes[2] if len(partes) > 2 else ""}
    return E


def leer_compra(path, us):
    ids = {u["id"] for u in us}
    C = {}
    p = Path(path)
    if not p.exists():
        return C
    for ln in p.read_text(encoding="utf-8").splitlines():
        partes = [x.strip() for x in re.split(r"[;\t|,]", ln.strip())]
        if len(partes) >= 2 and partes[0] in ids:
            v = norm(partes[1])
            C[partes[0]] = "s" if v in ("s", "si") else "n" if v in ("n", "no") else "?"
    return C


def estados(inf, fi, us, E, C):
    """Decide, búsqueda por búsqueda, qué se puede hacer con ella. La IA etiquetó; aquí manda la regla.
    Estados: protegido (tema 1, 2, marca o zona) · ajena (se puede cortar) · competidor · propuesta (parece ajena,
    falta el OK del dueño) · duda (pregunta) · neutro (sin etiqueta ni regla). Sólo «ajena» y el competidor con
    «no aparecer» pueden llegar a una negativa."""
    R = reglas_de_ficha(inf, fi)
    P = palabras_protegidas(inf, fi)
    marcas = frases_de_marca(fi)
    sin_resp = bool(fi.get("sin_respuestas"))
    nombres = [] if sin_resp else [n for n in fi.get("nombres", []) if n.get("tipo") != "a"]
    tm = {t["id"]: t for t in temas(inf)}
    # tema partido: si el dueño vende una parte y no dijo que vende «lo demás», lo que no cae en ninguna parte es duda
    partidos = [tm[t["id"]]["regla"] for t in fi.get("temas", []) if t.get("id") in tm and t.get("valor") in (None, 3)
                and any(p.get("valor") in (1, 2) for p in t.get("partes", []))]
    for u in us:
        e = E.get(u["id"], {})
        et, pal = e.get("etiqueta"), e.get("palabra", "")
        compra = C.get(u["id"])
        u.update(etiqueta=et, tema=None, categoria=None, palabra="", aparecer=None)
        vals_pal = {v for r, v, _, de_pal in R if de_pal and cumple(u, r)}
        vals_grp = {v for r, v, _, de_pal in R if not de_pal and cumple(u, r)}
        prot = sorted({w for w in u["toks"] if bool(formas(w) & P)})
        sem = semillas_de(u)

        def ajena(cat, palabra, motivo):
            u.update(estado="ajena", categoria=cat, palabra=palabra, motivo=motivo)

        def duda(motivo):
            u.update(estado="duda", motivo=motivo)
        if any(t.get("corrida") for t in u["filas"]):
            duda("fila con las columnas corridas: no sé sus cifras")
            continue
        # 0) la marca del dueño, por frase, antes que todo
        if any(contiene(u["toks"], m) for m in marcas):
            u.update(estado="protegido", tema="marca", motivo="tu marca")
            continue
        # 1) nombres que el dueño contestó en P3 (el más largo manda; si dos se contradicen, duda)
        noms = sorted((n for n in nombres if contiene(u["toks"], toks(n["nombre"]))),
                      key=lambda n: -len(toks(n["nombre"])))
        if noms:
            tipos = {(n["tipo"], n.get("aparecer")) for n in noms}
            nom = noms[0]
            nom_prot = sorted(set(toks(nom["nombre"])) & {w for w in u["toks"] if bool(formas(w) & P)})
            if len(tipos) > 1:
                duda("trae dos nombres con respuestas distintas: " + ", ".join(f"«{n['nombre']}»" for n in noms))
            elif nom_prot and et in ("nucleo", "secundario"):
                u.update(estado="protegido", tema={"nucleo": 1, "secundario": 2}[et],
                         motivo=f"trae {', '.join('«' + w + '»' for w in nom_prot)}, que es de lo que vendes")
            elif nom_prot and et in (None, "no_se"):
                duda(f"«{nom['nombre']}» trae una palabra de lo que vendes")
            elif nom["tipo"] == "c":
                u.update(estado="protegido", tema="zona", motivo="tu ciudad o comuna (P3)")
            elif nom["tipo"] in ("b", "d"):
                # la frase negativa es el NOMBRE, nunca una palabra de lo que el dueño vende («poliurea sika» → «sika»)
                limpio = lambda x: bool(x) and not any(formas(w) & P for w in toks(x))  # noqa: E731
                pal_n = next((x for x in (pal, nom["nombre"]) if limpio(x) and contiene(u["toks"], toks(x))), "")
                if nom["tipo"] == "d":
                    ajena("otro_negocio", pal_n, "otro negocio (P3)")
                else:
                    ap = nom.get("aparecer") or "no_se"
                    u.update(estado="competidor", aparecer=ap, palabra=pal_n, motivo=f"competidor, ¿aparecer? {ap}")
            else:
                duda(f"«{nom['nombre']}»: el dueño no sabe qué es")
            continue
        # 2) lo que dice la ficha: las reglas de palabra son más específicas que las de grupo
        en_partido = any(cumple(u, r) for r in partidos)
        if vals_pal and 3 in vals_pal and prot:
            duda(f"trae {', '.join('«' + w + '»' for w in prot)} (lo que vendes) y una palabra que marcaste 3")
            continue
        if len(vals_pal) > 1:
            duda("dos reglas de la ficha dicen cosas distintas")
            continue
        if vals_pal:
            valor = next(iter(vals_pal))
        elif en_partido:
            duda("el dueño partió su tema y esta búsqueda no cae en ninguna de las partes")
            continue
        elif len(vals_grp) == 1:
            valor = next(iter(vals_grp))
        elif sin_resp and u["grupos"]:
            valor = 2
        else:
            valor = None
        # 3) la etiqueta de la IA contra la regla y contra la 2.ª pregunta
        if et in ("nucleo", "secundario", "marca"):
            if valor == 3:
                duda("la IA la ve como tuya, pero la ficha dice que no la vendes")
            elif compra == "n" and et != "marca":
                duda("la IA la ve tuya, pero dijo que quien busca no te compraría")
            elif compra == "?" and et != "marca" and valor is None:
                duda("la IA la ve tuya, pero no sabe si quien busca te compraría")
            else:
                u.update(estado="protegido", tema=valor or {"nucleo": 1, "secundario": 2}.get(et, "marca"),
                         motivo="lo que vendes")
        elif et in AJENAS:
            # ajena de verdad = la dijo el dueño (regla 3), o la IA, la semilla y la 2.ª pregunta coinciden
            semilla_prot = any(bool(formas(w) & P) for s_ in sem.get(et, []) for w in s_.split())
            fuertes = [s_ for s_ in sem.get(et, []) if s_ not in SEMILLAS_DEBILES]
            # sin palabra de lo que vende: basta la semilla. Con ella, sólo empleo y gratis con semilla fuerte
            # («sueldo fumigador», «fumigación gratis»); «curso de gas» o «trabajos de poda» pueden ser el servicio
            universal = et in ("empleo", "gratis", "formacion") and et in sem and not semilla_prot \
                and not (vals_pal & {1, 2}) and (
                    (not prot and (bool(fuertes) or valor not in (1, 2)))
                    or (bool(prot) and et in ("empleo", "gratis") and bool(fuertes)))
            ambigua = bool(prot) and "freelance" in u["toks"]
            if compra == "s":
                duda(f"la IA la ve ajena ({et}), pero dijo que quien busca podría comprarte")
            elif valor == 3 and not prot:
                ajena(et, pal, et)
            elif universal and compra == "n" and not ambigua:
                ajena(et, pal, et)
            elif (prot or valor in (1, 2)) and et != "otra_zona":   # «fumigación temuco» trae el servicio: normal
                duda(f"la IA la ve ajena ({et}), pero toca lo que vendes"
                     + (f" ({', '.join('«' + w + '»' for w in prot)})" if prot else f" (tema {valor})"))
            else:
                u.update(estado="propuesta", categoria=et, palabra=pal,
                         motivo="parece de otra zona: ¿atiendes ahí?" if et == "otra_zona" else
                         f"parece {LISTA.get(et, et).lower()}, pero no lo marcaste como algo que no vendes")
        elif et == "competidor":
            u.update(estado="competidor", aparecer=None, palabra=pal, motivo="posible competidor sin respuesta")
        elif valor == 3 and not prot and compra != "s" and et in (None, "no_se"):
            # la respuesta del dueño manda sobre el «no sé» de la IA (eval3: «Empleo (freelance) → 3» se perdía)
            w3 = palabra_regla_3(u, R)
            cat = next((c for c, (_, ss) in SEMILLAS.items() if w3 and norm(w3) in ss and c in AJENAS), "otro_negocio")
            ajena(cat, w3, "la ficha dice que no lo vendes")
        elif et == "no_se":
            duda("la IA no supo clasificarla")
        elif valor in (1, 2) or prot:
            u.update(estado="protegido", tema=valor if valor in (1, 2) else 2, motivo="lo que vendes")
        else:
            u.update(estado="neutro", motivo="sin etiqueta ni regla")
    return us

# ───────────────────────────── negativas: simulación de daño ─────────────────────────────


def variantes(frase):
    w = norm(frase).split()
    if not w:
        return []
    ult, pre = w[-1], w[:-1]
    out = [" ".join(w)]
    if ult.endswith("es") and len(ult) > 4:
        out.append(" ".join(pre + [ult[:-2]]))
    elif ult.endswith("s") and len(ult) > 3:
        out.append(" ".join(pre + [ult[:-1]]))
    elif ult[-1] in "aeiou":
        out.append(" ".join(pre + [ult + "s"]))
    elif ult.endswith("z"):
        out.append(" ".join(pre + [ult[:-1] + "ces"]))
    elif re.search(r"[lrnd]$", ult) and not re.search(r"(ing|ment|ance|ence|er|ail)$", ult):
        out.append(" ".join(pre + [ult + "es"]))
    return list(dict.fromkeys(out))


def grafias(us, frase_norm):
    """cómo aparece escrita la frase en el archivo (con tilde, si la trae), más la forma sin tilde"""
    ft = frase_norm.split()
    out = []
    for u in us:
        orig = re.findall(r"[\w]+", u["texto"].lower())
        nt = [norm(x) for x in orig]
        for i in range(len(nt) - len(ft) + 1):
            if nt[i:i + len(ft)] == ft:
                out.append(" ".join(orig[i:i + len(ft)]))
    out.append(frase_norm)
    return list(dict.fromkeys(out))


def simular(us, frase, plural=True):
    vs = variantes(frase) if plural else [norm(frase)]
    hits = [u for u in us if any(contiene(u["toks"], tuple(v.split())) for v in vs)]
    return vs, hits


def bloquea_ok(u):
    """¿esta búsqueda puede quedar bloqueada por una negativa? Sólo lo ajeno confirmado, con cero conversiones
    conocidas (un «--» no es cero)."""
    cortable = u["estado"] == "ajena" or (u["estado"] == "competidor" and u.get("aparecer") == "no")
    return cortable and u["cmax"] == 0 and not u.get("conv_desc")


def negativas(inf, fi, us):
    """Arma las listas de negativas por irrelevancia. Toda frase pasa por la simulación de daño:
    si toca algo del dueño, algo en duda o algo que convirtió, la frase no va y baja a exacta."""
    kw = inf["tipo"] == "palabras_clave"
    sin_resp = bool(fi.get("sin_respuestas")) or not ({"conv", "todas"} & set(inf["columnas"]))
    ajenas = [u for u in us if u["estado"] == "ajena" or (u["estado"] == "competidor" and u.get("aparecer") == "no")]
    por_pal = {}
    for u in ajenas:
        pal = norm(u.get("palabra") or "")
        # Google: una negativa tiene como máximo 10 palabras y 80 caracteres
        if pal and (not contiene(u["toks"], tuple(pal.split())) or len(pal.split()) > 10 or len(pal) > 80):
            pal = ""
        u["_pal"] = pal
        if pal:
            por_pal.setdefault(pal, []).append(u)
    nombres_fijos = {norm(n["nombre"]) for n in fi.get("nombres", [])} | {
        pal for pal, ms in por_pal.items() if all(u["estado"] == "competidor" for u in ms)}
    listas, tocados, cubiertos = {}, {}, set()

    def lista_de(cats):
        cat = max(sorted(set(cats)), key=lambda c: cats.count(c))
        return listas.setdefault(LISTA.get(cat, "Otros negocios"), {"frases": [], "exactas": [], "sims": []})
    faltan = set()
    if not kw:
        for pal, miembros in sorted(por_pal.items(), key=lambda x: (-suma(x[1], "costo"), x[0])):
            vs, hits = simular(us, pal, plural=pal not in nombres_fijos)
            malos = [h for h in hits if not bloquea_ok(h)]
            sin_etq = [h for h in malos if h["estado"] == "neutro" and h["costo"] == 0 and not h.get("etiqueta")]
            faltan |= {h["id"] for h in sin_etq}
            Ld = lista_de([u.get("categoria") or "competidor" for u in miembros])
            Ld["sims"].append({"frase": pal, "variantes": vs, "hits": hits, "malos": malos})
            if not malos:
                gs = list(dict.fromkeys(g for v in vs for g in grafias(us, v)))
                Ld["frases"].append({"frase": pal, "grafias": gs, "hits": hits})
                cubiertos |= {h["id"] for h in hits}
            else:
                tocados.update({h["id"]: h for h in malos if h not in sin_etq})
    for u in sorted(ajenas, key=lambda u: -u["costo"]):
        if not bloquea_ok(u) or u["id"] in cubiertos or u["costo"] <= 0:
            continue
        # la exacta sale en cada grafía que trae el archivo: Google no junta «diseño» con «diseno»
        u["grafias_exactas"] = list(dict.fromkeys(t["texto"] for t in u["filas"]))
        lista_de([u.get("categoria") or "competidor"])["exactas"].append(u)
        cubiertos.add(u["id"])
    for nombre in list(listas):
        if not listas[nombre]["frases"] and not listas[nombre]["exactas"]:
            del listas[nombre]
    preguntas = [{"tipo": "convirtio", "u": u} for u in ajenas if u["cmax"] > 0]
    preguntas += [{"tipo": "sin_dato", "u": u} for u in ajenas if u["cmax"] == 0 and u.get("conv_desc")
                  and u["costo"] > 0]
    bloqueados = [u for u in us if u["id"] in cubiertos]
    return {"listas": listas, "bloqueados": bloqueados, "preguntas": preguntas, "tocados": tocados,
            "faltan_etiquetas": sorted(faltan), "solo_candidatas": sin_resp}


# ───────────────────────────── compuertas de rendimiento ─────────────────────────────


def compuertas(inf, fi, us):
    filas = inf["terminos"]
    clics, costo, conv = suma(filas, "clics"), suma(filas, "costo"), suma(filas, "conv")
    cvr_c = conv / clics if clics else 0
    cpa_c = costo / conv if conv else None
    cob, med = cobertura(inf), medicion(inf)
    out = {"cvr_cuenta": cvr_c, "cpa_cuenta": cpa_c, "grupos": [], "no_evaluable": [], "hallazgos": [],
           "g8": [], "g7": [], "gatillos": [], "rendimiento": True, "motivo_sin_rendimiento": []}
    cierre = norm(fi.get("cierre", ""))
    if med["conv"] is None:
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append("el archivo no trae datos de «Conversiones»")
    if med["estado"] == "ninguna conversión":
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append("no hay ninguna conversión configurada: el primer problema es la medición")
    if med["factor"] and med["factor"] >= 1.5:
        out["gatillos"].append(("medición", f"las dos columnas de conversión divergen {fnum(med['factor'], 1)}×"
                                if med["factor"] != math.inf else "una columna de conversión está en cero"))
    if clics and cvr_c < 0.005 and re.search(r"whatsapp|telefono|llamad|formulario|fono", cierre):
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append(f"CVR {fpct(100 * cvr_c)} con venta por teléfono, WhatsApp o "
                                             "formulario: la columna de conversión probablemente no mide lo que cierra")
        out["gatillos"].append(("medición", "portón de medición cerrado"))
    if inf["dias"] and inf["dias"] < 30:
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append(f"la ventana es de {inf['dias']} días (< 30)")
    if clics < 100:
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append(f"{fnum(clics)} clics en el período (< 100)")
    if cob["pct"] is not None and cob["pct"] < 25:
        out["rendimiento"] = False
        out["motivo_sin_rendimiento"].append(f"el archivo ve el {fpct(cob['pct'])} del costo de la cuenta (< 25 %)")
    # G5 — salud de cada grupo, con la CVR de la cuenta como vara
    muertos = set()
    if med["conv"] is None:
        out["no_evaluable"].append(("Salud de los grupos (G5)", "las conversiones del archivo están incompletas «--»",
                                    costo, "el informe con la columna «Conversiones» completa"))
    elif "grupo" in inf["columnas"]:
        G, sin_dato = {}, set()
        for t in filas:
            e = G.setdefault(t["gkey"], {"clics": 0, "costo": 0, "conv": 0, "valor": 0})
            for k in e:
                e[k] += t.get(k) or 0
            if t.get("conv") is None:
                sin_dato.add(t["gkey"])
        con_gasto = [g for g, e in G.items() if e["costo"] > 0]
        for g in sorted(con_gasto, key=lambda x: -G[x]["costo"]):
            e = G[g]
            # la menor de las dos: 100 clics baratos no esperan lo mismo que 100 clics caros
            esp = min(e["clics"] * cvr_c, e["costo"] / cpa_c) if cpa_c else e["clics"] * cvr_c
            if g in sin_dato:
                st = "sin muestra"      # con conversiones «--» no se puede decir que un grupo está muerto
            elif e["conv"] == 0 and esp >= 3:
                st = "MUERTO"
            elif e["conv"] < esp / 3 and esp >= 5:
                st = "ENFERMO"
            elif esp >= 3:
                st = "sano"
            else:
                st = "sin muestra"
            out["grupos"].append({"grupo": g, **e, "esperadas": esp, "estado": st})
            if st in ("MUERTO", "ENFERMO"):
                muertos.add(g)
                out["gatillos"].append(("G5", f"grupo «{g}» {st.lower()}: {fnum(esp)} conversiones esperadas, "
                                              f"{fnum(e['conv'])} observadas"))
        if len(con_gasto) < 2:
            out["no_evaluable"].append(("Salud de los grupos (G5)", "hace falta más de un grupo con gasto",
                                        costo, "el export con todos los grupos"))
    else:
        out["no_evaluable"].append(("Salud de los grupos (G5)", "falta la columna «Grupo de anuncios»", costo,
                                    "añadir «Grupo de anuncios» al export"))
    out["muertos"] = sorted(muertos)
    # G4 — línea base por término
    vivos = [t for t in filas if t["gkey"] not in muertos]
    ajenos = {u["n"] for u in us if u["estado"] == "ajena"}
    base_f = [t for t in vivos if t["n"] not in ajenos]
    Gc, Cc = {}, {}
    for t in base_f:
        for D, k in ((Gc, t["gkey"]), (Cc, t["campana"])):
            e = D.setdefault(k, [0, 0, 0])
            e[0] += t["clics"] or 0
            e[1] += t["costo"] or 0
            e[2] += t["conv"] or 0
    cvrs = [e[2] / e[0] for e in Gc.values() if e[0] >= 50]
    disp = (max(cvrs) / min(cvrs) if min(cvrs) > 0 else math.inf) if len(cvrs) >= 2 else None
    out["dispersion"] = disp
    cb = sum(e[0] for e in Gc.values())
    base_cuenta = (sum(e[2] for e in Gc.values()) / cb if cb else 0,
                   (sum(e[1] for e in Gc.values()) / sum(e[2] for e in Gc.values()))
                   if sum(e[2] for e in Gc.values()) else None)

    def base(u):
        t = u["filas"][0]
        if t["gkey"] and Gc.get(t["gkey"], [0])[0] >= 30:
            e = Gc[t["gkey"]]
            return e[2] / e[0], (e[1] / e[2] if e[2] else None), f"grupo «{t['gkey']}»"
        if t["campana"] and Cc.get(t["campana"], [0])[0] >= 100:
            e = Cc[t["campana"]]
            return e[2] / e[0], (e[1] / e[2] if e[2] else None), f"campaña «{t['campana']}»"
        if disp is not None and disp > 3:
            return None, None, "prohibida (dispersión entre grupos > 3×)"
        return base_cuenta[0], base_cuenta[1], "cuenta, sin lo ajeno ni los grupos muertos"

    def esperadas(u):
        cvr, cpa, nivel = base(u)
        if cvr is None:
            return None, None, None, nivel
        a = u["clics"] * cvr
        b = u["costo"] / cpa if cpa else None
        return a, b, (min(a, b) if b is not None else a), nivel
    out["esperadas_de"] = esperadas
    out["base_de"] = base
    # G8 — rendimiento. El programa nunca corta por rendimiento algo que no está decidido: si una búsqueda que no es
    # de lo protegido junta ≥ 3 conversiones esperadas y rinde bajo un tercio de su base, sale como PREGUNTA al dueño
    # (con el número), nunca como negativa ni baja de puja.
    for u in us:
        if u["costo"] <= 0 or any(t["gkey"] in muertos for t in u["filas"]):
            continue
        a, b, m, nivel = esperadas(u)
        u["esperadas"] = (a, b, m, nivel)
        cortada = u["estado"] == "ajena" or (u["estado"] == "competidor" and u.get("aparecer") == "no")
        if u["estado"] == "protegido" or cortada or u["clics"] < 2 or m is None or not out["rendimiento"]:
            continue
        cvr, _, _ = base(u)
        if m >= 3 and (u["cmax"] == 0 or (u["clics"] and u["conv"] / u["clics"] < cvr / 3)):
            out["g8"].append((u, "rinde bajo su base, pero no sé si es tuya", m))
    # G7 — CPC fuera de escala
    if "grupo" in inf["columnas"]:
        por_g = {}
        for t in filas:
            if t["clics"]:
                por_g.setdefault(t["gkey"], []).append(t["costo"] / t["clics"])
        for u in us:
            for t in u["filas"]:
                if not t["clics"] or len(por_g.get(t["gkey"], [])) < 5:
                    continue
                med_g = statistics.median(por_g[t["gkey"]])
                cpc = t["costo"] / t["clics"]
                _, cpa, _ = base(u)
                if med_g and cpc > 5 * med_g and cpa and t["costo"] >= cpa:
                    out["g7"].append((u, t, cpc, med_g))
    # 5.3 — auto-competencia
    camps = {t["campana"] for t in filas if t["campana"]}
    if "campana" not in inf["columnas"]:
        out["no_evaluable"].append(("Auto-competencia (5.3)", "falta la columna «Campaña»", costo,
                                    "añadir «Campaña» al export"))
    elif len(camps) >= 2:
        sob, n3, costo3 = 0, 0, 0
        for u in us:
            cs = {t["campana"] for t in u["filas"] if t["clics"]}
            if len(cs) >= 2:
                cpcs = [t["costo"] / t["clics"] for t in u["filas"] if t["clics"]]
                mn = min(cpcs)
                sob += sum((t["costo"] - t["clics"] * mn) for t in u["filas"] if t["clics"])
                n3 += 1
                costo3 += u["costo"]
        out["auto"] = {"terminos": n3, "costo": costo3, "sobrecosto": sob}
        if costo and sob / costo >= 0.05:
            out["gatillos"].append(("5.3", f"auto-competencia: {fmoney(sob)} de sobrecosto "
                                           f"({fpct(100 * sob / costo)} del gasto visible)"))
    else:
        out["no_evaluable"].append(("Auto-competencia (5.3)", "el archivo trae una sola campaña", costo,
                                    "el export de Campañas confirma si hay más"))
    # 5.2 — tipo de concordancia
    if "concordancia" in inf["columnas"]:
        B = {}
        marca = {u["n"] for u in us if u.get("tema") == "marca"}
        for t in vivos:
            if t["n"] in marca:
                continue
            c = norm(t["conc"])
            k = ("exacta" if "exact" in c else "frase" if ("phrase" in c or "frase" in c)
                 else "ai max" if "ai max" in c else "amplia" if ("broad" in c or "amplia" in c) else None)
            if k:
                e = B.setdefault(k, [0, 0])
                e[0] += t["costo"] or 0
                e[1] += t["conv"] or 0
        ok = {k: e for k, e in B.items() if e[1] >= 5}
        if len(ok) >= 2:
            orden = ["exacta", "frase", "amplia", "ai max"]
            ref = next(k for k in orden if k in ok)
            cpa_ref = ok[ref][0] / ok[ref][1]
            exceso = sum(e[1] * (e[0] / e[1] - cpa_ref) for k, e in ok.items() if e[0] / e[1] > cpa_ref)
            out["conc"] = {"bloques": B, "ref": ref, "cpa_ref": cpa_ref, "exceso": exceso}
            if costo and exceso / costo >= 0.05:
                out["gatillos"].append(("5.2", f"concordancia: {fmoney(exceso)} de exceso de CPA frente a «{ref}»"))
        else:
            out["no_evaluable"].append(("Tipo de concordancia (5.2)", "menos de dos tipos con 5 conversiones cada uno",
                                        costo, "una ventana más larga"))
    elif inf["tipo"] == "terminos":
        out["no_evaluable"].append(("Tipo de concordancia (5.2)", "falta la columna", costo,
                                    "añadir «Tipo de concordancia» al export"))
    # 5.4 — valor
    if "valor" not in inf["columnas"]:
        out["no_evaluable"].append(("Concentración de valor (5.4)", "falta «Valor de conversión»", costo,
                                    "añadir «Valor de conversión» al export"))
    # G6 — intención separable (hazlo tú mismo / formación) que el dueño no marcó como ajena
    for cat in ("hazlo_tu_mismo", "formacion"):
        ms = [u for u in us if u.get("etiqueta") == cat and u["estado"] in ("duda", "propuesta", "protegido")
              and not any(t["gkey"] in muertos for t in u["filas"])]
        cl, cv = suma(ms, "clics"), suma(ms, "conv")
        if ms and cl * cvr_c >= 3 and cvr_c:
            r = (cv / cl) / cvr_c if cl else 0
            out["hallazgos"].append(("G6", cat, r, ms))
            if r < 0.70:
                out["gatillos"].append(("G6", f"«{SEMILLAS[cat][0]}» convierte a {fnum(r, 2)} veces la cuenta"))
    return out

# ───────────────────────────── ubicaciones (informe «Ubicaciones coincidentes») ─────────────────────────────

LUGAR_COLS = ("ubicacion coincidente", "ubicaciones coincidentes", "matched location", "ubicacion mas especifica",
              "most specific location", "ubicacion", "location", "ciudad", "city", "comuna", "municipio",
              "area metropolitana", "metro area", "region", "pais territorio", "pais", "country territory", "country")
TIPO_UBIC = ("tipo de ubicacion", "location type", "tipo de coincidencia de ubicacion")
RUTA_UBIC = ("Campañas → Informes y estadísticas → Cuándo y dónde se mostraron los anuncios → Ubicaciones "
             "coincidentes → descargar")


def leer_ubicaciones(path):
    """Lee el informe de ubicaciones coincidentes. El lugar es la columna más específica que traiga."""
    txt, _ = _decodificar(Path(path).read_bytes())
    lineas = [ln for ln in txt.splitlines() if ln.strip()]
    mejor = None
    for delim in ("\t", ",", ";", "|"):
        for i, ln in enumerate(lineas[:40]):
            if ln.count(delim) < 2:
                continue
            try:
                celdas = _partir(ln, delim)
            except (csv.Error, StopIteration):
                continue
            ns = [norm(c) for c in celdas]
            lug = [(LUGAR_COLS.index(next(a for a in LUGAR_COLS if n.startswith(a))), j) for j, n in enumerate(ns)
                   if any(n.startswith(a) for a in LUGAR_COLS) and not any(t in n for t in TIPO_UBIC)]
            m = {k: j for j, n in enumerate(ns) for k, al in COLS.items() if n in al and k not in ("termino",)}
            if lug and "costo" in m and "clics" in m and (mejor is None or len(m) > len(mejor[3])):
                tipo = next((j for j, n in enumerate(ns) if any(t in n for t in TIPO_UBIC)), None)
                mejor = (delim, i, sorted(lug), m, tipo)
    if mejor is None:
        raise SystemExit("ERROR: no reconocí el informe de ubicaciones (hace falta una columna de lugar, «Clics» y "
                         f"«Costo»). Se descarga en {RUTA_UBIC}.")
    delim, hi, lug, m, tipo = mejor
    filas_crudas = [_partir(ln, delim) for ln in lineas[hi + 1:]]
    loc = detectar_locale([f[m[k]] for f in filas_crudas for k in NUMERICAS if k in m and m[k] < len(f)])
    filas, totales = [], {}
    for f in filas_crudas:
        f = f + [""] * (max(list(m.values()) + [j for _, j in lug] + [tipo or 0]) + 1 - len(f))
        vals = {k: num(f[m[k]], loc) for k in NUMERICAS if k in m}
        et = next((c.strip() for c in f if re.match(r"\s*total\s*:", c, re.I)), None)
        if et:
            totales[et] = vals
            continue
        llenas = [(r, f[j].strip()) for r, j in lug if f[j].strip() and f[j].strip() not in ("--", " --")]
        completas = [x for r, x in llenas if r <= 6]          # «Ubicación coincidente», «Matched location»…
        if completas:
            lugar = completas[0]
        elif llenas:        # País / Región / Ciudad en columnas separadas: el lugar completo, del más específico
            lugar = ", ".join(dict.fromkeys(x for _, x in llenas))
        elif any((vals.get(k) or 0) for k in ("costo", "clics")):
            lugar = "(sin ubicación)"          # con gasto y sin lugar: se cuenta, no se descarta
        else:
            continue
        tv = norm(f[tipo]) if tipo is not None else ""
        t = {"lugar": lugar, "n": norm(lugar), "partes": [norm(x) for x in re.split(r",", lugar) if x.strip()],
             "tipo": "interes" if "interes" in tv or "interest" in tv else
             "fisica" if ("fisic" in tv or "physical" in tv or "presen" in tv) else None,
             "campana": f[m["campana"]].strip() if "campana" in m else "", **vals}
        for k in ("clics", "costo", "conv", "todas"):
            t.setdefault(k, None)
        filas.append(t)
    return {"archivo": str(path), "filas": filas, "totales": totales, "con_tipo": tipo is not None,
            "columnas": sorted(m), "con_conv": "conv" in m, "con_todas": "todas" in m}


def geo_de(args):
    """el informe de ubicaciones, si vino (--ubicaciones ARCHIVO)"""
    ruta = args.get("ubicaciones")
    return leer_ubicaciones(ruta) if ruta and ruta is not True else None


def resumen_geo(G):
    gs = [u for u in lugares_unicos(G) if u["costo"] > 0]
    c = suma(G["filas"], "costo")
    linea = f"- Ubicaciones: {len(lugares_unicos(G))} lugares, {len(gs)} con costo · {fmoney(c)}"
    if G["con_tipo"]:
        ci = sum(t["costo"] or 0 for t in G["filas"] if t["tipo"] == "interes")
        linea += (f" · por «área de interés»: {fmoney(ci)} ({fpct(100 * ci / c if c else 0)})" if ci else
                  " · todo por ubicación física")
    else:
        linea += " · sin la columna «Tipo de ubicación»"
    return linea


def lugares_top(G, n=10):
    agg = {}
    for u in lugares_unicos(G):
        k = corto(u)
        agg[k] = agg.get(k, 0) + u["costo"]
    return [(k, v) for k, v in sorted(agg.items(), key=lambda x: -x[1]) if v > 0][:n]


def lugares_unicos(G):
    d = {}
    for t in G["filas"]:
        u = d.setdefault(t["n"], {"n": t["n"], "lugar": t["lugar"], "partes": t["partes"], "filas": []})
        u["filas"].append(t)
    us = list(d.values())
    for u in us:
        for k in ("clics", "costo", "conv", "todas"):
            u[k] = suma(u["filas"], k)
        u["cmax"] = max(u["conv"], u["todas"])
        u["conv_desc"] = not (G["con_conv"] or G["con_todas"]) or any(
            (G["con_conv"] and t.get("conv") is None) or (G["con_todas"] and t.get("todas") is None)
            for t in u["filas"])
    us.sort(key=lambda u: (-u["costo"], u["n"]))
    for i, u in enumerate(us, 1):
        u["id"] = f"g{i:03d}"
    return us


def corto(u):
    return u["lugar"].split(",")[0].strip()


def nombre_visible(u, todos):
    """«Santiago» a secas si no se confunde; si otro lugar se llama igual, con su región"""
    c = corto(u)
    if sum(1 for x in todos if corto(x) == c) > 1:
        return u["lugar"].rsplit(",", 1)[0].strip() if "," in u["lugar"] else u["lugar"]
    return c


# regiones de Chile tal como las escribe Google (en inglés) → cómo las dice el dueño
REGIONES_CL = {
    "santiago metropolitan region": {"metropolitana", "rm", "santiago"},
    "valparaiso": {"valparaiso", "quinta"}, "biobio": {"biobio", "bio bio", "octava"}, "bio bio": {"biobio", "octava"},
    "araucania": {"araucania", "novena"}, "maule": {"maule", "septima"}, "nuble": {"nuble"},
    "coquimbo": {"coquimbo", "cuarta"}, "atacama": {"atacama", "tercera"}, "antofagasta": {"antofagasta", "segunda"},
    "tarapaca": {"tarapaca", "primera"}, "arica y parinacota": {"arica", "parinacota"},
    "los lagos": {"lagos", "decima"}, "los rios": {"rios"}, "aysen": {"aysen", "aisen"},
    "magallanes y antartica chilena": {"magallanes"}, "magallanes": {"magallanes"},
    "o higgins": {"higgins", "sexta"}, "libertador general bernardo o higgins": {"higgins", "sexta"},
}
_GENERICO_LUGAR = {"region", "regiones", "de", "del", "la", "las", "los", "el", "y", "province", "provincia",
                   "metropolitan", "metropolitana", "comuna", "ciudad", "state", "estado", "toda", "todo", "todas",
                   "todos", "area", "zona"}


def en_zona(parte, zona_toks):
    """¿el dueño nombró este componente del lugar? («Santiago Metropolitan Region» ≈ «Región Metropolitana»)"""
    if not parte:
        return False
    if parte in REGIONES_CL and (REGIONES_CL[parte] & zona_toks or any(" " in a and a in " ".join(zona_toks)
                                                                         for a in REGIONES_CL[parte])):
        return True
    nucleo = set(parte.split()) - _GENERICO_LUGAR
    return bool(nucleo) and nucleo <= zona_toks


def leer_lugares(path, gs):
    ids = {u["id"] for u in gs}
    E = {}
    p = Path(path)
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            partes = [x.strip() for x in re.split(r"[;\t|]", ln.strip())]
            if len(partes) >= 2 and partes[0] in ids:
                v = norm(partes[1]).replace(" ", "_")
                E[partes[0]] = v if v in ("dentro", "fuera", "no_se") else "no_se"
    return E


def geo_decidir(G, fi, E):
    """Cada lugar: dentro (no se toca) · fuera (excluir, PARA CONFIRMAR) · pregunta (convirtió o no se sabe).
    Dentro sin importar la IA: el lugar que el dueño nombró en su zona, y todo lugar que CONTIENE un lugar donde
    atiende (la región, el país). Si otro lugar con el mismo nombre convirtió, ninguno se excluye."""
    gs = lugares_unicos(G)
    zona_toks = set(toks(fi.get("zona", "")))
    for u in gs:
        u["literal"] = any(en_zona(p_, zona_toks) for p_ in u["partes"])
        u["et"] = "dentro" if u["literal"] else E.get(u["id"])
    # un lugar que contiene (es sufijo de) un lugar «dentro» también es dentro: no se excluye la región del cliente
    ancestros = {tuple(u["partes"][i:]) for u in gs if u["et"] == "dentro" for i in range(1, len(u["partes"]))}
    convirtio = {corto(u) for u in gs if u["cmax"] > 0}
    for u in gs:
        if u["lugar"] == "(sin ubicación)":
            u.update(estado="sin_lugar", motivo="sin ubicación en el informe")
        elif u["et"] == "dentro" or tuple(u["partes"]) in ancestros:
            u.update(estado="dentro", motivo="en tu zona" if u["et"] == "dentro" else "contiene tu zona")
        elif u["et"] == "fuera" and (u["cmax"] > 0 or u["conv_desc"] or corto(u) in convirtio):
            u.update(estado="pregunta", motivo="fuera de tu zona, pero convirtió" if u["cmax"] > 0 else
                     "fuera de tu zona, sin dato de conversiones" if u["conv_desc"] else
                     "fuera de tu zona, pero otro lugar con ese nombre convirtió")
        elif u["et"] == "fuera":
            u.update(estado="fuera", motivo="fuera de tu zona")
        elif u["et"] == "no_se":
            u.update(estado="pregunta", motivo="no sé si atiendes ahí")
        else:
            u.update(estado="sin_etiqueta", motivo="sin etiqueta")
    costo = suma(G["filas"], "costo")
    tot = _total({"totales": G["totales"]}, "cuenta", "account")
    out = {"lugares": gs, "costo": costo, "tipo": None, "gatillo": None,
           "total": tot.get("costo") if tot else None}
    if G["con_tipo"]:
        T = {}
        for t in G["filas"]:
            e = T.setdefault(t["tipo"] or "sin_tipo", {"clics": 0, "costo": 0, "conv": 0, "desc": False})
            e["clics"] += t["clics"] or 0
            e["costo"] += t["costo"] or 0
            e["conv"] += t["conv"] or 0
            e["desc"] = e["desc"] or t.get("conv") is None
        out["tipo"] = T
        fis, inte = T.get("fisica"), T.get("interes")
        if inte and inte["costo"] > 0:
            if not fis or fis["desc"] or inte["desc"] or not fis["clics"] or not fis["conv"]:
                inte["veredicto"] = "sin dato"
            else:
                cvr, cpa = fis["conv"] / fis["clics"], fis["costo"] / fis["conv"]
                esp = min(inte["clics"] * cvr, inte["costo"] / cpa)
                inte["esperadas"] = esp
                if esp >= 3 and inte["conv"] < esp / 3:
                    inte["veredicto"] = "enfermo"
                    out["gatillo"] = f"el tráfico por «área de interés» convierte {fnum(inte['conv'])} contra " \
                                     f"{fnum(esp)} esperadas"
                elif esp >= 3:
                    inte["veredicto"] = "sano"
                else:
                    inte["veredicto"] = "sin muestra"
    return out
def _lista_terms(hs, maxn=20, con_grupo=True):
    def f(h):
        extra = []
        if h["grupos"] and (con_grupo or not bloquea_ok(h)):
            extra.append(h["grupos"][0])
        if h["costo"] == 0:
            extra.append("sin costo")
        if h["cmax"] > 0:
            extra.append(f"{fnum(h['cmax'])} conv")
        if h["estado"] == "protegido":
            extra.append(f"tema {h['tema']}" if h["tema"] in (1, 2) else "protegido")
        elif h["estado"] == "duda":
            extra.append("en duda")
        elif h["estado"] == "propuesta":
            extra.append("por confirmar")
        return f"«{h['texto']}»" + (f" ({', '.join(extra)})" if extra else "")
    if len(hs) <= maxn:
        return " · ".join(f(h) for h in hs)
    malos = [h for h in hs if not bloquea_ok(h)]
    buenos = [h for h in hs if bloquea_ok(h)]
    resto = max(0, maxn - len(malos))
    partes = [f(h) for h in malos] + [f(h) for h in buenos[:resto]]
    faltan = len(buenos) - min(resto, len(buenos))
    return " · ".join(partes) + (f" · y {faltan} más" if faltan > 0 else "")


def a_etiquetar(us):
    """las búsquedas con costo que la IA debe etiquetar: todas hasta 1.500; si hay más, las del 95 % del costo"""
    con_costo = [u for u in us if u["costo"] > 0]
    total = suma(con_costo, "costo") or 1
    lista, acum = [], 0
    for u in con_costo:
        if len(con_costo) > 1500 and (acum / total >= 0.95 or len(lista) >= 1500):
            break
        lista.append(u)
        acum += u["costo"]
    return lista


def cmd_etiquetar(inf, args):
    fi = cargar_ficha(inf, args)
    if args.get("lugares"):
        G = geo_de(args)
        if not G:
            raise SystemExit("Uso: python3 auditor.py etiquetar INFORME --ubicaciones ARCHIVO --lugares")
        falta = [u for u in geo_decidir(G, fi, {})["lugares"] if u["estado"] == "sin_etiqueta" and u["costo"] > 0]
        print("# Escribe lugares.csv, una línea por id: id;dentro  |  id;fuera  |  id;no_se")
        print(f"# Zona que declaró el dueño: «{fi.get('zona') or 'no la dijo'}». dentro = atiende ahí (o el lugar "
              "contiene su zona, como el país o la región entera) · fuera = no atiende ahí · no_se = no estás seguro.")
        if not falta:
            print("# Ningún lugar que etiquetar: todos quedaron resueltos por la zona que dijo el dueño. No escribas "
                  "lugares.csv; sigue con: python3 auditor.py etiquetar " + Path(inf["archivo"]).name)
            return
        print(f"# {len(falta)} lugares por etiquetar (los que nombró el dueño ya quedaron dentro):")
        for u in falta:
            print(f"{u['id']} | {u['lugar']}")
        return
    us = unicos(inf)
    E = leer_etiquetas(args.get("etiquetas", "etiquetas.csv"), us)
    pedidos = set(str(args.get("ids", "")).split(",")) - {""}
    lista = a_etiquetar(us)
    lista += [u for u in us if u["id"] in pedidos and u not in lista]
    if args.get("compra"):          # la 2.ª pregunta va sobre las mismas búsquedas, tengan o no etiqueta
        Cp = leer_compra(args.get("compra_csv", "compra.csv"), us)
        lista = [u for u in lista if (u["id"] in pedidos if pedidos else (args.get("todo") or u["id"] not in Cp))]
    elif not args.get("todo"):
        lista = [u for u in lista if u["id"] not in E] if not pedidos else [u for u in lista if u["id"] in pedidos]
    tm = {t["id"]: t for t in temas(inf, us)}
    if args.get("compra"):
        print("# 2.ª pregunta. Escribe compra.csv, una línea por id: id;s  |  id;n  |  id;?")
        print("# ¿Quien busca esto podría comprarle al dueño algo que él vende? s = sí · n = no · ? = no sé")
        print("# Contesta mirando sólo la búsqueda y la ficha, no tus etiquetas.")
        for u in sorted(lista, key=lambda u: u["n"]):
            print(f"{u['id']} {u['texto']}")
        return
    print("# Escribe etiquetas.csv, una línea por id: id;etiqueta;palabra")
    print("# etiquetas: " + " · ".join(ETIQUETAS))
    print("# palabra: sólo en empleo…tercero y competidor: la palabra o frase de la búsqueda que la hace ajena "
          "(«freelance», «curso», «email», el nombre del competidor). Precio, cuánto cuesta, valor, cotización y "
          "barato son de comprador: nunca la hacen ajena.")
    print("# Ante la duda, no_se: una pregunta al dueño cuesta menos que cortarle una venta.")
    print("# En la MISMA ejecución escribe también compra.csv, una línea por id: id;s | id;n | id;? — ¿quien busca "
          "esto podría comprarle al dueño algo que él vende? Contéstala mirando la búsqueda, no tu etiqueta.")
    print("# FICHA")
    print(f"#  Negocio: {fi.get('negocio') or '—'} | Zona: {fi.get('zona') or '—'}")
    for t in fi.get("temas", []):
        b = tm.get(t.get("id"))
        if b:
            partes = "; ".join(f"parte «{p.get('palabras_del_dueno', '')}» → {p['valor']}" for p in t.get("partes", []))
            print(f"#  {t['id']}) {b['nombre']} [{fmt_regla(b['regla'])}] → {t.get('valor') or 'sin respuesta'}"
                  + (f" ({partes})" if partes else ""))
    for nv in fi.get("no_vende", []):
        print(f"#  No vende: {nv['texto']}")
    if fi.get("marca"):
        print(f"#  Marca: {' · '.join(fi['marca'])}")
    for n in fi.get("nombres", []):
        print(f"#  Nombre «{n['nombre']}» → {n['tipo']}" + (f", ¿aparecer? {n.get('aparecer')}" if n["tipo"] == "b"
                                                              else ""))
    print(f"# {len(lista)} búsquedas por etiquetar:")
    for u in lista:
        print(f"{u['id']} | {u['texto']} | {', '.join(u['grupos']) or '—'}")


def cmd_auditar(inf, args):
    fi = cargar_ficha(inf, args)
    us = unicos(inf)
    E = leer_etiquetas(args.get("etiquetas", "etiquetas.csv"), us)
    C = leer_compra(args.get("compra", "compra.csv"), us)
    exigidos = a_etiquetar(us)
    faltan = [u["id"] for u in exigidos if u["id"] not in E]
    if faltan:
        raise SystemExit(f"FALTAN ETIQUETAS para {len(faltan)} búsquedas: {', '.join(faltan[:40])}"
                         + (" …" if len(faltan) > 40 else "") + "\nCorre: python3 auditor.py etiquetar "
                         + Path(inf["archivo"]).name)
    faltan_c = [u["id"] for u in exigidos if u["id"] not in C]
    if faltan_c and not args.get("sin_compra"):
        raise SystemExit(f"FALTA compra.csv para {len(faltan_c)} búsquedas. Corre: python3 auditor.py etiquetar "
                         + Path(inf["archivo"]).name + " --compra")
    estados(inf, fi, us, E, C)
    N = negativas(inf, fi, us)
    if N["faltan_etiquetas"]:
        raise SystemExit("FALTAN ETIQUETAS (búsquedas sin costo que una negativa de frase tocaría): "
                         + ",".join(N["faltan_etiquetas"]) + "\nCorre: python3 auditor.py etiquetar "
                         + Path(inf["archivo"]).name + " --ids " + ",".join(N["faltan_etiquetas"])
                         + "  y agrega esas líneas a etiquetas.csv (y a compra.csv).")
    K = compuertas(inf, fi, us)
    geo = None
    G = geo_de(args)
    if G:
        Eg = leer_lugares(args.get("lugares_csv", "lugares.csv"), lugares_unicos(G))
        geo = geo_decidir(G, fi, Eg)
        falta = [u["id"] for u in geo["lugares"] if u["estado"] == "sin_etiqueta" and u["costo"] > 0]
        if falta:
            raise SystemExit(f"FALTAN LUGARES por etiquetar ({len(falta)}): {', '.join(falta[:40])}"
                             + (" …" if len(falta) > 40 else "") + "\nCorre: python3 auditor.py etiquetar "
                             + Path(inf["archivo"]).name + f" --ubicaciones {args['ubicaciones']} --lugares")
    completo, res = informe(inf, fi, us, N, K, args, geo)
    rep, _ = informe(inf, fi, us, N, K, args, geo, corto=True)
    Path("informe_completo.md").write_text(completo, encoding="utf-8")
    Path(args.get("salida", "informe.md")).write_text(rep, encoding="utf-8")
    Path("resultado.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(rep + "===== FIN DEL INFORME =====")


def seccion_geo(geo, visible):
    L = []
    gc = geo["costo"]
    L.append(f"- El informe de ubicaciones suma {fmoney(gc)} en {len(geo['lugares'])} lugares, "
             f"{sum(1 for u in geo['lugares'] if u['costo'] > 0)} con costo.")
    if geo.get("total") and abs(geo["total"] - gc) > max(1, 0.01 * geo["total"]):
        L.append(f"- Ojo: la fila «Total: Cuenta» dice {fmoney(geo['total'])}; las filas suman {fmoney(gc)}. Revisa "
                 "que el archivo esté completo antes de decidir por lugar.")
    T = geo["tipo"]
    if T is None:
        L.append("- No trae la columna «Tipo de ubicación»: no sé si parte del gasto llega por «área de interés».")
    else:
        inte = T.get("interes")
        if not inte or not inte["costo"]:
            L.append("- Todo el gasto llegó por ubicación física: la campaña está en «Presencia» o el tráfico por "
                     "interés no gastó. Evaluado, sin hallazgo.")
        else:
            pc = 100 * inte["costo"] / gc if gc else 0
            L.append(f"- Por «área de interés» (la opción «Presencia o interés», que Google usa por defecto): "
                     f"{fmoney(inte['costo'])} ({fpct(pc)} del gasto de ubicaciones), {fconv(inte['conv'])}.")
            v = inte.get("veredicto")
            if v == "enfermo":
                L.append(f"  → Convierte {fnum(inte['conv'])} contra {fnum(inte['esperadas'])} esperadas con la tasa "
                         "del tráfico físico: considera «Presencia» en Configuración → Ubicaciones → Opciones. Revisa "
                         "antes de dónde vienen esas búsquedas: puede ser gente que viaja o compra para tu zona.")
            elif v == "sano":
                L.append(f"  → Convierte {fnum(inte['conv'])} con {fnum(inte['esperadas'])} esperadas: está bien. "
                         "No cambies a «Presencia»: cortarías ventas.")
            elif v == "sin dato":
                L.append("  → No puedo compararlo: faltan datos de conversión (o el tráfico físico no tiene ninguna). "
                         "No lo toques.")
            else:
                L.append("  → Muestra chica (menos de 3 conversiones esperadas): no alcanza para decidir; "
                         "no lo toques.")
    fuera = [u for u in geo["lugares"] if u["estado"] == "fuera" and u["costo"] > 0]
    if fuera:
        c = suma(fuera, "costo")
        L.append(f"- **Fuera de tu zona, para confirmar** → {fmoney(c)} ({fpct(100 * c / gc if gc else 0)} del "
                 "gasto de ubicaciones), 0 conversiones: "
                 + " · ".join(f"{nombre_visible(u, geo['lugares'])} {fmoney(u['costo'])}" for u in fuera[:15])
                 + (f" · y {len(fuera) - 15} más" if len(fuera) > 15 else "")
                 + ". Si no atiendes ahí, exclúyelas en la campaña (Configuración → Ubicaciones → Excluir): es una "
                 "exclusión de ubicación, no una negativa de palabra.")
    else:
        L.append("- Nada con costo fuera de tu zona.")
    return L


def informe(inf, fi, us, N, K, args, geo=None, corto=False):
    """corto=True: la versión que la IA pega en el chat (listas con tope, lo no evaluable en un bloque); el detalle
    completo va a informe_completo.md. Menos texto que redigitar = menos errores al pegar (eval3)."""

    def tope(largo, corto_):
        return corto_ if corto else largo
    kw = inf["tipo"] == "palabras_clave"
    filas = inf["terminos"]
    visible = suma(filas, "costo")
    pv = (lambda x: 100 * x / visible) if visible else (lambda x: None)
    cob, med = cobertura(inf), medicion(inf)
    n_sec = [0]

    def sec(titulo):
        n_sec[0] += 1
        return f"## {n_sec[0]}. {titulo}"
    if geo and geo.get("gatillo") and not any(g[0] == "ubicación" for g in K["gatillos"]):
        K["gatillos"].append(("ubicación", geo["gatillo"]))
    res = {"version": VERSION, "visible": visible, "cobertura": cob, "medicion": {k: v for k, v in med.items()
                                                                                   if k != "factor"}}
    L = []
    # ── datos para la respuesta directa
    bloq = N["bloqueados"]
    costo_b = suma(bloq, "costo")
    # lo que el dueño pega: cada grafía de frase y cada exacta en cada grafía (eval4: «4 negativas» con 5 en la lista)
    n_neg = sum(len(f["grafias"]) for L_ in N["listas"].values() for f in L_["frases"]) + \
        sum(len(u.get("grafias_exactas", [u["texto"]])) for L_ in N["listas"].values() for u in L_["exactas"])
    prot = [u for u in us if u["estado"] == "protegido" and u["costo"] > 0]
    peor = max((u for u in prot if u["conv"] == 0), key=lambda u: u["costo"], default=None)
    flojas = []
    for u in prot:
        cvr_b = K["base_de"](u)[0]
        if u["conv"] > 0 and u["clics"] >= 10 and cvr_b and (u["conv"] / u["clics"]) < 0.75 * cvr_b:
            flojas.append((u["conv"] / u["clics"] / cvr_b, u))
    floja = min(flojas, key=lambda x: (x[0], x[1]["n"]))[1] if flojas else None
    dudas = [u for u in us if u["estado"] == "duda" and u["costo"] > 0]
    props_ = [u for u in us if u["estado"] == "propuesta" and u["costo"] > 0]
    comp_ns = [u for u in us if u["estado"] == "competidor" and u.get("aparecer") in (None, "no_se") and u["costo"] > 0]
    g8 = K["g8"]
    ya = {u["id"] for u in dudas + props_ + comp_ns}
    g8_solo = [u for u, _, _ in g8 if u["id"] not in ya]
    pend_costo = suma(dudas, "costo") + suma(comp_ns, "costo") + suma([p["u"] for p in N["preguntas"]], "costo") \
        + suma(props_, "costo") + suma(g8_solo, "costo")
    RD = []
    if g8 and K["rendimiento"]:
        RD.append(f"- Pausar por rendimiento: ninguna sin tu respuesta. {len(g8)} búsqueda(s) rinden bajo su base, "
                  f"pero no sé si son tuyas: {', '.join('«' + u['texto'] + '»' for u, _, _ in g8[:5])} (abajo).")
    else:
        con_costo_n = [u for u in us if u["costo"] > 0]
        todo_tuyo = con_costo_n and all(u["estado"] == "protegido" for u in con_costo_n)
        motivo = "; ".join(K["motivo_sin_rendimiento"]) or (
            "todo lo que gastó es de lo que vendes: no se pausa ni se baja por costo o CPA" if todo_tuyo
            else "ninguna búsqueda fuera de lo tuyo llega a 3 conversiones esperadas")
        RD.append(f"- Pausar por rendimiento: ninguna ({motivo}).")
    if floja:
        a, b, m, nivel = floja.get("esperadas") or (None, None, None, None)
        RD.append(f"- La tuya que menos convierte: «{floja['texto']}» {fnum(floja['conv'])} conv en "
                  f"{fclics(floja['clics'])}" + (f" ({fnum(m)} esperadas)" if m is not None else "")
                  + " → no se le baja la puja ni se pausa; si preocupa, se revisa su página.")
    if peor:
        a, b, m, nivel = peor.get("esperadas") or (None, None, None, None)
        RD.append(f"- Lo que más gasta sin convertir es tuyo: «{peor['texto']}» {fmoney(peor['costo'])}, "
                  f"{fnum(peor['clics'])} clics" + (f", {fnum(m)} conversiones esperadas" if m is not None else "")
                  + " → no se toca; si preocupa, se revisa su página y la medición.")
    if N["solo_candidatas"]:
        RD.append(f"- Candidatas a negativa (sin tus respuestas no las doy por buenas): {len(bloq)} búsquedas, "
                  f"{fmoney(costo_b)}.")
    elif n_neg:
        verbo = "Pausar o quitar (palabras clave de otro negocio)" if kw else "Negativar ya"
        RD.append(f"- {verbo}: {n_neg} negativa(s) en {len(N['listas'])} lista(s), que bloquean {len(bloq)} "
                  f"búsqueda(s) · {fmoney(costo_b)} ({fpct(pv(costo_b))} del gasto que este archivo ve).")
    else:
        RD.append("- Negativar: nada por ahora; no apareció ninguna búsqueda de otro negocio con costo.")
    npreg = len(dudas) + len(comp_ns) + len(N["preguntas"]) + len(props_) + len(g8_solo)
    if npreg:
        RD.append(f"- Pendientes tuyos: {npreg} búsqueda(s), {fmoney(pend_costo)} sin decidir (abajo).")
    if geo:
        fuera = [u for u in geo["lugares"] if u["estado"] == "fuera" and u["costo"] > 0]
        if fuera:
            RD.append(f"- Ubicaciones fuera de tu zona (para confirmar, no se cortan solas): {len(fuera)}, "
                      f"{fmoney(suma(fuera, 'costo'))}.")
        else:
            RD.append("- Ubicaciones: nada con costo fuera de tu zona.")
    # la primera línea la escribe el programa y la IA la copia arriba (eval2: parafraseada contradijo el informe)
    con_costo_n = [u for u in us if u["costo"] > 0]
    if g8 and K["rendimiento"]:
        p_ = (f"Pausar: ninguna sin tu respuesta; {len(g8)} búsqueda(s) rinden bajo su base y te pregunto si "
              "son tuyas")
    elif con_costo_n and all(u["estado"] == "protegido" for u in con_costo_n):
        p_ = "Pausar: ninguna, porque todo lo que gastó es de lo que vendes"
    elif K["motivo_sin_rendimiento"]:
        p_ = f"Pausar por rendimiento: ninguna, porque {K['motivo_sin_rendimiento'][0]}"
    else:
        p_ = "Pausar por rendimiento: ninguna; nada fuera de lo que vendes junta evidencia para cortarse"
    if N["solo_candidatas"]:
        n_ = f"Negativar: {len(bloq)} candidata(s), {fmoney(costo_b)}, cuando me confirmes tu negocio"
    elif n_neg:
        n_ = (f"{'Pausar o quitar' if kw else 'Negativar ya'}: {n_neg} negativa(s) que bloquean {len(bloq)} "
              f"búsqueda(s), {fmoney(costo_b)}")
    else:
        n_ = "Negativar: nada por ahora"
    q_ = f"Te pregunto por {npreg} búsqueda(s) más ({fmoney(pend_costo)})" if npreg else ""
    primera = ". ".join(x for x in (p_, n_, q_) if x) + "."
    res["primera_linea"] = primera
    res["respuesta_directa"] = RD
    # sólo la primera línea y el informe: sin bloque de «contexto» que invite a parafrasear
    RD = ["PRIMERA LÍNEA (cópiala tal cual, arriba de todo):", f"**{primera}**"]
    # ── encabezado de honestidad
    # qué hacer primero: lo escribe el programa (eval4: las frases libres de la IA mandaron negativar lo que el
    # programa había vetado); sólo con lo que el informe sostiene
    pasos = []
    medir_mal = any("mide" in m or "medición" in m for m in K["motivo_sin_rendimiento"])
    if (med["factor"] and med["factor"] >= 1.5) or medir_mal:
        pasos.append("Revisa primero la medición (abajo): hasta arreglarla, ningún número de rendimiento es confiable.")
    if n_neg and not N["solo_candidatas"]:
        pasos.append("Pega las negativas de la sección «Limpieza», cada una en su lista, tal como están: son minutos. "
                     "Las frases que la simulación dejó fuera no van.")
    malos = [g for g in K["grupos"] if g["estado"] in ("MUERTO", "ENFERMO")]
    if malos:
        pasos.append(f"Mira la página, la oferta y la medición del grupo «{malos[0]['grupo']}»: es donde más se "
                     "pierde.")
    if npreg:
        pasos.append(f"Contéstame las {npreg} búsqueda(s) pendientes (al final): con tu respuesta decido si van a la "
                     "limpieza o se quedan.")
    if not pasos and (med["todas"] is None or cob["pct"] is None):
        pasos.append("Antes de tocar nada, confirma que tus conversiones son ventas de verdad: descarga el informe con "
                     "«Todas las conv.» y la fila «Total: Cuenta», y cruza las conversiones con tus ventas.")
    if not pasos:
        pasos.append("Nada urgente con lo que este archivo deja ver: mantén la cuenta como está y vuelve a revisarla "
                     "con la ventana siguiente.")
    L += ["**Qué hacer primero**", ""] + [f"{i}. {x}" for i, x in enumerate(pasos[:3], 1)] + [""]
    res["que_hacer"] = pasos[:3]
    L += ["## Lo que miré", ""]
    L += resumen(inf, us) if not corto else [x for x in resumen(inf, us) if not x.startswith("- Columnas que faltan")]
    if not corto:
        L.append("- Columna de conversión usada: «Conversiones»; la simulación de daño usa la mayor de las dos "
                 "columnas.")
    if cob["pct"] is not None and cob["pct"] < 99.5 and not corto:
        L.append(f"- Lo invisible: {fmoney(cob['cuenta'] - cob['visible'])} ({fpct(100 - cob['pct'])} de la cuenta) "
                 "no tiene búsqueda visible en este archivo (umbral de privacidad de Google o campañas que el "
                 "informe no muestra).")
    if not corto:
        L.append(f"- Base de comparación: CVR de las búsquedas visibles {fpct(100 * K['cvr_cuenta'])}"
                 + (f", CPA {fmoney(K['cpa_cuenta'])}" if K["cpa_cuenta"] else "") + ".")
    if fi.get("sin_respuestas"):
        L.append("- Sin tus respuestas: protegí todo lo que está en un grupo de anuncios o convirtió; lo ajeno "
                 "sale como candidata, no como negativa; los competidores quedan sin decidir.")
    # ── medición
    if med["factor"] and med["factor"] >= 1.5 or not K["rendimiento"] and any("medición" in m or "mide" in m
                                                                               for m in K["motivo_sin_rendimiento"]):
        L += ["", "## Medición (lo primero)", ""]
        if med["factor"] and med["factor"] >= 1.5:
            L.append(f"«Conversiones» {fnum(med['conv'])} contra «Todas las conv.» {fnum(med['todas'])}: "
                     f"{med['estado']}. Antes que cualquier palabra, revisa qué acciones cuentan como principales "
                     "(export «Acciones de conversión»).")
        for m in K["motivo_sin_rendimiento"]:
            if "mide" in m or "medición" in m:
                L.append(f"- {m}.")
    cambios = (fi.get("cambios") or "").strip()
    if cambios and not re.match(r"(no|nada|ninguno|ninguna)\b", norm(cambios)):
        L += ["", "## Medición: un cambio en el período", "",
              f"Dijiste (P5): «{cambios}». Esta ventana puede mezclar dos formas de medir: antes de juzgar "
              "rendimiento, compara las semanas antes y después del cambio con el mismo informe partido en dos."]
    # ── limpieza
    L += ["", sec("Limpieza: búsquedas de otro negocio") + (" (candidatas)" if N["solo_candidatas"] else ""), ""]
    res["listas"] = {}
    if not N["listas"]:
        L.append("No encontré búsquedas de otro negocio con costo que se puedan cortar sin tocar lo tuyo.")
    contadas = set()
    for nombre, Ld in N["listas"].items():
        ms = [u for u in bloq if any(u in s["hits"] and not s["malos"] for s in Ld["sims"]) or u in Ld["exactas"]]
        ms = [u for u in {u["id"]: u for u in ms}.values() if u["id"] not in contadas]   # cada búsqueda cuenta una vez
        contadas |= {u["id"] for u in ms}
        c = suma(ms, "costo")
        L.append(f"**Lista «{nombre}»** → {fmoney(c)} ({fpct(pv(c))} del gasto visible) · {len(ms)} búsqueda(s)"
                 + (" nueva(s): las demás ya las cubre una lista de arriba" if len(ms) < len(
                     [u for u in bloq if u in Ld["exactas"] or any(u in s_["hits"] and not s_["malos"]
                                                                  for s_ in Ld["sims"])]) else ""))
        res["listas"][nombre] = {"costo": c, "frases": [],
                                 "exactas": [g for u in Ld["exactas"] for g in u.get("grafias_exactas", [u["texto"]])]}
        for s in Ld["sims"]:
            comillas = " / ".join(chr(34) + v + chr(34) for v in s["variantes"])
            if s["malos"]:
                n_m = len(s["malos"])
                L.append(f"  Simulación: {len(s['hits'])} búsqueda(s) contienen {comillas}; "
                         f"{n_m} no se puede{'n' if n_m > 1 else ''} bloquear: {_lista_terms(s['malos'], tope(12, 5))}")
                L.append("  → la frase no va; bajo a exacta sólo lo ajeno que costó.")
                continue
            L.append(f"  Simulación: {len(s['hits'])} búsqueda(s) contienen {comillas}: "
                     f"{_lista_terms(s['hits'], tope(30, 8), con_grupo=not corto)}")
            gs = next(f["grafias"] for f in Ld["frases"] if f["frase"] == s["frase"])
            L.append(f"  → limpia. Frase: {' · '.join(chr(34) + g + chr(34) for g in gs)}")
            res["listas"][nombre]["frases"].append({"frase": s["frase"], "grafias": gs,
                                                    "bloquea": [h["texto"] for h in s["hits"]]})
        if Ld["exactas"]:
            forma = "Pausar o quitar la palabra clave" if kw else "Exacta"
            L.append(f"  {forma}: " + " · ".join(" ".join(f"[{g}]" for g in u.get("grafias_exactas", [u["texto"]]))
                                                   + f" {fmoney(u['costo'])}" for u in Ld["exactas"]))
        L.append("")
    props = [u for u in us if u["estado"] == "propuesta" and u["costo"] > 0]
    if props:
        c = suma(props, "costo")
        L.append(f"**Para confirmar** (parecen de otro negocio, pero no lo dijiste; no las corto sin tu OK) → "
                 f"{fmoney(c)} ({fpct(pv(c))} del gasto visible): " + " · ".join(
                     f"«{u['texto']}» {fmoney(u['costo'])} ({LISTA.get(u['categoria'], u['categoria'])})"
                     for u in props[:tope(20, 8)]) + (f" · y {len(props) - tope(20, 8)} más"
                                                     if len(props) > tope(20, 8) else ""))
        L.append("")
    res["propuestas"] = [u["texto"] for u in props]
    if N["listas"]:
        L.append(f"Total de la limpieza: {fmoney(costo_b)} ({fpct(pv(costo_b))} del gasto visible), "
                 f"{len(bloq)} búsqueda(s), {fnum(sum(u['cmax'] for u in bloq))} conversiones. Esfuerzo: minutos. "
                 "Las listas con nombre se aplican a varias campañas a la vez.")
    res["limpieza"] = {"costo": costo_b, "pct": pv(costo_b), "terminos": [u["texto"] for u in bloq]}
    # ── ubicaciones
    if geo:
        L += ["", sec("Ubicaciones"), ""] + seccion_geo(geo, visible)
        res["ubicaciones"] = {"costo": geo["costo"], "fuera": [(u["lugar"], u["costo"]) for u in geo["lugares"]
                                                               if u["estado"] == "fuera" and u["costo"] > 0],
                              "preguntas": [u["lugar"] for u in geo["lugares"] if u["estado"] == "pregunta"],
                              "tipo": {k: {kk: vv for kk, vv in v.items()} for k, v in (geo["tipo"] or {}).items()}}
    # ── protegidos
    L += ["", sec("Lo que no toqué, y por qué"), ""]
    grupos_p = [(nombre, [u for u in prot if u["tema"] == v]) for v, nombre in (
        (1, "Tu servicio principal (tema 1)"), (2, "Lo que vendes como secundario (tema 2)"), ("marca", "Tu marca"),
        ("zona", "Tus ciudades o comunas (P3)"))]
    if corto and any(ms for _, ms in grupos_p):
        L.append("- " + " · ".join(f"{n}: {len(ms)} búsqueda(s), {fmoney(suma(ms, 'costo'))}, "
                                   f"{fconv(suma(ms, 'conv'))}" for n, ms in grupos_p if ms)
                 + ". Nada de eso se pausa, se negativa ni se le baja la puja: si rinde mal, se revisa la página, la "
                 "medición o el valor de la conversión.")
    for nombre, ms in ([] if corto else grupos_p):
        if ms:
            L.append(f"- {nombre}: {len(ms)} búsqueda(s), {fmoney(suma(ms, 'costo'))}, {fconv(suma(ms, 'conv'))}. "
                     "Ninguna pausa, negativa ni baja de puja: si rinde mal, se revisa la página, la medición o el "
                     "valor de la conversión.")
    if corto and peor and peor.get("esperadas") and peor["esperadas"][2] is not None:
        L.append(f"- La que más gasta sin convertir es tuya: «{peor['texto']}» {fmoney(peor['costo'])}, "
                 f"{fnum(peor['esperadas'][2])} conversiones esperadas: muestra chica, no dice nada.")
    elif peor and peor.get("esperadas") and peor["esperadas"][2] is not None:
        a, b, m, nivel = peor["esperadas"]
        cvr, cpa, _ = K["base_de"](peor)
        L.append(f"- La que más gasta sin convertir: «{peor['texto']}» {fmoney(peor['costo'])}, {fnum(peor['clics'])} "
                 f"clics. Esperadas: {fnum(peor['clics'])} × {fpct2(100 * cvr)} = {fnum(a)}"
                 + (f" · {fmoney(peor['costo'])} ÷ {fmoney(cpa)} = {fnum(b)}" if b is not None else "")
                 + f" → {fnum(m)} (base: {nivel}). Con menos de 3, la muestra no dice nada.")
    if floja and floja.get("esperadas") and floja["esperadas"][2] is not None:
        a, b, m, nivel = floja["esperadas"]
        cvr, cpa, _ = K["base_de"](floja)
        L.append(f"- La tuya que menos convierte: «{floja['texto']}» (tema {floja['tema']}), {fnum(floja['conv'])} "
                 f"conversiones en {fclics(floja['clics'])}, CVR {fpct(100 * floja['conv'] / floja['clics'])} contra "
                 f"{fpct(100 * cvr)} de la base ({nivel}). Esperadas: {fnum(floja['clics'])} × {fpct2(100 * cvr)} = "
                 f"{fnum(a)}" + (f" · {fmoney(floja['costo'])} ÷ {fmoney(cpa)} = {fnum(b)}" if b is not None else "")
                 + f" → {fnum(m)}. Es de lo que vendes: no se le baja la puja ni se pausa. Si quieres saber por qué "
                 "convierte menos, mira su página de destino y qué pasa después del clic.")
    tocados = list(N["tocados"].values())
    if tocados:
        L.append("- Daño evitado (una negativa de frase las habría bloqueado): " + " · ".join(
            (f"«{u['texto']}»" if corto else f"«{u['texto']}» ({'convirtió' if u['cmax'] > 0 else u['motivo']})")
            for u in tocados[:tope(15, 6)])
            + (f" · y {len(tocados) - tope(15, 6)} más" if len(tocados) > tope(15, 6) else ""))
    res["protegidos"] = {"costo": suma(prot, "costo"), "n": len(prot), "tocados": [u["texto"] for u in tocados]}
    # ── hallazgos
    L += ["", sec("Dónde está el resto del dinero"), ""]
    hay = False
    for g in K["grupos"]:
        if g["estado"] in ("MUERTO", "ENFERMO"):
            hay = True
            L.append(f"- Grupo «{g['grupo']}» {g['estado']}: {fmoney(g['costo'])} ({fpct(pv(g['costo']))}), "
                     f"{fnum(g['clics'])} clics, {fnum(g['esperadas'])} conversiones esperadas y {fnum(g['conv'])} "
                     "observadas. El problema es la página, la oferta, el teléfono o la etiqueta de ESE grupo, no "
                     "sus palabras.")
    sanos = [g for g in K["grupos"] if g["estado"] == "sano"]
    chicos = [g for g in K["grupos"] if g["estado"] == "sin muestra"]
    if corto and (sanos or chicos):
        L.append(f"- Grupos: {len(sanos)} sano(s), {len(chicos)} sin muestra para juzgar.")
        sanos, chicos = [], []
    if sanos:
        L.append("- Grupos sanos (evaluado, sin hallazgo): " + " · ".join(
            f"«{g['grupo']}» {fnum(g['esperadas'])} esperadas / {fnum(g['conv'])} observadas" for g in sanos))
    if chicos:
        L.append("- Grupos sin muestra para juzgar (< 3 conversiones esperadas): " + " · ".join(
            f"«{g['grupo']}» {fmoney(g['costo'])}" for g in chicos))
    t3 = [t for t in fi.get("temas", []) if t.get("valor") == 3]
    tm = {t["id"]: t for t in temas(inf, us)}
    for t in t3:
        b = tm.get(t["id"])
        if b and "grupo" in b["regla"]:
            hay = True
            ms = b["miembros"]
            L.append(f"- El grupo «{b['regla']['grupo']}» compra búsquedas de algo que no vendes: "
                     f"{fmoney(suma(ms, 'costo'))}. Revisa sus palabras clave; las negativas sólo tapan el síntoma.")
    for u, t, cpc, med_g in K["g7"][:tope(5, 3)]:
        hay = True
        L.append(f"- CPC fuera de escala: «{u['texto']}» {fmoney(cpc)} por clic contra {fmoney(med_g)} de mediana en "
                 f"su grupo. Averigua por qué diverge (calidad del anuncio, otra campaña comprando lo mismo); no le "
                 "bajes la puja a ciegas.")
    if K.get("auto") and K["auto"]["terminos"]:
        hay = True
        a = K["auto"]
        L.append(f"- Auto-competencia: {a['terminos']} búsqueda(s) compradas por más de una campaña, "
                 f"{fmoney(a['costo'])}; sobrecosto contra el CPC más barato de tu propia cuenta: "
                 f"{fmoney(a['sobrecosto'])} ({fpct(pv(a['sobrecosto']))}).")
    if K.get("conc"):
        hay = True
        c = K["conc"]
        L.append(f"- Concordancia: referencia «{c['ref']}» a CPA {fmoney(c['cpa_ref'])}; exceso de los tipos más "
                 f"sueltos: {fmoney(c['exceso'])} ({fpct(pv(c['exceso']))}). Bajarlos también baja volumen.")
    for _, cat, r, ms in K["hallazgos"]:
        hay = True
        L.append(f"- «{SEMILLAS[cat][0]}»: {fmoney(suma(ms, 'costo'))}, convierte a {fnum(r, 2)} veces la cuenta. "
                 + ("Sepáralo en una campaña propia para ponerle su propio presupuesto." if r < 0.70 else "Está bien."))
    if not hay:
        L.append("- Nada que mover por estructura con lo que este archivo deja ver.")
    if K["grupos"] and sum(1 for g in K["grupos"] if g["estado"] != "sin muestra") and hay:
        L.append("- Las cifras de estos hallazgos pueden superponerse: no se suman.")
    # ── rendimiento
    L += ["", sec("Rendimiento (G8)"), ""]
    if not K["rendimiento"]:
        L.append("Recomendaciones por rendimiento sobre búsquedas: ninguna, porque " +
                 "; ".join(K["motivo_sin_rendimiento"]) + ".")
    elif g8:
        L.append("Ninguna acción por rendimiento sin tu respuesta. Estas búsquedas juntan 3 o más conversiones "
                 "esperadas y rinden bajo su base, pero no sé si son tuyas; si no lo son, pasan a la limpieza:")
        for u, acc, m in g8:
            L.append(f"- «{u['texto']}»: {fmoney(u['costo'])}, {fnum(u['clics'])} clics, {fnum(m)} conversiones "
                     f"esperadas, {fnum(u['cmax'])} observadas ({u['motivo']}).")
    else:
        neut = [u for u in us if u["estado"] == "neutro" and u["costo"] > 0]
        L.append("Ninguna búsqueda fuera de lo tuyo junta 3 conversiones esperadas: sin evidencia para cortar por "
                 "rendimiento" + (f" ({len(neut)} búsqueda(s) sin clasificar, {fmoney(suma(neut, 'costo'))})."
                                  if neut else "."))
    res["g8"] = [{"texto": u["texto"], "accion": a, "esperadas": m} for u, a, m in g8]
    # ── no evaluable
    L += ["", sec("Lo que no pude mirar (y qué lo destraba)"), ""]
    if corto and K["no_evaluable"]:
        L.append("- No evaluable con este archivo: " + " · ".join(f"{eje.split(' (')[0].lower()} ({razon})"
                                                              for eje, razon, _, _ in K["no_evaluable"])
                 + ". Qué lo destraba, con el dinero de cada uno: informe_completo.md.")
    for eje, razon, dinero, destraba in ([] if corto else K["no_evaluable"]):
        L.append(f"- {eje}: NO EVALUABLE — {razon}. Queda sin juzgar {fmoney(dinero)} "
                 f"({fpct(pv(dinero))} del gasto visible). Lo destraba: {destraba}.")
    if corto:
        extra = (["el gasto sin búsqueda visible (" + fmoney(cob["cuenta"] - cob["visible"]) + ")"]
                 if cob["pct"] is not None and cob["pct"] < 99.5 else []) + \
            ([] if geo else ["ubicaciones (falta el informe «Ubicaciones coincidentes»)"]) + \
            ["qué cambió y cuándo (una sola ventana)"]
        L.append("- Tampoco: " + " · ".join(extra) + ".")
    else:
        if cob["pct"] is not None and cob["pct"] < 99.5:
            L.append(f"- El gasto sin búsqueda visible: {fmoney(cob['cuenta'] - cob['visible'])}. Lo destraba: el "
                     "export de Campañas con la columna «Tipo de campaña», mismo período.")
        if not geo:
            L.append("- Ubicaciones: NO EVALUABLE sin el informe «Ubicaciones coincidentes»: no sé cuánto gasto viene "
                     f"de fuera de tu zona ni por «área de interés». Lo destraba: {RUTA_UBIC}.")
        L.append("- Qué cambió y cuándo: NO EVALUABLE con una sola ventana. Lo destraba: el mismo informe de la "
                 "ventana anterior, de igual duración, y el Historial de cambios.")
    # ── pendientes
    L += ["", sec("Decisiones pendientes tuyas"), ""]
    geo_preg = [u for u in (geo or {}).get("lugares", []) if u["estado"] == "pregunta" and u["costo"] > 0]
    if not (dudas or comp_ns or N["preguntas"] or props_ or geo_preg):
        L.append("Ninguna.")
    if geo_preg:
        L.append("- Ubicaciones sin decidir: " + " · ".join(
            f"{nombre_visible(u, geo['lugares'])} {fmoney(u['costo'])} ({u['motivo']})" for u in geo_preg[:12])
            + (f" · y {len(geo_preg) - 12} más" if len(geo_preg) > 12 else "") + ". ¿Atiendes ahí?")
    if props_:
        L.append(f"- Las {len(props_)} búsqueda(s) «para confirmar» de la limpieza ({fmoney(suma(props_, 'costo'))}): "
                 "dime si no las vendes y pasan a su lista.")
    if comp_ns:
        c = suma(comp_ns, "costo")
        L.append(f"- Competidores sin decidir ({fmoney(c)}, {fpct(pv(c))}): " + " · ".join(
            f"«{u['texto']}» {fmoney(u['costo'])}, {fnum(u['clics'])} clics, {fconv(u['conv'])}" for u in comp_ns)
                 + ". ¿Quieres aparecer cuando los buscan? No → negativa de frase con su nombre; sí → campaña "
                 "propia; mientras no decidas, no se tocan.")
    for p in N["preguntas"]:
        u = p["u"]
        if p["tipo"] == "sin_dato":
            L.append(f"- «{u['texto']}» ({fmoney(u['costo'])}) parece de otro negocio, pero el archivo no trae su dato "
                     "de conversiones («--»): no la corto sin saber si convirtió.")
        elif u["estado"] == "competidor":
            L.append(f"- «{u['texto']}» es de un competidor donde no quieres aparecer, pero convirtió "
                     f"({fnum(u['cmax'])} conv, {fmoney(u['costo'])}). ¿Lo cortamos igual? Mientras tanto no se toca.")
        else:
            L.append(f"- «{u['texto']}» parece de otro negocio pero convirtió ({fnum(u['cmax'])} conv, "
                     f"{fmoney(u['costo'])}). ¿Lo vendes? Mientras tanto no se toca; si nadie compra eso, revisa qué "
                     "cuenta como conversión.")
    if g8_solo:
        L.append(f"- Las {len(g8_solo)} búsqueda(s) de la sección 4 ({fmoney(suma(g8_solo, 'costo'))}): "
                 "dime si son tuyas.")
    if dudas:
        c = suma(dudas, "costo")
        L.append(f"- Búsquedas en duda ({fmoney(c)}, {fpct(pv(c))} del gasto visible): " + " · ".join(
            f"«{u['texto']}» {fmoney(u['costo'])}" + ("" if corto else f" ({u['motivo']})")
            for u in dudas[:tope(15, 8)])
                 + (f" · y {len(dudas) - tope(15, 8)} más" if len(dudas) > tope(15, 8) else "")
                 + ". Dime si son tuyas.")
    res["pendientes"] = {"costo": pend_costo, "dudas": [u["texto"] for u in dudas],
                         "competidores": [u["texto"] for u in comp_ns],
                         "convirtieron": [p["u"]["texto"] for p in N["preguntas"]]}
    # ── recomendación y procedencia
    res["gatillos"] = [f"{a}: {b}" for a, b in K["gatillos"]]
    if K["gatillos"]:
        g = K["gatillos"][0]
        L += ["", "## Recomendación", "",
              f"Lo que sigue ya es trabajo: {g[1]} ({g[0]}). Si tienes quien lo haga, esto es todo lo que necesitas. "
              "Si quieres que lo miremos nosotros, que publicamos este skill, estamos en "
              "[herihe.digital](https://herihe.digital/) — y si ya trabajas con una agencia, este informe sirve igual "
              "para conversarlo con ella."]
    L += ["", "*Auditoría hecha con el skill abierto **auditor-google-ads** de "
          "[herihe.digital](https://herihe.digital/auditor/) · MIT · sin credenciales.*"]
    L += ["", "## Ficha del negocio", "", "Guarda esta ficha y pégala al comienzo de tu próxima auditoría.", "",
          "```", render_ficha(inf, fi), "```"]
    oferta = ("OFERTA: sí, gatillo " + K["gatillos"][0][0] + " (va al final del informe, ya escrita)\n") \
        if K["gatillos"] else ""
    cab = "\n".join(RD) + "\n" + oferta + "\n===== INFORME (pega lo que sigue, sin esta marca ni la de fin) =====\n\n"
    res["oferta"] = bool(K["gatillos"])
    return cab + "\n".join(L) + "\n", res

def decidir(path, ficha, etiquetas=None, compra=None):
    """Para pruebas y para quien quiera usar el motor desde Python: devuelve (informe, búsquedas, negativas,
    compuertas) sin escribir archivos. etiquetas: {id: (etiqueta, palabra)} · compra: {id: 's'|'n'|'?'}"""
    inf = leer_informe(path)
    us = unicos(inf)
    E = {k: {"etiqueta": v[0], "palabra": v[1] if len(v) > 1 else ""} for k, v in (etiquetas or {}).items()}
    estados(inf, ficha, us, E, dict(compra or {}))
    N = negativas(inf, ficha, us)
    K = compuertas(inf, ficha, us)
    return inf, us, N, K


# ───────────────────────────── CLI ─────────────────────────────


def _args(argv):
    a, pos, i = {}, [], 0
    while i < len(argv):
        x = argv[i]
        if x.startswith("--"):
            k = x[2:].replace("-", "_")
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                a[k] = argv[i + 1]
                i += 2
                continue
            a[k] = True
        else:
            pos.append(x)
        i += 1
    return pos, a


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    pos, a = _args(argv)
    if not pos or pos[0] in ("-h", "--help", "ayuda"):
        print(__doc__)
        return
    if pos[0] == "version":
        print(VERSION)
        return
    cmd = {"leer": cmd_leer, "turno1": cmd_turno1, "ficha": cmd_ficha, "etiquetar": cmd_etiquetar,
           "auditar": cmd_auditar}.get(pos[0])
    if not cmd or len(pos) < 2:
        raise SystemExit("Uso: python3 auditor.py leer|turno1|ficha|etiquetar|auditar INFORME [opciones]")
    cmd(leer_informe(pos[1]), a)


if __name__ == "__main__":
    main()
