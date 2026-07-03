; ============================================================================
;  peek.asm - native routine for the CYD IMPORT / CALL demo
;
;  Reads one byte from an arbitrary memory address - something the CYD virtual
;  machine cannot do by itself. This is exactly the kind of small, low-level job
;  native routines are meant for.
;
;  You write only the body of the routine (no ORG, no directives): the compiler
;  frames it, assembles it in isolation and places it for you.
;
;  ABI  (see the manual, section "Native routines (IMPORT / CALL)"):
;    * entered with DE = FLAGS, the base of the 256-byte variable array;
;    * arguments and results travel through FLAGS positions (i.e. CYD variables);
;    * it is a leaf routine: it must end with RET and must not call back into the
;      engine. It may use AF/BC/DE/HL/IX/IY freely (the engine saves IX/IY).
;
;  IN : FLAGS+0 = address low byte
;       FLAGS+1 = address high byte
;  OUT: FLAGS+2 = the byte stored at that address
; ============================================================================

    ld a, (de)          ; DE = FLAGS -> A = FLAGS+0 = address low byte
    ld l, a
    inc de
    ld a, (de)          ; A = FLAGS+1 = address high byte
    ld h, a             ; HL = the address to read
    inc de              ; DE -> FLAGS+2
    ld a, (hl)          ; A = the byte stored at that address
    ld (de), a          ; FLAGS+2 = result
    ret
