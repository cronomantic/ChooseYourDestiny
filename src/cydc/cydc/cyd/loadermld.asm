; ==============================================================================
; Choose Your Destiny - MLD loader (slot 0)
; ==============================================================================

    DEVICE ZXSPECTRUM128

    ORG 0

START_LOADER:
    di

    ; Ensure 48K ROM + RAM 0 visible before bulk copies.
    ld a, $04
    ld bc, $1FFD
    out (c), a

    ld a, $10
    ld bc, $7FFD
    out (c), a

    ld sp, $5FFF

    ; Copy RAM routine that performs slot mapping and block loads.
    ld hl, RAM_ROUTINE_ROM
    ld de, RAM_ROUTINE_ADDR
    ld bc, RAM_ROUTINE_END - RAM_ROUTINE_ROM
    ldir

    jp RAM_ROUTINE_ADDR

RAM_ROUTINE_ADDR EQU $5F00

RAM_ROUTINE_ROM:
    DISP RAM_ROUTINE_ADDR
RAM_ROUTINE:
    ; Cache MLDoffset at DAN_MLD_OFFSET ($5C00) while slot 0 is still mapped here.
    ; This fixes a multi-block bug (later loop iterations map data slots, so reading
    ; (MLDoffset) would pick up garbage from the data slot instead of the loader slot).
    ; The saved value is also read by bank_dan.asm SET_DAN_BANK at game runtime.
    ld a, (MLDoffset)
    ld ($5C00), a           ; DAN_MLD_OFFSET – must match bank_dan.asm
    ld hl, BLOCK_TABLE
.next_block:
    ld a, (hl)
    cp $FF
    jr z, .run_game

    ; Relative slot -> absolute Dandanator slot command (1..32)
    ld d, a
    ld a, ($5C00)           ; use cached value; Dandanator may be on a data slot now
    add a, d
    inc a
    call DAN_SET_SLOT_A

    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push de            ; source offset inside slot

    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push de            ; destination address in RAM

    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    push bc            ; block size

    ld c, (hl)
    inc hl
    call SETRAM_C      ; map destination RAM bank at C000 if needed

    pop bc             ; size
    pop de             ; destination
    pop hl             ; source
    ldir

    jr .next_block

.run_game:
    call DAN_RESTORE_ROM
    ld c, 0
    call SETRAM_C
    jp $8000

; C = RAM bank [0..7]
SETRAM_C:
    ld a, (23388)
    and %11111000
    or c
    ld bc, $7FFD
    out (c), a
    ld (23388), a
    ret

DAN_RESTORE_ROM:
    ld b, 33
    jp DAN_CMD_B

DAN_SET_SLOT_A:
    ld b, a
    jp DAN_CMD_B

DAN_CMD_B:
.slot_loop:
    nop
    nop
    ld (0), a
    djnz .slot_loop
    ld b, 64
.wait_loop:
    djnz .wait_loop
    ret

RAM_ROUTINE_END:
    ENT

BLOCK_TABLE:
@{BLOCK_TABLE}

PREVIEW_SCREEN:
@{PREVIEW_SCR_DATA}
PREVIEW_SCREEN_END:

    ; Footer required by Dandanator MLD parser.
    DEFS 16362-$, $FF
MLDoffset:
    DEFB 0
    DEFB @{MLD_TYPE}      ; MLD type: $83=48K, $88=128K, $C8=+2A
    DEFB 4                ; nsectors (fixed snapshot mode)
    DEFB 0, 0, 0, 0       ; sector IDs (rom generator may rewrite)
    DEFW 0                ; Data table address (unused)
    DEFW 0                ; Data row size (unused)
    DEFW 0                ; Number of rows (unused)
    DEFB 0                ; Slot byte offset in row (unused)
    DEFW @{PREVIEW_SCR_ADDR} ; Preview screen addr
    DEFW @{PREVIEW_SCR_SIZE} ; Preview screen size
    DEFB "MLD", 0

    SAVEBIN "@SLOT0_BIN", 0, $4000
