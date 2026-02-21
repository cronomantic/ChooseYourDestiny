; SPECTRUM PSG proPLAYER V 0.2 - WYZ 07.09.2011
; Modificado por na_th_an para música comprimida.
; Modificado por thEpOpE para efectos con canal de ruido.
; VER AL FINAL PARA DATOS PROPIOS:

;ISR_WYZ
;WYZ_INIT
;WYZ_PLAYER_OFF
;WYZ_LOAD_SONG

; ISR LLAMA A:
;INICIO: 
ISR_WYZ:
		CALL    ROUT
		LD      HL,PSG_REG
		LD      DE,PSG_REG_SEC
		LD      BC,14
		LDIR                
		CALL    REPRODUCE_SONIDO
		; CALL    REPRODUCE_EFECTO
		; CALL    PLAY
		; RET
        JP      PLAY

; ANTES DE EMPEZAR (CON DI):
;INIT_BUFFERS:
WYZ_INIT:
		LD      BC, $30
		LD      HL, BUFFERS_CANALES
		LD      (CANAL_A), HL
		ADD     HL, BC
		LD      (CANAL_B), HL
		ADD     HL, BC
		LD      (CANAL_C), HL
		ADD     HL, BC
		LD      (CANAL_P), HL
		xor		a
		ld      (INTERR), a
		RET
    
;VUELCA BUFFER DE SONIDO AL PSG DEL SPECTRUM

ROUT:       
		XOR     A
ROUT_A0:    
		LD      DE,$FFBF
		LD      BC,$FFFD
		LD      HL,PSG_REG_SEC
LOUT:       
		OUT     (C),A
		LD      B,E
		OUTI 
		LD      B,D
		INC     A
		CP      13
		JR      NZ,LOUT
		OUT     (C),A
		LD      A,(HL)
		AND     A
		RET     Z
		LD      B,E
		OUTI
		XOR     A
		LD      (PSG_REG_SEC+13),A
		LD      (PSG_REG+13),A
		RET

;INICIA EL SONIDO Nº (A)
WYZ_START_SOUND:
INICIA_SONIDO:  
		LD      HL,(TABLA_SONIDOS)
		CALL    EXT_WORD
		LD      (PUNTERO_SONIDO),HL
		LD      HL,INTERR
		SET     2,(HL)
		RET

;PLAYER OFF
WYZ_PLAYER_OFF:
		LD     	HL,INTERR
		LD     	A,%00010001
		AND		(HL)
		LD      (HL),A
    
		LD      HL,PSG_REG
		LD      DE,PSG_REG+1
		LD      BC,14
		LD      (HL),A
		LDIR
    
		LD      HL,PSG_REG_SEC
		LD      DE,PSG_REG_SEC+1
		LD      BC,14
		LD      (HL),A
		LDIR
    
	  
		LD      A,10111000B     ; **** POR SI ACASO ****
		LD      (PSG_REG+7),A
		CALL    ROUT
		RET

; HL -> Song Address
WYZ_LOAD_SONG:
        push    hl
        ld      de, TABLA_PAUTAS
        ld      bc, 6
        ldir                        ; Copy pointers
        ;ld      (TABLA_SONG), hl    ; Almacenar inicio de canción
        pop     de                  ; Restore on DE start of song 
        push    hl                  ; Store pointer to header
        ld      hl, (TABLA_PAUTAS)
        add     hl, de
        ld      (TABLA_PAUTAS), hl
        ld      hl, (TABLA_SONIDOS)
        add     hl, de
        ld      (TABLA_SONIDOS), hl
        ld      hl, (DATOS_NOTAS)
        add     hl, de
        ld      (DATOS_NOTAS), hl
        LD      HL,INTERR           ;CARGA CANCION
 		set     0,(HL)              
		res     1,(HL)				;NO REPRODUCE CANCION       
        pop     hl

; ;CARGA UNA CANCION
; ;IN:(A)=Nº DE CANCION

; CARGA_CANCION:  
; 		LD      HL,INTERR           ;CARGA CANCION
; 		SET     1,(HL)              ;REPRODUCE CANCION
; 		LD      HL,SONG
; 		LD      (HL),A              ;Nº (A)

; ;DECODIFICAR
; ;IN-> INTERR 0 ON
; ;     SONG

; ;CARGA CANCION SI/NO

; DECODE_SONG:
; 		LD      A,(SONG)

; ;LEE CABECERA DE LA CANCION
; ;BYTE 0=TEMPO;

; 		LD      HL,TABLA_SONG
; 		CALL    EXT_WORD

; ; descomprimir            
; 		ld		de, BUFFER_UNPACK
; 		push 	de
; 		push 	bc
; 		call    dzx0_turbo
; 		pop		bc
; 		pop		de
; 		ld		hl, BUFFER_UNPACK
; fin			
		LD      A,(HL)
		LD      (TEMPO),A
		XOR     A
		LD      (TTEMPO),A
		    
;HEADER BYTE 1
;(-|-|-|-|-|-|-|LOOP)

		INC     HL          ;LOOP 1=ON/0=OFF?
		LD      A,(HL)
		BIT     0,A
		JR      Z,NPTJP0
		PUSH    HL
		LD      HL,INTERR
		SET     4,(HL)
		POP     HL
		
NPTJP0:     
		INC     HL              ;2 BYTES RESERVADOS
		INC     HL
		INC     HL

;BUSCA Y GUARDA INICIO DE LOS CANALES EN EL MODULO MUS
	  
		LD      (PUNTERO_P_DECA),HL
		LD      E,$3F           ;CODIGO INTRUMENTO 0
		LD      B,$FF           ;EL MODULO DEBE TENER UNA LONGITUD MENOR DE $FF00 ... o_O!
		
BGICMODBC1: 
		XOR     A               ;BUSCA EL BYTE 0
		CPIR
		DEC     HL
		DEC     HL
		LD      A,E             ;ES EL INSTRUMENTO 0??
		CP      (HL)
		INC     HL
		INC     HL
		JR      Z,BGICMODBC1
    
		LD      (PUNTERO_P_DECB),HL

BGICMODBC2: 
		XOR     A               ;BUSCA EL BYTE 0
		CPIR
		DEC     HL
		DEC     HL
		LD      A,E
		CP      (HL)            ;ES EL INSTRUMENTO 0??
		INC     HL
		INC     HL
		JR      Z,BGICMODBC2
    
		LD      (PUNTERO_P_DECC),HL
	  
BGICMODBC3: 
		XOR     A               ;BUSCA EL BYTE 0
		CPIR
		DEC     HL
		DEC     HL
		LD      A,E
		CP      (HL)                ;ES EL INSTRUMENTO 0??
		INC     HL
		INC     HL
		JR      Z,BGICMODBC3
		LD      (PUNTERO_P_DECP),HL
	  
		    
;LEE DATOS DE LAS NOTAS
;(|)(|||||) LONGITUD\NOTA

INIT_DECODER:   
		LD      DE,(CANAL_A)
		LD      (PUNTERO_A),DE
		LD      HL,(PUNTERO_P_DECA)
		CALL    DECODE_CANAL    ;CANAL A
		LD      (PUNTERO_DECA),HL
		
		LD      DE,(CANAL_B)
		LD      (PUNTERO_B),DE
		LD      HL,(PUNTERO_P_DECB)
		CALL    DECODE_CANAL    ;CANAL B
		LD      (PUNTERO_DECB),HL
		
		LD      DE,(CANAL_C)
		LD      (PUNTERO_C),DE
		LD      HL,(PUNTERO_P_DECC)
		CALL    DECODE_CANAL    ;CANAL C
		LD      (PUNTERO_DECC),HL
		
		LD      DE,(CANAL_P)
		LD      (PUNTERO_P),DE
		LD      HL,(PUNTERO_P_DECP)
		CALL    DECODE_CANAL    ;CANAL P
		LD      (PUNTERO_DECP),HL
	     
		RET


;DECODIFICA NOTAS DE UN CANAL
;IN (DE)=DIRECCION DESTINO
;NOTA=0 FIN CANAL
;NOTA=1 SILENCIO
;NOTA=2 PUNTILLO
;NOTA=3 COMANDO I

DECODE_CANAL:   
		LD      A,(HL)
		AND     A                       ;FIN DEL CANAL?
		JR      Z,FIN_DEC_CANAL
		CALL    GETLEN

		CP      00000001B               ;ES SILENCIO?
		JR      NZ,NO_SILENCIO
		SET     6,A
		JR      NO_MODIFICA
		    
NO_SILENCIO:    
		CP      00111110B               ;ES PUNTILLO?
		JR      NZ,NO_PUNTILLO
		OR      A
		RRC     B
		XOR     A
		JR      NO_MODIFICA

NO_PUNTILLO:   
		CP      00111111B              ;ES COMANDO?
		JR      NZ,NO_MODIFICA
		BIT     0,B                     ;COMADO=INSTRUMENTO?
		JR      Z,NO_INSTRUMENTO   
		LD      A,11000001B             ;CODIGO DE INSTRUMENTO      
		LD      (DE),A
		INC     HL
		INC     DE
		LD      A,(HL)                  ;Nº DE INSTRUMENTO
		LD      (DE),A
		INC     DE
		INC     HL
		JR      DECODE_CANAL
		
NO_INSTRUMENTO: 
		BIT     2,B
		JR      Z,NO_ENVOLVENTE
		LD      A,11000100B             ;CODIGO ENVOLVENTE
		LD      (DE),A
		INC     DE
		INC HL
		LD  A,(HL)
		LD  (DE),A
		INC DE
		INC HL
		JR      DECODE_CANAL
     
NO_ENVOLVENTE:  
		BIT     1,B
		JR      Z,NO_MODIFICA           
		LD      A,11000010B             ;CODIGO EFECTO
		LD      (DE),A                  
		INC     HL                      
		INC     DE                      
		LD      A,(HL)                  
		CALL    GETLEN   
		    
NO_MODIFICA:    
		LD      (DE),A
		INC     DE
		XOR     A
		DJNZ    NO_MODIFICA
		SET     7,A
		SET     0,A
		LD      (DE),A
		INC     DE
		INC     HL
		RET                 ;** JR      DECODE_CANAL
		    
FIN_DEC_CANAL:  
		SET     7,A
		LD      (DE),A
		INC     DE
		RET

GETLEN:     LD      B,A
		AND     00111111B
		PUSH    AF
		LD      A,B
		AND     11000000B
		RLCA
		RLCA
		INC     A
		LD      B,A
		LD      A,10000000B
DCBC0:      RLCA
		DJNZ    DCBC0
		LD      B,A
		POP     AF
		RET
		    
;PLAY __________________________________________________

PLAY:   
		LD      HL,INTERR               ;PLAY BIT 1 ON?
		BIT     1,(HL)
		RET     Z
;TEMPO          
		LD      HL,TTEMPO               ;CONTADOR TEMPO
		INC     (HL)
		LD      A,(TEMPO)
		CP      (HL)
		JR      NZ,PAUTAS
		LD      (HL),0
		    
;INTERPRETA      
		LD      IY,PSG_REG
		LD      IX,PUNTERO_A
		LD      BC,PSG_REG+8
		CALL    LOCALIZA_NOTA
		LD      IY,PSG_REG+2
		LD      IX,PUNTERO_B
		LD      BC,PSG_REG+9
		CALL    LOCALIZA_NOTA
		LD      IY,PSG_REG+4
		LD      IX,PUNTERO_C
		LD      BC,PSG_REG+10
		CALL    LOCALIZA_NOTA
		LD      IX,PUNTERO_P            ;EL CANAL DE EFECTOS ENMASCARA OTRO CANAL
		CALL    LOCALIZA_EFECTO              

;PAUTAS               
PAUTAS: 
		LD      IY,PSG_REG+0
		LD      IX,PUNTERO_P_A
		LD      HL,PSG_REG+8
		CALL    PAUTA                   ;PAUTA CANAL A
		LD      IY,PSG_REG+2
		LD      IX,PUNTERO_P_B
		LD      HL,PSG_REG+9
		CALL    PAUTA                   ;PAUTA CANAL B
		LD      IY,PSG_REG+4
		LD      IX,PUNTERO_P_C
		LD      HL,PSG_REG+10
		CALL    PAUTA                   ;PAUTA CANAL C                

		RET

;REPRODUCE EFECTOS DE SONIDO 

REPRODUCE_SONIDO:

		LD      HL,INTERR   
		BIT     2,(HL)                  ;ESTA ACTIVADO EL EFECTO?
		RET     Z
		LD      HL,(PUNTERO_SONIDO)
		LD      A,(HL)
		CP      $FF
		JR      Z,FIN_SONIDO
		LD      (PSG_REG_SEC+2),A
		INC     HL
		LD      A,(HL)
		RRCA
		RRCA
		RRCA
		RRCA
		AND     00001111B
		LD      (PSG_REG_SEC+3),A
		LD      A,(HL)
		AND     00001111B
		LD      (PSG_REG_SEC+9),A
		INC     HL
		LD      A,(HL)
		AND     A
		JR      Z,NO_RUIDO
		LD      (PSG_REG_SEC+6),A
		LD      A,10101000B
		JR      SI_RUIDO

NO_RUIDO:   
		LD      A,10111000B
SI_RUIDO:   
		LD      (PSG_REG_SEC+7),A
	 
		INC     HL
		LD      (PUNTERO_SONIDO),HL
		RET
		
FIN_SONIDO: LD      HL,INTERR
		RES     2,(HL)

FIN_NOPLAYER:
		LD      A,10111000B
		LD      (PSG_REG+7),A
		RET         
		    
;LOCALIZA NOTA CANAL A
;IN (PUNTERO_A)

LOCALIZA_NOTA:  
		LD      L,(IX+PUNTERO_A-PUNTERO_A)  ;HL=(PUNTERO_A_C_B)
		LD      H,(IX+PUNTERO_A-PUNTERO_A+1)
		LD      A,(HL)
		AND     11000000B               ;COMANDO?
		CP      11000000B
		JR      NZ,LNJP0

;BIT(0)=INSTRUMENTO
		    
COMANDOS:   
		LD      A,(HL)
		BIT     0,A                     ;INSTRUMENTO
		JR      Z,COM_EFECTO

		INC     HL
		LD      A,(HL)                  ;Nº DE PAUTA
		INC     HL
		LD      (IX+PUNTERO_A-PUNTERO_A),L
		LD      (IX+PUNTERO_A-PUNTERO_A+1),H
		LD      HL,(TABLA_PAUTAS)
		CALL    EXT_WORD
		LD      (IX+PUNTERO_P_A0-PUNTERO_A),L
		LD      (IX+PUNTERO_P_A0-PUNTERO_A+1),H
		LD      (IX+PUNTERO_P_A-PUNTERO_A),L
		LD      (IX+PUNTERO_P_A-PUNTERO_A+1),H
		LD      L,C
		LD      H,B
		RES     4,(HL)                  ;APAGA EFECTO ENVOLVENTE
		XOR     A
		LD      (PSG_REG_SEC+13),A
		LD      (PSG_REG+13),A
		JR      LOCALIZA_NOTA

COM_EFECTO: 
		BIT     1,A                     ;EFECTO DE SONIDO
		JR      Z,COM_ENVOLVENTE

		INC     HL
		LD      A,(HL)
		INC     HL
		LD      (IX+PUNTERO_A-PUNTERO_A),L
		LD      (IX+PUNTERO_A-PUNTERO_A+1),H
		CALL    INICIA_SONIDO
		RET

COM_ENVOLVENTE: 
		BIT     2,A
		RET     Z                       ;IGNORA - ERROR            
	 
		INC     HL
		LD      A,(HL)                  ;CARGA CODIGO DE ENVOLVENTE
		LD      (ENVOLVENTE),A
		INC     HL
		LD      (IX+PUNTERO_A-PUNTERO_A),L
		LD      (IX+PUNTERO_A-PUNTERO_A+1),H
		LD      L,C
		LD      H,B
		LD      (HL),00010000B          ;ENCIENDE EFECTO ENVOLVENTE
		JR      LOCALIZA_NOTA
		  
LNJP0:      
		LD      A,(HL)
		INC     HL
		BIT     7,A
		JR      Z,NO_FIN_CANAL_A    ;
		BIT     0,A
		JR      Z,FIN_CANAL_A

FIN_NOTA_A: 
		LD      E,(IX+CANAL_A-PUNTERO_A)
		LD      D,(IX+CANAL_A-PUNTERO_A+1)      ;PUNTERO BUFFER AL INICIO
		LD      (IX+PUNTERO_A-PUNTERO_A),E
		LD      (IX+PUNTERO_A-PUNTERO_A+1),D
		LD      L,(IX+PUNTERO_DECA-PUNTERO_A)   ;CARGA PUNTERO DECODER
		LD      H,(IX+PUNTERO_DECA-PUNTERO_A+1)
		PUSH    BC
		CALL    DECODE_CANAL                    ;DECODIFICA CANAL
		POP     BC
		LD      (IX+PUNTERO_DECA-PUNTERO_A),L   ;GUARDA PUNTERO DECODER
		LD      (IX+PUNTERO_DECA-PUNTERO_A+1),H
		JP      LOCALIZA_NOTA
		
FIN_CANAL_A:    
		LD      HL,INTERR           ;LOOP?
		BIT     4,(HL)              
		JR      NZ,FCA_CONT
		CALL    WYZ_PLAYER_OFF
		RET

FCA_CONT:   
		LD      L,(IX+PUNTERO_P_DECA-PUNTERO_A) ;CARGA PUNTERO INICIAL DECODER
		LD      H,(IX+PUNTERO_P_DECA-PUNTERO_A+1)
		LD      (IX+PUNTERO_DECA-PUNTERO_A),L
		LD      (IX+PUNTERO_DECA-PUNTERO_A+1),H
		JR      FIN_NOTA_A
		    
NO_FIN_CANAL_A: 
		LD      (IX+PUNTERO_A-PUNTERO_A),L      ;(PUNTERO_A_B_C)=HL GUARDA PUNTERO
		LD      (IX+PUNTERO_A-PUNTERO_A+1),H
		AND     A                               ;NO REPRODUCE NOTA SI NOTA=0
		JR      Z,FIN_RUTINA
		BIT     6,A                             ;SILENCIO?
		JR      Z,NO_SILENCIO_A
		LD      A,(BC)
		AND     00010000B
		JR      NZ,SILENCIO_ENVOLVENTE
		XOR     A
		LD      (BC),A                          ;RESET VOLUMEN DEL CORRESPODIENTE CHIP
		LD      (IY+0),A
		LD      (IY+1),A
		RET
	  
SILENCIO_ENVOLVENTE:
		LD  A,$FF
		LD  (PSG_REG+11),A
		LD  (PSG_REG+12),A               
		XOR A
		LD  (PSG_REG+13),A                               
		LD  (IY+0),A
		LD  (IY+1),A
		RET

NO_SILENCIO_A:  
		LD  (IX+REG_NOTA_A-PUNTERO_A),A ;REGISTRO DE LA NOTA DEL CANAL         
		CALL    NOTA                    ;REPRODUCE NOTA
		LD      L,(IX+PUNTERO_P_A0-PUNTERO_A)   ;HL=(PUNTERO_P_A0) RESETEA PAUTA 
		LD      H,(IX+PUNTERO_P_A0-PUNTERO_A+1)
		LD      (IX+PUNTERO_P_A-PUNTERO_A),L    ;(PUNTERO_P_A)=HL
		LD      (IX+PUNTERO_P_A-PUNTERO_A+1),H
FIN_RUTINA:     
		RET

;LOCALIZA EFECTO
;IN HL=(PUNTERO_P)

LOCALIZA_EFECTO:
		LD      L,(IX+0)                ;HL=(PUNTERO_P)
		LD      H,(IX+1)
		LD      A,(HL)
		CP      11000010B
		JR      NZ,LEJP0

		INC     HL
		LD      A,(HL)
		INC     HL
		LD      (IX+00),L
		LD      (IX+01),H
		CALL    INICIA_SONIDO
		RET
		  
LEJP0:      
		INC     HL
		BIT     7,A
		JR      Z,NO_FIN_CANAL_P    ;
		BIT     0,A
		JR      Z,FIN_CANAL_P
		
FIN_NOTA_P: 
		LD      DE,(CANAL_P)
		LD      (IX+0),E
		LD      (IX+1),D
		LD      HL,(PUNTERO_DECP)       ;CARGA PUNTERO DECODER
		PUSH    BC
		CALL    DECODE_CANAL            ;DECODIFICA CANAL
		POP     BC
		LD      (PUNTERO_DECP),HL       ;GUARDA PUNTERO DECODER
		JP      LOCALIZA_EFECTO
		    
FIN_CANAL_P:    
		LD      HL,(PUNTERO_P_DECP)     ;CARGA PUNTERO INICIAL DECODER
		LD      (PUNTERO_DECP),HL
		JR      FIN_NOTA_P
		    
NO_FIN_CANAL_P: 
		LD      (IX+0),L                ;(PUNTERO_A_B_C)=HL GUARDA PUNTERO
		LD      (IX+1),H
		RET

; PAUTA DE LOS 3 CANALES
; IN:(IX):PUNTERO DE LA PAUTA
;    (HL):REGISTRO DE VOLUMEN
;    (IY):REGISTROS DE FRECUENCIA

; FORMATO PAUTA 
;       7    6     5     4   3-0                        3-0  
; BYTE 1 (LOOP|OCT-1|OCT+1|ORNMT|VOL) - BYTE 2 ( | | | |PITCH/NOTA)

PAUTA:      
		BIT     4,(HL)        ;SI LA ENVOLVENTE ESTA ACTIVADA NO ACTUA PAUTA
		RET     NZ

		LD      A,(IY+0)
		LD      B,(IY+1)
		OR      B
		RET     Z

		PUSH    HL
	     
PCAJP4:     
		LD      L,(IX+0)
		LD      H,(IX+1)         
		LD      A,(HL)
	  
		BIT     7,A             ;LOOP / EL RESTO DE BITS NO AFECTAN
		JR      Z,PCAJP0
		AND     00011111B       ;MÁXIMO LOOP PAUTA (0,32)X2!!!-> PARA ORNAMENTOS
		RLCA                    ;X2
		LD      D,0
		LD      E,A
		SBC     HL,DE
		LD      A,(HL)

PCAJP0:     
		BIT     6,A             ;OCTAVA -1
		JR      Z,PCAJP1
		LD      E,(IY+0)
		LD      D,(IY+1)
    
		AND     A
		RRC     D
		RR      E
		LD      (IY+0),E
		LD      (IY+1),D
		JR      PCAJP2
	  
PCAJP1:     
		BIT     5,A             ;OCTAVA +1
		JR      Z,PCAJP2
		LD      E,(IY+0)
		LD      D,(IY+1)

		AND     A
		RLC     E
		RL      D
		LD      (IY+0),E
		LD      (IY+1),D        

PCAJP2:     
		LD      A,(HL)
		BIT     4,A
		JR      NZ,PCAJP6   ;ORNAMENTOS SELECCIONADOS

		INC     HL      ;______________________ FUNCION PITCH DE FRECUENCIA__________________       
		PUSH    HL
		LD      E,A
		LD      A,(HL)      ;PITCH DE FRECUENCIA
		LD      L,A
		AND     A
		LD      A,E
		JR      Z,ORNMJP1

		LD      A,(IY+0)    ;SI LA FRECUENCIA ES 0 NO HAY PITCH
		ADD     A,(IY+1)
		AND     A
		LD      A,E
		JR      Z,ORNMJP1

		BIT     7,L
		JR      Z,ORNNEG
		LD      H,$FF
		JR      PCAJP3
		
ORNNEG:     
		LD      H,0
	  
PCAJP3:     
		LD      E,(IY+0)
		LD      D,(IY+1)
		ADC     HL,DE
		LD      (IY+0),L
		LD      (IY+1),H
		JR      ORNMJP1

PCAJP6:     
		INC     HL      ;______________________ FUNCION ORNAMENTOS__________________    
		PUSH    HL
		PUSH    AF
		LD      A,(IX+24)   ;RECUPERA REGISTRO DE NOTA EN EL CANAL
		LD      E,(HL)      ;
		ADC     A,E       	;+- NOTA 
		CALL    TABLA_NOTAS
		POP     AF  
	  
ORNMJP1:    
		POP     HL
	  
		INC     HL
		LD      (IX+0),L
		LD      (IX+1),H
PCAJP5:     POP     HL
		AND     00001111B   ;VOLUMEN FINAL
		LD      (HL),A
		RET

;NOTA : REPRODUCE UNA NOTA
;IN (A)=CODIGO DE LA NOTA
;   (IY)=REGISTROS DE FRECUENCIA


NOTA:       
		LD      L,C
		LD      H,B
		BIT     4,(HL)
		LD      B,A
		JR      NZ,ENVOLVENTES
		LD      A,B
TABLA_NOTAS:    
		LD      HL,(DATOS_NOTAS)      ;BUSCA FRECUENCIA
		CALL    EXT_WORD
		LD      (IY+0),L
		LD      (IY+1),H
		RET

;IN (A)=CODIGO DE LA ENVOLVENTE
;   (IY)=REGISTRO DE FRECUENCIA

ENVOLVENTES:
		LD      HL,(DATOS_NOTAS)      ;BUSCA FRECUENCIA
		CALL    EXT_WORD
	  
		LD      A,(ENVOLVENTE)      ;FRECUENCIA DEL CANAL ON/OFF

LOCALIZA_ENV:   
		RRA
		JR      FRECUENCIA_OFF
		LD      (IY+0),L
		LD      (IY+1),H
		JR      CONT_ENV
		    
FRECUENCIA_OFF:     
		LD      HL,$0000
		LD      (IY+0),L
		LD      (IY+1),H

;CALCULO DEL RATIO (OCTAVA ARRIBA)

CONT_ENV:   
		PUSH    AF
		PUSH    BC
		AND     00000011B
		LD      B,A
		INC     B
		XOR     A

OCTBC01:    
		ADD     A,12                ;INCREMENTA OCTAVAS
		DJNZ    OCTBC01
		POP     BC                  ;RECUPERA CODIGO DE LA NOTA
		ADD     A,B                   ;EN REGISTRO A CODIGO NOTA
		
		LD      HL,(DATOS_NOTAS)      ;BUSCA FRECUENCIA
		CALL    EXT_WORD
		    
		LD      A,L
		LD      (PSG_REG+11),A
		LD      A,H
		AND     00000011B
		LD      (PSG_REG+12),A
		POP     AF                  ;SELECCION FORMA DE ENVOLVENTE
		    
		RRA
		AND     00000110B           ;$08,$0A,$0C,$0E
		ADD     A,8                
		LD      (PSG_REG+13),A
	 
		RET

;EXTRAE UN WORD DE UNA TABLA
;IN:(HL)=DIRECCION TABLA
;   (A)= POSICION
;OUT(HL)=WORD

EXT_WORD:       
		LD      D,0
		RLCA
		LD      E,A
		ADD     HL,DE
		LD      E,(HL)
		INC     HL
		LD      D,(HL)
		EX      DE,HL
		RET

;;;;;;;; EFECTOS DE SONIDO ;;;;;;;;;;;
		
; INICIA_EFECTO:  
; 		LD      A,B
; 		LD      HL,TABLA_EFECTOS
; 		CALL    EXT_WORD
; 		LD      (PUNTERO_EFECTO),HL
; 		LD      HL,INTERR
; 		SET     3,(HL)
; 		RET       

; REPRODUCE_EFECTO:
; 		LD      HL,INTERR   
; 		BIT     3,(HL)             ;ESTA ACTIVADO EL EFECTO?
; 		RET     Z
; 		LD      HL,(PUNTERO_EFECTO)
; 		LD      A,(HL)
; 		CP      $FF
; 		JP      Z,FIN_EFECTO
; 		LD      B,A                 ;FRECUENCIA FINO
; 		INC     HL
; 		LD      A,(HL)
; 		RRCA
; 		RRCA
; 		RRCA
; 		RRCA
; 		AND     00001111B
; 		LD      C,A                 ;FRECUENCIA GRAVE
; 		LD      A,(HL)
; ;esto lo comento, porque lo considero un bug... si el volumen es 0, al decrecerlo y enmascararlo
; ;pasará a valor F! el máximo volumen!
; ;
; ;       DEC     A                   ;DEC A PARA BAJR VOLUMEN!!
; ;

; 		AND     00001111B

; 		LD   D,A                    ;VOLUMEN
; 		INC     HL                  ;INCREMENTA Y GUARDA EL PUNTERO

; ;
; ;gestión del canal de ruido
; ;
; 		ld a,(hl)
; 		inc hl
; 		ld e,$ff				; la máscara que usaremos con el mixer 
; 								; en principio no toca nada en el mixer 
; 								; (dejaría los canales tal cual)
; 		and a
; 		jr z,nonoise			; si el valor es 0 no hay ruido (no toco nada de los canales)

; 		and %00011111			; si hay ruido le pasamos la máscara para dejarlo en 5 bits
; 		ld (PSG_REG_SEC+6),a	; lo metemos en el buffer para el registro correspondiente del ay
; 		ld e,%11011111			; marcamos el canal C para el ruido como canal por defecto
; nonoise:	

; 		LD      (PUNTERO_EFECTO),HL     
; 		LD      IX,PSG_REG_SEC
; 		LD      A,(CANAL_EFECTOS)   ;SELECCION DE CANAL
; 		CP      1
; 		JR      Z,RS_CANALA
; 		CP      2
; 		JR      Z,RS_CANALB
 
; RS_CANALC:  
; 		LD      (IX+4),B
; 		LD      (IX+5),C
; 		LD      (IX+10),D

; poneruidomixer:		
; 								; este punto es comun a los 3 canales
; 		ld a,e					; cargamos la máscara para el mixer
; 		and (ix+7)				; lo aplicamos desde el buffer de registros del ay
; 		ld (ix+7),a				; dejamos el resultado en el buffer de registros del ay
; 		RET      
  
; RS_CANALA:  
; 		LD      (IX+0),B
; 		LD      (IX+1),C
; 		LD      (IX+8),D
; 		rrc e					; para situar bien la máscara para el canal A en el mixer, 
; 								; desplazamos el bit del ruido dos posiciones a la derecha
; 		rrc e
; 		jr poneruidomixer
	     
; RS_CANALB:  
; 		LD      (IX+2),B
; 		LD      (IX+3),C
; 		LD      (IX+9),D
; 		rrc e					; para situar bien la máscara para el canal B en el mixer, 
; 								; desplazamos el bit  del ruido una posición a la derecha
; 		jr poneruidomixer
	     
; FIN_EFECTO: 
; 		LD      HL,INTERR
; 		RES     3,(HL)  		;DESACTIVA EFECTO
; 		RET         
		
