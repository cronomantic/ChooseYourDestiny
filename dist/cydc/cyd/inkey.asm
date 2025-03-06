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


INKEY:
    exx

    call KEY_SCAN
    jp nz, .empty_inkey

    call K_TEST
    jp nc, .empty_inkey

    dec d   ; D is expected to be FLAGS so set bit 3 $FF
    ; 'L' Mode so no keywords.
    ld e, a ; main key to A
    ; C is MODE 0 'KLC' from above still.
    call K_DECODE ; routine K-DECODE
    ;Keycode on A
    exx
    ret
.empty_inkey:
    xor a
    exx
    ret

INKEY_WAIT_ITERATIONS       EQU 10
INKEY_NO_WAIT_ITERATIONS    EQU INKEY_WAIT_ITERATIONS


INKEY_SELECT_WAIT_MODE:
    or a
    jr nz, INKEY_NO_WAIT

INKEY_WAIT:
    push bc
1:  call INKEY
    or a
    jr z, 1b       ;Detect keypress
    ld c, a
    ld b, INKEY_WAIT_ITERATIONS
2:  call INKEY
    or a
    jr z, 2b       ;Detect keypress again
    cp c
    jr nz, 1b      ;Different key, we begin again
    djnz 2b        ;Decrease counter
3:  call INKEY
    or a
    jr nz, 3b       ;Detect key release
    ld a, c
    pop bc
    ret

INKEY_NO_WAIT:
    push bc
1:  call INKEY
    or a
    jr z, .empty_inkey
    ld c, a
    ld b, INKEY_NO_WAIT_ITERATIONS
2:  call INKEY
    or a
    jr z, .empty_inkey
    cp c
    jr nz, 1b      ;Different key, we begin again
    djnz 2b        ;Decrease counter
    ld a, c        ;Returns key pressed
.empty_inkey:
    pop bc
    ret

KEYPRESS_RIGHT EQU %00000001
KEYPRESS_LEFT  EQU %00000010
KEYPRESS_DOWN  EQU %00000100
KEYPRESS_UP    EQU %00001000
KEYPRESS_FIRE  EQU %00010000

;
; Keypress format:
;   xxxKUDLR

INKEY_MENU:
    push bc
    xor a
    ld c, a
    call INKEY
.right:
    cp $09  ; cursor right
    jr z, .right_ok
    cp 'p'
    jr nz, .left
.right_ok:
    ld b, a
    ld a, c
    or KEYPRESS_RIGHT
    ld c, a
    ld a, b
.left:
    cp $08  ; cursor left
    jr z, .left_ok
    cp 'o'
    jr nz, .down
.left_ok:
    ld b, a
    ld a, c
    or KEYPRESS_LEFT
    ld c, a
    ld a, b
.down:
    cp $0A  ; cursor down
    jr z, .down_ok
    cp 'a'
    jr nz, .up
.down_ok:
    ld b, a
    ld a, c 
    or KEYPRESS_DOWN
    ld c, a
    ld a, b
.up:
    cp $0B  ; cursor up
    jr z, .up_ok
    cp 'q'
    jr nz, .selected
.up_ok:
    ld b, a
    ld a, c
    or KEYPRESS_UP
    ld c, a
    ld a, b
.selected:
    cp ' '
    jr z, .selected_ok
    cp 'm'
    jr z, .selected_ok
    cp 13
    jr nz, .kempston
.selected_ok:
    ld a, KEYPRESS_FIRE
    or c
    ld c, a
.kempston:
    call KEMPSTON
    or c
    pop bc
    ret

KEMPSTON:
    ld a, (KEMPSTON_VALUE)
    cp $FF         ;Bus value if joystick not connected on blanking to avoid floating bus issues
    jr z, .invalid
    in a, ($1F)    ;Read kempston
    ld b, a
    and %00000011  ; Up + Down is invalid
    cp %00000011
    jr z, .invalid 
    ld a, b
    and %00001100  ; Left + Right is invalid
    cp %00001100
    jr z, .invalid 
    ld a, b
    ret
.invalid:
    xor a
    ret
