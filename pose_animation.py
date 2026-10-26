"""Small authored pose cards, with explicit holds and bounded transitions."""
import copy,math

EASINGS={'smooth':'柔和','linear':'匀速','snappy':'利落'}

def capture_pose(pose):
 import motion_resources as MR
 result=MR.pose_channels(pose)
 # Bake the optional independent-head frame into the normal chest-local yaw.
 # The two Y rotations commute before head pitch/roll, so this is exact.
 if not pose.get('head_follow_chest',True):result['head_yaw']=pose.get('head_yaw',0)-pose.get('chest_yaw',0)
 return result

def default_cards():
 import engine as E
 return [dict(pose=E.norm(E.F.POSES[key]),hold=.25,travel=1.,ease='smooth') for key in ('stand','cheer')]

def normalize_cards(cards):
 import engine as E
 if not isinstance(cards,(list,tuple)) or not 2<=len(cards)<=6:raise ValueError('请选择二至六张姿势卡。')
 result=[]
 rest=E.norm(E.F.POSES['stand'])
 for card in cards:
  if not isinstance(card,dict):raise ValueError('无效的姿势卡。')
  raw=capture_pose(card.get('pose',{}))
  pose={key:copy.deepcopy(raw.get(key,rest.get(key,[0.]*9 if key=='tail' else 0.))) for key in E.POSE_CHANNELS}
  timing={}
  for key,default,lo,hi in (('hold',.25,0,4),('travel',1.,.25,4)):
   value=card.get(key,default)
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
    raise ValueError('姿势停留应为0至4拍，过渡应为0.25至4拍。')
   timing[key]=float(value)
  ease=card.get('ease','smooth')
  if ease not in EASINGS:raise ValueError('无效的姿势过渡。')
  result.append(dict(pose=pose,**timing,ease=ease))
 return result

def segments(cards,loop):
 result=[];cursor=0.
 for index,card in enumerate(cards):
  result.append((cursor,cursor+card['hold'],index,index,card['ease']));cursor+=card['hold']
  if loop or index<len(cards)-1:
   result.append((cursor,cursor+card['travel'],index,(index+1)%len(cards),card['ease']));cursor+=card['travel']
 return result,cursor

def sample(cards,t,loop):
 spans,total=segments(cards,loop);position=(t%1 if loop else max(0.,min(1.,t)))*total
 if not loop and t>=1:return copy.deepcopy(cards[-1]['pose'])
 for start,end,a,b,ease in spans:
  if end>start and position<end:
   u=(position-start)/(end-start)
   if ease=='snappy':u=min(1.,u/.45)
   if ease!='linear':u=u*u*(3-2*u)
   first,last=cards[a]['pose'],cards[b]['pose'];result={}
   for key,x in first.items():
    y=last[key]
    result[key]=[v+(w-v)*u for v,w in zip(x,y)] if isinstance(x,list) else x+(y-x)*u
   return result
 return copy.deepcopy(cards[-1]['pose'])

def build(current,cards,seconds=2.,playback='loop',ground=True):
 import engine as E
 if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not .25<=seconds<=10:raise ValueError('动画时长应为0.25至10秒。')
 if playback not in E.MT.MODES:raise ValueError('无效的播放方式。')
 if not 2<=round(seconds*current.get('fps',12))<=120:raise ValueError('姿势动画需要2至120帧，请缩短时长或调整FPS。')
 normalized=normalize_cards(cards);result=copy.deepcopy(current)
 existing=result['base']['kind']=='poseclip' and 'pose' not in result
 entry=E.entry('poseclip');entry.update(cards=normalized,ground=bool(ground))
 if existing:
  for key in ('cycles','phase'):entry[key]=result['base'].get(key,entry[key])
 else:result.update(layers=[],controls={},physics={})
 result.update(base=entry,seconds=float(seconds),playback=playback)
 result.pop('pose',None);result.pop('base_playback',None)
 return result

class PoseAnimation:
 kind='poseclip';label='姿势动画';period=24;params=();add=();claims=()
 @classmethod
 def defaults(cls):return {}
 @classmethod
 def touches(cls,key):return ()
 @classmethod
 def at(cls,t,p,yaw):
  pose=sample(p['_cards'],t,p.get('_loop',True))
  pose['_ground']=bool(p.get('_ground',True))
  if pose['_ground']:pose['_feet_ground']=True
  return pose
