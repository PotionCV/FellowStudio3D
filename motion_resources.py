"""Portable poses and motion recipes, independent of character appearance."""
import copy,json,math
from pathlib import Path
import engine as E

BUILTIN_MOTIONS=(
 'Idle.json','Walk.json','Run.json',
 'sequences/ComboPunchKick.json','sequences/WalkGreetBow.json','sequences/JumpThenRoll.json',
 *(f'posecards/{name}.json' for name in ('SideStepDance','GuardSignal','ShyGreeting')),
 *(f'game/{name}.json' for name in ('SwimBreaststroke','SwimFrontCrawl','TreadWater','Hover')),
 *(f'fusions/{name}.json' for name in ('HoverWave','FloatingMage','SwimLookAround')),
 *(f'game/{name}.json' for name in ('Climb','Fall','Getup','Hitreaction','Jump','Kick','PushKick','Roll','Swingattack','Thrust','Turn','Waisttwist','Pickup','PutDown','LiftOverhead','LeanBack','WideSquat')),
 *(f'fusions/{name}.json' for name in ('Backpedal','CombatStance','CombatStraightPunch','CrouchWalk','GuardAndThrust','JumpKick','RunAim','RunJumpRoll','RunTimedSwing','RunWaveLeft','StrafeWalk','WalkCarry','WalkGuard','CombatTwist','CombatPushKick','ForwardCarry')))

def pose_channels(pose):
 result={}
 for key in E.POSE_CHANNELS:
  if key not in pose:continue
  value=pose[key]
  if key in E.LIMBS or key=='tail':
   if not isinstance(value,(list,tuple)) or len(value)!=(9 if key=='tail' else 4):raise ValueError('Invalid pose angles')
   value=[float(v) for v in value]
   if not all(math.isfinite(v) for v in value):raise ValueError('Invalid pose angles')
  else:
   value=float(value)
   if not math.isfinite(value):raise ValueError('Invalid pose value')
  result[key]=value
 if not result:raise ValueError('Empty pose resource')
 return result

def save_pose(pose,path):
 E.save(dict(type='FellowStudioPose',version=1,pose=pose_channels(pose)),path)

def load_pose(path):
 data=json.loads(Path(path).read_text(encoding='utf-8'))
 if data.get('type')!='FellowStudioPose' or data.get('version')!=1:raise ValueError('Choose a FellowStudio pose resource')
 return pose_channels(data.get('pose',{}))

def apply_motion(current,recipe):
 result=copy.deepcopy(recipe)
 for key in ('model','assets3d','render'):
  if key in current:result[key]=copy.deepcopy(current[key])
  else:result.pop(key,None)
 if 'camera_y' in current:result['camera_y']=current['camera_y']
 return result

def motion_recipe(project):
 """Animation only: reusable independently of model, paint and display."""
 keys=('version','name','seconds','fps','base','layers','controls','physics','pose','playback','base_playback','yaw','pitch')
 return {key:copy.deepcopy(project[key]) for key in keys if key in project}

def save_motion(project,path):E.save(motion_recipe(project),path)
