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
; ESXDOS music streaming (divMMC / divIDE, SD card).
;
; Sibling of music_manager.asm (+3): the Vortex (PT3) track streams from the SD
; card via the esxDOS RST $08 file API into the LOW half ($C000-$DFFF, 8 KB) of
; the staging bank 6 -- the SAME bank whose HIGH half ($E000) holds PIC_BUFFER for
; streamed images (screen_manager_esxdos). A PT3 is capped at 8 KB (cydc.py), so
; it ends at $E000 and never overlaps PIC_BUFFER. With Vortex music present the
; whole bank 6 is reserved (out of content allocation; see cydc.py).
;
; Unlike +3 (MDLADDR/VORTEX_BANK are EQU constants), cyd_esxdos inherits the tape
; MDLADDR/VORTEX_BANK *variables*, so we set them to $C000/6 at run time and init
; with VTR_INIT_HL (HL = module address) -- the ISR reads (VORTEX_BANK) and plays
; from that bank. This avoids rebasing cyd_esxdos on cyd_plus3.
;
; WyzTracker is unchanged from the tape/+3 path (its player + song live resident
; in their own bank 1); only WYZ_CALL is provided here.
; ==============================================================================

VORTEX_STAGE_BANK   EQU 6       ; == IMG_BANK (screen_manager_esxdos); track $C000, PIC_BUFFER $E000

    IFDEF USE_VORTEX
;Loads the music file with number on A
LOAD_MUSIC:
    push ix
    ; Build "NNN.BIN" (ASCIIZ) at TEXT_BUFFER+2.
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
    ld hl, TEXT_BUFFER+2
    push hl
    pop ix
    ld b, ESX_MODE_READ
    call ESXDOS_F_OPEN          ; A = handle, CF=1 on error
    jp c, DISK_ERROR
    ld (MUS_HANDLE), a

    ; Read the 2-byte size header into TEXT_BUFFER (resident low RAM).
    ld ix, TEXT_BUFFER
    ld bc, 2
    ld a, (MUS_HANDLE)
    call ESXDOS_F_READ
    jp c, DISK_ERROR

    ; Page the staging bank and stream the PT3 body to $C000.
    ld a, VORTEX_STAGE_BANK
    or ROM48KBASIC
    call SET_RAM_BANK
    ld ix, $C000
    ld bc, (TEXT_BUFFER)        ; PT3 size (<= 8 KB)
    ld a, (MUS_HANDLE)
    call ESXDOS_F_READ
    jp c, DISK_ERROR

    ld a, (MUS_HANDLE)
    call ESXDOS_F_CLOSE

    ; The module lives at $C000 in bank 6; record it for the ISR (tape-style vars).
    di
    ld hl, $C000
    ld (MDLADDR), hl
    ld a, VORTEX_STAGE_BANK
    ld (VORTEX_BANK), a

    ld bc, $7ffd
    push bc
    ld hl, (MDLADDR)
    ld a, (VORTEX_BANK)
    or ROM48KBASIC
    out (c), a                  ; page the track bank for VTR_INIT_HL
    call VTR_INIT_HL
    pop bc
    ld a, (PLUS3_DOS_BANKM)
    out (c), a

    ld hl, VTR_STAT
    res 2, (hl)
    set 1, (hl)
    ei

    ; Page the running script bank back so the interpreter can keep fetching.
    ld a, (SCRIPT_BANK)
    or ROM48KBASIC
    call SET_RAM_BANK
    pop ix
    ret

MUS_HANDLE:
    DB 0

VORTEX_EXTENSION:
    DB ".BIN", 0

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
