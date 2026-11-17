# Diagramas del documento, todos con schemdraw:
#   documento/img/esquema_electrico.png   esquema electrico por bloques (mismos pines que el firmware)
#   documento/img/diagrama_bloques.png    sensores, placa, actuadores y la red
#   documento/img/diagrama_flujo.png      ciclo principal del programa
#   documento/img/estados_riego.png       estados del riego
# Uso: python -I esquema.py

import tempfile
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
import schemdraw.flow as flow

CARPETA_IMG = Path(__file__).resolve().parent.parent / "img"
CARPETA_TEMPORAL = Path(tempfile.mkdtemp())
TINTA = "#16324F"


# ---------------------------------------------------------------- esquema electrico
def bloque_alimentacion(ruta):
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=12)
        d += (fuente := elm.SourceV().up().label("Eliminador\n5 V, 2 A", loc="left"))
        d += elm.Line().right(2.5)
        d += (nodo_5v := elm.Dot())
        d += elm.Line().right(2.5).label("Riel rojo: 5 V", loc="right", ofst=0.1)
        d += elm.Capacitor(polar=True).at(nodo_5v.center).down().label("1000 µF", loc="bottom")
        d += (nodo_tierra := elm.Dot())
        d += elm.Line().at(fuente.start).to(nodo_tierra.center)
        d += elm.Line().at(nodo_tierra.center).right(2.5).label("Riel azul: GND", loc="right", ofst=0.1)
        d += elm.Ground().at(nodo_tierra.center)
        d += elm.Line().at(nodo_tierra.center).down(1.6)
        d += elm.Dot(open=True).label("GND de la ESP32 (cable 4)", loc="bottom")
        d.save(str(ruta), dpi=200)


def bloque_sensor(ruta, nombre, pines, conexiones):
    """Modulo de tres pines con cada pin llevado a su destino."""
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=12)
        sensor = elm.Ic(pins=[elm.IcPin(p, side="left") for p in pines], edgepadW=1.6, pinspacing=1.6).label(nombre, loc="top")
        d += sensor
        for pin, destino in zip(pines, conexiones):
            d += elm.Line().at(getattr(sensor, pin)).left(2.2)
            if destino == "GND":
                d += elm.Ground()
            elif destino == "3.3 V":
                d += elm.Vdd().label("3.3 V")
            else:
                d += elm.Dot(open=True).label(destino, loc="left")
        d.save(str(ruta), dpi=200)


def bloque_actuador(ruta, pin, motor):
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=12)
        d += elm.Vdd().label("5 V")
        d += (nodo_arriba := elm.Dot())
        d += elm.Motor().down().label(motor, loc="top", ofst=0.2)
        d += (nodo_abajo := elm.Dot())
        # diodo de proteccion: anodo abajo, catodo (la franja) en los 5 V
        derecha_abajo = (nodo_abajo.center[0] + 2.6, nodo_abajo.center[1])
        derecha_arriba = (nodo_arriba.center[0] + 2.6, nodo_arriba.center[1])
        d += elm.Line().at(nodo_abajo.center).to(derecha_abajo)
        d += elm.Diode().at(derecha_abajo).to(derecha_arriba).label("1N4007", loc="bottom")
        d += elm.Line().at(derecha_arriba).to(nodo_arriba.center)
        d += elm.Line().at(nodo_abajo.center).down(0.6)
        d += (transistor := elm.BjtNpn(circle=True).anchor("collector"))
        d += elm.Label().at((transistor.collector[0] + 0.5, transistor.emitter[1] - 0.2)).label("TIP120\n(Darlington)", halign="left")
        d += elm.Ground().at(transistor.emitter)
        d += elm.Resistor().at(transistor.base).left().label("1 kΩ", loc="top")
        d += elm.Line().left(0.8)
        d += elm.Dot(open=True).label(pin, loc="left")
        d.save(str(ruta), dpi=200)


def bloque_servo(ruta):
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=12)
        servo = elm.Ic(pins=[elm.IcPin("GND (café)", side="left", anchorname="tierra"),
                             elm.IcPin("+5 V (rojo)", side="left", anchorname="cinco"),
                             elm.IcPin("señal (naranja)", side="left", anchorname="senal")],
                       edgepadW=2.6, pinspacing=1.6).label("Servo SG90", loc="top")
        d += servo
        d += elm.Line().at(servo.senal).left(2.2)
        d += elm.Dot(open=True).label("GPIO 15", loc="left")
        d += elm.Line().at(servo.cinco).left(2.2)
        d += elm.Vdd().label("5 V")
        d += elm.Line().at(servo.tierra).left(2.2)
        d += elm.Ground()
        d.save(str(ruta), dpi=200)


def esquema_electrico():
    bloques = [
        ("Alimentación de los actuadores", "alimentacion", bloque_alimentacion, ()),
        ("Temperatura: módulo DHT22", "dht", bloque_sensor, ("DHT22", ["GND", "out", "VCC"], ["GND", "GPIO 4", "3.3 V"])),
        ("Humedad del suelo: sensor capacitivo", "suelo", bloque_sensor,
         ("Sensor v1.2", ["GND", "AOUT", "VCC"], ["GND", "GPIO 5", "3.3 V"])),
        ("Actuador 1: ventilador", "ventilador", bloque_actuador, ("GPIO 6", "Ventilador")),
        ("Actuador 2: servo de la ventana", "servo", bloque_servo, ()),
        ("Actuador 3: bomba de riego", "bomba", bloque_actuador, ("GPIO 7", "Bomba")),
    ]
    figura, ejes = plt.subplots(2, 3, figsize=(15, 9.5))
    for eje, (titulo, clave, funcion, argumentos) in zip(ejes.flat, bloques):
        ruta = CARPETA_TEMPORAL / f"{clave}.png"
        funcion(ruta, *argumentos)
        eje.imshow(mpimg.imread(ruta))
        eje.set_title(titulo, fontsize=13)
        eje.axis("off")
    figura.suptitle("Esquema eléctrico por bloques (pines de la ESP32-S3)", fontsize=15)
    figura.text(0.5, 0.015, "Las tierras del eliminador y de la ESP32 se unen en el riel azul. Los sensores se alimentan "
                "con 3.3 V de la placa y los actuadores con los 5 V del eliminador.", ha="center", fontsize=11)
    figura.tight_layout(rect=(0, 0.03, 1, 0.97))
    figura.savefig(CARPETA_IMG / "esquema_electrico.png", dpi=200)
    plt.close(figura)


# ---------------------------------------------------------------- diagrama de bloques
def diagrama_bloques():
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=12, unit=1)
        caja = dict(w=3.6, h=1.4)

        def bloque(centro, texto, **medidas):
            return flow.Box(**(medidas or caja)).anchor("center").at(centro).label(texto)

        d += (dht := bloque((1.8, 5.2), "DHT22\ntemperatura y\nhumedad del aire"))
        d += (suelo := bloque((1.8, 2.4), "Sensor capacitivo\nhumedad del suelo"))
        d += (placa := bloque((8.6, 3.8), "ESP32-S3\n\nlee cada 2 s\ndecide con los límites\nsirve la página web",
                              w=4.4, h=5).fill("#E6EEF4"))
        d += (ventilador := bloque((15.4, 6.0), "Ventilador\n(TIP120)"))
        d += (servo := bloque((15.4, 3.8), "Servo SG90\nventana"))
        d += (bomba := bloque((15.4, 1.6), "Mini bomba\nriego (TIP120)"))
        d += (fuente := bloque((15.4, 8.4), "Eliminador 5 V", w=3.6, h=1.0))
        d += (red := bloque((8.6, -1.0), "Wifi 2.4 GHz\n(hotspot del celular)", w=4.4, h=1.4))
        d += (celular := bloque((1.8, -1.0), "Celular\nnavegador"))
        d += (compu := bloque((15.4, -1.0), "Computadora\nnavegador"))

        d += elm.Arrow().at(dht.E).to((placa.W[0], dht.E[1])).label("digital, 1 cable", fontsize=10)
        d += elm.Arrow().at(suelo.E).to((placa.W[0], suelo.E[1])).label("analógica (ADC)", fontsize=10)
        d += elm.Arrow().at((placa.E[0], ventilador.W[1])).to(ventilador.W).label("GPIO 6", fontsize=10)
        d += elm.Arrow().at((placa.E[0], servo.W[1])).to(servo.W).label("GPIO 15 (PWM)", fontsize=10)
        d += elm.Arrow().at((placa.E[0], bomba.W[1])).to(bomba.W).label("GPIO 7", fontsize=10)
        # los 5 V llegan a los tres actuadores por la derecha
        x_bus = ventilador.E[0] + 0.9
        d += elm.Line().at(fuente.E).to((x_bus, fuente.E[1]))
        d += elm.Line().at((x_bus, fuente.E[1])).to((x_bus, bomba.E[1])).label("5 V", loc="bottom", fontsize=10)
        for actuador in (ventilador, servo, bomba):
            d += elm.Arrow().at((x_bus, actuador.E[1])).to(actuador.E)
        d += elm.Arrow(double=True).at(placa.S).to(red.N)
        d += elm.Label().at((placa.S[0] + 0.25, (placa.S[1] + red.N[1]) / 2)).label("HTTP: / y /datos", halign="left", fontsize=10)
        d += elm.Arrow(double=True).at(red.W).to(celular.E)
        d += elm.Arrow(double=True).at(red.E).to(compu.W)
        d.save(str(CARPETA_IMG / "diagrama_bloques.png"), dpi=200)


# ---------------------------------------------------------------- diagrama de flujo del programa
def diagrama_flujo():
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=11, unit=0.7)
        d += (inicio := flow.Start(w=3, h=1).label("Inicio"))
        d += flow.Arrow().down()
        d += flow.Box(w=5.2, h=1.4).label("Apagar actuadores, cargar\nlímites y calibración guardados")
        d += flow.Arrow().down()
        d += flow.Box(w=5.2, h=1.2).label("Probar las redes wifi\n(sigue aunque no haya)")
        d += flow.Arrow().down()
        d += (ciclo := flow.Box(w=5.2, h=1.2).label("Atender al navegador\n(página, datos, ajustes)"))
        d += flow.Arrow().down()
        d += (pregunta := flow.Decision(w=4.4, h=1.8, E="no", S="sí").label("¿Pasaron 2 s?"))
        d += flow.Arrow().down()
        d += flow.Box(w=5.2, h=1.4).label("Leer DHT22 y sensor de suelo\n(promedio de 16 lecturas)")
        d += flow.Arrow().down()
        d += flow.Box(w=5.2, h=1.6).label("T ≥ límite alto: ventilador y\nventana. T ≤ límite bajo: apagar\ny cerrar. Guardar en historial")
        d += flow.Arrow().down()
        d += (riego := flow.Box(w=5.2, h=1.4).label("Atender el riego\n(estados de la figura aparte)"))
        d += flow.Arrow().down()
        d += flow.Box(w=5.2, h=1.2).label("Mover la ventana 2°\nhacia su posición")
        d += flow.Arrow().down()
        d += (wifi := flow.Box(w=5.2, h=1.2).label("Si se cayó el wifi, probar\nla siguiente red"))
        # regreso al inicio del ciclo
        d += elm.Wire("c", k=-3.6, arrow="->").at(wifi.W).to(ciclo.W)
        # si no han pasado 2 s, se salta la lectura y va directo al riego
        d += elm.Wire("c", k=3.2, arrow="->").at(pregunta.E).to(riego.E)
        d.save(str(CARPETA_IMG / "diagrama_flujo.png"), dpi=200)


# ---------------------------------------------------------------- estados del riego
def estados_riego():
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=11, unit=1)
        d += (esperando := flow.State(r=1.3).at((0, 0)).label("Esperando"))
        d += (regando := flow.State(r=1.3).at((7, 0)).label("Regando"))
        d += (absorbiendo := flow.State(r=1.3).at((7, -6)).label("Absorbiendo"))
        d += (pausado := flow.State(r=1.3).at((0, -6)).label("Pausado"))
        d += elm.Arc2(arrow="->", k=0.25).at(esperando.NE).to(regando.NW)
        d += elm.Arrow().at(regando.S).to(absorbiendo.N)
        d += elm.Arc2(arrow="->", k=0.25).at(absorbiendo.NW).to(esperando.SE)
        d += elm.Arc2(arrow="->", k=-0.3).at(absorbiendo.NE).to(regando.SE)
        d += elm.Arrow().at(absorbiendo.W).to(pausado.E)
        d += elm.Arrow().at(pausado.N).to(esperando.S)
        # textos de cada cambio, puestos a mano para que no tapen los circulos
        for (x, y), texto_cambio, alineacion in (
                ((3.5, 2.3), "tierra bajo el límite:\nse prende la bomba", "center"),
                ((6.8, -2.1), "pasan los segundos\nde riego: se apaga\nla bomba", "right"),
                ((10.6, -3.0), "tras la espera sigue\nseca (menos de\n3 riegos): riega otra vez", "left"),
                ((4.4, -5.2), "tras la espera la\ntierra ya tiene humedad", "center"),
                ((4.3, -6.8), "sigue seca tras\n3 riegos seguidos", "center"),
                ((-0.3, -3.0), "la tierra recupera\nhumedad o se presiona\n\"Reanudar riego\"", "right")):
            d += elm.Label().at((x, y)).label(texto_cambio, halign=alineacion, fontsize=10)
        d.save(str(CARPETA_IMG / "estados_riego.png"), dpi=200)


if __name__ == "__main__":
    CARPETA_IMG.mkdir(exist_ok=True)
    esquema_electrico()
    diagrama_bloques()
    diagrama_flujo()
    estados_riego()
    print("listo:", CARPETA_IMG)
