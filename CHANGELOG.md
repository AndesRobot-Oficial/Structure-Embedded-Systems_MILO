# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]
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
