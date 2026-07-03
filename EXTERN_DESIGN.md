# Diseño: rutinas nativas del autor (`IMPORT` / `CALL`, opcode `OP_EXTERN`)

> **Propósito.** Fijar el diseño de la extensibilidad nativa de CYD: permitir que
> un autor escriba una rutina en ensamblador Z80, la registre en su guion y la
> invoque desde él. Es la generalización del patrón que **ya usa el reproductor
> WYZ** (ensamblado aislado a un banco, `ORG` fijo, llamada desde el motor).
>
> Documento de referencia para no re-derivar el entendimiento. Las afirmaciones
> sobre el código actual llevan `fichero:línea` verificados salvo que se indique
> "(a verificar)". Asume [ARCHITECTURE.md](ARCHITECTURE.md).
>
> **Estado: 48k, 128k y +3 END-TO-END FUNCIONANDO y verificados en emulador.** Fases
> 1 (front-end), 2 (build/allocator, caminos 48k residente y 128k/+3 banked) y 3
> (runtime asm, handler resident + banked `$7FFD` + jump table) implementadas y
> verificadas: `IMPORT`+`CALL` de una rutina nativa que escribe en `FLAGS` corre en
> ZEsarUX en 48k, 128k y +3 (test `tests/test_extern.py`, los tres modelos; +3 desde
> DSK con máquina `P341`). **Pendiente:** el target **mld (Dandanator, `SET_DAN_BANK`)**
> — hoy da error limpio — y la fase 4 (ejemplo + sección de manual). Detalle §8.1–§8.3.

---

## 1. Qué resuelve y por qué estaba parado

`OP_EXTERN` existía **diseñado pero nunca cableado**: bloque comentado en
[interpreter.asm:2758-2790](src/cydc/cydc/cyd/interpreter.asm#L2758), sin entrada
en la jump table, sin keyword en el front-end, sin mención en el manual, y con el
handler a medio hacer (el `call` automodificado usa sintaxis de label malformada
`.jump_addr+1:` + `call 0-0`, nunca ensamblado).

Se frenó por dos problemas reales de inyectar código nativo:
1. **Romper el ensamblado**: si el `.asm` del autor se concatena con el motor,
   cualquier error suyo revienta toda la compilación con un mensaje confuso.
2. **Relocalización**: un binario Z80 con direcciones absolutas debe correr en la
   dirección para la que se ensambló; si CYD lo coloca en otro sitio, se rompe.
   Hacerlo portable exigiría código relocatable (PIC), que es inviable de exigir.

**Ambos se disuelven con el patrón del WYZ player** (§2) + **ORG calculado por
CYD** (§5).

---

## 2. Precedente ya existente: el reproductor WYZ

`create_wyz_player_bank` ([cydc_music.py:46-85](src/cydc/cydc/cydc_music.py#L46))
hace exactamente lo que necesita `IMPORT`:
- `wyz_player.asm` declara `ORG $C000` ([wyz_player.asm:2](src/cydc/cydc/cyd/wyz_player.asm#L2)).
- Se ensambla en una **pasada aislada** de sjasmplus (`run_assembler` propio) a un
  `.bin` ([cydc_music.py:79](src/cydc/cydc/cydc_music.py#L79)).
- Comprobación de tamaño en ensamblado: `ASSERT WYZ_LEN < $4000, Player file is too big!`
  ([cydc_music.py:75](src/cydc/cydc/cydc_music.py#L75)).
- El binario se coloca en un banco y el motor lo llama en `$C000` (`WYZ_TRACKER EQU $C000`).

Conclusión: **el ensamblado aislado con `ORG` controlado por CYD ya es un patrón
maduro del proyecto.** `IMPORT` lo generaliza a rutinas arbitrarias del autor.

- El problema (1) desaparece: la rutina se ensambla **aislada**, no concatenada;
  un error del autor da un fallo limpio y atribuible a *su* fichero, sin tocar el
  build del motor. CYD **enmarca** la rutina (pone él el `ORG`, el `SAVEBIN` y el
  `ASSERT`), así que el autor escribe solo el cuerpo.

---

## 3. Superficie de lenguaje

Dos keywords nuevas. El opcode del runtime sigue llamándose `OP_EXTERN`
(nombre interno); el lenguaje no lo expone.

```
IMPORT beeper FROM "rutinas/beeper.asm"   ; declaración (compile-time)
...
CALL beeper                               ; invocación (runtime -> OP_EXTERN)
```

- **`IMPORT nombre FROM "ruta.asm"`** — directiva de declaración (análoga en
  espíritu a `DECLARE`/`CONST`; NO es `INCLUDE`, que incluye fuente `.cyd`).
  Registra una rutina nativa bajo `nombre`. Se resuelve en compilación: CYD
  ensambla el fichero (§5), lo coloca (§6) y asocia `nombre` → (chunk, dirección).
- **`CALL nombre`** — invoca la rutina. Emite `OP_EXTERN` con los operandos
  `[chunk, addr_lo, addr_hi]` de `nombre`. Par mental con lo existente:
  `GOSUB etiqueta` = subrutina del guion (bytecode); `CALL nombre` = rutina Z80 nativa.

Impacto en el front-end (patrón ya existente de añadir opcodes/keywords):
- **Lexer**: tokens `IMPORT`, `FROM`, `CALL`.
- **Parser**: reglas para ambas sentencias; `IMPORT` alimenta una tabla de
  rutinas; `CALL` referencia un `nombre` (validar declarado, como labels/const).
- **Codegen**: nuevo byte de opcode para `OP_EXTERN` (elegir uno libre en el dict
  `opcodes` de [cydc_codegen.py](src/cydc/cydc/cydc_codegen.py)); emisión de los
  3 bytes de operando. El mapa `nombre → (chunk, dirección)` se resuelve tarde
  (tras la asignación de memoria, §6), así que el codegen emite un **placeholder**
  que la fase de layout parchea (como ya se hace con direcciones de labels).

---

## 4. ABI de la rutina nativa

Contrato mínimo, portable y simple:

- **Entrada**: `DE = FLAGS` (puntero base al array de 256 variables del motor).
  La rutina se ejecuta como una llamada (`call`), así que termina con `ret`.
- **E/S vía `FLAGS`**: el guion CYD y la rutina comparten el array de variables.
  El guion pone argumentos en variables (`SET`), hace `CALL`, la rutina lee/escribe
  esas posiciones (`FLAGS+n`), y el guion lee resultados (`@var`). No hace falta
  convención de registros más allá de `DE=FLAGS`.
- **Debe preservar el estado del intérprete**: el handler ya salva/restaura
  `CHUNK` (el banco activo) alrededor de la llamada. La rutina puede usar
  AF/BC/DE/HL/IX/IY libremente PERO no debe dejar el hardware/paginación en un
  estado que rompa el motor al volver (si toca `$7FFD`, restaurarlo). Documentado.
- **Debe caber en un banco** (16 KB, ventana `$C000-$FFFF`) en targets con banking;
  no puede repartirse entre bancos. Si no cabe → error de compilación limpio.
- **Sin sandbox**: es código nativo de confianza. Una rutina con bugs puede colgar
  la máquina. Es una feature **avanzada, opt-in**, con el mismo riesgo que ya
  asumen WYZ/BeepFx. Se documenta "a tu propio riesgo".

Abierto (§10): convención de valor de retorno más allá de FLAGS; si se permite
que la rutina llame de vuelta al motor (por ahora **no**: rutina hoja).

---

## 5. El núcleo: `ORG` calculado por CYD (resuelve la relocalización)

**El autor nunca especifica la dirección de carga; la calcula CYD.** La rutina se
ensambla en la ubicación real donde va a correr, así que las direcciones absolutas
resuelven bien **sin necesidad de código relocatable**.

Como la dirección final depende del layout de memoria (y en 128k, de qué banco y
offset le asigne el allocator), se usa el mismo two-pass que CYD ya aplica al
intérprete (ensamblar con `SHOW_SIZE_INTERPRETER` para medir antes de repartir
memoria, ARCHITECTURE §3 paso 7):

1. **Medir**: ensamblar la rutina aislada con un `ORG` provisional → obtener su
   **tamaño**.
2. **Colocar**: pasar ese tamaño al allocator, que le asigna **banco + offset**
   (banked) o una **dirección residente** (48k), como a cualquier recurso.
3. **Ensamblar final**: re-ensamblar la rutina con `ORG = dirección final` →
   los bytes definitivos, que se colocan en esa posición.

> **Asunción / riesgo (a verificar):** el tamaño de la rutina es **estable entre
> `ORG`s**. Cierto para Z80 escrito a mano (sjasmplus no auto-optimiza `jr`↔`jp`
> ni realinea por dirección). Si el autor usa construcciones dependientes de la
> dirección que cambien el tamaño entre pasadas, la asignación se invalidaría; hay
> que **verificar tamaño idéntico entre pasada 1 y 3 y abortar limpio** si difiere.

### 5.1 Modelo uniforme por target

| Target | `ORG` de la rutina | Colocación | Cómo la llama `OP_EXTERN` |
|---|---|---|---|
| **48k** | dirección residente **calculada** | residente en `$8000-$FFFF` | `call` directo (sin paginar) |
| **128k / plus3 / mld128** | `$C000 + offset_en_banco` | en un banco (compartible) que asigna el allocator | `LOAD_CHUNK` (paginar banco) + `call $C000+offset` |

El 48k **es requisito** (debe funcionar). Al no haber paginación, la rutina es
residente y el `ORG` es su dirección final en el mapa de 48K; `OP_EXTERN` hace
`call` directo e ignora el operando de banco.

### 5.2 Alternativa considerada y descartada: fijar en `$C000` (banco propio)

Se valoró dar a cada rutina un **banco propio** con `ORG $C000` fijo (como el WYZ
player), evitando el re-ensamblado en offset calculado. **Descartada**, porque:

1. **No sirve para 48k** (requisito): en 48k no hay banco `$C000` que paginar, la
   rutina va residente en dirección calculada → seguiría haciendo falta el
   ORG-calculado. Fijar `$C000` solo simplificaría la ruta banked → **dos
   mecanismos** en vez de uno.
2. **Desperdicia un banco entero (16 KB) por rutina** — inviable en 128k (~6 bancos,
   con banco 1 reservado a WYZ y el resto a texto/imágenes/música).
3. **No elimina el riesgo de size-stability** (48k lo mantiene).

Solo convendría en un MVP **banked-only** (sin 48k), que no es el caso. Decisión:
**allocator + ORG calculado, uniforme**.

---

## 6. Integración con el build y el allocator

La rutina nativa se trata como **un recurso más**, con su tamaño, que el allocator
coloca por best-fit (como TXT/SCR/TRK). Puntos de integración (a verificar en
implementación):

- **Tipo de recurso**: hoy el índice usa `TYPE_TXT/SCR/TRK/WYZ`
  ([cyd_tape.asm:416-419](src/cydc/cydc/cyd/cyd_tape.asm#L416)). Añadir `TYPE_CODE`
  (o reutilizar el mecanismo de bloques) para que `LOAD_CHUNK`/`FIND_IN_INDEX`
  puedan paginar el banco de la rutina. `LOAD_CHUNK` hoy busca `TYPE_TXT` fijo
  ([cyd_tape.asm:423-432](src/cydc/cydc/cyd/cyd_tape.asm#L423)); necesitará poder
  localizar el chunk de código.
- **Allocator**: `spectrum_banks` y el reparto best-fit en
  [cydc.py:796-915](src/cydc/cydc/cydc.py#L796). La rutina entra en el conjunto de
  bloques a colocar; debe **caber contigua en un banco** (no se puede trocear,
  a diferencia del texto).
- **Resolución tardía**: tras la colocación se conoce (banco, offset) → se calcula
  `dirección = $C000+offset` (banked) o la residente (48k) → se re-ensambla la
  rutina a ese `ORG` → se parchea el operando del `OP_EXTERN` correspondiente y el
  índice de recursos (mismo estilo que el remapeo de índices ya existente).
- **Pasada de ensamblado aislada**: reutilizar `run_assembler`
  ([cydc_utils.py:76](src/cydc/cydc/cydc_utils.py#L76)) con una plantilla que
  enmarque el fichero del autor: `ORG @ADDR` + cuerpo + `ASSERT tamaño` + `SAVEBIN`.
  Errores de ensamblado → mensaje limpio `IMPORT '<nombre>': fallo al ensamblar
  <fichero>` (encaja con la mejora de robustez de `run_assembler`, que ahora
  conserva el `.asm` y propaga el stderr).

---

## 7. Runtime: handler y jump table

- **Arreglar el handler** [interpreter.asm:2758-2790](src/cydc/cydc/cyd/interpreter.asm#L2758):
  el `call` automodificado tiene el label malformado. Rehacerlo limpio (p.ej.
  cargar la dirección en `HL`/una var y `ld (self+1),...` con el label del operando
  bien definido, o un salto indirecto). Descomentar.
- **Bifurcación por target**: 48k = `call` directo a la dirección residente (sin
  `LOAD_CHUNK`); banked = `LOAD_CHUNK` del banco + `call $C000+offset` + restaurar
  banco. Se implementa con los DEFINEs de target ya existentes (`IFDEF IS_128`,
  etc.) — mismo mecanismo que el resto de divergencias por target.
- **Jump table**: añadir la entrada con la guarda `UNUSED_OP_EXTERN`
  (`DW OP_EXTERN` / `DW ERROR_NOP`) en la posición del nuevo opcode, como el resto
  ([interpreter.asm:2798+](src/cydc/cydc/cyd/interpreter.asm#L2798)).
- **`DE = FLAGS`** antes del `call` (ya está en el diseño del handler).

---

## 8. Plan de implementación por fases

1. **Front-end** (Python, bajo riesgo): tokens `IMPORT`/`FROM`/`CALL`, reglas de
   parser, tabla de rutinas importadas, byte de opcode + emisión con placeholder,
   validación de `CALL` a nombre no declarado. **Testeable en aislado** (parser →
   bytecode), como los tests de codegen ya existentes.
2. **Build** (el grueso): pasada de medición, integración en el allocator, tipo de
   recurso/índice, resolución tardía + re-ensamblado al `ORG` final, parcheo de
   operandos. Verificar la estabilidad de tamaño (§5).
3. **Runtime** (asm): arreglar y activar el handler, bifurcación por target, jump
   table. Verificar en **emulador** (48k y 128k) con una rutina mínima.
4. **Ejemplo + docs**: `examples/import_demo/` (rutina que, p.ej., lee un puerto o
   hace un efecto de beeper y devuelve por FLAGS) + sección de manual con el ABI y
   el aviso de "avanzado, a tu propio riesgo".

Verificación empírica obligatoria antes de dar nada por hecho (emulador real, no
solo lectura): reproducir un `CALL` funcionando en 48k y 128k.

### 8.1 Estado de implementación (fase 1 hecha)

**Fase 1 (front-end) COMPLETA y verificada** (suite en verde, 279 tests):
- `cydc_lexer.py`: token `STRING` (`t_STRING`, regex `"[^"\n]*"`, sólo estado
  INITIAL; `rawtext` es exclusivo → no afecta al texto mostrado) + reserved words
  `IMPORT`/`FROM`/`CALL`.
- `cydc_parser.py`: `SymbolType.EXTERN`; `p_statement_import`
  (`IMPORT ID FROM STRING` → `("IMPORT", nombre, fichero)`, `_declare_symbol`);
  `p_statement_call` (`CALL ID` → `("EXTERN", nombre, 0, 0)`, `_symbol_usage`).
- `cydc_codegen.py`: opcode `"EXTERN": 0x7F`; `self.externs = {}` poblado en
  `code_extract_declarations` (rama `IMPORT`, no emite bytecode). `CALL` fluye por
  `code_translate`/`symbol_replacement` como los labels (placeholder `[0x7F, nombre, 0, 0]`).
- Tests nuevos en `tests/test_parser.py` (`test_parse_import_and_call`,
  `test_parse_call_without_import_errors`). `test_parse_print_statement` cambió de
  `PRINT "text"` (ahora error de sintaxis, correcto) a `PRINT 42`.

**Falta para que `CALL` compile end-to-end:** la fase 2 debe inyectar cada rutina
importada en `self.symbols` con su `(bank, offset)` tras la asignación, para que
`symbol_replacement` resuelva el placeholder (hoy daría "Label X does not exists").
El opcode `0x7F` aún no tiene handler ni entrada en la jump table (fase 3).

### 8.2 Mapa de implementación de la fase 2 (build) — verificado en el código

Flujo de build en `cydc.py` (función `main`), anclas verificadas:
- **Medir intérprete** (`cydc.py:707-784`): `get_asm_48_size`/`get_asm_128_size`/
  `get_asm_plus3_size`/`get_asm_mld_size` → `asm_size`. Patrón two-pass ya existente.
- **`generate_code`** (`cydc.py:798-800` aprox. + `819-821` real): produce `chunks`
  (bancos de bytecode) y resuelve labels vía `code_translate`+`symbol_replacement`.
  `bank0_offset = 5*num_blocks + asm_size + 0x8000` (`cydc.py:807`); bank 0 empieza
  ahí (48k/residente), los demás en `$C000`.
- **Allocator best-fit** (`cydc.py:836-915`): coloca `blocks` (recursos) en bancos.
  - `spectrum_banks` por target (`823-834`): 48k = `[0]`; 128k = `[0,1,3,4,6,7]`
    (o sin banco 1 si WYZ); etc.
  - `blocks` = lista de `(btype, bidx, bsize, bdata, bpath)` con `btype` en
    `TXT/SCR/TRK/WYZ`. Los `chunks` (bytecode) van primero como tipo 0 (`840-855`).
  - Best-fit: para cada block, banco con menor sobrante ≥ `bsize`; append `bdata`,
    `index.append((tipo_num, bidx, banco, offset))` donde `offset = pos_en_banco +
    (bank0_offset si banco 0 else 0xC000)`. **tipo_num: TRK=2, SCR=1, WYZ=3, TXT/bytecode=0**
    (`891-899`). Un recurso **no se trocea** (a diferencia del texto).
  - `index` final remapea banco→`spectrum_banks[banco]` y enmascara offset (`912-915`).
- **Salida** (`cydc.py:995-1080`): `do_asm_48/do_asm_128/do_asm_plus3/do_asm_mld`
  reciben `index` + `blocks=available_banks` (chunks+datos por banco) + `banks` y
  emiten el TAP/DSK con el índice de recursos que usa `LOAD_CHUNK`/`FIND_IN_INDEX`.

**Insight crítico (decidido):** la rutina EXTERN se coloca en el allocator, que corre
**después** de `generate_code`. Por eso los operandos de `CALL` (`[banco, addr_lo,
addr_hi]`) NO se pueden resolver en `symbol_replacement` como los labels → hay que
**parchearlos tarde**, tras la asignación. Implica que el codegen **registre las
posiciones** (chunk, offset de byte) de cada `OP_EXTERN` emitido, para parchearlas
una vez conocido `(banco, dirección)` de la rutina.

**Ensamblado aislado (patrón WYZ)** en `cydc_music.py:46-94` (`create_wyz_player_bank`):
monta un string ASM (template con `ORG`, contenido, `WYZ_LEN=($-$C000)`, `ASSERT
tamaño`, `SAVEBIN`), ensambla con `run_assembler(asm=..., filename=...)`
(`cydc_utils.py:76`), lee el `.bin`. Para IMPORT: enmarcar el `.asm` del autor con
`ORG @ADDR` + `INCLUDE fichero` (o volcado directo) + `ASSERT` + `SAVEBIN`.

**Pasos de la fase 2** (empezar por 48k, que es el requisito y no usa banking/índice/
`LOAD_CHUNK`):
1. Ensamblar cada rutina de `codegen.externs` con `ORG` provisional → tamaño;
   verificar estabilidad de tamaño re-ensamblando al ORG final (abortar si difiere).
2. 48k: colocar la rutina **residente** (bytes al final del bank 0 / mapa 48k),
   dirección = `bank0_offset + pos` (o tras los recursos); banked: entra en `blocks`
   como tipo `COD` no troceable y el best-fit le da banco+offset.
3. Parcheo tardío: rellenar los operandos de cada `CALL` con `[banco, addr_lo,
   addr_hi]` (48k: banco ignorado, `call` directo). Añadir la rutina al `index` si
   banked (para `LOAD_CHUNK`).
4. `do_asm_48` (y luego `do_asm_128`/etc.): emitir los bytes de la rutina en su banco.
5. **Fase 3**: handler `OP_EXTERN` (scaffold `interpreter.asm:2758-2790`, `call`
   automodificado con label malformado — rehacer limpio) + entrada jump table en
   posición **0x7F** de `OPCODES` (`interpreter.asm:2798+`, tras `PUSH_KEMPSTON`=0x7E)
   con guarda `IFNDEF UNUSED_OP_EXTERN`/`DW ERROR_NOP`. Bifurcar 48k (`call` directo)
   vs banked (`LOAD_CHUNK` + `call $C000+offset` + restaurar banco) con los DEFINEs de
   target. `DE=FLAGS` antes del `call`. **Verificar en emulador 48k + 128k** con
   [reference-emulator-harness] (una rutina que escriba un valor conocido en FLAGS+n).

### 8.3 Estado de implementación (fases 2 y 3, camino 48k) — HECHO y verificado

**Camino 48k completo y verificado en emulador** (ZEsarUX, `tests/test_extern.py`):

- **Codegen** (`cydc_codegen.py`): `symbol_replacement` ahora distingue labels de
  externs. Cuando el placeholder string es un nombre de `self.externs` (no un
  label), emite `[0,0,0]` y **registra** `(nombre, chunk_idx, byte_pos)` en
  `self.extern_calls` para el parcheo tardío (en vez de abortar con "Label does not
  exists"). `generate_code` resetea `self.extern_calls` y pasa el índice de chunk a
  `symbol_replacement`.
- **Build 48k** (`cydc.py`, tras el remapeo del `index`): si hay `codegen.externs`
  y el target no es 48k → **error limpio** (banked aún no soportado). Para 48k:
  (1) mide cada rutina con `assemble_extern_routine` a un ORG provisional;
  (2) comprueba que caben en `available_bank_size[0]`; (3) las coloca **residentes
  al final del bank 0**, re-ensamblando cada una a su ORG final =
  `bank0_offset + len(available_banks[0])` acumulado y **verificando que el tamaño
  no cambió entre pasadas** (aborta si difiere); (4) **parcheo tardío**: rellena
  `[bank=0, addr_lo, addr_hi]` en cada `CALL` de `codegen.extern_calls`. Los bytes
  de la rutina se emiten como parte del bloque 0 en `do_asm_48` (`ORG bank0_offset`),
  así que `dirección_rutina = bank0_offset + offset_en_bloque0`. Sin entrada de
  índice (residente, `call` directo).
- **Ensamblado aislado** (`cyd.py: assemble_extern_routine`): enmarca el `.asm` del
  autor con `DEVICE ZXSPECTRUM48` + `ORG` + `INCLUDE "<fichero>"` + medición +
  `SAVEBIN`, ensambla con `run_assembler(capture_output=True)` y lee el `.bin`.
  Errores → `OSError` con mensaje atribuible `IMPORT '<nombre>': failed to assemble
  <fichero>`. **La ruta del `.asm` se resuelve relativa al CWD** (`os.path.abspath`);
  mejora pendiente: resolverla relativa al fichero fuente `.cyd` como hace `INCLUDE`.
- **Runtime** (`interpreter.asm`): handler `OP_EXTERN` reescrito limpio (se eliminó
  el scaffold con el `call` automodificado malformado). 48k: `inc hl` (salta el byte
  de banco), carga `DE`=dirección, `push hl/ix/iy`, y llama a la rutina vía
  `push .cont / push de / ld de,FLAGS / ret` (idioma call-indirecto que deja
  `DE=FLAGS` al entrar); a la vuelta `pop iy/ix/hl` y `jp EXEC_LOOP`. **Preserva
  IX (pila de datos de la VM) e IY (sysvars ROM)** aunque la rutina los reviente.
  Entrada en la jump table `OPCODES` en posición **0x7F** con guarda
  `IFNDEF UNUSED_OP_EXTERN` / `DW ERROR_NOP` (antes del `REPT` de relleno).

**Camino 128k (banked)** — HECHO y verificado en emulador:

- **Build 128k** (`cydc.py`, mismo bloque que 48k, rama `model == "128k"`): cada
  rutina se coloca en un **banco PAGINADO** (índice `j >= 1` de `available_banks`,
  nunca el 0 residente), por best-fit entre los bancos ya usados; si ninguno tiene
  hueco, se añade uno nuevo de `spectrum_banks` (error si no quedan). ORG final =
  `$C000 + len(available_banks[j])`; el operando de `CALL` se parchea con
  `[banco_físico = spectrum_banks[j], $C000+offset]`. La rutina **no** entra en el
  índice de recursos: se alcanza sólo por el operando `[banco, addr]` del `CALL`
  (queda como bytes muertos tras el chunk/recurso de ese banco, nunca ejecutada por
  el bytecode). Sin `LOAD_CHUNK`/`FIND_IN_INDEX` ni `TYPE_COD` — más simple que lo
  esbozado en §6.
- **Runtime banked** (`interpreter.asm`, `IFDEF OP_EXTERN_BANKED` dentro de
  `OP_EXTERN`): lee `[banco, addr]`, `push hl/ix/iy`, `or ROM48KBASIC` +
  `call SET_RAM_BANK` (pagina el banco de la rutina en `$C000`; devuelve el valor
  previo del puerto), `push af` para guardarlo, invoca la rutina
  (`push .cont/push de/ld de,FLAGS/ret`), y a la vuelta `pop af` + `call SET_RAM_BANK`
  **restaura el banco del script**. Como el motor (handler + `FLAGS`) es **residente
  en `$8000-$BFFF`**, sigue ejecutándose mientras `$C000` apunta a la rutina.
  Restaurar el valor real del puerto (no `SCRIPT_BANK`) hace el retorno robusto sea
  cual sea el banco desde el que se hizo el `CALL`. La rama `ELSE` (48k y demás)
  mantiene el `call` directo.
- **El gate es `OP_EXTERN_BANKED`, no `IS_128_TAPE`.** Se define en `get_asm_128` y
  `get_asm_plus3` (ambos incluyen `bank_zx128.asm` → `SET_RAM_BANK`/`ROM48KBASIC`
  por `$7FFD`). NO se define en `get_asm_48` (residente) ni en mld (que paginan por
  Dandanator con `SET_DAN_BANK`), evitando que un build mld referencie `SET_RAM_BANK`
  aunque defina `IS_128_TAPE`.

- **+3 (`plus3`)**: **soportado, mismo camino que 128k.** El +3 banca bytecode en RAM
  por `$7FFD` igual que el 128k (los *recursos* SCR/TRK van a disco, pero los chunks
  y las rutinas nativas van a bancos). El allocator ya excluye el **banco 7** en +3
  (`spectrum_banks = [0,1,3,4]`, o `[0,3,4,6]` con WYZ); como la colocación usa
  `spectrum_banks[j]` y `len(spectrum_banks)` como tope, respeta ese límite sin
  código especial. `do_asm_plus3` emite cada banco con `PAGE {bank}` + `ORG $C000`.

**Verificación empírica** (`tests/test_extern.py`, emulador real, **48k, 128k y +3**):
una rutina que escribe 42 en `FLAGS+0` y 99 en `FLAGS+1` y **revienta IX/IY** a
propósito; el guion hace `CALL` y luego `SET 2 TO 123`. Resultado por ZRCP en los tres
modelos (+3 desde DSK, máquina `P341`): `FLAGS=[42,99,123]` → la rutina corrió con
`DE=FLAGS` y el intérprete **resumió intacto** tras el `CALL`.

**Pendiente (mld):** mld/mld128 paginan por **slots Dandanator** (`SET_DAN_BANK`,
`IS_MLD_DAN`), no por `$7FFD`; requieren su propia integración de colocación y su rama
en el handler. Hoy `IMPORT` fuera de 48k/128k/+3 da **error limpio** en `cydc.py`.
Además, fase 4 (ejemplo + manual).

---

## 9. Resumen de decisiones cerradas

- Sintaxis: **`IMPORT nombre FROM "fichero.asm"`** (declara) + **`CALL nombre`** (invoca).
- Opcode interno: `OP_EXTERN`, operandos `[chunk, addr_lo, addr_hi]`.
- ABI: `DE=FLAGS`, `ret`, E/S por el array `FLAGS`; rutina hoja; debe caber en un banco.
- Relocalización: **`ORG` calculado por CYD** + re-ensamblado en la dirección
  final. Nada de PIC. Uniforme entre targets.
- **48k soportado** (residente, `call` directo). 128k/plus3/mld por banco
  (posible offset ≠ 0 por el allocator) + paginación.
- Ensamblado **aislado** por rutina (patrón WYZ) → errores limpios, sin romper el motor.

## 10. Abierto / a decidir

- Convención de **valor de retorno** más allá de FLAGS (¿un registro que el handler
  guarde en una var? por ahora todo por FLAGS).
- ¿Se permite que la rutina **llame de vuelta al motor** (imprimir, etc.)? Por
  ahora **no** (rutina hoja); revisar si surge necesidad.
- **Varias rutinas por banco**: soportado por el modelo (offset por rutina); definir
  si `IMPORT` de varias del mismo `.asm` o de varios ficheros.
- Presión de memoria en **48k** (residente compite con el contenido): documentar y
  dar error claro si no cabe.
- Verificar la **estabilidad de tamaño** entre pasadas (§5) y abortar si difiere.
