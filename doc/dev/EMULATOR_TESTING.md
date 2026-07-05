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

### Verificar en 48k, 128k y +3 (varios targets)

`run_cyd` compila para el `model` que le pases **pero arranca ZEsarUX en 48k**. Para
ejecutar de verdad en 128k o +3 hay que pasar el **nombre de máquina de ZEsarUX** a
`run_in_zesarux` (que `run_cyd` no propaga). Verificado: DATA da el mismo resultado
en los tres.

| CYD `model` | salida       | máquina ZEsarUX (`machine=`) |
|-------------|--------------|------------------------------|
| `48k`       | `test.tap`   | `48k`                        |
| `128k`      | `test.tap`   | `128k`                       |
| `plus3`     | `test.DSK`   | `p3`                         |
| `mld`/`mld128` | `test.MLD` | (Dandanator, sin harness automatizado — solo se comprueba que ensambla) |

```python
from emu_harness import compile_cyd, run_in_zesarux
import tempfile
for model, mach in [("48k", "48k"), ("128k", "128k"), ("plus3", "p3")]:
    with tempfile.TemporaryDirectory() as wd:
        img, flags_addr = compile_cyd(SOURCE, model, wd)   # tap o DSK
        flags = run_in_zesarux(img, flags_addr, n_bytes=16, machine=mach)
        assert flags[0] == ...
```

`smartload` carga tanto TAP como DSK, así que el +3 (disco) funciona con `machine="p3"`.

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
- `run_cyd(source, model="48k", n_bytes=16, max_wait=25.0)` → `bytes` de
  `FLAGS[0:n_bytes]`.
- `compile_cyd(source, model, workdir)` → `(tap_path, flags_addr)`.
- `run_in_zesarux(tap_path, flags_addr, n_bytes, ...)` → `bytes`.
- `find_sjasmplus()` / `find_zesarux()` → ruta o `None`.

## Limitaciones / notas

- `run_cyd` arranca en 48k; **48k, 128k y +3 se verifican** pasando `machine=`
  (`48k`/`128k`/`p3`) a `run_in_zesarux` (ver arriba). `mld`/`mld128` (Dandanator)
  ensamblan pero **no** tienen harness de ejecución automatizado todavía.
- Es lento (~10 s por sesión de emulador) → **no** metas muchas sesiones en la
  suite rápida; agrupa casos y/o resérvalo para verificación puntual.
- Lee `FLAGS` como canal de salida. Para observar otra cosa (pantalla, puertos),
  se puede leer cualquier dirección con `read-memory`.
