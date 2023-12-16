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

PLUS3_DOS_BANKM      EQU $5B5C
PLUS3_DOS_BANK678    EQU $5B67
;PLUS3_DOS_BANK_PORT  EQU $7FFD
;PLUS3_DOS_BANK2_PORT EQU $1FFD


    MACRO createPlus3DosCall address
        CALL PLUS3_DOS_SETUP_BANKS
        CALL address
        JP PLUS3_DOS_RESTORE_BANKS
    ENDM

PLUS3_DOS_SETUP_BANKS:

    PUSH AF
    DI
    EXX

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
    OR %00000111                  ;Set ROM +3dos & Bank 7
    LD B, $7F                     ;BC=7FFD
    OUT (C), A                    ;update port
    LD (PLUS3_DOS_BANKM), A

    EXX
    EI
    POP AF

    RET


PLUS3_DOS_RESTORE_BANKS:
    PUSH AF
    DI
    EXX
    ;HL & BC have the values of the previous routine

    LD A, L                       ;BC=7FFD
    OUT (C), A                    ;update port
    LD (PLUS3_DOS_BANKM), A

    LD A, (PLUS3_DOS_BANK678)
    AND %11111000
    OR H
    LD B, $1F                     ;BC=1FFD
    OUT (C), A                    ;update port
    LD (PLUS3_DOS_BANK678), A

    EXX
    EI
    POP AF
    RET


    IFUSED PLUS3_DOS_INIT
PLUS3_DOS_INIT:
    createPlus3DosCall($0100)
    ENDIF

    IFUSED PLUS3_DOS_VERSION
PLUS3_DOS_VERSION:
    createPlus3DosCall($0103)
    ENDIF

    IFUSED PLUS3_DOS_OPEN
PLUS3_DOS_OPEN:
    createPlus3DosCall($0106)
    ENDIF

    IFUSED PLUS3_DOS_CLOSE
PLUS3_DOS_CLOSE:
    createPlus3DosCall($0109)
    ENDIF

    IFUSED PLUS3_DOS_ABANDON
PLUS3_DOS_ABANDON:
    createPlus3DosCall($010C)
    ENDIF

    IFUSED PLUS3_DOS_REF_HEAD
PLUS3_DOS_REF_HEAD:
    createPlus3DosCall($010F)
    ENDIF

    IFUSED PLUS3_DOS_READ
PLUS3_DOS_READ:
    createPlus3DosCall($0112)
    ENDIF

    IFUSED PLUS3_DOS_WRITE
PLUS3_DOS_WRITE:
    createPlus3DosCall($0115)
    ENDIF

    IFUSED PLUS3_DOS_SET_1346
PLUS3_DOS_SET_1346:
    createPlus3DosCall($013F)
    ENDIF

    IFUSED PLUS3_DOS_GET_1346
PLUS3_DOS_GET_1346:
    createPlus3DosCall($013C)
    ENDIF

    IFUSED PLUS3_DOS_OFF_MOTOR
PLUS3_DOS_OFF_MOTOR:
    createPlus3DosCall($019c)
    ENDIF

    IFUSED PLUS3_DOS_ON_MOTOR
PLUS3_DOS_ON_MOTOR:
    createPlus3DosCall($0196)
    ENDIF

    IFUSED PLUS3_DOS_BYTE_READ
PLUS3_DOS_BYTE_READ:
    createPlus3DosCall($0118)
    ENDIF

    IFUSED PLUS3_DOS_BYTE_WRITE
PLUS3_DOS_BYTE_WRITE:
    createPlus3DosCall($011B)
    ENDIF

    IFUSED PLUS3_DOS_FREE_SPACE
PLUS3_DOS_FREE_SPACE:
    createPlus3DosCall($0121)
    ENDIF

    IFUSED PLUS3_DOS_RENAME
PLUS3_DOS_RENAME:
    createPlus3DosCall($0127)
    ENDIF

    IFUSED PLUS3_DOS_DELETE
PLUS3_DOS_DELETE:
    createPlus3DosCall($0124)
    ENDIF

    IFUSED PLUS3_DOS_SET_DRIVE
PLUS3_DOS_SET_DRIVE:
    createPlus3DosCall($012D)
    ENDIF

    IFUSED PLUS3_DOS_SET_USER
PLUS3_DOS_SET_USER:
    createPlus3DosCall($0130)
    ENDIF

    IFUSED PLUS3_DOS_GET_POS
PLUS3_DOS_GET_POS:
    createPlus3DosCall($0133)
    ENDIF

    IFUSED PLUS3_DOS_SET_POS
PLUS3_DOS_SET_POS:
    createPlus3DosCall($0136)
    ENDIF

    IFUSED PLUS3_DOS_GET_EOF 
PLUS3_DOS_GET_EOF:
    createPlus3DosCall($0139)
    ENDIF

    IFUSED PLUS3_DOS_FLUSH
PLUS3_DOS_FLUSH:
    createPlus3DosCall($0142)
    ENDIF

    IFUSED PLUS3_DOS_SET_ACCESS
PLUS3_DOS_SET_ACCESS:
    createPlus3DosCall($0145)
    ENDIF

    IFUSED PLUS3_DOS_SET_ATTR
PLUS3_DOS_SET_ATTR:
    createPlus3DosCall($0148)
    ENDIF

    IFUSED PLUS3_DOS_SET_MESS
PLUS3_DOS_SET_MESS:
    createPlus3DosCall($014E)
    ENDIF


PLUS3_DOS_ACCESS_MODE_EXCLUSIVE_READ DEFL 1
PLUS3_DOS_ACCESS_MODE_EXCLUSIVE_WRITE DEFL 2
PLUS3_DOS_ACCESS_MODE_EXCLUSIVE_READ_WRITE DEFL 3
PLUS3_DOS_ACCESS_MODE_SHARED_READ DEFL 5
PLUS3_DOS_ACCESS_MODE_SHARED_WRITE DEFL 6
PLUS3_DOS_ACCESS_MODE_SHARED_READ_WRITE DEFL 7

PLUS3_DOS_OPEN_ACTION_ERROR DEFL 0
PLUS3_DOS_OPEN_ACTION_READ_HEADER DEFL 1
PLUS3_DOS_OPEN_ACTION_IGNORE_HEADER DEFL 2
PLUS3_DOS_OPEN_ACTION_BACK_EXISTING_AND_CREATE DEFL 3
PLUS3_DOS_OPEN_ACTION_ERASE_EXISTING_AND_CREATE DEFL 4

PLUS3_DOS_CREATE_ACTION_ERROR DEFL 0
PLUS3_DOS_CREATE_ACTION_WITH_HEADER DEFL 1
PLUS3_DOS_CREATE_ACTION_WITHOUT_HEADER DEFL 2
