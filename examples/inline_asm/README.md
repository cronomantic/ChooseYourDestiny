# `examples/inline_asm` — Ensamblador inline (`ASM … ENDASM`)

Ejemplo curado del **ensamblador inline**: escribir rutinas Z80 nativas
directamente en el guion `.cyd` y llamarlas desde CYD. Reúne en un solo programa
las piezas de la funcionalidad, y sirve como **test general** de la misma.

> ⚠️ **Avanzado, bajo tu responsabilidad.** Es código nativo tuyo, sin red de
> seguridad. Si no te manejas con ensamblador Z80, no necesitas esto. Consulta la
> sección "Rutinas nativas (IMPORT / CALL)" del manual.

## Qué demuestra

- **`ASM nombre … ENDASM`**: el cuerpo Z80 se escribe en el propio `.cyd` (no hace
  falta un fichero aparte como con `IMPORT`).
- **`EXPORTS a, b`**: un bloque (`arraylib`) con dos entradas (`suma_stats`,
  `mayor_stat`) que comparten el patrón de recorrer un array.
- **Broker de arrays**: las rutinas alcanzan el array `stats` del guion por nombre
  (`ARR_stats`, `ARR_stats_LEN`, `ARR_stats_BANK`) y lo recorren con
  `CYD_ARR_MAP` (en 128K/+3 el array puede vivir en un banco paginado; el servicio
  residente lo copia a un buffer directo, y en 48K es acceso directo).
- **`USES` + `CYD_CALL`**: la rutina `resumen` llama a `suma_stats` y `mayor_stat`,
  que están en **otro bloque** (y en 128K/+3 pueden estar en otro banco), mediante
  el trampolín residente `CYD_CALL` y los índices `RT_<nombre>` que inyecta `USES`.
- **Eliminación de código muerto**: el guion solo hace `CALL resumen`; `arraylib`
  se conserva únicamente por el cierre transitivo de `USES`. Una rutina que nadie
  alcanzara se descartaría sola, sin ocupar memoria.

El programa suma las 4 estadísticas (`12+7+15+9 = 43`), calcula la mayor (`15`) y
la resta (`43-15 = 28`), y muestra los tres valores. Funciona en **48K, 128K y +3**.

## Compilar

El ejemplo es un proyecto (`test.cyd`, 48K en su `cyd_project.ini`) y se compila
donde está, desde la carpeta de CYD:

```
make_adv.cmd examples\inline_asm        (Windows; o arrastra la carpeta sobre make_adv.cmd)
./make_adv.sh examples/inline_asm       (Linux, macOS)
```

o con *Abrir…* en la GUI. Lo compilado queda en `examples/inline_asm/OUTPUT/`.
Para los otros targets, añade `128k` o `plus3` tras la carpeta
(`make_adv.cmd examples\inline_asm 128k`).

## Por qué existe esta funcionalidad

El ensamblador inline es lo que ha permitido **reescribir en Z80 nativo las
librerías del proyecto** (el núcleo de `math16_32` y de `strings` ya es un bloque
`ASM` nativo) para ganar velocidad en los bucles calientes, manteniendo una
interfaz cómoda (multi-export, acceso a variables y arrays, llamadas entre
rutinas). Este ejemplo muestra esas piezas por separado.
