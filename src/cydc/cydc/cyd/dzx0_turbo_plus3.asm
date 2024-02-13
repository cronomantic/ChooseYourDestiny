;====================================================
; Cargamos en la RAM el contenido comprimido de un fichero zx0
; Parámetros: 
;    B = Numero de fichero abierto
;    C = Banco activo en $C000
;    HL = Dirección de destino
; Salida:
;    A = Codigo del error si NC
;   Carry = Si está activo, operacion correcta
; Registros afectados:
;   AF, BC, DE, HL, BC', HL'
;====================================================
PLUS3_DOS_READ_DZX0:
    LD      (BANK),BC             ;Guardamos el banco
    DI
    LD      (STACK),SP            ;Guardamos la pila
    EI

    LD      A, C
    CALL    CHG_RAM_BANK          ;Cambiamos al banco seleccionado, banco anterior en A
    EX      AF, AF'               ;Save original bank
    EX      HL, DE                ;Destiny to DE
    CALL    DZX0_TURBO_PLUS3      ; Si la carga del buffer es correcta, pasamos a descomprimir

END_DOS_READ_DZX0:
    PUSH    AF                    ; Guardamos el resultado
    EX      AF, AF'               ; Cargamos el banco original
    CALL    CHG_RAM_BANK          ; Restauramos el banco
    POP     AF                    ; Restauramos AF
    RET                           ; Salimos

;=====================================================
; Cambiamos el banco elegido en $C000
; Parámetros: 
;    A = Nuevo valor del banco
; Salida:
;    A = Valor anterior del banco
; Registros afectados:
;   AF, BC
;====================================================
CHG_RAM_BANK:
    AND %00010111                 ;mask correct bytes
    LD B, A
    LD A,($5b5c)                  ; Previous value of the port
    PUSH AF                       ; Saving in stack
    AND %11101000                 ; Change only bank bits
    OR B                          ; Select bank on B
    LD BC,$7ffd
    DI
    LD ($5b5c),A
    OUT (C),A                     ;update port
    EI
    POP AF                        ;Recovering previous value
    RET

;====================================================
; Registros afectados:
;   AF, BC, DE, HL, BC', HL'
;====================================================
DZX0_P3_READ_BYTE:
    PUSH    DE
    PUSH    BC
    PUSH    AF
    LD      BC, (BANK)
    CALL    PLUS3_DOS_BYTE_READ ;Leemos byte
    JR      C, 1f               ;No hay error
    DI
    LD      SP, (STACK)         ;Restauramos la pila (situacion inicial antes de entrar)
    EI
    JR      END_DOS_READ_DZX0   ;Salimos a saco, descartando todo lo guardado
1:  LD      L, A
    POP     AF
    LD      A, L
    POP     BC
    POP     DE
    RET

;====================================================
; Registros afectados:
;   AF, BC, DE, HL, BC', HL'
;====================================================
DZX0_P3_READ_BYTES:
    PUSH    AF
    EX      HL, DE              ;HL=Destino, DE=Origen
    LD      D, B
    LD      E, C                ;DE=Tamaño
    PUSH    HL                  ;Guardamod Destino
    ADD     HL, DE              ;Sumamos al destino el tamaño a leer
    EX      (SP), HL            ;Cambiamos Destino, con el destino modificado
    LD      BC, (BANK)
    CALL    PLUS3_DOS_READ      ;Leemos bytes
    JR      C, 1f               ;No hay error
    DI
    LD      SP, (STACK)         ;Restauramos la pila (situacion inicial antes de entrar)
    EI
    JR      END_DOS_READ_DZX0   ;Salimos a saco, descartando todo lo guardado
1:  POP     DE                  ;Restaurar Destino
    LD      BC, 0               ;Logitud a 0
    POP     AF
    RET

; -----------------------------------------------------------------------------
; ZX0 decoder by Einar Saukas & introspec
; "Turbo" version (126 bytes, 21% faster)
; -----------------------------------------------------------------------------
; Parameters:
;   HL: source address (compressed data)
;   DE: destination address (decompressing)
; -----------------------------------------------------------------------------
; Modified for load from disk
DZX0_TURBO_PLUS3:
        ld      bc, $ffff               ; preserve default offset 1
        ld      (dzx0t_last_offset+1), bc
        inc     bc
        ld      a, $80
        jr      dzx0t_literals
dzx0t_new_offset:
        ld      c, $fe                  ; prepare negative offset
        add     a, a
        jp      nz, dzx0t_new_offset_skip
        CALL    DZX0_P3_READ_BYTE       ; load another group of 8 bits
        rla
dzx0t_new_offset_skip:
        call    nc, dzx0t_elias         ; obtain offset MSB
        inc     c
        ret     z                       ; check end marker
        PUSH    AF
        CALL    DZX0_P3_READ_BYTE       ; load another group of 8 bits
        LD      B, C
        LD      C, A
        POP     AF
        rr      b                       ; last offset bit becomes first length bit
        rr      c
        ld      (dzx0t_last_offset+1), bc ; preserve new offset
        ld      bc, 1                   ; obtain length
        call    nc, dzx0t_elias
        inc     bc
dzx0t_copy:
dzx0t_last_offset:
        ld      hl, 0                   ; restore offset
        add     hl, de                  ; calculate destination - offset
        ldir                            ; copy from offset
        add     a, a                    ; copy from literals or new offset?
        jr      c, dzx0t_new_offset
dzx0t_literals:
        inc     c                       ; obtain length
        add     a, a
        jp      nz, dzx0t_literals_skip
        CALL    DZX0_P3_READ_BYTE       ; load another group of 8 bits
        rla
dzx0t_literals_skip:
        call    nc, dzx0t_elias
        CALL    DZX0_P3_READ_BYTES      ; copy literals
        add     a, a                    ; copy from last offset or new offset?
        jr      c, dzx0t_new_offset
        inc     c                       ; obtain length
        add     a, a
        jp      nz, dzx0t_last_offset_skip
        CALL    DZX0_P3_READ_BYTE       ; load another group of 8 bits
        rla
dzx0t_last_offset_skip:
        call    nc, dzx0t_elias
        jp      dzx0t_copy
dzx0t_elias:
        add     a, a                    ; interlaced Elias gamma coding
        rl      c
        add     a, a
        jr      nc, dzx0t_elias
        ret     nz
        CALL    DZX0_P3_READ_BYTE       ; load another group of 8 bits
        rla
        ret     c
        add     a, a
        rl      c
        add     a, a
        ret     c
        add     a, a
        rl      c
        add     a, a
        ret     c
        add     a, a
        rl      c
        add     a, a
        ret     c
dzx0t_elias_loop:
        add     a, a
        rl      c
        rl      b
        add     a, a
        jr      nc, dzx0t_elias_loop
        ret     nz
        CALL    DZX0_P3_READ_BYTE               ; load another group of 8 bits
        rla
        jr      nc, dzx0t_elias_loop
        ret
; -----------------------------------------------------------------------------
STACK:      DW 0
BANK:       DB 0
FILENO:     DB 0
; -----------------------------------------------------------------------------
