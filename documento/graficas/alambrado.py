# Diagrama de alambrado del invernadero sobre la protoboard de 830 puntos.
# Cada cable va de un hoyo exacto a un pin exacto; las filas (1 a 63) y las letras (a a j) son las que vienen
# impresas en la protoboard. Del mismo juego de datos salen:
#   documento/img/alambrado_completo.png        todo el circuito
#   documento/img/alambrado_<bloque>.png        cada bloque resaltado, para armar por partes
#   documento/tablas/cables.md y cables.tex     la lista numerada de cables y de piezas
# El SVG se pasa a PNG con Microsoft Edge sin ventana.
#
# Uso: python -I alambrado.py

import subprocess
import tempfile
from pathlib import Path

CARPETA_DOCUMENTO = Path(__file__).resolve().parent.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ---------------------------------------------------------------- medidas del dibujo
P = 24                      # distancia entre hoyos (2.54 mm en la protoboard real)
ANCHO, ALTO = 1900, 1300    # tamano del dibujo
BX, BY = 60, 150            # esquina de la protoboard
X0 = BX + 46                # centro del hoyo de la fila 1
ALTO_PROTO = 456
ABAJO = BY + ALTO_PROTO     # borde de abajo de la protoboard

# altura de cada columna y de cada riel, medida desde la orilla de arriba de la protoboard
Y_COLUMNA = {"a": 96, "b": 120, "c": 144, "d": 168, "e": 192,
             "f": 264, "g": 288, "h": 312, "i": 336, "j": 360}
Y_RIEL = {"arriba+": 26, "arriba-": 50, "-": 406, "+": 430}
# hoyos de los rieles: grupos de cinco, con un hueco mas grande a la mitad
FILAS_RIEL = [fila for inicio in (2, 8, 14, 20, 26, 33, 39, 45, 51, 57) for fila in range(inicio, inicio + 5)]

COLOR = {
    "rojo": "#D62828", "negro": "#262626", "naranja": "#F28C00", "amarillo": "#E8C200",
    "verde": "#2B9348", "azul": "#1F6FD1", "morado": "#7B2CBF", "blanco": "#F4F4F4",
    "cafe": "#7A4A23",
}
NOMBRE_COLOR = {"rojo": "Rojo", "negro": "Negro", "naranja": "Naranja", "amarillo": "Amarillo",
                "verde": "Verde", "azul": "Azul", "morado": "Morado", "blanco": "Blanco"}

BLOQUES = {
    "alimentacion": "Alimentación: eliminador de 5 V, rieles y tierra común",
    "temperatura": "Variable 1: temperatura (DHT22)",
    "humedad": "Variable 2: humedad del suelo (sensor capacitivo)",
    "ventilador": "Actuador 1: ventilador",
    "servo": "Actuador 2: servo de la ventana",
    "bomba": "Actuador 3: bomba de riego",
}

# pines de la ESP32-S3-DevKitC-1 en el orden en que quedan sobre la protoboard (filas 42 a 63).
# J1 es la fila de pines que empieza con 3V3; J3 la que empieza con GND, TX, RX
PINES_J1 = ["3V3", "3V3", "RST", "4", "5", "6", "7", "15", "16", "17", "18", "8", "3", "46",
            "9", "10", "11", "12", "13", "14", "5Vin", "GND"]
PINES_J3 = ["GND", "TX", "RX", "1", "2", "42", "41", "40", "39", "38", "37", "36", "35", "0",
            "45", "48", "47", "21", "20", "19", "GND", "GND"]
FILA_PRIMER_PIN = 42
USO_PIN = {"3V3": "naranja", "4": "amarillo", "5": "verde", "6": "azul", "7": "morado", "15": "blanco",
           "GND": "negro"}


def x_fila(fila):
    return X0 + (fila - 1) * P


def punto(ref):
    """Coordenadas de un hoyo ("j47") o de un hoyo de riel ("-9", "+11")."""
    if ref[0] in "+-":
        return x_fila(float(ref[1:])), BY + Y_RIEL[ref[0]]
    return x_fila(int(ref[1:])), BY + Y_COLUMNA[ref[0]]


def nombre_hoyo(ref):
    """Texto para la tabla: dice el hoyo y, si es un pin de la ESP32, cual pin es."""
    if ref[0] == "-":
        return f"riel azul (−), fila {ref[1:]}"
    if ref[0] == "+":
        return f"riel rojo (+), fila {ref[1:]}"
    fila = int(ref[1:])
    if ref[0] == "j" and fila >= FILA_PRIMER_PIN:
        pin = PINES_J1[fila - FILA_PRIMER_PIN]
        nombre = "GPIO " + pin if pin.isdigit() else pin
        return f"hoyo {ref} ({nombre} de la ESP32)"
    return f"hoyo {ref}"


# ---------------------------------------------------------------- piezas sobre la protoboard
# (clave, bloque, texto para la tabla de piezas)
PIEZAS = [
    ("ESP32", None, "ESP32-S3", "Pines de 3V3 a GND en i42 a i63; la otra fila en a42 a a63. El USB queda hacia la fila 63."),
    ("R1", "ventilador", "Resistencia 1 kΩ (café, negro, rojo)", "h3 y h7. Da igual hacia qué lado."),
    ("Q1", "ventilador", "Transistor TIP120", "f7 (B), f8 (C) y f9 (E). La cara con letras mira hacia los rieles de abajo."),
    ("D1", "ventilador", "Diodo 1N4007", "i8 y i12. La franja gris va en i12."),
    ("R2", "bomba", "Resistencia 1 kΩ (café, negro, rojo)", "h15 y h19. Da igual hacia qué lado."),
    ("Q2", "bomba", "Transistor TIP120", "f19 (B), f20 (C) y f21 (E). La cara con letras mira hacia los rieles de abajo."),
    ("D2", "bomba", "Diodo 1N4007", "i20 e i24. La franja gris va en i24."),
    ("C1", "alimentacion", "Capacitor 1000 µF", "Pata negativa (franja con signos −) en el riel azul, fila 29; la otra en el riel rojo, fila 29. Se dobla para que quede acostado fuera de la protoboard."),
]

# ---------------------------------------------------------------- cables
# Cada cable: numero, color, desde, hasta, bloque, tipo de jumper, carril y nota.
# "desde"/"hasta" son hoyos ("j47", "-9", "+11") o pines de una pieza de fuera ("dht:+").
# carril: altura (desde el borde de abajo de la protoboard) del tramo horizontal; None = cable recto o corto.
CABLES = [
    (1, "rojo", "adaptador:+", "+2", "alimentacion", "macho-macho, un extremo atornillado en el adaptador", None, ""),
    (2, "negro", "adaptador:-", "-4", "alimentacion", "macho-macho, un extremo atornillado en el adaptador", None, ""),
    (3, "negro", "-30", "-33", "alimentacion", "macho-macho corto", None, "puente entre las dos mitades del riel azul"),
    (4, "negro", "j63", "-61", "alimentacion", "macho-macho corto", None, "tierra de la ESP32 con la del eliminador"),
    (5, "azul", "j47", "j3", "ventilador", "macho-macho 20 cm", 68, "señal del ventilador"),
    (6, "negro", "j9", "-9", "ventilador", "macho-macho corto", None, "emisor del transistor a tierra"),
    (7, "rojo", "j12", "+11", "ventilador", "macho-macho corto", None, "5 V al ventilador"),
    (8, "negro", "clema_v:-", "j8", "ventilador", "macho-macho, un extremo atornillado en la regleta", None, "cable negro del ventilador"),
    (9, "rojo", "clema_v:+", "h12", "ventilador", "macho-macho, un extremo atornillado en la regleta", None, "cable rojo del ventilador"),
    (10, "morado", "j48", "j15", "bomba", "macho-macho 20 cm", 54, "señal de la bomba"),
    (11, "negro", "j21", "-21", "bomba", "macho-macho corto", None, "emisor del transistor a tierra"),
    (12, "rojo", "j24", "+23", "bomba", "macho-macho corto", None, "5 V a la bomba"),
    (13, "negro", "clema_b:-", "j20", "bomba", "macho-macho, un extremo atornillado en la regleta", None, "cable negro de la bomba"),
    (14, "rojo", "clema_b:+", "h24", "bomba", "macho-macho, un extremo atornillado en la regleta", None, "cable rojo de la bomba"),
    (15, "negro", "servo:cafe", "-26", "servo", "macho-macho, entra en el conector del servo", None, "cable café del servo"),
    (16, "rojo", "servo:rojo", "+27", "servo", "macho-macho, entra en el conector del servo", None, "cable rojo del servo"),
    (17, "blanco", "servo:naranja", "j49", "servo", "macho-macho, entra en el conector del servo", 40, "cable naranja del servo (señal)"),
    (18, "naranja", "dht:+", "j42", "temperatura", "hembra-macho 30 cm", None, ""),
    (19, "amarillo", "dht:out", "j45", "temperatura", "hembra-macho 30 cm", 90, ""),
    (20, "negro", "dht:-", "-40", "temperatura", "hembra-macho 30 cm", None, ""),
    (21, "naranja", "suelo:VCC", "j43", "humedad", "hembra-macho 30 cm (o el cable del sensor)", 118, ""),
    (22, "verde", "suelo:AOUT", "j46", "humedad", "hembra-macho 30 cm (o el cable del sensor)", 104, ""),
    (23, "negro", "suelo:GND", "-53", "humedad", "hembra-macho 30 cm (o el cable del sensor)", None, ""),
]
# los numeros finales siguen el orden de armado: primero por bloque (en el orden de BLOQUES)
# y dentro de cada bloque en el orden de la lista de arriba
CABLES = [(indice + 1,) + cable[1:] for indice, cable in
          enumerate(sorted(CABLES, key=lambda cable: (list(BLOQUES).index(cable[4]), cable[0])))]

NOMBRE_PIN_PIEZA = {
    "adaptador:+": "terminal + del adaptador del eliminador",
    "adaptador:-": "terminal − del adaptador del eliminador",
    "clema_v:-": "regleta del ventilador, junto al cable negro",
    "clema_v:+": "regleta del ventilador, junto al cable rojo",
    "clema_b:-": "regleta de la bomba, junto al cable negro",
    "clema_b:+": "regleta de la bomba, junto al cable rojo",
    "servo:cafe": "conector del servo, cable café",
    "servo:rojo": "conector del servo, cable rojo",
    "servo:naranja": "conector del servo, cable naranja",
    "dht:+": "DHT22, pin +",
    "dht:out": "DHT22, pin out",
    "dht:-": "DHT22, pin −",
    "suelo:VCC": "sensor de suelo, pin VCC",
    "suelo:AOUT": "sensor de suelo, pin AOUT",
    "suelo:GND": "sensor de suelo, pin GND",
}

# pines de las piezas de fuera: se colocan justo abajo del hoyo al que van (x a media fila)
# o abajo de su carril. La y es la del borde de arriba de cada pieza.
Y_PIEZAS = ABAJO + 150
PIN_PIEZA = {
    "adaptador:+": (x_fila(2.5), Y_PIEZAS), "adaptador:-": (x_fila(4.5), Y_PIEZAS),
    "clema_v:-": (x_fila(8.5), Y_PIEZAS), "clema_v:+": (x_fila(12.5), Y_PIEZAS),
    "clema_b:-": (x_fila(20.5), Y_PIEZAS), "clema_b:+": (x_fila(24.5), Y_PIEZAS),
    "servo:cafe": (x_fila(26.5), Y_PIEZAS), "servo:rojo": (x_fila(27.5), Y_PIEZAS),
    "servo:naranja": (x_fila(28.5), Y_PIEZAS),
    "dht:-": (x_fila(40.5), Y_PIEZAS), "dht:out": (x_fila(41.5), Y_PIEZAS), "dht:+": (x_fila(42.5), Y_PIEZAS),
    "suelo:AOUT": (x_fila(51.5), Y_PIEZAS), "suelo:VCC": (x_fila(52.5), Y_PIEZAS),
    "suelo:GND": (x_fila(53.5), Y_PIEZAS),
}


# ---------------------------------------------------------------- utilidades de dibujo
def trazo_redondeado(puntos, radio=7):
    """Camino SVG que pasa por los puntos, con las esquinas redondeadas."""
    texto = f"M{puntos[0][0]:.1f},{puntos[0][1]:.1f}"
    for i in range(1, len(puntos) - 1):
        (xa, ya), (xb, yb), (xc, yc) = puntos[i - 1], puntos[i], puntos[i + 1]
        largo_entrada = abs(xb - xa) + abs(yb - ya)
        largo_salida = abs(xc - xb) + abs(yc - yb)
        r = min(radio, largo_entrada / 2, largo_salida / 2)
        if largo_entrada == 0 or largo_salida == 0:
            continue
        x1 = xb - (xb - xa) / largo_entrada * r
        y1 = yb - (yb - ya) / largo_entrada * r
        x2 = xb + (xc - xb) / largo_salida * r
        y2 = yb + (yc - yb) / largo_salida * r
        texto += f" L{x1:.1f},{y1:.1f} Q{xb:.1f},{yb:.1f} {x2:.1f},{y2:.1f}"
    texto += f" L{puntos[-1][0]:.1f},{puntos[-1][1]:.1f}"
    return texto


def texto(x, y, contenido, tam=12, color="#1d2433", ancla="start", peso="normal", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" fill="{color}" text-anchor="{ancla}" '
            f'font-weight="{peso}" {extra}>{contenido}</text>')


def puntos_del_cable(desde, hasta, carril):
    """Lista de puntos por los que pasa un cable."""
    desde_es_pieza = ":" in desde
    if desde_es_pieza:
        xp, yp = PIN_PIEZA[desde]
        hx, hy = punto(hasta)
        # el tramo vertical va a media fila, entre dos hoyos, y entra al hoyo con un tramo corto
        xv = hx + P / 2
        if carril is None:
            return [(xp, yp), (xv, hy), (hx, hy)] if abs(xp - xv) < 0.5 else None
        yc = ABAJO + carril
        return [(xp, yp), (xp, yc), (xv, yc), (xv, hy), (hx, hy)]
    x1, y1 = punto(desde)
    x2, y2 = punto(hasta)
    if carril is None:
        return [(x1, y1), (x2, y2)]
    yc = ABAJO + carril
    return [(x1, y1), (x1 + P / 2, y1), (x1 + P / 2, yc), (x2 + P / 2, yc), (x2 + P / 2, y2), (x2, y2)]


def dibujar_cable(numero, color, puntos, es_puente=False):
    contorno = "#1a1a1a" if color != "negro" else "#000000"
    if es_puente:
        (x1, y1), (x2, y2) = puntos
        camino = f"M{x1:.1f},{y1:.1f} Q{(x1 + x2) / 2:.1f},{y1 - 34:.1f} {x2:.1f},{y2:.1f}"
    else:
        camino = trazo_redondeado(puntos)
    partes = [
        f'<path d="{camino}" fill="none" stroke="{contorno}" stroke-width="7.5" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<path d="{camino}" fill="none" stroke="{COLOR[color]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
    ]
    # puntas: un cuadrito oscuro en cada hoyo donde entra el cable
    for (x, y) in (puntos[0], puntos[-1]):
        partes.append(f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" rx="1.5" fill="{COLOR[color]}" '
                      f'stroke="#000" stroke-width="1.6"/>')
    # numero del cable en el tramo mas largo
    mejor, largo_mayor = None, -1
    for (xa, ya), (xb, yb) in zip(puntos, puntos[1:]):
        largo = abs(xb - xa) + abs(yb - ya)
        if largo > largo_mayor:
            largo_mayor, mejor = largo, ((xa + xb) / 2, (ya + yb) / 2)
    if es_puente:
        mejor = ((puntos[0][0] + puntos[1][0]) / 2, puntos[0][1] - 17)
    bx, by = mejor
    partes.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="9.5" fill="#ffffff" stroke="#1d2433" stroke-width="1.6"/>')
    partes.append(texto(bx, by + 4, str(numero), tam=11, ancla="middle", peso="bold"))
    return "\n".join(partes)


# ---------------------------------------------------------------- protoboard y placa
def dibujar_protoboard():
    partes = [f'<rect x="{BX}" y="{BY}" width="{x_fila(63) - BX + 46}" height="{ALTO_PROTO}" rx="10" '
              f'fill="#F3EBD6" stroke="#CDBF9E" stroke-width="2"/>']
    fin = x_fila(63) + 46
    # canal central
    partes.append(f'<rect x="{BX + 8}" y="{BY + 214}" width="{fin - BX - 16}" height="28" fill="#E3D8BC"/>')
    # lineas de color de los rieles, con un corte a la mitad (algunas protoboards lo traen)
    for nombre, (y_linea, color) in {"arriba+": (10, "#D62828"), "arriba-": (66, "#1F5FBF"),
                                     "-": (390, "#1F5FBF"), "+": (446, "#D62828")}.items():
        for xa, xb in ((x_fila(1), x_fila(31)), (x_fila(32), x_fila(62))):
            partes.append(f'<line x1="{xa}" y1="{BY + y_linea}" x2="{xb}" y2="{BY + y_linea}" stroke="{color}" stroke-width="2.4"/>')
    for nombre, y in Y_RIEL.items():
        signo = "+" if nombre.endswith("+") else "−"
        color = "#D62828" if signo == "+" else "#1F5FBF"
        partes.append(texto(BX + 16, BY + y + 5, signo, tam=15, color=color, ancla="middle", peso="bold"))
        partes.append(texto(fin - 16, BY + y + 5, signo, tam=15, color=color, ancla="middle", peso="bold"))
        for fila in FILAS_RIEL:
            x = x_fila(fila)
            partes.append(f'<rect x="{x - 3.5}" y="{BY + y - 3.5}" width="7" height="7" rx="1.2" fill="#3a3a3a"/>')
    # hoyos de las 63 filas
    for columna, y in Y_COLUMNA.items():
        partes.append(texto(BX + 22, BY + y + 4, columna, tam=11, color="#7a6f58", ancla="middle"))
        partes.append(texto(fin - 22, BY + y + 4, columna, tam=11, color="#7a6f58", ancla="middle"))
        for fila in range(1, 64):
            x = x_fila(fila)
            partes.append(f'<rect x="{x - 3.5}" y="{BY + y - 3.5}" width="7" height="7" rx="1.2" fill="#3a3a3a"/>')
    # numeros de fila, arriba y abajo
    for fila in [1] + list(range(5, 61, 5)) + [63]:
        x = x_fila(fila)
        partes.append(texto(x, BY + 79, str(fila), tam=10.5, color="#7a6f58", ancla="middle"))
        partes.append(texto(x, BY + 383, str(fila), tam=10.5, color="#7a6f58", ancla="middle"))
    partes.append(texto(x_fila(16), BY - 8, "Rieles de arriba: no se usan", tam=11, color="#7a6f58"))
    partes.append(texto(x_fila(31.5), BY - 8, "↓ aquí algunas protoboards traen cortados los rieles", tam=10.5, color="#7a6f58", ancla="middle"))
    return "\n".join(partes)


def dibujar_esp32():
    x_ini, x_fin = x_fila(38.8), x_fila(65.6)
    y_ini, y_fin = BY + Y_COLUMNA["a"] - 15, BY + Y_COLUMNA["i"] + 15
    partes = [f'<rect x="{x_ini}" y="{y_ini}" width="{x_fin - x_ini}" height="{y_fin - y_ini}" rx="8" '
              f'fill="#17191d" stroke="#000" stroke-width="2" opacity="0.97"/>']
    # modulo con la antena a la izquierda
    mx1, mx2 = x_fila(38.2), x_fila(48.6)
    partes.append(f'<rect x="{mx1}" y="{BY + 128}" width="{mx2 - mx1}" height="176" rx="4" fill="#b9bec6" stroke="#8a9099"/>')
    partes.append(f'<rect x="{mx1}" y="{BY + 128}" width="{x_fila(41) - mx1}" height="176" rx="4" fill="#24272c"/>')
    zigzag = " ".join(f"{x_fila(38.6) + (k % 2) * 34:.1f},{BY + 140 + k * 15}" for k in range(11))
    partes.append(f'<polyline points="{zigzag}" fill="none" stroke="#d4a72c" stroke-width="3"/>')
    partes.append(texto((x_fila(41.2) + mx2) / 2, BY + 206, "ESP32-S3-WROOM-1", tam=12.5, color="#2b2f36", ancla="middle", peso="bold"))
    partes.append(texto((x_fila(41.2) + mx2) / 2, BY + 224, "N16R8", tam=12, color="#2b2f36", ancla="middle"))
    # botones, LED de colores y conectores USB
    for etiqueta, fila in (("BOOT", 53.5), ("RST", 56.5)):
        partes.append(f'<rect x="{x_fila(fila) - 13}" y="{BY + 150}" width="26" height="26" rx="3" fill="#d9d9d9"/>')
        partes.append(f'<circle cx="{x_fila(fila)}" cy="{BY + 163}" r="7" fill="#333"/>')
        partes.append(texto(x_fila(fila), BY + 192, etiqueta, tam=10, color="#e8e8e8", ancla="middle"))
    partes.append(f'<rect x="{x_fila(52) - 11}" y="{BY + 236}" width="22" height="22" fill="#f4f4f4"/>')
    partes.append(texto(x_fila(52), BY + 272, "LED", tam=9.5, color="#e8e8e8", ancla="middle"))
    for etiqueta, y in (("COM", BY + 146), ("USB", BY + 244)):
        partes.append(f'<rect x="{x_fila(63.3)}" y="{y}" width="{x_fila(66.4) - x_fila(63.3)}" height="44" rx="10" '
                      f'fill="#c9cdd2" stroke="#8a9099" stroke-width="2"/>')
        partes.append(texto(x_fila(62.2), y + 27, etiqueta, tam=10.5, color="#e8e8e8", ancla="middle", peso="bold"))
    partes.append(texto(x_fila(66.8), BY + 262, "← cable USB-C aquí", tam=12, color="#1d2433", peso="bold"))
    partes.append(texto(x_fila(66.8), BY + 278, "(conector USB)", tam=11, color="#56697d"))
    partes.append(texto(x_fila(66.8), BY + 172, "← COM: no se usa", tam=11, color="#56697d"))
    # nombres de los pines junto a cada fila de pines
    for indice in range(22):
        fila = FILA_PRIMER_PIN + indice
        x = x_fila(fila)
        for nombre, y_pin, y_texto in ((PINES_J3[indice], BY + Y_COLUMNA["a"], BY + Y_COLUMNA["a"] + 21),
                                       (PINES_J1[indice], BY + Y_COLUMNA["i"], BY + Y_COLUMNA["i"] - 13)):
            usado = (y_pin == BY + Y_COLUMNA["i"]) and nombre in USO_PIN and not (nombre == "GND" and fila != 63)
            partes.append(f'<circle cx="{x}" cy="{y_pin}" r="6" fill="#d4a72c" stroke="#7a5c10" stroke-width="1"/>')
            partes.append(f'<circle cx="{x}" cy="{y_pin}" r="2.4" fill="#17191d"/>')
            if usado:
                partes.append(f'<rect x="{x - 12}" y="{y_texto - 11}" width="24" height="15" rx="3" fill="{COLOR[USO_PIN[nombre]]}" '
                              f'stroke="#fff" stroke-width="0.8"/>')
                color_letra = "#000" if USO_PIN[nombre] in ("blanco", "amarillo", "naranja") else "#fff"
                partes.append(texto(x, y_texto, nombre, tam=9.5, color=color_letra, ancla="middle", peso="bold"))
            else:
                partes.append(texto(x, y_texto, nombre, tam=9, color="#e8e8e8", ancla="middle"))
    partes.append(texto(x_fila(52), BY + 128, "ESP32-S3-DevKitC-1", tam=11, color="#9aa3ad", ancla="middle"))
    return "\n".join(partes)


def dibujar_resistencia(fila1, fila2, columna, etiqueta):
    x1, y = punto(f"{columna}{fila1}")
    x2, _ = punto(f"{columna}{fila2}")
    xm = (x1 + x2) / 2
    partes = [f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#9a9a9a" stroke-width="2.5"/>',
              f'<rect x="{xm - 28}" y="{y - 8}" width="56" height="16" rx="7" fill="#d9b77e" stroke="#9b7a45"/>']
    for desfase, color in ((-18, "#7A4A23"), (-8, "#111"), (2, "#D62828"), (16, "#C9A227")):
        partes.append(f'<rect x="{xm + desfase}" y="{y - 8}" width="5" height="16" fill="{color}"/>')
    for x in (x1, x2):
        partes.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="#777"/>')
    partes.append(f'<rect x="{xm - 22}" y="{y - 27}" width="44" height="15" rx="3" fill="#ffffffdd"/>')
    partes.append(texto(xm, y - 15, etiqueta, tam=11, ancla="middle", peso="bold"))
    return "\n".join(partes)


def dibujar_diodo(fila_anodo, fila_catodo, columna):
    x1, y = punto(f"{columna}{fila_anodo}")
    x2, _ = punto(f"{columna}{fila_catodo}")
    xm = (x1 + x2) / 2
    partes = [f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#9a9a9a" stroke-width="2.5"/>',
              f'<rect x="{xm - 24}" y="{y - 7}" width="48" height="14" rx="5" fill="#1b1b1b"/>',
              f'<rect x="{xm + 13}" y="{y - 7}" width="6" height="14" fill="#cfcfcf"/>']
    for x in (x1, x2):
        partes.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="#777"/>')
    partes.append(f'<rect x="{xm - 28}" y="{y + 9}" width="56" height="15" rx="3" fill="#ffffffdd"/>')
    partes.append(texto(xm, y + 21, "1N4007", tam=10.5, ancla="middle", peso="bold"))
    return "\n".join(partes)


def dibujar_tip120(fila_base):
    # visto desde arriba: la cara con letras mira hacia abajo (hacia los rieles) y la aleta de metal
    # queda sobre el canal central. Con esa orientacion las patas quedan B, C, E de izquierda a derecha.
    xb, y = punto(f"f{fila_base}")
    xm = xb + P
    partes = [f'<rect x="{xm - 47}" y="{y - 40}" width="94" height="12" rx="2" fill="#b8bec6" stroke="#80868f"/>',
              f'<circle cx="{xm}" cy="{y - 34}" r="3.5" fill="#80868f"/>',
              f'<rect x="{xm - 47}" y="{y - 28}" width="94" height="36" rx="3" fill="#202225" stroke="#000"/>',
              texto(xm, y - 13, "TIP120", tam=11, color="#f0f0f0", ancla="middle", peso="bold")]
    for desfase, letra in ((-P, "B"), (0, "C"), (P, "E")):
        partes.append(f'<circle cx="{xm + desfase}" cy="{y}" r="3.6" fill="#c9c9c9" stroke="#555"/>')
        partes.append(texto(xm + desfase, y + 21, letra, tam=11, color="#1d2433", ancla="middle", peso="bold",
                            extra='paint-order="stroke" stroke="#F3EBD6" stroke-width="4"'))
    return "\n".join(partes)


def dibujar_capacitor():
    # acostado fuera de la protoboard; las patas van a los dos rieles de abajo en la fila 29
    xm = x_fila(30.2)
    y = ABAJO + 22
    xmenos, xmas = x_fila(29.5), x_fila(29)
    partes = [
        # pata negativa: va por en medio de dos hoyos y entra al riel azul
        f'<path d="M{xmenos},{y - 8} L{xmenos},{BY + Y_RIEL["-"]} L{x_fila(29)},{BY + Y_RIEL["-"]}" fill="none" stroke="#9a9a9a" stroke-width="2.5"/>',
        f'<path d="M{xmas},{y - 8} L{xmas},{BY + Y_RIEL["+"]}" fill="none" stroke="#9a9a9a" stroke-width="2.5"/>',
        f'<rect x="{xm - 34}" y="{y - 11}" width="68" height="24" rx="6" fill="#1f3a6b" stroke="#0f1f3a"/>',
        f'<rect x="{xm - 34}" y="{y - 11}" width="18" height="24" rx="4" fill="#9fb3d6"/>',
        texto(xm - 25, y + 6, "−", tam=14, color="#1f3a6b", ancla="middle", peso="bold"),
        texto(xm + 44, y + 5, "1000 µF", tam=11, peso="bold"),
    ]
    for x, yy in ((x_fila(29), BY + Y_RIEL["-"]), (xmas, BY + Y_RIEL["+"])):
        partes.append(f'<circle cx="{x}" cy="{yy}" r="3.2" fill="#777"/>')
    return "\n".join(partes)


# ---------------------------------------------------------------- piezas de fuera de la protoboard
def etiqueta_pin(x, y, nombre):
    return texto(x, y, nombre, tam=10.5, ancla="middle", peso="bold", extra='paint-order="stroke" stroke="#fff" stroke-width="3"')


def dibujar_alimentacion():
    xa, xb = PIN_PIEZA["adaptador:+"][0], PIN_PIEZA["adaptador:-"][0]
    y = Y_PIEZAS
    partes = [
        # adaptador con bornera: dos tornillos marcados + y -
        f'<rect x="{xa - 24}" y="{y}" width="{xb - xa + 48}" height="40" rx="4" fill="#2f8f3a" stroke="#1d5e25"/>',
        f'<circle cx="{xa}" cy="{y + 14}" r="8" fill="#d9d9d9" stroke="#777"/>',
        f'<circle cx="{xb}" cy="{y + 14}" r="8" fill="#d9d9d9" stroke="#777"/>',
        f'<line x1="{xa - 5}" y1="{y + 14}" x2="{xa + 5}" y2="{y + 14}" stroke="#555" stroke-width="2"/>',
        f'<line x1="{xb - 5}" y1="{y + 14}" x2="{xb + 5}" y2="{y + 14}" stroke="#555" stroke-width="2"/>',
        texto(xa, y + 35, "+", tam=13, color="#fff", ancla="middle", peso="bold"),
        texto(xb, y + 35, "−", tam=13, color="#fff", ancla="middle", peso="bold"),
        f'<rect x="{(xa + xb) / 2 - 18}" y="{y + 40}" width="36" height="34" rx="6" fill="#1b1b1b"/>',
        texto((xa + xb) / 2 - 2, y + 102, "Adaptador jack", tam=11, peso="bold"),
        texto((xa + xb) / 2 - 2, y + 116, "con bornera", tam=11),
        # cable y eliminador
        f'<path d="M{(xa + xb) / 2},{y + 74} C{(xa + xb) / 2},{y + 150} {xa - 40},{y + 140} {xa - 40},{y + 200}" '
        f'fill="none" stroke="#1b1b1b" stroke-width="5"/>',
        f'<rect x="{xa - 85}" y="{y + 200}" width="90" height="70" rx="8" fill="#e9e9e9" stroke="#8d8d8d" stroke-width="2"/>',
        texto(xa - 40, y + 230, "Eliminador", tam=11.5, ancla="middle", peso="bold"),
        texto(xa - 40, y + 247, "5 V  2 A", tam=11.5, ancla="middle"),
        texto(xa - 40, y + 262, "(al final)", tam=10, color="#56697d", ancla="middle"),
    ]
    return "\n".join(partes)


def dibujar_clema(clave, nombre_motor):
    xm_, xp_ = PIN_PIEZA[f"{clave}:-"][0], PIN_PIEZA[f"{clave}:+"][0]
    y = Y_PIEZAS
    partes = [f'<rect x="{xm_ - 20}" y="{y}" width="{xp_ - xm_ + 40}" height="34" rx="3" fill="#f7f7f2" stroke="#9a9a8f" stroke-width="1.5"/>']
    for x in (xm_, xp_):
        partes.append(f'<circle cx="{x}" cy="{y + 17}" r="7" fill="#d0d0d0" stroke="#777"/>')
        partes.append(f'<line x1="{x - 4}" y1="{y + 17}" x2="{x + 4}" y2="{y + 17}" stroke="#555" stroke-width="2"/>')
    partes.append(texto((xm_ + xp_) / 2, y + 22, "regleta", tam=10, color="#56697d", ancla="middle"))
    # cables propios del motor, del otro lado de la regleta
    for x, color in ((xm_, COLOR["negro"]), (xp_, COLOR["rojo"])):
        partes.append(f'<path d="M{x},{y + 34} L{x},{y + 62} Q{x},{y + 72} {(xm_ + xp_) / 2 + (x - (xm_ + xp_) / 2) * 0.25},{y + 86}" '
                      f'fill="none" stroke="{color}" stroke-width="3"/>')
    partes.append(etiqueta_pin(xm_ - 20, y + 54, "−"))
    partes.append(etiqueta_pin(xp_ + 20, y + 54, "+"))
    return "\n".join(partes)


def dibujar_ventilador():
    xc = (PIN_PIEZA["clema_v:-"][0] + PIN_PIEZA["clema_v:+"][0]) / 2
    y = Y_PIEZAS + 86
    aspas = "".join(f'<ellipse cx="{xc}" cy="{y + 56 - 22}" rx="9" ry="22" fill="#5d6670" '
                    f'transform="rotate({angulo} {xc} {y + 56})"/>' for angulo in (0, 72, 144, 216, 288))
    partes = [dibujar_clema("clema_v", "ventilador"),
              f'<rect x="{xc - 56}" y="{y}" width="112" height="112" rx="10" fill="#2a2d31" stroke="#000"/>',
              f'<circle cx="{xc}" cy="{y + 56}" r="48" fill="#3a3f45"/>', aspas,
              f'<circle cx="{xc}" cy="{y + 56}" r="13" fill="#2a2d31"/>']
    for dx, dy in ((-44, 12), (44, 12), (-44, 100), (44, 100)):
        partes.append(f'<circle cx="{xc + dx}" cy="{y + dy}" r="4" fill="#111"/>')
    partes.append(texto(xc, y + 132, "Ventilador 5 V", tam=12, ancla="middle", peso="bold"))
    partes.append(texto(xc, y + 147, "40 × 40 mm", tam=11, ancla="middle"))
    return "\n".join(partes)


def dibujar_bomba():
    xc = (PIN_PIEZA["clema_b:-"][0] + PIN_PIEZA["clema_b:+"][0]) / 2
    y = Y_PIEZAS + 86
    partes = [dibujar_clema("clema_b", "bomba"),
              # deposito de agua con la bomba sumergida
              f'<path d="M{xc - 70},{y + 6} L{xc - 62},{y + 150} L{xc + 62},{y + 150} L{xc + 70},{y + 6}" fill="#eaf4fb" stroke="#8fb3cc" stroke-width="2"/>',
              f'<path d="M{xc - 67},{y + 46} L{xc - 62},{y + 150} L{xc + 62},{y + 150} L{xc + 67},{y + 46} Z" fill="#9cc9ea" opacity="0.8"/>',
              f'<rect x="{xc - 26}" y="{y + 82}" width="52" height="56" rx="10" fill="#f2f2f2" stroke="#666"/>',
              f'<rect x="{xc - 26}" y="{y + 82}" width="52" height="14" rx="6" fill="#1b1b1b"/>',
              # manguera hacia la maceta
              f'<path d="M{xc - 10},{y + 82} L{xc - 10},{y + 30} Q{xc - 10},{y + 18} {xc - 40},{y + 18} L{xc - 110},{y + 18}" '
              f'fill="none" stroke="#bcd9ee" stroke-width="9" stroke-linecap="round"/>',
              texto(xc - 112, y + 40, "manguera", tam=10.5, color="#56697d"),
              texto(xc - 112, y + 54, "a la maceta", tam=10.5, color="#56697d"),
              texto(xc, y + 170, "Mini bomba sumergible", tam=12, ancla="middle", peso="bold"),
              texto(xc, y + 185, "en el depósito de agua", tam=11, ancla="middle")]
    return "\n".join(partes)


def dibujar_servo():
    xs = [PIN_PIEZA[f"servo:{c}"][0] for c in ("cafe", "rojo", "naranja")]
    y = Y_PIEZAS
    xc = x_fila(31.5)      # el cuerpo va a la derecha del conector, lejos del deposito de agua
    yc = y + 120
    partes = [f'<rect x="{xs[0] - 13}" y="{y}" width="{xs[2] - xs[0] + 26}" height="20" rx="2" fill="#151515"/>']
    for indice, (x, color) in enumerate(zip(xs, ("cafe", "rojo", "naranja"))):
        partes.append(f'<rect x="{x - 3}" y="{y + 6}" width="6" height="8" fill="#555"/>')
        tono = {"cafe": COLOR["cafe"], "rojo": COLOR["rojo"], "naranja": "#F28C00"}[color]
        y_vuelta = y + 40 + indice * 7
        partes.append(f'<path d="M{x},{y + 20} L{x},{y_vuelta} Q{x},{y_vuelta + 10} {x + 10},{y_vuelta + 10} '
                      f'L{xc - 52 - indice * 0},{y_vuelta + 10} Q{xc - 40},{y_vuelta + 10} {xc - 40},{y_vuelta + 22} L{xc - 40},{yc}" '
                      f'fill="none" stroke="{tono}" stroke-width="3.2"/>')
    partes.append(etiqueta_pin(xs[0] - 22, y + 36, "café"))
    partes.append(etiqueta_pin(xs[2] + 36, y + 36, "naranja"))
    partes.append(etiqueta_pin(xs[1], y + 36, "rojo"))
    partes += [f'<rect x="{xc - 42}" y="{yc}" width="84" height="46" rx="4" fill="#2f6fd6" stroke="#1a3f7a"/>',
               f'<rect x="{xc - 58}" y="{yc + 12}" width="116" height="10" rx="2" fill="#2f6fd6" stroke="#1a3f7a"/>',
               f'<circle cx="{xc + 18}" cy="{yc + 23}" r="12" fill="#e9e9e9" stroke="#999"/>',
               f'<rect x="{xc + 14}" y="{yc - 14}" width="8" height="40" rx="4" fill="#f4f4f4" stroke="#999"/>',
               texto(xc - 14, yc + 39, "SG90", tam=11, color="#fff", ancla="middle", peso="bold"),
               texto(xc, yc + 66, "Servo de la ventana", tam=12, ancla="middle", peso="bold"),
               texto(xc, yc + 81, "(su conector se llena con 3 jumpers)", tam=10.5, color="#56697d", ancla="middle")]
    return "\n".join(partes)


def dibujar_dht22():
    xs = [PIN_PIEZA[f"dht:{c}"][0] for c in ("-", "out", "+")]
    y = Y_PIEZAS
    xc = xs[1]
    partes = [f'<rect x="{xc - 46}" y="{y + 8}" width="92" height="44" rx="4" fill="#1f5aa6" stroke="#123a6d"/>']
    for x, nombre in zip(xs, ("−", "out", "+")):
        partes.append(f'<rect x="{x - 4}" y="{y - 2}" width="8" height="14" fill="#c9a227"/>')
        partes.append(texto(x, y + 30, nombre, tam=10.5, color="#fff", ancla="middle", peso="bold"))
    partes.append(f'<rect x="{xc - 34}" y="{y + 52}" width="68" height="84" rx="5" fill="#f4f4f4" stroke="#aaa"/>')
    for fila in range(5):
        for col in range(3):
            partes.append(f'<rect x="{xc - 25 + col * 18}" y="{y + 62 + fila * 14}" width="14" height="8" rx="2" fill="#d4d4d4"/>')
    partes.append(texto(xc, y + 156, "DHT22 (módulo)", tam=12, ancla="middle", peso="bold"))
    partes.append(texto(xc, y + 171, "dentro del invernadero", tam=11, ancla="middle"))
    return "\n".join(partes)


def dibujar_sensor_suelo():
    xs = [PIN_PIEZA[f"suelo:{c}"][0] for c in ("AOUT", "VCC", "GND")]
    y = Y_PIEZAS
    xc = xs[1]
    partes = [f'<rect x="{xc - 40}" y="{y + 6}" width="80" height="20" rx="2" fill="#f2f2f2" stroke="#999"/>']
    for x, nombre in zip(xs, ("AOUT", "VCC", "GND")):
        partes.append(f'<rect x="{x - 4}" y="{y - 2}" width="8" height="12" fill="#c9a227"/>')
        partes.append(texto(x, y + 42, nombre, tam=9.5, color="#fff", ancla="middle", peso="bold"))
    partes.append(f'<path d="M{xc - 46},{y + 26} L{xc + 46},{y + 26} L{xc + 46},{y + 220} L{xc},{y + 262} L{xc - 46},{y + 220} Z" '
                  f'fill="#1d1d1d" stroke="#000"/>')
    partes.append(f'<line x1="{xc - 46}" y1="{y + 110}" x2="{xc + 46}" y2="{y + 110}" stroke="#f4f4f4" stroke-width="2" stroke-dasharray="6 4"/>')
    partes.append(texto(xc, y + 104, "hasta aquí", tam=10, color="#f4f4f4", ancla="middle"))
    partes.append(texto(xc, y + 128, "se entierra", tam=10, color="#f4f4f4", ancla="middle"))
    partes.append(texto(xc + 58, y + 150, "Sensor de humedad", tam=12, peso="bold"))
    partes.append(texto(xc + 58, y + 165, "de suelo capacitivo v1.2", tam=11))
    partes.append(texto(xc + 58, y + 180, "(en la tierra del tupper)", tam=11, color="#56697d"))
    return "\n".join(partes)


PIEZAS_FUERA = [
    ("alimentacion", dibujar_alimentacion),
    ("ventilador", dibujar_ventilador),
    ("bomba", dibujar_bomba),
    ("servo", dibujar_servo),
    ("temperatura", dibujar_dht22),
    ("humedad", dibujar_sensor_suelo),
]


# ---------------------------------------------------------------- leyenda y notas
NOTAS = [
    "La ESP32 se pone sobre la protoboard con el USB hacia la fila 63: la fila de pines que empieza con 3V3 entra en la columna i (filas 42 a 63)",
    "y la otra fila en la columna a. Del lado de la j queda un hoyo libre por pin, y ahí se conecta cada cable.",
    "Rieles de abajo: el de línea azul (−) es tierra y el de línea roja (+) son los 5 V del eliminador. Si en su protoboard van en otro orden, se respeta el color.",
    "TIP120: la cara con letras mira hacia los rieles de abajo y la aleta de metal hacia el canal central; así quedan B, C y E de izquierda a derecha.",
    "1N4007: la franja gris va del lado de los 5 V (i12 e i24).   Capacitor: la pata de la franja con signos − va al riel azul.",
    "Sensores: se conectan por el nombre impreso en cada módulo (+, out, −; AOUT, VCC, GND), no por la posición del pin.",
    "El cable 3 une las dos mitades del riel azul, por si la protoboard lo trae cortado a la mitad. Se pone siempre.",
    "El eliminador se enchufa al final, después de revisar todo. El riel rojo (5 V) nunca se une con el 3V3 de la placa.",
]
LEYENDA = [
    ("rojo", "5 V del eliminador"), ("negro", "Tierra (GND)"), ("naranja", "3.3 V de la ESP32"),
    ("amarillo", "GPIO 4: temperatura (DHT22)"), ("verde", "GPIO 5: humedad del suelo"),
    ("azul", "GPIO 6: ventilador"), ("morado", "GPIO 7: bomba"), ("blanco", "GPIO 15: servo de la ventana"),
]


def dibujar_leyenda_y_notas():
    y = Y_PIEZAS + 300
    partes = [f'<rect x="{BX}" y="{y}" width="{ANCHO - 2 * BX}" height="{ALTO - y - 24}" rx="8" fill="#ffffff" stroke="#d5dbe3"/>',
              texto(BX + 18, y + 26, "Colores de los cables", tam=13, peso="bold")]
    for indice, (color, descripcion) in enumerate(LEYENDA):
        columna, fila = indice // 4, indice % 4
        x = BX + 18 + columna * 260
        yy = y + 50 + fila * 22
        partes.append(f'<line x1="{x}" y1="{yy - 4}" x2="{x + 36}" y2="{yy - 4}" stroke="#111" stroke-width="7.5" stroke-linecap="round"/>')
        partes.append(f'<line x1="{x}" y1="{yy - 4}" x2="{x + 36}" y2="{yy - 4}" stroke="{COLOR[color]}" stroke-width="5" stroke-linecap="round"/>')
        partes.append(texto(x + 46, yy, descripcion, tam=11.5))
    partes.append(texto(BX + 18, y + 150, "Si no hay jumpers de ese color no pasa nada: lo que importa es el hoyo.", tam=11, color="#56697d"))
    partes.append(texto(BX + 18, y + 166, "Los círculos con número son los de la tabla de cables.", tam=11, color="#56697d"))
    x_notas = BX + 560
    partes.append(texto(x_notas, y + 26, "Antes de armar", tam=13, peso="bold"))
    for indice, nota in enumerate(NOTAS):
        partes.append(texto(x_notas, y + 48 + indice * 17, nota, tam=10.8))
    return "\n".join(partes)


# ---------------------------------------------------------------- armado del SVG
def armar_svg(resaltar=None):
    """Dibuja todo. Si resaltar es el nombre de un bloque, lo demas queda tenue."""
    def capa(bloque, contenido):
        if resaltar is None or bloque is None or bloque == resaltar:
            return contenido
        return f'<g opacity="0.16">{contenido}</g>'

    if resaltar:
        titulo = f"Invernadero IoT · {BLOQUES[resaltar]}"
        subtitulo = "Solo se resalta este bloque. Lo tenue se arma en los otros bloques."
    else:
        titulo = "Invernadero IoT · alambrado completo en la protoboard"
        subtitulo = ("Cada cable va de un hoyo a un pin. Las filas (1 a 63) y las letras (a a j) son las que vienen impresas "
                     "en la protoboard de 830 puntos. Los números en círculo son los de la tabla de cables.")
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{ALTO}" viewBox="0 0 {ANCHO} {ALTO}" '
              f'font-family="Segoe UI, Arial, sans-serif">',
              f'<rect width="{ANCHO}" height="{ALTO}" fill="#fbfbf8"/>',
              texto(BX, 44, titulo, tam=24, peso="bold"),
              texto(BX, 70, subtitulo, tam=12.5, color="#56697d"),
              texto(BX, 88, "Los multiplexores · Sistemas de Comunicaciones, FI UNAM", tam=11, color="#8a96a3"),
              dibujar_protoboard()]
    # piezas sobre la protoboard
    partes.append(capa("ventilador", dibujar_resistencia(3, 7, "h", "1 kΩ") + dibujar_tip120(7) + dibujar_diodo(8, 12, "i")))
    partes.append(capa("bomba", dibujar_resistencia(15, 19, "h", "1 kΩ") + dibujar_tip120(19) + dibujar_diodo(20, 24, "i")))
    partes.append(capa("alimentacion", dibujar_capacitor()))
    partes.append(dibujar_esp32())
    for bloque, funcion in PIEZAS_FUERA:
        partes.append(capa(bloque, funcion()))
    # cables: primero los largos, para que los cortos queden encima
    for numero, color, desde, hasta, bloque, tipo, carril, nota in sorted(CABLES, key=lambda c: c[6] is None):
        puntos = puntos_del_cable(desde, hasta, carril)
        if puntos is None:
            raise ValueError(f"el cable {numero} necesita carril: su pieza no esta abajo del hoyo")
        partes.append(capa(bloque, dibujar_cable(numero, color, puntos, es_puente=(desde == "-30"))))
    partes.append(dibujar_leyenda_y_notas())
    partes.append("</svg>")
    return "\n".join(partes)


def svg_a_png(svg, ruta_png):
    """Abre el SVG en Edge sin ventana y guarda una captura al doble de resolucion."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_html = Path(carpeta) / "dibujo.html"
        ruta_html.write_text(f'<!doctype html><html><body style="margin:0">{svg}</body></html>', encoding="utf-8")
        subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={ANCHO},{ALTO}", f"--screenshot={ruta_png}", ruta_html.as_uri()],
                       check=True, capture_output=True)


# ---------------------------------------------------------------- tablas
def descripcion(ref):
    return NOMBRE_PIN_PIEZA[ref] if ":" in ref else nombre_hoyo(ref)


def escribir_tablas():
    carpeta = CARPETA_DOCUMENTO / "tablas"
    carpeta.mkdir(exist_ok=True)
    orden_bloques = list(BLOQUES)
    lineas_md = ["| # | Color | Desde | Hasta | Jumper | Nota |", "|---|---|---|---|---|---|"]
    lineas_tex = []
    for bloque in orden_bloques:
        for numero, color, desde, hasta, b, tipo, carril, nota in CABLES:
            if b != bloque:
                continue
            lineas_md.append(f"| {numero} | {NOMBRE_COLOR[color]} | {descripcion(desde)} | {descripcion(hasta)} | {tipo} | {nota} |")
            texto_tex = lambda s: s.replace("µ", r"\textmu{}").replace("Ω", r"$\Omega$").replace("−", r"$-$")
            lineas_tex.append(f"{numero} & {NOMBRE_COLOR[color]} & {texto_tex(descripcion(desde))} & "
                              f"{texto_tex(descripcion(hasta))} \\\\")
    piezas_md = ["| Pieza | Dónde va |", "|---|---|"]
    piezas_tex = []
    for clave, bloque, nombre, donde in PIEZAS:
        piezas_md.append(f"| {nombre} | {donde} |")
        conv = lambda s: s.replace("µ", r"\textmu{}").replace("Ω", r"$\Omega$").replace("−", r"$-$")
        piezas_tex.append(f"{conv(nombre)} & {conv(donde)} \\\\")
    (carpeta / "cables.md").write_text(
        "<!-- generado por documento/graficas/alambrado.py; no editar a mano -->\n\n"
        "### Piezas sobre la protoboard\n\n" + "\n".join(piezas_md) +
        "\n\n### Cables (en el orden de armado, por bloque)\n\n" + "\n".join(lineas_md) + "\n", encoding="utf-8")
    (carpeta / "cables.tex").write_text(
        "% generado por documento/graficas/alambrado.py; no editar a mano\n" + "\n".join(lineas_tex) + "\n", encoding="utf-8")
    (carpeta / "piezas.tex").write_text(
        "% generado por documento/graficas/alambrado.py; no editar a mano\n" + "\n".join(piezas_tex) + "\n", encoding="utf-8")


def main():
    carpeta_img = CARPETA_DOCUMENTO / "img"
    carpeta_img.mkdir(exist_ok=True)
    svg = armar_svg()
    (carpeta_img / "alambrado_completo.svg").write_text(svg, encoding="utf-8")
    svg_a_png(svg, carpeta_img / "alambrado_completo.png")
    print(carpeta_img / "alambrado_completo.png")
    for bloque in BLOQUES:
        svg_a_png(armar_svg(resaltar=bloque), carpeta_img / f"alambrado_{bloque}.png")
        print(carpeta_img / f"alambrado_{bloque}.png")
    escribir_tablas()


if __name__ == "__main__":
    main()
