# Model presets

- `DefaultModel.json`: the built-in model with default textures.
- `TaperedCylinder.json`: independently tapered head width and depth.
- `MuzzleHead.json`, `LongMuzzleHead.json`: projecting faces with editable size,
  height, position and tip fullness.
- `ConeHead.json`, `PyramidHead.json`: additional head bases.
- `BarrelBody.json`: broader, deeper torso profile.
- `CurvedLimbs.json`: curved, tapered paired arms.
- `CustomModel.json`: the painted example character, including its proportions,
  shapes, embedded PNG textures and pixel protection groups.

Use Character model > Load model, select CustomModel.json, then Apply model.
The character appears in the preview before applying; Cancel discards it. Your
current animation and motion controls are retained. Try Walk or Run with it.

Save model creates the same reusable resource, including textures, in one JSON.
Shape details exposes profile, contour and local projection parameters. Linked
left/right curve edits are mirrored; other shape dimensions are shared.
Older shape-only presets are still accepted without replacing current textures.
For an entire neutral-pose project, use Open on ../characters/CustomCharacter.json.
