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

    DEVICE ZXSPECTRUM48

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
KSTATE              EQU $5C00

SCR_PXL_SIZE        EQU 32*192
SCR_ATT_SIZE        EQU 32*24
SCR_SIZE            EQU SCR_ATT_SIZE + SCR_PXL_SIZE

SCR_PXL             EQU $4000
SCR_ATT             EQU SCR_PXL + SCR_PXL_SIZE
SCR_ADDR            EQU SCR_PXL



    IFDEF USE_ROM_KEYB
KEY_SCAN          EQU $028E
K_TEST            EQU $031E
K_DECODE          EQU $0333
    ENDIF
