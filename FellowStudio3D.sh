#!/bin/sh
# Source launcher. A Windows portable runtime cannot run on macOS.
set -eu
APP_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
cd "$APP_DIR"
if [ "$(uname -s)" != Darwin ]; then
    echo "This launcher requires macOS. On Windows use FellowStudio3D.bat." >&2
    exit 1
fi
PYTHON=${FELLOWSTUDIO3D_PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Install Python 3.12 or newer from python.org, then run this script again." >&2
    exit 1
fi
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 or newer is required"; import tkinter' || {
    echo "Use the macOS Python installer from python.org (includes Tcl/Tk)." >&2
    exit 1
}
ENV_DIR="$APP_DIR/.venv-macos"
if [ ! -x "$ENV_DIR/bin/python" ]; then
    "$PYTHON" -m venv "$ENV_DIR"
fi
if ! "$ENV_DIR/bin/python" -c 'import numpy, PIL, tkinterdnd2' >/dev/null 2>&1; then
    echo "Installing dependencies in .venv-macos (first launch requires internet)..."
    "$ENV_DIR/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
fi
if [ "${1:-}" = '--check' ]; then
    "$ENV_DIR/bin/python" -c 'import platform, tkinter, numpy, PIL; print(platform.platform()); print("Python", platform.python_version(), "Tk API", tkinter.TkVersion, "NumPy", numpy.__version__, "Pillow", PIL.__version__); w=tkinter.Tk(); w.withdraw(); w.update(); print("Tcl", w.tk.call("info", "patchlevel"), "Tk runtime", w.tk.call("package", "provide", "Tk")); w.destroy(); print("Tk window check passed")'
    exit 0
fi
if [ "${1:-}" = '--check-fonts' ]; then
    exec "$ENV_DIR/bin/python" "$APP_DIR/platform_support.py"
fi
exec "$ENV_DIR/bin/python" "$APP_DIR/launch.py"
