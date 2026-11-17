// Copia este archivo como secretos.h (en la misma carpeta) y escribe los datos de tus redes.
// secretos.h no se sube al repositorio. La placa solo se conecta a redes de 2.4 GHz.
// Al prender prueba las redes en este orden; si se cae el wifi, va probando la siguiente.

#pragma once

struct RedWifi {
  const char* nombre;
  const char* contrasena;
};

const RedWifi REDES_WIFI[] = {
  {"", ""},   // red de la casa de quien esta probando
  {"", ""},   // hotspot del celular para la reunion y la presentacion
};
