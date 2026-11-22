# Reel promocional · Santo Pistón Garage

## Versión actual: recorrido por el garaje (tipo vídeo de inmobiliaria)

**Entregables**
- `santo_piston_garaje_recorrido_1080x1920.mp4`: 30,3 s, 1080 × 1920, 30 fps, H.264 + AAC, −14 LUFS
- `portada_garaje_recorrido.jpg`: portada 1080 × 1920

**Cómo está hecho.** El garaje es una creación 3D en Blender (Cycles), todo gratis y hecho en código: nave blanca, puerta acristalada al patio, banco de roble con cajoneras verde oliva, panel de herramientas, carteles retro originales, el logotipo en la pared y una galería de fotos del proceso. Las motos son las fotos reales recortadas y colocadas en la escena como «muebles», con su sombra de contacto. Los planos se renderizan a 10 fps, se interpolan a 30 fps y se montan con cortes a 105 BPM (`recorrido-3d/fuentes/`).

**Guion (30 s):** entrada con el título → zona de trabajo → detalle del banco → Honda Scoopy 75 → galería «El proceso» → Montesa (Enduro) → cuadro de las dos Scoopy → Bultaco Chispa → Montesa «Recién llegada» → plano general → cierre con el logotipo y «¿Tienes una clásica para restaurar? Escríbenos.»

**Honestidad:**
- El garaje es una recreación 3D, no un espacio real.
- La Montesa de trial y la Enduro 75 aparecen tal como llegaron; no se presenta ninguna restauración inventada.
- La Scoopy blanca y la Montesa de franjas solo salen en fotos enmarcadas porque no había recorte limpio.
- El Fiat 126 se ha quitado porque el recorte quedaba plano.
- La GasGas no aparece: es moderna, no una restauración.

El crédito de la música es el mismo que el de abajo y es obligatorio.

---

## Versión anterior: reel estilo móvil

**Entregables**
- `santo_piston_reel_1080x1920.mp4`: vertical 9:16, 1080 × 1920, 30 fps, H.264 + AAC, 28,6 s, −14 LUFS
- `portada_santo_piston.jpg`: portada del Reel, 1080 × 1920

## Cómo está hecho

No hay cuenta de Higgsfield ni de otro generador de vídeo, así que el Reel está montado en código: Python, PIL y ffmpeg. Se ha seguido la metodología de la skill de motion design de código abierto **howseen-ai/claude-motion-design** (licencia MIT), que está instalada en `.claude/skills/motion-design/`. En concreto:
- Mapa de pulsos: todos los cortes caen en la rejilla de 105 BPM de la música.
- Temblor de móvil suave y reproducible, con grano de sensor.
- Sonido de taller sintetizado y colocado en cada corte: interruptor, cajón metálico y carraca.
- Mezcla final a −14 LUFS.
- Dos rondas de críticos independientes (movimiento y diseño) que juzgan los fotogramas sin haber montado el vídeo.

La otra skill llamada «motion-design» (cth9191/motion-design) solo funciona con Higgsfield y no permite usar otro sistema, así que no era aplicable.

## Guion final (28,6 s, cortes en pulsos de 0,571 s)

| Tiempo | Plano | Fuente | Rótulo |
|---|---|---|---|
| 0,0–1,1 | Emblema del depósito de la moto de trial, tal como llegó | Foto real | — |
| 1,1–2,3 | Mismo encuadre, restaurado (clic de interruptor en el corte) | Recreación digital sobre la foto real | Etiqueta «Recreación digital» |
| 2,3–4,6 | El taller: panel de herramientas y elevador | Foto real | — |
| 4,6–8,6 | Las dos Scoopy | Foto real | Honda Scoopy 75 · Dos unidades |
| 8,6–9,7 | Escudo de la Scoopy, pulido | Foto real | Honda Scoopy 75 |
| 9,7–11,4 | Depósito rojo de franjas | Foto real | Montesa |
| 11,4–13,7 | La misma moto en el elevador | Foto real | Montesa |
| 13,7–17,1 | Montesa roja y amarilla, dos encuadres | Foto real | Montesa |
| 17,1–18,9 | Moto de trial completa | Foto real | Montesa · Así llegó |
| 18,9–20,6 | Depósito restaurado | Recreación digital | Montesa · Así quedó |
| 20,6–22,9 | Fiat 126 | Foto real | Fiat 126 |
| 22,9–25,1 | Salida de la Old School Ride | Foto real | — |
| 25,1–28,6 | Cierre sobre crema: logotipo original, nombre y llamada a la acción | Edición | SANTO PISTÓN GARAGE · ¿Tienes una clásica para restaurar? Escríbenos. |

Las Montesas llevan solo «Montesa», tal como se pidió.

## Decisiones tomadas

- **Restauración de la moto de trial.** No había fotos de cómo quedó, así que se ha recreado editando la foto real. El depósito queda blanco limpio y conserva las letras, las franjas y el emblema originales, de modo que el antes y el después están alineados al píxel. La moto completa restaurada no resultaba creíble (chasis rojo plano, recortes bruscos), por eso solo se muestra el depósito. Lleva la etiqueta «Recreación digital» para no presentar como trabajo real algo que no lo es ante posibles clientes. Si se quiere quitar, hay que borrar las dos llamadas a `small_tag` en `fuentes/montaje_final.py`. Cuando exista una foto real de la moto terminada, conviene sustituirla.
- **Taller.** Se probaron interiores generados con IA, con el modelo gratuito Sana vía Pollinations. Salían con poca resolución y marca de agua, y cada plano parecía un sitio distinto (uno, una cocina). Los críticos los rechazaron y se han quitado. El taller que aparece es vuestro garaje real, que encaja mejor con el estilo de vídeo grabado con móvil.
- **Duración.** Pasa de 35 s a 28,6 s. Así no hay planos vacíos, y en Reels lo corto retiene más.

## Música: obligatorio poner el crédito en el pie del Reel

Pista: «Funk Game Loop», de Kevin MacLeod (incompetech.com). Licencia Creative Commons Atribución 4.0, que permite el uso comercial y promocional. Hay que pegar esto en la descripción de la publicación:

```
Música: "Funk Game Loop" Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/
Recortada y mezclada con sonidos de taller.
```

Si preferís no poner el crédito, Kevin MacLeod vende una licencia sin atribución por unos 30 USD por canción.

## Texto propuesto para la publicación

> Así llegan y así se van. Dos Honda Scoopy 75 y tres Montesas que han pasado por el taller.
> ¿Tienes una clásica guardada? Escríbenos y la ponemos a punto. 🔧
> 📍 Maresme
>
> (crédito de la música, arriba)
>
> #motosclasicas #montesa #hondascoopy #restauracion #maresme #santopistongarage

## Para regenerar el vídeo

`fuentes/montaje_final.py` recibe tres argumentos: la carpeta de trabajo (con `photos/`, `restored/`, `fonts/` y `music/`), la carpeta de salida y la ruta del logotipo. `fuentes/restauracion_deposito.py` genera el depósito restaurado.
