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

    IFDEF USE_VORTEX
;Loads the music file with number on A
LOAD_MUSIC:
    ld de, TEXT_BUFFER
    ld h, 0
    ld l, a
    call CONV_HL_TO_STR
    ld hl, VORTEX_EXTENSION
    ld b, 5
.loop1:
    ld a, (hl)
    ld (de), a
    inc hl
    inc de
    djnz .loop1

; Opening file
    ld hl, TEXT_BUFFER+2
    ld bc, VORTEX_FILE_H+1   ; FIle id=0, exclusive read
    ld de, $0002            ; Open file
    call PLUS3_DOS_OPEN
    jp nc, DISK_ERROR

    ld b, VORTEX_FILE_H>>8
    call PLUS3_DOS_GET_EOF
    jp nc, DISK_ERROR

    ld a, e               ;test if E > 0
    or a
    jr nz, .invalid_size
    ld a, h
    cp $20                ; h-$20
    jr c, .valid_size     ; h < $20
    jr nz, .invalid_size  ; h > $20
    ld a, l               
    or a
    jr z, .valid_size
.invalid_size:
    ld a, 4
    jp SYS_ERROR
.valid_size:
    ex hl, de             ; hl -> de
    ld hl, MDLADDR
    ld bc, VORTEX_FILE_H+VORTEX_BANK
    call PLUS3_DOS_READ        ; Read header
    jp nc, DISK_ERROR          ; Error 1 if NC

    ld a, VORTEX_BANK
    call SET_RAM_BANK
    push af
    call VTR_INIT
    pop af
    call SET_RAM_BANK

    ld hl, VTR_STAT
    res 2, (hl)
    set 1, (hl)

    ld b, VORTEX_FILE_H>>8
    call PLUS3_DOS_CLOSE
    ret c
    jp DISK_ERROR          ; Error 1 if NC

VORTEX_EXTENSION:
    DB ".PT3", $FF

    ;INCLUDE "VTII10bG.asm"
    ENDIF
