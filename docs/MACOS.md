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

The pixel font is registered before Tk opens its first window. Both English
(`BoutiqueBitmap9x9 1.9`) and localized family names are recognized. If you still
see a system font, run `sh ./FellowStudio3D.sh --check-fonts` and include its output
in a bug report. A manual fallback is to open `Boutique9.ttf` in Font Book, install
it for your user, then fully quit and relaunch the tool; automatic registration
does not install fonts on your system.

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

## Small displays and window resizing

The window fits the screen, but controls start at the saved manual scale
(default 1.5). Window dimensions alone never shrink the UI. After startup layout
has settled, automatic fitting is only activated if the actual preview falls
below 240 logical pixels wide or 140 high. Once triggered, it reduces scale in
small steps until the preview reaches 280x180, or the 0.75 scale floor is reached.
Side panels still fit available width. A− / A＋ remains available. Automatic
fitting never overwrites the saved scale or changes exported sprite dimensions.
Mac behavior still requires real-device validation.

## Dropdown hangs and diagnostics

On macOS, option lists now open as ordinary transient picker windows, without
an override-redirect window or a new input grab. Selection work is deferred until
the picker has closed. Escape, the close button or clicking the parent dismisses
it. Windows keeps its existing borderless dropdown. Preview progress is consumed
in small batches and repeated identical layout requests are skipped.

This is a targeted mitigation, not a claim that a Mac freeze was reproduced or
fixed on hardware. Run `sh ./FellowStudio3D.sh --check` to report the actual Python,
macOS and Tcl/Tk runtime versions. On macOS the app creates
`user_data/runtime-diagnostics.log` (or the configured/fallback data folder).
If its event loop stops responding for 15 seconds, that file records Python thread
stacks automatically. Wait about 20 seconds before force-quitting. On restart,
the previous session's log is retained as `runtime-diagnostics.previous.log`.
These diagnostics contain runtime details and stack/file locations, not a project
snapshot. Callback exceptions are also recorded.

Separately, old Tk releases have a documented native-menu hang on macOS 27.
The CPython maintainers report fixed Tk builds in the python.org macOS installers
for Python 3.13.17 and 3.14.9 (and later releases in those series). See the
[official issue](https://github.com/python/cpython/issues/158053).
That system-menu issue is not established as the cause of this app's custom
picker freeze; update advice depends on the actual installed runtime.
