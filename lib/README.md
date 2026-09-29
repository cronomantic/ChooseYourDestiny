# Librerías de CYD

Rutinas reutilizables escritas **en CYD** (no tocan la máquina virtual ni añaden
dependencias). Se distribuyen como ficheros `.cyd` que incluyes en tu programa
con la directiva `INCLUDE` del preprocesador. Cada librería se **auto-salta** sus
rutinas (un `GOTO` interno al principio), así que puedes incluirla al comienzo de
tu guion sin que el flujo caiga dentro de las subrutinas: solo se ejecutan cuando
las llamas con `GOSUB`.

```
[[
    INCLUDE "../../lib/math16_32.cyd"
    INCLUDE "../../lib/strings.cyd"
    ... tu programa ...
]]
```

Cada librería reserva un bloque de variables como *workspace*. Los bloques **no
se solapan**, así que puedes usar ambas a la vez:

| Librería | Variables reservadas |
|----------|----------------------|
| `math16_32.cyd` | 224..247 y 253 |
| `strings.cyd`   | 216..223 |
| `sprites.cyd`   | 200..211 |
| `sprites_px.cyd` | 200..212 (en lugar de `sprites.cyd`) |

Todas las rutinas están verificadas automáticamente en el emulador (ZEsarUX vía
el harness, ver [doc/dev/EMULATOR_TESTING.md](../doc/dev/EMULATOR_TESTING.md)).

---

## `math16_32.cyd` — aritmética de 16 y 32 bits

Enteros anchos **sin signo** (16 bits: 0..65.535; 32 bits: 0..4.294.967.295) con
multiplicación y división, que en las variables de 8 bits de CYD no eran viables
por desbordar. El núcleo está escrito en **ensamblador Z80 nativo** (un bloque
`ASM`, ver la sección "Rutinas nativas" del manual), mucho más rápido que la
versión pura-CYD; la interfaz `GOSUB` no cambia. `print` usa el servicio
`SVC_PRINT_CHAR` (`CYD_SYSCALL`). Detalle de diseño en
[doc/dev/MATH_LIBRARY.md](../doc/dev/MATH_LIBRARY.md).

**Registros** (little-endian, byte bajo primero):
`A`=mlA0..mlA3, `B`=mlB0..mlB3, `C`=mlC0..mlC3. Las operaciones de 16 bits usan
los 2 bytes bajos de A/B/C. Carga literales anchos con asignación múltiple:
`SET mlA0 TO {226, 4}` (= 1250 = 0x04E2).

| Rutina | Efecto |
|--------|--------|
| `add16` / `add32` | `A = A + B` (envuelve) |
| `sub16` / `sub32` | `A = A - B` (envuelve; usa `cmp` para comprobar antes) |
| `cmp16` / `cmp32` | `mlCmp = 0/1/2` → `A<B` / `A=B` / `A>B` |
| `shl16` / `shl32` | `A = A << 1` |
| `shr16` / `shr32` | `A = A >> 1` |
| `mul32` | `C = A * B` (trunca a 32 bits) |
| `mul1632` | `C(32) = A(16) * B(16)` — **nunca desborda** (recomendada para puntuaciones) |
| `div32` | `A = A / B` (cociente), `C = A mod B` (resto). `mod32` = leer `C` |
| `print16` / `print32` | imprime `A` en decimal (destruye `A`) |

Para dividir entre un valor de 16 bits, ponlo en `B` con `B2=B3=0` y usa `div32`
(el cociente puede ser de 32 bits). El tier de 16 bits sigue siendo algo más
rápido que el de 32 (menos bytes por operación).

Ejemplo completo: [examples/math_library/](../examples/math_library/).

---

## `strings.cyd` — cadenas de texto

Entrada por teclado, impresión y manejo de cadenas guardadas como arrays de
caracteres en variables consecutivas (idiom de indirección `[@ptr]`), terminadas
en `0`. Generaliza el ejemplo [examples/input_test/](../examples/input_test/)
para operar sobre un buffer elegido por el autor. Las rutinas de datos
(`strClear`/`strLen`/`strCopy`/`strCmp`) y `strPrint` están en **ensamblador Z80
nativo** (bloque `ASM`; `strPrint` usa `SVC_PRINT_CHAR`); `strInput` es interactivo
y se queda en CYD (no gana con el nativo). La interfaz `GOSUB` no cambia.

Antes de llamar, fija los registros:

- `stBase` = índice de la primera variable del buffer
- `stLen`  = capacidad del buffer en caracteres
- `stB2`   = índice del segundo buffer (solo `strCopy`/`strCmp`)

| Rutina | Efecto |
|--------|--------|
| `strClear` | pone a 0 el buffer |
| `strLen`   | cuenta caracteres hasta el 0 o el final → `stRes` |
| `strPrint` | imprime el buffer hasta el 0 o el final |
| `strInput` | lee una cadena del teclado (cursor, ENTER termina, DELETE borra) |
| `strCopy`  | copia `stBase` → `stB2` (`stLen` bytes) |
| `strCmp`   | compara `stBase` con `stB2` → `stRes = 0/1/2` (menor/igual/mayor) |

Ejemplo: [examples/strings_library/](../examples/strings_library/).

**Estado de verificación:** `strClear`, `strLen`, `strCmp`, `strCopy` y la
captura de caracteres de `strInput` (limpieza, filtro de imprimibles, avance del
puntero y límites del buffer) están verificados en emulador —la entrada se inyecta
por el protocolo remoto de ZEsarUX—. El manejo de las teclas ENTER y DELETE es
idéntico al del ejemplo `input_test` ya probado.

---

## `sprites.cyd` — sprites con máscara

Pinta trozos de la imagen cargada en el buffer (`PICTURE`) sobre la pantalla **sin
borrar el fondo**. Cada sprite lleva su máscara: la silueta de lo que tapa, dibujada
en tinta en la misma imagen. El núcleo es ensamblador Z80 nativo; si no llamas a
ninguna rutina, no se incluye nada.

El sprite y su posición horizontal se miden en caracteres (8x8), como en `BLIT`. La
posición vertical es `sprDY` caracteres más `sprPY` píxeles: con `sprPY` a 0 todo va
por caracteres; para mover un sprite píxel a píxel, deja `sprDY` a 0 y usa `sprPY`
como la Y en píxeles (0..191). Lo que sale de la pantalla por la derecha o por abajo
se recorta. Parámetros (variables 200..211):

| Variables | Significado |
|-----------|-------------|
| `sprX`, `sprY` | esquina del sprite en el buffer |
| `sprW`, `sprH` | ancho y alto |
| `sprMX`, `sprMY` | esquina de su máscara en el buffer |
| `sprDX`, `sprDY` | posición en pantalla, en caracteres |
| `sprPY` | píxeles que se suman a `sprDY` |
| `sprAttr` | 0: los colores de la pantalla no cambian; 1: el sprite pone sus colores en las celdas donde su máscara no está vacía (con `sprPY`, en la celda donde cae la mayor parte) |
| `sprSlot` | hueco de `sprSave` / `sprRestore` (0..3) |
| `sprErr` | 1: lo que `sprSave` tenía que guardar no cabe en el hueco; 2: no existe ese hueco |

| Rutina | Efecto |
|--------|--------|
| `sprDraw` | pantalla = (pantalla AND NOT máscara) OR sprite |
| `sprXor` | pantalla = pantalla XOR sprite (sin máscara; repetirlo lo borra) |
| `sprSave` | guarda en el hueco `sprSlot` lo que hay en pantalla donde iría el sprite |
| `sprRestore` | vuelve a poner lo guardado en el hueco `sprSlot`, donde estaba |

**Ejemplo:** un personaje de 2x3 caracteres sobre un escenario.

```cyd
[[
    INCLUDE "../../lib/sprites.cyd"
    PICTURE 1 : DISPLAY 1        /* el escenario, en pantalla */
    PICTURE 2                    /* la hoja de sprites, al buffer (no se ve) */
    SET sprX TO 0 : SET sprY TO 0 : SET sprW TO 2 : SET sprH TO 3
    SET sprMX TO 2 : SET sprMY TO 0      /* la máscara, a su derecha */
    SET sprDX TO 14 : SET sprDY TO 10
    GOSUB sprDraw
]]
```

**Sprites que se mueven.** En cada paso: `sprSave` guarda el fondo donde va a ir el
sprite, `sprDraw` lo pinta y, antes de moverlo, `sprRestore` repone el fondo (en su
sitio, aunque ya hayas cambiado `sprDX`/`sprDY`). Si se mueven varios, cada uno usa
su hueco (`sprSlot`) y se restauran **en el orden contrario al que se guardaron**
(el último guardado, el primero): así el fondo queda bien aunque se crucen. Para
animarlos, cambia en cada paso `sprX`/`sprY` al siguiente fotograma de la hoja.

Hay un ejemplo completo en `examples/sprites`: un personaje que camina por
caracteres y una pelota que bota píxel a píxel, cada uno en su hueco.

Hay 4 huecos de 8 caracteres (un sprite de 2x3 que no está alineado toca 2x4
celdas); las constantes `SPR_SLOTS` y `SPR_SLOT_CHARS` del fichero los cambian, a 9
bytes por carácter. En total ocupa unos 1030 bytes (730 de código y 300 de huecos),
solo si se usa; en 128K y +3 van en un banco paginado, fuera de la memoria
principal.

**Estado de verificación:** las cuatro rutinas, la Y al píxel, varios huecos
restaurados en orden inverso, el recorte en los bordes, los atributos y los dos
códigos de `sprErr` se comprueban en emulador (48K y 128K) comparando la pantalla
entera con un modelo en Python (`tests/test_sprites_lib.py`).

---

## `sprites_px.cyd` — sprites con X al píxel

El sprite y su posición horizontal se miden en caracteres; `sprites_px.cyd` es la
misma librería con una variable más, `sprPX` (212): los píxeles que se suman a
`sprDX`. Todo lo demás (rutinas, parámetros y huecos) funciona igual. Para mover un
sprite píxel a píxel en horizontal, deja `sprDX` a 0 y usa `sprPX` como la X en
píxeles (0..255). Con `sprAttr` a 1, los colores van a la columna donde cae la mayor
parte de cada celda.

Es una librería aparte porque la X al píxel cuesta. Cuando no cae en un borde de
carácter, cada fila del sprite y de su máscara se desplaza al pintarla, y un sprite
de 2x3 tarda casi medio frame en vez de 0,2. Además ocupa unos 490 bytes más: el
código, dos buffers de fila y huecos de 12 caracteres en vez de 8 (un 2x3 que no
está alineado ni en X ni en Y toca 3x4 celdas). Incluye solo una de las dos:
comparten variables y etiquetas.

```cyd
[[
    INCLUDE "../../lib/sprites_px.cyd"
    PICTURE 1 : DISPLAY 1
    PICTURE 2
    SET sprX TO 0 : SET sprY TO 0 : SET sprW TO 2 : SET sprH TO 3
    SET sprMX TO 2 : SET sprMY TO 0
    SET sprDX TO 0 : SET sprPX TO 117    /* X = 117 píxeles */
    SET sprDY TO 0 : SET sprPY TO 80     /* Y = 80 píxeles */
    GOSUB sprDraw
]]
```

Hay un ejemplo en `examples/sprites_px`: el de `examples/sprites` con el personaje
caminando píxel a píxel.

**Estado de verificación:** los mismos casos que `sprites.cyd` y, además,
desplazamientos de 1 a 7 píxeles repartidos entre `sprDraw`, `sprXor` y
`sprSave`/`sprRestore`, el recorte por la derecha con desplazamiento, una X que se
sale de la pantalla, los colores en la columna donde cae la mayor parte y dos
sprites desplazados que se solapan en dos huecos. Se comprueban en emulador (48K y
128K) contra el mismo modelo en Python.
