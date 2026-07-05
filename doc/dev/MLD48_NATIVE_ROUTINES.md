# Rutinas nativas (IMPORT/CALL) en el strict mld (48K Dandanator)

> Estado: **✅ IMPLEMENTADO Y VERIFICADO EN EMULADOR (jul 2026).** Rama en la colocación
> de externs de `cydc.py` (`elif model == "mld"`): reusa `ARR_POOL`/`ARR_INIT` (cero asm
> nuevo, cero cambio de loader). Verificado: rutina simple (42/99/123), **librería
> `math16_32` real** (add32: 511), **automodificable** y **`DEFS`** (88/55 → RAM
> escribible confirmada), y **array+rutina sin colisión** (arrays intactos + rutina OK).
> Assert de invariante `ARR_POOL == bank0_offset + 7·num_entradas` en `do_asm_mld`
> (anti-colisión, falla el build si la fórmula se desalinea). Tests: `test_extern.py`
> (`test_import_call_mld`, `test_import_call_mld_writable_ram`).
>
> Motivación: las librerías `math16_32` y
> `strings` ya son **nativas** (bloques `ASM mathcore`/`strcore`), así que hoy **NO
> compilan** en `-m mld` (el compilador rechaza IMPORT/CALL en strict mld,
> `cydc.py:1122`). Cualquier guion que use math/strings queda sin ese target.
> Ver [[project-extern-pending]], [[reference-mld-architecture]], [[project-math-library]].

## 1. Por qué es más fácil de lo que parece

- **El runtime ya está.** El strict mld **no define `OP_EXTERN_BANKED`**, así que el
  handler `OP_EXTERN` usa su rama `ELSE` = **`call` directo**. Es exactamente lo que
  necesita una rutina residente. **No se toca `interpreter.asm`.**
- Falta solo la **colocación en el build** (`cyd.py`/`cydc.py`): hoy hay dos ramas —
  48k "residente al final del bank 0" y "128k/+3/mld128 en banco `$C000` vía `$7FFD`" —
  y el strict mld no es ninguna: su "bank 0" va a **slots flash** (solo lectura), no a
  un residente que se cargue entero.

## 2. Modelo de memoria del strict mld (verificado)

```
$0000..$3FFF   ventana de slot flash del Dandanator (bytecode/texto/gráficos, streaming)
START_INTERPRETER .. SIZE_INTERPRETER   imagen del INTÉRPRETE (guardada en flash, SAVETAP,
                                        cargada RESIDENTE al arrancar por loadermld)
   ... dentro: INDEX, EXTERN_DISPATCH, ARR_INIT_TABLE  (todos @{...} DEFB)
ARR_POOL:      RAM residente JUSTO DESPUÉS del image (NO guardada); ARR_INIT copia
               los DIM de flash→ARR_POOL al arrancar (writable)
```

Presupuesto residente: `$A95F–$EFFF` (~12–18 KB según tamaño del intérprete) +
`$E000–$FAFF` liberado. `SCREEN_BUFFER $6000–$7AFF` sagrado. Sin música (sin bancos).

## 3. Diseño (decisión de Sergio): la rutina se COPIA a un pool residente, como los arrays

**Requisito duro:** una rutina puede ser **automodificable** o usar **`DEFS`** como
scratch propio → escribe sobre su propio espacio → **debe estar en RAM escribible** en
ejecución. Es EXACTAMENTE el caso de los `DIM` en strict mld (viven en flash de solo
lectura; las escrituras se perderían) → por eso se copian a `ARR_POOL`. **No hay opción:
la rutina se trata igual que un array.**

Mecanismo (gemelo de `ARR_POOL`/`ARR_INIT`, [[reference-mld-architecture]]):

- **`EXTERN_POOL`**: región de RAM residente (tras `ARR_POOL`, también NO guardada). Cada
  rutina nativa se **ensambla en su dirección final dentro de `EXTERN_POOL`** (ORG
  = base del pool + offset acumulado; conocido tras el size-pass, como el ORG de los
  arrays reubicados).
- Los **bytes de la rutina viven en flash** (como recurso/chunk, o inline como el
  inicializador de un array — flash-readable).
- **`EXTERN_INIT`** (gemelo de `ARR_INIT`, en `START_LOADING`): al arrancar copia cada
  rutina de flash→`EXTERN_POOL` (reusa `LOAD_CHUNK`/`SET_DAN_BANK` + `LDIR`). Fresca en
  cada arranque → los automodificados NO persisten (correcto).
- El `CALL` va con **`call` directo** a la dirección en `EXTERN_POOL` (handler `ELSE`, ya
  existe — el strict mld no define `OP_EXTERN_BANKED`). Operando `[marcador_residente,
  pool_addr]`, análogo al `[0xFE, pool_off]` de los arrays (aquí es la dirección absoluta
  del pool porque es CÓDIGO que corre en su ORG, no un dato accedido por offset).
- Coste: ~1 KB (ambas libs) en `EXTERN_POOL` (RAM residente) — trivial frente a los
  ~12–18 KB; y otro ~1 KB en flash (la copia origen).

**Automodificable / `DEFS`**: al correr desde `EXTERN_POOL` (RAM), la automodificación y
el scratch `DEFS` funcionan igual que en 48k. (Enfoque descartado "rutina dentro de la
imagen del intérprete": aunque el intérprete corre en `$8000` RAM, es frágil y mezcla la
rutina con el motor; el pool con copia es el patrón correcto y ya probado con arrays.)

## 4bis. Refinamiento verificado en código: reusar `ARR_POOL`/`ARR_INIT` tal cual

`ARR_INIT` copia `(chunk, src_off) → ARR_POOL+pool_off` para cualquier entrada; no
distingue dato de código. Así que las rutinas nativas del strict mld son **entradas más
en `ARR_INIT_TABLE`** y viven en `ARR_POOL` (tras los arrays). **Cero asm nuevo.**

Fórmulas (derivadas de `cydc.py:929` y del layout del intérprete, a verificar en emulador):
- `num_entries = nº_arrays + nº_rutinas`; `ARR_POOL = bank0_offset + 7·num_entries`
  (7 = tamaño de entrada strict mld; el `+7·num_entries` es la tabla, que en el size-pass
  es un stub de 1 byte).
- Cada rutina: `ORG = ARR_POOL + arr_pool_size + offset_acumulado` (arrays primero).
- Bytes de la rutina → **apéndanse al chunk 0** (slot flash del bytecode); `src_off` =
  `len(available_banks[0])` antes de apéndar (slot-relativo, `bank_offset_list=[0,0]`).
- Entrada `arr_init_table`: `(nombre, chunk=0, src_off, pool_off, nbytes)` (5-tupla, como
  los arrays residentes).
- `CALL` → operando `[0, ORG]`; handler `ELSE` (directo), idéntico al 48k.

## 4. Flujo de colocación (en `cyd.py`/`cydc.py`, rama nueva para `model=="mld"`)

Combina la maquinaria de externs (assemble aislado, size estable, late-patch) con la de
reubicación de arrays residentes (`arr_init_table`/`ARR_POOL`/`ARR_INIT`):

1. **Size-pass**: medir el intérprete (incl. `EXTERN_INIT` + su tabla de copia) y
   `arr_pool_size`; medir el tamaño de cada rutina (assemble a ORG provisional).
2. Calcular `EXTERN_POOL` base = fin de `ARR_POOL` (= `$8000` + `SIZE_INTERPRETER` +
   `arr_pool_size`) y el **ORG residente** de cada rutina (consecutivo en el pool).
3. **Re-ensamblar** cada rutina en su ORG final (chequeo de tamaño estable, ya en
   `_place_block`). Guardar sus bytes como recurso en flash + una entrada en la tabla
   `EXTERN_INIT` (dest=ORG, src=chunk/offset, nº bytes) — gemela de `arr_init_table`.
4. **Late-patch** de cada `CALL` con `[marcador, pool_addr]`.
5. Quitar `mld` del gate de error (`cydc.py:1122`); `relocate_externs_resident` análogo a
   `relocate_arrays_resident`.

`CYD_CALL`/`USES`, broker de arrays y `CYD_SYSCALL` (que las libs usan para `print`) ya
son servicios residentes del intérprete alcanzables por dirección; funcionan igual.

## 5bis. Gotchas descubiertos al implementar (la suite completa los cazó)

- **Pantalla de carga (intro screen):** `MLD_INTRO_SCR_DATA` va dentro de la imagen
  guardada ANTES de `INDEX`, pero el size-pass la stubbea. La fórmula debe sumar su
  tamaño comprimido: `ARR_POOL = bank0_offset + 7·num_entradas + tamaño_intro_scr_zx7`.
  (Sin esto, con pantalla de carga la rutina cae en la dirección equivocada.)
- **pyZX7 es O(n²): ~48 s comprimir una pantalla de 6912 bytes.** NO recomprimir 3 veces
  (fórmula + assert + intro data) → +96 s. **NO cachear con `lru_cache` global**: persiste
  entre builds/tests y **rompe los tests de intro-screen que parchean `zx7_compress_data`
  con valores distintos** (el caché devuelve el del primer test). Solución correcta:
  `cydc.py` comprime UNA vez (para la fórmula, solo si hay externs Y pantalla) y **pasa el
  `arr_pool` ya calculado a `do_asm_mld` vía `resident_pool_base`**; el assert solo COMPARA
  (no recomprime). Sin externs+pantalla → 0 compresiones extra.
- **El assert va en `do_asm_mld`, que se testea unitariamente con `bank0_offset` MOCK.**
  Por eso solo corre cuando `resident_pool_base is not None` (cydc.py lo pasa SOLO si hay
  rutinas nativas strict mld); los tests unitarios (que no lo pasan) lo saltan.
- **`cyd.py` no importaba `sys`** — hubo que añadirlo (el assert usa `sys.exit`, con
  mensaje plano SIN `_()` porque el i18n no está instalado en `cyd.py`).

## 5. Puntos delicados (a cuidar en la implementación)

- **Presupuesto residente**: `intérprete + tabla EXTERN_INIT + ARR_POOL + EXTERN_POOL +
  pilas` ≤ ventana residente (`$A95F–$EFFF` + `$E000–$FAFF`); si no, error claro (como con
  arrays).
- **Accounting del loader**: la tabla `EXTERN_INIT` va dentro de `SIZE_INTERPRETER` (como
  `ARR_INIT_TABLE`); cuidar que el `block_list` cuente bien (mismo patrón que el fix de
  `EXTERN_DISPATCH`, [[project-extern-pending]]).
- **`EXTERN_POOL` NO se guarda** (RAM pura, como `ARR_POOL`): solo se reserva su dirección;
  el contenido lo pone `EXTERN_INIT` al arrancar.
- **Estabilidad de tamaño** entre pasadas (ya la exige `_place_block`).
- **Orden**: reubicación de externs junto a la de arrays, antes del size final.

## 6. Verificación (emulador, 5 targets ya soportados)

- `test_extern.py`: nuevo `test_import_call_mld` (paralelo al mld128) → rutina nativa en
  strict mld escribe FLAGS=[42,99,123]. Quitar/relajar `test_import_call_strict_mld_is_rejected`.
- Test de librería real: un `.cyd` que `INCLUDE "math16_32.cyd"` + `GOSUB add32/mul32`
  compilado a `mld` y verificado en emulador (paridad con 48k).
- Suite completa 5 targets sin regresión.

## 7. Alcance

Con esto el strict mld gana **paridad de rutinas nativas** con 48k/128k/+3/mld128 y las
librerías nativas (`math16_32`/`strings`) compilan en los 5 targets.

**Enfoque DECIDIDO (Sergio, jul 2026):** copia a `EXTERN_POOL` residente como los arrays
(§3) — es un requisito, no una preferencia: garantiza RAM escribible para rutinas
automodificables o con `DEFS`. Pendiente: implementación + verificación en emulador (un
`.cyd` que `INCLUDE` math/strings compilado a `mld`, paridad con 48k).
