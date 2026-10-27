# macOS source launcher (experimental)

Windows portable ZIPs contain a Windows runtime and cannot run on macOS.
Use the complete source folder, including `source/`, `defaults/`, `examples/`
and `docs/`. No native `.app` or bundled Mac Python runtime is provided.

1. Install Python 3.12 or newer using the macOS installer from
   [python.org](https://www.python.org/downloads/macos/). It includes Tcl/Tk.
2. Extract the source folder to a writable location. In Terminal, enter that
   folder, then run:

   ```sh
   sh ./FellowStudio3D.sh
   ```

First launch requires internet to install NumPy, Pillow and tkinterdnd2 in the
local `.venv-macos` environment. Later launches reuse it. Paths containing spaces
are supported. For an explicit Python installation:

```sh
FELLOWSTUDIO3D_PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 sh ./FellowStudio3D.sh
```

Run `sh ./FellowStudio3D.sh --check` to check dependencies and opening a Tk
window without starting the editor. Keep the folder in place after setup;
if you move it or change Python, recreate `.venv-macos` in the new location.

Projects and settings use `user_data/`. If that location is not writable,
macOS uses `~/Library/Application Support/FellowStudio3D/`. The environment
variable `FELLOWSTUDIO3D_DATA_DIR` can select another data folder.

Command-S saves, Command-Z undoes, Command-Shift-Z redoes. The UV editor also
accepts Command-C/V for image copy/paste. Fonts are registered only for the
current process, with a system-font fallback. PNG drag/drop is optional;
use the file picker if unavailable.

**Validation boundary:** developed on Windows. Script syntax, adapter tests,
source packaging and Windows regressions are checked; Intel/Apple Silicon Mac
launching, native fonts, drag/drop and clipboard interoperability still need
real macOS validation. This is experimental source compatibility, not a verified
Mac release. Report `user_data/startup-error.log` (or the fallback data folder)
if startup fails; dependency errors appear directly in Terminal.

中文：这是实验性 Mac 源码启动方式，不是 Mac 免安装包。先安装 python.org 的
Python 3.12+，在完整源码目录运行 `sh ./FellowStudio3D.sh`；首次启动需要联网。
尚未在 Mac 真机验证，不能保证所有桌面交互都与 Windows 一致。

日本語：実験的な macOS ソース起動です。python.org の Python 3.12 以降を
インストールし、ソースフォルダーで `sh ./FellowStudio3D.sh` を実行してください。
初回はネット接続が必要です。実機の Mac では未検証です。
