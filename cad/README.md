# Modelo CAD

Archivo CAD del robot: modelo 3D completo de MILO, hecho en **Autodesk Fusion 360**, igual al URDF rev. 1
([`milo_description`](../milo_description/README.md)).

| Archivo | Descripción |
|---|---|
| [`milo_ensamblaje.f3z`](milo_ensamblaje.f3z) | Archivo nativo de Fusion con todas las piezas referenciadas (exportado el 10-11-2026) |
| [`milo_ensamblaje.step`](milo_ensamblaje.step) | Ensamblaje completo en STEP (44 MB), exportado el 10-11-2026. Se abre en cualquier CAD |

## Contenido del modelo

Todo lo nuevo está agrupado en componentes `URDF rev1 - …`, en la posición del URDF:

- **Piezas modeladas en Fusion** (sketch + extrusión): bastidor V-slot 3030 con el collar de la columna y la caja trasera,
  columna 6060 con su tapa, 74 escuadras 3030, 2 SK16, placa de acrílico de 3 mm y placas de PAI de 2 mm.
- **CAD de fabricante:** ruedas de hoverboard 6,5", placa del hoverboard, Jetson Orin Nano (modelo simplificado),
  Arduino Mega 2560 (BlackBoard Mega), 6 drivers TB6600, regulador 36→12 V y RPLIDAR C1.
- **Piezas medidas del URDF** (secciones de sus mallas, como sólidos paramétricos): baterías 10S2P, IMU HFI-B9,
  rueda loca de 3" y monitor de 11,6".
- **Cámara de la muñeca:** Orbbec Gemini Plus modelada con sus medidas, con su soporte en L.
- **Brazo** en la pose plegada, sin la base redonda, montado sobre la placa del carro. **Cabeza** contra la cara frontal
  de la columna.

**Materiales y masas:** cada pieza tiene su material de Fusion (acrílico transparente, aluminio anodizado, PAI, acero, FR4…).
Donde el modelo no es macizo como la pieza real (electrónica, eslabones impresos, perfil V-slot simplificado), un material
`MILO …` ajusta la densidad para que la masa coincida con la del URDF.

**Articulaciones** (el 0 de cada una es la pose plegada): `joint_1`…`joint_6`, los dedos, `vertical_lift_joint`
(carro sobre la columna, 0 a 1000 mm) y las dos ruedas. La estructura está fija al suelo y todo lo que va fijo a la base
está en el grupo rígido `MILO base (fijo)`.

Las piezas del modelo anterior que fueron reemplazadas (bloque de la base, columna, ruedas, lidar, brazo con base redonda,
IMU, rueda loca) siguen en el archivo, **ocultas** y con sus articulaciones suprimidas.

## Cómo exportar desde Fusion 360

- **`.f3z`:** Archivo → Exportar → *Archivado de archivos de Autodesk Fusion (.f3z)*. Incluye las piezas referenciadas.
- **`.step`:** Archivo → Exportar → *STEP Files (.step)*.

Al actualizar el modelo, reemplaza los dos archivos y anota el cambio en el [CHANGELOG](../CHANGELOG.md).

> GitHub acepta archivos de hasta 100 MB.
