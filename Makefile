DISK_NAME:=test
DISK_LABEL:=TEST
TEXT_FILENAME:=test.txt
EXPORT_FILENAME:=test.json

.PHONY: clean clean_all build testtap

SCRIPT_FILENAME = SCRIPT.DAT
BEEPFX_FILENAME = SFX.BIN
BEEPFX_ASM_FILENAME = SFX.asm
CYDC_PATH := ./src/cydc/cydc
CYDCTAP_PATH := ./src/cydtap/cydtap

MKP3FS := ./tools/mkp3fs.exe

SCR_LIST := $(shell find ./IMAGES -type f -iregex '\.\/IMAGES\/[0-9][0-9][0-9].scr')
CSC_LIST := $(SCR_LIST:%.scr=%.csc)

PT3_LIST := $(shell find ./TRACKS -type f -iregex '\.\/TRACKS\/[0-9][0-9][0-9].pt3')

FILELIST = ./dist/DISK ./dist/CYD.BIN $(SCRIPT_FILENAME) $(CSC_LIST) $(PT3_LIST)

ifneq (,$(wildcard ./$(BEEPFX_FILENAME)))
FILELIST += $(BEEPFX_FILENAME)
endif

build: $(DISK_NAME).DSK testtap

testtap: $(EXPORT_FILENAME)
	python $(CYDCTAP_PATH)/cydtap.py -v -i ./IMAGES -t ./TRACKS -s $(BEEPFX_ASM_FILENAME) $(EXPORT_FILENAME) test.tap ./tools/zx0 ./tools/sjasmplus

$(DISK_NAME).DSK: $(FILELIST)
	$(MKP3FS) -180 -label $(DISK_LABEL) $(DISK_NAME).DSK $(FILELIST)

%.csc: %.scr
	./dist/csc.exe -f -o=$@ $<

$(EXPORT_FILENAME): $(TEXT_FILENAME)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
	python $(CYDC_PATH)/cydc.py -v -x -T tokens.json $(TEXT_FILENAME) $(EXPORT_FILENAME)
else
# Token file exists, use it...
	python $(CYDC_PATH)/cydc.py -v -x -t tokens.json $(TEXT_FILENAME) $(EXPORT_FILENAME)
endif

$(SCRIPT_FILENAME): $(TEXT_FILENAME)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
	python $(CYDC_PATH)/cydc.py -v -T tokens.json $(TEXT_FILENAME) $(SCRIPT_FILENAME)
else
# Token file exists, use it...
	python $(CYDC_PATH)/cydc.py -v -t tokens.json $(TEXT_FILENAME) $(SCRIPT_FILENAME)
endif

clean_all: clean
	rm -f tokens.json

clean:
	rm -f $(DISK_NAME).DSK
	rm -f $(CSC_LIST)
	rm -f $(SCRIPT_FILENAME)
