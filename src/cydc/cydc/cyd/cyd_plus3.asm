
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

    DEFINE RELEASE "0.8"

    ORG @INIT_ADDR
START_INTERPRETER:

INT_STACK_ADDR EQU $8000

DISK_BUFFER_SIZE    EQU (16*1024)/512
DISK_BUFFER         EQU ((128-DISK_BUFFER_SIZE) << 8) + DISK_BUFFER_SIZE

SCRIPT_BANK     EQU 0
SCRIPT_FILE_H   EQU 0 << 8

VORTEX_BANK     EQU 1
VORTEX_FILE_H   EQU 2 << 8

CHUNK_ADDR      EQU $C000
MDLADDR 		EQU $C000

    call PLUS3_DOS_INIT
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
    ei

    ;Disable CAPS_LOCK
    res 3,(IY+$30)

    xor a
    call BORDER
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

    org $8060
SIGNATURE:
    DB "Choose Your Destiny v", RELEASE, 0

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
/*
    ; Loads image 000 as loading screen
    ld hl, LOAD_FILENAME
    ld bc, IMAGE_FILE_H+1   ; FIle id=0, exclusive read
    ld de, $0002            ; Open file
    call PLUS3_DOS_OPEN     ; test if file exists
    jr c, .load_file_exists ; Open file successfully
    cp 23                   ; If file not found, ignore
    jr z, .no_intro         ; If file does not exists, then ignore
    jp DISK_ERROR 
.load_file_exists:
    ld b, IMAGE_FILE_H>>8
    call PLUS3_DOS_CLOSE
    jp nc, DISK_ERROR
    xor a                   ; Loads Image 0
    call IMG_LOAD
    call COPY_SCREEN
.no_intro:
*/

    ; Open history file
    ld hl, FILENAME_SCRIPT
    ld bc, SCRIPT_FILE_H+1   ; FIle id=0, exclusive read
    ld de, $0002             ; Open file
    call PLUS3_DOS_OPEN
    jp nc, DISK_ERROR          ; Error 1 if NC

    ;Load header size
    ld hl, FILE_HEADER
    push hl
    ld de, $02
    ld bc, SCRIPT_FILE_H+SCRIPT_BANK
    call PLUS3_DOS_READ
    jp nc, DISK_ERROR          ; Error 1 if NC

    ;Loads header
    ld de, (FILE_HEADER)
    pop hl
    ld bc, SCRIPT_FILE_H+SCRIPT_BANK
    call PLUS3_DOS_READ
    jp nc, DISK_ERROR          ; Error 1 if NC

    ; Adjunts pointers
    ld de, FILE_HEADER
    ld hl, (CHARSET_ADDR)
    add hl, de
    ld (CHARSET_ADDR), hl
    ld hl, (CHARSET_WIDTHS_ADDR)
    add hl, de
    ld (CHARSET_WIDTHS_ADDR), hl
    ld hl, (CHUNK_OFFSET_PTR)
    add hl, de
    ld (CHUNK_OFFSET_PTR), hl
    ld hl, (CHUNK_SIZE_PTR)
    add hl, de
    ld (CHUNK_SIZE_PTR), hl
    ld hl, (TOKENS_ADDR)
    add hl, de
    ld (TOKENS_ADDR), hl

    ld ix, INT_STACK_ADDR     ;Set internal Stack

    xor a
    call LOAD_CHUNK         ;Loads first CHUNK
    ld hl, CHUNK_ADDR       ;Start the CHUNK
    ; HL current pointer,
EXEC_LOOP:
    ld d, HIGH OPCODES
    ld e, (hl)                ; Loads instruction
    sla e
    jr nc, 1f
    inc d
1:  inc hl
    ld a, (de)
    ld (.smod), a
    inc de
    ld a, (de)
    ld (.smod+1), a
.smod+1:
    jp OP_END

    ;Close file
END_PROGRAM:
    call VTR_MUTE
    ld b, SCRIPT_FILE_H>>8
    call PLUS3_DOS_CLOSE
    jp nc, DISK_ERROR          ; Error 1 if NC
    jp RESET_SYS

; A - New CHUNK number
; On exit, new CHUNK in C
LOAD_CHUNK:
    ld (CHUNK), a
    ld c, a
    ld a, (NUM_CHUNKS)
    dec a
    cp c                      ; (NUM_CHUNK-1)-C
    ld a, 1
    jp c, SYS_ERROR           ; Number of CHUNK too big!
    ld a, (CHUNK)
    ld l, a
    ld h, 0
    add hl, hl                ; * 2
    push hl
    add hl, hl                ; * 4
    ld de, (CHUNK_OFFSET_PTR)
    add hl, de                ;Obtained in HL de pointer to the CHUNK on the index
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld a, (hl)
    ex de, hl
    ld e, a                    ; E - HL => position in the file of the CHUNK to load
    ld b, SCRIPT_FILE_H>>8     ; script file handle
    call PLUS3_DOS_SET_POS     ; set to the beginning of the CHUNK
    jp nc, DISK_ERROR          ; Error 1 if NC
    pop hl
    ld de, (CHUNK_SIZE_PTR)
    add hl, de
    ld e, (hl)
    inc hl
    ld d, (hl)                 ; We have on DE the size of the CHUNK
    ld hl, CHUNK_ADDR        ; Load in upper RAM
    ld bc, SCRIPT_FILE_H+SCRIPT_BANK
    call PLUS3_DOS_READ        ; Load CHUNK into ram
    jp nc, DISK_ERROR          ; Error 1 if NC
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
    DEFINE USE_VORTEX
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
FILENAME_SCRIPT:
    DB "@FILENAME_SCRIPT"
    DB $FF

FILE_HEADER:
NUM_CHUNKS          EQU  FILE_HEADER
CHUNK_OFFSET_PTR    EQU  FILE_HEADER + 2
CHUNK_SIZE_PTR      EQU  FILE_HEADER + 4
TOKENS_ADDR         EQU  FILE_HEADER + 6
CHARSET_ADDR        EQU  FILE_HEADER + 8
CHARSET_WIDTHS_ADDR EQU  FILE_HEADER + 10


SIZE_INTERPRETER = $ - START_INTERPRETER
    SAVEBIN "@INTERPRETER_FILENAME", START_INTERPRETER, SIZE_INTERPRETER
