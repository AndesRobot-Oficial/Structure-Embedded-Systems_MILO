# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]
### Agregado
- `milo_base_driver`: driver ROS 2 de la base (paquete `hoverboard_bridge`, nodo `base_driver_node`) para la placa
  del hoverboard con firmware hack-FOC: `cmd_vel` → ruedas, odometría (`/base/odom` + TF; copia en `/odom`),
  batería y parámetros probados en el robot (10/11-11-2026). Interfaces según el contrato de AndesRobot.
- Seta de emergencia física (pin 7 del Jetson, pull-down por overlay): la lee el driver y publica
  `/base/emergency_stop`; al soltarla, el robot sigue detenido hasta rearmarla (`/base/emergency_stop/rearmar`).
  Overlay, script de prueba y pruebas de fallas en `milo_base_driver/seta_emergencia/`.
### Corregido
- Driver: un `cmd_vel` con NaN se convertía en velocidad máxima hacia adelante; ahora NaN/inf = parar.
- Driver: los valores por defecto del código ahora son los del yaml probado.
### Cambiado
- CAD de Fusion actualizado al URDF rev. 1 y marcado como listo: bastidor V-slot, escuadras, placas, columna 6060,
  CAD de fabricante (ruedas, placa del hoverboard, Jetson, Arduino, TB6600, regulador, RPLIDAR C1), baterías, IMU,
  rueda loca, monitor y Orbbec; brazo sin base redonda y cabeza contra la columna; materiales y masas del URDF;
  articulaciones del URDF. Nuevo `cad/milo_ensamblaje.f3z` y STEP reexportado.
- URDF marcado como listo. Ruedas: el origen de cada joint pasa al centro de la llanta; `wheel_separation`
  (0,3604 m, igual que la navegación), `wheel_radius` y `wheel_width` como propiedades del xacro.
- `display.launch.py` / `rsp.launch.py`: argumento `gripper_camera` (por defecto activo en `display`).
- `milo_description` rev. 1: fusión del modelo del repo, de la estructura y masas de `milo_teleop` y del brazo/pinza/cámara
  del equipo garra (`milo_ws`, rama `brazo`). Estructura V-slot 3030/6060 con collar de la columna, escuadras, electrónica,
  carcasas y cabeza; brazo sin base redonda, montado en la placa del carro; pose plegada con `lock_arm:=true`;
  masas de las piezas reales (36.8 kg, sin lastre); args `arm_control` y `gripper_camera`; nuevo `gripper_tcp`.
- README: dimensiones (56 × 50 × 161 cm), peso (36,8 kg) y estado del URDF y del CAD.
- BOM: perfilería (10,04 m de 3030 + 1,5 m de 6060, con el collar de la columna), placas, SK16, rueda loca y tornillería
  de la estructura (74 escuadras); configuración de los TB6600 (800 pasos/rev) y motor propuesto para J3.
- CAD: lista de cambios del URDF rev. 1 que faltan en el modelo de Fusion.
### Agregado
- Estructura inicial del repositorio, plantillas de BOM, cableado y presupuesto de potencia.
- `milo_description`: paquete `andesrobot_description` del CAD de Fusion 360, con masas estimadas (rev. 0).
- Plano eléctrico rev. 1.0, tabla de cableado generada, presupuesto de potencia y revisión del plano.
