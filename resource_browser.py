"""Search, audition and combine resources before a single undoable Apply."""
import copy,math,tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox
import engine as E,model_data as MD,motion_resources as MR,resource_library as L
from model_editor import ModelEditor,BG,PANEL,FIELD,INK,ACC
from pixel_ui import PixelButton,PixelOption,PixelScale,PixelCheck,FlowBar
import localized_ui as UI
from i18n import tr

class ResourceBrowser(ModelEditor):
 def __init__(self,owner,target=None):
  self.target=target;self.caption_font=owner.caption_font;self.show_handles=False
  self.original_project=copy.deepcopy(target.preview_project() if target else owner.project)
  self.candidate=copy.deepcopy(self.original_project);self.resources=L.catalog(owner.state_path.parent/'models',owner.state_path.parent/'motions');self.filtered=[]
  self.chosen_model=tr('当前角色');self.chosen_motion=tr('当前动作');self.selected=None
  super().__init__(owner)
  if target:self.raw={};self.photos.clear()
  self.source=self.candidate;self.title(tr('创作资源库'));self.refresh_results();self.update_summary()
 def _build(self):
  footer=FlowBar(self,compact=True,bg=PANEL);footer.pack(side='bottom',fill='x',padx=12,pady=8)
  self.status=tk.StringVar(master=self,value=tr('选择资源后先预览，应用后才修改项目。'))
  UI.Label(footer,textvariable=self.status,font=self.caption_font,wrap=True).pack(side='left',fill='x',expand=True)
  PixelButton(footer,text='取消',command=self.cancel).pack(side='right',padx=4)
  self.apply_button=PixelButton(footer,text='应用搭配',command=self.apply,accent=True,state='disabled');self.apply_button.pack(side='right',padx=4)
  body=tk.PanedWindow(self,orient='horizontal',sashwidth=12,bg=BG,opaqueresize=False);body.pack(fill='both',expand=True,padx=12,pady=8)
  left=tk.Frame(body,bg=PANEL);body.add(left,width=round(400*self.ui_scale),minsize=300,stretch='never')
  bar=FlowBar(left,compact=True);bar.pack(fill='x',padx=8,pady=8)
  self.kind='models' if self.target else 'motions';self.tabs={}
  for key,name in (('motions','动作'),('models','角色')):
   if self.target and key!='models':continue
   b=PixelButton(bar,text=name,command=lambda key=key:self.change_kind(key),accent=key==self.kind);b.pack(side='left');self.tabs[key]=b
  UI.Label(left,text='搜索名称或关键词',font=self.caption_font,anchor='w').pack(fill='x',padx=12)
  self.query=tk.StringVar(master=self)
  entry=tk.Entry(left,textvariable=self.query,font=self.caption_font,bg=FIELD,fg=INK,insertbackground=INK,relief='flat');entry.pack(fill='x',padx=12,pady=6)
  self.query.trace_add('write',lambda *_:self.refresh_results())
  self.category=tk.StringVar(master=self,value='全部');self.category_shell=tk.Frame(left,bg=PANEL);self.category_shell.pack(fill='x',padx=12,pady=4);self.update_categories()
  self.count=tk.StringVar(master=self);UI.Label(left,textvariable=self.count,font=self.caption_font,anchor='w').pack(fill='x',padx=12,pady=4)
  listing=tk.Frame(left,bg=PANEL);listing.pack(fill='both',expand=True,padx=12)
  self.results=tk.Listbox(listing,font=self.caption_font,bg=FIELD,fg=INK,selectbackground=ACC,selectforeground=INK,bd=0,exportselection=False,activestyle='none')
  self.results.pack(side='left',fill='both',expand=True);self.results.bind('<<ListboxSelect>>',self.choose_result)
  scroll=tk.Scrollbar(listing,command=self.results.yview);scroll.pack(side='right',fill='y');self.results.configure(yscrollcommand=scroll.set)
  self.details=tk.StringVar(master=self,value=tr('点击条目，使用当前搭配预览。'))
  UI.Label(left,textvariable=self.details,font=self.caption_font,wrap=True,justify='left',anchor='w').pack(fill='x',padx=12,pady=8)
  bar=FlowBar(left,compact=True);bar.pack(fill='x',padx=8,pady=6)
  self.file_button=PixelButton(bar,text='载入文件…',command=self.load_file);self.file_button.pack(side='left')
  PixelButton(bar,text='还原本次选择',command=self.reset_selection).pack(side='left')
  center=tk.Frame(body,bg=BG);body.add(center,minsize=420,stretch='always')
  self.summary=tk.StringVar(master=self);UI.Label(center,textvariable=self.summary,font=self.caption_font,wrap=True,justify='left',anchor='w').pack(fill='x',pady=6)
  self.canvas=tk.Canvas(center,bg='#5a4d42',highlightthickness=0);self.canvas.pack(fill='both',expand=True)
  self.canvas.bind('<Configure>',self.resize);self.canvas.bind('<Button-1>',self.pick);self.canvas.bind('<Double-Button-1>',self.toggle_single_view)
  bar=FlowBar(center,compact=True);bar.pack(fill='x',pady=6)
  self.play_button=PixelButton(bar,text='▶ 播放',command=self.toggle_play,accent=True);self.play_button.pack(side='left')
  PixelCheck(bar,text='单视图',variable=self.single_view,command=self.draw).pack(side='left',padx=8)
  self.time_text=tk.StringVar(master=self);UI.Label(bar,textvariable=self.time_text,font=self.caption_font).pack(side='right')
  self.scrub=PixelScale(center,from_=0,to=1000,resolution=1,command=self.seek);self.scrub.pack(fill='x')
  UI.Label(center,text='动作保留已选角色，角色保留已选动作；应用后可继续编辑。',font=self.caption_font,wrap=True,justify='left').pack(fill='x',pady=8)
 def show_params(self):pass
 def preview_project(self):return copy.deepcopy(self.candidate)
 def request_preview(self):
  self.apply_button.configure(state='disabled');self.play_button.configure(state='disabled');super().request_preview()
 def receive_preview(self,seq,raw):
  super().receive_preview(seq,raw);self.play_button.configure(state='normal')
 def model_status(self):
  self.apply_button.configure(state='normal')
  return tr('预览就绪；应用可撤销。')
 def pick(self,event):
  for v,(x,y,size) in zip(self.cell_views,self.cells):
   if x<=event.x<x+size and y<=event.y<y+size:self.focus=v;self.draw();return
 def update_categories(self):
  for child in self.category_shell.winfo_children():child.destroy()
  values=['全部',*dict.fromkeys(r.category for r in self.resources if r.kind==self.kind)]
  PixelOption(self.category_shell,self.category,*values,command=lambda _:self.refresh_results()).pack(fill='x')
 def change_kind(self,kind):
  self.kind=kind;self.category.set('全部');self.update_categories()
  for key,b in self.tabs.items():b.accent=key==kind;b.draw()
  self.refresh_results()
 def refresh_results(self):
  if not hasattr(self,'results'):return
  self.filtered=L.search(self.resources,self.kind,self.query.get(),self.category.get());self.results.delete(0,'end')
  for i,r in enumerate(self.filtered):
   self.results.insert('end',r.title)
   if r==self.selected:self.results.selection_set(i)
  self.count.set(f'{len(self.filtered)} / {len([r for r in self.resources if r.kind==self.kind])}')
 def choose_result(self,event=None):
  selection=self.results.curselection()
  if selection:self.choose(self.filtered[selection[0]])
 def choose(self,resource):
  try:project=L.combine(self.candidate,resource)
  except Exception as ex:messagebox.showerror(tr('无法打开'),str(ex),parent=self);return
  self.selected=resource
  if resource.kind=='motions':self.chosen_motion=resource.title
  elif resource.kind=='models':self.chosen_model=resource.title
  self.details.set(resource.title+' · '+tr(resource.category)+'\n'+Path(resource.path).name)
  self.set_candidate(project)
 def set_candidate(self,project):
  self.stop_job(self.play_job);self.play_job=None;self.playing=False;self.play_button.configure(text='▶ 播放')
  self.candidate=project;self.source=project;self.frame=0;self.raw={};self.photos.clear();self.update_summary();self.request_preview();self.draw()
 def update_summary(self):
  self.summary.set(f'{tr("角色")} · {self.chosen_model}\n{tr("动作")} · {self.chosen_motion}   {self.candidate["seconds"]:g}s · {self.candidate["fps"]:g}fps')
 def reset_selection(self):
  self.chosen_model=tr('当前角色');self.chosen_motion=tr('当前动作');self.selected=None
  self.details.set(tr('点击条目，使用当前搭配预览。'));self.refresh_results();self.set_candidate(copy.deepcopy(self.original_project))
 def load_file(self):
  folder=self.owner.state_path.parent/self.kind
  path=filedialog.askopenfilename(parent=self,initialdir=folder if folder.is_dir() else E.ROOT/'examples'/self.kind,filetypes=[(tr('角色模型' if self.kind=='models' else '动作配方'),'*.json')])
  if not path:return
  try:
   project=L.apply_model(self.candidate,path) if self.kind=='models' else MR.apply_motion(self.candidate,E.load(path))
   # Reject invalid motions before replacing the last good candidate. Full
   # solve/render remains cancellable in the background preview worker.
   if not isinstance(project.get('base'),dict) or any(isinstance(project.get(k),bool) or not isinstance(project.get(k),(int,float)) or not math.isfinite(project[k]) or project[k]<=0 for k in ('fps','seconds')):raise ValueError(tr('无法打开'))
  except Exception as ex:messagebox.showerror(tr('无法打开'),str(ex),parent=self);return
  self.selected=None;self.details.set(str(path))
  if self.kind=='models':self.chosen_model=Path(path).stem
  else:self.chosen_motion=Path(path).stem
  self.set_candidate(project)
 def apply(self):
  # Do not commit a failed or still-running candidate, including direct calls.
  if self.apply_button.state=='disabled':return
  if self.candidate==self.original_project:self.cancel();return
  if self.target:
   import rounded_scene as S
   target=self.target;target.draft=MD.normalize(self.candidate.get('model'));target.draft_assets=S.assets(self.candidate);target.replace_assets=True
   target.face_mode=False;target.prop_mode=False
   for key in ('last_plush_body','structure_assets'):
    if hasattr(target,key):delattr(target,key)
   target.show_params();target.request_preview()
  else:
   self.owner.snapshot();self.owner.stop();self.owner.project=copy.deepcopy(self.candidate);self.owner.frame=0;self.owner.sync(('base',0));self.owner.changed()
  self.destroy()
 def destroy(self):
  saved=self.owner.model_editor;super().destroy();self.owner.model_editor=saved
  self.owner.resource_browser=None
  if self.target and self.target.winfo_exists():self.target.grab_set()

def show(owner,target=None):
 existing=getattr(owner,'resource_browser',None)
 if existing is not None and existing.winfo_exists():existing.lift();return existing
 owner.stop();owner.resource_browser=ResourceBrowser(owner,target)
 return owner.resource_browser

