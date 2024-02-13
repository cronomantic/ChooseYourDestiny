DISK_NAME:=test
DISK_LABEL:=TEST
TEXT_FILENAME:=test.txt

.PHONY: clean clean_all build test

BEEPFX_ASM_FILENAME = SFX.asm

CYDC_PATH := ./src/cydc/cydc

ASM := ./tools/sjasmplus.exe
MKP3FS := ./tools/mkp3fs.exe
ZX0 := ./tools/zx0.exe

SCR_LIST := $(shell find ./IMAGES -type f -iregex '\.\/IMAGES\/[0-9][0-9][0-9].scr')
CSC_LIST := $(SCR_LIST:%.scr=%.csc)
PT3_LIST := $(shell find ./TRACKS -type f -iregex '\.\/TRACKS\/[0-9][0-9][0-9].pt3')

FILELIST = $(TEXT_FILENAME) $(CSC_LIST) $(PT3_LIST) $(BEEPFX_ASM_FILENAME)

build: $(DISK_NAME).DSK

%.csc: %.scr
	./dist/csc.exe -f -o=$@ $<

$(DISK_NAME).DSK: $(FILELIST)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -T tokens.json -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(TEXT_FILENAME) $(ASM) $(ZX0) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -T tokens.json -csc ./IMAGES -trk ./TRACKS plus3 $(TEXT_FILENAME) $(ASM) $(ZX0) $(MKP3FS) .
endif
else
# Token file exists, use it...
ifneq (,$(wildcard ./$(BEEPFX_ASM_FILENAME)))
	python $(CYDC_PATH)/cydc.py -v -t tokens.json -csc ./IMAGES -trk ./TRACKS -sfx $(BEEPFX_ASM_FILENAME) plus3 $(TEXT_FILENAME) $(ASM) $(ZX0) $(MKP3FS) .
else
	python $(CYDC_PATH)/cydc.py -v -t tokens.json -csc ./IMAGES -trk ./TRACKS $(TEXT_FILENAME) plus3 $(ASM) $(ZX0) $(MKP3FS) .
endif
endif

test: $(DISK_NAME).DSK
	./EsPectrum.exe $(DISK_NAME).DSK

clean_all: clean
	rm -f tokens.json

clean:
	rm -f $(DISK_NAME).DSK
	rm -f $(CSC_LIST)
	rm -f DISK SCRIPT.DAT CYD.BIN cyd.lst
