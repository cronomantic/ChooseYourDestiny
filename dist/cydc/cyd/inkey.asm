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

INKEY:
    ;push hl
    ;push de
    ;push bc
    exx

    call KEY_SCAN
    jp nz, .empty_inkey

    call K_TEST
    jp nc, .empty_inkey

    dec d   ; D is expected to be FLAGS so set bit 3 $FF
    ; 'L' Mode so no keywords.
    ld e, a ; main key to A
    ; C is MODE 0 'KLC' from above still.
    call K_DECODE ; routine K-DECODE
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


    IFNDEF USE_ROM_KEYB
; THE 'KEYBOARD SCANNING' SUBROUTINE
; This very important subroutine is called by both the main keyboard subroutine (KEYBOARD) and the INKEY$ routine (S_INKEY).
; In all instances the E register is returned with a value in the range of +00 to +27, the value being different for each of the forty keys of the keyboard, or the value +FF, for no-key.
; The D register is returned with a value that indicates which single shift key is being pressed. If both shift keys are being pressed then the D and E registers are returned with the values for the CAPS SHIFT and SYMBOL SHIFT keys respectively.
; If no key is being pressed then the DE register pair is returned holding +FFFF.
; The zero flag is returned reset if more than two keys are being pressed, or neither key of a pair of keys is a shift key.
; Output
; D     Shift key pressed (+18 or +27), or +FF if no shift key pressed
; E     Other key pressed (+00 to +27), or +FF if no other key pressed
; F     Zero flag reset if an invalid combination of keys is pressed
KEY_SCAN:
    LD L,$2F        ;The initial key value for each line will be +2F, +2E,..., +28. (Eight lines.)
    LD DE,$FFFF     ;Initialise DE to 'no-key'.
    LD BC,$FEFE     ;C=port address, B=counter.
;Now enter a loop. Eight passes are made with each pass having a different initial key value and scanning a different line of five keys. (The first line is CAPS SHIFT, Z, X, C, V.)
KEY_LINE:
    IN A,(C)    ;Read from the port specified.
    CPL     ;A pressed key in the line will set its respective bit, from bit 0 (outer key) to bit 4 (inner key).
    AND $1F
    JR Z,KEY_DONE   ;Jump forward if none of the five keys in the line are being pressed.
    LD H,A  ;The key-bits go to the H register whilst the initial key value is fetched.
    LD A,L
KEY_3KEYS:
    INC D   ;If three keys are being pressed on the keyboard then the D register will no longer hold +FF - so return if this happens.
    RET NZ
KEY_BITS:
    SUB $08     ;Repeatedly subtract 8 from the present key value until a key-bit is found.
    SRL H
    JR NC,KEY_BITS
    LD D,E  ;Copy any earlier key value to the D register.
    LD E,A  ;Pass the new key value to the E register.
    JR NZ,KEY_3KEYS     ;If there is a second, or possibly a third, pressed key in this line then jump back.
KEY_DONE:
    DEC L   ;The line has been scanned so the initial key value is reduced for the next pass.
    RLC B   ;The counter is shifted and the jump taken if there are still lines to be scanned.
    JR C,KEY_LINE
;Four tests are now made.
    LD A,D  ;Accept any key value which still has the D register holding +FF, i.e. a single key pressed or 'no-key'.
    INC A
    RET Z
    CP $28  ;Accept the key value for a pair of keys if the D key is CAPS SHIFT.
    RET Z
    CP $19  ;Accept the key value for a pair of keys if the D key is SYMBOL SHIFT.
    RET Z
    LD A,E  ;It is however possible for the E key of a pair to be SYMBOL SHIFT - so this has to be considered.
    LD E,D
    LD D,A
    CP $18
    RET     ;Return with the zero flag set if it was SYMBOL SHIFT and 'another key'; otherwise reset.
; 031E: THE 'K-TEST' SUBROUTINE
; Used by the routines at KEYBOARD and S_INKEY.
; The key value is tested and a return made if 'no-key' or 'shift-only'; otherwise the 'main code' for that key is found.
; Input
; D     Shift key pressed (+18 or +27), or +FF if no shift key pressed
; E     Other key pressed (+00 to +27), or +FF if no other key pressed
; Output
; A     Main code (from the main key table)
; F     Carry flag reset if an invalid combination of keys is pressed
K_TEST:
    LD B,D  ;Copy the shift byte.
    LD D,$00    ;Clear the D register for later.
    LD A,E  ;Move the key number.
    CP $27  ;Return now if the key was 'CAPS SHIFT' only or 'no-key'.
    RET NC
    CP $18  ;Jump forward unless the E key was SYMBOL SHIFT.
    JR NZ,K_MAIN
    BIT 7,B     ;However accept SYMBOL SHIFT and another key; return with SYMBOL SHIFT only.
    RET NZ
;The 'main code' is found by indexing into the main key table.
K_MAIN:
    LD HL,KEYTABLE_A    ;The base address of the main key table.
    ADD HL,DE   ;Index into the table and fetch the 'main code'.
    LD A,(HL)
    SCF     ;   Signal 'valid keystroke' before returning.
    RET
; 0333: THE 'KEYBOARD DECODING' SUBROUTINE
; Used by the routines at KEYBOARD and S_INKEY.
; This subroutine is entered with the 'main code' in the E register, the value of FLAGS in the D register, the value of MODE in the C register and the 'shift byte' in the B register.
; By considering these four values and referring, as necessary, to the six key tables a 'final code' is produced. This is returned in the A register.
; Input
; B     Shift key pressed (+18 or +27), or +FF if no shift key pressed
; C     MODE
; D     FLAGS
; E     Main code (from the main key table)
; Output
; A     Final code (from the key tables)
K_DECODE:
    LD A,E  ;Copy the 'main code'.
    CP $3A  ;Jump forward if a digit key is being considered; also SPACE, ENTER and both shifts.
    JR C,K_DIGIT
    DEC C   ;Decrement the MODE value.
    JP M,K_KLC_LET  ;Jump forward, as needed, for modes 'K', 'L', 'C' and 'E'.
    JR Z,K_E_LET
;Only 'graphics' mode remains and the 'final code' for letter keys in graphics mode is computed from the 'main code'.
    ADD A,$4F   ;Add the offset.
    RET     ;Return with the 'final code'.
;Letter keys in extended mode are considered next.
K_E_LET:
    LD HL,KEYTABLE_B    ;The base address for table 'b'.
    INC B   ;Jump forward to use this table if neither shift key is being pressed.
    JR Z,K_LOOK_UP
    LD HL,KEYTABLE_C    ;Otherwise use the base address for table 'c'.
;Key tables 'b-f' are all served by the following look-up routine. In all cases a 'final code' is found and returned.
K_LOOK_UP:
    LD D,$00    ;Clear the D register.
    ADD HL,DE   ;Index the required table and fetch the 'final code'.
    LD A,(HL)
    RET     ;Then return.
;Letter keys in 'K', 'L' or 'C' modes are now considered. But first the special SYMBOL SHIFT codes have to be dealt with.
K_KLC_LET:
    LD HL,KEYTABLE_E    ;The base address for table 'e'.
    BIT 0,B     ;Jump back if using the SYMBOL SHIFT key and a letter key.
    JR Z,K_LOOK_UP
    BIT 3,D     ;Jump forward if currently in 'K' mode.
    JR Z,K_TOKENS
    BIT 3,(IY+$30)  ;If CAPS LOCK is set (bit 3 of FLAGS2 set) then return with the 'main code'.
    RET NZ
    INC B   ;Also return in the same manner if CAPS SHIFT is being pressed.
    RET NZ
    ADD A,$20   ;However if lower case codes are required then +20 has to be added to the 'main code' to give the correct 'final code'.
    RET
;The 'final code' values for tokens are found by adding +A5 to the 'main code'.
K_TOKENS:
    ADD A,$A5   ;Add the required offset and return.
    RET
;Next the digit keys, SPACE, ENTER and both shifts are considered.
K_DIGIT:
    CP "0"  ;Proceed only with the digit keys, i.e. return with SPACE (+20), ENTER (+0D) and both shifts (+0E).
    RET C
    DEC C   ;Now separate the digit keys into three groups - according to the mode.
    JP M,K_KLC_DGT  ;Jump with 'K', 'L' and 'C' modes, and also with 'G' mode. Continue with 'E' mode.
    JR NZ,K_GRA_DGT
    LD HL,KEYTABLE_F    ;The base address for table 'f'.
    BIT 5,B     ;Use this table for SYMBOL SHIFT and a digit key in extended mode.
    JR Z,K_LOOK_UP
    CP "8"  ;Jump forward with digit keys '8' and '9'.
    JR NC,K_8_9
;The digit keys '0' to '7' in extended mode are to give either a 'paper colour code' or an 'ink colour code' depending on the use of CAPS SHIFT.
    SUB $20     ;Reduce the range +30 to +37 giving +10 to +17.
    INC B   ;Return with this 'paper colour code' if CAPS SHIFT is not being used.
    RET Z
    ADD A,$08   ;But if it is then the range is to be +18 to +1F instead - indicating an 'ink colour code'.
    RET
;The digit keys '8' and '9' are to give 'BRIGHT' and 'FLASH' codes.
K_8_9:
    SUB $36     ;+38 and +39 go to +02 and +03.
    INC B   ;Return with these codes if CAPS SHIFT is not being used. (These are 'BRIGHT' codes.)
    RET Z
    ADD A,$FE   ;Subtract '2' if CAPS SHIFT is being used; giving +00 and +01 (as 'FLASH' codes).
    RET
;The digit keys in graphics mode are to give the block graphic characters (+80 to +8F), the GRAPHICS code (+0F) and the DELETE code (+0C).
K_GRA_DGT:
    LD HL,KEYTABLE_D    ;The base address of table 'd'.
    CP "9"  ;Use this table directly for both digit key '9' that is to give GRAPHICS, and digit key '0' that is to give DELETE.
    JR Z,K_LOOK_UP
    CP "0"
    JR Z,K_LOOK_UP
    AND $07     ;For keys '1' to '8' make the range +80 to +87.
    ADD A,$80
    INC B   ;Return with a value from this range if neither shift key is being pressed.
    RET Z
    XOR $0F     ;But if 'shifted' make the range +88 to +8F.
    RET
;Finally consider the digit keys in 'K', 'L' and 'C' modes.
K_KLC_DGT:
    INC B   ;Return directly if neither shift key is being used. (Final codes +30 to +39.)
    RET Z
    BIT 5,B     ;Use table 'd' if the CAPS SHIFT key is also being pressed.
    LD HL,KEYTABLE_D
    JR NZ,K_LOOK_UP
;The codes for the various digit keys and SYMBOL SHIFT can now be found.
    SUB $10     ;Reduce the range to give +20 to +29.
    CP $22  ;Separate the '@@' character from the others.
    JR Z,K_AT_CHAR
    CP $20  ;The '_' character has also to be separated.
    RET NZ  ;Return now with the 'final codes' +21, +23 to +29.
    LD A,"_"    ;Give the '_' character a code of +5F.
    RET
K_AT_CHAR:
    LD A,"@@"   ;Give the '@@' character a code of +40.
    RET

;(a) The main key table - L mode and CAPS SHIFT.
KEYTABLE_A:
    DEFB $42    ;B
    DEFB $48    ;H
    DEFB $59    ;Y
    DEFB $36    ;6
    DEFB $35    ;5
    DEFB $54    ;T
    DEFB $47    ;G
    DEFB $56    ;V
    DEFB $4E    ;N
    DEFB $4A    ;J
    DEFB $55    ;U
    DEFB $37    ;7
    DEFB $34    ;4
    DEFB $52    ;R
    DEFB $46    ;F
    DEFB $43    ;C
    DEFB $4D    ;M
    DEFB $4B    ;K
    DEFB $49    ;I
    DEFB $38    ;8
    DEFB $33    ;3
    DEFB $45    ;E
    DEFB $44    ;D
    DEFB $58    ;X
    DEFB $0E    ;SYMBOL SHIFT
    DEFB $4C    ;L
    DEFB $4F    ;O
    DEFB $39    ;9
    DEFB $32    ;2
    DEFB $57    ;W
    DEFB $53    ;S
    DEFB $5A    ;Z
    DEFB $20    ;SPACE
    DEFB $0D    ;ENTER
    DEFB $50    ;P
    DEFB $30    ;0
    DEFB $31    ;1
    DEFB $51    ;Q
    DEFB $41    ;A
;(b) Extended mode. Letter keys and unshifted.
KEYTABLE_B:
    DEFB $E3    ;READ
    DEFB $C4    ;BIN
    DEFB $E0    ;LPRINT
    DEFB $E4    ;DATA
    DEFB $B4    ;TAN
    DEFB $BC    ;SGN
    DEFB $BD    ;ABS
    DEFB $BB    ;SQR
    DEFB $AF    ;CODE
    DEFB $B0    ;VAL
    DEFB $B1    ;LEN
    DEFB $C0    ;USR
    DEFB $A7    ;PI
    DEFB $A6    ;INKEY$
    DEFB $BE    ;PEEK
    DEFB $AD    ;TAB
    DEFB $B2    ;SIN
    DEFB $BA    ;INT
    DEFB $E5    ;RESTORE
    DEFB $A5    ;RND
    DEFB $C2    ;CHR$
    DEFB $E1    ;LLIST
    DEFB $B3    ;COS
    DEFB $B9    ;EXP
    DEFB $C1    ;STR$
    DEFB $B8    ;LN
;(c) Extended mode. Letter keys and either shift.
KEYTABLE_C:
    DEFB $7E    ;~
    DEFB $DC    ;BRIGHT
    DEFB $DA    ;PAPER
    DEFB $5C    ;\
    DEFB $B7    ;ATN
    DEFB $7B    ;{
    DEFB $7D    ;}
    DEFB $D8    ;CIRCLE
    DEFB $BF    ;IN
    DEFB $AE    ;VAL$
    DEFB $AA    ;SCREEN$
    DEFB $AB    ;ATTR
    DEFB $DD    ;INVERSE
    DEFB $DE    ;OVER
    DEFB $DF    ;OUT
    DEFB $7F    ;©
    DEFB $B5    ;ASN
    DEFB $D6    ;VERIFY
    DEFB $7C    ;|
    DEFB $D5    ;MERGE
    DEFB $5D    ;]
    DEFB $DB    ;FLASH
    DEFB $B6    ;ACS
    DEFB $D9    ;INK
    DEFB $5B    ;[
    DEFB $D7    ;BEEP
;(d) Control codes. Digit keys and CAPS SHIFT.
KEYTABLE_D:
    DEFB $0C    ;DELETE
    DEFB $07    ;EDIT
    DEFB $06    ;CAPS LOCK
    DEFB $04    ;TRUE VIDEO
    DEFB $05    ;INV. VIDEO
    DEFB $08    ;Cursor left
    DEFB $0A    ;Cursor down
    DEFB $0B    ;Cursor up
    DEFB $09    ;Cursor right
    DEFB $0F    ;GRAPHICS
;(e) Symbol code. Letter keys and symbol shift.
KEYTABLE_E:
    DEFB $E2    ;STOP
    DEFB $2A    ;*
    DEFB $3F    ;?
    DEFB $CD    ;STEP
    DEFB $C8    ;>=
    DEFB $CC    ;TO
    DEFB $CB    ;THEN
    DEFB $5E    ;↑
    DEFB $AC    ;AT
    DEFB $2D    ;-
    DEFB $2B    ;+
    DEFB $3D    ;=
    DEFB $2E    ;.
    DEFB $2C    ;,
    DEFB $3B    ;;
    DEFB $22    ;"
    DEFB $C7    ;<=
    DEFB $3C    ;<
    DEFB $C3    ;NOT
    DEFB $3E    ;>
    DEFB $C5    ;OR
    DEFB $2F    ;/
    DEFB $C9    ;<>
    DEFB $60    ;£
    DEFB $C6    ;AND
    DEFB $3A    ;:
;(f) Extended mode. Digit keys and symbol shift.
KEYTABLE_F:
    DEFB $D0    ;FORMAT
    DEFB $CE    ;DEF FN
    DEFB $A8    ;FN
    DEFB $CA    ;LINE
    DEFB $D3    ;OPEN
    DEFB $D4    ;CLOSE
    DEFB $D1    ;MOVE
    DEFB $D2    ;ERASE
    DEFB $A9    ;POINT
    DEFB $CF    ;CAT

    ENDIF

