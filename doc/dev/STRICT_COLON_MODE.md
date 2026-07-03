# Strict Colon Mode: Grammar Enhancement

## Overview

The compiler now enforces strict BASIC-like syntax for statement separators. By default, statements on the same line inside a code block `[[ ... ]]` must be separated by colons (`:`), just like in Commodore BASIC or other classic BASIC dialects.

## Rules

### Strict Mode (Default: `--strict-colons` implied, or use `--no-strict-colons` to disable)

In strict mode, consecutive code statements **must** be separated by colons:

**✅ Valid:**
```
[[
    PRINT "Hello"
    GOTO Label
]]
```

```
[[
    PRINT "Hello" : GOTO Label
]]
```

**❌ Invalid (will produce an error):**
```
[[
    PRINT "Hello" GOTO Label
]]
```

### Text Transitions

Text following a code statement does **not** require a colon separator. This is automatically handled:

**✅ Always valid:**
```
[[PRINT "Hello"]]World here[[GOTO Label]]
```

This is parsed as:
- Code: `PRINT "Hello"`
- Text: `World here`
- Code: `GOTO Label`

The text acts as a natural separator between code blocks.

### Compatible Exception: Text Statement Pairs

Code statements followed by `TEXT` tokens (raw text content) do NOT require colons:

**✅ Valid:**
```
[[PRINT "Hello"]] Some text [[GOTO Label]]
```

Equivalent to:
```
[[
    PRINT "Hello"
]]
Some text
[[
    GOTO Label
]]
```

## Command-Line Options

### Enable Strict Mode (Default)
```bash
cydc.py input.cyd ...
# or explicitly:
cydc.py --strict-colons input.cyd ...  # (this is implicit)
```

When strict mode is enabled:
- Two code statements without a colon separator produce an **error**
- Compilation stops, and the error is reported
- Examples: `PRINT "x" GOTO Label` → ERROR

### Disable Strict Mode (Backwards Compatibility)
```bash
cydc.py --no-strict-colons input.cyd ...
```

When backwards compatibility mode is enabled:
- Two code statements without a colon are **allowed**
- Code parses silently without errors
- Legacy files that don't use colons will compile

## Examples

### Example 1: Multi-statement Line (Strict)

**Source:**
```cyd
[[
    SET x TO 5 : PRINT x : GOTO end
    #end
]]
```

This requires colons between statements. Without them → **ERROR**.

### Example 2: With Text Blocks

**Source:**
```cyd
[[PRINT "Question:"]]
What's your favorite color?
[[INK 2 : PRINT "Red" : GOTO q1
#q1
]]
```

The text `What's your favorite color?` between `]]` and `[[` acts as a separator, so colons are still needed between `INK 2`, `PRINT`, and `GOTO`.

### Example 3: Backwards Compat Mode

**Source (would fail in strict mode):**
```cyd
[[
    PRINT "Hello" GOTO Label1
]]
```

**Compilation:**
```bash
cydc.py --no-strict-colons input.cyd ...
# ✅ Success - parses without errors
```

vs.

```bash
cydc.py input.cyd ...
# ❌ Error: Colon required between statements on same line (line X)
```

## Implementation Details

### Grammar Changes

The parser now has two rule sets:

1. **Strict Rules** (default): `statements : statements COLON statement`
2. **Flexible Rules**: `statements : statements statement` (allowed in non-strict mode)

Both rules coexist in the grammar. PLY's parser chooses the best path based on the input. When strict mode is active, the flexible path triggers an error.

### Error Reporting

When a missing colon is detected in strict mode:
```
ERROR: Colon required between statements on same line (line 12)
```

The line number indicates where the violation occurs.

### Backwards Compatibility

The `--no-strict-colons` flag ensures that legacy `*.cyd` files written without colon separators continue to work. This allows gradual migration to strict syntax.

## Design Rationale

This enforces good coding practices:
- **Clarity**: Each statement is clearly delimited
- **BASIC Tradition**: Matches conventions from Commodore BASIC, Microsoft BASIC, etc.
- **Error Prevention**: Prevents accidental code concatenation bugs
- **Gradual Migration**: Existing code can use backwards compat mode while new code uses strict mode

## Testing

### Test Case 1: Strict Mode Default
```bash
echo '[[PRINT "a" GOTO x]]' | cydc ...
# Expected: ERROR about missing colon
```

### Test Case 2: With Colon
```bash
echo '[[PRINT "a" : GOTO x]]' | cydc ...
# Expected: Success
```

### Test Case 3: Multiple Statements
```bash
echo '[[PRINT "a" PRINT "b"]]' | cydc --no-strict-colons ...
# Expected: Success (backwards compat)
```

```bash
echo '[[PRINT "a" PRINT "b"]]' | cydc ...
# Expected: ERROR
```

### Test Case 4: Text Separator
```bash
echo '[[PRINT "a"]] Text [[PRINT "b"]]' | cydc ...
# Expected: Success (text acts as separator)
```

## See Also

- [LEXER_REFACTORING.md](LEXER_REFACTORING.md) - Lexer state machine fixes
- Grammar rules in `cydc_parser.py`:
  - `p_statements_no_colon()` - flexible rule set
  - `p_statements()` - strict rule set  
  - `p_statements_text_statement()` - text transitions
