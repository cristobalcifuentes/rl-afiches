"""Baja los datos publicos de THE ORIGIN desde la API de MatchZone (solo lectura, sin cuenta).

Uso (desde esta carpeta):  python bajar.py [edicion]
- datos/<AAAA-MM-DD>/: los JSON tal como los entrega MatchZone y la planilla de cada partido jugado.
- datos/consolidado.json: todo ordenado por fecha y partido, con las claves de equipo de RL
  (las de programacion-fecha/build.py). Se lee con resultados.py. Copia en la carpeta del dia.
- datos/resumen.txt: lo mismo, legible. Copia en la carpeta del dia.

Los goles de cada partido no son publicos: se reparten por diferencia con el consolidado anterior
(ver repartir_goles). Por eso hay que correrlo despues de cada fecha y no borrar consolidado.json.
"""
import collections
import datetime
import importlib.util
import json
import pathlib
import re
import shutil
import sys
import unicodedata
import urllib.request

API = "https://api.matchzone.cl/api/competitions"
EDICION = int(sys.argv[1]) if len(sys.argv) > 1 else 28  # 28 = Rancagua League, THE ORIGIN
HERE = pathlib.Path(__file__).resolve().parent
DATOS = HERE / "datos"
ARCHIVOS = {  # archivo: ruta bajo /editions/<id>
    "edicion": "", "fixture": "/fixture", "tabla": "/standings", "goleadores": "/scorers",
    "mvps": "/mvps", "tarjetas": "/discipline", "suspensiones": "/suspensions",
    "participantes": "/participants", "copas": "/cups",
}

# Nombre en MatchZone (normalizado con clave_nombre) -> clave de RL. Si MatchZone cambia un nombre,
# el programa se detiene y hay que sumarlo aqui.
ALIAS = {
    "rabanal": ["independienterabanal", "cdindependienterabanal"],
    "pierde-nunca": ["lospierdenunca"],
    "saca-chispas": ["lossacachispas"],
    "cerveceros": ["cervecerosfc", "cerveceros"],
    "camajo": ["camajoclubdefutbol", "camajofc", "camajocfc"],
    "gatinhos": ["gatinhosfc", "gatinhos"],
    "capybara": ["capibarasfc", "capybarafc", "capibarafc"],
    "irresponsables": ["irresponsablesfc"],
    "profesores": ["profesoresfc"],
    "control-dirigido": ["academiadeportivacontroldirigido", "controldirigido"],
    "rusticos": ["rusticosfc"],
    "ikigai-rcv": ["ikigaircv"],
    "bototos": ["bototosfc", "bototos"],
    "inter": ["equipo14pordefinir", "interderancagua", "irn", "irnrancagua"],
}
CLAVE = {a: k for k, v in ALIAS.items() for a in v}


def cargar_nombres():
    """NAMES de programacion-fecha/build.py (nombres de presentacion de RL)."""
    spec = importlib.util.spec_from_file_location("prog", HERE.parent / "programacion-fecha" / "build.py")
    prog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prog)
    return prog.NAMES


def clave_nombre(nombre):
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    if s not in CLAVE:
        raise SystemExit(f"Equipo desconocido en MatchZone: {nombre!r}. Sumarlo a ALIAS en bajar.py.")
    return CLAVE[s]


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "RL-datos/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def escribir(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- consolidado
def consolidar(raw, planillas, previo, names):
    avisos = []
    grupo = {clave_nombre(t["participantName"]): t["groupNumber"] for t in raw["tabla"]}

    equipos = {}
    for t in raw["tabla"]:
        k = clave_nombre(t["participantName"])
        equipos[k] = {"nombre": names[k], "nombre_mz": t["participantName"], "grupo": t["groupNumber"],
                      "inscripcion_mz": t["enrollmentId"], "logo_mz": t["logoUrl"]}
    if equipos.get("inter", {}).get("nombre_mz", "").startswith("Equipo 14"):
        avisos.append('En MatchZone, Inter de Rancagua sigue como "Equipo 14 (por definir)".')

    tabla = {}
    for t in raw["tabla"]:
        tabla.setdefault(str(t["groupNumber"]), []).append({
            "pos": len(tabla.get(str(t["groupNumber"]), [])) + 1, "equipo": clave_nombre(t["participantName"]),
            "pj": t["played"], "g": t["won"], "e": t["drawn"], "p": t["lost"], "gf": t["primaryFor"],
            "gc": t["primaryAgainst"], "dif": t["primaryDiff"], "pts": t["points"], "desempate": t["tiebreakReason"]})

    partidos = {}
    for m in raw["fixture"]:
        loc, vis = clave_nombre(m["homeName"]), clave_nombre(m["awayName"])
        jugado = m["status"] == "PLAYED"
        p = {
            "id": m["id"], "fecha": m["round"], "dia": m["matchDate"], "hora": (m["matchTime"] or "")[:5] or None,
            "cancha": int(re.sub(r"\D", "", m["courtName"])) if m["courtName"] else None,
            "grupo": grupo.get(loc), "local": loc, "visita": vis, "estado_mz": m["status"], "jugado": jugado,
            "marcador": [m["homeScore"], m["awayScore"]] if jugado else None,
            "penales": [m["homePenalties"], m["awayPenalties"]] if m["homePenalties"] is not None else None,
            "walkover": m["walkoverWinner"], "contexto": m["matchContext"], "goles_asignados_mz": m["goalsAssigned"],
            "goles": {"local": [], "visita": []}, "goles_sin_asignar": None,
            "tarjetas": {"local": [], "visita": []}, "mvp": None, "firmas": None,
        }
        pl = planillas.get(m["id"])
        if pl:
            for lado, k in (("local", "homePlayers"), ("visita", "awayPlayers")):
                equipo = loc if lado == "local" else vis
                for x in pl[k]:
                    if x["yellowCards"] or x["redCards"]:
                        p["tarjetas"][lado].append({"jugador": x["fullName"], "id": x["userId"],
                                                    "amarillas": x["yellowCards"], "rojas": x["redCards"],
                                                    "motivo": x["cardReason"]})
                    if x["mvp"]:
                        p["mvp"] = {"jugador": x["fullName"], "id": x["userId"], "numero": x["jerseyNumber"],
                                    "equipo": equipo, "foto_mz": x["photoUrl"]}
            p["firmas"] = {lado: [sum(x["signed"] for x in pl[k]), len(pl[k])]
                           for lado, k in (("local", "homePlayers"), ("visita", "awayPlayers"))}
        partidos[m["id"]] = p

    repartir_goles(raw["goleadores"], partidos, previo, avisos)

    for p in partidos.values():
        if p["jugado"]:
            p["goles_sin_asignar"] = {lado: p["marcador"][i] - sum(g["goles"] for g in p["goles"][lado])
                                      for i, lado in enumerate(("local", "visita"))}
            falta = sum(p["goles_sin_asignar"].values())
            if falta:
                avisos.append(f"Fecha {p['fecha']}, {names[p['local']]} {p['marcador'][0]}-{p['marcador'][1]} "
                              f"{names[p['visita']]}: " + ("falta 1 gol" if falta == 1 else f"faltan {falta} goles")
                              + " por asignar a jugadores en MatchZone.")
            if p["mvp"] is None:
                avisos.append(f"Fecha {p['fecha']}, {names[p['local']]} vs {names[p['visita']]}: sin jugador del partido.")

    fechas = []
    por_fecha = collections.defaultdict(list)
    for p in partidos.values():
        por_fecha[p["fecha"]].append(p)
    for n in sorted(por_fecha):
        ms = sorted(por_fecha[n], key=lambda p: (p["hora"] or "", p["cancha"] or 0))
        juegan = {p["local"] for p in ms} | {p["visita"] for p in ms}
        jugados = sum(p["jugado"] for p in ms)
        estado = "jugada" if jugados == len(ms) else "en curso" if jugados else "programada"
        proxima = estado != "jugada" and all(f["estado"] == "jugada" for f in fechas)
        if proxima and any(p["hora"] is None or p["cancha"] is None for p in ms):
            avisos.append(f"Fecha {n}: hay partidos sin horario o sin cancha en MatchZone.")
        fechas.append({"numero": n, "dia": ms[0]["dia"], "estado": estado,
                       "libres": sorted(k for k in equipos if k not in juegan),
                       "partidos": ms})

    goleadores = []
    for s in raw["goleadores"]:
        pf = {}
        for p in partidos.values():
            for lado in ("local", "visita"):
                for g in p["goles"][lado]:
                    if g["id"] == s["playerUserId"]:
                        pf[str(p["fecha"])] = pf.get(str(p["fecha"]), 0) + g["goles"]
        goleadores.append({"jugador": s["playerName"], "id": s["playerUserId"], "equipo": clave_nombre(s["teamName"]),
                           "goles": s["goals"], "por_fecha": pf})

    e = raw["edicion"]
    return {
        "bajado": datetime.datetime.now().isoformat(timespec="seconds"),
        "fuente": f"{API}/editions/{e['id']}",
        "edicion": {"id": e["id"], "competencia": e["competitionName"], "nombre": e["label"],
                    "estado_mz": e["statusCode"], "formato_mz": e["formatCode"], "inicio": e["startDate"],
                    "sede": e["venues"], "canchas": e["courts"], "horarios": e["scheduleSlots"]},
        "avisos": avisos,
        "equipos": equipos,
        "tabla": tabla,
        "fechas": fechas,
        "goleadores": goleadores,
        "mvps": [{"jugador": s["playerName"], "id": s["playerUserId"], "equipo": clave_nombre(s["teamName"]),
                  "mvps": s["mvps"]} for s in raw["mvps"]],
        "tarjetas": [{"jugador": c["playerName"], "id": c["playerUserId"], "equipo": clave_nombre(c["teamName"]),
                      "amarillas": c["yellows"], "rojas": c["reds"], "suspensiones": c["suspensions"],
                      "suspendido": c["suspended"]} for c in raw["tarjetas"]],
        "suspensiones_mz": raw["suspensiones"],
    }


def repartir_goles(goleadores, partidos, previo, avisos):
    """MatchZone solo publica el total de goles de cada jugador. Se reparte entre partidos asi:
    se mantiene lo que ya estaba repartido en el consolidado anterior y lo nuevo de cada jugador
    va al partido jugado de su equipo en que subieron los goles asignados. Si hay mas de uno,
    va al mas reciente y queda un aviso."""
    antes = {}  # id partido -> (goles asignados en MZ, {id jugador: goles})
    if previo:
        for f in previo["fechas"]:
            for p in f["partidos"]:
                antes[p["id"]] = (p["goles_asignados_mz"] or 0,
                                  {g["id"]: g["goles"] for lado in ("local", "visita") for g in p["goles"][lado]})
    reparto = {pid: dict(antes.get(pid, (0, {}))[1]) for pid in partidos}
    subio = {pid: (p["goles_asignados_mz"] or 0) > antes.get(pid, (0, {}))[0] for pid, p in partidos.items()}

    for s in goleadores:
        jid, equipo = s["playerUserId"], clave_nombre(s["teamName"])
        del_equipo = sorted((p for p in partidos.values() if p["jugado"] and equipo in (p["local"], p["visita"])),
                            key=lambda p: p["fecha"])
        ya = sum(reparto[p["id"]].get(jid, 0) for p in del_equipo)
        delta = s["goals"] - ya
        if delta > 0:
            candidatos = [p for p in del_equipo if subio[p["id"]]] or del_equipo
            if not candidatos:
                avisos.append(f"{s['playerName']}: {delta} gol(es) sin partido jugado de su equipo.")
                continue
            if len(candidatos) > 1:
                avisos.append(f"{s['playerName']}: {delta} gol(es) nuevo(s) que podrian ser de las fechas "
                              f"{', '.join(str(p['fecha']) for p in candidatos)}; se anotaron en la "
                              f"{candidatos[-1]['fecha']}. Confirmar en MatchZone.")
            pid = candidatos[-1]["id"]
            reparto[pid][jid] = reparto[pid].get(jid, 0) + delta
        elif delta < 0:
            avisos.append(f"{s['playerName']}: MatchZone le quito {-delta} gol(es); se descontaron de la fecha mas reciente.")
            for p in reversed(del_equipo):
                q = min(-delta, reparto[p["id"]].get(jid, 0))
                reparto[p["id"]][jid] = reparto[p["id"]].get(jid, 0) - q
                delta += q
                if not delta:
                    break

    # Un jugador al que MatchZone le quito todos sus goles ya no viene en `goleadores`: el bucle de arriba no lo
    # ve y su gol quedaba repartido (salia como "jugador <id>"). 2026-10-17: el usuario paso el gol de Rodrigo
    # Berroeta (id 9) a Jose Ignacio Martinez Zelada en Profesores-Control Dirigido.
    actuales = {s["playerUserId"] for s in goleadores}
    nombre_antes = {}
    if previo:
        nombre_antes = {g["id"]: g["jugador"] for f in previo["fechas"] for p in f["partidos"]
                        for lado in ("local", "visita") for g in p["goles"][lado]}
    for pid, goles in reparto.items():
        for jid in [j for j, n in goles.items() if n > 0 and j not in actuales]:
            avisos.append(f"{nombre_antes.get(jid, f'jugador {jid}')}: MatchZone le quito {goles[jid]} gol(es) "
                          f"(ya no figura entre los goleadores); se descontaron del partido {pid}.")
            goles[jid] = 0

    nombre = {s["playerUserId"]: s["playerName"] for s in goleadores}
    equipo_de = {s["playerUserId"]: clave_nombre(s["teamName"]) for s in goleadores}
    for pid, goles in reparto.items():
        p = partidos[pid]
        for jid, n in sorted(goles.items(), key=lambda x: -x[1]):
            if n <= 0:
                continue
            lado = "local" if equipo_de.get(jid) == p["local"] else "visita"
            p["goles"][lado].append({"jugador": nombre.get(jid, f"jugador {jid}"), "id": jid, "goles": n})
        if p["jugado"]:
            total = sum(g["goles"] for lado in ("local", "visita") for g in p["goles"][lado])
            if total != (p["goles_asignados_mz"] or 0):
                avisos.append(f"Partido {pid} (fecha {p['fecha']}): se repartieron {total} goles y MatchZone "
                              f"dice {p['goles_asignados_mz']} asignados.")
            for i, lado in enumerate(("local", "visita")):
                if sum(g["goles"] for g in p["goles"][lado]) > p["marcador"][i]:
                    avisos.append(f"Partido {pid} (fecha {p['fecha']}): el {lado} tiene mas goles repartidos que su marcador.")


# ---------------------------------------------------------------- resumen legible
def resumen(c):
    eq = {k: v["nombre"] for k, v in c["equipos"].items()}
    L = []
    p = L.append
    e = c["edicion"]
    p(f"{e['competencia']} - {e['nombre']} (MatchZone, edicion {e['id']}). Bajado el {c['bajado'].replace('T', ' ')}")
    if c["avisos"]:
        p("")
        p("AVISOS")
        for a in c["avisos"]:
            p(f"  - {a}")
    for g, filas in sorted(c["tabla"].items()):
        p("")
        p(f"GRUPO {g}{'':30}PJ  G  E  P  GF GC DIF PTS")
        for t in filas:
            p(f"  {t['pos']}. {eq[t['equipo']]:<34} {t['pj']:>2} {t['g']:>2} {t['e']:>2} {t['p']:>2}"
              f" {t['gf']:>3} {t['gc']:>2} {t['dif']:>3} {t['pts']:>3}")
    for f in c["fechas"]:
        if f["estado"] == "programada" and f is not next(x for x in c["fechas"] if x["estado"] != "jugada"):
            continue
        p("")
        p(f"FECHA {f['numero']} - {f['dia']} ({f['estado']})")
        for m in f["partidos"]:
            hora = m["hora"] or "--:--"
            cancha = f"C{m['cancha']}" if m["cancha"] else "C?"
            if not m["jugado"]:
                p(f"  {hora} {cancha}  {eq[m['local']]} vs {eq[m['visita']]}")
                continue
            p(f"  {hora} {cancha}  {eq[m['local']]} {m['marcador'][0]}-{m['marcador'][1]} {eq[m['visita']]}  (grupo {m['grupo']})")
            for lado in ("local", "visita"):
                goles = ", ".join(f"{g['jugador']}{' x' + str(g['goles']) if g['goles'] > 1 else ''}" for g in m["goles"][lado])
                falta = m["goles_sin_asignar"][lado]
                p(f"      Goles {eq[m[lado]]}: {goles or '-'}{f'  (+{falta} sin asignar)' if falta else ''}")
            tarj = [f"{t['jugador']} ({eq[m[lado]]}, {'roja' if t['rojas'] else 'amarilla'})"
                    for lado in ("local", "visita") for t in m["tarjetas"][lado]]
            p(f"      Tarjetas: {', '.join(tarj) or '-'}")
            mv = m["mvp"]
            p(f"      Jugador del partido: {mv['jugador'] + ' (n.' + str(mv['numero']) + ', ' + eq[mv['equipo']] + ')' if mv else '-'}")
            p(f"      Firmaron la planilla: {m['firmas']['local'][0]}/{m['firmas']['local'][1]} y "
              f"{m['firmas']['visita'][0]}/{m['firmas']['visita'][1]}")
        p(f"  Libres: {', '.join(eq[k] for k in f['libres']) or '-'}")
    p("")
    p("GOLEADORES")
    for s in c["goleadores"]:
        p(f"  {s['goles']:>2}  {s['jugador']} ({eq[s['equipo']]})")
    p("")
    p("TARJETAS (acumulado)")
    for t in c["tarjetas"]:
        p(f"  {t['jugador']} ({eq[t['equipo']]}): {t['amarillas']} amarilla(s), {t['rojas']} roja(s)"
          f"{', SUSPENDIDO' if t['suspendido'] else ''}")
    p(f"  Suspensiones vigentes: {len(c['suspensiones_mz'])}")
    return "\n".join(L) + "\n"


def main():
    base = f"{API}/editions/{EDICION}"
    dia = DATOS / f"{datetime.date.today():%Y-%m-%d}"
    (dia / "planillas").mkdir(parents=True, exist_ok=True)
    raw = {}
    for nombre, ruta in ARCHIVOS.items():
        raw[nombre] = get(base + ruta)
        escribir(dia / f"{nombre}.json", raw[nombre])
    planillas = {}
    for m in raw["fixture"]:
        if m["status"] == "PLAYED":
            planillas[m["id"]] = get(f"{API}/edition-matches/{m['id']}/lineup")
            escribir(dia / "planillas" / f"fecha{m['round']}-{m['id']}.json", planillas[m["id"]])

    actual = DATOS / "consolidado.json"
    previo = json.loads(actual.read_text(encoding="utf-8")) if actual.exists() else None
    if previo and previo["edicion"]["id"] != EDICION:
        previo = None
    c = consolidar(raw, planillas, previo, cargar_nombres())
    escribir(actual, c)
    (DATOS / "resumen.txt").write_text(resumen(c), encoding="utf-8")
    for f in ("consolidado.json", "resumen.txt"):
        shutil.copyfile(DATOS / f, dia / f)
    print(f"OK: {len(planillas)} planillas, {len(c['avisos'])} avisos. Datos en {DATOS}")


if __name__ == "__main__":
    main()
