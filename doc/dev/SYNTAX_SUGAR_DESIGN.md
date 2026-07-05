# Azúcar sintáctico de CYD — propuesta de diseño (VALORADA, NO implementada)

> **Estado:** propuesta cerrada en la *valoración* con Sergio (jul 2026), **sin
> implementar**. Recoge la forma acordada de dos features y el backlog de otras.
> Guía de decisión antes de construir. Ver también `MANUAL_es.md` (§Arrays,
> §Variables), `doc/dev/MLD_WRITABLE_ARRAYS.md` (por qué lo inmutable es "gratis" en
> MLD) y `EXTERN_DESIGN.md`/`INLINE_ASM_DESIGN.md` (mecanismos de runtime/extirpación).

## Principios (decididos con Sergio)

1. **El esfuerzo va al compilador y a la documentación, no al runtime Z80.** La VM es
   lo más caro de tocar (rendimiento y RAM escasa). No se añade más código de runtime
   que el estrictamente necesario.
2. **Todo lo que no se usa, no ocupa.** CYD ya envuelve cada opcode en `IFNDEF
   UNUSED_OP_x` y el compilador (`get_unused_opcodes`) extirpa del binario los opcodes
   que el programa no usa. Cualquier pieza nueva de runtime hereda esto: coste 0 para
   los programas que no la usan.
3. **CYD es orientado a bytes** (variables = bytes de `FLAGS`, pila de la VM = bytes).
   El **autor gestiona el layout de bytes**; el azúcar no introduce tipos anchos en la
   VM, solo los *baja a bytes* en compilación.

---

## 1. Datos inmutables — `DATA` / `READ` / `RESTORE` / `DATAEND()`  ✅ IMPLEMENTADO

> **Estado: implementado y verificado en 48k (emulador).** Single-chunk ≤16 KB,
> recurso `TYPE_DATA=4` cargado por `LOAD_DATA_CHUNK` uniforme, cursor `DATA_PTR` de
> 16 bits. `DATAEND` es una **función**: se escribe `DATAEND()`.

Análogo al `DATA` de BASIC. **Es el reverso de los arrays escribibles**: al no
modificarse nunca, el dato **puede quedarse en el slot flash del Dandanator** y leerse
en sitio → **coste 0 de RAM en MLD** (ni `ARR_INIT` ni bancos dedicados, al revés que
`DIM`). En 128k/+3 se lee de su chunk banqueado; en 48k residente.

### Sintaxis y semántica

```cyd
[[
  DATA 10, 20, 30          /* constantes de byte, se concatenan en un flujo global */
  DATA 40, 50              /* en orden de aparición en el fuente */

  RESTORE                  /* rebobina el cursor global al principio */
  RESTORE etiqueta         /* rebobina al primer DATA que aparezca tras 'etiqueta'
                              (semántica BASIC "RESTORE línea"; reutiliza LABEL) */
  WHILE (DATAEND() = 0)    /* DATAEND() = función booleana 0/1: cursor al final o no */
    READ v                 /* lee el siguiente byte al destino y avanza el cursor */
    READ [v]               /* destino indirecto (índice en v), como LET [v] */
    PRINT @v
  WEND
]]
```

- **Un único flujo global** y **un único cursor** (como BASIC). Los `DATA` se recogen
  en orden de fuente.
- `READ <destino>` usa destino **pelado** como `SET`/`LET`: `READ v` (directo) y
  `READ [v]` (indirecto). **NO `READ @v`** — sería incoherente, porque `@` es para *leer*
  valores, no para nombrar el destino de escritura (decisión de Sergio).
- **Cinta sin fin**: leer más allá del final rebobina el cursor a 0 (no es error).
  `OP_READ` normaliza el cursor antes de leer (`if DATA_PTR >= DATA_LEN: DATA_PTR = 0`).
- `DATAEND` es una **condición booleana** (no un terminador de bloque — de ahí el
  nombre `DATAEND` y no `ENDDATA`, para no chocar con la familia `END`/`ENDASM`). Al
  haber un solo cursor global, no lleva argumento. Sustituye a un hipotético
  `DATACOUNT`, que devolvería un número de 16 bits **no manejable de forma nativa** por
  el lenguaje de bytes.

### Almacenamiento

- El compilador junta **todos** los `DATA` en **un bloque de solo lectura** y lo coloca
  como un chunk más (tipo nuevo `TYPE_DATA` en el índice / `FIND_IN_INDEX`):
  - **MLD/mld128 → slot flash (0 RAM)**, **128k/+3 → banco**, **48k → residente**.
- **v1: un solo chunk ≤ 16 KB**, cursor de **16 bits** → hasta ~16384 elementos (muy
  por encima de los 256 de `DIM`). Si supera 16 KB → error de compilación.
- **v2 (futuro): spanning multi-chunk** (cursor `(chunk, offset)`). Se deja fuera de v1
  **a propósito**: es justo lo que mantiene `OP_READ` sin lógica de cruce de chunks
  (principio 1 — runtime mínimo).

### Runtime (mínimo y opt-in)

Es la **única** parte de todo este paquete que toca la VM. No hay forma de hacer un
flujo secuencial de >256 con cursor persistente reutilizando opcodes existentes (el de
array lee por índice de byte a la pila, sin cursor). Coste:

- **Programas sin `DATA` → 0 bytes** (opcodes extirpados por el mecanismo `UNUSED_*`).
- Con `DATA`: `OP_READ` compacto (reutiliza el idiom `LOAD_CHUNK` + salvar/restaurar
  chunk de los opcodes de array), `OP_RESTORE`/`OP_RESTORE_LABEL` diminutos, `DATAEND`
  (un par de comparaciones del cursor contra la longitud), y un estado `DATA_PTR`
  (16-bit) en `vars.asm`. Del orden de unas pocas decenas de bytes, y solo si se usa.

---

## 2. Constantes anchas — 16/32-bit y cadenas bajadas a bytes (100% front-end)

Una constante de **16/32-bit o cadena** válida **allí donde hoy va un byte**, que el
compilador expande a una secuencia **fija** de bytes consecutivos **little-endian**
(casa con el Z80 y con el layout de registros de la librería `math16_32`). **0 bytes de
runtime**: la VM ni se entera.

Tres contextos, una sola regla:

```cyd
[[
  DATA WORD 1000, 5, "HI"        /* 2 bytes + 1 byte + 2 bytes de glifos */
  DIM t() = { DWORD 100000, 42 } /* 4 bytes + 1 byte */
  LET @score = WORD 1000         /* FLAGS[score]=low, FLAGS[score+1]=high */
  LET @buf   = "HI"              /* FLAGS[buf]=cod('H'), FLAGS[buf+1]=cod('I') */
]]
```

- **En `DATA`/`DIM`**: quedan como **byte-plano**; el autor lee byte a byte y recompone
  (con `math16_32` si opera). **Sin opcodes anchos, sin acceso ancho a arrays**
  (decisión de Sergio: los arrays de 16/32-bit NO precisan acceso a ese tamaño; es
  responsabilidad del autor copiarlos a variables, igual que con `DATA`).
- **En `LET @var`**: se expande a N `SET`/`LET` de byte a índices **consecutivos**
  conocidos en compilación. Al quedar little-endian y alineados, **alimentan directo a
  la math lib**.
- **Solo destino directo.** `LET @@var = …` (indirección, índice en runtime) **no** — no
  se puede conocer el índice siguiente en compilación.
- **Cadenas:** bytes de glifo (sin comprimir, para lectura predecible), **sin
  terminador por defecto** (el autor conoce la longitud porque la escribió). Un
  prefijo de longitud / centinela sería del subsistema de strings (futuro), no de esto.

### Cómo se determina el ancho (DECIDIDO — jul 2026)

**Híbrido con marcador por keyword** (decisión de Sergio):

- **Por defecto: autodetección por magnitud.** `1000` → 2 bytes, `100000` → 4 bytes,
  `5` → 1 byte. Cómodo y sin keywords para el caso común.
- **Marcador `WORD n` / `DWORD n` para FORZAR un ancho mayor** que el mínimo: `WORD 5`
  = 2 bytes aunque 5 quepa en 1; `DWORD 5` = 4 bytes. `WORD`/`DWORD` son **keywords
  nuevas** (reservadas en el lexer + reglas de gramática + resaltador). No pueden forzar
  un ancho *menor* que el que exige la magnitud (`WORD 100000` = error).
- La cadena `"…"` se autodescribe (nº de glifos), no necesita marcador.

**Cuidado con `LET @v` en autodetección:** el nº de slots consumidos depende del valor
(`LET @v = 200` = 1 slot, `LET @v = 300` = 2 slots). Cuando el autor quiere un nº de
slots **estable** (p. ej. reservar siempre 2 bytes para un contador), usa el marcador
explícito: `LET @v = WORD 200`. Documentar este gotcha.

---

## 3. Azúcares de control y conveniencia (puro compilador, 0 runtime)  ✅ IMPLEMENTADO

> **Estado: implementado y verificado en runtime en los 5 targets (jul 2026).** `FOR`
> (§3.1), `SELECT/CASE/ENDSELECT` (§3.2), `ENUM` (§3.3, admite miembros multilínea),
> literales `'A'`/`{a..b}`/`{v REPEAT n}` (§3.4) y `SWAP a,b` con indirecto/mixto
> `SWAP [a],[b]` (§3.5). `SELECT @v` admite `varexpression` (sujeto re-evaluado por CASE,
> como el límite del FOR). Nota `REPEAT`: es SOLO el operador de repetición de listas; el
> bucle es `DO … UNTIL` (el manual antiguo lo llamaba "REPEAT…UNTIL" pero eso nunca
> compiló — corregido a `DO…UNTIL`, decisión de Sergio jul 2026).

Todas **bajan a construcciones que CYD ya tiene** (asignaciones, comparaciones,
`IF/GOTO`, `CONST`, la pila de bytes de la VM) con **etiquetas generadas por el
compilador**. Ninguna añade opcodes. CYD ya trae `IF/ELSE/ELSEIF/ENDIF`, `WHILE/WEND`,
`DO/UNTIL/LOOP`, `CONST`, `DECLARE … AS` (mapea **nombre→índice**, sin tipo), `++/--`,
operadores lógicos/bit; estas rellenan los huecos.

### 3.1 `FOR @i = a TO b [STEP s] … NEXT` — bucle contado

Falta el bucle contado (hoy solo `WHILE`/`DO`). Es el de más ergonomía.

```cyd
[[ FOR @i = 0 TO 9          /* STEP 1 implícito */
     PRINT @i
   NEXT
   FOR @j = 10 TO 0 STEP -2 /* cuenta atrás */
     PRINT @j
   NEXT ]]
```

Baja (contador **pelado**, coherente con `SET`/`LET`; en el cuerpo se lee `@i`) a:
`LET i = a` → guarda-cero superior → `LABEL cuerpo` → cuerpo → guardas de
actualización → `GOTO cuerpo`. Como **`s` es constante de compilación**, el compilador
sabe la dirección. **Semántica BASIC**: la guarda superior permite **0 iteraciones** si
el inicio ya pasó el límite; el cuerpo corre para `a, a±|s|, …` hasta pasar `b`.

**Contador de byte + aritmética que satura.** En CYD `ADD` clampa a 255 y `SUB` clampa a
0 (ver `OP_ADD`/`OP_SUB`), no hacen wrap. Un `while i<=b`/`i>=b` ingenuo se quedaría
**atascado** en el borde del byte (`255+1` vuelve a 255, `0-1` vuelve a 0) y NO
terminaría para los idioms comunes `FOR i = N TO 0 STEP -1` y `FOR i = 0 TO 255 STEP 1`.
Para evitarlo, la actualización se protege contra una **constante de compilación ANTES**
de que pueda saturar: al subir para si `i > 255-|s|` (el siguiente `+` clamparía) o si
`i+|s|` pasa `b`; al bajar para si `i < |s|` (el siguiente `-` clamparía) o si `i-|s|`
pasa `b`. Así `TO 0` y `TO 255` son correctos con **0 runtime nuevo** (solo un par de
comparaciones/saltos de más por iteración). `NEXT` (o `NEXT i`) cierra el `FOR` más
interno. Límite re-evaluado cada iteración (sin variable oculta), refleja cambios en vivo.

### 3.2 `SELECT @v … CASE … [CASE ELSE …] ENDSELECT` — multi-rama

Hoy son cadenas de `IF/ELSEIF`. Muy legible para menús/estados.

```cyd
[[ SELECT @estado
     CASE 0          GOSUB intro
     CASE 1, 2, 3    GOSUB juego     /* varios valores por rama */
     CASE ELSE       GOSUB fin       /* por defecto (opcional) */
   ENDSELECT ]]
```

Baja a: evaluar el sujeto una vez y una cadena de comparaciones `IF sujeto == k GOTO
cuerpo_k` (con `CASE k1,k2` = varias comparaciones a la misma rama), `CASE ELSE` = salto
al default. **Sin fall-through** (semántica BASIC): cada cuerpo salta a `ENDSELECT` al
acabar. v1 = cadena `IF`; si los `CASE` son densos y numéricos, una **tabla de saltos**
es optimización futura (seguiría siendo front-end, reusando `GOTO`).

**DECIDIDO — sintaxis del sujeto (Sergio, jul 2026):** SELECT admite una
**`varexpression`** (`SELECT @v`, `SELECT @a+1`), así que el **`@` se mantiene**, coherente
con los demás contextos de lectura (`PRINT @v`/`INK @v`). Es un contexto de LECTURA (se
evalúa el sujeto), a diferencia de SWAP (§3.5), que son destinos y va pelado.

### 3.3 `ENUM [nombre] { A, B, C }` — constantes secuenciales

Quita constantes mágicas; baja a `CONST`.

```cyd
[[ ENUM { NORTE, SUR, ESTE, OESTE }      /* 0,1,2,3 */
   ENUM Item { ESPADA=1, ESCUDO, POCION=10, LLAVE } ]] /* 1,2,10,11 */
```

Auto-incremento desde 0 (o desde el último valor explícito, estilo C). Los nombres se
declaran como **constantes globales** (`CONST NORTE=0 …`); el `nombre` opcional es solo
agrupación/legibilidad (CYD no tiene notación de punto). Colisión de nombres = mismo
error que redeclarar una `CONST`.

### 3.4 Conveniencias de literales (en `{ }`, `DATA`, y expresiones donde encaje)

- **Literal de carácter `'A'`** → el **código de glifo** de `A` (vía el charset). Usable
  donde vaya una constante de byte (`DATA`, `DIM`, `LET`, expresiones). Muy cómodo para
  datos de texto sin memorizar códigos.
- **Rangos `{1..8}`** → `1,2,3,4,5,6,7,8` (y descendente `{8..1}`).
- **Repetición** → N copias de un valor. **Ojo:** dentro de `{}` las expresiones
  constantes ya se evalúan, así que `{0 * 16}` daría **un** `0` (0·16=0), no 16 ceros →
  la repetición necesita **sintaxis propia** no aritmética. **DECIDIDO (jul 2026):
  `{ valor REPEAT n }`** (`{ 0 REPEAT 16 }` = dieciséis ceros). `REPEAT` es keyword
  contextual; `n` es constante de compilación. Combina con anchos y rangos dentro de la
  misma lista `{ …, 255 REPEAT 4, 1..3, … }`.

### 3.5 `SWAP a, b` — intercambio sin temporal

Intercambia dos variables **reusando la pila de bytes de la VM**, sin variable temporal
ni runtime nuevo. **Operandos PELADOS** (`SWAP a, b`, NO `@a, @b`): son **destinos** que
se escriben, igual que en `SET`/`LET`/`READ`/`FOR`; el `@` (valor-de) no tiene sentido
sobre un l-value (no se pueden intercambiar r-values). Baja a `PUSH a : PUSH b : POP a :
POP b` (el codegen lee/escribe cada variable). Pure front-end. (Decisión con Sergio,
jul 2026: sin `@` porque solo admite variables.)

---

## Impuesto por cada azúcar (no es gratis fuera del compilador)

Gramática **LALR** (riesgo de conflictos — sobre todo `SELECT/CASE`, `FOR/NEXT` con
`TO/STEP` ya reservados por `SET … TO`), **manual ES/EN**, el **resaltador** (repo
`chooseyourdestiny-highlighter`: keyword + snippets + VSIX + bump de submódulo) y
**tests** (codegen + emulador para lo que toque runtime). Priorizar por valor/coste.

## Orden de implementación sugerido

Por **coste de runtime** primero, luego por valor:

1. **Runtime 0 — se pueden hacer en cualquier orden:** constantes anchas (§2), y las
   azúcares de control/conveniencia (§3: `FOR`, `SELECT/CASE`, `ENUM`, literales,
   `SWAP`). Decidir antes el punto ABIERTO del ancho (§2) y la sintaxis de repetición
   (§3.4). Verificación: tests de codegen (comparar el bytecode expandido con el
   equivalente escrito a mano) — no hace falta emulador porque no cambia la VM.
2. **`DATA`/`READ`/`RESTORE`/`DATAEND` (§1)**: su propio bloque, con la porción mínima de
   VM y **verificación en emulador** (harness `tests/emu_harness.py` + probe MLD para
   confirmar el coste 0 de RAM en flash).

Recomendación de valor dentro de (1): `FOR` y las constantes anchas primero (encajan con
lo que ya diseñamos y con la math lib), luego `SELECT/CASE`, `ENUM`, literales y `SWAP`.
