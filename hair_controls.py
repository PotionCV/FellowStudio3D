"""Compact per-lock bone and secondary-motion controls in the main panel."""
import tkinter as tk
import hair,model_data as M,rounded_scene as S,engine as E,render_options as O
from pixel_ui import PixelOption

def active(model):return [p for p in M.normalize(model).get('attachments',[]) if p.get('kind')=='hair' and p['section']!='cap']

def selected(app,model):
    items=active(model)
    return next((p for p in items if hair.channel(p)==getattr(app,'hair_channel',None)),items[0] if items else None)

def mount(app,controls):
    items=active(app.project.get('model'));choices={hair.name(p):hair.channel(p) for p in items}
    if not choices:app.note('当前发型没有可动发束。');return
    channel=getattr(app,'hair_channel',None)
    if channel not in choices.values():channel=next(iter(choices.values()))
    app.hair_channel=channel;value=tk.StringVar(master=app,value=next(k for k,v in choices.items() if v==channel))
    def pick(label):app.hair_channel=choices[label];app.show_params();app.render()
    PixelOption(app.params,value,*choices,command=pick).pack(fill='x',padx=12,pady=6)
    bone=getattr(app,'hair_bone',0);names=('发根','发中','发梢');value=tk.StringVar(master=app,value=names[bone])
    def pick_bone(label):app.hair_bone=names.index(label);app.show_params();app.render()
    PixelOption(app.params,value,*names,command=pick_bone).pack(fill='x',padx=12,pady=6)
    def save_controls():app.project['controls']['hair']=controls
    for axis,label in (('pitch','上下弯曲（度）'),('yaw','左右弯曲（度）'),('roll','扭转（度）')):app.slide(label,controls,channel+'_'+('root','middle','tip')[bone]+'_'+axis,-90,90,0,1,onchange=save_controls)
    app.slide('摆动幅度',controls,'range',0,2,1,.05,onchange=save_controls)
    app.note('发顶固定跟随头部。发束可以单独摆姿势，叠加“头发飘动”后继续融合。')
    physics=dict(app.project['physics'].get('hair',hair.DEFAULT_PHYSICS))
    def save_physics():app.project['physics']['hair']=physics
    app.note('物理跟随 · 随身体运动产生惯性')
    for key,label in (('root','发根松软'),('middle','发中松软'),('tip','发梢松软')):app.slide(label,physics,key,0,1,physics.get('strength',hair.DEFAULT_PHYSICS[key]),.05,onchange=save_physics)
    app.slide('回弹',physics,'bounce',0,1,.25,.05,onchange=save_physics)
    app.note('短发默认更硬，长发和马尾更柔软。松软为0时仅保留主动动作；尚无肩背碰撞。')

def points(app,view):
    pose=app.view_pose(view);model=pose.get('_model')
    if not model:return []
    item=selected(app,model)
    if item is None:return []
    dx,dy=O.offset(app.active_project.get('render'));head=S.geometry(pose)[-1]
    return [(x+dx,y+dy) for x,y in (E.R._project(pose,p) for p in hair.joints(item,model,head,pose))]
