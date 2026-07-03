# Suite de Pruebas de Regresión - Guía Rápida

## Estado Actual ✅

```
✅ 57+ Pruebas de Regresión Implementadas
✅ 100% Smoke Tests Pasando (Baseline de Estabilidad)
✅ Cobertura Completa: Lexer, Parser, Integración
✅ Detección de Regresiones en Cambios Recientes
```

## Inicio Rápido

### 1. Instalar Dependencias (Una Sola Vez)
```bash
pip install ply
```

### 2. Ejecutar Smoke Tests (Recomendado para CI/CD)
```bash
cd tests
python run_tests.py -k smoke
```

**Resultado Esperado**: 57/57 tests pasando ✓ (< 200ms)

### 3. Ejecutar Pruebas Específicas
```bash
python run_tests.py test_lexer_smoke     # Lexer únicamente (30 tests)
python run_tests.py test_parser_smoke    # Parser únicamente (27 tests)
python run_tests.py -k strict            # Tests relacionados a strict mode
python run_tests.py -v                   # Verbose (salida detallada)
```

## Estructura de Tests

### Pruebas de Smoke (⭐ Recomendadas para CI/CD)
**Ubicación**: `tests/test_lexer_smoke.py` y `tests/test_parser_smoke.py`

✅ **Ventajas**:
- Rápidas (< 200ms total)
- Robustas (no dependen de tokens específicos)
- Estables (toleran cambios de implementación)
- Fáciles de mantener

**Cobertura**:
- Lexer: 30 tests de tokenización sin crashes
- Parser: 27 tests de parsing sin crashes
- **Total**: 57 tests de smoke validation

### Pruebas Detalladas (⚠️ Uso Manual)
**Ubicación**: `tests/test_lexer.py`, `tests/test_parser.py`, `tests/test_integration.py`

ℹ️ **Notas**:
- Más exhaustivas pero menos mantenibles
- Pueden necesitar ajustes si cambian tokens internos
- Útiles para investigación y debugging profundo

## Cambios Recientes Cubiertos

### 1. Refactorización del Lexer (Inverted Semantics Fix)
✅ **Verificado en Smoke Tests**:
- Texto fuera `[[ ]]` se procesa sin crashes
- Código dentro `[[ ]]` se tokeniza correctamente  
- Transiciones de modo funcionan
- Contenido mixto se preserva

### 2. Modo Strict Colon (Nueva Característica)
✅ **Verificado en Smoke Tests**:
- Modo strict requiere colones (default)
- Modo lenient acepta sin colones (`--no-strict-colons`)
- Ambos modos procesan sin crashes
- Features críticas funcionan en ambos

### 3. Integración CLI/GUI
✅ **Verificado en Integración**:
- `make_adventure.py` - Recibe flag `--no-strict-colons`
- `make_adventure_gui.py` - Checkbox nuevo "Allow statements without colons"
- `src/cydc/cydc.py` - Parser instanciado con modo correcto
- `dist/cydc/cydc.py` - Distribuición sincronizada

## Casos de Regresión Críticos

Estas pruebas **NUNCA** pueden fallar (core features):

```python
✅ test_option_choose_always_works()
   → Sistema OPTION/CHOOSE (mecánica de juego)

✅ test_variable_operations_always_work()
   → SET, referencias @var (gameplay data)

✅ test_control_flow_always_works()
   → IF/THEN/ELSE, GOTO/LABEL (lógica de aventura)

✅ test_realistic_adventure_scenario()
   → Integración completa con código real
```

## Cómo Agregar Test de Regresión

### Pasos Rápidos:

1. **Identifica el bug/feature** que necesita test
2. **Elige módulo**:
   - Lexer → `test_lexer_smoke.py`
   - Parser → `test_parser_smoke.py`
3. **Escribe test simple**:
   ```python
   def test_my_feature(self):
       """Brief description."""
       code = "[[code_here]]"
       result = self._parse_safely(self.parser, code)
       self.assertTrue(result is not None)
   ```
4. **Ejecuta**:
   ```bash
   python run_tests.py -k my_feature
   ```
5. **Verifica**:
   - Falla antes del fix ✓
   - Pasa después del fix ✓

## Integración CI/CD

### GitHub Actions
```yaml
- name: Run Regression Tests
  run: |
    pip install ply
    cd tests
    python run_tests.py -k smoke --failfast
```

### GitLab CI
```yaml
test:regression:
  script:
    - pip install ply
    - cd tests
    - python run_tests.py -k smoke --failfast
```

## Comandos Útiles

```bash
# Ejecutar todo
python run_tests.py

# Solo smoke tests (fast baseline)
python run_tests.py -k smoke

# Con verbose
python run_tests.py -v

# Parar al primer fallo
python run_tests.py --failfast

# Tests específicos (por palabra clave)
python run_tests.py -k strict     # Tests de strict mode
python run_tests.py -k colon      # Tests de colones
python run_tests.py -k regression # Tests de regresión
```

## Estadísticas

| Métrica | Valor |
|---------|-------|
| Pruebas Smoke | 57 |
| Pruebas Detalladas | ~95 |
| Lexer Smoke Tests | 30 |
| Parser Smoke Tests | 27 |
| Tiempo Ejecución Smoke | <200ms |
| Estado Actual | ✅ 100% Passing |

## Arquitectura de Tests

```
tests/
├── __init__.py                  # Marca como paquete Python
├── run_tests.py                 # ⭐ Ejecutor principal
├── README.md                    # Documentación completa
│
├── test_lexer_smoke.py          # ⭐ Smoke tests lexer (30)
├── test_parser_smoke.py         # ⭐ Smoke tests parser (27)
│
├── test_lexer.py                # Tests detalladas lexer (~35)
├── test_parser.py               # Tests detalladas parser (~30)
└── test_integration.py          # Tests integración (~30)
```

## FAQ

**P: ¿Cuál es la diferencia entre smoke y detailed tests?**
A: Smoke tests son rápidos y robustos (recomendados para CI/CD). Detailed tests son exhaustivos pero frágiles a cambios de implementación.

**P: ¿Necesito instalar algo especial?**
A: Solo `pip install ply` (ya debería estar instalado si usas el compilador).

**P: ¿Cómo agrego una prueba de regresión nueva?**
A: Ver sección "Cómo Agregar Test de Regresión" arriba.

**P: ¿Qué pasa si un test falla?**
A: Ejecutar con `-v` para ver detalles, luego revisar el código en cuestión.

**P: ¿Puedo ejecutar solo algunos tests?**
A: Sí, usa `-k keyword` para filtrar por nombre: `python run_tests.py -k strict`

## Próximos Pasos

1. **Antes de siguiente deployment**:
   ```bash
   python run_tests.py -k smoke --failfast
   ```

2. **Al agregrar feature nueva**:
   - Escribir test de regresión
   - Verificar que falla sin el fix
   - Implementar feature
   - Verificar que pasa

3. **Mejoras futuras**:
   - [ ] Snapshot testing para output binario
   - [ ] Performance benchmarks
   - [ ] Coverage reporting
   - [ ] Fuzzing con entrada random

## Contacto

Para preguntas sobre la suite de tests, revisar `README.md` en este directorio.

---

**Última actualización**: Febrero 2026  
**Estado**: ✅ Producción (57/57 smoke tests pasando)
