"""Staged pose-card authoring, reusing the proven four-view preview worker."""
import copy,math,tkinter as tk
from tkinter import filedialog,messagebox
import engine as E,pose_animation as PA,motion_resources as MR
from model_editor import ModelEditor,BG,PANEL,INK,VIEWS
from pixel_ui import PixelButton,PixelOption,PixelScale,PixelCheck,ScrollPanel,FlowBar
import localized_ui as UI
from i18n import tr

class PoseAnimationEditor(ModelEditor):
 def __init__(self,owner):
  self.caption_font=owner.caption_font
  self.original_project=copy.deepcopy(owner.project);self.edit_motion=False;self.queued_play=False;self.card_index=0;self.drag_pose=None
  existing=owner.project['base']['kind']=='poseclip' and 'pose' not in owner.project
  if existing:
   # Retained modifiers must not be baked into newly captured cards again.
   source=copy.deepcopy(owner.project);source.update(layers=[],controls={},physics={});self.capture_seq=E.poses(source)
  else:self.capture_seq=copy.deepcopy(owner.seq) if owner.active_project==owner.project and not getattr(owner,'preview_incomplete',False) else E.poses(owner.project)
  self.capture_label='基础动作帧' if existing else '原动作帧'
  self.cards=PA.normalize_cards(owner.project['base']['cards'] if existing else PA.default_cards())
  if not existing and owner.seq and owner.active_project==owner.project:self.cards[0]['pose']=PA.capture_pose(owner.seq[owner.frame])
  self.cards=PA.normalize_cards(self.cards)
  super().__init__(owner)
  if not existing:
   self.cards[0]['pose']=PA.capture_pose(self.capture_seq[owner.frame%len(self.capture_seq)]);self.cards=PA.normalize_cards(self.cards)
  self.title(tr('姿势动画'));self.part='armR';self.show_params()
 def _build(self):
  footer=tk.Frame(self,bg=PANEL);footer.pack(side='bottom',fill='x',padx=12,pady=8)
  self.status=tk.StringVar(master=self,value=tr('姿势卡修改仅在应用后写入项目'))
  UI.Label(footer,textvariable=self.status,wrap=True,font=self.owner.caption_font).pack(side='left',fill='x',expand=True)
  PixelButton(footer,text='取消',command=self.cancel).pack(side='right')
  PixelButton(footer,text='应用姿势动画',command=self.apply,accent=True).pack(side='right',padx=6)
  body=tk.PanedWindow(self,orient='horizontal',sashwidth=12,bg=BG);body.pack(fill='both',expand=True,padx=12,pady=8)
  center=tk.Frame(body,bg=BG);body.add(center,minsize=420,stretch='always')
  self.canvas=tk.Canvas(center,bg='#5a4d42',highlightthickness=0);self.canvas.pack(fill='both',expand=True)
  self.canvas.bind('<Configure>',self.resize);self.canvas.bind('<Button-1>',self.pick)
  self.canvas.bind('<B1-Motion>',self.move_pose);self.canvas.bind('<ButtonRelease-1>',self.end_pose)
  self.canvas.bind('<Double-Button-1>',self.toggle_single_view)
  bar=FlowBar(center,compact=True);bar.pack(fill='x')
  self.play_button=PixelButton(bar,text='▶ 播放',command=self.toggle_play,accent=True);self.play_button.pack(side='left')
  PixelCheck(bar,text='单视图',variable=self.single_view,command=self.draw).pack(side='left',padx=8)
  self.time_text=tk.StringVar(master=self);UI.Label(bar,textvariable=self.time_text,font=self.owner.caption_font).pack(side='right')
  self.scrub=PixelScale(center,from_=0,to=1000,resolution=1,command=self.seek);self.scrub.pack(fill='x')
  shell=tk.Frame(body,bg=PANEL);body.add(shell,width=round(430*self.ui_scale),minsize=330,stretch='never')
  self.scroll=ScrollPanel(shell);self.scroll.pack(fill='both',expand=True);content=self.scroll.content
  UI.Label(content,text='用二至六张姿势卡生成动作；选择卡片后可拖动手脚或调整角度。',wrap=True,font=self.owner.caption_font).pack(fill='x',padx=10,pady=8)
  self.card_list=tk.Listbox(content,height=4,exportselection=False,activestyle='none',font=self.owner.caption_font)
  self.card_list.pack(fill='x',padx=10);self.card_list.bind('<<ListboxSelect>>',self.pick_card)
  bar=FlowBar(content,compact=True);bar.pack(fill='x',padx=8,pady=4)
  self.card_buttons={};self.add_buttons=[]
  for label,fn in (('上移',lambda:self.move_card(-1)),('下移',lambda:self.move_card(1)),('复制',self.duplicate_card),('移除',self.remove_card),('镜像',self.mirror_card)):
   button=PixelButton(bar,text=label,command=fn);button.pack(side='left');self.card_buttons[label]=button
  bar=FlowBar(content,compact=True);bar.pack(fill='x',padx=8)
  self.preset=tk.StringVar(master=self,value=next(iter(E.POSES)))
  PixelOption(bar,self.preset,*E.POSES).pack(side='left',fill='x',expand=True)
  button=PixelButton(bar,text='＋ 添加',command=self.add_preset);button.pack(side='left');self.add_buttons.append(button)
  bar=FlowBar(content,compact=True);bar.pack(fill='x',padx=8,pady=4)
  button=PixelButton(bar,text='载入姿势…',command=self.load_card);button.pack(side='left');self.add_buttons.append(button)
  PixelButton(bar,text='保存姿势…',command=self.save_card).pack(side='left')
  bar=FlowBar(content,compact=True);bar.pack(fill='x',padx=8,pady=4)
  UI.Label(bar,text=self.capture_label,font=self.owner.caption_font).pack(side='left')
  self.capture_frame=tk.StringVar(master=self,value=str(self.owner.frame+1))
  PixelOption(bar,self.capture_frame,*map(str,range(1,len(self.capture_seq)+1))).pack(side='left')
  button=PixelButton(bar,text='采集为姿势卡',command=self.capture_card);button.pack(side='left');self.add_buttons.append(button)
  settings=FlowBar(content,compact=True);settings.pack(fill='x',padx=8,pady=6)
  UI.Label(settings,text='时长（秒）',font=self.owner.caption_font).pack(side='left')
  fps=self.original_project.get('fps',12)
  self.duration=tk.StringVar(master=self,value=str(max(.25,2/fps,min(10,120/fps,self.original_project.get('seconds',2)))))
  PixelOption(settings,self.duration,*[str(v) for v in (.5,1.,1.5,2.,3.,4.,5.,6.,8.,10.) if 2<=round(v*fps)<=120],command=lambda _:self.update_preview()).pack(side='left')
  self.mode_choices={'循环':'loop','播放一次':'once','保持末帧':'hold'}
  self.mode=tk.StringVar(master=self,value=next(k for k,v in self.mode_choices.items() if v==E.MT.mode(self.original_project)))
  PixelOption(settings,self.mode,*self.mode_choices,command=lambda _:self.mode_changed()).pack(side='left')
  self.ground=tk.BooleanVar(master=self,value=self.original_project['base'].get('ground',self.capture_seq[self.owner.frame%len(self.capture_seq)].get('_ground',True)))
  PixelCheck(content,text='保持地面接触',variable=self.ground,command=self.update_preview).pack(fill='x',padx=10)
  self.part_value=tk.StringVar(master=self,value='右臂')
  has_tail=any(p.get('kind')=='tail' for p in (self.original_project.get('model') or {}).get('attachments',[]))
  self.part_choices={E.LABELS[key]:key for key in (*E.LIMBS,'head','torso',*(['tail'] if has_tail else []))}
  PixelOption(content,self.part_value,*self.part_choices,command=lambda value:self.select(self.part_choices[value])).pack(fill='x',padx=10,pady=6)
  self.params=tk.Frame(content);self.params.pack(fill='x')
  UI.Label(content,text='新建时替换原动作与整体修改；已有姿势动画保留叠加与整体修改。应用可撤销。',wrap=True,font=self.owner.caption_font).pack(fill='x',padx=10,pady=10)
  UI.Label(content,text='卡片视图显示原姿势；播放时显示叠加和整体修改。拍数控制相对节奏，时长控制总长度。',wrap=True,font=self.owner.caption_font).pack(fill='x',padx=10,pady=(0,10))
  self.refresh_cards()
 def refresh_cards(self):
  self.card_list.delete(0,'end')
  for i,card in enumerate(self.cards):
   travel=f' + {card["travel"]:g}' if i<len(self.cards)-1 or self.mode_choices[self.mode.get()]=='loop' else ''
   self.card_list.insert('end',f'{i+1}. {tr("姿势卡")}  ·  {card["hold"]:g}{travel}')
  self.card_index=max(0,min(self.card_index,len(self.cards)-1));self.card_list.selection_set(self.card_index)
  for button in self.add_buttons+[self.card_buttons['复制']]:button.configure(state='disabled' if len(self.cards)>=6 else 'normal')
  for label,disabled in (('上移',self.card_index==0),('下移',self.card_index==len(self.cards)-1),('移除',len(self.cards)<=2)):
   self.card_buttons[label].configure(state='disabled' if disabled else 'normal')
 def pick_card(self,event=None):
  if not self.card_list.curselection():return
  self.card_index=self.card_list.curselection()[0];self.refresh_cards();self.show_params();self.update_preview()
 def select(self,key):self.part=key;self.show_handles=key!='tail';self.part_value.set(E.LABELS[key]);self.show_params();self.draw()
 def show_params(self):
  for child in self.params.winfo_children():child.destroy()
  card=self.cards[self.card_index]
  bar=FlowBar(self.params,compact=True);bar.pack(fill='x',padx=8)
  for key,label,values in (('hold','停留（拍）',(0.,.25,.5,1.,2.,4.)),('travel','过渡（拍）',(.25,.5,1.,2.,4.))):
   if key=='travel' and self.card_index==len(self.cards)-1 and self.mode_choices[self.mode.get()]!='loop':continue
   unit=tk.Frame(bar);unit.pack(side='left');UI.Label(unit,text=label,font=self.owner.caption_font).pack(side='left')
   value=tk.StringVar(master=self,value=str(card[key]));PixelOption(unit,value,*map(str,values),command=lambda v,k=key:self.set_timing(k,float(v))).pack(side='left')
  if self.card_index<len(self.cards)-1 or self.mode_choices[self.mode.get()]=='loop':
   easing={v:k for k,v in PA.EASINGS.items()};value=tk.StringVar(master=self,value=PA.EASINGS[card['ease']])
   PixelOption(self.params,value,*easing,command=lambda v:self.set_timing('ease',easing[v])).pack(fill='x',padx=10,pady=4)
  pose=card['pose'];part=self.part
  if part=='tail':
   selected=getattr(self,'tail_bone',0);names=('尾根','尾中','尾尖');choice=tk.StringVar(master=self,value=names[selected])
   def pick(value):self.tail_bone=names.index(value);self.show_params()
   PixelOption(self.params,choice,*names,command=pick).pack(fill='x',padx=10,pady=6)
   pose.setdefault('tail',[0.]*9);specs=[(selected*3+i,label,-120,120,1) for i,label in enumerate(('上下弯曲（度）','左右弯曲（度）','扭转（度）'))]
  elif part in E.LIMBS:
   specs=[(i,label,-170,170,1) for i,label in enumerate(('抬起 / 放下','侧向弯曲','前伸 / 后摆','前后屈伸'))]
  elif part=='head':specs=[('head_pitch','低头 / 抬头',-65,65,1),('head_yaw','左右转头',-90,90,1),('head','左右歪头',-45,45,1)]
  else:specs=[('lean','后仰 / 弯腰（度）',-65,65,1),('chest_yaw','胸腔转向',-90,90,1),('pelvis_yaw','骨盆转向',-90,90,1),('dy','身体高低（px）',-12,12,.25),('dx','身体左右（px）',-12,12,.25)]
  self.pose_scales={};self.pose_values={}
  for key,label,lo,hi,step in specs:
   row=tk.Frame(self.params);row.pack(fill='x',padx=10,pady=(6,0));number=pose[part][key] if isinstance(key,int) else pose.get(key,0)
   UI.Label(row,text=label,font=self.owner.caption_font).pack(side='left')
   value=tk.StringVar(master=self,value=f'{number:g}');self.pose_values[key]=value
   UI.Label(row,textvariable=value,font=self.owner.caption_font).pack(side='right')
   scale=PixelScale(self.params,from_=lo,to=hi,resolution=step);scale.set(number);scale.pack(fill='x',padx=10)
   scale.configure(command=lambda v,k=key:self.set_pose(k,float(v)));self.pose_scales[key]=scale
 def mode_changed(self):self.refresh_cards();self.show_params();self.update_preview()
 def set_pose(self,key,value):
  pose=self.cards[self.card_index]['pose']
  if isinstance(key,int):pose[self.part][key]=value
  else:pose[key]=value
  self.pose_values[key].set(f'{value:g}')
  self.update_preview()
 def set_timing(self,key,value):self.cards[self.card_index][key]=value;self.refresh_cards();self.update_preview()
 def add_pose(self,pose):
  if len(self.cards)>=6:return
  self.cards.append(dict(pose=PA.capture_pose(pose),hold=.25,travel=1.,ease='smooth'));self.cards=PA.normalize_cards(self.cards);self.card_index=len(self.cards)-1;self.refresh_cards();self.show_params();self.update_preview()
 def add_preset(self):self.add_pose(E.norm(E.F.POSES[E.POSES[self.preset.get()]]))
 def capture_card(self):self.add_pose(self.capture_seq[int(self.capture_frame.get())-1])
 def duplicate_card(self):
  if len(self.cards)>=6:return
  self.cards.insert(self.card_index+1,copy.deepcopy(self.cards[self.card_index]));self.card_index+=1;self.refresh_cards();self.show_params();self.update_preview()
 def remove_card(self):
  if len(self.cards)<=2:return
  self.cards.pop(self.card_index);self.refresh_cards();self.show_params();self.update_preview()
 def move_card(self,delta):
  target=self.card_index+delta
  if 0<=target<len(self.cards):self.cards[self.card_index],self.cards[target]=self.cards[target],self.cards[self.card_index];self.card_index=target;self.refresh_cards();self.show_params();self.update_preview()
 def mirror_card(self):self.cards[self.card_index]['pose']=E.mirror_pose(self.cards[self.card_index]['pose']);self.show_params();self.update_preview()
 def load_card(self):
  path=filedialog.askopenfilename(parent=self,initialdir=E.ROOT/'examples'/'poses',filetypes=[(tr('姿势层'),'*.json')])
  if path:
   try:self.add_pose(MR.load_pose(path))
   except Exception as ex:messagebox.showerror(tr('无法打开'),str(ex),parent=self)
 def save_card(self):
  path=filedialog.asksaveasfilename(parent=self,initialfile='Pose.json',defaultextension='.json',filetypes=[(tr('姿势层'),'*.json')])
  if path:
   try:MR.save_pose(self.cards[self.card_index]['pose'],path)
   except Exception as ex:messagebox.showerror(tr('保存失败'),str(ex),parent=self)
 def update_preview(self):
  self.stop_job(self.play_job);self.play_job=None;self.playing=False;self.queued_play=False;self.edit_motion=False;self.frame=0;self.show_handles=True;self.play_button.configure(text='▶ 播放');self.request_preview()
 def preview_project(self):
  project=PA.build(self.original_project,self.cards,float(self.duration.get()),self.mode_choices[self.mode.get()],self.ground.get());self.source=copy.deepcopy(project)
  if not self.edit_motion:
   project.update(pose=copy.deepcopy(self.cards[self.card_index]['pose']),layers=[],controls={},physics={},seconds=1/project.get('fps',12))
   if self.ground.get():project['pose'].update(_ground=True,_feet_ground=True)
  return project
 def model_status(self):return tr('姿势卡修改仅在应用后写入项目')
 def draw(self):
  super().draw()
  if not self.edit_motion:self.time_text.set(f'{tr("姿势卡")} {self.card_index+1} / {len(self.cards)}')
 def toggle_play(self):
  if self.playing:super().toggle_play();return
  self.edit_motion=True;self.queued_play=True;self.show_handles=False;self.frame=0;self.request_preview()
 def receive_preview(self,seq,raw):
  super().receive_preview(seq,raw)
  if self.queued_play and len(seq)>1:self.queued_play=False;super().toggle_play()
 def seek(self,value):
  if not self.edit_motion:return
  super().seek(value)
 def pick(self,event):
  self.drag_pose=None
  for view,(x,y,size) in zip(self.cell_views,self.cells):
   if x<=event.x<x+size and y<=event.y<y+size:
    self.focus=view;self.draw()
    if self.playing or self.edit_motion or not self.seq or getattr(self,'accepted_revision',None)!=self.revision:return
    p=copy.deepcopy(self.seq[0]);p['yaw']+=VIEWS[view][0];p['pitch']+=VIEWS[view][1];j=E.R.joints(p)
    opts=[(math.hypot(x+j[k][joint][0]*size/64-event.x,y+j[k][joint][1]*size/64-event.y),k,joint) for k in E.LIMBS for joint in ('mid','tip')]
    distance,key,joint=min(opts)
    if distance<24:self.select(key);self.drag_pose=(view,key,joint,p,(x,y,size))
    return
 def move_pose(self,event):
  if not self.drag_pose:return
  view,key,joint,p,(x,y,size)=self.drag_pose;target=((event.x-x)*64/size,(event.y-y)*64/size)
  p[key]=self.cards[self.card_index]['pose'][key]
  self.cards[self.card_index]['pose'][key]=list(E.R.ik(p,key,target,joint=joint,free=(0,2) if joint=='mid' else (0,1,2,3)))
  self.update_preview()
 def end_pose(self,event):
  if self.drag_pose:self.drag_pose=None;self.show_params()
 def apply(self):
  try:project=PA.build(self.original_project,self.cards,float(self.duration.get()),self.mode_choices[self.mode.get()],self.ground.get())
  except Exception as ex:messagebox.showerror(tr('姿势动画'),tr(str(ex)),parent=self);return
  self.owner.snapshot();self.owner.stop();self.owner.project=project;self.owner.frame=0;self.owner.sync(('base',0));self.owner.changed();self.destroy()
 def destroy(self):
  other_model=self.owner.model_editor;self.owner.pose_editor=None
  super().destroy()
  self.owner.model_editor=other_model
