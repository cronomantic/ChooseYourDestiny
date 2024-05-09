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
    ld a, c
    or a
    jr z, 1f
    ld a, b
    add a, c
    ret nc                ; If NC then < 256 so OK
1:  xor a
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

;------------------------------------------
; 0 <- Operation OK
; 1 <- Disk/tape error.
DO_SAVE:
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
    ld a, ($5b5c)
    or ROM48KBASIC
    call SET_RAM_BANK
    push af
    ld a, $FF
    ld ix, SAVE_START
    ld de, SAVE_SIZE
;Save
; On entry:
;  A=block type
;  IX=start
;  DE=length
    call $04C6      ; Call SA_BYTES+4
; On exit:
;   C    : Ok
;   NC   : SPACE pressed
    jr nc, .save_error
    xor a
    jr END_TAPE_OP
.save_error:
    ld a, 1
    jr END_TAPE_OP

; 0 <- Operation OK
; 1 <- Disk/tape error.
; 2 <- GameId error.
; 3 <- Slot error
; 4 <- Checksum error
DO_LOAD:
    push ix
    push hl
    ld a, ($5b5c)
    or ROM48KBASIC
    call SET_RAM_BANK
    push af
    ld a, $FF
    ld ix, SAVE_START
    ld de, SAVE_SIZE
    scf
;Loading data
; On entry:
;  A=block type
;  IX=start
;  DE=length
;  CS=load, CC=verify
    inc d
    ex af, af'       ; Set up flags
    dec d
    di               ; Disable interupts
    call $0562       ; Call LD_BYTES+12
;   C    : Ok
;   NC   : SPACE pressed or Loading error
    ei
    jr nc, .load_error
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
    jr END_TAPE_OP
.gameid_error:
    ld a, 2
    jr END_TAPE_OP
.slot_error:
    ld a, 3
    jr END_TAPE_OP
.chksum_error:
    ld a, 4
    jr END_TAPE_OP
.load_error:
    ld a, 1
END_TAPE_OP:
    ld (LAST_SAVE_RESULT), a
    ld a, (BORDCR)
    rrca
    rrca
    rrca
    and %00000111
    call BORDER
    pop af
    call SET_RAM_BANK
    pop hl
    pop ix
    ret

