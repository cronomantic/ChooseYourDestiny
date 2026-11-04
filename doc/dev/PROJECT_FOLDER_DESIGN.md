# Carpeta de proyecto — diseño

> **Estado (4 nov 2026):** decisiones acordadas con Sergio. Nada implementado.

## Objetivo

Que cada juego viva en **su propia carpeta (el proyecto)** y se compile desde
ahí, en lugar de tener que estar en la raíz de la instalación (`CYD_HOME`).

## 1. El proyecto

- **Un proyecto es una carpeta** con el `.cyd` principal y todo lo del juego.
- **Es obligatorio.**
  - No se compila nada en la raíz de `CYD_HOME`.
  - Sus subcarpetas sí pueden ser proyectos: los ejemplos (`examples/<x>/`)
    lo son.
- **Configuración en `cyd_project.ini`**, un INI en la raíz del proyecto. Es
  opcional y tiene nombre fijo. Todas las rutas son relativas a la raíz del
  proyecto:

  ```ini
  ; Mi aventura
  [project]
  name = aventura
  main = aventura.cyd
  target = 128k

  [paths]
  images = IMAGES
  tracks = TRACKS
  sfx = SFX.ASM
  load_scr = IMAGES/LOAD.scr
  tokens = tokens.json
  charset = charset.json
  output = OUTPUT
  include_paths =
  lib_paths =
  import_paths =

  [options]
  image_lines = 192
  ```

  - Sin el fichero, valen los valores de este ejemplo.
  - El `target` es el que se usa por defecto; al compilar se puede elegir otro.
  - No contiene nada de la máquina ni del usuario: ni sjasmplus, ni el
    emulador, ni la apariencia.
  - **Detalles comprobados:**
    - Los `.cmd` pueden leerlo, pero no distinguen secciones, así que una clave
      no puede repetirse en dos secciones.
    - `configparser.write()` borra los comentarios, así que la GUI tiene que
      guardar línea a línea.

## 2. Búsqueda de ficheros

| Caso | Opción del compilador | Clave en el INI | Orden de búsqueda |
|---|---|---|---|
| `INCLUDE "x.cyd"` | `-I` / `--include-path CARPETA` | `include_paths` | junto al fichero → raíz del proyecto → estas carpetas |
| `INCLUDE LIB "x.cyd"` (nuevo) | `--lib-path CARPETA` | `lib_paths` | estas carpetas → `CYD_HOME/lib/` |
| `IMPORT … FROM "x.asm"` | `--import-path CARPETA` | `import_paths` | junto al fichero → `.cyd` principal (como ahora) → estas carpetas |

- **Varias carpetas:** las opciones se pueden repetir; en el INI se separan con
  `;`.
- **El primer paso de cada fila es el comportamiento actual,** así que lo que
  ya compila sigue compilando igual.
  - En `INCLUDE`, buscar junto al fichero.
  - En `IMPORT`, el `.cyd` principal (el paso nuevo, junto al fichero, va
    antes, pero solo cambia algo si el fichero existe en los dos sitios).
- **El mismo fichero incluido dos veces:**
  - con `INCLUDE LIB` las dos veces: la segunda no hace nada;
  - en cualquier otra combinación: error, con un mensaje que dice desde dónde
    se incluyó antes;
  - un ciclo de verdad sigue dando el error de include circular.
- **Ejemplos y manual** pasan de `INCLUDE "../../lib/x.cyd"` a
  `INCLUDE LIB "x.cyd"`.
- **Cuatro superficies:** `INCLUDE LIB` es sintaxis nueva, así que se aplica la
  regla de siempre (resaltador, manual, tutorial y wiki).

## 3. Mensajes del compilador

- **Formato:** `NIVEL [ETAPA] ruta:línea[:columna]: mensaje`. La ubicación va
  siempre al principio, como en gcc.
- **La ruta:**
  - es relativa a la raíz del proyecto y usa `/`;
  - para los ficheros de fuera del proyecto, se escribe con `../`;
  - solo se muestra absoluta cuando el fichero está en otra unidad.
- **Avisos de "nunca se usa":** no se dan en las carpetas de librerías.
- **Hay que cambiar:**
  - los 87 mensajes que hoy llevan la ubicación en mitad de la frase, y sus 77
    traducciones;
  - la expresión regular de la GUI y la del problemMatcher del resaltador.
    Comprobado que hoy fallan: las dos con espacios y con letra de unidad, y la
    del resaltador también con tildes.

## 4. Salida

- **La salida va a `OUTPUT/`.**
- **Los intermedios van a `OUTPUT/cyd_tmp/`:**
  - se borran si todo va bien y se conservan si falla;
  - con `--keep-temp` se conservan siempre;
  - son `cyd.sym`, `cyd.asm`, `cyd.lst` y, en +3, `DISK` y `NOMBRE.BIN`.
- **La caché de imágenes va a `OUTPUT/cyd_cache/`:**
  - lleva las líneas y la simetría en el nombre del fichero; así se corrige el
    fallo de hoy, que ignora `-il` e `images.json` (comprobado);
  - un `.csc` puesto a mano en `IMAGES/` sigue valiendo.

## 5. Ajustes globales de la GUI

- **Pasan a `CYD_HOME/cyd_gui_settings.ini`:** apariencia, sjasmplus, emulador
  y proyectos recientes.
- **El `cyd_gui_settings.json` actual** se lee una vez y se renombra a
  `.json.old`.

## 6. Documentación

- **Manual en/es:**
  - INCLUDE y librerías;
  - cómo generar una aventura;
  - ejemplos;
  - sección nueva: **"Migrar un juego de una versión anterior"**.
- **Tutorial en/es:** se corrige desde el principio, para que empiece creando
  un proyecto.
- **Raíz y distribución:** se quitan `test.cyd`, `tokens.json` y los
  `readme.txt` de `IMAGES/` y `TRACKS/`.

## 7. Propuestas sin confirmar

- `make_adventure.py --new CARPETA`, para crear un proyecto mínimo sin la GUI.
- Que `make_adv` acepte el proyecto como argumento. En Windows permitiría
  arrastrar la carpeta sobre el script.
- Cuando un `INCLUDE "lib/x.cyd"` antiguo no se encuentra, sugerir
  `INCLUDE LIB "x.cyd"`.
- Una pantalla de bienvenida en la GUI cuando no hay ningún proyecto abierto.
- Cómo encuentra el compilador `CYD_HOME`: por la variable de entorno o, si no
  existe, subiendo de carpeta hasta la que tenga `lib/` y `version.txt`.
- El `Makefile` de desarrollo: adaptarlo o retirarlo.

## 8. Fallos encontrados (independientes de este diseño) — ARREGLADOS

- Incluir el mismo fichero desde dos sitios daba "Circular include" aunque no
  hubiera ningún ciclo. Ahora el ciclo se detecta con la cadena de includes
  abiertos, y la repetición da "File already included from X:N"
  (`cydc_preprocessor.py`).
- `make_adventure.py` leía `-T`, `-t`, `-C` y `-c` pero no se los pasaba al
  compilador. Ahora los pasa, y el automatismo de `-tok` y `-chr` solo se
  aplica si no se dan.
- La pantalla de carga por defecto queda unificada en `IMAGES/LOAD.scr`, en
  `make_adventure.py`, los manuales y los tutoriales.
