# Sirve la pagina del invernadero con datos simulados, para probarla en la computadora sin la placa.
# Toma la pagina tal cual de firmware/invernadero/pagina.h y responde /datos con lecturas que cambian:
# la temperatura sube y baja entre 23 y 31 grados, y la tierra se va secando hasta que la bomba riega.
# Uso: python -I simular_pagina.py   y abrir http://localhost:8765
import json
import math
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PAGINA_H = Path(__file__).resolve().parent.parent / "firmware" / "invernadero" / "pagina.h"
PUERTO = 8765
SEGUNDOS_ENTRE_LECTURAS = 2
TAMANO_HISTORIAL = 150

ajustes = {"temperaturaAbrir": 28.0, "temperaturaCerrar": 26.0, "humedadRegar": 35.0,
           "segundosRiego": 2, "segundosEspera": 15, "lecturaSeco": 3000, "lecturaMojado": 1300}
estado = {"lectura": 0, "ventilador": False, "ventana": False, "bomba": False, "riego": "esperando",
          "riegosSeguidos": 0, "inicioRiego": 0.0, "suelo": 55.0}
historial = {clave: [] for clave in ("temperatura", "humedadAire", "humedadSuelo", "ventilador", "ventana", "bomba")}
inicio = time.time()


def hacer_lectura():
    t = time.time() - inicio
    temperatura = round(27 + 4 * math.sin(t / 40), 1)
    if estado["ventilador"]:
        temperatura = round(temperatura - 1.0, 1)
    humedad_aire = round(48 + 6 * math.sin(t / 55))
    # la tierra se seca poco a poco y sube de golpe cuando la bomba riega
    estado["suelo"] = max(0.0, estado["suelo"] - 1.2) if not estado["bomba"] else min(100.0, estado["suelo"] + 9)
    if temperatura >= ajustes["temperaturaAbrir"]:
        estado["ventilador"] = estado["ventana"] = True
    elif temperatura <= ajustes["temperaturaCerrar"]:
        estado["ventilador"] = estado["ventana"] = False
    estado["lectura"] += 1
    for clave, valor in (("temperatura", temperatura), ("humedadAire", humedad_aire),
                         ("humedadSuelo", round(estado["suelo"])), ("ventilador", int(estado["ventilador"])),
                         ("ventana", int(estado["ventana"])), ("bomba", int(estado["bomba"]))):
        historial[clave].append(valor)
        del historial[clave][:-TAMANO_HISTORIAL]


def atender_riego():
    ahora = time.time()
    seco = estado["suelo"] < ajustes["humedadRegar"]
    transcurrido = ahora - estado["inicioRiego"]
    if estado["riego"] == "esperando" and seco:
        estado.update(riego="regando", bomba=True, inicioRiego=ahora, riegosSeguidos=1)
    elif estado["riego"] == "regando" and transcurrido >= ajustes["segundosRiego"]:
        estado.update(riego="absorbiendo", bomba=False, inicioRiego=ahora)
    elif estado["riego"] == "absorbiendo" and transcurrido >= ajustes["segundosEspera"]:
        if not seco:
            estado.update(riego="esperando", riegosSeguidos=0)
        elif estado["riegosSeguidos"] >= 3:
            estado["riego"] = "pausado"
        else:
            estado.update(riego="regando", bomba=True, inicioRiego=ahora, riegosSeguidos=estado["riegosSeguidos"] + 1)


def datos():
    restante = 0
    transcurrido = time.time() - estado["inicioRiego"]
    if estado["riego"] == "regando":
        restante = max(0, math.ceil(ajustes["segundosRiego"] - transcurrido))
    elif estado["riego"] == "absorbiendo":
        restante = max(0, math.ceil(ajustes["segundosEspera"] - transcurrido))
    lectura_suelo = round(ajustes["lecturaSeco"] - estado["suelo"] / 100 * (ajustes["lecturaSeco"] - ajustes["lecturaMojado"]))
    return {"lectura": estado["lectura"], "temperatura": historial["temperatura"][-1],
            "humedadAire": historial["humedadAire"][-1], "humedadSuelo": round(estado["suelo"]),
            "lecturaSuelo": lectura_suelo, "ventilador": estado["ventilador"], "ventana": estado["ventana"],
            "bomba": estado["bomba"], "riego": estado["riego"], "riegosSeguidos": estado["riegosSeguidos"],
            "riegosMaximos": 3, "segundosRestantes": restante, "ajustes": ajustes,
            "segundosEntreLecturas": SEGUNDOS_ENTRE_LECTURAS, "senalWifi": -58, "historial": historial}


class Manejador(BaseHTTPRequestHandler):
    def responder(self, codigo, tipo, cuerpo):
        datos_bytes = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos_bytes)))
        self.end_headers()
        self.wfile.write(datos_bytes)

    def do_GET(self):
        if self.path == "/":
            html = re.search(r'R"rawliteral\((.*)\)rawliteral"', PAGINA_H.read_text(encoding="utf-8"), re.S).group(1)
            self.responder(200, "text/html; charset=utf-8", html)
        elif self.path.startswith("/datos"):
            self.responder(200, "application/json", json.dumps(datos()))
        else:
            self.responder(404, "text/plain", "no existe")

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        campos = {k: v[0] for k, v in parse_qs(self.rfile.read(largo).decode()).items()}
        if self.path == "/ajustes":
            for clave in ("temperaturaAbrir", "temperaturaCerrar", "humedadRegar", "segundosRiego", "segundosEspera"):
                ajustes[clave] = float(campos[clave])
            self.responder(200, "text/plain", "Guardado")
        elif self.path == "/calibrar":
            self.responder(200, "text/plain", "Guardado: " + campos.get("punto", "?"))
        elif self.path == "/reanudar":
            estado.update(riego="esperando", riegosSeguidos=0)
            self.responder(200, "text/plain", "Riego reanudado")
        else:
            self.responder(200, "text/plain", "Valores de fabrica")

    def log_message(self, *argumentos):
        pass


if __name__ == "__main__":
    # se llena el historial como si la placa llevara 5 minutos prendida
    for _ in range(TAMANO_HISTORIAL):
        inicio -= SEGUNDOS_ENTRE_LECTURAS
        hacer_lectura()
    inicio += SEGUNDOS_ENTRE_LECTURAS * TAMANO_HISTORIAL
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    ultima = 0.0
    servidor.timeout = 0.2
    print(f"Abrir http://localhost:{PUERTO}")
    while True:
        servidor.handle_request()
        if time.time() - ultima >= SEGUNDOS_ENTRE_LECTURAS:
            ultima = time.time()
            hacer_lectura()
        atender_riego()
