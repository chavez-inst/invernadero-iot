# Invernadero IoT: control de ventilación y riego

Proyecto de Sistemas de Comunicaciones (Facultad de Ingeniería, UNAM, semestre 2027-1), grupo 02.
Equipo **Los multiplexores**: Chávez López Brayan Alejandro, Chávez García Isaac, Maya Torres Bruno y Muñoz Mendoza David.

Una ESP32-S3 mide la temperatura (DHT22) y la humedad de la tierra (sensor capacitivo) de un invernadero a escala.
Si hace calor prende un ventilador y un servo abre la ventana; si la tierra está seca, una bomba riega por pulsos.
La misma placa sirve una página web con las gráficas de los sensores y de los actuadores, que se abre desde el celular
o la computadora conectados a la misma red wifi.

## Contenido

| Carpeta | Qué hay |
|---|---|
| `firmware/invernadero/` | Programa principal (Arduino IDE), con la página web en `pagina.h` |
| `firmware/prueba_componentes/` | Programa para probar cada sensor y actuador por separado al armar |
| `documento/` | Trabajo escrito en LaTeX (`main.tex`); figuras en `img/`, generadas con los scripts de `graficas/` |
| `documento/tablas/` | Tabla de piezas y cables, generada por `graficas/alambrado.py` |
| `documento/datos/` | CSV que se bajan de la página durante las pruebas |
| `herramientas/simular_pagina.py` | Sirve la página con datos simulados en `http://localhost:8765`, para probarla sin la placa |

## Placa y conexiones

ESP32-S3-DevKitC-1 con ESP32-S3-WROOM-1 N16R8 (16 MB de flash y 8 MB de PSRAM), montada sobre una protoboard de 830
puntos con la fila de pines J1 en la columna i.

| Pin | Conexión |
|---|---|
| GPIO 4 | Dato del DHT22 |
| GPIO 5 | Salida AOUT del sensor de humedad (ADC1) |
| GPIO 6 | Base del TIP120 del ventilador (con 1 kΩ) |
| GPIO 7 | Base del TIP120 de la bomba (con 1 kΩ) |
| GPIO 15 | Señal del servo SG90 |

Los actuadores se alimentan con un eliminador de 5 V aparte y las tierras se unen. Diagrama completo en
`documento/img/alambrado_completo.png` y lista de cables en `documento/tablas/cables.md`.

## Cómo usarlo

1. En Arduino IDE, instalar el soporte de placas `esp32` de Espressif (versión 3) y la librería "DHT sensor library"
   (con "Adafruit Unified Sensor").
2. Placa "ESP32S3 Dev Module", "Flash Size" en 16 MB, "PSRAM" en "OPI PSRAM" y "USB CDC On Boot" en "Enabled".
3. Copiar `secretos_ejemplo.h` como `secretos.h` y escribir las redes wifi (de 2.4 GHz).
4. Cargar `firmware/invernadero/` y abrir el monitor serie a 115200 baudios. La placa escribe su IP.
5. Abrir `http://invernadero.local` o la IP en el navegador del celular o de la computadora, en la misma red.

## Qué muestra la página

Un dibujo del invernadero en el que el ventilador gira, la ventana se abre y caen gotas al regar; los valores de
temperatura, humedad del aire y humedad de la tierra; las gráficas de los últimos 5 minutos de los sensores y de los
actuadores; y un panel para cambiar los límites, calibrar el sensor de humedad y descargar las lecturas en CSV. No
necesita internet: todo va dentro de `pagina.h`. Los datos están en JSON en `/datos`.

## Contraseñas del wifi

Los nombres y contraseñas de las redes van en `firmware/.../secretos.h`, que no se sube al repositorio.
