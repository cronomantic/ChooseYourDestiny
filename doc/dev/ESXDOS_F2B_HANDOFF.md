# Prompt de continuación — ESXDOS F2b (streaming de música) y cierre del target

> Pega esto como primer mensaje de la próxima sesión. Sergio: Sergio Chico
> (cronomantic), trabaja en español, ZX Spectrum + Python a nivel profundo.
> Verificación EMPÍRICA en emulador OBLIGATORIA (ZEsarUX headless + ZRCP); NADA se da
> por bueno por leer código. Correr la SUITE COMPLETA (`python tests/run_tests.py`), no
> tests sueltos. Commits: autor Cronomantic, SIN firma de Claude.

## Contexto: qué hay hecho (NO rehacer)

Se está añadiendo el target de almacenamiento **ESXDOS** (divMMC/SD, API `RST $08`) al
compilador CYD, como espejo de `plus3` pero con esa API y arranque desde SD. Diseño
completo en `doc/dev/ESXDOS_BETADISK_DESIGN.md`. Memoria: `project_esxdos_betadisk_design`.

**HECHO + VERIFICADO en emulador (commit de ayer):**
- **F1 (bring-up):** `model=esxdos` arranca desde `.TAP` (loader BASIC) → `RANDOMIZE USR`
  → `RST $08` (F_OPEN/F_READ del `.DAT`) → bancos residentes → intérprete en $8000.
  Ficheros: `esxdos.asm` (wrappers RST $08 con DI/EI), `loaderesxdos.asm`,
  `cyd_esxdos.asm` (copia de cyd_tape con SAVEBIN @DAT_PATH + DISK_ERROR),
  `savegame_esxdos.asm` (por fichero). Verificado: programa DATA → MATCH.
- **F2a (streaming de IMAGEN):** `screen_manager_esxdos.asm` (IMG_LOAD por RST $08 de
  `NNN.CSC` → `PIC_BUFFER` en la mitad ALTA ($E000) del banco de staging IMG_BANK=6 →
  ZX0 a SCREEN_BUFFER → mirror; restaura SCRIPT_BANK). `cydc.py`:
  `spectrum_banks=[0,1,3,4,7,6]` (banco 6 al final, capado a 8KB en el allocator; mitad
  baja $C000-$DFFF allocable), SCR excluidos de residencia, `.csc` copiados sueltos al
  output. Verificado: PICTURE 0 + DISPLAY 1 → 6144/6144 bytes de píxel en pantalla.
- Suite completa en verde (con `test_esxdos` en test_data/sugar/sugar3_runtime.py).

**Gotchas durables (ya verificados):** `DISPLAY 0` es NOP (usar `DISPLAY 1`); los EQU
`ESX_*` van SOLO en esxdos.asm (el loader los referencia); NO reutilizar savegame_tape
($0562/$04C2 = traps divMMC); la ISR NO ataca la ROM; DI alrededor de toda llamada RST
$08; fórmulas de layout heredadas de do_asm_128/plus3 cuadran byte a byte.

## Tarea de esta sesión: F2b — streaming de MÚSICA

**Guía explícita de Sergio (decidida):**
- **Vortex Tracker (PT3):** se carga de disco al **RESTO del banco de staging (banco 6,
  `$C000-$DFFF`, 8 KB)**, compartiendo el banco con `PIC_BUFFER` ($E000). Es el modelo
  de `plus3` (`MDLADDR=$C000`, `VORTEX_BANK=6`). **Con música Vortex presente, el banco
  6 queda reservado ENTERO** (pista en $C000 + staging imagen en $E000) → sale de la
  allocación de contenido.
- **WyzTracker:** reserva su **propio banco (el 1)**, como ya hace hoy. Tenerlo en
  cuenta al planificar bancos.

**Plan (verificar cada paso en emulador + suite):**
1. **`music_manager_esxdos.asm`** (hermano de `music_manager.asm` de plus3): `LOAD_MUSIC`
   por `RST $08` — F_OPEN "NNN.BIN", F_READ cabecera (2B) + cuerpo a `$C000` (banco 6),
   F_CLOSE, `VTR_INIT`. Poner `MDLADDR`/`VORTEX_BANK` (que en cyd_esxdos, heredado de
   cyd_tape, son VARIABLES) a `$C000`/`6` en runtime → así la ISR de cyd_esxdos
   (`ld a,(VORTEX_BANK)`) funciona SIN rebasar cyd_esxdos sobre cyd_plus3. Restaurar
   SCRIPT_BANK al salir. WYZ_CALL igual que en music_manager.asm.
2. **`get_asm_esxdos`** (cyd.py): usar `music_manager_esxdos` en vez de
   `music_manager_tape` cuando `has_tracks`.
3. **`cydc.py` allocator:** cuando hay música **Vortex** (has_tracks and not wyz), quitar
   el banco 6 de la allocación de contenido (o size 0) — queda reservado para
   pista+staging. Sin Vortex, el banco 6 mantiene su mitad baja (8KB) allocable (F2a).
   TRK excluidos de `place_blocks` cuando se streamean (como SCR). El límite de pista
   8KB (`len(b) > 8*1024`, hoy solo plus3, línea ~700) extender a esxdos.
4. **Empaquetado:** copiar los `.BIN` de música sueltos al output (SD root), como los
   `.csc` de F2a. Ojo: en plus3 las pistas llevan `add_size_header` a `.BIN`; ver cómo
   se nombran para que `music_manager_esxdos` las abra ("NNN.BIN").
5. **WyzTracker:** verificar que el banco 1 reservado no colisiona con `[0,1,3,4,7,6]`
   (quitar el 1 de content cuando wyz, como ya hace 128k → `[0,3,4,7,6]`... ya está).
6. **Test en emulador:** compilar un `.cyd` con `-trk` (una pista PT3 de prueba) +
   `TRACK`/`PLAY`, verificar que arranca y suena (o al menos que VTR_STAT/registros AY
   cambian). Añadir un test permanente si es viable.

## Después de F2b (para dejar ESXDOS distribuible)

- **Autoarranque opcional** (flag): emitir `/SYS/AUTOBOOT.BAS` (nativo ESXDOS 0.8.6+) o
  utoboot. Ver §5.3 del diseño. Sub-decisión A1 vs A2 abierta.
- **`-scr` (loading screen):** hoy `do_asm_esxdos` la IGNORA (F1). Cablearla.
- **Test permanente de imagen/música** en el harness (hoy la verificación de imagen es
  ad-hoc; el harness `compile_cyd` no pasa `-img`/`-trk`). Valorar extenderlo.
- **Solo cuando ESXDOS esté completo y distribuible: regenerar `dist/`** (`make_dist.py`;
  los 4+1 `.asm` nuevos ya están en su lista) — Sergio pidió NO tocar dist hasta
  entonces. Luego actualizar el manual (sección de modelos) con `esxdos` (EXPERIMENTAL).

## Luego: BetaDisk / TR-DOS (diferido)

Ver §6/§9 del diseño. Decisiones abiertas: modelo de máquina (Pentagon 128?), carga por
nombre (#3D13 fn #0A/#0E) vs track/sector, escritor `.TRD` en Python. NO empezar hasta
cerrar ESXDOS.

## Verificación (recordatorio)

Harness: `tests/emu_harness.py` — `MACHINE_BY_MODEL["esxdos"]="128k"`; `run_in_zesarux`
con `--enable-divmmc --enable-esxdos-handler --esxdos-root-dir <dir>`. ZEsarUX 13.0 en
`tools/`. Para imagen/música hace falta test ad-hoc (ver los del scratchpad de ayer:
`test_img_esxdos.py`). Suite completa antes de dar por bueno.
