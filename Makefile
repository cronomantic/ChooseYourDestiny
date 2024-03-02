NAME:=test
CYD_FILENAME:=$(NAME).cyd

TAP_TARGET:=48k

.PHONY: clean clean_all disk test_disk tape test_tape all

BEEPFX_ASM_FILENAME = SFX.asm

CYDC_PATH := ./ChooseYourDestiny/src/cydc/cydc
CSC_PATH := ./ChooseYourDestiny/dist

ASM := ./ChooseYourDestiny/tools/sjasmplus.exe
MKP3FS := ./ChooseYourDestiny/tools/mkp3fs.exe

SCR_LIST := $(shell find ./IMAGES -type f -iregex '\.\/IMAGES\/[0-9][0-9][0-9].scr')
CSC_LIST := $(SCR_LIST:%.scr=%.csc)
PT3_LIST := $(shell find ./TRACKS -type f -iregex '\.\/TRACKS\/[0-9][0-9][0-9].pt3')

FILELIST = $(CYD_FILENAME) $(CSC_LIST) $(PT3_LIST) $(BEEPFX_ASM_FILENAME)


ifneq (,$(wildcard ./charset.json))
CHARSET_PARAM = -c ./charset.json
else
CHARSET_PARAM =
endif

disk: $(NAME).DSK

tape: $(NAME).TAP

all: tape disk

%.csc: %.scr
	$(CSC_PATH)/csc.exe -f -o=$@ $<

$(NAME).DSK: $(FILELIST)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -T tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -T tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
endif
else
# Token file exists, use it...
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -t tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -t tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS $(CYD_FILENAME) plus3 $(ASM) $(MKP3FS) .
endif
endif

$(NAME).TAP: $(FILELIST)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -T tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) $(TAP_TARGET) $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -T tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS $(TAP_TARGET) $(CYD_FILENAME) $(ASM)  $(MKP3FS) .
endif
else
# Token file exists, use it...
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -t tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) $(TAP_TARGET) $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -t tokens.json $(CHARSET_PARAM) -scr ./IMAGES/LOAD.SCR -csc ./IMAGES -pt3 ./TRACKS $(CYD_FILENAME) $(TAP_TARGET) $(ASM) $(MKP3FS) .
endif
endif

test_disk: $(NAME).DSK
	./EsPectrum.exe $(NAME).DSK

test_tape: $(NAME).TAP
	./EsPectrum.exe $(NAME).TAP

clean_all: clean
	rm -f tokens.json

clean:
	rm -f $(NAME).DSK
	rm -f $(NAME).TAP
	rm -f $(CSC_LIST)
	rm -f DISK SCRIPT.DAT CYD.BIN cyd.lst
