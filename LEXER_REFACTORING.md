# Lexer Refactoring: Fixed Inverted Grammar Semantics

## Problem

The original lexer had **inverted semantics** compared to the grammar definition:

### Original Implementation (Backwards)
```python
# WRONG: "text" state accumulated CODE content
def t_open_text(self, t):
    r"\[\["
    t.lexer.begin("text")  # Misleading: "text" state actually processes CODE

def t_text_TEXT(self, t):  # Misleading: "TEXT" at ][ boundaries
    r"\]\]"
    # Extracted content is CODE, not TEXT
```

**Result:** Even though files use `[[ CODE ]]` with TEXT outside, the lexer was treating `[[ ... ]]` as TEXT accumulation and everything else as CODE tokens.

### Grammar Definition (Natural)
```
Example source file:
    [[PRINT "test"]]         <- CODE block
This is text outside        <- TEXT (untokenized)
```

The grammar conceptually defines:
- **Outside `[[ ... ]]`**: Raw TEXT (like PHP/JSP)
- **Inside `[[ ... ]]`**: Executable CODE (statements, expressions)

## Solution

### Refactored Implementation (Correct)
Now the lexer semantics match the grammar:

```python
# CORRECT: "rawtext" state accumulates TEXT outside delimiters
# lexer starts in rawtext mode
def input(self, data):
    ...
    self.lexer.begin("rawtext")  # Start: accumulate raw text

# When [[ is found while accumulating text, emit accumulated text and enter code mode
def t_rawtext_open_code(self, t):
    r"\[\["
    string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos - 2]
    # Extract accumulated TEXT
    t.type, t.value = self._parse_string(string, t.lexer.lineno)
    t.lexer.begin("INITIAL")  # Enter CODE mode
    return t

# When ]] is found while in code mode, exit and return to text accumulation
def t_close_code(self, t):
    r"\]\]"
    self.txt_pos = t.lexer.lexpos
    t.lexer.begin("rawtext")  # Return to TEXT mode
    return None
```

## Key Changes

1. **State Renaming**: `"text"` state → `"rawtext"` state
   - `"rawtext"`: Accumulates untokenized raw text (default state)
   - `"INITIAL"`: Tokenizes code statements

2. **State Transitions**
   - **START**: Begin in `"rawtext"` state
   - **On `[[`** (in rawtext): Emit accumulated text as TEXT token, enter INITIAL
   - **On `]]`** (in INITIAL): Track position, return to rawtext without emitting
   - **At EOF**: Emit any remaining accumulated text

3. **Mode Semantics**
   - **RAWTEXT mode**: Ignores code keywords, accumulates all characters
   - **INITIAL mode**: Recognizes all code tokens (IF, PRINT, LABEL, etc.)

## Benefits

✅ **Eliminated Ugly Transformation**: No longer need to work around inverted logic
✅ **Natural Semantics**: Lexer state names and behavior now match grammar intent  
✅ **Cleaner Code**: Simpler to reason about and maintain
✅ **Same Output**: Parser receives the same token stream (compatible)
✅ **Better Error Messages**: Can now clearly distinguish code/text context

## Compatibility

The refactoring is **fully backward compatible** with the existing parser:
- Same token types are emitted
- Same state machine transitions occur
- Only the semantic meaning of state names changed (and their initial starting point)

## Example: How It Works Now

**Input:**
```
Hello world!
[[
    PRINT "test"
    GOTO Label1
]]
More text here
```

**Lexical Analysis Flow:**
```
Initial state: rawtext
1. Accumulate: "Hello world!\n"
2. Find [[: Emit TEXT("Hello world!\n"), enter INITIAL
3. Tokenize: PRINT, STRING("test"), PRINT, GOTO, ID(Label1)
4. Find ]]: Record position, enter rawtext
5. Accumulate: "\nMore text here"
6. EOF: Emit TEXT("\nMore text here")
```

**Tokens Emitted:**
```
TEXT("Hello world!\n")
PRINT
STRING("test")
PRINT
GOTO
ID("Label1")
TEXT("\nMore text here")
```

The parser already handles this interleaved code/text structure naturally through its grammar rules.
