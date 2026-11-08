# MILO — Estructura y Sistemas Embebidos

Repositorio del equipo de **base** de [AndesRobot](https://github.com/AndesRobot-Oficial) para el robot **MILO** (RoboCup@Home 2027).
Contiene el modelo CAD, el sistema eléctrico de la base y el modelo URDF para ROS 2.

## Especificaciones

| Parámetro | Valor |
|---|---|
| Dimensiones (L × A × H) | 56 × 50 × 161 cm (base 50 × 50; el largo incluye el RPLIDAR, que sobresale al frente; alto hasta la tapa de la columna, brazo plegado) |
| Peso | ~36,8 kg (URDF rev. 1, con masas de las piezas reales; faltan cables, tornillería y algunos componentes) |
| Tipo de tracción | Diferencial, 2 motores BLDC de hoverboard 6,5" (control FOC) |
| Velocidad máxima | 6 km/h |
| Batería | 2× Li-ion 10S2P 36 V · 4,4 Ah · 158 Wh (316 Wh en total) |
| Autonomía estimada | ~1,4 h, estimación preliminar (ver [presupuesto de potencia](electrica/presupuesto_potencia.csv)) |
| Computador principal | NVIDIA Jetson Orin Nano Dev Kit + Arduino Mega 2560 |
| Sensores | RPLIDAR C1, Orbbec Gemini Plus, IMU HFI-B9, IMU MPU-9250, Hiwonder WonderMV |
| Pantallas | Monitor MUCAI N116A 11,6" y Victron GX Touch 50 (no necesariamente serán estos modelos) |
| Software | ROS 2 Humble · Ubuntu 22.04 |
| CAD | Autodesk Fusion 360 |

## Estado actual

| Área | Estado |
|---|---|
| Diseño 3D | 🟡 El URDF rev. 1 tiene cambios que aún no están en el CAD de Fusion ([ver](cad/README.md#cambios-que-faltan-en-el-cad)) |
| Plano eléctrico | 🟡 Rev. 2.0 lista, pendientes las medidas de seguridad ([revisión](electrica/revision_plano.md)) |
| URDF | 🟡 Rev. 1: estructura completa, brazo plegado, masas de piezas reales; faltan componentes del plano eléctrico ([pendientes](milo_description/docs/ROBOT.md#pendiente-antes-del-robot-real)) |
| BOM | 🟡 Componentes eléctricos, perfilería y tornillería de la estructura listos; falta la tornillería de las carcasas |
| Fabricación | 🟡 Pendiente la carcasa exterior |

🔲 Pendiente · 🟡 En progreso · ✅ Listo

## Estructura del repositorio

```
.
├── bom/              # Lista de componentes
├── cad/              # Archivo CAD del robot
├── electrica/        # Diagrama de conexiones
└── milo_description/ # URDF del robot (rev. 1) con masas de las piezas reales
```

## Uso rápido del URDF

Requiere ROS 2 Humble.

```bash
cd ~/ros2_ws/src
git clone https://github.com/AndesRobot-Oficial/Structure-Embedded-Systems_MILO.git
cd ~/ros2_ws
colcon build --packages-select andesrobot_description
source install/setup.bash
ros2 launch andesrobot_description display.launch.py
```

## Contacto

Base de MILO: [@Dlpez](https://github.com/Dlpez)
