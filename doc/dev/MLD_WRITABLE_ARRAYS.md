# MLD/Dandanator — arrays de escritura (diseño)

> **Estado (5 jul 2026, sin commitear): AMBAS variantes HECHAS y VERIFICADAS en
> emulador (FLAGS[5] 20→99).** strict mld = pool residente; mld128 = MULTI-BANCO
> (arrays en bancos RAM dedicados). Detalle de ficheros y símbolos en la memoria
> `project-mld-writable-arrays` y `reference-mld-architecture`. Ver
> [EXPANSION_ABI.md](EXPANSION_ABI.md) (broker).
>
> **⚠️ GOTCHA (resuelto):** el pool residente NO vale para mld128. `bank0_offset`
> (dónde el loader precarga el bloque 0 en mld128) se calcula con `asm_size` SIN la
> tabla de arrays; la tabla hace crecer la imagen real y el preload aterrizaba DENTRO
> de ella → corrupción (verificado: bloque→`$AA33`, imagen acaba en `$AA3A`). Se
> resuelve por partida doble: (a) mld128 pone los arrays en **bancos RAM aparte** (no
> en la región residente), y (b) `bank0_offset` **suma ahora el tamaño real de la
> `ARR_INIT_TABLE`** (`8*num_arrays`), así el preload cae después de la imagen.

## 1. El problema

El lenguaje trata los arrays (`DIM`) como **almacenamiento mutable**: `LET a(i)=x`,
`LET a(i) += / -=`, y el manual (§"Arrays o secuencias") advierte explícitamente
que *"si se modifican los datos de un array, no se pueden recuperar los valores
originales a menos que se haga una copia en otro array previamente"*. Es decir, la
escritura de array **debe persistir** en todos los targets.

Hoy un `DIM` se emite **inline dentro del bytecode**: `[SKIP_ARRAY][len-1][datos…]`
(`cydc_codegen.py generate_code`, rama `ARRAY`). El bloque es a la vez
inicializador **y** almacenamiento. El opcode de escritura `OP_POP_VAL_ARRAY`
(`interpreter.asm`) hace `LOAD_CHUNK` del chunk del array y luego `ld (hl),a`.

- **48k/128k/+3**: el chunk vive en RAM (residente en 48k; banco RAM en `$C000`
  vía `SET_RAM_BANK` en 128k/+3). `ld (hl),a` cae en RAM → **la escritura persiste.
  Correcto, sin cambios necesarios.**
- **MLD/Dandanator**: el chunk vive en un slot flash del Dandanator, mapeado en
  `$0000-$3FFF` vía `SET_DAN_BANK` (`IS_MLD_DAN`). `ld (hl),a` cae en flash / la
  interfaz de comandos del Dandanator → **la escritura se pierde.**

## 2. Decisión de arquitectura

**Contrato uniforme, implementación divergente solo en Dandanator.** El array es
escribible en todos los targets (responsabilidad del autor, como ya dice el
manual). No se introduce un pool en 48k/128k (sería duplicar en RAM datos que ya
están en RAM escribible → desperdicio de memoria valiosa). Solo en MLD, donde el
bloque está en flash, **se copia a RAM al arrancar** (como el intérprete y la
música ya hacen) y el acceso a array va a esa copia.

Rechazado: array de solo lectura en MLD (rompe programas correctos en silencio);
pool en todos los targets (desperdicia RAM en 48k/128k).

## 3. Presupuesto de RAM medido (4 jul 2026)

Compilado un `.cyd` de referencia con arrays para `mld` y `mld128`; mapa leído del
listado sjasmplus (`cyd.lst`). Intérprete de referencia ≈ 10.6 KB.

| Región | Rango | Bytes |
|---|---|---|
| Vars (FLAGS/OPTIONS/buffers/escalares) | `$5D00–$5FFF` | 768 |
| Screen buffer (PXL+ATT) | `$6000–$7AFF` | 6912 |
| SAVE + WINDOWS | `$7B00–$7C54` | 341 |
| hueco libre bajo | `$7C55–$7FFF` | **939** |
| Intérprete + INDEX (`START_INTERPRETER..SIZE_INTERPRETER`) | `$8000–$A95E` | ~10591 |
| hueco libre alto | `$A95F–$DFFF` | **5793** |
| PIC_BUFFER | `$E000–$FAFF` | 6913 |

**El presupuesto NO es 5.7 KB en general — depende de si la máquina tiene bancos:**

- **strict `mld` (48K)**: no hay bancos RAM (`$7FFD` no existe en modo 48K;
  `spectrum_banks = range(0,16)` son todos **slots** Dandanator). NO precarga
  bloques (solo copia el intérprete a `$8000`). Los arrays caen en el hueco de RAM
  base `$A95F–$DFFF` (~5.7 KB) + huecos menores. **Este límite es inherente a una
  máquina de 48K**, no una elección de diseño. Si no caben → error de compilación.
- **`mld128` (128K)**: tiene bancos RAM reales `[0,1,3,4,6,7]` (`cydc.py`
  `ram_banks`); hoy mete casi todo en slots flash (ids ≥8) y solo la música en
  banco RAM. Los **arrays deben ir a bancos RAM, exactamente como el target 128k**:
  tantos bancos como haga falta, **menos los que reserve la música**. Presupuesto ≈
  hasta ~5 bancos × 16 KB (decenas de KB), NO 5.7 KB. Acceso vía `SET_RAM_BANK`
  (el camino que ya funciona en 128k), no vía el hueco de RAM base.

## 3bis. Verdad del runtime MLD (verificada en código+emulador, 5 jul 2026)

NO fiarse de docs viejos (ARCHITECTURE §8.4 no tenía MLD; ya corregido). Hechos:
- Ambos MLD (`mld` y `mld128`) **ejecutan bytecode y acceden a arrays desde el SLOT
  FLASH**: `LOAD_CHUNK`→`SET_DAN_BANK` mapea el slot en `$0000`, y el índice TXT es
  slot-relativo (`do_asm_mld`: `entry_offset - bank0_offset`). No hay camino
  `SET_RAM_BANK` para chunks. → arrays no persisten (FLAGS[5]=20 confirmado).
- El loader **ya copia bloques slot→RAM** al arrancar (`BLOCK_TABLE`/`table_entries`,
  `cyd.py:1504`); hoy solo la MÚSICA lo aprovecha. La precarga de bloques no-música a
  RAM existe pero está **muerta** (la ejecución/acceso sigue yendo a flash). El
  "mld128 ejecuta residente / vía B" de `CYD_MLD_DEBUG_STATUS.md` era FALSO/superado.
- La inline de cada array (`[SKIP_ARRAY][len-1][data]`) **se queda en flash**
  (`SKIP_ARRAY` la necesita para saltarla en tiempo de ejecución) y sirve de
  **fuente** de solo lectura; `ARR_INIT` la copia a la RAM escribible al arrancar y
  el operando de array apunta a esa copia RAM (residente en strict mld / banco RAM
  en mld128).

## 4. Dos mecanismos según la máquina

La clave es que el arreglo **difiere por variante** porque la RAM disponible es
distinta. En ambos casos los arrays acaban en RAM escribible; cambia *dónde*.

### 4.1 `mld128` — arrays en bancos RAM dedicados (multi-banco)

`mld128` es "una aventura 128k servida desde cartucho". Lo inmutable (texto,
imágenes, bytecode) se lee de slots flash; lo **mutable (arrays) va a bancos RAM**
y se accede con `SET_RAM_BANK` (el slot Dandanator en `$0000` y el banco `$7FFD` en
`$C000` son HW independiente). Implementación (HECHA):

- **Reserva de bancos** (`cydc.py` `plan_mld128_array_banks`): tras la 1ª
  `generate_code` (ya se conocen `codegen.array_lengths`), se **empaquetan los
  arrays en bancos RAM dedicados** (bin-packing first-fit-decreasing, cada array
  entero en un banco, ventana de `$C000-$FFFF` = 16 KB). Los bancos elegidos se
  pelan del **tope** de `ram_banks` (`[0,1,3,4,6,7]`, nunca el banco 0) y se
  **quitan** de `ram_banks` antes de construir `spectrum_banks` → el allocator de
  bloques (música/bytecode) **jamás** los usa ⇒ colisión con música imposible por
  construcción. Si no caben → error de compilación.
- **Operando banqueado** (`cydc_codegen.py`, param `array_bank_map`): `symbols[name]
  = (banco_real, $C000+offset)`; `symbol_replacement` hornea el operando
  `[banco, lo, hi]`. Entrada de tabla: `(name, src_chunk, src_off, banco, $C000+off,
  nbytes)`.
- **Opcodes** (`interpreter.asm`, `IFDEF IS_MLD_DAN`+`IFDEF OP_EXTERN_BANKED`):
  `OP_PUSH/POP/PUSH_LEN_VAL_ARRAY` **paginan el banco del array** (`SET_RAM_BANK`,
  con `or ROM48KBASIC`), acceden a `$C000+offset` en la ventana paginada, y
  restauran el banco previo. Sin sentinela `$FE`: el byte de banco del operando ya
  es el banco real.
- **`ARR_INIT` banqueado** (`interpreter.asm`): por entrada, `LOAD_CHUNK(src_chunk)`
  mapea el slot flash en `$0000` (`SET_DAN_BANK`) y `SET_RAM_BANK(banco)` pagina el
  banco destino en `$C000`; `LDIR` copia `src_off`→`$C000+off`. Al terminar deja el
  banco 0 paginado (default limpio). Tabla de 8 bytes: `DEFB chunk / DEFW src_off /
  DEFB banco / DEFW $C000+off / DEFW nbytes`, terminada en `$FF`.
- **Accounting**: `bank0_offset += 8*num_arrays` (la `ARR_INIT_TABLE` real vive
  dentro de la imagen del intérprete pero la sonda de tamaño solo emite el stub de 1
  byte; sin este ajuste el preload del bloque 0 corrompe la tabla).
- **Presupuesto**: hasta ~decenas de KB según bancos RAM libres tras la música.

### 4.2 `strict mld` (48K) — arrays en RAM base

Sin `$7FFD` no hay bancos: los arrays van al hueco de RAM base `$A95F–$DFFF`
(~5.7 KB), residente. Cambios:

- **Compilador**: reservar un pool a partir de `SIZE_INTERPRETER` (alineado),
  asignar a cada array un offset, emitir **tabla de init** `(chunk_ini, off_ini,
  addr_pool, len)`; error de compilación si el pool choca con `PIC_BUFFER`.
- **VM (`IS_MLD_DAN` sin bancos)**: rutina de init al arrancar (copia flash→pool,
  cero-relleno); los opcodes `OP_PUSH/POP/PUSH_LEN_VAL_ARRAY` con rama residente
  que direcciona el pool directo (sin `LOAD_CHUNK`).

`48k/128k/+3` no cambian en ninguno de los dos casos.

## 5. A verificar en emulador (confirmar bug + arreglo, no el alcance)

Colocamos los arrays en RAM deliberadamente en ambas variantes, así que la duda ya
no es "¿mld128 funciona de chiripa?" sino confirmar el bug y el arreglo:

1. ANTES: en ambos targets, `LET a(i)=x; PRINT a(i)` imprime el valor viejo
   (escritura perdida).
2. DESPUÉS: imprime el valor nuevo (persiste), incl. arrays en más de un banco RAM
   (mld128) y arrays que llenan el pool (strict mld).

**El harness ZEsarUX MLD direct-boot FUNCIONA** (5 jul 2026). Receta:
- Programa de test **con `[[ ]]`** (sin ellos el `.cyd` se compila como TEXTO, no
  código → cuelgue; fue mi error inicial).
- `cydc mld128|mld test.cyd sjasmplus .` → `test.MLD`; **padear a 512KB con `0xFF`**
  (0x00 cuelga).
- ZEsarUX `--machine 128k|48k --enable-dandanator --dandanator-rom <rom>
  --dandanator-press-button --vo null --ao null --enable-remoteprotocol
  --remoteprotocol-port 10000`; leer FLAGS por ZRCP. Runner: `scratchpad/ramtest/
  mld_probe.py`.

**BUG CONFIRMADO EN EMULADOR (mld128 Y strict mld, 5 jul):** `[[ DIM t(4)=
{10,20,30,40} / LET t(1)=99 / SET 5 TO t(1) / SET 6 TO t(2) / spin ]]` → FLAGS[5]=20
(la escritura de 99 se PIERDE), FLAGS[6]=30 (lectura OK). El arreglo se
auto-verifica igual (DESPUÉS: FLAGS[5]=99).

### 4.2bis strict mld — recordatorio del operando residente

El operando de array se emite como `[ARR_RESIDENT_BANK=0xFE, pool_off_lo,
pool_off_hi]`; la VM (bajo `IS_MLD_DAN` y **sin** `OP_EXTERN_BANKED`, si el banco ==
`0xFE`) direcciona `ARR_POOL + pool_off` sin `LOAD_CHUNK`. `ARR_INIT` (rama strict)
copia `[len-1][data]` desde el slot flash a `ARR_POOL+pool_off`. `ARR_POOL` = label
tras la imagen residente (el hueco `$A95F+` es RAM libre en 48K).

## 6. ABI / broker

- `mld128`: el byte de banco del operando es el id del banco RAM real del array.
  `CYD_ARR_MAP/FLUSH` siguen funcionando vía `SET_RAM_BANK` (idéntico a 128k).
- `strict mld`: banco `$FE` (residente); broker → no-op.

## 7. Estado de implementación — HECHO y VERIFICADO (5 jul 2026)

Ambas variantes implementadas y verificadas en emulador (ZEsarUX direct-boot;
`FLAGS[5]` pasa de 20 a **99**), sin regresión en 48k/128k/+3 ni en la suite (335).

- ✅ **strict mld (48K)** — pool residente `ARR_POOL`. Operando `[0xFE, pool_off]`;
  `ARR_INIT` copia flash→pool; rama residente en los 3 opcodes.
- ✅ **mld128** — MULTI-BANCO (§4.1). `plan_mld128_array_banks` reserva bancos RAM
  dedicados (fuera del pool del allocator ⇒ sin colisión con música); operando
  `[banco_real, $C000+off]`; `ARR_INIT` banqueado copia flash→banco; opcodes paginan
  con `SET_RAM_BANK`; `bank0_offset += 8*num_arrays`.
- ✅ **Verificación en emulador** (`scratchpad/ramtest/`): `mld_probe.py` (caso
  básico, mld/mld128 → 99), `mld_multi.py` (70 arrays de 250 B → **2 bancos**
  dedicados, primer y último array persisten), `mld_music.py` (mld128 + PT3/vortex:
  array persiste y el runtime sigue vivo → sin colisión con música).
- ✅ **Tests unitarios** (`tests/test_codegen.py`): `TestMld128ArrayRelocation`
  (operando y tabla banqueados) y `TestMld128ArrayBankPlanner` (bin-packing,
  multi-banco, exclusión del banco 0, error por desbordamiento).
- ⏳ Pendiente de cierre: rebuild `dist/`, revisar `EXPANSION_ABI.md`/manual si
  procede.
