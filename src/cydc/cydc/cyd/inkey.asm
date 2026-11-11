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
    ld hl,KEYTABLE_B-'A'   ; indexed by the key's code, as the ROM's (letters)
    inc b
    jr z,.K_LOOK_UP
    ld hl,KEYTABLE_C-'A'   ; indexed by the key's code, as the ROM's (letters)
.K_LOOK_UP:
    ld d,$00
    add hl,de
    ld a,(hl)
    ret
.K_KLC_LET:
    ld hl,KEYTABLE_E-'A'   ; indexed by the key's code, as the ROM's (letters)
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
    ld hl,KEYTABLE_F-'0'   ; indexed by the key's code, as the ROM's (digits)
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
    ld hl,KEYTABLE_D-'0'   ; indexed by the key's code, as the ROM's (digits)
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
    ld hl,KEYTABLE_D-'0'   ; indexed by the key's code, as the ROM's (digits)
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
    ld c, 0
    call INKEY
    or a
    jr z, .kempston
    ; Always: the cursor keys (CAPS SHIFT + 5..8) and ENTER
    ld b, KEYPRESS_RIGHT
    cp $09
    jr z, .key
    ld b, KEYPRESS_LEFT
    cp $08
    jr z, .key
    ld b, KEYPRESS_DOWN
    cp $0A
    jr z, .key
    ld b, KEYPRESS_UP
    cp $0B
    jr z, .key
    ld b, KEYPRESS_FIRE
    cp 13
    jr z, .key
    IFNDEF UNUSED_OP_POP_CONFIG
    ; The keys MENUKEY set, and those of the joystick MENUJOY chose
    push de
    push hl
    ld hl, CONFIG_MENU_KEYS
    call MENU_KEYS_MATCH
    ld b, a
    ld a, (CONFIG_MENU_JOY)
    dec a                       ; 1..3 -> 0..2; 0 (none) -> $FF
    cp 3
    jr nc, .no_joy
    ld e, a
    add a, a
    add a, a
    add a, e
    ld e, a
    ld d, 0
    ld hl, JOY_KEYS
    add hl, de                  ; JOY_KEYS + 5 * (type - 1)
    ld a, b
    call MENU_KEYS_MATCH
.no_joy:
    pop hl
    pop de
    jr .kempston
    ELSE
    ; The default keys: Q, A, O, P and SPACE
    ld b, KEYPRESS_UP
    cp 'q'
    jr z, .key
    ld b, KEYPRESS_DOWN
    cp 'a'
    jr z, .key
    ld b, KEYPRESS_LEFT
    cp 'o'
    jr z, .key
    ld b, KEYPRESS_RIGHT
    cp 'p'
    jr z, .key
    ld b, KEYPRESS_FIRE
    cp ' '
    jr nz, .kempston
    ENDIF
.key:
    ld c, b
.kempston:
    call KEMPSTON
    or c
    pop bc
    ret

    IFNDEF UNUSED_OP_POP_CONFIG
; A = key (not 0), HL -> 5 keys (up, down, left, right, select): ORs into C the
; masks of the ones that match. Keeps A; uses B, DE, HL.
MENU_KEYS_MATCH:
    ld de, MENU_MASKS
    ld b, 5
1:  cp (hl)
    jr nz, 2f
    ld a, (de)
    or c
    ld c, a
    ld a, (hl)                  ; the key again
2:  inc hl
    inc de
    djnz 1b
    ret

; The engine settings POP_CONFIG writes (MENUJOY, MENUKEY), in RAM.
; See doc/dev/MENU_KEYS_DESIGN.md.
CONFIG:
CONFIG_MENU_JOY:
    DB 0                        ; 0 none, 1 Sinclair 1, 2 Sinclair 2, 3 cursor
CONFIG_MENU_KEYS:
    DB 'q', 'a', 'o', 'p', ' '  ; up, down, left, right, select
CONFIG_SIZE EQU $ - CONFIG

MENU_MASKS:
    DB KEYPRESS_UP, KEYPRESS_DOWN, KEYPRESS_LEFT, KEYPRESS_RIGHT, KEYPRESS_FIRE
JOY_KEYS:
    DB '9', '8', '6', '7', '0'  ; Sinclair 1
    DB '4', '3', '1', '2', '5'  ; Sinclair 2
    DB '7', '6', '5', '8', '0'  ; cursor
    ENDIF

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
