# Choose Your Destiny

El programa es un interprete para ejecutar historias de tipo "Escoje tu propia aventura" o aventuras por opciones, para el Spectrum +3.

Consiste una máquina virtual que va intepretando "tokens" que se encuentra durante el texto para realizar las distintas acciones interactivas y un compilador que se encarga de traducir la aventura desde un lenguaje mas "humano" con el que se escribe el guión de la aventura, a un fichero interpretable por el motor.

El intérprete lee en cada momento un trozo de la aventura llamado "chunk" o "trozo" que ocupa 16 Kbytes, el mismo tamaño que el banco del Spectrum. El compilador divide el guión en estos fragmentos y ajusta de forma correspondiente las referencias a las direcciones. Cuando el intérprete debe cambiar en "trozo" en ejecución, lo carga de disco.

Además, también puede mostrar imágenes comprimidas y almacenadas en el mismo disco, así como efectos de sonido basados en BeepFX de Shiru.

---

## CYDC (Compilador)

Este programa es el compilador que traduce el texto de la aventura a un fichero interpretable por el motor, llamado **SCRIPT.DAT**. Además de compilar la lógica de la aventura, realiza una búsqueda heurística de las mejores abreviaturas para reducir el tamaño del texto.

```
cydc.exe [-h] [-l MIN_LENGTH] [-L MAX_LENGTH] [-s SUPERSET_LIMIT]
         [-T EXPORT-TOKENS_FILE] [-t IMPORT-TOKENS-FILE]
         [-C EXPORT-CHARSET] [-c IMPORT-CHARSET] [-v] [-V]
         input.txt SCRIPT.DAT
```

- **\-h**: Muestra la ayuda
- **\-l MIN_LENGTH**: La longitud mínima de las abreviaturas a buscar (por defecto, 3).
- **\-L MAX_LENGTH**: La longitud máxima de las abreviaturas a buscar (por defecto, 30).
- **\-s SUPERSET_LIMIT**: Límite para el super-conjunto de la heurística de la búsqueda (por defecto, 100).
- **\-T EXPORT-TOKENS_FILE**: Exportar al fichero JSON indicado por el parámetro las abreviaturas encontradas.
- **\-t IMPORT-TOKENS-FILE**: Importar abreviaturas desde el fichero indicado y obviar la búsqueda de las mismas.
- **\-C EXPORT-CHARSET**: Exporta el juego de caracteres 6x8 usado por defecto en formato JSON.
- **\-c IMPORT-CHARSET**: Importa en formato JSON el juego de caracteres 6x8 a emplear.
- **\-v**: Modo verboso, da más información del proceso.
- **\-V**: Indica la versión del programa.
- **input.txt**: Fichero de entrada con el guión de la aventura.
- **SCRIPT.DAT**: Fichero de salida para el motor.

---

## CYD (Motor)

Este es el motor principal del juego, y que debe incluirse en el disco junto con el fichero **SCRIPT.DAT** y el cargador **DISK** para tener una aventura funcional.

La aventura se puede lanzar con en autolanzador del menú de inicio del Spectrum +3 o desde Basic con el comando `LOAD"DISK"`.

Opcionalmente, se pueden incluir imágenes comprimidas con la utilidad CSC y efectos de sonido añadiendo un fichero generado con dicha utilidad llamado `BEEPFX.BIN`. Mas información en las secciones relevantes.

---

## CSC (Compresor de Imágenes)

Esta utilidad permite comprimir imágenes tipo **SCR** de ZX Spectrum para mostrarlas en el motor. Las pantallas pueden ser completas, o se puede limitar el número de líneas horizontales para ahorrar memoria. Además detecta imágenes espejadas (simétricas) por el eje vertical, con lo que sólo almacena la mitad de la misma, pudíendose forzar este comportamiento descartando el lado derecho de la imagen.

```
CSC [-f] [-m] [-l=num_lines] [-o=output] input
  -f, --force                Force overwrite of output file
  -m, --mirror               The right side of the image is the reflection of the left one.
  -o, --output=FILE          Output path for the file
  -l, --num-lines=NUMBER     Number of visible lines
  -h, --help                 Shows the command help
```

Esto es una definición de los parámetros:

- **\-f, --force**: Fuerza la sobre-escritura del fichero de destinosi ya existiese.
- **\-m, --mirror**: Descarta el lado derecho de la imagen y usa la imagen espejada del izquierdo.
- **\-o, --output=FILE**: Ruta del salida del fichero comprimido.
- **\-l, --num-lines=NUMBER**: Número de líneas de la pantalla a tratar (en carácteres, de 1 a 24).
- **\-h, --help**: Muestra la ayuda.

El motor soporta un máximo de 256 imágenes, aparte de lo que quepa en el disco, y deben estar nombradas con un número de 3 dígitos, que corresponderá al número de imagen que se invocará desde el programa. Por ejemplo, la imagen 0 debería llamarse `000.CSC`, la imagen número 1 `001.CSC`, y así hasta 255.

---

## Sintaxis

La sintaxis del guión es sencilla, y está orientada más a la escritura y la presentación que a la lógica programable.  
Todo texto que aparezca en el fichero se considera texto, incluidos los espacios y saltos de línea, y se presentarán como tal por el intérprete.  
La parte programable se define dentro de dos pares de corchetes, abiertos y cerrados respectivamente.  
Este es un ejemplo resumido y auto-explicativo de la sintaxis:

```
Esto es texto [[ INK 6 ]] Esto es texto de nuevo
    Sigue siendo texto [[
# Esto es un comentario dentro del código
        WAITKEY
        INK 7: PAPER 0
# Los comandos se separan por saltos de línea o dos puntos en la misma línea
    ]]
    Esto vuelve a ser texto.
```

El intérprete recorre el texto desde el principio, imprimiéndolo en pantalla. Cuando una palabra completa no cabe en lo que queda de la línea, la imprime en la línea siguiente. Y si no cabe en lo que queda de pantalla, se genera una espera y petición al usuario de que pulse la tecla de confirmación para borrar la sección de texto y seguir imprimendo.

Los comandos permiten introducir lógica programable dentro del texto para hacerlo dinámico y variado según ciertas condiciones. La más común y poderosa es la de solicitar escoger al jugador entre una serie de opciones (hasta un límite de 8), y que puede seleccionar con las teclas `P` y `Q` y seleccionar con `SPACE` o `ENTER`.  
De nuevo, éste es un ejemplo autoexplicativo:

```
Elige una opción:
[[OPTION GOTO Opcion1]]Primera opción.
[[OPTION GOTO Opcion2]]Segunda opción.
[[OPTION GOTO Opcion3]]Tercera opción.
[[
    CHOOSE
    LABEL Opcion1]]Has elegido la opción 1.
[[
    GOTO Final
    LABEL Opcion2]]Has elegido la opción 2.
[[
    GOTO Final
    LABEL Opcion3]]Has elegido la opción 3.
[[  LABEL Final ]] Gracias por jugar.
```

El comando `OPTION GOTO etiqueta` generará un punto de selección en el lugar donde se haya llegado al comando.  
Cuando llegue al comando `CHOOSE`, el intérprete permitirá elegir al usuario entre uno de los puntos de opción que haya acumulados en pantalla hasta el momento. Se permiten un máximo de 8 y siempre que la pantalla no se borre antes, ya que entonces se eliminarán las opciones acumuladas.

Al escoger una opción, el interprete saltará a la sección del texto donde se encuentre la etiqueta correspondiente indicada en la opción. Las etiquetas se declaran con el pseudo-comando `LABEL identificador` dentro del código, y cuando se indica un salto a la misma, el intérprete comenzará a procesar a partir del punto en donde hemos declarado la etiqueta.  
En el caso del ejemplo, si elegimos la opción 1, el intérprete saltará al punto indicado en `LABEL Opcion1`, con lo que imprimirá el texto _"Has elegido la opción 1"_, y después pasa a `GOTO final` que hará un salto incondicional a donde está definido `LABEL Final`, motrando "_Gracias por jugar_" e ignorando todo lo que haya entre medias.

Los identificadores de las etiquetas sólo soportan caracteres alfanuméricos (cifras y letras) y son sensibles al caso (se distinguen mayúsculas y minúsculas), es decir `LABEL Etiqueta` no es lo mismo que `LABEL etiqueta`. Los comandos, por el contrario, no son sensibles al caso, pero por claridad, es recomendable ponerlos en mayúsculas.

Además, hay a disposición del programador 256 variables o 'flags' de un byte para almacenar valores y realizar operaciones con ellos o realizar saltos de acuerdo a comparaciones con los valores contenidos en ellos.

Algunos comandos pueden hacer uso de indirección, indicada por `@`, es decir que el valor indicado no es el valor a utilizar, si no que el valor lo obtiene de la variable indicada. Es decir:

```
INK 7
INK @7
```

El primer comando pondrá el color del texto en blanco (color 7), mientras que el segundo pondrá el color del texto con el valor contenido en la variable número 7.

---

## Comandos

### END

Finaliza la aventura y reinicia el Spectrum.

### CLEAR

Borra el área de texto definida.

### GOTO labelId

Salta a la etiqueta labelId.

### GOSUB labelId

Salto de subrutina, hace un salto a la etiqueta labelId, pero vuelve a este punto en cuanto encuentra un comando `RETURN`.  
Se permiten hasta 8 niveles de anidamiento.

### RETURN

Retorna al punto de llamada de una subrutina, ver `GOSUB`

### LABEL labelId

Declara la etiqueta labelId en este punto. Todos los saltos con referencia a esta etiqueta dirigirán a partir de aquí.

### CENTER

Pone el cursor de impresión en el centro de la línea.

### WAITKEY

Espera la pulsación de la tecla de aceptación para continuar, presentando un icono animado de espera. Ideal para separar párrafos o pantallas.

### OPTION GOTO labelId

Crea un punto de opción que el usuario puede seleccionar (ver `CHOOSE`). Si confirma esta opción, salta a la etiqueta _labelId_. Si se borra la pantalla, el punto de opción se elimina y sólo se permiten 8 como máximo en una pantalla.

### CHOOSE

Permite al jugador seleccionar una de las opciones que haya en este momento en pantalla.

### CHOOSE IF WAIT expression THEN GOTO labelId

Funciona exactamente igual que `CHOOSE`, pero con la salvedad de que se declara un timeout, que si se agota sin seleccionar ninguna opción, salta a la etiqueta _LabelId_.  
El timeout tiene como máximo 65535 (16 bits).

### INKEY expression

Espera a la pulsación de la tecla con el código indicado.

### CHAR expression

Imprime el carácter indicando con su número correspondiente.

### PRINT expression

Imprime el valor indicado (máximo 16 bits).

### PRINT @ flag_no

Imprime el valor del flag indicado.

### TAB expression

Desplaza el cursor a la derecha tantas posiciones como indicadas en el parámetro.

### PAGEPAUSE expression

Controla si al rellenar el área de texto actual, debe solicitar continuar al jugador, presentando un icono animado de espera (parámetro \<> 0) ó hace un borrado de pantalla y sigue imprimiendo (parámetro = 0).

### INK expression

Define el valor del color de los caracteres (tinta). Valores de 0-7.

### INK @ flag_no

Igual que ´INK´ pero usando indirección con un flag cuyo contenido será el color a emplear.

### PAPER expression

Define el valor del color del fondo (papel). Valores de 0-7.

### PAPER @ flag_no

Igual que ´PAPER´ pero usando indirección con un flag cuyo contenido será el color a emplear.

### BORDER expression

Define el color del borde, valores 0-7.

### BORDER @ flag_no

Igual que ´BORDER´ pero usando indirección con un flag cuyo contenido será el color a emplear.

### BRIGHT expression

Activa o desactiva el brillo (0 desactivado, 1 activado).

### BRIGHT @ flag_no

Igual que ´BRIGHT´ pero usando indirección con un flag dado.

### FLASH expression

Activa o desactiva el parpadeo (0 desactivado, 1 activado).

### FLASH @ flag_no

Igual que ´BRIGHT´ pero usando indirección con un flag dado.

### SFX expression

Si se ha cargado un fichero de efectos de sonido, reproduce el efecto indicado.  
Si no se ha cargado dicho fichero, el comando es ignorado.

### SFX @ flag_no

Si se ha cargado un fichero de efectos de sonido, reproduce el efecto indicado en el flag correspondiente.  
Si no se ha cargado dicho fichero, el comando es ignorado.

### PICTURE expression

Carga en el buffer la imagen indicada como parámentro. Por ejemplo, si se indica 3, cargará el fichero `003.CSC`.  
La imagen no se muestra, lo que permite controlar cuándo se realiza la carga del fichero.

### PICTURE @ flag_no

Igual que `PICTURE`, pero usando el contenido de una variable como parámetro.

### DISPLAY expression

Muestra el contenido actual del buffer en pantalla.  
El parámetro indica si se muestra o no la imagen, con un 0 se muestra, y con un valor distinto de cero, no. En este caso, esta funcionalidad no es útil, pero sí lo es en su versión indirecta.  
Se muestran tantas líneas como se hayan definido en la imagen correspondiente y el contenido de la pantalla será sobreescrito.

### DISPLAY @ flag_no

Igual que `DISPLAY`, pero el parámetro que indica si se muestra o no, lo toma de una variable.

### WAIT expression

Realiza una pausa. El parámetro es el número de "fotogramas" (50 por segundo) a esperar, y es un número de 16 bits.

### PAUSE expression

Igual que `WAIT`, pero con la salvedad de que el jugador puede abortar la pausa con la pulsación de la tecla de confirmación.

### TYPERATE expression

Indica la pausa que debe haber entre la impresión de cada carácter. Mínimo 1, máximo 65535.

### MARGINS expression COMMA expression COMMA expression COMMA expression

Define el área de pantalla donde se escribirá el texto. Los parámetros, por órden, son:

- Columna inicial.
- Fila inicial.
- Ancho (en carácteres).
- Alto (en carácteres).

Los tamaños y posiciones siempre se definen como si fuesen caracteres 8x8.

### AT expression COMMA expression

Sitúa el cursor en una posición dada, relativa al área definida por el comando `MARGINS`.  
Los parámetros, por órden, son:

- Columna relativa al origen del área de texto.
- Fila relativa al origen del área de texto.

Las posiciones se asumen en tamaño de carácter 8x8.

### SET flag_no TO RANDOM

Almacena en el flag indicado un número aleatorio.

### SET NOT flag_no

Complementa los bits contenidos en el flag indicado.

### SET flag_no TO expression

Almacena en el flag indicado el valor del segundo parámetro (Sólo puede ser de un byte).

### SET flag_no TO @ flag_no

Almacena en el flag indicado en el primer parámetro el valor del segundo flag.

### SET flag_no + expression

Almacena en el flag indicado la suma de su contenido con el valor del segundo parámetro.  
Si la suma supera 255, entonces queda como 255.

### SET flag_no + @ flag_no

Almacena en el flag indicado la suma de su contenido con el contenido del flag del segundo parámetro.  
Si la suma supera 255, entonces queda como 255.

### SET flag_no - expression

Almacena en el flag indicado la resta de su contenido con el valor del segundo parámetro.  
Si la resta resulta menor que cero, queda almacenado cero.

### SET flag_no - @ flag_no

Almacena en el flag indicado la resta de su contenido con el contenido del flag del segundo parámetro.  
Si la resta resulta menor que cero, queda almacenado cero.

### SET flag_no AND expression

Almacena en el flag indicado la "Y" lógica de su contenido con el valor del segundo parámetro.

### SET flag_no AND @ flag_no

Almacena en el flag indicado la "Y" lógica de su contenido con el contenido del flag del segundo parámetro.

### SET flag_no OR expression

Almacena en el flag indicado la "O" lógica de su contenido con el valor del segundo parámetro.

### SET flag_no OR @ flag_no

Almacena en el flag indicado la "O" lógica de su contenido con el contenido del flag del segundo parámetro.

### IF flag_no = expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual al segundo, salta a la etiqueta indicada.

### IF flag_no = @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual al contenido del flag indicado por el segundo, salta a la etiqueta indicada.

### IF flag_no \<> expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro no es igual al segundo, salta a la etiqueta indicada.

### IF flag_no \<> @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro no es igual al contenido del flag indicado por el segundo, salta a la etiqueta indicada.

### IF flag_no \<= expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual o menor que el segundo, salta a la etiqueta indicada.

### IF flag_no \<= @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual o menor que el contenido del flag indicado por el segundo, salta a la etiqueta indicada.

### IF flag_no >= expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual o mayor que el segundo, salta a la etiqueta indicada.

### IF flag_no >= @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es igual o mayor que el contenido del flag indicado por el segundo, salta a la etiqueta indicada.

### IF flag_no \< expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es menor que el segundo, salta a la etiqueta indicada.

### IF flag_no \< @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es menor que el contenido del flag indicado por el segundo, salta a la etiqueta indicada.

### IF flag_no > expression THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es mayor que el segundo, salta a la etiqueta indicada.

### IF flag_no > @ flag_no THEN GOTO labelId

Si el contenido del flag indicado por el primer parámetro es mayor que el contenido del flag indicado por el segundo, salta a la etiqueta indicada.

---

## Cómo generar una aventura

Lo primero es generar un guión de la aventura mediante cualquier editor de textos empleando la sintaxis arriba descrita. Es MUY recomendable hacer el guión de la misma antes de ponerse a programar la lógica ya que conviene tener el texto perfilado antes para tener una compresión adecuada (más detalles en el siguiente párrafo). Es importante que la codificación del fichero sea UTF-8.

Una vez tenemos la aventura, usamos el compilador `CYDC` para generar el fichero **SCRIPT.DAT**. EL compilador busca las mejores abreviaturas para comprimir el texto lo máximo posible. El proceso puede ser muy largo dependiendo del tamaño de la aventura. Por eso es importante tener la aventura perfilada antes, para realizar este proceso al principio. La compilación la realizaremos con el parámetro `-T` de tal manera que con `-T abreviaturas.json`, por ejemplo, exportaremos las abreviaturas encontradas al fichero _abreviaturas.json_.

A partir de este momento, si ejecutamos el compilador con el parámetro `-t abreviaturas.json`, éste no realizará la búsqueda de abreviaturas y usará las que ya habíamos encontrado antes, con lo que la compilación será casi instantánea.  
Cuando ya consideremos que la aventura está terminada, podremos volver a realizar una nueva búsqueda de abreviaturas para intentar conseguir algo más de compresión, si hemos hecho muchas ediciones posteriores.

Si son necesarias imágenes, las comprimimos con CDC con el detalle ya indicado que deben estar nombradas con un número de 3 dígitos, que corresponderá al número de imagen que se invocará desde el programa (`000.CSC`, `001.CSC`, y así).

Si queremos añadir efectos de sonido, tendremos que usar el programa BeepFX de Shiru. Debemos exportar el fichero de efectos como un binario, que se llamará `BEEPFX.BIN` y a la hora de exportarlo **debemos indicar** como dirección inicial **49152** en decimal ó lo que es lo mismo, **0xC000** en hexadecimal.

Con esto, ya podemos ejecutar la aventura. Para ello, si usamos un emulador, tendremos que usar algún programa que nos permita crear imágenes de discos +3. Con ella incluimos los ficheros `CYD.BIN`, `SCRIPT.DAT`, los ficheros de imágenes `*.CSC` (si existiesen) y el fichero `BEEPFX.BIN` como se ha indicado antes.

Y con esto podríamos ejecutar la aventura. El proceso es bastante simple, pero tiene algunos pasos dependientes, con lo que se recomienda usar ficheros BAT (Windows) o guiones de shell (Linux, Unix) o la utilidad Make (o similar) para acelerar el desarrollo.

---

## Juego de caracteres

El motor soporta un juego de 256 caracteres, con 8 píxeles de altura y tamaño variable de ancho.  
El juego de caracteres por defecto incluido, tiene un tamaño 6x8, excepto los caracteres del 127 al 142, que son especiales (ver más adelante). El compilador dispone de dos parámetros, `-c` para importar un juego de caracteres nuevo, y `-C` para exportar el juego de caracteres actualmente empleado (por si puede servir de plantilla).

Este es el formato de importación del juego de caracteres:

```json
{"Character": [255, 128, ...], "Width":[8, 6, ...]}
```

Es un JSON con dos campos, _Character_, con un array de números que corresponde con el valor de los bytes del juego de caracteres, y _Width_, con el ancho en pixels de cada carácter (los valores no pueden ser menores que 1 ni mayores que 8).



Los caracteres por encima del valor 126 son especiales, como ya se ha indicado. Son utilizados como iconos en las opciones, es decir, en donde aparece el comando `OPTION`, y como indicadores de espera con un `WAITKEY` o al cambiar de página si el comando `PAGEPAUSE` está activo.

- El carácter 126 es el carácter usado cuando una opción no está seleccionada.
- Los caracteres del 127 al 134 forman el ciclo de animación de una opción seleccionada.
- Los caracteres del 135 al 142 forman el ciclo de animación del indicador de espera.

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

La aparición de estos errores ocurren cuando se accede al disco, al buscar más trozos de texto, imágenes, etc. Si aparece el error 23 (File not found), suele ser que se haya olvidado de incluir algún fichero necesario en el disco. Otros errores ya suponen algún error de la unidad de disco o del propio disco.

Los errores del motor, son errores propios del motor.

- Error 1: El trozo accedido no existe. (Se intenta acceder a un fragmento no existente en el índice)
- Error 2: Se han creado demasiadas opciones, se ha superado el límite de opciones posibles.
- Error 3: No hay opciones disponibles, se ha lanzado un comando `CHOOSE` sin tener antes ninguna `OPTION`, o puede que se haya borrado inadvertidamente la pantalla, y por tanto, las opciones.

---

## ToDo

- Una herramienda para comvertir el juego de caracteres.

---

## Referencias y agradecimientos

- David Beazley por [PLY](https://www.dabeaz.com/ply/ply.html)
- Einar Saukas por el compresor [ZX0](https://github.com/einar-saukas/ZX0).
- DjMorgul por el buscador de abreviaturas, adaptado de [Daad Reborn Tokenizer](https://https://github.com/daad-adventure-writer/DRT)
- Shiru por BeepFx.

---

## Licencia
