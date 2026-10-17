"""Lienzo "Dia 1 The Origin RL" (2026-10-08): piezas 21 y 22 del plan de la semana inaugural.

- Pieza 21 (10:00, solo historias): 01 "Hoy nos encontramos" y 02 "Programacion de hoy".
- Pieza 22 (12:00): carrusel 03-05 (portada "Hoy comienza The Origin", Grupo 1, Grupo 2)
  y sus historias 06-08.

Reutiliza la plantilla y los estilos de programacion-fecha/build.py (partidos, franja de auspiciadores).

    python build.py [--render [tablero ...]]

Escribe project/ (canvas.json + .dc.html) y preview/*.html con imagenes locales; con --render deja
out/<tablero>.png a 1080 de ancho (render a 2x reducido) para revisar.
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG_DIR = os.path.join(HERE, "..", "programacion-fecha")

_spec = importlib.util.spec_from_file_location("prog", os.path.join(PROG_DIR, "build.py"))
prog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prog)

# Assets del lienzo "Dia 1 The Origin RL" (copiados del lienzo de la programacion, mismos bytes)
BLOB = {
    "bototos": "ca7e3069070701351c5bdb8c8df9f92f",
    "camajo": "9a80c37e8fc993ec82db459c6f64592b",
    "capybara": "ce75ce6934eda57d97ca0e28a318c574",
    "cerveceros": "59b135effe8f2cdef1b2ce408b0a083f",
    "control-dirigido": "1f386163f852a22e533b15a66e366188",
    "gatinhos": "3a85ffba9225a2f0cdb8b2082a90ad1a",
    "ikigai-rcv": "559f3e88032c73732e6487dab7c4e3e4",
    "irresponsables": "49c0ca306ee0eeda585cfd7e0846a8d4",
    "pierde-nunca": "55187e3f82f55b245acf6011f31d016b",
    "profesores": "a6aba08267bf084f8c57580bf7c41afe",
    "rabanal": "7430c795e591aa688f36ea3e00ab9584",
    "rusticos": "10aeca819c1f02d57a6f892f9eac1670",
    "saca-chispas": "1c00d867cbc508d903b64face9b66233",
    "inter": "b57e3d77c0d93cf92a4b4f845e73d670",          # subido el 2026-10-15
    "fondo-feed": "dae9b8ae9d7820f1fbbf50cae6389573",
    "fondo-historia": "448ae4d01cd653a684ab22e0a7d1b32c",
    "rl": "c549b3770d2f51625eacc1e8a70adf3a",
    "sp-monina": "d0b887fdd6c112ecd54601f2b9fb3db2",
    "sp-turin": "eeb9ea521ca475b1bbcd750a198cbb2c",
    "sp-recovery": "1fd49c10bbf7990cfa788093a626b313",
    "sp-matchzone": "3b4a26931f33942443e37ba326392767",
    "sp-invictus": "65bfce27a8e069e69a9fd714423d1936",
    "sp-marbella": "144f6554ceb02bae7ce7efb2d0adc2a3",
    "sp-kine": "81e37cd787a9f21214922ee418133426",
    "sp-ikigai": "ae024bfd6f9e09b70085896a9dc68760",
}
PA = "../../programacion-fecha/assets"


def src(key, local):
    if local:
        if key.startswith("sp-"):
            return f"{PA}/auspiciadores/{key[3:]}.png"
        if key in ("fondo-feed", "fondo-historia", "rl"):
            return f"{PA}/{key}.png"
        return f"{PA}/escudos/{key}.png"
    return f"/_blob/{BLOB[key]}"


prog.src = src          # las funciones de la plantilla usan estos assets
prog.BLOB = BLOB
NAMES = prog.NAMES
F1 = prog.FECHA_1

# Partidos de cada grupo en la Fecha 1 (grupos de MatchZone; mismos cruces de la programacion)
GROUPS = {
    1: {"turnos": [("21:00", [(4, "rabanal", "pierde-nunca"), (6, "camajo", "gatinhos")]),
                   ("22:00", [(6, "rusticos", "ikigai-rcv")])],
        "libre": "bototos"},
    # 2026-10-15: entra Inter de Rancagua (equipo 14), libre en la Fecha 1. Antes el Grupo 2 no mostraba libre.
    2: {"turnos": [("21:00", [(5, "saca-chispas", "cerveceros")]),
                   ("22:00", [(4, "capybara", "irresponsables"), (5, "profesores", "control-dirigido")])],
        "libre": "inter"},
}
COVER_ROWS = [["rabanal", "pierde-nunca", "camajo", "gatinhos", "rusticos", "ikigai-rcv", "bototos"],
              ["saca-chispas", "cerveceros", "capybara", "irresponsables", "profesores", "control-dirigido", "inter"]]

CSS_EXTRA = """
.plate{position:absolute;display:flex;align-items:center;justify-content:center;box-sizing:border-box;
  background-image:linear-gradient(90deg,rgba(4,13,15,.9) 0%,rgba(5,15,17,.82) 100%);
  border:1px solid rgba(103,232,249,.32);box-shadow:0 10px 24px rgba(0,0,0,.5)}
.stat{flex-direction:column;gap:10px}
.lbl{font-family:'Barlow Condensed',system-ui,sans-serif;font-weight:700;letter-spacing:.2em;margin-right:-.2em;
  color:#67E8F9;line-height:1}
.crests{position:absolute;left:0;width:100%;display:flex;justify-content:center;align-items:center}
"""
CSS = prog.CSS.strip() + "\n" + CSS_EXTRA.strip()

T, K, CH, INF = prog.text_row, "kicker", "chrome", "info"


def info_lines(top, text, size, line_w):
    return prog.lines_row(top, f'<span class="info" style="font-size: {size}px">{text}</span>', line_w, 22)


def info_plain(top, text, size):
    return f'<div class="row" style="top: {top}px"><span class="info" style="font-size: {size}px">{text}</span></div>'


def dot():
    return '<span class="dot">·</span>'


def crest(key, local, box, base):
    return prog.crest_img(key, local, box, base)


def team_h(key, local, box, base, size, side):
    name = (f'<span class="tname" style="font-size: {size}px; text-align: {side}">{NAMES[key]}</span>')
    img = crest(key, local, box, base)
    just = "flex-start" if side == "left" else "flex-end"
    inner = img + name if side == "left" else name + img
    return f'<div class="team" style="gap: 14px; justify-content: {just}">{inner}</div>'


def match_h(top, cancha, home, away, local, height, box, base, size, tab=(120, 17, 60), vs=40, left=56, width=968):
    """Fila horizontal mas grande que la de la programacion (3 partidos por lamina)."""
    return (f'<div class="match" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; border-radius: 14px">'
            f'{prog.court_tab(cancha, *tab)}'
            f'<div class="teams" style="grid-template-columns: minmax(0, 1fr) 96px minmax(0, 1fr); padding: 0 14px">'
            f'{team_h(home, local, box, base, size, "left")}'
            f'<span class="vs" style="font-size: {vs}px">VS</span>'
            f'{team_h(away, local, box, base, size, "right")}'
            f'</div></div>')


def match_v(top, cancha, home, away, local, height=196):
    """Bloque vertical para historia: escudo sobre nombre."""
    def team(key):
        return (f'<div class="team" style="flex-direction: column; justify-content: center; gap: 10px">'
                f'{crest(key, local, 108, 98)}'
                f'<span class="tname" style="font-size: 32px; text-align: center; height: 66px; display: flex; '
                f'align-items: flex-start; justify-content: center">{NAMES[key]}</span></div>')
    return (f'<div class="match" style="top: {top}px; left: 60px; width: 960px; height: {height}px; border-radius: 16px">'
            f'{prog.court_tab(cancha, 130, 18, 64)}'
            f'<div class="teams" style="grid-template-columns: minmax(0, 1fr) 70px minmax(0, 1fr); padding: 0 14px">'
            f'{team(home)}<span class="vs" style="font-size: 42px; padding-bottom: 66px">VS</span>{team(away)}'
            f'</div></div>')


def libre_plate(top, key, local, left, width, height, box, name_size, lbl_size):
    return (f'<div class="plate" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; '
            f'border-radius: 14px; gap: 22px">'
            f'<span class="lbl" style="font-size: {lbl_size}px">LIBRE ESTA FECHA</span>'
            f'{crest(key, local, box, round(box * .9))}'
            f'<span class="tname" style="font-size: {name_size}px">{NAMES[key]}</span></div>')


def kickoff_plate(top, width, height, lbl_size, time_size):
    left = (1080 - width) // 2
    return (f'<div class="plate" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; '
            f'border-radius: 14px; gap: 30px">'
            f'<span class="lbl" style="font-size: {lbl_size}px">PRIMER PITAZO</span>'
            f'<span class="tx title" style="font-size: {time_size}px">21:00</span></div>')


def crest_rows(tops, local, box, gap):
    out = []
    for top, row in zip(tops, COVER_ROWS):
        imgs = "".join(crest(k, local, box, round(box * .9)) for k in row)
        out.append(f'<div class="crests" style="top: {top}px; gap: {gap}px">{imgs}</div>')
    return "\n".join(out)


def band_feed(local, top=1196):
    return prog.sponsor_band(local, 40, top, 1000, 84, 11, 62, 12)


def band_story(local):
    return prog.sponsor_band(local, 40, 1544, 1000, 84, 11, 62, 12)


# ---------------------------------------------------------------- pieza 21 (10:00)
def info_hoy(local):
    tiles = [("21:00", "PRIMER PITAZO"), ("6", "PARTIDOS"), ("3", "CANCHAS")]
    parts = [prog.background("fondo-historia", local),
             T(262, K, "RANCAGUA LEAGUE", 40),
             T(322, CH, "HOY NOS ENCONTRAMOS", 78),
             T(430, "title", "CANCHAS", 170),
             T(600, "title", "SAN DAMIÁN", 170),
             info_lines(812, "RANCAGUA", 48, 120),
             info_plain(888, f"JUEVES 15 DE OCTUBRE{dot()}THE ORIGIN{dot()}FECHA 1", 30)]
    for i, (big, lbl) in enumerate(tiles):
        parts.append(f'<div class="plate stat" style="top: 964px; left: {60 + i * 330}px; width: 300px; height: 180px; '
                     f'border-radius: 14px"><span class="tx title" style="font-size: 92px">{big}</span>'
                     f'<span class="lbl" style="font-size: 24px">{lbl}</span></div>')
    # 1180-1544: espacio libre para el sticker de ubicacion de Instagram
    parts.append(band_story(local))
    return "\n".join(parts)


def info_programacion(local):
    parts = [prog.background("fondo-historia", local),
             T(262, K, "RANCAGUA LEAGUE", 40),
             T(322, "title", "PROGRAMACIÓN DE HOY", 88),
             T(430, CH, "JUEVES 15 DE OCTUBRE", 58),
             info_lines(508, f"THE ORIGIN{dot()}FECHA 1{dot()}CANCHAS SAN DAMIÁN", 26, 40)]
    for (hour, matches), top in zip(F1["turnos"], (562, 1006)):
        parts.append(prog.time_row(top, hour, 54, 260))
        y = top + 68
        for cancha, home, away in matches:
            parts.append(prog.match_feed(y, 56, 968, 112, cancha, home, away, local))
            y += 122
    libres = f"{dot()}".join(NAMES[k] for k in F1["libres"])
    parts.append(info_plain(1456, f'<span style="color: #67E8F9">LIBRE ESTA FECHA:</span> {libres}', 28))
    parts.append(band_story(local))
    return "\n".join(parts)


# ---------------------------------------------------------------- pieza 22 (12:00)
ARROW = ('<svg width="44" height="30" viewBox="0 0 44 30" aria-hidden="true"><path d="M2 15 H38 M26 3 L40 15 L26 27" '
         'fill="none" stroke="#03181C" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path></svg>')
CHEVRON = ('<svg width="46" height="120" viewBox="0 0 46 120" aria-hidden="true" style="opacity: {op}">'
           '<path d="M8 10 L38 60 L8 110" fill="none" stroke="#67E8F9" stroke-width="9" stroke-linecap="round" '
           'stroke-linejoin="round"></path></svg>')


def swipe_pill(top, text, size=32, height=78):
    """Boton cian (como el de la historia de cupos) que avisa que la portada es un carrusel (2026-10-14)."""
    return (f'<div class="row" style="top: {top}px"><span style="display: inline-flex; align-items: center; gap: 20px; '
            f'height: {height}px; padding: 0 42px; border-radius: 999px; background: #67E8F9; color: #03181C; '
            f"font-family: 'Barlow Condensed',system-ui,sans-serif; font-weight: 800; font-size: {size}px; "
            f'letter-spacing: .1em; line-height: 1; box-shadow: 0 0 30px rgba(103,232,249,.5),0 10px 22px rgba(0,0,0,.55)">'
            f'{text}{ARROW}</span></div>')


def edge_chevrons(top, left=962):
    """Flechas en el borde derecho, a media altura: senal clasica de 'hay mas laminas'."""
    svgs = "".join(CHEVRON.format(op=op) for op in (1, .55))
    return (f'<div style="position: absolute; left: {left}px; top: {top}px; display: flex; gap: 0; '
            f'filter: drop-shadow(0 0 10px rgba(103,232,249,.7))">{svgs}</div>')


def portada_feed(local):
    parts = [prog.background("fondo-feed", local),
             T(104, K, "RANCAGUA LEAGUE", 34),
             T(156, CH, "HOY COMIENZA", 104),
             T(262, "title", "THE ORIGIN", 184),
             info_lines(478, "JUEVES 15 DE OCTUBRE", 40, 90),
             info_plain(536, "CANCHAS SAN DAMIÁN", 40),
             kickoff_plate(630, 540, 112, 26, 76),
             crest_rows((800, 912), local, 96, 24),
             edge_chevrons(626),
             swipe_pill(1070, "DESLIZA Y MIRA LOS PARTIDOS"),
             band_feed(local)]
    return "\n".join(parts)


def portada_story(local):
    parts = [prog.background("fondo-historia", local),
             T(262, K, "RANCAGUA LEAGUE", 42),
             T(326, CH, "HOY COMIENZA", 118),
             T(452, "title", "THE", 250),
             T(668, "title", "ORIGIN", 250),
             info_lines(950, "JUEVES 15 DE OCTUBRE", 44, 80),
             info_plain(1014, "CANCHAS SAN DAMIÁN", 44),
             kickoff_plate(1100, 580, 118, 28, 82),
             crest_rows((1272, 1384), local, 96, 24),
             band_story(local)]
    return "\n".join(parts)


def grupo_feed(n, local):
    g = GROUPS[n]
    parts = [prog.background("fondo-feed", local),
             T(42, K, "RANCAGUA LEAGUE", 30),
             T(80, CH, "THE ORIGIN · FECHA 1", 46),
             T(128, "title", f"GRUPO {n}", 112),
             prog.info_row(252, F1, 24, 70)]
    # posiciones: grupo 1 = 2 + 1 partidos y libre; grupo 2 = 1 + 2 partidos y libre (desde el 2026-10-15;
    # antes, sin libre: (330, [394]), (606, [670, 866]))
    layout = {1: [(306, [370, 566]), (774, [838])], 2: [(306, [370]), (578, [642, 838])]}[n]
    for (hour, matches), (t_top, m_tops) in zip(g["turnos"], layout):
        parts.append(prog.time_row(t_top, hour, 46, 250))
        for (cancha, home, away), y in zip(matches, m_tops):
            parts.append(match_h(y, cancha, home, away, local, 180, 120, 108, 34))
    if g["libre"]:
        parts.append(libre_plate(1044, g["libre"], local, 190, 700, 110, 86, 36, 24))
    parts.append(band_feed(local))
    return "\n".join(parts)


def grupo_story(n, local):
    g = GROUPS[n]
    parts = [prog.background("fondo-historia", local),
             T(262, K, "RANCAGUA LEAGUE", 40),
             T(316, CH, "THE ORIGIN · FECHA 1", 60),
             T(380, "title", f"GRUPO {n}", 150),
             prog.info_row(548, F1, 28, 60)]
    # grupo 2 con libre desde el 2026-10-15 (antes: (654, [730]), (960, [1038, 1248]))
    layout = {1: [(600, [676, 886]), (1100, [1176])], 2: [(600, [676]), (890, [966, 1176])]}[n]
    for (hour, matches), (t_top, m_tops) in zip(g["turnos"], layout):
        parts.append(prog.time_row(t_top, hour, 60, 220))
        for (cancha, home, away), y in zip(matches, m_tops):
            parts.append(match_v(y, cancha, home, away, local))
    if g["libre"]:
        parts.append(libre_plate(1392, g["libre"], local, 150, 780, 96, 76, 34, 24))
    parts.append(band_story(local))
    return "\n".join(parts)


# ---------------------------------------------------------------- pieza 20 (recordatorio, reutilizable)
RECORDATORIO = [
    ("CAMISETAS DEL MISMO COLOR",
     "Todas numeradas, sin números repetidos.<br>No necesitan ser del mismo conjunto."),
    ("CANILLERAS OBLIGATORIAS", None),
    ("REVISA TU HORARIO", None),
    ("LLEGA CON ANTICIPACIÓN", None),
]


def recordatorio(local):
    """Historia sin fecha: 4 bloques numerados (texto exacto de la ficha 20)."""
    parts = [prog.background("fondo-historia", local),
             T(262, K, "RANCAGUA LEAGUE", 40),
             T(322, CH, "ANTES DE ENTRAR", 96),
             T(428, "title", "A LA CANCHA", 164)]
    y = 652
    for i, (head, sub) in enumerate(RECORDATORIO, 1):
        h = 236 if sub else 168
        sub_html = (f'<span style="font-family: \'Barlow Condensed\',system-ui,sans-serif; font-weight: 600; '
                    f'font-size: 32px; line-height: 1.2; color: #C9D6DA; text-shadow: 0 2px 6px rgba(0,0,0,.9)">'
                    f'{sub}</span>') if sub else ""
        parts.append(
            f'<div class="match" style="top: {y}px; left: 60px; width: 960px; height: {h}px; border-radius: 16px">'
            f'<div class="court" style="width: 130px"><span class="court-n" style="font-size: 62px">{i:02d}</span></div>'
            f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 14px; padding: 0 40px">'
            f'<span class="tname" style="font-size: 54px; font-weight: 800; letter-spacing: .04em">{head}</span>'
            f'{sub_html}</div></div>')
        y += h + 22
    parts.append(band_story(local))
    return "\n".join(parts)


# (archivo, titulo de pagina, titulo del tablero, ancho, alto, cuerpo, x, y)
ROW2 = 2400
ROW3 = ROW2 + 1350 + 320
ROW4 = ROW3 + 1920 + 410
BOARDS = [
    ("Main", "Hoy nos encontramos", "01 · Info practica - Historia 1 Hoy nos encontramos 1080x1920",
     1080, 1920, info_hoy, 0, 0),
    ("Info-Programacion", "Programacion de hoy", "02 · Info practica - Historia 2 Programacion de hoy 1080x1920",
     1080, 1920, info_programacion, 1160, 0),
    ("Apertura-Portada", "Hoy comienza The Origin", "03 · Hoy comienza - Feed 1 Portada 1080x1350",
     1080, 1350, portada_feed, 0, ROW2),
    ("Apertura-Grupo-1", "Grupo 1 - Fecha 1", "04 · Hoy comienza - Feed 2 Grupo 1 1080x1350",
     1080, 1350, lambda local: grupo_feed(1, local), 1160, ROW2),
    ("Apertura-Grupo-2", "Grupo 2 - Fecha 1", "05 · Hoy comienza - Feed 3 Grupo 2 1080x1350",
     1080, 1350, lambda local: grupo_feed(2, local), 2320, ROW2),
    ("Apertura-Historia-Portada", "Hoy comienza The Origin", "06 · Hoy comienza - Historia portada 1080x1920",
     1080, 1920, portada_story, 0, ROW3),
    ("Apertura-Historia-Grupo-1", "Grupo 1 - Fecha 1", "07 · Hoy comienza - Historia Grupo 1 1080x1920",
     1080, 1920, lambda local: grupo_story(1, local), 1160, ROW3),
    ("Apertura-Historia-Grupo-2", "Grupo 2 - Fecha 1", "08 · Hoy comienza - Historia Grupo 2 1080x1920",
     1080, 1920, lambda local: grupo_story(2, local), 2320, ROW3),
    ("Recordatorio-Jugadores", "Antes de entrar a la cancha",
     "09 · Recordatorio jugadores - Historia reutilizable 1080x1920", 1080, 1920, recordatorio, 0, ROW4),
]


def check():
    keys = [k for g in GROUPS.values() for _h, ms in g["turnos"] for _c, a, b in ms for k in (a, b)]
    keys += [g["libre"] for g in GROUPS.values() if g["libre"]]
    assert sorted(keys) == sorted(sum(COVER_ROWS, [])) == sorted(NAMES), "los grupos no suman los 14 equipos"
    fixture = {(c, a, b) for _h, ms in F1["turnos"] for c, a, b in ms}
    grupos = {(c, a, b) for g in GROUPS.values() for _h, ms in g["turnos"] for c, a, b in ms}
    assert fixture == grupos, "los cruces por grupo no coinciden con la programacion"


def write_canvas():
    path = os.path.join(HERE, "project", "canvas.json")
    created = {"v": 1, "at": "2026-10-08T13:30:00Z"}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            created = json.load(fh).get("createdOnFiles", created)
    boards = {f"{n}.dc.html": {"x": x, "y": y, "w": w, "h": h, "title": t} for n, _p, t, w, h, _b, x, y in BOARDS}
    notes = {
        "p21": {"x": 0, "y": -300, "text": "10:00 · Info practica (historias)", "kind": "title1", "maxW": 2240},
        "p22": {"x": 0, "y": ROW2 - 300, "text": "12:00 · Hoy comienza The Origin (carrusel + historias)",
                "kind": "title1", "maxW": 3400},
        "p20": {"x": 0, "y": ROW4 - 300, "text": "Recordatorio para jugadores (reutilizable)",
                "kind": "title1", "maxW": 2240},
    }
    canvas = {"v": 3, "createdOnFiles": created, "title": "Dia 1 The Origin RL", "launch": {"view": "canvas"},
              "pages": [], "boards": boards, "order": list(boards), "notes": notes, "designSystems": []}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(canvas, fh, ensure_ascii=False, indent=1)


def dc_html(title, body, w, h):
    return prog.dc_html(title, body, w, h).replace(prog.CSS.strip(), CSS)


def preview_html(title, body, w, h):
    html = prog.preview_html(title, body, w, h).replace(prog.CSS.strip(), CSS)
    return html.replace("<style>", "<style>\nbody{margin:0}", 1)


def main():
    check()
    os.makedirs(os.path.join(HERE, "project"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    write_canvas()
    for name, title, _t, w, h, body, _x, _y in BOARDS:
        with open(os.path.join(HERE, "project", f"{name}.dc.html"), "w", encoding="utf-8") as fh:
            fh.write(dc_html(title, body(False), w, h))
        with open(os.path.join(HERE, "preview", f"{name}.html"), "w", encoding="utf-8") as fh:
            fh.write(preview_html(title, body(True), w, h))
        print("ok", name)
    if "--render" in sys.argv:
        prog.HERE = HERE
        wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
        for name, _p, _t, w, h, _b, _x, _y in BOARDS:
            if not wanted or name in wanted:
                prog.render(name, w, h)
                print("render", name)
        shutil.rmtree(os.path.join(HERE, "chrome-prof"), ignore_errors=True)


if __name__ == "__main__":
    main()
