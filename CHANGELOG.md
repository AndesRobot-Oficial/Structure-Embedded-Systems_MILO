# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]
### Cambiado
- `milo_description` rev. 1: fusión del modelo del repo, de la estructura y masas de `milo_teleop` y del brazo/pinza/cámara
  del equipo garra (`milo_ws`, rama `brazo`). Estructura V-slot 3030/6060 con collar de la columna, escuadras, electrónica,
  carcasas y cabeza; brazo sin base redonda, montado en la placa del carro; pose plegada con `lock_arm:=true`;
  masas de las piezas reales (36.8 kg, sin lastre); args `arm_control` y `gripper_camera`; nuevo `gripper_tcp`.
### Agregado
- Estructura inicial del repositorio, plantillas de BOM, cableado y presupuesto de potencia.
- `milo_description`: paquete `andesrobot_description` del CAD de Fusion 360, con masas estimadas (rev. 0).
- Plano eléctrico rev. 1.0, tabla de cableado generada, presupuesto de potencia y revisión del plano.
