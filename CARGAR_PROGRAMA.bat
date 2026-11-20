@echo off
rem Carga el programa del invernadero a la ESP32-S3. Se abre con doble clic.
rem Todo lo hace herramientas\cargar_invernadero.ps1; este archivo solo lo abre con los permisos necesarios.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0herramientas\cargar_invernadero.ps1"
