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

OP_END EQU END_PROGRAM

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
    jr z, .same_CHUNK
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
    ld a, (CHUNK)
    ld (ix-1), l
    ld (ix-2), h
    ld (ix-3), a
    ld de, 65536-3    ; ix-3
    add ix, de
    pop hl
    jp OP_GOTO

OP_RETURN:
    ld c, (ix+0)
    ld h, (ix+1)
    ld l, (ix+2)
    ld de, 3
    add ix, de
    ld a, (CHUNK)
    cp c       ; If the CHUNK is the same...
    jr z, .same_CHUNK
    push hl
    ld a, c
    call LOAD_CHUNK
    pop hl
.same_CHUNK:
    jp EXEC_LOOP

;-------------------------------------

    MACRO POP_INT_STACK
    ld a, (ix+0)
    inc ix
    ENDM

    MACRO PUSH_INT_STACK
    dec ix
    ld (ix+0), a
    ENDM

OP_IF_GOTO:
    POP_INT_STACK
    or a
    jp nz, OP_GOTO
    ld de, 3
    add hl, de
    jp EXEC_LOOP

OP_IF_N_GOTO:
    POP_INT_STACK
    or a
    jp z, OP_GOTO
    ld de, 3
    add hl, de
    jp EXEC_LOOP
;-------------------------------------------------------
    IFNDEF UNUSED_OP_POP_SET:
OP_POP_SET:
    ; [param] <- Stack
    POP_INT_STACK
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_SET_DI
OP_POP_SET_DI:
    ; [[param]] <- Stack
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ex de, hl
    POP_INT_STACK
    ld l, (hl)
    ld (hl), a
    ex de, hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_D
OP_PUSH_D:
    ; Stack <- Param
    ld a, (hl)
    inc hl
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_I
OP_PUSH_I:
    ; Stack <- [Param]
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_DI
OP_PUSH_DI:
    ; Stack <- [[Param]]
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    ld e, a
    ld a, (de)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_PUSH_I
OP_POP_PUSH_I:
    ; Stack <- [Stack]
    ld e, (ix+0)
    ld d, HIGH FLAGS
    ld a, (de)
    ld (ix+0), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SET_D
OP_SET_D:
    ;[Param1] <- Param2
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (hl)
    inc hl
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SET_I
OP_SET_I:
    ;[Param1] <- [Param2]
    ld c, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    ld e, c
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SET_DI
OP_SET_DI:
    ;[Param1] <- [[Param2]]
    ld c, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    ld e, a
    ld a, (de)
    ld e, c
    ld (de), a
    jp EXEC_LOOP
    ENDIF
;-------------------------------------
    MACRO OP_2PARAM_GET_STACK
    ld c, (ix+0)
    ld a, (ix+1)
    ENDM
    
    MACRO OP_2PARAM_STORE_STACK
    inc ix
    ld (ix+0), a
    jp EXEC_LOOP
    ENDM

    IFNDEF UNUSED_OP_NOT
OP_NOT:
    ld a, (ix+0)
    xor 1
    ld (ix+0), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_NOT_B
OP_NOT_B:
    ld a, (ix+0)
    cpl
    ld (ix+0), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_AND
OP_AND:
    OP_2PARAM_GET_STACK
    and c
    OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_OR
OP_OR:
    OP_2PARAM_GET_STACK
    or c
    OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_EQ
OP_CP_EQ:
    OP_2PARAM_GET_STACK
    cp c
    jr z, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_NE
OP_CP_NE:
    OP_2PARAM_GET_STACK
    cp c
    jr nz, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_LT
OP_CP_LT:                ; p1 < p2
    OP_2PARAM_GET_STACK  ; p2 = C, p1 = A
    cp c                 ; p1 - p2 -> p1 < p2
    jr c, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_ME
OP_CP_ME:               ; p1 >= p2
    OP_2PARAM_GET_STACK ; p2 = C, p1 = A
    cp c                ; p1 - p2
    jr nc, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_MT
OP_CP_MT:                ; p1 > p2
    OP_2PARAM_GET_STACK  ; p2 = C, p1 = A
    ld b, a
    ld a, c              ; p2 = A, p1 = B
    cp b                 ; p2 - p1 -> p2 < p1
    jr c, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_CP_LE
OP_CP_LE:                ; p1 <= p2
    OP_2PARAM_GET_STACK  ; p2 = C, p1 = A
    ld b, a
    ld a, c              ; p2 = A, p1 = B
    cp b                 ; p2 - p1 -> p2 < p1
    jr nc, 1f
    xor a
    jr 2f
1:  ld a, 1
2:  OP_2PARAM_STORE_STACK
    ENDIF

;-------------------------------------------------------

    IFNDEF UNUSED_OP_ADD
OP_ADD:
    OP_2PARAM_GET_STACK
    add a, c
    jr nc, 1f
    ld a, $FF
1:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_SUB
OP_SUB:
    OP_2PARAM_GET_STACK
    sub c
    jr nc, 1f
    xor a
1:  OP_2PARAM_STORE_STACK 
    ENDIF

    IFNDEF UNUSED_OP_INKEY
OP_INKEY:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (hl)
    inc hl
    call INKEY_SELECT_WAIT_MODE    
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_INKEY
OP_PUSH_INKEY:
    ld a, (hl)
    inc hl
    call INKEY_SELECT_WAIT_MODE 
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_RANDOM
OP_RANDOM:
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
2:  pop hl
    ld c, a
    ld b, (hl)
    inc hl
    ld a, b
    or a
    ld a, c
    jr nz, 3f
    ld a, c
4:  ld (de), a   
    jp EXEC_LOOP
3:  cp b           ; a - b
    jr c, 4b
    sub b
    jr 3b
    ENDIF

    IFNDEF UNUSED_OP_PUSH_RANDOM
OP_PUSH_RANDOM:
    push hl
    call RANDOM
    ld a, r
    rrca
    jr c, 1f
    ld a, l
    jr 2f
1:  ld a, h
2:  pop hl
    ld c, a
    ld b, (hl)
    inc hl
    ld a, b
    or a
    ld a, c
    jr nz, 3f
    ld a, c
4:  ;Stack
    PUSH_INT_STACK
    jp EXEC_LOOP
3:  cp b           ; a - b
    jr c, 4b
    sub b
    jr 3b
    ENDIF

    IFNDEF UNUSED_OP_RANDOMIZE
OP_RANDOMIZE:
    push hl
    call SET_RND_SEED
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_AT
OP_POP_AT:
    ;Get Rows
    POP_INT_STACK   
    cp 24
    jr c, 1f
    ld a, 23
1:  ld b, a
    ;Get Cols
    POP_INT_STACK
    cp 32
    jr c, 2f
    ld a, 31
2:  push hl
    push bc         ;Rows on B
    push af         ;Cols on A
    call SET_CURSOR
    pop hl
    jp EXEC_LOOP
    ENDIF
;============================================

    IFNDEF UNUSED_OP_INK_D
OP_INK_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp INK
    ENDIF

    IFNDEF UNUSED_OP_PAPER_D
OP_PAPER_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp PAPER
    ENDIF

    IFNDEF UNUSED_OP_BRIGHT_D
OP_BRIGHT_D:
    ld a, (hl)
    inc hl
    push hl
    call BRIGHT
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_FLASH_D
OP_FLASH_D:
    ld a, (hl)
    inc hl
    push hl
    call FLASH
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_BORDER_D
OP_BORDER_D:
    ld de, EXEC_LOOP
    push de
    ld a, (hl)
    inc hl
    jp BORDER
    ENDIF

    IFNDEF UNUSED_OP_PRINT_D
OP_PRINT_D:
    ld a, (hl)
    inc hl
    push hl
    call PRINT_A_BYTE
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_INK_I
OP_INK_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp INK
    ENDIF

    IFNDEF UNUSED_OP_PAPER_I
OP_PAPER_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp PAPER
    ENDIF

    IFNDEF UNUSED_OP_BRIGHT_I
OP_BRIGHT_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call BRIGHT
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_FLASH_I
OP_FLASH_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call FLASH
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_BORDER_I
OP_BORDER_I:
    ld de, EXEC_LOOP
    push de
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    jp BORDER
    ENDIF

    IFNDEF UNUSED_OP_PRINT_I
OP_PRINT_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call PRINT_A_BYTE
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_INK
OP_POP_INK:
    ld de, EXEC_LOOP
    push de
    POP_INT_STACK
    jp INK
    ENDIF

    IFNDEF UNUSED_OP_POP_PAPER
OP_POP_PAPER:
    ld de, EXEC_LOOP
    push de
    POP_INT_STACK
    jp PAPER
    ENDIF

    IFNDEF UNUSED_OP_POP_BRIGHT
OP_POP_BRIGHT:
    POP_INT_STACK
    push hl
    call BRIGHT
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_FLASH
OP_POP_FLASH:
    POP_INT_STACK
    push hl
    call FLASH
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_BORDER
OP_POP_BORDER:
    ld de, EXEC_LOOP
    push de
    POP_INT_STACK
    jp BORDER
    ENDIF

    IFNDEF UNUSED_OP_POP_PRINT
OP_POP_PRINT:
    POP_INT_STACK
    push hl
    call PRINT_A_BYTE
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_MARGINS
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
    call SET_BACKSPACE_MARGINS_WIDTH
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_AT
OP_AT:
    ld b, (hl)
    inc hl
    ld a, (hl)
    inc hl
    push hl
    push af         ;Rows on A
    push bc         ;Cols on B
    call SET_CURSOR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CENTER
OP_CENTER:
    ld de, EXEC_LOOP
    push de
    jp CENTER
    ENDIF

    IFNDEF UNUSED_OP_PICTURE_D
OP_PICTURE_D:
    ld a, (hl)
    inc hl
    push hl
    call IMG_LOAD
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_DISPLAY_D
OP_DISPLAY_D:
    ld a, (hl)
    inc hl
    or a
    jp z, EXEC_LOOP
    push hl
    call COPY_SCREEN
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PICTURE_I
OP_PICTURE_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    push hl
    call IMG_LOAD
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_DISPLAY_I
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
    ENDIF

    IFNDEF UNUSED_OP_POP_PICTURE
OP_POP_PICTURE:
    POP_INT_STACK
    push hl
    call IMG_LOAD
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_DISPLAY
OP_POP_DISPLAY:
    POP_INT_STACK
    or a
    jp z, EXEC_LOOP
    push hl
    call COPY_SCREEN
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_WAIT
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
    ENDIF

    IFNDEF UNUSED_OP_OPTION
OP_OPTION:
    ld a, (NUM_OPTIONS)
    cp MAXIMUM_OPTIONS    ;test if number of options is MAX4
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
    sla a
    sla a
    sla a
    ld l, a
    ld h, HIGH OPTIONS_TABLE
    ld (hl), e             ;Store screen pos
    inc hl
    ld (hl), d
    inc hl
    ex de, hl              ;Move option table address to DE
    pop hl
    ldi                    ;Copy Address to address table
    ldi
    ldi
    ldi
    pop af
    inc a
    ld (NUM_OPTIONS), a   ;Increment options
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_WAITKEY
OP_WAITKEY:
    push hl                          ;Save pointer
    call ADJUST_CHAR_POS_NO_ADVANCE  ;Advance to the best position for printing the choice
    push hl 
    push hl                     ;d = POS_Y, e = POS_X
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
    ENDIF

    IFNDEF UNUSED_OP_PAUSE
OP_PAUSE:
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl                     ;Save pointer
    ld (DOWN_COUNTER), de
    call ADJUST_CHAR_POS_NO_ADVANCE    ;Advance to the best position for printing the choice
    push hl 
    push hl                     ;d = POS_Y, e = POS_X
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
    ENDIF

    IFNDEF UNUSED_OP_CHOOSE
OP_CHOOSE:
    ld (.self_a), hl
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
    cp 'o'
    jp z, .left
    cp 'p'
    jp z, .right
    cp 'q'
    jp z, .up
    cp 'a'
    jp z, .down
    cp ' '
    jp z, .selected
    cp 13
    jp z, .selected
    call ANIMATE_OPTION_BULLET
    jr .inkey
.left:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .inkey
    jr 3b
.right:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY
    or a
    jp z, .inkey
    jr 4b
.up:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY
    or a
    jp z, .inkey
    jr 2b
.down:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .inkey
    jr 3b
.selected:
    ld a, (SELECTED_OPTION)
    sla a
    sla a
    sla a
    add a, 2
    ld l, a
    ld h, HIGH OPTIONS_TABLE
    xor a
    ld (NUM_OPTIONS), a
5:  call INKEY
    or a
    jr nz, 5b
    ld a, (hl)
    inc hl
    or a
    jp z, OP_GOTO
    push hl
.self_a+1:
    ld hl, 0-0
    ld a, (CHUNK)
    ld (ix-1), l
    ld (ix-2), h
    ld (ix-3), a
    ld de, 65536-3    ; ix-3
    add ix, de
    pop hl
    jp OP_GOTO
    ENDIF

;----------------------------------------------

    IFNDEF UNUSED_OP_CHOOSE_W
OP_CHOOSE_W:

    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl

    push de            ;Save timeout

    ld de, TIMEOUT_OPTION
    ldi
    ldi
    ldi
    ldi
 
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
    cp 'o'
    jp z, .left
    cp 'p'
    jp z, .right
    cp 'q'
    jp z, .up
    cp 'a'
    jp z, .down
    cp ' '
    jp z, .selected
    cp 13
    jp z, .selected
    ld bc, (DOWN_COUNTER)
    ld a, c
    or b
    jp z, .count_elapsed
    call ANIMATE_OPTION_BULLET
    ;jr 1b
    jr .inkey
.left:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .inkey
    jr 3b
.right:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY
    or a
    jp z, .inkey
    jr 4b
.up:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY
    or a
    jp z, .inkey
    jr 2b
.down:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .inkey
    jr 3b
.count_elapsed:
    ld hl, TIMEOUT_OPTION
    jr 3f
.selected:
    ld a, (SELECTED_OPTION) 
    sla a
    sla a
    sla a
    add a, 2
    ld l, a
    ld h, HIGH OPTIONS_TABLE
3:  ld c, (hl)               ;C= if is GOSUB
    inc hl
    xor a
    ld (NUM_OPTIONS), a
4:  call INKEY
    or a
    jr nz, 4b
    ld a, c
    or a
    jp z, OP_GOTO
    jp OP_GOSUB
    ENDIF

;----------------------------------------------

    IFNDEF UNUSED_OP_CHOOSE_CH
OP_CHOOSE_CH:
    ld a, (RETURN_FROM_CHOOSE_CH)
    or a
    jr nz, .no_store_ret_addr
    inc a                           ;Sets a to 1
    ld de, RETURN_FROM_CHOOSE_CH    
    ld (de), a                      ;Store 1 at RETURN_FROM_CHOOSE_CH (when we return here, skip this)
    inc de
    dec hl                          ;Returns to previous position
    ex de, hl
    ld a, (CHUNK)
    ld (hl), a
    inc hl
    ld (hl), e
    inc hl
    ld (hl), d
    inc hl
    ex de, hl
    inc hl                         ;restore IP to current position
    ;read destination address for change
    ldi
    ldi
    ldi
    xor a
    ld (SELECTED_OPTION), a        ;Resets selected option
    ld (.self_a), hl
    jp .on_change_gosub 
.no_store_ret_addr:
    ld a, (NUM_OPTIONS)
    or a
    jp nz, .options       ; No options available
    ld a, 3
    jp SYS_ERROR
.options:
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
.inkey:
    call INKEY
    cp 'o'
    jp z, .left
    cp 'p'
    jp z, .right
    cp 'q'
    jp z, .up
    cp 'a'
    jp z, .down
    cp ' '
    jp z, .selected
    cp 13
    jp z, .selected
    call ANIMATE_OPTION_BULLET
    jr .inkey
.left:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .on_change_gosub
    jr 3b
.right:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_ROW_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY
    or a
    jp z, .on_change_gosub
    jr 4b
.up:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY
    or a
    jp z, .on_change_gosub
    jr 2b
.down:
    ld a, (NUM_OPTIONS)
    ld c, a
    dec c
    ld a, (SELECTED_OPTION)
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (NUM_OPTIONS)
    ld c, a
    ld a, (INCR_COL_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY
    or a
    jp z, .on_change_gosub
    jr 3b
.selected:
    ld a, (SELECTED_OPTION)
    sla a
    sla a
    sla a
    add a, 2                ;Skips to jump address
    ld l, a
    ld h, HIGH OPTIONS_TABLE
    xor a
    ld (NUM_OPTIONS), a
    ld (RETURN_FROM_CHOOSE_CH), a
5:  call INKEY
    or a
    jr nz, 5b
    ld a, (hl)
    inc hl
    or a
    jp z, OP_GOTO
    push hl
.self_a+1:
    ld hl, 0-0
    ld a, (CHUNK)
    ld (ix-1), l
    ld (ix-2), h
    ld (ix-3), a
    ld de, 65536-3    ; ix-3
    add ix, de
    pop hl
    jp OP_GOTO
.on_change_gosub:
    ld hl, CHOOSE_CH_RET_ADDRESS
    ld e, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld (ix-1), e
    ld (ix-2), d
    ld (ix-3), a
    ld de, 65536-3    ; ix-3
    add ix, de
    jp OP_GOTO
    ENDIF

    IFNDEF OP_CLEAR_OPTIONS
OP_CLEAR_OPTIONS:
    xor a
    ld (NUM_OPTIONS), a          ;Clear options.
    jp EXEC_LOOP
    ENDIF

;----------------------------------------------------------

    IFNDEF UNUSED_OP_PUSH_OPTION_ST
OP_PUSH_OPTION_ST:
    ld de, NUM_OPTIONS
    ld a, (hl)
    inc hl
    or a
    jr z, .is_zero
    ld b, a
1:  inc de
    djnz 1b
.is_zero:
    ld a, (de)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

;----------------------------------------------------------

    IFNDEF UNUSED_OP_TYPERATE
OP_TYPERATE:
    ld d, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld (PRT_INTERVAL), de
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CLEAR
OP_CLEAR:
    push hl
    call CLEAR_WIN
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PAGEPAUSE
OP_PAGEPAUSE:
    ld a, (hl)
    inc hl
    ld (WAIT_NEW_SCREEN), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CHAR_D
OP_CHAR_D:
    ld a, (hl)
    inc hl
    push hl
    call PUT_VAR_CHAR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CHAR_I
OP_CHAR_I:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (de)
    push hl
    call PUT_VAR_CHAR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_CHAR
OP_POP_CHAR:
    POP_INT_STACK
    push hl
    call PUT_VAR_CHAR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_TAB
    IFDEF UNUSED_OP_REPCHAR
    UNDEFINE UNUSED_OP_REPCHAR
    ENDIF
OP_TAB:
    ld a, 32 
    jr OP_TAB2
    ENDIF

    IFNDEF UNUSED_OP_REPCHAR
OP_REPCHAR:
    ld a, (hl)
    inc hl
OP_TAB2:
    ld b, (hl)
    inc hl
    push hl
1:  push bc
    push af
    call PUT_VAR_CHAR
    pop af
    pop bc
    djnz 1b
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_NEWLINE
OP_NEWLINE:
    ld b, (hl)
    inc hl
    push hl
1:  push bc
    call CRLF
    pop bc
    djnz 1b
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_BACKSPACE
OP_BACKSPACE:
    ld b, (hl)
    inc hl
    push hl
1:  push bc
    call BACKSPACE
    pop bc
    djnz 1b
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SFX_D
OP_SFX_D:
    ld e, (hl)
    inc hl
    push hl
    ld a, BEEPFX_AVAILABLE
    or a
    jr z, 1f

    ld a, e
    ld (SFX_ID), a
    call BEEPFX

1:  pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SFX_I
OP_SFX_I:
    ld e, (hl)
    inc hl
    push hl
    ld a, BEEPFX_AVAILABLE
    or a
    jr z, 1f

    ld d, HIGH FLAGS
    ld a, (de)
    ld (SFX_ID), a
    call BEEPFX

1:  pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_SFX
OP_POP_SFX:
    push hl
    POP_INT_STACK
    ld a, BEEPFX_AVAILABLE
    or a
    jr z, 1f
    ld (SFX_ID), a
    call BEEPFX
1:  pop hl
    jp EXEC_LOOP
    ENDIF
    

    IFNDEF UNUSED_OP_TRACK_D
OP_TRACK_D:
    ld a, (hl)
    inc hl
    IFDEF USE_VORTEX
    di
    push hl
    call LOAD_MUSIC
    pop hl
    ei
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_TRACK_I
OP_TRACK_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    IFDEF USE_VORTEX
    di
    push hl
    call LOAD_MUSIC
    pop hl
    ei
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_TRACK
OP_POP_TRACK:
    POP_INT_STACK
    IFDEF USE_VORTEX
    di
    push hl
    call LOAD_MUSIC
    pop hl
    ei
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PLAY_D
OP_PLAY_D:
    ld a, (hl)
    inc hl
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PLAY_I
OP_PLAY_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_PLAY
OP_POP_PLAY:
    POP_INT_STACK
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_LOOP_D
OP_LOOP_D:
    ld a, (hl)
    inc hl
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_LOOP_I
OP_LOOP_I:
    ld e, (hl)
    inc hl
    ld d, HIGH FLAGS
    ld a, (de)
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_LOOP
OP_POP_LOOP:
    POP_INT_STACK
    IFDEF USE_VORTEX
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
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SET_XPOS
OP_SET_XPOS:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (POS_X)
    srl a
    srl a
    srl a
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SET_YPOS
OP_SET_YPOS:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    ld a, (POS_Y)
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_XPOS
OP_PUSH_XPOS:
    ld a, (POS_X)
    srl a
    srl a
    srl a
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_YPOS
OP_PUSH_YPOS:
    ld a, (POS_Y)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_MIN
OP_MIN:
    OP_2PARAM_GET_STACK  ; A= Param1, C=Param2
    cp c                 ; a-c   
    jr nc, 1f             ; A >= C
    ld a, c
    OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_MAX
OP_MAX:
    OP_2PARAM_GET_STACK  ; A= Param1, C=Param2
    cp c                 ; a-c
    jr c, 1f             ; A < C 
    ld a, c
1:  OP_2PARAM_STORE_STACK
    ENDIF

    IFNDEF UNUSED_OP_PUSH_IS_DISK
OP_PUSH_IS_DISK:
    ld a, IS_PLUS3
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF
;-------------------------------------------------------

    IFNDEF UNUSED_OP_POP_MENUCONFIG
OP_POP_MENUCONFIG:
    ld b, (ix+0)
    ld c, (ix+1)
    inc ix
    inc ix
    ld (INCR_ROW_OPTION), bc
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_MENUCONFIG
OP_MENUCONFIG:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld (INCR_ROW_OPTION), bc
    jp EXEC_LOOP
    ENDIF

;-------------------------------------------------------

    IFNDEF UNUSED_OP_POP_ALL_BLIT   
OP_POP_ALL_BLIT:
    push hl
    ld b, (ix+0)               ; GET Y
    inc ix
    ld c, (ix+0)               ; GET X
    inc ix
    push bc
    ld (CPY_SCR_BLK_X_D), bc
    ld d, (ix+0)               ; GET H
    inc ix
    ld e, (ix+0)               ; GET W
    inc ix
    ld b, (ix+0)               ; GET YO
    inc ix
    ld c, (ix+0)               ; GET XO
    inc ix
    call POS_ADJUST
    call RECT_ADJUST
    ld (CPY_SCR_BLK_X), bc
    ld (CPY_SCR_BLK_W), de
    pop bc
    jr 2f
    IFNDEF BLIT_USED
    DEFINE BLIT_USED
    ENDIF
    ENDIF

    IFNDEF UNUSED_OP_POP_BLIT   
OP_POP_BLIT:
    ld de, CPY_SCR_BLK_X
    ldi
    ldi
    ldi
    ldi
    ld b, (ix+0)               ; GET Y
    inc ix
    ld c, (ix+0)               ; GET X
    inc ix
    ld (CPY_SCR_BLK_X_D), bc
    jr 1f
    IFNDEF BLIT_USED
    DEFINE BLIT_USED
    ENDIF
    ENDIF

    IFNDEF UNUSED_OP_BLIT
OP_BLIT:
    ld de, CPY_SCR_BLK_X
    ldi
    ldi
    ldi
    ldi 
    ldi
    ldi
    ld bc, (CPY_SCR_BLK_X_D)
    IFNDEF BLIT_USED
    DEFINE BLIT_USED
    ENDIF
    ENDIF

    IFDEF BLIT_USED 
1:  ld de, (CPY_SCR_BLK_W)
    push hl
2:  call POS_CHECK
    jp c, .endBlit
    call RECT_ADJUST
    ld a, d
    or a
    jp z, .endBlit
    ld a, e
    or a
    jp z, .endBlit
4:  ld (CPY_SCR_BLK_W), de
    ld (CPY_SCR_BLK_X_D), bc
    
.getPxlAddr:
    ;ld bc,(CPY_SCR_BLK_X_D)
    ld a, b                 
    and %00011000
    add a, %01000000         ; Sumamos $40 (bits superiores = 010)
    ld d, a
    ld a, b
    and %00000111
    rrca
    rrca
    rrca
    add a, c
    ld e, a

    ld bc,(CPY_SCR_BLK_X)
    ld a, b
    and %00011111
    add a, HIGH SCREEN_BUFFER_PXL
    ld h, a
    ld a, c
    and %00011111
    ld l, a

;Copy pixels
    ld bc,(CPY_SCR_BLK_W)
.loopRowsPxl:
    push bc
    push de
    ld b, 0
    ld a, c

    REPT 7
    push hl
    push de
    ld c, a
    ex af, af'
    ldir
    pop de
    pop hl
    inc d
    ld a, l
    add a, 32 
    ld l, a
    ex af, af'
    ENDR

    push hl     ;Last line
    ld c, a
    ldir
    pop hl
    ld a, l
    and %00011111
    ld l, a
    inc h
    pop de
    ld a, e     ; A = lower part of the address. RRRC CCCC.
    add a, $20  ; Add one line (RRRC CCCC + 0010 0000).
    ld e, a     ; L = A.
    jr nc,1f    ; If there is no carry, the row follows between 0 
                ; and 7, it exits.  ; There is carry-over, the third of the screen has to be changed.
    ld a, d     ; A = upper part of memory address. 010T TSSS.
    add a, $08  ; Add one third (010T TSSS + 0000 1000).
    ld d, a     ; H = A.  ret

1:  pop bc
    djnz .loopRowsPxl

.getAttAddr:
    ld bc,(CPY_SCR_BLK_X)
    ld a, b
    rrca
    rrca
    rrca
    and %00000011
    add a, HIGH SCREEN_BUFFER_ATT
    ld h, a
    ld a, b
    and %00000111
    rrca
    rrca
    rrca
    add a, c
    ld l, a

    ld bc,(CPY_SCR_BLK_X_D)
    ld a, b
    rrca
    rrca
    rrca
    and %00000011
    add a, %01011000         ; Ponemos los bits 15-10 como 010110b
    ld d, a
    ld a, b
    and %00000111
    rrca
    rrca
    rrca
    add a, c
    ld e, a

;Copy attr
    ld bc,(CPY_SCR_BLK_W)
.loopRowsAtt:
    push bc
    ld b, 0
    push de
    push hl
    ldir
    pop hl
    pop de
    ld a, $20
    add a, l
    jr nc, 1f
    inc h
1:  ld l, a
    ld a, $20
    add a, e
    jr nc, 2f
    inc d
2:  ld e, a
    pop bc
    djnz .loopRowsAtt

.endBlit:
    pop hl
    jp EXEC_LOOP

CPY_SCR_BLK_X     EQU TMP_AREA + 0
CPY_SCR_BLK_Y     EQU TMP_AREA + 1
CPY_SCR_BLK_W     EQU TMP_AREA + 2
CPY_SCR_BLK_H     EQU TMP_AREA + 3
CPY_SCR_BLK_X_D   EQU TMP_AREA + 4
CPY_SCR_BLK_Y_D   EQU TMP_AREA + 5

    UNDEFINE BLIT_USED
    ENDIF
;---------------

    IFNDEF UNUSED_OP_FADEOUT

    IFNDEF GET_ATTR_ADDR_USED
    DEFINE GET_ATTR_ADDR_USED
    ENDIF

FADEOUT_ITERATIONS              EQU 8

OP_FADEOUT:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl
    ld (FADEOUT_W), de
    call GET_ATTR_ADDR
    ld (FADE_OUT_ADDRESS), hl
    ld a, FADEOUT_ITERATIONS ; Num iterations
    ld (FADE_OUT_ITERARIONS), a
1:  halt
    ld a, (FADE_OUT_ITERARIONS)
    or a
    jr nz, 1b
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_FILLATTR:
    IFNDEF GET_ATTR_ADDR_USED
    DEFINE GET_ATTR_ADDR_USED
    ENDIF
    IFNDEF FILLATTR_USED
    DEFINE FILLATTR_USED
    ENDIF
OP_POP_FILLATTR:
    push hl
    ;Get Height
    ld h, (ix+0)
    ;Get Width
    ld l, (ix+1)
    ;Get Rows
    ld b, (ix+2)
    ;Get Cols
    ld c, (ix+3)
    ;Get Attr
    ld a, (ix+4)
    ld de, 5
    add ix, de
    ex de, hl
    jr FILLATTR
    ENDIF

    IFNDEF UNUSED_OP_FILLATTR
    IFNDEF GET_ATTR_ADDR_USED
    DEFINE GET_ATTR_ADDR_USED
    ENDIF
    IFNDEF FILLATTR_USED
    DEFINE FILLATTR_USED
    ENDIF
OP_FILLATTR:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld a, (hl)
    inc hl
    push hl
    ENDIF
    
    IFDEF FILLATTR_USED
    ; bc: y - x
    ; de: height - width
FILLATTR:
    ex af, af'
    call POS_ADJUST
    call RECT_ADJUST
    call GET_ATTR_ADDR
    ex af, af'

    ld c, a
2:  ld b, e        ; width -> B
    push hl
1:  ld (hl), c     ; Fill color
    inc hl
    djnz 1b
    pop hl         ; Restore hl
    ld a, 32       ; next attr line
    add a, l
    jr nc, 3f
    inc h
3:  ld l, a
    dec d
    jr nz, 2b

    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUTATTR
    IFNDEF PUT_ATTR_USED
    DEFINE PUT_ATTR_USED
    ENDIF
OP_PUTATTR:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl
    call PUT_ATTR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_PUTATTR
    IFNDEF PUT_ATTR_USED
    DEFINE PUT_ATTR_USED
    ENDIF
OP_POP_PUTATTR:
    ;Get Rows
    ld b, (ix+0)
    ;Get Cols
    ld c, (ix+1)
    inc ix
    inc ix
    call POS_ADJUST
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl
    call PUT_ATTR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_ALL_PUTATTR
    IFNDEF PUT_ATTR_USED
    DEFINE PUT_ATTR_USED
    ENDIF
OP_POP_ALL_PUTATTR:
    ;Get Rows
    ld b, (ix+0)
    ;Get Cols
    ld c, (ix+1)
    call POS_ADJUST
    ;Get mask
    ld e, (ix+2)
    ;Get Attr
    ld d, (ix+3)
    push hl
    call PUT_ATTR
    ld de, 4
    add ix, de
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFDEF PUT_ATTR_USED
    IFNDEF GET_ATTR_ADDR_USED
    DEFINE GET_ATTR_ADDR_USED
    ENDIF
PUT_ATTR:
    call GET_ATTR_ADDR
    ld a, d
    and e
    ld d, a
    ld a, e
    cpl
    and (hl)        ;AND with mask
    or d              ;OR with new values
    ld (hl), a        ;Store value again
    ret
    ENDIF

    IFNDEF UNUSED_OP_PUSH_GETATTR
    IFNDEF GET_ATTR_ADDR_USED
    DEFINE GET_ATTR_ADDR_USED
    ENDIF
OP_PUSH_GETATTR:
    ;Get Rows
    ld b, (ix+0)
    inc ix
    ;Get Cols
    ld c, (ix+0)
    inc ix
    call POS_ADJUST
    push hl
    call GET_ATTR_ADDR
    ld a, (hl)        ;Get attribute
    PUSH_INT_STACK
    pop hl
    jp EXEC_LOOP
    ENDIF
  
    IFDEF GET_ATTR_ADDR_USED
GET_ATTR_ADDR:
    ; bc: y - x
    ld a, b
    rrca
    rrca
    rrca
    and %00000011
    add a, %01011000
    ld h, a
    ld a, b
    and %00000111
    rrca
    rrca
    rrca
    add a, c
    ld l, a        ; HL -> Attr coordinates
    ret
    UNDEFINE GET_ATTR_ADDR_USED
    ENDIF

;---------------
    IFNDEF UNUSED_OP_RAMLOAD
OP_RAMLOAD:
    ld b, (hl)
    inc hl
    ld c, (hl)
    inc hl
    push hl
    call CHK_RAMLOAD_PARAMETERS
    call RAMLOAD
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_RAMSAVE
OP_RAMSAVE:
    ld b, (hl)
    inc hl
    ld c, (hl)
    inc hl
    push hl
    call CHK_RAMLOAD_PARAMETERS
    call RAMSAVE
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_SLOT_LOAD
OP_POP_SLOT_LOAD:
    POP_INT_STACK
    ld (CURR_SAVE_SLOT), a
    call DO_LOAD
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_SLOT_SAVE
OP_POP_SLOT_SAVE:
    POP_INT_STACK
    ld (CURR_SAVE_SLOT), a
    ld b, (hl)
    inc hl
    ld c, (hl)
    inc hl
    call CHK_RAMLOAD_PARAMETERS
    call DO_SAVE
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_SAVE_RESULT
OP_PUSH_SAVE_RESULT:
    ld a, (LAST_SAVE_RESULT)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

;-------------------------------------------------------
    IFNDEF UNUSED_OP_SHIFT_R
OP_SHIFT_R:
    ; p2 = A, p1 = C
    ld a, (ix+0)
    ld c, (ix+1)
    or a
    jr z, 1f
    ld b, a
2:  srl c
    djnz 2b
1:  inc ix
    ld (ix+0), c
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SHIFT_L
OP_SHIFT_L:
    ; p2 = A, p1 = C
    ld a, (ix+0)
    ld c, (ix+1)
    or a
    jr z, 1f
    ld b, a
2:  sla c
    djnz 2b
1:  inc ix
    ld (ix+0), c
    jp EXEC_LOOP
    ENDIF

;-------------------------------------------------------

/*
    IFNDEF UNUSED_OP_EXTERN
OP_EXTERN:
    ld b, (hl)
    inc hl
    ld a, (hl)
    inc hl
    ld (.jump_addr+0), a
    ld a, (hl)
    inc hl
    ld (.jump_addr+1), a
    push hl
    ld a, (CHUNK)
    push af
    cp b       ; If the CHUNK is the same...
    jr z, 1f
    ld a, b
    push hl
    call LOAD_CHUNK
    pop hl
1:  ld de, FLAGS
.jump_addr+1:
    call 0-0
    pop bc
    ld a, (CHUNK)
    cp b       ; If the CHUNK is the same...
    jr z, 2f
    ld a, b
    call LOAD_CHUNK
2:  pop hl
    jp EXEC_LOOP
    ENDIF
*/
;------------------------
ERROR_NOP:
    ld a, 6
    jp SYS_ERROR


    ALIGN 256
OPCODES:
    DW OP_END
    DW OP_TEXT
    DW OP_GOTO
    DW OP_GOSUB
    DW OP_RETURN
    IFNDEF UNUSED_OP_MARGINS
    DW OP_MARGINS
    ENDIF
    IFDEF UNUSED_OP_MARGINS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CENTER
    DW OP_CENTER
    ENDIF
    IFDEF UNUSED_OP_CENTER
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_AT
    DW OP_AT
    ENDIF
    IFDEF UNUSED_OP_AT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_D
    DW OP_SET_D
    ENDIF
    IFDEF UNUSED_OP_SET_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_I
    DW OP_SET_I
    ENDIF
    IFDEF UNUSED_OP_SET_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_SET
    DW OP_POP_SET
    ENDIF
    IFDEF UNUSED_OP_POP_SET
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_D
    DW OP_PUSH_D
    ENDIF
    IFDEF UNUSED_OP_PUSH_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_I
    DW OP_PUSH_I
    ENDIF
    IFDEF UNUSED_OP_PUSH_I
    DW ERROR_NOP
    ENDIF
    DW OP_IF_GOTO
    DW OP_IF_N_GOTO
    IFNDEF UNUSED_OP_PUSH_INKEY
    DW OP_PUSH_INKEY
    ENDIF
    IFDEF UNUSED_OP_PUSH_INKEY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_RANDOM
    DW OP_PUSH_RANDOM
    ENDIF
    IFDEF UNUSED_OP_PUSH_RANDOM
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_NOT
    DW OP_NOT
    ENDIF
    IFDEF UNUSED_OP_NOT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_NOT_B
    DW OP_NOT_B
    ENDIF
    IFDEF UNUSED_OP_NOT_B
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_AND
    DW OP_AND
    ENDIF
    IFDEF UNUSED_OP_AND
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_OR
    DW OP_OR
    ENDIF
    IFDEF UNUSED_OP_OR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_ADD
    DW OP_ADD
    ENDIF
    IFDEF UNUSED_OP_ADD
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SUB
    DW OP_SUB
    ENDIF
    IFDEF UNUSED_OP_SUB
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_EQ
    DW OP_CP_EQ
    ENDIF
    IFDEF UNUSED_OP_CP_EQ
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_NE
    DW OP_CP_NE
    ENDIF
    IFDEF UNUSED_OP_CP_NE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_LE
    DW OP_CP_LE
    ENDIF
    IFDEF UNUSED_OP_CP_LE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_ME
    DW OP_CP_ME
    ENDIF
    IFDEF UNUSED_OP_CP_ME
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_LT
    DW OP_CP_LT
    ENDIF
    IFDEF UNUSED_OP_CP_LT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CP_MT
    DW OP_CP_MT
    ENDIF
    IFDEF UNUSED_OP_CP_MT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_INK_D
    DW OP_INK_D
    ENDIF
    IFDEF UNUSED_OP_INK_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PAPER_D
    DW OP_PAPER_D
    ENDIF
    IFDEF UNUSED_OP_PAPER_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BORDER_D
    DW OP_BORDER_D
    ENDIF
    IFDEF UNUSED_OP_BORDER_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PRINT_D
    DW OP_PRINT_D
    ENDIF
    IFDEF UNUSED_OP_PRINT_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_INK_I
    DW OP_INK_I
    ENDIF
    IFDEF UNUSED_OP_INK_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PAPER_I
    DW OP_PAPER_I
    ENDIF
    IFDEF UNUSED_OP_PAPER_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BORDER_I
    DW OP_BORDER_I
    ENDIF
    IFDEF UNUSED_OP_BORDER_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PRINT_I
    DW OP_PRINT_I
    ENDIF
    IFDEF UNUSED_OP_PRINT_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BRIGHT_D
    DW OP_BRIGHT_D
    ENDIF
    IFDEF UNUSED_OP_BRIGHT_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_FLASH_D
    DW OP_FLASH_D
    ENDIF
    IFDEF UNUSED_OP_FLASH_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BRIGHT_I
    DW OP_BRIGHT_I
    ENDIF
    IFDEF UNUSED_OP_BRIGHT_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_FLASH_I
    DW OP_FLASH_I
    ENDIF
    IFDEF UNUSED_OP_FLASH_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PICTURE_D
    DW OP_PICTURE_D
    ENDIF
    IFDEF UNUSED_OP_PICTURE_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_DISPLAY_D
    DW OP_DISPLAY_D
    ENDIF
    IFDEF UNUSED_OP_DISPLAY_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PICTURE_I
    DW OP_PICTURE_I
    ENDIF
    IFDEF UNUSED_OP_PICTURE_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_DISPLAY_I
    DW OP_DISPLAY_I
    ENDIF
    IFDEF UNUSED_OP_DISPLAY_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_RANDOM
    DW OP_RANDOM
    ENDIF
    IFDEF UNUSED_OP_RANDOM
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_OPTION
    DW OP_OPTION
    ENDIF
    IFDEF UNUSED_OP_OPTION
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_WAITKEY
    DW OP_WAITKEY
    ENDIF
    IFDEF UNUSED_OP_WAITKEY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_INKEY
    DW OP_INKEY
    ENDIF
    IFDEF UNUSED_OP_INKEY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_WAIT
    DW OP_WAIT
    ENDIF
    IFDEF UNUSED_OP_WAIT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PAUSE
    DW OP_PAUSE
    ENDIF
    IFDEF UNUSED_OP_PAUSE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHOOSE
    DW OP_CHOOSE
    ENDIF
    IFDEF UNUSED_OP_CHOOSE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHOOSE_W
    DW OP_CHOOSE_W
    ENDIF
    IFDEF UNUSED_OP_CHOOSE_W
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_TYPERATE
    DW OP_TYPERATE
    ENDIF
    IFDEF UNUSED_OP_TYPERATE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CLEAR
    DW OP_CLEAR
    ENDIF
    IFDEF UNUSED_OP_CLEAR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PAGEPAUSE
    DW OP_PAGEPAUSE
    ENDIF
    IFDEF UNUSED_OP_PAGEPAUSE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHAR_D
    DW OP_CHAR_D
    ENDIF
    IFDEF UNUSED_OP_CHAR_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_TAB
    DW OP_TAB
    ENDIF
    IFDEF UNUSED_OP_TAB
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_REPCHAR
    DW OP_REPCHAR
    ENDIF
    IFDEF UNUSED_OP_REPCHAR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SFX_D
    DW OP_SFX_D
    ENDIF
    IFDEF UNUSED_OP_SFX_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SFX_I
    DW OP_SFX_I
    ENDIF
    IFDEF UNUSED_OP_SFX_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_TRACK_D
    DW OP_TRACK_D
    ENDIF
    IFDEF UNUSED_OP_TRACK_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_TRACK_I
    DW OP_TRACK_I
    ENDIF
    IFDEF UNUSED_OP_TRACK_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PLAY_D
    DW OP_PLAY_D
    ENDIF
    IFDEF UNUSED_OP_PLAY_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PLAY_I
    DW OP_PLAY_I
    ENDIF
    IFDEF UNUSED_OP_PLAY_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_LOOP_D
    DW OP_LOOP_D
    ENDIF
    IFDEF UNUSED_OP_LOOP_D
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_LOOP_I
    DW OP_LOOP_I
    ENDIF
    IFDEF UNUSED_OP_LOOP_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_RANDOMIZE
    DW OP_RANDOMIZE
    ENDIF
    IFDEF UNUSED_OP_RANDOMIZE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_AT
    DW OP_POP_AT
    ENDIF
    IFDEF UNUSED_OP_POP_AT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_NEWLINE
    DW OP_NEWLINE
    ENDIF
    IFDEF UNUSED_OP_NEWLINE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_DI
    DW OP_SET_DI
    ENDIF
    IFDEF UNUSED_OP_SET_DI
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_SET_DI
    DW OP_POP_SET_DI
    ENDIF
    IFDEF UNUSED_OP_POP_SET_DI
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_DI
    DW OP_PUSH_DI
    ENDIF
    IFDEF UNUSED_OP_PUSH_DI
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_INK
    DW OP_POP_INK
    ENDIF
    IFDEF UNUSED_OP_POP_INK
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PAPER
    DW OP_POP_PAPER
    ENDIF
    IFDEF UNUSED_OP_POP_PAPER
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_BORDER
    DW OP_POP_BORDER
    ENDIF
    IFDEF UNUSED_OP_POP_BORDER
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_BRIGHT
    DW OP_POP_BRIGHT
    ENDIF
    IFDEF UNUSED_OP_POP_BRIGHT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_FLASH
    DW OP_POP_FLASH
    ENDIF
    IFDEF UNUSED_OP_POP_FLASH
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PRINT
    DW OP_POP_PRINT
    ENDIF
    IFDEF UNUSED_OP_POP_PRINT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHAR_I
    DW OP_CHAR_I
    ENDIF
    IFDEF UNUSED_OP_CHAR_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_CHAR
    DW OP_POP_CHAR
    ENDIF
    IFDEF UNUSED_OP_POP_CHAR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PICTURE
    DW OP_POP_PICTURE
    ENDIF
    IFDEF UNUSED_OP_POP_PICTURE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_DISPLAY
    DW OP_POP_DISPLAY
    ENDIF
    IFDEF UNUSED_OP_POP_DISPLAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_SFX
    DW OP_POP_SFX
    ENDIF
    IFDEF UNUSED_OP_POP_SFX
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_TRACK
    DW OP_POP_TRACK
    ENDIF
    IFDEF UNUSED_OP_POP_TRACK
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PLAY
    DW OP_POP_PLAY
    ENDIF
    IFDEF UNUSED_OP_POP_PLAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_LOOP
    DW OP_POP_LOOP
    ENDIF
    IFDEF UNUSED_OP_POP_LOOP
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PUSH_I
    DW OP_POP_PUSH_I
    ENDIF
    IFDEF UNUSED_OP_POP_PUSH_I
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_XPOS
    DW OP_SET_XPOS
    ENDIF
    IFDEF UNUSED_OP_SET_XPOS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_YPOS
    DW OP_SET_YPOS
    ENDIF
    IFDEF UNUSED_OP_SET_YPOS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_XPOS
    DW OP_PUSH_XPOS
    ENDIF
    IFDEF UNUSED_OP_PUSH_XPOS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_YPOS
    DW OP_PUSH_YPOS
    ENDIF
    IFDEF UNUSED_OP_PUSH_YPOS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_MAX
    DW OP_MIN
    ENDIF
    IFDEF UNUSED_OP_MIN
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_MAX
    DW OP_MAX
    ENDIF
    IFDEF UNUSED_OP_MAX
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BLIT
    DW OP_BLIT
    ENDIF
    IFDEF UNUSED_OP_BLIT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_BLIT
    DW OP_POP_BLIT
    ENDIF
    IFDEF UNUSED_OP_POP_BLIT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_MENUCONFIG
    DW OP_MENUCONFIG
    ENDIF
    IFDEF UNUSED_OP_MENUCONFIG
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_MENUCONFIG
    DW OP_POP_MENUCONFIG
    ENDIF
    IFDEF UNUSED_OP_POP_MENUCONFIG
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_IS_DISK
    DW OP_PUSH_IS_DISK
    ENDIF
    IFDEF UNUSED_OP_PUSH_IS_DISK
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_BACKSPACE
    DW OP_BACKSPACE
    ENDIF
    IFDEF UNUSED_OP_BACKSPACE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_RAMLOAD
    DW OP_RAMLOAD
    ENDIF
    IFDEF UNUSED_OP_RAMLOAD
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_RAMSAVE
    DW OP_RAMSAVE
    ENDIF
    IFDEF UNUSED_OP_RAMSAVE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_SLOT_LOAD
    DW OP_POP_SLOT_LOAD
    ENDIF
    IFDEF UNUSED_OP_POP_SLOT_LOAD
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_SLOT_SAVE
    DW OP_POP_SLOT_SAVE
    ENDIF
    IFDEF UNUSED_OP_POP_SLOT_SAVE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_SAVE_RESULT
    DW OP_PUSH_SAVE_RESULT
    ENDIF
    IFDEF UNUSED_OP_PUSH_SAVE_RESULT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_FADEOUT
    DW OP_FADEOUT
    ENDIF
    IFDEF UNUSED_OP_FADEOUT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_FILLATTR
    DW OP_FILLATTR
    ENDIF
    IFDEF UNUSED_OP_FILLATTR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUTATTR
    DW OP_PUTATTR
    ENDIF
    IFDEF UNUSED_OP_PUTATTR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_PUTATTR
    DW OP_POP_PUTATTR
    ENDIF
    IFDEF UNUSED_OP_POP_PUTATTR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHOOSE_CH
    DW OP_CHOOSE_CH
    ENDIF
    IFDEF UNUSED_OP_CHOOSE_CH
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_OPTION_ST
    DW OP_PUSH_OPTION_ST
    ENDIF
    IFDEF UNUSED_OP_PUSH_OPTION_ST
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CLEAR_OPTIONS
    DW OP_CLEAR_OPTIONS
    ENDIF
    IFDEF UNUSED_OP_CLEAR_OPTIONS
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_GETATTR
    DW OP_PUSH_GETATTR
    ENDIF
    IFDEF UNUSED_OP_PUSH_GETATTR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_ALL_BLIT
    DW OP_POP_ALL_BLIT
    ENDIF
    IFDEF UNUSED_OP_POP_ALL_BLIT
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SHIFT_R
    DW OP_SHIFT_R
    ENDIF
    IFDEF UNUSED_OP_SHIFT_R
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SHIFT_L
    DW OP_SHIFT_L
    ENDIF
    IFDEF UNUSED_OP_SHIFT_L
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_ALL_PUTATTR
    DW OP_POP_ALL_PUTATTR
    ENDIF
    IFDEF UNUSED_OP_POP_ALL_PUTATTR
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_FILLATTR
    DW OP_POP_FILLATTR
    ENDIF
    IFDEF UNUSED_OP_POP_FILLATTR
    DW ERROR_NOP
    ENDIF



    IFDEF USE_256_OPCODES
    REPT 256-(($-OPCODES)/2)
    DW ERROR_NOP
    ENDR
    ENDIF
    IFNDEF USE_256_OPCODES
    REPT 128-(($-OPCODES)/2)
    DW ERROR_NOP
    ENDR
    ENDIF

    

