"""Rebuild editable v0.2 examples without copying local user data."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import engine as E,model_data as M,rounded_scene as S,motion_resources as MR

def build():
 models={
  'TaperedCylinder':{'head':dict(shape='cylinder',top_width=1.3,bottom_width=.6,top_depth=1.15,bottom_depth=.7)},
  'MuzzleHead':{'head':dict(shape='rounded_box',size=.85,bulge_length=4.5,bulge_width=.7,bulge_height=.5,bulge_y=-.2,bulge_tip=.65)},
  'LongMuzzleHead':{'head':dict(shape='ellipsoid',size=.8,bulge_length=7.,bulge_width=.6,bulge_height=.4,bulge_y=-.25)},
  'ConeHead':{'head':dict(shape='cone')},'PyramidHead':{'head':dict(shape='pyramid')},
  'BarrelBody':{'torso':dict(shoulder=1.2,thickness=1.3,mid_width=1.15,mid_depth=1.25,front_mid=1.,back_mid=1.)},
  'CurvedLimbs':{'armL':dict(curve=-1.5,top_width=1.2,bottom_width=.6),'armR':dict(curve=1.5,top_width=1.2,bottom_width=.6)}}
 for name,parts in models.items():
  model=M.normalize()
  for part,changes in parts.items():model[part].update(changes)
  M.save(model,ROOT/'examples'/'models'/(name+'.json'),assets=S.assets({'model':model}))
 poses={'Carry':dict(armL=[-15,8,20,70],armR=[15,-8,20,70]),
        'Aim':dict(armL=[-15,10,65,30],armR=[12,-3,85,5]),
        'Crouch':dict(dy=4,lean=12,legL=[-6,4,50,-100],legR=[6,-4,50,-100]),
        'Guard':dict(armL=[-25,15,55,75],armR=[25,-15,55,75],head_pitch=-8.)}
 folder=ROOT/'examples'/'poses';folder.mkdir(exist_ok=True)
 for name,pose in poses.items():MR.save_pose(E.norm(pose),folder/(name+'.json'))
 motions=ROOT/'examples'/'motions'/'game';motions.mkdir(exist_ok=True)
 for kind in ('jump','thrust','swing','kick','hit','fall','getup','roll','climb','turn','twist','lift'):
  p=E.new_project(kind);E.save(p,motions/(p['name'].replace(' ','')+'.json'))
 p=E.new_project('kick',name='Push Kick');p['base']['style']='push';E.save(p,motions/'PushKick.json')
 p=E.new_project('lift',name='Put Down');p['base']['operation']='putdown';E.save(p,motions/'PutDown.json')
 p=E.new_project('lift',name='Lift Overhead');p['base']['params'].update(height=175,fold=0);p['camera_y']=4;E.save(p,motions/'LiftOverhead.json')
 p=E.new_project('bow',name='Lean Back');p['base']['params']['deep']=-35;E.save(p,motions/'LeanBack.json')
 p=E.new_project('squat',name='Wide Squat');p['base']['params']['spread']=35;E.save(p,motions/'WideSquat.json')
 fusions=ROOT/'examples'/'motions'/'fusions';fusions.mkdir(exist_ok=True)
 def save(p,name):p['name']=name;E.save(p,fusions/(name+'.json'))
 p=E.new_project('run');e=E.entry('wave');e.update(side='left',mix=.8,retain=.35,blend='posture');p['layers']=[e];save(p,'RunWaveLeft')
 for name,base,pose,scope in (('WalkCarry','walk','Carry','upper'),('RunAim','run','Aim','arms'),('WalkGuard','walk','Guard','upper'),('CrouchWalk','walk','Crouch','lower')):
  p=E.new_project(base);e=E.entry('pose');e.update(pose=MR.load_pose(folder/(pose+'.json')),scope=scope,retain=.65 if pose=='Crouch' else .25,ground=pose=='Crouch',blend='posture');p['layers']=[e];save(p,name)
 p=E.new_project('run');e=E.entry('swing');e.update(start=.25,end=.75,fade=.12,mix=.85,retain=.15,blend='replace');p['layers']=[e];save(p,'RunTimedSwing')
 p=E.new_project('stand');p['playback']='once';e=E.entry('pose');e.update(pose=MR.load_pose(folder/'Guard.json'),scope='armL',blend='posture');attack=E.entry('thrust');attack.update(scope='armR',blend='replace');p['layers']=[e,attack];save(p,'GuardAndThrust')
 p=E.new_project('run');p['playback']='once';p['seconds']=1.5;p['fps']=16;p['physics']={};p['controls']={};p['camera_y']=8
 jump=E.entry('jump');jump['params'].update(height=10,tuck=.3)
 roll=E.entry('roll');roll.update(start=.2,end=.75,contact='auto',blend='replace',retain=.15);roll['params']['distance']=0
 p['layers']=[jump,roll];save(p,'RunJumpRoll')
 p=E.new_project('stand');p['yaw']=25;p['base']['params'].update(breath=.6,sway=0)
 p['controls']={'torso':dict(turn=-12,hips_turn=15,height=1,lean=5),
                'arms':dict(raise_=-5,forward=30,fold=85),
                'armR':dict(forward=25,offset=[0,0,0,-15]),
                'head':dict(turn=-20,follow_chest=False)}
 p['controls']['arms']['raise']=p['controls']['arms'].pop('raise_');save(p,'CombatStance')
 p=E.load(fusions/'CombatStance.json');p.update(playback='once',seconds=1.5,fps=16);p['layers']=[E.entry('thrust')];save(p,'CombatStraightPunch')
 p=E.load(fusions/'CombatStance.json');p.update(playback='once',seconds=1.5,fps=24);p['layers']=[E.entry('twist')];save(p,'CombatTwist')
 p=E.load(fusions/'CombatStance.json');p.update(playback='once',seconds=1.5,fps=24);kick=E.entry('kick');kick['style']='push';p['layers']=[kick];save(p,'CombatPushKick')
 p=E.new_project('stand');p['base']['params']['breath']=0;raise_=E.entry('raise');raise_['params'].update(up=45,fold=80,open=8);p['layers']=[raise_];save(p,'ForwardCarry')
 p=E.new_project('jump');p.update(seconds=1.5,fps=24,camera_y=6)
 kick=E.entry('kick');kick.update(start=.2,end=.75,scope='all',blend='replace');p['layers']=[kick];save(p,'JumpKick')
 for name,direction in (('StrafeWalk',90),('Backpedal',180)):
  p=E.new_project('walk');p['base']['params'].update(direction=direction,stance=1.15,support=.6);save(p,name)

if __name__=='__main__':build()
