# v0.2 preview

## Shape rather than just scale

Head bases now include cones and pyramids. Every part supports independent
top/middle/bottom width and depth, front/back contour offsets, curve and a local
projection with editable length, width, height, placement and tip fullness.
Linked limb curve edits mirror left/right. Old resources keep their geometry
when these optional parameters are absent. Surface edits update UV compatibility
metadata and use the existing staged adaptation workflow.

## Build game actions from reusable pieces

- Real mirrored left/right/both waving and attacks, together or alternating.
- Loop, play once and hold-last-frame modes, including GIF export and physics.
- Portable pose resources; capture, load and save without copying character data.
- Body-region masks, mix and retained base motion; optional timing and fade.
- Replace, posture/motion and additive layer composition.
- Jump with preparation/flight/landing, thrust, swing attack, kick and hit reaction.
- Waist twist with signed angle, pelvis follow, anticipation and return.
- Stronger full-body attack follow-through, configurable from 0 to 3.
- Default straight-punch body drive is compact: about 10 degrees reverse
  preparation, 22 degrees shoulder and 10 degrees pelvis on extension.
- Physical wind-up poses for thrust/swing: arm retraction, elbow chamber and
  reverse body turn, separate from anticipation timing; recover the input guard.
- Forward arm raising with elbow bend and existing sideways compatibility.
- Pick up / put down, including overhead lift and body-proportion reach fitting.
- Refreshed CustomModel / CustomCharacter appearance with embedded textures and protection.
- Kick style: original swing or chamber / extend / retract push kick.
- Fall, get up, directional roll, climb cycle and turn in place.
- Walk/run travel direction, stance width and support timing, preserving existing
  published motion defaults when the new controls remain neutral.
- Pose-layer ground contact; shaped contact clouds shared across action frames.

The included library adds 7 models, 4 poses, 17 base-action recipes and 16 fusion
recipes. Motion examples retain the current character, textures and display.
Three offline guides cover the new workflow. Details stay behind expandable
controls in the existing three-panel/four-view interface.

The preview keeps native 64px rendering, integer 1x/4x/8x export, the previous
painted example and independent model/texture Apply/Cancel workflows. Additional
bones and accessory meshes are outside this batch.

## Preview follow-ups

New layers default to additive changes. Texture visibility and part colors are
independent, persisted switches. Frames and FPS are directly editable below the
preview. Layer timing uses absolute start/end positions, with legacy span files
remaining supported. Single-shot physics accounts for rotating parents in world
space. Roll can inherit airborne contact, force ground contact or stay airborne;
its pivot uses the character's center. RunJumpRoll demonstrates the composition.
Frame Y shifts every view, handle and export in integer source pixels without
invalidating geometry or physics caches. It is saved with the project.

Idle breathing plants feet with leg IK, including soft-leg motion, and retains
other actions' airborne trajectories. Pixel snapping separates breathing from
whole-character translation so planted feet do not flicker between pixel rows.
Torso controls include 1° whole-body facing; CombatStance demonstrates separate
facing, chest and pelvis angles.

Thrust layers now extend from the adjusted input guard and recover it instead
of reapplying global guard offsets after the strike. The selected arm stiffens
during extension so default running softness cannot bend the punch back into
a hook. Left/right, masks, timing, mixing and later layers remain supported.
CombatStraightPunch demonstrates the default additive combination.

Flight height and contact are now inherited across ordinary pose/action layers,
including kicks, hits, falls, get-up, turn and grounded poses. Replace blending
cannot zero the airborne height. Both layer orders and partial jump weights are
supported; explicit Ground roll still forces contact. JumpKick demonstrates it.

## Interactive calculation and preview

- IK prepares the model, body transform and camera matrices once per constraint
  solve. Inner joint probes use direct FK without model normalization, JSON or
  geometry rebuilding; the existing joint constraints and tolerances remain.
- Progressive preview shares its authored sequence with the physics stage and
  reuses current-frame images when physics is disabled.
- New edits cancel obsolete work during authoring and physics. Current-frame
  images arrive first; background chunks no longer redraw unrelated views.
- Local Windows/Python 3.12 check, CustomCharacter + Idle + Thrust (24 frames):
  adding the layer displayed its first result in 0.756 seconds; body-drive edits
  in 0.679 / 0.655 / 0.652 seconds. The previous changed-drive authoring alone
  took 13.203 seconds. Preview pixels match the export path.

## Bidirectional pose controls

Bow supports backward lean. Directional arm/joint/motion, torso follow and
travel parameters support signed values; duration, strength and dimensions
retain valid bounds. Squat has signed leg spread, with foot contact preserved
and unchanged legacy behavior at zero. LeanBack and WideSquat are included.
