# Diseño: soporte multi-plataforma (CPC / MSX / ZX Next)

> Documento de trabajo. Recoge el análisis de viabilidad y las decisiones de
> arquitectura para llevar el motor de Choose Your Destiny (CYD) a ordenadores
> objetivo distintos del ZX Spectrum. **En estado exploratorio**: las decisiones
> marcadas como tomadas son firmes; los frentes abiertos quedan por resolver.
>
> **Requisito previo:** para entender cómo funciona la herramienta hoy (pipeline
> de compilación, mecanismo multi-target por compilación condicional, opcodes,
> banking) leer primero [ARCHITECTURE.md](ARCHITECTURE.md). Este documento asume
> ese conocimiento. La referencia autoritativa del **lenguaje** es el manual del
> wiki (`MANUAL_es.md`).

---

## 1. Objetivo y alcance

Evaluar y diseñar la incorporación de nuevos ordenadores objetivo (Amstrad CPC,
MSX1, ZX Spectrum Next) al motor CYD, hoy específico del ZX Spectrum, sin
romper la base reaprovechable (lenguaje, compilador, intérprete de opcodes).

Todos los candidatos comparten CPU **Z80**, lo que permite reaprovechar toda la
mitad "alta" del sistema. El coste real de portabilidad está concentrado en el
**subsistema gráfico-textual** y en el **modelo de color**.

---

## 2. Estado actual de la arquitectura

CYD se compone de dos mitades:

### 2.1 Front-end y núcleo (independiente del hardware)

- **Lenguaje** tipo BASIC para librojuegos.
- **Lexer / parser / codegen** en Python ([src/cydc/cydc/](src/cydc/cydc/)).
- **Bytecode** de opcodes de 1 byte + operandos
  ([cydc_codegen.py](src/cydc/cydc/cydc_codegen.py)).
- **Intérprete** de opcodes en Z80
  ([interpreter.asm](src/cydc/cydc/cyd/interpreter.asm), ~3.500 líneas) — lógica
  de fetch-decode-execute, mayormente neutral respecto al hardware.
- **Compresión de texto**, **fuentes**, **descompresor ZX0** — neutrales.
- **Reproductores de música AY** ([VTII10bG.asm](src/cydc/cydc/cyd/VTII10bG.asm),
  [wyz_player.asm](src/cydc/cydc/cyd/wyz_player.asm)) — reaprovechables; CPC, MSX
  y Spectrum 128 comparten el PSG AY-3-89xx. Solo cambia el acceso de I/O.

### 2.2 Subsistema gráfico-textual (acoplado al Spectrum)

El motor tiene **dos rutas de render distintas que componen sobre la misma
pantalla visible. No hay back buffer**: todo se dibuja directo a pantalla.

**(a) Texto — blitter de fuentes proporcionales.**
`PUT_VAR_CHAR` ([text_manager.asm:504-686](src/cydc/cydc/cyd/text_manager.asm#L504-L686))
posiciona caracteres a pixel arbitrario con máscara + rotación. Tres supuestos
del Spectrum entretejidos en la aritmética:
1. **1 bit = 1 píxel** (la tabla `.MASK` y el `rrca` de rotación solo valen a 1bpp).
2. **Layout de pantalla en tercios** del Spectrum (direccionamiento no lineal).
3. **Read-modify-write directo** sobre la RAM de pantalla.

Además escribe el atributo de color (`ATTR_P`) directamente en el plano de
atributos, celda a celda ([text_manager.asm:598-608](src/cydc/cydc/cyd/text_manager.asm#L598-L608)).

**(b) Gráficos — compositor de bloques.**
- Imágenes en formato **CSC**: bloques parciales comprimidos con ZX0, planos de
  píxel y atributo separados, espejado opcional
  ([cydc_csc.py:35-76](src/cydc/cydc/cydc_csc.py#L35-L76)).
- `IMG_LOAD` descomprime al **almacén de imágenes** `SCREEN_BUFFER_PXL/ATT`
  ([screen_manager.asm:36](src/cydc/cydc/cyd/screen_manager.asm#L36)), que vive en
  un banco de RAM paginado.
- **`BLIT` / `PICTURE`** copian rectángulos **desde ese almacén hacia la
  pantalla** ([interpreter.asm:2063-2184](src/cydc/cydc/cyd/interpreter.asm#L2063-L2184)).

> **Aclaración importante:** el almacén `SCREEN_BUFFER_*` **no es un back
> buffer**: es la reserva de imágenes cargadas que sirve de *origen* a BLIT y
> PICTURE. Es de solo-lectura en la práctica. El texto **no** pasa por él.
>
> **`BLIT` no son sprites:** es un bitblt de bloques **alineados a byte** y
> **opacos** (sin máscara ni transparencia). El único render a nivel de bit es
> el blitter de texto.

### 2.3 Resolución y geometría: cocidas en constantes

```
SCR_PXL_SIZE EQU 32*192     ; sysvars.asm:54
SCR_ATT_SIZE EQU 32*24
SCR_PXL      EQU $4000      ; plano de atributos en $4000+6144
MAX_X        DEFB 255       ; vars.asm:113
```
El motor asume **256×192 con plano de atributos 32×24, fijo**
([sysvars.asm:54-60](src/cydc/cydc/cyd/sysvars.asm#L54-L60),
[vars.asm:113](src/cydc/cydc/cyd/vars.asm#L113)).

### 2.4 Otros puntos de acoplamiento

- **Teclado:** [inkey.asm](src/cydc/cydc/cyd/inkey.asm) llama a la ROM del Spectrum.
- **Paginación:** [bank_zx128.asm](src/cydc/cydc/cyd/bank_zx128.asm) (puerto `$7FFD`),
  [bank_dan.asm](src/cydc/cydc/cyd/bank_dan.asm) (Dandanator).
- **Interrupción:** IM2 / VSYNC a 50 Hz.
- **Formatos de salida:** .tap, .dsk (+3), .mld; selección por modelo en
  [cyd.py](src/cydc/cydc/cyd.py) (`get_asm_48/128/plus3/mld/mld128`).

---

## 3. Reparto de esfuerzo

| Bloque | Reaprovechable | Comentario |
|---|---|---|
| Lenguaje, parser, codegen, bytecode | ~100% | Neutral |
| Intérprete (núcleo) | ~80–90% | Solo cambian llamadas a rutinas HW |
| Música AY | ~90% | Cambia I/O, no lógica |
| Teclado / IRQ / banking base | ~30% | Reescritura mecánica, acotada |
| **Render de texto + compositor gráfico** | ~10–20% | **El coste real: rediseño, no port** |
| Loaders / formatos de salida | nuevo | Acotado, lado Python + un loader/máquina |
| Pipeline de imágenes (Python) | nuevo | Formato de asset por máquina |

---

## 4. Decisiones tomadas

1. **MSX1 queda descartado.** Su VRAM tras el puerto del VDP rompe el supuesto
   fundacional "vídeo = RAM" de ambas rutas de render. La alternativa (back
   buffer + flush por rectángulos sucios) exige una pantalla-sombra de RAM que,
   sumada al almacén de imágenes, no cabe en 64K. Inviable con esta arquitectura.

2. **El listón de diseño es el CPC** — el peor caso *viable*. La capa de
   abstracción se diseña contra él, no contra el caso fácil (Next), para que la
   frontera no se rompa al tocar la plataforma hostil.

3. **CPC: un único modo, el Modo 1** (320×200, 4 pens, 2 bpp, 4 px/byte,
   empaquetado entrelazado). Fijado en tiempo de compilación (un target, como
   hoy se elige 48k/128k/plus3). No se soporta conmutación de modo en runtime.

4. **Sin back buffer.** Al descartar MSX1, nada obliga a introducirlo: el CPC
   tiene la pantalla en RAM. La arquitectura se mantiene en **"directo a
   pantalla"**, como hoy.

5. **El lenguaje deja de ser idéntico entre máquinas**, pero con divergencia
   acotada (ver §6). Front-end mayormente compartido.

6. **ZX Next:** consciente de que es de baja complejidad (modo compatibilidad
   ≈ gratis; modo nativo Layer 2 incluso *más simple* por framebuffer lineal
   8bpp + DMA). Por eso **no sirve como primer objetivo**: validar la
   abstracción contra el Next sería "dar la patada adelante". Se aborda después
   del CPC, si interesa.

---

## 5. Capa de abstracción de hardware (HAL)

La frontera del HAL debe dibujarse **por encima** de "pon un píxel / pon un
carácter", porque el modelo de píxel difiere por máquina. El contrato no puede
fijar **ni resolución, ni profundidad de color, ni empaquetado**: los tres son
parámetros del target.

### Descriptor de target (ejemplo CPC Modo 1)
```
{ ancho: 320, alto: 200, pens: 4, bpp: 2,
  packing: cpc_mode1_entrelazado, plano_atributos: no }
```

### Operaciones del contrato

| Operación | Capa neutral (arriba) | Específico de máquina (abajo) |
|---|---|---|
| Texto | "pinta esta tirada de texto en X,Y con color C" | empaquetado de píxel + direccionamiento + expansión de pen |
| BLIT / PICTURE | "copia este bloque del almacén a X,Y" | geometría + granularidad en píxeles del byte |
| Color | INK/PAPER/BRIGHT/FLASH lógicos | mapeo a pens/paleta; lo inexistente se ignora o emula |
| Imágenes | opcode PICTURE/BLIT | **formato de asset por máquina** |

### Consecuencias concretas en CPC Modo 1

- **Blitter de texto reescrito a 2bpp entrelazado:** cada bit de fuente (1bpp en
  almacenamiento) se expande a 2 bits del pen activo, con cruce de byte cada
  4 px, vía **tablas de expansión precalculadas** (técnica estándar CPC). La
  máscara+rotación 1bpp actual se sustituye, no se adapta.
- **`BLIT` a granularidad de 4 px** (byte = 4 px, no 8). Decisión pendiente:
  normalizar coordenadas a píxeles o asumir granularidad dependiente de máquina
  (ver §7).
- **Arte específico por máquina:** el CSC es nativo Spectrum (1bpp + atributos +
  tercios). El CPC necesita otro formato (2bpp empaquetado, con paleta, sin
  atributos, 320×200) y su conversor en Python. Una aventura multi-target
  necesita **assets gráficos rehechos**, no solo recompilar.

---

## 6. Modelo de divergencia del lenguaje

Principio: **palabra clave y slot de opcode son cosas distintas.**

- **Front-end:** la palabra clave **diverge** por target (p.ej. `FLASH` en
  Spectrum, `PALETTE` en CPC), cada una con su aridad natural.
- **Bytecode:** se **reutiliza el mismo slot de opcode**. El número no tiene
  semántica propia; se la da el intérprete del target.

Esto conserva el **recurso escaso (los 256 slots de opcode)**: al sobrecargar
slots que mueren en un target, el espacio de bytecode no se agota al añadir
máquinas. Como el flujo de bytecode es específico del target y nunca conviven dos
en el mismo binario, **la aridad del opcode puede diferir libremente** entre
máquinas (el intérprete CPC lee dos operandos donde el del Spectrum lee uno).

### Caso de referencia: FLASH → PALETTE

- **FLASH (Spectrum)** hoy: `FLASH <expr>`, un operando; opcodes `FLASH_D` 0x26,
  `FLASH_I` 0x28, `POP_FLASH` 0x4D
  ([cydc_codegen.py:66-105](src/cydc/cydc/cydc_codegen.py#L66)).
  Pone el bit 7 de `ATTR_P/ATTR_T`.
- **Aclaración (verificada en código, may 2026 — corrige una afirmación previa
  errónea):** existe una rama `cp 8` en INK/PAPER/BRIGHT/FLASH que escribe bits
  en el byte contiguo a `ATTR_P`/`ATTR_T` (los comentarios lo llaman
  `MASK_P`/`MASK_T`) ([text_manager.asm:104-220](src/cydc/cydc/cyd/text_manager.asm#L104-L220)).
  **Pero ese byte no se lee en ningún sitio** — ni siquiera existe como símbolo;
  `PUT_VAR_CHAR` vuelca el atributo con `ld a,(ATTR_P); ld (hl),e` sin consultar
  máscara ([text_manager.asm:598-608](src/cydc/cydc/cyd/text_manager.asm#L598-L608)).
  Es código **vestigial: CYD no tiene transparencia de texto** (confirmado por
  Sergio). No hay nada que portar por ese lado.
- **PALETTE (CPC):** keyword propia, `PALETTE pen, color` (dos operandos
  naturales), que **emite los mismos slots 0x26/0x28/0x4D**. El intérprete CPC
  los decodifica como definición de paleta del Gate Array.
- La **transparencia (valor 8) sigue teniendo sentido en CPC** → el espacio de
  valores/semántica debe partirse, no reemplazarse de cuajo.

El motor ya soporta el mecanismo: la tabla de salto usa ensamblado condicional
(`IFNDEF UNUSED_OP_… / DW OP_…`,
[interpreter.asm:3010+](src/cydc/cydc/cyd/interpreter.asm#L3010)). En el build
CPC, el slot 0x26 sería `DW OP_PALETTE` en vez de `DW OP_FLASH`.

### Reparto preciso compartido vs nuevo

| | Compartido | Nuevo por target |
|---|---|---|
| **Espacio de 256 opcodes** | ✅ recurso conservado (slots reutilizados) | — |
| Lexer (keywords) | — | conjunto de palabras válidas |
| Parser (reglas) | estructura común | regla y aridad de statements divergentes |
| Codegen | armazón | emisión y peephole D/I del operando |
| Intérprete | dispatch | handler del opcode |

Este es el **molde general del port**: un solo flujo de bytecode-semántica por
target, slots reutilizados, keywords y handlers divergentes donde el hardware
obliga. Los conceptos Spectrum-only (BRIGHT, FLASH, familia de atributos) **no se
portan**: sus slots se liberan y se reutilizan para comandos nativos CPC (ver §6).

### El color en CYD: lo que el lenguaje expone (verificado en el manual)

> Esta subsección reescribe un análisis previo que era superficial: planificó
> sobre `INK`/`PAPER`/`PALETTE` ignorando que el modelo de atributos del Spectrum
> está **expuesto como característica de primera clase del lenguaje**. Datos
> tomados del manual (`MANUAL_es.md`) y del codegen.

Comandos de color del lenguaje y sus valores **reales**:
- `INK` / `PAPER` / `BORDER`: **0-7** (colores Spectrum).
- `BRIGHT` / `FLASH`: **0/1** (toggle). No hay transparencia de texto (el `cp 8`
  del runtime escribe una máscara que nadie lee — vestigial; ver §6 arriba).
- **Familia de atributos (1ª clase, no interna):**
  - `FILLATTR x,y,w,h,attr` — rellena un rectángulo con un byte `FBPPPIII`,
    **"los píxeles no se alteran"**.
  - `PUTATTR attr,mask AT x,y` — atributo de una celda 8×8 con **máscara**
    (bit 0 = conserva pantalla, bit 1 = usa nuevo). **"Píxeles no se alteran"**.
  - `GETATTR(x,y)` — **lee** el atributo `FBPPPIII` de una celda.
  - `ATTRVAL(ink,paper,bright,flash)` / `ATTRMASK(...)` — arman el byte y la
    máscara en **tiempo de compilación** (no tienen opcode).
  - `FADEOUT x,y,w,h` — fundido a negro (en Spectrum, rampa de atributos).

### El núcleo del problema: color areal vs. color por píxel

Toda la familia de atributos (y `FADEOUT`) descansa sobre una premisa: **el color
vive en un plano areal (celdas 8×8) modificable de forma independiente de los
píxeles** — el manual lo dice literal, *"los píxeles no se alteran"*. En CPC
Modo 1 **eso no existe**: el color *es* el valor del píxel. No se puede cambiar
color sin tocar píxeles (`FILLATTR`/`PUTATTR`), ni "leer el atributo de una celda"
(64 píxeles con color propio — `GETATTR`), ni el formato `FBPPPIII` tiene sentido.
No es un swap de keyword/handler: es una familia cuyo **contrato semántico no
tiene sustrato hardware** en CPC. Esto, no `PALETTE`, es el verdadero coste del
color en el port.

### Principio rector del port (decisión de Sergio)

**El target CPC NO replica el lenguaje del Spectrum.** Se puede *alterar* lo que
haga falta: quitar lo que no tiene sustrato, redefinir lo que se puede mejorar, y
añadir lo nativo. Consecuencia inmediata: el "roce de portabilidad" (p.ej. `INK 5`
fuera del rango de pens) **deja de ser un problema a resolver** — es divergencia
aceptada, coherente con "un fuente con tramos por máquina". Un fuente CPC es un
fuente CPC.

### Decisiones de color CPC

| Comando | Decisión CPC |
|---|---|
| `INK` / `PAPER` | toman **pen 0-3** (handler selecciona pen, no escribe atributo). Mismo slot/aridad/par perm-temp; valores 4-7 = divergencia aceptada |
| `PALETTE pen,color` | **nuevo**, aridad 2. pen 0-3, color = nº firmware **0-26** (runtime traduce al GA). Reusa slots de FLASH `0x26`/`0x28`/`0x4D` |
| `BORDER` | reinterpretado a **0-26** (el borde es el pen 16 del GA). Sin slot nuevo |
| `BRIGHT` / `FLASH` | **no portados**; slots liberados (ver presupuesto) |
| `FILLATTR`/`PUTATTR`/`GETATTR` | **no portados** (sin sustrato). error-vs-NOP **configurable en el compilador** |
| `ATTRVAL`/`ATTRMASK` | desaparecen (compile-time, sin opcode; nada que armar en CPC) |
| `FADEOUT` | **redefinido**: `FADEOUT frames` = fundir **toda** la paleta a negro vía GA. **Cambia aridad** (la paleta es global, no admite rectángulo). Conserva `0x69` |
| `FADEIN` (nuevo) | fundir de negro a la paleta actual. Trivial en CPC; imprescindible para transiciones de escena |

**Paleta por defecto de 4 pens:** un fuente que use solo `INK`/`PAPER` sin
declarar `PALETTE` debe verse decente. Se fija una paleta de arranque sensata.

### Presupuesto de opcodes que libera el CPC (verificado en codegen)

| Familia Spectrum-only | Slots liberados |
|---|---|
| BRIGHT | `0x25` `0x27` `0x4C` |
| FLASH | `0x26` `0x28` `0x4D` → tomados por `PALETTE` |
| Familia ATTR | `0x6A` `0x75` (FILLATTR), `0x6B` `0x6C` `0x74` (PUTATTR), `0x70` (GETATTR) |
| FADEOUT | `0x69` — *no liberado*, redefinido para CPC |

≈ **9 slots libres** (BRIGHT ×3 + ATTR ×6) tras dedicar FLASH a `PALETTE`.

### Set de comandos nativos CPC — Fase 1: núcleo + transiciones (decidido)

`PALETTE`, `BORDER 0-26`, `FADEOUT` (paleta), `FADEIN`. Construidos sobre **la
superpotencia del CPC: la paleta del Gate Array** (4 pens × 27 colores,
recoloreable al instante sin tocar píxeles) — lo único que el Spectrum no puede, y
el reemplazo natural de lo que se quitó (BRIGHT/FLASH/ATTR eran manipulación de
color; en CPC la manipulación de color *es* la paleta).

**Fase 2 (diferida): ciclado / animación de paleta** — la firma del CPC (agua,
fuego, brillos, texto que "late"; recupera el `FLASH` en espíritu). Decisión
pendiente: **bloqueante** vs **en segundo plano** (servido por la IRQ de 50 Hz).
Quedan ~5-7 slots libres para añadirlo sin agobio. **Fuera de alcance** por ahora:
efectos raster/split de paleta, rainbow borders, scroll CRTC como comando.

### Estado de color en runtime (CPC) y blitter de texto

- `INK_PEN`/`PAPER_PEN` actuales (con par permanente/temporal).
- **LUT de expansión de 16 entradas** (`nibble 4px → byte Modo 1`), regenerada al
  cambiar INK/PAPER (no por glyph). Paleta del GA independiente del bitmap.
- **Blitter solo opaco** (no hay transparencia): cada celda del glyph se pinta con
  pen INK donde el bit de fuente es 1 y PAPER donde es 0,
  `pantalla = (pantalla AND mask_extent) OR pen_bits`. `mask_extent` cubre solo
  las columnas del glyph (los bytes parciales a fase sub-byte no deben pisar
  vecinos). Arquitectura completa del blitter en §5 / discusión del blitter 2bpp.

---

## 7. Frentes abiertos

- [x] **Color CPC:** RESUELTO (contrastado con manual). INK/PAPER = pen 0-3;
      `PALETTE`/`BORDER 0-26`; familia ATTR + BRIGHT/FLASH no portadas (slots
      liberados); `FADEOUT` redefinido + `FADEIN`. Ver §6.
- [ ] **Ciclado/animación de paleta CPC (Fase 2):** bloqueante vs background
      (IRQ 50 Hz). ~5-7 slots libres reservados.
- [x] **Blitter de texto 2bpp CPC:** DISEÑO HECHO (ver §10). Pantalla única
      `&C000` + buffer de imágenes; texto opaco (machaca fondo); máscara solo para
      straddle de ancho variable; vertical fila-alineado (+&800/línea, sin tabla);
      horizontal = shift 1bpp + `EXPAND_LUT[16]` (regen al cambiar INK/PAPER) +
      `COVER_LUT[16]`; camino rápido para ancho 8 alineado.
- [x] **Coordenadas de `BLIT`:** RESUELTO — mantener unidades de carácter 8×8
      (independiente de máquina; en CPC = 2 bytes/char, byte-alineado). Ver §11.
- [x] **Pipeline de imágenes:** DISEÑO HECHO (§11). Formato CSC-CPC (píxel Modo 1
      + paleta incrustada + mirror, ZX0, sin plano de atributos); conversor Python
      hermano de [cydc_csc.py](src/cydc/cydc/cydc_csc.py); BLIT solo píxel;
      paleta aplicada por flag explícito en `DISPLAY` (nunca automática, por ser
      global); mirror mantenido (tabla `FLIP4_LUT[256]`).
- [~] **Plataforma CPC (firmware/carga/memoria):** DECIDIDO usar **firmware en
      todos los targets** (AMSDOS disco, CAS cinta, KM teclado, IRQ firmware);
      modelo de carga = texto residente / cinta-todo-residente / disco-streamea
      medios. Ver §12. Implementación (módulos `amsdos`, `cas`, `bank_cpc`,
      driver AY-PPI, `screen_manager_cpc`) pendiente.
- [ ] **Alcance de targets CPC:** ¿464 cinta/64K, 664 disco/64K, 6128 disco/128K?
      (candidato a primero: 6128). Sin decidir. Ver §12.5.
- [~] **Front-end "target-aware":** DISEÑO HECHO (ver §9), implementación
      pendiente. Estrategia: superset de gramática + gating semántico; opcodes
      libres por target; superficie divergente pequeña (INK/PAPER/BORDER sin
      cambio; quitar 7 comandos ATTR/BRIGHT/FLASH; añadir PALETTE/FADEIN; FADEOUT
      cambia aridad). El build/asm sigue el patrón existente (ARCHITECTURE §8).
- [ ] **Geometría parametrizable:** sustituir las constantes fijas de §2.3
      (`sysvars.asm`/`vars.asm` + lógica de memoria de `cydc.py`) por parámetros
      del target. También sigue el patrón multi-target existente.

---

## 8. Resumen de targets

| Target | Texto 1bpp | Geometría | Acceso vídeo | Veredicto |
|---|---|---|---|---|
| **ZX Spectrum** (actual) | ✅ | ✅ tercios | ✅ RAM | Base |
| **Next (compat)** | ✅ igual | ✅ igual | ✅ igual | Casi gratis, sin ganancia |
| **Next (nativo L2)** | ❌ → 8bpp (más simple) | ✅ lineal | ✅ RAM + DMA | Reescritura *hacia abajo*; el más agradecido. Posterior al CPC |
| **CPC Modo 1** | ❌ 2bpp entrelazado | ❌ no lineal, 320×200 | ✅ RAM | **Listón de diseño** |
| **MSX1** | ✅ 1bpp (SCREEN 2) | ❌ tablas VDP | ❌ VRAM por puerto | **Descartado** (RAM/velocidad) |

---

## 9. Front-end "target-aware": diseño (DECIDIDO)

> Requisito: leer [ARCHITECTURE.md](ARCHITECTURE.md) §5 (modelo de opcodes y el
> hecho de que **hoy el bytecode es independiente del target**). Esta sección
> diseña el único trabajo Python sin precedente: dar a parser/codegen conciencia
> de target. El lado build/asm sigue el patrón existente (§8 / ARCHITECTURE §4,8).

### 9.1 La superficie de divergencia es pequeña (verificado en código)

Camino de un comando: lexer (dict `reserved` keyword→token,
[cydc_lexer.py:109+](src/cydc/cydc/cydc_lexer.py#L109)) → regla `p_*` que emite
tuplas de código (p.ej. `statement : INK varexpression` → `[expr…, ("POP_INK",)]`,
[cydc_parser.py:736-741](src/cydc/cydc/cydc_parser.py#L736)) → codegen (peephole
`PUSH+POP_INK → INK_D/INK_I` + dict opcode→byte).

- **`INK`/`PAPER`/`BORDER`: CERO cambio en front-end.** Gramática idéntica, mismos
  bytes. Que en CPC sean "pen" es solo el handler `.asm` (cubierto por intercambio
  de módulos).
- **Quitar** del target CPC: `BRIGHT`, `FLASH`, `FILLATTR`, `PUTATTR`, `GETATTR`,
  `ATTRVAL`, `ATTRMASK`.
- **Añadir**: `PALETTE pen,color` (2 operandos), `FADEIN frames` (1).
- **Cambiar aridad**: `FADEOUT` (4 operandos en ZX → 1 en CPC).

### 9.2 Estrategia: superset de gramática + gating semántico (DECIDIDO)

- **Una sola gramática PLY** con la **unión** de keywords/reglas de todos los
  targets. Ventaja: una sola tabla cacheada (`parsetab.py`), respeta el modelo de
  introspección de PLY; no se lucha contra él.
- **Capa de validación post-parse, parametrizada por target.** Usar un comando no
  permitido en el target activo → **error o NOP, configurable** (la política ya
  decidida para la familia ATTR / BRIGHT / FLASH). Las keywords "añadidas"
  (`PALETTE`/`FADEIN`) existen siempre en la gramática pero el gating las rechaza
  fuera de CPC.
- **Aridad divergente (`FADEOUT`)**: la gramática acepta **ambas** formas (1 y 4
  operandos); la validación por target comprueba el conteo correcto (ZX=4, CPC=1).

### 9.3 Opcodes: libres por target (DECIDIDO)

El bytecode es target-específico y la jump table también, así que **CPC no está
apretado de slots** (libera ~9, añade ~3). Por tanto:

- Los comandos **neutrales** mantienen su byte compartido (el codegen no necesita
  tablas por target para la mayoría).
- Los **divergentes** del CPC (`PALETTE`, `FADEIN`, `FADEOUT`-1arg) toman los bytes
  que convenga, **sin atarse a "reusar el slot de FLASH"** (ese ahorro del recurso
  de 256 opcodes no hace falta aquí; era pensar en un recurso escaso que en CPC no
  lo es).

### 9.4 Mecanismos concretos a implementar (sin precedente en el código)

1. **Propagar `target`/`model` a `CydcParser` y `CydcCodegen`** (hoy ninguno lo
   recibe; `model` ya existe en `cydc.py` y se pasa al lado asm, no al front-end).
2. **Tabla de "command set" por target** (datos de gating): qué comandos son
   válidos por target. Es el descriptor de target mínimo del lado Python.
3. **Pase de validación post-parse**: recorre las tuplas de código, aplica el
   gating con política error-vs-NOP.
4. **Mapa opcode→byte + tripletas D/I/POP por target** solo para el conjunto
   divergente; lo neutral se comparte.

### 9.5 Lo que NO cambia

PLY table caching intacto (un único superset). Control de flujo, expresiones,
variables, arrays, opciones, texto, sonido, save/load: **target-neutral, sin
tocar**. El lado build/asm: copia del patrón (`get_asm_cpc()`, plantilla `cyd_cpc`,
jump table condicional — ARCHITECTURE §8).

---

## 10. Blitter de texto CPC Modo 1: diseño (DECIDIDO)

> Verificado contra el blitter Spectrum real
> ([text_manager.asm](src/cydc/cydc/cyd/text_manager.asm): `PUT_VAR_CHAR`
> :504-686, `PUT_8X8_CHAR` :1067-1106) y el hardware CPC. Es el mayor coste del
> port (§3: render ~10-20% reaprovechable).

### 10.1 Modelo de pantalla (confirmado por Sergio)

- **Una sola pantalla visible en `&C000`**, CRTC por defecto: **80 bytes/línea ×
  200 líneas**, layout entrelazado clásico (las 8 líneas de una fila de carácter a
  saltos de `&800`). Se compone directo sobre ella (sin back buffer).
- **Buffer aparte para carga de imágenes**, origen de `BLIT`/`PICTURE` — análogo
  CPC del almacén `SCREEN_BUFFER_*` del Spectrum (no es back buffer; es el almacén
  de imágenes, de solo lectura en la práctica). Su ubicación/tamaño es parte del
  frente de geometría/memoria.

### 10.2 Modelo de render del texto (igual que Spectrum, reexpresado)

- **Texto OPACO: cada carácter machaca el fondo en su huella** (W píxeles × 8). No
  hay transparencia ni preservación de fondo (coherente con que el `cp 8` del
  Spectrum es vestigial, §6).
- **La única "máscara" es el straddle por ancho variable**: como la fuente
  proporcional no cae en la rejilla (4 px en CPC), un carácter a posición sub-byte
  reparte sus bits entre bytes; la máscara escribe solo las W columnas del glyph y
  **preserva el resto del byte compartido (el vecino)**. Es el equivalente exacto
  del `and (hl)` ("Mask screen") del `PUT_VAR_CHAR` Spectrum, NO transparencia.
- **Camino rápido** (ancho 8 + alineado a 4 px): escritura plana de bytes
  completos, sin máscara — como `PUT_8X8_CHAR`.
- Vertical **alineado a fila de carácter** (POS_Y en filas, no píxeles; verificado
  en el Spectrum). Solo la X es a píxel arbitrario.

### 10.3 Direccionamiento vertical: trivial, sin tabla

Como el texto es fila-alineado, las 8 líneas del glyph son
`base, base+&800, … base+&3800`, con
`base = &C000 + 80*fila + (x>>2)`. Avanzar de línea = **sumar 8 a H** (= +&800);
para filas 0-24 se queda dentro de `&C000–&FFFF` sin acarreo problemático. Más
simple que el `inc h` del Spectrum.

### 10.4 Horizontal: shift 1bpp + expansión por LUT

Mejora sobre el boceto inicial — **elimina tablas de shift de Modo 1**:
1. La fila de fuente (8 bits, 1bpp) se coloca en una ventana de **12 bits = 3
   nibbles** y se desplaza a la derecha `phase = x & 3` (0-3). Shift 1bpp puro,
   barato, **independiente del color**.
2. Cada uno de los 3 nibbles → `EXPAND_LUT[16]` → un byte Modo 1. Esa LUT
   (nibble→byte: pen INK donde bit=1, PAPER donde=0, ya en encoding disperso del
   Gate Array) es **la única cosa dependiente del color**: 16 bytes, regenerada
   solo al cambiar INK/PAPER (pens).
3. RMW en los bytes de pantalla `xbyte, xbyte+1, xbyte+2`.

Encoding Modo 1 (clave, absorbido por la LUT): un byte = dos planos alineados a
nibble — nibble alto (bits 7-4) = bit0/LSB de los pens de los 4 píxeles, nibble
bajo (bits 3-0) = bit1/MSB. Píxel 0 = bits 7 y 3, píxel 1 = bits 6 y 2, etc.

### 10.5 Máscara de straddle (cobertura de las W columnas)

El ancho W es constante por carácter, así que se calcula **una vez por carácter,
no por línea**: patrón de `W` unos → desplazado por `phase` (igual que la fuente)
→ expandido con `COVER_LUT[16]` (nibble→byte con `0b11` por píxel cubierto; fija,
independiente del color). RMW por byte:
`pantalla = (pantalla AND ~cover) OR (expand AND cover)`.

### 10.6 Coste y estado

Por línea: un shift 1bpp + 3 lookups `EXPAND_LUT` + 3 RMW (la cobertura ya está).
×8 líneas. Sobradamente absorbido por la pausa `PRT_INTERVAL` (motor de
librojuegos, texto a velocidad de lectura).

| Estructura | Tamaño | Cuándo se genera |
|---|---|---|
| `EXPAND_LUT[16]` | 16 B | al cambiar INK/PAPER (pens) |
| `COVER_LUT[16]` | 16 B | fija (build) |
| (sin tablas de shift Modo 1) | — | — |

### 10.7 Parámetros de geometría que fija

320×200, 80 bytes/línea, 25 filas de carácter, `MAX_X` = 319 (vs 255 Spectrum),
base `&C000`. Alimentan el frente de "geometría parametrizable" (§7).

---

## 11. Clúster gráfico CPC: BLIT + pipeline de imágenes (DECIDIDO)

> Verificado contra: formato CSC ([cydc_csc.py](src/cydc/cydc/cydc_csc.py)),
> carga ([screen_manager_tape.asm:33-181](src/cydc/cydc/cyd/screen_manager_tape.asm#L33)),
> y el handler `BLIT` ([interpreter.asm:2078-2218](src/cydc/cydc/cyd/interpreter.asm#L2078)).

### 11.1 Cómo es en Spectrum (base)

- **CSC**: cabecera (filesize + nº líneas pxl/att, bit 7 = mirror) + plano de píxel
  des-entrelazado a lineal + plano de atributos (768 B), ambos ZX0; mirror guarda
  solo la mitad izquierda.
- **Buffer**: `SCREEN_BUFFER_PXL` (bitmap lineal 32×192) + `SCREEN_BUFFER_ATT`.
  `PICTURE` carga CSC al buffer; `DISPLAY` lo vuelca a pantalla; `BLIT` copia un
  rectángulo.
- **`BLIT`**: coords en **unidades de carácter 8×8**, byte-alineado, opaco.
  Copia **dos planos**: 8 scanlines/fila (píxel) + 1 fila de atributo. 1 char =
  1 byte de ancho.

### 11.2 Decisiones CPC

- **`BLIT` mantiene unidades de carácter 8×8** (independiente de máquina; cierra
  §7). En CPC: 1 char = 8 px = **2 bytes**, sigue byte-alineado → copia de bloque
  **opaca, sin máscara**. Destino con direccionamiento entrelazado `&C000`
  (+&800/scanline dentro de la fila, +80/fila). **Solo plano de píxel: fuera el
  bucle de atributos** (no hay plano de atributos en CPC).
- **Formato `CSC-CPC`** (hermano de CSC): plano de píxel **Modo 1** (2bpp,
  reorganizado lineal para BLIT, sin plano de atributos) + **paleta incrustada de
  4 pens** en cabecera + flag mirror, todo ZX0. Conversor Python nuevo
  (hermano de `cydc_csc.py`) desde una imagen Modo 1 + su paleta.
- **Paleta: incrustada en el asset pero aplicada SOLO por decisión explícita del
  autor, nunca automática.** Razón: en CPC la **paleta es global** → aplicarla
  recolorea todo lo ya dibujado (texto incluido). Mecanismo decidido: **flag en
  `DISPLAY`** que indica si además de mostrar se aplica la paleta de la imagen
  (encoding — bitflags en el parámetro actual o 2º operando — a afinar en
  implementación; el front-end §9 permite aridad por target). `PICTURE` carga al
  buffer y guarda la paleta para un posible apply posterior, **sin tocar el GA**.
  - Consecuencia asumida: si el autor muestra una imagen sin aplicar su paleta,
    se verá con los pens actuales. Es el precio de los 4 pens globales; el autor
    decide qué paleta manda. Coherente con "un fuente con tramos por máquina".
- **Mirror: se mantiene** (ahorra espacio en imágenes simétricas). Coste 2bpp: en
  CPC reflejar = invertir orden de píxeles **y** reordenar los bits dispersos
  dentro del byte. Runtime: tabla fija de 256 entradas "voltea 4 px Modo 1" +
  copia en orden de columna inverso (análogo al bucle mirror de `IMG_LOAD`, pero
  con la tabla en vez del bit-reverse 1bpp). Detección de simetría (build, Python)
  también ajustada al reordenamiento Modo 1.

### 11.3 Resumen de lo nuevo a construir

| Pieza | Qué |
|---|---|
| Conversor `cydc_csc_cpc.py` | imagen Modo 1 + paleta → CSC-CPC (pixel ZX0 + paleta + mirror) |
| Runtime carga | `IMG_LOAD` CPC: descomprime a buffer Modo 1, guarda paleta, reconstruye mirror vía tabla 256 |
| `BLIT` CPC | copia opaca 2 bytes/char, solo píxel, destino entrelazado `&C000` |
| `DISPLAY` CPC | vuelca buffer a pantalla; flag aplica (o no) la paleta de la imagen |
| Tabla `FLIP4_LUT[256]` | voltea 4 px Modo 1 (para mirror) — fija |

---

## 12. Plataforma CPC: carga de recursos, firmware y memoria (DECIDIDO en parte)

> Verificado: carga de texto/imágenes/música en cinta y disco
> ([cyd_tape.asm:423](src/cydc/cydc/cyd/cyd_tape.asm#L423),
> [screen_manager.asm:36-151](src/cydc/cydc/cyd/screen_manager.asm#L36),
> [music_manager.asm:34-84](src/cydc/cydc/cyd/music_manager.asm#L34),
> [music_manager_tape.asm:34](src/cydc/cydc/cyd/music_manager_tape.asm#L34)).

### 12.1 El eje cinta/disco no es formato, es modelo de carga

| Recurso | Cinta (48k/128k) | Disco (plus3) |
|---|---|---|
| Texto | residente en banco (`FIND_IN_INDEX`) | **igual** (residente) |
| Imágenes | residente; `IMG_LOAD` descomprime banco→buffer | abre `.CSC` (+3DOS) → banco staging → descomprime→buffer |
| Música | residente; player apunta al banco | abre `.BIN` de disco → banco → `VTR_INIT` |

**Regla:** texto **siempre residente**; **cinta = todo residente** (límite RAM);
**disco = imágenes y música streameadas** de fichero a un banco de staging, bajo
demanda (límite disco, ahorra RAM). El disco usa la API de ficheros de la ROM
(`+3DOS`). Este eje se traslada tal cual al CPC.

### 12.2 Decisión: usar el firmware Amstrad en TODOS los targets

Coherente con el patrón que CYD ya usa en plus3 (llama a `+3DOS` *en la ROM*, no
reimplementa disco). Razón decisiva: **el disco en CPC = AMSDOS, que es una ROM
del firmware**; hacerlo a hierro pelado obligaría a pilotar el uPD765 a mano
(desproporcionado) o a usar la ROM AMSDOS igualmente (que requiere el firmware).

El firmware da vía jumpblock: **AMSDOS** (disco), **CAS** (cinta `.cdt`),
**KM_READ_KEY** (teclado), y el **ticker de interrupción** (el CPC genera IRQ a
300 Hz = 6/frame). Coste: ~6 KB de workspace arriba.

> Hierro pelado descartado como punto de partida; solo se consideraría como
> optimización posterior para un hipotético target cinta/64K sin disco.

### 12.3 Implicaciones de mapa de memoria (CPC)

- **Pantalla visible: `&C000-&FFFF` (16 KB)**. Las escrituras a `&C000` van
  siempre a RAM (el vídeo no estorba a la ROM alta).
- **Firmware: workspace + jumpblock ~`&A700-&BFFF`**; **AMSDOS baja HIMEM** (~`&A680`)
  para su buffer de sector. (Valores exactos según config; confirmar al implementar.)
- **Banking CPC**: puerto `&7Fxx` (el 6128 conmuta los 4 bloques de 16 K en
  `&4000-&7FFF`), distinto del `$7FFD` del Spectrum → módulo `bank_cpc`.
- **AY vía PPI 8255** (no `OUT` directo) en cinta y disco por igual → cambia el
  driver de I/O del reproductor, no su lógica.
- **Tensión 64K**: pantalla 16 K + buffer de imagen (hasta 16 K) + ~6 K firmware
  dejan poco para intérprete+texto. Mitigación: dimensionar el buffer al alto real
  de la imagen (el `-il num_lines` ya existe).

### 12.4 Módulos `.asm` CPC nuevos (siguen el patrón multi-target, ARCHITECTURE §4)

`bank_cpc` (paginación `&7Fxx`), `amsdos` (API ficheros, hermano de `plus3dos`),
`cas` (cinta), `screen_manager_cpc` en dos variantes (cinta residente / disco
stream), música con driver AY-PPI, teclado vía `KM_READ_KEY`, setup de IRQ. Más el
`get_asm_cpc()` y la plantilla `cyd_cpc`.

### 12.5 Alcance de targets CPC: estudio de 64K y recomendación

Trinidad análoga a 48k/128k/plus3: **CPC464** (cinta/64K), **CPC664** (disco/64K),
**CPC6128** (disco/128K, cómodo).

**Estudio del 64K — el mapa real (RAM usable ≠ 64K − pantalla):**
- `&0000-&3FFF`: ROM baja (OS); la RAM de debajo solo es ejecutable si se
  desactiva la ROM baja.
- `&4000-&BFFF`: siempre RAM (~32K), menos workspace de firmware arriba
  (~`&A680-&BFFF`, ~6K con AMSDOS).
- `&C000-&FFFF`: pantalla (16K; escrituras siempre a RAM).
- → **Modo "fácil"** (ROM baja mapeada): ejecutable solo en `&4000-&A67F` ≈
  **~26K**. **Modo "reclaim"** (desactivar ROM baja: handler IM1 propio en
  `&0038` + reactivar ROM alrededor de cada llamada a firmware/AMSDOS):
  recupera ~16K → **~42K**. El presupuesto real es 26-42K, **no 48K**.

**Consumidores residentes:** buffer de imagen **hasta 16K** (Modo 1 pantalla
completa, sin plano de atributos; vs ~6.75K en Spectrum — **el gran devorador**,
dimensionable con `-il`); intérprete (a medir); texto residente (el grueso);
vars/fuente/pila ~2-3K.

**Giro cinta vs disco en 64K:** cinta (464) = **todo residente incl. medios** →
lo más apretado. Disco (664 / 464+unidad) = **medios streameados** → solo buffer
de descompresión transitorio + intérprete + texto residentes → **netamente más
viable**. En 64K el disco no es comodidad: es lo que hace caber una aventura media.

**Palancas:** streaming por disco (la mayor) · dimensionar buffer con `-il` ·
reclaim de `&0000-&3FFF` · cinta sin AMSDOS (~1.4K).

**Recomendación (opinión honesta, pedida por Sergio):**
- **6128 disco/128K**: target principal y de bring-up (el cómodo).
- **Perfil 64K-disco** (664 / 464+unidad): objetivo "llegar a más máquinas";
  incremento modesto sobre el 6128 (mismo streaming, menos banking).
- **Cinta/464 (casete): NO merece la pena** como objetivo — pelea contra el
  fuerte de CYD (texto + medios residentes en el modelo más apretado), peor
  UX (cargas largas), I/O extra que mantener (deuda de variantes, cf. Dandanator),
  y el usuario real de 464 hoy suele tener disco/SD. **Solo si hay meta concreta
  de edición física en casete**, y entonces tarde y como modo "aventuras pequeñas".
- En una frase: **soportar 64K sí, pero por disco; saltar la cinta** salvo casete
  físico.

**Estado: estudio y recomendación cerrados; decisión formal de alcance diferida**
(se paró aquí para continuar otro día).
