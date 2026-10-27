# Development and release guide

UI additions must follow the [workspace/ownership framework](UI-DESIGN.zh-CN.md): peer model categories, object-first controls, whole-action toolbar wrapping, explicit draft versus live settings, and session-only export options.

## Layout

- `app.py`, `studio_ui.py`: desktop workflow and background preview coordination.
- `engine.py`, `layers.py`, `rig.py`: motion composition, physics and IK.
- `retro_animation.py`: deterministic local cel reuse in `engine.visible`, after physics and before shared preview/export rendering. Defaults off; never store stylized samples in motion recipes.
- `game_actions.py`, `motion_timing.py`: staged actions and shared playback timing.
- `aerial_actions.py`: periodic swim/hover generators and explicit airborne contact.
- `directional_export.py`: bounded-size directional atlases, frame descriptors and staged output.
- `pose_animation.py`, `pose_animation_editor.py`: authored pose cards and staged four-view animation editing.
- `hand_props.py`, `hand_prop_editor.py`: paintable closed props and wrist-local placement.
- `tail_motion.py`: transferable three-joint tail channels and ordinary layer blending.
- `resource_library.py`, `resource_browser.py`: public allowlisted catalog, multilingual search and staged character/motion audition using the shared cancellable preview worker.
- `sculpt.py`, `motion_resources.py`: seam-consistent shaping and portable poses.
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
checks run with `python -m unittest tests test_extensions test_release -q`. GUI checks use real
Tk windows and temporary project/preferences directories. Run them on an
interactive Windows desktop: `python -m unittest test_ui test_export_preferences -q`.
When enabled, the provided Windows GitHub Actions workflow template performs
these checks without access to the developer's other tools or personal files.

For rendering changes, compare the vector rasterizer against its reference,
verify 1x export and integer upscaling, and inspect front/side/three-quarter
animation. Outline styling must never change the owner/depth ordering.

Preview workers render the current frame first, then stream remaining frames.
The creation library reuses this worker and enables Apply only after the current
revision completes. Filtering never chooses a resource. Character replacement
loads its own embedded paint (or fresh defaults), and motion replacement retains
the staged character and display settings. Public catalog membership comes only
from `BUILTIN_MODELS` / `BUILTIN_MOTIONS`; private files enter by explicit selection.
Nested character selection returns to the model draft before the outer Apply.
The UI must not synchronously rasterize a missing frame during an incomplete
preview. Old worker revisions are discarded. Physics/IK chain shortcuts are
checked against the full geometry, including root offsets and torso rotations.
Export snapshots the project and renders in a separate process; output files use
the exact same engine as the preview. The export dialog prevents duplicate
submission while work is in progress.

Painting workspaces are coordinated by `paint_workspace.py`. PNG surface records
are independent of local resume bindings. `painting_key` hashes original embedded
PNG records, excluding motion and model sizing; up to 32 artwork/folder bindings
live only in preferences. Different artwork must explicitly select a folder.
Identical/unpainted artwork shares a key. Existing preferences without bindings
require a one-time folder selection; no path enters portable model resources.
PNG surface records
are defined in `uv_assets.py` and exclude spatial offsets that do not change UVs.
They check mapping provenance, not painted content or alpha silhouettes. Keep
the PNG text record and adjacent UV_Model.json checks consistent. Poll only stable
file saves, retain last good data on failures, and never overwrite the old folder
during adaptation. Sharing links are persisted in character assets and resolved
only between supported counterparts. Painted legacy resources keep their existing
independent sides. Optional `model.attachments` records describe head-local ears
and pelvis-local tails or wrist-local props (`attachments.py`); `uv_assets.parts(bundle)` supplies the dynamic
part list, with the original body indices unchanged. Do not mutate `U.PARTS`.
Attachment geometry is separate from placement in texture surface signatures.
Both raster geometry and protection frames inherit the head's pixel-grid shift.
Attachment PNGs and protection groups are embedded in the same portable assets.
The model editor stages attachments and texture sharing independently. This adds
no ear bones or ear physics; arbitrary imported meshes need a separate resource design.

Tail attachments use IDs `tailN`, kind `tail` and parent `pelvis`, validated in
`tails.py`. Static closed meshes bend after UV projection. Their frame inherits
the pelvis or lower mascot surface, while `_motion_phase` drives whole-tail wag
with an integer cycle count. Head-grid shifts must apply only to head children.
`_attachment_local` caches shaped local vertices and UVs independently of pose,
and batch transforms place them each frame. Protection frames use the same tail
transform. Default ground queries ignore decorative tails; explicitly querying
a tail still returns its surface. Shape changes affect UV provenance, while
placement/wag settings do not. New tails use three FK joints and continuous
skinning; `tail` is a flat nine-angle pose channel. `tails.physical` uses the
shared deterministic spring solver with root/middle/tip softness and bounce.
Legacy whole-tail wag is converted when physics is enabled. Repetitive generated
tail-character variants have been retired; do not regenerate them.

## Clean archives

Automatic face overlays have been removed. Legacy face metadata is ignored; original PNG content is retained.

Hand props use IDs `propN`, kind `prop` and parent `armL`/`armR`. Box, cylinder,
sphere and cone provide closed UV-mapped meshes; legacy weapon shapes remain readable.
Grip transforms use the authored forearm angles rather than a world-axis frame,
avoiding flips when an arm crosses 90 degrees. The origin is the actual FK/IK
wrist endpoint; root/chest transforms and physical limb results are inherited.
Shape and size enter UV provenance; grip placement and transferring hands do not.
Static local vertices/UVs use the common attachment cache. Props do not inherit
head pixel shifts, contribute to default contact queries or change roll/float
pivots. The model arm panel switches between shape and hand-prop controls;
linked arm shaping is hidden in prop mode. Repetitive equipped-character examples
have been retired. No imported personal artwork is used in public builds.

Pose-card animation is an ordinary `base.kind = "poseclip"` entry. Its 2–6 cards
contain whitelisted numeric pose channels, hold/travel beats and an easing key.
Normalize once per sampled entry, interpolate bounded joint values without
overshoot, and include the final return transition only for loop playback.
Holds/travel are relative weights across the clip duration; sampling remains
shared with other motions. Ground contact aligns the feet, not decorative parts.
`pose_animation.build` bakes a new source's pose and clears old layers/controls/
physics to avoid double application; re-editing an existing clip preserves them.
The editor reuses ModelEditor's background four-view preview/cancellation and
integer display. Static card previews exclude modifiers; full playback includes
them. IK edits only the selected card, and Apply is one project undo operation.
Existing clips capture from their unmodified base sequence; new clips capture
the full source result. Independent-head poses are baked into equivalent
chest-local yaw before their boolean frame choice is discarded.
Regenerate only registered card recipes with
`python tools/build_pose_animation_examples.py`.

Directional export is selected through `engine.export(..., directions=4|8)`.
The default `directions=1` retains existing single-view behavior and filenames.
One pose sequence serves all cameras. Atlas pages are at most 4096 pixels wide;
eight rows at maximum 8x scale use at most 64 MiB of RGBA page pixels. GIF frames
are quantized at native size before integer upscaling and handled per direction.
Planned destinations are checked before rendering, files are staged and copied
with exclusive creation, and newly published files roll back on collision/error.
Metadata is the last published file; its format is in DIRECTIONAL-ATLASES.md.
`export_directions` is output metadata, excluded from motion-cache keys.
Regenerate the three public demo packs into a new empty folder using
`python tools/build_atlas_examples.py --output build/atlas-demo`.

Swimming and hovering reuse the existing root orientation and limb channels.
Their rotation pivot is derived once per model from the cached body center.
Airborne contact hints remain false through grounded attack layers, and idle
breathing must not create foot targets for these poses. This also lets optional
leg softness work on a floating layer above an idle base. Front-crawl Body roll
is intentionally hidden for the other swimming styles. Rebuild the seven public
aerial recipes with `python tools/build_aerial_examples.py`; this script touches
only those registered examples. They are also generated by build_v02_examples.

Motion recipes shipped in archives are listed in `motion_resources.BUILTIN_MOTIONS`.
Keep this list synchronized with `tools/build_v02_examples.py` when adding an
official example. User-saved recipes beside the examples remain local unless
explicitly added to that list.

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

For itch.io, first verify a Windows archive, then run:

```powershell
python tools/build_itch_release.py dist/FellowStudio3D-v0.2.0-Windows-x64.zip --output dist/FellowStudio3D-v0.2.0-itch-Windows-x64.zip
```

This produces a flat archive with itch launch/manual actions and a new hash
manifest. Only registered model and motion examples enter the release archive.


## Continuous mascot structure

`model.structure = "plush"` enables the validated `body` section in `plush.py`. Missing structure keeps legacy normalization unchanged. The internal head/torso rig controls remain available for animation compatibility, while the renderer emits one closed `body` surface. Body sockets derive from the continuous profile; both full geometry and the fast IK query use that same definition. Meshes are cached independently of pose. Batch deformation blends pelvis, chest and optional head transforms without duplicated join rings. Protected body motifs use an affine frame sampled at their own surface anchor. Ears follow the deformed surface rather than an unrelated head proxy. `uv_assets.parts()` is the source of truth for texture cards, export/import, sharing, and per-render owner indices. Body dimensions affect UV provenance; head/body linking and flexibility do not.


## Local review revision

Lighting controls and canvas sizing have separate UI entries. The two display
switches live beside Show textures. `light_strength` affects normal shading or
painted bands, while `shadow_strength` independently composites cast shadows;
turning lighting off does not disable the shadow map. The default `painted` style
uses projected per-part bounds and large fixed color blocks, so triangle normals
cannot create extra facet bands. `facet` retains the earlier normal-based style.

Native canvas dimensions and pixel-light settings live in project `render`, with
64×64/unlit defaults. `render_options` supplies the common canvas size, anchored
offset and preview transforms; rig/IK coordinates retain their existing 64-unit
reference. Preview input removes the canvas offset before solving IK. Changing
canvas size never changes model geometry, UV dimensions or animation caches.
`pixel_lighting` applies quantized world-normal bands and alpha-aware orthographic
shadow maps before outlines, after protected pixels. Light-space depth caches are
shared by camera views; disabled lighting bypasses the work entirely. Shadows use
bounded map resolution and slope bias, with no blur, ambient occlusion or bounce.
Large atlases page in both axes; oversized single-view export uses the same
streaming path. Very large GIF buffers are rejected before creating output.

Automatic pixel-face rendering has been removed; legacy face metadata is ignored and embedded PNGs remain unchanged. Tail poses use a flat nine-value pitch/yaw/roll channel, shared by three FK joints. Only geometry-independent bone deltas live in animation recipes. Skinning follows UV projection and leaves UV identities intact. The default character catalog contains three templates; optional private local models live under local_characters and are included only with --personal, never in a public build. Local review changes are submitted together only when requested by the user.

The single-UV editor stages raw texture replacement and protection groups together.
`image_clipboard.py` provides registered PNG and DIBV5 clipboard formats, preserving
alpha without new dependencies. `uv_assets.import_image` rejects size, surface or
part mismatches before mutation. Pasted textures carry `painting_override` so old
workspace or linked-file polling cannot revert them; explicit import or preparing
a new painting copy reconnects external editing. UI tests mock clipboard images;
native HGLOBAL round-trip checks leave the desktop clipboard unchanged.

## Hair

`hair.py` defines five procedural styles, closed paintable meshes, seven three-joint pose channels and inertia. `hair_editor.py` stages appearance; `hair_controls.py` exposes bone posing and softness. No body/hair collisions are simulated. `model.hairstyle` rebuilds stable attachment IDs during normalization; old models stay unchanged.

`hair_assembly.py` stages independent caps/locks, paint-preserving duplicates and reciprocal mirror pairs. `hairstyle.assembly/pieces` stores explicit component geometry; generated preset data stays compatible. Extra lock IDs have stable `hair_extra1`…`hair_extra32` channels. Only used channels are sampled; pose cards normalize the union of extra channels across cards.
