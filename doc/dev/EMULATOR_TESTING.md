# Verificación automática en emulador (headless)

Herramienta para **verificar el comportamiento en tiempo de ejecución** de un
programa CYD sin que nadie lo cargue a mano en un emulador. Compila un `.cyd`, lo
ejecuta en **ZEsarUX sin ventana** y lee de vuelta el array de variables `FLAGS`
del motor por el **protocolo remoto ZRCP**.

> **Por qué existe.** Los cambios de runtime sin verificar son lo que dejó pasar
> en silencio los bugs del soporte Dandanator (yo tocaba algo y había que probarlo
> a mano). Este harness cierra ese ciclo: cualquier cosa que corra en el Spectrum
> se puede **aseverar automáticamente**.

## Requisitos

- `tools/sjasmplus(.exe)`
- Una build `tools/ZEsarUX_*/zesarux(.exe)` (se coge la de versión más alta).

Si falta alguno, el harness lo señala y los tests que lo usan **se saltan**
(`@unittest.skipUnless(emulator_available(), ...)`), igual que `test_e2e_build`.

## Cómo funciona

1. **Compila** el `.cyd` a TAP con `cydc -v` (el `-v` conserva el listado
   `cyd.lst`, del que se extrae la dirección de `FLAGS`).
2. **Lanza ZEsarUX headless**: `--vo null --ao null` (sin vídeo ni audio) +
   `--enable-remoteprotocol` (ZRCP en el puerto TCP 10000).
3. **`smartload`** del TAP; espera a que la ROM 48k arranque y el intérprete
   ejecute (hace *polling* de `PC` y de `FLAGS` hasta que `PC ≥ $8000` y las
   variables quedan estables).
4. **Lee** `FLAGS` con `read-memory` y devuelve los bytes.

La dirección de `FLAGS` se saca del `.lst` (cambia con el tamaño del intérprete,
así que se parsea en cada compilación). Alternativa robusta: poner un marcador
(p.ej. `DE AD BE EF`) en las primeras variables y escanear la RAM.

## Uso

```python
from emu_harness import run_cyd, emulator_available

flags = run_cyd(SOURCE, model="48k", n_bytes=16)   # bytes de FLAGS[0..15]
assert flags[4] == 42
```

**Patrón recomendado:** el arranque del emulador cuesta ~5-6 s, así que mete
**todos los casos de una prueba en UN solo programa**, guardando cada resultado en
una variable distinta, ejecútalo una vez y léelos todos juntos. No arranques el
emulador por caso.

### Verificar los 5 targets

`run_cyd(source, model=...)` **maneja los 5 targets** y elige solo la máquina de
ZEsarUX y el método de arranque (`MACHINE_BY_MODEL`). Verificado: DATA da el mismo
resultado en todos.

| CYD `model` | salida     | máquina ZEsarUX | arranque                 |
|-------------|------------|-----------------|--------------------------|
| `48k`       | `test.tap` | `48k`           | `smartload` (cinta)      |
| `128k`      | `test.tap` | `128k`          | `smartload` (cinta)      |
| `plus3`     | `test.DSK` | `p3`            | `smartload` (disco)      |
| `mld`       | `test.rom` | `48k`           | Dandanator (ver abajo)   |
| `mld128`    | `test.rom` | `128k`          | Dandanator (ver abajo)   |

```python
from emu_harness import run_cyd
for model in ("48k", "128k", "plus3", "mld", "mld128"):
    flags = run_cyd(SOURCE, model=model, n_bytes=16)
    assert flags[0] == ...
```

(API de bajo nivel si necesitas control: `compile_cyd` / `build_mld_rom` para generar la
imagen, y `run_in_zesarux(img, flags_addr, machine=..., dandanator_rom=...)` para
ejecutarla. `smartload` carga TAP o DSK indistintamente.)

### Verificar mld / mld128 (Dandanator) en ZEsarUX

`run_cyd(source, model="mld")` (o `"mld128"`) ya hace todo esto por dentro. Lo que
sigue es **qué hace y los flags que costó descubrir** (por si necesitas depurar o
usar la ruta a mano). Es totalmente automatizable, sin hardware. El flujo es
`.cyd → .MLD → .rom (512 KB) → ZEsarUX con Dandanator`:

1. **Compilar** a `.MLD`: `cydc.py -v mld  t.cyd <sjasmplus> .`  (o `mld128`). Produce
   `t.MLD` y `cyd.lst` (de donde sale la dirección de `FLAGS`, igual que en cinta).
2. **Empaquetar** a ROM con el conversor **Python puro** del repo (el firmware+menú
   Dandanator ya está vendorizado en `external/dandanator-mini/`, **no** hace falta base ROM):

   ```bash
   python mld2rom.py -o t.rom -a t.MLD      # -a = autoboot; t.rom debe medir 524288 B
   ```
3. **Arrancar en ZEsarUX** headless con emulación Dandanator y leer `FLAGS` por ZRCP. Los
   flags correctos (la doc antigua los tenía mal) son:

   ```text
   --machine 48k            # mld strict 48K   (mld128 -> --machine 128k)
   --enable-dandanator
   --dandanator-rom t.rom
   --dandanator-press-button   # IMPRESCINDIBLE: sin él ZEsarUX se queda en el menú/ROM
   --vo null --ao null --enable-remoteprotocol --remoteprotocol-port 10000
   ```

**El gotcha que costó**: `--dandanator-press-button` es **obligatorio** para disparar el
autoboot; sin él el PC se queda en la ROM (~`$11xx`/`$38`) y `FLAGS` sale todo ceros.
Con él, el intérprete arranca (PC ≥ `$8000`) y se lee `FLAGS` como en cualquier target.
Verificado: DATA da el mismo `[11,22,33,44,55,1,44,0]` en `mld` y `mld128` que en cinta.
Receta manual completa (con capturas, save/load) en
[tests/MANUAL_DANDANATOR_SMOKE.md](../../tests/MANUAL_DANDANATOR_SMOKE.md).

### Cómo escribir el programa `.cyd` de prueba (gotchas reales)

- **Termina siempre con un bucle infinito** `LABEL spin` / `GOTO spin`. Si el
  programa acaba con `END` (implícito o explícito), vuelve a BASIC, `PC` baja de
  `$8000` y el harness lee **ceros** (espera `PC ≥ $8000` estable). No es un bug del
  código: es que ya no está corriendo.
- **`FLAGS[n]` es la variable número `n`.** Las variables por número son índices
  directos en `FLAGS` (no hace falta `DECLARE` para usar `SET 5 TO ...` o `READ 5`).
  Escribe tus resultados en variables 0..15 y léelas con `n_bytes=16`.
- **Para leer el valor de una variable en una expresión usa `@v`**, no `v` a secas
  (el nombre pelado es *destino*/etiqueta): `WHILE (@i < 10)`, `SET 5 TO @v`.
- **Palabras reservadas como nombre de etiqueta**: `loop` es `LOOP` (keyword). Usa
  otro nombre (`spin`, `bucle`, `rd`…) o dará "missing identifier".
- El emulador es lento y el sondeo tiene ventana: usa el bucle `spin` para mantener
  `FLAGS` estable mientras el harness lo lee.

Ejemplo de test (gated): [tests/test_emu_harness.py](../../tests/test_emu_harness.py).
Módulo: [tests/emu_harness.py](../../tests/emu_harness.py).

## API

- `emulator_available()` → `bool`. Úsalo en `@unittest.skipUnless`.
- `run_cyd(source, model="48k", n_bytes=16, max_wait=None)` → `bytes` de
  `FLAGS[0:n_bytes]`. **Maneja los 5 targets** (elige máquina y arranque).
- `MACHINE_BY_MODEL` → dict `model → máquina ZEsarUX`.
- `compile_cyd(source, model, workdir)` → `(tap_o_dsk_path, flags_addr)` (tape/disk).
- `build_mld_rom(source, model, workdir)` → `(rom_path, flags_addr)` (mld/mld128).
- `run_in_zesarux(img, flags_addr, n_bytes, machine=..., dandanator_rom=...)` → `bytes`.
- `find_sjasmplus()` / `find_zesarux()` → ruta o `None`.

## Limitaciones / notas

- `run_cyd` arranca en 48k; **los 5 targets se verifican en runtime**: 48k/128k/+3
  pasando `machine=` a `run_in_zesarux`, y mld/mld128 vía `mld2rom.py` +
  `--enable-dandanator`/`--dandanator-press-button` (ver arriba). Ninguno necesita
  hardware.
- Es lento (~10 s por sesión de emulador) → **no** metas muchas sesiones en la
  suite rápida; agrupa casos y/o resérvalo para verificación puntual.
- Lee `FLAGS` como canal de salida. Para observar otra cosa (pantalla, puertos),
  se puede leer cualquier dirección con `read-memory`.
