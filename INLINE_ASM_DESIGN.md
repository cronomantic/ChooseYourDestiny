# Estudio de diseño: ensamblador inline + ABI ampliada (`ASM` / `CALL`)

> **Propósito.** Fijar el diseño de escribir rutinas Z80 **directamente en el guion
> `.cyd`** (bloques `ASM … ENDASM`) y de la **ABI ampliada** que las hace útiles de
> verdad (acceso a arrays, memoria de vídeo, buffer de imagen, servicios del motor,
> llamadas entre rutinas). Es la generalización de `IMPORT`/`CALL`
> ([EXTERN_DESIGN.md](EXTERN_DESIGN.md)): **azúcar sobre el mismo mecanismo**, el
> cuerpo viene inline en vez de un fichero.
>
> Documento de referencia para no re-derivar el entendimiento. Las afirmaciones
> sobre el código actual llevan `fichero:línea` verificados salvo que se indique
> "(a verificar)". Asume [ARCHITECTURE.md](ARCHITECTURE.md) y
> [EXTERN_DESIGN.md](EXTERN_DESIGN.md).
>
> **Estado: DISEÑO. Nada implementado.** `IMPORT`/`CALL` (EXTERN) sí está hecho y
> verificado (48k/128k/+3); este estudio construye encima.

---

## 1. Motivación y tesis

El objetivo que motiva la feature: **portar las librerías `math16_32`/`strings` a
ensamblador** de forma cómoda, sin trocearlas en ficheros `.asm` sueltos, y en
general **poder escribir comandos nuevos** (gráficos, datos) que el intérprete no
tiene. Hoy esas librerías son bytecode CYD puro (bucles interpretados, lentos en
mul/div; ver cabecera de [lib/math16_32.cyd](lib/math16_32.cyd)).

**Tesis:** el ensamblador inline **no es una vía nueva**. Un bloque `ASM nombre …
ENDASM` registra la **misma clase de rutina nativa** que `IMPORT nombre FROM
"fichero.asm"`, con el cuerpo escrito en el propio `.cyd`. Todo lo de aguas abajo se
reutiliza: ensamblado aislado (patrón WYZ), `ORG` calculado por CYD, colocación por
el allocator, parcheo tardío de operandos, handler `OP_EXTERN`. Lo único genuinamente
nuevo es (a) capturar el cuerpo verbatim en el front-end, (b) la **ABI ampliada** de
las §4–§8, y (c) multi-export + limpieza (§9–§10).

---

## 2. Superficie de lenguaje

```
ASM mathcore EXPORTS add32, sub32, mul32, div32   ; bloque con nombre + exports
             USES   printdec                       ; llama a otra rutina nativa
add32:  ...                                         ; cuerpo Z80 verbatim
        ret
sub32:  ...
        ret
_carry: ...              ; helper PRIVADO (no exportado): compartido por las anteriores
        ret
ENDASM

...
CALL add32                                          ; invoca (runtime -> OP_EXTERN)
```

- **`ASM nombre [EXPORTS a, b, …] [USES x, y, …]` … `ENDASM`** — declara un bloque de
  código nativo. Directiva de declaración (como `IMPORT`/`CONST`/`DECLARE`), a nivel
  de guion (no lexicamente dentro de un `LABEL`/`GOSUB`).
  - Sin `EXPORTS`: el bloque **es** una única rutina, invocable por `nombre`
    (entrada = principio del bloque).
  - Con `EXPORTS a, b, …`: el bloque exporta **varios puntos de entrada**; cada
    `nombre_exportado` se invoca por separado con `CALL`. Comparten helpers privados y
    se llaman entre sí con `call` **intra-banco** (§7). El propio `nombre` del bloque
    es la unidad de ensamblado/colocación/limpieza, no un símbolo invocable.
  - Con `USES x, y, …`: declara que el código **llama a otras rutinas nativas** de
    OTRO bloque vía `CYD_CALL` (§8). Necesario para el parcheo de direcciones y para
    la limpieza (§10). Llamadas dentro del mismo bloque NO se declaran (son `call`
    normales).
- **`IMPORT nombre FROM "fichero.asm"`** — igual que hoy; equivalente a un `ASM`
  cuyo cuerpo se lee de fichero. Podrá aceptar `EXPORTS`/`USES` con la misma
  semántica.
- **`CALL nombre`** — invoca. Emite `OP_EXTERN` con operandos `[banco, addr_lo,
  addr_hi]` de `nombre`, resueltos por parcheo tardío.

**Front-end (Python), lo único nuevo:**
- **Lexer**: un estado exclusivo que capture el cuerpo **verbatim** entre `ASM` y
  `ENDASM` (precedente directo: el estado `rawtext` para el texto mostrado, y el
  token `STRING` que ya se añadió para `IMPORT`). Terminador: `ENDASM` a principio de
  línea. El cuerpo NO se tokeniza como CYD (tiene `;`, `:`, comillas, etc.).
- **Parser**: regla `ASM ID [EXPORTS idlist] [USES idlist] rawasm ENDASM` →
  `("ASM", nombre, cuerpo, exports, uses)`; alimenta la tabla de rutinas. `EXPORTS`
  declara cada nombre como símbolo `EXTERN` invocable (§9).
- **Codegen**: reutiliza el opcode `EXTERN = 0x7F` y `self.externs` (hoy `nombre →
  fichero`; pasa a `nombre → ("file", ruta) | ("inline", texto)` + metadatos de
  export/uses). `CALL` fluye por `symbol_replacement` como hoy, registrando la
  posición en `self.extern_calls` para el parcheo tardío
  ([cydc_codegen.py:1157-1163](src/cydc/cydc/cydc_codegen.py#L1157)).

---

## 3. Modelo de invocación (cerrado)

**Rutina con nombre, NO interleaving.** El bloque es una rutina invocable; se entra
con `DE=FLAGS`, termina en `ret`. Se descartó el interleaving de asm dentro del
bytecode: convertiría la ABI en el estado interno crudo de la VM (IX=pila,
IY=sysvars, HL=puntero de instrucción), divergería por target y complicaría la
relocalización dentro del chunk. Rutina con nombre = reutiliza EXTERN y encaja con
"portar rutinas invocables".

---

## 4. ABI: entrada, salida y contrato

- **Entrada:** `DE = FLAGS` (base de las 256 variables). Sin gramática formal de
  argumentos por pila en v1 (ver justificación abajo).
- **Salida:** `ret`. **Resultados por FLAGS** (el guion pone argumentos con `SET`,
  hace `CALL`, la rutina lee/escribe `FLAGS+n`, el guion lee con `@var`). Es lo que
  ya hacen math/strings (registros en posiciones fijas de FLAGS) y maneja valores
  **anchos** (16/32 bits en posiciones consecutivas) de forma natural.
- **Preservación:** el handler salva/restaura IX (pila de datos de la VM) e IY
  (sysvars ROM) y restaura el banco. La rutina puede reventar AF/BC/DE/HL libremente.
- **Rutina hoja respecto al bytecode:** no retorna al bucle del intérprete a mitad;
  corre entera y hace `ret`. Puede, eso sí, llamar a **servicios del motor** (§6) y a
  **otras rutinas nativas** (§7–§8).

**Por qué NO pasar la pila de enteros como canal de argumentos (decisión).** La
"pila de enteros" de la VM es en realidad una **pila de bytes** e **IX** la comparte
con los frames de retorno de `GOSUB`
([interpreter.asm:56-95](src/cydc/cydc/cyd/interpreter.asm#L56)): `PUSH_INT_STACK` =
`dec ix : ld (ix+0),a`; `OP_GOSUB` apila un frame de 3 bytes en `ix-1/-2/-3`. Exponerla
como canal formal es (a) mal encaje para valores anchos (habría que apilar 2-4
bytes), (b) arriesgado (desbalancear IX corrompe la pila de retorno). FLAGS es
genuinamente el mejor canal aquí.

**Extensión futura (opcional, no v1):** permitir que una rutina que devuelve **un
solo byte** haga `PUSH_INT_STACK`, y así `CALL nombre` sea usable como
**byte-expresión** (`SET x TO …`). Ortogonal; no rompe v1.

---

## 5. Modelo de memoria y colocación

Reproduce el de EXTERN (verificado, [EXTERN_DESIGN.md §8.3](EXTERN_DESIGN.md)):

| Target | Colocación de la rutina | Cómo la llama `OP_EXTERN` |
|---|---|---|
| **48k** | residente al final del bank 0 (`$8000-$BFFF`) | `call` directo |
| **128k / +3 / mld128** | banco **paginado** (`$C000+offset`), best-fit, compartible | `SET_RAM_BANK` (paginа el banco) + `call $C000+offset` + restaura |

### 5.1 El banco propio de la rutina = su RAM privada directa
Lo que la rutina ensambla es su banco: **código + tablas (`DEFB`) + scratch (`DEFS`)**,
todo directamente accesible en `$C000` mientras está paginada.
- Para datos propios de **más de 256 B** no hace falta broker ni FLAGS: `DEFS` en el
  bloque, uso directo con `ld (hl),a`.
- Ese scratch **persiste entre llamadas** en 128k/+3 (la RAM del banco no se limpia y
  el allocator no reusa su región) → estado nativo entre CALLs (semilla RNG, buffer).
  **(a verificar)** en mld128 (los bloques se precargan una vez; la persistencia
  depende de que no se re-paginen desde slots).
- **Tamaño real:** la rutina se coloca por best-fit **compartiendo banco** con otros
  recursos; su RAM privada = lo que declare (`DEFS`), que el allocator le reserva. No
  se lleva 16 KB salvo que quepa/lo pida.

### 5.2 La regla de oro (sostiene todo el modelo)
**La rutina NUNCA paginа `$C000` por su cuenta.** No se expone `SET_RAM_BANK` crudo.
*Todo* cruce de banco (arrays §6, memoria de otro banco §6.3, llamada a rutina en otro
banco §8) pasa por **servicios residentes** que: guardan el banco actual → paginan lo
que toque a `$C000` → copian a RAM baja fija (`$4000-$7FFF`) → **repaginan la rutina**
→ retornan. Si la rutina paginara `$C000`, se auto-expulsaría (su código y su
dirección de retorno desaparecen). Los servicios son residentes (`$8000-$BFFF`,
siempre mapeados), así que la rutina siempre puede alcanzarlos con un `call`.

---

## 6. ABI: acceso a datos del motor (el `cyd_abi.inc` inyectado)

CYD ensambla cada rutina **en aislado** y conoce la tabla de símbolos del build actual
y dónde colocó cada recurso. Por eso el contrato es un **include generado que CYD
antepone** a cada rutina, exponiendo solo lo curado. Tres tipos de entrada:

### 6.1 Direcciones de estructuras (residentes, `$4000-$7FFF`, siempre mapeadas)
Verificado: `vars.asm` hace `ORG $5d00` → FLAGS, pila, buffers viven en RAM baja fija,
**no** en `$8000-$BFFF` como creí al principio ([vars.asm:33-179](src/cydc/cydc/cyd/vars.asm#L33)).
- `FLAGS` — base de las 256 variables (también en `DE`).
- `SCREEN_BUFFER_PXL` / `SCREEN_BUFFER_ATT` — el buffer de imagen del motor
  ([vars.asm:159-162](src/cydc/cydc/cyd/vars.asm#L159), `$6000`). Habilita rutinas
  gráficas que el intérprete no tiene (blits con máscara, scroll, efectos): la rutina
  compone en el buffer y usa `DISPLAY`/`COPY_SCREEN` para volcar.
- `VIDEO_PXL` / `VIDEO_ATT` — base de la memoria de vídeo del hardware (`$4000`/`$5800`
  en Spectrum, **siempre mapeada**). Marcada target-dependiente (el port CPC la
  redefine).

### 6.2 Acceso a arrays (irrenunciable) — broker MAP/FLUSH + PEEK/POKE
Los arrays son datos inline del bytecode y pueden acabar en un banco paginado (los
declarados en chunks que desbordan el bank 0). Como la rutina vive en `$C000`, no puede
paginar el banco del array sin auto-expulsarse (§5.2). Solución: **servicios residentes
que hacen el banking con buffer intermedio**. Aprovecha que **todo array es ≤ 256 B**
([cydc_codegen.py:485](src/cydc/cydc/cydc_codegen.py#L485), `array_len in range(1,257)`)
→ cabe entero de una copia.

- **`CYD_ARR_MAP(id) → HL=puntero, BC=longitud`** (G1): paginа el banco del array,
  copia sus N bytes al scratch residente, repaginа la rutina, devuelve puntero+longitud.
  La rutina trabaja a velocidad nativa sobre el scratch.
- **`CYD_ARR_FLUSH(id)`**: copia el scratch de vuelta al array (solo si la rutina
  escribió). **1 paginada por MAP + 1 por FLUSH.**
- **Uniforme (esconde el banking):** si el array es **residente** (chunk 0), `MAP`
  devuelve su dirección real sin copiar y `FLUSH` es no-op. El autor escribe un solo
  patrón (`MAP` → trabaja por HL → `FLUSH` si tocó) y no sabe si está en banco.
- **`CYD_ARR_PEEK(id, idx) → val` / `CYD_ARR_POKE(id, idx, val)`** (G2): acceso por
  elemento sin buffer (un byte por registro). Para accesos sueltos o el **segundo**
  operando en operaciones de dos arrays (copiar A→B, comparar A vs B): `MAP` del primero
  al scratch + `PEEK`/`POKE` sobre el segundo.

**Scratch = `SAVE_FLAGS`** (256 B ya existentes,
[vars.asm:174](src/cydc/cydc/cyd/vars.asm#L174)): es el staging del salvado de partida,
usado **exclusivamente** en `savegame_tape/plus3/mld.asm` durante SAVE/LOAD, que **nunca
se solapa con un `CALL`** (ambos son operaciones síncronas del bucle de bytecode). →
**0 bytes residentes nuevos**. Invariante a documentar: no exponer SAVE/LOAD como
servicio invocable desde asm; el contenido del scratch solo es válido dentro del `CALL`.

### 6.3 Acceso a memoria de otro banco (avanzado)
Generaliza el broker de arrays a memoria banco cruda:
`CYD_COPY_FROM_BANK(banco, addr, len)` / `CYD_COPY_TO_BANK(banco, addr, len)` sobre el
mismo scratch. **Servicio avanzado, no núcleo** (crudo, sin bounds; los números de
banco son target-específicos). Se expone, con aviso.

---

## 7. Servicios del motor (callbacks) — syscall numerada

Los "servicios del motor" (imprimir carácter, imprimir byte decimal, leer tecla,
esperar frames, RNG, volcar buffer, cargar recurso, y los brokers de §6) se exponen por
un **único punto de entrada estable** `CYD_SYSCALL` + **servicios por número**:

```
    ld a, SVC_PRINT_CHAR
    ld l, 65
    call CYD_SYSCALL
```

CYD inyecta en `cyd_abi.inc` solo `CYD_SYSCALL EQU $xxxx` (dirección real del build) y
las constantes `SVC_*`. **Por qué numerada (no EQU directo a cada rutina del motor):**
solo una dirección se inyecta; los IDs son estables por contrato → la ABI es
**versionable** y sobrevive a una reescritura del intérprete sin recompilar las rutinas
del autor contra internos que se mueven. Superficie **curada** y **versionada** (empezar
mínima, crecer deliberado). Las direcciones de datos (§6.1, arrays, memoria) sí van por
EQU inyectado porque son datos, no puntos de entrada del motor.

**El dispatcher `CYD_SYSCALL` y cada servicio se compilan condicionalmente (Sergio,
4 jul 2026): si ningún bloque nativo los usa, NO entran en el build.** Es el mismo
mecanismo `UNUSED_OP_*` de los opcodes (§ARCHITECTURE 5.3): guardas `IFNDEF
UNUSED_SVC_<NAME>` alrededor del cuerpo de cada servicio + entrada de la tabla de
despacho a `ERROR_NOP`, y `IFNDEF UNUSED_SYSCALL` alrededor del dispatcher entero. CYD
calcula qué servicios se referencian (ver §10) y emite los `DEFINE UNUSED_SVC_*`
correspondientes. Motivo: el motor es residente y la RAM escasa; un programa que no
llama a servicios no debe pagar su coste. Ver §10.

---

## 8. Llamadas entre rutinas nativas: banking del `CALL` y `CYD_CALL`

El salto del `CALL` script→rutina es **un salto bancado**, y lo seguimos soportando:
**lo hace el handler `OP_EXTERN` residente**, no la rutina (coherente con §5.2). Ya
está implementado y verificado.

**Compone en anidamiento** porque el handler guarda/restaura el **valor real del
puerto** `$7FFD`, no un banco fijo (EXTERN_DESIGN.md §8.3: *"restaurar el valor real
del puerto … hace el retorno robusto sea cual sea el banco desde el que se hizo el
CALL"*). Cada nivel (CALL o servicio broker) apila su puerto previo en la pila hardware
(residente) y lo restaura al volver → cascada correcta, sin estado global de banco que
se corrompa.

Rutina → rutina, dos casos:
- **Mismo bloque (multi-export):** `add32` llama a `mul32` con `call` **intra-banco**
  normal (ambas en el mismo banco, mapeadas juntas). **Cero banking.** Vía recomendada
  para librerías.
- **Bloques distintos (cross-bank) → `CYD_CALL`:** A (banco Ba) no puede hacer `call B`
  crudo (Bb no está mapeado; paginarlo evict­aría a A). Usa el **trampolín residente**:
  ```
      ld a, RT_printdec        ; índice de rutina inyectado por CYD (ver abajo)
      call CYD_CALL
  ```
  `CYD_CALL` guarda el banco de A, paginа Bb, llama a B, **repaginа A** y retorna.
  Mientras B corre, A está expulsada pero su dirección de retorno vive en la pila
  hardware; al volver, A se repaginа. Compone con el anidamiento de arriba.

**Mecanismo de resolución de `CYD_CALL` (índice + tabla de despacho).** B se coloca
tarde (allocator), así que su `(banco, addr)` no se conoce al ensamblar A. Se resuelve
como los `CALL` del script: CYD mantiene una **tabla de despacho de rutinas** `[(banco,
addr_lo, addr_hi)]` indexada por rutina, rellenada tras la colocación; `CYD_CALL(idx)`
la indexa. CYD inyecta en el `cyd_abi.inc` de A un `RT_<nombre> EQU <idx>` por cada
rutina que A declara en `USES`. El `USES` es lo que le dice a CYD (a) qué índices
inyectar y (b) las **aristas nativa→nativa** para la limpieza (§10), sin tener que
parsear el asm.

---

## 9. Multi-export: unidad de ensamblado y colocación

`ASM mathcore EXPORTS add32, sub32, mul32, div32` se ensambla **una vez**; las cuatro
comparten helpers privados y se llaman entre sí con `call` interno (resuelto por
sjasmplus dentro del mismo ensamblado aislado). Mecanismo:
- CYD enmarca el bloque (`DEVICE + ORG + <cuerpo> + medición + SAVEBIN`) y pide a
  sjasmplus el **fichero de símbolos** (`--sym`); parsea la dirección de cada nombre
  de `EXPORTS` → `export = base_del_bloque + offset_del_label`.
- El bloque se coloca como **una unidad** (un banco o zona residente); cada export es
  un destino de `CALL` con su `(banco, addr)`.
- Cada `nombre` de `EXPORTS` se registra como símbolo `EXTERN` en el codegen para que
  `CALL nombre` valide y emita el placeholder.

Por qué: es la **unidad natural de una librería** (comparten helpers, se llaman entre
sí sin banking §8). Sin multi-export cada rutina sería un bloque aislado que no puede
compartir helpers ni llamar a hermanas — justo lo incómodo al portar math/strings.

---

## 10. Limpieza (`-dce`): rutinas nativas no usadas se eliminan

Requisito: una rutina nativa importada/inline que **nadie llama** no debe ensamblarse
ni colocarse (ahorra RAM residente/banco, que es el recurso escaso).

**Hallazgo que lo hace casi gratis.** En `generate_code`
([cydc_codegen.py:1226-1254](src/cydc/cydc/cydc_codegen.py#L1226)) el orden es:
declaraciones → peephole → **DCE** ([dead_code_elimination](src/cydc/cydc/cydc_codegen.py#L930),
si `-dce`) → `code_translate` → `symbol_replacement`. Como **`self.extern_calls` se
puebla en `symbol_replacement`, DESPUÉS de la DCE**, ya contiene **solo los `CALL` de
bytecode alcanzable**. Pero el build actual ([cydc.py:981-992](src/cydc/cydc/cydc.py#L981))
ensambla y coloca **todas** las rutinas de `codegen.externs`, aunque nadie las llame.

**Diseño de la limpieza:**
1. **Conjunto usado inicial** = `{ nombre : (nombre, chunk, pos) ∈ codegen.extern_calls }`
   (rutinas referenciadas por un `CALL` alcanzable).
2. **Cierre transitivo por `USES`**: si una rutina usada A declara `USES B` (§8), B es
   usada aunque el guion no la llame directamente. Punto fijo sobre las aristas `USES`.
3. **Granularidad = bloque.** Un bloque `ASM` se **conserva** si **alguno** de sus
   `EXPORTS` está en el conjunto usado; si **ninguno** lo está, se **descarta entero**
   (no se ensambla, no se coloca, no se parchea). Exports parciales **no** se pueden
   podar (un bloque = una unidad de ensamblado indivisible; los helpers privados
   pueden usarlos varios exports). A documentar.
4. Solo se ensamblan/colocan (§5, §9) los bloques conservados.

**Semántica respecto al flag.** Filtrar `externs` por el conjunto usado da el
comportamiento correcto en ambos modos, porque `extern_calls` ya refleja la
alcanzabilidad post-DCE:
- **`-dce` off:** `extern_calls` = todos los `CALL` del código → se conservan las
  rutinas con ≥1 `CALL`; un `IMPORT`/`ASM` **nunca llamado** se descarta igualmente
  (mejora siempre-activa razonable — hoy se colocaría en balde).
- **`-dce` on:** `extern_calls` = `CALL` de código **alcanzable** → también se
  descartan las rutinas alcanzadas solo desde bytecode muerto.

Combina con la idea de "librería gorda, salida mínima" que ya persigue `-dce`
(EXTERN_DESIGN.md, DCE): una librería nativa multi-export grande con `-dce` deja fuera
los bloques cuyos exports no se usan.

### 10.1 Extirpar la maquinaria de la ABI si no se usa (Sergio, 4 jul 2026)

No solo los bloques: **los servicios `CYD_SYSCALL` y el broker de arrays
(`MAP`/`FLUSH`/`PEEK`/`POKE`, §6.2) también deben desaparecer del build si ningún
bloque nativo los referencia.** El motor es residente y la RAM baja/residente es
escasa; un programa que no usa arrays desde asm no debe pagar el coste del broker, ni
uno que no llama a servicios el del dispatcher.

Mecanismo (idéntico al `UNUSED_OP_*` de los opcodes, §ARCHITECTURE 5.3, cero maquinaria
nueva en el lado asm):

1. **Detección**: como cada rutina se ensambla **aislada con el `cyd_abi.inc`
   inyectado**, CYD sabe qué símbolos de la ABI se resuelven de verdad. Basta con que
   el `cyd_abi.inc` de cada bloque **defina solo los servicios que ese bloque declara
   usar** (vía una cláusula tipo `USES` de servicios, o escaneando qué `SVC_*`/`CYD_*`
   referencia el cuerpo), y CYD acumula la unión sobre los bloques **conservados** tras
   la DCE de bloques (§10).
2. **Emisión**: por cada servicio/broker no referenciado, CYD emite un `DEFINE
   UNUSED_SVC_<NAME>` (y `UNUSED_SYSCALL` si no se usa ninguno, y `UNUSED_ARR_BROKER`
   si ningún bloque toca arrays). El motor guarda cada cuerpo con `IFNDEF UNUSED_*` y
   pone `ERROR_NOP` en la entrada de la tabla de despacho.
3. **Consistencia**: el conjunto de servicios usados se calcula **después** de la DCE
   de bloques, así un servicio referenciado solo por un bloque descartado también se
   extirpa. Mismo cierre transitivo que §10 (un bloque conservado que use un servicio
   → ese servicio se conserva).

Esto exige que el front-end/una cláusula haga explícito (o infiera) qué servicios usa
cada bloque, análogo a `USES` para rutinas. A diseñar en fase 3 junto con la ABI.

---

## 11. Soporte por target

| Target | Rutina | Arrays/broker | `CYD_CALL` | Notas |
|---|---|---|---|---|
| 48k | residente, `call` directo | todo residente (broker = no-op de copia) | intra-región | listón; sin banking |
| 128k | banco paginado | broker `$7FFD` + `SAVE_FLAGS` | trampolín | verificado (base EXTERN) |
| +3 | banco paginado (excluye banco 7) | íd. | trampolín | verificado (base EXTERN) |
| mld128 | banco paginado | íd. | trampolín | **runtime a verificar** cuando arranque MLD |
| mld | — | — | — | error limpio (allocator de 1 banco) |

`VIDEO_PXL/ATT` y la geometría son target-dependientes (el port CPC redefine
`cyd_abi.inc`).

---

## 12. Riesgos y a verificar

- **Estabilidad de tamaño entre pasadas** (medir a ORG provisional → colocar →
  re-ensamblar a ORG final): abortar limpio si difiere. Ya resuelto para EXTERN; aplica
  igual a bloques inline y multi-export.
- **`--sym` de sjasmplus**: confirmar el formato exacto del fichero de símbolos y que
  `run_assembler` puede pedirlo/parsearlo (§9). Alternativa si falla: emitir los
  offsets de export como datos al final del `.bin` y leerlos.
- **Errores de ensamblado de sjasmplus (REQUISITO de primer orden, Sergio insistió
  4 jul 2026)**: para bloques inline, sjasmplus referenciará el `.asm` **temporal**
  generado, no el `.cyd`. Hay que **capturarlos muy bien**: (a) conservar el temporal
  (ya se hace) con el framing en offset conocido → **mapear la línea del temporal a la
  línea del `.cyd`** (el `INCLUDE`/volcado del cuerpo empieza en una línea fija del
  framing; línea_cyd = línea_temporal − offset_de_cabecera_framing + línea_del_bloque
  en el `.cyd`), o inyectar directivas de línea de sjasmplus; (b) **atribuir el bloque**
  (`ASM '<nombre>'` / `IMPORT '<nombre>'`); (c) propagar el stderr de sjasmplus íntegro.
  Base: el `assemble_extern_routine` actual ya reporta `IMPORT '<nombre>': failed to
  assemble <fichero>\n{stderr}`; falta el mapeo de línea para inline. Fase 2/3.
- **Persistencia del scratch de banco en mld128** (§5.1) — a verificar en emulador
  cuando arranque MLD.
- **Anidamiento profundo de banking** (CALL→CYD_CALL→broker): validar que el guardado
  del puerto por-nivel en la pila hardware no desborda ni descuadra IX/SP.
- **Verificación empírica obligatoria** (emulador real, no lectura): un bloque inline
  multi-export que use un array paginado (MAP/FLUSH) y un `CYD_CALL` cross-bank, en 48k
  y 128k; y que `-dce` descarte un bloque no usado (comparar tamaños). Usar el harness
  ZEsarUX headless.

---

## 13. Plan de implementación por fases

1. **Front-end** (Python, bajo riesgo): lexer verbatim `ASM…ENDASM`, parser
   `EXPORTS`/`USES`, `externs` con cuerpo inline + metadatos, registro de exports como
   símbolos `EXTERN`. Testeable en aislado (parser → tabla de rutinas).
2. **Build — inline + multi-export**: `assemble_extern_routine` acepta `inline_source`;
   framing con `--sym`; resolución de exports; colocación por bloque; parcheo de `CALL`.
3. **ABI de datos**: generar e inyectar `cyd_abi.inc` (FLAGS, buffers, vídeo,
   `ARR_*`/ids); broker de arrays MAP/FLUSH+PEEK/POKE sobre `SAVE_FLAGS`; servicios
   `CYD_SYSCALL` mínimos.
4. **`CYD_CALL`**: tabla de despacho de rutinas + trampolín residente + inyección de
   `RT_*` por `USES`.
5. **Limpieza** (§10): filtrar `externs` por el conjunto usado + cierre `USES`, a
   granularidad de bloque.
6. **Ejemplo + documentación (tarea de primer orden, no opcional)** — sigue el
   pipeline de docs del proyecto ([reference-release-automation], `AUTOMATION.md`):
   - **Ejemplo curado**: portar (parte de) `math16_32` a un bloque `ASM` multi-export
     (`examples/`), con su README, verificado en emulador.
   - **Manual** (`documentation/{es,en}/MANUAL_*.md`, fuente canónica en el REPO):
     sección "Ensamblador inline" — sintaxis `ASM/ENDASM/EXPORTS/USES`, ABI
     (`DE=FLAGS`, resultados por FLAGS), `cyd_abi.inc` (FLAGS, buffer de imagen,
     vídeo, arrays), servicios `CYD_SYSCALL`, broker de arrays (`MAP`/`FLUSH`/`PEEK`/
     `POKE`), `CYD_CALL`, la regla de oro y el límite de un banco. Aviso "avanzado, a
     tu propio riesgo".
   - **Tutorial** (vive SOLO en la wiki, `external/ChooseYourDestiny.wiki`): entrada
     introductoria como la de IMPORT/CALL.
   - **Regenerar PDFs** por WSL (pandoc + xelatex) y **sincronizar/pushear la wiki**
     (+ bump del submódulo en el repo padre).
   - **Resaltador** (repo aparte `chooseyourdestiny-highlighter`): keywords nuevas
     `ASM`/`ENDASM`/`EXPORTS`/`USES`/`CYD_CALL`, e idealmente resaltar el **cuerpo
     verbatim** como ensamblador (bloque embebido). Snippets `asm`/`call`. Bump de
     versión + VSIX + bump del submódulo en el repo principal. Igual que se hizo con
     `IMPORT`/`FROM`/`CALL` en v2.1.1.
   - Verificar en emulador en cada fase de código antes de dar nada por hecho.

---

## 14. Resumen de decisiones

- **Azúcar sobre EXTERN**: `ASM…ENDASM` = `IMPORT` con cuerpo inline; mismo `OP_EXTERN`,
  mismo `CALL`, misma colocación/handler.
- **Invocación**: rutina con nombre (no interleaving). `DE=FLAGS`, `ret`, resultados por
  FLAGS. Pila de enteros NO como canal de argumentos (es de bytes y comparte IX con
  GOSUB). Byte-push como extensión futura opcional.
- **ABI de datos**: `cyd_abi.inc` inyectado por build (FLAGS, buffer de imagen, vídeo,
  arrays). **Arrays irrenunciables**: broker `MAP`/`FLUSH` (uniforme, fast-path
  residente) + `PEEK`/`POKE`, scratch = `SAVE_FLAGS` (**0 bytes nuevos**).
- **Servicios del motor**: syscall numerada `CYD_SYSCALL` (curada, versionable).
- **Regla de oro**: la rutina nunca paginа `$C000`; todo cruce de banco por servicios
  residentes. El `CALL` bancado lo hace el handler residente y **compone** por el
  guardado del puerto por-nivel.
- **Rutina→rutina**: mismo bloque (multi-export, `call` intra-banco, sin banking) o
  `CYD_CALL` (trampolín residente, resuelto por índice + tabla de despacho + `USES`).
- **Banco propio** = RAM privada directa (código+tablas+`DEFS`), para datos >256 B;
  persiste entre CALLs (a verificar en mld128).
- **Limpieza `-dce`**: bloque conservado si ≥1 export es alcanzable (cierre transitivo
  por `USES`); si no, se descarta entero. Casi gratis: `extern_calls` ya es post-DCE.
  **Además, la maquinaria de la ABI se extirpa si no se usa** (§10.1): dispatcher
  `CYD_SYSCALL`, cada servicio y el broker de arrays van con guardas `UNUSED_*` y solo
  entran en el build si un bloque conservado los referencia.
- **v1**: un banco por rutina; `CYD_CALL` incluido; `COPY_FROM/TO_BANK` como avanzado.
