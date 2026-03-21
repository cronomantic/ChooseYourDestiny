; ==============================================================================
; Choose Your Destiny - Dandanator MLD savegame backend
; ==============================================================================

; Fixed 4KB EEPROM sectors reserved for save slots.
; Slot 0 -> sector 124, slot 1 -> 125, slot 2 -> 126, slot 3 -> 127
SAVE_SECTOR_BASE    EQU 124
SAVE_SECTOR_SIZE    EQU $1000
SAVE_SLOTS_MASK     EQU %00000011

; B <- Start flag
; C <- Number of flags to save
CHK_RAMLOAD_PARAMETERS:
    ld a, c
    or b
    ret z
    ld a, c
    or a
    jr z, 1f
    ld a, b
    add a, c
    ret nc
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
    djnz 1b
2:  ld a, c
    or a
    jr nz, 3f
    inc b
3:  ldir
    ret

CRC16:
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

COMPARE_GAME_ID:
    ld de, SAVE_GAME_ID
    ld hl, GAME_ID
    ld b, 16
1:  ld a, (de)
    cp (hl)
    ret nz
    djnz 1b
    xor a
    ret

; ---------------- Dandanator commands ----------------
PAUSELOOPSN EQU 64

DAN_CMD_B:
.slot_b:
    nop
    nop
    ld (0), a
    djnz .slot_b
    ld b, PAUSELOOPSN
.wait_b:
    djnz .wait_b
    ret

DAN_RESTORE_ROM:
    ld b, 33
    jp DAN_CMD_B

DAN_SET_SLOT_A:
    ld b, a
    jp DAN_CMD_B

; Command 48, data1, data2 + confirmation pulse
DAN_SPECIAL_48:
    push af
    ld b, 48
    call DAN_CMD_B
    ld b, d
    call DAN_CMD_B
    ld b, e
    call DAN_CMD_B
    ld (0), a
    ld b, PAUSELOOPSN
.wait_s:
    djnz .wait_s
    pop af
    ret

; Input: A = save slot [0..3]
; Output: A = sector [124..127], E = sector-quarter [0..3], D preserved-ish
GET_SAVE_SECTOR:
    and SAVE_SLOTS_MASK
    ld e, a
    add a, SAVE_SECTOR_BASE
    ld c, a
    ld a, c
    and %00000011
    ld e, a
    ld a, c
    ret

; Input: A = absolute sector [0..127]
DAN_EEPROM_ERASE_SECTOR:
    push af
    ld d, 16
    ld e, a
    call DAN_SPECIAL_48

    ; JEDEC sector erase sequence, using #1555 / #2AAA aliases.
    ; DE must point to an address inside the target 4KB quarter.
    pop af
    and %00000011
    rlca
    rlca
    rlca
    rlca
    ld d, a
    ld e, 0

    ld a, $AA
    ld ($1555), a
    rrca
    ld ($2AAA), a
    ld a, $80
    ld ($1555), a
    ld a, $AA
    ld ($1555), a
    rrca
    ld ($2AAA), a
    ld a, $30
    ld (de), a

.waitsec:
    ld a, (de)
    ld b, a
    ld a, (de)
    xor b
    jr nz, .waitsec
    ret

; Input: A = absolute sector [0..127], HL = source buffer (4KB)
DAN_EEPROM_WRITE_SECTOR:
    push hl
    push af
    ld d, 32
    ld e, a
    call DAN_SPECIAL_48

    pop af
    and %00000011
    rlca
    rlca
    rlca
    rlca
    ld d, a
    ld e, 0
    pop hl

    ld bc, SAVE_SECTOR_SIZE
.write_loop:
    ld a, $AA
    ld ($1555), a
    rrca
    ld ($2AAA), a
    ld a, $A0
    ld ($1555), a
    ldi
    call .delay
    jp pe, .write_loop
    ret
.delay:
    ld a, (hl)
    ret

; Input: A = absolute sector [0..127]
; Output: PIC_BUFFER contains 4KB payload
DAN_READ_SECTOR_TO_BUFFER:
    push af
    ; Sector 124..127 all live in slot 32 of EEPROM map.
    ld a, 32
    call DAN_SET_SLOT_A

    pop af
    and %00000011
    rlca
    rlca
    rlca
    rlca
    ld h, a
    ld l, 0
    ld de, PIC_BUFFER
    ld bc, SAVE_SECTOR_SIZE
    ldir

    call DAN_RESTORE_ROM
    ret

; ------------------------------------------
; 0 <- Operation OK
; 1 <- Dandanator I/O error
DO_SAVE:
    push ix
    push hl

    ld a, (CURR_SAVE_SLOT)
    and SAVE_SLOTS_MASK
    ld (SAVE_SLOT), a
    ld (SAVE_NVARS), bc

    call RAMSAVE

    ld de, SAVE_GAME_ID
    ld hl, GAME_ID
    ld bc, 16
    ldir

    ld de, SAVE_START
    ld bc, SAVE_SIZE-2
    call CRC16
    ld (SAVE_CHECKSUM), hl

    ; Build fixed 4KB snapshot in PIC_BUFFER
    ld hl, SAVE_START
    ld de, PIC_BUFFER
    ld bc, SAVE_SIZE
    ldir
    ld hl, PIC_BUFFER + SAVE_SIZE
    ld de, PIC_BUFFER + SAVE_SIZE + 1
    ld bc, SAVE_SECTOR_SIZE - SAVE_SIZE - 1
    ld (hl), $FF
    ldir

    ld a, (SAVE_SLOT)
    call GET_SAVE_SECTOR
    push af
    call DAN_EEPROM_ERASE_SECTOR
    pop af
    ld hl, PIC_BUFFER
    call DAN_EEPROM_WRITE_SECTOR

    call DAN_RESTORE_ROM
    xor a
    jr .end

.end:
    ld (LAST_SAVE_RESULT), a
    pop hl
    pop ix
    ret

; 0 <- Operation OK
; 1 <- Dandanator I/O error
; 2 <- GameId error
; 3 <- Slot error
; 4 <- Checksum error
DO_LOAD:
    push ix
    push hl

    ld a, (CURR_SAVE_SLOT)
    and SAVE_SLOTS_MASK
    call GET_SAVE_SECTOR
    call DAN_READ_SECTOR_TO_BUFFER

    ld hl, PIC_BUFFER
    ld de, SAVE_START
    ld bc, SAVE_SIZE
    ldir

    call TEST_CHECKSUM
    jr nz, .chksum_error
    call COMPARE_GAME_ID
    jr nz, .gameid_error

    ld a, (CURR_SAVE_SLOT)
    and SAVE_SLOTS_MASK
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

.end:
    ld (LAST_SAVE_RESULT), a
    pop hl
    pop ix
    ret
