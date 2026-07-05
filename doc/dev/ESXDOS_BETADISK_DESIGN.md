# Diseño: targets de almacenamiento ESXDOS y BetaDisk / TR-DOS

> Documento de trabajo. Recoge el análisis del framework y el diseño para incorporar
> dos nuevos **targets de almacenamiento** al motor CYD sobre ZX Spectrum: **ESXDOS**
> (divMMC/divIDE, tarjeta SD) y **BetaDisk / TR-DOS** (interfaz Beta 128, disquete).
>
> **A diferencia del port a CPC** ([MULTITARGET_DESIGN.md](../../MULTITARGET_DESIGN.md)),
> aquí **NO cambia ni el lenguaje, ni el bytecode, ni el render, ni el color**: la
> máquina sigue siendo un ZX Spectrum. Lo único que cambia es **la capa de
> almacenamiento** (cómo llegan intérprete + datos a memoria, y cómo se leen medios y
> se guardan partidas). Es, por tanto, un trabajo del mismo tipo que `plus3` frente a
> `48k`/`128k`, **acotado al lado build/asm**, sin tocar parser/codegen.
>
> **Requisito previo:** leer [ARCHITECTURE.md](../../ARCHITECTURE.md) (pipeline de
> compilación, mecanismo multi-target por compilación condicional, size-pass,
> `LOAD_CHUNK`, banking). Este documento asume ese conocimiento.
>
> **Estado: DISEÑO. Nada implementado.** Las decisiones de arranque están abiertas y
> deben cerrarse con Sergio ANTES de tocar código (§9). Todo cambio de código irá a
> `src/cydc/cydc/`; `dist/` se regenera después (ARCHITECTURE §11).

---

## 1. Objetivo y alcance

Añadir dos `model` nuevos al compilador (`cydc.py` `choices`), cada uno con su trío
`get_asm_<t>` / `get_asm_<t>_size` / `do_asm_<t>` en `cyd.py`, su plantilla "main"
(`cyd_esxdos.asm` / `cyd_trdos.asm`), su loader, y sus módulos de disco (acceso a
chunks, imágenes, música, savegame). **El objetivo de valor** de estos targets frente
a `48k`/`128k` (cinta) es el mismo que aporta `plus3`: **streaming de imágenes/música
desde ficheros de disco**, liberando RAM residente para más contenido; más el
**savegame en fichero** (múltiples ranuras, sin la fricción de la cinta).

Fuera de alcance: cualquier cambio en el lenguaje, el bytecode, el render o el modelo
de color. Si un cambio de esos aparece, es señal de que algo se ha entendido mal.

---

## 2. El contrato de la capa de almacenamiento (verificado en código)

Extraído leyendo `cyd_tape.asm`, `cyd_plus3.asm`, `cyd_mld.asm`, sus loaders,
`plus3dos.asm`, `screen_manager*.asm`, `savegame_*.asm` y el pipeline `cyd.py`/`cydc.py`.
**Un target de almacenamiento nuevo debe reimplementar exactamente esta interfaz.**

### 2.1 Hecho clave: el texto/bytecode es RESIDENTE en TODOS los targets Spectrum

Contra la intuición de "target de disco = todo se streamea de disco": en `plus3`,
igual que en cinta, **`LOAD_CHUNK` no toca el disco**. Es idéntico al de cinta:

```
; cyd_plus3.asm:435-444  (idéntico a cyd_tape.asm:424-433)
LOAD_CHUNK:              ; A = nº de chunk
    ld (CHUNK), a
    ld c, a
    ld b, TYPE_TXT
    call FIND_IN_INDEX   ; -> B=banco RAM, HL=offset (índice residente)
    ld (CHUNK_ADDR), hl
    ld (SCRIPT_BANK), a
    or ROM48KBASIC
    call SET_RAM_BANK    ; pagina el banco RAM vía $7FFD
    ret
```

El texto/bytecode vive en **bancos RAM residentes** (`spectrum_banks`), cargados de
una vez por el loader al arrancar. El disco (+3DOS) se usa **solo** para: (a) el
loader, (b) imágenes (`screen_manager.asm`, `IMG_LOAD`), (c) música
(`music_manager.asm`), (d) savegame (`savegame_plus3.asm`). Ese es el eje
cinta/disco: **texto siempre residente; en disco, medios streameados**
([MULTITARGET_DESIGN §12.1](../../MULTITARGET_DESIGN.md); ARCHITECTURE §8.4).

**Consecuencia para ESXDOS/TR-DOS:** el grueso del intérprete (`LOAD_CHUNK`,
`FIND_IN_INDEX`, render, banking $7FFD, ISR) es **compartido con `plus3` sin
cambios**. Solo hay que reescribir 4 piezas de I/O: loader, `IMG_LOAD`, `LOAD_MUSIC`,
savegame — cambiando la API +3DOS por RST $08 (ESXDOS) o #3D13 (TR-DOS).

### 2.2 Símbolos y ABI que un target debe proveer

| Símbolo / rutina | ABI | Provisto hoy por |
|---|---|---|
| `LOAD_CHUNK` (A=chunk → pagina banco RAM residente) | igual en todos | `cyd_<t>.asm` |
| `LOAD_DATA_CHUNK` (A=DATA id → pagina banco, HL=offset) | igual | `cyd_<t>.asm` |
| `FIND_IN_INDEX` (B=tipo, C=idx → B=banco, HL=off) | igual | `cyd_<t>.asm` |
| `IMG_LOAD` (A=nº imagen → descomprime a `SCREEN_BUFFER_*`) | igual | `screen_manager*.asm` |
| `COPY_SCREEN` (vuelca buffer→pantalla vía ISR) | igual | `screen_manager*.asm` |
| `LOAD_MUSIC` / `VTR_INIT` | igual | `music_manager*.asm` |
| `DO_SAVE` / `DO_LOAD` (A=slot, BC=rango FLAGS) | igual | `savegame_*.asm` |
| `SET_RAM_BANK`, `SET_DEFAULT_BANKS` | $7FFD | `bank_zx128.asm` (compartido) |

Los tipos del índice: `TYPE_TXT=0, TYPE_SCR=1, TYPE_TRK=2, TYPE_WYZ=3, TYPE_DATA=4`
([cyd_plus3.asm:427-431](../../src/cydc/cydc/cyd/cyd_plus3.asm#L427)).

### 2.3 La API +3DOS (lo que ESXDOS/TR-DOS deben emular)

`plus3dos.asm` envuelve cada llamada +3DOS en `PLUS3_DOS_SETUP_BANKS` / `..._RESTORE_BANKS`
(pagina la ROM +3DOS y el banco 7, llama, restaura). Las que CYD usa realmente:

| Uso | Rutina +3DOS | Dónde |
|---|---|---|
| Loader (arranque) | `DOS_OPEN $0106`, `DOS_READ $0112`, `DOS_CLOSE $0109`, `DOS_SET_1346 $013F`, `DOS_OFF_MOTOR $019C` | `loaderplus3.asm` |
| Imagen | `PLUS3_DOS_OPEN`, `PLUS3_DOS_READ` (cabecera 2B + cuerpo), `PLUS3_DOS_CLOSE` | `screen_manager.asm:53-148` |
| Savegame | `PLUS3_DOS_OPEN` (acción crear/leer), `PLUS3_DOS_WRITE/READ`, `PLUS3_DOS_CLOSE`, `PLUS3_DOS_ABANDON` (error) | `savegame_plus3.asm:199-271` |

**Peculiaridad crítica de +3DOS que NO comparten ESXDOS ni TR-DOS:** `DOS_READ`/`DOS_WRITE`
reciben en `C` **el banco RAM a paginar** para el buffer, y +3DOS lo pagina por ti. En
ESXDOS/TR-DOS, la lectura va a la **dirección del mapa de memoria ACTUAL** — hay que
**paginar el banco destino manualmente con $7FFD antes de la llamada** y pasar la
dirección ($C000, $E000…). Esto es una diferencia de forma, no de fondo: se resuelve en
el wrapper de cada API.

---

## 3. Las fórmulas de layout (aquí vivieron los bugs de mld48 — verificadas)

Un target de almacenamiento replica el patrón `plus3`. **Si el size-pass y la pasada
final no coinciden byte a byte, el loader lee de menos y la máquina cuelga.** Las dos
fórmulas a replicar con exactitud, derivadas del código real:

### 3.1 Tamaño del bloque del intérprete en el `BLOCK_LIST` del loader

El size-pass mide el intérprete con `INDEX` y `EXTERN_DISPATCH` **vacíos**
([cyd_plus3.asm:577-593](../../src/cydc/cydc/cyd/cyd_plus3.asm#L577):
en la rama `SHOW_SIZE_INTERPRETER`, `INDEX:` y `EXTERN_DISPATCH:` son labels sin
contenido; `get_asm_plus3_size` pasa `index=""`, `size_index=0` y sin
`extern_dispatch` — [cyd.py:797-810](../../src/cydc/cydc/cyd.py#L797)). Por eso la
pasada final debe **sumar** al tamaño el índice y la tabla de dispatch:

```python
# do_asm_plus3 (cyd.py:1421-1425)
dispatch_bytes = extern_dispatch.count("DEFB") * 3
block_list  = "DEFW $8000\n"                                        # dir del intérprete
block_list += f"DEFW ${size_interpreter + 5*len(index) + dispatch_bytes:X}\n"  # ← tamaño REAL
block_list += "DEFB $0\n"                                           # banco 0
```

El `+ 5*len(index)` = 5 bytes por entrada del índice (`DEFB tipo,idx,banco : DEFW off`).
El `+ dispatch_bytes` = 3 bytes por rutina nativa (tabla `EXTERN_DISPATCH`, colocada
justo tras el índice en la imagen guardada). **Este `+dispatch` fue el bug de "loader
leyendo de menos" del handoff.** El target nuevo hereda esta fórmula tal cual.

### 3.2 `bank0_offset` (dónde empieza el contenido del banco 0)

```python
# cydc.py:929-931
bank0_offset = (5*num_blocks) + dispatch_size + asm_size + mld128_arr_table_bytes + 0x8000
```

El intérprete vive desde `$8000`; tras él van el índice (`5*num_blocks`), la tabla de
dispatch (`dispatch_size`), y en el banco 0 empieza el contenido en `bank0_offset`.
`mld128_arr_table_bytes` es 0 en targets no-MLD. Para `plus3`, `num_blocks =
len(chunks)` (los medios no cuentan como bloques residentes); para cinta,
`len(blocks)+len(chunks)` ([cydc.py:917-920](../../src/cydc/cydc/cydc.py#L917)).
**ESXDOS/TR-DOS siguen la rama `plus3`** (`num_blocks = len(chunks)`).

### 3.3 Invariante de protección (lección mld48)

Al implementar, **añadir un assert de invariante** que falle el build si el tamaño
declarado en `BLOCK_LIST` ≠ (bytes realmente escritos por `SAVEBIN` del intérprete +
índice + dispatch). En `plus3` esto se cumple porque `cyd_plus3.asm:592` hace
`SAVEBIN "@DSK_PATH", START_INTERPRETER, SIZE_INTERPRETER` con `SIZE_INTERPRETER =
$ - START_INTERPRETER` **después** de emitir índice y dispatch, así que el fichero
guardado ya incluye todo. Hay que reproducir ese orden exacto en la plantilla nueva.

---

## 4. El uso de la ROM Spectrum por el intérprete (aviso de Sergio — verificado)

El intérprete **usa la ROM Spectrum en $0000–$3FFF** para cosas concretas. Esto
importa porque los dos backends de disco manipulan justo esa zona:

- **Teclado:** `INKEY` llama a `KEY_SCAN`, `K_TEST`, `K_DECODE` (rutinas de la ROM 48K
  a direcciones fijas) — [inkey.asm:43-53](../../src/cydc/cydc/cyd/inkey.asm#L43). En
  MLD ya hay precaución `RESTORE_DAN_ROM` porque el slot Dandanator ocupa $0000
  ([inkey.asm:36-41](../../src/cydc/cydc/cyd/inkey.asm#L36)).
- **Banking:** el intérprete pagina la **ROM 48K BASIC** (`or ROM48KBASIC`,
  `ROM48KBASIC EQU %00010000`, [bank_zx128.asm:32](../../src/cydc/cydc/cyd/bank_zx128.asm#L32))
  en 13 sitios de `interpreter.asm` al mapear bancos RAM — deja la ROM 48K visible.
- **Save/load de cinta:** `savegame_tape.asm` llama a `$04C6` (SA_BYTES) y **`$0562`**
  (LD_BYTES) — [savegame_tape.asm:188,225](../../src/cydc/cydc/cyd/savegame_tape.asm#L188).
- **ISR:** IM2 con tabla propia en `$8080` (`ISR_TABLE` = `HIGH ISR`); **no** encadena
  con la ROM (`;jp $3a` está comentado, [cyd_plus3.asm:390](../../src/cydc/cydc/cyd/cyd_plus3.asm#L390)).

### 4.1 Por qué esto es MÁS fácil que en Dandanator (pero hay que vigilarlo)

El automap del divMMC y la paginación de la ROM Beta **solo se activan durante la
llamada de disco y se auto-desmapean al volver** (§5.1, §6.1). A diferencia del
Dandanator —que deja un slot mapeado en $0000 de forma persistente y por eso necesita
`RESTORE_DAN_ROM` antes de cada `KEY_SCAN`— aquí **la ROM Spectrum está visible en
$0000–$3FFF el 99% del tiempo** (todo lo que no sea el instante de una lectura de
disco), así que **el teclado funciona sin tratamiento especial**. Las lecturas de disco
son atómicas: pagina → lee → desmapea.

### 4.2 Riesgos concretos a vigilar (checklist de verificación en emulador)

1. **Direcciones-trap del divMMC.** El automap se dispara al hacer *fetch* en
   `$0000, $0008, $0038, $0066, $04C2, $0562`. Hay que confirmar que **ninguna rutina
   ROM que el intérprete invoca pasa por esas direcciones**: `KEY_SCAN`/`K_TEST`/
   `K_DECODE` no lo hacen; la ISR es IM2 propia (no `$0038`). ✔ en teoría, **verificar
   en emulador**.
2. **`savegame_tape` es inutilizable en ESXDOS/TR-DOS.** Usa `$0562`/`$04C2`, que son
   direcciones-trap del divMMC (¡son las rutinas de cinta que ESXDOS intercepta para
   redirigir a SD!). El savegame de estos targets **debe ser por fichero** (F_WRITE /
   #3D13), nunca `savegame_tape`.
3. **Código y buffers del backend fuera de $0000–$3FFF.** El intérprete vive en $8000+
   y los buffers en $C000+ (intactos por el automap). El loader vive en el área BASIC
   ($5Cxx+) — también a salvo. Ninguna rutina de disco debe ejecutar ni bufferar en
   $0000–$3FFF.
4. **TR-DOS:** durante `#3D13` la ROM Spectrum se sustituye por la ROM Beta; la llamada
   no puede depender simultáneamente de la ROM 48K. Atomicidad estricta.

### 4.3 La ISR: ¿ataca la ROM? (revisado a fondo — aviso de Sergio)

Revisada la ISR completa ([cyd_tape.asm:130-389](../../src/cydc/cydc/cyd/cyd_tape.asm#L130),
[cyd_plus3.asm:140-390](../../src/cydc/cydc/cyd/cyd_plus3.asm#L140)): **en operación
normal NO toca la ROM.**

- Sus únicas `CALL` son a rutinas **propias en RAM alta**: `VTR_ISR`, `VTR_MUTE`
  (reproductor Vortex en el banco paginado a $C000), `WYZ_TRACKER` ($C000). Ninguna
  llamada a $0000–$3FFF.
- El resto es acceso a **pantalla ($4000)**, `SCREEN_BUFFER_*`, `SCR_ATT`, puertos
  (`in a,($1f)` kempston, `out ($7ffd)` banking) y variables — todo RAM/E-S.
- El `reti` **no encadena con la ROM** (`;jp $3a` comentado,
  [cyd_plus3.asm:390](../../src/cydc/cydc/cyd/cyd_plus3.asm#L390)). No depende del ISR
  de la ROM.
- El vector IM2 se lee de `ISR_TABLE` en `$8080` (`= HIGH ISR`), **no de la ROM**;
  `I=$80`. Independiente de qué haya en $0000–$3FFF.
- (El `LD SP,$3131` de `VTII10bG.asm` es código automodificable del reproductor, **no**
  una dirección de ROM: es un `LD SP,nn`, no un `CALL`.)

**Conclusión:** la ISR es indiferente a lo que haya paginado en $0000–$3FFF; puede
disparar con la ROM Spectrum, la ROM ESXDOS o la ROM Beta abajo sin corromper nada,
**porque no lee ni ejecuta de esa zona.**

**El único riesgo** es que la IRQ salte *durante* una lectura de disco, si la rutina de
disco dejara las interrupciones habilitadas: entonces la ISR se ejecutaría bien (no toca
$0000–$3FFF), **pero volvería (`reti`) al medio de la secuencia de disco**, y sobre todo
el reproductor de música pagina bancos con `$7FFD` a mitad de una transferencia →
corrupción del banking de la lectura. **Invariante obligatorio (ya lo hace +3DOS):
`DI` alrededor de toda llamada de disco, `EI`/`RETI` al terminar.** +3DOS lo hace en
`PLUS3_DOS_SETUP_BANKS` (`DI`, [plus3dos.asm:47](../../src/cydc/cydc/cyd/plus3dos.asm#L47))
y `..._RESTORE_BANKS` (`EI`). Los wrappers `esxdos.asm`/`trdos.asm` deben replicarlo:
`DI` → paginar banco → RST $08 / CALL #3D13 → restaurar → `EI`.

---

## 5. Target ESXDOS (divMMC / divIDE, tarjeta SD)

### 5.1 La API ESXDOS y el automap (investigado; fuentes en §10)

Llamada: `RST $08 : DEFB hook`. Tras ella cambian `AF,BC,DE,HL`. Las que CYD necesita:

| Hook | Nº | Entrada | Salida |
|---|---|---|---|
| `F_OPEN` | `$9A` | `IX`=nombre ASCIIZ, `B`=modo (`$01` read, `$0C` create/al), `A`=drive (`$FF`/`*`=actual) | `A`=handle, CF error |
| `F_READ` | `$9D` | `A`=handle, `IX`=dir destino, `BC`=nº bytes | CF si error |
| `F_WRITE` | `$9E` | `A`=handle, `IX`=dir origen, `BC`=nº bytes | CF si error |
| `F_CLOSE` | `$9B` | `A`=handle | CF error |
| `F_SEEK` | `$9F` | `A`=handle, `BCDE`=offset, `L`=modo | — |

Dos diferencias de forma frente a +3DOS: (a) la dirección va en **`IX`** (no `HL`); (b)
lee/escribe al **mapa actual**, así que hay que **paginar el banco destino con $7FFD**
antes de `F_READ` y pasar `IX`=$C000/$E000.

**Automap:** los *fetch* en las direcciones-trap mapean la ROM ESXDOS en $0000–$1FFF y
un banco RAM del divMMC en $2000–$3FFF; el primer byte se lee de la ROM Spectrum, los
siguientes de ESXDOS; al salir de la ventana, se desmapea. **Solo afecta $0000–$3FFF**
→ el intérprete ($8000+) y los bancos ($C000+) quedan **intactos**. Por eso `RST $08`
es seguro desde memoria alta y no interfiere con el banking $7FFD.

### 5.2 Banking: ESXDOS libera bancos 6 y 7 (aprovechando el apunte de Sergio)

`plus3` reserva bancos 6/7 para +3DOS: `spectrum_banks = [0,1,3,4]`
([cydc.py:992-996](../../src/cydc/cydc/cydc.py#L992)); el banco 6 es staging de
imágenes (`IMG_BANK=6`) + `PIC_BUFFER` en $E000, y el 7 es workspace de +3DOS.
**ESXDOS no usa +3DOS**, así que:

- El banco 7 queda **libre** → recuperable como banco de contenido residente.
- El banco 6 sigue haciendo falta como **staging** para descomprimir imágenes (F_READ
  lee la imagen comprimida a un buffer y `dzx0_turbo` la expande a `SCREEN_BUFFER`),
  pero eso es un uso transitorio, no un DOS residente.
- **DECIDIDO (Sergio): `spectrum_banks = [0,1,3,4,6,7]`** — el presupuesto completo del
  `128k`, sin dedicar un banco entero a staging. La descompresión de imágenes se hace en
  un **buffer residente pequeño** (leer el CSC comprimido por trozos, o a un buffer del
  tamaño del CSC, y expandir a `SCREEN_BUFFER`), **no** reservando el banco 6 como en
  plus3. Explícitamente **no replicar las limitaciones de plus3** siendo conservadores:
  ESXDOS lleva tanto contenido residente como el `128k`. (Detalle de implementación: el
  buffer de staging residente debe dimensionarse al peor caso del CSC — pantalla
  completa comprimida; encaja porque ZX0 comprime y `-il` limita líneas.)

### 5.3 Modelo de arranque (DECIDIDO: núcleo + autoarranque OPCIONAL)

ESXDOS **no arranca de la SD automáticamente** como el +3. **Sergio: el autoarranque es
imprescindible como OPCIÓN** (muchos usuarios lo reclaman; análogo al `-a` de
`mld2rom`). El diseño separa **bootstrap** (siempre igual) de **cómo se dispara**
(manual por defecto, automático con flag).

**Núcleo del loader (siempre):** un cargador **BASIC** idéntico en estructura a
`loadertape.asm` (línea REM con código máquina + `RANDOMIZE USR`), pero el código, en
vez de `LD_BYTES` (cinta ROM), hace `RST $08` `F_OPEN`+`F_READ` para leer el fichero de
datos (`.DAT`) desde la SD a los bancos residentes (paginando cada banco antes del
`F_READ`), y `CALL $8000`. Reutiliza toda la maquinaria de `loadertape` (estructura
BASIC + `BLOCK_LIST`); la ROM 128K queda inicializada (arranca por BASIC normal). **El
bootstrap va en RAM alta ($5Cxx / $8000+), nunca en $0000–$3FFF** (lo pisaría el
automap durante el `F_READ`).

**Cómo se dispara — dos modos (flag del compilador, p.ej. `-autoboot`):**

- **Por defecto (sin flag): lanzamiento manual.** Salida = `.TAP` (el loader BASIC) +
  `JUEGO.DAT` (datos). El usuario copia ambos a la SD y lanza el `.TAP` desde el
  **navegador NMI** de ESXDOS. Simple, funciona en cualquier versión de ESXDOS.
- **Con `-autoboot`: autoarranque.** Dos mecanismos posibles (sub-decisión §9):
  - **(A1) AUTOBOOT nativo (ESXDOS 0.8.6+).** El mismo loader BASIC se emite como
    `/SYS/AUTOBOOT.BAS`; ESXDOS lo auto-ejecuta en el arranque si
    `/SYS/CONFIG/ESXDOS.CFG` tiene `AutoBoot=1`. **Ventaja:** mecanismo oficial y
    limpio, ROM inicializada, sin incluir binarios de sistema. **Pega:** requiere
    ESXDOS ≥ 0.8.6 y que la config lo habilite. **Recomendado por defecto.**
  - **(A2) utoboot (Utodev).** `AUTOEXEC.BIN` en raíz + stubs `ESXDOS.SYS`/`BETADISK.SYS`
    incluidos; se ejecuta en $8000. **Ventaja:** funciona en cualquier versión de
    divMMC (lleva su propio core), ideal para copias físicas. **Pega:** la ROM **no**
    queda inicializada ("don't expect the system variables to be there") → el arranque
    debe montar las sysvars mínimas a mano antes de usar la ROM (teclado). Opción
    "compatibilidad universal", más frágil.

**Recomendación:** por defecto manual (`.TAP`+`.DAT`); `-autoboot` genera además el
`AUTOBOOT.BAS` nativo (A1); dejar utoboot (A2) como modo avanzado documentado. Encaja
con el pipeline: `SAVETAP` para el loader, `SAVEBIN` concatenado para el `.DAT` (como
el `.BIN` de `plus3`), y un emisor de `AUTOBOOT.BAS`/config para el modo autoboot.

> **A revisar en implementación:** el formato exacto de `AUTOBOOT.BAS` que espera
> ESXDOS (fichero BASIC tokenizado, con/ sin cabecera), cómo emitirlo desde el pipeline
> (hoy `SAVETAP BASIC`), y si conviene que la herramienta genere/parchee
> `ESXDOS.CFG`. Verificar en ZEsarUX con `--esxdos-root-dir` apuntando a una carpeta
> con `/SYS/AUTOBOOT.BAS`.

### 5.4 Mapeo de la capa de almacenamiento a ESXDOS

| Pieza | plus3 (+3DOS) | ESXDOS (RST $08) |
|---|---|---|
| Loader | `loaderplus3.asm`: OPEN fichero datos, READ bloques a bancos, CLOSE, `CALL $8000` | `loaderesxdos.asm`: F_OPEN `.DAT`, por cada `BLOCK_LIST` paginar banco + F_READ a `IX`, F_CLOSE, `CALL $8000` |
| `IMG_LOAD` | `screen_manager.asm` (OPEN `NNN.CSC`, READ cabecera+cuerpo a banco 6, descomprime) | `screen_manager_esxdos.asm`: F_OPEN, F_READ cabecera (2B) a buffer, F_READ cuerpo a banco staging, descomprime (idéntico de aquí en adelante) |
| Música | `music_manager.asm` (OPEN `.BIN`, READ a banco, VTR_INIT) | `music_manager_esxdos.asm`: F_OPEN/F_READ a banco, VTR_INIT |
| Savegame | `savegame_plus3.asm` (OPEN `NN.SAV`, WRITE/READ SAVE_START, CLOSE/ABANDON) | `savegame_esxdos.asm`: F_OPEN (create/read), F_WRITE/F_READ, F_CLOSE. **Nunca `savegame_tape`.** |
| `wrapper` | `plus3dos.asm` (SETUP/RESTORE_BANKS) | `esxdos.asm`: wrappers finos `RST $08 : DEFB hook`, con paginación previa del banco destino |

El resto (`interpreter`, `text_manager`, `bank_zx128`, `dzx0_turbo`, ISR, `LOAD_CHUNK`,
`FIND_IN_INDEX`) es **el mismo binario que plus3/128k**.

### 5.5 Verificación en emulador (ZEsarUX 13.0, ya en `tools/`)

ZEsarUX soporta ESXDOS headless. Flags (de `--experthelp`): `--enable-divmmc`
(ports+paging), `--enable-esxdos-handler` (**requiere** divmmc o divide paging),
`--esxdos-root-dir <dir>`, `--mmc-file <img>`, `--copy-file-to-mmc <src> <dst>`. ROM
incluida: `esxmmc085.rom`. Dos modos: (i) **handler trampeado** del emulador
(`--enable-esxdos-handler`, intercepta RST $08 → ficheros del host; rápido para CI pero
no ejercita el automap real); (ii) **divMMC + ROM ESXDOS real** (.mmc; ejercita el
automap). **Para fiabilidad usar (ii) al menos en una prueba**; (i) para el grueso de CI.

---

## 6. Target BetaDisk / TR-DOS (interfaz Beta 128, disquete)

### 6.1 La API TR-DOS y la paginación de la ROM Beta (investigado; §10)

Acceso: `CALL #3D13` con `C`=nº de función (y registros según función). La **ROM
TR-DOS se pagina por hardware al hacer *fetch* en `#3Dxx`** con la ROM BASIC activa;
al salir de esa zona, vuelve la ROM Spectrum. Controlador VG93 (=WD1793) por puertos
`$1F/$3F/$5F/$7F/$FF` si se quisiera pilotar a hierro.

Carga de fichero por nombre (funciones de la ROM TR-DOS):
- **Fn `#0A` (buscar fichero):** nombre/tipo en variables DOS `#5CDD…`; devuelve nº de
  descriptor o `#FF` si no existe.
- **Fn `#0E` (cargar):** descriptor en `#5DCC`; `A=#03` → `HL`=dirección, `DE`=longitud
  (o `A=#00`/`#FF` para tomar dir/long del catálogo).

Alternativa directa por track/sector (más simple de controlar, sin variables DOS):
`LD HL,dir : LD DE,track/sector : LD BC,nº_sectores : CALL #3D13` (subfunción de lectura
de sectores). Requiere conocer la geometría del fichero en el catálogo (lo sabe el
empaquetador Python al construir el `.TRD`).

### 6.2 Arranque TR-DOS

TR-DOS ejecuta automáticamente un fichero **`boot.B`** (BASIC) al entrar (por
`RANDOMIZE USR 15616`, botón "magic", o arranque de máquina tipo Pentagon en TR-DOS).
`boot.B` hace un `RANDOMIZE USR` que lanza el cargador máquina; éste usa `#3D13` para
leer el fichero de datos a los bancos y salta a $8000. Análogo al loader BASIC de
`plus3`, pero el auto-arranque lo da TR-DOS (no hace falta navegador).

### 6.3 Riesgos específicos de TR-DOS (mayores que ESXDOS)

1. **Coexistencia con 128K.** TR-DOS clásico es de mundo 48K; la ROM Beta y el banking
   `$7FFD` deben coordinarse. El intérprete usa `$7FFD` intensivamente (bancos
   residentes). Hay que confirmar que la ROM Beta no interfiere con el banking en
   memoria alta, o restringir TR-DOS a un modelo de máquina concreto (Pentagon 128, o
   48K residente puro).
2. **Atomicidad ROM Beta ↔ ROM 48K.** Durante `#3D13`, la ROM Spectrum no está; el
   teclado (KEY_SCAN) no puede ejecutar a la vez. Igual que ESXDOS, pero por otro
   mecanismo.
3. **Variables DOS.** La carga por nombre (`#0A`/`#0E`) escribe en el área de sistema
   `#5CDD…`; hay que asegurar que no pisa datos del intérprete (el intérprete arranca
   en $8000, sysvars intactas por debajo).
4. **Modelo de máquina.** Beta 128 se asocia normalmente a Pentagon. Decidir el/los
   modelos objetivo (Pentagon 128, Spectrum 128 + Beta, 48K + Beta).

### 6.4 Verificación en emulador

ZEsarUX: `--enable-betadisk`, `--enable-trd`, `--trd-file <f>`, ROM `trdos.rom`;
máquinas `Pentagon`/`P340`/`P341`/`P3S` en `--machinelist`. Empaquetar el `.TRD` en
Python (formato de disco TR-DOS: pista/sector/catálogo — Python puro, sin binarios
externos, coherente con [[feedback-minimize-external-tooling]]).

---

## 7. Comparativa de complejidad y plan por fases

| Eje | ESXDOS | TR-DOS |
|---|---|---|
| API | POSIX limpia (F_OPEN/READ/WRITE/CLOSE) | `#3D13` + variables DOS, o track/sector |
| Automap/paginación | solo $0000–$3FFF, atómico, auto-desmapea | ROM Beta por fetch $3Dxx; coexistencia 128K delicada |
| Arranque | `.TAP` bootstrap (reusa `loadertape`) | `boot.B` auto (TR-DOS lo lanza) |
| Empaquetado Python | fichero `.DAT` (SAVEBIN concat) + `.TAP` | escritor de `.TRD` (catálogo/pista/sector) nuevo |
| Emulación ZEsarUX | handler trampeado + divMMC real | Betadisk + `.TRD` + máquina Pentagon |
| **Coste relativo** | **bajo–medio** (espejo de `plus3`) | **medio–alto** (ROM Beta + `.TRD` writer) |

**Plan por fases (cada fase: verde en la suite completa + verificada en ZEsarUX):**

1. **F1 — ESXDOS bring-up. ✅ HECHO + VERIFICADO (jul 2026).** Implementado como
   **espejo del target 128k RESIDENTE** (todo el contenido en bancos RAM cargados al
   arranque; `screen_manager_tape`/`music_manager_tape` residentes) con la I/O de
   arranque/save por `RST $08`. Ficheros nuevos (en `src/cydc/cydc/`): `esxdos.asm`
   (wrappers `ESXDOS_F_OPEN/READ/WRITE/CLOSE`, `DI`/`EI`), `loaderesxdos.asm`
   (bootstrap BASIC en `.TAP` que F_READ el `.DAT` a los bancos), `cyd_esxdos.asm`
   (copia de `cyd_tape` con `SAVEBIN @DAT_PATH`), `savegame_esxdos.asm` (savegame por
   fichero; NO `savegame_tape`). En `cyd.py`: `get_asm_esxdos`/`_size`/`do_asm_esxdos`
   (empaquetado `.DAT` único como +3, contenido residente como 128k). En `cydc.py`:
   `esxdos` en `choices`, size-pass, banking `[0,1,3,4,6,7]`, guarda de externs,
   despacho `do_asm`. Harness: `MACHINE_BY_MODEL["esxdos"]="128k"`, `run_in_zesarux`
   con `--enable-divmmc --enable-esxdos-handler --esxdos-root-dir`; `test_esxdos` en
   `test_data/sugar/sugar3_runtime.py`. **Verificado en ZEsarUX (MATCH exacto del
   programa DATA); suite completa 421/0/0.** Gotchas resueltos: (a) los EQU `ESX_*`
   se definen SOLO en `esxdos.asm` (el loader los referencia; duplicarlos daba
   "Duplicate label"); (b) fórmulas de layout heredadas de do_asm_128/plus3 cuadran
   byte a byte (`.DAT` = interp+índice+contenido). **Falta para ser distribuible:
   streaming de medios (F2), autoarranque, y `-scr` (loading screen no cableada aún).
   NO regenerar `dist/` hasta que ESXDOS esté completo (decisión de Sergio).**
2. **F2 — ESXDOS streaming de medios.**
   - **F2a — IMÁGENES: ✅ HECHO + VERIFICADO (jul 2026).** `screen_manager_esxdos.asm`
     (IMG_LOAD por `RST $08`: F_OPEN/F_READ `NNN.CSC` de la SD → `PIC_BUFFER` en la
     **mitad alta ($E000) del banco de staging IMG_BANK=6** → ZX0 a `SCREEN_BUFFER` →
     mirror; restaura `SCRIPT_BANK`). `get_asm_esxdos` usa `screen_manager_esxdos` +
     `USE_PIC_BUFFER` (en vez del residente `screen_manager_tape`). `cydc.py`:
     `spectrum_banks=[0,1,3,4,7,6]` (staging **banco 6 al final, capado a 8KB** en el
     allocator; mitad baja $C000-$DFFF allocable — opción B de Sergio); SCR excluidos
     de residencia (`place_blocks`), streameados; `.csc` copiados sueltos al output
     (SD root). `cyd_esxdos.asm`: añadido `DISK_ERROR`. Verificado en ZEsarUX:
     `PICTURE 0`+`DISPLAY 1` de una imagen full → **6144/6144 bytes de píxel en
     pantalla** (streaming desde fichero SD, no residente). Gotcha del test durable:
     **`DISPLAY 0` es NOP** (`OP_DISPLAY_D` hace `or a; jp z`), usar `DISPLAY 1`.
     Limitación conocida: un chunk de TEXTO que caiga en el banco 6 y exceda 8KB da
     error limpio ("Block too big"); solo en aventuras muy grandes (≥6 chunks).
   - **F2b — MÚSICA (pendiente):** Vortex Tracker streamea de disco al **resto del
     banco de staging (banco 6, `$C000-$DFFF`)** compartiendo con `PIC_BUFFER` ($E000)
     — modelo plus3 (`MDLADDR=$C000`, `VORTEX_BANK=6`). Con música Vortex, el banco 6
     queda reservado entero (fuera de la allocación de contenido). WyzTracker reserva
     su propio banco (1). `music_manager_esxdos.asm` (F_READ el `.BIN`) + `.bin`
     sueltos + allocator condicional a presencia de música. Se puede hacer con las
     variables `MDLADDR`/`VORTEX_BANK` de cyd_tape puestas a $C000/6 en runtime (sin
     rebasar cyd_esxdos sobre cyd_plus3).
   - **Savegame:** ya hecho en F1 (`savegame_esxdos.asm`, por fichero).
3. **F3 — TR-DOS bring-up.** Escritor `.TRD` en Python, `boot.B`, `loadertrdos.asm`,
   `trdos.asm` (`#3D13`), plantilla `cyd_trdos`. Fijar modelo de máquina (§6.3).
   Texto/bytecode residente. Test runtime en ZEsarUX Pentagon+TRD.
4. **F4 — TR-DOS medios + savegame.** Espejo de F2 con `#3D13`.

**Empezar por ESXDOS** (F1) porque es el espejo más directo de `plus3` y el automap no
toca la zona del intérprete.

---

## 8. Riesgos de layout/build (resumen accionable)

- **Size-pass ↔ pasada final byte-exactos** (§3): heredar `5*len(index)+dispatch_bytes`
  en el `BLOCK_LIST` y `bank0_offset`; añadir assert de invariante.
- **Orden en la plantilla:** el `SAVEBIN` del intérprete debe ir *después* de emitir
  índice y `EXTERN_DISPATCH`, como en `cyd_plus3.asm:584-593`.
- **`num_blocks = len(chunks)`** (rama plus3), no la de cinta.
- **No reutilizar `savegame_tape`** (traps $0562/$04C2).
- **pyZX0/pyZX7 son O(n²):** no recomprimir la pantalla de carga N veces (lección
  mld48); comprimir una sola vez.
- **Símbolos importados:** `import sys`/`os`/`re` donde haga falta en las funciones
  nuevas de `cyd.py` (lección mld48).
- **Suite COMPLETA** (`python tests/run_tests.py`), no tests sueltos; los bugs de
  layout aparecen con mocks/orden de la suite.

---

## 9. Decisiones (CERRADAS con Sergio) y sub-decisiones pendientes

**Cerradas:**
- **Alcance:** ESXDOS primero (completo y verificado); **TR-DOS diferido** a otra sesión.
- **ESXDOS banking:** `[0,1,3,4,6,7]` (presupuesto 128k, staging de imagen en buffer
  residente; no replicar las limitaciones de plus3). §5.2.
- **ESXDOS arranque:** núcleo = loader BASIC (`RST $08`) que reusa `loadertape`;
  **autoarranque OPCIONAL** vía flag; por defecto manual (`.TAP`+`.DAT`). §5.3.
- **TR-DOS máquina objetivo:** decidir al llegar a TR-DOS.

**Sub-decisiones pendientes (no bloquean el bring-up F1; cerrar durante F1/F2):**
1. **Autoarranque — mecanismo:** (A1) `AUTOBOOT.BAS` nativo 0.8.6+ [recomendado] vs
   (A2) utoboot (`AUTOEXEC.BIN` + stubs SYS). Ver §5.3.
2. **Formato de salida:** `.TAP` (loader) + `JUEGO.DAT` (datos), y en modo autoboot
   además `/SYS/AUTOBOOT.BAS` (+ opcionalmente `ESXDOS.CFG`). ¿Nombre del `.DAT`?
   ¿Se genera también una carpeta/imagen de SD lista para copiar?
3. **Nombre del flag** de autoarranque (`-autoboot`?) y su UX en las herramientas GUI.

**TR-DOS (cuando se aborde):** modelo de máquina; carga por nombre (`#0A`/`#0E`) vs
track/sector directo; escritor `.TRD` en Python.

---

## 10. Fuentes (investigación web)

- esxDOS API / RST $08: dailly.blogspot.com "esxDOS File access"; board.esxdos.org
  (nail down esxdos api); ESXDOS manual.
- Automap divMMC: DivMMC docs (mprato/DivMMC `Divmmc_allram_manual.txt`); SpecNext Wiki
  "DIVMMC"; utoboot (Utodev) para el modelo de arranque SD.
- TR-DOS / `#3D13`: spectrumcomputing.co.uk `TR-DOS_Programming.txt`; "Loading TR-DOS
  files through $3D13"; TR-DOS Wikipedia; Beta Disk Interface.
- ZEsarUX: chernandezba/zesarux README y `--experthelp` (flags ESXDOS/Betadisk/TRD);
  ROMs en `tools/ZEsarUX_windows-13.0/`.

> **Advertencia de rigor:** todo lo de este documento marcado como "investigado" (§5.1,
> §6.1) procede de fuentes web y **debe confirmarse en ZEsarUX** antes de darlo por
> bueno. Lo marcado con `file:line` está verificado de primera mano en el repo.
