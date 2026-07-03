# Librería de matemática ancha en CYD (32 bits) — núcleo probado

> **Estado (3 jul 2026): núcleo PROBADO en emulador, pendiente de completar y
> empaquetar.** `add32` y `mul32` (incl. overflow) verificados automáticamente en
> ZEsarUX vía el harness ([EMULATOR_TESTING.md](EMULATOR_TESTING.md)). Falta
> `div32`/`mod32`, helpers (`load32`/`store32`/`cmp32`/`print32`/`inc32`),
> empaquetado como fichero `INCLUDE`-able y un ejemplo + manual.

## Objetivo y decisiones

Dar aritmética de **32 bits (0..4.294.967.295)** a los autores **sin tocar la
máquina virtual** — una librería de subrutinas CYD (`GOSUB`-ables) que se
distribuye e incluye con `INCLUDE`. Recupera multiplicación/división (que en 8
bits no tenían sentido por desbordar) y contadores/puntuaciones grandes.

- **Modelo de registros fijos** (estilo CPU): un bloque de variables reservadas es
  el *workspace* de cómputo; el autor guarda sus valores largos en sus propios
  arrays y los carga a los registros para operar. Coste de memoria fijo y
  predecible; el que no la use no paga.
- **Sin deps externas, VM intacta.** Todo sobre las primitivas existentes.

Layout del PoC (a revisar al empaquetar): little-endian, 4 bytes por valor.
`P`(producto/acumulador)=236..239, `M`(multiplicando)=240..243,
`Q`(multiplicador)=244..247; scratch `cy`=248, `tmp`=249, `c1`=250, `cnt`=251.

## El reto: aritmética SATURADA, no con acarreo

`OP_ADD`/`OP_SUB` **saturan** (`interpreter.asm:337-351`): al desbordar dan 255,
al pedir prestado dan 0 — el carry Z80 se descarta. Los shifts (`OP_SHIFT_L/R`,
`sla`/`srl`) **enmascaran** (el bit que sale se pierde). Por eso el acarreo se
detecta **antes** de operar. Verificado en modelo Python (add y mul, 40.000 casos
aleatorios + bordes, 0 fallos) y luego en emulador.

**Suma de un byte con acarreo (el truco central):**
```
LET tmp = 255
LET tmp -= @src            /* tmp = 255 - src  (resta saturada, segura) */
IF @dst > @tmp THEN        /* dst + src > 255  -> hay acarreo */
 LET dst = @dst - @tmp     /* (dst+src) mod 256 = dst - (255-src) - 1 */
 LET dst -= 1
 SET c1 TO 1
ELSE
 LET dst += @src           /* exacto (no desborda) */
 SET c1 TO 0
ENDIF
IF @cy = 1 THEN            /* sumar el acarreo entrante */
 IF @dst = 255 THEN
  SET dst TO 0
  SET c1 TO 1
 ELSE
  LET dst += 1
 ENDIF
ENDIF
SET cy TO @c1             /* acarreo saliente (c1 y c2 nunca son 1 a la vez) */
```

## Rutinas probadas (verificadas en emulador)

`add32` — `P += M` (repite el bloque anterior para los 4 bytes, `cy=0` al inicio):
```
LABEL add32
SET cy TO 0
<add-byte 236,240>  <add-byte 237,241>  <add-byte 238,242>  <add-byte 239,243>
RETURN
```

`shl32` (M <<= 1) — por byte, de bajo a alto; acarreo = bit 7:
```
/* por cada byte b de M, bajo->alto: */
SET c1 TO 0
IF @b >= 128 THEN SET c1 TO 1 ENDIF   /* carry out */
LET b = @b << 1
LET b = @b | @cy                       /* mete el carry-in en bit 0 */
SET cy TO @c1
```

`shr32` (Q >>= 1) — por byte, de alto a bajo; acarreo = bit 0:
```
/* por cada byte b de Q, alto->bajo: */
SET c1 TO 0
IF (@b & 1) = 1 THEN SET c1 TO 1 ENDIF
LET b = @b >> 1
IF @cy = 1 THEN LET b = @b | 128 ENDIF
SET cy TO @c1
```

`mul32` (P = M × Q, shift-and-add, 32 iteraciones):
```
LABEL mul32
SET 236 TO 0 : SET 237 TO 0 : SET 238 TO 0 : SET 239 TO 0
SET cnt TO 0
WHILE (@cnt < 32)
 IF (@244 & 1) = 1 THEN GOSUB add32 ENDIF   /* bit 0 de Q */
 GOSUB shlM                                  /* M <<= 1 */
 GOSUB shrQ                                  /* Q >>= 1 */
 LET cnt += 1
WEND
RETURN
```

Casos verificados en ZEsarUX: `300×3=900`, `65000×1000=65.000.000`,
`70000×60000=4.200.000.000`, `100000×100000=1.410.065.408` (overflow mod 2^32). Todos PASS.

## Pendiente para librería usable

- **`div32`/`mod32`**: división restauradora (shift-and-subtract). La resta de un
  byte con préstamo es el espejo del add-byte (saturación → detectar préstamo con
  `IF @dst < @src` y reconstruir). Verificar en emulador con `1000/7`, etc.
- **Helpers**: `load32`/`store32` (array del autor ↔ registros), `cmp32` (devuelve
  <,=,> en una variable), `inc32`, y **`print32`** (imprimir en decimal — necesita
  dividir por 10 repetidamente usando `div32`).
- **Literales de 32 bits**: los literales CYD son de 8 bits; para cargar `1000` hay
  que hacerlo byte a byte o con un helper `set32 b3,b2,b1,b0`.
- **Empaquetado**: fichero `INCLUDE`-able (p.ej. `dist/.../lib/math32.cyd`), bloque
  de registros documentado, sección de manual y un `examples/` que lo use.
- **Velocidad**: `mul32` son ~32 iteraciones de bytecode interpretado con sumas
  multi-byte; bien para uso ocasional (calcular una puntuación), lento en bucles
  apretados. Documentar.

## Cómo verificar (imprescindible)

Usar el harness ([EMULATOR_TESTING.md](EMULATOR_TESTING.md)): generar un `.cyd` con
todos los casos (guardando cada resultado en variables bajas 0..15), `run_cyd(...)`,
y comparar contra la aritmética real de Python. Un caso por sesión de emulador es
caro (~10 s) → agrupar casos en un solo programa.
