#!/bin/bash
# Instala el overlay del botón de emergencia (pull-down interno en el pin 7) en el arranque.
# Uso (desde esta carpeta):  sudo bash instalar.sh      (después: reiniciar)
# Deshacer: sudo cp /boot/extlinux/extlinux.conf.antes_milo /boot/extlinux/extlinux.conf
#           (o elegir "primary kernel" en el menú de arranque)
set -e
[ "$(id -u)" = 0 ] || { echo "Correr con sudo"; exit 1; }
DIR=$(dirname "$(readlink -f "$0")")
DTBO=milo-boton-emergencia.dtbo
CONF=/boot/extlinux/extlinux.conf
FDT=/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb

[ -f "$FDT" ] || { echo "No existe $FDT"; exit 1; }
cp "$DIR/$DTBO" /boot/$DTBO
echo "Copiado /boot/$DTBO"

if grep -q "^LABEL milo" $CONF; then
  echo "La entrada 'milo' ya estaba en $CONF (no se cambia)"
else
  [ -f $CONF.antes_milo ] || cp $CONF $CONF.antes_milo
  echo "Respaldo: $CONF.antes_milo"
  # Misma línea APPEND que la entrada "primary" de fábrica.
  APPEND=$(awk '/^LABEL primary/{p=1} p && /^[[:space:]]*APPEND/{sub(/^[[:space:]]*/,""); print; exit}' $CONF)
  [ -n "$APPEND" ] || { echo "No encontré APPEND de 'primary'"; exit 1; }
  cat >> $CONF <<EOF

LABEL milo
      MENU LABEL Milo: boton de emergencia (pin 7 pull-down)
      LINUX /boot/Image
      FDT $FDT
      INITRD /boot/initrd
      $APPEND
      OVERLAYS /boot/$DTBO
EOF
  sed -i 's/^DEFAULT .*/DEFAULT milo/' $CONF
  echo "Entrada 'milo' agregada y puesta por defecto. 'primary' queda como respaldo."
fi
echo
echo "Listo. Reinicia la Jetson:  sudo reboot"
