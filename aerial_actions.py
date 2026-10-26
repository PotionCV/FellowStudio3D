"""Swimming and hovering: periodic full-body motion without floor contact."""
import math
from game_actions import Action,P,curve

TAU=math.tau

class Swim(Action):
 kind='swim';label='游泳';playback='loop';blend='replace';scope='all'
 claims=('armL','armR','legL','legR','dy','body_pitch','body_pivot','chest_yaw','pelvis_yaw','head_pitch')
 params=(P('stroke','划臂幅度',0,1.4,1.,.05),P('kick','蹬腿幅度',0,1.4,.75,.05),
         P('bob','浮动幅度（px）',-3,3,.5,.1),P('tilt','泳姿前后倾（度）',-35,35,0.,1),
         P('roll','身体滚转（度）',-30,30,12.,1))
 @classmethod
 def at(cls,t,p,yaw):
  t=t%1.;style=p.get('_style','breast');stroke=p['stroke'];kick=p['kick']
  pitch={'breast':78.,'crawl':85.,'tread':0.}.get(style,78.)+p['tilt']
  out=dict(body_pitch=pitch,body_pivot=p.get('_float_pivot',10.),dy=-2.+p['bob']*math.cos(TAU*t),
           chest_yaw=0.,pelvis_yaw=0.,head_pitch=-12. if style!='tread' else 0.,_ground=False)
  for side,sign,shift in (('L',-1,0.),('R',1,.5)):
   if style=='crawl':
    u=(t+shift)%1.
    reach=curve(u,[(0,165),(.48,-35),(.62,-55),(1,165)])
    recovery=max(0.,math.sin(math.pi*(u-.5)/.5)) if u>=.5 else 0.
    out['arm'+side]=[sign*(8.+70*recovery)*stroke,0.,reach*stroke,75*recovery*stroke]
    flutter=math.sin(TAU*(2*t+shift))
    out['leg'+side]=[sign*7.,0.,18*flutter*kick,-25*max(0.,flutter)*kick]
   elif style=='tread':
    u=(t+shift)%1.;scull=math.sin(TAU*u)
    out['arm'+side]=[sign*(50+20*scull)*stroke,0.,(45+15*math.cos(TAU*u))*stroke,55*stroke]
    fold=(.5-.5*math.cos(TAU*u))*kick
    out['leg'+side]=[sign*(8+18*fold),0.,35*fold,-70*fold]
   else:
    spread=curve(t,[(0,5),(.18,5),(.43,95),(.65,28),(.86,5),(1,5)])
    reach=curve(t,[(0,165),(.18,165),(.43,65),(.65,85),(.86,165),(1,165)])
    elbow=curve(t,[(0,0),(.25,5),(.50,65),(.65,105),(.86,0),(1,0)])
    out['arm'+side]=[sign*spread*stroke,0.,reach*stroke,elbow*stroke]
    fold=curve(t,[(0,0),(.20,0),(.43,1),(.62,.25),(.82,0),(1,0)])*kick
    opening=curve(t,[(0,0),(.30,0),(.50,.55),(.62,1),(.82,0),(1,0)])*kick
    out['leg'+side]=[sign*(7+32*opening),0.,48*fold,-105*fold]
  if style=='crawl':
   roll=p['roll']*math.sin(TAU*t)
   out.update(chest_yaw=roll,pelvis_yaw=-roll*.3)
  return out

class Hover(Action):
 kind='hover';label='悬浮';playback='loop';blend='replace';scope='all'
 claims=('armL','armR','legL','legR','dy','body_pitch','body_pivot','chest_yaw')
 params=(P('height','离地高度（px）',0,14,5.,.25),P('bob','浮动幅度（px）',-4,4,1.5,.1),
         P('open','手臂展开（度）',0,150,45.,1),P('beat','拍臂幅度（度）',-70,70,12.,1),
         P('fold','悬空屈腿（度）',0,110,35.,1),P('tilt','前倾 / 后仰（度）',-60,60,8.,1))
 @classmethod
 def at(cls,t,p,yaw):
  phase=TAU*(t%1.);wave=math.sin(phase);fold=p['fold'];opening=p['open']+p['beat']*wave
  return dict(armL=[-opening,0.,10.,15.],armR=[opening,0.,10.,15.],
              legL=[-8.,0.,fold*.5,-fold],legR=[8.,0.,fold*.5,-fold],
              dy=-p['height']+p['bob']*math.cos(phase),body_pitch=p['tilt'],
              body_pivot=p.get('_float_pivot',10.),chest_yaw=0.,_ground=False)

CLASSES=(Swim,Hover)
