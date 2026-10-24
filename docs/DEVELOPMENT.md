# Development and release guide

## Layout

- `app.py`, `studio_ui.py`: desktop workflow and background preview coordination.
- `engine.py`, `layers.py`, `rig.py`: motion composition, physics and IK.
- `rounded_scene.py`, `core3d.py`: meshes, UV mapping and 64px depth rasterizer.
- `model_editor.py`, `texture_editor.py`, `protection_editor.py`: staged editors.
- `pixel_ui.py`, `localized_ui.py`, `i18n.py`, `uv_i18n.py`: pixel controls and text.
- `source/`, `defaults/`: required bundled assets and motion presets.
- `fixtures/`: frozen motion regression data; no sibling checkout is needed.
- `user_data/`: private autosave/preferences. Do not commit this directory.
- `tools/build_release.py`: independent allowlist-based archive builder.

Compatibility modules such as `fellow.py` and `uv_panel_legacy.py` are runtime
implementation dependencies. They are not separate tools and must remain in
both archive types. Historical prototype folders are not dependencies.

## Checking changes

Use Python 3.12 on Windows with `requirements-lock.txt`. Renderer and release
checks run with `python -m unittest tests test_release -q`. GUI checks use real
Tk windows and temporary project/preferences directories. Run them on an
interactive Windows desktop: `python -m unittest test_ui test_export_preferences -q`.
When enabled, the provided Windows GitHub Actions workflow template performs
these checks without access to the developer's other tools or personal files.

For rendering changes, compare the vector rasterizer against its reference,
verify 1x export and integer upscaling, and inspect front/side/three-quarter
animation. Outline styling must never change the owner/depth ordering.

Preview workers render the current frame first, then stream remaining frames.
The UI must not synchronously rasterize a missing frame during an incomplete
preview. Old worker revisions are discarded. Physics/IK chain shortcuts are
checked against the full geometry, including root offsets and torso rotations.
Export snapshots the project and renders in a separate process; output files use
the exact same engine as the preview. The export dialog prevents duplicate
submission while work is in progress.

Painting workspaces are coordinated by `paint_workspace.py`. PNG surface records
are defined in `uv_assets.py` and exclude spatial offsets that do not change UVs.
They check mapping provenance, not painted content or alpha silhouettes. Keep
the PNG text record and adjacent UV_Model.json checks consistent. Poll only stable
file saves, retain last good data on failures, and never overwrite the old folder
during adaptation. Sharing links are persisted in character assets and resolved
only between supported counterparts. Painted legacy resources keep their existing
independent sides. Additional meshes, attachment points and skeleton topology
require a separate resource-design change; this painting workflow adds no new bones.

## Clean archives

An optional GitHub Actions workflow is provided at
`tools/workflow-templates/windows-checks.yml`. To enable hosted checks, copy it
to `.github/workflows/checks.yml` using an account with workflow-write permission.
The initial publication keeps it as a template because the publishing login
does not have that permission. Local validation commands remain available.

The three user guides live in `docs/GUIDE.en.md`, `GUIDE.zh-CN.md` and
`GUIDE.ja.md`. Keep their ten sections aligned. `python tools/build_manuals.py`
generates the standalone, dependency-free HTML versions; release builds also
regenerate them before copying documentation. The User guide button and F1 open
the HTML matching the current interface language.

`python tools/build_release.py` writes `dist/FellowStudio3D-source.zip`.
`python tools/build_release.py --portable` writes the Windows x64 archive.
Use `--output <new path.zip>` for a separate build; existing files are refused.
The portable builder uses `sys.base_prefix`, so building from a venv still copies
the base interpreter and stdlib, then only the installed NumPy/Pillow/TkDND
package files and metadata. It does not copy arbitrary site-packages. Native
runtime distribution is currently supported only on Windows x64.
The portable build compiles `tools/Launcher.cs` with the Windows .NET Framework
C# compiler and embeds `FellowStudio3D.ico`. The resulting windowed EXE starts
the adjacent `runtime/pythonw.exe` and `launch.py` without a console window.
`launch.py` records startup exceptions in `user_data/startup-error.log` (or the
normal writable fallback directory). Source users can run `python app.py`.

Before a public release, extract into a fresh path (including spaces), launch,
open Model and UV, and export 1x and 4x. Check SHA256.json and third-party notices.
The application is released under MIT; keep `LICENSE` and all third-party notices
with redistributed packages.

Existing debug screenshots, prototypes and local sessions are intentionally
preserved on the developer's machine but ignored by Git and the builder. Always
review `git status` before committing. Do not publish the entire parent tools
folder or bundle another tool's Git checkout.
