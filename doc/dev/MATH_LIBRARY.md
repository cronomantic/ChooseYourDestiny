# Librería de matemática ancha en CYD (16 y 32 bits)

> **Estado: COMPLETA y verificada en emulador.** Ambos tiers (16 y 32 bits) más
> la multiplicación ensanchada `mul16→32` están probados automáticamente en
> ZEsarUX vía el harness ([EMULATOR_TESTING.md](EMULATOR_TESTING.md)). Empaquetada
> como fichero `INCLUDE`-able con ejemplo:
> [`examples/math_library/math16_32.cyd`](../../examples/math_library/math16_32.cyd)
> + [`examples/math_library/test.cyd`](../../examples/math_library/test.cyd).

## Objetivo y decisiones

Dar aritmética de **16 bits (0..65.535)** y **32 bits (0..4.294.967.295)** a los
autores **sin tocar la máquina virtual** — una librería de subrutinas CYD
(`GOSUB`-ables) que se distribuye e incluye con la directiva `INCLUDE`. Recupera
multiplicación/división (que en 8 bits no tenían sentido por desbordar) y
contadores/puntuaciones grandes.

- **Dos tiers desde un generador paramétrico por anchura.** El de 16 bits es
  ~2–4× más rápido y usa la mitad de memoria; para lo cotidiano (oro, vidas,
  puntos, posiciones). El de 32 bits, para acumuladores y productos grandes.
- **`mul16→32` (ensanchada).** La `mul` de 8 bits se descartó por desbordar a
  255; `mul16→16` tiene la misma enfermedad a 65.535. La forma útil es
  `C(32) = A(16) × B(16)`, que **nunca desborda** (65535² < 2³²). Es la
  multiplicación recomendada para puntuaciones.
- **Modelo de registros fijos** (estilo CPU): un bloque de variables reservadas
  (224..254) es el *workspace*; el autor carga sus valores y opera. Coste de
  memoria fijo; el que no la use no paga. Las ops de 16 bits usan los 2 bytes
  bajos de A/B/C, dejando los altos libres para el ensanchado.
- **Sin deps externas, VM intacta.** Todo sobre las primitivas existentes.
- **Auto-guarda:** la librería empieza con `GOTO mlSkip` y termina en
  `LABEL mlSkip`, así que se incluye al principio del programa sin que el flujo
  caiga dentro de las rutinas (solo se ejecutan por `GOSUB`).

Mapa de registros (little-endian, byte bajo primero):
`A`=mlA0..mlA3 (236..239), `B`=mlB0..mlB3 (240..243), `C`=mlC0..mlC3 (244..247);
scratch `mlCy`(248) `mlTmp`(249) `mlKar`(250) `mlCnt`(251) `mlNt`(252) `mlCmp`(253)
`mlDec`(254); print `mlNdig`(234) `mlDptr`(235) y buffer de dígitos 224..233.

## El reto: aritmética SATURADA, no con acarreo

`OP_ADD`/`OP_SUB` **saturan** (`interpreter.asm:337-351`): al desbordar dan 255,
al pedir prestado dan 0 — el carry Z80 se descarta. Los shifts **enmascaran** (el
bit que sale se pierde). Por eso el acarreo se detecta **antes** de operar.
Verificado en modelo Python (40.000 casos, 0 fallos) y en emulador.

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
SET cy TO @c1             /* acarreo saliente */
```

Piezas derivadas del mismo mecanismo:
- **`sub` = suma en complemento a dos**: `A − B = A + (~B) + 1`. El `~B` por byte
  es `255 − B_byte` (resta saturada segura) y el `+1` es `cy=1` inicial → reusa el
  bloque `add-byte`. Además el **carry final = NOT(borrow)**, que da la comparación.
- **`shl`/`shr`**: por byte, propagando el bit que sale/entra por `cy`.
- **`mul`** (shift-and-add): `C += A` si el bit bajo de B es 1; `A<<=1`; `B>>=1`.
- **`div`** (restauradora): shift de 64 bits `C:A` a la izquierda, comparar `C`
  contra `B`, restar y poner el bit del cociente si `C ≥ B`. Al terminar,
  `A`=cociente, `C`=resto.
- **`print`**: extrae dígitos con `div ÷ 10` (cada resto es un dígito 0..9), y los
  imprime en orden inverso desde el buffer.

## API pública

| Rutina | Efecto |
|---|---|
| `add16` / `add32` | `A = A + B` (envuelve mód 2¹⁶ / 2³²) |
| `sub16` / `sub32` | `A = A - B` (envuelve; usa `cmp` para comprobar antes) |
| `cmp16` / `cmp32` | `mlCmp = 0/1/2` → `A<B` / `A=B` / `A>B` |
| `shl16` / `shl32` | `A = A << 1` |
| `shr16` / `shr32` | `A = A >> 1` |
| `mul32` | `C = A * B` (trunca a 32 bits) |
| `mul1632` | `C(32) = A(16) * B(16)` — nunca desborda |
| `div32` | `A = A / B` (cociente), `C = A mod B` (resto). `mod32` = leer `C` |
| `print16` / `print32` | imprime `A` en decimal (destruye `A`; usa `B` y `C`) |

Cargar literales anchos (los literales CYD son de 8 bits) con asignación múltiple:
`SET mlA0 TO {226, 4}` (= 1250 = 0x04E2, byte bajo primero).
Para dividir entre un valor de 16 bits, ponlo en `B` con `B2=B3=0` y usa `div32`.

## Verificación (emulador)

Casos comprobados en ZEsarUX vía el harness (todos PASS):
- **32-bit**: `1e9+1e9`; `1e9−999999999`; `70000×60000=4.200.000.000`;
  `4.2e9/60000=70000 r0`; `1000/7=142 r6`; `cmp` <,=,>; `shl/shr 0x11223344`;
  `print32 1234567 → 1234567`.
- **16-bit**: `40000+20000`; `50000−20000`; `5−7` (envuelve a 65534);
  `cmp` <,=,>; `shl/shr 0x1234`; `print16 54321 → 54321`.
- **widening**: `mul1632 50000×50000=2.500.000.000`; `1000×1000=1.000.000`.
- **end-to-end**: el ejemplo (`INCLUDE` + `mul1632` + `add32` + `print32`) compila
  y produce `1.234.567`.

Cómo re-verificar: agrupar casos en un programa, guardar cada resultado en
variables bajas, `run_cyd(...)` y comparar contra la aritmética de Python. Un caso
por sesión de emulador es caro (~10 s) → agrupar casos. Respeta la VM intacta y
sin deps ([reference-emulator-harness], [feedback-minimize-external-tooling]).

## Notas de velocidad

`mul32`/`div32` son ~32 iteraciones de bytecode interpretado con sumas multibyte;
bien para cálculos ocasionales (una puntuación), lento en bucles apretados. El
tier de 16 bits (`mul16`/ops de 2 bytes) es ~2–4× más rápido. Documentarlo al
usuario para que elija el tier adecuado.

## Posibles ampliaciones (no imprescindibles)

- Helpers de conveniencia: `load32`/`store32` (array del autor ↔ registros con un
  puntero), `set16`/`set32` desde variables del autor, `neg`/signo si algún día se
  quiere aritmética con signo.
- `printn` con ancho fijo / relleno de ceros para marcadores alineados.
