# CYD Include Mechanism - Example

This example demonstrates how to use the `INCLUDE` directive to organize a Choose Your Destiny adventure into multiple files.

## Project Structure

```
include_example/
  ├── main.cyd              # Main entry point
  ├── config/
  │   └── variables.cyd     # Variable declarations
  ├── lib/
  │   └── common.cyd        # Common utility functions
  └── chapters/
      ├── intro.cyd         # Introduction chapter
      ├── chapter1.cyd      # Chapter 1
      └── chapter2.cyd      # Chapter 2
```

## File Contents

### main.cyd
```cyd
[[
/* Load configuration and common functions */
INCLUDE "config/variables.cyd"
INCLUDE "lib/common.cyd"

/* Setup initial state */
PAPER 0
INK 7
BORDER 0
CLEAR
]]

#Start
[[INCLUDE "chapters/intro.cyd"]]
[[GOTO Chapter1]]

#Chapter1
[[INCLUDE "chapters/chapter1.cyd"]]

#Chapter2
[[INCLUDE "chapters/chapter2.cyd"]]

#TheEnd
[[GOSUB ShowTheEnd]]
[[END]]
```

### config/variables.cyd
```cyd
[[
/* Game state variables */
DECLARE 0 AS PlayerHealth
DECLARE 1 AS PlayerGold
DECLARE 2 AS HasSword
DECLARE 3 AS HasKey
DECLARE 4 AS CurrentChapter

/* Initialize variables */
SET @PlayerHealth TO 100
SET @PlayerGold TO 0
SET @HasSword TO 0
SET @HasKey TO 0
SET @CurrentChapter TO 1
]]
```

### lib/common.cyd
```cyd
[[
/* Common utility functions */

#ShowStatus
INK 6
PRINT "Health: "
PRINT @PlayerHealth
PRINT " Gold: "
PRINT @PlayerGold
INK 7
NEWLINE
RETURN

#ShowTheEnd
CENTER
INK 2
PRINT "THE END"
INK 7
NEWLINE
PRINT "Thanks for playing!"
RETURN

#GameOver
CENTER
INK 2
PRINT "GAME OVER"
INK 7
NEWLINE
WAITKEY
GOTO Start
]]
```

### chapters/intro.cyd
```cyd
[[CENTER]]
Welcome to the Adventure!
[[NEWLINE : NEWLINE]]
You wake up in a dark dungeon...
[[NEWLINE]]
[[GOSUB ShowStatus]]
[[NEWLINE]]
```

### chapters/chapter1.cyd
```cyd
You are in a stone corridor. There are two doors ahead.
[[NEWLINE : NEWLINE]]

[[OPTION GOTO LeftDoor]]Take the left door
[[OPTION GOTO RightDoor]]Take the right door
[[CHOOSE]]

#LeftDoor
[[CLEAR]]
You found a treasure chest!
[[SET @PlayerGold TO 50]]
[[NEWLINE]]
[[GOSUB ShowStatus]]
[[GOTO Chapter2]]

#RightDoor
[[CLEAR]]
A trap! You lose health.
[[SET @PlayerHealth TO 50]]
[[NEWLINE]]
[[GOSUB ShowStatus]]
[[IF @PlayerHealth > 0 THEN
    GOTO Chapter2
ELSE
    GOSUB GameOver
ENDIF]]
```

### chapters/chapter2.cyd
```cyd
[[CLEAR]]
You reach the exit of the dungeon!
[[NEWLINE : NEWLINE]]

[[IF @PlayerGold > 0 THEN
    INK 6
    PRINT "You escaped with treasure!"
    INK 7
ELSE
    PRINT "You escaped, but with no treasure."
ENDIF]]
[[NEWLINE : NEWLINE]]
[[GOTO TheEnd]]
```

## Compiling the Example

To compile this adventure:

```bash
# Navigate to your project directory
cd include_example

# Compile (adjust paths as needed)
cydc_cli.py 48k main.cyd path/to/sjasmplus output/

# Or using the make_adventure script
make_adventure.py -n MyAdventure 48k main.cyd path/to/sjasmplus output/
```

## Benefits of Using INCLUDE

1. **Organization**: Keep related code together in separate files
2. **Reusability**: Share common functions across multiple adventures
3. **Maintainability**: Easier to find and fix bugs in specific files
4. **Collaboration**: Multiple people can work on different files simultaneously
5. **Modularity**: Test individual chapters or components separately

## Important Notes

- The `INCLUDE` directive must be placed inside `[[ ]]` code blocks
- The `INCLUDE` directive is processed before compilation
- Circular includes (A includes B, B includes A) are detected and cause errors
- Maximum include depth is 20 levels
- Relative paths are resolved from the directory containing the file with the INCLUDE directive
- Included files can have their own `[[ ]]` blocks; the preprocessor handles this automatically
- Error messages will show the original filename and line number where errors occur
- CYD uses `/* */` for comments, not `//`
