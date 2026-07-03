# ChooseYourDestiny — Examples

This directory contains sample adventures and technical demos for the CYD engine.
Each example is a folder with a `test.cyd` source (plus any assets it needs).

To build one, point the compiler at its `test.cyd` (see the manual, section
*Workflow* / *Flujo de trabajo*), for example:

```
make_adv 48k examples/test/test.cyd
```

## Basic

| Example | What it demonstrates |
|---------|----------------------|
| [`test`](test/) | Introduction to the engine: text, colours, options and jumps. The starting point. |
| [`multicolumn_menu`](multicolumn_menu/) | Laying out option menus across multiple columns. |
| [`guess_the_number`](guess_the_number/) | A complete "guess the number" game: `RANDOM`, a 6-column menu and game logic. |
| [`input_test`](input_test/) | Keyboard input with `INKEY()` and character arrays via `[@ptr]` indirection (`inputStr`/`printStr`). |
| [`math_library`](math_library/) | Using `lib/math16_32.cyd`: 16/32-bit arithmetic (`mul1632`, `add32`, `print32`) to compute a score. |
| [`strings_library`](strings_library/) | Using `lib/strings.cyd`: read a name from the keyboard (`strInput`) and print it (`strPrint`, `strLen`). |
| [`windows`](windows/) | Splitting the screen into independent areas with `WINDOW` and `MARGINS`. |

## Intermediate

| Example | What it demonstrates |
|---------|----------------------|
| [`ETPA_ejemplo`](ETPA_ejemplo/) | A "choose your own adventure" gamebook structure with branching sections. |
| [`include_demo`](include_demo/) | Organising a large project across multiple files with the `INCLUDE` directive. |

## Advanced graphics

| Example | What it demonstrates |
|---------|----------------------|
| [`blit`](blit/) | Introduction to `BLIT` for moving graphic blocks. |
| [`blit_island`](blit_island/) | Advanced `BLIT` graphics work. |
| [`Rocky_Horror_Show`](Rocky_Horror_Show/) | Character animation. |
| [`CYD_presents`](CYD_presents/) | Complex visual effects. |
| [`Golden_Axe_select_character`](Golden_Axe_select_character/) | Dynamic character selection with colour effects. |

## Complete projects

| Example | What it demonstrates |
|---------|----------------------|
| [`SCUMM_16`](SCUMM_16/) | A SCUMM/LucasArts-style point-and-click interface. |
| [`Delerict`](Delerict/) | A full adventure built on its own engine on top of CYD. |

---

New to CYD? Start with [`test`](test/), then [`guess_the_number`](guess_the_number/)
and [`input_test`](input_test/). See the manual and tutorial (in `documentation/`)
for the full language reference and a step-by-step walkthrough.
