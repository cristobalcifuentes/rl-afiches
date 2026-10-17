"""Lee datos/consolidado.json (lo escribe bajar.py) para responder preguntas o llenar piezas.

Desde otra herramienta:
    sys.path.insert(0, r"...\\herramientas\\matchzone-datos"); import resultados
    c = resultados.cargar()
    resultados.para_carrusel(1)   # PARTIDOS de resultados-fecha/build.py, con datos reales

Por consola (desde esta carpeta):
    python resultados.py                 resumen completo (datos/resumen.txt)
    python resultados.py fecha 1         una fecha
    python resultados.py equipo rabanal  partidos, goles y tarjetas de un equipo
    python resultados.py tabla | goleadores | avisos
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONSOLIDADO = HERE / "datos" / "consolidado.json"


def cargar():
    if not CONSOLIDADO.exists():
        raise SystemExit("Falta datos/consolidado.json: correr primero python bajar.py")
    return json.loads(CONSOLIDADO.read_text(encoding="utf-8"))


def fecha(n, c=None):
    c = c or cargar()
    return next(f for f in c["fechas"] if f["numero"] == n)


def para_carrusel(n, c=None):
    """Lista en el formato PARTIDOS de resultados-fecha/build.py (mismo orden: hora y cancha).
    Lo que falta queda en None (el carrusel dibuja el relleno de ejemplo)."""
    c = c or cargar()
    out = []
    for m in fecha(n, c)["partidos"]:
        jugado = m["jugado"]
        goles = {lado: [(g["jugador"].upper(), f"x{g['goles']}" if g["goles"] > 1 else "") for g in m["goles"][lado]]
                 for lado in ("local", "visita")}
        tarjetas = {lado: [(t["jugador"].upper(), color) for t in m["tarjetas"][lado]
                           for color, k in (("amarilla", "amarillas"), ("roja", "rojas")) for _ in range(t[k])]
                    for lado in ("local", "visita")}
        out.append(dict(
            hora=m["hora"], cancha=m["cancha"], local=m["local"], visita=m["visita"],
            marcador=tuple(m["marcador"]) if jugado else None,
            goles=goles if jugado else None,
            tarjetas=tarjetas if jugado else None,
            figura=(m["mvp"]["jugador"].upper(), m["mvp"]["equipo"]) if m["mvp"] else None,
        ))
    return out


def _texto_fecha(f, eq):
    L = [f"FECHA {f['numero']} - {f['dia']} ({f['estado']})"]
    for m in f["partidos"]:
        cab = f"  {m['hora'] or '--:--'} C{m['cancha'] or '?'}  {eq[m['local']]}"
        if not m["jugado"]:
            L.append(f"{cab} vs {eq[m['visita']]}")
            continue
        L.append(f"{cab} {m['marcador'][0]}-{m['marcador'][1]} {eq[m['visita']]}")
        for lado in ("local", "visita"):
            g = ", ".join(f"{x['jugador']}{' x' + str(x['goles']) if x['goles'] > 1 else ''}" for x in m["goles"][lado])
            falta = m["goles_sin_asignar"][lado]
            L.append(f"      Goles {eq[m[lado]]}: {g or '-'}{f'  (+{falta} sin asignar)' if falta else ''}")
        t = [f"{x['jugador']} ({'roja' if x['rojas'] else 'amarilla'})" for lado in ("local", "visita") for x in m["tarjetas"][lado]]
        L.append(f"      Tarjetas: {', '.join(t) or '-'}")
        if m["mvp"]:
            L.append(f"      Jugador del partido: {m['mvp']['jugador']} (n.{m['mvp']['numero']}, {eq[m['mvp']['equipo']]})")
    L.append(f"  Libres: {', '.join(eq[k] for k in f['libres']) or '-'}")
    return "\n".join(L)


def main(args):
    sys.stdout.reconfigure(encoding="utf-8")
    c = cargar()
    eq = {k: v["nombre"] for k, v in c["equipos"].items()}
    print(f"(bajado el {c['bajado'].replace('T', ' ')})")
    if not args:
        print((HERE / "datos" / "resumen.txt").read_text(encoding="utf-8"))
    elif args[0] == "fecha":
        print(_texto_fecha(fecha(int(args[1]), c), eq))
    elif args[0] == "equipo":
        k = args[1]
        for f in c["fechas"]:
            for m in f["partidos"]:
                if k in (m["local"], m["visita"]):
                    print(_texto_fecha(dict(f, partidos=[m]), eq).rsplit("\n  Libres", 1)[0])
            if k in f["libres"]:
                print(f"FECHA {f['numero']} - {f['dia']}: libre")
        print("Goleadores: " + (", ".join(f"{s['jugador']} {s['goles']}" for s in c["goleadores"] if s["equipo"] == k) or "-"))
    elif args[0] == "tabla":
        for g, filas in sorted(c["tabla"].items()):
            print(f"GRUPO {g}{'':30}PJ  G  E  P  GF GC DIF PTS")
            for t in filas:
                print(f"  {t['pos']}. {eq[t['equipo']]:<34} {t['pj']:>2} {t['g']:>2} {t['e']:>2} {t['p']:>2}"
                      f" {t['gf']:>3} {t['gc']:>2} {t['dif']:>3} {t['pts']:>3}")
    elif args[0] == "goleadores":
        for s in c["goleadores"]:
            print(f"  {s['goles']:>2}  {s['jugador']} ({eq[s['equipo']]})")
    elif args[0] == "avisos":
        print("\n".join(f"- {a}" for a in c["avisos"]) or "Sin avisos.")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
