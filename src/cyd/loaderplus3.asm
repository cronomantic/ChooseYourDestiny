    DEVICE ZXSPECTRUM48

    LUA ALLPASS

      function generateFiledata(filename, startaddress, bank)
        local fp = assert(io.open(filename))
        local fsize = assert(fp:seek("end"))
        assert(fp:close())
        if fsize > 64*1024 then
            error("invalid size")
        end
        _pc('DB "' .. string.upper(filename) .. '", $FF')
        _pc("DB " .. bank)
        _pc("DW " .. fsize)
        _pc("DW " .. startaddress)
      end


      function endList()
        _pc("DB $FF")
      end

    ENDLUA


SCR_ADDR   EQU  16384
SCR_SIZE   EQU  6912


DOS_OPEN      EQU $0106
DOS_READ      EQU $0112
DOS_SET_1346  EQU $013f
DOS_CLOSE     EQU $0109
DOS_OFF_MOTOR EQU $019c


START_ADDRESS EQU 23755

;INIT_ADDR     EQU $5A00
EXEC_ADDR     EQU INIT_ADDR
STACK_ADDRESS EQU INIT_ADDR-2

    ORG START_ADDRESS

LINEA0:
    DB 0,0 ;NUMERO DE LINEA
    DW SIZE_LINE0 - 4 ;TAMAÑO
    DB 234 ;TOKEN DE REM

LOAD_TABLE:
    LUA ALLPASS
      --generateFiledata("CYD.bin", _c("INIT_ADDR"), 0)
      generateFiledata(sj.get_define("_INTERPRETER_FILENAME_BARE_"), _c("INIT_ADDR"), 0)
      endList()
    ENDLUA

;    DB "DEEPTIME.BIN", $ff  ; File name
;    DB $0                   ; Bank
;    DW $6000                ; Size
;    DW $6000                ; Destination address
;    DB $ff                  ; End of load

START:
    DI
    LD SP, STACK_ADDRESS
    CALL INIT_STATE

    LD HL, LOAD_TABLE       ;
LOOP_TABLE:
    LD A, $FF
    CP (HL)                 ; Checks if the first character of the filename is $ff
    JR Z, END_LOAD

    PUSH HL
    LD BC, $0001 ;B: FICHERO 0 , C: MODO DE LECTURA
    LD DE, $0001 ;HA DE EXISTIR EL ARCHIVO, CARGAR SIN CABECERA
    ;HL has the start of the FILENAME
    CALL DOS_OPEN
    JR NC, RESET

    POP HL

    LD A, $FF
NEXT_FIELD_LOOP:
    CP (HL)                 ; Checks if the first character of the filename is $ff
    INC HL
    JR NZ, NEXT_FIELD_LOOP

    LD C, (HL)    ;C: RAM A PAGINAR
    INC HL
    LD E, (HL)    ;E: LSB of size
    INC HL
    LD D, (HL)    ;D: MSB of size
    INC HL
    PUSH DE
    LD E, (HL)    ;E: LSB of address
    INC HL
    LD D, (HL)    ;D: MSB of address
    INC HL
    EX (SP), HL   ; HL has size, DE = Address
    EX DE, HL     ; HL = Address, DE = size
    LD B, $00     ;B: FICHERO,
    CALL DOS_READ
    JR NC, RESET
    LD B, $00
    CALL DOS_CLOSE
    POP HL
    JR LOOP_TABLE

RESET:
    XOR A
    LD BC, $7ffd
    DI
    OUT (C),A          ;update port
    LD B,$1F           ;BC=1FFD
    OUT (C),A          ;update port
    JP 0

END_LOAD:
    CALL DOS_OFF_MOTOR
    CALL MAINROM ;rom interprete 48k
    LD C, 0
    CALL SETRAM
    JP EXEC_ADDR

;en C se indica la pagina de ram
SETRAM:
    LD A,(23388)
    AND %11111000
    OR C
    LD BC,$7FFD
    OUT (C),A
    LD (23388),A
    RET

MAINROM:
    LD A,(23388)
    SET 4,A
    LD BC,$7FFD
    OUT (C),A
    LD (23388),A
    LD A,(23399)
    RES 0,A
    SET 2,A
    LD B, $1F ;BC=$1FFD
    OUT (C),A
    LD (23399),A
    RET


;Y el siguiente codigo solo se ejecuta al inicio
;y puede ser pisado por la pila posteriormente
INIT_STATE:
    XOR A
    OUT (254), A                    ;Black border
    LD HL, SCR_ADDR                 ;pixels
    LD DE, SCR_ADDR+1               ;pixels + 1
    LD BC, SCR_SIZE                 ;T
    LD (HL), L                      ;pone el primer byte a '0' ya que HL = 16384 = $4000  por tanto L = 0
    LDIR                            ;copia

    LD A, (23388)
    LD BC, $7FFD
    AND %11101000                 ;SELECCION DE ROM0
    OR %00000111                  ;SELECCION DE RAM7
    OUT (C),A
    LD (23388),A
    LD B, $1F                     ;BC=1FFD
    LD A, (23399)
    AND %11111000
    OR %00000100                  ;SELECCION DE ROM2
    OUT (C),A
    LD (23399),A
    LD HL, $7800                  ;H 120, L 0
                                  ;8 last buffers of RAM 6
                                  ;0 for Ram Disc
    LD DE, $7808                  ;H 120, L 8
                                  ;8 last buffers of RAM 6
                                  ;4kb for cache
    JP DOS_SET_1346

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
SIZEOFBASIC = $ - START_ADDRESS

    SAVE3DOS _LOADER_FILENAME_, START_ADDRESS, SIZEOFBASIC, 0, 10

