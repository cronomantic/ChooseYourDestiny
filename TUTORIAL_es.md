# Tutorial de Choose Your Destiny

(En progreso)

- [Tutorial de Choose Your Destiny](#tutorial-de-choose-your-destiny)
  - [Instalación](#instalación)
    - [Windows](#windows)
  - [Preparando nuestra primera aventura](#preparando-nuestra-primera-aventura)
  - [Formato del fichero fuente](#formato-del-fichero-fuente)
  - [Saltos y etiquetas](#saltos-y-etiquetas)
  - [Opciones](#opciones)
  - [Pausas y esperas](#pausas-y-esperas)
  - [Formato del texto](#formato-del-texto)
  - [Imágenes](#imágenes)
  - [Efectos de sonido](#efectos-de-sonido)
  - [Música](#música)
  - [Variables e indirecciones](#variables-e-indirecciones)

---

## Instalación

### Windows

Para instalar en Windows 10 (64 bits) o superiores, descarga el archivo ChooseYourDestiny.Win64.zip de la sección [Releases](https://github.com/cronomantic/ChooseYourDestiny/releases) del repositorio y descomprímelo en una carpeta llamada Tutorial que puedes crear donde creas conveniente.

El ejecutable para compilar aventuras se llama `MakeAdv.bat`, si al ejecutarlo te da error el antivirus, es debido a que el compilador tiene incorporado un entorno Python que puede hacer dar un falso positivo al detector heurístico de éstos. Para evitarlo, puedes añadir una excepción al archivo `dist\cydc.exe` en tu antivirus.

---

## Preparando nuestra primera aventura

Lo primero que vamos a hacer es cambiar un par de cosas para poder generar una aventura personalizada. Para ello abrimos el fichero `MakeAdv.bat` con cualquier editor de texto y vemos ésto al principio:

```batch
@echo off  &SETLOCAL

REM ---- Configuration variables 

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.txt with this example
REM   - The +3 disk image file will be called test.dsk with this example
...
```

Lo primero que vamos a hacer es poner nuestro nombre a la aventura que vamos a crear. Por ejemplo, la llamaremos `Tutorial`:

```batch
@echo off  &SETLOCAL

REM ---- Configuration variables 

REM Name of the game
SET GAME=Tutorial
REM This name will be used as:
REM   - The file to compile will be test.txt with this example
REM   - The +3 disk image file will be called test.dsk with this example
...
```

Guardamos el fichero y ahora creamos un fichero nuevo de texto, llamado `Tutorial.txt`. En este fichero, escribimos ésto:

```
Hola Mundo[[WAITKEY]]
```

Y lo guardamos en el mismo sitio que `MakeAdv.bat`. Ejecutamos el fichero BAT y si todo va bien, se te habrá creado un fichero de disco llamado Tutorial.DSK, que puedes ejecutar con tu emulador favorito.

## Formato del fichero fuente

Al lanzar el fuchero DSK resultante con un emulador, sale ésto:

![Pantalla 1](assets/tut001.png)

Vamos a analizar lo que sucede...

Al cargar sale la pantalla que tenemos dentro de la carpeta IMAGES, que tiene el nombre `000.scr`. Si existe, esta pantalla se carga automáticamente al cargar el intérprete, por lo que la pantalla 0 se considera la pantalla de presentación.

Volviendo al código de la aventura, vemos que se pinta el texto *Hola Mundo* y después sale una especie de cursor. Si pulsamos la tecla `Enter` o `Space`, se reinicia el programa. Si volvemos al código:

```
Hola Mundo[[WAITKEY]]
```

Hay dos partes diferenciadas, una es el *Hola Mundo*, y después *[[WAITKEY]]*. La segunda parte es un comando que se le manda al intérprete para que saque ese cursor animado y espere la pulsación de una tecla. Esto es la base fundamental para entender cómo funciona el compilador: **Todo lo que se encuentre entre `[[` y `]]` se considera código o comandos para el motor y todo lo que esté fuera se considera texto imprimible**.

Para entender ésto mejor, vamos a hacer un experimento. Vamos a poner un salto de línea detrás de los dos corchetes abiertos, tal que así:

```
Hola Mundo[[
WAITKEY]]
```

Si compilamos y cargamos el juego, vemos que sale lo mismo. Ahora, borramos el salto de línea que hemos puesto y lo ponemos **antes** de los dobles corchetes:

```
Hola Mundo
[[WAITKEY]]
```

Si compilamos y cargamos de nuevo, vemos que ahora el icono está en la siguiente línea:

![Pantalla 2](assets/tut002.png)

Eso es debido a que el salto de línea, al estar fuera de los dobles corchetes, es considerado texto imprimible, y por tanto, el icono de espera pasa a la siguiente línea. Ten en cuenta estas situaciones cuando escribas la aventura.

Dejemos de momento esto como estaba y vamos a añadir más comandos. Teclea ésto dentro de `Tutorial.txt`:

```
[[CLEAR]]Hola Mundo[[WAITKEY]]
```

Ahora hemos puesto un comando por delante del texto. Si compilamos y ejecutamos, obtenemos ésto:

![Pantalla 3](assets/tut003.png)

Con el comando CLEAR borramos la zona imprimible que, de momento, es la pantalla completa. Con esto, eliminamos la pantalla de carga y tenemos la pantalla limpia para imprimir desde el comienzo. Tienes una referencia completa de los comandos en el [manual](https://github.com/cronomantic/ChooseYourDestiny/blob/main/MANUAL_es.md).

Ahora vamos a cambiar el color del texto. Para ello vamos a usar el comando INK n, donde n es un número del 0 al 7 que corresponde con los colores del Spectrum. Por defecto es blanco, así que vamos a ponerlo de color cian, que es el número 5, con lo que sería INK 5. Lo pondremos antes del CLEAR, tal que así:

```
[[INK 5]][[CLEAR]]Hola Mundo[[WAITKEY]]
```

El resultado es...

![Pantalla 4](assets/tut004.png)

Pero el color es un poco apagado... ¡Vamos a darle brillo!
Para ello usamos el comando BRIGHT 1, (de nuevo, mirar la referencia en el [manual](https://github.com/cronomantic/ChooseYourDestiny/blob/main/MANUAL_es.md)), de esta manera:

```
[[INK 5]][[BRIGHT 1]][[CLEAR]]Hola Mundo[[WAITKEY]]
```

![Pantalla 5](assets/tut005.png)

Esto ya está mejor.

Pero tanto corchete puede ser bastante confuso y poco agradable a la vista. Como ya he indicado, cada vez que se encuetra `[[`, el compilador interpreta que lo siguiente son comandos. ¿Cómo podemos encadenarlos sin estar abriendo y cerrando corchetes? Pues hay dos maneras:

- Mediante saltos de línea:
  
```
[[
    INK 5
    BRIGHT 1
    CLEAR
]]Hola Mundo[[WAITKEY]]
```

- Mediante dos puntos en la misma línea:

```
[[ INK 5 : BRIGHT 1 : CLEAR ]]Hola Mundo[[ WAITKEY ]]
```

Las dos variantes anteriores producirán el mismo resultado y son equivalentes.

Un último punto son los comentarios. Dentro del código podemos poner comentarios encerrándolos con `/*` y `*/`:

```
[[
    INK 5     /* Imprime en color Cyan */
    BRIGHT 1  /* Activamos brillo */
    CLEAR     /* Borramos la pantalla */
]]Hola Mundo[[
  WAITKEY     /* Espera a pulsar tecla */
]]
```

Con esto ya deberías tener una buena noción de cómo funciona el código fuente de CYD.

---

## Saltos y etiquetas

En el ejemplo del capítulo anterior, habrás notado que cuando pulsamos la tecla de selección, se resetea el Spectrum. Eso es debido a que al pulsar la tecla de validación (estando en espera con WAITKEY), llega al final del fichero. Cuando ésto sucede, se reinicia el Spectrum. Podemos hacer lo mismo usando el comando END en cualquier parte del código.

Pero no queremos que haga eso. Queremos que vuelva a empezar de nuevo. Para ello copia lo siguiente en el fichero fuente:

```
[[
  LABEL principio
  INK 5
  BRIGHT 1
  CLEAR
]]Hola Mundo[[
  WAITKEY
  GOTO principio
]]
```

Cuando compiles y ejecutes, no se verá muy bien, pero notarás que cuando pulses la tecla de validación, no se reinicia, sino que borra la pantalla y vuelve a imprimir el texto y hacer la espera.

Los dos añadidos al código son `LABEL principio` y `GOTO principio`. El primer comando no es en realidad un comando, sino una etiqueta, que lo que hace es poner un marcador es ese punto con un identificador de nombre *principio*; y el segundo lo que hace es indicar al intérprete que salte hacia donde se encuentre la etiqueta *principio*.

El resultado es que, al pulsar la tecla de validación con WAITKEY, se encuentra el `GOTO principio` y salta hacia donde está declarada la etiqueta *principio*, que al ser el comienzo, lo que hace es volver a ejecutar todos los comandos posteriores e imprimir el texto *Hola Mundo*, y esperar con WAITKEY de nuevo... En resumen, hemos hecho un bucle infinito.

Sin embargo, podemos mejorar el ejemplo así:

```
[[
  INK 5
  BRIGHT 1
  LABEL principio
  CLEAR
]]Hola Mundo[[
  WAITKEY
  GOTO principio
]]
```

Ahora la etiqueta está declarada justo antes del borrado de la pantalla, y allí irá cuando se alcance el GOTO, dejando sin ejecutar de nuevo el INK y el BRIGHT. ¿Por qué? Pues porque ya no es necesario ejecutarlos otra vez, ya hemos puesto el color del texto y el brillo al principio y ¡ejecutarlos de nuevo es redundante!

El concepto de etiquetas y saltos es fundamental para comprender cómo hacer un "Elige tu propia aventura", ya que presentaremos opciones al jugador, y dependiendo de esas opciones, iremos de un lugar a otro del texto.

Un importante detalle es el formato de los identificadores de etiquetas. Éstos sólo pueden ser una **secuencia de cifras y letras, sin espacios y deben empezar por una letra**. Es decir, `LABEL 1` o `LABEL La Etiqueta` no son válidos, pero `LABEL l1` o `LABEL LaEtiqueta` sí lo son. Además son sensibles al caso, es decir, que **se distinguen mayúsculas y minúsculas**, con lo que `LABEL Etiqueta` y `LABEL etiqueta` no son la misma etiqueta. Y, obviamente, no se puede declarar una etiqueta con el mismo nombre dos veces.

Por el contrario, los comandos no son sensibles al caso, es decir, que `CLEAR`, `clear` ó `Clear`, son perfectamente válidos. Sin embargo, yo recomiendo ponerlos en mayúsculas para distinguirlos mejor.

---

## Opciones

Las opciones es el punto mas importante del motor. De nuevo, vamos a verlo con el ejemplo del manual:

```
[[ /* Pone colores de pantalla y la borra */
   PAPER 0    /* Color de fondo negro  */
   INK   7    /* Color de texto blanco */
   BORDER 0   /* Borde de color negro  */
   CLEAR      /* Borramos la pantalla*/
]][[ LABEL Localidad1]]Estás en la localidad 1. ¿Donde quieres ir?
[[ OPTION GOTO Localidad2 ]]Ir a la localidad 2
[[ OPTION GOTO Localidad3 ]]Ir a la localidad 3
[[ CHOOSE ]]
[[ LABEL Localidad2 ]]¡¡¡Lo lograste!!!
[[ GOTO Final ]]
[[ LABEL Localidad3 ]]¡¡¡Estas muerto!!!
[[ GOTO Final]]
[[ LABEL Final : WAITKEY: END ]]
```

Al compilar y ejecutar tenemos esto:

![Menú de opciones](assets/tut006.png)

Nos aparecen dos opciones que podemos elegir con las teclas **P** y **Q** y seleccionar una con **Space** o **Enter**.
Si elegimos la primera opción, nos sale esto:

![PElegimos la primera opción](assets/tut007.png)

Y si elegimos la segunda:

![Elegimos la segunda opción](assets/tut008.png)


Con el comando `OPTION GOTO etiqueta`, lo que hacemos es declarar una opción seleccionable. El lugar donde esté el cursor en ese momento será el punto donde aparezca el icono de opción. Vamos a recolocar un poco las opciones para ilustrar esto último:

```
[[ /* Pone colores de pantalla y la borra */
   PAPER 0    /* Color de fondo negro  */
   INK   7    /* Color de texto blanco */
   BORDER 0   /* Borde de color negro  */
   CLEAR      /* Borramos la pantalla*/
]][[ LABEL Localidad1]]Estás en la localidad 1.
¿Donde quieres ir?

  [[ OPTION GOTO Localidad2 ]]Ir a la localidad 2

  [[ OPTION GOTO Localidad3 ]]Ir a la localidad 3
[[ CHOOSE ]]
[[ LABEL Localidad2 ]]¡¡¡Lo lograste!!!
[[ GOTO Final ]]
[[ LABEL Localidad3 ]]¡¡¡Estas muerto!!!
[[ GOTO Final]]
[[ LABEL Final : WAITKEY: END ]]
```

![Menú organizado](assets/tut009.png)

Como se puede ver, hemos separado las opciones con saltos de línea y puesto dos espacios de sangrado por delante del comando `OPTION GOTO` y eso se refleja en el resultado final.

Una vez declaradas las opciones, con el comando `CHOOSE`, activamos el menú, que nos permitirá elegir entre una de las opciones que ya estuviesen en pantalla. Cuando seleccionemos una, se saltará a la etiqueta indicada en el correspondiente `OPTION GOTO`. En el ejemplo, Si seleccionamos la primera opción, `OPTION GOTO Localidad2`, saltará a la etiqueta `LABEL Localidad2` e imprimirá *Lo lograste* y luego saltará a la etiqueta `LABEL Final`. El `GOTO Final` es necesario hacerlo, porque si no, nos imprimiría *¡¡¡Lo lograste!!!* y después *¡¡¡Estas muerto!!!*; el `GOTO` es necesario, en este caso, para evitar que se ejecute el resultado de la segunda opción.

**IMPORTANTE**, cuando se ejecute `CHOOSE`, **¡sólo se podrán elegir las opciones que haya en ese momento en la pantalla!**. Ten en cuenta que si imprimes en la última línea y pasas a la siguiente, la pantalla se borra para seguir imprimiendo desde el principio. Cuando se borra la pantalla las opciones que hubiese hasta ese momento son descartadas, con lo que si imprimes demasiado puedes perder opciones. Ten cuidado con esto a la hora de disponer tu menú de opciones en pantalla.

Como nota adicional con `CHOOSE`, sólo se permiten un máximo de 16 opciones y un mínimo de una (inútil, pero se permite). Fuera de ese rango el intérprete dará un error.

También destacar que hay una variante de `CHOOSE` temporizada, compila y ejecuta esto sin seleccionar nada en el menú :

```
[[ /* Pone colores de pantalla y la borra */
   PAPER 0    /* Color de fondo negro  */
   INK   7    /* Color de texto blanco */
   BORDER 0   /* Borde de color negro  */
   CLEAR      /* Borramos la pantalla*/
]][[ LABEL Localidad1]]Estás en la localidad 1.
¿Donde quieres ir?

  [[ OPTION GOTO Localidad2 ]]Ir a la localidad 2

  [[ OPTION GOTO Localidad3 ]]Ir a la localidad 3
[[ CHOOSE IF WAIT 500 THEN GOTO Localidad3]]
[[ LABEL Localidad2 ]]¡¡¡Lo lograste!!!
[[ GOTO Final ]]
[[ LABEL Localidad3 ]]¡¡¡Estas muerto!!!
[[ GOTO Final]]
[[ LABEL Final : WAITKEY: END ]]
```

Te darás cuenta que al pasar unos 10 segundos, ha mostrado *¡¡¡Estas muerto!!!*.

Lo que hace `CHOOSE IF WAIT 500 THEN GOTO Localidad3` es lo mismo que `CHOOSE`, activar la selección de opciones, pero con la salvedad que también realiza una cuenta atrás, en este caso desde 500. Si dicha cuenta atrás llega a cero sin seleccionarse nada, entonces se hace el salto a la etiqueta indicada; en este caso *Localidad3*.
El contador funciona en base a los fotogramas del Spectrum, es decir, 1/50 de segundo, con lo que 500/50 = 10 segundos. Esto lo veremos en el siguiente capítulo.

Con esto ya tenemos las base para hacer un "Elije tu propia aventura" básico. Pero todavía tenemos muchas más posibilidades que explorar...

---

## Pausas y esperas

En los ejemplos anteriores ya habrás visto el comando `WAITKEY`. Ese comando genera una pausa, con un icono animado, en espera de que se pulse la tecla de confirmación. Con eso puedes controlar la visualización del texto y evitar que el usuario tenga que leer un muro de texto de una sentada, además de permitir controlar la presentación.

Un ejemplo sería cuando se está acabando la "página" y queremos que el usuario pulse una tecla para pasar a la siguiente, que podemos hacer así:

```
Texto al final de la página.[[ 
  WAITKEY 
  CLEAR
]]Texto al principio de la siguiente página.
```

Con el `WAITKEY` hacemos la espera, y al confirmar, con el `CLEAR` siguiente borramos el texto en pantalla y comenzamos a escribir desde el principio de lo que sería la siguiente "página".

Sin embargo, hay una opción para que CYD haga esto por sí solo. El comportamiento por defecto cuando acabamos de imprimir en la última línea es borrar completamente la pantalla y seguir escribiendo; pero con el comando `PAGEPAUSE` podemos activar un comportamiento alternativo. Si indicamos `PAGEPAUSE 1`, por ejemplo, cuando se acabe el espacio disponible, generará automáticamente una espera para que el usuario pulse la tecla de confirmación antes de borrar la pantalla y seguir imprimiendo.

Además, también se dispone de esperas "temporizadas", siendo `CHOOSE IF WAIT X THEN GOTO Y` del capítulo anterior un ejemplo. Cuando se ejecutan, un contador se carga con el valor que se pasa como parámetro y se realiza una cuenta atrás hasta que el contador llega a cero. El contador se decrementa una vez cada fotograma del Spectrum, es decir, una vez cada 1/50 de segundo, o lo que es lo mismo, 50 veces por segundo. De tal manera, que si queremos esperar un segundo, tenemos que poner el contador a 50.

Con ésto, ya tenemos lo necesario para conocer los comandos:

- Con el comando `WAIT`, se realiza una espera incondicional, es una detención hasta que se agote el contador.
  
```
Espera tres segundos[[WAIT 150]]
Ya está[[WAITKEY]]
```

- El comando `PAUSE` es una combinación de `WAITKEY` y `WAIT`, se realiza una espera hasta que se agote el contador ó el usuario pulse la tecla de confirmación, podríamos considerarlo un `WAITKEY` con caducidad.
  
```
Espera tres segundos o pulsa una tecla[[PAUSE 150]]
Ya está[[WAITKEY]]
```

- `CHOOSE IF WAIT X THEN GOTO Y` ya ha sido explicado el en capítulo anterior, si se agota el contador antes de que se seleccione una opción del menú, se realiza el salto indicado.

Para terminar, hablar del comando `TYPERATE`, que es un poco especial comparado con el resto de comandos de espera. Con este comando indicamos la espera que se produce cada vez que se imprime un carácter. Ésta espera no está ajustada a los fotogramas, sino que es un contador que ya depende de la velocidad del procesador (más rápido). La idea de este comando es la de escribir de forma más pausada y paulatina, para cierta situaciones "dramáticas".

```
[[TYPERATE 100]]Esto imprime lento
[[TYPERATE 1]]Esto imprime normal[[WAITKEY]]
```

---

## Formato del texto

Una de las partes más importantes para el diseño de una aventura con CYD es ajustar la presentación del texto. CYD no "sabe" como presentar el texto. Como autores, tenemos que ayudarle.

Como ya se ha indicado, el motor simplemente imprime el texto que se encuentre a pantalla completa, procurando que nunca divida palabras entre una línea y la siguiente. Cuando llegue a la última línea, se borra la pantalla y sigue imprimiendo (excepto si se usa el comando `PAGEPAUSE`, como ya se ha indicado).



---

## Imágenes

---

## Efectos de sonido

---

## Música

---

## Variables e indirecciones

---
