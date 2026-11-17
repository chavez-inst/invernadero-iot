// Invernadero IoT - Los multiplexores
// La ESP32-S3 mide la temperatura (DHT22) y la humedad de la tierra (sensor capacitivo).
// Si hace calor prende el ventilador y el servo abre la ventana; si la tierra esta seca
// riega unos segundos, espera a que el agua se absorba y vuelve a medir.
// La misma placa sirve una pagina web con los valores, las graficas y los ajustes.

#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <DHT.h>
#include "secretos.h"
#include "pagina.h"

// ---------- pines (ver documento/img/alambrado_completo.png) ----------
const int PIN_DHT = 4;          // dato del DHT22
const int PIN_SUELO = 5;        // salida AOUT del sensor de humedad; tiene que ser un pin del 1 al 10
const int PIN_VENTILADOR = 6;   // base del TIP120 del ventilador (con su resistencia de 1 k)
const int PIN_BOMBA = 7;        // base del TIP120 de la bomba (con su resistencia de 1 k)
const int PIN_SERVO = 15;       // senal del servo de la ventana
const int PIN_LED_RGB = 48;     // LED de colores de la tarjeta

// ---------- valores de fabrica ----------
// estos se pueden cambiar desde la pagina; la placa guarda lo ultimo que se ajusto,
// asi que solo se usan la primera vez o al presionar "volver a los valores de fabrica"
const float TEMPERATURA_ABRIR_FABRICA = 28.0;    // grados C: se prende el ventilador y se abre la ventana
const float TEMPERATURA_CERRAR_FABRICA = 26.0;   // grados C: se apaga y se cierra
const float HUMEDAD_REGAR_FABRICA = 35.0;        // % de humedad de la tierra: por debajo se riega
const int SEGUNDOS_RIEGO_FABRICA = 2;            // cuanto tiempo se prende la bomba en cada riego
const int SEGUNDOS_ESPERA_FABRICA = 15;          // cuanto se espera despues de regar antes de volver a medir
// lecturas del sensor de humedad (de 0 a 4095) con el sensor al aire y metido en agua.
// se calibran en la reunion desde la pagina; estos son valores tipicos para empezar
const int LECTURA_SECO_FABRICA = 3000;
const int LECTURA_MOJADO_FABRICA = 1300;

// ---------- valores fijos ----------
const int RIEGOS_SEGUIDOS_MAXIMOS = 3;           // si despues de estos riegos sigue seco, se pausa el riego
const int ANGULO_VENTANA_CERRADA = 0;            // grados del servo; se ajustan segun como quede pegado
const int ANGULO_VENTANA_ABIERTA = 90;
const int PULSO_0_GRADOS = 500;                  // microsegundos; el SG90 va de 0 a 180 grados entre estos dos
const int PULSO_180_GRADOS = 2400;
const unsigned long TIEMPO_ENTRE_LECTURAS = 2000;   // el DHT22 no puede leer mas rapido
const int TAMANO_HISTORIAL = 150;                   // 150 lecturas cada 2 s = 5 minutos
const int MUESTRAS_SUELO = 16;                      // lecturas que se promedian para bajar el ruido
const int FALLAS_DHT_PERMITIDAS = 3;                // lecturas fallidas seguidas antes de marcar "sin lectura"
const unsigned long ESPERA_POR_RED_AL_ARRANCAR = 8000;   // tiempo que se prueba cada red al prender
const unsigned long TIEMPO_ENTRE_RECONEXIONES = 12000;   // sin wifi, cada cuanto se prueba la siguiente red
const char* NOMBRE_EN_LA_RED = "invernadero";            // la pagina tambien abre en http://invernadero.local

DHT sensorDht(PIN_DHT, DHT22);
WebServer servidor(80);
Preferences memoria;

// ajustes actuales (se cargan de la memoria de la placa)
float temperaturaAbrir, temperaturaCerrar, humedadRegar;
int segundosRiego, segundosEspera, lecturaSeco, lecturaMojado;

// ultima lectura
float temperaturaActual = NAN;
float humedadAireActual = NAN;
float humedadSueloActual = NAN;
int lecturaSueloActual = 0;
int fallasSeguidasDht = 0;
unsigned long numeroDeLectura = 0;

// actuadores
bool ventiladorPrendido = false;
bool ventanaAbierta = false;
bool bombaPrendida = false;
bool bombaPrendioEnEsteIntervalo = false;   // para que la grafica marque riegos cortos
int anguloServo = ANGULO_VENTANA_CERRADA;   // donde esta el servo ahora
int anguloObjetivo = ANGULO_VENTANA_CERRADA;
unsigned long ultimoPasoServo = 0;

// riego: espera a que la tierra este seca, riega, deja que el agua se absorba y vuelve a revisar
enum EstadoRiego { ESPERANDO, REGANDO, ABSORBIENDO, PAUSADO };
EstadoRiego estadoRiego = ESPERANDO;
unsigned long inicioEstadoRiego = 0;
int riegosSeguidos = 0;

// historial circular para que las graficas tengan datos al abrir la pagina
float historialTemperatura[TAMANO_HISTORIAL];
float historialHumedadAire[TAMANO_HISTORIAL];
float historialHumedadSuelo[TAMANO_HISTORIAL];
bool historialVentilador[TAMANO_HISTORIAL];
bool historialVentana[TAMANO_HISTORIAL];
bool historialBomba[TAMANO_HISTORIAL];
int lecturasGuardadas = 0;
int siguientePosicion = 0;

unsigned long ultimaLectura = 0;
unsigned long ultimoIntentoWifi = 0;
int redActual = 0;
bool estabaConectada = false;
const int CANTIDAD_DE_REDES = sizeof(REDES_WIFI) / sizeof(REDES_WIFI[0]);

// ---------- ajustes guardados ----------

void cargarAjustes() {
  memoria.begin("invernadero", true);
  temperaturaAbrir = memoria.getFloat("tAbrir", TEMPERATURA_ABRIR_FABRICA);
  temperaturaCerrar = memoria.getFloat("tCerrar", TEMPERATURA_CERRAR_FABRICA);
  humedadRegar = memoria.getFloat("hRegar", HUMEDAD_REGAR_FABRICA);
  segundosRiego = memoria.getInt("sRiego", SEGUNDOS_RIEGO_FABRICA);
  segundosEspera = memoria.getInt("sEspera", SEGUNDOS_ESPERA_FABRICA);
  lecturaSeco = memoria.getInt("lSeco", LECTURA_SECO_FABRICA);
  lecturaMojado = memoria.getInt("lMojado", LECTURA_MOJADO_FABRICA);
  memoria.end();
}

void guardarAjustes() {
  memoria.begin("invernadero", false);
  memoria.putFloat("tAbrir", temperaturaAbrir);
  memoria.putFloat("tCerrar", temperaturaCerrar);
  memoria.putFloat("hRegar", humedadRegar);
  memoria.putInt("sRiego", segundosRiego);
  memoria.putInt("sEspera", segundosEspera);
  memoria.putInt("lSeco", lecturaSeco);
  memoria.putInt("lMojado", lecturaMojado);
  memoria.end();
}

// ---------- sensores ----------

// promedia varias lecturas seguidas del sensor de humedad: el ruido sube y baja al azar
// y en el promedio se cancela en buena parte
int leerSueloCrudo() {
  long suma = 0;
  for (int i = 0; i < MUESTRAS_SUELO; i++) {
    suma += analogRead(PIN_SUELO);   // de 0 a 4095
  }
  return suma / MUESTRAS_SUELO;
}

// el sensor capacitivo da una lectura mas alta mientras mas seca esta la tierra.
// con las dos lecturas de calibracion se pasa a porcentaje: seco = 0 %, en agua = 100 %
float convertirAHumedad(int lectura) {
  if (lecturaSeco == lecturaMojado) {
    return NAN;
  }
  float porcentaje = 100.0 * (lecturaSeco - lectura) / (lecturaSeco - lecturaMojado);
  if (porcentaje < 0) porcentaje = 0;
  if (porcentaje > 100) porcentaje = 100;
  return porcentaje;
}

// lee el DHT22; si falla unas pocas veces seguidas se conserva el ultimo valor bueno,
// para que el ventilador no se apague por una sola lectura mala
void leerDht() {
  float temperatura = sensorDht.readTemperature();
  float humedad = sensorDht.readHumidity();
  if (!isnan(temperatura) && !isnan(humedad)) {
    fallasSeguidasDht = 0;
    temperaturaActual = temperatura;
    humedadAireActual = humedad;
    return;
  }
  fallasSeguidasDht++;
  if (fallasSeguidasDht >= FALLAS_DHT_PERMITIDAS) {
    temperaturaActual = NAN;
    humedadAireActual = NAN;
  }
}

void guardarEnHistorial() {
  historialTemperatura[siguientePosicion] = temperaturaActual;
  historialHumedadAire[siguientePosicion] = humedadAireActual;
  historialHumedadSuelo[siguientePosicion] = humedadSueloActual;
  historialVentilador[siguientePosicion] = ventiladorPrendido;
  historialVentana[siguientePosicion] = ventanaAbierta;
  historialBomba[siguientePosicion] = bombaPrendioEnEsteIntervalo;
  siguientePosicion = (siguientePosicion + 1) % TAMANO_HISTORIAL;
  if (lecturasGuardadas < TAMANO_HISTORIAL) {
    lecturasGuardadas++;
  }
  // el siguiente intervalo empieza con el estado que tiene la bomba ahora
  bombaPrendioEnEsteIntervalo = bombaPrendida;
}

// ---------- actuadores ----------

void prenderBomba(bool prender) {
  bombaPrendida = prender;
  digitalWrite(PIN_BOMBA, prender ? HIGH : LOW);
  if (prender) {
    bombaPrendioEnEsteIntervalo = true;
  }
}

// el ventilador y la ventana van juntos: se usan dos limites para que no se prendan y apaguen
// a cada rato cuando la temperatura anda cerca de uno solo
void decidirVentilacion() {
  if (isnan(temperaturaActual)) {
    // sin lectura no se sabe si hace calor; se deja todo apagado y cerrado
    ventiladorPrendido = false;
    ventanaAbierta = false;
  } else if (temperaturaActual >= temperaturaAbrir) {
    ventiladorPrendido = true;
    ventanaAbierta = true;
  } else if (temperaturaActual <= temperaturaCerrar) {
    ventiladorPrendido = false;
    ventanaAbierta = false;
  }
  digitalWrite(PIN_VENTILADOR, ventiladorPrendido ? HIGH : LOW);
  anguloObjetivo = ventanaAbierta ? ANGULO_VENTANA_ABIERTA : ANGULO_VENTANA_CERRADA;
}

// el servo se mueve con pulsos de 50 por segundo; el ancho del pulso dice el angulo
void escribirAnguloServo(int angulo) {
  int pulso = map(angulo, 0, 180, PULSO_0_GRADOS, PULSO_180_GRADOS);   // microsegundos
  // con 14 bits el periodo de 20000 us se divide en 16384 partes
  uint32_t ciclo = (uint32_t)pulso * 16383 / 20000;
  ledcWrite(PIN_SERVO, ciclo);
}

// mueve la ventana de poco en poco, para que se vea suave y el servo no pida tanta corriente de golpe
void moverVentana() {
  if (anguloServo == anguloObjetivo || millis() - ultimoPasoServo < 15) {
    return;
  }
  ultimoPasoServo = millis();
  if (anguloServo < anguloObjetivo) {
    anguloServo = min(anguloServo + 2, anguloObjetivo);
  } else {
    anguloServo = max(anguloServo - 2, anguloObjetivo);
  }
  escribirAnguloServo(anguloServo);
}

// se revisa en cada vuelta del programa para que la bomba se apague justo a tiempo
void atenderRiego() {
  unsigned long transcurrido = millis() - inicioEstadoRiego;
  bool tierraSeca = !isnan(humedadSueloActual) && humedadSueloActual < humedadRegar;

  switch (estadoRiego) {
    case ESPERANDO:
      if (tierraSeca) {
        riegosSeguidos = 1;
        prenderBomba(true);
        estadoRiego = REGANDO;
        inicioEstadoRiego = millis();
      }
      break;

    case REGANDO:
      if (transcurrido >= (unsigned long)segundosRiego * 1000) {
        prenderBomba(false);
        estadoRiego = ABSORBIENDO;
        inicioEstadoRiego = millis();
      }
      break;

    case ABSORBIENDO:
      // despues de la espera se vuelve a medir: si ya hay humedad, se termina
      if (transcurrido >= (unsigned long)segundosEspera * 1000) {
        if (!tierraSeca) {
          riegosSeguidos = 0;
          estadoRiego = ESPERANDO;
        } else if (riegosSeguidos >= RIEGOS_SEGUIDOS_MAXIMOS) {
          // si sigue seco despues de varios riegos, algo pasa: el sensor esta fuera de la tierra
          // o el deposito esta vacio. se pausa para no tirar agua
          estadoRiego = PAUSADO;
          Serial.println("Riego en pausa: revisar el sensor o el deposito");
        } else {
          riegosSeguidos++;
          prenderBomba(true);
          estadoRiego = REGANDO;
          inicioEstadoRiego = millis();
        }
      }
      break;

    case PAUSADO:
      // se reanuda solo cuando la tierra vuelve a tener humedad, o con el boton de la pagina
      if (!tierraSeca && !isnan(humedadSueloActual)) {
        riegosSeguidos = 0;
        estadoRiego = ESPERANDO;
      }
      break;
  }
}

const char* nombreEstadoRiego() {
  switch (estadoRiego) {
    case REGANDO: return "regando";
    case ABSORBIENDO: return "absorbiendo";
    case PAUSADO: return "pausado";
    default: return "esperando";
  }
}

void hacerLectura() {
  leerDht();
  lecturaSueloActual = leerSueloCrudo();
  humedadSueloActual = convertirAHumedad(lecturaSueloActual);
  decidirVentilacion();
  numeroDeLectura++;
  guardarEnHistorial();

  // estado en el monitor serie, por si la pagina no abre
  Serial.printf("T: %s C  HR aire: %s %%  Suelo: %s %% (lectura %d)  Ventilador: %s  Ventana: %s  Riego: %s  IP: %s\n",
                isnan(temperaturaActual) ? "--" : String(temperaturaActual, 1).c_str(),
                isnan(humedadAireActual) ? "--" : String(humedadAireActual, 0).c_str(),
                isnan(humedadSueloActual) ? "--" : String(humedadSueloActual, 0).c_str(),
                lecturaSueloActual,
                ventiladorPrendido ? "prendido" : "apagado",
                ventanaAbierta ? "abierta" : "cerrada",
                nombreEstadoRiego(),
                WiFi.localIP().toString().c_str());
}

// ---------- pagina web ----------

// convierte un numero a texto para el JSON; si no hay lectura escribe null
String numeroParaJson(float valor, int decimales) {
  if (isnan(valor)) {
    return "null";
  }
  return String(valor, decimales);
}

void responderPagina() {
  servidor.send_P(200, "text/html", PAGINA_HTML);
}

void responderDatos() {
  unsigned long segundosRestantes = 0;
  unsigned long transcurrido = millis() - inicioEstadoRiego;
  if (estadoRiego == REGANDO && transcurrido < (unsigned long)segundosRiego * 1000) {
    segundosRestantes = ((unsigned long)segundosRiego * 1000 - transcurrido + 999) / 1000;
  } else if (estadoRiego == ABSORBIENDO && transcurrido < (unsigned long)segundosEspera * 1000) {
    segundosRestantes = ((unsigned long)segundosEspera * 1000 - transcurrido + 999) / 1000;
  }

  String json;
  json.reserve(9000);
  json = "{";
  json += "\"lectura\":" + String(numeroDeLectura) + ",";
  json += "\"temperatura\":" + numeroParaJson(temperaturaActual, 1) + ",";
  json += "\"humedadAire\":" + numeroParaJson(humedadAireActual, 0) + ",";
  json += "\"humedadSuelo\":" + numeroParaJson(humedadSueloActual, 0) + ",";
  json += "\"lecturaSuelo\":" + String(lecturaSueloActual) + ",";
  json += "\"ventilador\":" + String(ventiladorPrendido ? "true" : "false") + ",";
  json += "\"ventana\":" + String(ventanaAbierta ? "true" : "false") + ",";
  json += "\"bomba\":" + String(bombaPrendida ? "true" : "false") + ",";
  json += "\"riego\":\"" + String(nombreEstadoRiego()) + "\",";
  json += "\"riegosSeguidos\":" + String(riegosSeguidos) + ",";
  json += "\"riegosMaximos\":" + String(RIEGOS_SEGUIDOS_MAXIMOS) + ",";
  json += "\"segundosRestantes\":" + String(segundosRestantes) + ",";
  json += "\"ajustes\":{";
  json += "\"temperaturaAbrir\":" + numeroParaJson(temperaturaAbrir, 1) + ",";
  json += "\"temperaturaCerrar\":" + numeroParaJson(temperaturaCerrar, 1) + ",";
  json += "\"humedadRegar\":" + numeroParaJson(humedadRegar, 0) + ",";
  json += "\"segundosRiego\":" + String(segundosRiego) + ",";
  json += "\"segundosEspera\":" + String(segundosEspera) + ",";
  json += "\"lecturaSeco\":" + String(lecturaSeco) + ",";
  json += "\"lecturaMojado\":" + String(lecturaMojado) + "},";
  json += "\"segundosEntreLecturas\":" + String(TIEMPO_ENTRE_LECTURAS / 1000) + ",";
  // intensidad de la senal wifi que recibe la placa, en dBm
  json += "\"senalWifi\":" + String(WiFi.RSSI()) + ",";

  // el historial se manda de la lectura mas vieja a la mas nueva
  int primeraPosicion = (siguientePosicion - lecturasGuardadas + TAMANO_HISTORIAL) % TAMANO_HISTORIAL;
  String temperaturas, humedadesAire, humedadesSuelo, ventiladores, ventanas, bombas;
  for (int i = 0; i < lecturasGuardadas; i++) {
    int posicion = (primeraPosicion + i) % TAMANO_HISTORIAL;
    String separador = (i > 0) ? "," : "";
    temperaturas += separador + numeroParaJson(historialTemperatura[posicion], 1);
    humedadesAire += separador + numeroParaJson(historialHumedadAire[posicion], 0);
    humedadesSuelo += separador + numeroParaJson(historialHumedadSuelo[posicion], 0);
    ventiladores += separador + String(historialVentilador[posicion] ? 1 : 0);
    ventanas += separador + String(historialVentana[posicion] ? 1 : 0);
    bombas += separador + String(historialBomba[posicion] ? 1 : 0);
  }
  json += "\"historial\":{";
  json += "\"temperatura\":[" + temperaturas + "],";
  json += "\"humedadAire\":[" + humedadesAire + "],";
  json += "\"humedadSuelo\":[" + humedadesSuelo + "],";
  json += "\"ventilador\":[" + ventiladores + "],";
  json += "\"ventana\":[" + ventanas + "],";
  json += "\"bomba\":[" + bombas + "]}";
  json += "}";

  // que el navegador no guarde la respuesta y siempre pida datos nuevos
  servidor.sendHeader("Cache-Control", "no-store");
  servidor.send(200, "application/json", json);
}

// lee un numero del formulario y revisa que este dentro de un rango razonable
bool leerNumero(const char* nombre, float minimo, float maximo, float &destino) {
  if (!servidor.hasArg(nombre)) {
    return false;
  }
  float valor = servidor.arg(nombre).toFloat();
  if (valor < minimo || valor > maximo) {
    return false;
  }
  destino = valor;
  return true;
}

// la pagina manda los cinco ajustes juntos; si alguno no tiene sentido no se cambia nada
void recibirAjustes() {
  float abrir, cerrar, regar, riego, espera;
  bool completos = leerNumero("temperaturaAbrir", 10, 50, abrir) &&
                   leerNumero("temperaturaCerrar", 5, 49, cerrar) &&
                   leerNumero("humedadRegar", 5, 95, regar) &&
                   leerNumero("segundosRiego", 1, 10, riego) &&
                   leerNumero("segundosEspera", 5, 120, espera);
  if (!completos || cerrar >= abrir) {
    servidor.send(400, "text/plain", "Revisa los valores: la temperatura para cerrar tiene que ser menor que la de abrir.");
    return;
  }
  temperaturaAbrir = abrir;
  temperaturaCerrar = cerrar;
  humedadRegar = regar;
  segundosRiego = (int)riego;
  segundosEspera = (int)espera;
  guardarAjustes();
  decidirVentilacion();
  Serial.println("Ajustes cambiados desde la pagina");
  servidor.send(200, "text/plain", "Guardado");
}

// guarda la lectura actual del sensor de suelo como "seco" (al aire) o "mojado" (en agua)
void recibirCalibracion() {
  String punto = servidor.arg("punto");
  int lectura = leerSueloCrudo();
  if (punto == "seco") {
    lecturaSeco = lectura;
  } else if (punto == "mojado") {
    lecturaMojado = lectura;
  } else {
    servidor.send(400, "text/plain", "Falta indicar seco o mojado");
    return;
  }
  guardarAjustes();
  lecturaSueloActual = lectura;
  humedadSueloActual = convertirAHumedad(lectura);
  Serial.printf("Calibracion: %s = %d\n", punto.c_str(), lectura);
  servidor.send(200, "text/plain", "Guardado: " + punto + " = " + String(lectura));
}

void reanudarRiego() {
  riegosSeguidos = 0;
  prenderBomba(false);
  estadoRiego = ESPERANDO;
  servidor.send(200, "text/plain", "Riego reanudado");
}

void volverAFabrica() {
  temperaturaAbrir = TEMPERATURA_ABRIR_FABRICA;
  temperaturaCerrar = TEMPERATURA_CERRAR_FABRICA;
  humedadRegar = HUMEDAD_REGAR_FABRICA;
  segundosRiego = SEGUNDOS_RIEGO_FABRICA;
  segundosEspera = SEGUNDOS_ESPERA_FABRICA;
  lecturaSeco = LECTURA_SECO_FABRICA;
  lecturaMojado = LECTURA_MOJADO_FABRICA;
  guardarAjustes();
  decidirVentilacion();
  servidor.send(200, "text/plain", "Valores de fabrica");
}

// ---------- wifi ----------

void ponerLed(int rojo, int verde, int azul) {
  rgbLedWrite(PIN_LED_RGB, rojo, verde, azul);
}

void probarRed(int indice) {
  WiFi.disconnect();
  WiFi.begin(REDES_WIFI[indice].nombre, REDES_WIFI[indice].contrasena);
  Serial.printf("Probando la red %d de %d\n", indice + 1, CANTIDAD_DE_REDES);
}

// al prender se prueba cada red unos segundos; si ninguna aparece, la placa sigue sin wifi
// para no dejar los actuadores sin control, y sigue probando en segundo plano
void conectarWifiAlArrancar() {
  WiFi.mode(WIFI_STA);
  // sin ahorro de energia en el wifi, para que la pagina responda rapido
  WiFi.setSleep(false);
  WiFi.setHostname(NOMBRE_EN_LA_RED);
  for (int indice = 0; indice < CANTIDAD_DE_REDES; indice++) {
    if (strlen(REDES_WIFI[indice].nombre) == 0) {
      continue;
    }
    redActual = indice;
    probarRed(indice);
    unsigned long inicio = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - inicio < ESPERA_POR_RED_AL_ARRANCAR) {
      ponerLed(0, 0, 40);   // parpadea en azul mientras se conecta
      delay(250);
      ponerLed(0, 0, 0);
      delay(250);
    }
    if (WiFi.status() == WL_CONNECTED) {
      return;
    }
  }
  Serial.println("No se encontro ninguna red; se sigue intentando en segundo plano");
  ponerLed(40, 0, 0);
}

// cada vez que se conecta se anuncia el nombre invernadero.local y se escribe la IP
void alConectarse() {
  MDNS.end();
  if (MDNS.begin(NOMBRE_EN_LA_RED)) {
    MDNS.addService("http", "tcp", 80);
  }
  Serial.print("Conectada. Abrir en el navegador: http://");
  Serial.print(WiFi.localIP());
  Serial.print("  o  http://");
  Serial.print(NOMBRE_EN_LA_RED);
  Serial.println(".local");
  ponerLed(0, 40, 0);   // verde fijo cuando ya hay wifi
}

// si se cae el wifi, el LED se pone rojo y cada pocos segundos se prueba la siguiente red.
// WiFi.begin no espera a que se conecte, asi que la placa sigue controlando todo mientras tanto
void revisarWifi() {
  bool conectada = (WiFi.status() == WL_CONNECTED);
  if (conectada && !estabaConectada) {
    alConectarse();
  } else if (!conectada && estabaConectada) {
    Serial.println("Se perdio el wifi");
    ponerLed(40, 0, 0);
    ultimoIntentoWifi = millis();
  }
  estabaConectada = conectada;

  if (!conectada && millis() - ultimoIntentoWifi >= TIEMPO_ENTRE_RECONEXIONES) {
    ultimoIntentoWifi = millis();
    // se busca la siguiente red que tenga nombre
    for (int intento = 0; intento < CANTIDAD_DE_REDES; intento++) {
      redActual = (redActual + 1) % CANTIDAD_DE_REDES;
      if (strlen(REDES_WIFI[redActual].nombre) > 0) {
        break;
      }
    }
    probarRed(redActual);
  }
}

void setup() {
  // primero se apagan los actuadores, antes que cualquier otra cosa
  pinMode(PIN_VENTILADOR, OUTPUT);
  pinMode(PIN_BOMBA, OUTPUT);
  digitalWrite(PIN_VENTILADOR, LOW);
  digitalWrite(PIN_BOMBA, LOW);

  Serial.begin(115200);
  // si nadie esta leyendo el monitor serie, los mensajes se descartan en vez de esperar;
  // sin esto la placa se frena y la pagina deja de responder
  Serial.setTxTimeoutMs(0);
  delay(1000);
  Serial.println();
  Serial.println("=== Invernadero IoT ===");

  cargarAjustes();

  // servo: pulsos de 50 Hz con 14 bits de resolucion
  ledcAttach(PIN_SERVO, 50, 14);
  escribirAnguloServo(ANGULO_VENTANA_CERRADA);

  analogReadResolution(12);
  sensorDht.begin();
  delay(2000);     // el DHT22 necesita unos segundos al prenderse
  hacerLectura();  // primera lectura antes del wifi, para que los actuadores arranquen bien

  conectarWifiAlArrancar();
  ultimoIntentoWifi = millis();

  servidor.on("/", responderPagina);
  servidor.on("/datos", responderDatos);
  servidor.on("/ajustes", HTTP_POST, recibirAjustes);
  servidor.on("/calibrar", HTTP_POST, recibirCalibracion);
  servidor.on("/reanudar", HTTP_POST, reanudarRiego);
  servidor.on("/fabrica", HTTP_POST, volverAFabrica);
  servidor.begin();
}

void loop() {
  servidor.handleClient();

  if (millis() - ultimaLectura >= TIEMPO_ENTRE_LECTURAS) {
    ultimaLectura = millis();
    hacerLectura();
  }

  atenderRiego();
  moverVentana();
  revisarWifi();
}
