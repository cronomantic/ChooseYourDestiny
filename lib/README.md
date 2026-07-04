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
