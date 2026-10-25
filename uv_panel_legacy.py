"""FellowStudio3D: body-first pixel animation and per-part UV painting."""
import copy,ctypes,json,math,time,tkinter as tk
from tkinter import font,filedialog,messagebox
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from PIL import Image,ImageTk,ImageDraw
import core3d as C
import uv_assets as U
import i18n
from i18n import tr
from pixel_ui import PixelButton,PixelCheck,PixelScale,PixelOption,PixelEntry,ScrollPanel
from localized_ui import Label
try:
 from tkinterdnd2 import TkinterDnD,DND_FILES
 Root=TkinterDnD.Tk
except ImportError:Root=tk.Tk
ROOT=Path(__file__).resolve().parent
BG='#ece4d8';PANEL='#f8f0df';INK='#493c32';CELL='#5a4d42';ACC='#e7a34c'
PART_NAMES=dict(zip(U.PARTS,('头部','躯干','左上臂','左前臂','右上臂','右前臂','左大腿','左小腿','右大腿','右小腿')))
MOTIONS={'站立':'idle','走路':'walk','跑步':'run','下蹲':'squat','跳跃':'jump'}
VN=('正面','侧面','斜面','斜俯')
BODY_LABELS=('肩宽','腰宽','胯宽','躯干高度','头部大小','头部间距','上臂长度','前臂长度','大腿长度','小腿长度','手臂粗细','腿部粗细','肩部间距')
PARAM_LABELS=dict(zip(('stride','swing','bounce','speed','raiseL','raiseR','mix','lean','nod','softUpper','softLower'),('步幅','摆臂','上下起伏','速度','左臂举起','右臂举起','姿势混合','身体前倾','低头 / 抬头','上臂跟随','前臂跟随')))
class App(Root):
 def __init__(self,state=None):
  super().__init__();self.state_path=Path(state or ROOT/'studio3d.json');self.settings=self.state_path.parent/'studio3d_settings.json'
  self.project=C.new_project();self.dirty=False;self.load_error='';self.links={};self.closed=False;self.jobs=set();self.pending=None;self.resize_job=None;self.play_job=None;self.frame=0;self.focus=0;self.tab='动画';self.raw={};self.joints=[];self.photos={};self.refs=[];self.cells=[];self.history=[];self.future=[];self.revision=0;self.worker=None;self.latest=None;self.pool=None;self.playing=False;self.drag=None;self.body_source=None
  try:pref=json.loads(self.settings.read_text(encoding='utf-8'))
  except (OSError,ValueError):pref={}
  self.ui_scale=max(.75,min(2,float(pref.get('scale',1))));self.language=pref.get('language','en');i18n.set_language(self.language)
  try:
   if self.state_path.exists():self.project=C.load(self.state_path)
  except Exception as ex:self.load_error=str(ex)
  self.title('FellowStudio3D');self.configure(bg=BG);self.minsize(1100,760)
  for f in ROOT.glob('Boutique*.ttf'):
   try:ctypes.windll.gdi32.AddFontResourceExW(str(f),0x10,0)
   except (OSError,AttributeError):pass
  self.ui_font=font.Font(family='精品点阵体9×9 1.9 R',size=-round(21*self.ui_scale));self.option_add('*Font',self.ui_font);self.option_add('*Background',PANEL);self.option_add('*Foreground',INK)
  w=min(self.winfo_screenwidth()-80,1600);h=min(self.winfo_screenheight()-100,1000);self.geometry(f'{w}x{h}+30+30')
  self.status=tk.StringVar(value=self.load_error or '就绪');self.bones=tk.BooleanVar(value=False);self.layout=tk.StringVar(value='四视图')
  self.build();self.protocol('WM_DELETE_WINDOW',self.close);self.bind('<Control-z>',lambda e:self.undo());self.bind('<Control-s>',lambda e:self.save_as());self.bind('<space>',lambda e:self.toggle_play() if not isinstance(self.focus_get(),tk.Entry) else None);self.bind('<MouseWheel>',self.wheel)
  self.request_preview()
 def later(self,ms,fn):
  holder=[]
  def run():
   self.jobs.discard(holder[0])
   if not self.closed:fn()
  holder.append(self.after(ms,run));self.jobs.add(holder[0]);return holder[0]
 def cancel_job(self,job):
  if job in self.jobs:self.after_cancel(job);self.jobs.discard(job)
 def button(self,parent,text,cmd,accent=False):return PixelButton(parent,text=text,command=cmd,accent=accent)
 def label(self,parent,text,**kw):return Label(parent,text=text,**kw)
 def build(self):
  top=tk.Frame(self,bg=PANEL);top.pack(fill='x',padx=10,pady=(10,4))
  self.label(top,'FellowStudio3D',fg=INK).pack(side='left',padx=8)
  for text,fn in (('新建',self.new),('打开',self.open),('保存',self.save_as),('撤销',self.undo),('A−',lambda:self.zoom(-.25)),('A＋',lambda:self.zoom(.25))):
   self.button(top,text,fn).pack(side='left',padx=3)
  lang=tk.StringVar(value=i18n.LANGUAGES.get(self.language,'English'));PixelOption(top,lang,*i18n.LANGUAGES.values(),command=self.change_language).pack(side='right',padx=4)
  self.button(top,'导出',self.export_dialog,True).pack(side='right',padx=4)
  tools=tk.Frame(self,bg=BG);tools.pack(fill='x',padx=10,pady=4)
  for key,label in (('colors','纹理 / 分色'),('outline','外边线'),('gaps','重叠分隔'),('onepx','1px')):
   var=tk.BooleanVar(value=self.project['render'][key]);PixelCheck(tools,text=label,variable=var,command=lambda k=key,v=var:self.render_setting(k,v.get()),bg=BG).pack(side='left',padx=3)
  PixelCheck(tools,text='骨骼',variable=self.bones,command=self.draw,bg=BG).pack(side='left')
  PixelOption(tools,self.layout,'四视图','焦点视图',command=lambda _:self.draw()).pack(side='right')
  footer=tk.Frame(self,bg=PANEL);footer.pack(side='bottom',fill='x',padx=10,pady=8)
  Label(footer,textvariable=self.status,wrap=True,anchor='w',justify='left').pack(fill='x',padx=8,pady=5)
  self.panes=tk.PanedWindow(self,orient='horizontal',sashwidth=14,opaqueresize=False,bg='#8d7257',bd=0);self.panes.pack(fill='both',expand=True,padx=10,pady=4)
  left=tk.Frame(self.panes,bg=BG);self.panes.add(left,minsize=460,stretch='always')
  self.canvas=tk.Canvas(left,bg=CELL,highlightthickness=0);self.canvas.pack(fill='both',expand=True);self.canvas.bind('<Configure>',self.resize);self.canvas.bind('<Button-1>',self.pick);self.canvas.bind('<B1-Motion>',self.move_ik);self.canvas.bind('<ButtonRelease-1>',self.end_ik)
  bar=tk.Frame(left,bg=BG);bar.pack(fill='x',pady=6);self.play_button=self.button(bar,'播放',self.toggle_play,True);self.play_button.pack(side='left');self.clock=tk.StringVar(value='0.00 s');Label(bar,textvariable=self.clock,bg=BG).pack(side='right')
  self.scrub=PixelScale(left,from_=0,to=1000,resolution=1,command=self.seek,bg=BG);self.scrub.pack(fill='x')
  right=tk.Frame(self.panes,bg=PANEL);self.panes.add(right,width=round(550*self.ui_scale),minsize=380,stretch='never')
  nav=tk.Frame(right);nav.pack(fill='x',padx=6,pady=6);nav.columnconfigure((0,1,2),weight=1,uniform='tabs')
  for i,key in enumerate(('动画','身体','贴图')):PixelButton(nav,text=key,command=lambda k=key:self.show_tab(k),accent=key==self.tab,compact=True).grid(row=0,column=i,sticky='ew',padx=3)
  self.scroll=ScrollPanel(right);self.scroll.pack(fill='both',expand=True);self.content=self.scroll.content;self.populate()
 def show_tab(self,key):
  self.tab=key
  for button in self.scroll.master.winfo_children()[0].winfo_children():button.accent=button.text==key;button.draw()
  self.populate()
 def populate(self):
  for w in self.content.winfo_children():w.destroy()
  self.card_photos=[]
  if self.tab=='动画':self.motion_controls()
  elif self.tab=='身体':self.body_controls()
  else:self.texture_controls()
  self.scroll.canvas.yview_moveto(0)
 def hint(self,text):self.label(self.content,text,wrap=True,anchor='w',justify='left',fg='#8a7967').pack(fill='x',padx=14,pady=10)
 def slider(self,parent,label,value,lo,hi,step,callback):
  row=tk.Frame(parent);row.pack(fill='x',padx=14,pady=(9,0));row.columnconfigure(0,weight=1)
  self.label(row,label,wrap=True,anchor='w').grid(row=0,column=0,sticky='ew');var=tk.StringVar(value=f'{value:g}');Label(row,textvariable=var,width=5,anchor='e').grid(row=0,column=1)
  scale=PixelScale(parent,from_=lo,to=hi,resolution=step);scale.set(value);scale.pack(fill='x',padx=14)
  def update(v):var.set(f'{float(v):g}');callback(float(v))
  scale.configure(command=update)
  def begin(event):self.snapshot();scale.move(event)
  def key_move(delta):self.snapshot();scale.user_set(scale.get()+delta)
  scale.bind('<Button-1>',begin);scale.bind('<Left>',lambda e:key_move(-step));scale.bind('<Right>',lambda e:key_move(step))
  return scale
 def motion_controls(self):
  motion=tk.StringVar(value=next(k for k,v in MOTIONS.items() if v==self.project['motion']));PixelOption(self.content,motion,*MOTIONS,command=self.change_motion).pack(fill='x',padx=14,pady=10)
  self.hint('基础动作始终保留，举臂改变姿势中心并保留摆臂。')
  for k in ('stride','swing','bounce','speed'):self.slider(self.content,PARAM_LABELS[k],self.project['params'][k],0 if k!='speed' else .25,2,.05,lambda v,key=k:self.set_param(key,v))
  for k in ('raiseL','raiseR'):self.slider(self.content,PARAM_LABELS[k],self.project['params'][k],0,150,2,lambda v,key=k:self.set_param(key,v))
  self.slider(self.content,'姿势混合',self.project['params']['mix'],0,1,.05,lambda v:self.set_param('mix',v))
  self.hint('头颈与躯干控制')
  for k in ('lean','nod'):self.slider(self.content,PARAM_LABELS[k],self.project['params'][k],-45,60,1,lambda v,key=k:self.set_param(key,v))
  self.hint('跟随效果');self.hint('父部位带动弹簧与惯性；上臂与前臂可分别设置。')
  for k in ('softUpper','softLower'):self.slider(self.content,PARAM_LABELS[k],self.project['params'][k],0,1,.05,lambda v,key=k:self.set_param(key,v))
  self.slider(self.content,'时长（秒）',self.project['seconds'],.5,4,.25,lambda v:self.set_timing('seconds',v))
  self.slider(self.content,'每秒帧数',self.project['fps'],6,30,1,lambda v:self.set_timing('fps',int(v)))
 def body_controls(self):
  self.hint('模型修改会保留各面图案，并按新尺寸重排 UV。')
  for key,label in zip(U.MODEL,BODY_LABELS):
   lo,hi=U.LIMITS[key];self.slider(self.content,label,self.project['model'][key],lo,hi,.05 if hi<=2 else .25,lambda v,k=key:self.set_model(k,v))
  self.button(self.content,'恢复基础形体',self.reset_body).pack(fill='x',padx=14,pady=12)
 def texture_controls(self):
  self.hint('拖入 PNG 或点击替换；图片尺寸需与模板相同。')
  tools=tk.Frame(self.content);tools.pack(fill='x',padx=12,pady=4);tools.columnconfigure((0,1),weight=1,uniform='uvtools')
  for col,(text,fn) in enumerate((('导出整套 UV',self.export_uv),('导入整套 UV',self.import_uv))):
   PixelButton(tools,text=text,command=fn,accent=col==0,compact=True).grid(row=0,column=col,sticky='ew',padx=3)
  self.button(self.content,'重载已替换贴图',self.reload_textures).pack(fill='x',padx=14,pady=4)
  self.hint('绘画 PNG 与参考线图分别导出。项目内嵌贴图，可独立保存。')
  self.cards=tk.Frame(self.content);self.cards.pack(fill='x',padx=8);self.cards.columnconfigure((0,1),weight=1,uniform='uvcards')
  for i,part in enumerate(U.parts(self.project)):self.texture_card(part,i)
  self.button(self.content,'恢复全部贴图',self.reset_textures).pack(fill='x',padx=14,pady=12)
 def texture_card(self,part,index):
  card=tk.Frame(self.cards,bg=INK,bd=0);card.grid(row=index//2,column=index%2,sticky='nsew',padx=5,pady=6);inside=tk.Frame(card,bg=PANEL);inside.pack(fill='both',expand=True,padx=4,pady=4)
  self.label(inside,U.part_name(part,self.project),anchor='w',wrap=True).pack(fill='x',padx=8,pady=4)
  middle=tk.Frame(inside);middle.pack(fill='x',padx=8)
  image=self.checker(U.texture_image(self.project,part),(112,80));photo=ImageTk.PhotoImage(image,master=self);self.card_photos.append(photo)
  thumb=tk.Label(middle,image=photo,bg='#cbbba4',cursor='hand2');thumb.pack(pady=3);thumb.bind('<Button-1>',lambda e:self.inspect_uv(part))
  w,h=self.project['textures'][part]['layout']['size'];self.label(middle,f'{w} × {h} px',wrap=True,justify='left',anchor='w').pack(fill='x')
  self.label(inside,self.project['textures'][part]['name'],wrap=True,anchor='w').pack(fill='x',padx=8)
  row=tk.Frame(inside);row.pack(fill='x',padx=5,pady=6);row.columnconfigure((0,1),weight=1,uniform='card')
  for i,(text,fn) in enumerate((('换图',lambda:self.replace_texture(part)),('恢复',lambda:self.reset_texture(part)))):
   PixelButton(row,text=text,command=fn,compact=True).grid(row=0,column=i,sticky='ew',padx=2)
  if hasattr(card,'drop_target_register'):
   for target in (card,inside,middle,thumb):
    target.drop_target_register(DND_FILES);target.dnd_bind('<<Drop>>',lambda event,p=part:self.drop_texture(p,event.data));target.dnd_bind('<<DropEnter>>',lambda e,c=card:self.drop_enter(c));target.dnd_bind('<<DropLeave>>',lambda e,c=card:c.configure(bg=INK))
 def drop_enter(self,card):card.configure(bg=ACC);return 'copy'
 def drop_texture(self,part,data):
  paths=self.tk.splitlist(data)
  if len(paths)!=1:self.error('选择一个 PNG 文件');return 'refuse_drop'
  self.replace_texture(part,paths[0]);return 'copy'
 def checker(self,source,size):
  w,h=size;bg=Image.new('RGBA',size);d=ImageDraw.Draw(bg)
  for y in range(0,h,8):
   for x in range(0,w,8):d.rectangle((x,y,x+7,y+7),fill='#cbbba4' if (x//8+y//8)%2 else '#e4d5bd')
  factor=max(1,min(w//source.width,h//source.height));im=source.resize((source.width*factor,source.height*factor),Image.Resampling.NEAREST)
  if im.width>w or im.height>h:im.thumbnail(size,Image.Resampling.NEAREST)
  bg.alpha_composite(im,((w-im.width)//2,(h-im.height)//2));return bg
 def replace_texture(self,part,path=None):
  path=path or filedialog.askopenfilename(parent=self,filetypes=[('PNG','*.png')])
  if not path:return
  try:
   candidate=copy.deepcopy(self.project);U.import_texture(candidate,part,path);self.snapshot();self.project=candidate;self.links[part]=str(path);self.changed();self.populate()
  except Exception as ex:self.error(str(ex))
 def reset_texture(self,part):
  self.snapshot();self.project['textures'][part].update(png=None,name='Default');self.links.pop(part,None);self.changed();self.populate()
 def reset_textures(self):
  self.snapshot();self.project['textures']=U.create_textures(self.project['model']);self.links={};self.changed();self.populate()
 def inspect_uv(self,part):
  dialog=tk.Toplevel(self);dialog.title(tr(U.part_name(part,self.project))+' · UV');dialog.transient(self);dialog.configure(bg=PANEL);dialog.geometry('760x700');dialog.minsize(500,400)
  preview=tk.Canvas(dialog,bg=CELL,highlightthickness=0);preview.pack(fill='both',expand=True,padx=10,pady=10);guide=tk.BooleanVar(master=dialog,value=False)
  def draw(event=None):
   if not dialog.winfo_exists():return
   source=U.template(part,self.project['textures'][part]['layout'],True) if guide.get() else U.texture_image(self.project,part)
   image=self.checker(source,(max(40,preview.winfo_width()),max(40,preview.winfo_height())));preview.photo=ImageTk.PhotoImage(image,master=self);preview.delete('all');preview.create_image(0,0,anchor='nw',image=preview.photo)
  PixelCheck(dialog,text='显示参考线',variable=guide,command=draw).pack(fill='x',padx=10)
  self.label(dialog,'F = front · R = right · B = back · L = left\nT = top · D = bottom',wrap=True).pack(fill='x',padx=10,pady=5)
  self.button(dialog,'关闭',dialog.destroy).pack(pady=8);preview.bind('<Configure>',draw)
 def export_uv(self):
  folder=filedialog.askdirectory(parent=self,title=tr('导出整套 UV'))
  if not folder:return
  try:U.export_pack(self.project,folder);self.status.set(str(folder))
  except Exception as ex:self.error(str(ex))
 def import_uv(self):
  folder=filedialog.askdirectory(parent=self,title=tr('导入整套 UV'))
  if not folder:return
  try:
   candidate=copy.deepcopy(self.project);U.import_pack(candidate,folder);self.snapshot();self.project=candidate;self.links={p:str(Path(folder)/f'{p}.png') for p in U.parts(candidate)};self.changed();self.populate()
  except Exception as ex:self.error(str(ex))
 def reload_textures(self):
  if not self.links:self.status.set('所有贴图使用默认资源');return
  try:
   candidate=copy.deepcopy(self.project)
   for part,path in self.links.items():U.import_texture(candidate,part,path)
   self.snapshot();self.project=candidate;self.changed();self.populate()
  except Exception as ex:self.error(str(ex))
 def set_model(self,key,value):
  self.project['model'][key]=value
  if self.body_source is not None:self.project['textures']=copy.deepcopy(self.body_source)
  U.repack(self.project);self.links={};self.changed()
 def reset_body(self):self.snapshot();self.project['model']=copy.deepcopy(U.MODEL);U.repack(self.project);self.links={};self.changed();self.populate()
 def set_param(self,key,value):self.project['params'][key]=value;self.project.pop('targets',None);self.changed()
 def set_timing(self,key,value):self.project[key]=value;self.changed()
 def render_setting(self,key,value):self.snapshot();self.project['render'][key]=value;self.changed()
 def change_motion(self,label):
  self.snapshot();self.project['motion']=MOTIONS[label];self.project['params']=C.new_project()['params'];self.project.pop('targets',None);self.frame=0;self.changed();self.populate()
 def snapshot(self):
  if self.tab=='身体':self.body_source=copy.deepcopy(self.project['textures'])
  if not self.history or self.history[-1]!=self.project:self.history.append(copy.deepcopy(self.project));self.history=self.history[-30:]
 def undo(self):
  if not self.history:return
  self.project=self.history.pop();self.links={};self.body_source=None;self.changed();self.populate()
 def changed(self):self.dirty=True;self.request_preview()
 def request_preview(self):
  self.revision+=1;self.cancel_job(self.pending);self.pending=self.later(140,self.submit)
 def submit(self):
  self.pending=None;self.latest=(self.revision,copy.deepcopy(self.project));self.start_latest()
 def start_latest(self):
  if self.worker or self.latest is None:return
  revision,p=self.latest;self.latest=None
  if self.pool is None:self.pool=ProcessPoolExecutor(max_workers=1)
  self.worker=(revision,self.pool.submit(C.compile_preview,p));self.status.set('正在更新预览，可继续操作');self.later(30,self.poll)
 def poll(self):
  if not self.worker:return
  version,future=self.worker
  if not future.done():self.later(30,self.poll);return
  self.worker=None
  try:
   frames,joints=future.result()
   if version==self.revision:self.raw=frames;self.joints=joints;self.photos.clear();self.frame%=len(joints);self.draw();self.status.set('预览已更新')
  except Exception as ex:self.status.set(str(ex))
  self.start_latest()
 def resize(self,event):self.cancel_job(self.resize_job);self.resize_job=self.later(100,self.draw)
 def draw(self):
  self.resize_job=None
  if not self.raw:return
  w,h=self.canvas.winfo_width(),self.canvas.winfo_height();four=self.layout.get()=='四视图';cols=2 if four else 1;rows=2 if four else 1;size=max(64,int(min(w/cols,h/rows)//64)*64);x=(w-cols*size)/2;y=(h-rows*size)/2
  self.canvas.delete('all');self.cells=[];self.refs=[]
  for pos,v in enumerate(range(4) if four else (self.focus,)):
   cx=x+pos%cols*size;cy=y+pos//cols*size;self.cells.append((v,cx,cy,size));key=(v,self.frame,size)
   if key not in self.photos:
    self.photos[key]=ImageTk.PhotoImage(Image.fromarray(self.raw[v,self.frame]).resize((size,size),Image.Resampling.NEAREST),master=self)
    while len(self.photos)>8 and sum(k[2]**2*4 for k in self.photos)>64*1024*1024:self.photos.pop(next(iter(self.photos)))
   self.refs.append(self.photos[key]);self.canvas.create_image(cx,cy,anchor='nw',image=self.photos[key]);self.canvas.create_rectangle(cx,cy,cx+size,cy+size,outline=ACC if v==self.focus else '#8a7967',width=3 if v==self.focus else 1)
   self.canvas.create_text(cx+10,cy+10,anchor='nw',text=tr(VN[v]),font=self.ui_font,fill=ACC if v==self.focus else '#d9cbb6')
   if self.bones.get() and self.joints:
    for key,chain in self.joints[self.frame].items():
     if not key.startswith(('arm','leg')):continue
     projected=C.project(np.array(chain),*C.VIEWS[v])
     for a,b in zip(projected,projected[1:]):self.canvas.create_line(cx+a[0]*size/64,cy+a[1]*size/64,cx+b[0]*size/64,cy+b[1]*size/64,fill='#ead59b',width=2)
     for a in projected:self.canvas.create_rectangle(cx+a[0]*size/64-3,cy+a[1]*size/64-3,cx+a[0]*size/64+3,cy+a[1]*size/64+3,fill=ACC,outline=INK)
  self.scrub.set(self.frame/max(1,len(self.joints)-1)*1000);self.clock.set(f'{self.frame/self.project["fps"]:.2f} / {self.project["seconds"]:g} s')
 def pick(self,event):
  if self.playing:return
  for v,x,y,size in self.cells:
   if x<=event.x<x+size and y<=event.y<y+size:
    self.focus=v
    if self.bones.get() and self.joints:
     candidates=[]
     for key,chain in self.joints[self.frame].items():
      if key.startswith(('arm','leg')):
       q=C.project(np.array([chain[-1]]),*C.VIEWS[v])[0];candidates.append((math.hypot(x+q[0]*size/64-event.x,y+q[1]*size/64-event.y),key,q[2]))
     distance,key,depth=min(candidates)
     if distance<18*self.ui_scale:self.snapshot();self.drag=(v,x,y,size,key,depth)
    self.draw();return
 def move_ik(self,event):
  if self.drag is None:return
  v,x,y,size,key,depth=self.drag;target=C.unproject(((event.x-x)*64/size,(event.y-y)*64/size,depth),*C.VIEWS[v])
  self.project.setdefault('targets',{})[key]=target.tolist();self.changed()
 def end_ik(self,event):self.drag=None
 def toggle_play(self):
  self.cancel_job(self.play_job);self.playing=not self.playing;self.play_button.configure(text='暂停' if self.playing else '播放')
  if self.playing:self.started=time.perf_counter()-self.frame/(self.project['fps']*max(.25,self.project['params']['speed']));self.tick()
  else:self.draw()
 def tick(self):
  if not self.playing:return
  if self.joints:
   frame=int((time.perf_counter()-self.started)*self.project['fps']*max(.25,self.project['params']['speed']))%len(self.joints)
   if frame!=self.frame:self.frame=frame;self.draw()
  self.play_job=self.later(25,self.tick)
 def seek(self,value):
  if self.playing:self.toggle_play()
  self.frame=min(max(0,len(self.joints)-1),int(float(value)/1000*len(self.joints)));self.draw()
 def wheel(self,event):
  node=self.winfo_containing(event.x_root,event.y_root)
  while node is not None:
   if isinstance(node,ScrollPanel):return node.wheel(event)
   node=getattr(node,'master',None)
 def rebuild_ui(self):
  if self.playing:self.toggle_play()
  self.cancel_job(self.resize_job)
  for w in self.winfo_children():w.destroy()
  self.ui_font.configure(size=-round(21*self.ui_scale));self.build();self.photos.clear();self.draw()
  self.settings.write_text(json.dumps(dict(scale=self.ui_scale,language=self.language)),encoding='utf-8')
 def zoom(self,amount):self.ui_scale=max(.75,min(2,self.ui_scale+amount));self.rebuild_ui()
 def change_language(self,label):self.language=next(k for k,v in i18n.LANGUAGES.items() if v==label);i18n.set_language(self.language);self.rebuild_ui()
 def error(self,text):messagebox.showerror(tr('操作失败'),tr(text),parent=self)
 def discard(self):return not self.dirty or messagebox.askyesno('FellowStudio3D',tr('关闭会丢弃未保存的修改吗？'),parent=self)
 def new(self):
  if not self.discard():return
  self.snapshot();self.project=C.new_project();self.links={};self.frame=0;self.changed();self.rebuild_ui()
 def open(self):
  if not self.discard():return
  path=filedialog.askopenfilename(parent=self,filetypes=[('FellowStudio3D','*.json')])
  if not path:return
  try:self.project=C.load(path);self.links={};self.history=[];self.frame=0;self.dirty=False;self.request_preview();self.rebuild_ui()
  except Exception as ex:self.error(str(ex))
 def save_as(self):
  path=filedialog.asksaveasfilename(parent=self,initialfile=self.project['name']+'.json',defaultextension='.json',filetypes=[('FellowStudio3D','*.json')])
  if not path:return
  try:C.save(self.project,path);C.save(self.project,self.state_path);self.dirty=False;self.status.set(str(path))
  except Exception as ex:self.error(str(ex))
 def export_dialog(self):
  if self.playing:self.toggle_play()
  d=tk.Toplevel(self);d.title(tr('导出'));d.transient(self);d.configure(bg=PANEL);d.geometry(f'{round(680*self.ui_scale)}x{min(self.winfo_screenheight()-100,round(780*self.ui_scale))}');d.minsize(540,480);d.grab_set()
  bottom=tk.Frame(d);bottom.pack(side='bottom',fill='x',padx=14,pady=10);panel=ScrollPanel(d);panel.pack(fill='both',expand=True,padx=10,pady=10);body=panel.content
  directory=tk.StringVar(master=d);name=tk.StringVar(master=d,value=self.project['name']);view=tk.StringVar(master=d,value=VN[self.focus]);folder=tk.BooleanVar(master=d,value=True);formats={k:tk.BooleanVar(master=d,value=k in ('png','strip')) for k in ('png','strip','gif','project')};error=tk.StringVar(master=d)
  self.button(body,'选择目录',lambda:directory.set(filedialog.askdirectory(parent=d) or directory.get())).pack(fill='x',padx=14,pady=8);PixelEntry(body,textvariable=directory).pack(fill='x',padx=14)
  self.label(body,'导出名称').pack(fill='x',padx=14,pady=(10,2));PixelEntry(body,textvariable=name).pack(fill='x',padx=14)
  PixelCheck(body,text='创建子文件夹',variable=folder).pack(fill='x',padx=14,pady=8);self.label(body,'输出视角').pack(fill='x',padx=14);PixelOption(body,view,*VN).pack(fill='x',padx=14)
  for key,label in zip(formats,('PNG 序列','PNG 条带','GIF 预览','项目 JSON')):PixelCheck(body,text=label,variable=formats[key]).pack(fill='x',padx=14,pady=5)
  Label(body,textvariable=error,wrap=True,fg='#a34d35').pack(fill='x',padx=14,pady=8)
  busy=[False]
  def submit():
   if busy[0]:return
   if not directory.get():error.set(tr('选择目录'));return
   if not any(v.get() for v in formats.values()):error.set('Choose an export format');return
   if self.pool is None:self.pool=ProcessPoolExecutor(max_workers=1)
   busy[0]=True;error.set(tr('正在更新预览，可继续操作'))
   future=self.pool.submit(C.export,copy.deepcopy(self.project),directory.get(),name.get().strip(),[k for k,v in formats.items() if v.get()],VN.index(view.get()),folder.get())
   def poll_export():
    if not future.done():self.later(50,poll_export);return
    busy[0]=False
    try:
     dest=future.result();self.status.set(str(dest))
     if d.winfo_exists():d.destroy()
    except Exception as ex:
     if d.winfo_exists():error.set(str(ex))
     else:self.status.set(str(ex))
   self.later(50,poll_export)
  self.button(bottom,'取消',d.destroy).pack(side='right');self.button(bottom,'开始导出',submit,True).pack(side='right',padx=8)
 def close(self):
  # Keep an automatic recovery project separate from explicit user saves.
  if self.dirty:
   try:C.save(self.project,self.state_path if not self.load_error else self.state_path.with_name('recovered3d.json'))
   except Exception as ex:self.error(str(ex));return
  self.closed=True;self.playing=False
  for job in list(self.jobs):self.cancel_job(job)
  if self.pool:self.pool.shutdown(wait=False,cancel_futures=True)
  self.destroy()

# Kept here to avoid importing numpy into pixel UI controls.
import numpy as np
if __name__=='__main__':
 import multiprocessing
 multiprocessing.freeze_support()
 try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
 except (OSError,AttributeError):pass
 App().mainloop()

