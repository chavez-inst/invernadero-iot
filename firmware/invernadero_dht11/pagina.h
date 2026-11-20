// Pagina web que sirve la placa. Pide los datos a /datos cada 2 segundos y dibuja el invernadero
// y las graficas sin librerias externas, para que funcione aunque el hotspot no tenga internet.
// Idea del diseno: el invernadero visto de frente es la pagina. Cada lectura se escribe junto al
// sensor que la mide, y las graficas parecen el papel milimetrico de un registrador.
// Colores tomados del logo del equipo (Proyecto/Logo/logo.svg).

#pragma once

const char PAGINA_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#16324F">
<title>Invernadero IoT</title>
<style>
  :root {
    --tinta: #16324F;          /* azul marino del logo: estructura y texto */
    --tinta-suave: #56697D;
    --papel: #FFFFFF;
    --fina: #E6EEF4;           /* rejilla fina */
    --gruesa: #CFDDE8;         /* rejilla gruesa */
    --calor: #E8604C;          /* temperatura */
    --calor-texto: #B83B28;
    --agua: #3E8EDE;           /* humedad de la tierra y riego */
    --agua-texto: #1F63A8;
    --ventana: #F2A33A;        /* ventana */
    --activo: #1FA3A0;         /* actuador prendido */
    --activo-texto: #0E7471;
    --tierra: #8B5E3C;
    --letra-plano: Bahnschrift, "DIN Alternate", "Roboto Condensed", "Arial Narrow", system-ui, sans-serif;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--papel); color: var(--tinta);
         font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .pagina { max-width: 1000px; margin: 0 auto; padding: 20px 20px 32px; }

  header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 24px; }
  .marca { display: flex; align-items: center; gap: 12px; }
  .marca svg { height: 40px; width: auto; flex: none; }
  h1 { font-family: var(--letra-plano); font-weight: 600; font-size: 1.56rem; line-height: 1.1; margin: 0; }
  .equipo { margin: 0; font-size: 0.85rem; color: var(--tinta-suave); }
  .conexion { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--tinta-suave); }
  .punto { width: 9px; height: 9px; border-radius: 50%; background: var(--gruesa); flex: none; }
  .conexion.en-linea .punto { background: var(--activo); }
  .conexion.sin-respuesta .punto { background: var(--calor); }
  .conexion.sin-respuesta { color: var(--calor-texto); }

  /* el invernadero: es lo principal de la pagina */
  .dibujo { margin: 14px 0 0; }
  .dibujo svg { display: block; width: 100%; height: auto; max-height: 70vh; }
  .dibujo text { font-family: var(--letra-plano); }
  .nombre { font-size: 12px; fill: var(--tinta-suave); }
  .cifra { font-size: 34px; font-weight: 600; fill: var(--tinta); font-variant-numeric: tabular-nums; }
  .cifra .unidad { font-size: 16px; font-weight: 400; fill: var(--tinta-suave); }
  .cifra.sin-dato { font-size: 15px; fill: var(--calor-texto); }
  .detalle { font-size: 11.5px; fill: var(--tinta-suave); }
  .estado { font-size: 11.5px; fill: var(--tinta-suave); }
  .estado tspan { font-weight: 600; fill: var(--tinta); }
  .estado tspan.prendido { fill: var(--activo-texto); }

  #aspas { transform-box: fill-box; transform-origin: center; fill: #A9B7C4; transition: fill 0.6s; }
  .girando #aspas { fill: var(--activo); animation: girar 0.8s linear infinite; }
  @keyframes girar { to { transform: rotate(360deg); } }
  #hoja { transform-box: view-box; transform-origin: 80px 128px; transition: transform 0.9s ease-in-out; }
  #manguera { transition: stroke 0.4s; }
  .regando #manguera { stroke: var(--agua); }
  #gotas { opacity: 0; transition: opacity 0.3s; }
  .regando #gotas { opacity: 1; }
  #gotas circle { animation: caer 0.7s linear infinite; }
  #gotas circle:nth-child(2) { animation-delay: 0.23s; }
  #gotas circle:nth-child(3) { animation-delay: 0.46s; }
  @keyframes caer { from { transform: translateY(0); opacity: 1; } to { transform: translateY(18px); opacity: 0.2; } }

  .aviso { margin: 6px 0 0; font-size: 0.95rem; color: var(--calor-texto); }
  .aviso:empty { display: none; }
  .aviso button { margin-left: 8px; }

  .registro { margin-top: 26px; }
  h2 { font-family: var(--letra-plano); font-weight: 600; font-size: 1.25rem; margin: 0 0 12px; }
  .graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
  .grafica { margin: 0; }
  .grafica.ancha { grid-column: 1 / -1; }
  .grafica h3 { margin: 0 0 6px; font-family: var(--letra-plano); font-size: 1rem; font-weight: 600; }
  .grafica h3 span { font-weight: 400; color: var(--tinta-suave); }
  .grafica p { margin: 8px 0 0; font-size: 0.85rem; color: var(--tinta-suave); max-width: 60ch; }
  canvas { display: block; width: 100%; height: 200px; }
  #graficaActuadores { height: 130px; }

  /* ajustes */
  details { margin-top: 30px; border-top: 2px solid var(--fina); padding-top: 14px; }
  summary { font-family: var(--letra-plano); font-weight: 600; font-size: 1.15rem; cursor: pointer; }
  .ajustes { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px 22px; margin: 14px 0;
             align-items: end; }
  label { display: block; font-size: 0.88rem; color: var(--tinta-suave); }
  input { display: block; width: 100%; margin-top: 3px; padding: 7px 9px; font: inherit; color: var(--tinta);
          border: 1.5px solid var(--gruesa); border-radius: 6px; }
  input:focus { outline: 2px solid var(--agua); border-color: var(--agua); }
  button { font: inherit; font-size: 0.92rem; padding: 7px 14px; border-radius: 6px; cursor: pointer;
           border: 1.5px solid var(--tinta); background: var(--papel); color: var(--tinta); }
  button.principal { background: var(--tinta); color: var(--papel); }
  button:disabled { opacity: 0.5; cursor: default; }
  .botones { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .respuesta { font-size: 0.88rem; color: var(--activo-texto); }
  .calibracion { margin-top: 22px; }
  .calibracion p, .descarga p { font-size: 0.9rem; color: var(--tinta-suave); margin: 4px 0 10px; max-width: 70ch; }
  .lectura-cruda { font-family: var(--letra-plano); font-size: 1.1rem; color: var(--tinta); font-weight: 600; }
  .descarga { margin-top: 22px; }
  h4 { margin: 0; font-family: var(--letra-plano); font-weight: 600; font-size: 1rem; }

  footer { margin-top: 32px; font-size: 0.8rem; color: var(--tinta-suave); }

  @media (prefers-reduced-motion: reduce) {
    .girando #aspas, #gotas circle { animation: none; }
    #hoja, #aspas, #manguera { transition: none; }
  }
  @media (max-width: 720px) {
    .pagina { padding: 14px 12px 24px; }
    .graficas { grid-template-columns: 1fr; gap: 22px; }
    canvas { height: 180px; }
  }
</style>
</head>
<body>
<div class="pagina">

<header>
  <div class="marca">
    <!-- simbolo del logo: cuatro entradas, el multiplexor y la antena -->
    <svg viewBox="30 10 340 255" aria-hidden="true">
      <g transform="translate(10,0)" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <g stroke-width="6">
          <line x1="58" y1="100" x2="122" y2="100" stroke="#1FA3A0"/>
          <line x1="58" y1="130" x2="122" y2="130" stroke="#3E8EDE"/>
          <line x1="58" y1="160" x2="122" y2="160" stroke="#F2A33A"/>
          <line x1="58" y1="190" x2="122" y2="190" stroke="#E8604C"/>
        </g>
        <circle cx="50" cy="100" r="9" fill="#1FA3A0"/>
        <circle cx="50" cy="130" r="9" fill="#3E8EDE"/>
        <circle cx="50" cy="160" r="9" fill="#F2A33A"/>
        <circle cx="50" cy="190" r="9" fill="#E8604C"/>
        <line x1="163" y1="203" x2="163" y2="238" stroke="#16324F" stroke-width="5"/>
        <circle cx="163" cy="245" r="6" fill="#FFFFFF" stroke="#16324F" stroke-width="4"/>
        <polygon points="122,70 205,105 205,185 122,220" fill="#16324F" stroke="#16324F" stroke-width="6"/>
        <path d="M205 145 H300 V82" stroke="#16324F" stroke-width="6"/>
        <circle cx="300" cy="72" r="8" fill="#16324F"/>
        <g stroke="#16324F" stroke-width="5">
          <path d="M314.1 57.9 A20 20 0 0 1 314.1 86.1"/>
          <path d="M285.9 57.9 A20 20 0 0 0 285.9 86.1"/>
          <path d="M324 48 A34 34 0 0 1 324 96" opacity="0.7"/>
          <path d="M276 48 A34 34 0 0 0 276 96" opacity="0.7"/>
        </g>
      </g>
    </svg>
    <div>
      <h1>Invernadero</h1>
      <p class="equipo">Control de ventilación y riego · Los multiplexores</p>
    </div>
  </div>
  <div class="conexion" id="conexion" aria-live="polite">
    <span class="punto"></span><span id="textoConexion">Buscando la placa...</span>
  </div>
</header>

<!-- el invernadero visto de frente, con las lecturas escritas junto a cada sensor -->
<div class="dibujo" id="dibujo">
  <svg viewBox="0 0 420 300" role="img" id="dibujoInvernadero" aria-label="Invernadero">
    <!-- piso -->
    <line x1="4" y1="262" x2="416" y2="262" stroke="#16324F" stroke-width="2"/>
    <g stroke="#CFDDE8" stroke-width="1">
      <path d="M10 270 l8 -8 M30 270 l8 -8 M50 270 l8 -8 M70 270 l8 -8 M310 270 l8 -8 M390 270 l8 -8 M410 270 l6 -6"/>
    </g>

    <!-- estructura con vidrio -->
    <polygon points="80,262 80,112 190,50 300,112 300,262" fill="#3E8EDE" fill-opacity="0.06"/>
    <g stroke="#B9D3EC" stroke-width="1">
      <line x1="135" y1="81" x2="135" y2="262"/>
      <line x1="190" y1="50" x2="190" y2="262"/>
      <line x1="245" y1="81" x2="245" y2="262"/>
      <line x1="80" y1="112" x2="300" y2="112"/>
    </g>
    <!-- igual que en la maqueta: ventana en la pared izquierda y ventilador en la derecha -->
    <polyline points="80,128 80,112 190,50 300,112 300,262" fill="none" stroke="#16324F" stroke-width="4" stroke-linejoin="round"/>
    <line x1="80" y1="186" x2="80" y2="262" stroke="#16324F" stroke-width="4"/>

    <!-- ventana en la pared izquierda: el servo hace de bisagra arriba y la abre hacia afuera -->
    <rect x="76" y="128" width="8" height="58" fill="#FFFFFF"/>
    <g id="hoja">
      <line x1="80" y1="128" x2="80" y2="186" stroke="#F2A33A" stroke-width="6" stroke-linecap="round"/>
    </g>
    <rect x="84" y="118" width="13" height="8" rx="1.5" fill="#2F6FD6"/>
    <circle cx="80" cy="128" r="3.5" fill="#16324F"/>
    <text class="estado" x="6" y="100">Ventana</text>
    <text class="estado" x="6" y="114"><tspan id="estadoVentana">--</tspan></text>

    <!-- ventilador en la pared derecha, sacando el aire caliente -->
    <g id="ventilador">
      <circle cx="300" cy="160" r="18" fill="#FFFFFF" stroke="#16324F" stroke-width="3"/>
      <g id="aspas">
        <path d="M300 160 C295 151 297 143 300 142 C303 143 305 151 300 160 Z"/>
        <path d="M300 160 C309 161 315 168 314 171 C311 173 303 168 300 160 Z"/>
        <path d="M300 160 C295 169 287 171 285 169 C286 166 292 159 300 160 Z"/>
        <circle cx="300" cy="160" r="3" fill="#16324F"/>
      </g>
    </g>
    <text class="estado" x="308" y="96">Ventilador</text>
    <text class="estado" x="308" y="110"><tspan id="estadoVentilador">--</tspan></text>

    <!-- temperatura: DHT11 o DHT22 en la pared del fondo -->
    <rect x="112" y="122" width="10" height="15" rx="2" fill="#E8604C"/>
    <text class="nombre" x="128" y="132">Temperatura</text>
    <text class="cifra" id="cifraTemperatura" x="126" y="166">--</text>
    <text class="detalle" x="128" y="184" id="textoAire">Humedad del aire: --</text>

    <!-- maceta (tupper) con la tierra, la planta y el sensor de humedad -->
    <rect x="184" y="220" width="94" height="42" rx="3" fill="#EEF2F5" stroke="#9AAABA" stroke-width="1.5"/>
    <rect x="186" y="226" width="90" height="33" fill="#8B5E3C"/>
    <g fill="#1FA3A0">
      <path d="M245 226 V194" stroke="#0E7471" stroke-width="2.5"/>
      <ellipse cx="236" cy="206" rx="10" ry="5" transform="rotate(-25 236 206)"/>
      <ellipse cx="254" cy="200" rx="10" ry="5" transform="rotate(25 254 200)"/>
      <ellipse cx="243" cy="191" rx="5" ry="9"/>
    </g>
    <rect x="206" y="198" width="7" height="50" rx="1.5" fill="#1D1D1D"/>
    <text class="nombre" x="98" y="214">Humedad del suelo</text>
    <text class="cifra" id="cifraSuelo" x="96" y="248">--</text>

    <!-- deposito de agua con la bomba, y la manguera que entra al invernadero -->
    <path d="M330 226 L336 262 L376 262 L382 226" fill="#EAF4FB" stroke="#8FB3CC" stroke-width="1.5"/>
    <path d="M332 238 L336 262 L376 262 L380 238 Z" fill="#9CC9EA" opacity="0.8"/>
    <rect x="346" y="244" width="20" height="14" rx="3" fill="#F2F2F2" stroke="#666"/>
    <path id="manguera" d="M356 244 V200 H252" fill="none" stroke="#B9CBDB" stroke-width="4" stroke-linecap="round"/>
    <g id="gotas" fill="#3E8EDE">
      <circle cx="250" cy="206" r="2.2"/>
      <circle cx="253" cy="206" r="2.2"/>
      <circle cx="248" cy="206" r="2.2"/>
    </g>
    <text class="estado" x="414" y="280" text-anchor="end">Riego <tspan id="estadoRiego">--</tspan></text>
    <text class="detalle" x="414" y="294" text-anchor="end" id="detalleRiego"></text>
  </svg>
  <p class="aviso" id="aviso" role="status"></p>
</div>

<section class="registro">
  <h2>Últimos 5 minutos</h2>
  <div class="graficas">
    <figure class="grafica">
      <h3>Temperatura <span>en °C</span></h3>
      <canvas id="graficaTemperatura" aria-label="Gráfica de temperatura de los últimos 5 minutos"></canvas>
      <p id="reglaVentilacion"></p>
    </figure>
    <figure class="grafica">
      <h3>Humedad <span>en %: tierra (línea gruesa) y aire (punteada)</span></h3>
      <canvas id="graficaHumedad" aria-label="Gráfica de humedad de los últimos 5 minutos"></canvas>
      <p id="reglaRiego"></p>
    </figure>
    <figure class="grafica ancha">
      <h3>Actuadores <span>prendido o abierto cuando hay franja</span></h3>
      <canvas id="graficaActuadores" aria-label="Estado de los actuadores en los últimos 5 minutos"></canvas>
    </figure>
  </div>
</section>

<details id="panelAjustes">
  <summary>Ajustes, calibración y datos</summary>

  <form id="formularioAjustes">
    <div class="ajustes">
      <label>Abrir ventana y prender ventilador a (°C)
        <input name="temperaturaAbrir" type="number" step="0.5" min="10" max="50" required></label>
      <label>Cerrar y apagar al bajar a (°C)
        <input name="temperaturaCerrar" type="number" step="0.5" min="5" max="49" required></label>
      <label>Regar si la tierra baja de (%)
        <input name="humedadRegar" type="number" step="1" min="5" max="95" required></label>
      <label>Segundos de riego
        <input name="segundosRiego" type="number" step="1" min="1" max="10" required></label>
      <label>Segundos de espera después de regar
        <input name="segundosEspera" type="number" step="1" min="5" max="120" required></label>
    </div>
    <div class="botones">
      <button class="principal" type="submit">Guardar ajustes</button>
      <button type="button" id="botonFabrica">Volver a los valores de fábrica</button>
      <span class="respuesta" id="respuestaAjustes" role="status"></span>
    </div>
  </form>

  <div class="calibracion">
    <h4>Calibrar el sensor de humedad</h4>
    <p>Con el sensor limpio y seco, al aire, presiona "Al aire". Luego mételo en un vaso con agua hasta la línea
       que marca hasta dónde se entierra y presiona "En agua". La placa guarda las dos lecturas.</p>
    <p>Lectura del sensor ahora: <span class="lectura-cruda" id="lecturaCruda">--</span>
       (al aire: <span id="lecturaSeco">--</span>, en agua: <span id="lecturaMojado">--</span>)</p>
    <div class="botones">
      <button type="button" data-punto="seco">Al aire (seco)</button>
      <button type="button" data-punto="mojado">En agua (mojado)</button>
      <span class="respuesta" id="respuestaCalibracion" role="status"></span>
    </div>
  </div>

  <div class="descarga">
    <h4>Descargar los datos</h4>
    <p>La página guarda cada lectura desde que se abrió (más los 5 minutos que ya traía la placa).
       El archivo se abre en Excel o en Python para hacer las gráficas del documento.</p>
    <div class="botones">
      <button type="button" id="botonDescargar">Descargar CSV</button>
      <span class="respuesta" id="cuentaRegistro"></span>
    </div>
  </div>
</details>

<footer>Los multiplexores. Facultad de Ingeniería, UNAM. Sistemas de Comunicaciones, grupo 02.</footer>
</div>

<script>
const COLORES = {
  tinta: "#16324F", suave: "#56697D", fina: "#E6EEF4", gruesa: "#CFDDE8",
  calor: "#E8604C", agua: "#3E8EDE", aire: "#8FA3B6", ventana: "#F2A33A", activo: "#1FA3A0"
};
const LETRA = "12px Bahnschrift, 'DIN Alternate', 'Roboto Condensed', 'Arial Narrow', system-ui, sans-serif";
let ultimosDatos = null;
let ultimaRespuesta = null;
let ultimaLecturaRegistrada = -1;
let ajustesEnFormulario = false;
const registro = [];   // todas las lecturas desde que se abrio la pagina, para el CSV

// ---------- graficas ----------

function prepararCanvas(id) {
  const canvas = document.getElementById(id);
  const escala = window.devicePixelRatio || 1;
  const ancho = canvas.clientWidth, alto = canvas.clientHeight;
  canvas.width = ancho * escala;
  canvas.height = alto * escala;
  const ctx = canvas.getContext("2d");
  ctx.scale(escala, escala);
  ctx.clearRect(0, 0, ancho, alto);
  ctx.font = LETRA;
  return { ctx, ancho, alto };
}

function linea(ctx, x1, y1, x2, y2) {
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
}

// rejilla de tiempo comun a las tres graficas: una linea fina cada medio minuto y una gruesa por minuto
function dibujarEjeTiempo(ctx, cantidad, xDe, arriba, abajo, alto, segundosEntreLecturas, conTexto) {
  const lecturasPorMinuto = 60 / segundosEntreLecturas;
  ctx.lineWidth = 1;
  ctx.strokeStyle = COLORES.fina;
  for (let k = cantidad - 1; k >= 0; k -= lecturasPorMinuto / 2) linea(ctx, xDe(k), arriba, xDe(k), abajo);
  ctx.strokeStyle = COLORES.gruesa;
  ctx.fillStyle = COLORES.suave;
  ctx.textAlign = "center";
  for (let minuto = 1; minuto * lecturasPorMinuto <= cantidad - 1; minuto++) {
    const x = xDe(cantidad - 1 - minuto * lecturasPorMinuto);
    linea(ctx, x, arriba, x, abajo);
    if (conTexto) ctx.fillText("-" + minuto + " min", x, alto - 6);
  }
  if (conTexto) { ctx.textAlign = "right"; ctx.fillText("ahora", xDe(cantidad - 1), alto - 6); }
}

// grafica de linea sobre papel milimetrico. series: [{valores, color, grosor, punteada}].
// zona: franja entre dos valores (bajo y alto) con su texto en cada orilla
function dibujarGrafica(id, series, opciones) {
  const { ctx, ancho, alto } = prepararCanvas(id);
  const izq = 32, der = 8, arriba = 8, abajo = 22;
  const anchoUtil = ancho - izq - der, altoUtil = alto - arriba - abajo;
  const cantidad = series[0].valores.length;

  let minimo = opciones.minimo, maximo = opciones.maximo;
  if (minimo === null) {
    const validos = series[0].valores.filter(v => v !== null);
    const todos = validos.concat([opciones.zona.bajo, opciones.zona.alto]);
    minimo = Math.floor(Math.min(...todos) - 2);
    maximo = Math.ceil(Math.max(...todos) + 2);
    // el rango se ajusta a un multiplo de 4 para que las divisiones caigan en numeros enteros
    maximo = minimo + 4 * Math.ceil((maximo - minimo) / 4);
  }
  const yDe = v => arriba + altoUtil - altoUtil * (v - minimo) / (maximo - minimo);
  const xDe = i => izq + anchoUtil * i / Math.max(cantidad - 1, 1);

  // rejilla
  ctx.lineWidth = 1;
  ctx.strokeStyle = COLORES.fina;
  for (let i = 0; i <= 8; i++) { const y = arriba + altoUtil * i / 8; linea(ctx, izq, y, ancho - der, y); }
  dibujarEjeTiempo(ctx, cantidad, xDe, arriba, arriba + altoUtil, alto, opciones.segundosEntreLecturas, true);
  ctx.strokeStyle = COLORES.gruesa;
  ctx.fillStyle = COLORES.suave;
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const valor = minimo + (maximo - minimo) * i / 4;
    linea(ctx, izq, yDe(valor), ancho - der, yDe(valor));
    ctx.fillText(valor.toFixed(0), izq - 6, yDe(valor) + 4);
  }

  // franja de la zona, con linea punteada en cada orilla
  const z = opciones.zona;
  const yBajo = yDe(z.bajo), yAlto = yDe(z.alto);
  ctx.fillStyle = z.color + "22";
  ctx.fillRect(izq, yAlto, anchoUtil, yBajo - yAlto);
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = z.color;
  if (z.textoAlto) linea(ctx, izq, yAlto, ancho - der, yAlto);
  if (z.textoBajo) linea(ctx, izq, yBajo, ancho - der, yBajo);
  ctx.setLineDash([]);

  // lineas de datos, como la pluma de un registrador; los null (sin lectura) quedan como hueco
  for (const serie of series) {
    ctx.strokeStyle = serie.color;
    ctx.lineWidth = serie.grosor;
    ctx.lineJoin = "round";
    ctx.setLineDash(serie.punteada ? [5, 4] : []);
    ctx.beginPath();
    let enTrazo = false;
    serie.valores.forEach((v, i) => {
      if (v === null) { enTrazo = false; return; }
      if (enTrazo) ctx.lineTo(xDe(i), yDe(v)); else ctx.moveTo(xDe(i), yDe(v));
      enTrazo = true;
    });
    ctx.stroke();
  }
  ctx.setLineDash([]);

  ctx.textAlign = "left";
  if (z.textoAlto) escribirEtiqueta(ctx, z.textoAlto, izq + 6, yAlto - 5);
  if (z.textoBajo) escribirEtiqueta(ctx, z.textoBajo, izq + 6, yBajo + 15);

  // punto en la lectura mas reciente de la serie principal
  const ultimo = series[0].valores[cantidad - 1];
  if (ultimo !== undefined && ultimo !== null) {
    ctx.fillStyle = series[0].color;
    ctx.beginPath(); ctx.arc(xDe(cantidad - 1), yDe(ultimo), 4, 0, 2 * Math.PI); ctx.fill();
  }
  ctx.strokeStyle = COLORES.tinta;
  ctx.lineWidth = 1.2;
  linea(ctx, izq, arriba + altoUtil, ancho - der, arriba + altoUtil);
}

// tres carriles, uno por actuador; la franja de color marca cuando estuvo prendido o abierto
function dibujarActuadores(datos) {
  const { ctx, ancho, alto } = prepararCanvas("graficaActuadores");
  const izq = 78, der = 8, arriba = 4, abajo = 22;
  const h = datos.historial;
  const cantidad = h.ventilador.length;
  const anchoUtil = ancho - izq - der;
  const xDe = i => izq + anchoUtil * i / Math.max(cantidad - 1, 1);
  const carriles = [
    ["Ventilador", h.ventilador, COLORES.activo],
    ["Ventana", h.ventana, COLORES.ventana],
    ["Bomba", h.bomba, COLORES.agua]
  ];
  const altoCarril = (alto - arriba - abajo) / carriles.length;
  dibujarEjeTiempo(ctx, cantidad, xDe, arriba, alto - abajo, alto, datos.segundosEntreLecturas, true);
  carriles.forEach(([nombre, valores, color], indice) => {
    const y = arriba + indice * altoCarril;
    ctx.strokeStyle = COLORES.gruesa;
    ctx.lineWidth = 1;
    linea(ctx, izq, y + altoCarril, ancho - der, y + altoCarril);
    ctx.fillStyle = color;
    const paso = anchoUtil / Math.max(cantidad - 1, 1);
    valores.forEach((v, i) => {
      if (v) ctx.fillRect(xDe(i) - paso / 2, y + 5, paso + 0.6, altoCarril - 10);
    });
    ctx.fillStyle = COLORES.tinta;
    ctx.textAlign = "right";
    ctx.fillText(nombre, izq - 8, y + altoCarril / 2 + 4);
  });
}

function escribirEtiqueta(ctx, texto, x, y) {
  const ancho = ctx.measureText(texto).width;
  ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
  ctx.fillRect(x - 3, y - 11, ancho + 6, 15);
  ctx.fillStyle = COLORES.tinta;
  ctx.fillText(texto, x, y);
}

function dibujarGraficas() {
  if (!ultimosDatos) return;
  const d = ultimosDatos, a = d.ajustes, h = d.historial;
  dibujarGrafica("graficaTemperatura", [{ valores: h.temperatura, color: COLORES.calor, grosor: 2.2 }], {
    minimo: null, maximo: null, segundosEntreLecturas: d.segundosEntreLecturas,
    zona: { bajo: a.temperaturaCerrar, alto: a.temperaturaAbrir, color: COLORES.calor,
            textoAlto: "abre a " + a.temperaturaAbrir + " °C", textoBajo: "cierra a " + a.temperaturaCerrar + " °C" }
  });
  dibujarGrafica("graficaHumedad", [
    { valores: h.humedadSuelo, color: COLORES.agua, grosor: 2.4 },
    { valores: h.humedadAire, color: COLORES.aire, grosor: 1.4, punteada: true }
  ], {
    minimo: 0, maximo: 100, segundosEntreLecturas: d.segundosEntreLecturas,
    zona: { bajo: 0, alto: a.humedadRegar, color: COLORES.agua, textoAlto: "riega abajo de " + a.humedadRegar + " %" }
  });
  dibujarActuadores(d);
}

// ---------- dibujo y textos ----------

function mostrarCifra(id, valor, decimales, unidad) {
  const cifra = document.getElementById(id);
  if (valor === null) {
    cifra.setAttribute("class", "cifra sin-dato");
    cifra.textContent = "sin lectura";
    return;
  }
  cifra.setAttribute("class", "cifra");
  cifra.innerHTML = valor.toFixed(decimales) + '<tspan class="unidad" dx="3">' + unidad + "</tspan>";
}

function mostrarEstado(id, activo, textoSi, textoNo) {
  const estado = document.getElementById(id);
  estado.setAttribute("class", activo ? "prendido" : "");
  estado.textContent = activo ? textoSi : textoNo;
}

function describirRiego(d) {
  if (d.riego === "regando") return ["regando", "riego " + d.riegosSeguidos + " de " + d.riegosMaximos + " · faltan " + d.segundosRestantes + " s"];
  if (d.riego === "absorbiendo") return ["en espera", "vuelve a medir en " + d.segundosRestantes + " s"];
  if (d.riego === "pausado") return ["en pausa", "sigue seco tras " + d.riegosMaximos + " riegos"];
  return ["listo", "riega abajo de " + d.ajustes.humedadRegar + " %"];
}

// traduce los dBm a una palabra; los cortes son aproximados
function describirSenal(dbm) {
  if (dbm >= -60) return "buena";
  if (dbm >= -70) return "regular";
  return "débil";
}

function mostrarConexion(enLinea, texto) {
  document.getElementById("conexion").className = "conexion " + (enLinea ? "en-linea" : "sin-respuesta");
  document.getElementById("textoConexion").textContent = texto;
}

function llenarFormulario(a) {
  const f = document.getElementById("formularioAjustes");
  for (const nombre of ["temperaturaAbrir", "temperaturaCerrar", "humedadRegar", "segundosRiego", "segundosEspera"]) {
    f.elements[nombre].value = a[nombre];
  }
  ajustesEnFormulario = true;
}

// ---------- registro para el CSV ----------

function agregarAlRegistro(hora, d, i) {
  const h = d.historial;
  registro.push([hora, h.temperatura[i], h.humedadAire[i], h.humedadSuelo[i], h.ventilador[i], h.ventana[i], h.bomba[i]]);
}

function actualizarRegistro(d) {
  const ultimo = d.historial.temperatura.length - 1;
  if (ultimo < 0 || d.lectura === ultimaLecturaRegistrada) return;
  if (ultimaLecturaRegistrada < 0) {
    // la primera vez se toma todo el historial de la placa, con la hora aproximada de cada lectura
    const ahora = Date.now();
    for (let i = 0; i <= ultimo; i++) {
      agregarAlRegistro(new Date(ahora - (ultimo - i) * d.segundosEntreLecturas * 1000), d, i);
    }
  } else {
    // si se perdieron lecturas mientras no hubo respuesta, se agregan las que falten
    const nuevas = Math.min(d.lectura - ultimaLecturaRegistrada, ultimo + 1);
    for (let i = ultimo - nuevas + 1; i <= ultimo; i++) {
      agregarAlRegistro(new Date(Date.now() - (ultimo - i) * d.segundosEntreLecturas * 1000), d, i);
    }
  }
  ultimaLecturaRegistrada = d.lectura;
  document.getElementById("cuentaRegistro").textContent = registro.length + " lecturas guardadas";
}

function descargarCsv() {
  const dosDigitos = n => String(n).padStart(2, "0");
  const formatoHora = t => t.getFullYear() + "-" + dosDigitos(t.getMonth() + 1) + "-" + dosDigitos(t.getDate()) + " " +
    dosDigitos(t.getHours()) + ":" + dosDigitos(t.getMinutes()) + ":" + dosDigitos(t.getSeconds());
  const filas = ["hora,temperatura_C,humedad_aire_pct,humedad_suelo_pct,ventilador,ventana,bomba"];
  for (const [hora, ...valores] of registro) {
    filas.push(formatoHora(hora) + "," + valores.map(v => v === null ? "" : v).join(","));
  }
  const archivo = new Blob([filas.join("\n") + "\n"], { type: "text/csv" });
  const enlace = document.createElement("a");
  const ahora = new Date();
  enlace.href = URL.createObjectURL(archivo);
  enlace.download = "invernadero_" + ahora.getFullYear() + "-" + dosDigitos(ahora.getMonth() + 1) + "-" +
    dosDigitos(ahora.getDate()) + "_" + dosDigitos(ahora.getHours()) + dosDigitos(ahora.getMinutes()) + ".csv";
  enlace.click();
  URL.revokeObjectURL(enlace.href);
}

// ---------- pedir datos ----------

async function actualizar() {
  try {
    const respuesta = await fetch("/datos", { cache: "no-store" });
    const d = await respuesta.json();
    ultimosDatos = d;
    ultimaRespuesta = new Date();

    mostrarCifra("cifraTemperatura", d.temperatura, 1, "°C");
    mostrarCifra("cifraSuelo", d.humedadSuelo, 0, "%");
    document.getElementById("textoAire").textContent =
      "Humedad del aire: " + (d.humedadAire === null ? "--" : d.humedadAire.toFixed(0) + " %");
    mostrarEstado("estadoVentilador", d.ventilador, "prendido", "apagado");
    mostrarEstado("estadoVentana", d.ventana, "abierta", "cerrada");
    const [estado, detalle] = describirRiego(d);
    mostrarEstado("estadoRiego", d.riego === "regando", estado, estado);
    document.getElementById("detalleRiego").textContent = detalle;

    // el dibujo refleja el estado de los actuadores; la ventana gira hasta 60 grados en el dibujo
    const dibujo = document.getElementById("dibujo");
    dibujo.classList.toggle("girando", d.ventilador);
    dibujo.classList.toggle("regando", d.bomba);
    document.getElementById("hoja").style.transform = "rotate(" + (d.ventana ? 60 : 0) + "deg)";

    // avisos con lo que hay que revisar
    const aviso = document.getElementById("aviso");
    const textos = [];
    if (d.temperatura === null) {
      // el programa dice para que sensor se compilo; si no coincide con el conectado, no hay lectura
      const sensor = d.sensorTemperatura || "sensor de temperatura";
      textos.push("El " + sensor + " no responde: revisa sus cables (+, out y −) y que el programa cargado sea el de ese sensor.");
    }
    if (d.riego === "pausado") textos.push("El riego está en pausa porque la tierra sigue seca: revisa que el sensor esté en la tierra y que haya agua en el depósito.");
    aviso.textContent = textos.join(" ");
    if (d.riego === "pausado") {
      const boton = document.createElement("button");
      boton.textContent = "Reanudar riego";
      boton.onclick = () => enviar("/reanudar", null, "respuestaAjustes");
      aviso.appendChild(boton);
    }

    const a = d.ajustes;
    document.getElementById("reglaVentilacion").textContent =
      "Arriba de " + a.temperaturaAbrir + " °C se prende el ventilador y se abre la ventana; se apaga y se cierra al bajar a " +
      a.temperaturaCerrar + " °C. La franja marca ese margen.";
    document.getElementById("reglaRiego").textContent =
      "Si la tierra baja de " + a.humedadRegar + " %, la bomba riega " + a.segundosRiego + " s y espera " + a.segundosEspera +
      " s antes de volver a medir. Después de " + d.riegosMaximos + " riegos seguidos se pausa.";
    document.getElementById("lecturaCruda").textContent = d.lecturaSuelo;
    document.getElementById("lecturaSeco").textContent = a.lecturaSeco;
    document.getElementById("lecturaMojado").textContent = a.lecturaMojado;
    if (!ajustesEnFormulario) llenarFormulario(a);

    // descripcion del dibujo para lectores de pantalla
    document.getElementById("dibujoInvernadero").setAttribute("aria-label",
      "Invernadero. Temperatura " + (d.temperatura === null ? "sin lectura" : d.temperatura.toFixed(1) + " °C") +
      ", ventilador " + (d.ventilador ? "prendido" : "apagado") + ", ventana " + (d.ventana ? "abierta" : "cerrada") +
      ". Humedad de la tierra " + (d.humedadSuelo === null ? "sin lectura" : d.humedadSuelo.toFixed(0) + " %") +
      ", riego " + estado + ".");

    actualizarRegistro(d);
    dibujarGraficas();
    mostrarConexion(true, "Señal wifi " + describirSenal(d.senalWifi) + " (" + d.senalWifi + " dBm), " +
      ultimaRespuesta.toLocaleTimeString());
  } catch (error) {
    const desde = ultimaRespuesta ? " desde las " + ultimaRespuesta.toLocaleTimeString() : "";
    mostrarConexion(false, "Sin respuesta de la placa" + desde + ". Revisa que estés en la misma red wifi.");
  }
}

// manda un cambio a la placa y escribe su respuesta junto a los botones
async function enviar(ruta, cuerpo, idRespuesta) {
  const salida = document.getElementById(idRespuesta);
  salida.textContent = "Enviando...";
  try {
    const respuesta = await fetch(ruta, { method: "POST", body: cuerpo });
    salida.textContent = await respuesta.text();
    if (respuesta.ok) { ajustesEnFormulario = false; actualizar(); }
  } catch (error) {
    salida.textContent = "No se pudo enviar. Revisa la conexión.";
  }
}

document.getElementById("formularioAjustes").addEventListener("submit", evento => {
  evento.preventDefault();
  enviar("/ajustes", new URLSearchParams(new FormData(evento.target)), "respuestaAjustes");
});
document.getElementById("botonFabrica").addEventListener("click", () => {
  if (confirm("¿Regresar los límites y la calibración a los valores de fábrica?")) enviar("/fabrica", null, "respuestaAjustes");
});
document.querySelectorAll("[data-punto]").forEach(boton => boton.addEventListener("click", () =>
  enviar("/calibrar", new URLSearchParams({ punto: boton.dataset.punto }), "respuestaCalibracion")));
document.getElementById("botonDescargar").addEventListener("click", descargarCsv);

window.addEventListener("resize", dibujarGraficas);
actualizar();
setInterval(actualizar, 2000);
</script>
</body>
</html>
)rawliteral";
