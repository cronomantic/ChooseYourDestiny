
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
;

    DEFINE RELEASE "1.0"

    DEFINE IS_PLUS3 1

    ORG @INIT_ADDR
START_INTERPRETER:

INT_STACK_ADDR EQU $8000

DISK_BUFFER_SIZE    EQU (1*1024)/512
DISK_BUFFER         EQU ((128-DISK_BUFFER_SIZE) << 8) + DISK_BUFFER_SIZE

    IFDEF USE_VORTEX
VORTEX_BANK     EQU 6
VORTEX_FILE_H   EQU 2 << 8
MDLADDR 		EQU $C000
    ENDIF

    IFDEF USE_WYZ
WYZ_BANK     EQU 1
WYZ_TRACKER  EQU $C000
    ENDIF

SAVEGAME_BANK     EQU 0
SAVEGAME_FILE_H   EQU 0 << 8



    ld hl, 0                  ; No RAM disk
    ld de, DISK_BUFFER        ; Restrict cache to bank 6
    call PLUS3_DOS_SET_1346
    jp nc, DISK_ERROR          ; Error 1 if NC

    ;Clear data area
    xor a
    ld hl, START_VARS
    ld (hl), a
    ld de, START_VARS+1
    ld bc, END_VARS-START_VARS-1
    ldir
    di

    ld sp, INITIAL_STACK      ; Set stack
    ld a, high ISR_TABLE      ; load interrupt service routine
    ld i, a
    im 2
    call SET_DEFAULT_BANKS
    IFDEF USE_WYZ
    ld d, $FF
    call WYZ_CALL
    ENDIF
    ei

    ;Disable CAPS_LOCK
    res 3,(IY+$30)

    ld a, $FF
    ld (LAST_SAVE_RESULT), a

    xor a
    call BORDER

    IFDEF PAUSE_AT_START_VAL
    ld de, PAUSE_AT_START_VAL
    ld (DOWN_COUNTER), de
1:  call INKEY_MENU
    or a
    jr nz, 2f
    ld bc, (DOWN_COUNTER)
    ld a, b
    or c
    jr nz, 1b
2:  call INKEY_MENU
    or a
    jr nz, 2b
    ENDIF

    xor a
    call PAPER
    ld a, 7
    call INK
    call INIT_WIN
    call CLS_BUFFER
    call SET_RND_SEED

    jp START_LOADING

RND_SEED:
    DW 0
DOWN_COUNTER:
    DW 0
UPDATE_SCR_FLAG:
    DB 0

CHUNK_ADDR:
    DW 0
SCRIPT_BANK:
    DB 0

KEMPSTON_VALUE:
    DB $FF

    org $8070
TMP_AREA:
    DS 16, 0

    org $8080
ISR:
    push af
    push hl                  ; these will be restored by ROM
    push bc
    push de
    push ix
    push iy
    exx
    ex af, af'
    push af
    push hl
    push bc
    push de                  ;Full context save

    in a, ($1f)
    ld (KEMPSTON_VALUE), a

    ld a, (UPDATE_SCR_FLAG)  ; Get flag
    or a                     ; test if active
    jp z, .no_screen         ; Do nothing if 0 
    ;Update screen here!


;Copy Pixels
    ld hl, SCREEN_BUFFER_PXL
    ld a, (PIC_NUM_LINES_PXL)
    LD (.Copy_Screen_End),SP   ; This is some self-modifying code; stores the stack pointer in an LD SP,nn instruction at the end
    EXX                         ; Switch to alternate registers
    LD HL,0x4000                ; HL' = screen pointer
1:  LD (.Copy_Screen_HL1), HL  ; Store the screen position for later
    EXX                         ; Switch to normal registers
    ld (.Dec_Line), a
    LD SP,HL            ; HL = Buffer address
    POP AF              ; Fetch the data
    POP BC
    POP DE
    POP IX
    EXX             ; Switch to alternate registers
    EX AF,AF'
    LD DE,16
    ADD HL,DE           ; Add Offset for screen
    POP AF
    POP BC
    POP DE
    POP IY
    LD (.Copy_Screen_SP1),SP   ; Save the current buffer address for later
    LD SP,HL            ; The screen address
    PUSH IY             ; Push the data
    PUSH DE
    PUSH BC
    PUSH AF
    EX AF,AF'           ; Switch to normal registers
    EXX
    PUSH IX
    PUSH DE
    PUSH BC
    PUSH AF
.Copy_Screen_SP1+1:    
    LD HL,0             ; HL = Buffer

    LD SP,HL            ; HL = Buffer address
    POP AF              ; Fetch the data
    POP BC
    POP DE
    POP IX
    EXX             ; Switch to alternate registers
    EX AF,AF'
    LD DE,16
    ADD HL,DE           ; Add Offset for screen
    POP AF
    POP BC
    POP DE
    POP IY
    LD (.Copy_Screen_SP2),SP   ; Save the current buffer address for later
    LD SP,HL            ; The screen address
    PUSH IY             ; Push the data
    PUSH DE
    PUSH BC
    PUSH AF
    EX AF,AF'           ; Switch to normal registers
    EXX
    PUSH IX
    PUSH DE
    PUSH BC
    PUSH AF
.Copy_Screen_SP2+1:    
    LD HL,0             ; HL = Buffer

    EXX             ; Switch to alternate registers
.Copy_Screen_HL1+1:    
    LD HL,0             ; HL' = Screen 
    INC H               ; Drop down 1 pixel row in screen memory
    LD A,H              ; Check whether we've gone past a character boundary
    AND 0x07
    JR NZ,2F            
    LD A,H              ; Go to the next character line
    SUB 8
    LD H,A
    ld A,L
    ADD A,32
    LD L,A
    JR NC,2F            ; Check for next third
    LD A,H              ; Go to next third
    ADD A,8
    LD H,A
.Dec_Line+1:
2:  ld a, 0
    dec a
    jr nz,1B

.Copy_Screen_End+1:
    LD SP,0         ; Restore the SP
    EXX             ; Switch to normal registers

    ; Copy attributes
    ld hl, SCREEN_BUFFER_ATT
    ld de, SCR_ATT
    ld a, (PIC_NUM_LINES_ATT)
    ld b, a
1:  ld c, $ff
    REPT 32
    ldi
    ENDR
    djnz 1B

    xor a
    ld (UPDATE_SCR_FLAG), a
.no_screen:

    ld a, (FADE_OUT_ITERARIONS)
    or a
    jr z, .no_fadeout
    ld hl, (FADE_OUT_ADDRESS)
    ld de, (FADEOUT_W)
    dec a
    ld (FADE_OUT_ITERARIONS), a
2:  ld b, e        ; width -> B
    push hl
1:  ld a, (hl)     ; read current attribute; for both PAPER and INK (individually), all three bits are merged into one by OR
    ld c, a        ; the merged bits will land into "bottom" bit (b0 INK, b3 PAPER)
    rra                 ; setting those to "1" for non-zero INK/PAPER value
    or c           ; and "0" for zero INK/PAPER - this will be then subtracted
    rra                 ; from current attribute
    or c           ; *here* the bits 0 and 3 are "1" for non-zero INK and PAPER
    and %00001001   ; extract those bottom INK (+1)/PAPER (+8) bits into A
    ; subtract that value from current attribute, to decrement INK/PAPER individually
    sub c           ; A = decrement - attribute
    neg             ; A = attribute - decrement (new attribute value)
    ld (hl), a     ; write the darkened attribute value
    inc hl
    djnz 1b
    pop hl         ; Restore hl
    ld a, 32       ; next attr line
    add a, l
    jr nc, 4f
    inc h
4:  ld l, a
    dec d
    jr nz, 2b   
.no_fadeout:

    IFDEF USE_VORTEX
VORTEX_PLAYER_ISR:
    ;call vortex tracker here?
    ld hl, VTR_STAT
    bit 1, (hl)        ;Test if loaded module
    jr z, .no_ay

    bit 2, (hl)        ;test if play module
    jr z, .mute

    push hl

    ld a, (PLUS3_DOS_BANKM)
    ld bc, $7ffd
    push af                  ; Save current bank
    push bc
    ld a, VORTEX_BANK|%00010000
    out (c), a  ;Sets bank 3

    call VTR_ISR

    pop bc
    pop af
    out (c), a

    pop hl

    bit 0, (hl)
    jr z, .no_ay

    bit 7, (hl) ;test if end of song
    jr z, .no_ay
    res 2, (hl) ;Disable play  

.mute:
    call VTR_MUTE
.no_ay:
    ENDIF

    IFDEF USE_WYZ
WYZ_PLAYER_ISR:
    ld a, (PLUS3_DOS_BANKM)
    ld bc, $7ffd
    push af                  ; Save current bank
    push bc
    ld a, WYZ_BANK|%00010000
    out (c), a  ;Sets bank
    xor a
    CALL WYZ_TRACKER
    pop bc
    pop af
    out (c), a   
    ENDIF

    ; Downcounter for pauses
    ld hl, (DOWN_COUNTER)
    ld a, l
    or h
    jr z,.cont_zero
    dec hl
    ld (DOWN_COUNTER), hl
.cont_zero:

; Frame counter for random function
    ld hl, (FRAMES)
    inc hl
    ld (FRAMES), hl
    ld a, l
    srl a
    srl a
    and 7
    ld (CYCLE_OPTION), a

.restore_context:
    pop de                  ; Restore context
    pop bc
    pop hl
    pop af
    ex af, af'
    exx
    pop iy
    pop ix
    pop de
    pop bc
    ;
    pop hl
    pop af
    ei
    reti
    ;jp $3a                   ; Chain with ROM ISR

    align 256
ISR_TABLE:
    DEFS 257, HIGH ISR

START_LOADING:
    ld ix, INT_STACK_ADDR     ;Set internal Stack

    xor a
    call LOAD_CHUNK         ;Loads first CHUNK    
    ;ld hl, CHUNK_ADDR       ;Start the CHUNK
    ; HL current pointer,
EXEC_LOOP:
    ld d, HIGH OPCODES
    ld e, (hl)                ; Loads instruction
    sla e
    ex de, hl
    ld c, (hl)
    inc hl
    ld b, (hl)
    push bc
    ex de, hl
    inc hl
    ret

    ;Close file
END_PROGRAM:
    IFDEF USE_VORTEX
    call VTR_MUTE
    ENDIF
    IFDEF USE_WYZ
    ld de, $0200
    call WYZ_CALL
    ENDIF
    jp RESET_SYS

TYPE_TXT EQU  0
TYPE_SCR EQU  1
TYPE_TRK EQU  2

; A - New CHUNK number
; On exit, new CHUNK in C
LOAD_CHUNK:
    ld (CHUNK), a
    ld c, a
    ld b, TYPE_TXT
    call FIND_IN_INDEX
    ld (CHUNK_ADDR), hl
    ld (SCRIPT_BANK), a
    or ROM48KBASIC
    call SET_RAM_BANK
    ret

;Input: B = type of element, C = index of element
;Output: B = Bank, HL = Offset
;Uses: AF, AF', IX, DE, HL, BC
FIND_IN_INDEX:
    push ix
    ld hl, @SIZE_INDEX
    ld ix, INDEX
    ld de, @SIZE_INDEX_ENTRY
.loop:
    ld a, l
    or h
    jr z, .end_loop
    ld a, (ix+0)
    cp b
    jr nz, .next
    ld a, (ix+1)
    cp c
    jr z, .found
.next:
    add ix, de
    dec hl
    jr .loop
.end_loop:
    ld a, 1
    jp SYS_ERROR
.found:
    ld a, (ix+2)
    ld l, (ix+3)
    ld h, (ix+4)
    pop ix
    ret

SET_RND_SEED:
    ld hl,(FRAMES) ;get data from frames
    jr RANDOM_2
RANDOM:
    ld hl,(RND_SEED)
RANDOM_2:
    ld a, r
    and %11
    inc a
    ld b, a
.loop:
    ld a,h
    rra
    ld a,l
    rra
    xor h
    ld h,a
    ld a,l
    rra
    ld a,h
    rra
    xor l
    ld l,a
    xor h
    ld h,a
    djnz .loop
    ld (RND_SEED), hl
    ret

;----------------------------------------------------
SIGNATURE:
    DB "CYD v", RELEASE, 0
GAME_ID:
@{GAMEID}

;----------------------------------------------------
@{INCLUDES}
;----------------------------------------------------
; System Error message
; A = Error number
SYS_ERROR:
    or a
    push af
    ld a, %11110010
    ld (ATTR_P), a
    call INIT_WIN
    ld hl, SYS_ERROR_MSG
    call PRINT_STR
    pop af
    call PRINT_A_BYTE
.endless:
    jr .endless

; Disk Error message
; A = Error number
DISK_ERROR:
    push af
    ld a, %11110010
    ld (ATTR_P), a
    call INIT_WIN
    ld hl, DISK_ERROR_MSG
    call PRINT_STR
    pop af
    call PRINT_A_BYTE
.endless:
    jr .endless

SYS_ERROR_MSG:
    DB "SYSTEM ERROR No:",0

DISK_ERROR_MSG:
    DB "DISK ERROR No:",0

;---------------------------------------------------
TOKENS_ADDR         DW TOKENS
CHARSET_ADDR        DW CHARSET_S
CHARSET_WIDTHS_ADDR DW CHARSET_W

TOKENS:
@{TOKENS}

CHARSET_S:
@{CHARS}

CHARSET_W:
@{CHARW}

    IFDEF SHOW_SIZE_INTERPRETER
INDEX:
SIZE_INTERPRETER = $ - START_INTERPRETER
    DISPLAY "SIZE_INTERPRETER=", /D, SIZE_INTERPRETER, " <"
    ENDIF

    IFNDEF SHOW_SIZE_INTERPRETER
INDEX:
@{INDEX}


SIZE_INTERPRETER = $ - START_INTERPRETER
    SAVEBIN "@DSK_PATH", START_INTERPRETER, SIZE_INTERPRETER
    ENDIF

