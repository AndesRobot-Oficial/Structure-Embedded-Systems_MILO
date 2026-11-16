# hoverboard_bridge: driver de la base de MILO

Nodo ROS 2 en Python (`base_driver_node`) entre ROS y la placa del hoverboard (firmware
[hoverboard-firmware-hack-FOC](https://github.com/EFeru/hoverboard-firmware-hack-FOC) por
USART, adaptador USB-serie CH340 a 115200 baudios). Reemplaza a ros2_control +
`hoverboard_hardware_interface` + `diff_drive_controller`, con las mismas entradas y salidas.

Es del equipo **Estructura** en el
[contrato de interfaces de AndesRobot](https://alejapinzonf.github.io/Robot_arquitecture_ROS2/#contrato):
hace de `base_driver_node` y, como también lee la seta, de `safety_monitor_node`.

```
cmd_vel (v, w) ──► [topes + parada + batería] ──► [rampa] ──► v,w → RPM de cada rueda
                                                                    │  (matriz de calibración)
                                                                    ▼
                                                   (speed, steer) por serie, 50 veces/s
placa ──► RPM medidas + contadores Hall + batería + temperatura ──► odometría, TF,
                                                                    /joint_states, batería
```

## Cada ciclo (50 Hz)

1. Aplica la parada de emergencia (seta física + pantalla, ver `seta_emergencia/README.md`).
2. Lee los paquetes de la placa (22 bytes): RPM de cada rueda, contadores Hall, batería y
   temperatura.
3. Decide la velocidad pedida: sin `cmd_vel` por 0,5 s → 0; `cmd_vel` con NaN/inf → 0; parada
   de emergencia → 0 al instante, sin rampa; batería agotada → motores bloqueados; batería baja
   → 50 % de velocidad; y nunca más que los topes.
4. Rampa: acelera suave y frena fuerte.
5. Pasa (v, w) a RPM de cada rueda y, con la matriz de calibración, a los `(speed, steer)` del
   firmware; los envía (paquete de 8 bytes).
6. Odometría con los contadores Hall (90 pasos por vuelta de rueda): publica la odometría, la
   TF `odom → base_footprint` y `/joint_states`.

Robustez: sin datos de la placa por 0,5 s → para y avisa; puerto abierto pero mudo 1,5 s → lo
cierra y lo reabre (el CH340 se cuelga con el ruido de los motores); USB desconectado → reintenta
cada 1 s. Si **este nodo** se cuelga, el firmware frena solo al dejar de recibir comandos
(probado el 16-11-2026).

## Interfaces

| Interfaz | Tipo | Dirección | Nota |
|---|---|---|---|
| `cmd_vel` | `geometry_msgs/Twist` | entra | solo `linear.x` y `angular.z` (contrato: `/cmd_vel`) |
| `/base/odom` | `nav_msgs/Odometry` | sale | contrato. `odom → base_footprint`. Con el EKF pasa a `/base/wheel_odom` (ver abajo) |
| `/odom` | `nav_msgs/Odometry` | sale | copia de compatibilidad mientras Navegación pasa a `/base/odom` |
| TF `odom → base_footprint` | | sale | mientras no exista `odom_ekf_node` |
| `/joint_states` | `sensor_msgs/JointState` | sale | posición y velocidad de las ruedas |
| `/base/emergency_stop` | `std_msgs/Bool` | sale | contrato: `true` = robot detenido |
| `/base/emergency_stop/pantalla`, `/seta`, `/rearmar` | | | internas, ver `seta_emergencia/README.md` |
| `/hoverboard/bateria`, `/hoverboard/bateria_pct` | `std_msgs/Float32` | sale | V y %. No están en el contrato |
| `/hoverboard/markers` | `visualization_msgs/Marker` | sale | textos para RViz |

**Cuando exista `odom_ekf_node`** (ruedas + IMU, contrato): en el yaml poner
`odom_topic: /base/wheel_odom`, `publish_tf: false` y `odom_compat_topic: ''`. El EKF publica
entonces `/base/odom` y la TF.

## Parámetros guardados

Todo en `config/hoverboard_bridge.yaml` (probado en el robot el 10 y 11-11-2026; seta y prueba
de fallas el 16-11-2026). Los valores por defecto de `bridge.py` son **los mismos**: el nodo se
comporta igual aunque se lance sin `--params-file`. Si se cambia uno, cambiarlo en los dos.

| Grupo | Parámetro | Valor | Nota |
|---|---|---|---|
| Puerto | `port` | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` | por id: `ttyUSBx` cambia con el orden de conexión |
| Geometría | `wheel_radius` | 0,08255 m | rueda de 6,5" |
| | `wheel_separation` | **0,346 m** | efectiva, calibrada con el lidar (1 vuelta en el lugar): la física es 0,32 m (CAD/URDF 0,3604) y las ruedas patinan al girar |
| | `ticks_per_rev` | 90 | medido: 90,6 / 90,0 |
| Topes | `max_linear` | 1,67 m/s | 6 km/h |
| | `max_angular` | 0,6 rad/s | ~34°/s |
| | `max_command` | 400 | de 1000 del firmware |
| Rampas | `linear_accel` / `linear_decel` | 0,25 / 1,0 m/s² | 0 → 6 km/h en ~6,7 s; 6 km/h → 0 en ~1,7 s |
| | `angular_accel` / `angular_decel` | 0,5 / 1,2 rad/s² | |
| Control | `kp`, `ki` | 0, 0 | PI apagado: el firmware ya controla la velocidad (con PI temblaba al frenar) |
| Seguridad | `cmd_timeout` / `feedback_timeout` / `stall_reopen` | 0,5 / 0,5 / 1,5 s | |
| | `rate` | 50 Hz | |
| Odometría | `odom_topic` / `odom_compat_topic` / `publish_tf` | `/base/odom` / `/odom` / true | ver "Interfaces" |
| Batería 10S | `bat_warn` | 34,0 V | aviso + velocidad al 50 % (`bat_warn_speed`) |
| | `bat_cutoff` / `bat_resume` | 32,0 / 35,0 V | motores bloqueados / se desbloquean al cargar |
| | `bat_overvoltage` | 42,3 V | aviso de sobrecarga |
| | `bat_filter_tau` | 5 s | filtro del voltaje (ignora caídas al acelerar) |
| Seta | `estop_gpio_chip` / `estop_gpio_line` | gpiochip0 / 144 | pin 7; línea < 0 la desactiva |
| | `estop_gpio_period` / `estop_gpio_fail` | 0,05 / 1,0 s | sin poder leer el pin 1 s → se toma como presionada |

Calibración de ruedas, `config/hoverboard_calibracion.yaml` (10-11-2026, ruedas en el aire):
`mix` (RPM de cada rueda por unidad de `speed`/`steer`; `speed` positivo = **atrás**), signos
`rpm_sign`/`tick_sign`, y `swap_wheels: true` (la rueda "izquierda" del firmware es la derecha
del robot). Se regenera con `ros2 run hoverboard_bridge calibrar --port <puerto>` (**ruedas en
el aire**) y se copia aquí desde `~/.ros/hoverboard_calibracion.yaml`; el nodo lanzado sin
`calibration_file` lee la de `~/.ros`.

## Uso

Es un paquete ROS 2 (`hoverboard_bridge`): se clona o copia en `~/ros2_ws/src` y se compila.

```bash
cd ~/ros2_ws && colcon build --packages-select hoverboard_bridge && source install/setup.bash
ros2 run hoverboard_bridge bridge --ros-args \
  --params-file $(ros2 pkg prefix hoverboard_bridge)/share/hoverboard_bridge/config/hoverboard_bridge.yaml
```

En el robot lo lanzan los launch del robot de Navegación (`robot.launch.py driver:=bridge`), con
este yaml y la calibración del paquete. Necesita `gpioget` (`sudo apt install gpiod`) para la
seta; sin él, la seta se toma como presionada y el robot no se mueve (falla segura).

Pruebas de la parada de emergencia (ruedas en el aire): `seta_emergencia/pruebas/`.
