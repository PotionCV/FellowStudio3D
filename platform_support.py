"""Small desktop adapters; no shell commands or global system changes."""
import ctypes
import os
import subprocess
import sys
from pathlib import Path

# Family and typographic-family names from bundled Boutique9.ttf's name table.
# Core Text commonly exposes name ID 16; Windows Tk commonly exposes name ID 1.
PIXEL_FAMILIES = (
    '精品点阵体9×9 1.9 R', 'BoutiqueBitmap9x9 1.9',
    'BoutiqueBitmap9x9 1.9 R', '精品點陣體9×9 1.9',
    '精品點陣體9×9 1.9 R', '精品点阵体9×9 1.9',
)


def pixel_font_family(families, fallback):
    available = {name.casefold(): name for name in families}
    for candidate in PIXEL_FAMILIES:
        if candidate.casefold() in available:
            return available[candidate.casefold()]
    return fallback


def register_fonts(root):
    try:
        if sys.platform == 'win32':
            for path in Path(root).glob('Boutique*.ttf'):
                ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)
        elif sys.platform == 'darwin':
            cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
            ct = ctypes.CDLL('/System/Library/Frameworks/CoreText.framework/CoreText')
            cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
            cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
            cf.CFRelease.argtypes = [ctypes.c_void_p]
            ct.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
            ct.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
            for path in Path(root).glob('Boutique*.ttf'):
                raw = os.fsencode(path.resolve())
                url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
                if url:
                    try: ct.CTFontManagerRegisterFontsForURL(url, 1, None)
                    finally: cf.CFRelease(url)
    except (AttributeError, OSError):
        pass  # Tk's system font remains available.


def wheel_units(delta):
    if not delta: return 0
    if sys.platform == 'darwin' and abs(delta) < 120:
        return -int(delta) or (-1 if delta > 0 else 1)
    return -int(delta / 120)


def open_folder(path):
    path = str(Path(path).resolve())
    if sys.platform == 'win32': os.startfile(path)
    else: subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', path])


def set_icon(window, root):
    import tkinter as tk
    try:
        if sys.platform == 'win32': window.iconbitmap(default=str(Path(root) / 'FellowStudio3D.ico'))
        else:
            window._app_icon = tk.PhotoImage(master=window, file=str(Path(root) / 'source/FellowStudio3D-icon.png'))
            window.iconphoto(True, window._app_icon)
    except (tk.TclError, OSError): pass


def check_fonts():
    """Print the native Tk result, rather than claiming registration succeeded."""
    import tkinter as tk
    from tkinter import font
    register_fonts(Path(__file__).resolve().parent)
    root = tk.Tk();root.withdraw()
    try:
        families = font.families(root)
        fallback = font.nametofont('TkDefaultFont', root=root).actual('family')
        selected = pixel_font_family(families, fallback)
        actual = font.Font(root=root, family=selected, size=-24).actual('family')
        print('Tk:', root.tk.call('info', 'patchlevel'), 'window system:', root.tk.call('tk', 'windowingsystem'))
        print('Pixel font candidates:', [name for name in families if name.casefold() in {x.casefold() for x in PIXEL_FAMILIES}])
        print('Selected:', selected, '| actual:', actual)
        print('Pixel font available:', selected != fallback)
    finally: root.destroy()


if __name__ == '__main__': check_fonts()
