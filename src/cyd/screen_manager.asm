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

IMG_BANK        EQU 4
IMAGE_FILE_H    EQU 1 << 8


IMG_LOAD:
    ld de, TEXT_BUFFER
    ld h, 0
    ld l, a
    call CONV_HL_TO_STR
    ld hl, DCP_EXTENSION
    ld b, 5
.loop6:
    ld a, (hl)
    ld (de), a
    inc hl
    inc de
    djnz .loop6
    ld hl, TEXT_BUFFER+2
    ld bc, IMAGE_FILE_H+1   ; FIle id=0, exclusive read
    ld de, $0002            ; Open file
    call PLUS3_DOS_OPEN
    jp nc, DISK_ERROR

    ld hl, TEXT_BUFFER
    ld de, $02
    ld bc, IMAGE_FILE_H+IMG_BANK
    call PLUS3_DOS_READ        ; Read header
    jp nc, DISK_ERROR          ; Error 1 if NC

    ld hl, PIC_BUFFER
    ld bc, IMAGE_FILE_H+IMG_BANK
    ld de, (TEXT_BUFFER)
    call PLUS3_DOS_READ;
    jp nc, DISK_ERROR          ; Error 1 if NC

    ld a, IMG_BANK
    call SET_RAM_BANK
    push af

    call CLS_BUFFER
    ld hl, PIC_BUFFER_SCR
    ld de, SCREEN_BUFFER_PXL
    call dzx0_turbo
    ld de, SCREEN_BUFFER_ATT
    call dzx0_turbo

    ld a,(PIC_NUM_LINES_ATT)  ; Test if has mirroring
    ld b, a
    and %01111111
    ld (PIC_NUM_LINES_ATT), a ; Put the correct number of att lines
    ld (att_self_m), a ; Self modified code for later
    ld a, %10000000
    and b                      ; If Zero, then not mirroring
    jr z, .no_mirror

;Mirror pixels
    ld de, SCREEN_BUFFER_PXL
    ld a, (PIC_NUM_LINES_PXL)
    ld b, a
.loop1:
    ld c, b
    ld hl, 31
    add hl, de
    push hl
    ld b, 16
.loop2:
    ld a, (de)
    inc de
    ;inverting the byte
    exx  
    ld b, 8
.loop3:
    rra
    rl c
    djnz .loop3
    ld a, c
    exx
    ld (hl), a
    dec hl
    djnz .loop2
    pop de
    inc de
    ld b, c
    djnz .loop1

;Mirror attributtes
    ld de, SCREEN_BUFFER_ATT
    ld a, (PIC_NUM_LINES_ATT)
    ld b, a
.loop4:
    ld c, b
    ld hl, 31
    add hl, de
    push hl
    ld b, 16
.loop5:
    ld a, (de)
    inc de
    ld (hl), a
    dec hl
    djnz .loop5
    pop de
    inc de
    ld b, c
    djnz .loop4

.no_mirror:
    pop af
    call SET_RAM_BANK

    ld b, IMAGE_FILE_H>>8
    call PLUS3_DOS_CLOSE
    ret c
    jp DISK_ERROR          ; Error 1 if NC

COPY_SCREEN:
    call SET_CLEAR_COLOR
    push af
att_self_m+1:
    ld a, 0
    rrca
    rrca
    rrca
    ld b, a
    and %11100000
    ld c, a
    ld a, %00011111
    and b
    ld b, a
    dec bc
    pop af
    ld hl, SCR_ATT
    ld (hl), a
    ld de, SCR_ATT+1
    ldir
    ld a, 1
    ld (UPDATE_SCR_FLAG), a
    halt
1:  ld a, (UPDATE_SCR_FLAG)  ; Get flag
    or a
    jr nz, 1b
    ret

;--------------
SET_CLEAR_COLOR:
    ld A, (23693)      ;Get ATTR
    and %11111000      ;Mask INK
    ld B, A            ;Saving on b
    rrca
    rrca
    rrca               ;Move PAPER to the left
    and %00000111      ;Mask new INK
    or B               ;Set new INK the same as PAPER
    ret
;---------------
CLS_BUFFER:
    ld de, SCREEN_BUFFER_PXL+1
    ld hl, SCREEN_BUFFER_PXL
    ld bc, SCR_SIZE-1
    xor a
    ld (hl), 0
    ldir
    ret

LOAD_FILENAME:
    DB "000"
DCP_EXTENSION:
    DB ".CSC", $FF

;------------------------------------------------------------------------

