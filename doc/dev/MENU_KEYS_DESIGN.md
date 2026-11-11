# Teclas configurables en los menús — diseño

> **Estado:** implementado (nov 2026), pendiente de commit. Ver también
> `SYNTAX_SUGAR_DESIGN.md` (principios: el esfuerzo va al compilador, no al runtime)
> y `MLD48_NATIVE_ROUTINES.md` (presupuesto de MLD 48K).

## Resumen

- Las 5 teclas de los menús (arriba, abajo, izquierda, derecha, seleccionar) pasan a
  la **RAM del motor**, y el script las cambia con **`MENUKEY accion, tecla`**.
- El joystick que va por el teclado se elige aparte con **`MENUJOY tipo`** (ninguno,
  Sinclair 1, Sinclair 2 o cursor): **teclado y joystick funcionan a la vez**. El
  Kempston se lee aparte y funciona siempre.
- **No gasta variables, ni arrays, ni DATA.**
- Las dos sentencias son azúcar sobre **un opcode de configuración genérico,
  `POP_CONFIG ajuste, valor`**, que escribe un byte de configuración del motor. Los
  ajustes futuros de ese tipo lo reutilizan sin gastar más opcodes.
- **El opcode sale de liberar `SET_KEMPSTON`** (`0x7D`), que solo era un atajo del
  compilador. No hay prefijo extendido ni segunda tabla de saltos.
- Con `-trim`, los juegos que no usan estas sentencias no llevan nada de esto; sin
  `-trim` (lo normal), el intérprete lleva todos los opcodes y crece 49 bytes.
- Dos cambios para **todos** los juegos: la **`M` deja de seleccionar** y la **pausa de
  página acepta el disparo del Kempston**.

## Situación actual

Todo lo que sigue sale del código (`src/cydc/cydc/cyd/inkey.asm`,
`interpreter.asm`, `text_manager.asm`, `cyd_*.asm`).

- **Una sola rutina lee los controles de los menús:** `INKEY_MENU` (`inkey.asm`).
  Devuelve una máscara `xxxFUDLR` (`KEYPRESS_RIGHT`=1, `LEFT`=2, `DOWN`=4, `UP`=8,
  `FIRE`=16) y la usan `CHOOSE` (todas sus variantes, vía `MENU_MOVE`), `WAITKEY`,
  `PAUSE` y la pausa del arranque (`PAUSE_AT_START_VAL`) de los cinco cargadores.
- **Las teclas están fijas en el código, como valores inmediatos:**
  - derecha: `p` o cursor derecha (`$09`, CAPS SHIFT + 8);
  - izquierda: `o` o cursor izquierda (`$08`, CAPS SHIFT + 5);
  - abajo: `a` o cursor abajo (`$0A`, CAPS SHIFT + 6);
  - arriba: `q` o cursor arriba (`$0B`, CAPS SHIFT + 7);
  - seleccionar: espacio, `m` o Enter.
- **El Kempston se suma siempre** (`KEMPSTON`), con la detección del bus flotante
  hecha al arrancar (`KEMPSTON_VALUE`). Su máscara de bits coincide con la de las
  teclas, por eso basta un `or`.
- **La pausa de página no usa `INKEY_MENU`.** `WAIT_NEXT_PAGE` (`text_manager.asm`)
  llama a `INKEY` y compara a mano con Enter, espacio y `m`, así que **el disparo del
  Kempston no pasa de página**, aunque sí sirve en `WAITKEY` y en los menús.
- `INKEY` decodifica en modo `L` con el Bloq Mayús desactivado al arrancar (también
  en MLD, que pone `IY=$5C3A` antes), así que las letras llegan siempre en minúscula y
  los dígitos sin desplazar llegan como `'0'`..`'9'`.

## Qué falta

- **Joystick Sinclair (Interface 2).** Está cableado a la matriz del teclado: el
  puerto 1 son las teclas 6 (izquierda), 7 (derecha), 8 (abajo), 9 (arriba) y 0
  (disparo); el puerto 2, 1, 2, 3, 4 y 5. CYD no responde a ninguno de los dos.
- **Joystick de cursor (Protek, AGF).** Manda 5, 6, 7, 8 y 0 **sin** CAPS SHIFT. CYD
  solo acepta las flechas con CAPS SHIFT ($08-$0B), así que tampoco responde.
- **Teclado a gusto del jugador.** Q/A/O/P es un estándar razonable, pero no hay
  forma de cambiarlo.
- **No se pueden aceptar todos a la vez.** Sinclair y cursor usan las mismas teclas
  con significados distintos (el 6 es izquierda en Sinclair y abajo en cursor; igual
  con 7 y 8). Hay que elegir, como en el menú «Teclado / Kempston / Sinclair /
  Cursor» de los juegos de Spectrum. Kempston no choca con nada.

Una tabla de teclas cambiable cubre las tres cosas: Sinclair y cursor no son más que
juegos de cinco teclas concretos.

## Restricciones

- **La tabla de opcodes está llena.** `OPCODES` (`interpreter.asm`) está alineada a
  256 bytes con entradas de 2 bytes, y el bytecode guarda cada opcode multiplicado
  por 2 (`EXEC_LOOP`: `ld d, HIGH OPCODES` / `ld e, (hl)`). El límite es 128 opcodes y
  `CydcCodegen.opcodes` los ocupa todos, del `0x00` (`END`) al `0x7F` (`EXTERN`).
- **Sin prefijo extendido** (decisión de Sergio): añade otra tabla de saltos y
  dispara el uso de memoria.
- **Sin gastar variables, arrays ni DATA** (decisión de Sergio): las 256 variables
  son del juego, y los arrays y DATA viven en chunks paginados o en flash, según el
  target, así que leerlos desde `INKEY_MENU` obligaría a paginar en cada pulsación.

## Opciones descartadas

- **Teclas fijadas al compilar** (un `DEFINE` por tecla): coste cero, pero el jugador
  no puede elegir.
- **Teclas en variables del script** (una declaración `MENUKEYS v` que reserva 5
  variables): sin opcode, pero gasta variables.
- **Grupos de teclas sinónimas:** descartados; el joystick que va por teclado se
  elige por tipo con `MENUJOY`, y así teclado y joystick funcionan a la vez sin
  gastar teclas del jugador.
- **Una rutina nativa con `IMPORT`/`CALL`:** obliga a pasarle los argumentos por
  variables y a que el autor importe una librería para algo que debería ser del
  lenguaje.
- **Un prefijo extendido** que abra otra tabla de 128 opcodes: descartado arriba.

## La solución

### Liberar el `0x7D`

`SET_KEMPSTON` no hace nada propio: es una fusión de mirilla. Cuando el script dice
`LET v = KEMPSTON()`, el codegen (`cydc_codegen.py`, en la pasada que crea `SET_D`,
`SET_I`, `RANDOM`, `INKEY`, `SET_XPOS`...) convierte `PUSH_KEMPSTON` + `POP_SET v` en
`SET_KEMPSTON v`.

- **Se quita esa fusión.** `LET v = KEMPSTON()` vuelve a ser `PUSH_KEMPSTON` +
  `POP_SET v`: 3 bytes en vez de 2, con el mismo resultado.
- Es la fusión menos usada: las demás (`SET_D`, `INK_D`, `RANDOM`...) aparecen en
  casi cualquier programa.
- Se borran `OP_SET_KEMPSTON` del runtime y su entrada de `OPCODES`, y el `0x7D` pasa
  al opcode nuevo. El bytecode se compila siempre junto con su runtime, así que no hay
  compatibilidad binaria que guardar.
- **Reserva para el futuro:** `SET_XPOS` y `SET_YPOS` son fusiones igual de poco
  usadas (`LET v = XPOS()`, `LET v = YPOS()`). Si algún día hace falta otro opcode de
  verdad, se pueden liberar del mismo modo, por 1 byte por uso.

### El opcode de configuración: `POP_CONFIG`

- Saca de la pila de la VM un **valor** y un **número de ajuste**, y escribe el valor
  en el byte `CONFIG + ajuste` de la RAM del motor. Un ajuste fuera de rango no hace
  nada.
- Los ajustes son bytes seguidos en un bloque `CONFIG`:

  | Ajuste | Qué es | Valor al arrancar |
  |--------|--------|-------------------|
  | 0 | joystick por teclado | 0 (ninguno) |
  | 1 | tecla de arriba | `q` |
  | 2 | tecla de abajo | `a` |
  | 3 | tecla de izquierda | `o` |
  | 4 | tecla de derecha | `p` |
  | 5 | tecla de seleccionar | espacio |

  El joystick va primero a propósito: `MENUKEY` escribe en `accion + 1`, y como la
  VM satura, una acción calculada fuera de rango (5 o más) acaba en el ajuste 6 o
  más, que se ignora, en vez de pisar el joystick.

- **El autor no ve `POP_CONFIG`:** lo usan las sentencias de abajo. Un ajuste nuevo
  en el futuro (otro byte de configuración del motor) añade una fila a la tabla, una
  sentencia al compilador y el código del motor que lo lea, pero **ningún opcode**.

### `MENUKEY accion, tecla`

- **`accion`:** 0 arriba, 1 abajo, 2 izquierda, 3 derecha, 4 seleccionar (el orden
  de Q, A, O, P y espacio). El autor les pone nombre con `CONST` si quiere.
- **`tecla`:** el código que devuelve `INKEY`; 0 deja la acción sin tecla.
- Se ejecuta: el compilador apila `accion + 1` y `tecla` y emite `POP_CONFIG`. Si
  `accion` es una constante (también un `CONST`), el codegen la comprueba (0..4, si
  no es un error de compilación) y suma el 1 (operando `CONSTANT_SETTING`); si es una
  expresión, la suma la hace la VM con `ADD`, que satura.

### `MENUJOY tipo`

- **`tipo`:** 0 ninguno, 1 Sinclair puerto 1, 2 Sinclair puerto 2, 3 cursor.
- El compilador apila un 0 y `tipo` y emite `POP_CONFIG`. Una constante fuera de
  0..3 es un error de compilación; en ejecución, un tipo desconocido cuenta como 0.
- Las teclas de cada tipo son fijas y van en el código del motor (15 bytes):

  | Tipo | Arriba | Abajo | Izquierda | Derecha | Seleccionar |
  |------|--------|-------|-----------|---------|-------------|
  | 1, Sinclair puerto 1 | 9 | 8 | 6 | 7 | 0 |
  | 2, Sinclair puerto 2 | 4 | 3 | 1 | 2 | 5 |
  | 3, cursor | 7 | 6 | 5 | 8 | 0 |

### Semántica

- **Al arrancar**, las teclas son Q, A, O, P y espacio, y no hay joystick por
  teclado. Un juego que no usa estas sentencias se maneja como ahora (sin la `m`).
- **Teclado y joystick funcionan a la vez:** una pulsación activa una acción si es
  su tecla o la del joystick elegido para esa acción.
- **Siempre funcionan, además:** las flechas con CAPS SHIFT, Enter para seleccionar
  y el Kempston. El jugador nunca se queda sin poder manejar el menú, aunque defina
  mal las teclas.
- **La configuración no se graba con la partida:** `RAMSAVE` y `SAVE` guardan las
  variables, y `CONFIG` está fuera de ellas. Es una preferencia del jugador, así que
  cargar una partida no le cambia los controles.
- **El script no puede leer la configuración** (haría falta otro opcode). Una
  pantalla de redefinir enseña cada tecla en el momento de definirla.
- **Validar es cosa del script.** Si una tecla está en dos acciones, activa las dos.
  Si una tecla del teclado coincide con una del joystick elegido para otra acción
  (por ejemplo, definir `6` como seleccionar con Sinclair 1), activa las dos.

### Ejemplo

```cyd
[[
    CONST KeyUp = 0
    CONST KeyDown = 1
    CONST KeyLeft = 2
    CONST KeyRight = 3
    CONST KeySelect = 4

#Controls
    OPTION GOTO NoJoystick  ]]Teclado o Kempston[[
    OPTION GOTO UseSinclair ]]Sinclair[[
    OPTION GOTO UseCursor   ]]Cursor[[
    OPTION GOTO Redefine    ]]Redefinir teclas[[
    CHOOSE

#NoJoystick
    MENUJOY 0 : GOTO Menu
#UseSinclair
    MENUJOY 1 : GOTO Menu
#UseCursor
    MENUJOY 3 : GOTO Menu

/* tmp es cualquier variable temporal del juego */
#Redefine
    ]]Arriba: [[ LET tmp = INKEY(0) : MENUKEY KeyUp, @tmp : CHAR @tmp : NEWLINE
    ]]Abajo: [[  LET tmp = INKEY(0) : MENUKEY KeyDown, @tmp : CHAR @tmp : NEWLINE
    /* ... */
]]
```

El jugador elige joystick y, aparte, puede redefinir el teclado. La variable
temporal solo se usa durante la pantalla de redefinir; no queda ninguna ocupada.

## Runtime

- **`CONFIG`** (`inkey.asm`): 6 bytes con `DB` y sus valores de arranque, como
  `KEMPSTON_VALUE`. En los seis targets el intérprete está en RAM (también en MLD,
  donde lo que va en flash es el bytecode), así que no hace falta código de arranque.
- **`OP_POP_CONFIG`** (`interpreter.asm`): saca valor y ajuste de la pila de la VM
  (`ix`), comprueba `ajuste < CONFIG_SIZE` y escribe en `CONFIG + ajuste`. Termina en `jp EXEC_LOOP`, sin `JR`
  que salgan del bloque ni `DEFINE`, para que `plan_opcode_layout` pueda moverlo.
- **`INKEY_MENU`:** las comparaciones con `q`, `a`, `o`, `p`, espacio y `m` se
  sustituyen por un bucle sobre las 5 teclas de `CONFIG` y, si el tipo de joystick es
  1..3, sobre las 5 de su fila, con una tabla de 5 máscaras (`UP`, `DOWN`, `LEFT`,
  `RIGHT`, `FIRE`). Una tecla a 0 no coincide con nada (`INKEY` devuelve 0 cuando no
  hay tecla, así que hay que saltarlo antes de comparar). Se mantienen las flechas
  ($08-$0B), Enter y el Kempston.
- **Contratos que no se pueden romper** (el bug de los ceros a la izquierda de
  `8d7d977` salió de uno así):
  - `INKEY_MENU` hoy solo guarda `BC`, y quien la llama cuenta con que `DE` y `HL` no
    cambian (`WAITKEY` guarda la posición en `DE`): la versión nueva tiene que guardar
    todo lo que use;
  - `EXEC_LOOP` entra en cada opcode con el acarreo a 0, y `PRINT_A_BYTE` cuenta con
    ello: `OP_POP_CONFIG` no puede depender de otra cosa ni dejar estado raro;
  - `WAIT_NEXT_PAGE` se llama desde la impresión de texto: tiene que conservar los
    mismos registros que ahora.
- **Condicionado como los demás opcodes:** con `-trim` el compilador define
  `UNUSED_OP_POP_CONFIG` cuando el programa no usa el opcode, y `CONFIG`, las tablas
  y el bucle van dentro de `IFNDEF UNUSED_OP_POP_CONFIG`; entonces `INKEY_MENU`
  compara con sus teclas fijas (como antes, menos la `m`). Sin `-trim`, que es lo
  normal (`trim_interpreter = no`), todos los programas llevan el opcode y usan la
  tabla con sus valores de arranque.

Medido: el intérprete crece **49 bytes** (de 9.797 a 9.846 en `blit`, por ejemplo)
en todos los juegos sin `-trim`. Con `-trim`, solo los que usan `MENUKEY` o
`MENUJOY`.

## Cambios para todos los juegos

- **Fuera la `m`** (decisión de Sergio): se quita de `INKEY_MENU` y de
  `WAIT_NEXT_PAGE`. Seleccionar queda con espacio (o la tecla configurada), Enter y el
  disparo del Kempston.
- **La pausa de página usa `INKEY_MENU`** (decisión de Sergio): `WAIT_NEXT_PAGE`
  espera el bit `FIRE`, como `WAITKEY`. Así el Kempston pasa página, y con `MENUKEY`
  o `MENUJOY` también las teclas configuradas.
- Los dos van en el manual (la frase de la sección de menús que dice «seleccionar con
  `SPACE`, `M` o `ENTER`»), en el tutorial si la menciona, en las notas de la versión
  y en el README de Delerict (que dice «Space, M or Enter»).

## Compilador

- **Lexer:** palabras nuevas `MENUKEY` y `MENUJOY`.
- **Parser:** `MENUKEY varexpression, varexpression` y `MENUJOY varexpression`, como
  `MENUCONFIG`: apilan los valores (y el 5 en `MENUJOY`) y emiten `("POP_CONFIG",)`.
  Con constantes, comprueban los rangos.
- **Codegen:** `"POP_CONFIG": 0x7D` en lugar de `"SET_KEMPSTON"`, y fuera la fusión
  `PUSH_KEMPSTON` → `SET_KEMPSTON`.
- **Runtime:** `OP_POP_CONFIG` en la entrada `0x7D` de `OPCODES`, con su guarda
  `IFNDEF UNUSED_OP_POP_CONFIG`.

## Pruebas

Exhaustivas, por el antecedente del bug de los ceros:

- **La suite completa** antes y después, con los mismos resultados.
- **Bytecode:** los ejemplos generan el mismo bytecode antes y después, salvo los que
  usan `LET v = KEMPSTON()`.
- **`LET v = KEMPSTON()`** sigue dando el mismo valor sin la fusión, con el Kempston
  quieto y con una dirección pulsada.
- **`PRINT` sin ceros a la izquierda** justo después de `MENUKEY` y de `MENUJOY`
  (como `test_print_numbers.py`).
- **En el emulador, en los seis targets** (48K, 128K, +3, esxDOS, MLD y MLD 128),
  ampliando el arnés para que también pulse teclas en MLD:
  - teclas de arranque: Q/A/O/P/espacio mueven y seleccionan; `m` ya no;
  - Enter y las flechas con CAPS SHIFT siguen funcionando;
  - una tecla redefinida funciona y la antigua ya no; una acción sin tecla;
  - acción fuera de rango en ejecución: no cambia nada;
  - `MENUJOY` 1, 2 y 3, pulsando el joystick emulado de ZEsarUX
    (`--joystickemulated` y `set-ui-io-ports`) a la vez que funciona el teclado;
  - el Kempston emulado mueve, selecciona y **pasa página**;
  - la pausa de página acepta espacio, Enter y la tecla de seleccionar configurada, y
    ya no la `m`.
- **Delerict:** la partida completa con el arnés de juego.
- **`dist/`** sincronizado (`test_dist_sync.py`).

## Superficies

- **Resaltador:** `MENUKEY` y `MENUJOY` (submódulo, commit aparte).
- **Manual**, en los dos idiomas: las dos sentencias, la nota de `KEMPSTON()` si
  menciona la fusión, y la frase de las teclas de los menús (sin `M`, con la pausa de
  página).
- **Tutorial:** un ejemplo de pantalla de controles.
- **Notas de la versión:** las sentencias, la `M` y la pausa de página.

## Decisiones de Sergio (nov 2026)

1. **`MENUKEY accion, tecla`** para el teclado y **`MENUJOY tipo`** para el joystick
   que va por teclado, sin grupos de teclas; teclado y joystick a la vez. No se gastan
   variables, ni arrays, ni DATA.
2. **Orden de las acciones:** arriba, abajo, izquierda, derecha, seleccionar.
3. **La pausa de página se arregla** para que use `INKEY_MENU`.
4. **La `m` se quita en todos los juegos.**
5. **No hay prefijo extendido.** Se libera el `0x7D` quitando la fusión
   `SET_KEMPSTON`, y el opcode es **genérico** (`POP_CONFIG`) para que los ajustes
   futuros no gasten más.
