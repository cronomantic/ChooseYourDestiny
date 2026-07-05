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
; ESXDOS image streaming (divMMC / divIDE, SD card).
;
; Sibling of screen_manager.asm (+3): instead of +3DOS it uses the esxDOS RST $08
; file API to stream "NNN.CSC" images from the SD card into the resident image
; store SCREEN_BUFFER_*. The compressed image is F_READ into PIC_BUFFER ($E000),
; which lives in the HIGH half of the staging bank IMG_BANK; that bank's LOW half
; ($C000-$DFFF) is still available to the block allocator (unlike +3, which
; reserved the whole bank for the +3DOS disk cache). Decompression (ZX0) and the
; optional mirror are identical to +3/tape.
;
; F_READ writes into the CURRENT memory map, so IMG_BANK is paged in at $C000
; before reading to PIC_BUFFER. On exit the running script bank (SCRIPT_BANK) is
; paged back so the interpreter can keep fetching bytecode.
; ==============================================================================

IMG_BANK        EQU 6           ; staging bank; PIC_BUFFER lives in its $E000 half

IMG_LOAD:
    push ix
    ; Build "NNN.CSC" (ASCIIZ) at TEXT_BUFFER+2 (CONV_HL_TO_STR writes 5 padded
    ; digits; +2 keeps the last 3, matching the packaged {i:03d}.csc names).
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
    push hl
    pop ix                      ; IX = filename
    ld b, ESX_MODE_READ
    call ESXDOS_F_OPEN          ; A = handle, CF=1 on error
    jp c, DISK_ERROR
    ld (IMG_HANDLE), a

    ; Read the 2-byte size header into TEXT_BUFFER (resident low RAM).
    ld ix, TEXT_BUFFER
    ld bc, 2
    ld a, (IMG_HANDLE)
    call ESXDOS_F_READ
    jp c, DISK_ERROR

    ; Page the staging bank so PIC_BUFFER ($E000) is writable, then read the body.
    ld a, IMG_BANK
    or ROM48KBASIC
    call SET_RAM_BANK
    ld ix, PIC_BUFFER
    ld bc, (TEXT_BUFFER)         ; number of bytes after the size header
    ld a, (IMG_HANDLE)
    call ESXDOS_F_READ
    jp c, DISK_ERROR

    ld a, (IMG_HANDLE)
    call ESXDOS_F_CLOSE

    ; Ensure the staging bank is still paged (defensive) and decompress.
    ld a, IMG_BANK
    or ROM48KBASIC
    call SET_RAM_BANK

    ld a, (PIC_BUFFER)
    ld (PIC_NUM_LINES_PXL), a
    ld a, (PIC_BUFFER+1)
    ld (PIC_NUM_LINES_ATT), a
    call CLS_BUFFER
    ld hl, PIC_BUFFER_SCR
    ld de, SCREEN_BUFFER_PXL
    call dzx0_turbo
    ld de, SCREEN_BUFFER_ATT
    call dzx0_turbo

    ld a,(PIC_NUM_LINES_ATT)     ; Test if has mirroring
    ld b, a
    and %01111111
    ld (PIC_NUM_LINES_ATT), a
    ld (att_self_m), a
    ld a, %10000000
    and b
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
    ; Page the running script bank back so the interpreter can keep fetching.
    ld a, (SCRIPT_BANK)
    or ROM48KBASIC
    call SET_RAM_BANK
    pop ix
    ret

IMG_HANDLE:
    DB 0

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
1:  ld a, (UPDATE_SCR_FLAG)
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
;---------------

DCP_EXTENSION:
    DB ".CSC", 0

;------------------------------------------------------------------------
