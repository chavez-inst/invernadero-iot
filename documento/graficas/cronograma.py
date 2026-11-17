# Diagrama de Gantt del cronograma del proyecto, para el trabajo escrito.
# Las etapas son las de Proyecto/01_Planeacion/PLAN.md.
# Genera documento/img/cronograma.png

from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

AZUL, GRIS, ROJO, VERDE = "#2b4c7e", "#9aa8bf", "#d9534f", "#1FA3A0"

# (etapa, primer dia, ultimo dia, color)
etapas = [
    ("Primera propuesta (cuarto inteligente):\nplaca, programa y página web", date(2026, 11, 4), date(2026, 11, 15), GRIS),
    ("Asignación del proyecto: invernadero", date(2026, 11, 16), date(2026, 11, 16), ROJO),
    ("Plan, compras, diagramas, programa y página", date(2026, 11, 16), date(2026, 11, 17), AZUL),
    ("Compra de material y documento", date(2026, 11, 18), date(2026, 11, 20), AZUL),
    ("Partes de la maqueta en casa", date(2026, 11, 19), date(2026, 11, 20), AZUL),
    ("Reunión: armado, calibración,\nprueba completa y grabación", date(2026, 11, 21), date(2026, 11, 21), VERDE),
    ("Resultados en el documento y\nedición del video", date(2026, 11, 22), date(2026, 11, 22), AZUL),
    ("Entrega", date(2026, 11, 23), date(2026, 11, 23), ROJO),
]

figura, ejes = plt.subplots(figsize=(9.5, 4.4))

for indice, (nombre, inicio, fin, color) in enumerate(etapas):
    # la barra cubre desde el inicio del primer dia hasta el final del ultimo
    duracion = (fin - inicio).days + 1
    ejes.barh(indice, duracion, left=mdates.date2num(inicio), height=0.55, color=color)

ejes.set_yticks(range(len(etapas)))
ejes.set_yticklabels([etapa[0] for etapa in etapas], fontsize=9)
ejes.invert_yaxis()

ejes.xaxis_date()
ejes.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ejes.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
ejes.set_xlim(mdates.date2num(date(2026, 11, 4)), mdates.date2num(date(2026, 11, 24)))
ejes.grid(axis="x", color="#dddddd", linewidth=0.8)
ejes.set_axisbelow(True)

ejes.set_title("Cronograma del proyecto")
ejes.set_xlabel("Fecha (noviembre de 2026)")
ejes.set_ylabel("Etapa")

figura.tight_layout()
salida = Path(__file__).resolve().parent.parent / "img" / "cronograma.png"
salida.parent.mkdir(exist_ok=True)
figura.savefig(salida, dpi=200)
print(salida)
