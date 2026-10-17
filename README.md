# Afiches de resultados · Rancagua League

Los 14 afiches de resultados de cada fecha de **THE ORIGIN** (portada y un afiche por partido, en feed 4:5 e historia 9:16, a 2160 px de ancho), armados con los datos públicos de MatchZone.

**Afiches publicados:** https://cristobalcifuentes.github.io/rl-afiches/

## Cómo se piden

1. Terminar de cargar la fecha en MatchZone: resultados, jugador del partido y los goleadores que se tengan.
2. En la app de GitHub: **rl-afiches › Actions › Afiches de resultados › Run workflow**.
   - **Fecha:** vacío toma la última con partidos jugados.
   - **Generar igual:** arma los afiches aunque falten datos.
   - **Prueba:** no publica ni avisa; los afiches quedan para descargar en la corrida.
3. En unos 3 minutos llega un WhatsApp con el link a la página de la fecha, donde cada afiche se descarga en x2.

Si a un partido le falta el resultado o el jugador del partido, no se publica nada y el WhatsApp dice qué falta. Los goles sin goleador informado no frenan: lo no informado no se muestra (ese lado lleva "-") y el WhatsApp los avisa.

## Qué hay aquí

- `herramientas/resultados-fecha/`: el diseño (`build.py`), los afiches de una fecha (`fecha.py`), el botón (`boton.py`) y el mensaje (`avisar.py`).
- `herramientas/matchzone-datos/`: la bajada de datos de MatchZone (`bajar.py`) y el estado entre corridas (`datos/consolidado.json`, que reparte los goles por partido).
- `herramientas/programacion-fecha/`: estilos, escudos, logos de los auspiciadores y fondos.
- `docs/`: la página publicada en GitHub Pages.

Las herramientas se editan en la carpeta de Rancagua League del PC y se suben con `herramientas/automatizacion/sincronizar.py`. La clave de WhatsApp va en los secretos del repositorio (`RL_WHATSAPP_PHONE`, `RL_CALLMEBOT_APIKEY`), nunca en el código.
