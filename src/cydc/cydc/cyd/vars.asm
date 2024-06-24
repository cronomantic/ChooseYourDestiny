
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



    ORG $5d00

START_VARS:
INITIAL_STACK EQU START_VARS

    ALIGN 256
FLAGS:
    DEFS 256, 0
;------------------------------------------------------------------------
    DEFINE MAXIMUM_OPTIONS 32
    ALIGN 256
OPTIONS_TABLE:
    DEFS 256, 0
TIMEOUT_OPTION:
    DEFS 4, 0
;  X, Y Cursor Marker - Addr Jump
;------------------------------------------------------------------------
    IFNDEF TEXT_BUFFER_LEN
    DEFINE TEXT_BUFFER_LEN   128
    ENDIF

    IFNDEF TOKEN_BUFFER_LEN
    DEFINE TOKEN_BUFFER_LEN  32
    ENDIF
;------------------------------------------------------------------------
BUFFER:
    DEFS TEXT_BUFFER_LEN+TOKEN_BUFFER_LEN,0

;Buffer for text
TEXT_BUFFER EQU BUFFER
;Buffer for decompressing token
TOKEN_BUFFER EQU TEXT_BUFFER + TEXT_BUFFER_LEN
;------------------------------------------------------------------------
    ; OPTIONS
NUM_OPTIONS:
    DEFB 0
SELECTED_OPTION:
    DEFB 0
SELECTED_OPTION_VALUE:
    DEFB 0
INCR_X_OPTION:
    DEFB 0
INCR_Y_OPTION:
    DEFB 1
DEFAULT_OPTION:
    DEFB 0
OPTION_BULLET_ENABLED:
    DEFB 1
CYCLE_OPTION:
    DEFB 0
RETURN_FROM_CHOOSE_CH:
    DEFB 0
CHOOSE_CH_RET_ADDRESS:
    DEFS 3, 0
CHOOSE_CH_GOSUB_ADDRESS:
    DEFS 3, 0

;--------------------------------------------------------------------------
;Print speed
PRT_INTERVAL:
    DEFW 0

CURR_WINDOW:
    DEFB 0

CHARSET_OFFSET:
    DEFB 0

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
PRINTED_LINES:
    DEFB 0

CHUNK:
    DEFB 0

WAIT_NEW_SCREEN:
    DEFB 0
SKIP_SPACES:
    DEFB 0

FADE_OUT_ITERARIONS:
    DEFB 0
FADE_OUT_ADDRESS:
    DEFW 0
FADEOUT_W:
    DEFB 0
FADEOUT_H:
    DEFB 0

MAX_X_BACKSPACE:
    DEFB 0
WIDTH_BACKSPACE:
    DEFB 0

CURR_SAVE_SLOT:
    DEFB 0
LAST_SAVE_RESULT:
    DEFB 255
LAST_DISK_ERROR:
    DEFB 0

NO_SELECTED_BULLET  EQU 127
SELECTED_BULLET     EQU 128
WAIT_TO_KEY_BULLET  EQU SELECTED_BULLET+8

PIC_NUM_LINES_PXL:
    DEFB 0
PIC_NUM_LINES_ATT:
    DEFB 0

SCR_BUFF_ADDR EQU $6000
    ORG SCR_BUFF_ADDR
SCREEN_BUFFER_PXL:
    DEFS SCR_PXL_SIZE,0
SCREEN_BUFFER_ATT:
    DEFS SCR_ATT_SIZE,0

;--------------------------------------------------
SAVE_START:
SAVE_GAME_ID:
    DEFS 16, 0
SAVE_SLOT:
    DEFB 0
SAVE_NVARS:
    DEFB 0
SAVE_ORIGIN:
    DEFB 0   
SAVE_FLAGS:
    DEFS 256, 0
SAVE_CHECKSUM:
    DEFW 0
SAVE_END:
SAVE_SIZE EQU SAVE_END-SAVE_START

MAXWINDOWS EQU 8

WINDOWS:
    DEFS MAXWINDOWS*8,0
WINDOWS_END:
;--------------------------------------------------
    ;INCLUDE "VTII10bG_vars.asm"

END_VARS:
;--------------------------------------------------

    ORG $C000
PIC_BUFFER:
    DEFW 0
PIC_BUFFER_SCR:
    DEFS SCR_PXL_SIZE+SCR_ATT_SIZE
