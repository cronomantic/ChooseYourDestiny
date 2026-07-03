# Arquitectura de la herramienta CYD (Choose Your Destiny)

> **Propósito de este documento.** Describir **cómo funciona la herramienta CYD
> por dentro** — el compilador Python y el runtime/VM en Z80 — con énfasis en el
> mecanismo **multi-target por compilación condicional**, que es maduro y ya
> existe. Es un documento de referencia para no tener que reconstruir este
> entendimiento en cada sesión. Las afirmaciones llevan `fichero:línea`
> verificados de primera mano salvo que se indique lo contrario.
>
> Para el diseño del port a CPC/Next y la capa gráfica, ver
> [MULTITARGET_DESIGN.md](MULTITARGET_DESIGN.md). Este documento es el "cómo es
> hoy"; aquel es el "cómo se extenderá".

---

## 1. Qué es CYD

Dos mitades sobre CPU Z80:

1. **Compilador (Python)** en [src/cydc/cydc/](src/cydc/cydc/): traduce un guion
   `.cyd` (lenguaje tipo BASIC para librojuegos) a **bytecode de opcodes de 1
   byte**, comprime el texto, y ensambla (vía **sjasmplus** externo) un binario
   ejecutable por el motor, empaquetado en `.tap`, `.dsk` o `.mld`.
2. **Runtime / máquina virtual (Z80 ensamblador)** en
   [src/cydc/cydc/cyd/](src/cydc/cydc/cyd/): un intérprete fetch-decode-execute
   de ese bytecode + subsistemas (render de texto/gráficos, música AY, save/load,
   banking).

El **bytecode no se guarda en disco como artefacto suelto**: se incrusta como
`DEFB` dentro del fuente ensamblador que se genera al vuelo y se pasa a sjasmplus.

---

## 2. Disposición del repositorio

| Ruta | Contenido |
|---|---|
| [src/cydc/cydc/](src/cydc/cydc/) | Fuente del compilador Python (lo "vivo") |
| [src/cydc/cydc/cyd/](src/cydc/cydc/cyd/) | **Plantillas `.asm`** del runtime (módulos del motor) |
| `dist/cydc/cyd/*.asm` | **Artefactos** copiados del source; NO editar (el source está en `src/cydc/cydc/cyd/`) |
| [documentation/](documentation/) | Manuales PDF (es/en) |
| `ChooseYourDestiny.wiki/` (workdir aparte) | Manual y tutorial en Markdown — **referencia autoritativa del lenguaje** (`MANUAL_es.md`) |

> Nota: `dist/cydc/cyd/*.asm` aparecen como untracked pero **no son WIP**; son
> copias del build. El source real está en `src/cydc/cydc/cyd/`.

---

## 3. Pipeline de compilación (`cydc.py main()`)

Orquestador: [cydc.py](src/cydc/cydc/cydc.py), función `main()` ([cydc.py:99](src/cydc/cydc/cydc.py#L99)).
Argumentos en [cydc.py:118-313](src/cydc/cydc/cydc.py#L118-L313); el posicional
**`model`** ∈ `{48k,128k,plus3,mld,mld128}` ([cydc.py:280-286](src/cydc/cydc/cydc.py#L280)).

Etapas (en orden):

1. **Preprocesado de `INCLUDE`** — `CydcPreprocessor` resuelve includes (hasta 20
   niveles, detecta circulares), produce `text` + `line_map` ([cydc.py:337-359](src/cydc/cydc/cydc.py#L337)).
2. **Parse** — `CydcParser` (PLY) → lista `code` de tuplas `(opcode, args...)`
   ([cydc.py:466-483](src/cydc/cydc/cydc.py#L466)). Modo colon estricto por defecto.
3. **Compresión de texto** — `CydcTextCompressor` tokeniza/abrevia los strings
   `TEXT` (búsqueda de abreviaturas, exportable/importable con `-T`/`-t`)
   ([cydc.py:504-525](src/cydc/cydc/cydc.py#L504)).
4. **Fuente** — `CydcFont`; importable/exportable JSON (`-c`/`-C`)
   ([cydc.py:399-533](src/cydc/cydc/cydc.py#L399)).
5. **Recursos externos** — imágenes `.scr`→`.csc` (comprime ZX0, detecta
   espejado), pistas `PT3`/WyzTracker, SFX (BeepFx), pantalla de carga
   ([cydc.py:548-659](src/cydc/cydc/cydc.py#L548)).
6. **Codegen + trim** — `CydcCodegen`; si `-trim`, calcula `unused_opcodes`
   ([cydc.py:688-697](src/cydc/cydc/cydc.py#L688)).
7. **Ensamblado "para tamaño"** — se ensambla el intérprete con
   `DEFINE SHOW_SIZE_INTERPRETER` para medir su tamaño antes de repartir memoria
   ([cydc.py:707-784](src/cydc/cydc/cydc.py#L707); funciones `get_asm_*_size` en
   [cyd.py](src/cydc/cydc/cyd.py)). Límites: 48k ≤ 32 KB; resto ≤ 16 KB
   ([cydc.py:781-784](src/cydc/cydc/cydc.py#L781)).
8. **Organización de memoria** — calcula `bank0_offset`, reparte chunks/recursos
   en bancos (`spectrum_banks`), encaja bloques (best-fit) y construye el
   **índice** de recursos ([cydc.py:796-915](src/cydc/cydc/cydc.py#L796)).
9. **Ensamblado final + empaquetado** — `do_asm_*` por target → `.tap`/`.dsk`/`.mld`
   ([cydc.py:995-1095](src/cydc/cydc/cydc.py#L995)).

---

## 4. El mecanismo multi-target (núcleo)

**Idea central: no hay "un binario configurable". Por cada target se construye un
fuente ensamblador distinto, concatenando un conjunto de módulos `.asm` elegido y
inyectando símbolos `DEFINE`; sjasmplus resuelve el resto con compilación
condicional.** Todo esto vive en [cyd.py](src/cydc/cydc/cyd.py).

### 4.1 Carga de plantillas y sustitución

- `get_asm_template(name)` lee `src/cydc/cydc/cyd/<name>.asm` y lo envuelve en
  `AsmTemplate` ([cydc_utils.py:66-73](src/cydc/cydc/cydc_utils.py#L66)).
- **`AsmTemplate` usa `@` como delimitador de sustitución** (no `$`), por eso el
  ensamblador puede usar `$` libremente para hex y se ve `ORG @INIT_ADDR`,
  `@INCLUDES`, `@TOKENS`, `@DEFINE_IS_128`, etc.
- `run_assembler()` vuelca el string ensamblado a un `.asm` temporal
  (`cyd.asm`) y ejecuta sjasmplus con `--nologo -Wno-all`
  ([cydc_utils.py:76-92](src/cydc/cydc/cydc_utils.py#L76)).
- `bytes2str()` serializa listas de bytes a `DEFB $XX, ...` (16 por línea)
  ([cydc_utils.py:125-147](src/cydc/cydc/cydc_utils.py#L125)).

### 4.2 Funciones generadoras por target (en `cyd.py`)

| Target | Builder intérprete | Builder final | Plantilla "main" |
|---|---|---|---|
| 48k | `get_asm_48` ([cyd.py:401](src/cydc/cydc/cyd.py#L401)) | `do_asm_48` ([cyd.py:649](src/cydc/cydc/cyd.py#L649)) | `cyd_tape` |
| 128k | `get_asm_128` ([cyd.py:136](src/cydc/cydc/cyd.py#L136)) | `do_asm_128` ([cyd.py:746](src/cydc/cydc/cyd.py#L746)) | `cyd_tape` |
| plus3 | `get_asm_plus3` ([cyd.py:49](src/cydc/cydc/cyd.py#L49)) | `do_asm_plus3` ([cyd.py:851](src/cydc/cydc/cyd.py#L851)) | `cyd_plus3` |
| mld | `get_asm_mld` ([cyd.py:221](src/cydc/cydc/cyd.py#L221)) | `do_asm_mld` ([cyd.py:965](src/cydc/cydc/cyd.py#L965)) | `cyd_mld` |
| mld128 | `get_asm_mld128` ([cyd.py:302](src/cydc/cydc/cyd.py#L302)) | `do_asm_mld` (`mld_is_128=True`) | `cyd_mld` |

Cada `get_asm_*` construye un dict `d` con sustituciones (`INIT_ADDR`, `TOKENS`,
`CHARS`, `CHARW`, `INDEX`, `GAMEID`...), concatena módulos con
`get_asm_template(...).substitute(d)` en una variable `includes`, añade DEFINEs, y
finalmente sustituye en la plantilla "main" (`cyd_tape`/`cyd_plus3`/`cyd_mld`) con
`@INCLUDES = includes`.

### 4.3 Matriz de módulos `.asm` por target

Derivada directamente de las funciones `get_asm_*` ([cyd.py](src/cydc/cydc/cyd.py)).
`(*)` = condicionado a `has_tracks`/`use_wyz_tracker`.

| Módulo | 48k | 128k | plus3 | mld | mld128 | Rol |
|---|---|---|---|---|---|---|
| `inkey` | ✓ | ✓ | ✓ | ✓ | ✓ | teclado (ROM Spectrum) |
| `bank_zx128` | ✓ | ✓ | ✓ | ✓ | ✓ | paginación $7FFD |
| `bank_dan` | – | – | – | ✓ | ✓ | conmutación de slot Dandanator |
| `plus3dos` | – | – | ✓ | – | – | acceso +3DOS |
| `dzx0_turbo` | ✓ | ✓ | ✓ | ✓ | ✓ | descompresor ZX0 |
| `savegame_tape` | ✓ | ✓ | – | – | – | save/load cinta |
| `savegame_plus3` | – | – | ✓ | – | – | save/load disco |
| `savegame_mld` | – | – | – | ✓ | ✓ | save/load cartucho |
| `music_manager` | – | – | ✓(*) | – | – | gestor música (disco) |
| `music_manager_tape` | – | ✓(*) | – | – | ✓(*) | gestor música (cinta/banco) |
| `VTII10bG` (+`_vars`) | – | ✓(*) | ✓(*) | – | ✓(*) | reproductor Vortex PT3 |
| `screen_manager` | – | – | ✓ | – | – | gráficos (disco) |
| `screen_manager_tape` | ✓ | ✓ | – | ✓ | ✓ | gráficos (cinta/banco) |
| `text_manager` | ✓ | ✓ | ✓ | ✓ | ✓ | blitter de texto proporcional |
| `interpreter` | ✓ | ✓ | ✓ | ✓ | ✓ | núcleo fetch-decode-execute |
| `sysvars` / `vars` | ✓ | ✓ | ✓ | ✓ | ✓ | sysvars Spectrum + variables motor |

### 4.4 Símbolos `DEFINE` que distinguen target

Inyectados por `cyd.py`; consumidos con `IFDEF`/`IFNDEF` en el `.asm`.

| DEFINE | Dónde se pone | Significado | Consumo verificado |
|---|---|---|---|
| `IS_PLUS3` (1/0) | `cyd_plus3.asm` / `cyd_tape.asm` (en plantilla) | rama +3DOS | `cyd_tape.asm:35` (`=0`) |
| `IS_MLD` (1) | `cyd_mld.asm` | rama Dandanator | (agente) `cyd_mld.asm:35` |
| `IS_MLD_DAN` | [cyd.py:281](src/cydc/cydc/cyd.py#L281),[372](src/cydc/cydc/cyd.py#L372) | slot-switch puro Dandanator en LOAD_CHUNK/IMG_LOAD | `screen_manager_tape` (agente) |
| `IS_128_TAPE` | [cyd.py:213](src/cydc/cydc/cyd.py#L213),[393](src/cydc/cydc/cyd.py#L393) | inicializa bancos 128K | `cyd_tape.asm:61` (`SET_DEFAULT_BANKS`) |
| `USE_WYZ` / `USE_VORTEX` | [cyd.py:124-126](src/cydc/cydc/cyd.py#L124) etc. | reproductor musical | `cyd_tape.asm:37,64` |
| `PAUSE_AT_START_VAL n` | [cyd.py:115](src/cydc/cydc/cyd.py#L115) etc. | pausa tras carga | `cyd_tape.asm:79` |
| `MLD_HAS_INTRO_SCR` | [cyd.py:284](src/cydc/cydc/cyd.py#L284),[375](src/cydc/cydc/cyd.py#L375) | pantalla intro MLD | — |
| `SHOW_SIZE_INTERPRETER` | [cyd.py:494](src/cydc/cydc/cyd.py#L494) etc. | emite tamaño por stderr para medir | — |
| `IS_128` | [cyd.py:815](src/cydc/cydc/cyd.py#L815) (`do_asm_128`) | loader de cinta 128K | `loadertape` (`@DEFINE_IS_128`) |
| `LOADING_SCREEN` | [cyd.py:929](src/cydc/cydc/cyd.py#L929) | pantalla de carga plus3 | `loaderplus3` |

### 4.5 Puntos de entrada / loaders por target

- Cinta (48k/128k): plantilla `loadertape` ([cyd.py:712](src/cydc/cydc/cyd.py#L712),[817](src/cydc/cydc/cyd.py#L817)); cada bloque se emite con `SAVETAP ...,HEADLESS,...`.
- Disco (plus3): plantilla `loaderplus3` ([cyd.py:942](src/cydc/cydc/cyd.py#L942)); bloques a `.BIN` con `SAVEBIN`, luego ensamblados en `.DSK` (`make_plus3_dsk`).
- Dandanator (mld/mld128): plantilla `loadermld` ([cyd.py:1114](src/cydc/cydc/cyd.py#L1114)); layout de slots: 0=loader/footer, 1=intérprete, 2..N=bloques (uno por banco RAM usado). El índice TXT/SCR se **remapea** a slot+offset relativo ([cyd.py:1006-1016](src/cydc/cydc/cyd.py#L1006)).
- Plantilla "main" del intérprete: `cyd_tape.asm` (`START_INTERPRETER` en `@INIT_ADDR=$8000`, IM2, limpia variables, lee `IS_128_TAPE`/`USE_WYZ`/`PAUSE_AT_START_VAL`).

---

## 5. Modelo de opcodes y bytecode

### 5.1 Tabla de opcodes

- Diccionario `opcodes` (nombre→byte, 0x00-0x7E) en
  [cydc_codegen.py:~30-155](src/cydc/cydc/cydc_codegen.py#L30). Opcodes de 1 byte +
  operandos. Variantes por modo de operando: **`_D`** (literal directo), **`_I`**
  (indirecto vía `FLAGS[]`), **`POP_*`** (operando desde la pila de enteros). Un
  **peephole** pliega `POP_* + literal/var` en `_D`/`_I`
  ([cydc_codegen.py:~560-630](src/cydc/cydc/cydc_codegen.py#L560)).

### 5.2 ⚑ El bytecode es HOY independiente del target

**Hecho clave.** `codegen.generate_code()` produce **el mismo bytecode para los 5
targets** ([cydc.py:798-821](src/cydc/cydc/cydc.py#L798), llamado igual sin mirar
`model`). **Toda** la divergencia entre targets vive en el lado `.asm` (módulos +
DEFINEs). El parser y el codegen **no tienen ninguna noción de `model`**.

Implicación para el port CPC: CPC sería **el primer target donde diverge el
lenguaje/bytecode mismo** (keywords nuevas, aridad distinta, comandos eliminados),
así que es el primero que **obliga a dar a parser+codegen conciencia de target**.

### 5.3 Opcodes condicionales (`UNUSED_OP_*`) — driven por `-trim`, no por target

- `codegen.get_unused_opcodes(code)` calcula qué opcodes NO usa la aventura
  ([cydc.py:694-697](src/cydc/cydc/cydc.py#L694); codegen ~1152-1167).
- `get_unused_opcodes_defines()` emite `DEFINE UNUSED_OP_<NAME>` por cada uno
  ([cyd.py:26-32](src/cydc/cydc/cyd.py#L26)).
- En `interpreter.asm`, doble guarda: el cuerpo del handler va en
  `IFNDEF UNUSED_OP_<NAME>`, y la **jump table** pone `DW OP_<NAME>` o
  `DW ERROR_NOP` según `IFDEF/IFNDEF`. La tabla mantiene índices fijos.

> **Este es exactamente el mecanismo que el port CPC reutilizará** para divergir
> handlers por target (p.ej. `DW OP_PALETTE` vs `DW OP_FLASH` en el slot 0x26),
> con un DEFINE de target en vez de (o además de) `UNUSED_OP_*`. No hay maquinaria
> nueva que inventar en el lado asm.

---

## 6. Modelo de memoria y banking

- `spectrum_banks` por target ([cydc.py:823-834](src/cydc/cydc/cydc.py#L823)):
  48k/mld → `[0]`; 128k/mld128 → `[0,1,3,4,6,7]` (o `[0,3,4,6,7]` con WYZ); plus3 →
  `[0,1,3,4]` (o `[0,3,4,6]` con WYZ). El **banco 1 se reserva para WyzTracker**.
- `bank0_offset = 5*num_blocks + asm_size + 0x8000` ([cydc.py:807](src/cydc/cydc/cydc.py#L807));
  el intérprete vive desde `$8000`.
- Recursos se reparten por best-fit en los bancos; el **índice** es una tabla de
  entradas `(type, idx, bank, offset)` con tipos: **0=TXT, 1=SCR, 2=TRK, 3=WYZ**
  ([cydc.py:891-915](src/cydc/cydc/cydc.py#L891)).
- Límites de intérprete: 48k ≤ 32 KB; resto ≤ 16 KB ([cydc.py:781-784](src/cydc/cydc/cydc.py#L781)).
- **Geometría de pantalla** (256×192, plano de atributos 32×24, layout en tercios)
  está cocida en `sysvars.asm`/`vars.asm` + la lógica de memoria de `cydc.py`. Es
  uno de los puntos a parametrizar por target (ver MULTITARGET_DESIGN §2.3/§7).

---

## 7. Runtime / VM (resumen)

- **Intérprete** ([interpreter.asm](src/cydc/cydc/cyd/interpreter.asm), ~3.500
  líneas): fetch-decode-execute; jump table `OPCODES` indexada por opcode.
- **Render** (no hay back buffer; todo directo a pantalla, ver MULTITARGET_DESIGN
  §2): `text_manager` (blitter proporcional 1bpp con máscara+`rrca`, escribe
  atributo por celda) y `screen_manager*` (compositor de bloques; `BLIT`/`PICTURE`
  copian desde el almacén de imágenes `SCREEN_BUFFER_*` a pantalla).
- **Música AY** (`VTII10bG`/WyzTracker), **SFX** (BeepFx), **save/load**
  (`savegame_*`), **teclado** (`inkey`), **IRQ** IM2 a 50 Hz.

> Detalle del modelo de color/atributos del lenguaje (`INK`/`PAPER` 0-7,
> `BRIGHT`/`FLASH` 0/1, familia `FILLATTR`/`PUTATTR`/`GETATTR`/`ATTRVAL`/`ATTRMASK`,
> `FADEOUT`), y la corrección de que **no hay transparencia de texto** (el `cp 8`
> escribe una máscara que nadie lee): ver MULTITARGET_DESIGN §6.

---

## 8. Subsistema gráfico y modelo de carga de recursos (verificado)

> Descubrimientos verificados leyendo el código (no fiarse de resúmenes). Esto es
> el "cómo funciona hoy"; el diseño CPC que se construye encima está en
> MULTITARGET_DESIGN §10 (blitter texto), §11 (gráficos), §12 (carga/firmware).

### 8.1 Formato de imagen CSC ([cydc_csc.py](src/cydc/cydc/cydc_csc.py))

`.scr` (volcado de pantalla Spectrum, 6912 B) → `.csc` comprimido. Estructura:
cabecera `[filesize(2 B) + num_lines_pxl + num_lines_att]` (bit 7 de num_lines_att
= **flag mirror**) + **plano de píxel** (des-entrelazado de los tercios a orden
lineal) comprimido ZX0 + **plano de atributos** (768 B) comprimido ZX0. Si la
imagen es simétrica (detectado o forzado), **solo se guarda la mitad izquierda**
(cols 0-15); la derecha se reconstruye al cargar.

### 8.2 El buffer de imágenes (NO es back buffer)

`SCREEN_BUFFER_PXL` (bitmap lineal, 32 B/fila × hasta 192) + `SCREEN_BUFFER_ATT`
(768 B). Es el **almacén de imágenes** (origen de `BLIT`/`PICTURE`/`DISPLAY`), de
solo-lectura en la práctica — **no** una pantalla-sombra. El texto NO pasa por él
(va directo a pantalla).

### 8.3 Comandos de imagen (runtime)

- **`PICTURE` → `IMG_LOAD`**: carga el CSC al buffer (descomprime), **sin mostrar**.
- **`DISPLAY` → `COPY_SCREEN`** ([screen_manager_tape.asm:134](src/cydc/cydc/cyd/screen_manager_tape.asm#L134)):
  vuelca el buffer entero a pantalla.
- **`BLIT`** ([interpreter.asm:2078-2218](src/cydc/cydc/cyd/interpreter.asm#L2078)):
  copia un rectángulo en **unidades de carácter 8×8**, byte-alineado, **opaco**
  (sin máscara). Copia **dos planos**: píxel (8 scanlines/fila, +32 en buffer,
  direccionamiento de tercios en destino) **y** atributo (1 fila). 1 char = 1 byte
  de ancho. Coords en `CPY_SCR_BLK_*` (TMP_AREA); solo destino acepta variables.
- **Mirror** reconstruido al cargar ([screen_manager_tape.asm:72-141](src/cydc/cydc/cyd/screen_manager_tape.asm#L72)):
  píxeles invertidos bit a bit (`rra`/`rl`) + columnas en orden inverso; atributos
  solo invertidos por columna.

### 8.4 Modelo de carga de recursos: texto residente, medios cinta/disco

Índice de recursos: entradas `(tipo, idx, banco, offset)`; tipos **TYPE_TXT=0,
TYPE_SCR=1, TYPE_TRK=2, TYPE_WYZ=3**. `FIND_IN_INDEX` lo recorre.

| Recurso | Cinta (48k/128k) | Disco (plus3) |
|---|---|---|
| Texto | residente en banco; `LOAD_CHUNK`→`FIND_IN_INDEX`→`SET_RAM_BANK` | **idéntico** (residente) |
| Imágenes | residentes; `IMG_LOAD` descomprime banco→buffer ([screen_manager_tape.asm:33](src/cydc/cydc/cyd/screen_manager_tape.asm#L33)) | `IMG_LOAD` abre `.CSC` (`+3DOS`)→banco staging (img=6)→descomprime ([screen_manager.asm:36](src/cydc/cydc/cyd/screen_manager.asm#L36)) |
| Música | residente; `LOAD_MUSIC` apunta el player al banco ([music_manager_tape.asm:34](src/cydc/cydc/cyd/music_manager_tape.asm#L34)) | abre `.BIN`→banco→`VTR_INIT` ([music_manager.asm:34](src/cydc/cydc/cyd/music_manager.asm#L34)) |

**Regla:** texto **siempre residente** (se accede constantemente; streamearlo sería
letal). **Cinta = todo residente** (límite RAM). **Disco = imágenes y música
streameadas** de fichero a un banco de staging, bajo demanda (límite disco). El
reparto lo fija [cydc.py:803-806](src/cydc/cydc/cydc.py#L803) (`num_blocks`:
plus3 = solo chunks de texto; resto = texto+medios) y la elección de módulo
(`screen_manager` disco vs `screen_manager_tape`; `music_manager` vs `_tape`).

---

## 9. Añadir un target nuevo (p.ej. CPC): tres frentes

Sabiendo lo anterior, incorporar CPC se reparte así:

- **(a) Lado build/asm — sigue el patrón existente, mecánico.** Añadir `cpc` a las
  choices de `model`, escribir `get_asm_cpc()` (selección de módulos CPC + DEFINEs
  CPC), una plantilla "main" `cyd_cpc`, y la jump table condicional. Copia
  estructural de lo que ya hacen los 5 targets.
- **(b) Lado parser/codegen — genuinamente nuevo.** Hoy el bytecode es
  target-independiente (§5.2); CPC es el primero que diverge en el lenguaje, así
  que hay que parametrizar lexer (keywords válidas por target), parser (aridad y
  reglas divergentes) y codegen (mapa keyword→opcode y peephole por target). **No
  existe precedente: es el verdadero núcleo del trabajo Python.**
- **(c) Módulos `.asm` CPC nuevos — el grueso de esfuerzo.** Blitter de texto 2bpp
  entrelazado, screen/compositor, color (Gate Array/paleta), loader (.dsk AMSDOS /
  .cdt), teclado (firmware), AY (vía PPI 8255), IRQ 50 Hz. Diseño en
  MULTITARGET_DESIGN §5-§7.

---

## 10. Targets Dandanator/MLD (`mld` / `mld128`)

Estado (3 jul 2026): **funcionando y verificados en emulador** (ZEsarUX headless
con `--enable-dandanator`). Un cartucho Dandanator Mini son 32 bancos de 16 KB
mapeables en `$0000-$3FFF`. Layout MLD: slot 0 = loader (`loadermld.asm`), slot 1 =
intérprete (copiado a `$8000` al arrancar), slots 2..N = datos.

- **Direccionamiento slot-relativo (clave).** El intérprete MLD (define `IS_MLD_DAN`)
  lee TXT/SCR/bytecode desde el slot Dandanator mapeado en `$0000`: `LOAD_CHUNK`
  hace `SET_DAN_BANK(slot)` y `HL` es un offset **0-based dentro del slot**. Por eso
  las direcciones de salto del bytecode se emiten slot-relativas:
  `cydc.py` fija `codegen.set_bank_offset_list([0, 0])` para `model in (mld, mld128)`
  (vs `[bank0_offset, 0xC000]` residente de cinta), y `bank_size_list=[16K,16K]`
  (cada chunk en su slot de 16 KB). `bank_dan.asm SET_DAN_BANK` escribe el nº de
  comando en `$0001` (protocolo dual: vale para HW real por conteo de pulsos y para
  ZEsarUX por valor).
- **Diferencia `mld` vs `mld128`.** Es solo `spectrum_banks` y la música, NO el
  direccionamiento: `mld` (48K, `$83`) usa varios slots vía conmutación Dandanator
  (sin banking `$7FFD`), hasta 16 slots (~256 KB). `mld128` (128K, `$88`) además
  precarga la **música** a bancos RAM (el ISa del player lee de `$C000`); como el
  resto se lee de slots, desacopla slots (muchos, ids ≥ 8 "slot-only", sin precarga)
  de bancos RAM (≤6, solo música) → hasta ~480 KB. Limitación conocida: música +
  >96 KB de contenido no cabe (la música obliga a los 6 bancos RAM) → error limpio.
- **Runtime NO verificable en HW físico desde aquí** (no hay Dandanator); ZEsarUX es
  la vía autoritativa, salvo el *timing de pulsos* del PIC que no emula.

---

## 11. Cómo se construye la distribución (`dist/`) — IMPORTANTE

**`src/cydc/*` son los fuentes; `dist/*` es la COPIA que se distribuye y la que
ejecutan las herramientas de autor.** El build lo hace
[make_dist.py](make_dist.py): `copy_source_files()` copia la lista `get_source_files()`
(~57 ficheros: `cydc/*.py`, `cydc/cyd/*.asm`, `ply`, `pyZX0/7`…) de `src/cydc/` a
`dist/`, compila `.po`→`.mo`, y zipea por plataforma (`--skip-compile` salta la copia).

- **Las herramientas usan `dist/`, no `src/`.** `make_adventure.py` y
  `make_adventure_gui.py` ejecutan `dist/python/python.exe` (Python embebido) +
  `dist/cydc_cli.py`, que hace `sys.path.append('.../dist/cydc')` y
  `from cydc import main` → importa **`dist/cydc/`**.
- ⚠️ **El redirect a `src/` está MUERTO (a propósito, no tocar — solo saberlo).**
  Hay un `dist/python/Lib/sitecustomize.py` (generado por `setup_embedded_python.py`)
  que inserta `src/cydc` en `sys.path`, pero (1) apunta un nivel de más
  (los módulos están en `src/cydc/cydc/`) y (2) **nunca se ejecuta**: el `._pth` del
  Python embebido tiene `import site` comentado (`site` deshabilitado). Ambos son
  artefactos untracked.
- **CONSECUENCIA OPERATIVA: cualquier cambio en `src/cydc/` NO llega a las
  herramientas ni a la distribución hasta rehacer `dist/`** (ejecutar `make_dist.py`
  o su paso de copia). Es fácil olvidarlo y probar con un `dist/` stale. El
  `PYTHONIOENCODING=utf-8` que fijan ambas herramientas en el subproceso del
  compilador es obligatorio en Windows (consola cp1252 vs barras Unicode de uso de RAM).
