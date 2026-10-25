# v0.2 implementation plan

Work is implemented and checked in order. The public v0.1.0 release stays intact; the completed work ships as v0.2.0.

- [x] 1. Side selection: left/right/both waving, mirrored joint conventions,
  synchronous/alternating paired actions; preserve unaffected base motion.
- [x] 2. Playback: loop/once/hold, exact action endpoints, non-periodic physics,
  matching main/model/UV playback and GIF export behavior.
- [x] 3. Shape editing: tapered profiles, independent width/depth bands,
  front/back contour and local muzzle/bulge; matching UV adaptation and examples.
- [x] 4. Composition: reusable pose layers, upper/lower/head/individual masks,
  layer timing, weight and retained base motion; examples for carrying and aiming.
- [x] 5. Game actions: staged jump, thrust/swing/kick and directional hit reaction;
  preparation, action and recovery parameters rather than keyframes.
- [x] 6. Recovery/mobility: fall/death/get-up, roll/dodge, climb, turn;
  directional gait and foot-support controls where the existing gait is insufficient.
- [x] 7. Resource library: editable model examples and motion/fusion examples;
  accessible through existing editors with localized labels.
- [x] 8. Validation/delivery: old project compatibility, native pixels and export,
  UI staging/undo, offline documentation, clean separate preview archives.

Acceptance: a tapered cylinder and projecting muzzle must alter real geometry;
left-arm waving must animate the left arm while preserving the right arm; once
and hold must not wrap their final pose to their first; timed attacks must leave
the base motion untouched outside their active interval; resources must include
their shape parameters and must not contain personal paths or autosaves.

Delivered: seven model resources, four poses, seventeen game-action recipes and sixteen
fusion recipes. Updated the curated painted character and its matching model.
Validation: 80 engine/resource/release checks and 25 GUI checks, rendered
shape/action/fusion sheets and new wind-up/lift/overhead previews, isolated
bundled-runtime export at 1x/4x/8x, manifest verification and unchanged hashes
of the published v0.1 archives. Only registered models/motions enter release packs.

The implementation has been prepared for a separate v0.2.0 GitHub release and
itch.io archive; published v0.1 files are retained.

The custom-character Idle + Thrust interaction now refreshes its first result
in 0.65–0.76 seconds locally. Direct FK in the IK inner loop, shared authoring
and mid-calculation cancellation replace the previous slow preview path.
