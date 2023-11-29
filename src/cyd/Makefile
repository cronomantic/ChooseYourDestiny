VER = $(shell git log --format="%h" -n 1)

.PHONY: clean loader interpreter all

SCRIPT_FILENAME = SCRIPT.DAT
BEEPFX_FILENAME = SFX.BIN
START_ADDRESS = 0x8000

ASM = ../../bin/sjasmplus.exe
ASM_PARAMS = --color=on
ASM_DEFINES = -DINIT_ADDR=$(START_ADDRESS)
ASM_DEFINES += -D_FILENAME_SCRIPT_='"'$(SCRIPT_FILENAME)'"'
ASM_DEFINES += -D_FILENAME_BEEPFX_='"'$(BEEPFX_FILENAME)'"'

CYD_DEPS = bank_zx128.asm dzx0_turbo.asm plus3dos.asm interpreter.asm
CYD_DEPS += screen_manager.asm text_manager.asm 

build: interpreter loader

interpreter: CYD.BIN

loader: DISK

DISK: loaderplus3.asm CYD.BIN
	$(ASM) $(ASM_PARAMS) $(ASM_DEFINES) loaderplus3.asm

CYD.BIN : main.asm vars.sym $(CYD_DEPS)
	$(ASM) $(ASM_PARAMS) $(ASM_DEFINES) --lst main.asm

vars.sym: vars.asm sysvars.asm
	$(ASM) $(ASM_PARAMS) --sym=vars.sym vars.asm

clean:
	rm -f CYD.BIN vars.sym main.lst DISK
