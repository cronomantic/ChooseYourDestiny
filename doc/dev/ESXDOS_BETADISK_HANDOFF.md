# Prompt de continuación — Targets ESXDOS y BetaDisk (+ evaluación PLY→Lark)

> Pega esto como primer mensaje de la próxima sesión. Está escrito para que Claude
> **revise el framework a fondo ANTES de tocar nada** y no reaparezcan los problemas de la
> tanda mld48 (fórmulas de layout mal, tests sueltos que pasan pero la suite completa
> falla, caché global que rompe mocks, símbolos sin importar). Sergio: Sergio Chico
> (cronomantic), trabaja en español, ZX Spectrum + Python a nivel profundo. Verificación
> EMPÍRICA en emulador obligatoria; NADA se da por bueno por leer código.

---

## Contexto (lo ya hecho — NO rehacer)

CYD (ChooseYourDestiny) es un compilador Python (PLY LALR) de un lenguaje CYOA a bytecode
de 1-byte-opcode que corre un intérprete Z80. Targets actuales, **los 5 verdes**:
`48k`/`128k` (TAP), `plus3` (DSK), `mld`/`mld128` (Dandanator MLD). La capa de
almacenamiento está **abstraída por target**: loaders (`loadertape/plus3/mld.asm`), acceso
a chunks (`cyd_tape/plus3/mld.asm` con `LOAD_CHUNK`), savegame (`savegame_*.asm`),
`plus3dos.asm`. Front-end en `src/cydc/cydc/` (`cydc_lexer/parser/codegen.py`),
orquestación de build en `cydc.py` + `cyd.py` (`get_asm_*`/`do_asm_*` por target).

Recién cerrado y **pusheado**: rutinas nativas IMPORT/CALL/ASM en **los 5 targets**
(el strict mld48 copia la rutina de flash a RAM residente vía ARR_POOL/ARR_INIT — igual
que los arrays escribibles). Ver `doc/dev/MLD48_NATIVE_ROUTINES.md`, `EXTERN_DESIGN.md`,
`INLINE_ASM_DESIGN.md`. Librerías `math16_32`/`strings` en `lib/`.

## Lo que pide Sergio para esta sesión

1. **Targets nuevos de almacenamiento: ESXDOS y BetaDisk (TR-DOS).**
   - ESXDOS: API por `RST $08` + nº de llamada (F_OPEN/F_READ/F_WRITE/F_CLOSE, etc.),
     estándar de facto en divMMC/divIDE/esxDOS. Necesita DOS residente; el binario carga
     típicamente vía `.tap`/dot-command o carga BASIC + `RANDOMIZE USR`.
   - BetaDisk / TR-DOS: interfaz Beta 128 (Technology Research), TR-DOS en ROM paginada;
     acceso por llamadas a la ROM TR-DOS (`#3D13`) o programación directa del WD1793.
   - Decidir la **estrategia de arranque** de cada uno (cómo llega el intérprete + datos a
     memoria), y cómo mapear `LOAD_CHUNK`/savegame a sus APIs de fichero.

2. **Evaluar si conviene migrar el parser de PLY a Lark** (Sergio lo preguntó
   explícitamente). Es una decisión de ARQUITECTURA: **no migrar sin acuerdo**. Pesar:
   madurez PLY vs Lark, coste de reescribir la gramática LALR y el codegen acoplado,
   mensajes de error, mantenimiento, y [[feedback-minimize-external-tooling]] (Lark es una
   dep nueva). Entregar recomendación razonada, NO empezar la migración.

## ANTES de proponer o tocar nada — revisión OBLIGATORIA del framework

Sergio insistió: *"sé concienzudo para que revises el framework en la siguiente sesión y no
me vuelva a encontrar problemas como los que nos pasó"*. Concretamente, leer y mapear:

- **`MULTITARGET_DESIGN.md`** (raíz) — decisiones de multiplataforma ya tomadas
  (CPC/MSX/Next aparcados; ver qué principios aplican a targets de disco Spectrum).
- **`ARCHITECTURE.md`** (herramienta) y **`MANUAL_es.md`/`MANUAL_en.md`** (lenguaje).
- **La capa de almacenamiento como CONTRATO**: leer `cyd_tape.asm`, `cyd_plus3.asm`,
  `cyd_mld.asm` y sus loaders + `savegame_*.asm` para extraer la interfaz EXACTA que un
  target nuevo debe implementar (símbolos, ABI de `LOAD_CHUNK`, cómo se cuenta el tamaño
  del intérprete en el `block_list`, cómo se colocan chunks/bancos). El `plus3` es el
  espejo más cercano (disco real, `plus3dos.asm`).
- **El pipeline de build en `cyd.py`/`cydc.py`**: cada target tiene `get_asm_<t>`,
  `get_asm_<t>_size`, `do_asm_<t>`. Entender el **size-pass** (stubs) vs pasada final, el
  `bank0_offset`, y el `block_list` del loader — ahí vivieron los bugs del mld48
  (fórmula de pool sin el intro-screen; loader leyendo de menos bytes al no contar la
  tabla de despacho). Un target nuevo replica ese patrón: **si el size-pass y la pasada
  final no coinciden byte a byte, el loader desalinea y cuelga**.

## Lecciones de la tanda mld48 (NO repetir)

- **Correr la SUITE COMPLETA (`python tests/run_tests.py`), no tests sueltos.** Los bugs
  del mld48 pasaban aislados y fallaban en la suite (mocks, caché global, orden de tests).
- **Verificar en EMULADOR** (`tests/emu_harness.py`, ZEsarUX headless + ZRCP) antes de
  afirmar que algo funciona. Compilar ≠ funciona. Añadir un `test_*_runtime` por target.
- **Nada de caché global** que persista entre builds/tests (rompió mocks de compresión).
- **pyZX7/pyZX0 son O(n²)**: comprimir una pantalla de carga ~48 s. No recomprimir N veces.
- **Los símbolos hay que importarlos** (`sys` no estaba importado en `cyd.py`).
- **Fórmulas de layout: derivarlas del código real, no de memoria**, y protegerlas con un
  assert de invariante que falle el build si se desalinean.

## Restricciones permanentes (memoria)

- Commits SIN firma de Claude (autor Cronomantic; nada de Co-Authored-By ni "Generated
  with"). Ver [[feedback-no-claude-signature]].
- **No cambiar semántica documentada del lenguaje sin consultar a Sergio.**
- **Minimizar tooling externo**: Python puro/vendorizado; sin binarios nativos ni deps
  nuevas salvo acuerdo (relevante para la decisión Lark).
- Todo cambio de lenguaje toca **4 superficies**: resaltador (SUBMÓDULO
  `external/chooseyourdestiny-highlighter`) + manual ES/EN + tutorial + wiki (SUBMÓDULO,
  commit aparte). Ver [[feedback-language-change-surfaces]].
- No pararse a medias ni preguntar "¿sigo?": ejecutar el plan entero; parar solo ante
  decisión de arquitectura o bloqueo real. Ver [[feedback-dont-stop-midtask]].
- Anotar hallazgos/decisiones/estado en memoria proactivamente al cambiar de conversación.

## Entregable de la sesión

1. Un **documento de diseño** (`doc/dev/ESXDOS_BETADISK_DESIGN.md`) con: modelo de arranque
   por target, mapeo de la capa de almacenamiento a cada API, riesgos de layout/build, y
   plan por fases (empezar por el más simple — probablemente ESXDOS sobre TAP-loader
   existente reutilizado). **Cerrar con Sergio las decisiones de arranque ANTES de
   implementar.**
2. Recomendación PLY vs Lark (sección aparte o doc propio), con veredicto claro.
3. Solo tras el visto bueno: implementación por fases, cada una verificada en emulador y
   con la suite completa en verde.
