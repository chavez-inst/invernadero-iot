# Croquis de la maqueta con medidas en centimetros (lo explica Proyecto/04_Maqueta/propuesta.md).
# Genera documento/img/maqueta_croquis.png con tres vistas:
#   vista de arriba de la base, piezas que se cortan del medio pliego de carton pluma y vista de frente.
# Uso: python -I maqueta.py

from pathlib import Path

import matplotlib.patches as parches
import matplotlib.pyplot as plt

TINTA = "#16324F"
CARTON = "#F4F1EA"
MICA = "#DCEBF7"
AGUA = "#9CC9EA"


def rectangulo(ejes, x, y, ancho, alto, color=CARTON, borde=TINTA, texto=None, tam=8, **extra):
    ejes.add_patch(parches.Rectangle((x, y), ancho, alto, facecolor=color, edgecolor=borde, linewidth=1.2, **extra))
    if texto:
        ejes.text(x + ancho / 2, y + alto / 2, texto, ha="center", va="center", fontsize=tam, color=TINTA)


def cota(ejes, x1, y1, x2, y2, texto, desfase=(0, 0), tam=7.5):
    ejes.annotate("", xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle="<->", color="#56697D", lw=0.8))
    ejes.text((x1 + x2) / 2 + desfase[0], (y1 + y2) / 2 + desfase[1], texto, ha="center", va="center", fontsize=tam,
              color="#56697D", bbox=dict(facecolor="white", edgecolor="none", pad=0.6))


def vista_arriba(ejes):
    ejes.set_title("1. Vista de arriba de la base (50 × 35 cm)", fontsize=11, loc="left")
    rectangulo(ejes, 0, 0, 50, 35, color="#FBFAF6")
    # invernadero: 26 de ancho por 18 de fondo; el frente da hacia la orilla de abajo del dibujo
    rectangulo(ejes, 3, 5, 26, 18, color=MICA)
    ejes.text(16, 21.6, "Invernadero (26 × 18)", ha="center", fontsize=8.5, color=TINTA, weight="bold")
    rectangulo(ejes, 3, 5, 0.5, 18, color=CARTON)       # pared izquierda (ventana)
    rectangulo(ejes, 28.5, 5, 0.5, 18, color=CARTON)    # pared derecha (ventilador)
    rectangulo(ejes, 3, 22.5, 26, 0.5, color=CARTON)    # pared trasera
    ejes.text(3.8, 13, "ventana\ny servo", fontsize=7, color=TINTA, va="center")
    ejes.text(28.2, 13, "ventilador", fontsize=7, color=TINTA, va="center", ha="right")
    # tupper con tierra
    rectangulo(ejes, 7, 6, 15, 15, color="#C9A27E", texto="Tupper con tierra\n(15 × 15)", tam=7.5)
    ejes.add_patch(parches.Rectangle((18.5, 12), 0.8, 2.2, facecolor="#1D1D1D"))
    ejes.text(19.6, 11.4, "sensor de\nhumedad", fontsize=6.5, color=TINTA)
    ejes.add_patch(parches.Rectangle((23.5, 22.0), 1.6, 0.5, facecolor="#E8604C"))
    ejes.text(24.3, 20.6, "DHT22", fontsize=6.5, color=TINTA, ha="center")
    # deposito, protoboard y eliminador
    ejes.add_patch(parches.Circle((34, 28.5), 4, facecolor=AGUA, edgecolor=TINTA, linewidth=1.2))
    ejes.text(34, 28.5, "Depósito\ncon bomba", ha="center", va="center", fontsize=7.5, color=TINTA)
    ejes.plot([31, 26, 26], [28.5, 28.5, 22.5], color="#7FA9C9", linewidth=2.5)
    ejes.text(26.4, 30.0, "manguera (entra por la pared trasera)", fontsize=6.5, color="#56697D", ha="right")
    rectangulo(ejes, 31.5, 12, 16.5, 5.5, color="#F3EBD6")
    ejes.text(36.6, 14.75, "Protoboard 830\nfila 1 a la\nizquierda", ha="center", va="center", fontsize=6.5, color=TINTA)
    rectangulo(ejes, 42, 12.3, 6.3, 4.9, color="#2B2F36")
    ejes.text(45.1, 14.75, "ESP32", fontsize=7, color="white", ha="center", va="center")
    ejes.annotate("cable USB a la\nlaptop o cargador", xy=(48.3, 14.7), xytext=(44, 4), fontsize=6.5, color=TINTA,
                  arrowprops=dict(arrowstyle="->", color=TINTA, lw=0.8))
    rectangulo(ejes, 41, 26, 6, 4, color="#2F8F3A", texto="adaptador\ndel eliminador", tam=6.5)
    ejes.text(32.5, 21.2, "cables de los sensores y\nel servo: por la muesca de\nla pared derecha (abajo, atrás)", fontsize=6.5,
              color="#56697D")
    ejes.text(16, 1.5, "FRENTE (lado de la cámara)", ha="center", fontsize=8, color=TINTA, weight="bold")
    cota(ejes, 0, -1.6, 50, -1.6, "50")
    cota(ejes, -1.6, 0, -1.6, 35, "35", desfase=(0, 0))
    cota(ejes, 3, 3.6, 29, 3.6, "26")
    cota(ejes, 30.2, 5, 30.2, 23, "18", desfase=(0.6, 0))
    ejes.set_xlim(-3.5, 51.5)
    ejes.set_ylim(-3.5, 36)


def piezas(ejes):
    ejes.set_title("2. Piezas de cartón pluma (medio pliego de 50 × 35 cm)", fontsize=11, loc="left")
    rectangulo(ejes, 0, 0, 50, 35, color="#FFFFFF", borde="#9AAABA", linestyle="--")
    # pared trasera: pentagono de 26 de ancho, 16 en los lados y 21 en la punta
    ejes.add_patch(parches.Polygon([(0.5, 0.5), (26.5, 0.5), (26.5, 16.5), (13.5, 21.5), (0.5, 16.5)],
                                   facecolor=CARTON, edgecolor=TINTA, linewidth=1.2))
    ejes.text(13.5, 9, "Pared trasera\n26 de ancho, 16 de alto\ny 21 en la punta", ha="center", fontsize=8, color=TINTA)
    ejes.add_patch(parches.Circle((22.5, 12.5), 0.6, facecolor="white", edgecolor=TINTA))
    ejes.text(22.5, 13.8, "hoyo para la\nmanguera (Ø 1)", ha="center", fontsize=6.5, color="#56697D")
    # pared izquierda con la ventana
    rectangulo(ejes, 28, 0.5, 18, 16)
    rectangulo(ejes, 32, 7.5, 10, 6, color="#FFE7C2")
    ejes.text(37, 10.5, "ventana 10 × 6\n(se recorta y\nse vuelve la hoja)", ha="center", va="center", fontsize=6.5, color=TINTA)
    ejes.text(37, 3.0, "Pared izquierda 18 × 16", ha="center", fontsize=8, color=TINTA)
    cota(ejes, 28, 15.6, 46, 15.6, "18", desfase=(0, 0))
    cota(ejes, 44.6, 0.5, 44.6, 7.5, "7")
    # pared derecha con el hueco del ventilador
    rectangulo(ejes, 28, 18, 18, 16)
    rectangulo(ejes, 35, 24, 4, 4, color="#FFFFFF")
    ejes.text(37, 26, "4 × 4", ha="center", va="center", fontsize=6.5, color=TINTA)
    ejes.text(36, 23.4, "Pared derecha 18 × 16\nhueco del ventilador al centro,\na 9 del piso; muesca de 2 × 1.5\nabajo atrás para los cables",
              ha="center", va="top", fontsize=6.8, color=TINTA)
    ejes.add_patch(parches.Rectangle((44, 18), 2, 1.5, facecolor="#FFFFFF", edgecolor=TINTA))
    # tira del frente
    rectangulo(ejes, 0.5, 23.5, 26, 2, texto="Tira del frente 26 × 2 (viga de arriba)", tam=7)
    ejes.text(13.5, 30, "Sobra: guardarla por si una pieza sale mal", ha="center", fontsize=7.5, color="#56697D")
    ejes.set_xlim(-1, 51)
    ejes.set_ylim(-1, 36)


def vista_frente(ejes):
    ejes.set_title("3. Vista de frente del invernadero (medidas en cm)", fontsize=11, loc="left")
    ejes.plot([-4, 34], [0, 0], color=TINTA, linewidth=1.5)
    # paredes
    ejes.add_patch(parches.Rectangle((0, 0), 0.5, 16, facecolor=CARTON, edgecolor=TINTA))
    ejes.add_patch(parches.Rectangle((25.5, 0), 0.5, 16, facecolor=CARTON, edgecolor=TINTA))
    ejes.add_patch(parches.Polygon([(0, 16), (13, 21), (26, 16)], closed=False, fill=False, edgecolor=TINTA, linewidth=2))
    ejes.add_patch(parches.Polygon([(0.5, 16), (13, 20.8), (25.5, 16)], facecolor=MICA, edgecolor="none"))
    ejes.text(13, 18.2, "techo de mica\n(2 piezas de 18 × 14)", ha="center", fontsize=7, color=TINTA)
    ejes.add_patch(parches.Rectangle((0, 15), 26, 1, facecolor=CARTON, edgecolor=TINTA))
    ejes.add_patch(parches.Rectangle((0.5, 0.2), 25, 14.8, facecolor=MICA, edgecolor="#7FA9C9", alpha=0.45, linestyle="--"))
    ejes.text(13, 13.5, "frente: hoja de mica pegada solo de arriba (se levanta)", ha="center", fontsize=7, color=TINTA)
    # ventana abierta con el servo como bisagra
    ejes.plot([0.25, -3.5], [13, 8.8], color="#F2A33A", linewidth=3)
    ejes.add_patch(parches.Rectangle((0.6, 13.1), 1.3, 2.2, facecolor="#2F6FD6"))
    ejes.text(-4.9, 17.2, "ventana abierta;\nel servo es la bisagra", fontsize=6.5, color=TINTA)
    # ventilador en la pared derecha
    ejes.add_patch(parches.Rectangle((26, 7), 1, 4, facecolor="#2A2D31"))
    ejes.text(27.4, 9, "ventilador\n(saca aire)", fontsize=6.5, color=TINTA, va="center")
    # tupper, planta, sensor y dht
    ejes.add_patch(parches.Rectangle((4, 0), 15, 7, facecolor="#C9A27E", edgecolor=TINTA))
    ejes.add_patch(parches.Rectangle((15.5, 2), 0.8, 7.5, facecolor="#1D1D1D"))
    ejes.plot([9, 9], [7, 10.5], color="#0E7471", linewidth=2)
    ejes.add_patch(parches.Ellipse((9, 11), 3, 1.4, facecolor="#1FA3A0"))
    ejes.add_patch(parches.Rectangle((20.5, 8), 1.6, 2.2, facecolor="#E8604C"))
    ejes.text(21.3, 6.6, "DHT22 (en la\npared trasera)", fontsize=6.3, color=TINTA, ha="center")
    ejes.text(16.6, 4.8, "sensor", fontsize=6.3, color="white")
    cota(ejes, -1.6, 0, -1.6, 16, "16", desfase=(0, 0))
    cota(ejes, 28.5, 0, 28.5, 21, "21", desfase=(0.9, 0))
    cota(ejes, 0, -1.2, 26, -1.2, "26")
    cota(ejes, 1.8, 7, 1.8, 13, "6", desfase=(0.5, 0))
    ejes.set_xlim(-5, 34)
    ejes.set_ylim(-2.5, 23)


def main():
    figura = plt.figure(figsize=(14, 10))
    malla = figura.add_gridspec(2, 2, height_ratios=[1, 0.9])
    ejes_arriba = figura.add_subplot(malla[0, 0])
    ejes_piezas = figura.add_subplot(malla[0, 1])
    ejes_frente = figura.add_subplot(malla[1, :])
    for ejes, funcion in ((ejes_arriba, vista_arriba), (ejes_piezas, piezas), (ejes_frente, vista_frente)):
        funcion(ejes)
        ejes.set_aspect("equal")
        ejes.axis("off")
    figura.suptitle("Maqueta del invernadero: croquis con medidas en centímetros", fontsize=14, color=TINTA)
    figura.tight_layout()
    salida = Path(__file__).resolve().parent.parent / "img" / "maqueta_croquis.png"
    figura.savefig(salida, dpi=200)
    print(salida)


if __name__ == "__main__":
    main()
