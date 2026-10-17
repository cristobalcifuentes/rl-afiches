"""Descarga en x2 (regla de la seccion 6) tableros del lienzo "Dia 1 The Origin RL" desde preview/.

    python exportar.py "<carpeta destino>" <Tablero>=<nombre de archivo> [...]

Ejemplo: python exportar.py "../../2 Instagram/X" "Beneficios-1-Portada=1 - Beneficios portada 4x5@2x.png"
El tamano sale del data-props del .dc.html (1080x1350 -> 2160x2700; 1080x1920 -> 2160x3840).
Antes de exportar, comparar project/ con el lienzo vivo (si se edito a mano, bajarlo primero).
"""
import json
import os
import re
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


def size_of(board):
    html = open(os.path.join(HERE, "project", f"{board}.dc.html"), encoding="utf-8").read()
    props = json.loads(re.search(r"data-props='([^']*)'", html).group(1))
    return props["$preview"]["width"], props["$preview"]["height"]


def export(board, dest):
    w, h = size_of(board)
    prof = os.path.join(HERE, "chrome-prof")
    raw = os.path.join(HERE, f"raw-{board}.png")
    url = "file:///" + os.path.join(HERE, "preview", f"{board}.html").replace("\\", "/")
    subprocess.run([CHROME, *CHROME_EXTRA, "--headless=new", "--hide-scrollbars", f"--user-data-dir={prof}",
                    "--force-device-scale-factor=2", f"--window-size={w + 200},{h + 200}",
                    "--virtual-time-budget=30000", f"--screenshot={raw}", url], check=True, capture_output=True)
    im = Image.open(raw).convert("RGB")
    assert im.size[0] >= w * 2 and im.size[1] >= h * 2, (board, im.size)
    im.crop((0, 0, w * 2, h * 2)).save(dest)
    os.remove(raw)
    return w * 2, h * 2


def main():
    folder = sys.argv[1]
    os.makedirs(folder, exist_ok=True)
    for arg in sys.argv[2:]:
        board, name = arg.split("=", 1)
        print(name, export(board, os.path.join(folder, name)))
    shutil.rmtree(os.path.join(HERE, "chrome-prof"), ignore_errors=True)


if __name__ == "__main__":
    main()
