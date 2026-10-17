"""Boton de los afiches de resultados (2026-10-17). Lo corre GitHub Actions (repo cristobalcifuentes/rl-afiches).

El usuario no sabe a que hora va a terminar de cargar la fecha en MatchZone: cuando termina, aprieta el boton
(Run workflow en la app de GitHub) y le llega un WhatsApp con el link a los 14 afiches en x2.

    python boton.py generar [--fecha N] [--forzar] [--sitio <carpeta>] [--version <id>]
    python boton.py avisar --url-base https://cristobalcifuentes.github.io/rl-afiches/ [--sin-esperar] [--ver]

generar: baja MatchZone, elige la fecha (la pedida, o la ultima con partidos jugados) y revisa que este completa:
  resultados, jugador del partido y todos los goles asignados. Si esta completa (o con --forzar), arma los afiches
  en <sitio>/fecha-<n>/ (fecha.py --web) y actualiza <sitio>/index.html. Si falta algo, no genera nada.
  Deja lo que paso en entrega/boton.json. FECHA y FORZAR tambien se pueden pasar como variables de entorno.
avisar: manda el WhatsApp segun entrega/boton.json: el link (espera a que la pagina este publicada) o lo que falta.
"""
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
RAIZ = os.path.dirname(TOOLS)
DATOS = os.path.join(TOOLS, "matchzone-datos")
ESTADO = os.path.join(HERE, "entrega", "boton.json")
sys.path.insert(0, DATOS)
import resultados  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def arg(nombre, defecto=None):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


def guardar(estado):
    os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
    with open(ESTADO, "w", encoding="utf-8") as fh:
        json.dump(estado, fh, ensure_ascii=False, indent=1)
    print(json.dumps(estado, ensure_ascii=False, indent=1))


def lo_que_falta(f, eq):
    faltan = []
    for m in f["partidos"]:
        vs = f"{eq[m['local']]} vs {eq[m['visita']]}"
        if not m["jugado"]:
            faltan.append(f"{vs}: sin resultado")
            continue
        if m["mvp"] is None:
            faltan.append(f"{vs}: sin jugador del partido")
        k = sum(m["goles_sin_asignar"].values())
        if k:
            a, b = m["marcador"]
            faltan.append(f"{eq[m['local']]} {a}-{b} {eq[m['visita']]}: "
                          + ("falta 1 gol" if k == 1 else f"faltan {k} goles") + " por asignar")
    return faltan


def indice(sitio):
    """Portada del sitio: una tarjeta por fecha publicada."""
    fechas = sorted((int(m.group(1)) for d in os.listdir(sitio) if (m := re.fullmatch(r"fecha-(\d+)", d))
                     and os.path.exists(os.path.join(sitio, d, "index.html"))), reverse=True)
    items = "".join(f'<a class="f" href="fecha-{n}/"><img src="fecha-{n}/mini/01.jpg" alt="" width="540" height="675">'
                    f'<span>Fecha {n}</span></a>' for n in fechas) or "<p>Todavia no hay afiches.</p>"
    page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Afiches RL</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;800&family=Tomorrow:ital,wght@1,800&display=swap">
<style>
:root{{--bg:#0C0D0D;--fg:#EEF3F5;--muted:#9DB1B6;--cian:#67E8F9;--line:rgba(103,232,249,.26);color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:'Barlow Condensed','Arial Narrow',system-ui,sans-serif}}
.wrap{{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:28px 56px;display:flex;flex-direction:column;gap:22px}}
.k{{font-weight:600;letter-spacing:.22em;font-size:14px;color:var(--muted);text-transform:uppercase}}
h1{{margin:0;font-family:'Tomorrow',system-ui,sans-serif;font-style:italic;font-weight:800;font-size:clamp(34px,8vw,52px);color:var(--cian)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}
.f{{display:flex;flex-direction:column;gap:8px;color:var(--fg);text-decoration:none;font-weight:800;font-size:20px;letter-spacing:.08em;text-transform:uppercase}}
.f img{{width:100%;height:auto;border:1px solid var(--line);border-radius:8px}}
.f:focus-visible{{outline:3px solid var(--fg);outline-offset:2px}}
</style>
</head>
<body>
<div class="wrap"><div class="k">Rancagua League · THE ORIGIN</div><h1>Afiches de resultados</h1>
<div class="grid">{items}</div></div>
</body>
</html>
"""
    with open(os.path.join(sitio, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    open(os.path.join(sitio, ".nojekyll"), "w").close()


def generar():
    fecha = arg("--fecha") or os.environ.get("FECHA", "").strip() or None
    forzar = "--forzar" in sys.argv or os.environ.get("FORZAR", "").lower() == "true"
    sitio = os.path.abspath(arg("--sitio", os.path.join(RAIZ, "docs")))
    version = arg("--version", datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    if fecha is not None and not fecha.isdigit():
        guardar({"tipo": "error", "detalle": f"La fecha tiene que ser un numero (llego {fecha!r})."})
        return
    subprocess.run([sys.executable, "bajar.py"], cwd=DATOS, check=True)
    c = resultados.cargar()
    eq = {k: v["nombre"] for k, v in c["equipos"].items()}
    if fecha is None:
        jugadas = [f for f in c["fechas"] if any(m["jugado"] for m in f["partidos"])]
        if not jugadas:
            guardar({"tipo": "sin-fechas"})
            return
        f = jugadas[-1]
    else:
        f = next((x for x in c["fechas"] if x["numero"] == int(fecha)), None)
        if f is None:
            guardar({"tipo": "error", "detalle": f"MatchZone no tiene una Fecha {fecha}."})
            return
    n = f["numero"]
    faltan = lo_que_falta(f, eq)
    if faltan and not forzar:
        guardar({"tipo": "incompleta", "fecha": n, "faltan": faltan})
        return
    carpeta = os.path.join(sitio, f"fecha-{n}")
    if os.path.isdir(carpeta):
        for raiz, _dirs, archivos in os.walk(carpeta):
            for a in archivos:
                os.remove(os.path.join(raiz, a))
    cmd = [sys.executable, "fecha.py", str(n), "--sin-bajar", "--web", carpeta] + (["--forzar"] if forzar else [])
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        # solo la ultima linea (el motivo): el WhatsApp no es lugar para un traceback
        lineas = [l.strip() for l in (r.stderr or r.stdout).splitlines() if l.strip()]
        guardar({"tipo": "error", "fecha": n, "detalle": lineas[-1][:300] if lineas else "error desconocido"})
        return
    with open(os.path.join(carpeta, "version.txt"), "w", encoding="utf-8") as fh:
        fh.write(version)
    indice(sitio)
    guardar({"tipo": "listo", "fecha": n, "version": version, "forzado": bool(faltan)})


def esperar_publicacion(url, version, minutos=8):
    """GitHub Pages publica 1 a 2 minutos despues del push: espera a que version.txt sea el de esta corrida."""
    fin = time.time() + minutos * 60
    while time.time() < fin:
        try:
            req = urllib.request.Request(f"{url}version.txt?t={int(time.time())}", headers={"Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.read().decode().strip() == version:
                    return True
        except Exception:
            pass
        time.sleep(15)
    return False


def avisar():
    wa = _load("whatsapp", os.path.join(TOOLS, "comunes", "whatsapp.py"))
    av = _load("avisar", os.path.join(HERE, "avisar.py"))
    with open(ESTADO, encoding="utf-8") as fh:
        e = json.load(fh)
    base = arg("--url-base", "").rstrip("/") + "/"
    tipo, n = e["tipo"], e.get("fecha")
    if tipo == "listo":
        url = f"{base}fecha-{n}/"
        if "--sin-esperar" not in sys.argv and not esperar_publicacion(url, e["version"]):
            print("OJO: la pagina todavia no muestra esta version; se avisa igual")
        texto = av.mensaje(n, url)
        if e.get("forzado"):
            texto = texto.replace("LISTOS*", "LISTOS (GENERADOS CON DATOS INCOMPLETOS)*", 1)
    elif tipo == "incompleta":
        texto = "\n".join([f"*RL · FECHA {n}: FALTAN DATOS EN MATCHZONE*", "Todavia no arme los afiches. Falta:", ""]
                          + [f"- {x}" for x in e["faltan"]]
                          + ["", "Cuando lo completes, vuelve a apretar el boton (o elige *generar igual*)."])
    elif tipo == "sin-fechas":
        texto = "*RL · Todavia no hay partidos jugados en MatchZone.*"
    else:
        texto = (f"*RL · NO SE PUDIERON ARMAR LOS AFICHES{f' DE LA FECHA {n}' if n else ''}*\n"
                 f"{e.get('detalle', '')}\n\nRevisa la corrida en GitHub Actions.")
    if "--ver" in sys.argv:
        print(texto)
        return
    wa.enviar(texto)
    print("WhatsApp enviado:\n" + texto)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in ("generar", "avisar"):
        raise SystemExit(__doc__)
    generar() if sys.argv[1] == "generar" else avisar()
