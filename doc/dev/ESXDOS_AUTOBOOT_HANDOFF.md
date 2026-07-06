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
- **Subdirectorios: RESUELTO.** `--copy-file-to-mmc` **no CREA** subdirs, pero **SÍ
  escribe dentro de uno pre-existente**. Solución: `mkfat16b.py` pre-crea `SYS/` y
  `SYS/CONFIG/` (entrada attr 0x10 + cluster con `.`/`..`). VERIFICADO: copiar a
  `SYS/ESXDOS.SYS` mete el fichero en el `SYS/` correcto (entrada attr 0x20).
- **MBR/partición: RESUELTO.** `mkfat16c.py` genera imagen con MBR (partición FAT16
  LBA tipo 0x0E en sector 2048). VERIFICADO que **el copiador de ZEsarUX es consciente
  de la partición** (escribe en el `SYS/` DENTRO de la partición, no en superfloppy).
  Ambas (superfloppy `mkfat16b` y MBR `mkfat16c`) son FAT válidas que ZEsarUX escribe.
- **Generación de `AUTOBOOT.BAS`: VALIDADA (formato).** `test_autoboot.py` en scratchpad:
  compila el juego a esxdos, extrae el programa BASIC del `.tap` (bloque 2, quita
  flag+checksum → 204 B para el DATA de prueba, autostart línea 10), y le antepone la
  cabecera **+3DOS de 128 B** (`PLUS3DOS`\x1A, issue1 ver0, len32=128+prog, tipo0,
  datalen=prog, param1=línea 10, param2=prog, checksum=sum(0..126)&0xFF). Reusable en
  cyd.py.
- **DIAGNÓSTICO (jul 2026): ESXDOS 0.8.9 SÍ arranca en ZEsarUX; lo que falla es el
  AutoBoot.** Verificado con trazas de PC/pantalla:
  - **ESXDOS arranca y toma el control con el divMMC.** Comparando pantalla CON vs SIN
    `--enable-divmmc --divmmc-rom ESXMMC.BIN`: DIFIEREN (con divMMC PC pasa por la ROM
    ESXDOS 0x1e58→0xf6, atributos distintos). El divMMC + ROM 0.8.9 funcionan. NO es
    problema de flags de arranque.
  - **El `ESXDOS.CFG` con `AutoBoot=3` está correctamente en `/SYS/CONFIG/ESXDOS.CFG`
    dentro de la partición** (verificado en la imagen: `AutoBoot=3` presente, sin
    `AutoBoot=0` residual, en el cluster del dir CONFIG). Config correcto y en su sitio.
  - **Traza de PC (AutoBoot=3, AUTOBOOT.BAS presente):** t5s=0x1e58 → t6-10s=0xf6 (ROM
    ESXDOS) → t11s+=0x15e1/0x15e6/0x15e8/0x38 = **menú 128 BASIC** (bucle del menú +
    IM1). Es decir, ESXDOS arranca, NO ejecuta AUTOBOOT.BAS, y hand-off al menú 128.
  - **Conclusión:** el bloqueo es el **AutoBoot** (ESXDOS no carga/ejecuta
    `/SYS/AUTOBOOT.BAS` pese a `AutoBoot=3`). Dos hipótesis vivas: **(1) formato de
    `AUTOBOOT.BAS`** — asumí cabecera +3DOS de 128 B, pero quizá ESXDOS `SAVE *"x"`
    escribe otro formato (¿headerless? ¿cabecera propia?); conviene **obtener un .BAS
    real guardado por ESXDOS y comparar bytes**. **(2) 128K** — el menú 128 podría
    interceptar el AutoBoot; probar con máquina **+2A/+3 o 48K**, o ver si el AutoBoot
    exige entrar en 48 BASIC. **Test aislante recomendado:** un `AUTOBOOT.BAS` TRIVIAL
    (p.ej. `10 POKE 16384,255`) con cabecera +3DOS; si el POKE ocurre → formato+AutoBoot
    OK y el fallo está en el loader bajo autoboot; si no → formato/AutoBoot. (Requiere
    tokenizar BASIC a mano con el encoding de números, o extraerlo de un .cyd trivial.)

### Decisión pendiente (para Sergio)
Verificación en emulador del arranque en frío BLOQUEADA. Opciones: (A) seguir
peleando la config de ESXDOS-en-ZEsarUX (conseguir la imagen 0.8.5 de referencia);
(B) implementar el flag `-autoboot` con el formato ya validado (genera
`/SYS/AUTOBOOT.BAS` + `ESXDOS.CFG` con `AutoBoot=1` + carpeta lista para la SD) y
**verificar en HW real** (Sergio tiene divMMC + 0.8.9); el loader en sí ya está
verificado en emulador (F1/F2), lo único sin verificar es que ESXDOS auto-cargue el
`.BAS` (comportamiento estándar de ESXDOS). Recomendación: B (entrega la función; la
única incógnita es comportamiento estándar de ESXDOS, verificable en HW).

### Scripts del harness (en scratchpad, FUNCIONAN): `mkfat16.py`, `mkfat16b.py`
(superfloppy+subdirs), `mkfat16c.py` (MBR+partición), `test_autoboot.py` (genera
AUTOBOOT.BAS + monta .mmc + arranca). El `mkfat16` original está inline abajo; los
otros añaden pre-creación de `SYS/`/`SYS/CONFIG/` y MBR.

### Arranque a probar (comando):
`zesarux --noconfigfile --machine 128k --vo null --ao null --enable-remoteprotocol
--remoteprotocol-port N --enable-divmmc --diviface-ram-size 512 --divmmc-rom
<.../ESXMMC.BIN> --enable-mmc --mmc-file <img.mmc>`. Con `AutoBoot=1`+`/SYS/AUTOBOOT.BAS`
ESXDOS debe auto-cargarlo → el juego arranca; leer `FLAGS` por ZRCP (DATA →
`[11,22,33,44,55,1,44,0]`). El `--enable-esxdos-handler` NO sirve aquí (no hace el
arranque en frío de la ROM real).

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
