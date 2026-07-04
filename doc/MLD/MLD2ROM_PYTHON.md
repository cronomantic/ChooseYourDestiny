# mld2rom en Python puro (dan_romgen) — nota técnica

Fecha: 4 jul 2026. Registra la reescritura de `mld2rom.py` para generar una ROM
Dandanator Mini completa y **arrancable** en Python puro, byte a byte idéntica a
la herramienta oficial.

## El problema que resolvió

`mld2rom.py` (versión vieja) partía del firmware de 3584 B y lo **pad-eaba con
ceros** hasta 512 KB. Eso dejaba **vacía toda la "menu zone" del slot 0**: la
tabla CBlocks, los bloques comprimidos (charset+PIC-fw, textos, pantalla) y el
`slot1.rom`. El firmware arrancaba, mostraba a medias el menú y **colgaba con
artefactos**. Verificado por Sergio en EsPectrum: fallaban IGUAL una ROM CYD y una
ROM comercial (Shadow of the Unicorn) empaquetadas así ⇒ **no era bug de CYD ni
del loader MLD**, sino de la ROM incompleta. (El juego CYD arranca perfecto: la
ROM correcta SÍ funciona en EsPectrum.)

## La solución

`dan_romgen.py` (raíz del repo) es un **port puro-Python** del ensamblado de la
herramienta oficial [grelobites/dandanator-mini](https://github.com/cronomantic/dandanator-mini)
v10.4.3 (`DandanatorMiniV9RomSetHandler.exportRomSet`). `mld2rom.py` lo invoca.

- **Compresión**: `pyZX7` (ya vendorizado en CYD, `src/cydc/cydc/pyZX7`). Su ZX7
  óptima da **bytes idénticos** a la Zx7 de Java → la ROM sale byte a byte igual.
- **Sin dependencias externas / sin Java en runtime.** La jar Java se usó SOLO
  como oráculo temporal de validación (`cmp`); no forma parte de nada.

## Layout del slot 0 (16 KB) que ensambla dan_romgen

| Offset | Contenido |
|---|---|
| 0 | baserom (firmware, 3584 B) |
| 3584 | game count (1 B) |
| 3585 | game-structs (131 B × 25 juegos; resto a cero) |
| 6860 (GREY_ZONE) | bloques comprimidos ZX7: pantalla, textos, pokes, charset-extendido+"DNTRMFW-Up"+PIC-fw |
| … | game chunks (256 B/juego; **vacío para MLD**) |
| … | EEPROM loader (pantalla + código, comprimidos) |
| 16352 | version info ("v10.4.3", 8 B null-term) |
| 16360 | **tabla CBlocks** (5 pares word: punteros/len a los bloques + locs eeprom) |
| 16380/1/2/3 | flags: border, **autoboot**, dansnap-type (0xFF), pause (2 para MLD) |
| slot 1 | `slot1.rom` (300 B) + relleno 0xFF |
| … | datos de juegos (en orden INVERSO: game[0] en slots altos) |
| slot 31 | extra ROM |

Detalles por tipo (validados byte a byte): hw-mode {0x83→0, 0x88→4}; símbolo del
nombre {0x83→130 (48K), 0x88→128 (128K)}; pause=2. Footer MLD: `reallocate`
parchea `MLDoffset`=slot; `allocateSaveSpace` escribe los sector-IDs con un
**contador global decreciente** en orden inverso de juego. Textos del menú =
locale **es**.

## Recursos vendorizados (`external/dandanator-mini/`)

`baserom.bin`, `extcharset.bin` (896 B = charset.rom 768 + 12 glifos de símbolo
de 8 B en offset (code-32)*8), `pic-fw.bin`, `slot1.bin`, `menu.scr` (fondo),
`eeprom-screen.scr`, `eeprom-loader.bin`, `extra.rom`. Copiados/derivados del repo
oficial. `dan_romgen` los localiza junto a sí mismo (override: `CYD_DANDANATOR_RES`).

## Uso y validación

```bash
python mld2rom.py -o juego.rom [-a] juego.MLD        # -a = autoboot; sin --base-rom
```

Regresión automática (sin Java ni EsPectrum): `tests/test_dan_romgen.py` compara
el sha256 de la ROM generada contra hashes de referencia (fixtures en
`tests/fixtures/`). **Cero validación manual.**

Para regenerar los hashes o revalidar contra el oráculo: compilar un `.cyd` a
`.MLD`, generar la referencia con la jar oficial
(`java -jar tools/dandanator-mini-10.4.3.jar --cli -o ref.rom juego.MLD`; en JDK
sin JavaFX bundleado, añadir los módulos openjfx) y `cmp` contra la salida de
`mld2rom.py`. (La jar es un oráculo temporal; no se distribuye.)

## Pendiente

- Añadir el paso MLD→ROM a la GUI (`make_adventure_gui.py`) y a `make_adventure.py`.
- Limpieza de `mld2rom.py`: código muerto (`find_start_slot`, `build_game_struct`,
  constantes sin uso; `read_existing_uncompressed_slots` la usa un test).
- `mld2rom.py`/`dan_romgen.py`/recursos ya añadidos a `make_dist.py` → rehacer `dist/`.
