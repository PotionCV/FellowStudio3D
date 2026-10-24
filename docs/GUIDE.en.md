# FellowStudio3D User Guide

[English](GUIDE.en.html) · [简体中文](GUIDE.zh-CN.html) · [日本語](GUIDE.ja.html) · [Project README](../README.md)

## 1. Start and try a character

Extract the entire Windows portable ZIP and double-click **FellowStudio3D.exe**. No Python installation is needed. Keep the EXE, runtime and other files together. The BAT file is an alternative launcher. This package runs on Windows, not macOS.

Use the language menu at the upper right to choose English, Simplified Chinese or Japanese. The choice is remembered. **A− / A＋** changes the interface size. Side panels scroll; drag their dividers to change their width. **F1** or **User guide** opens this offline guide.

Automatically generated project names stay in English (Idle, Walk, Run) in every interface language. Names you type yourself are preserved.

For a quick first result:

1. Open **Character model → Load model** and select `examples/models/CustomModel.json`.
2. Click **Apply model** to use the included painted character with your current motion.
3. Choose **Walk** or **Run**, then play the animation.
4. Click a preview to focus that view, then export it as a PNG strip at **1x**.

`DefaultModel.json` restores the built-in appearance. A new installation starts with the default mannequin, not the painted example or another user's session.

## 2. Poses and animation without keyframes

Choose a **Base motion** or a preset pose on the left. Select **Edit base motion** to change its rhythm, stride, arm swing and other available parameters. Duration, frame rate and cycle count affect the resulting sequence.

Selecting a body part changes its pose across the whole animation. Use both arms or both legs for broad changes, and a single limb for a correction. **Swing range** changes movement around the average pose; it does not simply multiply every angle.

Add another motion as a layer. **Mix** controls its influence: zero removes that layer's contribution. For raising or waving an arm, **Keep base swing** keeps some of the base motion. For example, combine Run with a right-arm raise, then adjust Mix and Keep base swing until the arm stays raised while moving. Layers have an enabled state and applicable body-part scope.

Changing the base motion resets motion adjustments to that base's defaults. It preserves the character's model, textures and display settings. Save a project before switching if you want to keep a particular combination. **Undo / Ctrl+Z** reverses edits; **Ctrl+Y** redoes them.

## 3. Head, torso, IK and physical follow

Under **Head**, adjust nod, turn, tilt and forward/back position independently. Turn off **Follow chest turn** to keep the head from inheriting chest yaw. Walk and Run also offer **Stride twist** for opposing chest and pelvis rotation.

Torso controls adjust lean, height, side tilt, chest turn and pelvis turn. **Keep feet when adjusting body** uses leg IK to preserve foot positions within the reach of the legs. Pause and drag the visible IK handles to adjust limbs. If a pose cannot be reached, check limb lengths and reduce the displacement. **Flip elbow / knee** changes a limb's bend direction.

**Upper softness** and **Lower softness** control physical follow separately. Start with small values: excessive softness can overpower the intended pose. The first preview after an edit can show the authored pose while physics and the remaining frames are still being calculated. Wait for the update to finish when judging the complete motion.

## 4. Views and pixel appearance

Click one of the four previews to focus it. Front and Side are orthographic; the three-quarter view is level, while the elevated view adds downward pitch. Model and UV editors offer **Single view**, or double-click a view to enlarge it. Hold **Before** to compare with the appearance at the time the editor opened.

The native image is **64 × 64 pixels**. Preview magnification does not add drawing detail. Outlines are always one native pixel wide; choose an outline color or use automatic gray. Part colors, overlap gaps and outlines are independent display options. Surface intersections at connected parts suppress internal lines; genuine foreground occlusion can retain a dividing edge.

## 5. Shape the character

Open **Character model**. Select a body part and choose its base shape, then adjust proportions. Head shapes include an ellipsoid, cylinder, rounded box and box. Torso and limb shapes also have alternatives. **Link left / right** applies paired-limb edits together.

Shoulder, waist and hip width affect the front silhouette. **Torso thickness** changes front-to-back depth, including the pelvis; try **1.15–1.3** for a slightly sturdier body. New models use 1.15, while older models retain their original thickness. Head gap and forward/back position, limb lengths, joint offsets and connection gaps let you adjust placement. Negative offsets move inward or overlap; positive offsets move outward or separate. Pelvis coverage fills the area between the leg roots.

Edits are staged. **Apply model** commits them; **Cancel** discards them. **Save model** stores the model, embedded textures and pixel protection groups in one reusable JSON. Loading it changes appearance while keeping the current animation. Older shape-only presets preserve the current textures.

## 6. Paint and replace textures

Use an external pixel-painting application; painting directly on the model is not supported.

1. Set the shape first, then open **UV textures → Start / resume painting** and choose a painting folder.
2. Edit the part PNGs in your painting app. Keep the canvas size and the UV face positions unchanged. `*_Guide.png` files are references, not replacement textures.
3. Keep `UV_Model.json` beside the PNGs. Guide labels F/R/B/L/T/D mean front/right/back/left/top/bottom.
4. Save the PNG to refresh the preview automatically. An incomplete or unreadable save leaves the last valid texture in place. **Open painting folder** returns to the folder.
5. To replace one part, use **Swap** or drag its PNG onto that part's card. Check the preview and click **Apply textures**. Cancel discards this editor's unapplied changes.

Cards report whether the mapping matches, its source is unknown, or a file is missing/unreadable. Matching checks the part, UV layout and surface shape; it cannot tell whether you painted an eye or garment in the right place. A correctly sized PNG without reliable metadata is accepted as **unknown source**. Similar transparent areas do not prove a match.

Shape, length and thickness changes can change the UV mapping. Existing artwork is adapted face by face, but details may need repainting. Use **Create adapted painting copy** to prepare a new `-v2` / `-v3` folder from your painting files; the old folder is preserved. Placement-only changes do not alter a part's UV layout.

New unpainted characters share paired limb textures. Painted examples may have independent sides. On a right-side card, disable **Share left texture** to paint it independently; its current image is kept. **Advanced texture tools** contains pixel groups, pack import/export and reset controls.

## 7. Protect small pixel patterns

Open **Pixel groups** from a part's advanced controls or its thumbnail. Select a small motif, such as facial pixels, that should keep its relative arrangement during modest movement.

- Use box selection or the brush. Shift adds, Ctrl subtracts, and the right mouse button temporarily erases the selection.
- The wheel zooms around the pointer. Drag with the middle button or Space to pan. **Fit** brings the UV faces into view.
- Choose **Protect selected pixels** to create a group, or select an existing group to edit it. Orange marks the current selection; cyan marks saved groups. Ctrl+Z undoes selection strokes.
- Adjust the group's **Angle limit**. Beyond it, the group returns to ordinary UV sampling. The default is 40°.
- Click **Apply groups**, then **Apply textures** in the parent UV editor to commit the result to the project.

A group may cross adjacent UV faces. Protection does not make a pattern visible through other parts or outside the silhouette, and does not guarantee a lossless result at every angle. Use small coherent groups; inspect rotation and animation before exporting. Groups are stored in project/model JSON and UV packs, not in a plain PNG alone.

## 8. Export sprites

Open **Export frames** and choose the directory, file name, view, scale and formats. The focused view is the initial choice unless another export view was selected. Check it before exporting.

- **PNG sequence**: individual transparent frames.
- **PNG strip**: frames in a horizontal transparent strip.
- **GIF**: an animation preview; use PNG for final pixel assets.
- **JSON recipe**: an editable project/animation resource.

**1x** gives 64 × 64 frames; **4x** gives 256 × 256; **8x** gives 512 × 512. Scaling uses nearest-neighbor integer enlargement. A one-pixel outline becomes four display pixels at 4x.

**Create same-name subfolder** is off by default: files go directly into the selected directory. The last directory is remembered. Existing output files are not overwritten; change the name or directory if there is a conflict. Export runs in the background; wait for the completion status.

## 9. Save, share and recover work

**Save / Ctrl+S** saves a project JSON containing the character, textures, pixel groups and motion. **Open** loads a complete project, unlike Load model, which keeps the current motion. The original painted PNGs are not needed to open a saved project on another computer. Keep the painting folder separately if you want to continue editing those source files.

Examples are grouped by purpose: `examples/models` for reusable appearance, `examples/characters` for complete neutral-pose projects, `examples/motions` for motion recipes, and `examples/UV` for default-model templates. Default UV templates may not fit a modified shape.

Autosave is `user_data/studio3d_motion.json`; local preferences are `user_data/ui_settings.json`. If the installation folder is not writable, data falls back to `%LOCALAPPDATA%\FellowStudio3D`. Back up your saved JSONs before replacing an installation. Release ZIPs exclude personal autosaves and preferences; the painted example is intentionally included.

## 10. Common issues

- **The EXE does not open:** extract the complete package again. Do not move only the EXE. If a startup error is reported, check `startup-error.log` in the local data folder.
- **A texture will not load:** check the part, canvas size and matching model. Known incompatible files need adaptation; correct size alone is insufficient.
- **A face flickers during rotation:** try a small pixel protection group and check its angle limit. Surface occlusion and the native resolution still apply.
- **An edit looks delayed:** wait for the current calculation to finish before judging physics. Pause playback while making precise changes.
- **The interface is too small:** use A＋; scroll the side panel or widen it if controls no longer fit.

Arbitrary external mesh import, additional bones and attached accessory models are not currently available. See [Development guide](DEVELOPMENT.md) for source setup and release building.
