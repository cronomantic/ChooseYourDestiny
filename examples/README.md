# ChooseYourDestiny — Examples

This directory contains sample adventures and technical demos for the CYD engine.
Each example is a **project**: a folder with its main `.cyd` file, the assets it
needs and a `cyd_project.ini` that says which is the main file and the target.
The main file is `test.cyd`, except in `Delerict` (`delerict.cyd`),
`import_demo` (`import_demo.cyd`) and `include_demo` (`main.cyd`); the target is
48K, except in `test` and `Delerict` (128K).

Every example also ships its compiled `.tap`, so you can load it straight into
an emulator to see it running. To build one yourself, build it where it is, from
CYD's folder:

- **Windows:** `make_adv.cmd examples\test`, or drag the example's folder onto
  `make_adv.cmd`.
- **Linux/macOS:** `./make_adv.sh examples/test`
- **GUI:** open the example's folder with *Open…* and compile it.
- **Command line:** `python make_adventure.py examples/test` (on Windows,
  `dist\python\python make_adventure.py examples\test`).

A target given after the folder (`make_adv.cmd examples\test 48k`) is used
instead of the project's. The build writes its files to the example's `OUTPUT/`
folder (and creates its `tokens.json` if it has none).

In the repository, `python tools/build_example_taps.py` regenerates the shipped
tape of every example with the current compiler, reading each one's
`cyd_project.ini`.

## Basic

| Example | What it demonstrates |
|---------|----------------------|
| [`test`](test/) | Introduction to the engine: text, colors, options and jumps. The starting point. |
| [`multicolumn_menu`](multicolumn_menu/) | Laying out option menus across multiple columns. |
| [`guess_the_number`](guess_the_number/) | A complete "guess the number" game: `RANDOM`, a 6-column menu and game logic. |
| [`input_test`](input_test/) | Keyboard input with `INKEY()` and character arrays via `[@ptr]` indirection (`inputStr`/`printStr`). |
| [`menu_keys`](menu_keys/) | Letting the player choose the controls: redefine the menu keys with `MENUKEY` (asking with `INKEY(0)`), choose a Sinclair or cursor joystick with `MENUJOY`, and try them on a 3×3 grid. Explained in the tutorial. |
| [`math_library`](math_library/) | Using `lib/math16_32.cyd`: 16/32-bit arithmetic (`mul1632`, `add32`, `print32`) to compute a score. |
| [`strings_library`](strings_library/) | Using `lib/strings.cyd`: read a name from the keyboard (`strInput`) and print it (`strPrint`, `strLen`). |
| [`sprites`](sprites/) | Using `lib/sprites.cyd`: a walking character and a bouncing ball drawn with masks over a scene, moved by characters and by pixels, each saving its background in its own slot. |
| [`sprites_px`](sprites_px/) | Using `lib/sprites_px.cyd`: the same scene with the character walking pixel by pixel (`sprPX`). |
| [`windows`](windows/) | Splitting the screen into independent areas with `WINDOW` and `MARGINS`. |

## Intermediate

| Example | What it demonstrates |
|---------|----------------------|
| [`ETPA_ejemplo`](ETPA_ejemplo/) | A "choose your own adventure" gamebook structure with branching sections. |
| [`include_demo`](include_demo/) | Organizing a large project across multiple files with the `INCLUDE` directive. |

## Advanced graphics

| Example | What it demonstrates |
|---------|----------------------|
| [`blit`](blit/) | Introduction to `BLIT` for moving graphic blocks. |
| [`blit_island`](blit_island/) | Advanced `BLIT` graphics work. |
| [`Rocky_Horror_Show`](Rocky_Horror_Show/) | Character animation. |
| [`CYD_presents`](CYD_presents/) | Complex visual effects. |
| [`Golden_Axe_select_character`](Golden_Axe_select_character/) | Dynamic character selection with color effects. |

## Complete projects

| Example | What it demonstrates |
|---------|----------------------|
| [`SCUMM_16`](SCUMM_16/) | A SCUMM/LucasArts-style point-and-click interface. |
| [`Delerict`](Delerict/) | A small but complete space adventure in Spanish, with location pictures, puzzles, save/load and an escape against the clock, on its own engine — see its [README](Delerict/README.md). |

## Native code (Z80)

| Example | What it demonstrates |
|---------|----------------------|
| [`import_demo`](import_demo/) | Calling an external native Z80 routine from CYD with `IMPORT` / `CALL` — see its [README](import_demo/README.md). |
| [`inline_asm`](inline_asm/) | Inline `ASM ... ENDASM` native routines invoked with `CYD_CALL` — see its [README](inline_asm/README.md). |

---

New to CYD? Start with [`test`](test/), then [`guess_the_number`](guess_the_number/)
and [`input_test`](input_test/). See the manual and tutorial (in `documentation/`)
for the full language reference and a step-by-step walkthrough.
