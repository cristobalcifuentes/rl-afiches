"""Rancagua League - plantilla de programacion de partidos (una fecha).

Genera 3 piezas por fecha:
- Feed 1080x1350 con todos los partidos, agrupados por horario, y el equipo libre al pie.
- Una historia 1080x1920 por horario (zona segura: contenido entre y=250 e y=1670).

Estilo del carrusel "Los equipos de The Origin" (Tomorrow italic para titulares, Barlow Condensed
para nombres y datos) sobre el fondo de cancha. Escudos originales recortados solo al bbox del
alpha (assets/escudos, misma preparacion que herramientas/carrusel-the-origin/preparar.py).

Para una fecha nueva: copiar el bloque FECHA_1, cambiar los datos y agregarlo a FECHAS.
Cada fecha ocupa una fila del lienzo (tableros nuevos; los anteriores no se tocan).

Escribe:
- project/canvas.json y project/<tablero>.dc.html (lienzo Design, imagenes por /_blob/<id>)
- preview/<tablero>.html (mismos tableros con archivos locales, para revisar con Chrome)

Uso: python build.py              (indice completo + archivos de las fechas no congeladas)
     python build.py --fecha 2    (solo los archivos de esa fecha)
     python build.py --render     (ademas renderiza out/<tablero>.png a escala 1)
"""
import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
# Chrome: el de Windows en el PC; en Linux (GitHub Actions) google-chrome, sin sandbox. CHROME manda si esta definida.
CHROME = os.environ.get("CHROME") or next(
    (p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "/usr/bin/google-chrome",
                 "/usr/bin/chromium", "/usr/bin/chromium-browser") if os.path.exists(p)), "google-chrome")
CHROME_EXTRA = [] if os.name == "nt" else ["--no-sandbox"]

# clave -> blob en el lienzo "Programacion de fechas RL"
BLOB = {
    "bototos": "dcf28a5970288a7aaafbe3c4bdde83d0",
    "camajo": "26c7801beaa086168137153a297f2e22",
    "capybara": "11f7d59e7b2553155e0099c3fdccff0d",
    "cerveceros": "26f5c52cd1a728bfa72340329158cc07",
    "control-dirigido": "0efe4caaa24532ce7da0855fdd82059d",
    "gatinhos": "affc32c31e7452eb82347fd54ef3ac73",
    "ikigai-rcv": "654ab67414f557c3d2941f9ef1150b8f",
    "irresponsables": "5bbd34bf4e360a2716720c88e9d04c75",
    "pierde-nunca": "b799979186e7482be8cc5c325df3cba3",
    "profesores": "502d1b3b77adae192666fb5241702d7c",
    "rabanal": "c74e56e59aae8bfd70591ab86c312145",
    "rusticos": "b9f41abf22b6940e6bccd99434666867",
    "saca-chispas": "db335f533c6fffcf4ae85ee4edfe988c",
    "inter": "3bee58fd20546f276a919ad111c1d69c",          # subido el 2026-10-20 (Fecha 2)
    "fondo-feed": "faa7657705ee8b0b7a692ef2e81bce2d",
    "fondo-historia": "e75db2d1aac8cf336f773c32bad1ec2b",
    "rl": "273c1ca5762cb377efbcbaade2e60ba3",
    "sp-monina": "d6e1afe164618c6c298afe6c60171044",
    "sp-turin": "12fde04ad4bb6b511ef890a06246147f",
    "sp-recovery": "9c170a0e80694896903c9674696e77bc",
    "sp-matchzone": "bae3d7c11ef194a020a14cf037aa06f7",
    "sp-invictus": "419df5d1b866d9dfd15ca79e4f970144",
    "sp-marbella": "b7f7d184d8b07928421258a831053130",
    "sp-kine": "0e99b5415374c976b675f481977d2c49",
    "sp-ikigai": "432068673eb73a14c8732bfee0d14f65",
}
LOCAL = {"fondo-feed": "../assets/fondo-feed.png", "fondo-historia": "../assets/fondo-historia.png",
         "rl": "../assets/rl.png"}

# Nombres de presentacion (los que van en la grafica)
NAMES = {
    "bototos": "BOTOTOS FC",
    "camajo": "CAMAJO FC",
    "capybara": "CAPYBARA FC",
    "cerveceros": "CERVECEROS FC",
    "control-dirigido": "CONTROL DIRIGIDO",
    "gatinhos": "GATINHOS",
    "ikigai-rcv": "IKIGAI RCV",
    "irresponsables": "IRRESPONSABLES FC",
    "pierde-nunca": "LOS PIERDE NUNCA",
    "profesores": "PROFESORES F.C.",
    "rabanal": "INDEPENDIENTE RABANAL",
    "rusticos": "RÚSTICOS FC",
    "saca-chispas": "LOS SACA CHISPAS",
    "inter": "INTER DE RANCAGUA",      # equipo 14, entro el 2026-10-15 (Grupo 2)
}

# ---------------------------------------------------------------- datos de cada fecha
FECHA_1 = {
    "id": "Fecha1",
    "numero": 1,
    "edicion": "THE ORIGIN",
    "dia": "JUEVES 15 DE OCTUBRE",
    "sede": "CANCHAS SAN DAMIÁN",
    # (horario, [(cancha, local, visita), ...]) en el orden de la programacion oficial
    "turnos": [
        ("21:00", [(4, "rabanal", "pierde-nunca"),
                   (5, "saca-chispas", "cerveceros"),
                   (6, "camajo", "gatinhos")]),
        ("22:00", [(4, "capybara", "irresponsables"),
                   (5, "profesores", "control-dirigido"),
                   (6, "rusticos", "ikigai-rcv")]),
    ],
    # 2026-10-15: entra Inter de Rancagua (equipo 14, Grupo 2), libre en la Fecha 1. Los tableros
    # publicados el 12 dicen solo Bototos; si se regenera este lienzo, sube su escudo y agregalo a BLOB.
    "libres": ["bototos", "inter"],
    # Sello junto al dia (solo en la variante con auspiciadores). 2026-10-12: se suspendio por lluvia
    # el jueves 8 y se juega el 15.
    "aviso": "REPROGRAMADA",
    # Ya publicada: sus tableros del lienzo son la referencia y build.py no los reescribe
    # (con los libres de hoy cambiaria la linea de libres). --fecha 1 los fuerza.
    "congelada": True,
}
FECHA_2 = {
    "id": "Fecha2",
    "numero": 2,
    "edicion": "THE ORIGIN",
    "dia": "JUEVES 22 DE OCTUBRE",
    "sede": "CANCHAS SAN DAMIÁN",
    # MatchZone, revisado el 2026-10-20
    "turnos": [
        ("21:00", [(4, "capybara", "profesores"),
                   (5, "saca-chispas", "control-dirigido"),
                   (6, "camajo", "rusticos")]),
        ("22:00", [(4, "rabanal", "ikigai-rcv"),
                   (5, "pierde-nunca", "bototos"),
                   (6, "cerveceros", "inter")]),
    ],
    "libres": ["gatinhos", "irresponsables"],
    # Desde la Fecha 2 solo la version con la franja de auspiciadores (regla del 2026-10-08)
    "variantes": [("", "", True)],
}
FECHAS = [FECHA_1, FECHA_2]

# Franja de auspiciadores: 4 a cada lado del logo RL (mismas versiones que la lona y el backdrop;
# MatchZone = isotipo sobre logotipo en una sola imagen)
SPONSORS = [("monina", "Pinturas Monina"), ("turin", "Turín Pizzería &amp; Sushi"),
            ("recovery", "Recovery Room by Warriors"), ("matchzone", "MatchZone"),
            ("invictus", "Invictus Barber Studio"), ("marbella", "Panadería Marbella"),
            ("kine", "Kine Nohm"), ("ikigai", "Ikigai Gourmet")]

# Variantes de cada fecha que se generan (sufijo del archivo, texto del titulo, con franja)
VARIANTES = [("", "", False), ("-Auspiciadores", " con auspiciadores", True)]

with open(os.path.join(HERE, "assets", "escudos", "medidas.json"), encoding="utf-8") as fh:
    MEDIDAS = json.load(fh)
with open(os.path.join(HERE, "assets", "auspiciadores", "medidas.json"), encoding="utf-8") as fh:
    SP_MEDIDAS = json.load(fh)


def crest_size(key, base):
    """Iguala el peso visual: media geometrica entre 'ajustar al cuadro' y 'misma superficie'."""
    m = MEDIDAS[key]
    w, h, cover = m["w"], m["h"], m["cover"]
    s_box = base / max(w, h)
    s_area = base * math.sqrt(0.74 / (cover * w * h))
    s = min(math.sqrt(s_box * s_area), base * 1.08 / max(w, h))
    return round(w * s), round(h * s)


CSS = """
body{margin:0;background:#020606}
.slide{position:relative;overflow:hidden;background:#020606;font-family:'Barlow Condensed',system-ui,sans-serif}
.layer{position:absolute;left:0;top:0;width:100%;height:100%}
.bg{object-fit:cover}
.veil{background-image:radial-gradient(ellipse 70% 52% at 50% 58%,rgba(2,8,9,.66) 0%,rgba(2,8,9,.42) 62%,rgba(2,8,9,.14) 100%)}
.row{position:absolute;left:0;width:100%;display:flex;justify-content:center;align-items:center;white-space:nowrap}
.tx{display:inline-block;font-family:'Tomorrow',system-ui,sans-serif;font-style:italic;line-height:1;transform-origin:50% 50%}
.kicker{font-weight:800;letter-spacing:.2em;margin-right:-.2em;transform:scaleX(.74);
  background-image:linear-gradient(180deg,#FFFFFF 0%,#E9EDEF 45%,#9AA3A8 62%,#DCE1E4 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 2px 0 #1A2124) drop-shadow(0 4px 8px rgba(0,0,0,.8))}
.title{font-weight:800;letter-spacing:-.005em;transform:scaleX(.75) skewX(-5deg);
  background-image:linear-gradient(180deg,#F2FEFF 0%,#A8F3FF 24%,#5EE2FA 46%,#2CC6F4 70%,#139FE6 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 3px 0 #06405C) drop-shadow(0 3px 0 #022231) drop-shadow(0 12px 16px rgba(0,0,0,.75))
         drop-shadow(0 0 26px rgba(103,232,249,.28))}
.chrome{font-weight:800;letter-spacing:-.005em;transform:scaleX(.74) skewX(-5deg);
  background-image:linear-gradient(180deg,#FFFFFF 0%,#F7F9FA 34%,#C3C9CD 50%,#8C9499 56%,#D3D8DB 78%,#FFFFFF 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 2px 0 #3B4347) drop-shadow(0 3px 0 #161B1E) drop-shadow(0 12px 16px rgba(0,0,0,.8))}
.info{font-family:'Barlow Condensed',system-ui,sans-serif;font-weight:700;letter-spacing:.16em;margin-right:-.16em;
  line-height:1;color:#EEF3F5;text-shadow:0 2px 6px rgba(0,0,0,.95)}
.dot{color:#67E8F9;margin:0 .35em}
.sideline{height:2px;box-shadow:0 0 8px rgba(103,232,249,.5)}
.match{position:absolute;display:flex;align-items:stretch;box-sizing:border-box;overflow:hidden;
  background-image:linear-gradient(90deg,rgba(4,13,15,.9) 0%,rgba(5,15,17,.82) 100%);
  border:1px solid rgba(103,232,249,.32);box-shadow:0 10px 24px rgba(0,0,0,.5)}
.court{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:none;
  background-image:linear-gradient(180deg,rgba(103,232,249,.2) 0%,rgba(16,130,124,.2) 100%);
  border-right:2px solid #67E8F9}
.court-k{font-weight:700;letter-spacing:.2em;margin-right:-.2em;color:#67E8F9;line-height:1}
.court-n{font-family:'Tomorrow',system-ui,sans-serif;font-style:italic;font-weight:800;color:#FFFFFF;line-height:1;
  text-shadow:0 2px 0 #0B3A46,0 0 18px rgba(103,232,249,.35)}
.teams{flex:1;display:grid;align-items:center;min-width:0}
.team{display:flex;align-items:center;min-width:0}
.cbox{display:flex;align-items:center;justify-content:center;flex:none}
.crest{display:block;object-fit:contain}
.tname{font-weight:700;letter-spacing:.03em;line-height:1.02;color:#F4F8FA;text-shadow:0 2px 6px rgba(0,0,0,.95)}
.vs{font-family:'Tomorrow',system-ui,sans-serif;font-style:italic;font-weight:800;color:#67E8F9;text-align:center;line-height:1;
  text-shadow:0 0 14px rgba(103,232,249,.45),0 2px 0 #06405C}
.sponsors{position:absolute;display:flex;align-items:center;justify-content:center;box-sizing:border-box;border-radius:14px;
  background-image:linear-gradient(180deg,rgba(14,30,34,.88) 0%,rgba(6,15,17,.9) 100%);
  border-top:1px solid rgba(103,232,249,.55);border-bottom:1px solid rgba(103,232,249,.55);
  box-shadow:0 10px 24px rgba(0,0,0,.5),inset 0 1px 18px rgba(103,232,249,.06)}
.rl{position:absolute;border-radius:50%;
  box-shadow:0 0 0 2px rgba(103,232,249,.95),0 0 14px 2px rgba(103,232,249,.75),0 0 40px 6px rgba(103,232,249,.35)}
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Tomorrow:ital,wght@1,700;1,800'
         '&amp;family=Barlow+Condensed:wght@600;700;800&amp;display=swap">')


def src(key, local):
    if local:
        if key.startswith("sp-"):
            return f"../assets/auspiciadores/{key[3:]}.png"
        return LOCAL.get(key, f"../assets/escudos/{key}.png")
    return f"/_blob/{BLOB[key]}"


def text_row(top, cls, text, size):
    return (f'<div class="row" style="top: {top}px"><span class="tx {cls}" style="font-size: {size}px">'
            f'{text}</span></div>')


def lines_row(top, inner, line_w, gap):
    return (f'<div class="row" style="top: {top}px; gap: {gap}px">'
            f'<div class="sideline" style="width: {line_w}px; background-image: linear-gradient(90deg,rgba(103,232,249,0),#67E8F9)"></div>'
            f'{inner}'
            f'<div class="sideline" style="width: {line_w}px; background-image: linear-gradient(90deg,#67E8F9,rgba(103,232,249,0))"></div>'
            f'</div>')


def info_row(top, f, size, line_w, aviso=None):
    inner = (f'<span class="info" style="font-size: {size}px">{f["dia"]}<span class="dot">·</span>{f["sede"]}</span>')
    if aviso:
        # Sello cian solido con letra negra antes del dia (estilo del boton de la historia de cupos)
        pill = (f'<span style="font-weight: 800; font-size: {round(size * .82)}px; letter-spacing: .14em; line-height: 1; '
                f'padding: .3em .46em .26em .6em; border-radius: 6px; background: #67E8F9; color: #0C0D0D; '
                f'box-shadow: 0 0 18px rgba(103,232,249,.45), 0 4px 10px rgba(0,0,0,.6)">{aviso}</span>')
        inner = f'<span style="display: flex; align-items: center; gap: {round(size * .55)}px">{pill}{inner}</span>'
    if not line_w:
        return f'<div class="row" style="top: {top}px">{inner}</div>'
    return lines_row(top, inner, line_w, 22)


def time_row(top, hour, size, line_w):
    return lines_row(top, f'<span class="tx title" style="font-size: {size}px">{hour}</span>', line_w, 18)


def background(key, local):
    return (f'<img class="layer bg" src="{src(key, local)}" alt="">\n'
            f'<div class="layer veil"></div>')


def footer_rl(local, width, center, size, line):
    gap = 22
    left_x = width / 2 - size / 2 - gap - line
    right_x = width / 2 + size / 2 + gap
    return (f'<div class="sideline" style="position: absolute; left: {left_x:.0f}px; top: {center - 1}px; width: {line}px; '
            f'background-image: linear-gradient(90deg,rgba(103,232,249,0),#67E8F9)"></div>\n'
            f'<div class="sideline" style="position: absolute; left: {right_x:.0f}px; top: {center - 1}px; width: {line}px; '
            f'background-image: linear-gradient(90deg,#67E8F9,rgba(103,232,249,0))"></div>\n'
            f'<img class="rl" src="{src("rl", local)}" alt="Rancagua League" '
            f'style="left: {(width - size) / 2:.0f}px; top: {center - size / 2:.0f}px; width: {size}px; height: {size}px">')


def sponsor_size(key, slot_w, box_h):
    """Mismo criterio que los escudos: media entre 'ajustar a la caja' y 'misma superficie de tinta'."""
    m = SP_MEDIDAS[key]
    w, h, cover = m["w"], m["h"], max(m["cover"], 0.3)
    s_box = min(slot_w / w, box_h / h)
    s_area = math.sqrt(0.42 * slot_w * box_h / (cover * w * h))
    s = min(s_box ** 0.6 * s_area ** 0.4, s_box)
    return round(w * s), round(h * s)


def sponsor_band(local, left, top, width, box_h, pad, rl_size, rl_gap):
    """Placa a lo ancho con 4 auspiciadores, logo RL chico y 4 auspiciadores. Cada logo es un bloque
    propio; las cajas usan todo el ancho disponible (sin espacio entre ellas) y su ancho es proporcional a
    la raiz de la proporcion del logo: los alargados reciben mas ancho y los redondos mas alto."""
    side = 10
    free = width - 2 * side - rl_size - 2 * rl_gap
    weight = {k: math.sqrt(SP_MEDIDAS[k]["w"] / SP_MEDIDAS[k]["h"]) for k, _a in SPONSORS}
    total = sum(weight.values())

    def slot(key, alt):
        slot_w = int(free * weight[key] / total)
        lw, lh = sponsor_size(key, slot_w - 8, box_h)
        return (f'<div class="cbox" style="width: {slot_w}px; height: {box_h}px">'
                f'<img class="crest" src="{src("sp-" + key, local)}" alt="Logo {alt}" '
                f'style="width: {lw}px; height: {lh}px"></div>')
    left_logos = "".join(slot(k, a) for k, a in SPONSORS[:4])
    right_logos = "".join(slot(k, a) for k, a in SPONSORS[4:])
    rl = (f'<img class="rl" src="{src("rl", local)}" alt="Rancagua League" '
          f'style="position: relative; flex: none; width: {rl_size}px; height: {rl_size}px; margin: 0 {rl_gap}px">')
    return (f'<div class="sponsors" style="top: {top}px; left: {left}px; width: {width}px; height: {box_h + 2 * pad}px; '
            f'padding: 0 {side}px">{left_logos}{rl}{right_logos}</div>')


def crest_img(key, local, box, base):
    cw, ch = crest_size(key, base)
    return (f'<div class="cbox" style="width: {box}px; height: {box}px">'
            f'<img class="crest" src="{src(key, local)}" alt="Escudo {NAMES[key].title()}" '
            f'style="width: {cw}px; height: {ch}px"></div>')


def court_tab(cancha, width, k_size, n_size):
    return (f'<div class="court" style="width: {width}px; gap: 4px">'
            f'<span class="court-k" style="font-size: {k_size}px">CANCHA</span>'
            f'<span class="court-n" style="font-size: {n_size}px">{cancha}</span></div>')


def match_feed(top, left, width, height, cancha, home, away, local):
    """Fila horizontal: [CANCHA n] escudo NOMBRE  VS  NOMBRE escudo."""
    return (f'<div class="match" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; border-radius: 12px">'
            f'{court_tab(cancha, 104, 15, 46)}'
            f'<div class="teams" style="grid-template-columns: minmax(0, 1fr) 58px minmax(0, 1fr); padding: 0 12px">'
            f'<div class="team" style="gap: 12px; justify-content: flex-start">{crest_img(home, local, 92, 84)}'
            f'<span class="tname" style="font-size: 34px; text-align: left">{NAMES[home]}</span></div>'
            f'<span class="vs" style="font-size: 32px">VS</span>'
            f'<div class="team" style="gap: 12px; justify-content: flex-end">'
            f'<span class="tname" style="font-size: 34px; text-align: right">{NAMES[away]}</span>'
            f'{crest_img(away, local, 92, 84)}</div>'
            f'</div></div>')


def match_story(top, left, width, height, cancha, home, away, local):
    """Bloque vertical: [CANCHA n] | escudo sobre nombre  VS  escudo sobre nombre."""
    def team(key):
        return (f'<div class="team" style="flex-direction: column; justify-content: center; gap: 12px">'
                f'{crest_img(key, local, 120, 108)}'
                f'<span class="tname" style="font-size: 34px; text-align: center; height: 70px; display: flex; '
                f'align-items: flex-start; justify-content: center">{NAMES[key]}</span></div>')
    return (f'<div class="match" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; border-radius: 16px">'
            f'{court_tab(cancha, 140, 19, 70)}'
            f'<div class="teams" style="grid-template-columns: minmax(0, 1fr) 76px minmax(0, 1fr); padding: 0 14px">'
            f'{team(home)}<span class="vs" style="font-size: 44px; padding-bottom: 70px">VS</span>{team(away)}'
            f'</div></div>')


def feed_body(f, local, sponsors=False):
    W = 1080
    parts = [background("fondo-feed", local),
             text_row(42, "kicker", "RANCAGUA LEAGUE", 30),
             text_row(80, "chrome", f["edicion"], 46),
             text_row(128, "title", f"FECHA {f['numero']}", 112),
             info_row(252, f, 24, 70, f.get("aviso") if sponsors else None)]
    left, width, card_h, card_gap = 56, W - 112, 108, 12
    block_tops = [298, 724]
    for (hour, matches), top in zip(f["turnos"], block_tops):
        parts.append(time_row(top, hour, 46, 250))
        y = top + 56
        for cancha, home, away in matches:
            parts.append(match_feed(y, left, width, card_h, cancha, home, away, local))
            y += card_h + card_gap
    if f.get("congelada"):
        libres, label = ", ".join(NAMES[k] for k in f["libres"]), "LIBRE ESTA FECHA:"
    else:
        libres = '<span class="dot">·</span>'.join(NAMES[k] for k in f["libres"])
        label = "LIBRES ESTA FECHA:" if len(f["libres"]) > 1 else "LIBRE ESTA FECHA:"
    parts.append(f'<div class="row" style="top: {1146 if sponsors else 1152}px"><span class="info" style="font-size: 26px">'
                 f'<span style="color: #67E8F9">{label}</span> {libres}</span></div>')
    if sponsors:
        parts.append(sponsor_band(local, 40, 1192, W - 80, 78, 11, 58, 12))
    else:
        parts.append(footer_rl(local, W, 1240, 70, 170))
    return "\n".join(parts)


def story_body(f, hour, matches, local, sponsors=False):
    W = 1080
    parts = [background("fondo-historia", local),
             text_row(262, "kicker", "RANCAGUA LEAGUE", 40),
             text_row(316, "chrome", f["edicion"], 64),
             text_row(384, "title", f"FECHA {f['numero']}", 170),
             # con sello, la fila no cabe con las lineas laterales: van sin lineas
             info_row(576, f, 30, 0 if sponsors and f.get("aviso") else 60, f.get("aviso") if sponsors else None),
             time_row(632, hour, 120, 200)]
    left, width, card_h, card_gap = 60, W - 120, (226 if sponsors else 236), 24
    y = 800
    for cancha, home, away in matches:
        parts.append(match_story(y, left, width, card_h, cancha, home, away, local))
        y += card_h + card_gap
    if sponsors:
        parts.append(sponsor_band(local, 40, 1544, W - 80, 84, 11, 62, 12))
    else:
        parts.append(footer_rl(local, W, 1614, 84, 170))
    return "\n".join(parts)


def dc_html(page_title, body, w, h):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{page_title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
{CSS.strip()}
</style>
</helmet>
<div class="slide" style="width: {w}px; height: {h}px">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def preview_html(page_title, body, w, h):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{page_title}</title>
{FONTS}
<style>
{CSS.strip()}
</style>
</head>
<body>
<div class="slide" style="width: {w}px; height: {h}px">
{body}
</div>
</body>
</html>
"""


def boards():
    """(archivo, titulo de la pagina, titulo del tablero, ancho, alto, cuerpo) por fecha y pieza."""
    out = []
    num = 1
    for f in FECHAS:
        fid, n = f["id"], f["numero"]
        for suf, label, sp in f.get("variantes", VARIANTES):
            feed_file = "Main" if fid == "Fecha1" and not suf else f"{fid}-Feed{suf}"
            out.append((feed_file, f"Fecha {n} - Programacion", f"{num:02d} · Fecha {n} - Feed{label} 1080x1350",
                        1080, 1350, (lambda f, sp: lambda local: feed_body(f, local, sp))(f, sp)))
            num += 1
            for hour, matches in f["turnos"]:
                hh = hour.replace(":", "")
                out.append((f"{fid}-Historia-{hh}{suf}", f"Fecha {n} - {hour}",
                            f"{num:02d} · Fecha {n} - Historia {hour}{label} 1080x1920", 1080, 1920,
                            (lambda f, h, m, sp: lambda local: story_body(f, h, m, local, sp))(f, hour, matches, sp)))
                num += 1
    return out


def write_canvas(items):
    path = os.path.join(HERE, "project", "canvas.json")
    created = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            created = json.load(fh).get("createdOnFiles")
    entries, order = {}, []
    per_fecha = 1 + max(len(f["turnos"]) for f in FECHAS)
    for index, (name, _p, title, w, h, _b) in enumerate(items):
        row, col = divmod(index, per_fecha)    # cada fecha y variante llena una fila (feed + 2 historias)
        key = f"{name}.dc.html"
        entries[key] = {"x": col * (1080 + 80), "y": row * (1920 + 320), "w": w, "h": h, "title": title}
        order.append(key)
    canvas = {"v": 3, "createdOnFiles": created or {"v": 1, "at": "2026-10-08T15:00:00Z"},
              "title": "Programacion de fechas RL", "launch": {"view": "canvas"}, "pages": [],
              "boards": entries, "order": order, "notes": {}, "designSystems": []}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(canvas, fh, ensure_ascii=False, indent=1)


def render(name, w, h):
    prof = os.path.join(HERE, "chrome-prof")
    raw = os.path.join(HERE, f"raw-{name}.png")
    url = "file:///" + os.path.join(HERE, "preview", f"{name}.html").replace("\\", "/")
    subprocess.run([CHROME, *CHROME_EXTRA, "--headless=new", "--hide-scrollbars", f"--user-data-dir={prof}",
                    "--force-device-scale-factor=2", f"--window-size={w + 200},{h + 200}",
                    "--virtual-time-budget=20000", f"--screenshot={raw}", url],
                   check=True, capture_output=True)
    image = Image.open(raw).convert("RGB").crop((0, 0, w * 2, h * 2))
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    image.resize((w, h), Image.LANCZOS).save(os.path.join(HERE, "out", f"{name}.png"))
    os.remove(raw)


def check(f):
    keys = [k for _h, ms in f["turnos"] for _c, a, b in ms for k in (a, b)] + f["libres"]
    assert len(keys) == len(set(keys)), f"{f['id']}: un equipo aparece dos veces"
    assert all(k in NAMES and k in BLOB for k in keys), f"{f['id']}: equipo sin nombre o sin blob"


def main():
    os.makedirs(os.path.join(HERE, "project"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    for f in FECHAS:
        check(f)
    items = boards()
    write_canvas(items)
    # Archivos: las fechas no congeladas, o solo las pedidas con --fecha N (el indice va completo)
    pedidas = [a for a in sys.argv[1:] if a.isdigit()] if "--fecha" in sys.argv else None
    ids = {f["id"] for f in FECHAS if (str(f["numero"]) in pedidas if pedidas else not f.get("congelada"))}
    items = [it for it in items if any(it[0] == "Main" and i == "Fecha1" or it[0].startswith(i + "-") for i in ids)]
    for name, page_title, _t, w, h, body in items:
        with open(os.path.join(HERE, "project", f"{name}.dc.html"), "w", encoding="utf-8") as fh:
            fh.write(dc_html(page_title, body(False), w, h))
        with open(os.path.join(HERE, "preview", f"{name}.html"), "w", encoding="utf-8") as fh:
            fh.write(preview_html(page_title, body(True), w, h))
        print("ok", name)
    if "--render" in sys.argv:
        for name, _p, _t, w, h, _b in items:
            render(name, w, h)
            print("render", name)
        shutil.rmtree(os.path.join(HERE, "chrome-prof"), ignore_errors=True)


if __name__ == "__main__":
    main()
