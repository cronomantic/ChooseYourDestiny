# Manual smoke test — Dandanator (MLD + ROM)

Receta reproducible para verificar el flujo completo `.cyd → .MLD → .rom → emulador`. Los tests automatizados ([test_mld2rom.py](test_mld2rom.py), [test_mld_footer.py](test_mld_footer.py), [test_mld_index_mapping.py](test_mld_index_mapping.py), [test_mld_rom_emulation.py](test_mld_rom_emulation.py)) cubren la lógica de Python y la generación de ASM, pero no pueden probar que el cartucho resultante arranque en hardware. Este documento cubre esa pieza.

Tiempo estimado: 10-15 min la primera vez (descargar emulador/ROM base si hace falta), 2 min en ejecuciones posteriores.

---

## Requisitos previos

1. **sjasmplus** disponible en `./tools/sjasmplus.exe` (ya viene con el repo si compilaste `external/sjasmplus`).
2. **Python 3.10+** con `progressbar` instalado.
3. **Base ROM de Dandanator Mini**: archivo `dandanator-mini.rom`. Dos opciones:
   - **Firmware-only (3584 B)**: descargar de
     https://github.com/cronomantic/dandanator-mini/blob/master/src/main/resources/dandanator-mini/dandanator-mini.rom
     `mld2rom.py` lo rellena a 512 KB automáticamente.
   - **Full 512 KB**: extraer del JAR oficial o desde una release del proyecto Dandanator Mini.

   Colocar el archivo en `./external/dandanator-mini.rom` (ruta que espera el [Makefile](../Makefile)).
4. **Emulador** con soporte Dandanator. Opciones:
   - **ESPectrum** (incluido en el repo: `EsPectrum.exe` + `Espectrum.ini`). Configurar `MachineType=Dandanator` en el `.ini` o desde el menú interno.
   - **ZEsarUX**: `zesarux --machine 48k --enable-dandanator --dandanator-rom <rom_file> --dandanator-press-button` (para `mld128`, usa `--machine 128k`). El `--dandanator-press-button` es **imprescindible** para disparar el autoboot; sin él ZEsarUX se queda en el menú/ROM. Para verificación automatizada headless añade `--vo null --ao null --enable-remoteprotocol --remoteprotocol-port 10000` y lee `FLAGS` por ZRCP (ver [doc/dev/EMULATOR_TESTING.md](../doc/dev/EMULATOR_TESTING.md)).
   - **FUSE** con plugin Dandanator instalado.

---

## Procedimiento

### Paso 1 — Elegir un ejemplo mínimo y reproducible

Recomendado: [examples/guess_the_number/test.cyd](../examples/guess_the_number/test.cyd) — script pequeño con input numérico, condicionales y branching, y sin recursos pesados.

```powershell
Copy-Item -Recurse examples/guess_the_number/* test_dandanator/
Set-Location test_dandanator
```

### Paso 2 — Compilar a `.MLD` (modo strict 48k)

```powershell
python ../src/cydc/cydc/cydc.py -v -code -T tokens.json mld test.cyd ../tools/sjasmplus.exe .
```

**Verificación intermedia**: archivo `test.MLD` creado, tamaño múltiplo de 16384 bytes. Validar contra la spec:

```powershell
python ../mld2rom.py --validate-only test.MLD
```

Salida esperada: `0 critical, 0 error(s)`. Pueden aparecer INFO/WARNING informativos (p.ej. "Type byte 0x83 -> 48K MLD", "Relocation table fields are all zero").

### Paso 3 — Empaquetar a `.rom`

```powershell
python ../mld2rom.py -o test.rom -a -v test.MLD
```

El firmware + menú Dandanator ya está vendorizado en `external/dandanator-mini/`, así que **no** hace falta pasar una base ROM (`-b`/`--base-rom` ya no existe).

Flags:
- `-a` → autoboot (arranca el juego al encender, sin pasar por el menú Dandanator).
- `-v` → output verbose.

**Verificación intermedia**: `test.rom` tiene **exactamente 524288 bytes**.

```powershell
(Get-Item test.rom).Length    # debe ser 524288
```

### Paso 4 — Cargar en ESPectrum

```powershell
Copy-Item test.rom ../  # ESPectrum espera ROMs en su directorio
Set-Location ..
./EsPectrum.exe
```

En el menú interno de ESPectrum, seleccionar **Machine → Dandanator** y cargar `test.rom`.

### Paso 5 — Verificaciones de smoke

Marcar manualmente:

- [ ] **Boot**: aparece la pantalla del juego sin errores (o el menú Dandanator si no usaste `-a`).
- [ ] **Input**: las teclas responden; números se aceptan en el prompt.
- [ ] **Gameplay**: el flujo del juego progresa correctamente (condicionales, branching).
- [ ] **Save**: invocar un `save` desde dentro del juego (si el script lo permite). No debe colgar.
- [ ] **Load**: reiniciar el emulador con el mismo `.rom`, intentar `load`. Debe restaurar el estado.
- [ ] **Estrés save/load**: 10 ciclos save→load seguidos sin colgar ni corromper.
- [ ] **Sin glitches gráficos** notables en la transición entre pantallas.
- [ ] **Sin sonido roto** (en modo `mld` strict 48k no hay AY pero sí beeper SFX si el script los usa).

### Paso 6 — Versión 128k (opcional, solo si el ejemplo usa música)

Repetir pasos 2-5 con `mld128` en lugar de `mld`. Verifica adicionalmente:

- [ ] **Música AY** suena correctamente (PT3 o WYZ según el script).
- [ ] **Cambios de banco RAM** no producen pops ni cortes en la música.
- [ ] **Arrays escribibles**: si el script modifica un `DIM` (`LET a(i)=x`, `+=`) y
      lee el valor después, el nuevo valor persiste (en mld128 los arrays viven en
      bancos RAM dedicados; en strict mld en un pool residente). Con música presente,
      la escritura del array y la música conviven sin corromperse.

---

## Si algo falla

| Síntoma | Causa probable | Acción |
|---|---|---|
| `make rom` o `mld2rom.py` aborta con `UnicodeEncodeError` | Consola Windows cp1252 sin parche aplicado | Verificar que el commit del fix Unicode está aplicado (busca caracteres `→`, `✗`, `·`, `–` en mld2rom.py — no deben aparecer) |
| `.rom` tiene tamaño distinto de 524288 | Base ROM corrupta o tamaño no esperado | Re-descargar `dandanator-mini.rom` (firmware-only 3584 B o full 512 KB) |
| Cuelgue al iniciar | Posible problema en `loadermld.asm` o `bank_dan.asm` | Anotar slot reproducible, capturar screenshot, abrir issue. Probar con `--no-validate` desactivado para descartar MLD corrupto |
| Save/load corrompe la partida | Posible race en EEPROM (B1 del plan: faltan `di`/`ei`) | Documentar reproductor; es el siguiente fix en el plan |
| Teclado no responde tras un save | Slot mapping no se restaura tras `RESTORE_DAN_ROM` | Anotar y reportar; relacionado con `IS_MLD_DAN` guards en inkey.asm |

---

## Evidencia archivable

Tras un smoke verde, guardar:

- Captura de pantalla del menú Dandanator o juego corriendo en `doc/MLD/smoke_test_evidence/<fecha>/`.
- El `.rom` resultante (524288 B) junto con el `.cyd` fuente y el hash SHA-256 de ambos.
- Versión exacta de ESPectrum / ZEsarUX usada.

Esto sirve de referencia para detectar regresiones futuras sin tener que reconstruir todo el contexto.
