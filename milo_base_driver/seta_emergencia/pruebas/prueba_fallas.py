#!/usr/bin/env python3
"""Prueba de fallas de la parada de emergencia de Milo. RUEDAS EN EL AIRE.

Simula un ROS "loco": publica en /cmd_vel (lo que escucha el driver lanzado con
prueba_emergencia.sh o "Solo robot") comandos absurdos que cambian cada 0.4 s:
velocidades de 1000 m/s, giros de 1000 rad/s, NaN, infinito, marcha atrás y adelante
alternadas, al azar... El driver los recorta a sus topes (1.67 m/s, 0.6 rad/s), así que en el
aire las ruedas se aceleran y frenan solas. Al presionar la seta deben frenar en seco.

Uso:
  prueba_fallas.py              # comandos locos a 50 Hz
  prueba_fallas.py --liberar    # además publica /base/emergency_stop/pantalla False a
                                # 10 Hz (un nodo que intenta "liberar" la parada siempre)
Imprime una línea por cambio de estado y cada 2 s: parada, seta y velocidad de cada rueda
(medida por la hoverboard, en /joint_states). Ctrl+C para salir (deja de publicar: el driver
para solo por cmd_timeout).
"""
import random
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

LOCOS = [  # (v [m/s], w [rad/s], nombre)
    (1000.0, 0.0, 'adelante 1000 m/s'),
    (-1000.0, 0.0, 'atrás 1000 m/s'),
    (0.0, 1000.0, 'giro 1000 rad/s'),
    (float('nan'), float('nan'), 'NaN'),
    (float('inf'), float('-inf'), 'infinito'),
    (5.0, -5.0, 'adelante + giro'),
    (None, None, 'al azar'),
]


class Loco(Node):
    def __init__(self, liberar):
        super().__init__('prueba_fallas')
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.estop_pub = (self.create_publisher(Bool, '/base/emergency_stop/pantalla', latched)
                          if liberar else None)
        self.estado = self.seta = None
        self.rueda = None            # [izq, der] rad/s
        self.t_js = 0.0
        self.t_seta_on = None        # cuándo se presionó la seta (para medir el frenado)
        self.cmd = LOCOS[0]
        self.ultimo = ''
        self.t_print = 0.0
        self.create_subscription(Bool, '/base/emergency_stop', self.on_estado, latched)
        self.create_subscription(Bool, '/base/emergency_stop/seta', self.on_seta, latched)
        self.create_subscription(JointState, '/joint_states', self.on_js, 10)
        self.create_timer(0.02, self.publicar)
        self.create_timer(0.4, self.cambiar)
        self.create_timer(0.1, self.mostrar)
        if liberar:
            self.create_timer(0.1, lambda: self.estop_pub.publish(Bool(data=False)))

    def on_estado(self, m):
        self.estado = m.data

    def on_seta(self, m):
        if m.data and not self.seta:
            self.t_seta_on = time.time()
        self.seta = m.data

    def on_js(self, m):
        if len(m.velocity) >= 2:
            self.rueda = list(m.velocity[:2])
            self.t_js = time.time()

    def cambiar(self):
        self.cmd = random.choice(LOCOS)

    def publicar(self):
        v, w, _ = self.cmd
        if v is None:
            v, w = random.uniform(-50, 50), random.uniform(-50, 50)
        t = Twist()
        t.linear.x, t.angular.z = v, w
        self.cmd_pub.publish(t)

    def mostrar(self):
        ahora = time.time()
        if ahora - self.t_js > 1.0:
            ruedas = 'SIN DATOS DEL DRIVER'
            girando = None
        else:
            ruedas = f'ruedas {self.rueda[0]:+6.1f} {self.rueda[1]:+6.1f} rad/s'
            girando = max(abs(x) for x in self.rueda) > 0.3
        txt_estado = {True: 'PARADA', False: 'libre', None: '?'}[self.estado]
        txt_seta = {True: 'PRESIONADA', False: 'suelta', None: '?'}[self.seta]
        txt_ruedas = {True: 'girando', False: 'quietas', None: '?'}[girando]
        linea = f'parada={txt_estado} seta={txt_seta} {txt_ruedas}'
        extra = ''
        if self.t_seta_on is not None and girando is False:
            extra = f'  -> quietas {ahora - self.t_seta_on:.2f} s después de presionar la seta'
            self.t_seta_on = None
        if linea != self.ultimo or extra or ahora - self.t_print > 2.0:
            print(f'{time.strftime("%H:%M:%S")} {linea} | {ruedas} | mando: {self.cmd[2]}'
                  f'{extra}', flush=True)
            self.ultimo, self.t_print = linea, ahora


def main():
    rclpy.init()
    n = Loco('--liberar' in sys.argv)
    print('PRUEBA DE FALLAS: comandos locos a /cmd_vel'
          + (' + /base/emergency_stop/pantalla False a 10 Hz' if n.estop_pub else '')
          + '. RUEDAS EN EL AIRE.',
          flush=True)
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        n.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
