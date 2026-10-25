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

Directional sliders now accept negative values where useful: Bow leans backward, Nod/Shake reverse, arm raising can reach behind, elbow bend and hand spacing can reverse, gait arm swing/torso twist and attack body drive can oppose their original direction. **Motion range** below 0 reverses movement around the average pose; **Forward / backward joint bend** separately adjusts elbows/knees. **Squat → Leg spread** opens the legs for positive values and brings them inward for negative values; 0 preserves the old squat. Try `examples/motions/game/LeanBack.json` and `WideSquat.json`. Durations, counts, physical dimensions and physical-follow strength retain their valid ranges.

Default Thrust is a compact straight punch: approximately 10° of reverse shoulder turn in preparation, then 22° shoulder and 10° pelvis drive on extension. These are changes relative to the input stance, not the camera direction. Increase Body follow-through or add Waist twist for a deliberately larger turn.

Thrust and Swing attack have separate **Wind-up amount** and **Anticipation time** controls. Wind-up pulls the elbow/fist back, bends the elbow and turns the chest/pelvis against the strike, before extending into the attack and recovering the original guard. Set Wind-up amount to 0 for an immediate strike; time alone does not change the preparation pose. Both attacks now start from the adjusted guard, rather than adding guard offsets after the strike.

**Waist twist** turns the chest and pelvis and returns to the original stance. Use a negative angle for the other side; Pelvis follow controls how much of the turn reaches the hips. It can be layered onto a combat guard or an attack. Thrust, Swing attack and Kick now include stronger body follow-through (0–3). New attacks affect All relevant parts, including pelvis rotation; an explicit arm/leg mask still limits their effect. For an older attack layer, select All relevant parts to enable its complete body drive.

**Raise arms → Raise direction → Forward** provides forward reaching, carrying and overhead poses, with independent height and elbow bend. Choose Sideways for the old lateral raise; existing recipes keep their previous direction.

**Pick up / put down** reaches down, lifts and ends holding the item pose, or reverses that process to put it down. Choose Left, Right or Both, and adjust reach bend/crouch, hand spacing, lift height and elbow bend. Lift height reaches 180°; elbows automatically straighten for high lifts. Ground reach reduces excessive bend/crouch for long-arm, short-leg models so the hands do not push the feet off the floor. Your object is not added by this action. Use Hold last frame to keep the final carry pose. Examples: `game/Pickup.json`, `game/PutDown.json`, `game/LiftOverhead.json`, `fusions/CombatTwist.json`, `fusions/CombatPushKick.json` and `fusions/ForwardCarry.json` under `examples/motions/`.

Kick now has a **Kick style** selector: **Swing kick** keeps the original motion; **Push kick** chambers the knee, extends the leg forward, then retracts before lowering. Left/right/both and timing controls apply to either style. Try `examples/motions/game/PushKick.json`, or use Push kick in a jump layer.

During a jump or bounce, pose/action layers inherit airborne contact and keep the flight height, including Replace and Pose-and-motion blends. Kicks, hits, falls, turns and grounded pose resources do not pull the character onto the floor. The rule also applies when the action layer comes before the jump. Explicit Ground roll remains a deliberate ground constraint. `examples/motions/fusions/JumpKick.json` demonstrates an airborne kick.

Thrust starts from the adjusted guard pose, extends the selected arm, then returns to that same guard. Arm pose controls are applied before the strike, so a bent-elbow guard is not added back onto the extended punch. The striking arm stiffens as it extends and resumes ordinary soft follow on recovery. Try `examples/motions/fusions/CombatStraightPunch.json` or add Thrust directly to CombatStance.

Idle breathing keeps the feet planted by compressing the legs slightly and returning to the standing pose. It remains active when combining upper-body poses and leg softness. Turn off **Keep feet when adjusting body** to allow free foot movement. Breathing does not force a jump's feet back onto the floor.

For a slightly side-on combat pose, select Torso and adjust **Whole-body facing** in 1° steps. Then twist Chest and Pelvis separately; pelvis turn affects the lower torso and leg roots, so small angles can be subtle at 64px. Try `examples/motions/fusions/CombatStance.json` for a breathing guard stance with opposing chest/pelvis angles and a forward-looking head.

Below the preview, enter **Frames** (1–120) and press Enter or leave the field. This is the total sequence length. **FPS** controls playback speed: 24 frames at 12 FPS lasts 2 seconds. Changing FPS preserves the frame count. The base motion's repeat count determines how many cycles fit inside that sequence.

Above the preview, **Frame Y (px)** shifts the framing in whole source pixels: positive moves the character down, negative moves it up. This affects all views, IK handles and exported frames, and stays with the project when changing motions. It changes composition without moving the character in world space. It cannot fit a character taller than the canvas by itself.

**Show textures** and **Part colors** are independent: turn textures off to inspect the colored mannequin, or turn both off for white. Turning part colors off keeps painted textures visible. These display choices are remembered. New layers default to **Add changes**; existing explicit blend modes are preserved. **Start position / End position** are absolute positions within the sequence, from 0 to 1; the end must follow the start.

For a somersault, combine Run, Jump and Roll. Roll's **Follow base motion** mode preserves the jump's airborne trajectory; Ground roll forces contact and Aerial roll disables contact. Set the roll's start/end within the flight stage. `examples/motions/fusions/RunJumpRoll.json` demonstrates this and includes Frame Y = 8. A previously selected framing is retained when importing motion examples. Non-looping physics follows the rotating parent in world space; inspect frames during the motion, as playback stops at the final frame.

**Playback** offers Loop, Play once and Hold last frame. Non-looping motions include the final pose and stop there; GIF previews also play once. Fall holds its lying pose, and Get up ends standing. Soft follow starts fresh for non-looping actions.

**Motion examples…** opens recipes while retaining your model, textures and display. The `game` folder adds Jump and land, Thrust, Swing attack, Kick, Hit reaction, Fall, Get up, Roll, Climb cycle and Turn in place. Attacks have anticipation and strike timing; Jump has preparation, flight and landing. Hit reaction with Recovery amount = 0 retains the recoil. Walk/Run offer Travel direction for strafing/backpedaling, Stance width and Support time.

Add **Pose layer** to capture the current frame. Load Carry, Aim, Guard or Crouch from `examples/poses`, or save your own. Select affected body parts, Mix and Keep base swing. Waving and attacks support Left, Right or Both, together or alternating. Under **Timing and blend**, set the start, end position, fade and blend mode. Pose and motion adjusts posture while retaining base swing; Replace follows the action; Add applies changes relative to neutral. Play once layers exit after their interval; Hold last frame retains the final pose. Prefer Replace for short actions and inspect transitions before export. The `fusions` examples demonstrate these combinations. Save your current motion before replacing it with an example.

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

In **Character model → Shape details**, Section profile adjusts top/middle/bottom width and depth independently. Front / back profile adjusts the contours and curve. Local projection adds an adjustable face or muzzle. Tapering changes the actual mesh, not only the joints. Cone and Pyramid are additional head bases. Try TaperedCylinder, MuzzleHead, LongMuzzleHead, BarrelBody and CurvedLimbs in `examples/models`. Set the shape before painting: adaptation after shape edits may need manual touch-up.

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
