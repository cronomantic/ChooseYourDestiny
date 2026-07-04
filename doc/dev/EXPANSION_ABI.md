# ABI de expansión de CYD (rutinas nativas Z80)

> **Estado: IMPLEMENTADA y verificada en emulador.** Cubre `IMPORT`/`CALL`
> (opcode `OP_EXTERN`), el ensamblador inline `ASM…ENDASM`, el broker de arrays,
> `CYD_CALL` (llamadas entre bloques), `CYD_SYSCALL` (servicios del motor), la
> extirpación de maquinaria no usada y la DCE de bloques nativos. Todo probado en
> `tests/test_extern.py` y usado por las librerías nativas de `lib/`.
>
> Este documento es la **referencia canónica para el desarrollo del motor** (nivel
> de implementación). La documentación **de cara al autor** está en el manual,
> sección *"Rutinas nativas"* (`MANUAL_es/en.md`). El estudio de diseño y su
> razonamiento están en [`INLINE_ASM_DESIGN.md`](../../INLINE_ASM_DESIGN.md) y
> [`EXTERN_DESIGN.md`](../../EXTERN_DESIGN.md) (documentos históricos de diseño).

Punteros de código: `src/cydc/cydc/cyd/interpreter.asm` (runtime), `src/cydc/cydc/cyd.py`
(inyección/ensamblado), `src/cydc/cydc/cydc.py` (orquestación del build).

---

## 1. Modelo general

Una **rutina nativa** es código Z80 del autor que el guion invoca con `CALL`
(azúcar sobre el opcode interno `OP_EXTERN`, `0x7F`). Se declara de dos formas
equivalentes en el front-end:

- **`IMPORT nombre FROM "fichero.asm"`** — cuerpo en un fichero (ruta relativa al
  `.cyd`).
- **`ASM nombre [EXPORTS a,b] [USES x,y] … ENDASM`** — cuerpo inline en el `.cyd`.

Ambas producen la misma estructura interna (`codegen.externs[bloque]`), se
ensamblan **aisladas** (errores limpios atribuidos al bloque/línea `.cyd`) y se
colocan en memoria por el build, que re-ensambla cada bloque en su **ORG final**
(nada de PIC) y parchea tardíamente el operando `[banco, addr_lo, addr_hi]` de
cada `CALL`.

Un bloque expone uno o varios **callables**: sin `EXPORTS`, el propio nombre del
bloque (entrada = inicio); con `EXPORTS`, cada etiqueta listada.

---

## 2. Contrato de la rutina (ABI de entrada/salida)

| Aspecto | Contrato |
|---|---|
| Entrada | `DE = FLAGS` (base del array de 256 variables; la variable `n` es `FLAGS+n`). |
| Salida | termina con `RET`. |
| Registros | libre uso de `AF/BC/DE/HL/IX/IY`. El handler `OP_EXTERN` **guarda y restaura IX/IY** (el intérprete los usa: IX=puntero de pila de la VM, IY=sysvars ROM). |
| Estado | debe **caber en un banco de 16 KB** y no dejar el hardware roto al volver (si toca `$7FFD`, restaurarlo — pero lo normal es no paginar, ver §3). |
| Callbacks | no saltar a internos del motor por su cuenta; usar los **servicios sancionados** (broker §4, `CYD_CALL` §5, `CYD_SYSCALL` §6). |

**IY en los servicios.** Al entrar, `IY = sysvars ROM` (heredado del intérprete).
Los servicios que llaman a rutinas ROM (teclado) lo asumen: **una rutina no debe
clobbear IY antes de invocar un `CYD_SYSCALL`** (o restaurarlo).

Runtime del handler: `interpreter.asm`, etiqueta `OP_EXTERN` (bajo `IFNDEF
UNUSED_OP_EXTERN`). Operando `[banco, lo, hi]`; en banked hace `SET_RAM_BANK`
guardando el valor real del puerto `$7FFD` en la pila y restaurándolo tras el
`RET` de la rutina (compone en anidamiento).

---

## 3. Colocación y banking

| Target | Colocación | `OP_EXTERN_BANKED` |
|---|---|---|
| 48k | residente al final del bank 0; `call` directo | no |
| 128k / +3 | banco de RAM paginado (`$C000+offset`), best-fit entre `spectrum_banks[j≥1]` | sí |
| mld128 | banco paginado (reusa el camino `$7FFD`) | sí — runtime sin verificar |
| mld (estricto) | error limpio (1 solo banco) | — |

**Regla de oro:** una rutina bancada corre en su propio banco en `$C000` y **NUNCA
paginaría `$C000` por su cuenta** (se autoexpulsaría). Todo cruce de banco (arrays,
`CYD_CALL`) lo hacen **servicios/handlers residentes** que paginan → operan → repaginan.
El motor y sus servicios viven en la RAM baja fija (`$4000-$7FFF`, `vars.asm ORG
$5d00`) y en `$8000-$BFFF` (residente en tape), siempre mapeados.

`SET_RAM_BANK` (`bank_zx128.asm`): In `A`=banco (`| ROM48KBASIC` = `%00010000`),
Out `A`=valor previo COMPLETO del puerto; **clobbers AF/BC, preserva HL/DE/IX/IY**.

---

## 4. Símbolos inyectados (`cyd_abi.inc`)

El build antepone al cuerpo de cada bloque un `cyd_abi.inc` con EQUs de las
estructuras residentes y direcciones de servicio (de `build_abi_inc` +
`build_arrays_inc` en `cyd.py`). Las direcciones salen del `--sym` del motor
(sección `wanted` en `build_abi_inc`); los servicios que se extirpan (§7) no
aparecen si no se usan.

| Símbolo | Qué es | Origen |
|---|---|---|
| `FLAGS` | base del array de variables (`$5d00`) | sym del motor |
| `SCREEN_BUFFER_PXL` / `_ATT` | buffer de imagen del motor | sym del motor |
| `VIDEO_PXL` / `VIDEO_ATT` | pantalla física (`$4000` / `$5800`) | constante hardware |
| `CYD_PEEK` `CYD_POKE` `CYD_ARR_MAP` `CYD_ARR_FLUSH` | broker (§4) | sym (si no extirpado) |
| `CYD_CALL` | trampolín cross-bloque (§5) | sym (si no extirpado) |
| `CYD_SYSCALL` | gateway de servicios (§6) | sym (si no extirpado) |
| `SVC_*` | ids de servicio (§6) | constantes fijas (`SYSCALL_SERVICES`) |
| `ARR_<n>` / `_LEN` / `_BANK` | por cada array `DIM` (§4.1) | `build_arrays_inc` |
| `RT_<n>` | índice de callable en la tabla de despacho, por `USES` (§5) | `build_uses_inc` |

### 4.1 Arrays y el broker

Por cada array `DIM <n>` el compilador inyecta:

- `ARR_<n>` = dirección del **elemento 0** (`_convert_address(offset+1, chunk) + 1`;
  layout `[SKIP_ARRAY][len-1][datos…]`, `codegen.symbols[<n>]=(chunk, offset+1)`).
- `ARR_<n>_LEN` = nº de elementos (`codegen.array_lengths[<n>]`).
- `ARR_<n>_BANK` = banco físico donde vive, o **`$FF`** si es residente (chunk 0).

En 128k/+3 un array puede estar en un banco paginado; el acceso va por servicios
residentes (`interpreter.asm`, bajo `IFNDEF UNUSED_ARR_BROKER`) que paginan con la
regla de oro. Scratch de MAP/FLUSH = `SAVE_FLAGS` (256 B en `vars.asm`, libre fuera
de SAVE/LOAD → 0 bytes residentes nuevos). Con `$FF` (o en 48k) son acceso directo.

| Servicio | In | Out | Preserva |
|---|---|---|---|
| `CYD_PEEK` | `A`=banco/`$FF`, `HL`=dir | `A`=byte | BC/DE/HL/IX/IY |
| `CYD_POKE` | `A`=banco, `HL`=dir, `E`=byte | — | BC/DE/HL/IX/IY |
| `CYD_ARR_MAP` | `A`=banco, `HL`=`ARR_<n>`, `BC`=`ARR_<n>_LEN` | `HL`=copia de trabajo residente | — |
| `CYD_ARR_FLUSH` | `A`=banco, `HL`=`ARR_<n>`, `BC`=nº | — | — |

`CYD_ARR_MAP` copia el array entero a `SAVE_FLAGS` y devuelve un puntero directo
(residente/48k: devuelve el propio `HL`); `CYD_ARR_FLUSH` vuelca de vuelta (no-op si
residente). Solo un array mapeado a la vez.

---

## 5. Llamadas entre rutinas nativas (`CYD_CALL`)

Rutinas del **mismo bloque** (multi-export) se llaman con `call` normal (mismo
banco). Entre **bloques distintos** (posiblemente en otro banco), el trampolín
residente `CYD_CALL`:

```
    ld a, RT_<callee>       ; índice inyectado por USES
    call CYD_CALL           ; entra al callee con DE=FLAGS; paginado por CYD
```

- `USES a,b,…` declara los callees; por cada uno se inyecta `RT_<name> EQU <idx>`
  (`build_uses_inc`). El índice es la posición del callable en la **tabla de
  despacho residente** `EXTERN_DISPATCH`.
- `EXTERN_DISPATCH` (una fila `DEFB banco,lo,hi` por callable superviviente,
  `build_dispatch_table`) se coloca **al final de la imagen del motor**, tras la
  tabla `INDEX`, en las plantillas `cyd_tape/plus3/mld.asm`. Vacía en el size-pass;
  rellenada tras la colocación. Su tamaño (`3·nº callables`) se reserva en
  `bank0_offset` **y** en el `block_list` del cargador (`do_asm_*`: `+ dispatch_bytes`).
- Runtime: `interpreter.asm`, `CYD_CALL` (bajo `IFNDEF UNUSED_CYD_CALL`): indexa
  `EXTERN_DISPATCH` (idx·3), pagina el banco del callee, entra con `DE=FLAGS`,
  repagina el banco del caller. Compone como `OP_EXTERN` (guarda `$7FFD` por nivel).
  48k = llamada directa.

---

## 6. Servicios del motor (`CYD_SYSCALL`)

Punto de entrada único, servicios por número. Solo se inyecta la dirección de
`CYD_SYSCALL`; los ids `SVC_*` son un **contrato numérico estable** → la ABI es
versionable (el intérprete puede reescribirse sin recompilar las rutinas del autor).

```
    ld e, 65                ; argumento (según servicio)
    ld a, SVC_PRINT_CHAR    ; id
    call CYD_SYSCALL
```

Runtime: `interpreter.asm`, bajo `IFNDEF UNUSED_SYSCALL` (anidado en
`UNUSED_OP_EXTERN`). El dispatcher indexa la tabla **estática** `SVC_TABLE` (los
servicios son rutinas del motor; **no** hay inyección desde Python como
`EXTERN_DISPATCH`) y hace `jp (hl)` al servicio, cuyo `RET` vuelve al llamante.
El dispatcher clobbea `A`/`HL` y preserva `DE` (push/pop) → **los argumentos de
servicio van en `E`/registros, no en `A`/`HL`**.

| id | Servicio | In | Out | Rutina del motor |
|---|---|---|---|---|
| 0 | `SVC_PRINT_CHAR` | `E`=carácter | — | `PUT_VAR_CHAR` (text_manager) |
| 1 | `SVC_WAIT_KEY` | — | `A`=tecla | `INKEY_SELECT_WAIT_MODE` (A=0) |
| 2 | `SVC_INKEY` | — | `A`=tecla (0 si ninguna) | `INKEY_SELECT_WAIT_MODE` (A≠0) |

### 6.1 Añadir un servicio nuevo (receta)

1. **Runtime** (`interpreter.asm`, bloque `CYD_SYSCALL`): añade la etiqueta
   `_SVC_<NUEVO>` con su cuerpo (`jp <RUTINA_MOTOR>` o cuerpo propio, termina en
   `RET`) y una fila `DW _SVC_<NUEVO>` **al final** de `SVC_TABLE` (los ids son la
   posición; no reordenar los existentes → contrato estable). Convención de args:
   evita `A`/`HL` (los usa el dispatcher); usa `E`/`BC`/`DE`.
2. **Constante** (`cyd.py`): añade `("SVC_<NUEVO>", <id>)` a `SYSCALL_SERVICES`
   con el id = índice en `SVC_TABLE`. Se inyecta como EQU automáticamente.
3. Listo: la extirpación (§7) y la detección funcionan sin más (el servicio vive
   bajo el mismo `UNUSED_SYSCALL`). Documenta el servicio en el manual.

> Extirpación por-servicio (`UNUSED_SVC_<NAME>`) está prevista en el diseño (§10.1)
> pero **no** implementada: hoy es todo-o-nada (`UNUSED_SYSCALL`). Si un servicio
> nuevo es pesado y raro, considera implementar el guard per-servicio.

---

## 7. Extirpación de maquinaria no usada

Todo lo residente se **quita del build si ningún bloque lo referencia** (motor
residente, RAM escasa), con el mismo mecanismo `UNUSED_*` de los opcodes:

| `DEFINE` | Quita | Cuándo |
|---|---|---|
| `UNUSED_OP_EXTERN` | handler + broker + CYD_CALL + syscall | no hay externs |
| `UNUSED_ARR_BROKER` | `CYD_PEEK/POKE/ARR_MAP/ARR_FLUSH` | ningún bloque referencia el broker |
| `UNUSED_CYD_CALL` | trampolín + tabla de despacho | ningún bloque usa `CYD_CALL` |
| `UNUSED_SYSCALL` | dispatcher + `SVC_TABLE` + servicios | ningún bloque usa `CYD_SYSCALL` |

**Detección — sonda de símbolo no definido** (`cyd.py`): cada bloque se ensambla
contra un `cyd_abi.inc` que define FLAGS/pantalla/`ARR_*` pero **NO** los servicios
(`build_probe_abi` / `probe_block_services` / `extern_probe_used`). Los servicios
que quedan sin resolver salen como `Label not found: <NOMBRE>`; se intersecan con
`PROBE_SERVICES = broker + CYD_CALL + CYD_SYSCALL`. En `cydc.py`, tras la sonda, se
añaden los `UNUSED_*` a `unused_opcodes` **antes del size-pass** (para que el motor
se mida a su tamaño real y las tablas se reserven solo si se usan). Los errores
reales del autor se ignoran aquí (no están en el set) y se cazan en el ensamblado real.

---

## 8. DCE de bloques nativos

Un bloque `IMPORT`/`ASM` que **nadie llama** no se ensambla ni se coloca
(`extern_live_blocks` en `cyd.py`). Conjunto usado inicial = callables en
`codegen.extern_calls` (poblado tras la DCE de bytecode → solo `CALL` alcanzables)
+ cierre transitivo por `USES`. **Granularidad = bloque**: se conserva si ALGÚN
export está usado (los exports parciales no se podan: un bloque = unidad de
ensamblado indivisible). Solo los callables supervivientes reciben fila en
`EXTERN_DISPATCH` / índice `RT_`. Correcto con y sin `-dce`.

---

## 9. Sangrado (el compilador lo gestiona)

sjasmplus exige **etiquetas en la columna 0** e **instrucciones indentadas**. El
autor sangra el bloque `ASM` para alinearlo con el `[[ ]]`; `_dedent_asm_labels`
(`cyd.py`) lleva a la columna 0 **solo** las líneas de etiqueta / `EQU`, dejando el
resto verbatim (un dedent global rompería el caso sin etiquetas). Preserva el nº de
líneas → el remapeo de errores a la línea `.cyd` sigue exacto. (`:` NO es separador
de instrucciones en sjasmplus: una instrucción por línea.)

---

## 10. Mapa del pipeline de build (`cyd.py` / `cydc.py`)

Orden en `cydc.py` (build por target):

1. `unused_opcodes` (opcodes muertos) + `codegen.code_extract_declarations(code)`
   (temprano, puebla `codegen.externs` para la sonda).
2. **Sonda** `extern_probe_used` → `UNUSED_ARR_BROKER` / `UNUSED_CYD_CALL` /
   `UNUSED_SYSCALL`.
3. **Size-pass** (`get_asm_*_size`) con esos defines → `asm_size` + `cyd.sym`.
4. `generate_code` (aprox) → `codegen.extern_calls` poblado → **DCE de bloques**
   (`extern_live_blocks`) → `route_names`/`route_index`/`dispatch_size`.
5. `bank0_offset = 5·num_blocks + dispatch_size + asm_size + 0x8000`.
6. `generate_code` (real, con `bank0_offset`) → bytecode + `codegen.symbols`.
7. Colocación de bloques (`_place_block`): `build_abi_inc + build_arrays_inc +
   build_uses_inc` por bloque, `assemble_extern_routine` a ORG final, `extern_addr`
   por callable, late-patch de los `CALL`.
8. `build_dispatch_table` → `extern_dispatch_asm`.
9. `do_asm_*` con `unused_opcodes`, `extern_dispatch` (tabla), y `block_list` del
   cargador incluyendo `dispatch_bytes`.

Funciones clave en `cyd.py`: `build_abi_inc`, `build_arrays_inc`, `build_uses_inc`,
`build_dispatch_table`, `build_probe_abi`, `probe_block_services`,
`extern_probe_used`, `extern_live_blocks`, `assemble_extern_routine`,
`_dedent_asm_labels`, `get_unused_opcodes_defines` (emite `UNUSED_*` como DEFINE).

**Estabilidad de tamaño**: cada bloque se mide a un ORG provisional y luego se
re-ensambla a su ORG final; si el tamaño cambia entre pasadas se aborta limpio (el
tamaño de una rutina no puede depender de su dirección de carga).

---

## 11. Contrato y versionado

- Los **símbolos de datos** (`FLAGS`, `SCREEN_BUFFER_*`, `ARR_*`) van por EQU
  inyectado: son direcciones, pueden moverse entre builds sin romper contrato.
- Los **puntos de entrada del motor** (broker, `CYD_CALL`, `CYD_SYSCALL`) van por
  EQU inyectado desde el `--sym` → su dirección puede moverse; el autor los llama
  por nombre.
- Los **ids `SVC_*`** son el único **contrato numérico**: no reordenar, solo
  añadir al final. Es lo que permite reescribir el intérprete sin recompilar las
  rutinas del autor.

---

## 12. Verificación

`tests/test_extern.py` (gated en emulador ZEsarUX) cubre: IMPORT/CALL 48k/128k/+3,
inline single/multi-export, ABI de datos, broker PEEK/POKE y MAP/FLUSH (residente +
banco), `CYD_CALL` (48k/128k/cross-bank), `CYD_SYSCALL` (print), extirpación de cada
pieza (compile-time), DCE de bloques, y sangrado natural/uniforme. Las **librerías
nativas** (`lib/math16_32.cyd`, `lib/strings.cyd`) son el uso real end-to-end,
verificadas en `tests/test_libraries.py`. Ver [EMULATOR_TESTING.md](EMULATOR_TESTING.md).
