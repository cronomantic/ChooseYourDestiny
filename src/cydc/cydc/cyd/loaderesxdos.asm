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
;
; ESXDOS bootstrap loader (divMMC / divIDE, SD card).
;
; A tiny BASIC program (REM line with the machine code + a CLEAR/RANDOMIZE USR
; line) shipped in a .TAP. The user launches it from the ESXDOS NMI browser (or,
; in autoboot mode, it is emitted as /SYS/AUTOBOOT.BAS). The machine code opens
; the game data file on the SD card and, driven by the resident BLOCK_LIST,
; F_READs each block into its RAM bank, then jumps to the interpreter at
; @INIT_ADDR.
;
; Interrupts are kept DISABLED for the whole load: the divMMC automap only
; rewrites $0000-$3FFF (this code lives at $5Cxx and the interpreter/banks at
; $8000+/$C000, all safe), but with DI there is no chance of the ROM ISR firing
; between the F_READs. RST $08 issued from here works because ESXDOS is resident
; in the divMMC regardless of which Spectrum ROM is paged.
;
; BLOCK_LIST entry format (same as loadertape/loaderplus3): DEFW addr, DEFW size,
; DEFB bank; terminated by DEFW $0. The interpreter is the first entry
; (addr $8000, bank 0 -> paged bank is irrelevant, $8000 is the fixed bank 2).
; ==============================================================================

    DEVICE ZXSPECTRUM48

LD_SCR_ADDR   EQU  16384
LD_SCR_SIZE   EQU  6912

; ESX_F_* / ESX_MODE_* / ESX_DRIVE_DEFAULT are defined once in esxdos.asm (which
; is assembled right after this loader in the same source), so they are not
; redefined here to avoid duplicate-label errors.

PORT_128      EQU  $7FFD

START_ADDRESS EQU 23755

;INIT_ADDR must be passed as parameter on SJASMPLUS

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
    LD (HL), L                      ;first byte to 0 (HL=$4000 -> L=0)
    LDIR

    CALL MAINROM                    ;page 48K BASIC ROM (interpreter expects it)
    LD C, 0
    CALL SETRAM

    ; Open the game data file on the SD card.
    LD IX, FILENAME_LOAD
    LD B, ESX_MODE_READ
    LD A, ESX_DRIVE_DEFAULT
    RST $08
    DB ESX_F_OPEN                   ; A = handle, CF=1 on error
    JR C, RESET
    LD (FILE_HANDLE), A

    LD HL, LOAD_TABLE               ;Blocks table
LOOP_TABLE:
    LD E, (HL)
    INC HL
    LD D, (HL)
    INC HL                          ; DE = start address
    LD A, E
    OR D
    JR Z, END_LOAD                  ; addr 0 -> done
    LD C, (HL)
    INC HL
    LD B, (HL)
    INC HL                          ; BC = size
    LD A, (HL)
    INC HL                          ; A = bank
    PUSH HL                         ; save table pointer

    PUSH BC                         ; save size
    LD C, A
    DI
    CALL SETRAM                     ; page the destination bank at $C000 (dest may be there)
    POP BC                          ; BC = size back
    PUSH DE
    POP IX                          ; IX = destination address
    LD A, (FILE_HANDLE)
    RST $08
    DB ESX_F_READ                   ; read BC bytes into IX, CF=1 on error
    JR C, RESET
    POP HL
    JR LOOP_TABLE

END_LOAD:
    LD A, (FILE_HANDLE)
    RST $08
    DB ESX_F_CLOSE

    DI
    LD C, 0
    CALL SETRAM
    XOR A
    OUT (254), A                    ;Black border
    CALL @INIT_ADDR

RESET:
    XOR A                           ;Reset on error
    LD BC, $7ffd
    DI
    OUT (C),A                       ;update port
    LD B,$1F                        ;BC=1FFD
    OUT (C),A                       ;update port
    JP 0

;en C se indica la pagina de ram
SETRAM:
    LD A,(23388)
    AND %00010000                   ;keep ROM select bit
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

FILE_HANDLE:
    DB 0

FILENAME_LOAD:
    DB "@DSK_FILENAME_BASE", 0      ; ASCIIZ (esxDOS F_OPEN)

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
