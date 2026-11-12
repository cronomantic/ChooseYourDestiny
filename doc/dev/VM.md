# Máquina virtual de CYD

> **Para quién es.** Para quien toque el intérprete (`src/cydc/cydc/cyd/*.asm`) o
> el generador de código (`cydc_codegen.py`): cómo se ejecuta el bytecode, qué
> reglas tiene que cumplir cada opcode y qué significa cada uno. No hace falta
> para escribir aventuras; el lenguaje está en el manual.
>
> Documentos relacionados: [ARCHITECTURE.md](ARCHITECTURE.md) (la herramienta
> entera: pipeline, targets, memoria por target), [EXPANSION_ABI.md](EXPANSION_ABI.md)
> (la interfaz de las rutinas nativas de `IMPORT`/`CALL`/`ASM`) y los códigos de
> error de sistema en el manual (sección *Códigos de error*).
>
> La tabla de opcodes del final la comprueba `tests/test_vm_doc.py` contra el
> compilador y contra la tabla de saltos del intérprete: si se cambia un opcode,
> el test falla hasta que se actualiza este documento.

---

## 1. Visión general

El compilador traduce el guion a una lista de tuplas `(OPCODE, operandos...)`
(parser), las simplifica (optimizador de mirilla de `code_simple_optimize`, que
fusiona secuencias en opcodes más cortos) y las convierte en bytes repartidos en
bloques de 16 KB como máximo (`code_translate`). El intérprete, escrito en
assembly Z80, ejecuta esos bytes.

Es una máquina de pila de bytes:

- Todos los valores son de **8 bits sin signo** (0-255).
- Las expresiones se evalúan en una **pila de la VM** propia: los opcodes `PUSH_*`
  apilan, los operadores (`ADD`, `CP_EQ`, ...) sacan dos valores y apilan el
  resultado, y los `POP_*` consumen el valor de arriba.
- Las **variables** son los 256 bytes de `FLAGS`.
- El bytecode es **el mismo para los seis targets**; lo que cambia de un target a
  otro está en los módulos `.asm` (ver ARCHITECTURE §5.2).

---

## 2. Registros y estado

| Registro | Uso en el intérprete |
| --- | --- |
| `HL` | Contador de programa de la VM: al entrar en un opcode apunta a su primer operando, y al saltar a `EXEC_LOOP` tiene que apuntar al siguiente opcode. |
| `IX` | Puntero de la pila de la VM (apunta al valor de arriba). |
| `SP` | Pila de la máquina (Z80), separada de la de la VM. |
| `IY` | Variables del sistema de la ROM (`$5C3A`); no se toca. En MLD el arranque lo deja en `$FFFF` y `cyd_mld.asm` lo repone. |
| `A`, `BC`, `DE` | Libres dentro de un opcode. |

Estado en memoria que conviene conocer (`vars.asm` y los ficheros principales
`cyd_tape.asm`, `cyd_plus3.asm`, `cyd_esxdos.asm`, `cyd_mld.asm`):

- `FLAGS`: las variables, alineadas a página (`LOW(FLAGS) = 0`), así que
  `ld d, HIGH FLAGS : ld e, n` apunta a la variable `n`.
- `CHUNK`: el bloque de bytecode en ejecución; `CHUNK_ADDR` y `SCRIPT_BANK`, dónde
  está y en qué banco.
- `DATA_PTR`: el cursor de `READ` sobre los datos de `DATA`.
- `NUM_OPTIONS`, `SELECTED_OPTION`, `SELECTED_OPTION_VALUE` y `OPTIONS_TABLE`: el
  menú.
- `CONFIG` (en `inkey.asm`): el tipo de joystick y las teclas de los menús que
  cambian `MENUKEY` y `MENUJOY`.

---

## 3. El bucle de ejecución

`EXEC_LOOP` (igual en los cuatro ficheros principales):

```
EXEC_LOOP:
    ld d, HIGH OPCODES
    ld e, (hl)                ; el opcode, guardado x2
    ex de, hl
    ld c, (hl)
    inc l
    ld b, (hl)                ; BC = dirección del manejador
    push bc
    ex de, hl
    inc hl                    ; HL = primer operando
    or a                      ; acarreo a 0 al entrar en cada opcode
    ret                       ; salta al manejador
```

- **El opcode se guarda multiplicado por 2.** Así el byte es directamente el
  desplazamiento de su entrada en `OPCODES`, una tabla de 128 entradas de 2 bytes
  alineada a página. Por eso caben 128 opcodes como máximo (`0x00`-`0x7F`), y hoy
  están **todos ocupados**. El compilador lo hace en `_opcode_byte()`.
- **El acarreo llega a 0.** Hay rutinas que cuentan con ello (por ejemplo,
  `PRINT_A_BYTE` imprime sin ceros por delante solo con el acarreo a 0). Durante el desarrollo
  de la 1.7.0 un cambio rompió esta regla y los números salían con ceros
  delante.
- **Cada opcode termina** con `jp EXEC_LOOP`, o apilando `EXEC_LOOP` como
  dirección de vuelta y saltando a una rutina que acaba en `ret`
  (`ld de, EXEC_LOOP : push de : jp INK`).

---

## 4. Memoria

Mapa común a todos los targets (direcciones de un juego de 48K; las de la zona de
variables son fijas, las del intérprete dependen de lo que se incluya):

| Dirección | Contenido |
| --- | --- |
| hasta `$5CFF` | Variables de la ROM; la pila de la máquina crece hacia abajo desde `$5D00` (`INITIAL_STACK`). |
| `$5D00` | `FLAGS`: las 256 variables. |
| `$5E00` | `OPTIONS_TABLE`: 32 opciones de 8 bytes. |
| `$5F00`... | Buffer de texto y el resto de variables del intérprete. |
| `$6000` | `SCREEN_BUFFER_PXL` y `SCREEN_BUFFER_ATT`: el almacén de imágenes (no es un segundo buffer de pantalla). |
| `$7B00` | Copia de la partida (`SAVE_START`), ventanas y `END_VARS`. |
| `END_VARS`-`$7FFF` | Pila de la VM: crece hacia abajo desde `$8000` (`INT_STACK_ADDR`). |
| `$8000` | Intérprete (`START_INTERPRETER`); `$8070` `TMP_AREA`, `$8080` la rutina de interrupción (IM 2, 50 Hz) y su tabla alineada. |
| `OPCODES` | La tabla de saltos, alineada a página. |
| después | Abreviaturas, juego de caracteres, índice de recursos y tabla de rutinas nativas. |
| hasta `$FFFF` | Bloque 0 del bytecode (en 48K, todo el guion; en 128K, el primero). |

Los bloques de bytecode de más de 16 KB van a otros bancos, vistos en `$C000`.
`LOAD_CHUNK` busca el bloque en el índice (tipo `TYPE_TXT`) y pagina su banco;
en MLD pagina su slot de la flash del Dandanator. Los límites del intérprete (32 KB en 48K, 16 KB en
los demás) y el reparto de bancos de cada target están en ARCHITECTURE §6.

---

## 5. Variables y aritmética

- Las variables son `FLAGS[0..255]` y se guardan enteras con la partida
  (`SAVE_FLAGS`).
- `ADD` y `SUB` **saturan**: una suma que pasa de 255 da 255 y una resta que baja
  de 0 da 0. No dan la vuelta.
- Las comparaciones dejan **0 o 1**. `IF_GOTO` salta si el valor no es 0 e
  `IF_N_GOTO` si es 0.
- `AND` y `OR` operan bit a bit; con valores 0/1 funcionan como operadores
  lógicos. `NOT` cambia 0 por 1 y al revés (`xor 1`); `NOT_B` invierte todos los
  bits.
- `MIN(a, b)` devuelve el **mayor** de los dos y `MAX(a, b)` el **menor**: el
  manual los define como "acotar `a` a un mínimo" y "a un máximo".
- Los valores de 16 o 32 bits (`WORD`, `DWORD`, la librería `math16_32`) son
  varias variables seguidas. La VM no los conoce: el compilador emite una
  asignación por byte.

---

## 6. La pila de la VM

```
    MACRO POP_INT_STACK       ; A = valor de arriba
    ld a, (ix+0)
    inc ix
    ENDM

    MACRO PUSH_INT_STACK      ; apila A
    dec ix
    ld (ix+0), a
    ENDM
```

- Con dos operandos, el primero se apila antes: en `a - b`, `b` está arriba
  (`(ix+0)`) y `a` debajo (`(ix+1)`). Las macros `OP_2PARAM_GET_STACK` y
  `OP_2PARAM_STORE_STACK` lo hacen para los operadores binarios.
- Los opcodes `POP_*` de varios parámetros (`POP_MENUCONFIG`, `POP_ALL_BLIT`...)
  leen los valores con `(ix+n)` y suben `IX` de una vez.
- **`GOSUB` usa la misma pila**: guarda un marco de 3 bytes (bloque y dirección de
  vuelta) y `RETURN` lo saca. El compilador garantiza que no quedan valores de
  expresiones en la pila al hacer `GOSUB`.
- Con `--debug-stack` (`STACK_CHECK`) se comprueba que un `GOSUB` no baje de
  `END_VARS + 64` (error de sistema 10) y que un `RETURN` tenga adónde volver
  (error 9). Sin la opción no se añade código.

---

## 7. Codificación del bytecode

- **Opcode**: 1 byte, el número x2.
- **Operandos**: siguen al opcode, 1 byte cada uno, en el orden de la tupla.
- **Etiquetas**: 3 bytes, bloque y dirección (little-endian). El compilador deja
  el nombre y lo resuelve en `symbol_replacement` cuando ya sabe dónde cae.
- **Valores de 16 bits** (`WAIT`, `PAUSE`, `CHOOSE IF WAIT`, `RANDOMIZE`,
  `RESTORE`, `TYPERATE`): little-endian, el byte bajo primero.
- **Texto** (`TEXT`): cada byte se guarda como `255 - c`. Si el valor recuperado
  es 128 o más, es la abreviatura `c & $7F`. El texto termina con el byte `$F5`
  (el 10 codificado).
- **Arrays**: van dentro del bytecode, precedidos de `SKIP_ARRAY` y de su longitud
  menos 1. La etiqueta del array apunta a ese byte de longitud. En MLD, donde el
  bytecode está en flash, el compilador los recoloca en RAM (ver
  [MLD_WRITABLE_ARRAYS.md](MLD_WRITABLE_ARRAYS.md)) y el operando pasa a ser
  `[banco, dirección]`, con el banco `$FE` (`ARR_RESIDENT_BANK`) para la zona
  residente de MLD de 48K.
- **Cambio de bloque**: cuando una sentencia no cabe en el bloque, el compilador
  pone un `GOTO` al principio del siguiente. Un texto largo se puede partir
  (`slice_text`).

---

## 8. Familias de opcodes y fusiones

Los nombres siguen un patrón:

| Sufijo o prefijo | El valor sale de... | Ejemplo |
| --- | --- | --- |
| `_D` | un operando literal | `INK_D 2` |
| `_I` | una variable (operando = número de variable) | `INK_I v` |
| `_DI` | una variable cuyo valor es el número de otra (`[v]`) | `PUSH_DI v` |
| `POP_` | la pila de la VM | `POP_INK` |
| `POP_ALL_` | la pila, todos los parámetros | `POP_ALL_BLIT` |
| `PUSH_` | apila el resultado | `PUSH_XPOS` |

El parser genera siempre la forma de pila (`PUSH_D 2`, `POP_INK`) y el optimizador
la fusiona en la corta (`INK_D 2`). Las fusiones de `code_simple_optimize` son:

- `PUSH_D`/`PUSH_I`/`PUSH_DI`/`PUSH_RANDOM`/`PUSH_INKEY`/`PUSH_XPOS`/`PUSH_YPOS` +
  `POP_SET` → `SET_D`, `SET_I`, `SET_DI`, `RANDOM`, `INKEY`, `SET_XPOS`,
  `SET_YPOS`.
- `PUSH_D`/`PUSH_I` + `POP_INK`, `POP_PAPER`, `POP_BORDER`, `POP_BRIGHT`,
  `POP_FLASH`, `POP_PRINT`, `POP_CHAR`, `POP_PICTURE`, `POP_DISPLAY`, `POP_SFX`,
  `POP_TRACK`, `POP_PLAY`, `POP_LOOP` → su `_D` o `_I` (para `BORDER`, `BRIGHT` y
  `FLASH` solo existe la `_D`).
- `PUSH_D`/`PUSH_I` + `POP_PUSH_I` → `PUSH_I`/`PUSH_DI`.
- `NOT` + `IF_N_GOTO` → `IF_GOTO`.
- Todos los parámetros con `PUSH_D` + `POP_AT`, `POP_MENUCONFIG`, `POP_FILLATTR`,
  `POP_ALL_PUTATTR`, `POP_ALL_BLIT` → `AT`, `MENUCONFIG`, `FILLATTR`, `PUTATTR`,
  `BLIT`; con solo los primeros constantes → `POP_PUTATTR`, `POP_BLIT`.

**Las fusiones son opcionales**: sin optimizador el programa funciona igual, solo
ocupa más. Por eso son la reserva para liberar un opcode cuando haga falta uno
nuevo. Así se liberó `0x7D` (la fusión `SET_KEMPSTON`) para `POP_CONFIG`. Las
siguientes candidatas son `SET_XPOS` y `SET_YPOS`, poco usadas: liberarlas cuesta
un byte de bytecode por uso y ahorra su manejador.

---

## 9. `-trim` y la tabla de saltos

- `get_unused_opcodes()` calcula los opcodes que el programa no usa y
  `get_unused_opcodes_defines()` emite un `DEFINE UNUSED_OP_<NOMBRE>` por cada
  uno.
- Cada manejador va dentro de `IFNDEF UNUSED_OP_<NOMBRE>`, y su entrada en
  `OPCODES` es doble:

  ```
      IFNDEF UNUSED_OP_INK_D
      DW OP_INK_D
      ENDIF
      IFDEF UNUSED_OP_INK_D
      DW ERROR_NOP
      ENDIF
  ```

  Así la tabla conserva sus 128 posiciones con o sin `-trim`. `ERROR_NOP` da el
  error de sistema 6.
- `END`, `TEXT`, `GOTO`, `GOSUB`, `RETURN`, `IF_GOTO` e `IF_N_GOTO` están siempre
  (sin guarda).
- **El nombre de la guarda tiene que ser exactamente el del compilador.** Si no
  coincide, el manejador no se quita nunca o la tabla pierde una entrada y todos
  los opcodes de detrás se desplazan. `tests/test_vm_doc.py` lo comprueba.
- Un manejador no puede saltar a etiquetas de otro (por ejemplo, un `jr 1f` que
  acaba en el `1:` del siguiente): con `-trim` el otro puede no estar.
- Un manejador que usa una rutina compartida la pide con un `DEFINE` (por ejemplo,
  `DEFINE GET_ATTR_ADDR_USED`), y la rutina va en `IFDEF ..._USED` después.
- **Disposición**: `OPCODES` va alineada a página, y el hueco de delante (hasta
  255 bytes) se rellena: `plan_opcode_layout()` (`cyd.py`) ensambla una vez para
  medir y mueve detrás de la tabla los manejadores que caben en el hueco. Solo se
  mueven los que acaban en `jp`/`ret`, no tienen `jr`/`djnz` que entren o salgan
  y no hacen `DEFINE`.

---

## 10. Errores de sistema y depuración

- `SYS_ERROR` (con el número en `A`) pinta `SYSTEM ERROR No:n` y se queda
  parado. La lista de errores está en el manual.
- Con `--debug-errors` (`DEBUG_ERRORS`), los opcodes que pueden fallar ejecutan
  `DEBUG_POS`, que guarda su posición en `DBG_PC`. El error añade el bloque y la
  dirección, y el `.map` que escribe el compilador lo traduce a fichero y línea.
  Sin la opción no se añade código.

---

## 11. Rarezas conocidas

- **`TYPERATE` leía su valor al revés antes de la 1.7.0.** El compilador lo guarda
  little-endian y `OP_TYPERATE` lo cargaba con el primer byte en `D`, así que
  `TYPERATE n` ponía una pausa de `(n & 255) * 256 + (n >> 8)`: `TYPERATE 1`
  valía 256 vueltas y `TYPERATE 256`, 1. Desde la 1.7.0 la pausa es `n`; un juego
  antiguo con `TYPERATE n` (`n` de 1 a 255) necesita `TYPERATE n*256` para ir a la
  misma velocidad. Cada vuelta del bucle de espera son 31 ciclos.

---

## 12. Cómo añadir o cambiar un opcode

1. **Buscar sitio.** No quedan números libres: hay que liberar una fusión (§8) o
   reutilizar un opcode.
2. **Compilador**: el nombre y el número en `CydcCodegen.opcodes`; el parser
   emite la tupla, y si hay una forma corta, su fusión en `code_simple_optimize`.
3. **Intérprete**: el manejador `OP_<NOMBRE>` en `interpreter.asm` dentro de
   `IFNDEF UNUSED_OP_<NOMBRE>`, y su entrada doble en `OPCODES` en la posición de
   su número.
4. **Reglas del manejador**: dejar `HL` en el siguiente opcode, respetar `IX`
   salvo para apilar o desapilar, no tocar `IY`, no saltar dentro de otro
   manejador, no contar con nada de los registros salvo el acarreo a 0 y llamar a
   `DEBUG_POS` si puede acabar en error de sistema.
5. **Comprobar**: `tests/test_vm_doc.py` (y actualizar la tabla de abajo), una
   prueba en el emulador con y sin `-trim` y el tamaño del intérprete en 48K.
6. **Documentar**: manual, tutorial y resaltador si cambia el lenguaje.

---

## 13. Tabla de opcodes

Operandos: los bytes que siguen al opcode. Pila: lo que saca y lo que apila; el
valor de arriba va a la derecha (`a b → r` saca `b` y luego `a`, y apila `r`).
"Fusión" quiere decir que solo la genera el optimizador (§8).

<!-- OPCODES:BEGIN -->
| Código | Opcode | Operandos | Pila | Qué hace |
| --- | --- | --- | --- | --- |
| `0x00` | `END` | | | Termina el programa: para la música y reinicia. |
| `0x01` | `TEXT` | texto hasta `$F5` | | Imprime texto con abreviaturas (§7). |
| `0x02` | `GOTO` | etiqueta (3) | | Salta; carga el bloque si es otro. |
| `0x03` | `GOSUB` | etiqueta (3) | `→ marco` | Llamada: apila un marco de vuelta de 3 bytes. |
| `0x04` | `RETURN` | | `marco →` | Vuelve del último `GOSUB`. |
| `0x05` | `MARGINS` | col, fila, ancho, alto | | `MARGINS`. |
| `0x06` | `CENTER` | | | `CENTER`. |
| `0x07` | `AT` | col, fila | | `AT` con constantes (fusión). |
| `0x08` | `SET_D` | var, valor | | `var = valor` (fusión). |
| `0x09` | `SET_I` | var, var2 | | `var = @var2` (fusión). |
| `0x0A` | `POP_SET` | var | `v →` | `var = v`. |
| `0x0B` | `PUSH_D` | valor | `→ valor` | Apila un literal. |
| `0x0C` | `PUSH_I` | var | `→ @var` | Apila una variable. |
| `0x0D` | `IF_GOTO` | etiqueta (3) | `v →` | Salta si `v` no es 0. |
| `0x0E` | `IF_N_GOTO` | etiqueta (3) | `v →` | Salta si `v` es 0. |
| `0x0F` | `PUSH_INKEY` | modo | `→ tecla` | `INKEY`: con modo 0 espera una tecla; con otro, no. |
| `0x10` | `PUSH_RANDOM` | límite | `→ n` | Aleatorio de 0 a `límite` (255: sin límite). |
| `0x11` | `NOT` | | `v → v xor 1` | `NOT` lógico. |
| `0x12` | `NOT_B` | | `v → ~v` | Invierte los bits. |
| `0x13` | `AND` | | `a b → a and b` | Bit a bit. |
| `0x14` | `OR` | | `a b → a or b` | Bit a bit. |
| `0x15` | `ADD` | | `a b → a+b` | Satura en 255. |
| `0x16` | `SUB` | | `a b → a-b` | Satura en 0. |
| `0x17` | `CP_EQ` | | `a b → 0/1` | `a = b`. |
| `0x18` | `CP_NE` | | `a b → 0/1` | `a <> b`. |
| `0x19` | `CP_LE` | | `a b → 0/1` | `a <= b`. |
| `0x1A` | `CP_ME` | | `a b → 0/1` | `a >= b`. |
| `0x1B` | `CP_LT` | | `a b → 0/1` | `a < b`. |
| `0x1C` | `CP_MT` | | `a b → 0/1` | `a > b`. |
| `0x1D` | `INK_D` | valor | | `INK` (fusión). |
| `0x1E` | `PAPER_D` | valor | | `PAPER` (fusión). |
| `0x1F` | `BORDER_D` | valor | | `BORDER` (fusión). |
| `0x20` | `PRINT_D` | valor | | `PRINT` de un número (fusión). |
| `0x21` | `INK_I` | var | | `INK` (fusión). |
| `0x22` | `PAPER_I` | var | | `PAPER` (fusión). |
| `0x23` | `READ` | | `→ byte` | Siguiente byte de `DATA`; al acabar vuelve al principio. |
| `0x24` | `PRINT_I` | var | | `PRINT` de una variable (fusión). |
| `0x25` | `BRIGHT_D` | valor | | `BRIGHT` (fusión). |
| `0x26` | `FLASH_D` | valor | | `FLASH` (fusión). |
| `0x27` | `RESTORE` | posición (2) | | Pone el cursor de `READ`. |
| `0x28` | `DATAEND` | | `→ 0/1` | 1 si ya se han leído todos los datos. |
| `0x29` | `PICTURE_D` | imagen | | `PICTURE`: carga la imagen en el almacén (fusión). |
| `0x2A` | `DISPLAY_D` | valor | | `DISPLAY`: si no es 0, copia la imagen a la pantalla (fusión). |
| `0x2B` | `PICTURE_I` | var | | `PICTURE` (fusión). |
| `0x2C` | `DISPLAY_I` | var | | `DISPLAY` (fusión). |
| `0x2D` | `RANDOM` | var, límite | | `var = ` aleatorio (fusión). |
| `0x2E` | `OPTION` | tipo, etiqueta (3) | | Declara una opción; tipo 0 `GOTO`, `$FF` `GOSUB`. |
| `0x2F` | `WAITKEY` | | | Espera la tecla de seleccionar. |
| `0x30` | `INKEY` | var, modo | | `var = INKEY` (fusión). |
| `0x31` | `WAIT` | cincuentavos (2) | | Espera. |
| `0x32` | `PAUSE` | cincuentavos (2) | | Espera o hasta que se pulse seleccionar. |
| `0x33` | `CHOOSE` | | | Menú. |
| `0x34` | `CHOOSE_W` | cincuentavos (2), tipo, etiqueta (3) | | `CHOOSE IF WAIT`. |
| `0x35` | `TYPERATE` | pausa (2) | | Pausa entre caracteres, en vueltas de 31 ciclos (§11). |
| `0x36` | `CLEAR` | | | Borra la ventana. |
| `0x37` | `PAGEPAUSE` | valor | | `PAGEPAUSE`. |
| `0x38` | `CHAR_D` | código | | `CHAR` (fusión). |
| `0x39` | `TAB` | n | | Imprime `n` espacios. |
| `0x3A` | `REPCHAR` | código, n | | Imprime un carácter `n` veces. |
| `0x3B` | `SFX_D` | efecto | | `SFX` (fusión). |
| `0x3C` | `SFX_I` | var | | `SFX` (fusión). |
| `0x3D` | `TRACK_D` | pista | | `TRACK`: carga una pista (fusión). |
| `0x3E` | `TRACK_I` | var | | `TRACK` (fusión). |
| `0x3F` | `PLAY_D` | valor | | `PLAY` (fusión). |
| `0x40` | `PLAY_I` | var | | `PLAY` (fusión). |
| `0x41` | `LOOP_D` | valor | | `LOOP` (fusión). |
| `0x42` | `LOOP_I` | var | | `LOOP` (fusión). |
| `0x43` | `RANDOMIZE` | semilla (2) | | Semilla del aleatorio; 0 la toma del contador de cuadros. |
| `0x44` | `POP_AT` | | `col fila →` | `AT`. |
| `0x45` | `NEWLINE` | n | | `n` saltos de línea. |
| `0x46` | `SET_DI` | var, var2 | | `var = [var2]` (fusión). |
| `0x47` | `POP_SET_DI` | var | `v →` | `[var] = v`. |
| `0x48` | `PUSH_DI` | var | `→ [var]` | Apila la variable cuyo número está en `var`. |
| `0x49` | `POP_INK` | | `v →` | `INK`. |
| `0x4A` | `POP_PAPER` | | `v →` | `PAPER`. |
| `0x4B` | `POP_BORDER` | | `v →` | `BORDER`. |
| `0x4C` | `POP_BRIGHT` | | `v →` | `BRIGHT`. |
| `0x4D` | `POP_FLASH` | | `v →` | `FLASH`. |
| `0x4E` | `POP_PRINT` | | `v →` | `PRINT`. |
| `0x4F` | `CHAR_I` | var | | `CHAR` (fusión). |
| `0x50` | `POP_CHAR` | | `v →` | `CHAR`. |
| `0x51` | `POP_PICTURE` | | `v →` | `PICTURE`. |
| `0x52` | `POP_DISPLAY` | | `v →` | `DISPLAY`. |
| `0x53` | `POP_SFX` | | `v →` | `SFX`. |
| `0x54` | `POP_TRACK` | | `v →` | `TRACK`. |
| `0x55` | `POP_PLAY` | | `v →` | `PLAY`. |
| `0x56` | `POP_LOOP` | | `v →` | `LOOP`. |
| `0x57` | `POP_PUSH_I` | | `n → @n` | Cambia el valor de arriba por la variable de ese número. |
| `0x58` | `SET_XPOS` | var | | `var = XPOS()` (fusión). |
| `0x59` | `SET_YPOS` | var | | `var = YPOS()` (fusión). |
| `0x5A` | `PUSH_XPOS` | | `→ col` | `XPOS()`. |
| `0x5B` | `PUSH_YPOS` | | `→ fila` | `YPOS()`. |
| `0x5C` | `MIN` | | `a b → r` | `MIN(a, b)`: el mayor de los dos (§5). |
| `0x5D` | `MAX` | | `a b → r` | `MAX(a, b)`: el menor de los dos (§5). |
| `0x5E` | `BLIT` | 6 parámetros | | `BLIT` con constantes (fusión). |
| `0x5F` | `POP_BLIT` | 4 parámetros | `col fila →` | `BLIT` con el destino variable (fusión). |
| `0x60` | `MENUCONFIG` | 4 parámetros | | `MENUCONFIG` con constantes (fusión). |
| `0x61` | `POP_MENUCONFIG` | | `x y def ver →` | `MENUCONFIG`. |
| `0x62` | `PUSH_IS_DISK` | | `→ 0/1` | `ISDISK()`. |
| `0x63` | `BACKSPACE` | n | | Borra `n` caracteres. |
| `0x64` | `RAMLOAD` | var, n | | Recupera variables de la copia en RAM. |
| `0x65` | `RAMSAVE` | var, n | | Copia variables en RAM. |
| `0x66` | `POP_SLOT_LOAD` | | `ranura →` | `LOAD`. |
| `0x67` | `POP_SLOT_SAVE` | var, n | `ranura →` | `SAVE`. |
| `0x68` | `PUSH_SAVE_RESULT` | | `→ r` | `SAVERESULT()`. |
| `0x69` | `FADEOUT` | col, fila, ancho, alto | | `FADEOUT`. |
| `0x6A` | `FILLATTR` | 5 parámetros | | `FILLATTR` con constantes (fusión). |
| `0x6B` | `PUTATTR` | 4 parámetros | | `PUTATTR` con constantes (fusión). |
| `0x6C` | `POP_PUTATTR` | 2 parámetros | `2 valores →` | `PUTATTR` con parte variable (fusión). |
| `0x6D` | `CHOOSE_CH` | etiqueta (3) | | `CHOOSE IF CHANGED`. |
| `0x6E` | `PUSH_OPTION_ST` | n | `→ v` | `NUMOPTIONS()` (0), `OPTIONSEL()` (1), `OPTIONVAL()` (2). |
| `0x6F` | `CLEAR_OPTIONS` | | | `CLEAROPTIONS`. |
| `0x70` | `PUSH_GET_ATTR` | | `a b → atributo` | `GETATTR()`. |
| `0x71` | `POP_ALL_BLIT` | | `6 valores →` | `BLIT`. |
| `0x72` | `SHIFT_R` | | `v n → v>>n` | Desplazamiento a la derecha. |
| `0x73` | `SHIFT_L` | | `v n → v<<n` | Desplazamiento a la izquierda. |
| `0x74` | `POP_ALL_PUTATTR` | | `4 valores →` | `PUTATTR`. |
| `0x75` | `POP_FILLATTR` | | `5 valores →` | `FILLATTR`. |
| `0x76` | `POP_VAL_OPTION` | tipo, etiqueta (3) | `v →` | `OPTION VALUE(v)`. |
| `0x77` | `WINDOW` | n | | Cambia de ventana (0-7). |
| `0x78` | `CHARSET` | n | | Cambia de juego de caracteres. |
| `0x79` | `SKIP_ARRAY` | longitud - 1, datos | | Salta los datos de un array (§7). |
| `0x7A` | `PUSH_VAL_ARRAY` | array (3) | `i → array[i]` | Lee un elemento; fuera de rango, error 7. |
| `0x7B` | `POP_VAL_ARRAY` | array (3) | `v i →` | `array[i] = v`; fuera de rango, error 7. |
| `0x7C` | `PUSH_LEN_ARRAY` | array (3) | `→ longitud - 1` | `LASTPOS()`. |
| `0x7D` | `POP_CONFIG` | | `s v →` | `CONFIG[s] = v` (`MENUKEY`, `MENUJOY`); un `s` fuera de rango no hace nada. |
| `0x7E` | `PUSH_KEMPSTON` | | `→ v` | `KEMPSTON()`. |
| `0x7F` | `EXTERN` | rutina (3), uso | `→ v` si uso 1 | `CALL` a una rutina nativa ([EXPANSION_ABI.md](EXPANSION_ABI.md)). |
<!-- OPCODES:END -->
