TonA	EQU 0
TonB	EQU 2
TonC	EQU 4
Noise	EQU 6
Mixer	EQU 7
AmplA	EQU 8
AmplB	EQU 9
AmplC	EQU 10
Env	    EQU 11
EnvTp	EQU 13

;vars from here can be stripped
;you can move VARS to any other address

VTR_VARS:

;ChannelsVars
	STRUCT	CHP
;reset group
PsInOr	DB 0
PsInSm	DB 0
CrAmSl	DB 0
CrNsSl	DB 0
CrEnSl	DB 0
TSlCnt	DB 0
CrTnSl	DW 0
TnAcc	DW 0
COnOff	DB 0
;reset group

OnOffD	DB 0

;IX for PTDECOD here (+12)
OffOnD	DB 0
OrnPtr	DW 0
SamPtr	DW 0
NNtSkp	DB 0
Note	DB 0
SlToNt	DB 0
Env_En	DB 0
Flags	DB 0
 ;Enabled - 0,SimpleGliss - 2
TnSlDl	DB 0
TSlStp	DW 0
TnDelt	DW 0
NtSkCn	DB 0
Volume	DB 0
	ENDS

ChanA	DS CHP
ChanB	DS CHP
ChanC	DS CHP

;GlobalVars
DelyCnt	DB 0
CurESld	DW 0
CurEDel	DB 0
Ns_Base_AddToNs
Ns_Base	DB 0
AddToNs	DB 0

AYREGS:

VT_	DS 256 ;CreatedVolumeTableAddress

EnvBase	EQU VT_+14

T1_	EQU VT_+16 ;Tone tables data depacked here

T_OLD_1	EQU T1_
T_OLD_2	EQU T_OLD_1+24
T_OLD_3	EQU T_OLD_2+24
T_OLD_0	EQU T_OLD_3+2
T_NEW_0	EQU T_OLD_0
T_NEW_1	EQU T_OLD_1
T_NEW_2	EQU T_NEW_0+24
T_NEW_3	EQU T_OLD_3

NT_	DS 192 ;CreatedNoteTableAddress

;local var
Ampl	EQU AYREGS+AmplC

VTR_VAR0END	EQU VT_+16 ;INIT zeroes from VARS to VAR0END-1

VTR_VARSEND EQU $

;--------------------------------
PLAY_MODULE     EQU %00000001
MODULE_LOADED   EQU %10000000


