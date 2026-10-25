# Editable motion recipes

Use **Motion examples…** to retain your character, textures and display settings.
The regular **Open** command instead opens a complete project.

- Idle, Walk, Run preserve the published defaults.
- `game/PushKick.json`: chamber, forward push and retract; Kick style remains editable.
- `game/`: staged jump, attacks, hit, fall, get up, roll, climb and turn.
- `fusions/`: carrying, aiming, guarding, left-hand waving, timed attack,
  crouched walking, strafing, backpedaling, RunJumpRoll (airborne somersault)
  CombatStance (a side-on breathing guard pose), CombatStraightPunch and JumpKick.

CombatStraightPunch uses the default Thrust layer on CombatStance: prepare,
extend the striking arm and recover the original guard. No pose-cancelling
offsets are needed. The other arm remains in guard.

RunJumpRoll includes Frame Y = 8 to leave room above the character. An explicitly
chosen framing is retained when importing an example. New layers default to Add
changes; examples can explicitly use posture/replace modes for their purpose.

All recipes are editable. Travel offsets stay within the 64px canvas for the
default mannequin; extreme model dimensions or action parameters may crop.

Waisttwist returns to its starting orientation; negative angles twist the other way.
CombatTwist and CombatPushKick combine body drive with the guard stance.
Pickup and PutDown share matching endpoints and default to Hold last frame.
LiftOverhead demonstrates lifting above the head; high lift angles reduce elbow fold.
ForwardCarry uses the new Forward direction of Raise arms.
Attack follow-through now ranges from 0 to 3. For older attack layers, select
All relevant parts to include both chest and pelvis movement.

Thrust and Swing attack have Wind-up amount independent of Anticipation time.
Their elbow/fist retracts and the torso counter-turns before the strike. Both
recover the adjusted input guard; Wind-up amount = 0 skips preparation movement.

LeanBack uses a negative Bow amount. WideSquat opens the legs during crouching;
its Leg spread parameter supports inward/outward adjustment and defaults to
zero in ordinary Squat. Signed motion range reverses swing around its mean.
