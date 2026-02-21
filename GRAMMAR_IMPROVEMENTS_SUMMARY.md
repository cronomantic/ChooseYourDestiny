# Grammar Improvements Summary

This document summarizes the two major improvements to the ChooseYourDestiny compiler grammar.

## 1. Lexer Refactoring: Fixed Inverted Semantics

**Problem:** The lexer had backwards semantics compared to the grammar definition.
- Inside `[[ ... ]]`: treated as TEXT accumulation (wrong)
- Outside `[[ ... ]]`: tokenized as CODE (wrong semantically)

**Solution:** Inverted the lexer state machine to match the grammar.
- **INITIAL state** (code mode): Tokenizes executable statements
- **RAWTEXT state**: Accumulates untokenized raw text
- Transitions happen at `[[` and `]]` delimiters

**Benefits:**
- ✅ Natural semantics matching PHP/JSP patterns
- ✅ Cleaner state names (`rawtext` instead of `text`)
- ✅ Eliminated "ugly transformation" in intermediate processing
- ✅ Fully backwards compatible with existing parser

**Files Modified:**
- `src/cydc/cydc/cydc_lexer.py` - Core refactoring
- `LEXER_REFACTORING.md` - Detailed documentation
- `LEXER_REFACTORING_DETAILS.md` - Before/after comparison

**Key Functions Changed:**
- `t_open_text()` → `t_rawtext_open_code()` - Now emits TEXT, enters code mode
- `t_text_TEXT()` → `t_close_code()` - Now just switches modes
- Completely revamped state initialization

---

## 2. Strict Colon Mode: Enforces BASIC-Like Syntax

**Problem:** The grammar allowed two code statements on the same line without a colon separator, which should not be allowed. Example:
```
[[PRINT "hello" GOTO Label1]]  ← Should be: PRINT "hello" : GOTO Label1
```

**Solution:** Added dual-mode grammar with strict enforcement options.

### Default Behavior (Strict Mode)
- Requires colons between consecutive code statements
- Error on violations: `ERROR: Colon required between statements on same line (line X)`
- Follows BASIC tradition (Commodore BASIC, Microsoft BASIC, etc.)

### Backwards Compatibility Mode
- Use `--no-strict-colons` flag to disable strict checking
- Allows legacy code without colons to compile
- Useful for migrating existing code

### Text Transitions (Always Allowed)
- Code followed by text doesn't require a colon
- Example: `[[PRINT "x"]]Text[[GOTO L]]` ✅
- Text naturally separates code blocks

**Implementation:**
- Added `strict_colon_mode` parameter to CydcParser (default: True)
- Added alternative grammar rule: `p_statements_no_colon()`
- Both rule sets coexist; PLY chooses based on input
- Strict mode flags violations but continues parsing for error reporting

**Command-Line Options:**
```bash
cydc.py input.cyd ...                    # Default: strict colons enforced
cydc.py --no-strict-colons input.cyd ... # Backwards compat: colons optional
```

**Benefits:**
- ✅ Prevents accidental code concatenation bugs
- ✅ Encourages clear, readable code
- ✅ Gradual migration path for existing projects
- ✅ Maintains backwards compatibility

**Files Modified:**
- `src/cydc/cydc/cydc_parser.py` - Grammar rules and validation
- `src/cydc/cydc/cydc.py` - Command-line argument and instantiation
- `STRICT_COLON_MODE.md` - Detailed documentation

**Key Functions Changed:**
- `CydcParser.__init__()` - Added `strict_colon_mode` parameter
- `p_statements_no_colon()` - New flexible rule set
- `p_statements()` - Refined strict rule set

---

## Combined Impact

These two changes work together to improve the compiler:

| Aspect | Before | After |
|--------|--------|-------|
| **Lexer Semantics** | Inverted (backwards) | Correct (natural) |
| **State Names** | Misleading (`text` state) | Clear (`rawtext` state) |
| **Statement Syntax** | Ambiguous | Enforced with BASIC-style colons |
| **Backwards Compat** | N/A | Via `--no-strict-colons` |
| **Parser Compatibility** | N/A | 100% (same token stream) |

## Testing Recommendations

1. **Lexer Refactoring Tests:**
   - Verify existing `.cyd` files parse identically
   - Check line number tracking accuracy
   - Test nested `[[ ]]` blocks
   - Validate text compression results match

2. **Strict Colon Mode Tests:**
   - Test strict mode rejects missing colons
   - Test backwards compat mode accepts missing colons  
   - Test text transitions work without colons
   - Test colon-separated statements always work
   - Check error messages are clear

3. **Integration Tests:**
   - Compile example projects in both modes
   - Verify output bytecode is identical
   - Test with different VerboseLevel settings

## Migration Guide

For project maintainers:

1. **Default (Recommended):** Keep strict mode enabled
   - Run `cydc.py project.cyd` as usual
   - Fix any "Colon required" errors
   - Add colons between statements on same line

2. **Gradual Migration:** Use backwards compat temporarily
   - Run `cydc.py --no-strict-colons project.cyd`
   - Fix errors incrementally as needed
   - Remove `--no-strict-colons` flag when ready

3. **Validation:**
   - Test output is identical with/without flag
   - Verify functionality after fixes
   - Document colon usage in project guidelines

## Future Improvements

- [ ] IDE integration with real-time colon validation
- [ ] Automatic colon insertion tool
- [ ] Linting rules for style consistency
- [ ] Extended grammar validation checks
- [ ] Performance analysis of dual grammar path
