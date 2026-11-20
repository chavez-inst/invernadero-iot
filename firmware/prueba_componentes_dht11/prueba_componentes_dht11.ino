// Prueba de componentes del invernadero - Los multiplexores
// Sirve para armar por bloques en la reunion: muestra las lecturas tal cual salen de cada sensor
// y deja prender cada actuador a mano, desde una pagina sencilla o desde el monitor serie.
// No toma ninguna decision sola: nada se prende si no se pide.
//
// Monitor serie (115200 baudios), escribir una letra y Enter:
//   v = prender o apagar el ventilador     b = bomba 2 segundos
//   a = ventana abierta (90)   c = ventana cerrada (0)   m = servo a la mitad (45)
//   x = apagar todo

#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <DHT.h>
#include "secretos.h"

// ---------- sensor de temperatura ----------
// hay dos carpetas con el mismo programa: prueba_componentes_dht11 y prueba_componentes_dht22.
// solo cambian estas dos lineas; lo demas siempre se cambia en las dos (herramientas/sincronizar.ps1)
const uint8_t MODELO_DHT = DHT11;
const char* NOMBRE_DHT = "DHT11";

// mismos pines que el programa principal
const int PIN_DHT = 4;
const int PIN_SUELO = 5;
const int PIN_VENTILADOR = 6;
const int PIN_BOMBA = 7;
const int PIN_SERVO = 15;
const int PIN_LED_RGB = 48;

const int PULSO_0_GRADOS = 500;
const int PULSO_180_GRADOS = 2400;
const unsigned long SEGUNDOS_BOMBA = 2;
const char* NOMBRE_EN_LA_RED = "invernadero";   // la pagina tambien abre en http://invernadero.local

DHT sensorDht(PIN_DHT, MODELO_DHT);
WebServer servidor(80);

float temperatura = NAN, humedadAire = NAN;
int lecturaSuelo = 0;
bool ventiladorPrendido = false;
bool bombaPrendida = false;
unsigned long inicioBomba = 0;
int anguloServo = 0;
unsigned long ultimaLectura = 0;

void escribirAnguloServo(int angulo) {
  anguloServo = angulo;
  int pulso = map(angulo, 0, 180, PULSO_0_GRADOS, PULSO_180_GRADOS);
  ledcWrite(PIN_SERVO, (uint32_t)pulso * 16383 / 20000);
}

void ponerVentilador(bool prender) {
  ventiladorPrendido = prender;
  digitalWrite(PIN_VENTILADOR, prender ? HIGH : LOW);
}

void regarUnPoco() {
  bombaPrendida = true;
  inicioBomba = millis();
  digitalWrite(PIN_BOMBA, HIGH);
}

void apagarTodo() {
  ponerVentilador(false);
  bombaPrendida = false;
  digitalWrite(PIN_BOMBA, LOW);
  escribirAnguloServo(0);
}

int leerSuelo() {
  long suma = 0;
  for (int i = 0; i < 16; i++) {
    suma += analogRead(PIN_SUELO);
  }
  return suma / 16;
}

void imprimirEstado() {
  Serial.printf("%s: %s C, %s %%   Suelo (0 a 4095): %d   Ventilador: %s   Bomba: %s   Servo: %d grados   IP: %s\n",
                NOMBRE_DHT,
                isnan(temperatura) ? "sin lectura" : String(temperatura, 1).c_str(),
                isnan(humedadAire) ? "--" : String(humedadAire, 0).c_str(),
                lecturaSuelo,
                ventiladorPrendido ? "prendido" : "apagado",
                bombaPrendida ? "prendida" : "apagada",
                anguloServo,
                WiFi.localIP().toString().c_str());
}

void atenderComando(char letra) {
  switch (letra) {
    case 'v': ponerVentilador(!ventiladorPrendido); break;
    case 'b': regarUnPoco(); break;
    case 'a': escribirAnguloServo(90); break;
    case 'c': escribirAnguloServo(0); break;
    case 'm': escribirAnguloServo(45); break;
    case 'x': apagarTodo(); break;
    default: return;
  }
  imprimirEstado();
}

const char PAGINA_PRUEBA[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Prueba de componentes</title>
<style>
 body { font: 17px system-ui, sans-serif; color: #16324F; margin: 16px; max-width: 560px; }
 h1 { font-size: 1.3rem; } td { padding: 4px 10px 4px 0; } td.valor { font-weight: 600; font-size: 1.15rem; }
 button { font: inherit; padding: 9px 14px; margin: 4px 6px 4px 0; border-radius: 6px; border: 1.5px solid #16324F; background: #fff; }
 p { color: #56697D; font-size: 0.9rem; }
</style></head><body>
<h1>Prueba de componentes</h1>
<table>
 <tr><td>Temperatura (<span class="dht">DHT</span>)</td><td class="valor" id="t">--</td></tr>
 <tr><td>Humedad del aire (<span class="dht">DHT</span>)</td><td class="valor" id="ha">--</td></tr>
 <tr><td>Sensor de suelo (0 a 4095)</td><td class="valor" id="s">--</td></tr>
 <tr><td>Ventilador</td><td class="valor" id="v">--</td></tr>
 <tr><td>Bomba</td><td class="valor" id="b">--</td></tr>
 <tr><td>Servo</td><td class="valor" id="a">--</td></tr>
</table>
<p>El sensor de suelo da un número más alto mientras más seco está. Al aire debe quedar alto y en agua bajo.</p>
<div>
 <button onclick="pedir('v')">Ventilador sí / no</button>
 <button onclick="pedir('b')">Bomba 2 s</button>
</div>
<div>
 <button onclick="pedir('c')">Ventana 0°</button>
 <button onclick="pedir('m')">Ventana 45°</button>
 <button onclick="pedir('a')">Ventana 90°</button>
</div>
<div><button onclick="pedir('x')">Apagar todo</button></div>
<script>
async function pedir(letra) { await fetch('/accion?letra=' + letra, { method: 'POST' }); actualizar(); }
async function actualizar() {
  try {
    const d = await (await fetch('/datos', { cache: 'no-store' })).json();
    document.querySelectorAll('.dht').forEach(e => e.textContent = d.sensor);
    document.getElementById('t').textContent = d.temperatura === null ? 'sin lectura' : d.temperatura.toFixed(1) + ' °C';
    document.getElementById('ha').textContent = d.humedadAire === null ? '--' : d.humedadAire.toFixed(0) + ' %';
    document.getElementById('s').textContent = d.suelo;
    document.getElementById('v').textContent = d.ventilador ? 'prendido' : 'apagado';
    document.getElementById('b').textContent = d.bomba ? 'prendida' : 'apagada';
    document.getElementById('a').textContent = d.servo + '°';
  } catch (e) {}
}
actualizar(); setInterval(actualizar, 1000);
</script></body></html>
)rawliteral";

void responderDatos() {
  String json = "{";
  json += "\"sensor\":\"" + String(NOMBRE_DHT) + "\",";
  json += "\"temperatura\":" + (isnan(temperatura) ? String("null") : String(temperatura, 1)) + ",";
  json += "\"humedadAire\":" + (isnan(humedadAire) ? String("null") : String(humedadAire, 0)) + ",";
  json += "\"suelo\":" + String(lecturaSuelo) + ",";
  json += "\"ventilador\":" + String(ventiladorPrendido ? "true" : "false") + ",";
  json += "\"bomba\":" + String(bombaPrendida ? "true" : "false") + ",";
  json += "\"servo\":" + String(anguloServo) + "}";
  servidor.sendHeader("Cache-Control", "no-store");
  servidor.send(200, "application/json", json);
}

void setup() {
  pinMode(PIN_VENTILADOR, OUTPUT);
  pinMode(PIN_BOMBA, OUTPUT);
  digitalWrite(PIN_VENTILADOR, LOW);
  digitalWrite(PIN_BOMBA, LOW);

  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);
  delay(1000);
  Serial.printf("=== Prueba de componentes (version %s) ===\n", NOMBRE_DHT);
  Serial.println("v ventilador, b bomba 2 s, a/m/c ventana 90/45/0, x apagar todo");

  ledcAttach(PIN_SERVO, 50, 14);
  escribirAnguloServo(0);
  analogReadResolution(12);
  sensorDht.begin();

  // se prueba cada red unos segundos; sin wifi, la prueba sigue por el monitor serie
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setHostname(NOMBRE_EN_LA_RED);
  const int cantidad = sizeof(REDES_WIFI) / sizeof(REDES_WIFI[0]);
  for (int i = 0; i < cantidad && WiFi.status() != WL_CONNECTED; i++) {
    if (strlen(REDES_WIFI[i].nombre) == 0) continue;
    WiFi.disconnect();
    WiFi.begin(REDES_WIFI[i].nombre, REDES_WIFI[i].contrasena);
    unsigned long inicio = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - inicio < 8000) {
      rgbLedWrite(PIN_LED_RGB, 0, 0, 40);
      delay(250);
      rgbLedWrite(PIN_LED_RGB, 0, 0, 0);
      delay(250);
    }
  }
  if (WiFi.status() == WL_CONNECTED) {
    rgbLedWrite(PIN_LED_RGB, 0, 40, 0);
    // se anuncia el nombre invernadero.local, igual que el programa principal
    if (MDNS.begin(NOMBRE_EN_LA_RED)) {
      MDNS.addService("http", "tcp", 80);
    }
    Serial.print("Abrir en el navegador: http://");
    Serial.print(WiFi.localIP());
    Serial.print("  o  http://");
    Serial.print(NOMBRE_EN_LA_RED);
    Serial.println(".local");
  } else {
    rgbLedWrite(PIN_LED_RGB, 40, 0, 0);
    Serial.println("Sin wifi: usar el monitor serie");
  }

  servidor.on("/", []() { servidor.send_P(200, "text/html", PAGINA_PRUEBA); });
  servidor.on("/datos", responderDatos);
  servidor.on("/accion", HTTP_POST, []() {
    String letra = servidor.arg("letra");
    if (letra.length() == 1) atenderComando(letra[0]);
    servidor.send(200, "text/plain", "ok");
  });
  servidor.begin();
}

void loop() {
  servidor.handleClient();

  if (Serial.available()) {
    atenderComando((char)Serial.read());
  }

  // la bomba se apaga sola a los 2 segundos
  if (bombaPrendida && millis() - inicioBomba >= SEGUNDOS_BOMBA * 1000) {
    bombaPrendida = false;
    digitalWrite(PIN_BOMBA, LOW);
    imprimirEstado();
  }

  // cada segundo se leen los sensores y se escribe el estado
  if (millis() - ultimaLectura >= 1000) {
    ultimaLectura = millis();
    lecturaSuelo = leerSuelo();
    // el sensor de temperatura se lee cada 2 segundos (el DHT22 no aguanta menos)
    static bool tocaDht = false;
    tocaDht = !tocaDht;
    if (tocaDht) {
      temperatura = sensorDht.readTemperature();
      humedadAire = sensorDht.readHumidity();
    }
    imprimirEstado();
  }
}
