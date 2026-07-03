; ==============================================================================
; Choose Your Destiny - Dandanator bank management
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

; Fixed free-RAM address (below the 0x5D00 game-variable area) where the
; loader stores the MLD slot base offset before handing control to the game.
; Both loadermld.asm (loader) and this module (runtime) must agree on $5C00.
DAN_MLD_OFFSET EQU $5C00

; Address where a Dandanator command byte is written. On real hardware any
; address inside the mapped slot ($0000-$3FFF) works (it just counts write
; pulses); ZEsarUX emulates the command interface at $0001 (DDNTRADDRCMD) and
; reads the written value as the command number, so both agree on $0001.
DAN_CMD_ADDR EQU $0001

;====================================================
; SET_DAN_BANK
;   Switch the Dandanator to a given MLD-relative slot.
;
;   Input : A  = MLD-relative slot index
;               (0=slot 0/loader, 1=interpreter, 2=first data slot, ...)
;   Effect: Dandanator maps that slot at 0x0000-0x3FFF.
;   Registers: all preserved (AF, BC saved/restored internally).
;   Interrupts: disabled during the write sequence, re-enabled after.
;
;   Absolute Dandanator bank = (DAN_MLD_OFFSET) + A + 1
;====================================================
SET_DAN_BANK:
    push af
    push bc
    di
    ; absolute = base + slot + 1  (Dandanator counts from 1)
    ld b, a
    ld a, (DAN_MLD_OFFSET)
    add a, b
    inc a
    ld b, a             ; B = command number (absolute slot) = pulse count
    ; Dual protocol (see the Dandanator menu's SENDNRCMD): write the command
    ; number itself (A) as the VALUE to DDNTRADDRCMD ($0001), repeated B times.
    ; Real hardware counts the writes as pulses (value ignored); ZEsarUX reads
    ; the written VALUE at $0001 as the command number.
.loop:
    nop
    nop
    ld (DAN_CMD_ADDR), a ; A holds the absolute slot number
    djnz .loop
    ld b, 64            ; settling delay
.wait:
    djnz .wait
    ei
    pop bc
    pop af
    ret

;====================================================
; RESTORE_DAN_ROM
;   Return the Dandanator to pass-through (ROM) mode.
;   33 write-pulses selects the "no-cartridge" / 48K ROM state.
;   Registers: all preserved.
;====================================================
RESTORE_DAN_ROM:
    push af
    push bc
    di
    ld a, 33            ; command 33 = switch to internal ROM
    ld b, a             ; B = pulse count = 33
.loop:
    nop
    nop
    ld (DAN_CMD_ADDR), a
    djnz .loop
    ld b, 64
.wait:
    djnz .wait
    ei
    pop bc
    pop af
    ret
