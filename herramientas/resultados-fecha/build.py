"""Lienzo "Resultados Fecha 1 RL" (2026-10-17): carrusel unico de resultados de una fecha.

Pedido del usuario: "un carrusel unico para resultados, donde la portada sea el general de los 6 partidos
y despues cada lamina un detallado de los resultados con detalles de goles, tarjetas, etc".

- 01 Main: portada 1080x1350 con los 6 partidos por horario (bloques de la programacion con el marcador
  en vez del VS), los libres y el aviso "DESLIZA".
- 02-07 Partido-<n>: una lamina 1080x1350 por partido, en el orden del fixture: marcador grande, goles y
  tarjetas de cada equipo y jugador del partido.
- 08-14 (2026-10-17, pedido del usuario: "esto mismo, la misma cantidad de laminas en formato historia y agrega
  los logos de los 2 equipos que no jugaron esta fecha"): las mismas 7 en historia 1080x1920, cada una bajo su
  lamina de feed. La portada de historia muestra los libres con su escudo (sin boton DESLIZA: en historias se
  avanza tocando). Lo esencial entre y=262 e y=1650.

Todas con la franja de auspiciadores (regla de la seccion 6 de CLAUDE.md). Reusa los estilos de
programacion-fecha/build.py y los botones de dia-1-the-origin/build.py.

Datos: PARTIDOS. Mientras un dato es None, la lamina muestra un relleno de ejemplo ("NOMBRE JUGADOR",
marcador "-") para ver el diseno; nunca inventar datos reales.

    python build.py [--render [tablero ...]]

Escribe project/ (canvas.json + .dc.html) y preview/*.html con imagenes locales; con --render deja
out/<tablero>.png a escala 1 (render a 2x reducido) para revisar.
"""
import importlib.util
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prog = _load("prog", os.path.join(TOOLS, "programacion-fecha", "build.py"))
dia1 = _load("dia1", os.path.join(TOOLS, "dia-1-the-origin", "build.py"))

# Assets del lienzo "Resultados Fecha 1 RL" (https://claude.ai/artifact/H91kYp48yjJNMGrXUzkKUz), copiados del
# lienzo "Dia 1 The Origin RL" el 2026-10-17 (mismos bytes)
BLOB = {
    "bototos": "608d6eaa5bbecbd4c738d7a50612c9b2",
    "camajo": "c76579b59f288be89a03a87e5213bb96",
    "capybara": "e5ecedad768d3902063cef462a931d52",
    "cerveceros": "3ad2dcd9c6cd4648f9d2504a6a789696",
    "control-dirigido": "2a2fbb2baa950bbaa828769a919af6ca",
    "gatinhos": "1a1f527547c20e61f83d88055c512e55",
    "ikigai-rcv": "5c3e9faa90ab10ac651baa91e09cc1ed",
    "irresponsables": "19480b4dfbbe49fdd90e170ecf96be91",
    "pierde-nunca": "7e061c3a4d9ce79082b7e2db65cfa475",
    "profesores": "165523f4be3e04366f2f80f433ac25a0",
    "rabanal": "499ff04c20693e34a9000d4b1f0e9e2b",
    "rusticos": "23efc012297cf85c3db7bd7f198dd8e0",
    "saca-chispas": "1ec5de69a32d84ac843b9ad3be1c5920",
    "inter": "af1e35e742d9b46ef5d5667929b9b436",
    "fondo-feed": "920d5641fce64a084ef1329ea40513d2",
    "fondo-historia": "86728b94bdc3c1af74c8b96bbde0fbc0",
    "rl": "7ef67a53709b053b211ccbc950556b43",
    "sp-monina": "669ce1953086eaf0fb802445b038b24e",
    "sp-turin": "d831af7ea1a934d9ab3cb8ceaa98fa85",
    "sp-recovery": "06bcd2079a39e46703d3f9bcffdadbc8",
    "sp-matchzone": "357a8023eaf86899f2530f22e86163c9",
    "sp-invictus": "9bbdf5a2deefaccf4f042fb9e08be0c4",
    "sp-marbella": "ab404840fd4ffbf01c7338bed89514a1",
    "sp-kine": "0a05853ad87851f7c34c0205db429e51",
    "sp-ikigai": "b378d6dc62f28d92edc592d80620e17d",
}
PA = "../../programacion-fecha/assets"


def src(key, local):
    if not local:
        return f"/_blob/{BLOB[key]}"
    if key.startswith("sp-"):
        return f"{PA}/auspiciadores/{key[3:]}.png"
    if key in ("fondo-feed", "fondo-historia", "rl"):
        return f"{PA}/{key}.png"
    return f"{PA}/escudos/{key}.png"


prog.src = src          # la plantilla (escudos, franja) usa estos assets
prog.BLOB = BLOB
NAMES = prog.NAMES
F1 = prog.FECHA_1

GRUPO = {k: 1 for k in ("bototos", "camajo", "gatinhos", "ikigai-rcv", "rabanal", "pierde-nunca", "rusticos")}
GRUPO.update({k: 2 for k in ("control-dirigido", "capybara", "cerveceros", "irresponsables", "saca-chispas",
                             "profesores", "inter")})

# ---------------------------------------------------------------- datos (MatchZone)
# marcador: (goles local, goles visita). goles / tarjetas: {"local": [...], "visita": [...]}
#   gol     = ("NOMBRE", "x2")  o  ("NOMBRE", "")  o  ("NOMBRE", "AUTOGOL") (se anota al equipo que suma)
#   tarjeta = ("NOMBRE", "amarilla" | "roja" | "azul")
# figura: ("NOMBRE", clave del equipo) = jugador del partido (tarjeta de Kine Nohm)
# None = dato pendiente: se dibuja el relleno de ejemplo.
PARTIDOS = [
    dict(hora=h, cancha=c, local=a, visita=b, marcador=None, goles=None, tarjetas=None, figura=None)
    for h, ms in F1["turnos"] for c, a, b in ms
]

EJEMPLO_GOLES = {"local": [("NOMBRE JUGADOR", "x2"), ("NOMBRE JUGADOR", "")],
                 "visita": [("NOMBRE JUGADOR", "")]}
EJEMPLO_TARJETAS = {"local": [("NOMBRE JUGADOR", "amarilla")], "visita": [("NOMBRE JUGADOR", "roja")]}

CSS_EXTRA = """
.plate{position:absolute;box-sizing:border-box;
  background-image:linear-gradient(90deg,rgba(4,13,15,.9) 0%,rgba(5,15,17,.84) 100%);
  border:1px solid rgba(103,232,249,.32);box-shadow:0 10px 24px rgba(0,0,0,.5)}
.lbl{font-family:'Barlow Condensed',system-ui,sans-serif;font-weight:700;letter-spacing:.2em;margin-right:-.2em;
  color:#67E8F9;line-height:1}
.score{display:flex;align-items:center;justify-content:center;white-space:nowrap}
.dash{display:block;width:.42em;height:.09em;border-radius:3px;transform:skewX(-12deg);
  background-image:linear-gradient(90deg,#8FA3A9,#DCE1E4,#8FA3A9);box-shadow:0 2px 6px rgba(0,0,0,.7)}
.final{font-weight:800;letter-spacing:.18em;margin-right:-.18em;line-height:1;padding:.32em .5em .28em .68em;border-radius:6px;
  background:#67E8F9;color:#0C0D0D;box-shadow:0 0 18px rgba(103,232,249,.45),0 4px 10px rgba(0,0,0,.6)}
.ev{display:flex;align-items:center;gap:.4em;font-weight:700;letter-spacing:.02em;line-height:1;color:#F4F8FA;
  text-shadow:0 2px 6px rgba(0,0,0,.95);white-space:nowrap}
.ev .d{color:#67E8F9;font-weight:800}
.ev.none{color:#5F7479}
.card{display:inline-block;flex:none;width:.6em;height:.84em;border-radius:3px;transform:rotate(8deg);
  box-shadow:0 2px 5px rgba(0,0,0,.7)}
.card.amarilla{background-image:linear-gradient(160deg,#FFE07A 0%,#F5C518 60%,#D9A40B 100%)}
.card.roja{background-image:linear-gradient(160deg,#FF7B7F 0%,#E5383B 60%,#B71C22 100%)}
.card.azul{background-image:linear-gradient(160deg,#8CC4FF 0%,#2F80ED 60%,#1B5FC2 100%)}
.vline{width:2px;background-image:linear-gradient(180deg,rgba(103,232,249,0),rgba(103,232,249,.55),rgba(103,232,249,0))}
.sec{display:flex;flex-direction:column;align-items:stretch}
.cols{display:grid;grid-template-columns:minmax(0,1fr) 2px minmax(0,1fr);column-gap:28px}
.col{display:flex;flex-direction:column;justify-content:flex-start}
.fig-name{font-weight:800;letter-spacing:.03em;line-height:1;color:#FFFFFF;text-shadow:0 2px 6px rgba(0,0,0,.95)}
.fig-team{font-weight:700;letter-spacing:.12em;line-height:1;color:#A9B8BD}
"""
CSS = prog.CSS.strip() + "\n" + CSS_EXTRA.strip()

T = prog.text_row
BALL = ('<svg width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true" style="flex: none; '
        'filter: drop-shadow(0 0 6px rgba(103,232,249,.45))">'
        '<circle cx="12" cy="12" r="10.6" fill="#F4F8FA" stroke="#0C0D0D" stroke-width="1"></circle>'
        '<polygon points="12,7.3 16.1,10.3 14.6,15.1 9.4,15.1 7.9,10.3" fill="#0C0D0D"></polygon>'
        '<path d="M12 7.3V1.6 M16.1 10.3 21.9 8.6 M14.6 15.1 18.2 20 M9.4 15.1 5.8 20 M7.9 10.3 2.1 8.6" '
        'stroke="#0C0D0D" stroke-width="1.4" fill="none"></path></svg>')


def dot():
    return '<span class="dot">·</span>'


def score_html(m, size, dash_size, gap):
    """Marcador: el numero del ganador en cian, el del perdedor cromado; empate, los dos en cian."""
    if m["marcador"] is None:
        a = b = "-"
        ca = cb = "chrome"
    else:
        a, b = m["marcador"]
        ca = "title" if a >= b else "chrome"
        cb = "title" if b >= a else "chrome"
    return (f'<div class="score" style="gap: {gap}px">'
            f'<span class="tx {ca}" style="font-size: {size}px">{a}</span>'
            f'<span class="dash" style="font-size: {dash_size}px"></span>'
            f'<span class="tx {cb}" style="font-size: {size}px">{b}</span></div>')


# ---------------------------------------------------------------- portada
def match_row(top, m, local, height=104, left=56, width=968):
    """Fila de la programacion (escudo + nombre) con el marcador al centro. Sin la pestana CANCHA n: en la
    portada la cancha no importa (usuario, 2026-10-17); en la lamina de cada partido si va."""
    def team(key, side):
        name = f'<span class="tname" style="font-size: 30px; text-align: {side}">{NAMES[key]}</span>'
        img = prog.crest_img(key, local, 88, 80)
        inner = img + name if side == "left" else name + img
        just = "flex-start" if side == "left" else "flex-end"
        return f'<div class="team" style="gap: 12px; justify-content: {just}">{inner}</div>'
    return (f'<div class="match" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; border-radius: 12px">'
            f'<div class="teams" style="grid-template-columns: minmax(0, 1fr) 168px minmax(0, 1fr); padding: 0 24px">'
            f'{team(m["local"], "left")}{score_html(m, 58, 40, 10)}{team(m["visita"], "right")}'
            f'</div></div>')


def portada(local):
    parts = [prog.background("fondo-feed", local),
             T(42, "kicker", "RANCAGUA LEAGUE", 30),
             T(80, "chrome", "THE ORIGIN", 46),
             T(128, "title", "RESULTADOS", 112),
             prog.lines_row(252, f'<span class="info" style="font-size: 24px">FECHA {F1["numero"]}{dot()}{F1["dia"]}'
                                 f'{dot()}{F1["sede"]}</span>', 60, 22)]
    for (hour, _ms), top in zip(F1["turnos"], (296, 706)):
        parts.append(prog.time_row(top, hour, 46, 250))
        y = top + 54
        for m in [p for p in PARTIDOS if p["hora"] == hour]:
            parts.append(match_row(y, m, local))
            y += 104 + 12
    libres = dot().join(NAMES[k] for k in F1["libres"])
    pill = dia1.swipe_pill(0, "DESLIZA", 24, 52).replace('class="row" style="top: 0px"', 'style="display: flex"')
    parts.append(f'<div class="row" style="top: 1116px; gap: 34px"><span class="info" style="font-size: 25px">'
                 f'<span style="color: #67E8F9">LIBRES:</span> {libres}</span>{pill}</div>')
    parts.append(prog.sponsor_band(local, 40, 1196, 1000, 84, 11, 62, 12))
    return "\n".join(parts)


def libres_plate(top, local, left=60, width=960, height=120):
    """Placa con los equipos libres: escudo + nombre de cada uno (pedido del usuario, 2026-10-17)."""
    teams = "".join(f'<div style="display: flex; align-items: center; gap: 14px">{prog.crest_img(k, local, 86, 80)}'
                    f'<span class="tname" style="font-size: 32px">{NAMES[k]}</span></div>' for k in F1["libres"])
    return (f'<div class="plate" style="top: {top}px; left: {left}px; width: {width}px; height: {height}px; '
            f'border-radius: 14px; display: flex; align-items: center; justify-content: center; gap: 40px">'
            f'<span class="lbl" style="font-size: 22px; line-height: 1.25; text-align: center">LIBRES<br>ESTA FECHA</span>'
            f'<div class="vline" style="align-self: stretch; margin: 20px 0"></div>{teams}</div>')


def portada_story(local):
    parts = [prog.background("fondo-historia", local),
             T(262, "kicker", "RANCAGUA LEAGUE", 40),
             T(314, "chrome", "THE ORIGIN", 58),
             T(374, "title", "RESULTADOS", 136),
             prog.lines_row(528, f'<span class="info" style="font-size: 24px">FECHA {F1["numero"]}{dot()}{F1["dia"]}'
                                 f'{dot()}{F1["sede"]}</span>', 40, 20)]
    for (hour, _ms), top in zip(F1["turnos"], (586, 990)):
        parts.append(prog.time_row(top, hour, 46, 250))
        y = top + 54
        for m in [p for p in PARTIDOS if p["hora"] == hour]:
            parts.append(match_row(y, m, local, 102, 60, 960))
            y += 102 + 10
    parts.append(libres_plate(1392, local))
    parts.append(prog.sponsor_band(local, 40, 1544, 1000, 84, 11, 62, 12))
    return "\n".join(parts)


# ---------------------------------------------------------------- lamina de cada partido
# Medidas de cada formato. Zona de goles y tarjetas: marcador normal o compacto (muchos eventos, deja mas alto a
# los eventos). La letra se calcula para que entren todas las filas Y el nombre mas largo en su columna.
# sb_sizes: (escudo, base del escudo, letra del nombre, alto del nombre, marcador, guion)
FEED = dict(w=1080, h=1350, bg="fondo-feed", left=56, width=968,
            kicker=(42, 30), chrome=(80, 46), info=(138, 26, 90),
            sb_top=184, sb_h={False: 350, True: 280},
            sb_sizes={False: (190, 176, 36, 74, 176, 110), True: (150, 140, 32, 66, 140, 88)},
            ev_bottom=1036, fig=(1052, 120), band=1196, max_row=60)
STORY = dict(w=1080, h=1920, bg="fondo-historia", left=60, width=960,
             kicker=(262, 40), chrome=(312, 58), info=(392, 28, 100),
             sb_top=446, sb_h={False: 410, True: 330},
             sb_sizes={False: (214, 198, 40, 82, 196, 124), True: (166, 154, 34, 70, 156, 100)},
             ev_bottom=1392, fig=(1408, 120), band=1544, max_row=66)
EV_PAD, EV_HEAD, EV_SEC_GAP = 30, 26 + 14, 30
SUB_GAP = 22                                     # entre sub-columnas cuando un lado va en 2
CHAR_EM = .47                                    # ancho medio de una mayuscula de Barlow Condensed 700 (medido)
MIN_SIZE = 26                                    # bajo esto avisa: en el celular ya se lee mal


def col_w(L):
    """Ancho de cada lado (local / visita) dentro de la placa de eventos."""
    return (L["width"] - 2 * 40 - 2 * 28 - 2) / 2


def event_lists(m):
    goles = m["goles"] if m["goles"] is not None else EJEMPLO_GOLES
    tarjetas = m["tarjetas"] if m["tarjetas"] is not None else EJEMPLO_TARJETAS
    g = {s: [(n, d, None) for n, d in goles[s]] for s in ("local", "visita")}
    t = {s: [(n, "", c) for n, c in tarjetas[s]] for s in ("local", "visita")}
    return g, t


def item_em(name, detail, is_card):
    """Ancho de un evento en em: nombre, detalle ("x2"), icono y separaciones."""
    w = len(name) * CHAR_EM + (.6 if is_card else .92) + .4
    if detail:
        w += (len(detail) + .3) * CHAR_EM + .4
    return w


def plan(m, L=FEED):
    """Elige el diagrama con la letra mas grande: (marcador normal o compacto) x (1 o 2 sub-columnas por lado)."""
    g, t = event_lists(m)
    sin_tarjetas = not any(t.values())
    widest = max([item_em(n, d, False) for s in g for n, d, _x in g[s]] +
                 [item_em(n, "", True) for s in t for n, _d, _x in t[s]] + [item_em("SIN GOLES", "", True)])
    best = None
    for compact in (False, True):
        height = L["ev_bottom"] - (L["sb_top"] + L["sb_h"][compact] + 16)
        avail = height - 2 * EV_PAD - (EV_HEAD + EV_SEC_GAP + (26 if sin_tarjetas else EV_HEAD))
        for sub in (1, 2):
            rows = max(-(-len(g["local"]) // sub), -(-len(g["visita"]) // sub), 1)
            if not sin_tarjetas:
                rows += max(-(-len(t["local"]) // sub), -(-len(t["visita"]) // sub), 1)
            row_h = min(L["max_row"], avail / rows)
            cw = (col_w(L) - (sub - 1) * SUB_GAP) / sub
            size = min(round(row_h * .64), int(cw * .97 / widest))
            cand = dict(compact=compact, sub=sub, size=size, gap=max(6, round(row_h - size)), height=height)
            # prefiere el diagrama normal y de 1 columna; cambia solo si la letra crece al menos 3 px
            if best is None or size >= best["size"] + 3:
                best = cand
        if best["size"] >= 34:
            break
    return best


def scoreboard(m, local, compact, L):
    height = L["sb_h"][compact]
    crest, base, name_size, name_h, score, dash = L["sb_sizes"][compact]

    def team(key):
        return (f'<div style="display: flex; flex-direction: column; align-items: center; gap: {10 if compact else 14}px">'
                f'{prog.crest_img(key, local, crest, base)}'
                f'<span class="tname" style="font-size: {name_size}px; text-align: center; height: {name_h}px; display: flex; '
                f'align-items: flex-start; justify-content: center">{NAMES[key]}</span></div>')
    estado = "FINAL"
    return (f'<div class="plate" style="top: {L["sb_top"]}px; left: {L["left"]}px; width: {L["width"]}px; height: {height}px; '
            f'border-radius: 16px; '
            f'display: grid; grid-template-columns: minmax(0, 1fr) 300px minmax(0, 1fr); align-items: center; '
            f'padding: 0 20px">'
            f'{team(m["local"])}'
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: {14 if compact else 18}px; '
            f'padding-bottom: {name_h - 14}px">'
            f'{score_html(m, score, dash, 16)}<span class="final" style="font-size: {20 if compact else 22}px">{estado}</span></div>'
            f'{team(m["visita"])}</div>')


def ev_item(name, detail, icon, side, size):
    d = f'<span class="d">{detail}</span>' if detail else ""
    n = f'<span>{name}</span>'
    inner = (n + d + icon) if side == "local" else (icon + n + d)
    just = "flex-end" if side == "local" else "flex-start"
    return f'<div class="ev" style="font-size: {size}px; justify-content: {just}; direction: ltr">{inner}</div>'


def ev_none(text, side, size):
    just = "flex-end" if side == "local" else "flex-start"
    return f'<div class="ev none" style="font-size: {size}px; justify-content: {just}; direction: ltr">{text}</div>'


def section(title, icon_head, data, icon_fn, empty, size, gap, sub):
    """`empty`: texto de un lado sin eventos (un texto para los dos lados, o {"local": ..., "visita": ...})."""
    head = prog.lines_row(0, f'<span style="display: flex; align-items: center; gap: 12px">{icon_head}'
                             f'<span class="lbl" style="font-size: 24px">{title}</span></span>', 150, 18)
    head = head.replace('class="row" style="top: 0px', 'class="row" style="position: relative; top: 0px')
    cols = []
    for side in ("local", "visita"):
        items = data[side]
        vacio = empty[side] if isinstance(empty, dict) else empty
        rows = ([ev_item(n, d, icon_fn(x), side, size) for n, d, x in items] if items
                else [ev_none(vacio, side, size)])
        if sub == 1:
            cols.append(f'<div class="col" style="gap: {gap}px">{"".join(rows)}</div>')
        else:
            # 2 sub-columnas que se llenan de arriba abajo; en el local la primera es la del centro (rtl)
            k = -(-len(rows) // sub)
            dirn = "rtl" if side == "local" else "ltr"
            cols.append(f'<div style="display: grid; grid-template-rows: repeat({k}, auto); grid-auto-flow: column; '
                        f'row-gap: {gap}px; column-gap: {SUB_GAP}px; justify-content: start; align-content: start; '
                        f'direction: {dirn}">{"".join(rows)}</div>')
    return (f'<div class="sec" style="gap: 14px">{head}'
            f'<div class="cols">{cols[0]}<div class="vline"></div>{cols[1]}</div></div>')


def events(m, local, p, L):
    g, t = event_lists(m)
    size, gap, sub = p["size"], p["gap"], p["sub"]
    ball = BALL.format(s=round(size * .92))
    head_ball = BALL.format(s=26)
    head_card = '<span class="card amarilla" style="font-size: 30px"></span>'
    # Lo no informado en MatchZone no se muestra (usuario, 2026-10-17: "lo no informado es no informado nomas").
    # "SIN GOLES" solo si el equipo no marco; si marco y no tiene goleadores informados, "-" (no se inventa nada).
    marc = m["marcador"] or (0, 0)
    vacio = {s: "SIN GOLES" if marc[i] == 0 else "-" for i, s in enumerate(("local", "visita"))}
    goles_html = section("GOLES", head_ball, g, lambda _x: ball, vacio, size, gap, sub)
    if not any(t.values()):
        tarj_html = (prog.lines_row(0, '<span class="lbl" style="font-size: 24px">SIN TARJETAS</span>', 150, 18)
                     .replace('class="row" style="top: 0px', 'class="row" style="position: relative; top: 0px'))
    else:
        tarj_html = section("TARJETAS", head_card, t,
                            lambda c: f'<span class="card {c}"></span>', "-", size, gap, sub)
    top = L["ev_bottom"] - p["height"]
    return (f'<div class="plate" style="top: {top}px; left: {L["left"]}px; width: {L["width"]}px; height: {p["height"]}px; '
            f'border-radius: 16px; '
            f'display: flex; flex-direction: column; justify-content: center; gap: {EV_SEC_GAP}px; padding: {EV_PAD}px 40px">'
            f'{goles_html}{tarj_html}</div>')


def figura(m, local, L):
    """Jugador del partido. Sin "PREMIO" ni el logo de Kine Nohm (usuario, 2026-10-17): repetido en las 6 laminas
    le daba mas peso que al resto de los auspiciadores; Kine va en la franja como los demas y el premio se le
    acredita en las historias del jugador del partido y en la descripcion."""
    top, height = L["fig"]
    name, key = m["figura"] if m["figura"] is not None else ("NOMBRE JUGADOR", m["local"])
    name_size = min(42, int(780 / (len(name) * .5)))       # que un nombre largo no se salga de la placa
    return (f'<div class="plate" style="top: {top}px; left: {L["left"]}px; width: {L["width"]}px; height: {height}px; '
            f'border-radius: 16px; '
            f'display: flex; align-items: center; justify-content: center; gap: 24px; padding: 0 30px">'
            f'{prog.crest_img(key, local, 86, 80)}'
            f'<div style="display: flex; flex-direction: column; gap: 9px; min-width: 0">'
            f'<span class="lbl" style="font-size: 22px">JUGADOR DEL PARTIDO</span>'
            f'<span class="fig-name" style="font-size: {name_size}px">{name}</span>'
            f'<span class="fig-team" style="font-size: 20px">{NAMES[key]}</span></div></div>')


def partido(i, local, L=FEED):
    m = PARTIDOS[i]
    p = plan(m, L)
    info = f'GRUPO {GRUPO[m["local"]]}{dot()}CANCHA {m["cancha"]}{dot()}{m["hora"]}'
    (k_top, k_size), (c_top, c_size), (i_top, i_size, i_line) = L["kicker"], L["chrome"], L["info"]
    parts = [prog.background(L["bg"], local),
             T(k_top, "kicker", "RANCAGUA LEAGUE", k_size),
             T(c_top, "chrome", f'THE ORIGIN{dot()}FECHA {F1["numero"]}', c_size),
             prog.lines_row(i_top, f'<span class="info" style="font-size: {i_size}px">{info}</span>', i_line, 22),
             scoreboard(m, local, p["compact"], L),
             events(m, local, p, L),
             figura(m, local, L),
             prog.sponsor_band(local, 40, L["band"], 1000, 84, 11, 62, 12)]
    return "\n".join(parts)


STORY_Y = 1350 + 320          # fila de las historias (320 px bajo el feed)


def boards():
    """(archivo, titulo de pagina, titulo del tablero, cuerpo, ancho, alto, x, y)"""
    out = [("Main", "Resultados Fecha 1", "01 · Portada - resultados de los 6 partidos 1080x1350", portada,
            1080, 1350, 0, 0)]
    for i, m in enumerate(PARTIDOS):
        title = (f"{i + 2:02d} · Partido {i + 1} - {NAMES[m['local']].title()} vs {NAMES[m['visita']].title()} "
                 f"({m['hora']}, cancha {m['cancha']}) 1080x1350")
        out.append((f"Partido-{i + 1}", f"Resultado partido {i + 1}", title,
                    (lambda i: lambda local: partido(i, local))(i), 1080, 1350, (i + 1) * 1160, 0))
    n = len(out)
    out.append(("Historia-Portada", "Resultados Fecha 1",
                f"{n + 1:02d} · Historia portada - resultados y libres 1080x1920", portada_story, 1080, 1920, 0, STORY_Y))
    for i, m in enumerate(PARTIDOS):
        title = (f"{n + i + 2:02d} · Historia partido {i + 1} - {NAMES[m['local']].title()} vs "
                 f"{NAMES[m['visita']].title()} ({m['hora']}, cancha {m['cancha']}) 1080x1920")
        out.append((f"Historia-Partido-{i + 1}", f"Resultado partido {i + 1}", title,
                    (lambda i: lambda local: partido(i, local, STORY))(i), 1080, 1920, (i + 1) * 1160, STORY_Y))
    return out


def goles_de(lista):
    total = 0
    for _n, d in lista:
        d = d.strip().lower()
        total += int(d[1:]) if d[:1] in ("x", "×") and d[1:].isdigit() else 1
    return total


def check():
    fixture = [(h, c, a, b) for h, ms in F1["turnos"] for c, a, b in ms]
    assert [(m["hora"], m["cancha"], m["local"], m["visita"]) for m in PARTIDOS] == fixture, "no calza con la programacion"
    for m in PARTIDOS:
        assert GRUPO[m["local"]] == GRUPO[m["visita"]], f"{m['local']} y {m['visita']} no son del mismo grupo"
        if m["figura"] is not None:
            assert m["figura"][1] in (m["local"], m["visita"]), "el jugador del partido no es de este partido"
        for fmt, L in (("feed", FEED), ("historia", STORY)):
            if m["goles"] is not None and plan(m, L)["size"] < MIN_SIZE:
                print(f"OJO ({fmt}): {NAMES[m['local']]} vs {NAMES[m['visita']]}: goles y tarjetas a "
                      f"{plan(m, L)['size']} px; acortar los nombres (inicial + apellido) o dividir en 2 laminas")
        if m["marcador"] is not None and m["goles"] is not None:
            for side, n in zip(("local", "visita"), m["marcador"]):
                if goles_de(m["goles"][side]) != n:
                    print(f"OJO: {NAMES[m[side]]} tiene {n} goles y la lista suma {goles_de(m['goles'][side])}")


def write_canvas(items):
    path = os.path.join(HERE, "project", "canvas.json")
    created = {"v": 1, "at": "2026-10-17T08:00:00Z"}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            created = json.load(fh).get("createdOnFiles", created)
    entries = {f"{n}.dc.html": {"x": x, "y": y, "w": w, "h": h, "title": t}
               for n, _p, t, _b, w, h, x, y in items}
    canvas = {"v": 3, "createdOnFiles": created, "title": "Resultados Fecha 1 RL", "launch": {"view": "canvas"},
              "pages": [], "boards": entries, "order": list(entries), "notes": {}, "designSystems": []}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(canvas, fh, ensure_ascii=False, indent=1)


def main():
    check()
    os.makedirs(os.path.join(HERE, "project"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    items = boards()
    write_canvas(items)
    for name, title, _t, body, w, h, _x, _y in items:
        with open(os.path.join(HERE, "project", f"{name}.dc.html"), "w", encoding="utf-8") as fh:
            fh.write(prog.dc_html(title, body(False), w, h).replace(prog.CSS.strip(), CSS))
        with open(os.path.join(HERE, "preview", f"{name}.html"), "w", encoding="utf-8") as fh:
            html = prog.preview_html(title, body(True), w, h).replace(prog.CSS.strip(), CSS)
            fh.write(html.replace("<style>", "<style>\nbody{margin:0}", 1))
        print("ok", name)
    if "--render" in sys.argv:
        prog.HERE = HERE
        wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
        for name, _p, _t, _b, w, h, _x, _y in items:
            if not wanted or name in wanted:
                prog.render(name, w, h)
                print("render", name)
        shutil.rmtree(os.path.join(HERE, "chrome-prof"), ignore_errors=True)


if __name__ == "__main__":
    main()
