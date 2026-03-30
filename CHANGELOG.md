# Changelog

All notable changes to ChooseYourDestiny are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] — after v1.3.2

No functional changes since v1.3.2. This entry tracks work in progress on the current development branch.

---

## [v1.3.2] — 2026-03-27

### Changed
- Updated PDF documentation (manuals and tutorials) in English and Spanish to reflect recent changes introduced in v1.3.0 and v1.3.1.

---

## [v1.3.1] — 2026-03-25

### Added
- **MLD/Dandanator cartridge support**: New compilation target for the Dandanator Mini cartridge format, allowing adventures to be distributed as Dandanator ROM images.
- **ZX7 compression for MLD targets**: Experimental ZX7 compression support for MLD and mld128 targets, reducing the size of text and screen data stored in Dandanator slots.
- **`mld2rom.py` tool**: New standalone tool that converts an MLD adventure file into a Dandanator-compatible ROM image, including validation of the MLD structure and automatic padding to 512 KB.
- **New Makefile targets**: Added `mld`, `mld_music`, and `rom` build targets to `Makefile` to streamline Dandanator ROM builds from the command line.
- **Dandanator ROM included**: Bundled `dandanator-mini.rom` (the Dandanator firmware) as a build resource for ROM packaging.
- **CI/CD pipeline**: Added a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the full test suite and regression tests automatically on every push.
- **Regression test auto-discovery**: Replaced the previous hardcoded list of example tests with an automatic discovery mechanism that finds and tests all available `.cyd` examples without manual maintenance.
- **MLD-specific test suite**: New test modules (`test_mld_footer.py`, `test_mld_index_mapping.py`, `test_mld_rom_emulation.py`, `test_zx7.py`) covering MLD footer structure, slot-index mapping, ROM emulation correctness, and ZX7 compression roundtrips.

### Fixed
- **MLD runtime slot mapping**: The MLD runtime now always maps text and screen data directly from Dandanator ROM slots, preventing incorrect memory mapping when running on real hardware or accurate emulators.
- **ROM emulation in MLD**: Fixed the MLD ROM emulation layer so that the Spectrum ROM is correctly restored when reading keyboard input, and the normal intro screen is displayed on startup instead of a blank screen.
- **Base ROM size error**: `mld2rom.py` now accepts a 3584-byte Dandanator firmware file (the actual distributed size) and automatically pads it to the required 512 KB, instead of rejecting files that are not already full-size.
- **Updated SjASMPlus assembler**: Bundled SjASMPlus updated to a newer build with bug fixes and improved compatibility.

### Changed
- **Manual updates**: English and Spanish manuals updated to document the new MLD/Dandanator build targets and usage.
- **`make_adv.cmd` / `make_adv.sh`**: Updated build scripts to support the new MLD compilation targets.

---

## [v1.3.0] — 2026-03-07

### Added
- **INCLUDE directive**: Source files can now `#INCLUDE` other `.cyd` files, enabling projects to be split across multiple files for easier organisation and reuse. A new preprocessor module (`cydc_preprocessor.py`) handles recursive inclusion with circular-include detection.
- **Increment and decrement operators**: The language now supports `++` and `--` as shorthand for incrementing and decrementing integer variables (e.g. `counter++`).
- **Internationalisation (i18n) of tools**: All Python tools (`cydc.py`, `cyd_chr_conv.py`, etc.) now use `gettext` for user-facing strings. Spanish locale files (`.po`/`.mo`) are included and compiled automatically during the distribution build, so the tools display Spanish messages when the system language is Spanish.
- **Graphical user interface for distribution builder**: `make_dist.py` now includes a GUI (`make_adventure_gui.py`) with a form-based interface for configuring and launching distribution builds without using the command line.
- **Automation master script (`automate.py`)**: A new top-level automation script orchestrates the full development and release workflow — locale extraction, PDF generation, distribution packaging, and wiki synchronisation — from a single command (`--all` or `--release` flags).
- **`update_locales.py`**: Automates extraction of translatable strings from Python source files and updates the `.po` locale files.
- **`update_wiki.py`**: Synchronises the repository's documentation Markdown files with the GitHub wiki.
- **PDF documentation in distribution package**: A `documentation/` directory containing the English and Spanish manuals and tutorials in PDF format is now included in the release ZIP.
- **"Delerict" example adventure**: A new example adventure demonstrating advanced features.
- **INCLUDE directive documentation and examples**: `INCLUDE_EXAMPLE.md` and tutorial sections (English and Spanish) explain how to use multi-file projects.
- **`AUTOMATION.md`**: Comprehensive documentation for the automation system.
- **`ADVENTURE_SCRIPTS.md`**: Guide to the adventure build scripts (`make_adv.sh`, `make_adv.cmd`, etc.).
- **`DISTRIBUTION.md`**: Documentation for the distribution build system.
- **Regression test suite for examples**: All built-in examples are now compiled and checked automatically as part of the test suite to catch regressions.
- **`setup_embedded_python.py` / `verify_embedded_python.py`**: Scripts for setting up and verifying the bundled Windows Python distribution used in the release package.
- **UTF-8 character support expanded**: Additional characters added to the UTF-8 to ZX Spectrum character conversion tables.

### Fixed
- **Colon parsing errors**: Corrected a regression where colons used as statement separators in certain positions caused parse errors.
- **gettext bug in `cydc`**: Fixed an initialisation bug that prevented the Spanish locale from loading correctly in the compiler.
- **Grammar and error reporting**: Improved the parser's error reporting infrastructure to give more precise source locations for syntax errors.
- **INCLUDE example**: Corrected errors in the bundled INCLUDE directive example.

### Changed
- **Embedded Python updated to 3.14.3**: The bundled Windows Python runtime used for the distribution package is now Python 3.14.3.
- **SjASMPlus updated**: The bundled SjASMPlus assembler has been updated to a newer version.
- **Syntax highlighter updated**: The VSCode syntax highlighter submodule updated to support the new `INCLUDE` directive and `++`/`--` operators.
- **Cross-platform distribution builder**: The distribution build script (`make_dist.py`) now works natively on Windows, Linux, and macOS, replacing the previous shell-script-only approach.
- **GUI appearance configuration**: The GUI tool now saves its window layout and settings to disk between sessions.
- **Manuals updated**: English and Spanish manuals updated to document the INCLUDE directive, new operators, and GUI tool.

---

## [v1.2.1] — 2025-07-25

### Fixed
- Fixed a bug in the `CHOOSE IF WAIT` command that caused it to behave incorrectly under certain conditions.

---

*For changes prior to v1.2.1, see the [git log](https://github.com/cronomantic/ChooseYourDestiny/commits/main).*
