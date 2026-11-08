# Lista de materiales (BOM)

Lista de componentes de MILO: todo lo que hay que comprar o fabricar.

## Componentes eléctricos

### Energía

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Batería Li-ion 10S2P 36 V · 4,4 Ah · 158 Wh | BMS 20 A continuos / 30 A pico | 2 | Carga a 42 V |
| Conversor DC-DC 42 V → 24 V, 20 A | UENPO (entrada 30–75 V) | 1 | |
| Conversor DC-DC 24 V → 12 V, 20 A | Kuongshun (entrada 6–40 V) | 1 | 15 A continuos |
| Conversor DC-DC 24 V → 6,6 V, 300 W | Kuongshun (entrada 7–32 V) | 1 | Hasta 8 A |

### Seguridad

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Seta de emergencia | 2 contactos NC | 1 | |

### Tracción

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Placa controladora de hoverboard | STM32, firmware FOC (EFeru) | 1 | |
| Pulsador de encendido | Original de la placa | 1 | |
| Rueda con motor BLDC en buje 6,5" | 36 V · ~350 W | 2 | |

### Control

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Computador principal | NVIDIA Jetson Orin Nano Dev Kit | 1 | Entrada 9–20 V |
| Microcontrolador | Arduino Mega 2560 | 1 | |
| Adaptador USB a TTL | CH340G | 1 | Puente 5 V / 3,3 V |
| Hub USB 3.0 alimentado, 7 puertos | Entrada 12 V | 1 | |

### Sensores

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Cámara de profundidad | Orbbec Gemini Plus | 1 | |
| LiDAR | Slamtec RPLIDAR C1 | 1 | |
| IMU 9 ejes USB | Handsfree HFI-B9 | 1 | |
| IMU 9 ejes I2C | MPU-9250 (módulo GY-9250) | 1 | |
| Cámara de visión IA | Hiwonder WonderMV (K210) | 1 | |

### Pantallas

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Monitor 11,6" | MUCAI N116A | 1 | Modelo no definitivo |
| Pantalla táctil 5" | Victron GX Touch 50 | 1 | Modelo no definitivo |
| Hub DisplayPort MST (1× DP → 2× HDMI) | _por elegir_ | 1 | |

### Actuadores

| Componente | Modelo / N° de parte | Cant. | Notas |
|---|---|:-:|---|
| Driver paso a paso (9–42 V · 0,5–4,0 A) | TB6600 | 7 | Configurados a 800 pasos/rev (1/4 de micropaso); reductores EBA de 38,4:1 → 30 720 pasos por vuelta de articulación |
| Motor NEMA 23, 1,26 N·m · 2,8 A/fase | StepperOnline 23HS22-2804S1 | 3 | J1, J3 y elevador. **Propuesta para J3:** NEMA 23 2,0 N·m · 2,8 A, 76 mm, eje 6,35 mm (57HS76-3004A635-D21, ~1,1 kg): con 24 V y J3 limitado a ~0,6 rad/s da ~2 kg en la pinza con margen 2× (el actual, ~0,6 kg) |
| Motor NEMA 23, 2,9 N·m · 3,0 A/fase | 57HS112-3004 | 1 | |
| Motor NEMA 17, ~0,45 N·m · ~1,5 A/fase | _por confirmar_ | 3 | Confirmar corriente en la etiqueta |
| Servo digital 20 kg·cm a 6,6 V | Power HD LF-20MG | 1 | |

## Perfilería

Perfil V-slot de aluminio (0,835 kg/m el 3030, ranura 8). Largos de corte sacados del URDF rev. 1
([`milo_description`](../milo_description/README.md)). Total: **10,04 m de 3030 + 1,5 m de 6060**.

### Base (500 × 500 × 230 mm)

| Componente | Medida | Cant. | Notas |
|---|---|:-:|---|
| Perfil V-slot 3030 | 440 mm | 12 | Anillos inferior y superior (8), travesaños inferiores largos (2), collar superior de la columna (2, de lado a lado) |
| Perfil V-slot 3030 | 230 mm | 4 | Verticales de las esquinas |
| Perfil V-slot 3030 | 173 mm | 3 | Travesaños inferiores cortos (2) y travesaño delantero del collar inferior (1) |
| Perfil V-slot 3030 | 60 mm | 4 | Topes laterales de la columna, collar inferior (2) y superior (2) |

El **collar** son los 7 perfiles que encierran la columna 6060 por sus 4 caras en el nivel inferior y en el superior de la base.

### Columna y caja trasera

| Componente | Medida | Cant. | Notas |
|---|---|:-:|---|
| Perfil V-slot 6060 | 1500 mm | 1 | Columna del elevador |
| Tapa plástica para 6060 | — | 1 | Extremo superior |
| Perfil V-slot 3030 | 500 mm | 4 | Verticales de la caja trasera (50 cm de alto, sobre la base) |
| Perfil V-slot 3030 | 240 mm | 2 | Travesaños traseros, abajo y arriba |
| Perfil V-slot 3030 | 90 mm | 4 | Travesaños delanteros de la caja, de la columna a las verticales |
| Perfil V-slot 3030 | 60 mm | 4 | Laterales de la caja, abajo y arriba |

### Placas y estructura

| Componente | Medida | Cant. | Notas |
|---|---|:-:|---|
| Plancha de acrílico | 3 mm, 500 × 500 mm | 1 | Piso interior sobre los perfiles de abajo; muescas en las esquinas y agujero para la columna |
| Placas de carcasa PAI | 2 mm, 0,793 m² | — | Base (lados y tapa; abajo abierta para las ruedas) |
| Placas de carcasa PAI | 2 mm, 0,431 m² | — | Caja trasera |
| Soporte de eje SK16 | Ø16 mm | 2 | Eje de cada rueda motriz, bajo el travesaño inferior largo |
| Rueda loca giratoria 3" con freno | Alto 100 mm, rueda PU Ø75 × 32 | 1 | Más una suplencia de 9,6 mm |

## Tornillería

| Componente | Medida | Cant. | Notas |
|---|---|:-:|---|
| Escuadra 90° para perfil 3030 | 28 × 28 mm | 74 | Posiciones en el URDF (`herrajes_link`) |
| Tornillo + tuerca en T para las escuadras | M6 × 12 + tuerca T M6 ranura 8 | 148 + 148 | 2 por escuadra (medida típica para 3030: confirmar con la escuadra comprada) |
| Anclaje interno 3030 | — | 6 | Uniones del collar inferior, donde no caben escuadras |
| Tornillo + tuerca en T para los SK16 | M5 + tuerca T M5 ranura 8 | 4 + 4 | |
| Tornillería de la rueda loca | según placa 62 × 93 mm (agujeros 45 × 75) | 4 | |
