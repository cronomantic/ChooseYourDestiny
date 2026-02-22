# Sistema de Automatización de ChooseYourDestiny

Este documento describe el sistema de automatización que simplifica las tareas comunes de desarrollo y lanzamiento.

## Tabla de Contenidos

- [Requisitos](#requisitos)
- [Script Principal: automate.py](#script-principal-automatepy)
- [Scripts Individuales](#scripts-individuales)
  - [update_locales.py](#update_localespy)
  - [make_pdf.bat / make_pdf.sh](#make_pdfbat--make_pdfsh)
  - [update_wiki.py](#update_wikipy)
  - [tests/run_tests.py](#testsrun_testspy)
  - [make_dist.py](#make_distpy)
- [Flujos de Trabajo Comunes](#flujos-de-trabajo-comunes)
- [Resolución de Problemas](#resolución-de-problemas)

---

## Requisitos

### Todos los Sistemas

- Python 3.11 o superior
- Git (para actualizar la wiki)

### Windows

- Pandoc con Tectonic (incluido en `tools/pandoc/`)
- Python embebido (incluido en `dist/python/`)

### Linux/macOS

- Pandoc: `sudo apt install pandoc texlive-latex-base texlive-latex-extra` (Ubuntu/Debian)
- Pandoc: `sudo dnf install pandoc texlive-scheme-medium` (Fedora)
- Pandoc: `brew install pandoc basictex` (macOS)
- Bash shell

---

## Script Principal: automate.py

El script `automate.py` es el punto de entrada unificado para todas las tareas de automatización.

### Uso Básico

```bash
python automate.py [opciones]
```

### Opciones Disponibles

#### Tareas Individuales

- `--locales` - Actualizar archivos de traducción (.po) desde el código fuente
- `--tests` - Ejecutar suite de tests de regresión
- `--pdf` - Generar documentación PDF (manual + tutorial, EN/ES)
- `--dist` - Crear paquetes de distribución
- `--wiki` - Actualizar GitHub Wiki

#### Flujos de Trabajo Combinados

- `--all` - Ejecutar todas las tareas excepto actualizar wiki
- `--release` - Flujo completo de lanzamiento (incluye wiki)

#### Opciones Adicionales

- `--platform {windows|linux|macos|all}` - Plataforma objetivo para distribución

### Ejemplos de Uso

```bash
# Actualizar traducciones y ejecutar tests
python automate.py --locales --tests

# Generar PDFs y crear distribución para Windows
python automate.py --pdf --dist --platform windows

# Flujo completo de desarrollo (sin wiki)
python automate.py --all

# Flujo completo de lanzamiento
python automate.py --release

# Crear distribuciones para todas las plataformas
python automate.py --dist --platform all
```

### Secuencia de Ejecución

Cuando se ejecutan múltiples tareas, se procesan en este orden:

1. **Actualizar locales** (`--locales`)
   - Extrae cadenas traducibles del código fuente Python
   - Actualiza archivos .po preservando traducciones existentes
   - Compila .po a .mo automáticamente

2. **Ejecutar tests** (`--tests`)
   - Tests del lexer (análisis léxico)
   - Tests del parser (análisis sintáctico)
   - Tests de integración (compilación completa)
   - Genera reporte de cobertura si está disponible

3. **Generar PDFs** (`--pdf`)
   - MANUAL_es.pdf y MANUAL_en.pdf
   - TUTORIAL_es.pdf y TUTORIAL_en.pdf
   - Incluye tabla de contenidos automática

4. **Crear distribuciones** (`--dist`)
   - Copia archivos fuente a dist/
   - Compila traducciones
   - Crea ZIP con nombramiento automático basado en versión git
   - Soporta Windows, Linux y macOS

5. **Actualizar wiki** (`--wiki`)
   - Verifica cambios en repositorio wiki
   - Solicita confirmación antes de hacer commit
   - Hace push a GitHub

---

## Scripts Individuales

### update_locales.py

Extrae cadenas traducibles del código fuente y actualiza archivos .po.

**Ubicación:** Raíz del proyecto

**Uso:**
```bash
python update_locales.py
```

**Qué hace:**
1. Escanea archivos Python buscando llamadas a `_("string")`
2. Actualiza archivos .po en:
   - `locale/es/LC_MESSAGES/make_adventure.po`
   - `locale/es/LC_MESSAGES/make_adventure_gui.po`
   - `src/cydc/cydc/locale/es/LC_MESSAGES/cydc.po`
   - `src/cydc/locale/es/LC_MESSAGES/cyd_font_conv.po`
3. Preserva traducciones existentes
4. Añade nuevas cadenas sin traducir

**Después de ejecutar:**
- Revisa los archivos .po actualizados
- Añade/actualiza traducciones al español para cadenas nuevas
- Ejecuta `make_dist.py` para compilar .po a .mo

**Archivos procesados:**
- `make_adventure.py`
- `make_adventure_gui.py`
- `src/cydc/cydc/cydc.py`
- `src/cydc/cydc/cydc_parser.py`
- `src/cydc/cydc/cydc_lexer.py`
- `src/cydc/cyd_chr_conv.py`

---

### make_pdf.bat / make_pdf.sh

Genera documentación PDF desde archivos Markdown.

**Ubicación:** Raíz del proyecto

**Uso:**
```batch
REM Windows
make_pdf.bat

# Linux/macOS
./make_pdf.sh
```

**Requisitos:**
- Repositorio wiki clonado como directorio hermano: `../ChooseYourDestiny.wiki/`
- Windows: Pandoc incluido en `tools/pandoc/`
- Linux/macOS: Pandoc y LaTeX instalados en el sistema

**PDFs generados:**
- `documentation/es/MANUAL_es.pdf`
- `documentation/es/TUTORIAL_es.pdf`
- `documentation/en/MANUAL_en.pdf`
- `documentation/en/TUTORIAL_en.pdf`

**Características:**
- Márgenes de 1 pulgada
- Tabla de contenidos automática
- Motor LaTeX: Tectonic (Windows) o auto-detectado (Linux/macOS)

**Clonar repositorio wiki:**
```bash
cd ..
git clone https://github.com/cronomantic/ChooseYourDestiny.wiki.git
```

---

### update_wiki.py

Sincroniza documentación con el repositorio GitHub Wiki.

**Ubicación:** Raíz del proyecto

**Uso:**
```bash
python update_wiki.py
```

**Qué hace:**
1. Verifica que el repositorio wiki esté clonado
2. Detecta cambios en archivos de documentación
3. Muestra un diff de los cambios
4. Solicita confirmación del usuario
5. Hace commit y push al repositorio wiki

**Requisitos:**
- Repositorio wiki clonado en `../ChooseYourDestiny.wiki/`
- Permisos de escritura en el repositorio wiki de GitHub
- Git configurado con credenciales

**Archivos sincronizados:**
- `MANUAL_es.md`
- `MANUAL_en.md`
- `TUTORIAL_es.md`
- `TUTORIAL_en.md`

**Nota:** Este script **NO** copia archivos desde el repositorio principal. Los archivos ya deben estar en el repositorio wiki. El script solo detecta cambios y los publica.

---

### tests/run_tests.py

Ejecuta la suite completa de tests de regresión.

**Ubicación:** `tests/run_tests.py`

**Uso:**
```bash
# Ejecutar todos los tests
python tests/run_tests.py

# Modo verbose
python tests/run_tests.py -v

# Ejecutar módulo específico
python tests/run_tests.py test_lexer

# Ejecutar tests que coincidan con patrón
python tests/run_tests.py -k test_strict

# Generar reporte de cobertura
python tests/run_tests.py --coverage
```

**Categorías de tests:**
- **test_lexer.py** - Tests del análisis léxico (tokenización)
- **test_lexer_smoke.py** - Tests rápidos del lexer
- **test_parser.py** - Tests del análisis sintáctico
- **test_parser_smoke.py** - Tests rápidos del parser
- **test_integration.py** - Tests de la pipeline completa
- **test_preprocessor.py** - Tests del sistema INCLUDE

**Estadísticas reportadas:**
- Número de tests ejecutados
- Tests pasados/fallados/omitidos
- Tiempo de ejecución
- Cobertura de código (si está instalado `coverage`)

**Ver documentación completa:**
```bash
cd tests
cat README.md
```

---

### make_dist.py

Crea paquetes de distribución para múltiples plataformas.

**Ubicación:** Raíz del proyecto

**Uso:**
```bash
# Crear distribución para plataforma actual
python make_dist.py

# Crear para plataforma específica
python make_dist.py --platform windows
python make_dist.py --platform linux
python make_dist.py --platform macos

# Crear para todas las plataformas
python make_dist.py --all

# Solo compilar, sin crear ZIP
python make_dist.py --skip-compile
```

**Proceso:**
1. Copia archivos fuente de `src/cydc/` a `dist/`
2. Compila traducciones (.po → .mo)
3. Recopila archivos específicos de plataforma
4. Obtiene versión desde git tags
5. Crea archivo ZIP con nombre versionado

**Archivos incluidos:**
- Runtime de Python (solo Windows: `dist/python/`)
- Código fuente del compilador (`dist/cydc/`)
- Scripts de construcción (`make_adv.*`, `make_adventure_gui.*`)
- Herramientas (`sjasmplus`, `csc`)
- Ejemplos (`examples/`)
- Documentación PDF (`documentation/`)
- Archivos de traducción (`locale/`)
- Assets (`assets/`, `IMAGES/`, `TRACKS/`)

**Nombre del ZIP generado:**
```
ChooseYourDestiny_{Platform}_{Arch}_v{version}_{date}.zip

Ejemplo:
ChooseYourDestiny_Win_x64_v1_2_1_2026_02_21.zip
```

**Ver documentación completa:**
```bash
cat DISTRIBUTION.md
```

---

## Flujos de Trabajo Comunes

### Desarrollo Diario

```bash
# Después de modificar código con strings traducibles
python automate.py --locales

# Ejecutar tests antes de hacer commit
python automate.py --tests
```

### Antes de Hacer un Pull Request

```bash
# Asegurar que todo funciona
python automate.py --all
```

### Preparar un Lanzamiento

```bash
# 1. Actualizar versión en git
git tag v1.3.0
git push --tags

# 2. Ejecutar flujo completo de lanzamiento
python automate.py --release --platform all

# 3. Verificar PDFs generados
ls -la documentation/

# 4. Verificar distribuciones creadas
ls -la ChooseYourDestiny_*.zip
```

### Solo Generar Documentación

```bash
# PDFs y wiki
python automate.py --pdf --wiki
```

### Actualizar Solo Traducciones

```bash
# 1. Actualizar archivos .po
python update_locales.py

# 2. Editar manualmente los .po para añadir traducciones
# (Usar editor de texto o herramienta como Poedit)

# 3. Compilar a .mo y crear distribución
python automate.py --dist
```

---

## Resolución de Problemas

### Error: "pandoc is not installed"

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-latex-base texlive-latex-extra

# Fedora
sudo dnf install pandoc texlive-scheme-medium

# macOS
brew install pandoc basictex
```

**Windows:** Debería estar incluido en `tools/pandoc/`. Si falta, descarga desde [pandoc.org](https://pandoc.org/).

### Error: "Wiki directory not found"

Clona el repositorio wiki:
```bash
cd ..
git clone https://github.com/cronomantic/ChooseYourDestiny.wiki.git
cd ChooseYourDestiny
```

### Error: "Permission denied" en scripts .sh

Haz los scripts ejecutables:
```bash
chmod +x make_pdf.sh
chmod +x make_adv.sh
chmod +x make_adventure_gui.sh
```

### Tests fallan después de cambios en gramática

1. Verifica que los cambios en la gramática sean intencionales
2. Actualiza los tests para reflejar el nuevo comportamiento
3. Si añadiste nuevas palabras clave, actualiza `test_lexer.py`
4. Si cambiaste la sintaxis, actualiza `test_parser.py`

### Error: "No module named 'coverage'"

Instala el paquete opcional de cobertura:
```bash
pip install coverage
```

O ejecuta tests sin cobertura:
```bash
python tests/run_tests.py
```

### PDFs no se generan correctamente

**Verifica que el repositorio wiki esté actualizado:**
```bash
cd ../ChooseYourDestiny.wiki
git pull
cd ../ChooseYourDestiny
```

**Verifica sintaxis Markdown:**
- Los archivos .md deben tener sintaxis válida
- Las imágenes deben existir en el directorio `assets/`

### Distribución no incluye nuevos archivos

Edita `make_dist.py` y añade los archivos a:
- `get_source_files()` - Archivos fuente del compilador
- `get_common_files()` - Archivos comunes a todas las plataformas
- `get_platform_specific_files()` - Archivos específicos de plataforma

---

## Notas Adicionales

### Orden de Ejecución Recomendado para Lanzamientos

1. Tests → 2. Locales → 3. PDFs → 4. Distribuciones → 5. Wiki

El comando `--release` ya hace esto automáticamente.

### Archivos Generados (añadir a .gitignore si es necesario)

- `*.zip` - Paquetes de distribución
- `documentation/**/*.pdf` - PDFs generados
- `**/*.mo` - Archivos de traducción compilados
- `tests/__pycache__/` - Cache de Python
- `dist/cydc/parser.out` - Archivos generados por PLY
- `dist/cydc/parsetab.py` - Tabla de parsing generada

### Compatibilidad

- **Windows:** Probado en Windows 10/11
- **Linux:** Probado en Ubuntu 20.04+, Debian 11+, Fedora 35+
- **macOS:** Probado en macOS 11+ (Big Sur y superiores)

### Backup Antes de Automatización

Se recomienda hacer backup de:
- Archivos `.po` personalizados antes de ejecutar `--locales`
- Repositorio wiki antes de ejecutar `--wiki`
- Archivos de configuración personalizados

---

## Soporte

Para problemas o preguntas:
- GitHub Issues: https://github.com/cronomantic/ChooseYourDestiny/issues
- Wiki: https://github.com/cronomantic/ChooseYourDestiny/wiki

---

**Última actualización:** Febrero 2026  
**Versión del sistema:** 1.0
