    DEVICE ZXSPECTRUM48


LD_SCR_ADDR   EQU  16384
LD_SCR_SIZE   EQU  6912

PROG       EQU  $5C53
LD_BLOCK   EQU  $0802
LD_BYTES   EQU  $0556
REPORT_R   EQU  $0806
PORT_128   EQU  $7FFD
BANK_VAR   EQU  $5b5c


START_ADDRESS EQU 23755

; INIT_ADDR must be passed as parameter on SJASMPLUS
;INIT_ADDR     EQU $8000

    ORG START_ADDRESS

LINEA0:
    DB 0,0 ;NUMERO DE LINEA
    DW SIZE_LINE0 - 4 ;TAMAÑO
    DB 234 ;TOKEN DE REM

LOAD_TABLE:
@{BLOCK_LIST}


START_LOADER:
    ; Clear screen
    DI
    LD SP, @STACK_ADDRESS
    XOR A
    OUT (254), A                    ;Black border
    LD HL, LD_SCR_ADDR              ;pixels
    LD DE, LD_SCR_ADDR+1            ;pixels + 1
    LD BC, LD_SCR_SIZE              ;T
    LD (HL), L                      ;pone el primer byte a '0' ya que HL = 16384 = $4000  por tanto L = 0
    LDIR                            ;copia

    CALL MAINROM
    LD C, 0
    CALL SETRAM

    LD HL, LOAD_TABLE               ;Blocks table
LOOP_TABLE:
    LD C, (HL)
    INC HL
    LD B, (HL)
    INC HL                          ; Get program start address
    LD A, C
    OR B
    JR Z, RUN                       ; Start program if address = 0
    LD E, (HL)
    INC HL
    LD D, (HL)                      
    INC HL                          ; Get size
    LD IX, 0
    ADD IX, BC                      ; IX = start address, DE = size
    LD C, (HL)                      ; Set Bank
    INC HL
    DI
    CALL SETRAM
    EI
    SCF                             ; Set Carry Flag -> CF=1 -> LOAD
    LD A, $FF                       ; A = 0xFF (cargar datos)
    PUSH HL
    CALL LD_BYTES                   ; Load block
    POP HL
    JR C, LOOP_TABLE                ;If load OK , next entry...

RESET:                        
    XOR A                           ;Reset on error
    LD BC, $7ffd
    DI
    OUT (C),A                       ;update port
    LD B,$1F                        ;BC=1FFD
    OUT (C),A                       ;update port
    JP 0

RUN:
    DI
    LD C, 0
    CALL SETRAM
    CALL @INIT_ADDR
    JR RESET

SETRAM:
    LD A,(23388)
    AND %00010111
    OR C
    LD BC,$7FFD
    OUT (C),A
    LD (23388),A
    RET

MAINROM:
    LD A,(23388)
    SET 4,A
    LD BC,$7FFD
    OUT (C),A
    LD (23388),A
    LD A,(23399)
    RES 0,A
    SET 2,A
    LD B, $1F ;BC=$1FFD
    OUT (C),A
    LD (23399),A
    RET

SIZE_LINE0 = $ - LINEA0
LINEA10:
    DB 0,10
    DW SIZE_LINE10 - 4
    DB 253 ;CLEAR
    DB '.',14,0,0 ;SHORTNUMBER
    DW @INIT_ADDR - 1
    DB 0 ;FIN DEL SHORTNUMBER
    DB ':'
    DB 242 ;PAUSE
    DB 192 ;USR
    DB '.',14,0,0 ;SHORTNUMBER
    DW START_LOADER
    DB 0 ;FIN DEL SHORTNUMBER
    DB 13

SIZE_LINE10 = $ - LINEA10
SIZEOFBASIC = $ - START_ADDRESS

    EMPTYTAP "@TAP_NAME"
    SAVETAP "@TAP_NAME",BASIC,"@TAP_LABEL",START_ADDRESS,SIZEOFBASIC,10
