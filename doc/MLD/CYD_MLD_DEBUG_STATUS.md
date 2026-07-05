# CYD MLD / Dandanator — debug status

> **⚠️ HISTÓRICO / SUPERADO (5 jul 2026).** Log de depuración del 3 jul 2026, cuando
> el MLD "nunca arrancaba". Desde entonces: **mld y mld128 arrancan y están
> verificados**, están **expuestos en el CLI** (`{48k,128k,plus3,mld,mld128}`) y los
> **arrays `DIM` son escribibles** en ambos. Algunas afirmaciones de abajo (p.ej.
> "mld128 ejecuta residente / vía B", "aparcado y oculto del CLI") quedaron obsoletas
> o refutadas. Estado real y arquitectura en `ARCHITECTURE.md §8.4/§10`,
> `doc/dev/MLD_WRITABLE_ARRAYS.md` y `doc/dev/EXPANSION_ABI.md`. Se conserva por el
> valor de las notas del harness.

Estado del intento de desbloquear el target Dandanator/MLD de CYD (que
históricamente "nunca arrancaba"). Escrito el 3 jul 2026. El MLD sigue
**aparcado y oculto del CLI**; esto documenta lo aprendido para retomarlo.

## Cómo se prueba (harness ZEsarUX headless)

- ZEsarUX emula Dandanator: `--enable-dandanator --dandanator-rom <ROM>`
  `--dandanator-press-button` (el botón es OBLIGATORIO; sin él arranca la ROM
  normal del Spectrum en passthrough). Combinar con
  `--machine 128k --vo null --ao null --enable-remoteprotocol --remoteprotocol-port 10000`.
- **ROM direct-boot para test** (representativa: al lanzar una MLD el Dandanator
  mapea su slot 0 en $0000 y le da control): coger la `.MLD` cruda (MLDoffset=0)
  y rellenar a 512 KB. `slot0=loader, slot1=intérprete, slot2..=bloques`.
- Compilar MLD: `mld`/`mld128` NO están en el CLI (`cydc.py` choices); re-añadir
  temporalmente para poder compilar.
- Scripts de sonda en `scratchpad/dan/` de la sesión (probe/diag/pulsetest…).

### Debug NO intrusivo (imprescindible)

Insertar `di:halt` en el `.asm` para congelar **DESPLAZA el BLOCK_TABLE** (flota
tras la RAM-routine) y falsea las lecturas. Usar breakpoints ZRCP por CLI, que no
tocan el binario:

```
--enable-breakpoints
--set-breakpoint 1 PC=5F32h  --set-breakpointaction 1 "let var0=A"
```
y leer con `evaluate var0` por ZRCP. La acción `break` NO detiene headless
(necesita ventana de debug). Sintaxis de condición: `PC=8000h` (sufijo `h`, no
`0x`); el ORDEN importa: `enable-breakpoints` ANTES de `set-breakpoint`.

## El protocolo de comandos Dandanator en ZEsarUX

Fuente: menú Z80 oficial + firmware PIC que añadió Sergio a `doc/MLD/`
(`2017.06.03 - Dandanator Mini Menu Z80 Code`, `2017.09.22 - … PIC Firmware`).

- **Hardware real**: un comando = ráfaga de **N pulsos** (escrituras) a cualquier
  dirección de la zona Dandanator ($0000-$3FFF); el VALOR escrito da igual; el PIC
  cuenta por tiempos (8-30 µs entre pulsos, 32 µs = fin).
- **ZEsarUX NO emula esa parte de tiempos** (`nmiroutine.asm`: *"any Dandanator
  Memory addr since ZesarUX wont be emulating this part"*). En su lugar lee el
  **VALOR escrito en la dirección $0001** (`DDNTRADDRCMD EQU 1`) como el número de
  comando. Data1/Data2/confirmación de comandos especiales van en $0002/$0003/$0000.
- **Comando N → banco N-1** (`Main - dmini66.asm`: *"slots 0-31 = commands 1-32"*,
  *"command 1 → slot 0"*). Verificado empíricamente: valor 2/3/4 en $0001 → bancos
  1/2/3. Comando 33 = ROM interna; 34 = ROM interna + deshabilitar.
- El menú (`dandanator_hw_65.asm SENDNRCMD`) escribe el nº de comando COMO VALOR en
  $0001, N veces → **una sola rutina sirve para real (N pulsos) y ZEsarUX (valor)**.

## Cadena de bugs

| Bug | Descripción | Afecta | Estado |
|---|---|---|---|
| **#1** | `loadermld.asm`: `ld bc, RAM_ROUTINE_END - RAM_ROUTINE_ROM` mezcla etiqueta dentro del `DISP $5F00` (=$5F76) con física (=$0020) → LDIR de $5F56 (24406) bytes en vez de $76 (118) → arrasa la RAM, el intérprete nunca llega a $8000. | HW real + emu | ✅ commit `0b0f961` (`… - RAM_ROUTINE`) |
| **#3** | `loadermld.asm`: **colisión de scratch**. `slot_id` guardado en `$5C03`, machacado por `ld ($5C02),hl` (puntero word en $5C02-$5C03). Al releerlo, slot_id=0 → `abs = MLDoffset+0+1 = 1` → comando 1 → mapea el slot LOADER en vez del intérprete → se copia a sí mismo y hace bucle. Es el verdadero "MLD slot-switch bug" que 8eb76e3 no cerró. | HW real + emu | ✅ commit `b491534` (slot_id → `$5C04`) |
| **#2** | CYD escribía valor 0 en dir 0; ahora escribe el nº de comando en `DAN_CMD_ADDR EQU $0001` en `DAN_CMD_B`/`SET_DAN_BANK`/`RESTORE_DAN_ROM` (como el menú) → funciona en real y ZEsarUX. Decisión de Sergio (toca protocolo, no verificable en HW desde aquí; replica patrón probado del menú). | emu (compat) | ✅ commit `b491534` |
| **#4** | **Las direcciones de salto del bytecode (GOTO/label) se emitían RESIDENTES (`offset + bank0_offset` → $A9xx / `+ 0xC000`), no slot-relativas.** Pero el intérprete MLD (`IS_MLD_DAN`) lee TXT/SCR/bytecode desde slots Dandanator: `LOAD_CHUNK` mapea el slot en $0000-$3FFF y `HL` es un offset 0-based. Ej: `SET 5 TO 123 / spin / GOTO spin` → `08 05 7b 02 00 35 a9 …`, `$A935` sale del slot → basura → cuelga. Afectaba a **mld Y mld128** (en mld128 el single-bank funcionaba de chiripa porque el bloque 0 tiene copia residente en la ventana fija $8000; el multi-banco fallaba). | `mld` + `mld128` | ✅ **ARREGLADO** (ver abajo) |

Con #1+#3+#2 el loader copia el intérprete y arranca; con **#4 arreglado** ejecuta
bytecode completo en ambos targets.

## ✅ BUG #4 ARREGLADO (3 jul 2026) — verificado en emulador

Fix en [cydc.py](../../src/cydc/cydc/cydc.py) (coherente con ARCHITECTURE §5.2: el
codegen NO conoce `model`; se configura el parámetro de layout ya existente
`set_bank_offset_list`, que ya divergía por target):

- Para `model in ("mld","mld128")`: `bank_offset_list = [0, 0]` (direcciones
  **slot-relativas** 0-based) y `bank_size_list = [16K, 16K]` (cada chunk vive en
  su propio slot Dandanator de 16 KB, sin compartir la ventana residente $8000).
- Índice: chunk 0 capado a 16 KB para MLD.
- **`mld` y `mld128` leen TXT/SCR/bytecode desde slots Dandanator** (`IS_MLD_DAN`,
  ambos). Diferencia real entre ambos: nº de slots (`spectrum_banks`: mld=`[0]` un
  solo slot de datos; mld128=`[0,1,3,4,6,7]` multi-slot) y música en bancos RAM.
  La precarga a RAM que hace `do_asm_mld` para mld128 es solo para los music managers.

Verificado (harness ZEsarUX 13.0, ROM direct-boot 512 KB, lecturas ZRCP, todo
**determinista** repitiendo cada test; ⚠️ NO correr otros emuladores en el puerto
10000 a la vez: contención → lecturas corruptas / falsos "crashes"):

| Caso | strict `mld` | `mld128` |
|---|---|---|
| Control de flujo (FLAGS[5]=123) | ✅ | ✅ |
| Saltos adelante+atrás (FLAGS[5]=7B, FLAGS[6]=37) | ✅ | ✅ |
| Texto / camino TXT | ✅ | ✅ |
| Imagen (IMG_LOAD + DISPLAY) | ✅ (single-slot) | ✅ (single-slot) |
| Bytecode multi-slot (GOTO cross-slot, 9000 ops) | N/A (1 slot) | ✅ 5/5 |
| Imagen cross-slot (IMG_LOAD de otro slot) | N/A | ✅ 6/6 |

Suite de regresión: **290 tests, 0 fallos, 0 errores, 37 skipped** (el cambio solo
afecta a `model in (mld,mld128)`; 48k/128k/plus3 intactos).

Scripts nuevos en `scratchpad/dan/`: `testb.py` (FLAGS/PC), `testscr.py` (pantalla);
`bigcode/big.cyd` (9000 SET → multi-slot), `mb/` (12-14 imágenes → multi-banco),
`simg/` (imagen single-slot).

## ✅ VÍA B (`mld128`) — VERIFICADA EN EMULADOR (3 jul 2026)

`mld128` **arranca y ejecuta bytecode completo en ZEsarUX**. A diferencia de strict
`mld`, `do_asm_mld` con `mld_is_128=True` **precarga los bloques a RAM residente**
(bloque 0 → `bank0_offset`≈$A932 en la ventana fija $8000-$BFFF/banco 2; bloques
i>0 → $C000 en su banco). El intérprete ejecuta el bytecode **residente**, así que
las direcciones de salto $A9xx resuelven tal cual → **el bug #4 no muerde**.
Esencialmente `mld128` = "aventura 128k servida desde slots Dandanator" (mismo
camino que el target 128k de cinta, pero cargado del cartucho).

Pruebas empíricas (harness ZEsarUX 13.0, ROM direct-boot 512 KB, breakpoints/lecturas ZRCP no intrusivas):
- **Control de flujo:** `SET 5 TO 123 / spin / GOTO spin` → `FLAGS[5]`($5D05)=`7B`=123, PC en bucle a $8080 (intérprete), no $0038. ✓
- **Saltos adelante+atrás:** `GOTO start … SET 5 TO 123 … GOTO other … SET 6 TO 55 … spin` → `FLAGS[5]`=`7B` **y** `FLAGS[6]`=`37`=55 → ambos GOTO (forward $A93D y backward) resuelven bien. ✓
- **Camino de datos (TXT):** `CLEAR / AT 5,10 / "HELLO DANDANATOR" / spin` → display file con 84 bytes de píxel no-cero (texto renderizado), atributos 768/768 (CLEAR), PC en $8080. ✓

Scripts: `scratchpad/dan/testb.py` (flags), `testscr.py` (pantalla); fuentes
`mini.cyd`/`mini2.cyd`/`mini3.cyd`; ROMs `db128*.rom`.

## Próximos pasos

- **`mld128` funciona en emulador.** Pendiente antes de exponerlo en el CLII:
  (1) probar una aventura más rica (varios bancos/imágenes/música: bloques i>0 en
  $C000 con paginación) — el test cubre 1 solo bloque residente; (2) **verificar en
  HW real** (afecta a #1/#3/protocolo Dandanator, no verificable desde aquí);
  (3) decidir el UX (¿exponer solo `mld128` y dejar strict `mld` oculto/deprecado?).
- **(A) strict `mld` (bug #4):** requiere rework de codegen — los saltos in-chunk
  deben ser slot-relativos (o ir por chunk+offset como `LOAD_CHUNK`). Opcional si
  `mld128` cubre el caso de uso; strict `mld` (48K puro) solo interesa para
  cartuchos sin 128K.
- La vía firmware-launched headless quedó bloqueada (autoboot no dispara; menú
  necesita tecla no encontrada). El test direct-boot es representativo del arranque.

Estado git: `main` con `0dec5e4` < `0b0f961` (#1) < `b491534` (#3+#2). `cydc.py`
con `mld`/`mld128` re-añadidos al CLI = cambio LOCAL sin commitear (temporal para
compilar).
