# Evaluación: ¿migrar el parser de PLY a Lark?

> Pregunta explícita de Sergio. Es una decisión de **arquitectura**: no se migra sin
> acuerdo. Este documento pesa el coste real (medido en el código, no de memoria) y da
> un **veredicto**.
>
> **Veredicto: NO migrar. Quedarse con PLY.** El coste es alto y no mecánico; el
> beneficio es marginal y en parte negativo (habría que *reconstruir* capacidades que
> hoy ya funcionan); y Lark sería una **dependencia externa nueva**, contra
> [[feedback-minimize-external-tooling]]. Detalle abajo.

---

## 1. Cómo es el front-end hoy (cifras verificadas)

| Módulo | Tamaño | Datos |
|---|---|---|
| `cydc_lexer.py` | 573 líneas | **142 tokens** (104 keywords + 38 base); **42 reglas** `t_*`; **2 estados** (`INITIAL` + exclusivo `rawtext`) |
| `cydc_parser.py` | 3486 líneas | **192 funciones `p_*`**; **376 alternativas de producción / 47 no-terminales**; `precedence` de 6 niveles |
| `cydc_codegen.py` | 1533 líneas | **128 opcodes**; consume una **lista plana de tuplas** `(TAG, *operandos)` |

- **PLY está vendorizado en el repo** (`src/cydc/cydc/ply/`, `lex.py` 901 líneas +
  `yacc.py` 2482). No hay dependencia externa que fijar.
- **No hay caché de tabla LALR en disco.** El PLY vendorizado en `src` es una versión
  modernizada: `yacc.yacc(module=self)` **construye la tabla LALR en memoria en cada
  ejecución**; no escribe `parsetab.py` ni `parser.out`. (El `parsetab.py` que aparece
  en `dist/cydc/` es un artefacto congelado de un PLY más viejo, no lo consume el
  compilador de `src`.) → **cero coste de mantenimiento de tablas hoy.**

---

## 2. El coste de migrar (por qué NO es mecánico)

### 2.1 El parser hace *lowering*, no construye un AST

Las 191 acciones con gramática **emiten código destino directamente como tuplas**, no un
árbol. Ejemplo, `p_loop_while_statement` genera in situ
`[("LABEL",…), ("IF_N_GOTO",label,0,0), ("GOTO",label,0,0), ("LABEL",…)]`. En las
acciones vive:

- **Desazucarado** de `FOR`/`WHILE`/`DO`/`SELECT` a saltos + labels.
- **Generación de labels ocultas** (`_get_hidden_label`).
- **Validación semántica** (`_check_byte_value`, `_check_word_value`, tabla de símbolos
  `self.symbols`), con ~90 `self.errors.append(...)`.
- **114 tags de tupla literales distintos** emitidos por las acciones.

Migrar a Lark (que produce un árbol) obliga a **reescribir toda esta capa de lowering**
como una pasada de transformación aparte. No es traducir gramática: es rehacer el
compilador intermedio.

### 2.2 Construcciones sin equivalente 1:1 en Lark

- **Lexer con estado exclusivo `rawtext`** (texto fuera de `[[ ]]`) + **`t_rawtext_eof`**
  (Lark no tiene hook de token EOF) + ignores/errores por estado (3 manejadores).
- **Captura cruda de `ASM…ENDASM`** leyendo/escribiendo `t.lexer.lexdata/lexpos/lineno`
  directamente (`_capture_asm_body`, lexer:358-395): salta el tokenizador para extraer
  el cuerpo verbatim. Es el constructo más difícil de portar.
- **`p_error` que introspecciona `self.parser.symstack`** para contar IF/ENDIF,
  WHILE/WEND, DO/UNTIL y emitir *"Missing ENDIF/WEND/UNTIL"* (parser:3053-3107), con
  recuperación vía `parser.token()`/`errok()`. Lark usa excepciones
  (`UnexpectedToken`) y otro modelo de recuperación: **estos diagnósticos habría que
  reconstruirlos desde cero**, con más esfuerzo del que costó tenerlos.

### 2.3 Tests acoplados a la forma exacta de salida

- `test_parser.py:102` fija la tupla exacta: `assertIn(("EXTERN","peek",0,0), result)`.
- `test_lexer.py` depende de **nombres de token** (30+ asserts sobre `"GOTO"`,
  `"PRINT"`, `"TEXT"`, `"COLON"`…): las 142 etiquetas deben preservarse.
- Dependencia de la subcadena `"colon"` en el diagnóstico de colon-estricto.

Un cambio en la forma del árbol/tupla rompe estos tests directamente.

### 2.4 El límite de migración que SÍ protege

La única frontera limpia: **codegen depende solo del protocolo de tuplas
`(TAG, *operandos)`, no de PLY**. Si un port reprodujera idéntica la lista de tuplas,
codegen (1533 líneas) y los consumidores en `cydc.py` no cambian. Pero eso **no reduce**
el coste del parser: solo evita tocar codegen. El grueso (gramática + lowering +
diagnósticos + lexer de estados/ASM) sigue siendo reescritura completa.

---

## 3. Balance riesgo / beneficio

| | PLY (hoy) | Lark (migrado) |
|---|---|---|
| Dependencia | vendorizada, Python puro, sin caché a disco | **dep externa nueva** (contra la norma del proyecto) |
| Mensajes de error | específicos (cuenta IF/ENDIF, colon, etc.), ya funcionando | habría que **reconstruirlos** (Earley/LALR de Lark, otro modelo) |
| Gramática declarativa (EBNF) | no (docstrings) | sí — **único beneficio real**, pero marginal para una gramática ya estable |
| Coste de migración | 0 | **376 producciones + 191 acciones de lowering + lexer de estados + captura ASM + p_error**; rehacer tests |
| Riesgo de regresión | 0 | alto (todo el front-end tocado a la vez) |
| Rendimiento | tabla LALR en memoria, suficiente | Earley más lento; LALR similar |

El único beneficio tangible de Lark —gramática declarativa EBNF y errores "de fábrica"—
no compensa: la gramática CYD ya está estable y **los errores de CYD ya son mejores que
los genéricos de Lark** (introspección de bloques sin cerrar). Se pagaría una
reescritura grande para, en el mejor caso, empatar.

---

## 4. Veredicto y alternativa

**No migrar.** Mantener PLY vendorizado. Es la opción coherente con
[[feedback-minimize-external-tooling]] (sin deps nuevas), tiene coste de mantenimiento
actual nulo (tabla en memoria, sin binarios) y evita un riesgo de regresión grande en
la pieza más delicada del compilador.

**Si en el futuro se quiere mejorar el front-end**, invertir *dentro* de PLY:
- Mejores mensajes de error (ya hay base sólida en `p_error`).
- Refactor opcional: extraer el lowering de las acciones a una pasada separada (haría el
  parser más limpio **y**, de paso, dejaría el front-end mejor preparado por si algún
  día se reconsidera Lark — pero eso es valor por sí mismo, no una migración).

**Cuándo reconsiderar Lark (gatillos concretos):**
- Que el PLY vendorizado deje de funcionar con una versión futura de Python (improbable:
  es Python puro y está congelado en el repo).
- Que se necesite una gramática **ambigua / GLR / Earley** que LALR(1) no pueda expresar
  (no es el caso: la gramática CYD es LALR limpia).
- Que el port CPC ([MULTITARGET_DESIGN §9](../../MULTITARGET_DESIGN.md)) —que sí toca el
  front-end para hacerlo "target-aware"— revele que el superset de gramática es
  inmanejable en PLY (poco probable; el diseño actual lo resuelve con gating post-parse).

Ninguno de esos gatillos está activo hoy.
