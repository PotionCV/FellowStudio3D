"""Shared anatomical attachment frames, independent of camera and UV layout."""
import numpy as np
import i18n

LABELS={'head':'头部','neck':'颈部','torso':'胸口','back':'背部','pelvis':'骨盆',
        'upperArmL':'左上臂','lowerArmL':'左前臂','armL':'左手',
        'upperArmR':'右上臂','lowerArmR':'右前臂','armR':'右手',
        'thighL':'左大腿','shinL':'左小腿','legL':'左脚',
        'thighR':'右大腿','shinR':'右小腿','legR':'右脚'}
for zh,en,ja in (
 ('跟随骨骼','Follow bone','追従する骨'),('头部','Head','頭'),('颈部','Neck','首'),
 ('胸口','Chest','胸'),('背部','Back','背中'),('骨盆','Pelvis','骨盤'),
 ('左上臂','Left upper arm','左上腕'),('右上臂','Right upper arm','右上腕'),
 ('左前臂','Left forearm','左前腕'),('右前臂','Right forearm','右前腕'),
 ('左大腿','Left thigh','左太もも'),('右大腿','Right thigh','右太もも'),
 ('左小腿','Left shin','左すね'),('右小腿','Right shin','右すね'),
 ('左脚','Left foot','左足'),('右脚','Right foot','右足'),
 ('切换骨骼会复位局部位置；形状、贴图和动画保留。','Changing the bone resets local position; shape, textures and animation stay.','骨の変更でローカル位置をリセット。形状・画像・動きは保持します。'),
 ('位置相对所选骨骼，使用原始像素单位。','Position is relative to the selected bone, in base pixels.','位置は選んだ骨を基準とする元のピクセル単位です。'),
 ('位置按头部比例；尺寸按原始像素。','Position uses head proportions; dimensions use base pixels.','位置は頭の比率、サイズは元のピクセル単位です。')):
 i18n.CATALOG.setdefault(zh,{'zh':zh,'en':en,'ja':ja})

def validate(parent):
 if not isinstance(parent,str) or parent not in LABELS:raise ValueError('Invalid attachment bone')
 return parent

def mirrored(parent):
 other=parent[:-1]+('R' if parent.endswith('L') else 'L')
 return other if other in LABELS else parent

def rebind(item,parent):
 validate(parent)
 if item['parent']==parent:return
 item.update(parent=parent,x=0.,y=0.,z=0.)
 if item.get('kind')=='ear' and parent=='head':
  import attachments as A
  item.update({k:A.PRESETS[item['preset']][k] for k in ('x','y','z')})
 elif item.get('kind')=='tail' and parent=='pelvis':
  import tails
  item.update({k:tails.PRESETS[item['preset']][k] for k in ('x','y','z')})

def frame(parent,model,pose):
 import rounded_scene as S
 from core3d import rx,ry,rz
 validate(parent)
 _,j,chains,_,torso,head=S.geometry(pose)
 if parent=='head':return head
 if parent=='neck':return j['neck']['tip'],torso[1]
 if parent=='torso':return torso
 if parent=='back':
  depth=model['body']['depth']/2 if model.get('structure')=='plush' else 3.5*model['torso']['thickness']
  return torso[0]+torso[1]@np.array((0.,0.,-depth-.6)),torso[1]
 if parent=='pelvis':return j['waist']['tip'],S.root_rotation(pose)@ry(pose.get('pelvis_yaw',0))@rz(-pose.get('pelvis',0))
 side=parent[-1];arm=parent.startswith(('arm','upperArm','lowerArm'));chain=('arm' if arm else 'leg')+side
 first=parent.startswith(('upperArm','thigh'));end=parent.startswith(('arm','leg'))
 lat,bend,sag,fold=(tuple(pose.get(chain,(0,0)))+(0,0,0,0))[:4]
 rotation=S.root_rotation(pose)
 if arm:rotation=rotation@rx(pose.get('lean',0))@ry(pose.get('chest_yaw',0))
 else:rotation=rotation@ry(pose.get('pelvis_yaw',0))
 rotation=rotation@rz(lat+(0 if first else bend))@rx(-sag-(0 if first else fold))
 return chains[chain][3 if end else 1 if first else 2],rotation

def mount(parent,editor,item,on_change):
 import tkinter as tk
 import localized_ui as UI
 from pixel_ui import PixelOption
 UI.Label(parent,text='跟随骨骼',anchor='w').pack(fill='x',pady=(8,2))
 choices={i18n.tr(label):key for key,label in LABELS.items()}
 value=tk.StringVar(master=editor,value=i18n.tr(LABELS[item['parent']]))
 option=PixelOption(parent,value,*choices,command=lambda label:on_change(choices[label]));option.pack(fill='x',pady=4)
 UI.Label(parent,text='切换骨骼会复位局部位置；形状、贴图和动画保留。',wrap=True,anchor='w',font=editor.caption_font).pack(fill='x',pady=4)
 return option

PROP_LABELS={'pitch':'局部俯仰（度）','yaw':'局部转向（度）','roll':'局部侧倾（度）',
             'x':'局部左右（px）','y':'局部上下（px）','z':'局部前后（px）'}
for zh,en,ja in (
 ('位置与角度','Position and angles','位置と角度'),('收起位置与角度','Hide position and angles','位置と角度を隠す'),
 ('复位位置与角度','Reset position and angles','位置と角度をリセット'),
 ('局部俯仰（度）','Local pitch (degrees)','ローカル上下角（度）'),('局部转向（度）','Local yaw (degrees)','ローカル左右角（度）'),
 ('局部侧倾（度）','Local roll (degrees)','ローカル傾き（度）'),('局部左右（px）','Local X (px)','ローカルX（px）'),
 ('局部上下（px）','Local Y (px)','ローカルY（px）'),('局部前后（px）','Local Z (px)','ローカルZ（px）')):
 i18n.CATALOG.setdefault(zh,{'zh':zh,'en':en,'ja':ja})
