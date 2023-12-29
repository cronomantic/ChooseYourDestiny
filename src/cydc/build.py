import PyInstaller.__main__
import shutil
import os

DST_PATH = "../../dist/cydc/"
SRC_PATH = "./"
SRC_FILES = [
    "cydc_cli.py",
    "cydc/cydc.py",
    "cydc/cydc_codegen.py",
    "cydc/cydc_font.py",
    "cydc/cydc_lexer.py",
    "cydc/cydc_parser.py",
    "cydc/cydc_txt_compress.py",
    "cydc/__init__.py",
    "cydc/ply/lex.py",
    "cydc/ply/yacc.py",
    "cydc/ply/__init__.py",
]

for file in SRC_FILES:
    srcPath = os.path.join(SRC_PATH, file)
    dstPath = os.path.join(DST_PATH, file)
    os.makedirs(os.path.dirname(dstPath), exist_ok=True)
    shutil.copy(srcPath, dstPath)

PyInstaller.__main__.run(
    [
        "cydc_cli.py",
        "--onefile",
        "--name",
        "cydc",
        "--distpath",
        "../../dist",
        "--paths=./cydc",
        "--paths=./cydc/ply",
        "--hidden-import=cydc_txt_compress",
        "--hidden-import=cydc_parser",
        "--hidden-import=cydc_codegen",
        "--hidden-import=cydc_font",
    ]
)
