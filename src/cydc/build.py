import PyInstaller.__main__

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
