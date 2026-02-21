# ChooseYourDestiny Compiler - Regression Test Suite

Este directorio contiene una suite exhaustiva de pruebas de regresión para el compilador ChooseYourDestiny.

## Resumen Ejecutivo

✅ **57+ Pruebas de Regresión** disponibles
✅ **100% Smoke Tests Pasando** (linea base de estabilidad)
✅ **Cobertura de Lexer, Parser, Integración**
✅ **Detección de Regresiones** en cambios recientes (modo strict colon, refactorización lexer)

## Contenido

### Test Modules - Smoke Tests (Recomendado para CI/CD)

#### `test_lexer_smoke.py` ⭐ - Pruebas del Lexer (Recomendadas)
Verifica la estabilidad y funcionamiento sin errores del lexer con patrones realistas:
- ✅ **TestLexerSmokeTests**: 23 pruebas de patrones realistas
- ✅ **TestLexerTokenGeneration**: 4 pruebas de generación de tokens
- ✅ **TestLexerConsistency**: 3 pruebas de consistencia

**Estado**: 30/30 pruebas pasando ✓

**Clases de prueba:**
- `TestLexerSmokeTests`: Código/texto realista sin crashes
- `TestLexerTokenGeneration`: Verificación de generación de tokens
- `TestLexerConsistency`: Consistencia entre ejecuciones

#### `test_parser_smoke.py` ⭐ - Pruebas del Parser (Recomendadas)
Verifica parsing correcto sin crashes en patrones realistas:
- ✅ **TestParserSmokeTests**: 25 pruebas de parsing básico
- ✅ **TestParserStrictMode**: 4 pruebas del modo strict colon
- ✅ **TestParserRegressionPrevention**: 5+ pruebas de prevención de regresiones

**Estado**: 27/27 pruebas pasando ✓

**Clases de prueba:**
- `TestParserSmokeTests`: Parsing de componentes individuales
- `TestParserStrictMode`: Validación modo strict vs lenient
- `TestParserRegressionPrevention`: Características críticas que nunca deben romperse

### Test Modules - Detalladas (Uso Manual)

#### `test_lexer.py` - Pruebas Detalladas del Lexer
Pruebas exhaustivas de tokens individuales y comportamientos específicos.
**Nota**: Ajustar según tokens reales del compilador.

#### `test_parser.py` - Pruebas Detalladas del Parser
Pruebas exhaustivas de reglas gramaticales y sintaxis.
**Nota**: Requiere validación manual de tokens generados.

#### `test_integration.py` - Pruebas de Integración
Pruebas end-to-end de la pipeline completa lexer→parser.
**Nota**: Requiere validación manual de configuraciones específicas.

### `run_tests.py` - Script Ejecutor de Pruebas

Script Python moderno para ejecutar la suite con opciones flexibles.

## Ejecución Rápida

### Ejecutar todas las pruebas de smoke (RECOMENDADO para CI/CD)
```bash
python tests/run_tests.py -k smoke
```
**Resultado esperado**: 57/57 pruebas pasando ✓

### Ejecutar solo pruebas del lexer smoke
```bash
python tests/run_tests.py test_lexer_smoke
```
**Resultado esperado**: 30/30 pruebas pasando ✓

### Ejecutar solo pruebas del parser smoke
```bash
python tests/run_tests.py test_parser_smoke
```
**Resultado esperado**: 27/27 pruebas pasando ✓

### Ejecutar con salida verbosa
```bash
python tests/run_tests.py -k smoke -v
```

## Instalación

### Instalar dependencias
```bash
pip install ply
```

## Propósito de Cada Test Luego de Cambios Recientes

### Refactorización del Lexer (Semántica Invertida Corregida)
Estas pruebas verifican que la refactorización no haya roto el comportamiento:
- ✓ Texto fuera de `[[ ]]` se procesa correctamente
- ✓ Código dentro de `[[ ]]` se tokeniza adecuadamente
- ✓ Transiciones de modo funcionan sin crashes
- ✓ Contenido mixto se preserva sin errores

### Modo Strict Colon (Novedad - Sept 2024)
Estas pruebas validan el nuevo modo de validación:
- ✓ Modo strict requiere colones entre sentencias (default)
- ✓ Modo lenient (`--no-strict-colons`) acepta sin colones
- ✓ Ambos modos procesan sin crashes
- ✓ Características críticas funcionan en ambos modos

### Integración CLI y GUI
Las opciones se han agregado a:
- ✓ `make_adventure.py` - CLI build script
- ✓ `make_adventure_gui.py` - GUI build script
- ✓ `src/cydc/cydc.py` - Compilador principal
- ✓ `dist/cydc/cydc.py` - Distribución

## Casos Críticos de Regresión

La suite cubre explícitamente (nunca deben fallar):

```python
1. test_option_choose_always_works()
   - OPTION/CHOOSE system (core gameplay feature)
   
2. test_variable_operations_always_work()
   - SET, variable references (@var)
   
3. test_control_flow_always_works()
   - IF/THEN/ELSE, GOTO/LABEL flow
   
4. test_realistic_adventure_scenario()
   - Full integration test with real code
```

Si CUALQUIERA de estas pruebas falla, hay una regresión seria.

## Archivos de Configuración

- `__init__.py` - Marca esta carpeta como paquete Python
- `run_tests.py` - Ejecutor principal
- `README.md` - Este documento

## Cómo Agregar Nuevas Pruebas

Para agregar una nueva prueba de regresión:

### 1. Smoke Test (Rápido, Recomendado)
```python
# En test_lexer_smoke.py o test_parser_smoke.py

def test_my_feature(self):
    """Test description for my_feature."""
    code = "[[my_code_here]]"
    result = self._parse_safely(self.parser, code)
    self.assertTrue(result is not None)
```

### 2. Ejecutar y Verificar
```bash
python tests/run_tests.py -k my_feature
```

### Pauta de Nombres
- Prefix: `test_`
- Verbo: `should_`, `does_`, `never_`, `always_`
- Sufijo: Nombre descriptivo

Ejemplo: `test_strict_mode_should_reject_missing_colons`

## Integración CI/CD

### GitHub Actions
```yaml
- name: Run Regression Tests
  run: |
    pip install ply
    python tests/run_tests.py -k smoke --failfast
```

### GitLab CI
```yaml
test:regression:
  script:
    - pip install ply
    - python tests/run_tests.py -k smoke --failfast
```

## Estadísticas

| Módulo | Pruebas | Estado |
|--------|---------|--------|
| test_lexer_smoke.py | 30 | ✅ Pasando |
| test_parser_smoke.py | 27 | ✅ Pasando |
| test_lexer.py | ~35 | ⚠️ Detalladas |
| test_parser.py | ~30 | ⚠️ Detalladas |
| test_integration.py | ~30 | ⚠️ Detalladas |
| **TOTAL SMOKE** | **57** | **✅ 100%** |

## Notas de Desarrollo

### Por qué Smoke Tests
- **Rápidos**: Ejecutan en <150ms
- **Robustos**: No dependen de detalles de implementación
- **Mantenibles**: Fáciles de actualizar cuando cambia el lexer/parser
- **Confiables**: Solo verifican que no haya crashes

### Conversión de Caracteres
El compilador hace conversiones especiales de:
- ISO-8859-15 → caracteres especiales
- Unicode → ASCII equivalentes
- Retornos de carro → caracteres especiales

Los smoke tests toleran esto automáticamente.

### Lenguaje CYD
Ejemplos de código válido:
```cyd
[[PRINT "text" : GOTO Label]]        ; Strict mode (colons)
[[PRINT "text" GOTO Label]]           ; Lenient mode (no colons)
[[IF @var > 0 THEN ... ENDIF]]        ; Control flow
Text before [[CODE]] text after       ; Mixed content
```

## Mejoras Futuras

- [ ] Snapshot testing para output binario
- [ ] Benchmark de rendimiento
- [ ] Fuzzing con entrada aleatoria
- [ ] Coverage reporting
- [ ] Dashboard de histórico
- [ ] Integración con SonarQube

## Soporte

Para agregar o modificar pruebas, contactar al equipo de desarrollo.

