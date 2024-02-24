
; 
; MIT License
; 
; Copyright (c) 2023 Sergio Chico
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



    IFNDEF MAX_OPTIONS
    DEFINE MAX_OPTIONS 16
    ENDIF

    ORG $5d00

START_VARS:
INITIAL_STACK EQU START_VARS

    ALIGN 256
FLAGS:
    DEFS 256
;------------------------------------------------------------------------
;Print speed
PRT_INTERVAL:
    DEFW 1
; X is in pixels, y in chars
POS_X:
    DEFB 0
POS_Y:
    DEFB 0
;Window min & max size
; X is in pixels, y in chars
MIN_X:
    DEFB 0
MIN_Y:
    DEFB 0
MAX_X:
    DEFB 255
MAX_Y:
    DEFB 23
;MAX_LINES:
;    DEFB 24
;NUM_LINES:
;    DEFB 0
INT_STACK_PTR:
    DEFW 0
INT_CURRENT_PC:
    DEFW 0
CHUNK:
    DEFB 0

NUM_OPTIONS:
    DEFB 0
; X, Y Cursor Marker
OPTIONS_POS:
    DEFS 2*MAX_OPTIONS, 0
; Addr Jump
OPTIONS_JMP_ADDR:
    DEFS 4*MAX_OPTIONS, 0
TIMEOUT_OPTION:
    DEFS 4, 0

SELECTED_OPTION:
    DB 0
CYCLE_OPTION:
    DB 0
WAIT_NEW_SCREEN:
    DB 0
SKIP_SPACES:
    DB 0

MAXIMUM_OPTIONS EQU MAX_OPTIONS

NO_SELECTED_BULLET  EQU 127
SELECTED_BULLET     EQU 128
WAIT_TO_KEY_BULLET  EQU SELECTED_BULLET+8

PIC_NUM_LINES_PXL:
    DB 0
PIC_NUM_LINES_ATT:
    DB 0

SCR_BUFF_ADDR EQU $6000
    ORG SCR_BUFF_ADDR
SCREEN_BUFFER_PXL:
    DEFS SCR_PXL_SIZE,0
SCREEN_BUFFER_ATT:
    DEFS SCR_ATT_SIZE,0

BUFFER:
    DEFS 1024

;------------------------------------------------------------------------
    IFNDEF TEXT_BUFFER_LEN
    DEFINE TEXT_BUFFER_LEN   128
    ENDIF

    IFNDEF TOKEN_BUFFER_LEN
    DEFINE TOKEN_BUFFER_LEN  32
    ENDIF
;------------------------------------------------------------------------
;Buffer for text
TEXT_BUFFER EQU BUFFER
;Buffer for decompressing token
TOKEN_BUFFER EQU TEXT_BUFFER + TEXT_BUFFER_LEN

;------------------------------------------------------------------------

    ;INCLUDE "VTII10bG_vars.asm"

END_VARS:
;--------------------------------------------------

    ORG $C000
PIC_BUFFER:
    DEFW 0
PIC_BUFFER_SCR:
    DEFS SCR_PXL_SIZE+SCR_ATT_SIZE
