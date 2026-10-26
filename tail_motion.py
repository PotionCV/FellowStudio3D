"""Reusable three-joint tail motion, independent of character geometry."""
import math
class TailMotion:
 kind='tail';label='尾巴摆动';period=24;claims=('tail',);add=('tail',);playback='loop';blend='add';scope='all'
 params=tuple(dict(key=k,label=label,lo=lo,hi=hi,dflt=default,step=step) for k,label,lo,hi,default,step in (
  ('sway','左右摆动（度）',-70,70,25,1),('lift','上下摆动（度）',-70,70,0,1),('follow','尾尖跟随',0,1,.65,.05)))
 @classmethod
 def defaults(cls):return {p['key']:p['dflt'] for p in cls.params}
 @classmethod
 def touches(cls,key):return cls.claims
 @classmethod
 def at(cls,t,p,yaw):
  result=[]
  for joint in range(3):
   phase=math.tau*(t%1-joint*p['follow']*.12)
   result.extend((p['lift']*math.sin(phase)*(.5+.25*joint),p['sway']*math.sin(phase)*(.45+.2*joint),0.))
  return {'tail':result}
