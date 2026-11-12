# Delerict — a complete adventure

A small but complete space adventure in Spanish, with ten illustrated locations,
several endings and its own adventure engine written in CYD.

The "Carl Sagan" has reached an alien wreck after months of travel. You are the
only one of the exploration crew who woke up from hibernation. Board the wreck,
recover what it holds, and get back alive: once you take the artifact, the
creature that guards it comes after you, and you have a few turns to reach your
pod, seal the airlock and undock.

- [delerict.cyd](delerict.cyd) — the whole game: the engine (menus, objects,
  exits, turns) and the content (descriptions, puzzles, endings).
- [make_images.py](make_images.py) — generates the location pictures and the
  object icons in pure Python. Run it again after changing a drawing.
- `IMAGES/` — the pictures the build packs: the screen frame (`001.scr`), the
  menu and object icons (`002.scr`), one picture per location (`011.scr` to
  `020.scr`) and the variants that show a location's state (`026.scr` to
  `030.scr`).

## Build

Like every example, it is a project: its `cyd_project.ini` says the main file
(`delerict.cyd`) and the target (128K). Build it where it is, from CYD's folder:

```
make_adv.cmd examples\Delerict        (Windows; or drag the folder onto make_adv.cmd)
./make_adv.sh examples/Delerict       (Linux, macOS)
python make_adventure.py examples/Delerict
```

or open its folder with *Open…* in the GUI. The `.tap` goes to
`examples/Delerict/OUTPUT/`.

To regenerate the pictures (it needs only Python):

```
python examples/Delerict/make_images.py
```

## How to play

Everything is done with menus. Move the cursor with `Q`, `A`, `O` and `P` and
confirm with `Space` or `Enter`. The cursor keys, `Enter` and a Kempston
joystick always work too.

- The command menu is a 3×3 grid. The center option (`-<>-`) switches between
  its three pages: actions, more actions (including the inventory) and options
  (save, load, restart and controls).
- *Controles* chooses a Sinclair (port 1 or 2) or cursor joystick, which works
  together with the keyboard, and redefines the five keys of the menus (up,
  down, left, right, select), or puts the original ones back.
- *Ir a...* opens the movement menu: north, south, east, west, up, down, enter
  and exit. Its center goes back to the commands.
- After a verb, an object selector appears at the bottom, with two arrows, a
  tick and a cross. Move between them with `O` and `P`: confirming an arrow
  shows the previous or next object, the tick picks the one shown and the
  cross cancels.

Each action takes a turn. Some places are dangerous if you stay too long.

## How it works

- **Variables.** Variables 0 to 11 hold where each object is: a location
  number, carried (255), worn (254) or out of play (0). Variables 128 to 140
  hold the rest of the game state (location, flags, turn counters).
  `RAMSAVE` saves variables 0 to 140, so a saved game keeps both.
- **Objects.** `objectAttr` gives each object a bit mask of the verbs it
  accepts (`ObjCanBeCarriedMask`, `ObjCanBeWearMask`, `ObjCanBeOpenedMask`...). The object selector lists the
  objects in the location, then the ones you carry, and keeps only those whose
  mask matches the chosen verb.
- **Exits.** `GenerateCurrLocationExits` builds the exits of the current
  location from the flags in `flagA` (the hatch, the outer door, the lamp, the
  alien door, the console), so a puzzle opens a way just by setting a bit.
- **Turns.** `TickTurn` runs before every command: radiation in the engine
  room without the suit, the creature in the nursery, and the final chase.
- **Pictures.** Each location shows picture `loc + 10`; when its state
  changes (the door forced, the console powered...), it shows `loc + 20`
  instead.
- **Endings.** Deaths and endings set `gameState` and return to the main loop,
  which shows the ending and starts again, so no `GOSUB` is left pending.
- **Controls.** `ControlsMenu` uses `MENUJOY` for the joystick and `MENUKEY`
  for the keys. Redefining asks for each key with `INKEY(0)`, refuses a key
  already chosen and the control codes (`Enter` and the cursor keys always
  work), and applies the five keys at the end. The settings live in the
  interpreter, so they take no variables and are not saved with the game.

## Walkthrough

<details>
<summary>Spoilers</summary>

1. *Sur* to the crew area. *Coger* and *Ponerse* the space suit. *Abrir* the
   hatch.
2. *Bajar* to the hold. *Abrir* the cabinet and *Coger* the pistol.
3. *Sur* to the engine room (safe with the suit on) and *Coger* the
   multi-tool.
4. *Norte*, *Subir*, *Sur* to the airlock. *Usar* the controls to open the
   outer door, and *Salir* to the wreck.
5. *Usar* the multi-tool on the sealed door. *Norte* to the gallery.
6. *Encender* the suit's lamp. *Este* to the nursery and *Usar* the pistol:
   the creature flees. *Coger* the energy cell.
7. *Oeste*, *Norte* to the control room. *Usar* the cell on the console, and
   *Norte* to the sanctuary.
8. *Coger* the artifact. The chase starts: *Sur*, *Sur*, *Sur*, *Entrar* to
   the airlock, *Usar* the controls to close the outer door, *Norte*,
   *Norte* to the cabin, and *Usar* the command console to undock.

</details>
