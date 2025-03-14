NAME:=test
CYD_FILENAME:=$(NAME).cyd

TAP_TARGET:=128k

.PHONY: clean clean_all disk test_disk tape test_tape all

BEEPFX_ASM_FILENAME = SFX.asm

CYDC_PATH := ./src/cydc/cydc
CSC_PATH := ./dist

ASM := ./tools/sjasmplus.exe
MKP3FS := ./tools/mkp3fs.exe

SCR_LIST := $(shell find ./IMAGES -type f -iregex '\.\/IMAGES\/[0-9][0-9][0-9].scr')
CSC_LIST := $(SCR_LIST:%.scr=%.csc)
PT3_LIST := $(shell find ./TRACKS -type f -iregex '\.\/TRACKS\/[0-9][0-9][0-9].pt3')

FILELIST = $(CYD_FILENAME) $(CSC_LIST) $(PT3_LIST) 
#$(BEEPFX_ASM_FILENAME)

EXTRA_PARAM = -v -code
#EXTRA_PARAM += -trim
#EXTRA_PARAM += -pause 5
#EXTRA_PARAM += -720
#EXTRA_PARAM += -wyz

ifneq (,$(wildcard ./charset.json))
EXTRA_PARAM += -c ./charset.json
endif

ifneq (,$(wildcard ./IMAGES/LOAD.SCR))
EXTRA_PARAM += -scr ./IMAGES/LOAD.SCR
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
	python $(CYDC_PATH)/cydc.py -T tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -T tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
endif
else
# Token file exists, use it...
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -t tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -t tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS plus3 $(CYD_FILENAME) $(ASM) $(MKP3FS) .
endif
endif

$(NAME).TAP: $(FILELIST)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -T tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) $(TAP_TARGET) $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -T tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS $(TAP_TARGET) $(CYD_FILENAME) $(ASM)  $(MKP3FS) .
endif
else
# Token file exists, use it...
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -t tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) $(TAP_TARGET) $(CYD_FILENAME) $(ASM) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -t tokens.json $(EXTRA_PARAM) -csc ./IMAGES -trk ./TRACKS $(TAP_TARGET) $(CYD_FILENAME) $(ASM) $(MKP3FS) .
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
