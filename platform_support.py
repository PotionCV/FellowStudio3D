"""Small desktop adapters; no shell commands or global system changes."""
import ctypes
import os
import subprocess
import sys
from pathlib import Path


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
