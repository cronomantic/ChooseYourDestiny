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

    IFNDEF IS_MLD_DAN
INKEY:
    exx
    call KEY_SCAN
    ld c, $0
    jr nz, .empty_inkey
    call K_TEST
    jr nc, .empty_inkey
    dec d   ; ; +FF to D for 'L' mode (bit 3 set) (it was 0 before)
    ; 'L' Mode so no keywords.
    ld e, a ;  	Key-value to E for decoding.
    ; C is MODE 0 'KLC' from above still.
    call K_DECODE ; routine K-DECODE
    ;Keycode on A
    exx
    ret
.empty_inkey:
    xor a
    exx
    ret
    ENDIF

	IFDEF IS_MLD_DAN
;===========================================================
; ZX Spectrum ROM keyboard routines translation
; Reubicable for sjasmplus
;
; ROM original:
;   0205 KEY TABLES
;   028E KEY_SCAN
;   031E K_TEST
;   0333 K_DECODE
;
;   https://skoolkid.github.io/rom/asm/0205.html
;   https://skoolkid.github.io/rom/asm/028E.html
;   https://skoolkid.github.io/rom/asm/031E.html
;   https://skoolkid.github.io/rom/asm/0333.html
;
;===========================================================

;-----------------------------------------------------------
; KEY TABLE A
;-----------------------------------------------------------

KEYTABLE_A:

    db $42,$48,$59,$36,$35,$54,$47,$56
    db $4E,$4A,$55,$37,$34,$52,$46,$43
    db $4D,$4B,$49,$38,$33,$45,$44,$58
    db $0E,$4C,$4F,$39,$32,$57,$53,$5A
    db $20,$0D,$50,$30,$31,$51,$41


;-----------------------------------------------------------
; KEY TABLE B
;-----------------------------------------------------------

KEYTABLE_B:

    db $E3,$C4,$E0,$E4,$B4,$BC,$BD,$BB
    db $AF,$B0,$B1,$C0,$A7,$A6,$BE,$AD
    db $B2,$BA,$E5,$A5,$C2,$E1,$B3,$B9
    db $C1,$B8


;-----------------------------------------------------------
; KEY TABLE C
;-----------------------------------------------------------

KEYTABLE_C:

    db $7E,$DC,$DA,$5C,$B7,$7B,$7D,$D8
    db $BF,$AE,$AA,$AB,$DD,$DE,$DF,$7F
    db $B5,$D6,$7C,$D5,$5D,$DB,$B6,$D9
    db $5B,$D7


;-----------------------------------------------------------
; KEY TABLE D
;-----------------------------------------------------------

KEYTABLE_D:

    db $0C,$07,$06,$04,$05
    db $08,$0A,$0B,$09,$0F


;-----------------------------------------------------------
; KEY TABLE E
;-----------------------------------------------------------

KEYTABLE_E:

    db $E2,$2A,$3F,$CD,$C8,$CC,$CB,$5E
    db $AC,$2D,$2B,$3D,$2E,$2C,$3B,$22
    db $C7,$3C,$C3,$3E,$C5,$2F,$C9,$60
    db $C6,$3A


;-----------------------------------------------------------
; KEY TABLE F
;-----------------------------------------------------------

KEYTABLE_F:

    db $D0,$CE,$A8,$CA,$D3
    db $D4,$D1,$D2,$A9,$CF


;===========================================================
; KEY_SCAN  (ROM 028E)
;===========================================================

KEY_SCAN_RAM:
    ld l,$2F
    ld de,$FFFF
    ld bc,$FEFE
.KEY_LINE:
    in a,(c)
    cpl
    and $1F
    jr z,.KEY_DONE
    ld h,a
    ld a,l
.KEY_3KEYS:
    inc d
    ret nz
.KEY_BITS:
    sub $08
    srl h
    jr nc,.KEY_BITS
    ld d,e
    ld e,a
    jr nz,.KEY_3KEYS
.KEY_DONE:
    dec l
    rlc b
    jr c,.KEY_LINE
    ld a,d
    inc a
    ret z
    cp $28
    ret z
    cp $19
    ret z
    ld a,e
    ld e,d
    ld d,a
    cp $18
    ret

;===========================================================
; K_TEST  (ROM 031E)
;===========================================================

K_TEST_RAM:
    ld b,d
    ld d,$00
    ld a,e
    cp $27
    ret nc
    cp $18
    jr nz,.K_MAIN
    bit 7,b
    ret nz
.K_MAIN:
    ld hl,KEYTABLE_A
    add hl,de
    ld a,(hl)
    scf
    ret


;===========================================================
; K_DECODE  (ROM 0333)
;===========================================================

K_DECODE_RAM:
    ld a,e
    cp $3A
    jr c,.K_DIGIT
    dec c
    jp m,.K_KLC_LET
    jr z,.K_E_LET
    add a,$4F
    ret
.K_E_LET:
    ld hl,KEYTABLE_B
    inc b
    jr z,.K_LOOK_UP
    ld hl,KEYTABLE_C
.K_LOOK_UP:
    ld d,$00
    add hl,de
    ld a,(hl)
    ret
.K_KLC_LET:
    ld hl,KEYTABLE_E
    bit 0,b
    jr z,.K_LOOK_UP
    bit 3,d
    jr z,.K_TOKENS
    bit 3,(iy+$30)
    ret nz
    inc b
    ret nz
    add a,$20
    ret
.K_TOKENS:
    add a,$A5
    ret
.K_DIGIT:
    cp '0'
    ret c
    dec c
    jp m,.K_KLC_DGT
    jr nz,.K_GRA_DGT
    ld hl,KEYTABLE_F
    bit 5,b
    jr z,.K_LOOK_UP
    cp '8'
    jr nc,.K_8_9
    sub $20
    inc b
    ret z
    add a,$08
    ret
.K_8_9:
    sub $36
    inc b
    ret z
    add a,$FE
    ret
.K_GRA_DGT:
    ld hl,KEYTABLE_D
    cp '9'
    jr z,.K_LOOK_UP
    cp '0'
    jr z,.K_LOOK_UP
    and $07
    add a,$80
    inc b
    ret z
    xor $0F
    ret
.K_KLC_DGT:
    inc b
    ret z
    bit 5,b
    ld hl,KEYTABLE_D
    jr nz,.K_LOOK_UP
    sub $10
    cp $22
    jr z,.K_AT_CHAR
    cp $20
    ret nz
    ld a,'_'
    ret
.K_AT_CHAR:
    ld a,$40    ; ASCII 64 (at-sign) as a number: the at-sign char is the asm-template
                ; delimiter, so a literal one here would break Template.substitute
    ret
;====================================================
INKEY:
    exx
    call KEY_SCAN_RAM
    ld c, $0
    jr nz, .empty_inkey
    call K_TEST_RAM
    jr nc, .empty_inkey
    dec d   ; +FF to D for 'L' mode (bit 3 set) (it was 0 before)
    ; 'L' Mode so no keywords.
    ld e, a ;  	Key-value to E for decoding.
    ; C is MODE 0 'KLC' from above still.
    call K_DECODE_RAM ; routine K-DECODE
    ;Keycode on A
    exx
    ret
.empty_inkey:
    xor a
    exx
    ret
    ENDIF

INKEY_WAIT_ITERATIONS       EQU 10
INKEY_NO_WAIT_ITERATIONS    EQU INKEY_WAIT_ITERATIONS


INKEY_SELECT_WAIT_MODE:
    or a
    jr nz, INKEY_NO_WAIT

INKEY_WAIT:
    push bc
1:  call INKEY
    or a
    jr z, 1b       ;Detect keypress
    ld c, a
    ld b, INKEY_WAIT_ITERATIONS
2:  call INKEY
    or a
    jr z, 2b       ;Detect keypress again
    cp c
    jr nz, 1b      ;Different key, we begin again
    djnz 2b        ;Decrease counter
3:  call INKEY
    or a
    jr nz, 3b       ;Detect key release
    ld a, c
    pop bc
    ret

INKEY_NO_WAIT:
    push bc
1:  call INKEY
    or a
    jr z, .empty_inkey
    ld c, a
    ld b, INKEY_NO_WAIT_ITERATIONS
2:  call INKEY
    or a
    jr z, .empty_inkey
    cp c
    jr nz, 1b      ;Different key, we begin again
    djnz 2b        ;Decrease counter
    ld a, c        ;Returns key pressed
.empty_inkey:
    pop bc
    ret

KEYPRESS_RIGHT EQU %00000001
KEYPRESS_LEFT  EQU %00000010
KEYPRESS_DOWN  EQU %00000100
KEYPRESS_UP    EQU %00001000
KEYPRESS_FIRE  EQU %00010000

;
; Keypress format:
;   xxxKUDLR

INKEY_MENU:
    push bc
    xor a
    ld c, a
    call INKEY
.right:
    cp $09  ; cursor right
    jr z, .right_ok
    cp 'p'
    jr nz, .left
.right_ok:
    ld b, a
    ld a, c
    or KEYPRESS_RIGHT
    ld c, a
    ld a, b
.left:
    cp $08  ; cursor left
    jr z, .left_ok
    cp 'o'
    jr nz, .down
.left_ok:
    ld b, a
    ld a, c
    or KEYPRESS_LEFT
    ld c, a
    ld a, b
.down:
    cp $0A  ; cursor down
    jr z, .down_ok
    cp 'a'
    jr nz, .up
.down_ok:
    ld b, a
    ld a, c
    or KEYPRESS_DOWN
    ld c, a
    ld a, b
.up:
    cp $0B  ; cursor up
    jr z, .up_ok
    cp 'q'
    jr nz, .selected
.up_ok:
    ld b, a
    ld a, c
    or KEYPRESS_UP
    ld c, a
    ld a, b
.selected:
    cp ' '
    jr z, .selected_ok
    cp 'm'
    jr z, .selected_ok
    cp 13
    jr nz, .kempston
.selected_ok:
    ld a, KEYPRESS_FIRE
    or c
    ld c, a
.kempston:
    call KEMPSTON
    or c
    pop bc
    ret

KEMPSTON:
    ld a, (KEMPSTON_VALUE)
    cp $FF         ;Bus value if joystick not connected on blanking to avoid floating bus issues
    jr z, .invalid
    in a, ($1F)    ;Read kempston
    ld b, a
    and %00000011  ; Up + Down is invalid
    cp %00000011
    jr z, .invalid
    ld a, b
    and %00001100  ; Left + Right is invalid
    cp %00001100
    jr z, .invalid
    ld a, b
    ret
.invalid:
    xor a
    ret
