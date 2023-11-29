
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

