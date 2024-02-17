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
;------------------------------

INIT_WIN:
    ld de, PRT_INTERVAL
    ld bc, .end_data-.data
    ld hl, .data
    ldir
    jp CLEAR_WIN
.data:
    DEFW 1
    DEFB 0
    DEFB 0
    DEFB 0
    DEFB 0
    DEFB 255
    DEFB 23
.end_data:

; The border color is on A
; Set C on error
BORDER:
    cp $08
    jr nc, .t2
    out ($FE), A 	;The 'OUT' instruction is then used to set the border colour.
    rlca 	        ;The parameter is then multiplied by eight.
    rlca
    rlca
    bit 5,A 	    ;Is the border colour a 'light' colour?
    jr nz, .t1 	    ;Jump if so (the INK colour will be black).
    xor $07 	    ;Change the INK colour to white.
.t1: 
    ld (BORDCR),a 	;Set the system variable (BORDCR) as required and return.
    or a
    ret
.t2:
    scf
    ret

;
; Set INK value
;
; Sets the INK color passed in A register in the ATTR_T variable
INK_TMP:
    ld de, ATTR_T
    jr .SET_INK
!INK:
    ld de, ATTR_P
.SET_INK:
    cp 8
    jr nz, .SET_INK2
    inc de ; Points DE to MASK_T or MASK_P
    ld a, (de)
    or 7 ; Set bits 0,1,2 to enable transparency
    ld (de), a
    ret
.SET_INK2:
    ; Another entry. This will set the ink color at location pointer by DE
    and 7	; # Gets color mod 8
    ld b, a	; Saves the color
    ld a, (de)
    and $F8 ; Clears previous value
    or b
    ld (de), a
    inc de ; Points DE to MASK_T or MASK_P
    ld a, (de)
    and 0F8h ; Reset bits 0,1,2 sign to disable transparency
    ld (de), a ; Store new attr
    ret

; Sets the PAPER color passed in A register in the ATTR_T variable
PAPER_TMP:
    ld de, ATTR_T
    jr .SET_PAPER
; Set Paper value
!PAPER:
    ld de, ATTR_P
.SET_PAPER:
    cp 8
    jr nz, .SET_PAPER2
    inc de
    ld a, (de)
    or $38
    ld (de), a
    ret
    ; Another entry. This will set the paper color at location pointer by DE
.SET_PAPER2:
    and 7	; # Remove
    rlca
    rlca
    rlca		; a *= 8
    ld b, a	; Saves the color
    ld a, (de)
    and $C7 ; Clears previous value
    or b
    ld (de), a
    inc de ; Points to MASK_T or MASK_P accordingly
    ld a, (de)
    and $C7  ; Resets bits 3,4,5
    ld (de), a
    ret


; Sets the BRIGHT flag passed in A register in the ATTR_T variable
BRIGHT_TMP:
    ld hl, ATTR_T
    jr .SET_BRIGHT
!BRIGHT:
    ld hl, ATTR_P
.SET_BRIGHT:
    ; Another entry. This will set the bright flag at location pointer by DE
    cp 8
    jr z, .IS_TR
    ; # Convert to 0/1
    or a
    jr z, .IS_ZERO
    ld a, $40
.IS_ZERO:
    ld b, a	; Saves the color
    ld a, (hl)
    and $BF ; Clears previous value
    or b
    ld (hl), a
    inc hl
    res 6, (hl)  ;Reset bit 6 to disable transparency
    ret
.IS_TR:  ; transparent
    inc hl ; Points DE to MASK_T or MASK_P
    set 6, (hl)  ;Set bit 6 to enable transparency
    ret


; Sets the FLASH flag passed in A register in the ATTR_T variable
FLASH_TMP:
    ld hl, ATTR_T
    jr .SET_FLASH
!FLASH:
    ld hl, ATTR_P
.SET_FLASH:
    ; Another entry. This will set the flash flag at location pointer by DE
    cp 8
    jr z, .IS_TR
    ; # Convert to 0/1
    or a
    jr z, .IS_ZERO
    ld a, $80
.IS_ZERO:
    ld b, a	; Saves the color
    ld a, (hl)
    and $7F ; Clears previous value
    or b
    ld (hl), a
    inc hl
    res 7, (hl)  ;Reset bit 7 to disable transparency
    ret
.IS_TR:  ; transparent
    inc hl ; Points DE to MASK_T or MASK_P
    set 7, (hl)  ;Set bit 7 to enable transparency
    ret


;------------------------------------------------------------------------
SET_MARGINS:
    push ix
    ld ix, 0
    add ix, sp
    ld hl, 0
    push hl
    ld a, 32
    cp (ix+9)
    jp nc, .tmp1
    ld (ix+9), 32
.tmp1:
    ld a, 24
    cp (ix+11)
    jp nc, .tmp3
    ld (ix+11), 24
.tmp3:
    ld a, (ix+9)
    or a
    jp nz, .tmp5
    ld (ix+9), 1
.tmp5:
    ld a, (ix+11)
    or a
    jp nz, .tmp7
    ld (ix+11), 1
.tmp7:
    ld a, 31
    cp (ix+5)
    jp nc, .tmp9
    ld (ix+5), 31
.tmp9:
    ld a, 23
    cp (ix+7)
    jp nc, .tmp11
    ld (ix+7), 23
.tmp11:
    ld a, (ix+5)
    add a, a
    add a, a
    add a, a
    ld (MIN_X), a
    ld a, (ix+7)
    ld (MIN_Y), a
    ld a, (ix+9)
    dec a
    add a, a
    add a, a
    add a, a
    ld (ix+9), a
    ld a, (MIN_X)
    ld l, a
    push hl
    ld a, (ix+9)
    ld l, a
    ex de, hl
    pop hl
    add hl, de
    ld (ix-2), l
    ld (ix-1), h
    ex de, hl
    ld hl, 255
    or a
    sbc hl, de
    jp nc, .tmp13
    ld (ix-2), 255
    ld (ix-1), 0
.tmp13:
    ld l, (ix-2)
    ld a, l
    ld (MAX_X), a
    dec (ix+11)
    ld a, (MIN_Y)
    ld l, a
    ld h, 0
    push hl
    ld a, (ix+11)
    ld l, a
    ex de, hl
    pop hl
    add hl, de
    ld (ix-2), l
    ld (ix-1), h
    ex de, hl
    ld hl, 24
    or a
    sbc hl, de
    jp nc, .tmp15
    ld (ix-2), 24
    ld (ix-1), 0
.tmp15:
    ld l, (ix-2)
    ld h, (ix-1)
    ld a, l
    ld (MAX_Y), a
    ld a, (MIN_X)
    ld (POS_X), a
    ld a, (MIN_Y)
    ld (POS_Y), a
    ld sp, ix
    pop ix
    exx
    pop hl
    pop bc
    pop bc
    pop bc
    ex (sp), hl
    exx
    ret


SET_CURSOR:
    push ix
    ld ix, 0
    add ix, sp
    ld hl, 0
    push hl
    push hl
    ld a, 31
    cp (ix+5)
    jp nc, .tmp17
    ld (ix+5), 31
.tmp17:
    ld a, 23
    cp (ix+7)
    jp nc, .tmp19
    ld (ix+7), 23
.tmp19:
    ld a, (ix+5)
    add a, a
    add a, a
    add a, a
    ld (ix+5), a
    ld l, a
    push hl
    ld a, (MIN_X)
    ld l, a
    ex de, hl
    pop hl
    add hl, de
    ld (ix-2), l
    ld (ix-1), h
    ld d, h
    ld e, l
    ld a, (MAX_X)
    ld l, a
    ld h, 0
    or a
    sbc hl, de
    jp nc, .tmp21
    ld a, (MIN_X)
    ld l, a
    ld h, 0
    ld (ix-2), l
    ld (ix-1), h
.tmp21:
    ld a, (ix+7)
    ld l, a
    ld h, 0
    push hl
    ld a, (MIN_Y)
    ld l, a
    ex de, hl
    pop hl
    add hl, de
    ld (ix-4), l
    ld (ix-3), h
    ld d, h
    ld e, l
    ld a, (MAX_Y)
    ld l, a
    ld h, 0
    or a
    sbc hl, de
    jp nc, .tmp23
    ld a, (MIN_Y)
    ld l, a
    ld h, 0
    ld (ix-4), l
    ld (ix-3), h
.tmp23:
    ld l, (ix-2)
    ld a, l
    ld (POS_X), a
    ld l, (ix-4)
    ld h, (ix-3)
    ld a, l
    ld (POS_Y), a
    ld sp, ix
    pop ix
    exx
    pop hl
    pop bc
    ex (sp), hl
    exx
    ret


;------------------------------------------------------------------------
GET_CHARACTER_POINTER:
PROC
    ld de, (CHARSET_ADDR)
    ld l, a
    ld h, 0
    add hl, hl     ; hl <= 2 * hl
    add hl, hl     ; hl <= 4 * hl
    add hl, hl     ; hl <= 8 * hl
    add hl, de     ; Pointer to character
    ret

GET_CHARACTER_WIDTH:
    ld bc, (CHARSET_WIDTHS_ADDR)
    add a, c
    ld c, a
    adc a, b
    sub c
    ld b, a       ; bc = bc + a
    ld a, (bc)
    ret

;    Entry param : A = Character width of character
;    Output: H = Y for next char
;            L = X for next char
;            D = Y for printing this char
;            E = X for printing this char
UPDATE_POS:
    ld (.s_mod),a ; Self modificable core, store character width on an instruction
    ld hl, (POS_X) ; h = POS_Y, l = POS_X
    ld d, h        ; Save old position in DE
    ld e, l        ; d = POS_Y, e = POS_X 
    add a, l       ; X = X + Char Width
    jr c, .new_l    ; detect screen overflow
    ld l, a        ; Set L = X + Char Width
    ld a, (MAX_X)  ; Set A = MAX_X
    cp l           ; MAX_X-X
    jr nc, .upd_pos ; MAX_X >= X
.new_l:
    ld a, 1
    ld (SKIP_SPACES), a ;NEWLINE DONE
    ld bc, (MIN_X) ; b = MIN_Y, c = MIN_X
    ld l, c        ; Set X = MIN_X
    inc h          ; Increment Y
    ld a, (MAX_Y)  ; Set A = MAX_Y
    cp h           ; MAX_Y-Y
    jr nc, .upd_pos2; MAX_Y >= Y
    ;cleaning the screen...
    call CLEAR_WIN
    ld hl, (POS_X)
    jr .upd_pos3
.upd_pos2:
    jr nz, .upd_pos3
    ld a, (WAIT_NEW_SCREEN)
    or a
    jr z, .upd_pos3
    call WAIT_NEXT_PAGE
    ld hl, (POS_X)
.upd_pos3:
    ld d, h        ; Save new position in DE
    ld e, l
.s_mod+1:          ; If we jump to next line, the next pos_x must be updated
    ld a, 0-0      ; The parameter is self_modified here
    add a, l       ; add the width of the character to the next position
    ld l, a        ; Update POS_X
    ; POS_X should never be zero in this case
.upd_pos:
    ld (POS_X), hl ; Update next position
.tmp_ret:
    ret
ENDP

PUT_VAR_CHAR:

    call GET_CHARACTER_POINTER
    push hl        ; Store address to character

    call GET_CHARACTER_WIDTH
    push af        ; Store character width

    cp 8
    jr c, .t5      ;Width < 8
    jr nz, .t6     ;width > 8
    pop af
    call ADJUST_CHAR_POS
    pop hl
    jp PUT_8X8_CHAR
.t6:
    ld a, 4         ;Character too big
    jp SYS_ERROR

.t5:
    call UPDATE_POS
    ; d = POS_Y, e = POS_X

    ld a, e        ; Grab our pixel number
    and 7          ; And do mod 8 [So now we have how many pixels into the character square we're starting at]
    push af        ; Save A (pixels into character square)
    exx
    ld d, a        ; d' -> pixels into character square
    ld hl, .MASK
    add a, l
    ld l, a
    adc a, h
    sub l
    ld h, a        ; hl = hl + a
    ld a, (hl)
    ld b, a
    cpl            ; Complementing mask bits
    ld c, a        ; b' -> mask, c' -> complemented mask
    ld a, d        ; restore A on D
    or a           ; Set Z flag if is zero
    ex af, af'     ; Saving in AF' the displacement
    exx

    ;Condiciones para NO dibujar el siguiente caracter
    ;- Su posición dentro del + ancho del caracter es menor que 8
    ;- si no, si el siguiente carácter es X > 255
    ;- si no, si el siguiente carácter es X > MAX_W

    pop af         ; Restore pos_x in char on A
    pop bc         ; restore char size on B
    add a, b       ; pos_x_in_char + size
    cp 8           ; It more than 7? ((a - 8) = (A >= 8)) 
    rla            ; Carry to A ( C = A < 8)
    and 1          ; Discard 7 MSB bits
    ld c, a        ; Saving condition in C
    ld a, b        ; Char size on A
    add a, e       ; Add charsize + posX
    rl c           ; If C it most than the screen, add condition doing RL on C
    ld b, a        ; Storing charsize + posX on b
    ld a, (MAX_X)  ; Storing MAX_X on A
    cp b           ; MAX_X-X -> NC = MAX_X >= x
    rl c           ; Add the condition on C
    ld a, c        ; COndition on A again
    ; bit 2 enabled if pos_x_in_char + size >= 8
    ; bit 1 enabled if pos_x + size > 255
    ; bit 0 enabled if pos_x + size > MAX_X
    ld (.s_mod2), a
    ld (.s_mod3), a
    ; This should be unnecesary with a variable instead of
    ; self-modified code, but this way is a bit faster because
    ; read of the variable is done 16 times.

    ld a, e        ; Get x pos
    ld l, a        ; put x into L
    srl a          ; divide by 2
    srl a          ; divide by another 2 (/4)
    srl a          ; divide by another 2 (/8)
    ld e, a        ; Put the result in e (Since the screen has 8 pixel bytes, pixel/8 = which char pos along our first pixel is in)

    ld a, d        ; Get y pos into A'
    sra a          ; Divide by 2
    sra a          ; Divide by another 2 (/4 total)
    sra a          ; Divide by another 2 (/8) [Gives us a 1/3 of screen number]
    add a, 88      ; Add in start of screen attributes high byte
    ld h, a        ; And put the result in H
    ld a, d        ; grab our Y co-ord again
    and 7          ; Mod 8 (why? *I thought to give a line in this 1/3 of screen, but we're in attrs here)
    rrca           ;
    rrca
    rrca           ; Bring the bottom 3 bits to the top - Multiply by 32
      ; (since there are 32 bytes across the screen), here, in other words. [Faster than 5 SLA instructions]
    add a, e       ; add in our x coordinate byte to give us a low screen byte
    ld l, a        ; Put the result in L. So now HL -> screen byte at the top of the character

    ld a, (ATTR_P)   ; ATTR P     Permanent current colours, etc (as set up by colour statements).
    ld e, a          ; Copy ATTR into e
    ld (hl), e       ; Drop ATTR value into screen


.s_mod2+1:
    ld a, 0-0        ; self_modified
    or a             ; test if value is zero
    jr nz, .t1        ; if not zero, do not process next character
    inc hl           ; Go to next position along
    ld (hl), e       ; 63446 Must be yes - we're setting the attributes in the next square too.
    dec hl           ; Back up to last position

.t1: 
    ld a, d          ; Y Coord into A'
    and 248          ; Turn it into 0,8 or 16. (y=0-23)
    add a, 64        ; Turn it into 64,72,80  [40,48,50 Hex] for high byte of screen pos
    ld h, a          ; Stick it in H (we have screen coords now)
    push hl          ; Save it
    exx              ; Swap registers
    pop hl           ; Put it into HL' the screen pointer, b -> mask, c -> pixels into character square
    exx              ; Swap Back

    pop hl           ; Restore pointer to char
    ex af, af'       ; Recover displacement to the right
    jp nz, .t2        ; test if is zero
    ld a, 8          ; In that case, set to 8
.t2: 
    ld d, a          ; D = num of pixel rotations to do

    ld b, 8

.loop1:
    ld a, (hl)       ; get char line pxl
    inc hl           ; next char line
    ld c, b          ; Save line counter on c
    ld b, d          ; Set on b the displacement to the right

.loop2:
    rrca             ; Rotate a
    djnz .loop2

    exx
    ;HL' the screen pointer, b' -> mask, c' -> mask complemented
    ld d, a
    and c
    ld e, a         ; Get the left part of the rotated character
    ld a, b
    and d
    ld d, a         ; Get the right part of the rotated character
;HL' -> the screen pointer, b' -> mask, c' -> mask complemented
;d' -> left char line data, e' -> right char line data
    ld a, c         ; Get inverted mask
    and (hl)        ; Mask screen
    or d            ; or with char
    ld (hl), a      ; To screen again

.s_mod3+1:
    ld a, 0-0       ; Self-modified to check if next char must be written
    or a            ; Check if right mask is zero
    jr nz, .t3       ; Next char doesn't need update
    inc l           ; next char
    ld (hl), e      ; To screen
    dec l           ; Return to previous char
.t3:
    inc h           ; next char line
    exx
    ld b, c         ; Restore on b the line counter
    djnz .loop1

    ; Typing pause
    ld hl, (PRT_INTERVAL)
.t4: dec hl
    ld a, h
    or l
    ret z
    jr .t4

.MASK:
    DEFB %11111111  ;CPL =>  %00000000
    DEFB %01111111  ;CPL =>  %10000000
    DEFB %00111111  ;CPL =>  %11000000
    DEFB %00011111  ;CPL =>  %11100000
    DEFB %00001111  ;CPL =>  %11110000
    DEFB %00000111  ;CPL =>  %11111000
    DEFB %00000011  ;CPL =>  %11111100
    DEFB %00000001  ;CPL =>  %11111110


; Carriage return
; Uses: A & C
CRLF:
    ld a, (MIN_X)
    ld (POS_X), a
    ld a, (POS_Y)
    inc a
    ld c, a
    ld a, (MAX_Y)
    cp c              ; MAX_Y-Y
    jr nc, .t1        ; MAX_Y >= Y
    jp CLEAR_WIN
.t1:
    jr nz, .t2
    ld a, (WAIT_NEW_SCREEN)
    or a
    jp nz, WAIT_NEXT_PAGE   ; MAX_Y = Y
.t2:
    ld a, c
    ld (POS_Y), a
    ret

CENTER:
    ld a, (MIN_X)
    ld c, a
    ld a, (MAX_X)
    sub c
    srl a
    add a, c
    ld (POS_X), a
    ret

WAIT_NEXT_PAGE:
    call CENTER
    ld de, (POS_X)
    inc d
.loop:
    call INKEY
    cp 13
    jr z, .keyp
    cp 32
    jr z, .keyp

    ld a, (CYCLE_OPTION)
    push de
    push de
    add a, WAIT_TO_KEY_BULLET
    call GET_CHARACTER_POINTER
    pop de
    halt
    call PUT_8X8_CHAR
    pop de
    jr .loop
.keyp:
    call INKEY
    or a
    jr nz, .keyp
    jp CLEAR_WIN 


PRINT_SELECTED_OPTION_BULLET:
    push af
    ld bc, (POS_X)
    ld a, (SELECTED_OPTION)
    ld l, a
    ld h, 0
    ld de, OPTIONS_POS
    add hl, hl
    add hl, de
    ld e, (hl)
    inc hl
    ld d, (hl)
    ld (POS_X), de
    pop af
    push de
    call GET_CHARACTER_POINTER
    pop de
    call PUT_8X8_CHAR
    ld (POS_X), bc
    ret

ANIMATE_OPTION_BULLET:
    ld a, (CYCLE_OPTION)
    add a, SELECTED_BULLET
    halt
    call PRINT_SELECTED_OPTION_BULLET
    ret

; HL <- Pointer to the null ended string
PRINT_STR:
    ld a, l
    or h
    ret z          ; Exit if null pointer

.loop1:
    ld a, (hl)
    or a
    ret z         ; Exit if null character found
    cp 13         ; EOL
    jr z, .eol
    cp 10         ; CR
    jr z, .eol
    cp 32         ; Space
    jr z, .space

    ; search for end of current word
    ld d, h
    ld e, l       ; Store current pointer on D
    ld c, 0       ; size count
.loop2:
    ld a, (de)    ; get next character
    or a
    jr z, .end_loop2
    cp 13
    jr z, .end_loop2
    cp 10
    jr z, .end_loop2
    cp 32
    jr z, .end_loop2
    push bc
    call GET_CHARACTER_WIDTH
    pop bc
    add a, c
    ld c, a
    inc de        ; Increment counter 
    jp .loop2
.end_loop2:
    ld a, (POS_X)
    ld b, a
    ld a, (MAX_X)
    sub b           ; MAX_X - POS_X
    cp c            ; Width - word size
    push hl
    push de
    call c, CRLF    ; If the word doesn't fit, do a carriage return
    pop de
    pop hl

    ;Print rest of the word
.loop3:
    ld a, (hl)
    or a
    ret z         ; Exit if null character found
    cp 10         ; CR
    jr z, .eol
    cp 13         ; EOL
    jr z, .eol
    cp 32         ; Space
    jr z, .space
    push hl
    call PUT_VAR_CHAR
    xor a
    ld (SKIP_SPACES), a      ; Disable space skip after a non-space character
    pop hl
    inc hl
    jp .loop3

.space:     
    ld a, (SKIP_SPACES)
    or a
    jr nz, .skip_space   ; Space is not printed in this case
    push de              ; Reserve space only
    push bc
    push hl
    ld a, 32
    call PUT_VAR_CHAR
    ld a, (SKIP_SPACES)  ;Skip space after auto-carriage return
    or a
    jr z, .no_backstep ; Space is not printed in this case
    ld a, (MIN_X)
    ld (POS_X), a
.no_backstep:    
    pop hl
    pop bc
    pop de
.skip_space:
    inc hl
    jp .loop1

.eol:
    push de                   ; Reserve space only
    push bc
    push hl
    call CRLF
    xor a                    ; Disable space skip after a EOL
    ld (SKIP_SPACES), a
    pop hl
    pop bc
    pop de
    inc hl
    jp .loop1


PRINT_TOKEN_STR:
    xor a
    ld de, TEXT_BUFFER
    ld (de), a
.loop3:
    ld c, (hl)
    inc hl
    ld a, 255
    sub c
    ld c, a                   ; Decrypting character
    and $80                   ; Test if is token
    jr z, .not_token          ; if c >= 128, it is a token

    ld a, $7F                ; Mask for token
    and c                    ; Recovering character
    push hl
    push de
;----------------------------------------------------------
    ; Get token
    ld de, (TOKENS_ADDR)
    or a
    jr z, .token_found
    ld b, a                   ; B as counter
.loop1:
    ld a, (de)
    inc de
    cp 128
    jr c, .loop1               ; A < 128 don't decrement b
    djnz .loop1                ; Decrease B IF A > 127
.token_found:
    ld hl, TOKEN_BUFFER        ;HL = ptr to token buffer
    push hl
.loop2:
    ld a, (de)
    ld c, a                   ; C character
    and $7F
    ld (hl), a
    inc de
    inc hl
    ld a, c                  ;Loop if c < 127
    cp 127
    jr c, .loop2
    ld (hl), 0               ;Null at the end...
;----------------------------------------------------------
    pop hl                   ;Restore start token buffer
    pop de                   ;restore text buffer
    ; hl has the token buffer;
    ; de has the text buffer
.loop4:
    ld a, (hl)
    inc hl
    or a
    jr z, .end_loop4
    ld (de), a
    inc de
    cp 32
    jr z, .end_token
    cp 10
    jr z, .end_token
    cp 13
    jr nz, .loop4
.end_token:                  ; Print current text buffer
    call PRINT_STR_BUFFER
    jr .loop4
.end_loop4:
    pop hl                  ; Restoring string pointer on HL
    jp .loop3                ; Next iteration
;-------------------------
.not_token:
    ld a, c
    ld (de), a
    inc de
    cp 32
    jr z, .end_word
    cp 10
    jr nz, .end_str
    dec de
.end_word:
    push bc
    call PRINT_STR_BUFFER
    pop bc
.end_str:
    ld a, $0A               ; = 255 - 0xf5
    cp c
    ret z
    jp .loop3            ; char <> (255 - 0xf5)
PRINT_STR_BUFFER:
    xor a                   ; A = 0
    ld (de), a              ; Set the final mark on text buffer
    ld de, TEXT_BUFFER
    ex de, hl               ; Put the thex buffer on hl
    push hl
    push de
    call PRINT_STR
    pop hl                  ; Restore register on its original positions
    pop de
    ret

; Get the number in A as text in DE
; With C set, print leading zeroes
PRINT_A_BYTE:
    ld h, 0
    ld l, a

; Get the number in HL as text in DE
; With C set, print leading zeroes
PRINT_HL_WORD:
    ex af, af'                ;Save carry
    ld de, TEXT_BUFFER
    push de                   ;Save start of text buffer address on stack
    call CONV_HL_TO_STR
    xor a
    ld (de), a                ; Set NULL at the end of the string
    pop hl                    ; Restore start buffer on HL
    ex af, af'                ; Restore carry
    jp c, PRINT_STR           ; On carry, leave any leading zeroes.
    dec de                    ; Step over NULL
    dec de                    ; Step over first digit
    ld b, 4                   ; Number of digits
.loop1:
    ld a, (de)                ; Get digit
    cp $30                    ; is Zero char
    jr z, .end_loop1          ; In that case, we leave
    dec de                    ; Advance pointer
    djnz .loop1               ; Iterate over all digits
    jp PRINT_STR              ; Full number, so returns HL
.end_loop1:
    inc de                    ; Restore to the first not Zero digit
    ex de, hl                 ; Move DE to HL
    jp PRINT_STR              ; Print number

CONV_HL_TO_STR:
    ld bc, -10000
    call .one
    ld bc, -1000
    call .one
    ld bc, -100
    call .one
    ld bc, -10
    call .one
    ld c, -1
.one
    ld a, $30-1    ;"0"-1
.two
    inc a
    add hl, bc
    jr c, .two
    push bc
    push af
    ld a, b
    cpl
    ld b, a
    ld a, c
    cpl
    ld c, a
    inc bc
    call c, .carry
    pop af
    add hl, bc
    pop bc
    ld (de), a
    inc de
    ret
.carry:
    dec bc
    ret

ADJUST_CHAR_POS:
    ld a, (POS_X)
    and 7
    jr z, 1f
    ld c, a
    ld a, 8
    sub c
    call UPDATE_POS       ;Advance to match 8x8 character
1:  ld a, 8
    jp UPDATE_POS
    ; d = POS_Y, e = POS_X

ADJUST_CHAR_POS_NO_ADVANCE:
    ld a, (POS_X)
    and 7
    jr z, 1f
    ld c, a
    ld a, 8
    sub c
    jp UPDATE_POS       ;Advance to match 8x8 character
1:  ld a, 0
    jp UPDATE_POS
    ; d = POS_Y, e = POS_X



; hl character input
; d = POS_Y, e = POS_X
PUT_8X8_CHAR:
    push hl
    srl e
    srl e
    srl e
    ld a, d
    rrca
    rrca
    rrca
    and 3
    add a, $58
    ld h, a
    ld a, d
    and 7
    rrca
    rrca
    rrca
    add a, e
    ld l, a
    ld a, (ATTR_P)
    ld (hl), a
    ld a, d
    and $18
    add a, $40
    ld h, a
    ld a, d
    and 7
    rrca
    rrca
    rrca
    add a, e
    ld l, a
    pop de
    REPT 8
    ld a, (de)
    inc de
    ld (hl), a
    inc h
    ENDR
    ret
;-----------------------------------------------------
CLEAR_WIN:
    push ix
    ld ix, 0
    add ix, sp
    ld hl, 0
    push hl
    push hl

    ld bc, (MIN_X)
    ld de, (MAX_X)
    ld (POS_X), bc         ;set to origin of window

    ld (ix-2), b           ; YPOS

    srl c
    srl c
    srl c

    srl e
    srl e
    srl e

    ld (ix-1), c          ; XPOS

    ld a, e
    sub c
    inc a
    ld (ix-3), a          ;Width

    ld a, d
    sub b
    ld d, a
    inc a
    ld (ix-4), a        ; Height

    ld      a,(ix-2)   ; ypos
    rrca
    rrca
    rrca               ; Multiply by 32
    ld      l,a        ; Pass to L
    and     3          ; Mask with 00000011
    add     a,88       ; 88 * 256 = 22528 - start of attributes. Change this if you are working with a buffer or somesuch.
    ld      h,a        ; Put it in the High Byte
    ld      a,l        ; We get y value *32
    and     224        ; Mask with 11100000
    ld      l,a        ; Put it in L
    ld      a,(ix-1)   ; xpos
    add     a,l        ; Add it to the Low byte
    ld      l,a        ; Put it back in L, and we're done. HL=Address.

    push HL            ; save address
    LD A, (ATTR_P)     ; attribute
    LD DE,32
    LD c,(ix-4)       ; height

.BLPaintHeightLoop:
    LD b,(ix-3)        ; width

.BLPaintWidthLoop:
    LD (HL),a          ; paint a character
    INC L              ; Move to the right (Note that we only would have to inc H if we are crossing from the right edge to the left, and we shouldn't be needing to do that)
    DJNZ .BLPaintWidthLoop

.BLPaintWidthExitLoop:
    POP HL             ; recover our left edge
    DEC C
    JR Z, .BLPaintHeightExitLoop

    ADD HL,DE          ; move 32 down
    PUSH HL            ; save it again
    JP .BLPaintHeightLoop

.BLPaintHeightExitLoop:

    ld b,(ix-1)     ; get x value
    ld c,(ix-2)     ; get y value

    ld a, c         ; Set HL to screen byte for this character.
    and 24
    or 64
    ld h, a
    ld a, c
    and 7
    rra
    rra
    rra
    rra
    add a, b
    ld l, a

    ld b,(ix-4)     ; get height
    ld c,(ix-3)     ; get width

.clearbox_outer_loop:
    xor a
    push bc       ; save height.
    push hl       ; save screen address.
    ld d, 8       ; 8 rows to a character.

.clearbox_mid_loop:
    ld e,l        ; save screen byte lower half.
    ld b,c        ; get width.

.clearbox_inner_loop:
    ld (hl), a    ; write out a zero to the screen.

    inc l         ; go right.
    djnz .clearbox_inner_loop    ; repeat.

    ld l,e        ; recover screen byte
    inc h         ; down a row

    dec d
    jp nz, .clearbox_mid_loop  ; repeat for this row.

    pop hl        ; get back address at start of line
    pop bc        ; get back char count.

    ld a, 32      ; Go down to next character row.
    add a, l
    ld l, a
    jp nc, .clearbox_row_skip

    ld a, 8
    add a, h
    ld h, a

.clearbox_row_skip:
    djnz .clearbox_outer_loop
    ld sp, ix
    pop ix
    xor a
    ld (NUM_OPTIONS), a          ;Clear options.
    ret


INKEY:
    ;push hl
    ;push de
    ;push bc
    exx

    call KEY_SCAN
    jp nz, .empty_inkey

    call KEY_TEST
    jp nc, .empty_inkey

    dec d	; D is expected to be FLAGS so set bit 3 $FF
    ; 'L' Mode so no keywords.
    ld e, a	; main key to A
    ; C is MODE 0 'KLC' from above still.
    call KEY_CODE ; routine K-DECODE
    ;Keycode on A
    exx
    ret
    ;jr 1f

.empty_inkey:
    xor a
1:
    ;pop bc
    ;pop de
    ;pop hl
    exx
    ret

;' scrolls the window defined by (row, col, width, height) 1 cell up
;WIN_SCROLL_UP:
;    ld bc, (MIN_X)
;    ld de, (MAX_X)
;
;    srl c
;    srl c
;    srl c
;
;    srl e
;    srl e
;    srl e
;
;    ld a, e
;    sub c
;    inc a
;    ex af, af'
;
;    ld a, d
;    sub b
;    ld d, a
;    inc a
;
;    ld e, a
;    ex af, af'
;    ld d, a
;
;
;    ; b=row, c=col
;    ; d=width, e=height
;
;    ld a, e
;    or a
;    ret z
;    or d
;    ret z
;
;    push bc
;    push de
;
;    ld a,b
;    and 18h
;    ld h,a
;    ld a,b
;    and 07h
;    add a,a
;    add a,a
;    add a,a
;    add a,a
;    add a,a
;    add a,c
;    ld l,a   ;HL=top-left window address in bitmap coord
;    ld bc, SCR_PXL
;    add hl, bc
;    ld a,e
;    ld c, d  ; c = width
;    ld d, h
;    ld e, l
;    dec a
;    jr z, .CleanLast
;    add a,a
;    add a,a
;    add a,a
;    ld b, a  ; b = 8 * (height - 1)
;
;    inc h
;    inc h
;    inc h
;    inc h
;    inc h
;    inc h
;    inc h
;    call PIXEL_DOWN
;
;.BucleScans:
;    push bc
;    push de
;    push hl
;    ld b, 0
;    ldir
;    pop hl
;    pop de
;    pop bc
;    call PIXEL_DOWN
;    ex de, hl
;    call PIXEL_DOWN
;    ex de, hl
;    djnz .BucleScans
;
;.CleanLast:
;    ex de,hl
;    pop de
;    ld b, 8
;    ld c, d
;    push de
;
;.CleanLastLoop:
;    push bc
;    push hl
;    ld (hl), 0
;    dec c
;    jr z, .EndCleanScan
;    ld d, h
;    ld e, l
;    inc de
;    ld b, 0
;    ldir
;
;.EndCleanScan:
;    pop hl
;    pop bc
;    inc h
;    djnz .CleanLastLoop
;
;.ScrollAttrs:
;    pop de
;    pop bc
;    ld l,b
;    ld h,0
;    add hl,hl
;    add hl,hl
;    add hl,hl
;    add hl,hl
;    add hl,hl
;    ld a,l
;    add a,c
;    ld l,a
;    ld a,h
;    ld h,a    ;HL=top-left address in attr coords
;    ld bc, SCR_ATT
;    add hl, bc
;    ld b,e
;    dec b
;    ret z
;
;.BucleAttrs:
;    push bc
;    push de
;    push hl
;    ld b,0
;    ld c,d
;    ex de,hl
;    ld hl,32
;    add hl,de
;    ldir
;    pop hl
;    ld de,32
;    add hl,de
;    pop de
;    pop bc
;    djnz .BucleAttrs
;    ret
;;-----------------------------------
;; Pixel Down
;;
;; Adjusts screen address HL to move one pixel down in the display.
;; (0,0) is located at the top left corner of the screen.
;;
;; enter: HL = valid screen address
;; exit : Carry = moved off screen
;;        Carry'= moved off current cell (needs ATTR update)
;;        HL = moves one pixel down
;; used : AF, HL
;PIXEL_DOWN:
;    push de
;    ld de, SCR_PXL
;    or a
;    sbc hl, de
;    inc h
;    ld a,h
;    and $07
;    jr nz, .leave
;    scf         ;  Sets carry on F', which flags ATTR must be updated
;    ex af, af'
;    ld a,h
;    sub $08
;    ld h,a
;    ld a,l
;    add a,$20
;    ld l,a
;    jr nc, .leave
;    ld a,h
;    add a,$08
;    ld h,a
;    cp $19     ; carry = 0 => Out of screen
;    jr c, .leave ; returns if out of screen
;    ccf
;    pop de
;    ret
;.leave:
;    add hl, de ; This always sets Carry = 0
;    pop de
;    ret