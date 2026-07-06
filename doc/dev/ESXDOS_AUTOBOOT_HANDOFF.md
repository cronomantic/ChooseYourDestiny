# Prompt de continuación — ESXDOS autoarranque (AUTOBOOT.BAS) y cierre para distribuible

> Sergio: Sergio Chico (cronomantic), español, ZX Spectrum + Python a fondo.
> Verificación EMPÍRICA en emulador OBLIGATORIA. Suite completa
> (`python tests/run_tests.py`). Commits autor Cronomantic, SIN firma de Claude.

## Estado (commiteado, verificado)

Target **ESXDOS** (divMMC/SD, RST $08) ya funcional y verificado en ZEsarUX:
- F1 arranque `.TAP`+`.DAT`; F2a streaming imagen; F2b streaming música Vortex;
  savegame por fichero; errores de disco documentados en manual; `ISDISK()` cierto en
  disco (plus3+esxdos); `-scr` (loading screen). Commits: `69f2b39`, `fb69810`,
  `537a4aa`, `ba360a7`. Suite 421/0/0. **`dist/` SIN tocar.**
- Diseño: `doc/dev/ESXDOS_BETADISK_DESIGN.md`. Memoria: `project_esxdos_betadisk_design`.

## Tarea: autoarranque opcional (flag `-autoboot`)

Hoy el juego se lanza desde el navegador NMI de ESXDOS. Muchos usuarios reclaman
autoarranque. Mecanismo elegido: **A1 — `AUTOBOOT.BAS` nativo de ESXDOS 0.8.7+**
(A2/utoboot descartado: `AUTOEXEC.BIN` a $8000 choca con el intérprete y la ROM no
queda inicializada). Ver §5.3 y §9 del diseño.

### Formato (investigado)
- **`AUTOBOOT.BAS`** = cabecera **+3DOS de 128 bytes** (`PLUS3DOS`\x1A ... tipo 0 =
  programa, param1 = línea de autostart 10, param2 = offset de variables = longitud
  del programa) **+ el programa BASIC tokenizado del loader** (el MISMO que hoy genera
  `loaderesxdos.asm` vía `SAVETAP BASIC`, pero sin la cabecera de cinta). Reusar la
  lógica de cabecera +3DOS de `src/cydc/cydc/plus3fs.py`.
- Va en **`/SYS/AUTOBOOT.BAS`** de la SD. Se activa con **`AutoBoot=1`** en
  `/SYS/CONFIG/ESXDOS.CFG` (0=off, 1=cold boot, 2=warm, 3=always).
- El programa BASIC ya hace `CLEAR` + `RANDOMIZE USR START_LOADER`; el loader (RST $08)
  lee el `.DAT` a bancos y salta a $8000. Idéntico a lo ya verificado; lo nuevo es solo
  que ESXDOS lo auto-carga.
- Cómo generarlo desde CYD: SAVEBIN del área BASIC del loader (START_ADDRESS..
  SIZEOFBASIC) a un binario, y en Python prepender la cabecera +3DOS. El flag
  `-autoboot` produce además `ESXDOS.CFG` (o el fragmento) y, idealmente, una carpeta
  lista para copiar a la SD (`/SYS/AUTOBOOT.BAS`, `/SYS/CONFIG/ESXDOS.CFG`, `.DAT`,
  medios).

### VERIFICACIÓN — ROM 0.8.9 disponible (esxdos089.zip en la raíz del repo)
`esxdos089.zip` contiene la distribución ESXDOS 0.8.9:
- **`ESXMMC.BIN`** (8 KB) = ROM firmware del **divMMC** (para ZEsarUX `--divmmc-rom`).
  `ESXIDE.BIN` = versión divIDE.
- **`SYS/`**: `ESXDOS.SYS`, `BETADISK.SYS`, `NMI.SYS`, `CONFIG/ESXDOS.CFG`,
  `CONFIG/TRDOS.CFG`. (Estos van en `/SYS/` de la SD; la versión de `ESXDOS.SYS` debe
  casar con la ROM.)

**Harness de verificación (parcialmente PROBADO):**
- ZEsarUX **NO formatea** una `.mmc` en blanco: hay que darle una imagen FAT16 ya
  formateada. **`mkfat16.py` (abajo) funciona** — ZEsarUX acepta el FAT16 (16 MB,
  512 B/sector, 4 sec/cluster).
- `--copy-file-to-mmc <src> <dest>` escribe ficheros en la imagen (sync ANTES de
  arrancar el emu; un `terminate()` a los ~6 s basta). **VERIFICADO**: copiar a RAÍZ
  crea la entrada de directorio correcta (root dir en sector 65 = 0x8200; datos desde
  cluster 2 = 0xC200). p.ej. copiar `ESXDOS.SYS` a `ESXDOS.SYS` → entrada
  `ESXDOS  SYS`, cluster 2, size 4090. ✔
- **OBSTÁCULO (pendiente):** `--copy-file-to-mmc` **NO crea subdirectorios**. Copiar a
  `SYS/ESXDOS.SYS` deja el root vacío. ESXDOS necesita `/SYS/...`. **Siguiente paso:**
  (a) pre-crear en `mkfat16.py` los directorios `SYS/` y `SYS/CONFIG/` (entrada attr
  0x10 + cluster con `.`/`..`), y PROBAR si `--copy-file-to-mmc SYS/x` escribe dentro
  del subdir existente; si NO, (b) construir el FS FAT16 completo en Python (escribir
  todos los ficheros + subdirs directamente, sin depender de `--copy-file-to-mmc`).
- **Arranque a probar:** `zesarux --noconfigfile --machine 128k --vo null --ao null
  --enable-remoteprotocol --remoteprotocol-port N --enable-divmmc --divmmc-rom
  <.../ESXMMC.BIN> --enable-mmc --mmc-file <img.mmc>`. Con `AutoBoot=1` y
  `/SYS/AUTOBOOT.BAS` presentes, ESXDOS debe auto-cargarlo → el juego arranca. Leer
  `FLAGS` por ZRCP (como los demás tests) para confirmar (p.ej. programa DATA →
  `[11,22,33,44,55,1,44,0]`). Handler NO sirve para esto (necesita el arranque en frío
  de la ROM real, por eso la `.mmc`+ROM).

### `mkfat16.py` (formateador FAT16 que funciona — reconstruir en scratchpad/tests)
```python
import struct, sys
def mkfat16(path, size_mb=16):
    SEC=512; spc=4
    total=(size_mb*1024*1024)//SEC; reserved=1; nfats=2; rootent=512
    rootsec=(rootent*32+SEC-1)//SEC; fatsz=32
    for _ in range(8):
        data=total-reserved-nfats*fatsz-rootsec; clus=data//spc
        need=((clus+2)*2+SEC-1)//SEC
        if need==fatsz: break
        fatsz=need
    assert 4085<=clus<=65524
    bs=bytearray(SEC); bs[0:3]=bytes([0xEB,0x3C,0x90]); bs[3:11]=b"MSDOS5.0"
    struct.pack_into("<H",bs,11,SEC); bs[13]=spc; struct.pack_into("<H",bs,14,reserved)
    bs[16]=nfats; struct.pack_into("<H",bs,17,rootent)
    if total<0x10000: struct.pack_into("<H",bs,19,total)
    else: struct.pack_into("<I",bs,32,total)
    bs[21]=0xF8; struct.pack_into("<H",bs,22,fatsz)
    struct.pack_into("<H",bs,24,63); struct.pack_into("<H",bs,26,255)
    bs[36]=0x80; bs[38]=0x29; struct.pack_into("<I",bs,39,0x12345678)
    bs[43:54]=b"ESXDOS     "; bs[54:62]=b"FAT16   "; bs[510]=0x55; bs[511]=0xAA
    with open(path,"wb") as f:
        f.write(bs)
        for _ in range(nfats):
            fat=bytearray(SEC*fatsz); fat[0:4]=bytes([0xF8,0xFF,0xFF,0xFF]); f.write(fat)
        f.write(bytes(SEC*rootsec)); f.write(bytes(SEC*data))
```
Layout resultante (16 MB): boot=sec0; FAT1=1..32; FAT2=33..64; root=65..96 (0x8200);
data=97+ (0xC200, cluster 2).

## Restricciones y cierre
- Cambio de lenguaje → 4 superficies (resaltador submódulo + manual ES/EN + tutorial +
  wiki submódulo). El flag `-autoboot` NO es keyword del lenguaje (es opción del
  compilador) → documentar en manual (sección de opciones/modelos), no en resaltador.
- Cuando ESXDOS esté completo (autoarranque incluido) y distribuible: **regenerar
  `dist/`** (`make_dist.py`; los 6 `.asm` nuevos ya están en su lista) y añadir `esxdos`
  a la sección de modelos del manual (EXPERIMENTAL). Solo entonces tocar `dist/`.
- Después: **BetaDisk/TR-DOS** (diferido; ver §6/§9 del diseño). El zip 0.8.9 incluye
  `SYS/CONFIG/TRDOS.CFG` y `.trd` tooling (`MKTRD`, `SCL2TRD`) por si sirve.
