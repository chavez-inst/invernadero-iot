# Graficas de resultados para el documento, a partir del CSV que se baja de la pagina
# (boton "Descargar CSV" en "Ajustes, calibracion y datos").
# Genera documento/img/resultados_temperatura.png y documento/img/resultados_humedad.png
#
# Uso: python -I resultados.py ../datos/invernadero_2026-11-21_1830.csv
# Antes de correrlo, poner abajo los limites que quedaron en la pagina el dia de la prueba.

import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

# limites que se usaron en la prueba (se copian de la pagina)
TEMPERATURA_ABRIR = 28.0
TEMPERATURA_CERRAR = 26.0
HUMEDAD_REGAR = 35.0

CARPETA_IMG = Path(__file__).resolve().parent.parent / "img"


def leer_csv(ruta):
    columnas = {"hora": [], "temperatura": [], "aire": [], "suelo": [], "ventilador": [], "ventana": [], "bomba": []}
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            columnas["hora"].append(datetime.strptime(fila["hora"], "%Y-%m-%d %H:%M:%S"))
            # las celdas vacias son lecturas que fallaron; se dejan como hueco en la grafica
            numero = lambda texto: float(texto) if texto else float("nan")
            columnas["temperatura"].append(numero(fila["temperatura_C"]))
            columnas["aire"].append(numero(fila["humedad_aire_pct"]))
            columnas["suelo"].append(numero(fila["humedad_suelo_pct"]))
            columnas["ventilador"].append(int(fila["ventilador"] or 0))
            columnas["ventana"].append(int(fila["ventana"] or 0))
            columnas["bomba"].append(int(fila["bomba"] or 0))
    return columnas


def sombrear(ejes, horas, estados, color, etiqueta):
    """Sombrea los tramos en los que el actuador estuvo prendido."""
    ejes.fill_between(horas, 0, 1, where=[e == 1 for e in estados], step="mid", color=color, alpha=0.18,
                      transform=ejes.get_xaxis_transform(), label=etiqueta, linewidth=0)


def grafica_temperatura(datos):
    figura, ejes = plt.subplots(figsize=(9, 4))
    sombrear(ejes, datos["hora"], datos["ventilador"], "#1FA3A0", "Ventilador prendido y ventana abierta")
    ejes.plot(datos["hora"], datos["temperatura"], color="#E8604C", linewidth=1.8, label="Temperatura (DHT22)")
    ejes.axhline(TEMPERATURA_ABRIR, color="#E8604C", linestyle="--", linewidth=1, label=f"Abre a {TEMPERATURA_ABRIR} °C")
    ejes.axhline(TEMPERATURA_CERRAR, color="#56697D", linestyle="--", linewidth=1, label=f"Cierra a {TEMPERATURA_CERRAR} °C")
    ejes.set_title("Temperatura y ventilación durante la prueba")
    ejes.set_xlabel("Hora")
    ejes.set_ylabel("Temperatura (°C)")
    ejes.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ejes.grid(color="#e3e3e3")
    ejes.legend(fontsize=8, loc="best")
    figura.tight_layout()
    figura.savefig(CARPETA_IMG / "resultados_temperatura.png", dpi=200)
    plt.close(figura)


def grafica_humedad(datos):
    figura, ejes = plt.subplots(figsize=(9, 4))
    sombrear(ejes, datos["hora"], datos["bomba"], "#3E8EDE", "Bomba regando")
    ejes.plot(datos["hora"], datos["suelo"], color="#3E8EDE", linewidth=1.8, label="Humedad del suelo")
    ejes.plot(datos["hora"], datos["aire"], color="#8FA3B6", linewidth=1.2, linestyle=":", label="Humedad del aire (DHT22)")
    ejes.axhline(HUMEDAD_REGAR, color="#1F63A8", linestyle="--", linewidth=1, label=f"Riega abajo de {HUMEDAD_REGAR:.0f} %")
    ejes.set_ylim(0, 100)
    ejes.set_title("Humedad del suelo y riego durante la prueba")
    ejes.set_xlabel("Hora")
    ejes.set_ylabel("Humedad (%)")
    ejes.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ejes.grid(color="#e3e3e3")
    ejes.legend(fontsize=8, loc="best")
    figura.tight_layout()
    figura.savefig(CARPETA_IMG / "resultados_humedad.png", dpi=200)
    plt.close(figura)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Falta la ruta del CSV. Ejemplo: python -I resultados.py ../datos/invernadero_2026-11-21_1830.csv")
        sys.exit(1)
    datos = leer_csv(sys.argv[1])
    CARPETA_IMG.mkdir(exist_ok=True)
    grafica_temperatura(datos)
    grafica_humedad(datos)
    print("listo:", CARPETA_IMG)
