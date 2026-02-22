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

;INIT_ADDR must be passed as parameter on SJASMPLUS
;INIT_ADDR     EQU $8000

    ORG START_ADDRESS

LINEA0:
    DB 0,0 ;NUMERO DE LINEA
    DW SIZE_LINE0 - 4 ;TAMAÑO
    DB 234 ;TOKEN DE REM

LOAD_TABLE:
@{BLOCK_LIST}

    @DEFINE_IS_128

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

    IFDEF IS_128
    CALL TESTBANK128
    ENDIF

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
    IFDEF IS_128
    LD C, (HL)                      ; Set Bank
    INC HL
    DI
    CALL SETRAM
    EI
    ENDIF
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
    XOR A
    OUT (254), A                    ;Black border
    CALL @INIT_ADDR
    JR RESET

SETRAM:
    LD A,(23388)
    AND %00010000
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

    IFDEF IS_128
TESTBANK128:
    ld c, 0
    call SETRAM
    xor a
    ld ($FFFF), a
    ld c, 1
    call SETRAM
    ld a, $A5
    ld ($FFFF), a
    ld c, 0
    call SETRAM
    ld a, ($FFFF)
    or a
    ret z
    jp RESET
    ENDIF


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
