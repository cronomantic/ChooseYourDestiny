# import_demo — native routines (IMPORT / CALL)

A minimal example of CYD's native-routine feature: write a small Z80 routine,
register it with `IMPORT`, and run it with `CALL`.

- [peek.asm](peek.asm) — the native routine. It reads one byte from an arbitrary
  memory address (something the virtual machine cannot do) and returns it through
  the variable array.
- [import_demo.cyd](import_demo.cyd) — the script. It imports `peek`, asks for the
  byte at address `0000h`, and reports the result.

## Build

Compile it like any other example (from this directory), e.g. for 48K:

```
python ../../src/cydc/cydc/cydc.py 48k import_demo.cyd <path-to-sjasmplus> .
```

The routine is assembled in isolation and placed automatically; you only write
the body of `peek.asm` (no `ORG`, no directives).

## How it works

`peek` is entered with `DE = FLAGS` (the base of the 256-byte variable array) and
exchanges data through it: the script puts the address in variables 0 and 1, calls
the routine, and reads the byte back from variable 2. See the manual section
**"Native routines (IMPORT / CALL)"** for the full ABI and the important safety
notes — native code is an advanced, use-at-your-own-risk feature.

Supported targets: 48K, 128K and +3. (This particular demo checks a 48K ROM byte,
so its `IF` branch is written for the 48K model.)
