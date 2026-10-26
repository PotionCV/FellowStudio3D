"""Rebuild only the three registered pose-card animation recipes."""
import sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import engine as E,pose_animation as PA,motion_resources as MR

def card(pose,hold=.25,travel=1.,ease='smooth'):
 return dict(pose=MR.pose_channels(pose),hold=hold,travel=travel,ease=ease)

def build():
 folder=ROOT/'examples'/'motions'/'posecards';folder.mkdir(parents=True,exist_ok=True)
 def save(name,cards,mode='loop',seconds=2):
  p=E.new_project(name=name);p.update(fps=16,yaw=20)
  p=PA.build(p,cards,seconds,mode,True);E.save(p,folder/(name+'.json'))
 rest=E.norm(E.F.POSES['stand'])
 step=copy.deepcopy(rest);step.update(armL=[-75,25,25,75],armR=[40,-10,-30,45],legL=[-12,0,12,-25],legR=[16,0,-8,-12],chest_yaw=-18,pelvis_yaw=12,head=-12,head_yaw=18,dx=-1)
 cross=copy.deepcopy(rest);cross.update(armL=[-45,10,55,100],armR=[45,-10,55,100],legL=[-8,0,25,-50],legR=[8,0,25,-50],lean=8,head_pitch=12)
 save('SideStepDance',[card(step,.15),card(cross,0,.5,'snappy'),card(E.mirror_pose(step),.15),card(cross,0,.5,'snappy')])
 guard=MR.load_pose(ROOT/'examples'/'poses'/'Guard.json')
 signal=copy.deepcopy(rest);signal.update(armR=[145,-10,25,25],armL=[-25,10,30,75],head_yaw=-25,chest_yaw=-12)
 ready=copy.deepcopy(guard);ready.update(head_yaw=25,head_pitch=-5,chest_yaw=15)
 save('GuardSignal',[card(guard,.5,1),card(ready,.5,.5,'snappy'),card(signal,1.5)],'hold',2.5)
 shy=copy.deepcopy(rest);shy.update(armL=[-30,10,35,105],armR=[30,-10,35,105],head=18,head_pitch=15,head_yaw=-30,lean=5)
 glance=copy.deepcopy(shy);glance.update(head_yaw=20,head_pitch=-5,head=5)
 greet=copy.deepcopy(glance);greet.update(armR=[85,-8,25,70],head=-10)
 save('ShyGreeting',[card(shy,.6,.6),card(glance,.4,.35,'snappy'),card(greet,.8,1.2),card(shy,.2,.5)],'once',3)
 return folder

if __name__=='__main__':print(build())
