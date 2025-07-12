; ==============================================================================
; Choose Your Destiny
; 
; Copyright (c) 2025 Sergio Chico (Cronomantic)
; 
; Permission is hereby granted, free of charge, to any person obtaining a copy
; of this software and associated documentation files (the "Software"), to deal
; in the Software without restriction, including without limitation the rights 
; to use, copy, modify, merge, publish, distribute and/or sell copies of the 
; Software, and to permit persons to whom the Software is furnished to do so, 
; subject to the following conditions:
; 
; - The above copyright notice and this permission notice shall be included 
; in all copies or substantial portions of the Software.
; 
; - The above copyright notice and/or one of the project logos must 
; be prominently displayed both on the loading screen and/or within 
; the programs that include this Software, as well as on the 
; download website in the case of a digital copy and/or on the 
; cover page in the case of a physical copy.
; 
; - THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
; EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
; MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
; IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
; DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
; OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR 
; THE USE OR OTHER DEALINGS IN THE SOFTWARE.
;
; ==============================================================================

ROM48KBASIC EQU %00010000

;====================================================
; Cambiamos el banco elegido en $C000
; Parámetros: 
;    A = Nuevo valor del banco
; Salida:
;    A = Valor anterior del banco
; Registros afectados:
;   AF, BC
;====================================================
SET_RAM_BANK:
    AND %00010111                 ;mask correct bytes
    LD B, A
    LD A,(PLUS3_DOS_BANKM)        ; Previous value of the port
    PUSH AF                       ; Saving in stack
    AND %11101000                 ; Change only bank bits
    OR B                          ; Select bank on B
    LD BC,$7ffd
    DI
    LD (PLUS3_DOS_BANKM),A
    OUT (C),A                     ;update port
    EI
    POP AF                        ;Recovering previous value
    RET

RESET_SYS:
    XOR A
    LD BC, $7ffd
    DI
    OUT (C),A          ;update port
    LD B,$1F           ;BC=1FFD
    OUT (C),A          ;update port
    LD HL, 0
    EX (SP), HL
    RET

SET_DEFAULT_BANKS:
    LD A, (PLUS3_DOS_BANK678)
    LD L, A
    AND %00000111
    LD H, A
    LD A, L
    AND %11111000
    OR %00000100                  ;Rom 2/3 selection (+3dos / 48 basic)
    LD BC,$1FFD                   ;BC=1FFD
    OUT (C), A                     ;update port
    LD (PLUS3_DOS_BANK678), A

    LD A, (PLUS3_DOS_BANKM)
    LD L, A
    AND %11101000                 ;Change only bank bits
    OR %00010000                  ;Set ROM 48K & Bank 0
    LD B, $7F                     ;BC=7FFD
    OUT (C), A                    ;update port
    LD (PLUS3_DOS_BANKM), A
    RET
