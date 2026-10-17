"""Avisa por WhatsApp (CallMeBot) que los afiches de una fecha estan listos, con el link de la pagina de descarga.

    python avisar.py <n> <link de la pagina> [--ver]

Arma el mensaje con entrega/fecha-<n>/resultado.json (lo escribe fecha.py). Con --ver solo lo muestra.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def mensaje(n, link):
    with open(os.path.join(HERE, "entrega", f"fecha-{n}", "resultado.json"), encoding="utf-8") as fh:
        r = json.load(fh)
    dia = r["dia"].capitalize().replace(" De ", " de ")
    L = [f"*RL · AFICHES FECHA {n} LISTOS*", f"{dia} · 14 afiches en x2 (7 feed + 7 historias)", "",
         "Descargalos aqui:", link]
    if r["avisos"]:
        L += ["", "*Antes de publicar:*"] + [f"- {a}" for a in r["avisos"]]
    else:
        L += ["", "Datos completos en MatchZone."]
    return "\n".join(L)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    texto = mensaje(int(sys.argv[1]), sys.argv[2])
    if "--ver" in sys.argv:
        print(texto)
        return
    spec = importlib.util.spec_from_file_location("whatsapp", os.path.join(HERE, "..", "comunes", "whatsapp.py"))
    wa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wa)
    wa.enviar(texto)
    print("WhatsApp enviado.")


if __name__ == "__main__":
    main()
