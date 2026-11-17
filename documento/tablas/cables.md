<!-- generado por documento/graficas/alambrado.py; no editar a mano -->

### Piezas sobre la protoboard

| Pieza | Dónde va |
|---|---|
| ESP32-S3 | Pines de 3V3 a GND en i42 a i63; la otra fila en a42 a a63. El USB queda hacia la fila 63. |
| Resistencia 1 kΩ (café, negro, rojo) | h3 y h7. Da igual hacia qué lado. |
| Transistor TIP120 | f7 (B), f8 (C) y f9 (E). La cara con letras mira hacia los rieles de abajo. |
| Diodo 1N4007 | i8 y i12. La franja gris va en i12. |
| Resistencia 1 kΩ (café, negro, rojo) | h15 y h19. Da igual hacia qué lado. |
| Transistor TIP120 | f19 (B), f20 (C) y f21 (E). La cara con letras mira hacia los rieles de abajo. |
| Diodo 1N4007 | i20 e i24. La franja gris va en i24. |
| Capacitor 1000 µF | Pata negativa (franja con signos −) en el riel azul, fila 29; la otra en el riel rojo, fila 29. Se dobla para que quede acostado fuera de la protoboard. |

### Cables (en el orden de armado, por bloque)

| # | Color | Desde | Hasta | Jumper | Nota |
|---|---|---|---|---|---|
| 1 | Rojo | terminal + del adaptador del eliminador | riel rojo (+), fila 2 | macho-macho, un extremo atornillado en el adaptador |  |
| 2 | Negro | terminal − del adaptador del eliminador | riel azul (−), fila 4 | macho-macho, un extremo atornillado en el adaptador |  |
| 3 | Negro | riel azul (−), fila 30 | riel azul (−), fila 33 | macho-macho corto | puente entre las dos mitades del riel azul |
| 4 | Negro | hoyo j63 (GND de la ESP32) | riel azul (−), fila 61 | macho-macho corto | tierra de la ESP32 con la del eliminador |
| 5 | Naranja | DHT22, pin + | hoyo j42 (3V3 de la ESP32) | hembra-macho 30 cm |  |
| 6 | Amarillo | DHT22, pin out | hoyo j45 (GPIO 4 de la ESP32) | hembra-macho 30 cm |  |
| 7 | Negro | DHT22, pin − | riel azul (−), fila 40 | hembra-macho 30 cm |  |
| 8 | Naranja | sensor de suelo, pin VCC | hoyo j43 (3V3 de la ESP32) | hembra-macho 30 cm (o el cable del sensor) |  |
| 9 | Verde | sensor de suelo, pin AOUT | hoyo j46 (GPIO 5 de la ESP32) | hembra-macho 30 cm (o el cable del sensor) |  |
| 10 | Negro | sensor de suelo, pin GND | riel azul (−), fila 53 | hembra-macho 30 cm (o el cable del sensor) |  |
| 11 | Azul | hoyo j47 (GPIO 6 de la ESP32) | hoyo j3 | macho-macho 20 cm | señal del ventilador |
| 12 | Negro | hoyo j9 | riel azul (−), fila 9 | macho-macho corto | emisor del transistor a tierra |
| 13 | Rojo | hoyo j12 | riel rojo (+), fila 11 | macho-macho corto | 5 V al ventilador |
| 14 | Negro | regleta del ventilador, junto al cable negro | hoyo j8 | macho-macho, un extremo atornillado en la regleta | cable negro del ventilador |
| 15 | Rojo | regleta del ventilador, junto al cable rojo | hoyo h12 | macho-macho, un extremo atornillado en la regleta | cable rojo del ventilador |
| 16 | Negro | conector del servo, cable café | riel azul (−), fila 26 | macho-macho, entra en el conector del servo | cable café del servo |
| 17 | Rojo | conector del servo, cable rojo | riel rojo (+), fila 27 | macho-macho, entra en el conector del servo | cable rojo del servo |
| 18 | Blanco | conector del servo, cable naranja | hoyo j49 (GPIO 15 de la ESP32) | macho-macho, entra en el conector del servo | cable naranja del servo (señal) |
| 19 | Morado | hoyo j48 (GPIO 7 de la ESP32) | hoyo j15 | macho-macho 20 cm | señal de la bomba |
| 20 | Negro | hoyo j21 | riel azul (−), fila 21 | macho-macho corto | emisor del transistor a tierra |
| 21 | Rojo | hoyo j24 | riel rojo (+), fila 23 | macho-macho corto | 5 V a la bomba |
| 22 | Negro | regleta de la bomba, junto al cable negro | hoyo j20 | macho-macho, un extremo atornillado en la regleta | cable negro de la bomba |
| 23 | Rojo | regleta de la bomba, junto al cable rojo | hoyo h24 | macho-macho, un extremo atornillado en la regleta | cable rojo de la bomba |
