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

OP_END:
    ;Close file
    ld b, SCRIPT_FILE_H>>8
    call PLUS3_DOS_CLOSE
    jp nc, DISK_ERROR          ; Error 1 if NC
    jp RESET_SYS

OP_TEXT:
    ld de, EXEC_LOOP
    push de
    jp PRINT_TOKEN_STR

OP_GOTO:
    ld c, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    ex de, hl
    ld a, (CHUNK)
    cp c       ; If the CHUNK is the same...
    jr z, .same_CHUNK:
    push hl
    ld a, c
    call LOAD_CHUNK
    pop hl
.same_CHUNK:
    jp EXEC_LOOP

OP_GOSUB:
    push hl
    ld de, 3
    add hl, de
    ex de, hl
    ld hl, (INT_STACK_PTR)
    dec hl
    ld (hl), e
    dec hl
    ld (hl), d
    dec hl
    ld a, (CHUNK)
    ld (hl), a
    ld (INT_STACK_PTR), hl
    pop hl
    jp OP_GOTO

OP_RETURN:
    ex de, hl
    ld hl, (INT_STACK_PTR)
    ld c, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld (INT_STACK_PTR), hl
    ex de, hl
    ld a, (CHUNK)
    cp c       ; If the CHUNK is the same...
    jr z, .same_CHUNK:
    push hl
    ld a, c
    call LOAD_CHUNK
    pop hl
.same_CHUNK:
    jp EXEC_LOOP

OP_SET_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (hl)
    inc hl
    ld (de), a
    jp EXEC_LOOP

OP_IF_EQ_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    cp c
    jp z, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_NE_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    cp c
    jp nz, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_LE_D:    ; p1 <= p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    cp c             ; p2 - p1
    jp nc, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_ME_D:    ;  p1 >= p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    ld b, a
    ld a, c
    cp b             ; p1 - p2
    jp nc, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_LT_D:         ; p1 < p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    ld b, a
    ld a, c
    cp b          ; p1 - p2
    jp c, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_MT_D:       ; p1 > p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)    
    cp c       ; p2 - p1
    jp c, OP_GOTO
    ;jr NO_GOTO_ON_CMP

NO_GOTO_ON_CMP:
    inc hl
    inc hl
    inc hl
    jp EXEC_LOOP

OP_IF_EQ_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (de)
    ld c, a
    ld a, (bc)
    cp c
    jp z, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_NE_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (de)
    ld c, a
    ld a, (bc)
    cp c
    jp nz, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_LE_I:    ; p1 <= p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (de)
    ld c, a
    ld a, (bc)
    cp c             ; p2 - p1
    jp nc, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_ME_I:    ;  p1 >= p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    cp c             ; p1 - p2
    jp nc, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_LT_I:         ; p1 < p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    cp c          ; p1 - p2
    jp c, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_IF_MT_I:       ; p1 > p2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (de)
    ld c, a
    ld a, (bc)
    cp c       ; p2 - p1
    jp c, OP_GOTO
    jr NO_GOTO_ON_CMP

OP_ADD_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    add a, c
    jr nc, 1f
    ld a, $FF
1:  ld (de), a
    jp EXEC_LOOP

OP_SUB_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    sub c
    jr nc, 1f
    xor a
1:  ld (de), a 
    jp EXEC_LOOP

OP_ADD_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    add a, c
    jr nc, 1f
    ld a, $FF
1:  ld (de), a
    jp EXEC_LOOP

OP_SUB_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    sub c
    jr nc, 1f
    xor a
1:  ld (de), a 
    jp EXEC_LOOP

OP_INK_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp INK

OP_PAPER_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp PAPER

OP_BRIGHT_D:
    ld a, (hl)
    inc hl
    push hl
    call BRIGHT
    pop hl
    jp EXEC_LOOP


OP_FLASH_D:
    ld a, (hl)
    inc hl
    push hl
    call FLASH
    pop hl
    jp EXEC_LOOP

OP_BORDER_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp BORDER

OP_PRINT_D:
    ld a, (hl)
    inc hl
    push hl
    call PRINT_A_BYTE
    pop hl
    jp EXEC_LOOP

OP_SET_I:
    ld c, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    ld e, c
    ld (de), a
    jp EXEC_LOOP

OP_INK_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp INK

OP_PAPER_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp PAPER

OP_BRIGHT_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call BRIGHT
    pop hl
    jp EXEC_LOOP

OP_FLASH_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call FLASH
    pop hl
    jp EXEC_LOOP

OP_BORDER_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp BORDER

OP_PRINT_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call PRINT_A_BYTE
    pop hl
    jp EXEC_LOOP

OP_MARGINS:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld a, (hl)
    inc hl
    push hl
    push af
    push de
    push bc
    ld a, c
    push af
    call SET_MARGINS
    pop hl
    jp EXEC_LOOP

OP_AT:
    ld b, (hl)
    inc hl
    ld a, (hl)
    inc hl
    push hl
    push af
    push bc  
    call SET_CURSOR
    pop hl
    jp EXEC_LOOP

OP_CENTER:
    ld de, EXEC_LOOP
    push de
    jp CENTER

OP_PICTURE_D:
    ld a, (hl)
    inc hl
    push hl
    call IMG_LOAD
    pop hl
    jp EXEC_LOOP

OP_DISPLAY_D:
    ld a, (hl)
    inc hl
    or a
    jp z, EXEC_LOOP
    push hl
    call COPY_SCREEN
    pop hl
    jp EXEC_LOOP

OP_PICTURE_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call IMG_LOAD
    pop hl
    jp EXEC_LOOP

OP_DISPLAY_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    or a
    jp z, EXEC_LOOP
    push hl
    call COPY_SCREEN
    pop hl
    jp EXEC_LOOP

OP_SET_RANDOM:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    push hl
    call RANDOM
    ld a, r
    rrca
    jr c, 1f
    ld a, l
    jr 2f
1:  ld a, h
2:  ld (de), a
    pop hl
    jp EXEC_LOOP

OP_AND_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    and c
    ld (de), a
    jp EXEC_LOOP

OP_OR_D:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld a, (de)
    or c
    ld (de), a
    jp EXEC_LOOP

OP_AND_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    and c
    ld (de), a
    jp EXEC_LOOP

OP_OR_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld b, d
    ld c, (hl)
    inc hl
    ld a, (bc)
    ld c, a
    ld a, (de)
    or c
    ld (de), a
    jp EXEC_LOOP

OP_NOT:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    cpl                   ;This is not a NOT
    ld (de), a
    jp EXEC_LOOP

OP_INKEY:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
1:  call INKEY
    or a
    jr z, 1b
    ld (de), a
    jp EXEC_LOOP

OP_WAIT:
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld (DOWN_COUNTER), de
.wait:
    ld de, (DOWN_COUNTER)
    ld a, d
    or e
    jr nz, .wait
    jp EXEC_LOOP

OP_OPTION:
    ld a, (NUM_OPTIONS)
    cp MAXIMUM_OPTIONS    ;test if number of options is MAX
    jr c,.option_ok
    ld a, 2
    jp SYS_ERROR
.option_ok:
    push af                    ;Adding the current position of the cursor
    push hl                    ;Store pointer
    push af
    call ADJUST_CHAR_POS  ;Advance to the best position for printing the choice
    push de
    push de                    ; ; d = POS_Y, e = POS_X
    ld a, NO_SELECTED_BULLET
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
    pop af
    ld hl, OPTIONS_POS
    sla a
    add a, l
    jr nc, 1f
    inc h
1:  ld l, a
    ld (hl), e                  ;Store address
    inc hl
    ld (hl), d
    pop hl
    ld de, OPTIONS_JMP_ADDR
    pop af
    ld b, a               ;Save current pos to B
    or a
    jr z, 2f              ;search the top of the address table
.loop:
    inc de                ;Advance 3 positions
    inc de
    inc de
    djnz .loop
2:  ldi                   ;Copy Address to address table
    ldi
    ldi
    inc a
    ld (NUM_OPTIONS), a   ;Increment options
    jp EXEC_LOOP

OP_WAITKEY:
    push hl                     ;Save pointer
    call ADJUST_CHAR_POS    ;Advance to the best position for printing the choice
    push de 
    push de                     ;d = POS_Y, e = POS_X
    ld a, WAIT_TO_KEY_BULLET 
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
1:  call INKEY
    cp 13
    jr z, .keyp
    cp 32
    jp z, .keyp
.animate_bullet:
    push de
    ld a, (CYCLE_OPTION)
    add a, WAIT_TO_KEY_BULLET 
    push de
    call GET_CHARACTER_POINTER
    pop de
    halt
    call PUT_8X8_CHAR
    pop de
    jr 1b
.keyp:
    push de 
    push de                     ;d = POS_Y, e = POS_X
    ld a, 32 
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
    ld (POS_X), de
2:  call INKEY
    or a
    jr nz, 2b
    pop hl
    jp EXEC_LOOP

OP_PAUSE:
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl                     ;Save pointer
    ld (DOWN_COUNTER), de
    call ADJUST_CHAR_POS    ;Advance to the best position for printing the choice
    push de 
    push de                     ;d = POS_Y, e = POS_X
    ld a, WAIT_TO_KEY_BULLET 
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
1:  call INKEY
    cp 13
    jr z, .keyp
    cp 32
    jr z, .keyp
    ld bc, (DOWN_COUNTER)
    ld a, b
    or c
    jr z, .keyp
.animate_bullet:
    push de
    ld a, (CYCLE_OPTION)
    add a, WAIT_TO_KEY_BULLET 
    push de
    call GET_CHARACTER_POINTER    
    pop de
    halt
    call PUT_8X8_CHAR
    pop de
    jr 1b
.keyp:
    push de 
    push de                     ;d = POS_Y, e = POS_X
    ld a, 32 
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
    ld (POS_X), de
2:  call INKEY
    or a
    jr nz, 2b
    pop hl
    jp EXEC_LOOP

OP_CHOOSE:
    xor a
    ld (SELECTED_OPTION), a
    ld a, (NUM_OPTIONS)
    or a
    jp nz, .options         ; No options available
    ld a, 3
    jp SYS_ERROR

.options:
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
.inkey:
    call INKEY
    cp 'q'
    jr z, .up
    cp 'a'
    jr z, .down
    cp ' '
    jr z, .selected
    cp 13
    jr z, .selected
    call ANIMATE_OPTION_BULLET
    ;jr 1b
    jr .inkey
.up:
    ld a, (SELECTED_OPTION)
    or a
    jr z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    pop af
    dec a
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY
    or a
    jr z, .inkey
    jr 2b
.down:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jr nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    pop af
    inc a
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jr z, .inkey
    jr 3b
.selected:
    ld hl, OPTIONS_JMP_ADDR
    ld a, (SELECTED_OPTION)
    or a
    jr z, 2f
1:  ld c, (hl)
    inc hl
    inc hl
    inc hl
    dec a
    jr nz, 1b
2:  xor a
    ld (NUM_OPTIONS), a
4:  call INKEY
    or a
    jr nz, 4b
    jp OP_GOTO

OP_CHOOSE_W:

    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl

    push de            ;Save timeout

    ld a, (hl)
    inc hl
    ld c, (hl)
    inc hl
    ld b, (hl)

    ld hl, TIMEOUT_OPTION
    ld (hl), a
    inc hl
    ld (hl), c
    inc hl
    ld (hl), b

    pop de           ;Restore timeout
    
    xor a
    ld (SELECTED_OPTION), a
    ld a, (NUM_OPTIONS)
    or a
    jp nz, .options         ; No options available
    ld a, 3
    jp SYS_ERROR

.options:
    ld (DOWN_COUNTER), de
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
.inkey:
    call INKEY
    cp 'q'
    jr z, .up
    cp 'a'
    jr z, .down
    cp ' '
    jr z, .selected
    cp 13
    jr z, .selected
    ld bc, (DOWN_COUNTER)
    ld a, c
    or b
    jr z, .count_elapsed
    call ANIMATE_OPTION_BULLET
    ;jr 1b
    jr .inkey
.up:
    ld a, (SELECTED_OPTION)
    or a
    jr z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    pop af
    dec a
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
6:  call INKEY
    or a
    jr z, .inkey
    jr 6b
.down:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jr nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    pop af
    inc a
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
5:  call INKEY
    or a
    jr z, .inkey
    jr 5b
.count_elapsed:
    ld a, MAXIMUM_OPTIONS
    jr 3f
.selected:
    ld a, (SELECTED_OPTION)
    or a
    jr z, 2f
3:  ld hl, OPTIONS_JMP_ADDR
1:  ld c, (hl)
    inc hl
    inc hl
    inc hl
    dec a
    jr nz, 1b
2:  xor a
    ld (NUM_OPTIONS), a
4:  call INKEY
    or a
    jr nz, 4b
    jp OP_GOTO

OP_TYPERATE:
    ld d, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld (PRT_INTERVAL), de
    jp EXEC_LOOP

OP_CLEAR:
    push hl
    call CLEAR_WIN
    pop hl
    jp EXEC_LOOP

OP_PAGEPAUSE:
    ld a, (hl)
    inc hl
    ld (WAIT_NEW_SCREEN), a
    jp EXEC_LOOP

OP_CHAR:
    ld a, (hl)
    inc hl
    push hl
    call PUT_VAR_CHAR
    pop hl
    jp EXEC_LOOP

OP_TAB:
    ld a, (hl)
    inc hl
    push hl
    ld bc, (POS_X)
    add a, c
    ld c, b
    ld b, a
    ld a, c
    push af
    push bc  
    call SET_CURSOR
    pop hl
    jp EXEC_LOOP


OP_SFX_D:
    ld e, (hl)
    inc hl
    push hl
    ld a, (BEEPFX_AVAILABLE)
    or a
    jr z, 1f

    ld a, BEEPFX_BANK
    call SET_RAM_BANK
    push af
    ld a, e
    ld (SFX_ID), a
    call BEEPFX
    pop af
    call SET_RAM_BANK

1:  pop hl
    jp EXEC_LOOP

OP_SFX_I:
    ld e, (hl)
    inc hl
    push hl
    ld a, (BEEPFX_AVAILABLE)
    or a
    jr z, 1f

    ld a, BEEPFX_BANK
    call SET_RAM_BANK
    push af
    ld d, HIGH FLAGS
    ld a, (de)
    ld (SFX_ID), a
    call BEEPFX
    pop af
    call SET_RAM_BANK

1:  pop hl
    jp EXEC_LOOP


OP_TRACK_D:
    ld a, (hl)
    inc hl
    di
    push hl
    call LOAD_MUSIC
    pop hl
    ei
    jp EXEC_LOOP

OP_TRACK_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    di
    push hl
    call LOAD_MUSIC
    pop hl
    ei
    jp EXEC_LOOP

OP_PLAY_D:
    ld a, (hl)
    inc hl
    push hl
    ld hl, VTR_STAT
    bit 1, (hl)
    jr nz, 3f
    ld a, 5
    jp SYS_ERROR
3:  or a
    jr nz, 2f
    res 2, (hl)
    jr 1f
2:  set 2, (hl)
1:  pop hl
    jp EXEC_LOOP

OP_PLAY_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    ld hl, VTR_STAT
    bit 1, (hl)
    jr nz, 3f
    ld a, 5
    jp SYS_ERROR
3:  or a
    jr nz, 2f
    res 2, (hl)
    jr 1f
2:  set 2, (hl)
1:  pop hl
    jp EXEC_LOOP

OP_LOOP_D:
    ld a, (hl)
    inc hl
    push hl
    ld hl, VTR_STAT
    bit 1, (hl)
    jr nz, 3f
    ld a, 5
    jp SYS_ERROR
3:  or a
    jr nz, 2f
    set 0, (hl)
    jr 1f
2:  res 0, (hl)
1:  pop hl
    jp EXEC_LOOP

OP_LOOP_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    ld hl, VTR_STAT
    bit 1, (hl)
    jr nz, 3f
    ld a, 5
    jp SYS_ERROR
3:  or a
    jr nz, 2f
    set 0, (hl)
    jr 1f
2:  res 0, (hl)
1:  pop hl
    jp EXEC_LOOP
;------------------------

    ALIGN 256
OPCODES:
    DW OP_END
    DW OP_TEXT
    DW OP_GOTO
    DW OP_GOSUB
    DW OP_RETURN
    DW OP_MARGINS
    DW OP_CENTER
    DW OP_AT
    DW OP_SET_D
    DW OP_IF_EQ_D
    DW OP_IF_NE_D
    DW OP_IF_LE_D
    DW OP_IF_ME_D
    DW OP_IF_LT_D
    DW OP_IF_MT_D
    DW OP_ADD_D
    DW OP_SUB_D
    DW OP_INK_D
    DW OP_PAPER_D
    DW OP_BORDER_D
    DW OP_PRINT_D
    DW OP_SET_I
    DW OP_IF_EQ_I
    DW OP_IF_NE_I
    DW OP_IF_LE_I
    DW OP_IF_ME_I
    DW OP_IF_LT_I
    DW OP_IF_MT_I
    DW OP_ADD_I
    DW OP_SUB_I
    DW OP_INK_I
    DW OP_PAPER_I
    DW OP_BORDER_I
    DW OP_PRINT_I
    DW OP_BRIGHT_D
    DW OP_FLASH_D
    DW OP_BRIGHT_I
    DW OP_FLASH_I
    DW OP_PICTURE_D
    DW OP_DISPLAY_D
    DW OP_PICTURE_I
    DW OP_DISPLAY_I
    DW OP_SET_RANDOM
    DW OP_AND_D
    DW OP_OR_D
    DW OP_AND_I
    DW OP_OR_I
    DW OP_NOT
    DW OP_OPTION
    DW OP_WAITKEY
    DW OP_INKEY
    DW OP_WAIT
    DW OP_PAUSE
    DW OP_CHOOSE
    DW OP_CHOOSE_W
    DW OP_TYPERATE
    DW OP_CLEAR
    DW OP_PAGEPAUSE
    DW OP_CHAR
    DW OP_TAB
    DW OP_SFX_D
    DW OP_SFX_I
    DW OP_TRACK_D
    DW OP_TRACK_I
    DW OP_PLAY_D
    DW OP_PLAY_I
    DW OP_LOOP_D
    DW OP_LOOP_I
