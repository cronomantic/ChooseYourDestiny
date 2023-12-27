DISK_NAME=test
DISK_LABEL=TEST
TEXT_FILENAME=test.txt

.PHONY: clean clean_all build

SCRIPT_FILENAME = SCRIPT.DAT
BEEPFX_FILENAME = SFX.BIN

MKP3FS = ./tools/mkp3fs.exe

SCR_LIST := $(shell find ./IMAGES -type f -iregex '\.\/IMAGES\/[0-9][0-9][0-9].scr')
CSC_LIST := $(SCR_LIST:%.scr=%.csc)

PT3_LIST := $(shell find ./TRACKS -type f -iregex '\.\/TRACKS\/[0-9][0-9][0-9].pt3')

FILELIST = ./dist/DISK ./dist/CYD.BIN $(SCRIPT_FILENAME) $(CSC_LIST) $(PT3_LIST)

ifneq (,$(wildcard ./$(BEEPFX_FILENAME)))
FILELIST += $(BEEPFX_FILENAME)
endif

build: $(DISK_NAME).DSK

$(DISK_NAME).DSK: $(FILELIST)
	$(MKP3FS) -180 -label $(DISK_LABEL) $(DISK_NAME).DSK $(FILELIST)

%.csc: %.scr
	./dist/csc.exe -f -o=$@ $<

$(SCRIPT_FILENAME): $(TEXT_FILENAME)
ifeq (,$(wildcard ./tokens.json))
# Token file does not exists, create a new one
	python ./src/cydc/cydc_cli.py -v -T tokens.json $(TEXT_FILENAME) $(SCRIPT_FILENAME)
else
# Token file exists, use it...
	python ./src/cydc/cydc_cli.py -v -t tokens.json $(TEXT_FILENAME) $(SCRIPT_FILENAME)
endif

clean_all: clean
	rm -f tokens.json

clean:
	rm -f $(DISK_NAME).DSK
	rm -f $(CSC_LIST)
	rm -f $(SCRIPT_FILENAME)
