# Modelo CAD

Archivo CAD del robot: modelo 3D completo de MILO, hecho en **Autodesk Fusion 360**.

| Archivo | Descripción |
|---|---|
| [`milo_ensamblaje.step`](milo_ensamblaje.step) | Ensamblaje completo en STEP (17 MB), exportado de Fusion 360 el 25-10-2026. Se abre en cualquier CAD |
| _por subir_ | Archivo nativo de Fusion (`.f3z`) |

## Cómo exportar desde Fusion 360

- **`.f3z`:** Archivo → Exportar → *Fusion Archive Files (.f3z)*. Incluye todas las piezas referenciadas del ensamblaje.
- **`.step`:** Archivo → Exportar → *STEP Files (.step)*.

Al actualizar el modelo, reemplaza los dos archivos y anota el cambio en el [CHANGELOG](../CHANGELOG.md).

> GitHub acepta archivos de hasta 100 MB.

## Cambios que faltan en el CAD

El URDF rev. 1 ([`milo_description`](../milo_description/README.md), 2026-11-08) tiene la geometría más nueva.
Hay que pasar estos cambios a Fusion y volver a exportar el STEP:

- Base de perfiles V-slot 3030 con el **collar** de la columna (7 perfiles nuevos) y 74 escuadras: ver la [BOM](../bom/README.md#perfilería).
- Caja trasera de 3030 (50 cm) con las placas de PAI de 2 mm.
- El brazo va atornillado **directo a la placa del carro**: se elimina la base redonda impresa (Ø150 × 37 mm).
- La **cabeza** va pegada a la cara frontal de la columna, con 10 cm de perfil por encima (techo de la carcasa a 1,40 m del pie de la columna).
- Las mallas STL del URDF (`milo_description/meshes/`) sirven de referencia, en mm.
