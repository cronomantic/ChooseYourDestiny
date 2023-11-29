

    INCLUDE "sysvars.asm"

    ORG $5d00

START_VARS:
INITIAL_STACK EQU START_VARS

BUFFER:
    DEFS 1024
;------------------------------------------------------------------------
    IFNDEF TEXT_BUFFER_LEN
    DEFINE TEXT_BUFFER_LEN   128
    ENDIF

    IFNDEF TOKEN_BUFFER_LEN
    DEFINE TOKEN_BUFFER_LEN  32
    ENDIF

    IFNDEF MAX_OPTIONS
    DEFINE MAX_OPTIONS 16
    ENDIF
;------------------------------------------------------------------------
;Buffer for text
TEXT_BUFFER EQU BUFFER
;Buffer for decompressing token
TOKEN_BUFFER EQU TEXT_BUFFER + TEXT_BUFFER_LEN

;------------------------------------------------------------------------
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
    DEFS 3+3*MAX_OPTIONS, 0

SELECTED_OPTION:
    DB 0
CYCLE_OPTION:
    DB 0
WAIT_NEW_SCREEN:
    DB 0

MAXIMUM_OPTIONS EQU MAX_OPTIONS

NO_SELECTED_BULLET  EQU 127
SELECTED_BULLET     EQU 128
WAIT_TO_KEY_BULLET  EQU SELECTED_BULLET+8

;--------------------------------------------------

SCR_BUFF_ADDR EQU $C000

    ORG SCR_BUFF_ADDR
SCREEN_BUFFER_PXL:
    DEFS SCR_PXL_SIZE,0
SCREEN_BUFFER_ATT:
    DEFS SCR_ATT_SIZE,0

PIC_BUFFER:
PIC_NUM_LINES_PXL:
    DB 0
PIC_NUM_LINES_ATT:
    DB 0
PIC_BUFFER_SCR:
    DEFS SCR_PXL_SIZE+SCR_ATT_SIZE
