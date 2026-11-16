#!/bin/bash
# Prueba de la parada de emergencia con las ruedas reales: SOLO el driver del hoverboard + teleop
# por teclado directo a /cmd_vel (sin lidar ni filtro de seguridad). RUEDAS EN EL AIRE.
# Abre dos ventanas:
#   "Driver Milo"  -> hoverboard_bridge (lee la seta física; sus mensajes dicen cuándo frena)
#   "Teleop Milo"  -> teclado: mantener i (adelante) / , (atrás) / j l (girar), k parar
# Prueba: mover las ruedas, presionar la seta -> deben frenar al instante; soltarla -> siguen
# frenadas hasta pulsar LIBERAR PARADA en el Panel de Milo.
# Cerrar: Ctrl+C en cada ventana (o "Detener TODO" en el panel).
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
# Mismo entorno ROS que el panel (milo_panel.sh), para que el panel vea al driver.
export ROS_DOMAIN_ID=7
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/.ros/fastdds_usb.xml
export DISPLAY=${DISPLAY:-:0}
HOVER=/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
CFG=$HOME/ros2_ws/install/hoverboard_bridge/share/hoverboard_bridge/config/hoverboard_bridge.yaml

[ -e "$HOVER" ] || { echo "No está conectado el hoverboard ($HOVER)"; exit 1; }
if pgrep -f "hoverboard_bridge/bridge" > /dev/null; then
  echo "Ya hay un driver del hoverboard corriendo: ciérralo primero (Detener TODO en el panel)."
  exit 1
fi

gnome-terminal --title="Driver Milo" -- bash -c \
  "ros2 run hoverboard_bridge bridge --ros-args --params-file $CFG -p port:=$HOVER; \
   echo; read -p 'Driver cerrado. Enter para cerrar la ventana.'"
sleep 2
gnome-terminal --title="Teleop Milo" -- bash -c \
  "echo 'TELEOP DIRECTO A /cmd_vel (sin filtro de seguridad). RUEDAS EN EL AIRE.'; \
   echo 'Mantener i adelante | , atrás | j/l girar | k parar | q/z velocidad'; \
   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
     -p speed:=0.15 -p turn:=0.3"
