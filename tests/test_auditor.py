"""Pruebas del motor con una cuenta ficticia de control de plagas (ningún dato real).

Cada prueba es un control positivo: la trampa está en los datos y el motor tiene que esquivarla.
Correr: python3 -m pytest tests/
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auditor as A  # noqa: E402

ENC = ["Término de búsqueda", "Campaña", "Grupo de anuncios", "Tipo de concordancia", "Clics", "Impr.", "Costo",
       "Conversiones", "Todas las conv."]
C = "Búsqueda — Plagas"
FILAS = [
    # término, grupo, clics, impr, costo, conv
    ("fumigacion valparaiso", "Fumigación", 40, 400, 60000, 4),
    ("fumigacion viña del mar", "Fumigación", 20, 200, 30000, 2),
    ("fumigacion precio", "Fumigación", 10, 150, 15000, 0),
    ("fumigacion temuco", "Fumigación", 2, 20, 3000, 1),          # otra ciudad que CONVIRTIÓ
    ("fumigacion gratis", "Fumigación", 1, 10, 1500, 0),
    ("cotizacion gratis fumigacion", "Fumigación", 1, 10, 1500, 1),  # «gratis» de comprador
    ("curso de fumigacion", "Fumigación", 2, 30, 3000, 0),
    ("fumigador freelance", "Fumigación", 3, 30, 4500, 0),           # empleo
    ("desratizacion freelance", "Desratización", 0, 5, 0, 0),        # trae la palabra que vende
    ("desratizacion", "Desratización", 15, 150, 20000, 2),
    ("veneno para ratas", "Desratización", 5, 60, 6000, 0),
    ("como eliminar ratas", "Desratización", 4, 50, 5000, 0),
    ("sanitizacion de oficinas", "Sanitización", 5, 50, 7000, 0),
    ("limpieza de alfombras", "Sanitización", 4, 40, 5000, 0),
    ("lavado de alfombras", "Sanitización", 1, 10, 1000, 0),
    ("desinfeccion de ambientes", "Sanitización", 2, 20, 2500, 0),   # tema partido, no cae en ninguna parte
    ("plagasur fumigaciones", "Fumigación", 1, 5, 2000, 0),          # nombre desconocido
    ("control plagas temu", "Fumigación", 1, 8, 900, 0),             # temu ≠ temuco
    ("freesia fumigacion", "Fumigación", 0, 3, 0, 0),                # free ≠ freesia
]


def exporta(path, filas=FILAS, muerto=False, utf16=True, extra=()):
    lineas = ["Informe de términos de búsqueda", "1 de julio de 2026 - 28 de septiembre de 2026", "\t".join(ENC)]
    todas = list(filas) + list(extra)
    if muerto:
        todas.append(("termitas", "Termitas", 60, 600, 90000, 0))
    for t, g, cl, im, co, cv in todas:
        costo = f'"{co:,}"' if co >= 1000 else str(co)
        lineas.append("\t".join([t, C, g, "Phrase match", str(cl), str(im), costo, f"{cv:.2f}", f"{cv:.2f}"]))
    tot_cl = sum(f[2] for f in todas)
    tot_co = sum(f[4] for f in todas)
    tot_cv = sum(f[5] for f in todas)
    for nombre, factor in (("Total: Cuenta", 2), ("Total: Búsqueda", 2), ("Total: Términos de búsqueda", 1)):
        lineas.append("\t".join(["", "", nombre, "", str(tot_cl * factor), "", f'"{tot_co * factor:,}"',
                                 f"{tot_cv * factor:.2f}", f"{tot_cv * factor:.2f}"]))
    txt = "\n".join(lineas) + "\n"
    path.write_bytes(txt.encode("utf-16") if utf16 else txt.encode("utf-8"))
    return path


def ficha_base():
    return {
        "negocio": "control de plagas en Valparaíso",
        "zona": "Valparaíso y Viña del Mar",
        "temas": [{"id": "a", "valor": 1}, {"id": "b", "valor": 2},
                  {"id": "c", "valor": None, "partes": [
                      {"contiene": ["alfombra", "alfombras"], "valor": 3, "palabras_del_dueno": "alfombras no"},
                      {"contiene": ["sanitizacion"], "valor": 2, "palabras_del_dueno": "sanitización sí"}]}],
        "no_vende": [{"texto": "no vendemos venenos", "contiene": ["veneno"]}],
        "marca": [],
        "nombres": [{"nombre": "plagasur", "tipo": "b", "aparecer": "no_se"}],
        "cierre": "por WhatsApp", "cpa": "", "cambios": "no",
    }


def etiquetas_buenas(us):
    E = {}
    for u in us:
        t = u["texto"]
        if "freelance" in t:
            E[u["id"]] = ("empleo", "freelance")
        elif "curso" in t:
            E[u["id"]] = ("formacion", "curso")
        elif "veneno" in t:
            E[u["id"]] = ("otro_negocio", "veneno")
        elif t.startswith("como eliminar"):
            E[u["id"]] = ("hazlo_tu_mismo", "como eliminar")
        elif "alfombras" in t:
            E[u["id"]] = ("otro_negocio", "alfombras")
        elif "temuco" in t:
            E[u["id"]] = ("otra_zona", "temuco")
        elif t == "fumigacion gratis":
            E[u["id"]] = ("gratis", "gratis")
        elif "plagasur" in t:
            E[u["id"]] = ("competidor", "plagasur")
        elif "desinfeccion" in t:
            E[u["id"]] = ("otro_negocio", "desinfeccion")   # la IA se equivoca a propósito
        else:
            E[u["id"]] = ("nucleo", "")
    return E


def corre(tmp_path, ficha=None, muerto=False, cambia=None):
    f = exporta(tmp_path / "informe.csv", muerto=muerto)
    inf = A.leer_informe(f)
    us = A.unicos(inf)
    E = etiquetas_buenas(us)
    if cambia:
        E.update({u["id"]: cambia[u["texto"]] for u in us if u["texto"] in cambia})
    C_ = {k: "n" if v[0] in A.AJENAS else "s" for k, v in E.items()}
    return A.decidir(f, ficha or ficha_base(), E, C_)


def bloqueadas(N):
    return {u["texto"] for u in N["bloqueados"]}


# ─── lectura ───

def test_lee_utf16_tabulador_y_descarta_totales_en_tercera_columna(tmp_path):
    inf = A.leer_informe(exporta(tmp_path / "x.csv"))
    assert inf["encoding"] == "UTF-16" and inf["delim"] == "tabulador"
    assert len(inf["terminos"]) == len(FILAS)
    assert not any(t["texto"].lower().startswith("total") for t in inf["terminos"])
    assert A.suma(inf["terminos"], "costo") == sum(f[4] for f in FILAS)
    assert A.cobertura(inf)["pct"] == pytest.approx(50.0)
    assert inf["dias"] == 90


def test_desconocido_nunca_es_cero_y_decimales_chilenos(tmp_path):
    assert A.num("--", "en") is None and A.num(" —", "es") is None
    assert A.num('"97,904"', "en") == 97904 and A.num("0,50", "es") == 0.5 and A.num("$122.231", "es") == 122231
    assert A.detectar_locale(["1,5", "$122.231", "2"]) == "es"
    assert A.detectar_locale(["2.00", '"6,751"']) == "en"


def test_tabla_pegada_con_texto_antes(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("Tengo una pyme, en Chile. Estas son mis palabras de los últimos 50 días.\n\n"
                 "Palabra clave | Clics | Costo | Conversiones\n---|---|---|---\n"
                 "fumigacion | 48 | $122.231 | 5\ndesratizacion | 29 | $74.386 | 1,5\n", encoding="utf-8")
    inf = A.leer_informe(p)
    assert inf["tipo"] == "palabras_clave" and inf["dias"] == 50
    assert [t["costo"] for t in inf["terminos"]] == [122231, 74386]
    assert [t["conv"] for t in inf["terminos"]] == [5, 1.5]


def test_archivo_en_una_columna_no_es_nada(tmp_path):
    p = tmp_path / "malo.csv"
    p.write_text("hola\nmundo\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        A.leer_informe(p)


# ─── temas y frontera de palabra ───

def test_temu_no_toca_temuco_y_free_no_toca_freesia(tmp_path):
    inf = A.leer_informe(exporta(tmp_path / "x.csv"))
    us = A.unicos(inf)
    temuco = next(u for u in us if u["texto"] == "fumigacion temuco")
    freesia = next(u for u in us if u["texto"] == "freesia fumigacion")
    assert "tercero" not in A.semillas_de(temuco)
    assert "gratis" not in A.semillas_de(freesia)
    cot = next(u for u in us if u["texto"] == "cotizacion gratis fumigacion")
    assert "gratis" not in A.semillas_de(cot)          # «cotización gratis» es comprador
    _, hits = A.simular(us, "temu")
    assert {h["texto"] for h in hits} == {"control plagas temu"}


def test_temas_son_estables(tmp_path):
    f = exporta(tmp_path / "x.csv")
    t1 = [(t["id"], t["nombre"], json.dumps(t["regla"])) for t in A.temas(A.leer_informe(f))]
    t2 = [(t["id"], t["nombre"], json.dumps(t["regla"])) for t in A.temas(A.leer_informe(f))]
    assert t1 == t2 and t1[0][1] == "Fumigación"


# ─── protección y simulación de daño ───

def test_freelance_sin_respuesta_del_dueno_es_duda(tmp_path):
    """«freelance» es semilla débil («contratar freelance» compra): dentro de un tema vendido no corta sola."""
    _, us, N, _ = corre(tmp_path)
    u = next(u for u in us if u["texto"] == "fumigador freelance")
    assert u["estado"] == "duda" and not bloqueadas(N) & {"fumigador freelance", "desratizacion freelance"}


def test_frase_vetada_si_toca_lo_que_vende(tmp_path):
    """El dueño dijo «freelance no»: la frase igual toca «desratizacion freelance» (tema 2) y baja a exacta."""
    fi = ficha_base()
    fi["no_vende"].append({"texto": "freelance no", "contiene": ["freelance"]})
    _, us, N, _ = corre(tmp_path, ficha=fi)
    frases = {f["frase"] for L in N["listas"].values() for f in L["frases"]}
    assert "freelance" not in frases
    assert "fumigador freelance" in bloqueadas(N)
    assert "desratizacion freelance" not in bloqueadas(N)


def test_ajena_que_convirtio_nunca_se_bloquea(tmp_path):
    fi = ficha_base()
    fi["no_vende"].append({"texto": "no vendemos venenos", "contiene": ["ratas"]})
    _, us, N, _ = corre(tmp_path, ficha=fi, cambia={"desratizacion": ("otro_negocio", "")})
    assert "fumigacion temuco" not in bloqueadas(N)
    assert all(p["u"]["cmax"] > 0 or p["tipo"] == "sin_dato" for p in N["preguntas"])


def test_otra_zona_nunca_se_corta_sola(tmp_path):
    """«Atendemos Temuco, no Santiago» no se distingue de «Temuco no» por reglas: otra zona siempre se pregunta."""
    _, us, N, _ = corre(tmp_path)
    u = next(u for u in us if u["texto"] == "fumigacion temuco")
    assert u["estado"] == "propuesta" and "fumigacion temuco" not in bloqueadas(N)


def test_etiqueta_equivocada_de_la_ia_no_pasa_en_tema_partido(tmp_path):
    """La IA dice «otro_negocio» para «desinfeccion de ambientes»; el dueño partió el tema y vende una parte."""
    _, us, N, _ = corre(tmp_path)
    u = next(u for u in us if u["texto"] == "desinfeccion de ambientes")
    assert u["estado"] == "duda"
    assert "desinfeccion de ambientes" not in bloqueadas(N)


def test_etiqueta_equivocada_en_tema_1_es_duda(tmp_path):
    _, us, N, _ = corre(tmp_path, cambia={"fumigacion precio": ("otro_negocio", "precio")})
    u = next(u for u in us if u["texto"] == "fumigacion precio")
    assert u["estado"] == "duda" and "fumigacion precio" not in bloqueadas(N)


def test_nucleo_nunca_recibe_accion_por_rendimiento(tmp_path):
    _, us, N, K = corre(tmp_path)
    protegidos = {u["texto"] for u in us if u["estado"] == "protegido"}
    assert "fumigacion valparaiso" in protegidos
    assert not ({u["texto"] for u, _, _ in K["g8"]} & protegidos)
    assert not (bloqueadas(N) & protegidos)


def test_competidor_no_se_es_pregunta(tmp_path):
    _, us, N, _ = corre(tmp_path)
    u = next(u for u in us if u["texto"] == "plagasur fumigaciones")
    assert u["estado"] == "competidor" and u["aparecer"] == "no_se"
    assert "plagasur fumigaciones" not in bloqueadas(N)


def test_competidor_no_aparecer_va_en_frase_sin_plural(tmp_path):
    fi = ficha_base()
    fi["nombres"] = [{"nombre": "plagasur", "tipo": "b", "aparecer": "no"}]
    _, us, N, _ = corre(tmp_path, ficha=fi)
    comp = N["listas"]["Competidores"]
    assert [f["frase"] for f in comp["frases"]] == ["plagasur"]
    assert comp["sims"][0]["variantes"] == ["plagasur"]


def test_limpieza_de_lo_declarado_sale_en_frase_con_simulacion_completa(tmp_path):
    _, us, N, _ = corre(tmp_path)
    frases = {f["frase"]: f for L in N["listas"].values() for f in L["frases"]}
    assert "alfombras" in frases or "alfombra" in frases
    f = frases.get("alfombras") or frases["alfombra"]
    assert {h["texto"] for h in f["hits"]} == {"limpieza de alfombras", "lavado de alfombras"}
    assert "veneno" in frases and "veneno para ratas" in bloqueadas(N)


# ─── números ───

def test_esperadas_son_la_menor_de_las_dos(tmp_path):
    _, us, N, K = corre(tmp_path)
    u = next(u for u in us if u["texto"] == "fumigacion precio")
    a, b, m, nivel = u["esperadas"]
    cvr, cpa, _ = K["base_de"](u)
    assert a == pytest.approx(u["clics"] * cvr) and b == pytest.approx(u["costo"] / cpa)
    assert m == min(a, b)


def test_limpieza_suma_lo_mismo_que_sus_terminos(tmp_path):
    inf, us, N, K = corre(tmp_path)
    rep, res = A.informe(inf, ficha_base(), us, N, K, {})
    assert res["limpieza"]["costo"] == sum(u["costo"] for u in N["bloqueados"])
    assert sum(v["costo"] for v in res["listas"].values()) == res["limpieza"]["costo"]
    assert A.fmoney(res["limpieza"]["costo"]) in rep


# ─── oferta: sólo con gatillo ───

def test_sin_gatillo_no_hay_oferta(tmp_path):
    inf, us, N, K = corre(tmp_path)
    rep, res = A.informe(inf, ficha_base(), us, N, K, {})
    assert res["oferta"] is False and "quieres que lo miremos" not in rep


def test_grupo_muerto_dispara_oferta_con_su_nombre(tmp_path):
    inf, us, N, K = corre(tmp_path, muerto=True)
    rep, res = A.informe(inf, ficha_base(), us, N, K, {})
    assert res["oferta"] is True and any("Termitas" in g for g in res["gatillos"])
    assert "Termitas" in rep.split("## Recomendación")[1]


# ─── ficha literal ───

def test_ficha_rechaza_glosa(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exporta(tmp_path / "informe.csv")
    (tmp_path / "respuestas.txt").write_text("P1: control de plagas en Valparaíso y Viña del Mar", encoding="utf-8")
    fi = ficha_base()
    fi["negocio"] = "control de plagas para empresas y hogares"   # glosa: el dueño no lo dijo
    (tmp_path / "ficha.json").write_text(json.dumps(fi), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        A.cargar_ficha(A.leer_informe(tmp_path / "informe.csv"), {})
    assert "negocio" in str(e.value)


def test_sinonimo_de_la_ia_va_a_supuestos(tmp_path):
    inf = A.leer_informe(exporta(tmp_path / "x.csv"))
    fi = ficha_base()
    fi["temas"][2]["partes"][0]["contiene"] = ["alfombras", "tapetes"]
    txt = A.render_ficha(inf, fi)
    assert "Supuestos (míos, no del dueño): cuento «tapetes»" in txt


# ─── flujo completo por la línea de comandos ───

def test_flujo_completo(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    exporta(tmp_path / "informe.csv")
    A.main(["leer", "informe.csv"])
    (tmp_path / "nombres.txt").write_text("plagasur\nlugar: temuco\n", encoding="utf-8")
    A.main(["turno1", "informe.csv"])
    t1 = capsys.readouterr().out
    assert "**P1b" in t1 and "«plagasur»" in t1 and "temuco" in t1
    (tmp_path / "respuestas.txt").write_text(
        "control de plagas en Valparaíso · Valparaíso y Viña del Mar · a) fumigación 1 · b) desratización 2 · "
        "alfombras no · sanitización sí · no vendemos venenos · plagasur no sé quién es · temuco no · por WhatsApp · "
        "no",
        encoding="utf-8")
    fi = ficha_base()
    fi["temas"][0]["palabras_del_dueno"] = "a) fumigación 1"
    fi["temas"][1]["palabras_del_dueno"] = "b) desratización 2"
    fi["nombres"] = [{"nombre": "plagasur", "tipo": "e", "aparecer": None,
                      "palabras_del_dueno": "plagasur no sé quién es"}]
    (tmp_path / "ficha.json").write_text(json.dumps(fi), encoding="utf-8")
    inf = A.leer_informe(tmp_path / "informe.csv")
    us = A.unicos(inf)
    E = etiquetas_buenas(us)
    (tmp_path / "etiquetas.csv").write_text("\n".join(f"{k};{v[0]};{v[1]}" for k, v in E.items()), encoding="utf-8")
    (tmp_path / "compra.csv").write_text("\n".join(f"{k};s" for k in E), encoding="utf-8")
    try:
        A.main(["auditar", "informe.csv"])
    except SystemExit as e:        # puede pedir etiquetas de términos sin costo: se las damos
        assert "FALTAN ETIQUETAS" in str(e)
        ids = str(e).split(":")[1].split()[0].split("\n")[0].split(",")
        with open(tmp_path / "etiquetas.csv", "a", encoding="utf-8") as fh:
            fh.write("\n" + "\n".join(f"{i};no_se;" for i in ids))
        A.main(["auditar", "informe.csv"])
    out = capsys.readouterr().out
    assert "===== INFORME" in out and "FICHA DEL NEGOCIO" in out
    res = json.loads((tmp_path / "resultado.json").read_text(encoding="utf-8"))
    assert res["oferta"] is False


def test_ficha_exige_la_frase_que_sostiene_cada_decision(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exporta(tmp_path / "informe.csv")
    (tmp_path / "respuestas.txt").write_text("control de plagas en Valparaíso", encoding="utf-8")
    fi = {"negocio": "control de plagas en Valparaíso", "temas": [{"id": "a", "valor": 1}],
          "nombres": [{"nombre": "plagasur", "tipo": "b", "aparecer": "no"}]}
    (tmp_path / "ficha.json").write_text(json.dumps(fi), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        A.cargar_ficha(A.leer_informe(tmp_path / "informe.csv"), {})
    assert "temas.a.palabras_del_dueno" in str(e.value) and "plagasur" in str(e.value)


def test_sin_respuestas_no_admite_decisiones_inventadas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exporta(tmp_path / "informe.csv")
    fi = {"sin_respuestas": True, "nombres": [{"nombre": "plagasur", "tipo": "b", "aparecer": "no"}]}
    (tmp_path / "ficha.json").write_text(json.dumps(fi), encoding="utf-8")
    with pytest.raises(SystemExit):
        A.cargar_ficha(A.leer_informe(tmp_path / "informe.csv"), {})


# ─── ubicaciones ───

def exporta_geo(path, filas):
    """filas: (lugar, tipo, clics, costo, conv) — formato «Ubicaciones coincidentes» de la interfaz"""
    L = ["Ubicaciones coincidentes", "1 de julio de 2026 - 28 de septiembre de 2026",
         "Ubicación coincidente,Tipo de ubicación,Campaña,Clics,Impr.,Costo,Conversiones,Todas las conv."]
    for lugar, tipo, cl, co, cv in filas:
        L.append(f'"{lugar}",{tipo},{C},{cl},{cl * 10},{co},{cv:.2f},{cv:.2f}')
    L.append(f"Total: Cuenta,,,{sum(f[2] for f in filas)},,{sum(f[3] for f in filas)},"
             f"{sum(f[4] for f in filas):.2f},{sum(f[4] for f in filas):.2f}")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


GEO = [("Valparaíso, Valparaíso, Chile", "Ubicación física", 200, 200000, 20),
       ("Viña del Mar, Valparaíso, Chile", "Ubicación física", 100, 100000, 10),
       ("Temuco, Araucanía, Chile", "Ubicación física", 20, 20000, 0),
       ("Santiago, Región Metropolitana, Chile", "Ubicación física", 10, 10000, 2)]


def test_geo_lugar_que_nombro_el_dueno_queda_dentro_aunque_la_ia_diga_fuera(tmp_path):
    G = A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", GEO))
    us = A.lugares_unicos(G)
    E = {u["id"]: "fuera" for u in us}                      # la IA se equivoca en todo
    o = A.geo_decidir(G, {"zona": "Valparaíso y Viña del Mar"}, E)
    est = {A.corto(u): u["estado"] for u in o["lugares"]}
    assert est["Valparaíso"] == "dentro" and est["Viña del Mar"] == "dentro"
    assert est["Temuco"] == "fuera"                          # sin conversiones: para confirmar
    assert est["Santiago"] == "pregunta"                     # convirtió: pregunta, nunca exclusión


def test_geo_interes_que_convierte_bien_no_se_toca(tmp_path):
    filas = GEO[:2] + [("Valparaíso, Valparaíso, Chile", "Área de interés", 100, 100000, 10)]
    o = A.geo_decidir(A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", filas)), {"zona": "Valparaíso"}, {})
    assert o["tipo"]["interes"]["veredicto"] == "sano" and o["gatillo"] is None


def test_geo_interes_que_no_convierte_dispara_el_gatillo(tmp_path):
    filas = GEO[:2] + [("Valparaíso, Valparaíso, Chile", "Área de interés", 100, 100000, 0)]
    o = A.geo_decidir(A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", filas)), {"zona": "Valparaíso"}, {})
    assert o["tipo"]["interes"]["veredicto"] == "enfermo" and "interés" in o["gatillo"]


def test_geo_en_el_informe_y_sin_archivo_no_evaluable(tmp_path, monkeypatch, capsys):
    inf, us, N, K = corre(tmp_path)
    rep, res = A.informe(inf, ficha_base(), us, N, K, {})
    assert "Ubicaciones: NO EVALUABLE" in rep and "Ubicaciones coincidentes" in rep
    G = A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", GEO))
    geo = A.geo_decidir(G, ficha_base(), {u["id"]: "fuera" for u in A.lugares_unicos(G)})
    rep, res = A.informe(inf, ficha_base(), us, N, K, {}, geo)
    assert "Fuera de tu zona, para confirmar" in rep and "exclúyelas" in rep
    assert [x[0] for x in res["ubicaciones"]["fuera"]] == ["Temuco, Araucanía, Chile"]
    assert "Santiago" in rep.split("Decisiones pendientes")[1]


def test_geo_faltan_etiquetas_de_lugares(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exporta(tmp_path / "informe.csv")
    exporta_geo(tmp_path / "u.csv", GEO)
    (tmp_path / "respuestas.txt").write_text("control de plagas en Valparaíso · Valparaíso y Viña del Mar · a) "
                                             "fumigación 1", encoding="utf-8")
    fi = {"negocio": "control de plagas en Valparaíso", "zona": "Valparaíso y Viña del Mar",
          "temas": [{"id": "a", "valor": 1, "palabras_del_dueno": "a) fumigación 1"}]}
    (tmp_path / "ficha.json").write_text(json.dumps(fi), encoding="utf-8")
    inf = A.leer_informe(tmp_path / "informe.csv")
    E = {u["id"]: ("nucleo", "") for u in A.unicos(inf)}
    (tmp_path / "etiquetas.csv").write_text("\n".join(f"{k};{v[0]};" for k, v in E.items()), encoding="utf-8")
    (tmp_path / "compra.csv").write_text("\n".join(f"{k};s" for k in E), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        A.main(["auditar", "informe.csv", "--ubicaciones", "u.csv"])
    assert "FALTAN LUGARES" in str(e.value)


def test_geo_region_en_ingles_y_lugar_que_contiene_la_zona(tmp_path):
    filas = [("Maipu, Maipu, Santiago Metropolitan Region, Chile", "Ubicación física", 20, 20000, 0),
             ("Viña del Mar, Valparaíso, Chile", "Ubicación física", 50, 50000, 5),
             ("Valparaíso, Chile", "Ubicación física", 10, 10000, 0),
             ("Chile", "Ubicación física", 10, 10000, 0)]
    G = A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", filas))
    todo_fuera = {u["id"]: "fuera" for u in A.lugares_unicos(G)}
    o = A.geo_decidir(G, {"zona": "Toda la Región Metropolitana"}, todo_fuera)
    est = {u["lugar"]: u["estado"] for u in o["lugares"]}
    assert est["Maipu, Maipu, Santiago Metropolitan Region, Chile"] == "dentro"
    o = A.geo_decidir(G, {"zona": "Viña del Mar"}, todo_fuera)
    est = {u["lugar"]: u["estado"] for u in o["lugares"]}
    assert est["Valparaíso, Chile"] == "dentro" and est["Chile"] == "dentro"   # contienen la zona


def test_geo_mismo_nombre_que_convirtio_no_se_excluye(tmp_path):
    filas = [("Santiago, Región Metropolitana, Chile", "Ubicación física", 20, 20000, 2),
             ("Santiago, Santiago, Región Metropolitana, Chile", "Ubicación física", 20, 20000, 0)]
    G = A.leer_ubicaciones(exporta_geo(tmp_path / "u.csv", filas))
    o = A.geo_decidir(G, {"zona": "Valparaíso"}, {u["id"]: "fuera" for u in A.lugares_unicos(G)})
    assert all(u["estado"] == "pregunta" for u in o["lugares"])


def test_geo_columnas_separadas_y_fila_sin_lugar(tmp_path):
    p = tmp_path / "u.csv"
    p.write_text("Ubicaciones\n1 de julio de 2026 - 28 de septiembre de 2026\n"
                 "País/territorio,Región,Ciudad,Tipo de ubicación,Clics,Costo,Conversiones\n"
                 "Chile,Valparaíso,San Pedro,Ubicación física,10,5000,1.00\n"
                 "Chile,Región Metropolitana,San Pedro,Ubicación física,10,8000,0.00\n"
                 "--,--,--,Área de interés,10,4000,0.00\n"
                 "Total: Cuenta,,,,30,17000,1.00\n", encoding="utf-8")
    G = A.leer_ubicaciones(p)
    lugares = {u["lugar"] for u in A.lugares_unicos(G)}
    assert "San Pedro, Valparaíso, Chile" in lugares and "San Pedro, Región Metropolitana, Chile" in lugares
    assert "(sin ubicación)" in lugares and A.suma(G["filas"], "costo") == 17000


# ─── correcciones del eval 27-set ───

def test_no_vendemos_x_tiene_que_quedar_en_la_ficha(tmp_path):
    inf = A.leer_informe(exporta(tmp_path / "x.csv"))
    fi = ficha_base()
    fi["no_vende"] = []
    errores = A.no_vende_sin_regla(inf, fi, "P1: control de plagas. No vendemos venenos ni hacemos jardinería.")
    assert any("No vendemos venenos" in e for e in errores) and any("ni hacemos jardinería" in e for e in errores)
    fi["no_vende"] = [{"texto": "No vendemos venenos", "contiene": ["veneno"]},
                      {"texto": "ni hacemos jardinería", "contiene": ["jardineria"]}]
    assert A.no_vende_sin_regla(inf, fi, "P1: control de plagas. No vendemos venenos ni hacemos jardinería.") == []


def test_competidor_con_palabra_del_negocio_negativa_solo_el_nombre(tmp_path):
    """«plagasur fumigaciones» anotado como nombre: la frase negativa es «plagasur», nunca «fumigaciones»."""
    fi = ficha_base()
    fi["nombres"] = [{"nombre": "plagasur fumigaciones", "tipo": "b", "aparecer": "no"}]
    _, us, N, _ = corre(tmp_path, ficha=fi)
    frases = {f["frase"] for L in N["listas"].values() for f in L["frases"]}
    assert "plagasur" in frases and not any("fumigacion" in f for f in frases)


def test_primera_linea_con_unidades_y_sin_linea_de_oferta(tmp_path):
    fi = ficha_base()
    fi["no_vende"].append({"texto": "freelance no", "contiene": ["freelance"]})
    inf, us, N, K = corre(tmp_path, ficha=fi)
    rep, res = A.informe(inf, fi, us, N, K, {})
    cab = rep.split("===== INFORME")[0]
    assert "negativa(s)" in cab and "búsqueda(s)" in cab and "OFERTA" not in cab


def test_regla_3_del_dueno_manda_sobre_el_no_se_de_la_ia(tmp_path):
    """eval3: el dueño dijo «freelance → 3» y la IA etiquetó no_se: se corta igual (sin palabra de lo que vende)."""
    fi = ficha_base()
    fi["no_vende"].append({"texto": "freelance no", "contiene": ["freelance"]})
    f = exporta(tmp_path / "informe.csv")
    us0 = A.unicos(A.leer_informe(f))
    E = etiquetas_buenas(us0)
    k = next(u["id"] for u in us0 if u["texto"] == "fumigador freelance")
    E[k] = ("no_se", "")
    C_ = {i: "n" if v[0] in A.AJENAS else "s" for i, v in E.items()}
    C_[k] = "?"                                   # como en el eval3: «no sé» y «?»
    _, us, N, _ = A.decidir(f, fi, E, C_)
    u = next(u for u in us if u["texto"] == "fumigador freelance")
    assert u["estado"] == "ajena" and u["palabra"] == "freelance" and "fumigador freelance" in bloqueadas(N)
    C_[k] = "s"                                   # si la IA dice que podría comprar, hay conflicto: se pregunta
    _, us, N, _ = A.decidir(f, fi, E, C_)
    assert next(u for u in us if u["texto"] == "fumigador freelance")["estado"] == "duda"


def test_parte_vendida_de_tema_partido_tiene_que_quedar_en_la_ficha(tmp_path):
    """eval5: la parte «X sí la vendemos» se perdió de la ficha y el programa no lo notó."""
    fi = ficha_base()
    resp = "c) alfombras no; la sanitización de oficinas sí la vendemos"
    fi["temas"][2]["partes"] = [p for p in fi["temas"][2]["partes"] if p["valor"] == 3]
    assert A.si_vende_sin_parte(fi, resp)
    fi["temas"][2]["partes"].append({"contiene": ["sanitizacion"], "valor": 2,
                                     "palabras_del_dueno": "la sanitización de oficinas sí la vendemos"})
    assert A.si_vende_sin_parte(fi, resp) == []


def test_tema_partido_no_toma_el_valor_de_una_parte():
    """eval6: la frase de una parte («… sí la vendemos (2)») subió a 2 el tema entero y protegió lo que el dueño no
    había contestado; y como la frase quedó en el tema, la revisión de partes vendidas la dio por recogida."""
    tms = {"c": {"nombre": "AG Limpieza Sanitizacion"}}
    fi = ficha_base()
    c = fi["temas"][2]
    resp = "c) alfombras no; la sanitización de oficinas sí la vendemos (2)"
    c["partes"] = [p for p in c["partes"] if p["valor"] == 3]
    c["valor"], c["palabras_del_dueno"] = 2, "la sanitización de oficinas sí la vendemos (2)"
    assert A.si_vende_sin_parte(fi, resp)                  # la frase en el tema no cuenta como parte vendida
    assert A.valor_de_tema_partido(fi, tms)                # y el 2 es de la parte, no del resto
    c["partes"].append({"contiene": ["sanitizacion"], "valor": 2, "palabras_del_dueno": "la sanitización de oficinas "
                        "sí la vendemos (2)"})
    assert A.valor_de_tema_partido(fi, tms)                # con la parte ya puesta, el tema sigue sin respuesta
    for frase in ("Limpieza: alfombras no", "Sanitizacion 2"):    # la palabra de la parte junto al número no vale
        c["palabras_del_dueno"] = frase
        assert A.valor_de_tema_partido(fi, tms), frase
    for frase in ("alfombras no, lo demás 2", "c) 2, menos alfombras"):
        c["palabras_del_dueno"] = frase
        assert A.valor_de_tema_partido(fi, tms) == [], frase
    c["valor"], c["palabras_del_dueno"] = None, ""
    assert A.valor_de_tema_partido(fi, tms) == []
