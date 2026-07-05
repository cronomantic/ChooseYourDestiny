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

### ABIERTO — cómo se determina el ancho (SIN decidir)

Sergio: los marcadores `WORD`/`DWORD` **por sí solos no convencen**; el ancho **también
podría autodetectarse**. Opciones sobre la mesa:

- **(a) Autodetección por magnitud.** `1000` → 2 bytes, `100000` → 4 bytes. Cómodo y sin
  keywords. **Riesgo:** en `LET @v = 200` gastaría 1 slot y `LET @v = 300` gastaría 2 →
  el nº de variables consumidas cambia con el valor (sorpresa). Aceptable en `DATA`/`DIM`
  (ves el valor) pero delicado en `LET`.
- **(b) Marcador explícito** `WORD n` / `DWORD n` (la cadena `"…"` se autodescribe).
  Predecible (el autor sabe cuántos slots reserva) pero verboso, sobre todo por-elemento
  en listas.
- **(c) Híbrido (candidato preferente a documentar):** autodetección por magnitud por
  defecto **+** marcador explícito para **forzar un ancho mayor** que el mínimo (p. ej.
  `WORD 5` = 2 bytes aunque 5 quepa en 1). Da comodidad y, cuando importa, predecibilidad.

Decisión pendiente para cuando se pase a implementar. Sintaxis del marcador si se usa:
keyword `WORD`/`DWORD` (al reservado + reglas) o sufijo de lexer (`1000w`/`100000d`, sin
keywords nuevas) — también sin decidir.

---

## 3. Azúcares de control y conveniencia (puro compilador, 0 runtime)

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

Baja a: `LET @i = a` → `LABEL ini` → cuerpo → `@i += s` → comparación → `IF cond GOTO
ini`. Como **`s` es constante de compilación**, el compilador sabe la dirección y emite
la comparación correcta: `s > 0` → continúa mientras `@i <= b`; `s < 0` → mientras
`@i >= b`. `NEXT` (o `NEXT @i`) cierra el `FOR` más interno; el compilador lleva la pila
de anidamiento. **Gotcha a documentar:** contador de byte (0-255) → `FOR @i = 0 TO 255
STEP 1` desborda al incrementar (255→0) y no termina; es responsabilidad del autor
(igual que en BASIC de 8 bits).

### 3.2 `SELECT @v … CASE … [CASE ELSE …] ENDSELECT` — multi-rama

Hoy son cadenas de `IF/ELSEIF`. Muy legible para menús/estados.

```cyd
[[ SELECT @estado
     CASE 0          GOSUB intro
     CASE 1, 2, 3    GOSUB juego     /* varios valores por rama */
     CASE ELSE       GOSUB fin       /* por defecto (opcional) */
   ENDSELECT ]]
```

Baja a: evaluar `@v` una vez y una cadena de comparaciones `IF @v == k GOTO cuerpo_k`
(con `CASE k1,k2` = varias comparaciones a la misma rama), `CASE ELSE` = salto al
default. **Sin fall-through** (semántica BASIC): cada cuerpo salta a `ENDSELECT` al
acabar. v1 = cadena `IF`; si los `CASE` son densos y numéricos, una **tabla de saltos**
es optimización futura (seguiría siendo front-end, reusando `GOTO`).

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
  la repetición necesita **sintaxis propia** no aritmética. Candidatos (sin decidir):
  `{ 16 OF 0 }`, `{ 0 REPEAT 16 }`. A elegir al implementar.

### 3.5 `SWAP @a, @b` — intercambio sin temporal

Intercambia dos variables **reusando la pila de bytes de la VM**, sin variable temporal
ni runtime nuevo: `PUSH @a : PUSH @b : POP @a : POP @b` (los opcodes de pila ya existen;
el azúcar los emite en codegen). Pure front-end.

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
