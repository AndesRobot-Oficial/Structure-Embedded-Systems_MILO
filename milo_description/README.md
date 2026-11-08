# milo_description

URDF del robot con masas calculadas: paquete ROS 2 (`andesrobot_description`) con el modelo URDF/xacro de MILO, exportado del CAD de Fusion 360.

- Modelo principal: [`urdf/andesrobot.urdf.xacro`](urdf/andesrobot.urdf.xacro)
- Mallas del CAD: [`meshes/`](meshes/)
- Frames, medidas y argumentos del xacro: [`docs/ROBOT.md`](docs/ROBOT.md)
- Masas: rev. 1, de las piezas reales (perfiles, impresiones por vóxeles, fichas); total 36.8 kg; ver [`docs/ROBOT.md`](docs/ROBOT.md)

El modelo incluye la estructura de perfiles V-slot (base, collar de la columna y caja trasera), la base diferencial, la columna con el elevador, la electrónica, las carcasas, la cabeza (RealSense D435 + pantalla), el RPLIDAR C1, la IMU, el brazo (pose plegada por defecto), la pinza y la cámara Orbbec de la muñeca.

## Visualizar

```bash
cd ~/ros2_ws/src
git clone https://github.com/AndesRobot-Oficial/Structure-Embedded-Systems_MILO.git
cd ~/ros2_ws
colcon build --packages-select andesrobot_description
source install/setup.bash
ros2 launch andesrobot_description display.launch.py
```
