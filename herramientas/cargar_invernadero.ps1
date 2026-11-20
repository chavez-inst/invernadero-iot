# Carga el programa del invernadero a la ESP32-S3, paso a paso.
# Revisa que este todo el software (Arduino, soporte esp32 y librerias) y ofrece instalar lo que falte,
# pide los datos del wifi, detecta la placa, compila, carga el programa y abre la pagina con las graficas.
#
# Se abre con doble clic en CARGAR_PROGRAMA.bat (en la carpeta principal del proyecto).
# Tambien se puede correr desde PowerShell:
#   powershell -ExecutionPolicy Bypass -File herramientas\cargar_invernadero.ps1
# Opciones para no contestar preguntas (sirven para probar):
#   -Programa principal|prueba   -Sensor dht11|dht22   -Puerto COM5   -UsarRedesGuardadas   -SinAbrirPagina

param(
    [ValidateSet("", "principal", "prueba")][string]$Programa = "",
    [ValidateSet("", "dht11", "dht22")][string]$Sensor = "",
    [string]$Puerto = "",
    [switch]$UsarRedesGuardadas,
    [switch]$SinAbrirPagina
)

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "Invernadero IoT - cargar programa a la ESP32-S3"

# ---------- datos fijos ----------
$URL_PLACAS = "https://espressif.github.io/arduino-esp32/package_esp32_index.json"
$URL_ARDUINO_CLI = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
$FQBN = "esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,CDCOnBoot=cdc"
$VERSION_MINIMA_ESP32 = [version]"3.0.0"     # el servo usa ledcAttach, que existe desde la version 3
$LIBRERIAS = @("DHT sensor library", "Adafruit Unified Sensor")
$NOMBRE_EN_LA_RED = "invernadero"

# carpeta del proyecto (la que tiene firmware\) y carpeta de trabajo en esta computadora
$raiz = Split-Path $PSScriptRoot -Parent
$firmware = Join-Path $raiz "firmware"
$trabajo = Join-Path $env:USERPROFILE "Invernadero_ESP32"
$archivoSecretos = Join-Path $trabajo "secretos.h"
$archivoPreferencias = Join-Path $trabajo "ultima_carga.json"

# ---------- funciones para escribir en pantalla ----------

function Titulo($numero, $texto) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host " Paso $numero. $texto" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}
function Info($texto) { Write-Host "  $texto" }
function Bien($texto) { Write-Host "  [OK] $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "  [!] $texto" -ForegroundColor Yellow }
function Falla($texto) { Write-Host "  [X] $texto" -ForegroundColor Red }

function Preguntar($texto, $porDefecto) {
    if ($porDefecto) { $texto = "$texto [$porDefecto]" }
    $respuesta = Read-Host "  $texto"
    if ([string]::IsNullOrWhiteSpace($respuesta)) { return $porDefecto }
    return $respuesta.Trim()
}

function PreguntarSiNo($texto, $porDefecto = "s") {
    while ($true) {
        $opciones = if ($porDefecto -eq "s") { "S/n" } else { "s/N" }
        $respuesta = Read-Host "  $texto ($opciones)"
        if ([string]::IsNullOrWhiteSpace($respuesta)) { $respuesta = $porDefecto }
        switch -Regex ($respuesta.Trim().ToLower()) {
            "^(s|si|sí|y|yes)$" { return $true }
            "^(n|no)$" { return $false }
        }
        Aviso "Escribe s o n."
    }
}

# muestra opciones numeradas y regresa el numero elegido
function Elegir($texto, $opciones, $porDefecto = 1) {
    Write-Host ""
    Write-Host "  $texto"
    for ($i = 0; $i -lt $opciones.Count; $i++) {
        Write-Host ("    {0}) {1}" -f ($i + 1), $opciones[$i])
    }
    while ($true) {
        $respuesta = Preguntar "Escribe el numero" "$porDefecto"
        $numero = 0
        if ([int]::TryParse($respuesta, [ref]$numero) -and $numero -ge 1 -and $numero -le $opciones.Count) {
            return $numero
        }
        Aviso "Escribe un numero del 1 al $($opciones.Count)."
    }
}

function Terminar($codigo) {
    Write-Host ""
    if ($codigo -ne 0) {
        Aviso "Si no sabes que paso, manda a Alejandro el archivo del registro:"
        Info $registro
    }
    try { Stop-Transcript | Out-Null } catch {}
    Write-Host ""
    Read-Host "  Presiona Enter para cerrar"
    exit $codigo
}

# corre un programa sin que se vea su texto, mostrando puntos mientras trabaja.
# regresa el codigo de salida; lo que escribio queda en $archivoSalida
function CorrerConPuntos($programa, $argumentos, $archivoSalida) {
    $errores = "$archivoSalida.err"
    $proceso = Start-Process -FilePath $programa -ArgumentList $argumentos -NoNewWindow -PassThru `
        -RedirectStandardOutput $archivoSalida -RedirectStandardError $errores
    # en PowerShell 5.1 hay que tocar Handle para que despues se pueda leer ExitCode
    $null = $proceso.Handle
    $inicio = Get-Date
    Write-Host -NoNewline "  "
    while (-not $proceso.HasExited) {
        Start-Sleep -Milliseconds 2000
        Write-Host -NoNewline "."
    }
    $proceso.WaitForExit()
    $segundos = [int]((Get-Date) - $inicio).TotalSeconds
    Write-Host " ($segundos s)"
    if (Test-Path $errores) {
        Get-Content $errores | Add-Content $archivoSalida
        Remove-Item $errores -ErrorAction SilentlyContinue
    }
    return $proceso.ExitCode
}

# las rutas con espacios van entre comillas para Start-Process
function Comillas($texto) { return "`"$texto`"" }

# ---------- inicio ----------

New-Item -ItemType Directory -Force $trabajo | Out-Null
$registro = Join-Path $trabajo ("registro_" + (Get-Date -Format "yyyy-MM-dd_HHmm") + ".txt")
try { Start-Transcript -Path $registro -Force | Out-Null } catch {}

Clear-Host
Write-Host ""
Write-Host "  INVERNADERO IoT - Los multiplexores" -ForegroundColor Green
Write-Host "  Cargar el programa a la ESP32-S3" -ForegroundColor Green
Write-Host ""
Info "Este programa te guia paso a paso:"
Info "  1. Revisa que esten los archivos del proyecto"
Info "  2. Revisa el software de Arduino y ofrece instalar lo que falte"
Info "  3. Pregunta que programa cargar y para que sensor (DHT11 o DHT22)"
Info "  4. Pide el nombre y la contrasena del wifi (o del hotspot)"
Info "  5. Busca la placa conectada por USB"
Info "  6. Compila y carga el programa"
Info "  7. Lee la direccion de la placa y abre la pagina con las graficas"
Info ""
Info "Puedes cerrar esta ventana cuando quieras; lo que ya se instalo no se pierde."
Info "Tus datos del wifi se guardan solo en esta computadora, en $trabajo"

# ---------- 1. archivos del proyecto ----------
Titulo 1 "Archivos del proyecto"

$carpetasNecesarias = @("invernadero_dht11", "invernadero_dht22", "prueba_componentes_dht11", "prueba_componentes_dht22")
$faltan = @($carpetasNecesarias | Where-Object { -not (Test-Path (Join-Path $firmware $_)) })
if ($faltan.Count -gt 0) {
    Falla "No encuentro los programas de la placa."
    Info "Este archivo tiene que estar dentro de la carpeta del proyecto, que se ve asi:"
    Info ""
    Info "  invernadero-iot\"
    Info "  |-- CARGAR_PROGRAMA.bat        <- el que se abre con doble clic"
    Info "  |-- firmware\                  <- los programas de la placa"
    Info "  |   |-- invernadero_dht11\"
    Info "  |   |-- invernadero_dht22\"
    Info "  |   |-- prueba_componentes_dht11\"
    Info "  |   '-- prueba_componentes_dht22\"
    Info "  '-- herramientas\"
    Info "      '-- cargar_invernadero.ps1"
    Info ""
    Info "Como conseguir la carpeta completa:"
    Info "  - Desde GitHub: boton verde 'Code' > 'Download ZIP'."
    Info "  - Desde Drive: clic derecho en la carpeta > 'Descargar'."
    Info "Despues: clic derecho en el .zip > 'Extraer todo', entra a la carpeta extraida"
    Info "y abre CARGAR_PROGRAMA.bat desde ahi (no desde dentro del .zip)."
    Info ""
    Info "Ahora estoy en: $raiz"
    Terminar 1
}
Bien "Programas encontrados en $firmware"

# ---------- 2. software de Arduino ----------
Titulo 2 "Software de Arduino"

function BuscarArduinoCli {
    $candidatos = @(
        "$env:LOCALAPPDATA\Programs\arduino-ide\resources\app\lib\backend\resources\arduino-cli.exe",
        "$env:ProgramFiles\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe",
        (Join-Path $trabajo "arduino-cli\arduino-cli.exe")
    )
    foreach ($ruta in $candidatos) {
        if (Test-Path $ruta) { return $ruta }
    }
    $enPath = Get-Command arduino-cli -ErrorAction SilentlyContinue
    if ($enPath) { return $enPath.Source }
    return $null
}

function HayInternet {
    try {
        $respuesta = Invoke-WebRequest "https://downloads.arduino.cc" -Method Head -UseBasicParsing -TimeoutSec 10
        return $true
    } catch {
        # algunos servidores no aceptan HEAD; si contesto algo, hay internet
        if ($_.Exception.Response) { return $true }
        return $false
    }
}

function RevisarInternet {
    if (-not (HayInternet)) {
        Falla "No hay internet, y hace falta para descargar lo que falta."
        Info "Conecta la computadora a internet y vuelve a abrir CARGAR_PROGRAMA.bat."
        Terminar 1
    }
}

$cli = BuscarArduinoCli
if ($cli) {
    Bien "Arduino encontrado: $cli"
} else {
    Aviso "No esta instalado Arduino (ni el Arduino IDE ni arduino-cli)."
    $hayWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
    $opciones = @()
    if ($hayWinget) {
        $opciones += "Instalar Arduino IDE (recomendado: sirve para cargar y tambien para ver o cambiar el codigo; unos 200 MB)"
    }
    $opciones += "Instalar solo arduino-cli (mas ligero, unos 20 MB; solo sirve para cargar desde aqui)"
    $opciones += "Salir sin instalar nada"
    $eleccion = Elegir "Que quieres hacer?" $opciones 1
    $textoElegido = $opciones[$eleccion - 1]

    if ($textoElegido -like "Salir*") { Terminar 1 }
    RevisarInternet

    if ($textoElegido -like "Instalar Arduino IDE*") {
        Info "Instalando Arduino IDE con winget. Si Windows pregunta si permites cambios, contesta que si."
        winget install --id ArduinoSA.IDE.stable -e --accept-package-agreements --accept-source-agreements
        $cli = BuscarArduinoCli
        if (-not $cli) {
            Aviso "El Arduino IDE se instalo, pero no encuentro su arduino-cli. Instalo solo arduino-cli en su lugar."
        }
    }
    if (-not $cli) {
        $zip = Join-Path $trabajo "arduino-cli.zip"
        $destino = Join-Path $trabajo "arduino-cli"
        Info "Descargando arduino-cli de downloads.arduino.cc ..."
        try {
            $ProgressPreference = "SilentlyContinue"
            Invoke-WebRequest $URL_ARDUINO_CLI -OutFile $zip -UseBasicParsing
            $ProgressPreference = "Continue"
            Expand-Archive $zip -DestinationPath $destino -Force
            Remove-Item $zip
        } catch {
            Falla "No se pudo descargar arduino-cli: $($_.Exception.Message)"
            Terminar 1
        }
        $cli = BuscarArduinoCli
    }
    if (-not $cli) {
        Falla "No se pudo instalar Arduino."
        Info "Instala el Arduino IDE a mano desde https://www.arduino.cc/en/software y vuelve a abrir este programa."
        Terminar 1
    }
    Bien "Arduino listo: $cli"
}

# soporte de placas esp32 (de Espressif)
function VersionEsp32 {
    $lineas = & $cli core list 2>$null
    foreach ($linea in $lineas) {
        if ($linea -match "^esp32:esp32\s+(\d+\.\d+\.\d+)") { return [version]$Matches[1] }
    }
    return $null
}

$versionEsp32 = VersionEsp32
if ($versionEsp32 -and $versionEsp32 -ge $VERSION_MINIMA_ESP32) {
    Bien "Soporte para placas ESP32 instalado (version $versionEsp32)"
} else {
    if ($versionEsp32) {
        Aviso "El soporte para ESP32 que tienes es muy viejo (version $versionEsp32); el programa necesita la 3 o mas nueva."
    } else {
        Aviso "Falta el soporte para placas ESP32 (de Espressif)."
    }
    Info "Es una descarga grande (varios cientos de MB). Puede tardar de 10 a 30 minutos segun el internet."
    if (-not (PreguntarSiNo "Lo instalo ahora?")) {
        Info "Sin el soporte para ESP32 no se puede compilar. Vuelve a abrir este programa cuando quieras instalarlo."
        Terminar 1
    }
    RevisarInternet
    Info "Actualizando la lista de placas..."
    & $cli core update-index --additional-urls $URL_PLACAS
    Info "Instalando el soporte esp32 (vas a ver el avance de cada descarga)..."
    & $cli core install esp32:esp32 --additional-urls $URL_PLACAS
    $versionEsp32 = VersionEsp32
    if (-not $versionEsp32 -or $versionEsp32 -lt $VERSION_MINIMA_ESP32) {
        Falla "No se pudo instalar el soporte esp32. Revisa el internet y vuelve a intentar."
        Terminar 1
    }
    Bien "Soporte para placas ESP32 instalado (version $versionEsp32)"
}

# librerias del sensor de temperatura
$instaladas = (& $cli lib list 2>$null) -join "`n"
$libreriasFaltantes = @($LIBRERIAS | Where-Object { $instaladas -notmatch [regex]::Escape($_) })
if ($libreriasFaltantes.Count -eq 0) {
    Bien "Librerias del sensor DHT instaladas"
} else {
    Aviso ("Faltan librerias: " + ($libreriasFaltantes -join ", "))
    if (-not (PreguntarSiNo "Las instalo ahora? (son pequenas)")) { Terminar 1 }
    RevisarInternet
    & $cli lib update-index
    & $cli lib install @libreriasFaltantes
    $instaladas = (& $cli lib list 2>$null) -join "`n"
    $libreriasFaltantes = @($LIBRERIAS | Where-Object { $instaladas -notmatch [regex]::Escape($_) })
    if ($libreriasFaltantes.Count -gt 0) {
        Falla "No se pudieron instalar las librerias."
        Terminar 1
    }
    Bien "Librerias del sensor DHT instaladas"
}

# ---------- 3. que programa cargar ----------
Titulo 3 "Que programa cargar"

$preferencias = $null
if (Test-Path $archivoPreferencias) {
    try { $preferencias = Get-Content $archivoPreferencias -Raw | ConvertFrom-Json } catch {}
}

if (-not $Programa) {
    $porDefecto = 1
    if ($preferencias -and $preferencias.programa -eq "prueba") { $porDefecto = 2 }
    $eleccion = Elegir "Que programa quieres cargar?" @(
        "Programa principal: el invernadero completo, con la pagina, las graficas y el control automatico",
        "Prueba de componentes: para armar por bloques; cada sensor y actuador se prueba a mano"
    ) $porDefecto
    $Programa = if ($eleccion -eq 1) { "principal" } else { "prueba" }
}

if (-not $Sensor) {
    $porDefecto = 1
    if ($preferencias -and $preferencias.sensor -eq "dht22") { $porDefecto = 2 }
    Info ""
    Info "El sensor de temperatura puede ser de dos modelos, y cada uno lleva su version del programa:"
    Info "  DHT11: azul y mas chico (el que tenemos ahora)"
    Info "  DHT22: blanco y un poco mas grande (mide con mas precision)"
    $eleccion = Elegir "Que sensor de temperatura esta conectado?" @("DHT11 (azul)", "DHT22 (blanco)") $porDefecto
    $Sensor = if ($eleccion -eq 1) { "dht11" } else { "dht22" }
}

$nombreCarpeta = if ($Programa -eq "principal") { "invernadero_$Sensor" } else { "prueba_componentes_$Sensor" }
Bien "Se va a cargar: $nombreCarpeta"

# ---------- 4. wifi ----------
Titulo 4 "Red wifi (o hotspot) a la que se conecta la placa"

# lee los nombres de las redes de un secretos.h (sin mostrar las contrasenas)
function RedesGuardadas($ruta) {
    if (-not (Test-Path $ruta)) { return @() }
    $texto = Get-Content $ruta -Raw
    $nombres = @()
    foreach ($coincidencia in [regex]::Matches($texto, '\{\s*"((?:[^"\\]|\\.)*)"\s*,')) {
        $nombre = $coincidencia.Groups[1].Value -replace '\\(.)', '$1'
        if ($nombre) { $nombres += $nombre }
    }
    return $nombres
}

# red wifi a la que esta conectada esta computadora ahora
function RedDeLaComputadora {
    $lineas = netsh wlan show interfaces 2>$null
    foreach ($linea in $lineas) {
        if ($linea -match "^\s*SSID\s*:\s*(.+)$") { return $Matches[1].Trim() }
    }
    return $null
}

# canal de la red de esta computadora; del 36 para arriba es 5 GHz
function CanalDeLaComputadora {
    $lineas = netsh wlan show interfaces 2>$null
    foreach ($linea in $lineas) {
        if ($linea -match "^\s*(Channel|Canal)\s*:\s*(\d+)") { return [int]$Matches[2] }
    }
    return $null
}

# escapa comillas y barras para escribir el texto dentro de un programa en C
function TextoParaC($texto) { return ($texto -replace '\\', '\\' -replace '"', '\"') }

function PedirRedes {
    Info "La placa solo se conecta a redes de 2.4 GHz."
    Info "  - Hotspot de iPhone: en 'Compartir internet' activa 'Maximizar compatibilidad'."
    Info "  - Hotspot de Android: en 'Punto de acceso' > 'Banda', elige 2.4 GHz."
    Info "  - Wifi de casa: casi todos los modems tienen una red de 2.4 GHz (la que no dice 5G)."
    Info "Puedes poner dos redes: la placa prueba la primera y, si no la encuentra, la segunda."
    Info "Lo usual: la 1 es el hotspot del celular y la 2 el wifi de tu casa."
    $redes = @()
    $sugerida = RedDeLaComputadora
    for ($i = 1; $i -le 2; $i++) {
        Write-Host ""
        if ($i -eq 1) {
            $nombre = Preguntar "Nombre de la red $i" $sugerida
        } else {
            $nombre = Preguntar "Nombre de la red $i (Enter para no poner otra)" ""
        }
        if ([string]::IsNullOrWhiteSpace($nombre)) {
            if ($i -eq 1) { Aviso "Hace falta al menos una red."; $i--; continue }
            break
        }
        while ($true) {
            $segura = Read-Host "  Contrasena de '$nombre' (no se ve al escribir; Enter si no tiene)" -AsSecureString
            $puntero = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
            $contrasena = [Runtime.InteropServices.Marshal]::PtrToStringAuto($puntero)
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($puntero)
            if ($contrasena.Length -eq 0 -or ($contrasena.Length -ge 8 -and $contrasena.Length -le 63)) { break }
            Aviso "Las contrasenas de wifi tienen de 8 a 63 caracteres. Escribela otra vez."
        }
        $redes += , @($nombre, $contrasena)
    }

    $lineas = @()
    $lineas += "// Redes wifi de la placa. Lo escribio cargar_invernadero.ps1 y solo esta en esta computadora."
    $lineas += "// No se sube al repositorio ni se comparte. La placa solo se conecta a redes de 2.4 GHz."
    $lineas += ""
    $lineas += "#pragma once"
    $lineas += ""
    $lineas += "struct RedWifi {"
    $lineas += "  const char* nombre;"
    $lineas += "  const char* contrasena;"
    $lineas += "};"
    $lineas += ""
    $lineas += "const RedWifi REDES_WIFI[] = {"
    foreach ($red in $redes) {
        $lineas += ('  {{"{0}", "{1}"}},' -f (TextoParaC $red[0]), (TextoParaC $red[1]))
    }
    $lineas += "};"
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($archivoSecretos, ($lineas -join "`n") + "`n", $utf8)
    Bien "Redes guardadas en $archivoSecretos"
}

$redes = @(RedesGuardadas $archivoSecretos)
if ($redes.Count -gt 0) {
    Info ("Redes guardadas de la vez pasada: " + ($redes -join ", "))
    if (-not $UsarRedesGuardadas -and -not (PreguntarSiNo "Las uso otra vez?")) {
        PedirRedes
    }
} else {
    PedirRedes
}
$redes = @(RedesGuardadas $archivoSecretos)

$canal = CanalDeLaComputadora
$redComputadora = RedDeLaComputadora
if ($redComputadora -and ($redes -contains $redComputadora) -and $canal -and $canal -gt 14) {
    Aviso "Esta computadora esta en '$redComputadora' por 5 GHz (canal $canal). Si esa red solo tiene 5 GHz,"
    Aviso "la placa no la va a ver. Revisa que el hotspot o el modem tenga activada la banda de 2.4 GHz."
}

# ---------- preparar la copia del programa ----------
# se copia el programa a la carpeta de trabajo y se le agrega secretos.h, para no tocar la carpeta del proyecto
$copia = Join-Path $trabajo $nombreCarpeta
New-Item -ItemType Directory -Force $copia | Out-Null
Get-ChildItem (Join-Path $firmware $nombreCarpeta) -File |
    Where-Object { $_.Name -ne "secretos.h" } |
    Copy-Item -Destination $copia -Force
Copy-Item $archivoSecretos (Join-Path $copia "secretos.h") -Force

# ---------- 5. buscar la placa ----------
Titulo 5 "Buscar la placa"

# puertos COM de esta computadora, con lo que se sabe de cada uno
function PuertosSerie {
    $lista = @()
    $dispositivos = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "\((COM\d+)\)" }
    foreach ($dispositivo in $dispositivos) {
        $null = $dispositivo.Name -match "\((COM\d+)\)"
        $com = $Matches[1]
        $tipo = "otro"
        if ($dispositivo.DeviceID -match "VID_303A") { $tipo = "esp32" }
        elseif ($dispositivo.DeviceID -match "VID_(1A86|10C4|0403)") { $tipo = "uart" }
        $lista += [pscustomobject]@{ Puerto = $com; Nombre = $dispositivo.Name; Tipo = $tipo }
    }
    return $lista
}

# una ESP32 conectada pero sin driver aparece sin puerto COM y con error
function PlacaSinDriver {
    $sinDriver = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
        Where-Object { $_.DeviceID -match "VID_(303A|1A86|10C4)" -and $_.ConfigManagerErrorCode -ne 0 }
    return [bool]$sinDriver
}

function ElegirPuerto {
    while ($true) {
        $puertos = @(PuertosSerie)
        $placas = @($puertos | Where-Object { $_.Tipo -eq "esp32" })
        $uart = @($puertos | Where-Object { $_.Tipo -eq "uart" })

        if ($placas.Count -eq 1) {
            Bien "Placa ESP32-S3 encontrada en $($placas[0].Puerto) ($($placas[0].Nombre))"
            return $placas[0].Puerto
        }
        if ($placas.Count -gt 1) {
            $eleccion = Elegir "Hay varias placas ESP32 conectadas. Cual uso?" @($placas | ForEach-Object { "$($_.Puerto): $($_.Nombre)" }) 1
            return $placas[$eleccion - 1].Puerto
        }
        if ($uart.Count -gt 0) {
            Aviso "La placa esta conectada por el USB-C equivocado ($($uart[0].Puerto), $($uart[0].Nombre))."
            Info "Nuestra placa tiene dos USB-C. El programa usa el que dice USB (el USB nativo), no el que dice COM o UART."
            Info "Cambia el cable al otro USB-C de la placa."
            if (-not (PreguntarSiNo "Ya lo cambiaste? (n = usar este puerto de todos modos; carga, pero no se ven los mensajes)")) {
                return $uart[0].Puerto
            }
            continue
        }

        Aviso "No encuentro la placa."
        if (PlacaSinDriver) {
            Aviso "Windows ve un dispositivo USB de la placa pero sin driver."
            Info "Prueba con el otro USB-C de la placa; el que dice USB no necesita driver en Windows 10 y 11."
        }
        Info "Revisa esto:"
        Info "  1. Que la placa este conectada con un cable de DATOS. Muchos cables solo cargan: si con"
        Info "     ese cable el celular no aparece en la computadora, prueba con otro."
        Info "  2. Que el cable vaya al USB-C de la placa que dice USB."
        Info "  3. Que el LED de la placa prenda al conectarla."
        Info "  4. Si nada de eso funciona, pon la placa en modo de carga: deja presionado BOOT,"
        Info "     presiona y suelta RST (o RESET), y despues suelta BOOT."
        $respuesta = Preguntar "Presiona Enter para buscar otra vez, o escribe s para salir" ""
        if ($respuesta -eq "s") { Terminar 1 }
    }
}

if ($Puerto) {
    Bien "Se usa el puerto indicado: $Puerto"
} else {
    $Puerto = ElegirPuerto
}

# ---------- 6. compilar y cargar ----------
Titulo 6 "Compilar y cargar el programa"

# la compilacion se guarda fuera de Drive y de OneDrive; si el nombre de usuario tiene acentos se usa C:\
$carpetaCompilacion = Join-Path $env:TEMP "invernadero_build\$nombreCarpeta"
if ($env:TEMP -match "[^\x00-\x7F]") { $carpetaCompilacion = "$env:SystemDrive\invernadero_build\$nombreCarpeta" }
$salidaCompilacion = Join-Path $trabajo "ultima_compilacion.txt"

Info "Compilando $nombreCarpeta. La primera vez tarda de 2 a 5 minutos; despues es mas rapido."
$argumentos = "compile --fqbn $FQBN --build-path $(Comillas $carpetaCompilacion) $(Comillas $copia)"
$codigo = CorrerConPuntos $cli $argumentos $salidaCompilacion
if ($codigo -ne 0) {
    Falla "No compilo. Estos son los errores:"
    Get-Content $salidaCompilacion | Select-String "error" | Select-Object -First 15 | ForEach-Object { Info $_.Line }
    Info "Texto completo de la compilacion: $salidaCompilacion"
    Terminar 1
}
$tamano = Get-Content $salidaCompilacion | Select-String "Sketch uses|El Sketch usa" | Select-Object -First 1
if ($tamano) { Info $tamano.Line }
Bien "Compilo bien"

$salidaCarga = Join-Path $trabajo "ultima_carga.txt"
$cargado = $false
for ($intento = 1; $intento -le 3 -and -not $cargado; $intento++) {
    Info "Cargando a la placa por $Puerto (tarda de 20 a 60 segundos)..."
    $argumentos = "upload -p $Puerto --fqbn $FQBN --input-dir $(Comillas $carpetaCompilacion) $(Comillas $copia)"
    $codigo = CorrerConPuntos $cli $argumentos $salidaCarga
    if ($codigo -eq 0) { $cargado = $true; break }

    $texto = (Get-Content $salidaCarga) -join "`n"
    Falla "No se pudo cargar (intento $intento de 3)."
    if ($texto -match "FileNotFoundError|cannot find the file|no puede encontrar") {
        Info "El puerto $Puerto ya no existe: la placa se desconecto o cambio de puerto."
        Info "Revisa el cable; al intentar otra vez se busca la placa de nuevo."
    } elseif ($texto -match "Access is denied|Acceso denegado|PermissionError|busy") {
        Info "Otro programa esta usando el puerto $Puerto. Cierra el Arduino IDE (o su monitor serie) y"
        Info "cualquier otra ventana que este leyendo la placa."
    } elseif ($texto -match "No serial data received|Failed to connect|Wrong boot mode|not open port|does not exist") {
        Info "La placa no contesto. Ponla en modo de carga:"
        Info "  deja presionado BOOT, presiona y suelta RST (o RESET), y despues suelta BOOT."
    } else {
        Get-Content $salidaCarga -Tail 8 | ForEach-Object { Info $_ }
    }
    if ($intento -lt 3) {
        Read-Host "  Presiona Enter para intentar otra vez"
        # el numero de puerto puede cambiar al reiniciar la placa
        $placas = @(PuertosSerie | Where-Object { $_.Tipo -eq "esp32" })
        if ($placas.Count -eq 0) {
            $Puerto = ElegirPuerto
        } elseif ($placas.Count -eq 1 -and $placas[0].Puerto -ne $Puerto) {
            $Puerto = $placas[0].Puerto
            Info "La placa ahora esta en $Puerto."
        }
    }
}
if (-not $cargado) {
    Info "Texto completo de la carga: $salidaCarga"
    Terminar 1
}
Bien "Programa cargado"
Info "Si pusiste la placa en modo de carga con BOOT, presiona RST (o RESET) una vez para que arranque."

# se guarda lo que se eligio para proponerlo la proxima vez
@{ programa = $Programa; sensor = $Sensor; puerto = $Puerto } | ConvertTo-Json | Set-Content $archivoPreferencias

# ---------- 7. direccion de la placa y pagina ----------
Titulo 7 "Conexion de la placa al wifi"

# lee el monitor serie unos segundos y busca la IP; los programas escriben su estado cada 1 o 2 segundos
function LeerMonitor($puertoSerie, $segundos) {
    $texto = ""
    $serie = $null
    # despues de cargar, el puerto tarda un poco en aparecer otra vez
    $limiteAbrir = (Get-Date).AddSeconds(15)
    while (-not $serie -and (Get-Date) -lt $limiteAbrir) {
        try {
            $serie = New-Object System.IO.Ports.SerialPort $puertoSerie, 115200
            # la placa solo manda texto cuando la computadora avisa que esta escuchando (DTR)
            $serie.DtrEnable = $true
            $serie.RtsEnable = $true
            $serie.ReadTimeout = 500
            $serie.Open()
        } catch {
            $serie = $null
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $serie) { return "" }
    $fin = (Get-Date).AddSeconds($segundos)
    while ((Get-Date) -lt $fin) {
        try { $texto += $serie.ReadExisting() } catch {}
        if ($texto -match "IP: (\d+\.\d+\.\d+\.\d+)" -and $Matches[1] -ne "0.0.0.0") { break }
        if ($texto -match "http://(\d+\.\d+\.\d+\.\d+)") { break }
        Start-Sleep -Milliseconds 300
    }
    try { $serie.Close() } catch {}
    return $texto
}

function IpDelTexto($texto) {
    if ($texto -match "http://(\d+\.\d+\.\d+\.\d+)") { return $Matches[1] }
    foreach ($coincidencia in [regex]::Matches($texto, "IP: (\d+\.\d+\.\d+\.\d+)")) {
        if ($coincidencia.Groups[1].Value -ne "0.0.0.0") { return $coincidencia.Groups[1].Value }
    }
    return $null
}

function PaginaResponde($direccion) {
    try {
        $respuesta = Invoke-WebRequest "http://$direccion/datos" -UseBasicParsing -TimeoutSec 4
        return ($respuesta.StatusCode -eq 200)
    } catch { return $false }
}

Info "Esperando a que la placa se conecte al wifi (hasta 40 segundos)..."
Info "El LED de la placa parpadea en azul mientras se conecta, queda verde con wifi y rojo sin wifi."
$textoMonitor = LeerMonitor $Puerto 40
$ip = IpDelTexto $textoMonitor

if ($textoMonitor) {
    $ultimas = ($textoMonitor -split "`r?`n" | Where-Object { $_.Trim() }) | Select-Object -Last 4
    Info "Lo ultimo que escribio la placa:"
    foreach ($linea in $ultimas) { Write-Host "    $linea" -ForegroundColor DarkGray }
}

if ($ip) {
    Bien "La placa se conecto al wifi. Su direccion es $ip"
} elseif ($textoMonitor -match "No se encontro ninguna red|Sin wifi") {
    Falla "La placa no encontro ninguna de las redes: $($redes -join ', ')"
    Info "Revisa que el hotspot este prendido, en 2.4 GHz, y que el nombre y la contrasena esten bien escritos"
    Info "(mayusculas y minusculas cuentan). Para cambiarlos, abre otra vez CARGAR_PROGRAMA.bat y contesta"
    Info "que no a 'Las uso otra vez?'."
} elseif (-not $textoMonitor) {
    Aviso "No pude leer los mensajes de la placa. Busco la pagina en la red de todos modos."
}

# si no salio la IP por el monitor, se intenta con el nombre invernadero.local
$direccionLocal = "$NOMBRE_EN_LA_RED.local"
Info "Probando si la pagina responde desde esta computadora..."
$abreLocal = PaginaResponde $direccionLocal
$abreIp = $false
if ($ip) { $abreIp = PaginaResponde $ip }

# revisa si la computadora esta en la misma red que la placa (mismos tres primeros numeros de la IP)
if ($ip -and -not $abreIp) {
    $prefijo = ($ip -split "\.")[0..2] -join "."
    $mismaRed = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -like "$prefijo.*" }
    if (-not $mismaRed) {
        $redComputadora = RedDeLaComputadora
        Aviso "Esta computadora no esta en la misma red que la placa."
        if ($redComputadora) { Info "La computadora esta en '$redComputadora'." }
        Info "Conecta la computadora a la misma red que la placa ($($redes -join ' o ')) y abre la direccion de abajo."
    }
}

Write-Host ""
Write-Host ("*" * 70) -ForegroundColor Green
Write-Host "  PAGINA DEL INVERNADERO" -ForegroundColor Green
if ($abreLocal -or -not $ip) {
    Write-Host "    En la computadora:  http://$direccionLocal" -ForegroundColor White
}
if ($ip) {
    Write-Host "    En la computadora o el celular:  http://$ip" -ForegroundColor White
}
Write-Host "  El celular o la computadora tienen que estar en la misma red que la placa." -ForegroundColor Green
Write-Host "  En el celular conviene usar la direccion con numeros: algunos Android no abren .local" -ForegroundColor Green
Write-Host "  La direccion con numeros puede cambiar cada vez que la placa se conecta; .local no cambia." -ForegroundColor Green
Write-Host ("*" * 70) -ForegroundColor Green

if (-not $SinAbrirPagina) {
    if ($abreLocal) {
        Start-Process "http://$direccionLocal"
        Bien "Abri la pagina en el navegador."
    } elseif ($abreIp) {
        Start-Process "http://$ip"
        Bien "Abri la pagina en el navegador."
    } else {
        Aviso "La pagina todavia no responde desde esta computadora."
        Info "Cuando la computadora este en la misma red que la placa, abre en el navegador la direccion de arriba."
    }
}

# ---------- final ----------
while ($true) {
    $eleccion = Elegir "Que mas quieres hacer?" @(
        "Ver los mensajes de la placa (monitor serie)",
        "Salir"
    ) 2
    if ($eleccion -eq 2) { break }
    Info "Mostrando los mensajes de la placa. Para terminar presiona Ctrl+C (se cierra este programa)."
    if ($Programa -eq "prueba") {
        Info "Aqui puedes escribir una letra y Enter: v ventilador, b bomba, a/m/c ventana, x apagar todo."
    }
    & $cli monitor -p $Puerto --config baudrate=115200
}

Bien "Listo."
Terminar 0
