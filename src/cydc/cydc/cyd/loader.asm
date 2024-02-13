    DEVICE ZXSPECTRUM48

    LUA ALLPASS

      function generateFiledata(filename, startaddress)
        local fp = assert(io.open(filename))
        local fsize = assert(fp:seek("end"))
        assert(fp:close())
        if (fsize > 64*1024 or fsize == 0) then
            error("invalid size")
        end
        _pc("DW " .. startaddress)
        _pc("DW " .. fsize)
      end

      function endList()
        _pc("DW $0000")
      end

    ENDLUA

SCR_ADDR   EQU  16384
SCR_SIZE   EQU  6912

PROG       EQU  $5C53
LD_BLOCK   EQU  $0802
LD_BYTES   EQU  $0556
REPORT_R   EQU  $0806


START_ADDRESS EQU 23755

; INIT_ADDR must be passed as parameter on SJASMPLUS
;INIT_ADDR     EQU $8000

    ORG START_ADDRESS

LINEA0:
    DB 0,0 ;NUMERO DE LINEA
    DW SIZE_LINE0 - 4 ;TAMAÑO
    DB 234 ;TOKEN DE REM

LOAD_TABLE:
    LUA ALLPASS
    --generateFiledata("load.scr", _c("SCR_ADDR"))
      generateFiledata("CYD_CORE.bin", _c("INIT_ADDR"))
      endList()
    ENDLUA

START:

    ; Clear screen
    XOR A
    OUT (254), A                    ;Black border
    LD HL, SCR_ADDR                 ;pixels
    LD DE, SCR_ADDR+1               ;pixels + 1
    LD BC, SCR_SIZE                 ;T
    LD (HL), L                      ;pone el primer byte a '0' ya que HL = 16384 = $4000  por tanto L = 0
    LDIR                            ;copia

    LD HL, LOAD_TABLE               ;Blocks table
LOOP_TABLE:
    LD C, (HL)
    INC HL
    LD B, (HL)
    INC HL                          ; Get program start address
    LD A, C
    OR B
    JR Z, RUN                       ; Start program if address = 0
    LD E, (HL)
    INC HL
    LD D, (HL)                      
    INC HL                          ; Get size
    LD IX, 0
    ADD IX, BC                      ; IX = start address, DE = size
    SCF                             ; Set Carry Flag -> CF=1 -> LOAD
    LD A, $FF                       ; A = 0xFF (cargar datos)
    PUSH HL
    CALL LD_BYTES                   ; Load block
    POP HL
    JR C, LOOP_TABLE                ;If load OK , next entry...
RESET:                        
    XOR A                           ;Reset on error
    LD BC, $7ffd
    DI
    OUT (C),A                       ;update port
    LD B,$1F                        ;BC=1FFD
    OUT (C),A                       ;update port
    JP 0
RUN:
    CALL INIT_ADDR
    JR RESET

SIZE_LINE0 = $ - LINEA0
LINEA10:
    DB 0,10
    DW SIZE_LINE10 - 4
    DB 253 ;CLEAR
    DB '.',14,0,0 ;SHORTNUMBER
    DW INIT_ADDR - 1
    DB 0 ;FIN DEL SHORTNUMBER
    DB ':'
    DB 242 ;PAUSE
    DB 192 ;USR
    DB '.',14,0,0 ;SHORTNUMBER
    DW START
    DB 0 ;FIN DEL SHORTNUMBER
    DB 13

SIZE_LINE10 = $ - LINEA10
SIZEOFBASIC = $ - 23755

    EMPTYTAP "CYD.tap"
    SAVETAP "CYD.tap",BASIC,"CYD",START_ADDRESS,SIZEOFBASIC,10
;    TAPOUT "SuperCobra.tap"
;    INCBIN "load.scr"
;    TAPEND
    TAPOUT "CYD.tap"
    INCBIN "CYD_CORE.bin"
    TAPEND

    END

