; 
; MIT License
; 
; Copyright (c) 2024 Sergio Chico
; 
; Permission is hereby granted, free of charge, to any person obtaining a copy
; of this software and associated documentation files (the "Software"), to deal
; in the Software without restriction, including without limitation the rights
; to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
; copies of the Software, and to permit persons to whom the Software is
; furnished to do so, subject to the following conditions:
; 
; The above copyright notice and this permission notice shall be included in all
; copies or substantial portions of the Software.
; 
; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
; OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
; SOFTWARE.

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
    LD A,($5b5c)                  ; Previous value of the port
    PUSH AF                       ; Saving in stack
    AND %11101000                 ; Change only bank bits
    OR B                          ; Select bank on B
    LD BC,$7ffd
    DI
    LD ($5b5c),A
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

