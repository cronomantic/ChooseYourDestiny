"""The window icon of CYD's GUIs (make_adventure_gui.py, mld2rom_gui.py).

assets/cyd_icon_<size>.png and assets/cyd_icon.ico (tools/make_gui_icons.py):
the red "CYD" letters for the small sizes, the whole logo for the large ones.
"""

import os
import sys
import tkinter as tk

ICON_SIZES = (16, 24, 32, 48, 64, 128)
_icon = {"ico": None, "photos": [], "handles": []}


def set_app_id(app_id):
    """On Windows, an application of its own for the taskbar: otherwise it
    groups the window with python.exe and shows Python's icon instead of CYD's.
    Call it before creating the first window."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass  # Non‑critical – skip silently


def init_window_icon(root, base_path):
    """Give the application its icon: every PNG size to Tk (the default of all
    its windows), which is what Linux and macOS use; on Windows, the .ico."""
    assets = os.path.join(base_path, "assets")
    paths = [os.path.join(assets, f"cyd_icon_{size}.png") for size in ICON_SIZES]
    try:
        _icon["photos"] = [tk.PhotoImage(file=p) for p in paths if os.path.isfile(p)]
        if _icon["photos"]:
            root.iconphoto(True, *_icon["photos"])
    except Exception:
        pass  # Non‑critical – skip silently
    ico = os.path.join(assets, "cyd_icon.ico")
    _icon["ico"] = ico if os.path.isfile(ico) else None
    set_windows_icon(root)


def set_windows_icon(window):
    """On Windows, Tk makes the small icon (the title bar) out of a large image,
    whatever images it gets: ask Windows for each size of the .ico instead, the
    small one for the title bar and the big one for the taskbar and Alt+Tab.
    Call it for each new top-level window too."""
    if sys.platform != "win32" or not _icon["ico"]:
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                                      ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                        wintypes.LPARAM]
        window.update_idletasks()
        hwnd = int(window.wm_frame(), 16)
        # (ICON_SMALL, SM_CXSMICON), (ICON_BIG, SM_CXICON)
        for which, metric in ((0, 49), (1, 11)):
            size = user32.GetSystemMetrics(metric)
            handle = user32.LoadImageW(None, _icon["ico"], 1, size, size, 0x10)
            if handle:  # IMAGE_ICON, LR_LOADFROMFILE; kept alive while the GUI runs
                _icon["handles"].append(handle)
                user32.SendMessageW(hwnd, 0x80, which, handle)  # WM_SETICON
    except Exception:
        pass  # Non‑critical – skip silently
