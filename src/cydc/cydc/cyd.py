import os
import sys
import subprocess


from string import Template


class AsmTemplate(Template):
    delimiter = "@"


def get_asm_template(filename):
    filepath = os.path.join(os.path.dirname(__file__), "cyd", filename + ".asm")
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise ValueError(f"{filename} file not found")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return AsmTemplate(text)


def get_asm_plus3(sjasmplus_path, output_path, sfx_asm, filename_script="SCRIPT.DAT"):

    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    d = dict(
        INIT_ADDR="$8000",
        STACK_ADDRESS="$8000",
        INTERPRETER_FILENAME=os.path.join(output_path, "CYD.BIN"),
        INTERPRETER_FILENAME_BASE="CYD.BIN",
        LOADER_FILENAME=os.path.join(output_path, "DISK"),
        FILENAME_SCRIPT=filename_script,
    )

    t = get_asm_template("bank_zx128")
    includes = t.substitute(d)
    t = get_asm_template("plus3dos")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    t = get_asm_template("music_manager")
    includes += t.substitute(d)
    t = get_asm_template("VTII10bG")
    includes += t.substitute(d)
    t = get_asm_template("screen_manager")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    t = get_asm_template("VTII10bG_vars")
    includes += t.substitute(d)
    includes += sfx_asm

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm = t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    t = get_asm_template("cyd_plus3")
    asm += t.substitute(d)
    t = get_asm_template("loaderplus3")
    asm += t.substitute(d)

    # print(asm)
    run_assembler(sjasmplus_path, asm, os.path.join(output_path, "cyd.asm"))


def run_assembler(asm_path, asm, filename, listing=True):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    try:
        with open(filename, "w") as f:
            f.write(asm)
    except OSError:
        sys.exit("ERROR: Can't write temp file.")
    asm_path = os.path.abspath(asm_path)  # Get the absolute path of the executable
    command_line = [asm_path]
    if listing:
        command_line += ["--lst"]
    command_line += [filename]
    try:
        stdout = None
        # stdout=subprocess.DEVNULL
        stderr = None
        # stderr=subprocess.DEVNULL
        result = subprocess.run(
            command_line,
            check=True,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
    finally:
        if os.path.isfile(filename):
            os.remove(filename)
    if result.returncode != 0:
        raise OSError
    # try:
    #    with open(filename + ".zx0", "rb") as f:
    #        chunk = list(f.read())
    # except OSError:
    #    sys.exit("ERROR: Can't read temp file.")
    # finally:
    #    if os.path.isfile(filename + ".zx0"):
    #        os.remove(filename + ".zx0")
    # return chunk
