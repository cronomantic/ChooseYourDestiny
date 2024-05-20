# Manual de Choose Your Destiny

![logo](assets/cyddeluxe_small.png)

El programa es un compilador e intérprete para ejecutar historias de tipo "Escoge tu propia aventura" o aventuras por opciones y libro juegos, para el Spectrum 48, 128, +2 y +3.

Consiste una máquina virtual que va interpretando comandos que se encuentra durante el texto para realizar las distintas acciones interactivas y un compilador que se encarga de traducir la aventura desde un lenguaje similar a BASIC, con el que se escribe el guion de la aventura, a un fichero interpretable por el motor.

Además, también puede mostrar imágenes comprimidas y almacenadas en el mismo disco, así como efectos de sonido basados en BeepFX de Shiru y melodías tipo PT3 creadas con Vortex Tracker.

- [Manual de Choose Your Destiny](#manual-de-choose-your-destiny)
  - [Requerimientos e Instalación](#requerimientos-e-instalación)
    - [Windows](#windows)
    - [Linux, BSDs y compatibles (Experimental)](#linux-bsds-y-compatibles-experimental)
  - [CYDC (Compilador)](#cydc-compilador)
  - [CSC (Compresor de Imágenes)](#csc-compresor-de-imágenes)
  - [CYD Character Set Converter](#cyd-character-set-converter)
  - [Sintaxis Básica](#sintaxis-básica)
  - [Flags y expresiones numéricas](#flags-y-expresiones-numéricas)
  - [Control de flujo y expresiones condicionales](#control-de-flujo-y-expresiones-condicionales)
  - [Asignaciones e indirección](#asignaciones-e-indirección)
  - [Listado de comandos](#listado-de-comandos)
    - [**NOTA IMPORTANTE PARA USUARIOS DE VERSIONES ANTERIORES A v0.7**](#nota-importante-para-usuarios-de-versiones-anteriores-a-v07)
    - [LABEL ID](#label-id)
    - [#ID](#id)
    - [DECLARE expression AS ID](#declare-expression-as-id)
    - [GOTO ID](#goto-id)
    - [GOSUB ID](#gosub-id)
    - [RETURN](#return)
    - [IF condexpression THEN ... ENDIF](#if-condexpression-then--endif)
    - [IF condexpression THEN ... ELSE ... ENDIF](#if-condexpression-then--else--endif)
    - [IF condexpression1 THEN ... ELIF condexpression2 THEN ... ELSE ... ENDIF](#if-condexpression1-then--elif-condexpression2-then--else--endif)
    - [WHILE (condexpression) ... WEND](#while-condexpression--wend)
    - [SET varID TO numexpression](#set-varid-to-numexpression)
    - [SET \[varID\] TO numexpression](#set-varid-to-numexpression-1)
    - [SET varID TO {numexpression1, numexpression2,...}](#set-varid-to-numexpression1-numexpression2)
    - [SET \[varID\] TO {numexpression1, numexpression2,...}](#set-varid-to-numexpression1-numexpression2-1)
    - [LET varID = numexpression](#let-varid--numexpression)
    - [LET \[varID\] = numexpression](#let-varid--numexpression-1)
    - [LET varID = {numexpression1, numexpression2,...}](#let-varid--numexpression1-numexpression2)
    - [LET \[varID\] = {numexpression1, numexpression2,...}](#let-varid--numexpression1-numexpression2-1)
    - [END](#end)
    - [CLEAR](#clear)
    - [CENTER](#center)
    - [WAITKEY](#waitkey)
    - [OPTION GOTO ID](#option-goto-id)
    - [OPTION GOSUB ID](#option-gosub-id)
    - [CHOOSE](#choose)
    - [CHOOSE IF WAIT expression THEN GOTO ID](#choose-if-wait-expression-then-goto-id)
    - [CHOOSE IF CHANGED THEN GOSUB ID](#choose-if-changed-then-gosub-id)
    - [OPTIONSEL()](#optionsel)
    - [NUMOPTIONS()](#numoptions)
    - [CLEAROPTIONS](#clearoptions)
    - [MENUCONFIG numexpression, numexpression](#menuconfig-numexpression-numexpression)
    - [CHAR numexpression](#char-numexpression)
    - [REPCHAR expression, expression](#repchar-expression-expression)
    - [TAB expression](#tab-expression)
    - [PRINT numexpression](#print-numexpression)
    - [PAGEPAUSE expression](#pagepause-expression)
    - [INK numexpression](#ink-numexpression)
    - [PAPER numexpression](#paper-numexpression)
    - [BORDER numexpression](#border-numexpression)
    - [BRIGHT numexpression](#bright-numexpression)
    - [FLASH numexpression](#flash-numexpression)
    - [NEWLINE expression](#newline-expression)
    - [NEWLINE](#newline)
    - [BACKSPACE expression](#backspace-expression)
    - [BACKSPACE](#backspace)
    - [SFX numexpression](#sfx-numexpression)
    - [PICTURE numexpression](#picture-numexpression)
    - [DISPLAY numexpression](#display-numexpression)
    - [BLIT expression, expression, expression, expression AT numexpression, numexpression](#blit-expression-expression-expression-expression-at-numexpression-numexpression)
    - [WAIT expression](#wait-expression)
    - [PAUSE expression](#pause-expression)
    - [TYPERATE expression](#typerate-expression)
    - [MARGINS expression, expression, expression, expression](#margins-expression-expression-expression-expression)
    - [FADEOUT  expression, expression, expression, expression](#fadeout--expression-expression-expression-expression)
    - [AT numexpression, numexpression](#at-numexpression-numexpression)
    - [FILLATTR expression, expression, expression, expression, expression, expression, expression, expression](#fillattr-expression-expression-expression-expression-expression-expression-expression-expression)
    - [PUTATTR numexpression, numexpression, expression, expression, expression, expression](#putattr-numexpression-numexpression-expression-expression-expression-expression)
    - [GETATTR (numexpression, numexpression)](#getattr-numexpression-numexpression)
    - [RANDOM(expression)](#randomexpression)
    - [RANDOM()](#random)
    - [RANDOM(expression, expression)](#randomexpression-expression)
    - [INKEY(expression)](#inkeyexpression)
    - [INKEY()](#inkey)
    - [MIN(numexpression,numexpression)](#minnumexpressionnumexpression)
    - [MAX(numexpression,numexpression)](#maxnumexpressionnumexpression)
    - [YPOS()](#ypos)
    - [XPOS()](#xpos)
    - [RANDOMIZE](#randomize)
    - [TRACK numexpression](#track-numexpression)
    - [PLAY numexpression](#play-numexpression)
    - [LOOP numexpression](#loop-numexpression)
    - [RAMSAVE varID, expression](#ramsave-varid-expression)
    - [RAMSAVE varID](#ramsave-varid)
    - [RAMSAVE](#ramsave)
    - [RAMLOAD varID, expression](#ramload-varid-expression)
    - [RAMLOAD varID](#ramload-varid)
    - [RAMLOAD](#ramload)
    - [SAVE numexpression, varId, expression](#save-numexpression-varid-expression)
    - [SAVE numexpression, varId](#save-numexpression-varid)
    - [SAVE numexpression](#save-numexpression)
    - [LOAD numexpression](#load-numexpression)
    - [SAVERESULT()](#saveresult)
    - [ISDISK()](#isdisk)
  - [Imágenes](#imágenes)
  - [Efectos de sonido](#efectos-de-sonido)
  - [Melodías](#melodías)
  - [Cómo generar una aventura](#cómo-generar-una-aventura)
    - [Windows](#windows-1)
    - [Linux, BSDs](#linux-bsds)
  - [Ejemplos](#ejemplos)
  - [Juego de caracteres](#juego-de-caracteres)
  - [Códigos de error](#códigos-de-error)
  - [F.A.Q](#faq)
  - [Referencias y agradecimientos](#referencias-y-agradecimientos)
  - [Licencia](#licencia)

---

## Requerimientos e Instalación

Estos son los requerimientos externos de la herramienta:

- [Python 3.11 o superior](https://www.python.org/)
- [SjAsmPlus 1.20.3 o superior](http://z00m128.github.io/sjasmplus/documentation.html)
- [TAPTOOLS 1.0.8 o superior](http://www.seasip.info/ZX/unix.html), para ser más exactos la utilidad `mkp3fs`.
- Descompresor de ficheros ZIP

Si se actualiza una versión más antigua, es recomendable NO sobrescribirla. Es mejor renombrar el directorio de la versión antigua, descomprimir la nueva versión, copiar los archivos de tu aventura a la nueva versión y configurar de nuevo el guion `make_adv` para cada caso.

Estas son las instrucciones más detalladas para cada sistema operativo:

### Windows

La instalación es sencilla, simplemente descomprimir el fichero ZIP correspondiente descargado de la sección [Releases](https://github.com/cronomantic/ChooseYourDestiny/releases) del repositorio. En este caso, está todo incluido en el paquete. Se requiere Windows 10 o superior, versión de 64 bits (32 bits no soportados).

### Linux, BSDs y compatibles (Experimental)

Para estos sistemas, los requerimientos son:

- GNU/Linux / Unix / macOS / BSD con shell compatible con BASH.
- Python 3.11 o superior
- Todos los programas comunes del sistema (grep, cat, etc...).
- Todos los programas requeridos para compilar programas C en el sistema (libc, libstdc++, g++, GNU make, etc...).
- Autotools (autoconf, automake, aclocals...).
- wget
- git
- libdsk
  
Estos requerimientos son necesarios para compilar `SjAsmPlus` y `TAPTOOLS`. No existe distribución en binario de estas herramientas para sistemas compatibles UNIX, con lo que se requiere compilarlas directamente.

Debido a la heterodoxa naturaleza de las diferentes distribuciones, me resulta imposible dar instrucciones detalladas para instalar los requerimientos en cada caso en particular, con lo que se requieren conocimientos por parte del usuario para ello.

Lo primero que hay que hacer es clonar el repositorio del motor en cualquier lugar que creas conveniente y de forma recursiva para bajarse las dependencias:

```bash
git clone --recursive https://github.com/cronomantic/ChooseYourDestiny.git
cd ChooseYourDestiny
```

Ahora se puede proceder a compilar **SjASMPlus** con los siguientes comandos:

```bash
cd external/sjasmplus
make clean
make
cd ..
```

Ahora, pasaremos a compilar **TAPTOOLS**, pero antes necesitamos instalar la librería **LIBDSK**. Si estás en Debian o Ubuntu, las puedes instalar con el siguiente comando (si usas Ubuntu, tienes que tener activado el repositorio "Universe"):

```bash
sudo apt-get install libdsk4 libdsk4-dev libdsk-utils
```

Para ArchLinux, el comando sería el siguiente:

```bash
pacman -S libdsk
```

Consulta si dispones de dicha librería en tu distribución. Si no es el caso, tendrás que bajártela y compilarla tú mismo.

Una vez hecho esto, realizamos la siquiente secuencia de comandos:

```bash
tar -xf taptools-1.1.1.tar.gz
cd taptools-1.1.1
./configure
make
```

Y con esto ya tenemos preparadas las dependencias. Como último paso, debemos poner el script de compilación como ejecutable:

```bash
cd ../..
chmod a+x make_adv.sh
```

Y con esto ya podrías usar la herramienta en Linux.

## CYDC (Compilador)

Este programa es el compilador que traduce el texto de la aventura a un fichero TAP o DSK. Además de compilar la aventura en un fichero interpretable por el motor, realiza una búsqueda de las mejores abreviaturas para reducir el tamaño del texto.

```batch
cydc_cli.py [-h] [-l MIN_LENGTH] [-L MAX_LENGTH] [-s SUPERSET_LIMIT]
              [-T EXPORT-TOKENS_FILE] [-t IMPORT-TOKENS-FILE] [-C EXPORT-CHARSET]
              [-c IMPORT-CHARSET] [-S] [-n NAME] [-csc CSC_IMAGES_PATH] [-trk TRACKS_PATH]
              [-sfx SFX_ASM_FILE] [-scr LOAD_SCR_FILE] [-v] [-V] [-trim] 
              {48k,128k,plus3} input.txt SJASMPLUS_PATH MKP3FS_PATH OUTPUT_PATH
```

- **\-h**: Muestra la ayuda
- **\-l MIN_LENGTH**: La longitud mínima de las abreviaturas a buscar (por defecto, 3).
- **\-L MAX_LENGTH**: La longitud máxima de las abreviaturas a buscar (por defecto, 30).
- **\-s SUPERSET_LIMIT**: Límite para el superconjunto de la heurística de la búsqueda (por defecto, 100).
- **\-T EXPORT-TOKENS_FILE**: Exportar al fichero JSON indicado por el parámetro las abreviaturas encontradas.
- **\-t IMPORT-TOKENS-FILE**: Importar abreviaturas desde el fichero indicado y obviar la búsqueda de las mismas.
- **\-C EXPORT-CHARSET**: Exporta el juego de caracteres 6x8 usado por defecto en formato JSON.
- **\-c IMPORT-CHARSET**: Importa en formato JSON el juego de caracteres a emplear.
- **\-S**: Si un fragmento de texto comprimido no cabe en un banco, se divide en dos entre el banco actual y el siguiente con esta opción activada. Si no, el fragmento pasa al banco siguiente.
- **\-n NAME**: Nombre a usar para el fichero de salida (nombre para el fichero TAP o DSK), si no se define será el mismo que el fichero de entrada.
- **\-scr LOAD_SCR_FILE**: Ruta hacia un fichero SCR con la pantalla de carga a usar.
- **\-csc CSC_PATH**: Ruta al directorio con las imágenes CSC comprimidas de la aventura.
- **\-trk TRACKS_PATH**: Ruta al directorio con los ficheros PT3 de música AY.
- **\-sfx SFX_ASM_FILE**: Ruta a un fichero ensamblador generado por BeepFx.
- **\-v**: Modo verboso, da más información del proceso.
- **\-V**: Indica la versión del programa.
- **\-trim**: (Experimental) Elimina el código de aquellos comandos que no se usen en la aventura.

-**{48k,128k,plus3}**: Modelo de Spectrum a emplear:
  -- **48k**: Versión para cinta en formato TAP, no incluye el reproductor de PT3 y se carga todo de una vez. Depende del tamaño de la memoria disponible.
  -- **128k**: Versión para cinta en formato TAP, se carga todo de una vez en los bancos de memoria y depende del tamaño de la memoria disponible.
  -- **plus3**: Esta versión generará un fichero DSK para ejecutarlo en Spectrum+3. Los recursos se cargan dinámicamente según se necesiten y depende del tamaño en disco.

- **input.txt**: Fichero de entrada con el guion de la aventura.
- **SJASMPLUS_PATH**: Ruta al ejecutable de SjASMPlus.
- **MKP3FS_PATH**: Ruta al ejecutable mkp3fs.
- **OUTPUT_PATH**: Ruta donde se depositarán los ficheros de salida.

El compilador es un programa escrito en Python, por lo que se requiere tener el entorno de Python instalado. Para mayor comodidad, se incluye en la distribución un Python embebido y un guion batch llamado `cydc.cmd` para lanzarlo desde la línea de comandos.

**El compilador depende de dos programas externos para funcionar**. El ensamblador `SjASMPlus` y el constructor de imágenes DSK `mkp3fs`, por lo que habrá que indicar en los parámetros de entrada las correspondientes rutas a esos programas, los cuales están incluidos en la distribución en el directorio `tools`.

También hay que indicar un directorio de destino para dejar los ficheros resultantes de la compilación.

Opcionalmente, podemos indicar las rutas a directorios que contengan las imágenes comprimidas en formato `CSC`, que se incluirán en la cinta o disco resultante. Lo mismo para los ficheros de tipo `PT3`. Ambos tipos de archivos deben estar nombrados con números de 3 dígitos, del 0 al 255, de tal forma que sean `000.CSC`, `001.CSC`, `002.PT3`, y así. Se indicarán los directorios que contienen ambos ficheros con los parámetros `-csc` y -`pt3` respectivamente.

Se pueden añadir efectos de sonido generados con la aplicación BeepFx de Shiru. Para utilizarlos, hay que exportar usando la opción `File->Compile` del menú superior. En la ventana flotante que aparece, debemos asegurarnos de que tenemos seleccionado `Assembly` e `Include Player Code`, el resto de las opciones son indiferentes. Luego guardar el fichero en algún punto accesible para indicar la ruta desde la línea de comandos con la opción `-sfx`.

---

## CSC (Compresor de Imágenes)

Esta utilidad permite comprimir imágenes tipo **SCR** de ZX Spectrum para mostrarlas en el motor. Las pantallas pueden ser completas, o se puede limitar el número de líneas horizontales para ahorrar memoria. Además detecta imágenes espejadas (simétricas) por el eje vertical, con lo que sólo almacena la mitad de la misma, pudiéndose incluso forzar este comportamiento y descartar el lado derecho de la imagen para ahorrar espacio.

```batch
CSC [-f] [-m] [-l=num_lines] [-o=output] input
    -f, --force                Force overwrite of output file
    -m, --mirror               The right side of the image is the reflection of the left one.
    -o, --output=FILE          Output path for the file
    -l, --num-lines=NUMBER     Number of visible lines
    -h, --help                 Shows the command help
```

Esto es una definición de los parámetros:

- **\-f, --force**: Fuerza la sobreescritura del fichero de destino si ya existiese.
- **\-m, --mirror**: Descarta el lado derecho de la imagen y usa la imagen espejada del izquierdo.
- **\-o, --output=FILE**: Ruta del salida del fichero comprimido.
- **\-l, --num-lines=NUMBER**: Número de líneas de la pantalla a tratar (en carácteres, de 1 a 24).
- **\-h, --help**: Muestra la ayuda.

El motor soporta un máximo de 256 imágenes, aparte de lo que quepa en el disco o la memoria, y deben estar nombradas con un número de 3 dígitos, que corresponderá al número de imagen que se invocará desde el programa. Por ejemplo, la imagen 0 debería llamarse `000.CSC`, la imagen número 1 `001.CSC`, y así hasta 255, como ya se ha indicado en la sección anterior.

---

## CYD Character Set Converter

Esta utilidad permite convertir juegos de caracteres en formato `.chr`, `.ch8`, `.ch6` y `.ch4` en un fichero utilizable por el compilador en formato JSON. Estos formatos son editables con ZxPaintbrush.

```batch
cyd_chr_conv.py [-h] [-w WITDH] [-v] [-V] charset.chr charset.json
```

Los parámetros que soporta:

- **\-w, --width**: Ancho de los caracteres (1-8).
- **\-h, --help**: Muestra la ayuda.
- **\-v, --verbose**: Modo verboso.
- **\-V, --verbose**: Versión del programa.
- **charset.chr**: Huego de caracteres de entrada.
- **charset.json**: Fichero con el juego de caracteres para el compilador.

El ancho de los caracteres empleado depende de la extensión del fichero de entrada, 8 pixels para `.chr` y `.ch8`, 6 para `.ch6` y 4 para`.ch4`, pero se pueden forzar el ancho con el parámetro `-w`. Indicar que los caracteres del 127 al 143 son especiales para los cursores y siempre tendrán ancho 8, con lo que el tamaño de la fuente será ignorado en esos caracteres. Si se desea definir un ancho específico para cada carácter tendrás que editarlo en el fichero JSON de salida. Tienes más información en la sección [Juego de caracteres](#juego-de-caracteres).

---

## Sintaxis Básica

Los comandos para el intérprete se delimitan dentro de dos pares de corchetes, abiertos y cerrados respectivamente. Todo texto que aparezca fuera de esto, se considera "texto imprimible", incluidos los espacios y saltos de línea, y se presentarán como tal por el intérprete. Los comandos se separan entre sí con saltos de línea o dos puntos si están en la misma línea.

Los comentarios dentro del código se delimitan con `/*` y `*/`, todo lo que haya en medio se considera un comentario.

Este es un ejemplo resumido y auto explicativo de la sintaxis:

```
Esto es texto [[ INK 6 ]] Esto es texto de nuevo pero amarillo
    Sigue siendo texto [[
         /* Esto es un comentario y lo siguiente son comandos */
        WAITKEY
        INK 7: PAPER 0
    ]]
    Esto vuelve a ser texto pero blanco, y ¡ojo con el salto de línea que lo precede!
```

El intérprete recorre el texto desde el principio, imprimiéndolo en pantalla si es "texto imprimible". Cuando una palabra completa no cabe en lo que queda de la línea, la imprime en la línea siguiente. Y si no cabe en lo que queda de pantalla, se genera una espera y petición al usuario de que pulse la tecla de confirmación para borrar la sección de texto y seguir imprimiendo (este último comportamiento es opcional).

Cuando el intérprete detecta comandos, los ejecuta secuencialmente, a menos que encuentre saltos. Los comandos permiten introducir lógica programable dentro del texto para hacerlo dinámico y variado según ciertas condiciones. La más común y poderosa es la de solicitar escoger al jugador entre una serie de opciones (hasta un límite de 8 a la vez), y que puede elegir con las teclas `P` y `Q` y seleccionar con `SPACE` o `ENTER`.  
De nuevo, éste es un ejemplo auto explicativo:

```
[[ /* Comandos que ponen colores de pantalla y la borra */
   PAPER 0   /* Color de fondo a cero (negro)*/
   INK   7   /* Color de la tinta (blanco) */
   BORDER 0  /* Color del borde (negro) */
   CLEAR     /* Borrar el área de texto (pantalla completa) */
   LABEL Localidad1]]Estás en la localidad 1. ¿Donde quieres ir?
[[OPTION GOTO Localidad2]]Ir a la localidad 2
[[OPTION GOTO Localidad3]]Ir a la localidad 3
[[CHOOSE]]
[[ LABEL Localidad2]]¡¡¡Lo lograste!!!
[[ GOTO Final]]
[[ LABEL Localidad3]]¡¡¡Estas muerto!!!
[[ GOTO Final]]
[[ LABEL Final : WAITKEY: END ]]
```

El comando `OPTION GOTO etiqueta` generará un punto de selección en el lugar en donde se haya llegado al comando.  
Cuando llegue al comando `CHOOSE`, el intérprete permitirá elegir al usuario entre uno de los puntos de opción que haya acumulados en pantalla hasta el momento. Se permiten un máximo de 32.

Al escoger una opción, el intérprete saltará a la sección del texto donde se encuentre la etiqueta correspondiente indicada en la opción. Las etiquetas se declaran con el pseudo-comando `LABEL identificador` dentro del código, y cuando se indica un salto a la misma, el intérprete comenzará a procesar a partir del punto en donde hemos declarado la etiqueta.  
En el caso del ejemplo, si elegimos la opción 1, el intérprete saltará al punto indicado en `LABEL localidad2`, con lo que imprimirá el texto _"¡¡¡Lo lograste!!!"_, y después pasa a `GOTO Final` que hará un salto incondicional a donde está definido `LABEL Final` e ignorando todo lo que haya entre medias.

Los identificadores de las etiquetas sólo soportan caracteres alfanuméricos (cifras y letras), deben empezar con una letra y son sensibles al caso (se distinguen mayúsculas y minúsculas), es decir `LABEL Etiqueta` no es lo mismo que `LABEL etiqueta`. Los comandos, por el contrario, no son sensibles al caso, pero por claridad, es recomendable ponerlos en mayúsculas.

También se permite una versión acortada de las etiquetas precediendo el caracter `#` al identificador de la etiqueta, de tal manera que `#MiEtiqueta` es lo mismo que `LABEL MiEtiqueta`. Con esto, podríamos reescribir el anterior código así:

```
[[ /* Comandos que ponen colores de pantalla y la borra */
   PAPER 0   /* Color de fondo a cero (negro)*/
   INK   7   /* Color de la tinta (blanco) */
   BORDER 0  /* Color del borde (negro) */
   CLEAR     /* Borrar el área de texto (pantalla completa) */
   LABEL Localidad1]]Estás en la localidad 1. ¿Donde quieres ir?
[[OPTION GOTO Localidad2]]Ir a la localidad 2
[[OPTION GOTO Localidad3]]Ir a la localidad 3
[[CHOOSE]]
[[ #Localidad2 ]]¡¡¡Lo lograste!!!
[[ GOTO Final ]]
[[ #Localidad3 ]]¡¡¡Estas muerto!!!
[[ GOTO Final]]
[[ #Final : WAITKEY: END ]]
```

Los comandos disponibles están descritos en su [sección](#comandos) correspondiente.

---

## Flags y expresiones numéricas

Hay a disposición del programador 256 contenedores de un byte (de 0 a 255) para almacenar valores, realizar operaciones y comparaciones con ellos. Constituyen el estado del programa. A partir de este momento, pueden ser llamados variables, banderas o "flags" indistintamente a lo largo de este documento.

Para referirnos a una variable en una expresión numérica, el número debe estar precedido por el carácter `@`. Pero es posible dar un nombre significativo a las variables usando el comando `DECLARE` de la siguiente manera:

```
[[
DECLARE 7 AS ColorTinta
INK @ColorTinta
]]
```

Hay que indicar que no se puede declarar una variable dos veces, ni puede haber etiquetas y variables con los mismos nombres, pero se permiten sinónimos de la siguiente forma:

```
[[
DECLARE 10 AS UnNombre
DECLARE 10 AS OtroNombre
]]
```

Así, tanto _UnNombre_ como _OtroNombre_ servirán para identificar el flag 10. Ten en cuenta de a pesar de tener distinto nombre, son la misma variable.

Para asignar valores a un flag, usamos el comando `SET varId TO numexpression`, de la siguiente manera:

```
[[
  SET 0 TO 1                      /* Ponemos el flag cero a 1 */
  SET variable TO 2               /* Ponemos el flag llamado variable a 2 */
  SET variable2 TO @variable + 2  /* Ponemos el flag llamado variable2 al dos sumado al valor del flag llamado variable */
  SET variable2 TO @variable2 - (@variable + 2)  /* Permite paréntesis */
]]

```

También tenemos ahora el siguiente sinónimo con `LET varId = numexpression`, de tal forma que los ejemplos anteriores se podrían reescribir así:

```
[[
  LET 0 = 1                      /* Ponemos el flag cero a 1 */
  LET variable = 2               /* Ponemos el flag llamado variable a 2 */
  LET variable2 = @variable + 2  /* Ponemos el flag llamado variable2 al dos sumado al valor del flag llamado variable */
  LET variable2 = @variable2 - (@variable + 2)  /* Permite paréntesis */
]]
```

Como se puede ver, a un flag se le puede asignar el valor de una expresión matemática compuesta por números, funciones y variables. Como ya se ha indicado, las variables dentro de una expresión numérica, es decir, el lado derecho de una asignación **siempre deben estar precedidas del carácter `@`**.

Los operandos disponibles son:

- Suma: `SET variable TO @variable + 2`
- Resta: `SET variable TO @variable - 2`
- "AND" binario: `SET variable TO @variable & 2`
- "OR" binario: `SET variable TO @variable | 2`
- "NOT binario o complemento de bits: `SET variable TO !@variable`

El resultado de una expresión numérica no pueden ser mayor de 255 (1 byte) ni menor que cero (no se soportan números negativos). Si al realizar las operaciones se rebasan ambos límites, el resultado se ajustará al límite correspondiente, es decir, si una suma supera 255, se ajustará a 255 y una resta que dé un resultado inferior a cero, se quedará en cero.

Una cosa a destacar es que los operadores binarios **no son los mismos que los operadores lógicos de las expresiones condicionales** descritos más abajo. Un **&** no es lo mismo que un **AND**. Los operadores binarios realizan las correspondientes operaciones sobre los bits del flag.

La mayor parte de los comandos aceptan expresiones numéricas en sus parámetros, por ejemplo:

```
[[
INK 7
INK @7
]]
```

El primer comando pondrá el color del texto en blanco (color 7), mientras que el segundo pondrá el color del texto con el valor contenido en la variable número 7. Combinando con todo lo anteriormente descrito, se podría hacer:

```
[[
INK 3+4
INK @Var-1
]]
```

Consulta la referencia de [comandos](#comandos) para saber cuáles de ellos los aceptan.

Por último, hay una serie de comandos especiales llamados **funciones**. Estos comandos no pueden usarse por sí solos, sino que deben usarse dentro de una expresión numérica, ya que devuelven un valor a emplear dentro de ella.

- **RANDOM(expression)**: Devuelve un número aleatorio entre 0 y el valor indicado en **expression** menos uno. Si se indica cero, el resultado será como si fuese entre 0 y 255.
- **RANDOM()** : Devuelve un número aleatorio entre 0 y 255. Es el equivalente a `RANDOM(0)`.
- **RANDOM(expression,expression)**: Devuelve un número aleatorio entre el valor indicado en el primer parámetro y el segundo, ambos inclusive.
- **INKEY()** Se espera hasta que se pulse una tecla y devuelve el código de la tecla pulsada.
- **MIN(numexpression,numexpression)**: Acota el valor del primer parámetro al mínimo indicado por el segundo. Es decir, si el parámetro 1 es menor que el parámetro 2, se devuelve el parámetro 2, en otro caso se devuelve el 1.
- **MAX(numexpression,numexpression)**: Acota el valor del primer parámetro al máximo indicado por el segundo. Es decir, si el parámetro 1 es mayor que el parámetro 2, se devuelve el parámetro 2, en otro caso se devuelve el 1.
- **POSY()**: Devuelve la fila actual en la que se encuentra el cursor en coordenadas 8x8.
- **POSX()**: Devuelve la columna actual en la que se encuentra el cursor en coordenadas 8x8 (Debido a la naturaleza de la fuente de ancho variable, el valor devuelto será la columna 8x8 donde esté actualmente el cursor).

Así que, por ejemplo `SET flag_no TO RANDOM(6)`, asigna a la variable _flag_no_ un número aleatorio del 0 al 5. Y de la misma manera, podemos operar con ellos: `SET flag_no TO RANDOM(6) + @var + 1`

---

## Control de flujo y expresiones condicionales

Para controlar el flujo de ejecución, tenemos diferentes comandos, que describiré ahora:

- **GOTO ID**

Salta a la etiqueta _ID_.

- **GOSUB ID**

Salto de subrutina, hace un salto a la etiqueta _ID_, pero vuelve al siguiente comando cuanto encuentra un comando `RETURN`.  

- **RETURN**

Retorna al punto posterior de la llamada de la subrutina, ver `GOSUB`

- **IF condexpression THEN ... ENDIF**

Si la expresión condicional _condexpression_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ENDIF`.

- **IF condexpression THEN ... ELSE ... ENDIF**

Si la expresión condicional _condexpression_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ELSE`. En caso contrario, se imprime el texto y se ejecutan los comandos que haya desde `ELSE` hasta `ENDIF`

- **IF condexpression THEN ... ELIF condexpression THEN ... ELSE ... ENDIF**

Si la expresión condicional _condexpression1_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ELSE`. En caso contrario, se
verifica si la expresión condicional _condexpression2_ se cumple, en cuyo caso imprime el texto y se ejecutan los comandos que haya desde `ELIF` hasta el `ELSE` u otro `ELSEIF`. Se pueden encadenar varios `ELSEIF` hasta que se llegue a una última cláusula `ELSE`, que se ejecuta si ninguna de las condiciones anteriores se ha cumplido.

- **WHILE (condexpression) ... WEND**

Se repiten repetidamente el texto y los comandos que haya hasta el `WEND` mientras la condición _condexpression_ evalúe a cierto. La evaluación se realiza al principio de cada iteración.

Como se puede ver, muchos de estas funciones se ejecutan dependiendo de si se cumple una condición. Por ejemplo:

```
[[IF @var = 0 THEN GOTO salto ENDIF]]
```

Para que se ejecute el salto, tiene que cumplirse que la variable _var_ sea igual a cero. Esto es una expresión condicional.

Una condición es siempre una comparación entre dos expresiones numéricas:

- Igual que: `IF @variable = 0 THEN GOTO salto ENDIF`
- Mayor que: `IF @variable > 0 THEN GOTO salto ENDIF`
- Menor que: `IF @variable2 < @variable THEN GOTO salto ENDIF`
- Distinto que: `IF @variable <> 0 THEN GOTO salto ENDIF`
- Mayor o igual que: `IF @variable <= 0 THEN GOTO salto ENDIF`
- Menor o igual que: `IF @variable >= 0 THEN GOTO salto ENDIF`

Además, las condiciones se pueden combinar formando expresiones condicionales mediante operaciones lógicas. Por ejemplo:

```
[[IF (@variable = 0 AND @variable2 = 1) AND NOT @variable3 = 1 THEN GOTO salto ENDIF]]
```

- Cond1 AND Cond2: Cierto si se cumple tanto como Cond1 como Cond2.
- Cond1 OR Cond2: Cierto si se cumple Cond1 o Cond2.
- NOT Cond1: Cierto si la condición Cond1 es falsa.

Recuerdo de nuevo que los operadores lógicos de las expresiones condicionales **no son los mismos que los operadores binarios**. Además para aquellos que tengan nociones avanzadas de programación, las condiciones no son "cortocircuitantes", es decir, se evalúan todas las operaciones lógicas y comparaciones hasta el final.

---

## Asignaciones e indirección

Las asignaciones y expresiones numéricas ya las hemos visto en [su sección](#flags-y-expresiones-numéricas), pero vamos a explicar más detalladamente su funcionamiento con la indirección, lo cual merece una sección aparte.

La indirección se realiza poniendo entre corchetes simples una expresión numérica, por ejemplo `[@var+1]`. Lo que estamos queriendo decir es que **nos vamos a referir al flag o variable con el número calculado por la expresión numérica encerrada entre corchetes**. Vamos a verlo con ejemplos:

- `SET var to [2+2]`: indica que vamos a asignar a _var_ el contenido del flag 2+2, es decir 4. Esto es equivalente a `SET var TO @4`, pero nos permite ir afianzando el concepto.
- `SET var TO [@indice]`: aquí es donde se muestra realmente la utilidad, ya que estamos indicando que guardamos en _var_ el contenido de la variable cuyo número corresponde con el contenido de la variable _indice_. Es decir, podemos cambiar de forma dinámica la variable a la cual hacemos la asignación.
- `SET var TO [@indice+2]`: la indirección soporta cualquier expresión numérica, esto significa que guardamos en _var_ el contenido de la variable corresponda con el contenido de _indice_ mas dos.
- `SET [var] TO 0`: La indirección también puede usarse en el lado derecho, y en este caso, no se soportan expresiones numéricas, sólo el número o el identificador de la variable si se ha declarado. Esto significa "asigna cero a la variable cuyo índice corresponda con el contenido de la variable _var_.
- `INK [@var]`: La indirección también es soportada por aquellos comandos que admitan expresiones numéricas.
- `SET [@@var] TO 0`: Por completitud, ya que operamos con punteros, usando `@@` tenemos la operación complementaria a la indirección, es decir, devuelve el número de índice de una variable dada, con lo que en el ejemplo, la operación sería equivalente a `SET var TO 0`.

Si usamos los indicadores numéricos con las variables (p.ej. `@0`) no resulta muy útil. Su verdadera utilidad reside en usarlo con los identificadores de variables, tal que si tenemos:

```
[[
DECLARE 20 AS var : DECLARE 10 AS index: SET index AS @@var : SET [index] AS 0
]]
```

Vemos que esto nos permite inicializar variables que vayamos a usar para indirección con el identificador de otra variable.
  
La indirección constituye una herramienta poderosa que nos permite implementar arrays en los flags, pero ¡ojo, que sólo tenemos 256!

Por último, y relacionado con los arrays, podemos realizar asignaciones múltiples mediante la siguiente construcción:

```
[[
DECLARE 10 AS var
SET var AS {0, 1, 2, 3}
]]
```

Esto sería equivalente a:

```
[[
SET 10 AS 0
SET 11 AS 1
SET 12 AS 2
SET 13 AS 3
]]
```

Es decir, podemos asignar de forma consecutiva una secuencia de valores a una secuencia de variables, comenzando por la variable indicada en el lado izquierdo. Lo cual permite asignar valores para arrays, o asignar múltiples valores de forma consecutiva.

---

## Listado de comandos

Antes de describir los comandos, vamos a hablar resumidamente de la leyenda utilizada:

- **ID** es un identificador y es una cadena de cifras, letras o subrayado. No se admiten letras acentuadas ni la ñ.
- **expression** es una expresión numérica sin variables. Es un número en decimal o hexadecimal, pero también se admiten operaciones aritméticas simples que serán calculadas en tiempo de compilación.
- **numexpression**, expresión numérica tal y como es descrita en su [sección](#flags-y-expresiones-numéricas) correspondiente. Puede contener variables con `@` e indirecciones.
- **condexpression**, expresión condicional tal y como es descrita en su [sección](#control-de-flujo-y-expresiones-condicionales) correspondiente. Consisten en una comparación o varias comparaciones con operaciones lógicas entre las mismas.
- **varID**, identificador de variable, puede ser una _expression_ si usamos su índice numérico o un _ID_ si lo hemos declarado así con `DECLARE`.

### **NOTA IMPORTANTE PARA USUARIOS DE VERSIONES ANTERIORES A v0.7**

Debido a las adiciones al lenguaje, los comandos siguientes quedan obsoletos y las aventuras que los usen no compilarán. También indico el sustituto correspondiente para recuperar la funcionalidad:

| Comando obsoleto                    | Sustituir por...                          |
| ----------------------------------- | ----------------------------------------- |
| `IF condexpression THEN GOTO ID`    | `IF condexpression THEN GOTO ID ENDIF`    |
| `IF condexpression THEN GOSUB ID`   | `IF condexpression THEN GOSUB ID ENDIF`   |
| `IF condexpression OPTION GOTO ID`  | `IF condexpression OPTION GOTO ID ENDIF`  |
| `IF condexpression OPTION GOSUB ID` | `IF condexpression OPTION GOSUB ID ENDIF` |

---

Este es listado completo de comandos:

### LABEL ID

Declara la etiqueta labelId en este punto. Todos los saltos con referencia a esta etiqueta dirigirán la ejecución a este punto.

### #ID

Versión resumida para declarar la etiqueta _ID_, de tal manera que `#LabelId` es lo mismo que `LABEL LabelId`.

### DECLARE expression AS ID

Declara el identificador _ID_ como un símbolo que representa al flag _expression_ en su lugar.

### GOTO ID

Salta a la etiqueta _ID_.

### GOSUB ID

Salto de subrutina, hace un salto a la etiqueta _ID_, pero vuelve al siguiente comando cuanto encuentra un comando `RETURN`.  

### RETURN

Retorna al punto posterior de la llamada de la subrutina, ver `GOSUB`

### IF condexpression THEN ... ENDIF

Si la expresión condicional _condexpression_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ENDIF`.

### IF condexpression THEN ... ELSE ... ENDIF

Si la expresión condicional _condexpression_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ELSE`. En caso contrario, se imprime el texto y se ejecutan los comandos que haya desde `ELSE` hasta `ENDIF`

### IF condexpression1 THEN ... ELIF condexpression2 THEN ... ELSE ... ENDIF

Si la expresión condicional _condexpression1_ resulta cierta, se imprime el texto y se ejecutan los comandos que haya desde `THEN` hasta `ELSE`. En caso contrario, se
verifica si la expresión condicional _condexpression2_ se cumple, en cuyo caso imprime el texto y se ejecutan los comandos que haya desde `ELIF` hasta el `ELSE` u otro `ELSEIF`. Se pueden encadenar varios `ELSEIF` hasta que se llegue a una última cláusula `ELSE`, que se ejecuta si ninguna de las condiciones anteriores se ha cumplido.

### WHILE (condexpression) ... WEND

Se repiten repetidamente el texto y los comandos que haya hasta el `WEND` mientras la condición _condexpression_ evalúe a cierto. La evaluación se realiza al principio de cada iteración.

### SET varID TO numexpression

Asigna el valor de _numexpression_ a la variable _varID_.

### SET [varID] TO numexpression

Asigna el valor de _numexpression_ a la variable cuyo índice corresponde con el contenido de _varID_.

### SET varID TO {numexpression1, numexpression2,...}

Asigna el valor de _numexpression1_ a la variable _varID_,  _numexpression2_ a la variable _varID_+1, y así.

### SET [varID] TO {numexpression1, numexpression2,...}

Asigna el valor de _numexpression1_ a la variable cuyo índice corresponde con el contenido de _varID_, _numexpression2_ a la variable cuyo índice corresponde con el contenido de _varID_+1, y así.

### LET varID = numexpression

Asigna el valor de _numexpression_ a la variable _varID_.

### LET [varID] = numexpression

Asigna el valor de _numexpression_ a la variable cuyo índice corresponde con el contenido de _varID_.

### LET varID = {numexpression1, numexpression2,...}

Asigna el valor de _numexpression1_ a la variable _varID_,  _numexpression2_ a la variable _varID_+1, y así.

### LET [varID] = {numexpression1, numexpression2,...}

Asigna el valor de _numexpression1_ a la variable cuyo índice corresponde con el contenido de _varID_, _numexpression2_ a la variable cuyo índice corresponde con el contenido de _varID_+1, y así.

### END

Finaliza la aventura y reinicia el ordenador.

### CLEAR

Borra el área de texto definida.

### CENTER

Pone el cursor de impresión en el centro de la línea.

### WAITKEY

Espera la pulsación de la tecla de aceptación para continuar, presentando un icono animado de espera. Ideal para separar párrafos o pantallas.

### OPTION GOTO ID

Crea un punto de opción que el usuario puede seleccionar (ver `CHOOSE`). Si confirma esta opción, salta a la etiqueta _ID_. Si se borra la pantalla, el punto de opción se elimina y sólo se permiten 32 como máximo en una pantalla. Los puntos de opción se van acumulando en orden de declaración en una lista que será recorrida de acuerdo a la pulsación de las teclas de manejo.

### OPTION GOSUB ID

Crea un punto de opción que el usuario puede seleccionar (ver `CHOOSE`). Si confirma esta opción, hace un salto de subrutina a etiqueta _ID_, volviendo después del `CHOOSE` cuando encuentra un `RETURN`. Si se borra la pantalla, el punto de opción se elimina y sólo se permiten 32 como máximo en una pantalla. Los puntos de opción se van acumulando en orden de declaración en una lista que será recorrida de acuerdo a la pulsación de las teclas de manejo.

### CHOOSE

Detiene la ejecución y permite al jugador seleccionar una de las opciones que haya en este momento en pantalla. Realizará el salto a la etiqueta indicada en la opción correspondiente.
La selección se realiza con las teclas **O** y **P** para "desplazamiento horizontal" y **Q** y **A** para desplazamiento vertical. Cuando se pulsan las teclas, un puntero se desplaza sobre la lista de opciones realizando incrementos o decrementos de acuerdo a la configuración actual del mismo (ver [MENUCONFIG](#menuconfig-numexpression-numexpression)). Por defecto, sólo tiene configurado un desplazamiento vertical con las teclas **Q** y **A**. Es responsabilidad del usuario colocar los puntos de opción en pantalla de una forma coherente al movimiento del menú configurado.

Recuerda que si se borra la pantalla antes de este comando, perderás las opciones y dará un error de sistema.

### CHOOSE IF WAIT expression THEN GOTO ID

Funciona exactamente igual que `CHOOSE`, pero con la salvedad de que se declara un timeout, que si se agota sin seleccionar ninguna opción, salta a la etiqueta _ID_.  
El timeout tiene como máximo 65535 (16 bits).

### CHOOSE IF CHANGED THEN GOSUB ID

Funciona exactamente igual que `CHOOSE`, pero se hace un salto de subrutina a la etiqueta _ID_ cada vez que se cambia de opción. Por tanto, es recomendable que se haga un `RETURN` lo antes posible para evitar lentitud. Para saber la opción elegida y el número de opciones total de nuestro menú, podemos usar las funciones `OPTIONSEL()` y `NUMOPTIONS` respectivamente.

### OPTIONSEL()

_Función_ que devuelve la opción actualmente seleccionada en el menú actualmente activo. Si no tenemos un menú activo, el resultado de esta función está indefinido.

### NUMOPTIONS()

_Función_ que devuelve el número de opciones del menú actualmente activo. Si no tenemos un menú activo, el resultado de esta función está indefinido.

### CLEAROPTIONS

Elimina las opciones almacenadas en el menú.

### MENUCONFIG numexpression, numexpression

Configura el desplazamiento por el menú de opciones.

- El primer parámetro determina el incremento o decremento del número de opción seleccionado cuando pulsamos **P** y **O** respectivamente.
- El segundo parámetro determina el incremento o decremento del número de opción seleccionado cuando pulsamos **A** y **Q** respectivamente.

El comportamiento al iniciarse el intérprete es como si se hubiese ejecutado `MENUCONFIG 0,1`.

### CHAR numexpression

Imprime el carácter indicando con su número correspondiente.

### REPCHAR expression, expression

Imprime el carácter indicado en el primer parámetro tantas veces como número se indique en el segundo parámetro. Ambos valores tienen un tamaño de 1 byte, es decir, val del 0 al 255. Además, si el número de veces es cero, el carácter se repetirá 256 veces en lugar de ninguna.

### TAB expression

Imprime tantos espacios como los indicados en el parámetro. Es el equivalente a `REPCHAR 32, expression`, pero ocupa menos memoria.

### PRINT numexpression

Imprime el valor numérico indicado.

### PAGEPAUSE expression

Controla si al rellenar el área de texto actual, debe solicitar continuar al jugador, presentando un icono animado de espera (parámetro \<> 0) ó hace un borrado de pantalla y sigue imprimiendo (parámetro = 0).

### INK numexpression

Define el valor del color de los caracteres (tinta). Valores de 0-7, correspondientes a los colores del Spectrum.

### PAPER numexpression

Define el valor del color del fondo (papel). Valores de 0-7, correspondientes a los colores del Spectrum.

### BORDER numexpression

Define el color del borde, valores 0-7.

### BRIGHT numexpression

Activa o desactiva el brillo (0 desactivado, 1 activado).

### FLASH numexpression

Activa o desactiva el parpadeo (0 desactivado, 1 activado).

### NEWLINE expression

Imprime tantos saltos de línea como el número indicado en el parámetro (0 es 256)

### NEWLINE

Equivalente a `NEWLINE 1`.

### BACKSPACE expression

Retrasa el cursor de impresión tantas posiciones como las indicadas en el parámetro (0 es 256), eliminado el carácter en la nueva posición y sustituyéndolo por un espacio. El tamaño de carácter que se usará es el del espacio (número 32).
Hay que tener en cuenta que si se usan carácteres de distintos tamaños al del espacio, esta operación no funcionará bien.

### BACKSPACE

Equivalente a `BACKSPACE 1`.

### SFX numexpression

Si se ha cargado un fichero de efectos de sonido, reproduce el efecto indicado.  
Si no se ha cargado dicho fichero, el comando es ignorado.

### PICTURE numexpression

Carga en el buffer la imagen indicada como parámetro. Por ejemplo, si se indica 3, cargará el fichero `003.CSC`.  
La imagen no se muestra, lo que permite controlar cuándo se realiza la carga del fichero.

### DISPLAY numexpression

Muestra el contenido actual del buffer en pantalla.  
El parámetro indica si se muestra o no la imagen, con un 0 no se muestra, y con un valor distinto de cero, sí.
Se muestran tantas líneas como se hayan definido en la imagen correspondiente y el contenido de la pantalla será sobrescrito.

### BLIT expression, expression, expression, expression AT numexpression, numexpression

Copia una parte de la imagen cargada en el buffer a la pantalla.
Definimos con los parámetros un rectángulo dentro del buffer que se copiará en la pantalla a partir de la posición indicada.

Los parámetros, por órden, son:

- Columna origen del rectángulo a copiar desde el buffer.
- Fila origen del rectángulo a copiar desde el buffer.
- Ancho del rectángulo a copiar desde el buffer.
- Alto del rectángulo a copiar desde el buffer.
- Columna destino en pantalla.
- Fila destino en pantalla.

La unidad de medida empleada en todos los parámetros es el carácter 8x8 y sólo los dos últimos aceptan variables.

### WAIT expression

Realiza una pausa. El parámetro es el número de "fotogramas" (50 por segundo) a esperar, y es un número de 16 bits.

### PAUSE expression

Igual que `WAIT`, pero con la salvedad de que el jugador puede abortar la pausa con la pulsación de la tecla de confirmación.

### TYPERATE expression

Indica la pausa que debe haber entre la impresión de cada carácter. Mínimo 1, máximo 65535.

### MARGINS expression, expression, expression, expression

Define el área de pantalla donde se escribirá el texto. Los parámetros, por órden, son:

- Columna inicial.
- Fila inicial.
- Ancho (en carácteres).
- Alto (en carácteres).

Los tamaños y posiciones siempre se definen como si fuesen caracteres 8x8.

### FADEOUT  expression, expression, expression, expression

Hace un fundido en negro en el área de pantalla definida por los parámetros que, por órden, son:

- Columna inicial.
- Fila inicial.
- Ancho (en carácteres).
- Alto (en carácteres).

Los tamaños y posiciones siempre se definen como si fuesen caracteres 8x8.

### AT numexpression, numexpression

Sitúa el cursor en una posición dada, relativa al área definida por el comando `MARGINS`.  
Los parámetros, por orden, son:

- Columna relativa al origen del área de texto.
- Fila relativa al origen del área de texto.

Las posiciones se asumen en tamaño de carácter 8x8.

### FILLATTR expression, expression, expression, expression, expression, expression, expression, expression

Rellenamos en pantalla un rectángulo con un valor de atributos determinado. Los píxeles no se alteran.
Los parámetros, por órden, son:

- Columna origen del rectángulo a rellenar.
- Fila origen del rectángulo a rellenar.
- Ancho del rectángulo a rellenar.
- Alto del rectángulo a rellenar.
- Valor de "tinta". Valores permitidos: 0 al 7.
- Valor de color de fondo. Valores permitidos: 0 al 7.
- Valor de brillo. Valores permitidos: 0 ó 1.
- Valor de parpadeo. Valores permitidos: 0 ó 1.

### PUTATTR numexpression, numexpression, expression, expression, expression, expression

Ponemos los atributos de un carácter 8x8 en pantalla con unos valores determinados. Para aquellos campos en los que se indique un valor no permitido, el valor que ya existiese en pantalla no resultará alterado. Los píxeles tampoco se alteran.
Los parámetros, por órden, son:

- Columna del carácter 8x8.
- Fila del carácter 8x8.
- Valor de "tinta". Valores permitidos: 0 al 7. Si se indica otro valor, este valor del atributo no se modificará.
- Valor de color de fondo. Valores permitidos: 0 al 7. Si se indica otro valor, este valor del atributo no se modificará.
- Valor de brillo. Valores permitidos: 0 ó 1. Si se indica otro valor, este valor del atributo no se modificará.
- Valor de parpadeo. Valores permitidos: 0 ó 1. Si se indica otro valor, este valor del atributo no se modificará.

### GETATTR (numexpression, numexpression)

_Función_ que devuelve el valor de atributo de un carácter 8x8 en pantalla. Al contrario que `PUTATTR` o `FILLATTR`, los atributos están condensados en un sólo byte, que es el valor que se recupera de la memoria de vídeo del Spectrum.

Los parámetros, por órden, son:

- Columna del carácter 8x8.
- Fila del carácter 8x8.

### RANDOM(expression)

_Función_ que devuelve un número aleatorio entre 0 y el valor indicado en **expression** menos uno. Si se indica cero, el resultado será como si fuese entre 0 y 255.

### RANDOM()

_Función_ que devuelve un número aleatorio entre 0 y 255. Es el equivalente a `SET flag_no TO RANDOM(0)`.

### RANDOM(expression, expression)

_Función_ que devuelve un número aleatorio entre el valor indicado en el primer parámetro y el segundo, ambos inclusive.

### INKEY(expression)

_Función_ que devuelve el código de la tecla pulsada. Si el parámetro es cero, se espera hasta que se pulse una tecla. Si es distinto de cero, devuelve el código de la tecla pulsada en ese momento, y cero si no hay ninguna tecla pulsada.

### INKEY()

_Función_ que espera hasta que se pulse una tecla y devuelve el código de la tecla pulsada. Es equivalente a `INKEY(0)`

### MIN(numexpression,numexpression)

_Función_ que acota el valor del primer parámetro al mínimo indicado por el segundo. Es decir, si el parámetro 1 es menor que el parámetro 2, se devuelve el parámetro 2, en otro caso se devuelve el 1.

### MAX(numexpression,numexpression)

_Función_ que acota el valor del primer parámetro al máximo indicado por el segundo. Es decir, si el parámetro 1 es mayor que el parámetro 2, se devuelve el parámetro 2, en otro caso se devuelve el 1.

### YPOS()

_Función_ que devuelve la fila actual en la que se encuentra el cursor en coordenadas 8x8.

### XPOS()

_Función_ que devuelve la columna actual en la que se encuentra el cursor en coordenadas 8x8 (Debido a la naturaleza de la fuente de ancho variable, el valor devuelto será la columna 8x8 donde esté actualmente el cursor).

### RANDOMIZE

Inicializa el generador de números aleatorios. La generación de números aleatorios no es realmente "aleatoria" y esto puede ocasionar que el generador devuelva siempre los mismos resultados si se usa en un emulador, por lo que se necesita alguna fuente de aleatoriedad o entropía. Lo que hace este comando es inicializar el generador usando el número de "frames" o "fotogramas" transcurridos, con lo que si se ejecuta en respuesta a algún evento arbitrario, como la pulsación de una tecla, garantizamos la aleatoriedad.

### TRACK numexpression

Carga en memoria el fichero de Vortex Tracker como parámetro. Por ejemplo, si se indica 3, cargará la pista de música del fichero `003.PT3`. Si existiese una pista cargada previamente, la sobrescribirá.

### PLAY numexpression

Si el parámetro es distinto de cero y la música está desactivada, reproduce la pista musical cargada. Si está en ese momento reproduciendo, y se pasa 0 como parámetro, para la reproducción.

### LOOP numexpression

Establece si al acabar la pista musical cargada en ese momento, se repite de nuevo o no. Un valor 0 significa falso y distinto de cero, verdadero.

### RAMSAVE varID, expression

Copia desde la variable indicada en el primer parámetro, tantas variables como las indicadas en el segundo parámetro (si es cero, se considera como 256) a un almacenamiento temporal. Antes de realizar la copia, el almacén temporal se rellena con ceros, con lo que las variables no copiadas tendrán este valor en el almacén temporal.

### RAMSAVE varID

Es el equivalente a `RAMSAVE varId, 0`, es decir, copia todas las variables desde el primer parámetro hasta el final al almacén temporal.

### RAMSAVE

Es el equivalente a `RAMSAVE 0, 0`, es decir, copia todas las variables al almacén temporal.

### RAMLOAD varID, expression

Es la operación inversa a `RAMSAVE`. Copia desde el almacenamiento temporal a las variables, desde la variable indicada en el primer parámetro y tantas variables como las indicadas en el segundo (si es cero, se considera como 256).

### RAMLOAD varID

Es el equivalente a `RAMLOAD varId, 0`, es decir, copia todas las variables desde el primer parámetro hasta el final desde el almacén temporal.

### RAMLOAD

Es el equivalente a `RAMLOAD 0, 0`, es decir, copia todas las variables desde el almacén temporal.

### SAVE numexpression, varId, expression

Salva una serie de variables en cinta o disco.  El primer parámetro indica el número de fichero a guardar, el segundo parámetro es la variable inicial del rango de variables que se guardará el fichero, y el tercero en número de variables a guardar en ese rango (si es cero, se considera como 256).
Cualquier cosa que haya en el almacén temporal que se haya cargado con `RAMSAVE` será eliminado, ya que se usará para almacenar el fichero de forma temporal.

- En el caso del disco, se guardará el fichero con el número indicado de tres dígitos y extensión `.SAV`. P.ej. el fichero a cargar con 16 sería el `016.SAV`. Si el fichero ya existiese, se sobreescribirá.
- En el caso de la cinta, se guardará en ésta. El sistema empezará inmediatamente a guardar, con lo que el autor es el responsable de indicar al usuario que se va a grabar y que tiene que poner la unidad de casette (o equivalente) a grabar. El proceso puede interrumpirse con la tecla **BREAK**.
  
El resultado de la operación se puede consultar con la función `SAVERESULT()`.

### SAVE numexpression, varId

Es el equivalente a `SAVE numexpression, varId, 0`, es decir, guarda todas las variables desde el segundo parámetro hasta el final.

### SAVE numexpression

Es el equivalente a `SAVE numexpression, 0, 0`, es decir, guarda todas las variables

### LOAD numexpression

Carga una serie de variables desde cinta o disco. El parámetro indica el número de fichero a cargar, y se cargará el rango de variables que se haya indicado al salvar el fichero. Cualquier cosa que haya en el almacén temporal que se haya cargado con `RAMSAVE` será eliminado, ya que se usará para almacenar el fichero de forma temporal.

- En el caso del disco, se cargará el fichero con el número indicado de tres dígitos y extensión `.SAV`. P.ej. el fichero a cargar con 16 sería el `016.SAV`.
- En el caso de la cinta, se cargará el primer bloque sin cabecera que encuentre, con lo que es necesario que el usuario avance la cinta a la posición correcta. El sistema empezará inmediatamente a cargar, con lo que el autor es el responsable de indicar al usuario que se va a cargar y que tiene que poner la unidad de casette (o equivalente) a reproducir. El proceso puede interrumpirse con la tecla **BREAK**.

El resultado de la carga se puede consultar con la función `SAVERESULT()`.

### SAVERESULT()

_Función_ que devuelve el resultado de la última operación de `SAVE` o `LOAD`. Los valores posibles son los siguientes:

0. Resultado correcto.
1. Error al cargar/guardar en cinta/disco. En caso de cinta, operación interrumpida con **BREAK**.
2. La partida grabada no corresponde al juego actual.
3. El slot seleccionado de la partida grabada no corresponde al que se ha solicitado.
4. Error de chequeo del fichero de partida grabada.

Con cualquier otro valor, el resultado está indefinido.

### ISDISK()

_Función_ que devuelve 1 si el intérprete es la versión de Plus3 y 0 en caso contrario.

---

## Imágenes

Para mostrar imágenes, tenemos que comprimir ficheros en formato SCR de la pantalla de Spectrum con la utilidad `CSC`.  
Los ficheros deben estar nombradas con un número de 3 dígitos, que corresponderá al número de imagen que se invocará desde el programa, es decir, `000.CSC` para la imagen 0, `001.CSC` para la imagen 1, y así con el resto.

Se puede configurar el número de líneas horizontales de la imagen a mostrar usando el parámetro correspondiente con la utilidad `CSC` para reducir aún más el tamaño. Además, si detecta que la mitad derecha de la misma está espejada con la izquierda, descarta ésta para reducir aún mas el tamaño, aunque se puede forzar esto con otro parámetro de la misma.

Hay dos comandos necesarios para mostrar una imagen, el comando `PICTURE n` cargará en un buffer la imagen n. Es decir, si hacemos `PICTURE 1`, cargará el fichero `001.CSC` en el buffer. Esto es útil para controlar cuándo se debe cargar la imagen, ya que supondrá espera desde el disco (por ejemplo, hacerlo al iniciar un capítulo). Si se carga una imagen cuyo fichero no existe, se generará el error de disco 23.

Para mostrar una imagen cargada en el buffer, usamos `DISPLAY n`, donde n tiene que ser cero para ejecutarse. La imagen que se mostrará será la última cargada en el buffer (si existe). La imagen comienza a pintarse desde la esquina superior izquierda de la pantalla y se dibujan tantas líneas como las indicadas al comprimir el fichero y se sobrescribe todo lo que hubiese en pantalla hasta el momento.

---

## Efectos de sonido

Añadir efectos de sonido con el beeper es muy sencillo. Para ello tenemos que crear un banco de efectos con la utilidad BeepFx. Debemos exportar el fichero de efectos como un fichero en ensamblador usando la opción `File->Compile` del menú superior. En la ventana flotante que aparece, debemos asegurarnos de que tenemos seleccionado `Assembly` e `Include Player Code`, el resto de opciones son irrelevantes, ya que el compilador modificará el fichero fuente para incrustarlo en el intérprete.

Para invocar un efecto, usamos el comando `SFX n`, siendo n el número del efecto a reproducir. Si se llama a este comando sin que exista un fichero de efectos cargado, será ignorado y seguirá la ejecución.

No está contemplado llamar a un número de efecto que no exista en el fichero incluido.

---

## Melodías

El motor `CYD` también permite reproducir módulos de música creados con Vortex Tracker en formato `PT3`. Su funcionamiento replica el mecanismo de carga de imágenes, es decir, los módulos deben nombrarse con tres dígitos que representan el número de pista que el intérprete cargará con el comando `TRACK`. Por ejemplo, si el intérprete encuentra el comando `TRACK 3`, entonces buscará la pista del fichero `003.PT3` y cargará en memoria el módulo para su reproducción. Y de la misma manera, el máximo número de módulos que se pueden cargar son 256 (de 0 a 255) y no se permite que el módulo sea de más de 16 Kilobytes.

Una vez cargado un módulo, se podrá reproducir con el comando `PLAY`. Como se indica en la referencia de comandos, si el parámetro es distinto de cero, se reproducirá el módulo; y si es igual a cero, se detendrá la reproducción.

Cuando se llegue al final del módulo, la reproducción se detendrá automáticamente, pero podemos cambiar este comportamiento con el comando `LOOP`. De nuevo, según se indica en la referencia, si el parámetro es igual a cero, al llegar al final se detendrá la reproducción, como se ha indicado antes. Pero si el parámetro es distinto de cero, el módulo volverá a reproducirse desde el principio.

---

## Cómo generar una aventura

Lo primero es generar un guion de la aventura mediante cualquier editor de textos empleando la sintaxis arriba descrita. Es MUY recomendable hacer el guion de la misma antes de ponerse a programar la lógica ya que conviene tener el texto perfilado antes para tener una compresión adecuada (más detalles más adelante).

Es importante que la codificación del fichero sea UTF-8, pero hay que tener en cuenta que caractéres por encima de 128 no se imprimirán bien y sólo se admiten los caracteres propios del castellano, indicados en la sección [Juego de Caracteres](#juego-de-caracteres), que serán convertidos a los códigos allí indicados.

Una vez tenemos la aventura, usamos el compilador `CYDC` para generar un fichero DSK o TAP. EL compilador busca las mejores abreviaturas para comprimir el texto lo máximo posible. El proceso puede ser muy largo dependiendo del tamaño de la aventura. Por eso es importante tener la aventura perfilada antes, para realizar este proceso al principio. La compilación la realizaremos con el parámetro `-T` de tal manera que con `-T abreviaturas.json`, por ejemplo, exportaremos las abreviaturas encontradas al fichero _abreviaturas.json_.

A partir de este momento, si ejecutamos el compilador con el parámetro `-t abreviaturas.json`, éste no realizará la búsqueda de abreviaturas y usará las que ya habíamos encontrado antes, con lo que la compilación será casi instantánea.  
Cuando ya consideremos que la aventura está terminada, podremos volver a realizar una nueva búsqueda de abreviaturas para intentar conseguir algo más de compresión.

Para añadir efectos de sonido, imágenes y melodías, consulta las secciones correspondientes.

El proceso es bastante simple, pero tiene algunos pasos dependientes, con lo que se recomienda usar ficheros BAT (Windows) o guiones de shell (Linux, Unix) o la utilidad Make (o similar) para acelerar el desarrollo.

Para facilitar las cosas, se incluye un programa llamado `make_adventure.py` que realizará todas estas tareas por nosotros, además de los correspondientes scripts `make_adv.cmd` para Windows y `make_adv.sh` para UNIX para ejecutarlo.

El programa `make_adventure.py` buscará y comprimirá automáticamente los ficheros SCR que se atengan al formato de nombre establecido (número de 0 a 255 con 3 dígitos) dentro del directorio `.\IMAGES`. Lo mismo hará con los módulos que haya dentro del directorio `.\TRACKS` que cumplan el formato de nombre. Luego compilará el fichero `test.txt` y generará el fichero `tokens.json` con las abreviaturas, si no existiese previamente. Si se desea que se vuelva a generar el fichero de abreviaturas, simplemente borrándolo hará que el script indique al compilador que lo genere de nuevo. Además buscará de forma automática si existe un fichero de efectos de sonido llamado `SFX.ASM` que debe generarse con **BeepFX**, y si existiese un fichero JSON con el juego de caracteres llamado `charset.json`, también lo utilizará.

Este programa necesita los directorios `dist` y `tools` con su contenido para realizar el proceso. Ahora se detallan las peculiaridades en cada sistema operativo:

### Windows

Como ejemplo se ha incluido el fichero `make_adv.cmd` en la raíz del repositorio, que compilará la aventura de muestra incluida en el fichero `test.cyd`.

Puedes usarlo como base para crear tu propia aventura de forma sencilla. Se puede personalizar el comportamiento modificando en la cabecera del script algunas variables:

```batch
REM ---- Configuration variables ----------

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.cyd with this example
REM   - The name of the TAP file or +3 disk image

REM Target for the compiler (48k, 128k for TAP, plus3 for DSK)
SET TARGET=plus3

REM Number of lines used on SCR files at compressing
SET IMGLINES=192

REM Loading screen
SET LOAD_SCR="LOAD.scr"

REM Parameters for compiler
SET CYDC_EXTRA_PARAMS=

REM --------------------------------------
```

- La variable `GAME` será el nombre del fichero txt que se compilará y el nombre del fichero DSK o TAP resultante.
- La variable `TARGET` es el sistema y formato de salida, con estas posibles opciones:
  -- 48k: Genera un fichero TAP para Spectrum 48K, sin soporte de música AY.
  -- 128k: Genera un fichero TAP para Spectrum 128K.
  -- plus3: Genera un fichero DSK para Spectrum +3, con mayor capacidad y carga dinámica de recursos.
- La variable `IMGLINES` es el número de líneas horizontales de los ficheros de imagen que se comprimirán. Por defecto es 192 (la pantalla completa del Spectrum)
- La variable `LOAD_SCR` es la ruta a un fichero de tipo SCR (pantalla de Spectrum) con la pantalla que se usará durante la carga.

El guión producirá un fichero DSK o TAP (dependiendo del formato seleccionado en `TARGET`) que podrás ejecutar con tu emulador favorito. Pero si deseas acelerar más el trabajo, si te descargas [Zesarux](https://github.com/chernandezba/zesarux) y lo instalas en de la carpeta `.\tools\zesarux`, tras la compilación se ejecutará automáticamente con las opciones adecuadas.

### Linux, BSDs

Como ejemplo se ha incluido el fichero `make_adv.sh` en la raíz del repositorio, que compilará la aventura de muestra incluida en el fichero `test.cyd`.

Puedes usarlo como base para crear tu propia aventura de forma sencilla. Se puede personalizar el comportamiento modificando en la cabecera del script algunas variables:

```bash
# ---- Configuration variables ----------
# Name of the game
GAME="test"
# This name will be used as:
#   - The file to compile will be test.cyd with this example
#   - The name of the TAP file or +3 disk image
#
# Target for the compiler (48k, 128k for TAP, plus3 for DSK)
TARGET="plus3"
#
# Number of lines used on SCR files at compressing
IMGLINES="192"
#
# Loading screen
LOAD_SCR="./LOAD.scr"
#
# Parameters for compiler
CYDC_EXTRA_PARAMS=
# --------------------------------------
```

- La variable `GAME` será el nombre del fichero txt que se compilará y el nombre del fichero DSK o TAP resultante.
- La variable `TARGET` es el sistema y formato de salida, con estas posibles opciones:
  -- 48k: Genera un fichero TAP para Spectrum 48K, sin soporte de música AY.
  -- 128k: Genera un fichero TAP para Spectrum 128K.
  -- plus3: Genera un fichero DSK para Spectrum +3, con mayor capacidad y carga dinámica de recursos.
- La variable `IMGLINES` es el número de líneas horizontales de los ficheros de imagen que se comprimirán. Por defecto es 192 (la pantalla completa del Spectrum)
- La variable `LOAD_SCR` es la ruta a un fichero de tipo SCR (pantalla de Spectrum) con la pantalla que se usará durante la carga.

## Ejemplos

Dispones de una serie de ejemplos para comprobar las capacidades del motor y aprender de ellos:

- En la carpeta `examples\test` hay una muestra ampliada del ejemplo incluido en la sección de [Sintaxis](#sintaxis). Se incluye imágenes de prueba en el directorio `examples\test\IMAGES`, y una canción de prueba dentro de su directorio `examples\test\TRACKS`.

- En la carpeta `examples\ETPA_ejemplo` tienes un ejemplo del comienzo de un libro tipo "Elije Tu Propia Aventura" simple, que resulta algo más avanzado. Se incluyen imágenes de prueba en `examples\ETPA_ejemplo\IMAGES`

- En la carpeta `examples\guess_the_number` hay un ejemplo de uso para menús de múltiples columnas.

- En la carpeta `examples\input_test` se muestra cómo leer desde el teclado y el uso de la indirección para simular arrays.

- En la carpeta `examples\blit` se muestra el uso del comando `BLIT`, con ejemplos progresivamente más avanzados en `examples\blit_island`, `examples\Rocky_Horror_Show` y `examples\CYD_presents`. En la subcarpeta `IMAGES` se incluyen las imágenes de prueba.

- En la carpeta `examples\Golden_Axe_select_character` podrás aprender sobre los comandos `FILLATTR` y `CHOOSE IF CHANGED...`. En la subcarpeta `IMAGES` se incluyen las imágenes de prueba.

Para probarlos en vivo, simplemente habría que copiar los ficheros y directorios del ejemplo que quieras probar en el directorio principal de la distribución y ejecutar `make_adv.cmd`. Recuerda borrar (y guardar si fuese el caso) los ficheros que ya existiesen antes.

---

## Juego de caracteres

El motor soporta un juego de 256 caracteres, con 8 píxeles de altura y tamaño variable de ancho.  
El juego de caracteres por defecto incluido tiene un tamaño 6x8, excepto los caracteres del 127 al 143, que son especiales (ver más adelante) y tienen un tamaño 8x8. Éste es el juego de caracteres por defecto, ordenados de izquierda a derecha y de arriba a abajo:

![Juego de caracteres por defecto](assets/default_charset.png)

Los carácteres corresponden con el ASCII estándar, excepto los extendidos (mayor o igual que 128 hasta 255) y los de control (menores que 32).  
Los carácteres propios del castellano, corresponden a las siguientes posiciones:

| Carácter | Posición |
| -------- | -------- |
| 'ª'      | 16       |
| '¡'      | 17       |
| '¿'      | 18       |
| '«'      | 19       |
| '»'      | 20       |
| 'á'      | 21       |
| 'é'      | 22       |
| 'í'      | 23       |
| 'ó'      | 24       |
| 'ú'      | 25       |
| 'ñ'      | 26       |
| 'Ñ'      | 27       |
| 'ü'      | 28       |
| 'Ü'      | 29       |

Los caracteres por encima del valor 127 (empezando desde cero) son especiales, como ya se ha indicado. Son utilizados como iconos en las opciones, es decir, en donde aparece una opción cuando se procesa el comando `OPTION`, y como indicadores de espera con un `WAITKEY` o al cambiar de página si el comando `PAGEPAUSE` está activo.

- El carácter 127 es el carácter usado cuando una opción no está seleccionada en un menú. (En rojo en la captura inferior)
- Los caracteres del 128 al 135 forman el ciclo de animación de una opción seleccionada en un menú. (En verde en la captura inferior)
- Los caracteres del 135 al 143 forman el ciclo de animación del indicador de espera. (En azul en la captura inferior)

![Caracteres especiales](assets/special_characters.png)

El compilador dispone de dos parámetros, `-c` para importar un juego de caracteres nuevo, y `-C` para exportar el juego de caracteres actualmente empleado, por si puede servir de plantilla o realizar personalizaciones.

Este es el formato de importación/exportación del juego de caracteres:

```python
[{"Id": 0, "Character": [255, 128, ...], "Width":8}, {"Id": 1, "Character": [0, 1, ...], "Width":6}, ...]
```

Es un JSON con un array de registros de tres campos:

- _Id_: número del carácter de 0 a 255, que no se puede repetir.
- _Character_: un array de 8 números que corresponde con el valor de los bytes del caracter y, por tanto, no puede haber valores mayores de 255. Cada byte corresponde con los pixels de cada línea del carácter.
- _Width_: un array con el ancho en pixels del carácter (los valores no pueden ser menores que 1 ni mayores que 8). Dado que el tamaño de cada línea del carácter del campo anterior es 8, los píxeles que sobren por la derecha serán descartados.

Para facilitar la tarea de creación de un juego de caracteres alternativo, se ha incluido la herramienta [CYD Character Set Converter](#cyd-character-set-converter) o cyd_chr_conv. Esta herramienta permite convertir fuentes en formato `.chr`, `.ch8`, `.ch6` y `.ch4` creadas con ZxPaintbrush en el formato JSON anteriormente mencionado. Además, en el directorio `assest` de la distribución podrás encontrar el fichero `default_charset.chr` con la fuente por defecto para que puedas editarla y personalizarla con dicho programa.

---

## Códigos de error

La aplicación puede generar errores en tiempo de ejecución. Los errores son de dos tipos, de disco y del motor.  
Los errores de disco son los errores que pudiesen ocasionarse cuando el motor del juego accede al disco, y corresponden con los errores de +3DOS:

- Error 0: Drive not ready
- Error 1: Disk is write protected
- Error 2: Seek fail
- Error 3: CRC data error
- Error 4: No data
- Error 5: Missing address mark
- Error 6: Unrecognised disk format
- Error 7: Unknown disk error
- Error 8: Disk changed whilst +3DOS was using it
- Error 9: Unsuitable media for drive
- Error 20: Bad filename
- Error 21: Bad parameter
- Error 22: Drive not found
- Error 23: File not found
- Error 24: File already exists
- Error 25: End of file
- Error 26: Disk full
- Error 27: Directory full
- Error 28: Read-only file
- Error 29: File number not open (or open with wrong access)
- Error 30: Access denied (file is in use already)
- Error 31: Cannot rename between drives
- Error 32: Extent missing (which should be there)
- Error 33: Uncached (software error)
- Error 34: File too big (trying to read or write past 8 megabytes)
- Error 35: Disk not bootable (boot sector is not acceptable to DOS BOOT)
- Error 36: Drive in use (trying to re-map or remove a drive with files open)

La aparición de estos errores ocurre cuando se accede al disco, al buscar más trozos de texto, imágenes, etc. Si aparece el error 23 (File not found), suele ser que se haya olvidado de incluir algún fichero necesario en el disco. Otros errores ya suponen algún error de la unidad de disco o del propio disco.

Los errores de motor son, como su nombre indica, los errores propios del motor cuando detecta una situación anómala. Son los siguientes:

- Error 1: El trozo accedido no existe. (Se intenta acceder a un fragmento no existente en el índice)
- Error 2: Se han creado demasiadas opciones, se ha superado el límite de opciones posibles.
- Error 3: No hay opciones disponibles, se ha lanzado un comando `CHOOSE` sin tener antes ninguna `OPTION`.
- Error 4: El fichero con el módulo de música a cargar es demasiado grande, tiene que ser menor que 16Kib.
- Error 5: No hay un módulo de música cargado para reproducir.
- Error 6: Código de instrucción inválido.

---

## F.A.Q

(TBC)

---

## Referencias y agradecimientos

- David Beazley por [PLY](https://www.dabeaz.com/ply/ply.html)
- Einar Saukas por el compresor [ZX0](https://github.com/einar-saukas/ZX0).
- DjMorgul por el buscador de abreviaturas, adaptado de [Daad Reborn Tokenizer](https://https://github.com/daad-adventure-writer/DRT)
- Shiru por [BeepFx](http://shiru.untergrund.net).
- Seasip por mkp3fs de [Taptools](http://www.seasip.info/ZX/unix.html).
- [Tranqui69](https://mastodon.social/@tranqui69) por el logotipo.
- XimoKom y Fran Kapilla por su inestimable ayuda en las pruebas del motor.
- 𝕊𝕖𝕣𝕘𝕚𝕠 ᵗʰᴱᵖᴼᵖᴱ por meterme el gusanillo del Plus3.
- Pablo Martínez Merino por la ayuda con el testeo en Linux y ejemplos.
- [El_Mesías](https://twitter.com/El__Mesias__), [Arnau Jess](https://twitter.com/arnauballe) y la gente de [CAAD](https://caad.club) por el apoyo.

---

## Licencia

Copyright (c) 2024 Sergio Chico

Por la presente se concede permiso, libre de cargos, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados (el "Software"), a utilizar el Software sin restricción, incluyendo sin limitación los derechos a usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar, y/o vender copias del Software, y a permitir a las personas a las que se les proporcione el Software a hacer lo mismo, sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas las copias o partes sustanciales del Software.
EL SOFTWARE SE PROPORCIONA "COMO ESTÁ", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A GARANTÍAS DE COMERCIALIZACIÓN, IDONEIDAD PARA UN PROPÓSITO PARTICULAR E INCUMPLIMIENTO. EN NINGÚN CASO LOS AUTORES O PROPIETARIOS DE LOS DERECHOS DE AUTOR SERÁN RESPONSABLES DE NINGUNA RECLAMACIÓN, DAÑOS U OTRAS RESPONSABILIDADES, YA SEA EN UNA ACCIÓN DE CONTRATO, AGRAVIO O CUALQUIER OTRO MOTIVO, DERIVADAS DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE O SU USO U OTRO TIPO DE ACCIONES EN EL SOFTWARE.
