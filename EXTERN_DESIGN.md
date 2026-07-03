# Diseño: rutinas nativas del autor (`IMPORT` / `CALL`, opcode `OP_EXTERN`)

> **Propósito.** Fijar el diseño de la extensibilidad nativa de CYD: permitir que
> un autor escriba una rutina en ensamblador Z80, la registre en su guion y la
> invoque desde él. Es la generalización del patrón que **ya usa el reproductor
> WYZ** (ensamblado aislado a un banco, `ORG` fijo, llamada desde el motor).
>
> Documento de referencia para no re-derivar el entendimiento. Las afirmaciones
> sobre el código actual llevan `fichero:línea` verificados salvo que se indique
> "(a verificar)". Asume [ARCHITECTURE.md](ARCHITECTURE.md).
>
> **Estado: FASE 1 (front-end) IMPLEMENTADA y verificada** (suite completa en verde,
> +2 tests de IMPORT/CALL). Fases 2 (build/allocator), 3 (runtime asm) y 4
> (ejemplo+docs) pendientes. Detalle de lo hecho al final del §8.

---

## 1. Qué resuelve y por qué estaba parado

`OP_EXTERN` existía **diseñado pero nunca cableado**: bloque comentado en
[interpreter.asm:2758-2790](src/cydc/cydc/cyd/interpreter.asm#L2758), sin entrada
en la jump table, sin keyword en el front-end, sin mención en el manual, y con el
handler a medio hacer (el `call` automodificado usa sintaxis de label malformada
`.jump_addr+1:` + `call 0-0`, nunca ensamblado).

Se frenó por dos problemas reales de inyectar código nativo:
1. **Romper el ensamblado**: si el `.asm` del autor se concatena con el motor,
   cualquier error suyo revienta toda la compilación con un mensaje confuso.
2. **Relocalización**: un binario Z80 con direcciones absolutas debe correr en la
   dirección para la que se ensambló; si CYD lo coloca en otro sitio, se rompe.
   Hacerlo portable exigiría código relocatable (PIC), que es inviable de exigir.

**Ambos se disuelven con el patrón del WYZ player** (§2) + **ORG calculado por
CYD** (§5).

---

## 2. Precedente ya existente: el reproductor WYZ

`create_wyz_player_bank` ([cydc_music.py:46-85](src/cydc/cydc/cydc_music.py#L46))
hace exactamente lo que necesita `IMPORT`:
- `wyz_player.asm` declara `ORG $C000` ([wyz_player.asm:2](src/cydc/cydc/cyd/wyz_player.asm#L2)).
- Se ensambla en una **pasada aislada** de sjasmplus (`run_assembler` propio) a un
  `.bin` ([cydc_music.py:79](src/cydc/cydc/cydc_music.py#L79)).
- Comprobación de tamaño en ensamblado: `ASSERT WYZ_LEN < $4000, Player file is too big!`
  ([cydc_music.py:75](src/cydc/cydc/cydc_music.py#L75)).
- El binario se coloca en un banco y el motor lo llama en `$C000` (`WYZ_TRACKER EQU $C000`).

Conclusión: **el ensamblado aislado con `ORG` controlado por CYD ya es un patrón
maduro del proyecto.** `IMPORT` lo generaliza a rutinas arbitrarias del autor.

- El problema (1) desaparece: la rutina se ensambla **aislada**, no concatenada;
  un error del autor da un fallo limpio y atribuible a *su* fichero, sin tocar el
  build del motor. CYD **enmarca** la rutina (pone él el `ORG`, el `SAVEBIN` y el
  `ASSERT`), así que el autor escribe solo el cuerpo.

---

## 3. Superficie de lenguaje

Dos keywords nuevas. El opcode del runtime sigue llamándose `OP_EXTERN`
(nombre interno); el lenguaje no lo expone.

```
IMPORT beeper FROM "rutinas/beeper.asm"   ; declaración (compile-time)
...
CALL beeper                               ; invocación (runtime -> OP_EXTERN)
```

- **`IMPORT nombre FROM "ruta.asm"`** — directiva de declaración (análoga en
  espíritu a `DECLARE`/`CONST`; NO es `INCLUDE`, que incluye fuente `.cyd`).
  Registra una rutina nativa bajo `nombre`. Se resuelve en compilación: CYD
  ensambla el fichero (§5), lo coloca (§6) y asocia `nombre` → (chunk, dirección).
- **`CALL nombre`** — invoca la rutina. Emite `OP_EXTERN` con los operandos
  `[chunk, addr_lo, addr_hi]` de `nombre`. Par mental con lo existente:
  `GOSUB etiqueta` = subrutina del guion (bytecode); `CALL nombre` = rutina Z80 nativa.

Impacto en el front-end (patrón ya existente de añadir opcodes/keywords):
- **Lexer**: tokens `IMPORT`, `FROM`, `CALL`.
- **Parser**: reglas para ambas sentencias; `IMPORT` alimenta una tabla de
  rutinas; `CALL` referencia un `nombre` (validar declarado, como labels/const).
- **Codegen**: nuevo byte de opcode para `OP_EXTERN` (elegir uno libre en el dict
  `opcodes` de [cydc_codegen.py](src/cydc/cydc/cydc_codegen.py)); emisión de los
  3 bytes de operando. El mapa `nombre → (chunk, dirección)` se resuelve tarde
  (tras la asignación de memoria, §6), así que el codegen emite un **placeholder**
  que la fase de layout parchea (como ya se hace con direcciones de labels).

---

## 4. ABI de la rutina nativa

Contrato mínimo, portable y simple:

- **Entrada**: `DE = FLAGS` (puntero base al array de 256 variables del motor).
  La rutina se ejecuta como una llamada (`call`), así que termina con `ret`.
- **E/S vía `FLAGS`**: el guion CYD y la rutina comparten el array de variables.
  El guion pone argumentos en variables (`SET`), hace `CALL`, la rutina lee/escribe
  esas posiciones (`FLAGS+n`), y el guion lee resultados (`@var`). No hace falta
  convención de registros más allá de `DE=FLAGS`.
- **Debe preservar el estado del intérprete**: el handler ya salva/restaura
  `CHUNK` (el banco activo) alrededor de la llamada. La rutina puede usar
  AF/BC/DE/HL/IX/IY libremente PERO no debe dejar el hardware/paginación en un
  estado que rompa el motor al volver (si toca `$7FFD`, restaurarlo). Documentado.
- **Debe caber en un banco** (16 KB, ventana `$C000-$FFFF`) en targets con banking;
  no puede repartirse entre bancos. Si no cabe → error de compilación limpio.
- **Sin sandbox**: es código nativo de confianza. Una rutina con bugs puede colgar
  la máquina. Es una feature **avanzada, opt-in**, con el mismo riesgo que ya
  asumen WYZ/BeepFx. Se documenta "a tu propio riesgo".

Abierto (§10): convención de valor de retorno más allá de FLAGS; si se permite
que la rutina llame de vuelta al motor (por ahora **no**: rutina hoja).

---

## 5. El núcleo: `ORG` calculado por CYD (resuelve la relocalización)

**El autor nunca especifica la dirección de carga; la calcula CYD.** La rutina se
ensambla en la ubicación real donde va a correr, así que las direcciones absolutas
resuelven bien **sin necesidad de código relocatable**.

Como la dirección final depende del layout de memoria (y en 128k, de qué banco y
offset le asigne el allocator), se usa el mismo two-pass que CYD ya aplica al
intérprete (ensamblar con `SHOW_SIZE_INTERPRETER` para medir antes de repartir
memoria, ARCHITECTURE §3 paso 7):

1. **Medir**: ensamblar la rutina aislada con un `ORG` provisional → obtener su
   **tamaño**.
2. **Colocar**: pasar ese tamaño al allocator, que le asigna **banco + offset**
   (banked) o una **dirección residente** (48k), como a cualquier recurso.
3. **Ensamblar final**: re-ensamblar la rutina con `ORG = dirección final` →
   los bytes definitivos, que se colocan en esa posición.

> **Asunción / riesgo (a verificar):** el tamaño de la rutina es **estable entre
> `ORG`s**. Cierto para Z80 escrito a mano (sjasmplus no auto-optimiza `jr`↔`jp`
> ni realinea por dirección). Si el autor usa construcciones dependientes de la
> dirección que cambien el tamaño entre pasadas, la asignación se invalidaría; hay
> que **verificar tamaño idéntico entre pasada 1 y 3 y abortar limpio** si difiere.

### 5.1 Modelo uniforme por target

| Target | `ORG` de la rutina | Colocación | Cómo la llama `OP_EXTERN` |
|---|---|---|---|
| **48k** | dirección residente **calculada** | residente en `$8000-$FFFF` | `call` directo (sin paginar) |
| **128k / plus3 / mld128** | `$C000 + offset_en_banco` | en un banco (compartible) que asigna el allocator | `LOAD_CHUNK` (paginar banco) + `call $C000+offset` |

El 48k **es requisito** (debe funcionar). Al no haber paginación, la rutina es
residente y el `ORG` es su dirección final en el mapa de 48K; `OP_EXTERN` hace
`call` directo e ignora el operando de banco.

### 5.2 Alternativa considerada y descartada: fijar en `$C000` (banco propio)

Se valoró dar a cada rutina un **banco propio** con `ORG $C000` fijo (como el WYZ
player), evitando el re-ensamblado en offset calculado. **Descartada**, porque:

1. **No sirve para 48k** (requisito): en 48k no hay banco `$C000` que paginar, la
   rutina va residente en dirección calculada → seguiría haciendo falta el
   ORG-calculado. Fijar `$C000` solo simplificaría la ruta banked → **dos
   mecanismos** en vez de uno.
2. **Desperdicia un banco entero (16 KB) por rutina** — inviable en 128k (~6 bancos,
   con banco 1 reservado a WYZ y el resto a texto/imágenes/música).
3. **No elimina el riesgo de size-stability** (48k lo mantiene).

Solo convendría en un MVP **banked-only** (sin 48k), que no es el caso. Decisión:
**allocator + ORG calculado, uniforme**.

---

## 6. Integración con el build y el allocator

La rutina nativa se trata como **un recurso más**, con su tamaño, que el allocator
coloca por best-fit (como TXT/SCR/TRK). Puntos de integración (a verificar en
implementación):

- **Tipo de recurso**: hoy el índice usa `TYPE_TXT/SCR/TRK/WYZ`
  ([cyd_tape.asm:416-419](src/cydc/cydc/cyd/cyd_tape.asm#L416)). Añadir `TYPE_CODE`
  (o reutilizar el mecanismo de bloques) para que `LOAD_CHUNK`/`FIND_IN_INDEX`
  puedan paginar el banco de la rutina. `LOAD_CHUNK` hoy busca `TYPE_TXT` fijo
  ([cyd_tape.asm:423-432](src/cydc/cydc/cyd/cyd_tape.asm#L423)); necesitará poder
  localizar el chunk de código.
- **Allocator**: `spectrum_banks` y el reparto best-fit en
  [cydc.py:796-915](src/cydc/cydc/cydc.py#L796). La rutina entra en el conjunto de
  bloques a colocar; debe **caber contigua en un banco** (no se puede trocear,
  a diferencia del texto).
- **Resolución tardía**: tras la colocación se conoce (banco, offset) → se calcula
  `dirección = $C000+offset` (banked) o la residente (48k) → se re-ensambla la
  rutina a ese `ORG` → se parchea el operando del `OP_EXTERN` correspondiente y el
  índice de recursos (mismo estilo que el remapeo de índices ya existente).
- **Pasada de ensamblado aislada**: reutilizar `run_assembler`
  ([cydc_utils.py:76](src/cydc/cydc/cydc_utils.py#L76)) con una plantilla que
  enmarque el fichero del autor: `ORG @ADDR` + cuerpo + `ASSERT tamaño` + `SAVEBIN`.
  Errores de ensamblado → mensaje limpio `IMPORT '<nombre>': fallo al ensamblar
  <fichero>` (encaja con la mejora de robustez de `run_assembler`, que ahora
  conserva el `.asm` y propaga el stderr).

---

## 7. Runtime: handler y jump table

- **Arreglar el handler** [interpreter.asm:2758-2790](src/cydc/cydc/cyd/interpreter.asm#L2758):
  el `call` automodificado tiene el label malformado. Rehacerlo limpio (p.ej.
  cargar la dirección en `HL`/una var y `ld (self+1),...` con el label del operando
  bien definido, o un salto indirecto). Descomentar.
- **Bifurcación por target**: 48k = `call` directo a la dirección residente (sin
  `LOAD_CHUNK`); banked = `LOAD_CHUNK` del banco + `call $C000+offset` + restaurar
  banco. Se implementa con los DEFINEs de target ya existentes (`IFDEF IS_128`,
  etc.) — mismo mecanismo que el resto de divergencias por target.
- **Jump table**: añadir la entrada con la guarda `UNUSED_OP_EXTERN`
  (`DW OP_EXTERN` / `DW ERROR_NOP`) en la posición del nuevo opcode, como el resto
  ([interpreter.asm:2798+](src/cydc/cydc/cyd/interpreter.asm#L2798)).
- **`DE = FLAGS`** antes del `call` (ya está en el diseño del handler).

---

## 8. Plan de implementación por fases

1. **Front-end** (Python, bajo riesgo): tokens `IMPORT`/`FROM`/`CALL`, reglas de
   parser, tabla de rutinas importadas, byte de opcode + emisión con placeholder,
   validación de `CALL` a nombre no declarado. **Testeable en aislado** (parser →
   bytecode), como los tests de codegen ya existentes.
2. **Build** (el grueso): pasada de medición, integración en el allocator, tipo de
   recurso/índice, resolución tardía + re-ensamblado al `ORG` final, parcheo de
   operandos. Verificar la estabilidad de tamaño (§5).
3. **Runtime** (asm): arreglar y activar el handler, bifurcación por target, jump
   table. Verificar en **emulador** (48k y 128k) con una rutina mínima.
4. **Ejemplo + docs**: `examples/import_demo/` (rutina que, p.ej., lee un puerto o
   hace un efecto de beeper y devuelve por FLAGS) + sección de manual con el ABI y
   el aviso de "avanzado, a tu propio riesgo".

Verificación empírica obligatoria antes de dar nada por hecho (emulador real, no
solo lectura): reproducir un `CALL` funcionando en 48k y 128k.

### 8.1 Estado de implementación (fase 1 hecha)

**Fase 1 (front-end) COMPLETA y verificada** (suite en verde, 279 tests):
- `cydc_lexer.py`: token `STRING` (`t_STRING`, regex `"[^"\n]*"`, sólo estado
  INITIAL; `rawtext` es exclusivo → no afecta al texto mostrado) + reserved words
  `IMPORT`/`FROM`/`CALL`.
- `cydc_parser.py`: `SymbolType.EXTERN`; `p_statement_import`
  (`IMPORT ID FROM STRING` → `("IMPORT", nombre, fichero)`, `_declare_symbol`);
  `p_statement_call` (`CALL ID` → `("EXTERN", nombre, 0, 0)`, `_symbol_usage`).
- `cydc_codegen.py`: opcode `"EXTERN": 0x7F`; `self.externs = {}` poblado en
  `code_extract_declarations` (rama `IMPORT`, no emite bytecode). `CALL` fluye por
  `code_translate`/`symbol_replacement` como los labels (placeholder `[0x7F, nombre, 0, 0]`).
- Tests nuevos en `tests/test_parser.py` (`test_parse_import_and_call`,
  `test_parse_call_without_import_errors`). `test_parse_print_statement` cambió de
  `PRINT "text"` (ahora error de sintaxis, correcto) a `PRINT 42`.

**Falta para que `CALL` compile end-to-end:** la fase 2 debe inyectar cada rutina
importada en `self.symbols` con su `(bank, offset)` tras la asignación, para que
`symbol_replacement` resuelva el placeholder (hoy daría "Label X does not exists").
El opcode `0x7F` aún no tiene handler ni entrada en la jump table (fase 3).

---

## 9. Resumen de decisiones cerradas

- Sintaxis: **`IMPORT nombre FROM "fichero.asm"`** (declara) + **`CALL nombre`** (invoca).
- Opcode interno: `OP_EXTERN`, operandos `[chunk, addr_lo, addr_hi]`.
- ABI: `DE=FLAGS`, `ret`, E/S por el array `FLAGS`; rutina hoja; debe caber en un banco.
- Relocalización: **`ORG` calculado por CYD** + re-ensamblado en la dirección
  final. Nada de PIC. Uniforme entre targets.
- **48k soportado** (residente, `call` directo). 128k/plus3/mld por banco
  (posible offset ≠ 0 por el allocator) + paginación.
- Ensamblado **aislado** por rutina (patrón WYZ) → errores limpios, sin romper el motor.

## 10. Abierto / a decidir

- Convención de **valor de retorno** más allá de FLAGS (¿un registro que el handler
  guarde en una var? por ahora todo por FLAGS).
- ¿Se permite que la rutina **llame de vuelta al motor** (imprimir, etc.)? Por
  ahora **no** (rutina hoja); revisar si surge necesidad.
- **Varias rutinas por banco**: soportado por el modelo (offset por rutina); definir
  si `IMPORT` de varias del mismo `.asm` o de varios ficheros.
- Presión de memoria en **48k** (residente compite con el contenido): documentar y
  dar error claro si no cabe.
- Verificar la **estabilidad de tamaño** entre pasadas (§5) y abortar si difiere.
