# FellowStudio3D User Guide

[English](GUIDE.en.html) · [简体中文](GUIDE.zh-CN.html) · [日本語](GUIDE.ja.html) · [Project README](../README.md)

## 1. Start and try a character

Extract the entire Windows portable ZIP and double-click **FellowStudio3D.exe**. No Python installation is needed. Keep the EXE, runtime and other files together. The BAT file is an alternative launcher. This package runs on Windows, not macOS.

Use the language menu at the upper right to choose English, Simplified Chinese or Japanese. The choice is remembered. **A− / A＋** changes the interface size. Side panels scroll; drag their dividers to change their width. **F1** or **User guide** opens this offline guide.

Automatically generated project names stay in English (Idle, Walk, Run) in every interface language. Names you type yourself are preserved.

For a quick first result:

1. Open **Creation library… → Character** and choose **Kumamon** (private local package) or **Painted character**.
2. Switch to **Motion**, choose walking, swimming or your own animation, and play the four views.
3. **Apply combination**, then edit further; authoring tools share **Create animation…**.
4. Click a preview to focus that view, then export it as a PNG strip at **1x**.

`DefaultModel.json` restores the built-in appearance. A new installation starts with the default mannequin, not the painted example or another user's session.

**Creation library: audition before applying**

**Creation library…** replaces the motion-example file picker. Switch between **Motion / Character**, filter a category, or search Chinese, English or Japanese names and filenames. Try `swim`, `Kumamon` or `MyMotion`. Clear the query if there are no matches. Filtering and switching tabs leave the staged combination intact.

Select a motion to audition it on the chosen character; select a character to keep the chosen motion. The summary names both choices and shows duration/FPS. Play, scrub and double-click a view to enlarge it. Preview runs in the background and cancels obsolete requests. **Apply combination** becomes available after the complete preview succeeds and creates one undo step. **Cancel** leaves the project untouched; **Reset selections** restores the character and motion from when you entered.

**Load file…** auditions your own models or motion recipes with the same Apply step. The default catalog indexes only registered public examples and does not scan personal saves. **Character model → Character library…** selects appearance inside the existing model draft; **Apply model** in the outer editor still commits the draft, and Cancel still discards it. The original **Load model** file picker remains available.

The character catalog now has three distinct starting models: default, painted and seamless mascot. Repetitive tail/equipment/face variants were removed. Complete Kumamon and cat paintings appear under My characters in the private local package; public packages exclude these personal models.

**Save and transfer animation**: Create animation… → Save animation… stores base motion, layers, pose cards, tail channels, controllers and physics, without appearance. Files default to local `user_data/motions` and appear under My animations. Apply one on another character to retain the target model, painting and display. The top Save button still saves a complete project.

**Tail joints and animation**: the model editor sets shape. After Apply, choose Tail in body controls and select root, middle or tip to edit pitch/yaw/roll, or drag joint handles in the four views. Add a Tail motion layer for sway and tip follow-through with mix, timing, fades and blend modes. Pose cards also store all three joints. This uses three-joint FK and continuous skinning. Physics below the controls offers root/middle/tip softness and bounce. Softness defaults to zero; try 0.2/0.45/0.65. These settings are saved with animations and simulated consistently in preview and export. Collision is not simulated.

**Held objects** start from Box, Cylinder, Sphere or Cone. Define their purpose through shape and painting instead of selecting weapons. Change shape, dimensions and grip while retaining independent UVs and pixel groups. Legacy weapon models remain readable but are no longer defaults or catalog characters.

## 2. Poses and animation without keyframes

Choose a **Base motion** or a preset pose on the left. Select **Edit base motion** to change its rhythm, stride, arm swing and other available parameters. Duration, frame rate and cycle count affect the resulting sequence.

Selecting a body part changes its pose across the whole animation. Use both arms or both legs for broad changes, and a single limb for a correction. **Swing range** changes movement around the average pose; it does not simply multiply every angle.

Add another motion as a layer. **Mix** controls its influence: zero removes that layer's contribution. For raising or waving an arm, **Keep base swing** keeps some of the base motion. For example, combine Run with a right-arm raise, then adjust Mix and Keep base swing until the arm stays raised while moving. Layers have an enabled state and applicable body-part scope.

Changing the base motion resets motion adjustments to that base's defaults. It preserves the character's model, textures and display settings. Save a project before switching if you want to keep a particular combination. **Undo / Ctrl+Z** reverses edits; **Ctrl+Y** redoes them.

**Action sequence…** arranges 1–6 actions without keyframes. Add actions, move selected rows up/down or remove them, then choose frames per step and Soft/Snappy/Direct transitions. Total frames and FPS are shown before applying. Creating a sequence keeps the character, base motion and pose controls, replacing current layers with ordinary editable layers; Undo restores the previous motion. Playback runs once, while a walking/running base keeps its cadence. Steps recover toward the base between actions; this does not automatically solve physically continuous combo contact or momentum. Try the three recipes under `examples/motions/sequences`.

**Swim** is a looping base motion with **Swimming style → Breaststroke / Front crawl / Tread water**. Adjust Arm stroke, Kick strength, Float bob and Swimming tilt; Body roll is shown only for front crawl. **Hover** controls height, bobbing, arm spread/beat, airborne leg bend and forward/back tilt. Both are also available as layers and preserve airborne height when combined with a grounded attack. Add a head motion or a single-arm wave to make a character look around or signal while floating. Normal breathing foot locks do not apply to airborne poses; optional softness remains available. These generate character motion, without a water surface, buoyancy or wing geometry. Try SwimBreaststroke, SwimFrontCrawl, TreadWater and Hover under `examples/motions/game`, and HoverWave, FloatingMage and SwimLookAround under `examples/motions/fusions`.

**Pose animation…** animates 2–6 authored pose cards. Select a card, drag limbs in the four views, or choose a body part and adjust its angles. Add a built-in pose, load a saved pose, or choose a Source frame and Capture pose card. Duplicate, mirror, reorder and remove cards. Each card has hold/transition beats and Smooth/Linear/Snappy easing: beats set relative timing, while Duration sets total seconds. Loop transitions from the last card back to the first; Once/Hold ends on the last card.

Card views show raw poses; playback includes layers and overall edits. Creating a new clip retains character, textures and framing, bakes sampled edits into captured poses and resets old layers/controls/physics to avoid applying them twice. Re-editing an existing pose clip retains its layers and overall edits. **Apply pose animation** is one undo step; Cancel leaves the project unchanged. Add ordinary layers/physics afterward and reopen **Edit pose cards…** from base parameters. Ground contact aligns foot height; disable it for airborne poses. Joint interpolation does not plan footsteps, collisions or fixed-foot trajectories: check crossings and sliding in playback. Duration is limited to 2–120 frames. Try SideStepDance, GuardSignal and ShyGreeting under `examples/motions/posecards`.

When re-editing a pose clip, **Base frame** captures only the base pose. Layers and overall edits stay separate, so captured cards do not receive those edits twice.

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

**Creation library… → Motion** previews recipes while retaining your model, textures and display. The `game` folder adds Jump and land, Thrust, Swing attack, Kick, Hit reaction, Fall, Get up, Roll, Climb cycle and Turn in place. Attacks have anticipation and strike timing; Jump has preparation, flight and landing. Hit reaction with Recovery amount = 0 retains the recoil. Walk/Run offer Travel direction for strafing/backpedaling, Stance width and Support time.

Add **Pose layer** to capture the current frame. Load Carry, Aim, Guard or Crouch from `examples/poses`, or save your own. Select affected body parts, Mix and Keep base swing. Waving and attacks support Left, Right or Both, together or alternating. Under **Timing and blend**, set the start, end position, fade and blend mode. Pose and motion adjusts posture while retaining base swing; Replace follows the action; Add applies changes relative to neutral. Play once layers exit after their interval; Hold last frame retains the final pose. Prefer Replace for short actions and inspect transitions before export. The `fusions` examples demonstrate these combinations. Save your current motion before replacing it with an example.

Under **Head**, adjust nod, turn, tilt and forward/back position independently. Turn off **Follow chest turn** to keep the head from inheriting chest yaw. Walk and Run also offer **Stride twist** for opposing chest and pelvis rotation.

Torso controls adjust lean, height, side tilt, chest turn and pelvis turn. **Keep feet when adjusting body** uses leg IK to preserve foot positions within the reach of the legs. Pause and drag the visible IK handles to adjust limbs. If a pose cannot be reached, check limb lengths and reduce the displacement. **Flip elbow / knee** changes a limb's bend direction.

**Upper softness** and **Lower softness** control physical follow separately. Start with small values: excessive softness can overpower the intended pose. The first preview after an edit can show the authored pose while physics and the remaining frames are still being calculated. Wait for the update to finish when judging the complete motion.

## 4. Views and pixel appearance

The default **Painted** lighting uses broad color blocks and restrained highlights, independent of mesh facets. **Faceted** retains the earlier surface lighting. Light and Self shadows have independent switches and strengths: shadows remain with zero light strength or lighting switched off. They share the source direction/elevation.

**Canvas size…**, beside view direction and framing Y, sets native width and height independently from 32 to 256 pixels, with common presets. More canvas preserves model/UV pixel scale, horizontal centering and bottom margin. All previews and exports use the same canvas. A small preview may shrink with nearest-neighbor sampling; exported frames retain native pixels and integer output scaling.

Lighting and Self shadows switches sit beside Show textures and the other display options. Open **Lighting settings…** to adjust world-space light direction, elevation, strength, light color and shadow color. Lighting uses discrete bands, without gradients or blurred shadows. Original PNGs and protected groups remain unchanged. Edits preview live, support project Undo and save with the full project. Animation transfer preserves the target canvas and lighting. Older projects default to unlit 64×64. Large exports use paged atlases; very large GIFs ask for fewer frames or a smaller output scale.

Click one of the four previews to focus it. Front and Side are orthographic; the three-quarter view is level, while the elevated view adds downward pitch. Model and UV editors offer **Single view**, or double-click a view to enlarge it. Hold **Before** to compare with the appearance at the time the editor opened.

The native image is **64 × 64 pixels**. Preview magnification does not add drawing detail. Outlines are always one native pixel wide; choose an outline color or use automatic gray. Part colors, overlap gaps and outlines are independent display options. Surface intersections at connected parts suppress internal lines; genuine foreground occlusion can retain a dividing edge.

## 5. Shape the character

Open **Character model**. Select a body part and choose its base shape, then adjust proportions. Head shapes include an ellipsoid, cylinder, rounded box and box. Torso and limb shapes also have alternatives. **Link left / right** applies paired-limb edits together.

Shoulder, waist and hip width affect the front silhouette. **Torso thickness** changes front-to-back depth, including the pelvis; try **1.15–1.3** for a slightly sturdier body. New models use 1.15, while older models retain their original thickness. Head gap and forward/back position, limb lengths, joint offsets and connection gaps let you adjust placement. Negative offsets move inward or overlap; positive offsets move outward or separate. Pelvis coverage fills the area between the leg roots.

Edits are staged. **Apply model** commits them; **Cancel** discards them. **Save model** stores the model, embedded textures and pixel protection groups in one reusable JSON. Loading it changes appearance while keeping the current animation. Older shape-only presets preserve the current textures.

**Head → Ears** adds Human ears, Cat ears or Long ears as a mirrored pair. Select an ear, then open **Edit ear shape** for signed side/height/depth positions, root width, length, depth, tip width and three rotation controls. Positions are relative to the sculpted head; ear dimensions use source pixels. Disable **Link left / right** for an asymmetric ear, or remove one ear or the pair. Ears follow head animation rigidly. After **Apply model**, the UV editor shows an extra card for each ear; the right shares the left texture by default. Turn sharing off to paint independently. Ear meshes, textures and protection groups travel with the model/project. If an existing painting folder predates the ears, create an adapted painting copy to add their PNG templates.

**Body structure → Seamless mascot** replaces Head and Torso with one **Main body** panel. Five controls set total height, upper width, belly width, base width and depth. The surface is continuous from crown to belly, with no neck seam; arms, legs and ears remain separate. **Move head and body together** is enabled by default. Disable it to allow soft upper-body nods/turns, then adjust flexibility. Existing chest, pelvis, limb, IK and motion controls remain available. The UV window uses one Main body card instead of separate head/torso cards. Save the model to carry its body settings, textures and protection groups together. Switching structure changes the body UV layout; prepare a new painting folder for that structure. `examples/models/PlushModel.json` is an unpainted starting model. Your existing separate-head models retain their original geometry and UVs.

## 6. Paint and replace textures

Click a part texture to open its UV window. **Save PNG…** saves the original texture. **Copy texture (Ctrl+C) / Paste to replace (Ctrl+V)** exchange images with painting applications, preserving native size and alpha without grid, selection or guide overlays. Pasted images must match the current atlas size; they are never resized. Protection groups remain. Undo and Cancel are available; Apply texture stages the result in the parent editor. Older painting files cannot overwrite a pasted texture. Prepare painting for the new texture creates a new folder copy.

In **Character model → Shape details**, Section profile adjusts top/middle/bottom width and depth independently. Front / back profile adjusts the contours and curve. Local projection adds an adjustable face or muzzle. Tapering changes the actual mesh, not only the joints. Cone and Pyramid are additional head bases. Try TaperedCylinder, MuzzleHead, LongMuzzleHead, BarrelBody and CurvedLimbs in `examples/models`. Set the shape before painting: adaptation after shape edits may need manual touch-up.

Use an external pixel-painting application; painting directly on the model is not supported.

1. Set the shape first, then open **UV textures → Start / resume painting** and choose a painting folder. On later visits, **Resume last painting** connects to the folder shown below the button without another picker. Opening the editor alone does not import artwork. Use **Advanced texture tools → Switch painting folder** to choose another folder.
2. Edit the part PNGs in your painting app. Keep the canvas size and the UV face positions unchanged. `*_Guide.png` files are references, not replacement textures.
3. Keep `UV_Model.json` beside the PNGs. Guide labels F/R/B/L/T/D mean front/right/back/left/top/bottom.
4. Save the PNG to refresh the preview automatically. An incomplete or unreadable save leaves the last valid texture in place. **Open painting folder** returns to the folder.
5. To replace one part, use **Swap** or drag its PNG onto that part's card. Check the preview and click **Apply textures**. Cancel discards this editor's unapplied changes.

Resume folders are remembered by embedded artwork. Switching to different paint does not automatically reconnect the previous character's folder. Identical artwork can share the remembered folder; after an upgrade or on another computer, select it once again. Paths stay in local preferences, outside portable models. Unpainted characters share the default entry, with UV matching still checked on connection.

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

For a game direction set, choose **Four directions (level)** or **Eight directions (level)** in the same Export view menu. The strip option becomes a transparent directional atlas: each direction is a row and frames run left to right. PNG sequences and GIF previews can also be generated for each angle. A separate **NAME_atlas.json** records image/rectangle, frame duration, playback and a shared pivot; JSON recipe still saves an editable project. Wide atlases split into pages automatically (maximum width 4096 pixels), retaining all direction rows on each page. Output is staged, existing files are preserved and the descriptor is published last. See [Directional atlas format](DIRECTIONAL-ATLASES.md) or try the TailWalk, HoverWave and FrontCrawl packs under `examples/atlases`.

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

Ear attachments currently follow the head rigidly. Arbitrary external mesh import, custom bone topology and independent ear physics are not currently available. See [Development guide](DEVELOPMENT.md) for source setup and release building.

## Hair styling and animation

Head (Main body for plush) has separate Shape, Hair and Ears tabs. Hair follows one structure: Add component → Added components → Selected component settings. Add a hair body, left/right fringe, left/right middle lock, back hair, ponytail or free lock independently; duplicate, mirror or delete actual components. Reclassify older free locks in details without changing their shape or bones.

Hair bodies have five outlines and independent proportions, hairline, coverage and crown controls. Locks retain 14 shape controls, independent UVs and three bones. Pair shapes can be linked; adding a missing opposite side mirrors the existing part. Face and body painting remain intact.

Hairstyle templates are collapsed under a separate button. Select one of five templates and explicitly choose Replace with template to generate components once. This replaces current hair; cancel the model editor to discard changes, or undo after Apply.

Use Body controls → Hair for bone dragging, softness and rebound, or add Hair sway and pose cards. Shoulder/back collisions are not simulated. All attachments share a limit of 32. Tail → Tip thickness produces rounded cat-tail ends; zero retains the old shape.
