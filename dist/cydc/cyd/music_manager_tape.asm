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

;Loads the music file with number on A
    IFDEF USE_VORTEX
LOAD_MUSIC:
    ld c, a
    ld b, TYPE_TRK
    call FIND_IN_INDEX

    di
    ld (MDLADDR), hl
    ld (VORTEX_BANK), a

    ld bc, $7ffd
    push bc    
    ld hl, (MDLADDR)
    ld a, (VORTEX_BANK)
    or ROM48KBASIC
    out (c), a
    call VTR_INIT_HL
    pop bc
    ld a, (PLUS3_DOS_BANKM)
    out (c), a

    ld hl, VTR_STAT
    res 2, (hl)
    set 1, (hl)
    ei

    ret
    ENDIF

    IFDEF USE_WYZ
; D -> Operation
; E -> Parameter
WYZ_CALL:
    di
    push hl
    push ix
    ld bc, $7ffd
    push bc
    ld a, WYZ_BANK|%00010000
    out (c), a  ;Sets bank
    ld a, d
    ld b, e
    CALL WYZ_TRACKER
    pop bc
    ld a, (PLUS3_DOS_BANKM)
    out (c), a
    pop ix
    pop hl
    ei
    ret
    ENDIF

