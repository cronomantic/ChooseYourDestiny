# INCLUDE Demo Adventure

This is a simple demonstration adventure that shows how to use the `INCLUDE` directive to organize your Choose Your Destiny code across multiple files.

## Project Structure

```
include_demo/
  ├── main.cyd         # Main entry point - includes all other files
  ├── variables.cyd    # Variable declarations
  ├── common.cyd       # Common subroutines (ShowStatus, GameOver)
  ├── intro.cyd        # Introduction sequence
  ├── chapter1.cyd     # First chapter - the dungeon escape
  └── chapter2.cyd     # Second chapter - the ogre encounter
```

## How It Works

### main.cyd
The main file is the entry point. It includes all the other files and defines the main flow:
- Includes `variables.cyd` for variable declarations
- Includes `common.cyd` for shared subroutines
- Uses `INCLUDE` to load each chapter at the appropriate point

### variables.cyd
Contains all variable declarations in one place:
- PlayerHealth
- PlayerGold
- HasSword
- CurrentRoom

This makes it easy to see all game state variables at a glance.

### common.cyd
Contains reusable subroutines that are used throughout the adventure:
- `ShowStatus` - Displays player health and gold
- `GameOver` - Handles player death and restart

### Chapter Files
Each chapter is in its own file, making it easy to:
- Work on different parts of the adventure independently
- Test individual chapters
- Keep the code organized

## Compiling This Adventure

To compile this demo adventure, navigate to the example directory and run:

**Windows:**
```batch
..\..\dist\cydc_cli.py 48k main.cyd ..\..\tools\sjasmplus.exe ..\..\
```

**Linux/macOS:**
```bash
../../dist/cydc_cli.py 48k main.cyd ../../external/sjasmplus/sjasmplus ../../
```

Or copy the entire `include_demo` folder to the root of the ChooseYourDestiny directory and modify the `make_adv` script to compile it.

## Key Concepts Demonstrated

1. **Code Organization**: Related code is grouped in separate files
2. **Reusability**: Common subroutines can be used from multiple places
3. **Maintainability**: Easy to find and modify specific parts
4. **Modularity**: Each file has a clear, focused purpose

## Try Modifying It

Try making these changes to learn more:

1. Add a new chapter file (chapter3.cyd) and include it in main.cyd
2. Add a new variable (PlayerLevel) in variables.cyd
3. Create a new subroutine in common.cyd (e.g., ShowInventory)
4. Add more choices and outcomes in the existing chapters

## What You'll Learn

By examining this example, you'll understand:
- How to split a large adventure into manageable files
- Where to put different types of code (variables, functions, story)
- How to organize a multi-chapter adventure
- Best practices for file naming and structure

Enjoy exploring and happy coding!
