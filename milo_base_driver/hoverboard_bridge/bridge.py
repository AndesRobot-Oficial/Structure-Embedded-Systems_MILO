"""Puente ROS 2 <-> hoverboard (firmware hack-FOC por USART), en Python.

Reemplaza a ros2_control + hoverboard_hardware_interface + diff_drive_controller (ese driver
C++ no está en el repo). Mismos topics que diff_drive_controller, así el resto no cambia:

Es el base_driver_node de MILO en el contrato de interfaces de AndesRobot (equipo Estructura),
y hace también de safety_monitor_node (lee la seta y publica /base/emergency_stop).

Entrada:  cmd_vel (geometry_msgs/Twist): v [m/s] y w [rad/s] del robot
Salidas:  odometría (nav_msgs/Odometry) en odom_topic (/base/odom; copia en /odom mientras
          Navegación se cambia), TF odom -> base_footprint, /joint_states (ruedas),
          /hoverboard/bateria (std_msgs/Float32, volts)

Cómo controla: el firmware recibe (speed, steer) y devuelve las RPM y los contadores Hall de cada
rueda. Con la calibración (ros2 run hoverboard_bridge calibrar) se sabe cómo (speed, steer) mueve
cada rueda; el puente pide las RPM de cada rueda (hay un PI opcional sobre las RPM medidas,
apagado en Milo: kp = ki = 0, el firmware ya controla la velocidad).
Odometría: con los contadores Hall (ticks_per_rev por vuelta de rueda).
Seguridad: sin cmd_vel por cmd_timeout -> para; sin feedback del hoverboard -> para y avisa;
cmd_vel con NaN/inf -> para. Si este nodo se cuelga, el firmware frena solo al dejar de recibir
comandos (probado 16-11-2026 congelando el driver con las ruedas a 0.3 m/s).
Los valores por defecto de los parámetros son los de config/hoverboard_bridge.yaml (los probados
en Milo), así el nodo se comporta igual aunque se lance sin --params-file.
Batería (10S 18650, 36 V nominal, 12.5 Ah): voltaje filtrado (para que la caída al acelerar no
dispare nada). Bajo bat_warn -> velocidad limitada; bajo bat_cutoff -> motores bloqueados hasta
que suba sobre bat_resume (cargar). % según la curva de descarga de una celda 18650.
Publica /hoverboard/bateria_pct (0-100).
Parada de emergencia, dos fuentes:
  - Pantalla: /base/emergency_stop/pantalla (std_msgs/Bool, latcheado). True -> parada;
    False -> la libera.
  - Seta física: botón NC en el pin 7 del header (gpiochip0 línea 144, leído con gpioget en un
    hilo aparte). Pin en 0 = presionada o cable cortado -> parada. Al soltarla el robot NO
    arranca solo: queda "enganchado" hasta que se llame al servicio
    /base/emergency_stop/rearmar (std_srvs/Trigger; lo llama el botón LIBERAR del panel), como
    pide la norma de paradas de emergencia (ISO 13850). Publicar pantalla False NO rearma la
    seta: así un nodo que lo publique por error (o en bucle) no puede hacer arrancar el robot.
  Con cualquiera activa: ruedas a 0 al instante (sin rampa) e ignora cmd_vel.
  Publica /base/emergency_stop (parada efectiva; el topic del contrato) y
  /base/emergency_stop/seta (seta presionada), los dos en cada cambio y a 5 Hz (el panel lo usa
  también para saber que el driver está vivo).
  Conexión, overlay del pin y pruebas: seta_emergencia/README.md.
"""
import math
import os
import subprocess
import threading
import time

import numpy as np
import rclpy
import serial
import yaml
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Bool, Float32
from std_srvs.srv import Trigger
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker

from hoverboard_bridge.protocolo import FeedbackParser, delta_int16, make_command


class HoverboardBridge(Node):
    def __init__(self):
        # Nombre del contrato de AndesRobot (Estructura): base_driver_node.
        super().__init__('base_driver_node')
        p = self.declare_parameter
        # Por id y no /dev/ttyUSBx: el número cambia según el orden en que se enchufan (el lidar
        # también es ttyUSB). Este es el adaptador CH340 de la hoverboard de Milo.
        p('port', '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0')
        p('baud_rate', 115200)
        p('calibration_file', os.path.expanduser('~/.ros/hoverboard_calibracion.yaml'))
        p('wheel_radius', 0.08255)          # [m] rueda de hoverboard 6.5"
        # [m] separación EFECTIVA para la odometría. Física (centro a centro de los neumáticos,
        # medida): 0.32 m. Calibrada con el lidar (ICP) girando 1 vuelta en el lugar el 10-11-2026:
        # odom 372.5° vs real 344.7° con 0.32 -> 0.32 * 1.081 = 0.346 (las ruedas patinan al girar).
        p('wheel_separation', 0.346)
        p('ticks_per_rev', 90.0)            # pasos Hall por vuelta de rueda
        p('max_command', 400)               # tope de |speed| y |steer| enviados (de 1000)
        p('max_linear', 1.67)               # [m/s] tope duro (6 km/h), venga de donde venga
        p('max_angular', 0.6)               # [rad/s] ~34°/s (era 0.4; 11-11-2026)
        # Rampas: acelerar suave (sin "despegue") y frenar más fuerte (para no pasarse).
        p('linear_accel', 0.25)             # [m/s²] 0 -> 6 km/h en ~6.7 s (0.5 era brusco)
        p('linear_decel', 1.0)              # [m/s²] fuerte; 6 km/h -> 0 en ~1.7 s (~1.4 m)
        p('angular_accel', 0.5)             # [rad/s²] (era 0.8)
        p('angular_decel', 1.2)             # [rad/s²]
        # PI propio sobre las RPM: APAGADO. El firmware ya controla velocidad (comando 80 -> 80 RPM)
        # y un segundo lazo encima hacía que las ruedas "buscaran" la posición al frenar (temblor).
        p('kp', 0.0)
        p('ki', 0.0)
        p('integral_limit', 40.0)           # [RPM*s]
        p('cmd_timeout', 0.5)               # [s] sin cmd_vel -> parar
        p('feedback_timeout', 0.5)          # [s] sin feedback -> parar
        p('stall_reopen', 1.5)              # [s] sin feedback con el puerto abierto -> reabrir
                                            # (el CH340 se "cuelga" con el ruido de los motores)
        p('rate', 50.0)                     # [Hz]
        p('odom_frame', 'odom')
        p('base_frame', 'base_footprint')
        # Odometría. Contrato: este nodo publica /base/wheel_odom y odom_ekf_node (ruedas + IMU)
        # publica /base/odom y la TF. Mientras el EKF no exista en el robot real, este nodo hace
        # las dos cosas: /base/odom + TF. Cuando exista: odom_topic: /base/wheel_odom,
        # publish_tf: false y odom_compat_topic: ''.
        p('odom_topic', '/base/odom')
        # Copia de la odometría con el nombre viejo, mientras Navegación (Nav2, ir_a, RViz) pasa
        # a /base/odom. '' = no publicar la copia.
        p('odom_compat_topic', '/odom')
        p('publish_tf', True)
        p('left_joint', 'left_wheel_joint')
        p('right_joint', 'right_wheel_joint')
        # Batería 10S 18650 (Li-ion): 42 V llena (4.20 V/celda), 36 V nominal, 12.5 Ah.
        p('bat_cells', 10)
        p('bat_capacity_ah', 12.5)
        p('bat_warn', 34.0)                 # [V] 3.40 V/celda: avisa y limita la velocidad
        p('bat_warn_speed', 0.5)            # fracción de max_linear/max_angular bajo bat_warn
        p('bat_cutoff', 32.0)               # [V] 3.20 V/celda: bloquea los motores (0 %)
        p('bat_resume', 35.0)               # [V] 3.50 V/celda: desbloquea (histéresis)
        p('bat_overvoltage', 42.3)          # [V] sobre esto: aviso de sobrecarga
        p('bat_filter_tau', 5.0)            # [s] filtro del voltaje (ignora caídas por carga)
        # Seta de emergencia física (ver docstring). estop_gpio_line < 0 la desactiva.
        p('estop_gpio_chip', 'gpiochip0')
        p('estop_gpio_line', 144)           # pin 7 del header = GPIO09 = PAC.06
        p('estop_gpio_period', 0.05)        # [s] cada cuánto se lee (20 Hz)
        p('estop_gpio_fail', 1.0)           # [s] sin poder leer el pin -> se toma como presionada
        g = lambda n: self.get_parameter(n).value  # noqa: E731

        self.r = g('wheel_radius')
        self.sep = g('wheel_separation')
        self.tpr = g('ticks_per_rev')
        self.max_cmd = g('max_command')
        self.kp, self.ki, self.ilim = g('kp'), g('ki'), g('integral_limit')
        self.cmd_timeout = g('cmd_timeout')
        self.max_v, self.max_w = g('max_linear'), g('max_angular')
        self.acc_v, self.dec_v = g('linear_accel'), g('linear_decel')
        self.acc_w, self.dec_w = g('angular_accel'), g('angular_decel')
        self.v_ramp = self.w_ramp = 0.0     # velocidad que se está pidiendo, ya con rampa
        self.fb_timeout = g('feedback_timeout')
        self.stall_reopen = g('stall_reopen')
        self.port_opened_at = None
        self.odom_frame, self.base_frame = g('odom_frame'), g('base_frame')
        self.publish_tf = g('publish_tf')
        self.joints = [g('left_joint'), g('right_joint')]
        self.bat_cells, self.bat_ah = g('bat_cells'), g('bat_capacity_ah')
        self.bat_warn, self.bat_warn_speed = g('bat_warn'), g('bat_warn_speed')
        self.bat_cutoff, self.bat_resume = g('bat_cutoff'), g('bat_resume')
        self.bat_over, self.bat_tau = g('bat_overvoltage'), g('bat_filter_tau')
        self.bat_v = None                   # voltaje filtrado
        self.bat_locked = False             # motores bloqueados por batería baja
        self.last_marker = 0.0

        cal_path = g('calibration_file')
        if not os.path.exists(cal_path):
            raise RuntimeError(f'Falta la calibración {cal_path}: '
                               'correr "ros2 run hoverboard_bridge calibrar" (ruedas en el aire)')
        with open(cal_path) as f:
            cal = yaml.safe_load(f)
        self.rpm_sign = np.array([cal['rpm_sign_left'], cal['rpm_sign_right']], dtype=float)
        self.tick_sign = np.array([cal['tick_sign_left'], cal['tick_sign_right']], dtype=float)
        mix = np.array(cal['mix'], dtype=float).reshape(2, 2)
        # swap_wheels: la rueda que el firmware llama "izquierda" es la derecha del robot (en Milo
        # el giro salía invertido con el avance correcto). Se intercambian filas y signos para
        # que control Y odometría usen la rueda física correcta.
        self.swap = bool(cal.get('swap_wheels', False))
        if self.swap:
            self.rpm_sign = self.rpm_sign[::-1].copy()
            self.tick_sign = self.tick_sign[::-1].copy()
            mix = mix[::-1].copy()
        self.mix_inv = np.linalg.inv(mix)
        self.get_logger().info(f'Calibración: {cal_path} (swap_wheels={self.swap})')

        self.port, self.baud = g('port'), g('baud_rate')
        self.ser = None
        self.next_reconnect = 0.0
        self.parser = FeedbackParser()
        self.open_port()

        # Estado
        self.target = (0.0, 0.0)            # v, w pedidos
        self.last_cmd = None
        self.last_fb = None
        self.fb = None
        self.prev_cnt = None
        self.integ = np.zeros(2)
        self.f_meas = np.zeros(2)           # RPM hacia adelante medidas [izq, der]
        self.wheel_pos = np.zeros(2)        # [rad]
        self.x = self.y = self.th = 0.0
        self.last_bat_log = 0.0

        self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        # Parada de emergencia: QoS "transient local" = el último valor queda guardado, así un nodo
        # que arranca después igual recibe una parada que se pidió antes.
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.estop = False                  # parada EFECTIVA (la que frena las ruedas)
        self.estop_pantalla = False         # pedida por /base/emergency_stop/pantalla
        self.seta = False                   # seta física presionada AHORA (la escribe el hilo)
        self.seta_enganche = False          # se presionó y aún no se libera desde la pantalla
        # Contrato: /base/emergency_stop (std_msgs/Bool, true = robot detenido) es la parada
        # EFECTIVA; la escuchan el brazo y el orquestador. Lo demás es interno de Estructura.
        self.create_subscription(Bool, '/base/emergency_stop/pantalla', self.on_estop, latched)
        self.create_service(Trigger, '/base/emergency_stop/rearmar', self.on_rearmar)
        self.estop_pub = self.create_publisher(Bool, '/base/emergency_stop', latched)
        self.estop_pub.publish(Bool(data=False))
        self.seta_pub = self.create_publisher(Bool, '/base/emergency_stop/seta', latched)
        self.gpio = (g('estop_gpio_chip'), g('estop_gpio_line'))
        self.gpio_period, self.gpio_fail = g('estop_gpio_period'), g('estop_gpio_fail')
        if self.gpio[1] >= 0:
            threading.Thread(target=self.leer_seta, daemon=True).start()
        else:
            self.get_logger().warn('Seta de emergencia física DESACTIVADA (estop_gpio_line < 0)')
        # Los dos estados también a 5 Hz (además de en cada cambio): un suscriptor sin QoS
        # "latcheado" igual los recibe, y el panel sabe así que el driver está vivo.
        self.create_timer(0.2, self.publicar_estop)
        self.odom_pub = self.create_publisher(Odometry, g('odom_topic'), 10)
        compat = g('odom_compat_topic')
        self.odom_compat_pub = self.create_publisher(Odometry, compat, 10) if compat else None
        self.js_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.bat_pub = self.create_publisher(Float32, '/hoverboard/bateria', 10)
        self.bat_pct_pub = self.create_publisher(Float32, '/hoverboard/bateria_pct', 10)
        # Textos para RViz (display Marker en este topic): batería sobre el robot y velocidad
        # de cada rueda sobre su rueda.
        self.marker_pub = self.create_publisher(Marker, '/hoverboard/markers', 10)
        self.tf = TransformBroadcaster(self)
        self.dt = 1.0 / g('rate')
        self.create_timer(self.dt, self.step)

    def open_port(self):
        """Abre el puerto. Si el USB se desconecta (ruido de los motores), se reintenta cada 1 s."""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0)
            self.port_opened_at = self.get_clock().now()
            self.parser = FeedbackParser()
            self.prev_cnt = None  # el contador pudo avanzar mientras no leíamos
            self.get_logger().info(f'Hoverboard en {self.port}')
        except (serial.SerialException, OSError) as e:
            self.ser = None
            self.get_logger().warn(f'No se pudo abrir {self.port}: {e}', throttle_duration_sec=5.0)

    def drop_port(self, e):
        self.get_logger().error(f'Puerto serie perdido ({e}); reintentando cada 1 s')
        try:
            self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.integ[:] = 0.0

    @staticmethod
    def ramp(cur, tgt, acc, dec, dt):
        """Acerca cur a tgt: con `acc` si se aleja de 0 (acelera), con `dec` si frena."""
        speeding_up = tgt * cur >= 0.0 and abs(tgt) > abs(cur)
        step = (acc if speeding_up else dec) * dt
        return min(tgt, cur + step) if tgt > cur else max(tgt, cur - step)

    def on_cmd(self, msg):
        v, w = msg.linear.x, msg.angular.z
        # NaN/inf (p. ej. una división por cero en otro nodo): se toma como PARAR. Sin esto, el
        # recorte max(-m, min(m, nan)) da +m: ¡NaN se convertía en velocidad máxima adelante!
        if not (math.isfinite(v) and math.isfinite(w)):
            self.get_logger().error(f'cmd_vel inválido (v={v}, w={w}): se toma como parar',
                                    throttle_duration_sec=1.0)
            v = w = 0.0
        self.target = (v, w)
        self.last_cmd = self.get_clock().now()

    # Voltaje en reposo de una celda 18650 -> % de carga (0 % = 3.20 V, corte).
    CURVA_18650 = ((3.20, 0.0), (3.45, 5.0), (3.58, 10.0), (3.65, 20.0), (3.70, 30.0),
                   (3.74, 40.0), (3.79, 50.0), (3.85, 60.0), (3.92, 70.0), (4.00, 80.0),
                   (4.10, 90.0), (4.20, 100.0))

    def bat_percent(self, v):
        c = v / self.bat_cells
        pts = self.CURVA_18650
        if c <= pts[0][0]:
            return 0.0
        for (v0, p0), (v1, p1) in zip(pts, pts[1:]):
            if c <= v1:
                return p0 + (p1 - p0) * (c - v0) / (v1 - v0)
        return 100.0

    def update_battery(self, v_raw):
        """Filtra el voltaje y aplica los límites de descarga."""
        if self.bat_v is None:
            self.bat_v = v_raw
        else:
            self.bat_v += (v_raw - self.bat_v) * min(1.0, self.dt / self.bat_tau)
        v = self.bat_v
        log = self.get_logger()
        if not self.bat_locked and v <= self.bat_cutoff:
            self.bat_locked = True
            log.error(f'BATERÍA AGOTADA ({v:.2f} V <= {self.bat_cutoff:.1f} V): motores '
                      f'bloqueados. Cargar hasta > {self.bat_resume:.1f} V.')
        elif self.bat_locked and v >= self.bat_resume:
            self.bat_locked = False
            log.info(f'Batería {v:.2f} V: motores desbloqueados')
        if self.bat_locked:
            log.error(f'Batería agotada ({v:.2f} V): motores bloqueados',
                      throttle_duration_sec=30.0)
        elif v <= self.bat_warn:
            log.warn(f'Batería baja ({v:.2f} V, {self.bat_percent(v):.0f}%): velocidad al '
                     f'{self.bat_warn_speed * 100:.0f}%. Cargar pronto.', throttle_duration_sec=30.0)
        if v >= self.bat_over:
            log.warn(f'Batería sobre {self.bat_over:.1f} V ({v:.2f} V): desconectar el cargador',
                     throttle_duration_sec=30.0)

    def leer_seta(self):
        """Hilo: lee el pin de la seta con gpioget (libgpiod) cada estop_gpio_period.

        gpioget toma el pin solo un instante, así otros programas (boton.sh, el panel) también
        pueden leerlo; si justo está ocupado se reintenta. Falla segura: si no se puede leer
        durante estop_gpio_fail segundos, se toma como PRESIONADA.
        """
        chip, linea = self.gpio
        ultimo_ok = time.monotonic()
        while rclpy.ok():
            try:
                r = subprocess.run(['gpioget', chip, str(linea)], capture_output=True,
                                   text=True, timeout=0.5)
                valor = r.stdout.strip() if r.returncode == 0 else ''
            except (OSError, subprocess.TimeoutExpired) as e:
                valor = ''
                err = str(e)
            else:
                err = r.stderr.strip()
            if valor in ('0', '1'):
                ultimo_ok = time.monotonic()
                self.seta = valor == '0'      # NC: suelta = 1, presionada o cortada = 0
            elif time.monotonic() - ultimo_ok > self.gpio_fail:
                if not self.seta:
                    self.get_logger().error(f'No se puede leer la seta ({chip} línea {linea}): '
                                            f'{err or valor!r}. Se toma como PRESIONADA.')
                self.seta = True
            time.sleep(self.gpio_period)

    def publicar_estop(self):
        self.estop_pub.publish(Bool(data=self.estop))
        self.seta_pub.publish(Bool(data=self.seta))

    def on_estop(self, msg):
        """/base/emergency_stop/pantalla: solo la parada de la PANTALLA (la seta: on_rearmar)."""
        self.estop_pantalla = msg.data
        self.actualizar_estop()

    def on_rearmar(self, _req, res):
        """/base/emergency_stop/rearmar: quita el enganche de la seta si ya está suelta."""
        if self.seta:
            res.success = False
            res.message = 'La seta física sigue presionada: gírala para soltarla'
            self.get_logger().warn('No se rearma: la seta física sigue presionada',
                                   throttle_duration_sec=1.0)
        else:
            if self.seta_enganche:
                self.get_logger().warn('Seta rearmada')
            self.seta_enganche = False
            res.success = True
            res.message = ('Seta rearmada' if not self.estop_pantalla else
                           'Seta rearmada; sigue la parada pedida desde la pantalla')
            self.actualizar_estop()
        return res

    def actualizar_estop(self):
        """Parada efectiva = pantalla O seta presionada O seta soltada pero sin liberar."""
        if self.seta:
            self.seta_enganche = True
        estop = self.estop_pantalla or self.seta or self.seta_enganche
        if estop != self.estop:
            self.estop = estop
            if estop:
                motivo = 'seta física' if self.seta else 'pantalla'
                self.get_logger().error(f'PARADA DE EMERGENCIA ({motivo}): ruedas detenidas')
            else:
                self.get_logger().warn('Parada de emergencia liberada')
            self.estop_pub.publish(Bool(data=self.estop))
            self.seta_pub.publish(Bool(data=self.seta))

    def secs_since(self, t):
        return (self.get_clock().now() - t).nanoseconds * 1e-9 if t is not None else 1e9

    # ---------------- lectura ----------------
    def read_feedback(self):
        for fb in self.parser.feed(self.ser.read(1024)):
            self.fb = fb
            if fb.bat > 5.0:  # 0 V = dato inválido
                self.update_battery(fb.bat)
            self.last_fb = self.get_clock().now()
            cnt = np.array([fb.cnt_r, fb.cnt_l] if self.swap else [fb.cnt_l, fb.cnt_r])
            if self.prev_cnt is not None:
                d = np.array([delta_int16(cnt[0], self.prev_cnt[0]),
                              delta_int16(cnt[1], self.prev_cnt[1])], dtype=float)
                self.integrate(self.tick_sign * d * 2.0 * math.pi / self.tpr)
            self.prev_cnt = cnt
            rpm = [fb.rpm_r, fb.rpm_l] if self.swap else [fb.rpm_l, fb.rpm_r]
            self.f_meas = self.rpm_sign * np.array(rpm, dtype=float)

    def integrate(self, dphi):
        """dphi = ángulo girado por cada rueda [rad] (+ = hacia adelante)."""
        self.wheel_pos += dphi
        dl, dr = dphi * self.r
        ds = 0.5 * (dl + dr)
        dth = (dr - dl) / self.sep
        self.x += ds * math.cos(self.th + 0.5 * dth)
        self.y += ds * math.sin(self.th + 0.5 * dth)
        self.th = math.atan2(math.sin(self.th + dth), math.cos(self.th + dth))

    # ---------------- control ----------------
    def step(self):
        now = self.get_clock().now()
        self.actualizar_estop()  # la seta la lee otro hilo; aquí se aplica (cada 1/rate s)
        if self.ser is None:
            t = now.nanoseconds * 1e-9
            if t >= self.next_reconnect:
                self.next_reconnect = t + 1.0
                self.open_port()
            if self.ser is None:
                self.f_meas[:] = 0.0
                self.publish(now)
                return
        try:
            self.read_feedback()
        except (serial.SerialException, OSError) as e:
            self.drop_port(e)
            return
        # Puerto abierto pero mudo: el adaptador se colgó sin desconectarse. Reabrirlo.
        last_ok = self.last_fb if self.last_fb is not None else self.port_opened_at
        if self.secs_since(last_ok) > self.stall_reopen and \
                self.secs_since(self.port_opened_at) > self.stall_reopen:
            self.drop_port('sin datos %.1f s' % self.secs_since(last_ok))
            return

        v, w = self.target
        if self.secs_since(self.last_cmd) > self.cmd_timeout:
            v = w = 0.0
        max_v, max_w = self.max_v, self.max_w
        if self.estop:
            v = w = 0.0
            self.v_ramp = self.w_ramp = 0.0  # sin rampa: frena ya
        elif self.bat_locked:
            v = w = 0.0
        elif self.bat_v is not None and self.bat_v <= self.bat_warn:
            max_v, max_w = max_v * self.bat_warn_speed, max_w * self.bat_warn_speed
        v = max(-max_v, min(max_v, v))
        w = max(-max_w, min(max_w, w))
        fb_ok = self.secs_since(self.last_fb) <= self.fb_timeout
        if not fb_ok:
            v = w = 0.0
            self.v_ramp = self.w_ramp = 0.0
        # Rampa de aceleración / frenado.
        self.v_ramp = self.ramp(self.v_ramp, v, self.acc_v, self.dec_v, self.dt)
        self.w_ramp = self.ramp(self.w_ramp, w, self.acc_w, self.dec_w, self.dt)
        v, w = self.v_ramp, self.w_ramp
        if not fb_ok:
            self.get_logger().warn('Sin feedback del hoverboard: parado',
                                   throttle_duration_sec=2.0)

        k = 60.0 / (2.0 * math.pi * self.r)  # m/s -> RPM
        f_tgt = np.array([(v - w * self.sep / 2.0) * k, (v + w * self.sep / 2.0) * k])

        if not fb_ok or (abs(v) < 1e-3 and abs(w) < 1e-3):
            self.integ[:] = 0.0
            speed = steer = 0
        else:
            e = f_tgt - self.f_meas
            self.integ = np.clip(self.integ + e * self.dt, -self.ilim, self.ilim)
            f_cmd = f_tgt + self.kp * e + self.ki * self.integ
            speed, steer = self.mix_inv @ f_cmd
            speed = int(np.clip(round(speed), -self.max_cmd, self.max_cmd))
            steer = int(np.clip(round(steer), -self.max_cmd, self.max_cmd))
        try:
            self.ser.write(make_command(steer, speed))
        except (serial.SerialException, OSError) as e:
            self.drop_port(e)

        self.publish(now)

    def publish(self, now):
        stamp = now.to_msg()
        q_z, q_w = math.sin(self.th / 2.0), math.cos(self.th / 2.0)
        vel = self.f_meas * 2.0 * math.pi / 60.0 * self.r  # m/s de cada rueda
        v_meas = 0.5 * (vel[0] + vel[1])
        w_meas = (vel[1] - vel[0]) / self.sep

        od = Odometry()
        od.header.stamp = stamp
        od.header.frame_id = self.odom_frame
        od.child_frame_id = self.base_frame
        od.pose.pose.position.x = self.x
        od.pose.pose.position.y = self.y
        od.pose.pose.orientation.z = q_z
        od.pose.pose.orientation.w = q_w
        od.twist.twist.linear.x = v_meas
        od.twist.twist.angular.z = w_meas
        for i, c in zip((0, 7, 14, 21, 28, 35), (1e-3, 1e-3, 1e6, 1e6, 1e6, 5e-3)):
            od.pose.covariance[i] = c
            od.twist.covariance[i] = c
        self.odom_pub.publish(od)
        if self.odom_compat_pub is not None:
            self.odom_compat_pub.publish(od)

        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = stamp
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_frame
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.rotation.z = q_z
            t.transform.rotation.w = q_w
            self.tf.sendTransform(t)

        js = JointState()
        js.header.stamp = stamp
        js.name = self.joints
        js.position = [float(p) for p in self.wheel_pos]
        js.velocity = [float(x) for x in self.f_meas * 2.0 * math.pi / 60.0]
        self.js_pub.publish(js)

        t_s = now.nanoseconds * 1e-9
        if t_s - self.last_marker > 0.5:
            self.last_marker = t_s
            self.publish_battery_marker(stamp)
            self.publish_wheel_markers(stamp)
        if self.fb is not None:
            self.bat_pub.publish(Float32(data=float(self.fb.bat)))
            if self.bat_v is not None:
                pct = self.bat_percent(self.bat_v)
                self.bat_pct_pub.publish(Float32(data=float(pct)))
                if t_s - self.last_bat_log > 60.0:
                    self.last_bat_log = t_s
                    self.get_logger().info(
                        f'Batería {self.bat_v:.2f} V ({pct:.0f}%, ~{pct / 100 * self.bat_ah:.1f} Ah), '
                        f'placa {self.fb.temp:.1f} °C')

    def publish_battery_marker(self, stamp):
        m = Marker()
        m.header.stamp = stamp
        m.header.frame_id = self.base_frame
        m.ns, m.id = 'bateria', 0
        m.type, m.action = Marker.TEXT_VIEW_FACING, Marker.ADD
        m.pose.position.z = 1.9          # sobre la cabeza de Milo
        m.pose.orientation.w = 1.0
        m.scale.z = 0.18                 # alto del texto [m]
        m.color.a = 1.0
        ok = self.fb is not None and self.ser is not None and \
            self.secs_since(self.last_fb) <= self.fb_timeout
        if not ok or self.bat_v is None:
            m.text = 'Bateria: SIN DATOS'
            m.color.r, m.color.g, m.color.b = 0.6, 0.6, 0.6
        else:
            v = self.bat_v
            pct = self.bat_percent(v) / 100.0
            m.text = f'Bateria {v:.1f} V ({pct * 100:.0f}%, ~{pct * self.bat_ah:.1f} Ah)'
            if self.estop:
                m.text += '\nPARADA DE EMERGENCIA'
            elif self.bat_locked:
                m.text += '\nAGOTADA: MOTORES BLOQUEADOS'
            elif v <= self.bat_warn:
                m.text += '\nBAJA: velocidad limitada'
            elif v >= self.bat_over:
                m.text += '\nSOBRECARGA: desconectar cargador'
            # verde -> amarillo -> rojo
            m.color.r = min(1.0, 2.0 * (1.0 - pct))
            m.color.g = min(1.0, 2.0 * pct)
            m.color.b = 0.0
            if self.estop:  # rojo puro
                m.color.r, m.color.g = 1.0, 0.0
        self.marker_pub.publish(m)

    def publish_wheel_markers(self, stamp):
        ok = self.ser is not None and self.secs_since(self.last_fb) <= self.fb_timeout
        rpm = self.f_meas if ok else np.zeros(2)
        mps = rpm * 2.0 * math.pi / 60.0 * self.r
        for i, (nombre, y) in enumerate((('Izq', self.sep / 2.0), ('Der', -self.sep / 2.0))):
            m = Marker()
            m.header.stamp = stamp
            m.header.frame_id = self.base_frame
            m.ns, m.id = 'ruedas', i
            m.type, m.action = Marker.TEXT_VIEW_FACING, Marker.ADD
            # Sobre la cabeza, bajo el texto de la batería (a 0.55 m quedaban tapados por el cuerpo).
            m.pose.position.y = 0.45 if y > 0 else -0.45  # separados para que no se pisen
            m.pose.position.z = 1.55
            m.pose.orientation.w = 1.0
            m.scale.z = 0.14
            m.color.a = 1.0
            if not ok:
                m.text = f'{nombre}: --'
                m.color.r = m.color.g = m.color.b = 0.6
            else:
                m.text = f'{nombre}: {mps[i]:+.2f} m/s\n{rpm[i]:+.0f} rpm'
                # celeste adelante, naranjo atrás, blanco quieto
                if abs(rpm[i]) < 1.0:
                    m.color.r = m.color.g = m.color.b = 1.0
                elif rpm[i] > 0:
                    m.color.r, m.color.g, m.color.b = 0.3, 0.8, 1.0
                else:
                    m.color.r, m.color.g, m.color.b = 1.0, 0.6, 0.1
            self.marker_pub.publish(m)

    def stop(self):
        if self.ser is None:
            return
        for _ in range(5):
            try:
                self.ser.write(make_command(0, 0))
            except Exception:
                pass
        self.ser.close()


def main():
    rclpy.init()
    node = HoverboardBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
