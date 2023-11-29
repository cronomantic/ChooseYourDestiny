

CHARS	            EQU 23606  ; Pointer to ROM/RAM Charset
TVFLAGS             EQU 23612  ; TV Flags
UDG	                EQU 23675  ; Pointer to UDG Charset
COORDS              EQU 23677  ; Last PLOT coordinates
FLAGS2	            EQU 23681  ;
ECHO_E              EQU 23682  ;
DFCC                EQU 23684  ; Next screen addr for PRINT
DFCCL               EQU 23686  ; Next screen attr for PRINT
S_POSN              EQU 23688
ATTR_P              EQU 23693  ; Current Permanent ATTRS set with INK, PAPER, etc commands
ATTR_T	            EQU 23695  ; temporary ATTRIBUTES
P_FLAG	            EQU 23697  ;
MEM0                EQU 23698  ; Temporary memory buffer used by ROM chars
BORDCR              EQU $5C48  ; Border color
FRAMES              EQU $5C78  ; Frame counter
LASTK               EQU $5C08  ; Last key pressed
REPDEL              EQU $5C09  ; Time in 1/50s before key repeats
REPPER              EQU $5C0A  ; Delay in 1/50s between key repeats
PIP                 EQU $5C39  ; Length of keyboard click

SCR_PXL_SIZE        EQU 32*192
SCR_ATT_SIZE        EQU 32*24
SCR_SIZE            EQU SCR_ATT_SIZE + SCR_PXL_SIZE

SCR_PXL             EQU $4000
SCR_ATT             EQU SCR_PXL + SCR_PXL_SIZE

KEY_SCAN            EQU $028E
KEY_TEST            EQU $031E
KEY_CODE            EQU $0333

BEEPFX              EQU $C000
SFX_ID              EQU BEEPFX+1
