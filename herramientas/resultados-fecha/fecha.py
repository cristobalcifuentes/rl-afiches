"""Afiches de resultados de cualquier fecha, con los datos de MatchZone (2026-10-17).

Pedido del usuario: pedir desde el celular los afiches de resultados de una fecha y recibirlos en x2, feed e
historia. Las 14 laminas no son plantillas fijas: salen de build.py (el diseno del lienzo "Resultados Fecha 1 RL")
con los datos de la fecha que se pida.

    python fecha.py <n> [--sin-bajar] [--forzar] [--destino <carpeta>] [--web <carpeta>]

--web: deja los PNG, las miniaturas y la pagina (documento completo, descarga directa) juntos en esa carpeta,
para GitHub Pages (boton.py). Sin --web, la pagina es para un artifact de Claude (capacidad downloads).

1. Baja los datos de MatchZone (matchzone-datos/bajar.py), salvo --sin-bajar.
2. Arma los 14 tableros de la fecha en project/ y preview/. La Fecha 1 usa los nombres que ya tiene el lienzo
   (Main, Partido-1...); las demas, F<n>-Portada, F<n>-Partido-1... en filas nuevas del mismo lienzo, y suma sus
   entradas a project/canvas.json.
3. Los exporta en x2 (2160x2700 y 2160x3840) a "2 Instagram/9 Resultados/Fecha <n>/".
4. Prepara la pagina de descarga en entrega/fecha-<n>/ (index.html + miniaturas) y entrega/fecha-<n>/resultado.json
   con los avisos, los tableros, los archivos y los lotes para publicarla (64 MB por publicacion).

Se detiene si la fecha no esta jugada entera o le falta el jugador del partido a algun partido (--forzar
lo salta: lo que falta sale con el relleno de ejemplo). Los goles sin asignar no la detienen: quedan en los avisos.
"""
import contextlib
import datetime
import html
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.parse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
RL = os.path.dirname(TOOLS)
DATOS = os.path.join(TOOLS, "matchzone-datos")
DIAS = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE",
         "NOVIEMBRE", "DICIEMBRE"]
FILA_FECHA = 1350 + 320 + 1920 + 400        # alto de cada fecha en el lienzo (feed + historias + aire)
LOTE_MAX = 60 * 1024 * 1024                 # una publicacion acepta 64 MB


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rf = _load("rf", os.path.join(HERE, "build.py"))
exportar = _load("exportar", os.path.join(TOOLS, "dia-1-the-origin", "exportar.py"))
exportar.HERE = HERE
sys.path.insert(0, DATOS)
import resultados  # noqa: E402

NAMES = rf.NAMES


def nombre_corto(key):
    s = NAMES[key].title()
    for a, b in ((" Fc", " FC"), ("Rcv", "RCV"), ("F.C.", "F.C.")):
        s = s.replace(a, b)
    return s


def dia_texto(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day} DE {MESES[d.month - 1]}"


def datos_fecha(n, c, forzar):
    f = resultados.fecha(n, c)
    faltan = [m for m in f["partidos"] if not m["jugado"]]
    sin_figura = [m for m in f["partidos"] if m["jugado"] and m["mvp"] is None]
    if (faltan or sin_figura) and not forzar:
        msg = [f"La Fecha {n} no esta lista en MatchZone:"]
        msg += [f"  - {NAMES[m['local']]} vs {NAMES[m['visita']]}: sin resultado" for m in faltan]
        msg += [f"  - {NAMES[m['local']]} vs {NAMES[m['visita']]}: sin jugador del partido" for m in sin_figura]
        raise SystemExit("\n".join(msg) + "\n(--forzar la arma igual, con relleno de ejemplo en lo que falta)")
    turnos = {}
    for m in f["partidos"]:
        turnos.setdefault(m["hora"], []).append((m["cancha"], m["local"], m["visita"]))
    if len(turnos) != 2 or any(len(v) != 3 for v in turnos.values()) or None in turnos:
        raise SystemExit(f"La Fecha {n} no tiene 2 horarios de 3 partidos con hora y cancha; el diseno es para eso.")
    sede = rf.F1["sede"] if c["edicion"]["sede"] in (None, [], ["Canchas San Damian"]) else c["edicion"]["sede"][0].upper()
    F = {"numero": n, "dia": dia_texto(f["dia"]), "sede": sede, "libres": f["libres"],
         "turnos": [(h, sorted(v)) for h, v in sorted(turnos.items())]}
    partidos = resultados.para_carrusel(n, c)
    avisos = [a for a in c["avisos"] if f"Fecha {n}," in a or f"(fecha {n})" in a or f"Fecha {n}:" in a]
    for m in partidos:
        if m["goles"] is None:
            continue
        if min(rf.plan(m, L)["size"] for L in (rf.FEED, rf.STORY)) < rf.MIN_SIZE:
            largos = [x[0] for lado in ("local", "visita") for x in m["goles"][lado] + m["tarjetas"][lado]
                      if len(x[0].split()) >= 4]
            for k in ("goles", "tarjetas"):
                m[k] = {lado: [(corto(a), b) for a, b in m[k][lado]] for lado in ("local", "visita")}
            if largos:
                avisos.append(f"{NAMES[m['local']]} vs {NAMES[m['visita']]}: para que entre la letra se acortaron "
                              + ", ".join(f"{a} -> {corto(a)}" for a in sorted(set(largos))))
    return F, partidos, avisos


# Version corta elegida por el usuario para un nombre (en mayusculas, como sale en la lamina). Manda sobre la regla.
CORTOS = {}


def corto(nombre):
    """Nombre de 4 palabras o mas -> primer nombre + apellido paterno (el penultimo), salvo que este en CORTOS."""
    if nombre in CORTOS:
        return CORTOS[nombre]
    w = nombre.split()
    return f"{w[0]} {w[-2]}" if len(w) >= 4 else nombre


def tableros(n):
    """(archivo, titulo de pagina, titulo del tablero, cuerpo, ancho, alto, x, y, nombre del PNG)"""
    pre = "" if n == 1 else f"F{n}-"
    y0 = (n - 1) * FILA_FECHA
    num = (n - 1) * 14
    out = [(f"{pre}Main" if n == 1 else f"{pre}Portada", f"Resultados Fecha {n}",
            f"{num + 1:02d} · Fecha {n} - portada, resultados de los 6 partidos 1080x1350", rf.portada,
            1080, 1350, 0, y0, "01 - Portada feed 4x5@2x.png")]
    for i, m in enumerate(rf.PARTIDOS):
        vs = f"{nombre_corto(m['local'])} vs {nombre_corto(m['visita'])}"
        out.append((f"{pre}Partido-{i + 1}", f"Resultado partido {i + 1}",
                    f"{num + i + 2:02d} · Fecha {n} - partido {i + 1}, {vs} ({m['hora']}, cancha {m['cancha']}) 1080x1350",
                    (lambda i: lambda local: rf.partido(i, local))(i), 1080, 1350, (i + 1) * 1160, y0,
                    f"{i + 2:02d} - Partido {i + 1} {vs} feed 4x5@2x.png"))
    out.append((f"{pre}Historia-Portada", f"Resultados Fecha {n}",
                f"{num + 8:02d} · Fecha {n} - historia portada, resultados y libres 1080x1920", rf.portada_story,
                1080, 1920, 0, y0 + rf.STORY_Y, "08 - Portada historia 9x16@2x.png"))
    for i, m in enumerate(rf.PARTIDOS):
        vs = f"{nombre_corto(m['local'])} vs {nombre_corto(m['visita'])}"
        out.append((f"{pre}Historia-Partido-{i + 1}", f"Resultado partido {i + 1}",
                    f"{num + i + 9:02d} · Fecha {n} - historia partido {i + 1}, {vs} ({m['hora']}, cancha {m['cancha']}) 1080x1920",
                    (lambda i: lambda local: rf.partido(i, local, rf.STORY))(i), 1080, 1920, (i + 1) * 1160,
                    y0 + rf.STORY_Y, f"{i + 9:02d} - Partido {i + 1} {vs} historia 9x16@2x.png"))
    if n == 1:
        # la Fecha 1 conserva los titulos que ya tiene el lienzo (asi el indice no cambia)
        orig = {b[0]: b[2] for b in rf.boards()}
        out = [(it[0], it[1], orig.get(it[0], it[2])) + it[3:] for it in out]
    return out


def escribir_tableros(n, items):
    os.makedirs(os.path.join(HERE, "project"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    for name, title, _t, body, w, h, _x, _y, _png in items:
        with open(os.path.join(HERE, "project", f"{name}.dc.html"), "w", encoding="utf-8") as fh:
            fh.write(rf.prog.dc_html(title, body(False), w, h).replace(rf.prog.CSS.strip(), rf.CSS))
        with open(os.path.join(HERE, "preview", f"{name}.html"), "w", encoding="utf-8") as fh:
            page = rf.prog.preview_html(title, body(True), w, h).replace(rf.prog.CSS.strip(), rf.CSS)
            fh.write(page.replace("<style>", "<style>\nbody{margin:0}", 1))
    # indice: se suman (o actualizan) solo los tableros de esta fecha; el resto queda como estaba
    path = os.path.join(HERE, "project", "canvas.json")
    with open(path, encoding="utf-8") as fh:
        canvas = json.load(fh)
    antes = json.dumps(canvas, sort_keys=True)
    for name, _p, t, _b, w, h, x, y, _png in items:
        key = f"{name}.dc.html"
        canvas["boards"][key] = {**canvas["boards"].get(key, {}), "x": x, "y": y, "w": w, "h": h, "title": t}
        if key not in canvas["order"]:
            canvas["order"].append(key)
    if n > 1:
        canvas["title"] = "Resultados RL"
    cambio = json.dumps(canvas, sort_keys=True) != antes
    if cambio:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(canvas, fh, ensure_ascii=False, indent=1)
    return cambio


# ---------------------------------------------------------------- pagina de descarga
PAGE = """<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Tomorrow:ital,wght@1,800&display=swap">
<style>
/* Una columna de descarga: encabezado de la fecha, avisos, y una grilla por formato (feed, historias). */
:root{
  --bg:#0C0D0D; --panel:#131A1C; --line:rgba(103,232,249,.26); --fg:#EEF3F5; --muted:#9DB1B6;
  --cian:#67E8F9; --ink:#03181C; --warn:#F5C518; --warn-bg:rgba(245,197,24,.09);
  --display:'Tomorrow',system-ui,sans-serif; --body:'Barlow Condensed','Arial Narrow',system-ui,sans-serif;
  color-scheme:dark;
}
body{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:18px;line-height:1.35}
.wrap{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:28px 56px;display:flex;flex-direction:column;gap:28px}
header{display:flex;flex-direction:column;gap:6px}
.kicker{font-weight:700;letter-spacing:.22em;font-size:14px;color:var(--muted);text-transform:uppercase}
h1{margin:0;font-family:var(--display);font-style:italic;font-weight:800;font-size:clamp(34px,8vw,56px);line-height:1;
  color:var(--cian);text-wrap:balance}
.sub{margin:0;font-size:19px;color:var(--fg);letter-spacing:.04em}
.avisos{border:1px solid var(--warn);background:var(--warn-bg);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:6px}
.avisos h2{margin:0;font-size:16px;letter-spacing:.16em;text-transform:uppercase;color:var(--warn)}
.avisos ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:4px}
.nodl{margin:0;color:var(--muted);font-size:16px}
section{display:flex;flex-direction:column;gap:14px}
.sec-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 16px;
  border-bottom:1px solid var(--line);padding-bottom:10px}
.sec-head h2{margin:0;font-size:22px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.sec-head h2 span{color:var(--muted);font-weight:600;letter-spacing:.06em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}
.item{display:flex;flex-direction:column;gap:8px;min-width:0}
.thumb{display:block;width:100%;padding:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--panel);cursor:zoom-in}
.thumb img{display:block;width:100%;height:auto}
.cap{font-size:16px;line-height:1.2;color:var(--muted);min-height:2.4em}
.cap b{color:var(--fg);font-weight:700}
button.dl,button.all{font-family:var(--body);font-weight:800;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;
  border-radius:999px;min-height:44px;padding:0 18px;font-size:16px}
button.dl{background:transparent;color:var(--cian);border:1px solid var(--cian)}
button.all{background:var(--cian);color:var(--ink);border:0}
button:disabled{opacity:.6;cursor:default}
button:focus-visible,.thumb:focus-visible{outline:3px solid var(--fg);outline-offset:2px}
.status{font-size:15px;color:var(--muted);min-height:1.2em}
footer{color:var(--muted);font-size:15px;border-top:1px solid var(--line);padding-top:12px}
#zoom{position:fixed;inset:0;background:rgba(0,0,0,.92);display:flex;align-items:center;justify-content:center;
  padding:calc(env(safe-area-inset-top,0px) + 16px) 16px calc(env(safe-area-inset-bottom,0px) + 16px);z-index:10;cursor:zoom-out}
#zoom img{max-width:100%;max-height:100%;object-fit:contain}
@media (prefers-reduced-motion:no-preference){button{transition:opacity .15s}}
</style>
<div class="wrap">
  <header>
    <div class="kicker">Rancagua League · THE ORIGIN</div>
    <h1>__H1__</h1>
    <p class="sub">__SUB__</p>
  </header>
  __AVISOS__
  <p class="nodl" id="nodl" hidden>Para guardar una imagen, tócala para abrirla en grande y mantenla presionada.</p>
  __SECTIONS__
  <footer>__FOOT__</footer>
</div>
<div id="zoom" hidden><img alt=""></div>
<script>
const ITEMS = __ITEMS__;
const WEB = __WEB__;      // pagina en GitHub Pages: descarga directa con un enlace
let dl = null;
const zoom = document.getElementById("zoom");
function setStatus(id, text){ const el = document.getElementById("st-" + id); if (el) el.textContent = text; }
async function save(it){
  if (WEB) {
    const a = document.createElement("a"); a.href = it.png; a.download = it.filename;
    document.body.appendChild(a); a.click(); a.remove();
    setStatus(it.id, "Descargando"); await new Promise(r => setTimeout(r, 700)); return "ok";
  }
  if (!dl) return "unavailable";
  const btn = document.getElementById("b-" + it.id);
  btn.disabled = true; setStatus(it.id, "Preparando...");
  try {
    const blob = await (await fetch(it.png)).blob();
    await dl.save({filename: it.filename, data: blob});
    setStatus(it.id, "Guardada"); return "ok";
  } catch (e) {
    const code = (e && e.code) || "error";
    setStatus(it.id, code === "declined" ? "Cancelada" : code === "rate_limited" ? "Espera un momento y vuelve a tocar" : "No se pudo guardar");
    return code;
  } finally { btn.disabled = false; }
}
document.addEventListener("click", async (ev) => {
  const t = ev.target.closest("button");
  if (t && t.classList.contains("thumb")) {
    const it = ITEMS.find(x => x.id === t.dataset.id);
    zoom.querySelector("img").src = it.png; zoom.querySelector("img").alt = it.label; zoom.hidden = false; return;
  }
  if (t && t.classList.contains("dl")) { save(ITEMS.find(x => x.id === t.dataset.id)); return; }
  if (t && t.classList.contains("all")) {
    t.disabled = true;
    for (const it of ITEMS.filter(x => x.group === t.dataset.group)) {
      const r = await save(it);
      if (r !== "ok") break;
    }
    t.disabled = false;
  }
});
zoom.addEventListener("click", () => { zoom.hidden = true; });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") zoom.hidden = true; });
function noDownloads(){ document.querySelectorAll("button.dl, button.all").forEach(b => b.hidden = true);
  document.getElementById("nodl").hidden = false; }
if (WEB) {
  // nada que pedir: el navegador descarga directo
} else if (window.claude && window.claude.use) {
  window.claude.use("downloads").then(d => { dl = d; if (!d) noDownloads(); }).catch(noDownloads);
} else { noDownloads(); }
</script>
"""


def pagina(n, F, items, archivos, avisos, carpeta, web=False):
    os.makedirs(os.path.join(carpeta, "mini"), exist_ok=True)
    data, grupos = [], {"feed": [], "historia": []}
    for (name, _p, _t, _b, w, h, _x, _y, png), dest in zip(items, archivos):
        grupo = "feed" if h == 1350 else "historia"
        num = png[:2]
        mini = f"mini/{num}.jpg"
        im = Image.open(dest).convert("RGB")
        im.resize((540, round(540 * im.height / im.width)), Image.LANCZOS).save(os.path.join(carpeta, mini), quality=82)
        partido = png[5:].rsplit(" feed", 1)[0].rsplit(" historia", 1)[0]
        png_url = (urllib.parse.quote(os.path.relpath(dest, carpeta).replace("\\", "/")) if web
                   else f"png/{num}.png")
        it = {"id": num, "group": grupo, "png": png_url, "mini": mini, "label": partido,
              "filename": f"RL Fecha {n} - {png.replace('@2x', '')}", "board": name}
        data.append(it)
        grupos[grupo].append((it, w, h))
    marcador = {f"Partido {i + 1}": f"{rf.PARTIDOS[i]['marcador'][0]}-{rf.PARTIDOS[i]['marcador'][1]}"
                for i in range(len(rf.PARTIDOS)) if rf.PARTIDOS[i]["marcador"] is not None}
    secs = []
    for grupo, titulo, medida in (("feed", "Feed", "4:5 · 2160x2700"), ("historia", "Historias", "9:16 · 2160x3840")):
        cards = []
        for it, w, h in grupos[grupo]:
            lbl = html.escape(it["label"])
            for k, v in marcador.items():
                if lbl.startswith(k + " "):
                    lbl = f"<b>{k}</b> · {html.escape(it['label'][len(k) + 1:]).replace(' vs ', f' {v} ', 1)}"
            if lbl.startswith("Portada"):
                lbl = "<b>Portada</b>"
            cards.append(f'<div class="item"><button class="thumb" data-id="{it["id"]}" aria-label="Ver en grande: {html.escape(it["label"])}">'
                         f'<img src="{it["mini"]}" width="540" height="{round(540 * h / w)}" alt="{html.escape(it["label"])}" loading="lazy"></button>'
                         f'<div class="cap">{lbl}</div>'
                         f'<button class="dl" id="b-{it["id"]}" data-id="{it["id"]}">Descargar</button>'
                         f'<div class="status" id="st-{it["id"]}" aria-live="polite"></div></div>')
        secs.append(f'<section><div class="sec-head"><h2>{titulo} <span>{medida}</span></h2>'
                    f'<button class="all" data-group="{grupo}">Descargar las {len(cards)}</button></div>'
                    f'<div class="grid">{"".join(cards)}</div></section>')
    av = ""
    if avisos:
        av = ('<div class="avisos" role="note"><h2>Antes de publicar</h2><ul>'
              + "".join(f"<li>{html.escape(a)}</li>" for a in avisos) + "</ul></div>")
    c = resultados.cargar()
    out = (PAGE.replace("__TITLE__", f"Afiches Resultados Fecha {n}")
           .replace("__H1__", f"Resultados Fecha {n}")
           .replace("__SUB__", html.escape(f"{F['dia'].capitalize().replace(' De ', ' de ')} · {F['sede'].title().replace('Damián', 'Damián')} · 14 afiches en x2"))
           .replace("__AVISOS__", av)
           .replace("__SECTIONS__", "\n".join(secs))
           .replace("__FOOT__", html.escape(f"Datos de MatchZone bajados el {c['bajado'].replace('T', ' a las ')[:-3]}. "
                                            f"Los PNG pesan entre 2 y 8 MB cada uno."))
           .replace("__ITEMS__", json.dumps(data, ensure_ascii=False))
           .replace("__WEB__", "true" if web else "false"))
    if web:
        # pagina completa (en un artifact el esqueleto lo pone la publicacion)
        head, body = out.split("</style>\n", 1)
        out = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
               '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
               '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
               f'{head}</style>\n</head>\n<body>\n{body}</body>\n</html>\n')
    with open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(out)
    return data


def lotes(carpeta, data, archivos):
    """Archivos de la pagina repartidos en publicaciones de hasta LOTE_MAX ({ruta publicada: ruta completa})."""
    rel = lambda p: os.path.abspath(p).replace("\\", "/")
    base = {it["mini"]: rel(os.path.join(carpeta, it["mini"])) for it in data}
    out, actual, peso = [], dict(base), sum(os.path.getsize(os.path.join(carpeta, it["mini"])) for it in data)
    for it, dest in zip(data, archivos):
        s = os.path.getsize(dest)
        if peso + s > LOTE_MAX:
            out.append(actual)
            actual, peso = {}, 0
        actual[it["png"]] = rel(dest)
        peso += s
    out.append(actual)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args or not args[0].isdigit():
        raise SystemExit(__doc__)
    n = int(args[0])
    forzar = "--forzar" in args
    web = args[args.index("--web") + 1] if "--web" in args else None     # carpeta de la pagina en la web
    destino = web or (args[args.index("--destino") + 1] if "--destino" in args else
                      os.path.join(RL, "2 Instagram", "9 Resultados", f"Fecha {n}"))
    if "--sin-bajar" not in args:
        subprocess.run([sys.executable, "bajar.py"], cwd=DATOS, check=True)
    c = resultados.cargar()
    F, partidos, avisos = datos_fecha(n, c, forzar)
    rf.F1, rf.PARTIDOS = F, partidos
    ojo = io.StringIO()
    with contextlib.redirect_stdout(ojo):
        rf.check()
    # los "tiene n goles y la lista suma m" ya estan en los avisos de MatchZone (goles sin asignar)
    avisos += [l[4:].strip() if l.startswith("OJO") else l for l in ojo.getvalue().splitlines()
               if l.strip() and "la lista suma" not in l]

    items = tableros(n)
    indice = escribir_tableros(n, items)
    os.makedirs(destino, exist_ok=True)
    archivos = []
    for name, *_rest, png in items:
        dest = os.path.join(destino, png)
        exportar.export(name, dest)
        archivos.append(dest)
        print("x2", png)
    shutil.rmtree(os.path.join(HERE, "chrome-prof"), ignore_errors=True)

    carpeta = os.path.join(HERE, "entrega", f"fecha-{n}")
    os.makedirs(carpeta, exist_ok=True)
    data = pagina(n, F, items, archivos, avisos, web or carpeta, web=bool(web))
    rel = lambda p: os.path.abspath(p).replace("\\", "/")     # rutas completas: sirven desde cualquier carpeta
    res = {
        "fecha": n, "dia": F["dia"], "generado": datetime.datetime.now().isoformat(timespec="seconds"),
        "avisos": avisos,
        "lienzo": {"url": "https://claude.ai/artifact/H91kYp48yjJNMGrXUzkKUz", "root": rel(HERE),
                   "tableros": [f"project/{i[0]}.dc.html" for i in items], "indice_cambio": indice},
        "afiches": [rel(a) for a in archivos],
        # en la web (--web) la pagina y los PNG ya quedaron juntos: no hay lotes que publicar
        "pagina": {"root": rel(web or carpeta), "file_path": rel(os.path.join(web or carpeta, "index.html")),
                   "lotes": None if web else lotes(carpeta, data, archivos)},
        "megas": round(sum(os.path.getsize(a) for a in archivos) / 2 ** 20, 1),
    }
    with open(os.path.join(carpeta, "resultado.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("fecha", "dia", "avisos", "megas")}, ensure_ascii=False, indent=1))
    print(f"Listo: {len(archivos)} afiches en {destino}. Detalle en {os.path.join(carpeta, 'resultado.json')}")


if __name__ == "__main__":
    main()
