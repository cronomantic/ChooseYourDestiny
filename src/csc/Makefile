#CC = x86_64-w64-mingw32-gcc
CC = gcc
CFLAGS  = -O3 -Wall -DNDEBUG -s
RM = rm -f 
FILENAME = csc
EXTENSION = .exe
TARGET = ../../dist/$(FILENAME)$(EXTENSION)

all: $(TARGET)

$(TARGET): csc.c optimize.c compress.c memory.c zx0.h symmetry.c cargs.c symmetry.h cargs.h
	$(CC) $(CFLAGS) -o $(TARGET) csc.c symmetry.c optimize.c compress.c memory.c cargs.c

clean:
	$(RM) *.obj $(TARGET)
