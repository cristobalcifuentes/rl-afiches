"""Manda un mensaje de WhatsApp al numero del usuario con CallMeBot (gratis, solo texto, solo a uno mismo).

    python whatsapp.py "texto"          (o el texto por la entrada estandar)

La clave no va en el codigo ni en el chat. Se lee de las variables de entorno RL_WHATSAPP_PHONE y
RL_CALLMEBOT_APIKEY o, si no estan, del archivo %USERPROFILE%\\.rancagua-league\\callmebot.txt con 2 lineas:
el numero con codigo de pais (+569...) y la apikey que entrega CallMeBot. Si tampoco esta, usa CALLMEBOT_PHONE y
CALLMEBOT_APIKEY de Desktop\\MatchZone\\.env.deploy (el mismo bot y numero del usuario; autorizado el 2026-10-17).
Nunca se imprime la clave.
"""
import os
import pathlib
import sys
import urllib.parse
import urllib.request

ARCHIVO = pathlib.Path.home() / ".rancagua-league" / "callmebot.txt"
MATCHZONE_ENV = pathlib.Path.home() / "Desktop" / "MatchZone" / ".env.deploy"


def _env_file(path):
    datos = {}
    for linea in path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            datos[k.strip().removeprefix("export ").strip()] = v.strip().strip('"').strip("'")
    return datos


def credenciales():
    phone, key = os.environ.get("RL_WHATSAPP_PHONE"), os.environ.get("RL_CALLMEBOT_APIKEY")
    if not (phone and key) and ARCHIVO.exists():
        lineas = [l.strip() for l in ARCHIVO.read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(lineas) >= 2:
            phone, key = lineas[0], lineas[1]
    if not (phone and key) and MATCHZONE_ENV.exists():
        env = _env_file(MATCHZONE_ENV)
        phone, key = env.get("CALLMEBOT_PHONE"), env.get("CALLMEBOT_APIKEY")
    if not (phone and key):
        raise SystemExit(f"Falta la clave de CallMeBot: crear {ARCHIVO} con el numero (+569...) y la apikey, "
                         "una por linea.")
    return phone.replace(" ", ""), key


def enviar(texto):
    phone, key = credenciales()
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": phone, "text": texto, "apikey": key})
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "RL/1.0"}), timeout=60) as r:
        cuerpo = r.read().decode("utf-8", "replace")
    if r.status != 200 or "error" in cuerpo.lower() and "queued" not in cuerpo.lower():
        raise SystemExit(f"CallMeBot respondio {r.status}: {cuerpo[:200]}")
    return True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    texto = " ".join(sys.argv[1:]) or sys.stdin.read()
    enviar(texto.strip())
    print("WhatsApp enviado.")
