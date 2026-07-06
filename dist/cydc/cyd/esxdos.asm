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
; ESXDOS file API wrappers (divMMC / divIDE, SD card).
;
; Called from the RUNTIME (savegame; in a later phase also image/music streaming).
; The bootstrap loader (loaderesxdos.asm) does NOT use these; it issues its own
; RST $08 calls with interrupts kept disabled the whole time.
;
; ABI note (esxDOS, RST $08 + DEFB hook): entry params in registers, on return
; AF/BC/DE/HL change, and *the carry flag means ERROR* (CF=1 error, A=errno;
; CF=0 success). This is the OPPOSITE of +3DOS (where CF=1 meant OK), so the
; savegame_esxdos code branches on `jr c` for errors, not `jr nc`.
;
; The divMMC automap only touches $0000-$3FFF, so RST $08 issued from the
; interpreter ($8000+) with buffers at $C000+ is safe. Interrupts are disabled
; around each call (DI on entry, EI on exit) so the 50 Hz ISR -- whose music
; player pages RAM banks via $7FFD -- cannot fire mid-transfer and corrupt the
; banking of the operation. This mirrors what plus3dos.asm does with its
; SETUP/RESTORE_BANKS wrappers. Callers must therefore invoke these with
; interrupts enabled (the runtime always does).
; ==============================================================================

ESX_F_OPEN          EQU $9A
ESX_F_CLOSE         EQU $9B
ESX_F_READ          EQU $9D
ESX_F_WRITE         EQU $9E

; fopen() access modes (esxdos.h).
ESX_MODE_READ        EQU $01
ESX_MODE_WRITE       EQU $02
ESX_MODE_OPEN_EXIST  EQU $00
ESX_MODE_OPEN_CREAT  EQU $08
ESX_MODE_CREAT_TRUNC EQU $0C   ; open for create, truncate if it already exists

ESX_DRIVE_DEFAULT    EQU '*'   ; current/default drive

; ------------------------------------------------------------------------------
; Open a file.
;   IX = filename (ASCIIZ), B = access mode.
; On exit: A = file handle, CF = 1 on error (A = errno).
ESXDOS_F_OPEN:
    di
    ld a, ESX_DRIVE_DEFAULT
    rst $08
    DB ESX_F_OPEN
    ei
    ret

; ------------------------------------------------------------------------------
; Read from a file.
;   A = handle, IX = destination address, BC = byte count.
; The destination bank must already be paged in at $C000 by the caller (F_READ
; reads into the CURRENT memory map, unlike +3DOS which pages a bank for you).
; On exit: CF = 1 on error, BC = bytes actually read.
ESXDOS_F_READ:
    di
    rst $08
    DB ESX_F_READ
    ei
    ret

; ------------------------------------------------------------------------------
; Write to a file.
;   A = handle, IX = source address, BC = byte count.
; On exit: CF = 1 on error.
ESXDOS_F_WRITE:
    di
    rst $08
    DB ESX_F_WRITE
    ei
    ret

; ------------------------------------------------------------------------------
; Close a file.
;   A = handle.
; On exit: CF = 1 on error.
ESXDOS_F_CLOSE:
    di
    rst $08
    DB ESX_F_CLOSE
    ei
    ret
