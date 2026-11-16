#!/bin/bash
# Muestra en tiempo real el estado del botón de parada de emergencia.
# Botón NC entre pin 1 (3.3V) y pin 7 (GPIO09 = PAC.06 = gpiochip0 línea 144), con el pull-down
# interno que activa el overlay de la carpeta overlay/ (sin él, el pin queda flotando en 1):
#   circuito cerrado (suelto)              -> pin en 1 -> SUELTO
#   circuito abierto (presionado o cortado) -> pin en 0 -> PRESIONADO
# Salir: Ctrl+C
CHIP=gpiochip0
LINEA=144
prev=x
echo "Botón de emergencia (pin 7). Ctrl+C para salir."
while true; do
  # Si otro programa está leyendo el pin justo ahora ("busy"), reintentar en vez de salir.
  v=$(gpioget $CHIP $LINEA 2>/dev/null) || { sleep 0.05; continue; }
  if [ "$v" != "$prev" ]; then
    if [ "$v" = "1" ]; then
      printf '\r\033[K\033[1;42;97m  SUELTO  \033[0m  %s' "$(date +%T)"
    else
      printf '\r\033[K\033[1;41;97m  PRESIONADO  \033[0m  %s' "$(date +%T)"
    fi
    prev=$v
  fi
  sleep 0.05
done
