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
