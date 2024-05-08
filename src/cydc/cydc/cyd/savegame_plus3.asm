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
;

; B <- Start flag
; C <- Number of flags to save
CHK_RAMLOAD_PARAMETERS:
    ld a, c
    or b                  ;Both are zero
    ret z
    ld a, c               ; Number to copy 0 = 256
    or a
    jr z, 1f
    ld a, b
    add a, c
    ret nc                ; If NC then < 256 so OK
1:  xor a                 ; size = 256 - index
    sub b
    ld c, a
    ret

; B <- Start flag
; C <- Number of flags to load
RAMLOAD:
    ld hl, SAVE_FLAGS
    ld de, FLAGS
    jr COPY_FLAGS
; B <- Start flag
; C <- Number of flags to save
RAMSAVE:
    ;Clear save flags
    exx
    ld hl, SAVE_FLAGS
    ld de, SAVE_FLAGS+1
    ld bc, 255
    xor a
    ld (hl), a
    ldir
    exx
    ld hl, FLAGS
    ld de, SAVE_FLAGS
COPY_FLAGS:
    ld a, b
    or a
    jr z, 2f
1:  inc hl
    inc de
    djnz 1b  ;until B = 0
2:  ld a, c
    or a
    jr nz, 3f
    inc b    ;BC = 256
3:  ldir     ;We only have C
    ret

;https://wikiti.brandonw.net/index.php?title=Z80_Routines:Security:CRC16  
CRC16:
;Borrowed from http://zilog.sh.cvut.cz/~base/misc/z80bits.html
; and moddified to be a loop
;The arrow comments show what lines I added or commented out from the original.
;Inputs:    de->data bc=number of bytes
;Outputs:   hl=CRC16
    PUSH BC 
    PUSH DE
    PUSH AF
    LD HL,$FFFF
    PUSH BC
.CRC16_Read:
    LD A,(DE)
    INC DE
    XOR H
    LD H,A
    LD B,8
.CRC16_CrcByte:
    ADD HL,HL
    JR NC, .CRC16_Next
    LD A,H
    XOR $10
    LD H,A
    LD A,L
    XOR $21
    LD L,A
.CRC16_Next:
    DJNZ .CRC16_CrcByte
;    DEC C 
    POP BC
    DEC BC
    PUSH BC
    LD A,B
    OR C
    JR NZ, .CRC16_Read
    POP BC
    POP AF
    POP DE
    POP BC
    ret

    ;test checksum
; If Z = 1 , valid
; IF Z = 0, INVALID
TEST_CHECKSUM:
    ld de, SAVE_START
    ld bc, SAVE_SIZE-2
    call CRC16
    ld de, (SAVE_CHECKSUM)
    ld a, l
    cp e
    ret nz
    ld a, h
    cp d
    ret

;test game signature
; If Z = 1 , valid
; IF Z = 0, INVALID
COMPARE_GAME_ID:
    ld de, SAVE_GAME_ID
    ld hl, GAME_ID
    ld b, 16
1:  ld a, (de)
    cp (hl)
    ret nz
    djnz 1b
    xor a        ;Clear Z
    ret

BUILD_FILENAME:
    ; Input A <- File Index
    ; Output HL <- Start of filename string
    ld de, TEXT_BUFFER
    ld h, 0
    ld l, a
    call CONV_HL_TO_STR
    ld hl, SAV_EXTENSION
    ld b, 5
1:  ld a, (hl)
    ld (de), a
    inc hl
    inc de
    djnz 1b
    ld hl, TEXT_BUFFER+2
    ret

SAV_EXTENSION:
    DB ".SAV", $FF


; 0 <- Operation OK
; 1 <- Disk/tape error.
DO_SAVE:
    ; Input A <- Slot
    ; B <- Start flag
    ; C <- Number of flags to save
    push ix
    push hl
    ld a, (CURR_SAVE_SLOT)
    ld (SAVE_SLOT), a
    ld (SAVE_NVARS), bc
    call RAMSAVE
    ;Copy game ID
    ld de, SAVE_GAME_ID
    ld hl, GAME_ID
    ld bc, 16
    ldir
    ld de, SAVE_START
    ld bc, SAVE_SIZE-2
    call CRC16
    ld (SAVE_CHECKSUM), hl
    ld a, (SAVE_SLOT)
    call BUILD_FILENAME
    ld bc, SAVEGAME_FILE_H+3 ; FIle id, exclusive read/write
    ld de, $0204             ; Open file
    call PLUS3_DOS_OPEN
    jr nc, .disk_error
    ld bc, SAVEGAME_FILE_H+SAVEGAME_BANK
    ld de, SAVE_SIZE
    ld hl, SAVE_START
    call PLUS3_DOS_WRITE
    jr nc, .disk_error
    ld b, SAVEGAME_FILE_H>>8
    call PLUS3_DOS_CLOSE
    jr nc, .disk_error
    xor a
    jr .end
.disk_error:
    ld (LAST_DISK_ERROR), a
    ld b, SAVEGAME_FILE_H>>8
    call PLUS3_DOS_ABANDON
    ld a, 1
.end:
    ld (LAST_SAVE_RESULT), a
    pop hl
    pop ix
    ret

; 0 <- Operation OK
; 1 <- Disk/tape error.
; 2 <- GameId error.
; 3 <- Slot error
; 4 <- Checksum error
DO_LOAD:
    push ix
    push hl
    ld a, (CURR_SAVE_SLOT)
    call BUILD_FILENAME
    ld bc, SAVEGAME_FILE_H+3 ; FIle id, exclusive read/write
    ld de, $0002             ; Open file
    call PLUS3_DOS_OPEN
    jr nc, .disk_error
    ld bc, SAVEGAME_FILE_H+SAVEGAME_BANK
    ld de, SAVE_SIZE
    ld hl, SAVE_START
    call PLUS3_DOS_READ
    jr nc, .disk_error
    ld b, SAVEGAME_FILE_H>>8
    call PLUS3_DOS_CLOSE
    jr nc, .disk_error
    call TEST_CHECKSUM
    jr nz, .chksum_error
    call COMPARE_GAME_ID
    jr nz, .gameid_error
    ld a, (CURR_SAVE_SLOT)
    ld c, a
    ld a, (SAVE_SLOT)
    cp c
    jr nz, .slot_error
    ld bc, (SAVE_NVARS)
    call RAMLOAD
    xor a
    jr .end
.gameid_error:
    ld a, 2
    jr .end
.slot_error:
    ld a, 3
    jr .end
.chksum_error:
    ld a, 4
    jr .end
.disk_error:
    ld (LAST_DISK_ERROR), a
    ld b, SAVEGAME_FILE_H>>8
    call PLUS3_DOS_ABANDON
    ld a, 1
.end:
    ld (LAST_SAVE_RESULT), a
    pop hl
    pop ix
    ret
    

;------------------------------------------

