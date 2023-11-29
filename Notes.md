# "Choose Your Destiny"

El programa es un interpete para ejecutar historias de tipo "Escoje tu propia aventura" o aventuras por opciones, para el Spectrum +3.

Consiste una máquina virtual que va intepretando "tokens" que se encuentra durante el texto para realizar las distintas acciones interactivas y un compilador que se encarga de traducir la aventura desde un lenguaje mas "humano" con el que se escribe el guión de la aventura, a un fichero interpretable por el motor.

El intérprete lee en cada momento un trozo de la aventura llamado "chunk" o "trozo" que ocupa 16 Kbytes, el mismo tamaño que el banco del Spectrum. El compilador divlabel_ide el guión en estos fragmentos y ajusta de forma correspondiente las referencias a las direcciones. Cuando el intérprete debe cambiar en "trozo" en ejecución, lo carga de disco.

Además, también puede mostrar imágenes comprimlabel_idas y almacenadas en el mismo disco, así como efectos de sonlabel_ido basados en BeepFX de Shiru.

## CYDC (Compilador)

## CYD (Motor)

## CSC (Compresor de Imágenes)

## Listado de instrucciones

## Sintaxis

## Comandos

END
RETURN
CENTER
WAITKEY
CHOOSE
CLEAR
GOTO label_id
GOSUB label_id
OPTION GOTO label_id
LABEL label_id
INKEY expression
CHAR expression
TAB expression
PAGEPAUSE expression
SET flag_no TO RANDOM
SET NOT flag_no
PRINT @ flag_no
PRINT expression
INK @ flag_no
INK expression
PAPER @ flag_no
PAPER expression
BORDER @ flag_no
BORDER expression
BRIGHT @ flag_no
BRIGHT expression
FLASH @ flag_no
FLASH expression
SFX expression
SFX @ flag_no
PICTURE @ flag_no
DISPLAY @ flag_no
PICTURE expression
DISPLAY expression
WAIT expression
PAUSE expression
TYPERATE expression
MARGINS expression COMMA expression COMMA expression COMMA expression
AT expression COMMA expression
SET flag_no TO @ flag_no
SET flag_no TO expression
SET flag_no + @ flag_no
SET flag_no + expression
SET flag_no - @ flag_no
SET flag_no - expression
SET flag_no AND @ flag_no
SET flag_no AND expression
SET flag_no OR @ flag_no
SET flag_no OR expression
IF flag_no = @ flag_no THEN GOTO label_id
IF flag_no = expression THEN GOTO label_id
IF flag_no <> @ flag_no THEN GOTO label_id
IF flag_no <> expression THEN GOTO label_id
IF flag_no <= @ flag_no THEN GOTO label_id
IF flag_no <= expression THEN GOTO label_id
IF flag_no >= @ flag_no THEN GOTO label_id
IF flag_no >= expression THEN GOTO label_id
IF flag_no < @ flag_no THEN GOTO label_id
IF flag_no < expression THEN GOTO label_id
IF flag_no > @ flag_no THEN GOTO label_id
IF flag_no > expression THEN GOTO label_id
CHOOSE IF WAIT expression THEN GOTO label_id
