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

LD_SCR_ADDR      EQU  16384
LD_SCR_SIZE      EQU  6912

DOS_OPEN      EQU $0106
DOS_READ      EQU $0112
DOS_SET_1346  EQU $013f
DOS_CLOSE     EQU $0109
DOS_OFF_MOTOR EQU $019c

START_ADDRESS EQU 23755

;INIT_ADDR     EQU $5A00
;EXEC_ADDR     EQU @INIT_ADDR
;STACK_ADDRESS EQU @{INIT_ADDR}-2

    @DEFINE_LOADING_SCREEN

    ORG START_ADDRESS

LINEA0:
    DB 0,0 ;NUMERO DE LINEA
    DW SIZE_LINE0 - 4 ;TAMAÑO
    DB 234 ;TOKEN DE REM

LOAD_TABLE:
@{BLOCK_LIST}

START_LOADER:
    DI
    LD SP, @STACK_ADDRESS

    CALL INIT_STATE
    LD BC, $0001 ;B: FICHERO 0 , C: MODO DE LECTURA
    LD DE, $0002 ;HA DE EXISTIR EL ARCHIVO, CARGAR SIN CABECERA
    LD HL, FILENAME_LOAD
    ;HL has the start of the FILENAME
    CALL DOS_OPEN
    JR NC, RESET

    LD HL, LOAD_TABLE               ;Blocks table
LOOP_TABLE:
    LD E, (HL)
    INC HL
    LD D, (HL)
    INC HL                          ; Start address
    LD A, E
    OR D
    JR Z, END_LOAD
    LD C, (HL)
    INC HL
    LD B, (HL)
    INC HL                          ; Size
    LD A, (HL)                      
    INC HL                          ; Bank
    PUSH HL
    PUSH BC
    EX DE, HL                       ; Start Address HL
    LD C, A
    LD B, 0                         ;B: FILE HANDLE, C: RAM to page
    POP DE
    CALL DOS_READ
    JR NC, RESET
    POP HL
    JR LOOP_TABLE
;----------
END_LOAD:
    LD B, $00
    CALL DOS_CLOSE
    CALL DOS_OFF_MOTOR
    CALL MAINROM ;rom interprete 48k
    DI
    LD C, 0
    CALL SETRAM
    CALL @INIT_ADDR

RESET:
    XOR A
    LD BC, $7ffd
    DI
    OUT (C),A          ;update port
    LD B,$1F           ;BC=1FFD
    OUT (C),A          ;update port
    JP 0

;en C se indica la pagina de ram
SETRAM:
    LD A,(23388)
    AND %11111000
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


;Y el siguiente codigo solo se ejecuta al inicio
;y puede ser pisado por la pila posteriormente
INIT_STATE:
    XOR A
    OUT (254), A                    ;Black border
    LD HL, LD_SCR_ADDR                 ;pixels
    LD DE, LD_SCR_ADDR+1               ;pixels + 1
    LD BC, LD_SCR_SIZE                 ;T
    LD (HL), L                      ;pone el primer byte a '0' ya que HL = 16384 = $4000  por tanto L = 0
    LDIR                            ;copia

    LD A, (23388)
    LD BC, $7FFD
    AND %11101000                 ;SELECCION DE ROM0
    OR %00000111                  ;SELECCION DE RAM7
    OUT (C),A
    LD (23388),A
    LD B, $1F                     ;BC=1FFD
    LD A, (23399)
    AND %11111000
    OR %00000100                  ;SELECCION DE ROM2
    OUT (C),A
    LD (23399),A
    LD HL, $7800                  ;H 120, L 0
                                  ;8 last buffers of RAM 6
                                  ;0 for Ram Disc
    LD DE, $7E02                  ;H 120, L 8
                                  ;8 last buffers of RAM 6
                                  ;4kb for cache

    IFNDEF LOADING_SCREEN
    JP DOS_SET_1346
    ENDIF
    IFDEF LOADING_SCREEN
    CALL DOS_SET_1346
    LD HL, LOADSCR_DAT
    LD DE, LD_SCR_ADDR
    LD BC, LD_SCR_SIZE
    LDIR
    RET
LOADSCR_DAT:
@{LOADSCR_DAT}
    ENDIF

FILENAME_LOAD:
    DB "@DSK_FILENAME_BASE", $FF


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

    SAVE3DOS "@DSK_LOADER_FILENAME", START_ADDRESS, SIZEOFBASIC, 0, 10

