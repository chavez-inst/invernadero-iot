# Cómo cargar el programa a la placa desde tu laptop

Equipo "Los multiplexores" · Para Windows 10 u 11. No hace falta saber programar ni instalar nada antes: el
programa de carga revisa qué falta y te pregunta antes de instalarlo.

## 1. Conseguir la carpeta del proyecto

Cualquiera de las dos sirve:

- **Desde GitHub:** abrir el repositorio, botón verde **Code** y luego **Download ZIP**.
- **Desde Drive:** abrir el enlace que mandó Alejandro, clic derecho en la carpeta `Programa_invernadero` y
  **Descargar**.

Después, en la carpeta de Descargas: clic derecho en el `.zip`, **Extraer todo** y abrir la carpeta extraída.
Tiene que verse así:

```
CARGAR_PROGRAMA.bat       <- el que se abre
COMO_CARGAR.md            <- este archivo
firmware\                 <- los programas de la placa (versión DHT11 y DHT22)
herramientas\             <- el programa de carga
```

No abras `CARGAR_PROGRAMA.bat` desde dentro del `.zip`: primero hay que extraerlo.

## 2. Antes de abrirlo

- Ten internet la primera vez: si falta el software de Arduino, se descarga (unos cientos de MB; puede tardar 10 a
  30 minutos). Las siguientes veces ya no hace falta descargar nada.
- Ten a la mano el nombre y la contraseña de la red wifi o del hotspot al que se va a conectar la placa. Tiene que
  ser de **2.4 GHz**:
  - iPhone: en *Compartir internet*, activar **Maximizar compatibilidad**.
  - Android: en *Punto de acceso*, **Banda** en **2.4 GHz**.
- Conecta la placa con un cable USB-C **de datos** (muchos cables solo cargan) al conector de la placa que dice
  **USB**, no al que dice COM o UART.

## 3. Abrirlo

Doble clic en **`CARGAR_PROGRAMA.bat`**. Si Windows muestra "Windows protegió su PC", da clic en **Más
información** y luego en **Ejecutar de todas formas** (pasa con cualquier archivo descargado de internet).

El programa va por pasos y en cada uno dice qué hace:

1. Revisa que estén los archivos.
2. Revisa Arduino, el soporte para la ESP32 y las librerías. Si falta algo, pregunta si lo instala.
3. Pregunta qué programa cargar (**principal** o **prueba de componentes**) y qué sensor está conectado (**DHT11**,
   el azul, o **DHT22**, el blanco).
4. Pide la red wifi. Se puede poner una segunda red de respaldo (por ejemplo, el wifi de tu casa). Se guarda solo en
   tu computadora, en `C:\Users\<tu usuario>\Invernadero_ESP32`, y la próxima vez pregunta si la usa otra vez.
5. Busca la placa. Si no la encuentra, dice qué revisar.
6. Compila y carga el programa. La primera compilación tarda unos minutos.
7. Espera a que la placa se conecte al wifi, escribe su dirección y abre la página en el navegador.

## 4. Abrir la página

La computadora o el celular tienen que estar **en la misma red** que la placa. En el navegador:

- `http://invernadero.local` (en la computadora; en iPhone también funciona)
- o la dirección con números que escribe el programa, por ejemplo `http://192.168.1.50` (en Android usar esta)

La dirección con números puede cambiar cada vez que la placa se conecta; `invernadero.local` no cambia.

El LED de la placa parpadea en azul mientras se conecta, se queda verde cuando ya tiene wifi y rojo si no encontró
ninguna red.

## 5. Si algo falla

| Qué pasa | Qué hacer |
|---|---|
| No encuentra la placa | Otro cable (de datos), el conector que dice USB y que el LED prenda. Si sigue sin aparecer: dejar presionado BOOT, presionar y soltar RST y soltar BOOT |
| No se pudo cargar | Cerrar el Arduino IDE si está abierto. Poner la placa en modo de carga (BOOT y RST, como arriba) e intentar otra vez. Al terminar, presionar RST |
| El LED queda rojo | La red no es de 2.4 GHz, el hotspot está apagado o el nombre o la contraseña están mal (mayúsculas y minúsculas cuentan). Abrir otra vez el programa y contestar que no a "Las uso otra vez?" |
| La página no abre | Que la computadora o el celular estén en la misma red que la placa. Probar la dirección con números |
| La temperatura dice "sin lectura" | Revisar los cables del sensor y que el programa cargado sea el del sensor conectado (DHT11 o DHT22) |
| Otra cosa | Mandar a Alejandro el archivo `registro_...txt` de la carpeta `Invernadero_ESP32` (el programa dice dónde está) |

## Para cambiar el código

Los programas están en `firmware/`, uno por carpeta, y se abren con el Arduino IDE. Las versiones DHT11 y DHT22 son el
mismo programa; solo cambian dos líneas al inicio (`MODELO_DHT` y `NOMBRE_DHT`). Si cambias algo, avísale a Alejandro
para pasarlo a las dos versiones. Para cargarlo desde el Arduino IDE, en la misma carpeta del `.ino` tiene que estar
`secretos.h` con las redes (se copia de `secretos_ejemplo.h`); el programa de carga lo hace solo.
