VER = $(shell git log --format="%h" -n 1)

.PHONY: clean loader interpreter all


LOADER_FILENAME = DISK
INTERPRETER_FILENAME = CYD.BIN

LOADER = ../../dist/$(LOADER_FILENAME)
INTERPRETER = ../../dist/$(INTERPRETER_FILENAME)

SCRIPT_FILENAME = SCRIPT.DAT
BEEPFX_FILENAME = SFX.BIN
START_ADDRESS = 0x8000

ASM = ../../bin/sjasmplus.exe
ASM_PARAMS = --color=on
ASM_DEFINES = -DINIT_ADDR=$(START_ADDRESS)
ASM_DEFINES += -D_FILENAME_SCRIPT_='"'$(SCRIPT_FILENAME)'"'
ASM_DEFINES += -D_FILENAME_BEEPFX_='"'$(BEEPFX_FILENAME)'"'

ASM_DEFINES += -D_LOADER_FILENAME_='"'$(LOADER_FILENAME)'"'
ASM_DEFINES += -D_INTERPRETER_FILENAME_='"'$(INTERPRETER_FILENAME)'"'
ASM_DEFINES += -D_INTERPRETER_FILENAME_BARE_=$(INTERPRETER_FILENAME)


CYD_DEPS = bank_zx128.asm dzx0_turbo.asm plus3dos.asm interpreter.asm
CYD_DEPS += screen_manager.asm text_manager.asm
CYD_DEPS += music_manager.asm VTII10bG.asm 

dist: build $(LOADER_FILENAME) $(INTERPRETER_FILENAME)

build: interpreter loader

interpreter: $(INTERPRETER)

loader: $(LOADER)

$(LOADER) : $(LOADER_FILENAME)
	cp -f $(LOADER_FILENAME) $(LOADER) 

$(INTERPRETER): $(INTERPRETER_FILENAME)
	cp -f $(INTERPRETER_FILENAME) $(INTERPRETER)

$(LOADER_FILENAME) : loaderplus3.asm $(INTERPRETER_FILENAME)
	$(ASM) $(ASM_PARAMS) $(ASM_DEFINES) loaderplus3.asm

$(INTERPRETER_FILENAME) : main.asm vars.sym $(CYD_DEPS)
	$(ASM) $(ASM_PARAMS) $(ASM_DEFINES) --lst main.asm

vars.sym: vars.asm sysvars.asm VTII10bG_vars.asm
	$(ASM) $(ASM_PARAMS) --sym=vars.sym vars.asm

clean:
	rm -f $(LOADER) $(INTERPRETER) vars.sym main.lst $(INTERPRETER_FILENAME) $(LOADER_FILENAME)
