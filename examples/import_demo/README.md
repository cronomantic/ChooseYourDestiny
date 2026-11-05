# import_demo — native routines (IMPORT / CALL)

A minimal example of CYD's native-routine feature: write a small Z80 routine,
register it with `IMPORT`, and run it with `CALL`.

- [peek.asm](peek.asm) — the native routine. It reads one byte from an arbitrary
  memory address (something the virtual machine cannot do) and returns it through
  the variable array.
- [import_demo.cyd](import_demo.cyd) — the script. It imports `peek`, asks for the
  byte at address `0000h`, and reports the result.

## Build

Like every example, it is a project: its `cyd_project.ini` says the main file
(`import_demo.cyd`) and the target (48K). Build it where it is, from CYD's
folder:

```
make_adv.cmd examples\import_demo        (Windows; or drag the folder onto make_adv.cmd)
./make_adv.sh examples/import_demo       (Linux, macOS)
python make_adventure.py examples/import_demo
```

or open its folder with *Open…* in the GUI. The `.tap` goes to
`examples/import_demo/OUTPUT/`.

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
