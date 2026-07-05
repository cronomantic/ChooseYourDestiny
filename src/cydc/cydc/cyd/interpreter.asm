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

    IFNDEF UNUSED_OP_SET_KEMPSTON
OP_SET_KEMPSTON:
    ld d, HIGH FLAGS
    ld e, (hl)
    inc hl
    call KEMPSTON   
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_PUSH_KEMPSTON
OP_PUSH_KEMPSTON:
    call KEMPSTON
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF


    IFNDEF UNUSED_OP_PUSH_RANDOM
    IFNDEF USED_DIV_DE
    DEFINE USED_DIV_DE
    ENDIF
OP_PUSH_RANDOM:
    push hl
    call RANDOM
    ld a, r            ;Select if we use H or L value based in R value
    rrca
    jr c, 1f
    ld a, l
    jr 2f
1:  ld a, h
2:  pop hl
    ld d, a
    ld e, (hl)        ;Get max element
    inc hl
    ld a, $FF         ;If E is 255, leave the value as it is
    cp e
    jr nz, 3f
    ld a, d
    jr 4f
3:  inc e             ;Increment E to calculate mod E+1
    call DIV_DE
4:  ;Stack
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF


    IFNDEF UNUSED_OP_RANDOM
    IFNDEF USED_DIV_DE
    DEFINE USED_DIV_DE
    ENDIF
OP_RANDOM:
    ld e, (hl)
    ld d, HIGH FLAGS
    push de
    inc hl
    push hl
    call RANDOM
    ld a, r            ;Select if we use H or L value based in R value
    rrca
    jr c, 1f
    ld a, l
    jr 2f
1:  ld a, h
2:  pop hl
    ld d, a
    ld e, (hl)        ;Get max element
    inc hl
    ld a, $FF         ;If E is 255, leave the value as it is
    cp e
    jr nz, 3f
    ld a, d
    jr 4f
3:  inc e             ;Increment E to calculate mod E+1
    call DIV_DE
4:  pop de
    ld (de), a
    jp EXEC_LOOP
    ENDIF

    IFDEF USED_DIV_DE
    ; Divide D by E. The quotient is in D and remainder in A
DIV_DE:
   xor a
   ld b, 8
1: sla d
   rla
   cp e
   jr c, 2f
   sub e
   inc d
2: djnz	1b
   ret
   ENDIF


    IFNDEF UNUSED_OP_RANDOMIZE
OP_RANDOMIZE:
    ld e, (hl) 
    inc hl
    ld d, (hl)
    inc hl
    push hl
    ex de, hl
    ld a, h
    or l
    jr nz, 1f
    call SET_RND_SEED
    jr 2f
1:  call SET_RND_SEED2
2:  pop hl
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

; ------------------------------------------------------------------------------
; Immutable DATA stream (BASIC-style DATA/READ/RESTORE/DATAEND). The compiler
; gathers every DATA value into one read-only chunk (DATA_CHUNK, DATA_LEN bytes)
; placed like any other chunk (flash slot on MLD, banked on 128k/+3, resident on
; 48k), and keeps a 16-bit cursor DATA_PTR. These share the opcode slots freed
; from the rarely-used BRIGHT_I/FLASH_I/BORDER_I fusions (0x27/0x28/0x23).
;
; DATA_LEN (the blob's byte length) is emitted by the compiler (get_asm_*). The
; default keeps the size pass -- which assembles every opcode -- and DATA-less
; builds assembling; the real build overrides it with a DEFINE before this include.
; The single TYPE_DATA resource always has index 0, so OP_READ passes 0 directly
; (no DATA_CHUNK define: the token would be substring-substituted inside
; LOAD_DATA_CHUNK -> LOAD_0 by sjasmplus's textual DEFINE).
    IFNDEF DATA_LEN
    DEFINE DATA_LEN 0
    ENDIF

    IFNDEF UNUSED_OP_READ
; OP_READ: read the byte at the cursor into the VM data stack (a following
; POP_SET/POP_SET_DI stores it), then advance the cursor. LOAD_DATA_CHUNK maps the
; TYPE_DATA chunk and returns its base in HL; we save the running bytecode chunk
; and page it back with LOAD_CHUNK afterwards (like the array flash path). The VM
; stack (IX) and DATA_PTR are resident, so they survive the paging.
OP_READ:
    push hl                   ; save bytecode PC
    ; Endless tape: if the cursor has reached the end, restart at 0 (reading past
    ; the end wraps around instead of running off into undefined bytes).
    ld hl, DATA_LEN
    ld de, (DATA_PTR)
    or a
    sbc hl, de                ; DATA_LEN - DATA_PTR
    jr c, .wrap               ; DATA_PTR > DATA_LEN
    jr nz, .noWrap            ; DATA_PTR < DATA_LEN
.wrap:                        ; DATA_PTR >= DATA_LEN -> rewind
    ld hl, 0
    ld (DATA_PTR), hl
.noWrap:
    ld a, (CHUNK)
    push af                   ; save the running bytecode chunk id
    xor a                     ; the single TYPE_DATA resource has index 0
    call LOAD_DATA_CHUNK      ; map the TYPE_DATA chunk; HL = its base
    ld de, (DATA_PTR)
    add hl, de                ; HL = base + cursor
    ld a, (hl)                ; A = data byte
    PUSH_INT_STACK            ; push it to the VM data stack (resident, safe)
    ld hl, (DATA_PTR)
    inc hl
    ld (DATA_PTR), hl         ; advance the cursor (resident, safe)
    pop af                    ; A = saved bytecode chunk id
    call LOAD_CHUNK           ; remap the bytecode chunk
    pop hl                    ; restore bytecode PC
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_RESTORE
; OP_RESTORE: set the cursor to a 16-bit operand (0 for plain RESTORE, or the
; data offset of a label for RESTORE label; both baked by the compiler).
OP_RESTORE:
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    ld (DATA_PTR), de
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_DATAEND
; OP_DATAEND: push 1 if the cursor is at/past the end of the stream, else 0.
; HL is the bytecode PC, so save it across the DATA_PTR comparison.
OP_DATAEND:
    push hl                   ; save bytecode PC (the compare below clobbers HL)
    ld hl, (DATA_PTR)
    ld de, DATA_LEN
    or a
    sbc hl, de                ; carry set if DATA_PTR < DATA_LEN (more data left)
    ld a, 0
    jr c, 1f
    inc a                     ; DATA_PTR >= DATA_LEN -> at end -> 1
1:  PUSH_INT_STACK
    pop hl                    ; restore bytecode PC
    jp EXEC_LOOP
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

    ld c, (hl)       ;PosX
    inc hl
    ld b, (hl)       ;PosY
    inc hl
    ld e, (hl)       ;Width
    inc hl
    ld d, (hl)       ;Height
    inc hl
    push hl
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
    push hl                    ;Store pointer
    ld a, (OPTION_BULLET_ENABLED)
    or a
    jr z, 1f
    call ADJUST_CHAR_POS  ;Advance to the best position for printing the choice
    push de
    push de                    ; ; d = POS_Y, e = POS_X
    ld a, NO_SELECTED_BULLET
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
1:  ld a, (NUM_OPTIONS)
    sla a
    sla a
    sla a
    ld l, a
    ld h, HIGH OPTIONS_TABLE
    ld (hl), e             ;Store screen pos
    inc hl
    ld (hl), d
    inc hl
    ld a, (NUM_OPTIONS)    
    ld (hl), a             ;Storing num option as default value
    inc hl
    inc a
    ld (NUM_OPTIONS), a   ;Increment options
    ex de, hl              ;Move option table address to DE
    pop hl
    ldi                    ;Copy Address to address table
    ldi
    ldi
    ldi
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_VAL_OPTION
OP_POP_VAL_OPTION:
    ld a, (NUM_OPTIONS)
    cp MAXIMUM_OPTIONS    ;test if number of options is MAX4
    jr c,.option_ok
    ld a, 2
    jp SYS_ERROR
.option_ok:
    push hl                    ;Store pointer
    ld a, (OPTION_BULLET_ENABLED)
    or a
    jr z, 1f
    call ADJUST_CHAR_POS  ;Advance to the best position for printing the choice
    push de
    push de                    ; ; d = POS_Y, e = POS_X
    ld a, NO_SELECTED_BULLET
    call GET_CHARACTER_POINTER  ;Get character pointer
    pop de
    call PUT_8X8_CHAR           ; Print the character
    pop de
1:  ld a, (NUM_OPTIONS)
    push af
    sla a
    sla a
    sla a
    ld l, a
    ld h, HIGH OPTIONS_TABLE
    ld (hl), e             ;Store screen pos
    inc hl
    ld (hl), d
    inc hl
    pop af
    inc a
    ld (NUM_OPTIONS), a   ;Increment options
    POP_INT_STACK
    ld (hl), a             ;Storing value from stack
    inc hl
    ex de, hl              ;Move option table address to DE
    pop hl
    ldi                    ;Copy Address to address table
    ldi
    ldi
    ldi
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
1:  call INKEY_MENU
    and KEYPRESS_FIRE
    jr nz, .keyp
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
2:  call INKEY_MENU
    or a
    jr nz, 2b
    ;xor a
    ld (PRINTED_LINES), a
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
1:  call INKEY_MENU
    and KEYPRESS_FIRE
    jr nz, .keyp
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
2:  call INKEY_MENU
    or a
    jr nz, 2b
    ;xor a
    ld (PRINTED_LINES), a
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CHOOSE
OP_CHOOSE:
    ld (.self_a), hl
    ld a, (DEFAULT_OPTION)
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
    call INKEY_MENU
    rrca
    jp c, .right
    rrca
    jp c, .left
    rrca
    jp c, .down
    rrca
    jp c, .up
    rrca
    jp c, .selected
    call ANIMATE_OPTION_BULLET
    jr .inkey
.left:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
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
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
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
5:  call INKEY_MENU
    or a
    jr nz, 5b
    ld a, (hl)      ;Store selected option value
    inc hl
    ld (SELECTED_OPTION_VALUE), a 
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
    
    ld a, (DEFAULT_OPTION)
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
    call INKEY_MENU
    rrca
    jp c, .right
    rrca
    jp c, .left
    rrca
    jp c, .down
    rrca
    jp c, .up
    rrca
    jp c, .selected
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
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
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
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
    or a
    jp z, .inkey
    jr 3b
.count_elapsed:
    ld a, $FF
    ld (SELECTED_OPTION), a 
    ld (SELECTED_OPTION_VALUE), a 
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
    ld a, (hl)      ;Store selected option value
    inc hl
    ld (SELECTED_OPTION_VALUE), a 
3:  ld c, (hl)               ;C= if is GOSUB
    inc hl
    xor a
    ld (NUM_OPTIONS), a
4:  call INKEY_MENU
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
    ld a, (DEFAULT_OPTION)
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
    call INKEY_MENU
    rrca
    jp c, .right
    rrca
    jp c, .left
    rrca
    jp c, .down
    rrca
    jp c, .up
    rrca
    jp c, .selected
    call ANIMATE_OPTION_BULLET
    jr .inkey
.left:
    ld a, (SELECTED_OPTION)
    or a
    jp z, .inkey
    push af
    ld a, NO_SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
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
    ld a, (INCR_X_OPTION)
    ld b, a
    pop af
    add a, b
    cp c
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
4:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    sub b
    jp c, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
2:  call INKEY_MENU
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
    ld a, (INCR_Y_OPTION)
    ld b, a
    pop af
    add a, b
    cp c                        ; selected_option-numoptions
    jp nc, .inkey
    ld (SELECTED_OPTION), a
    ld a, SELECTED_BULLET
    call PRINT_SELECTED_OPTION_BULLET
3:  call INKEY_MENU
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
5:  call INKEY_MENU
    or a
    jr nz, 5b
    ld a, (hl)      ;Store selected option value
    inc hl
    ld (SELECTED_OPTION_VALUE), a 
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
    ld a, (hl)
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
    ld a, (CHARSET_OFFSET)
    add a, $20
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
    push ix
    push hl
    ld a, BEEPFX_AVAILABLE
    or a
    jr z, 1f

    ld a, e
    ld (SFX_ID), a
    call BEEPFX

1:  pop hl
    pop ix
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SFX_I
OP_SFX_I:
    ld e, (hl)
    inc hl
    push ix
    push hl
    ld a, BEEPFX_AVAILABLE
    or a
    jr z, 1f

    ld d, HIGH FLAGS
    ld a, (de)
    ld (SFX_ID), a
    call BEEPFX

1:  pop hl
    pop ix
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
    push ix
    call BEEPFX
    pop ix
1:  pop hl
    jp EXEC_LOOP
    ENDIF
    

    IFDEF USE_WYZ
FIND_WYZ_INDEX:
    push af
    push hl
    ld c, a
    ld b, TYPE_WYZ
    call FIND_IN_INDEX
    pop hl
    pop af
    ret
    ENDIF

    IFNDEF UNUSED_OP_TRACK_D
OP_TRACK_D:
    ld a, (hl)
    inc hl
    IFDEF USE_VORTEX
    push hl
    push ix
    call LOAD_MUSIC
    pop ix
    pop hl
    ENDIF
    IFDEF USE_WYZ
    call FIND_WYZ_INDEX
    ld d, 1
    ld e, a
    call WYZ_CALL
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
    push hl
    push ix
    call LOAD_MUSIC
    pop ix
    pop hl
    ENDIF
    IFDEF USE_WYZ
    call FIND_WYZ_INDEX
    ld d, 1
    ld e, a
    call WYZ_CALL
    ENDIF
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_TRACK
OP_POP_TRACK:
    POP_INT_STACK
    IFDEF USE_VORTEX
    push hl
    push ix
    call LOAD_MUSIC
    pop ix
    pop hl
    ENDIF
    IFDEF USE_WYZ
    call FIND_WYZ_INDEX
    ld d, 1
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 2
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 2
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 2
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 3
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 3
    ld e, a
    call WYZ_CALL
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
    IFDEF USE_WYZ
    ld d, 3
    ld e, a
    call WYZ_CALL
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
    ld d, (ix+0)
    ld e, (ix+1)
    ld b, (ix+2)
    ld c, (ix+3)
    ld (INCR_X_OPTION), bc
    ld (DEFAULT_OPTION), de
    ld de, 4
    add ix, de
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_MENUCONFIG
OP_MENUCONFIG:
    ld de, INCR_X_OPTION
    ldi
    ldi
    ldi
    ldi
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
    ;Get Attr
    ld a, (ix+0)
    ;Get Height
    ld h, (ix+1)
    ;Get Width
    ld l, (ix+2)
    ;Get Rows
    ld b, (ix+3)
    ;Get Cols
    ld c, (ix+4)
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
    ;Get Attr
    ld d, (hl)
    inc hl
    ;Get mask
    ld e, (hl)
    inc hl
    ;Get Cols
    ld c, (hl)
    inc hl
    ;Get Rows
    ld b, (hl)
    inc hl
    push hl
    call POS_ADJUST
    call PUT_ATTR
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_POP_PUTATTR
    IFNDEF PUT_ATTR_USED
    DEFINE PUT_ATTR_USED
    ENDIF
OP_POP_PUTATTR:
    ;Get Cols
    ld c, (hl)
    inc hl
    ;Get Rows
    ld b, (hl)
    inc hl
    push hl
    call POS_ADJUST
    ;Get mask
    ld e, (ix+0)
    ;Get Attr
    ld d, (ix+1)
    inc ix
    inc ix
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
    or d            ;OR with new values
    ld (hl), a      ;Store value again
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
    IFNDEF UNUSED_OP_WINDOW
OP_WINDOW:
    push hl
    push hl
    ld a, (CURR_WINDOW)
    ld de, WINDOWS
    add a, e
    jr nc, 1f
    inc d
1:  ld e, a
    ld hl, POS_X
    ld bc, 7
    ldir
    ld a, (ATTR_P)
    ld (de), a
    pop hl
    ld a, (hl)
    and 7
    sla a
    sla a
    sla a
    ld (CURR_WINDOW), a
    ld hl, WINDOWS
    add a, l
    jr nc, 1f
    inc h
1:  ld l, a
    ld de, POS_X
    ld bc, 7
    ldir
    ld a, (hl)
    ld (ATTR_P), a
    pop hl
    inc hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_CHARSET
    ; TODO: Add charset to Window?
OP_CHARSET:
    ld a, (hl)
    inc hl
    push hl
    or a
    jr z, 1f
    ld a, $80                ;If <> 0, sets offset to 128
1:  ld (CHARSET_OFFSET), a
    add a, $20               ;Space
    call GET_CHARACTER_WIDTH
    ld (WIDTH_BACKSPACE), a
    pop hl
    jp EXEC_LOOP
    ENDIF

    IFNDEF UNUSED_OP_SKIP_ARRAY
OP_SKIP_ARRAY:
    ld d, 0
    ld e, (hl)
    inc hl
    inc de
    add hl, de
    jp EXEC_LOOP
    ENDIF

; ARR_RESIDENT_BANK: sentinel "bank" byte the compiler puts in an array operand on
; MLD, where the array's own chunk is read-only Dandanator flash. It means "the
; array was copied to the resident RAM pool ARR_POOL; the operand address is a
; pool offset". Only meaningful under IS_MLD_DAN; on 48k/128k/+3 arrays keep their
; real chunk bank and this branch never triggers.
ARR_RESIDENT_BANK EQU $FE

    IFNDEF UNUSED_OP_PUSH_VAL_ARRAY
OP_PUSH_VAL_ARRAY:
    ld c, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl
    IFDEF IS_MLD_DAN
    IFDEF OP_EXTERN_BANKED
    ; mld128: the array lives in a real 128K RAM bank at $C000+offset (DE), with C
    ; the physical bank. Page it in, access the paged window, restore the caller's
    ; bank. The Dandanator slot ($0000) and $7FFD bank ($C000) are independent HW.
    ld a, c
    or ROM48KBASIC
    call SET_RAM_BANK         ; page the array's bank; A = previous $7FFD value
    push af
    call .push_val_array      ; DE -> [len-1][data] in the paged window
    pop af
    call SET_RAM_BANK         ; restore the caller's bank
    jr 1f
    ELSE
    ld a, c
    cp ARR_RESIDENT_BANK      ; resident (RAM pool) array?
    jr nz, .flash
    ld hl, ARR_POOL
    add hl, de                ; DE was the pool offset -> ARR_POOL+offset
    ex de, hl
    call .push_val_array
    jr 1f
.flash:
    ENDIF
    ENDIF
    ld a, (CHUNK)
    cp c                      ; If the CHUNK is the same...
    jr z, .same_CHUNK
    push af
    ld a, c
    push de
    call LOAD_CHUNK
    pop de
    call .push_val_array
    pop af
    call LOAD_CHUNK
    jr 1f
.same_CHUNK:
    call .push_val_array
1:  pop hl
    jp EXEC_LOOP
.push_val_array:
    ld a, (de)            ;Get size-1
    inc de
    ld h, 0
    ld l, (ix+0)          ;Get offset
    cp l                  ;test if offset > (size-1) (A-C)
    jr nc, 2f
    ;Error, array out of bounds
    ld a, 7
    jp SYS_ERROR
2:  add hl, de
    ld a, (hl)
    ld (ix+0), a
    ret
    ENDIF

    IFNDEF UNUSED_OP_POP_VAL_ARRAY
OP_POP_VAL_ARRAY:
    ld c, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    push hl
    IFDEF IS_MLD_DAN
    IFDEF OP_EXTERN_BANKED
    ; mld128: array in a real RAM bank at $C000+offset (DE); C = physical bank.
    ; Page it in, write to the paged window (persists in RAM), restore.
    ld a, c
    or ROM48KBASIC
    call SET_RAM_BANK         ; page the array's bank; A = previous $7FFD value
    push af
    call .pop_val_array       ; DE -> [len-1][data] in the paged window
    pop af
    call SET_RAM_BANK         ; restore the caller's bank
    jr 1f
    ELSE
    ld a, c
    cp ARR_RESIDENT_BANK      ; resident (RAM pool) array?
    jr nz, .flash
    ld hl, ARR_POOL
    add hl, de                ; DE was the pool offset -> ARR_POOL+offset
    ex de, hl
    call .pop_val_array
    jr 1f
.flash:
    ENDIF
    ENDIF
    ld a, (CHUNK)
    cp c       ; If the CHUNK is the same...
    jr z, .same_CHUNK
    push af
    ld a, c
    push de
    call LOAD_CHUNK
    pop de
    call .pop_val_array
    pop af
    call LOAD_CHUNK
    jr 1f
.same_CHUNK:
    call .pop_val_array
1:  pop hl
    jp EXEC_LOOP
.pop_val_array:
    ld a, (de)            ;Get size-1
    inc de
    ld h, 0
    ld l, (ix+0)          ;Get offset
    cp l                  ;test if offset > (size-1) (A-C)
    ld a, (ix+1)          ;Get value
    jr nc, 2f
    ;Error, array out of bounds
    ld a, 7
    jp SYS_ERROR
2:  add hl, de
    ld (hl), a
    inc ix
    inc ix
    ret
    ENDIF

    IFNDEF UNUSED_OP_PUSH_LEN_ARRAY
OP_PUSH_LEN_ARRAY:
    ld c, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl
    IFDEF IS_MLD_DAN
    IFDEF OP_EXTERN_BANKED
    ; mld128: array in a real RAM bank at $C000+offset (DE); C = physical bank.
    ; Page it in, read the length byte, restore, push it.
    ld a, c
    or ROM48KBASIC
    call SET_RAM_BANK         ; page the array's bank; A = previous $7FFD value
    ld b, a                   ; B = previous bank (survives the read below)
    ld a, (de)                ; length byte (size-1) from the paged window
    push af                   ; save the length across the restore
    ld a, b
    call SET_RAM_BANK         ; restore the caller's bank
    pop af                    ; A = length byte
    PUSH_INT_STACK
    jp EXEC_LOOP
    ELSE
    ld a, c
    cp ARR_RESIDENT_BANK      ; resident (RAM pool) array?
    jr nz, .flash
    ld hl, ARR_POOL
    add hl, de                ; DE was the pool offset -> ARR_POOL+offset
    ld a, (hl)                ; length byte (size-1)
    PUSH_INT_STACK
    jp EXEC_LOOP
.flash:
    ENDIF
    ENDIF
    ld a, (CHUNK)
    cp c                  ; If the CHUNK is the same...
    jr z, .same_CHUNK
    push hl
    push af
    ld a, c
    push de
    call LOAD_CHUNK
    pop de
    ld a, (de)
    PUSH_INT_STACK
    pop af
    call LOAD_CHUNK
    pop hl
    jp EXEC_LOOP
.same_CHUNK:
    ld a, (de)
    PUSH_INT_STACK
    jp EXEC_LOOP
    ENDIF

    IFDEF IS_MLD_DAN
; ARR_INIT: copy every DIM array's [len-1][data] record from its (read-only)
; Dandanator flash chunk into writable RAM, once at boot (called from
; START_LOADING before EXEC_LOOP). ARR_INIT_TABLE is emitted by the compiler
; (cyd_mld.asm), $FF-terminated. The destination differs per MLD variant.
    IFDEF OP_EXTERN_BANKED
; mld128: destination is a real 128K RAM bank at $C000+addr. LOAD_CHUNK maps the
; source flash slot at $0000 (SET_DAN_BANK) and SET_RAM_BANK pages the destination
; bank at $C000 -- independent hardware, both active for the LDIR. Table = 8-byte
; entries: DEFB chunk : DEFW src_off : DEFB dest_bank : DEFW dest_addr : DEFW nbytes
ARR_INIT:
    ld ix, ARR_INIT_TABLE
.loop:
    ld a, (ix+0)
    inc a
    jr z, .done               ; chunk byte $FF -> end of table
    ld a, (ix+0)
    call LOAD_CHUNK           ; map source flash slot at $0000 (IX preserved)
    ld a, (ix+3)              ; dest_bank
    or ROM48KBASIC
    call SET_RAM_BANK         ; page destination bank at $C000 (IX/DE/HL preserved)
    ld c, (ix+6)
    ld b, (ix+7)              ; BC = nbytes
    ld e, (ix+4)
    ld d, (ix+5)              ; DE = dest_addr ($C000+offset, in the paged bank)
    ld l, (ix+1)
    ld h, (ix+2)              ; HL = src_off (0-based inside the mapped flash slot)
    ldir                      ; copy the record: flash slot -> RAM bank
    ld de, 8
    add ix, de                ; advance to next 8-byte entry
    jr .loop
.done:
    xor a
    or ROM48KBASIC
    call SET_RAM_BANK         ; leave bank 0 paged at $C000 (a clean default)
    ret
    ELSE
; strict mld (48K): destination is the resident pool ARR_POOL (no banking).
; Table = 7-byte entries: DEFB chunk : DEFW src_off : DEFW pool_off : DEFW nbytes
ARR_INIT:
    ld ix, ARR_INIT_TABLE
.loop:
    ld a, (ix+0)
    inc a
    ret z                     ; chunk byte $FF -> end of table
    ld a, (ix+0)
    call LOAD_CHUNK           ; map source chunk's flash slot at $0000 (IX preserved)
    ld c, (ix+5)
    ld b, (ix+6)              ; BC = nbytes
    ld e, (ix+3)
    ld d, (ix+4)
    ld hl, ARR_POOL
    add hl, de                ; HL = ARR_POOL + pool_off (destination)
    ex de, hl                 ; DE = destination
    ld l, (ix+1)
    ld h, (ix+2)              ; HL = src_off (0-based inside the mapped slot)
    ldir                      ; copy the record: flash slot -> resident pool
    ld de, 7
    add ix, de                ; advance to next 7-byte entry
    jr .loop
    ENDIF
    ENDIF

/*

    ld a, (ix+0)
    inc ix
    ld a, (ix+0)
    inc ix

    MACRO OP_2PARAM_GET_STACK
    ld c, (ix+0)
    ld a, (ix+1)
    ENDM
    
    MACRO OP_2PARAM_STORE_STACK
    inc ix
    ld (ix+0), a
    jp EXEC_LOOP
    ENDM

    MACRO POP_INT_STACK
    ld a, (ix+0)
    inc ix
    ENDM

    MACRO PUSH_INT_STACK
    dec ix
    ld (ix+0), a
    ENDM
*/

    IFNDEF UNUSED_OP_EXTERN
; OP_EXTERN: invoke a native routine registered with IMPORT / called with CALL.
; Operand layout: [bank, addr_lo, addr_hi]. On entry HL points at the operand.
; ABI: the routine is entered with DE=FLAGS (base of the 256-byte variable
; array) and must end with RET. It may freely use AF/BC/DE/HL/IX/IY (the handler
; saves IX/IY, which the interpreter itself relies on). On 48k the routine is
; resident and the bank byte is ignored (direct call). On banked targets the
; bank byte is the physical RAM bank holding the routine at $C000+offset: the
; handler pages it in, calls it, and restores the script bank on return. The
; engine (including this handler and FLAGS) is resident at $8000-$BFFF, so it
; keeps running while $C000 is paged to the routine.
OP_EXTERN:
    ld a, (hl)          ; bank byte
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)
    inc hl              ; A = bank, DE = routine address, HL = next bytecode PC
    push hl             ; save interpreter PC
    push ix             ; save VM data-stack pointer
    push iy             ; save ROM sysvars pointer
    IFDEF OP_EXTERN_BANKED
    or ROM48KBASIC
    call SET_RAM_BANK   ; page the routine's bank at $C000; A = previous port
    push af             ; save previous $7FFD value to restore the script bank
    ld hl, .cont
    push hl             ; return address for the routine's RET
    push de             ; routine address (target of the RET below)
    ld de, FLAGS
    ret                 ; jump into the routine with DE=FLAGS
.cont:
    pop af              ; previous port value (the script's bank)
    call SET_RAM_BANK   ; page the script bank back at $C000
    ELSE
    ld hl, .cont        ; 48k: routine is resident, call it directly
    push hl             ; return address for the routine's RET
    push de             ; routine address
    ld de, FLAGS
    ret                 ; jump into the routine with DE=FLAGS
.cont:
    ENDIF
    pop iy
    pop ix
    pop hl              ; restore interpreter PC
    jp EXEC_LOOP

    IFNDEF UNUSED_ARR_BROKER
; ------------------------------------------------------------------------------
; Resident memory broker for native routines (inline ASM / IMPORT).
;
; A banked native routine runs at $C000 in its own RAM bank, so it cannot page
; another bank in at $C000 without evicting itself. These resident services do
; the paging on its behalf: page the target bank in, touch one byte, page the
; caller's bank back, and return. They live in the always-mapped engine image,
; so they keep running while $C000 is paged. On 48k everything is resident and
; the bank byte is ignored (direct access).
;
; The compiler injects, per CYD array, the constants a routine uses to reach it:
;   ARR_<name>       address of element 0 (in the paged window on banked targets)
;   ARR_<name>_LEN   element count
;   ARR_<name>_BANK  physical RAM bank ($FF = resident / low RAM, no paging)
;
; CYD_PEEK: read one byte from possibly-banked memory.
;   In:  A  = physical RAM bank ($FF = resident, no paging)
;        HL = address to read
;   Out: A  = byte read
;   Preserves BC/DE/HL/IX/IY.
CYD_PEEK:
    IFDEF OP_EXTERN_BANKED
    cp $FF
    jr z, .resident
    push bc
    push de
    or ROM48KBASIC
    call SET_RAM_BANK   ; page target bank at $C000; A = previous port value
    ld e, a             ; save previous port (SET_RAM_BANK preserves DE)
    ld a, (hl)
    ld d, a             ; save the byte read
    ld a, e
    call SET_RAM_BANK   ; page the caller's bank back
    ld a, d
    pop de
    pop bc
    ret
.resident:
    ld a, (hl)
    ret
    ELSE
    ld a, (hl)          ; 48k: everything resident, direct read
    ret
    ENDIF

; CYD_POKE: write one byte to possibly-banked memory.
;   In:  A  = physical RAM bank ($FF = resident, no paging)
;        HL = address to write
;        E  = byte to write
;   Preserves BC/DE/HL/IX/IY.
CYD_POKE:
    IFDEF OP_EXTERN_BANKED
    cp $FF
    jr z, .resident
    push bc
    push de
    or ROM48KBASIC
    call SET_RAM_BANK   ; page target bank at $C000; A = previous port value
    ld d, a             ; save previous port (E still holds the value byte)
    ld a, e
    ld (hl), a          ; write the value
    ld a, d
    call SET_RAM_BANK   ; page the caller's bank back
    pop de
    pop bc
    ret
.resident:
    ld a, e
    ld (hl), a
    ret
    ELSE
    ld a, e             ; 48k: everything resident, direct write
    ld (hl), a
    ret
    ENDIF

; CYD_ARR_MAP: obtain a directly-addressable working copy of an array for fast,
; banking-free access. On a banked target it copies the array from its paged
; bank into the resident SAVE_FLAGS scratch (256 bytes, free outside SAVE/LOAD)
; and returns a pointer to it; on a resident array (or 48k) it just returns the
; array's own address, since it is already directly addressable. Work on the
; returned pointer, then call CYD_ARR_FLUSH to write changes back.
;   In:  A  = physical RAM bank ($FF = resident)
;        HL = array address (element 0)
;        BC = element count (1..256)
;   Out: HL = pointer to the working copy (write through it directly)
;   Only one array may be mapped at a time (the scratch is shared).
CYD_ARR_MAP:
    IFDEF OP_EXTERN_BANKED
    cp $FF
    jr z, .resident
    push bc                 ; save count across the paging call
    or ROM48KBASIC
    call SET_RAM_BANK       ; page the array's bank in; A = previous port
    pop bc                  ; BC = count again
    push af                 ; save previous port
    ld de, SAVE_FLAGS
    ldir                    ; copy (HL, paged) -> (SAVE_FLAGS, resident)
    pop af
    call SET_RAM_BANK       ; page the caller's bank back
    ld hl, SAVE_FLAGS       ; return the resident working copy
    ret
.resident:
    ret                     ; HL already points at the live array
    ELSE
    ret                     ; 48k: HL already points at the live array
    ENDIF

; CYD_ARR_FLUSH: write a mapped array's working copy back to the array. On a
; banked target it copies SAVE_FLAGS back into the array's paged bank; for a
; resident array (or 48k) the routine wrote in place, so it is a no-op.
;   In:  A  = physical RAM bank ($FF = resident)
;        HL = array address (element 0)
;        BC = element count (1..256)
CYD_ARR_FLUSH:
    IFDEF OP_EXTERN_BANKED
    cp $FF
    ret z                   ; resident: written in place, nothing to flush
    push bc
    or ROM48KBASIC
    call SET_RAM_BANK       ; page the array's bank in; A = previous port
    pop bc
    push af
    ex de, hl               ; DE = array address (destination)
    ld hl, SAVE_FLAGS       ; HL = working copy (source)
    ldir                    ; copy (SAVE_FLAGS) -> (array, paged)
    pop af
    call SET_RAM_BANK       ; page the caller's bank back
    ret
    ELSE
    ret                     ; 48k: written in place, nothing to flush
    ENDIF
    ENDIF                   ; UNUSED_ARR_BROKER

    IFNDEF UNUSED_CYD_CALL
; CYD_CALL: call a native routine that lives in ANOTHER block (cross-bank), from
; within a native routine. The callee's (bank,address) is unknown when the caller
; is assembled, so the caller passes a routine index (RT_<name>, injected by the
; compiler from the block's USES clause) and CYD_CALL looks it up in the resident
; dispatch table (EXTERN_DISPATCH, filled by the compiler after placement), then
; performs the banked call: page the callee in, enter it with DE=FLAGS, and page
; the caller's bank back. Composes with nesting because each level saves and
; restores the real $7FFD port on the hardware stack.
;   In:  A = routine index (RT_<name>); args/results travel through FLAGS.
;   Same clobber contract as a script CALL (AF/BC/DE/HL and IX/IY are free).
CYD_CALL:
    ld l, a
    ld h, 0
    ld d, h
    ld e, l             ; DE = index
    add hl, hl          ; HL = index*2
    add hl, de          ; HL = index*3 (3-byte entries)
    ld de, EXTERN_DISPATCH
    add hl, de          ; HL -> [bank, addr_lo, addr_hi]
    ld a, (hl)
    inc hl
    ld e, (hl)
    inc hl
    ld d, (hl)          ; A = bank, DE = callee address
    IFDEF OP_EXTERN_BANKED
    or ROM48KBASIC
    call SET_RAM_BANK   ; page the callee's bank at $C000; A = previous port
    push af             ; save the caller's bank
    ld hl, .cont
    push hl             ; return address for the callee's RET
    push de             ; callee address (target of the RET below)
    ld de, FLAGS
    ret                 ; enter the callee with DE=FLAGS
.cont:
    pop af              ; caller's previous port
    call SET_RAM_BANK   ; page the caller's bank back
    ret
    ELSE
    ld hl, .cont        ; 48k: callee is resident, call it directly
    push hl
    push de
    ld de, FLAGS
    ret
.cont:
    ret
    ENDIF
    ENDIF                   ; UNUSED_CYD_CALL

    IFNDEF UNUSED_SYSCALL
; CYD_SYSCALL: numbered gateway to curated engine services (print a character,
; read a key, ...), callable from a native routine. The id indexes SVC_TABLE and
; the selected service runs and returns to CYD_SYSCALL's caller. Only ONE address
; is injected into cyd_abi.inc (CYD_SYSCALL); the ids (SVC_*) are a stable numeric
; contract, so author routines survive an interpreter rewrite without recompiling
; against internals that move.
;   In:  A = service id (SVC_*); further args in registers, per service.
CYD_SYSCALL:
    add a, a                ; id * 2 (2-byte table entries)
    push de                 ; preserve the caller's DE (may carry a service arg)
    ld l, a
    ld h, 0
    ld de, SVC_TABLE
    add hl, de
    ld a, (hl)
    inc hl
    ld h, (hl)
    ld l, a                 ; HL = service routine address
    pop de
    jp (hl)                 ; tail-call the service; its RET returns to the caller

SVC_TABLE:
    DW _SVC_PRINT_CHAR      ; SVC_PRINT_CHAR = 0
    DW _SVC_WAIT_KEY        ; SVC_WAIT_KEY   = 1
    DW _SVC_INKEY           ; SVC_INKEY      = 2

; SVC_PRINT_CHAR: print one character at the cursor (advances it, honours the
; current ink/paper/window). In: E = character code.
_SVC_PRINT_CHAR:
    ld a, e
    jp PUT_VAR_CHAR

; SVC_WAIT_KEY: wait for a debounced keypress. Out: A = key code.
_SVC_WAIT_KEY:
    ld d, HIGH FLAGS
    xor a                   ; A = 0 -> wait mode
    jp INKEY_SELECT_WAIT_MODE

; SVC_INKEY: read a key without waiting. Out: A = key code (0 if none).
_SVC_INKEY:
    ld d, HIGH FLAGS
    ld a, 1                 ; A <> 0 -> no-wait mode
    jp INKEY_SELECT_WAIT_MODE
    ENDIF                   ; UNUSED_SYSCALL
    ENDIF                   ; UNUSED_OP_EXTERN
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
    IFNDEF UNUSED_OP_READ
    DW OP_READ
    ENDIF
    IFDEF UNUSED_OP_READ
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
    IFNDEF UNUSED_OP_RESTORE
    DW OP_RESTORE
    ENDIF
    IFDEF UNUSED_OP_RESTORE
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_DATAEND
    DW OP_DATAEND
    ENDIF
    IFDEF UNUSED_OP_DATAEND
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
    IFNDEF UNUSED_OP_POP_VAL_OPTION
    DW OP_POP_VAL_OPTION
    ENDIF
    IFDEF UNUSED_OP_POP_VAL_OPTION
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_WINDOW
    DW OP_WINDOW
    ENDIF
    IFDEF UNUSED_OP_WINDOW
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_CHARSET
    DW OP_CHARSET
    ENDIF
    IFDEF UNUSED_OP_CHARSET
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SKIP_ARRAY
    DW OP_SKIP_ARRAY
    ENDIF
    IFDEF UNUSED_OP_SKIP_ARRAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_VAL_ARRAY
    DW OP_PUSH_VAL_ARRAY
    ENDIF
    IFDEF UNUSED_OP_PUSH_VAL_ARRAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_POP_VAL_ARRAY
    DW OP_POP_VAL_ARRAY
    ENDIF
    IFDEF UNUSED_OP_POP_VAL_ARRAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_LEN_ARRAY
    DW OP_PUSH_LEN_ARRAY
    ENDIF
    IFDEF UNUSED_OP_PUSH_LEN_ARRAY
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_SET_KEMPSTON
    DW OP_SET_KEMPSTON
    ENDIF
    IFDEF UNUSED_OP_SET_KEMPSTON
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_PUSH_KEMPSTON
    DW OP_PUSH_KEMPSTON
    ENDIF
    IFDEF UNUSED_OP_PUSH_KEMPSTON
    DW ERROR_NOP
    ENDIF
    IFNDEF UNUSED_OP_EXTERN
    DW OP_EXTERN
    ENDIF
    IFDEF UNUSED_OP_EXTERN
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

    

