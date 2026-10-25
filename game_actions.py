"""Game-oriented action generators: authored stages, not keyframe timelines."""
import math,copy
TAU=math.tau
REST={'armL':[-22.,6.,0.,0.],'armR':[22.,-6.,0.,0.],'legL':[-6.,4.,0.,0.],'legR':[6.,-4.,0.,0.]}
def P(key,label,lo,hi,default,step=.05):return dict(key=key,label=label,lo=lo,hi=hi,dflt=default,step=step)
def curve(t,points):
 for (a,x),(b,y) in zip(points,points[1:]):
  if t<=b:
   u=max(0.,min(1.,(t-a)/max(.001,b-a)));u=u*u*(3-2*u);return x+(y-x)*u
 return points[-1][1]
def stages(t,p):
 a=p.get('prepare',.2);b=min(.9,a+p.get('release',.18))
 return curve(t,[(0,0),(a,-.3),(b,1),(1,0)]),curve(t,[(0,0),(a,0),(b,1),(1,0)])

def windup(t,p):
 a=p['prepare'];b=min(.9,a+p['release'])
 return curve(t,[(0,0),(a,1),(b,0),(1,0)])*p.get('windup',1.)

class Action:
 params=();claims=();unilateral=False;playback='once';blend='add';scope='all';hint=''
 @classmethod
 def defaults(cls):return {p['key']:p['dflt'] for p in cls.params}
 @classmethod
 def touches(cls,key):return cls.claims

class Pose(Action):
 kind='pose';label='姿势层';playback='loop';blend='add'
 @classmethod
 def at(cls,t,p,yaw):return copy.deepcopy(p.get('_pose',REST))

class Jump(Action):
 kind='jump';label='起跳与落地';claims=tuple(REST)+('dy','lean')
 params=(P('height','跳跃高度（px）',0,14,7,.25),P('crouch','准备下蹲',0,1,.55),P('tuck','腾空收腿',0,1,.5),P('prepare','准备时间',.08,.4,.2),P('landing','落地时间',.1,.4,.25),P('forward','腾空前倾',-25,35,8,1))
 @classmethod
 def at(cls,t,p,yaw):
  a=p['prepare'];land=1-p['landing'];phase=max(0.,min(1.,(t-a)/max(.1,land-a)))
  airborne=a<t<land;flight=4*phase*(1-phase) if airborne else 0.
  c=curve(t,[(0,0),(a*.65,p['crouch']),(a,0),(land,0),(land+p['landing']*.35,p['crouch']*.7),(1,0)])
  bend=50*c+35*p['tuck']*flight
  return {'legL':[-6.,4.,bend,-2*bend],'legR':[6.,-4.,bend,-2*bend],
   'armL':[-22-55*flight,6.,-18*c,0.],'armR':[22+55*flight,-6.,-18*c,0.],
   'dy':12*(1-math.cos(math.radians(50*c)))-p['height']*flight,'lean':p['forward']*flight+10*c,'_ground':not airborne}

class Thrust(Action):
 kind='thrust';label='刺击';unilateral=True;scope='all';claims=('armR','chest_yaw','pelvis_yaw','lean')
 params=(P('reach','攻击幅度',0,1.5,1),P('angle','攻击仰角',-60,70,0,2),P('windup','蓄力幅度',0,1.5,1),P('prepare','蓄力时间',.05,.45,.22),P('release','发力时间',.06,.4,.15),P('twist','身体带动',-3,3,1))
 @classmethod
 def at(cls,t,p,yaw):
  arm,drive,_=cls.from_guard(t,p,REST['armR'],'right')
  return dict(armR=arm,**drive)
 @classmethod
 def from_guard(cls,t,p,guard,side):
  """Prepare, extend and recover relative to the actual input guard pose."""
  a,b=stages(t,p);reach=max(0.,p['reach']);extension=min(1.,b*reach);chamber=windup(t,p)*min(1.,reach)
  sign=-1 if side=='left' else 1
  prepared=[guard[0]+(sign*14-guard[0])*min(1.,chamber),guard[1]*(1-.65*min(1.,chamber)),
   guard[2]+(-25-guard[2])*chamber,min(155.,guard[3]+(max(110.,guard[3])-guard[3])*chamber)]
  target=[sign*8.,0.,90+p['angle'],0.]
  arm=[x+(y-x)*extension for x,y in zip(prepared,target)]
  # A straight punch uses a compact shoulder/hip drive, not a quarter turn.
  turn=b-.45*windup(t,p)
  return arm,dict(chest_yaw=-sign*22*turn*p['twist']*min(1.5,reach),pelvis_yaw=-sign*10*turn*p['twist']*min(1.5,reach),lean=(6*b-4*windup(t,p))*p['twist']*min(1.5,reach)),extension

class Swing(Thrust):
 kind='swing';label='挥击'
 params=Thrust.params+(P('arc','横扫 / 下劈',0,1,.25),)
 @classmethod
 def at(cls,t,p,yaw):
  arm,drive,_=cls.from_guard(t,p,REST['armR'],'right')
  return dict(armR=arm,**drive)
 @classmethod
 def from_guard(cls,t,p,guard,side):
  _,b=stages(t,p);reach=max(0.,p['reach']);extension=min(1.,b*reach)
  chamber=windup(t,p)*min(1.,reach);arc=p['arc'];sign=-1 if side=='left' else 1
  prepared=[guard[0]-sign*35*(1-arc)*chamber,guard[1],
   guard[2]+(-55*(1-arc)+40*arc)*chamber,min(155.,guard[3]+(max(105.,guard[3])-guard[3])*chamber)]
  target=[sign*(22+75*(1-arc)),0.,65+80*arc+p['angle'],20.]
  arm=[x+(y-x)*extension for x,y in zip(prepared,target)]
  turn=(b-.8*windup(t,p))*min(1.5,reach)*p['twist']
  return arm,dict(chest_yaw=-sign*65*turn,pelvis_yaw=-sign*30*turn,lean=14*b*arc),extension

class Kick(Thrust):
 kind='kick';label='踢击';scope='all';claims=('legR','legL','lean','dy','chest_yaw','pelvis_yaw')
 params=tuple(p for p in Thrust.params if p['key']!='windup')
 @classmethod
 def at(cls,t,p,yaw):
  if p.get('_style')=='push':
   # Chamber the knee, drive the foot forward, then fold before lowering.
   prepare=p['prepare'];strike=min(.9,prepare+p['release'])
   hold=strike+(1-strike)*.1;retract=strike+(1-strike)*.5
   reach=max(0.,p['reach'])
   hip=curve(t,[(0,0),(prepare,75),(strike,95+p['angle']),(hold,95+p['angle']),(retract,75),(1,0)])*reach
   knee=curve(t,[(0,0),(prepare,-135),(strike,0),(hold,0),(retract,-135),(1,0)])*min(1.,reach)
   drive=curve(t,[(0,0),(prepare,.2),(strike,1),(hold,1),(retract,.2),(1,0)])*min(1.,reach)
   turn=curve(t,[(0,0),(prepare,-.3),(strike,1),(hold,1),(retract,.2),(1,0)])*min(1.,reach)*p['twist']
   return {'legR':[6.,-4.,hip,knee],'legL':list(REST['legL']),
    'lean':-15*drive*p['twist'],'chest_yaw':-20*turn,'pelvis_yaw':-35*turn,'dy':0.,'_ground':True}
  a,b=stages(t,p);return {'legR':[6.,-4.,max(-20,95*a*p['reach'])+p['angle']*b,-50*max(0,-a)],
   'legL':REST['legL'],'lean':-15*b*p['twist'],'chest_yaw':-20*a*p['twist'],'pelvis_yaw':-35*a*p['twist'],'dy':0.,'_ground':True}

class Twist(Action):
 kind='twist';label='扭腰回正';claims=('chest_yaw','pelvis_yaw')
 params=(P('angle','扭腰角度（度）',-120,120,60,2),P('hips','骨盆跟随',-1,1,.45),P('prepare','蓄力时间',.05,.45,.22),P('release','发力时间',.06,.4,.18))
 @classmethod
 def at(cls,t,p,yaw):
  turn,_=stages(t,p);turn*=p['angle']
  return {'chest_yaw':turn,'pelvis_yaw':turn*p['hips']}

class Lift(Action):
 kind='lift';label='取放物品';playback='hold';unilateral=True
 claims=tuple(REST)+('lean','dy')
 params=(P('bend','取物弯腰（度）',0,75,65,1),P('crouch','取物下蹲',0,1,1),
  P('reach','向前够取（度）',0,60,10,1),P('height','举起高度（度）',0,180,55,2),
  P('fold','举起屈肘（度）',0,135,70,2),P('spacing','双手间距（度）',0,40,8,1),P('contact','够到物品的时刻',.2,.65,.4))
 @classmethod
 def reach_factor(cls,p,model,side='both'):
  """Long arms/short legs need less crouching to reach the same floor."""
  import rounded_scene as S
  def clearance(factor):
   q=cls.at(p['contact'],dict(p,_operation='pickup',_reach_factor=factor),0);q['_model']=model
   goal=q['armR'];q['armL']=[-goal[0],-goal[1],goal[2],goal[3]] if side in ('left','both') else q['armL']
   if side=='left':q['armR']=REST['armR']
   arms=('lowerArmL','lowerArmR') if side=='both' else ('lowerArmL',) if side=='left' else ('lowerArmR',)
   return S.ground_y(q,arms)-S.ground_y(q,('thighL','shinL','thighR','shinR'))
  if clearance(1)>=.1:return 1.
  lo,hi=0.,1.
  for _ in range(12):
   mid=(lo+hi)/2
   if clearance(mid)>=.1:lo=mid
   else:hi=mid
  return lo
 @classmethod
 def at(cls,t,p,yaw):
  if p.get('_operation')=='putdown':t=1-t
  contact=p['contact'];down=curve(t,[(0,0),(contact,1),(1,0)])*p.get('_reach_factor',1.)
  carry=curve(t,[(0,0),(contact,0),(1,1)]);active=curve(t,[(0,0),(contact,1),(1,1)])
  knee=55*p['crouch']*down;spread=22+(p['spacing']-22)*active
  fold=min(p['fold'],max(0.,180-p['height']))
  pitch=(p['bend']+p['reach'])*down+p['height']*carry
  lateral=spread if pitch<=90 else -spread
  return {'armL':list(REST['armL']),'armR':[lateral,-6*(1-active),pitch,fold*carry],
   'legL':[-6,4,knee,-2*knee],'legR':[6,-4,knee,-2*knee],
   'lean':p['bend']*down,'dy':12*(1-math.cos(math.radians(knee))),'_ground':True}

class Hit(Action):
 kind='hit';label='受击';claims=('rot','lean','dx','dy','head_pitch')
 params=(P('strength','受击强度',0,1.5,.8),P('direction','受力方向（度）',-180,180,0,15),P('release','冲击时间',.04,.4,.12),P('recover','恢复程度',0,1,1))
 @classmethod
 def at(cls,t,p,yaw):
  value=curve(t,[(0,0),(p['release'],1),(1,1-p['recover'])])*p['strength'];angle=math.radians(p['direction'])
  return {'rot':25*math.sin(angle)*value,'lean':-28*math.cos(angle)*value,'dx':-3*math.sin(angle)*value,'dz':-2*math.cos(angle)*value,'dy':value,'head_pitch':-18*value,'_ground':True}

class Fall(Action):
 kind='fall';label='倒地';playback='hold';claims=('rot','body_pitch','dy')
 params=(P('direction','倒地方向（度）',-180,180,0,15),P('delay','失衡准备',0,.5,.18),P('curl','蜷缩程度',0,1,.35))
 @classmethod
 def at(cls,t,p,yaw):
  u=curve(t,[(0,0),(p['delay'],.08),(1,1)]);a=math.radians(p['direction']);c=p['curl']*u
  return {'rot':0.,'body_axis':p['direction'],'body_pitch':90*u,'legL':[-6,4,50*c,-100*c],'legR':[6,-4,50*c,-100*c],
   'armL':[-22-35*u,6,35*u,30*u],'armR':[22+35*u,-6,35*u,30*u],'head_pitch':15*u,'_ground':True}

class GetUp(Fall):
 kind='getup';label='起身';playback='once'
 @classmethod
 def at(cls,t,p,yaw):return super().at(1-t,p,yaw)

class Roll(Action):
 kind='roll';label='翻滚';claims=tuple(REST)+('body_pitch','rot','dy','dz','dx')
 params=(P('direction','翻滚方向（度）',-180,180,0,15),P('curl','蜷缩程度',.3,1,.8),P('distance','移动距离（px）',-12,12,4,.5))
 @classmethod
 def at(cls,t,p,yaw):
  u=curve(t,[(0,0),(.15,.04),(.85,.96),(1,1)]);c=p['curl']*math.sin(math.pi*t);a=math.radians(p['direction'])
  return {'body_pitch':360*u,'body_axis':p['direction'],'body_pivot':p.get('_roll_pivot',10.),'rot':0.,'legL':[-6,4,90*c,-140*c],'legR':[6,-4,90*c,-140*c],
   'armL':[-22,6,70*c,60*c],'armR':[22,-6,70*c,60*c],'head_pitch':35*c,
   'dx':p['distance']*t*math.sin(a),'dz':p['distance']*t*math.cos(a),'_ground':True}

class Climb(Action):
 kind='climb';label='攀爬循环';playback='loop';claims=tuple(REST)+('dy','lean')
 params=(P('reach','攀爬幅度',.2,1.5,1),P('spacing','手脚张开',-1,1,.4),P('bob','身体起伏',-3,3,.8,.1))
 @classmethod
 def at(cls,t,p,yaw):
  s=math.sin(TAU*t);r=p['reach'];o=p['spacing']
  return {'armL':[-22-20*o,6,115*r+35*r*s,35*(1-s)],'armR':[22+20*o,-6,115*r-35*r*s,35*(1+s)],
   'legL':[-6-15*o,4,35*r*(1-s),-55*r*(1-s)],'legR':[6+15*o,-4,35*r*(1+s),-55*r*(1+s)],'dy':p['bob']*math.cos(TAU*t*2),'lean':8.}

class Turn(Action):
 kind='turn';label='原地转身';playback='hold';claims=('yaw','chest_yaw','pelvis_yaw')
 params=(P('angle','转身角度',-180,180,90,15),P('lead','骨盆 / 上身先行',-1,1,.5))
 @classmethod
 def at(cls,t,p,yaw):
  u=curve(t,[(0,0),(1,1)]);twist=math.sin(math.pi*t)*p['lead']*20
  return {'yaw':p['angle']*u,'chest_yaw':twist,'pelvis_yaw':-twist*.5,'_ground':True,
   'legL':[-6,4,10*math.sin(TAU*t),-18*max(0,math.sin(TAU*t))],'legR':[6,-4,-10*math.sin(TAU*t),-18*max(0,-math.sin(TAU*t))]}

CLASSES=(Pose,Jump,Thrust,Swing,Kick,Twist,Lift,Hit,Fall,GetUp,Roll,Climb,Turn)
