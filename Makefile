# Development builds of a project with the compiler in src/ (not dist/).
#
#   make tape PROJECT=examples/test          # TAP for TAP_TARGET
#   make disk PROJECT=../my_game              # +3 DSK
#   make mld | mld_music | rom | esxdos
#   make clean PROJECT=...                    # its OUTPUT folder
#
# The project's settings (images, tracks, tokens...) are in its
# cyd_project.ini, as with make_adventure.py, which does the build.

PROJECT ?= examples/test
TAP_TARGET ?= 48k
PY ?= python

# Base ROM template for Dandanator (required for the 'rom' target)
BASE_ROM := ./external/dandanator-mini.rom

ASM := ./tools/sjasmplus.exe
CYDC := ./src/cydc/cydc/cydc.py

EXTRA_PARAM = -v -code
#EXTRA_PARAM += -trim
#EXTRA_PARAM += -pause 5
#EXTRA_PARAM += -720
#EXTRA_PARAM += -wyz

MAKE_ADV = $(PY) ./make_adventure.py --compiler $(CYDC) --sjasmplus $(ASM) $(EXTRA_PARAM)

# The project's name and output folder, as make_adventure.py sees them.
describe = $(shell $(PY) ./make_adventure.py --describe $(PROJECT) | sed -n 's/^$(1)=//p')
NAME = $(call describe,NAME)
OUTPUT = $(call describe,OUTPUT)

.PHONY: clean tape disk esxdos mld mld_music rom all test_disk test_tape

tape:
	$(MAKE_ADV) $(PROJECT) $(TAP_TARGET)

disk:
	$(MAKE_ADV) $(PROJECT) plus3

esxdos:
	$(MAKE_ADV) $(PROJECT) esxdos

mld:
	$(MAKE_ADV) $(PROJECT) mld

mld_music:
	$(MAKE_ADV) $(PROJECT) mld128

rom: mld
	$(PY) ./mld2rom.py -b $(BASE_ROM) -o "$(OUTPUT)/$(NAME).ROM" "$(OUTPUT)/$(NAME).MLD"

all: tape disk

test_disk: disk
	./EsPectrum.exe "$(OUTPUT)/$(NAME).DSK"

test_tape: tape
	./EsPectrum.exe "$(OUTPUT)/$(NAME).tap"

clean:
	rm -rf "$(OUTPUT)"
