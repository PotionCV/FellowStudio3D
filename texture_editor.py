"""Texture workspace attached to the established model/animation editor."""
import copy,os,tkinter as tk
from pathlib import Path
from tkinter import messagebox,filedialog
import model_editor as M, rounded_scene as S
import uv_assets as U
from uv_panel_legacy import App as Cards
from pixel_ui import PixelButton,PixelCheck,FlowBar
from localized_ui import Label
from i18n import tr
class TextureEditor(M.ModelEditor):
 def __init__(self,owner):
  self.project=S.assets(owner.project);self.links={};self.link_stamps={};self.link_pending={};self.link_attempts={};self.uv_history=[];self.show_handles=False;self.workspace=None;self.match_vars={};self.match_states={};self.caption_font=owner.caption_font
  super().__init__(owner);self.title(tr('UV 贴图'));self.status.set('绘画 PNG 与参考线图分别导出。项目内嵌贴图，可独立保存。')
  self.later(500,self.watch_painting)
 def _build(self):
  super()._build();top,footer=self.winfo_children()[:2]
  for child in top.winfo_children():child.destroy()
  Label(top,text='UV 贴图',anchor='w',font=self.ui_font).pack(side='left',padx=10,pady=8)
  self.comparison_button(top).pack(side='left',padx=4)
  PixelButton(top,text='撤销',command=self.undo_texture).pack(side='right',padx=10)
  for child in footer.winfo_children():
   if isinstance(child,PixelButton) and child.text=='应用模型':child.configure(text='应用贴图')
  for child in self.scroll.content.winfo_children():child.destroy()
  self.content=self.scroll.content
  self.advanced=tk.BooleanVar(master=self,value=False);self.auto_reload=tk.BooleanVar(master=self,value=True);self.paint_message=tk.StringVar(master=self,value=self.painting_hint())
  self.scroll.master.master.paneconfigure(self.scroll.master,width=round(550*self.ui_scale))
 def show_params(self):self.populate()
 def populate(self):
  position=self.scroll.canvas.yview()[0]
  for child in self.content.winfo_children():child.destroy()
  self.card_photos=[];self.texture_controls();self.scroll.canvas.yview_moveto(position)
 def pick(self,event):
  for v,(x,y,size) in zip(self.cell_views,self.cells):
   if x<=event.x<x+size and y<=event.y<y+size:self.focus=v;self.draw();return
 def submit(self):
  self.pending=None;project=copy.deepcopy(self.source);project['assets3d']=copy.deepcopy(self.project);self.latest=(self.revision,project);self.start_latest()
 def snapshot(self):self.uv_history.append(copy.deepcopy(self.project))
 def undo_texture(self):
  if self.uv_history:self.project=self.uv_history.pop();self.changed();self.populate()
 def changed(self):U.apply_shared(self.project);self.request_preview()
 def reset_textures(self):self.snapshot();self.project=S.assets({'model':self.source.get('model')});self.links={};self.workspace=None;self.paint_message.set('选择绘画文件夹，保存 PNG 后自动更新。');self.changed();self.populate()
 def apply(self):
  self.owner.snapshot();self.owner.project['assets3d']=copy.deepcopy(self.project)
  if self.workspace:self.remember_painting()
  self.owner.changed();self.destroy()
 def destroy(self):
  super().destroy();self.owner.texture_editor=None
 def label(self,parent,text,**kw):return Label(parent,text=text,**kw)
 def hint(self,text):self.label(self.content,text,wrap=True,anchor='w',justify='left',fg='#8a7967').pack(fill='x',padx=14,pady=10)
 def error(self,text):messagebox.showerror(tr('操作失败'),tr(text),parent=self)
 def last_painting_folder(self):
  from paint_workspace import painting_key
  saved=self.owner.paint_bindings.get(painting_key(self.source))
  folder=Path(saved) if saved else None
  return folder if folder is not None and (folder/'UV_Model.json').is_file() else None
 def remember_painting(self):
  from paint_workspace import painting_key
  folder=str(self.workspace.folder.resolve());self.owner.paint_directory=folder
  # Keep the pre-edit artwork reconnectable after Cancel, and the applied
  # artwork reconnectable after Save/reopen. Both were explicitly connected.
  for project in (self.source,dict(self.source,assets3d=self.project)):
   key=painting_key(project);self.owner.paint_bindings.pop(key,None);self.owner.paint_bindings[key]=folder
  while len(self.owner.paint_bindings)>32:self.owner.paint_bindings.pop(next(iter(self.owner.paint_bindings)))
  self.owner.save_preferences()
 def painting_hint(self):
  folder=self.last_painting_folder()
  return tr('上次绘画文件夹：')+'\n'+str(folder) if folder else tr('选择绘画文件夹，保存 PNG 后自动更新。')
 def texture_controls(self):
  pending=any(r.get('painting_pending') for r in self.project['textures'].values())
  if pending:self.hint('新贴图尚未连接绘画文件；开始绘画会创建项目副本，旧文件保留。')
  bar=FlowBar(self.content,compact=True,bg=self.cget('bg'));bar.pack(fill='x',padx=12,pady=6)
  PixelButton(bar,text='为新贴图准备绘画' if pending else '打开绘画文件夹' if self.workspace else '继续上次绘制' if self.last_painting_folder() else '开始 / 继续绘制',command=self.open_painting_folder if self.workspace and not pending else self.start_painting,accent=True).pack(side='left')
  PixelButton(bar,text='重新读取',command=self.reload_textures).pack(side='left')
  PixelCheck(bar,text='自动刷新',variable=self.auto_reload).pack(side='left')
  Label(self.content,textvariable=self.paint_message,wrap=True,anchor='w',justify='left').pack(fill='x',padx=14,pady=8)
  if self.workspace and any(not self.workspace.compatible(self.project,p) for p in U.parts(self.project)):PixelButton(self.content,text='适配到新绘画文件夹',command=self.adapt_painting).pack(fill='x',padx=14,pady=4)
  PixelCheck(self.content,text='高级贴图操作',variable=self.advanced,command=self.populate).pack(fill='x',padx=14,pady=6)
  if self.advanced.get():
   PixelButton(self.content,text='切换绘画文件夹',command=lambda:self.start_painting(reuse_last=False)).pack(fill='x',padx=14,pady=3)
   for label,fn in (('导出整套 UV',self.export_uv),('导入整套 UV',self.import_uv),('恢复全部贴图',self.reset_textures)):
    PixelButton(self.content,text=label,command=fn).pack(fill='x',padx=14,pady=3)
  self.cards=tk.Frame(self.content);self.cards.pack(fill='x',padx=8);self.cards.columnconfigure((0,1),weight=1,uniform='uvcards')
  self.match_vars={}
  for index,part in enumerate(U.parts(self.project)):self.texture_card(part,index)
 def texture_card(self,part,index):
  Cards.texture_card(self,part,index)
  card=self.cards.grid_slaves(row=index//2,column=index%2)[0].winfo_children()[0]
  if self.advanced.get():PixelButton(card,text='像素保护',command=lambda:self.inspect_uv(part),compact=True).pack(fill='x',padx=8,pady=(0,6))
  counterpart=part[:-1]+('R' if part.endswith('L') else 'L')
  if part.endswith(('L','R')) and counterpart in self.project['textures']:
   if self.advanced.get():PixelButton(card,text='复制另一侧',command=lambda:self.copy_other_side(part),compact=True).pack(fill='x',padx=8,pady=(0,6))
  if part.endswith('R') and counterpart in self.project['textures']:
   shared=tk.BooleanVar(master=self,value=part in self.project.get('shared_textures',{}))
   PixelCheck(card,text='共用左侧贴图',variable=shared,command=lambda p=part,v=shared:self.set_shared(p,v.get())).pack(fill='x',padx=8,pady=4)
  value=tk.StringVar(master=self);self.match_vars[part]=value
  Label(card,textvariable=value,wrap=True,anchor='w',justify='left').pack(fill='x',padx=8,pady=5)
  self.update_match_labels()
 def copy_other_side(self,part):
  import uv_assets as U
  from pixel_protection import resize_groups
  other=part[:-1]+('R' if part.endswith('L') else 'L');source=self.project['textures'][other];target=self.project['textures'][part]
  self.snapshot()
  self.project.get('shared_textures',{}).pop(part,None)
  if source['layout']==target['layout']:
   target.update(png=source.get('png') or U.encode(U.texture_image(self.project,other)),name=source.get('name','Default'),protected_groups=copy.deepcopy(source.get('protected_groups',[])))
  else:
   from PIL import Image
   image=U.texture_image(self.project,other)
   result=Image.new('RGBA',target['layout']['size'])
   for face,(x,y,w,h) in target['layout']['rects'].items():
    ox,oy,ow,oh=source['layout']['rects'][face];result.paste(image.crop((ox,oy,ox+ow,oy+oh)).resize((w,h),Image.Resampling.NEAREST),(x,y))
   target.update(png=U.encode(result),name=source.get('name','Default'),protected_groups=resize_groups(source,target['layout']))
  self.links.pop(part,None);self.changed();self.populate()
 def set_shared(self,part,enabled):
  import uv_assets as U
  self.snapshot();links=self.project.setdefault('shared_textures',{})
  if enabled:links[part]=part[:-1]+'L'
  else:links.pop(part,None)
  U.apply_shared(self.project);self.changed();self.populate()
 checker=Cards.checker
 drop_enter=Cards.drop_enter
 drop_texture=Cards.drop_texture
 def replace_texture(self,part,path=None):
  import uv_assets as U
  if part in self.project.get('shared_textures',{}):self.error('请先关闭共用左侧贴图，再独立绘制右侧。');return
  path=path or filedialog.askopenfilename(parent=self,filetypes=[('PNG','*.png')])
  if not path:return
  try:
   candidate=copy.deepcopy(self.project);U.import_texture(candidate,part,path);self.snapshot();self.project=U.apply_shared(candidate)
   if self.workspace and Path(path).resolve()==(self.workspace.folder/f'{part}.png').resolve():self.links.pop(part,None);self.workspace.seen[part]=self.file_stamp(path)
   else:self.links[part]=str(path);self.link_stamps[part]=self.file_stamp(path)
   self.match_states.pop(part,None);self.changed();self.populate()
  except Exception as ex:self.error(str(ex))
 def reset_texture(self,part):
  part=self.project.get('shared_textures',{}).get(part,part)
  Cards.reset_texture(self,part);self.project['textures'][part].pop('protected_groups',None)
 def inspect_uv(self,part):
  from protection_editor import ProtectionEditor
  part=self.project.get('shared_textures',{}).get(part,part)
  return ProtectionEditor(self,part)
 export_uv=Cards.export_uv
 def import_uv(self):
  from paint_workspace import PaintWorkspace
  folder=filedialog.askdirectory(parent=self,title=tr('导入整套 UV'))
  if not folder:return
  try:
   candidate=copy.deepcopy(self.project);U.import_pack(candidate,folder);self.snapshot();self.project=candidate;self.links={};self.workspace=PaintWorkspace(folder);self.remember_painting();self.changed();self.populate();self.update_paint_message()
  except Exception as ex:self.error(str(ex))
 def start_painting(self,folder=None,*,reuse_last=True):
  from paint_workspace import prepare,PaintWorkspace
  interactive=folder is None
  if folder is None and reuse_last:folder=self.last_painting_folder()
  folder=folder or filedialog.askdirectory(parent=self,title=tr('选择绘画文件夹'),initialdir=self.owner.paint_directory or self.owner.state_path.parent)
  if not folder:return
  try:
   if any(r.get('painting_pending') for r in self.project['textures'].values()):
    from paint_workspace import project_copy
    workspace=project_copy(self.project,folder);folder=workspace.folder;self.snapshot()
    for resource in self.project['textures'].values():resource.pop('painting_pending',None);resource.pop('painting_override',None)
   else:workspace=PaintWorkspace(folder) if (Path(folder)/'UV_Model.json').exists() else prepare(self.project,folder)
   self.workspace=workspace;self.links={};self.remember_painting()
   self.reload_textures();self.populate()
   if interactive:self.open_painting_folder()
  except Exception as ex:self.error(str(ex))
 def open_painting_folder(self):
  if not self.workspace:return
  try:os.startfile(str(self.workspace.folder))
  except (AttributeError,OSError) as ex:self.error(str(ex))
 def adapt_painting(self):
  if not self.workspace:return
  from paint_workspace import adapted_folder
  try:
   self.workspace=adapted_folder(self.project,self.workspace.folder,skip=self.links);self.links={};self.remember_painting();self.match_states={};self.reload_textures();self.update_paint_message();self.populate()
  except Exception as ex:self.error(str(ex))
 def reload_textures(self):
  if not self.workspace:return Cards.reload_textures(self)
  result=self.workspace.poll(self.project,force=True,skip=self.links);self.match_states=dict(self.workspace.states)
  if result is not None:self.snapshot();self.project=result;self.changed();self.populate()
  if self.links:self.watch_linked_files(force=True)
  self.update_paint_message();self.update_match_labels()
 def watch_painting(self):
  if self.workspace and self.auto_reload.get():
   result=self.workspace.poll(self.project,skip=self.links);self.match_states=dict(self.workspace.states)
   if result is not None:self.snapshot();self.project=result;self.changed();self.populate()
   self.update_paint_message();self.update_match_labels()
  if self.links and self.auto_reload.get():self.watch_linked_files()
  self.later(500,self.watch_painting)
 @staticmethod
 def file_stamp(path):
  try:
   value=Path(path).stat();return value.st_mtime_ns,value.st_size
  except OSError:return None
 def watch_linked_files(self,force=False):
  candidate=copy.deepcopy(self.project);changed=False
  for part,path in self.links.items():
   if self.project['textures'][part].get('painting_override'):continue
   if part in self.project.get('shared_textures',{}):continue
   stamp=self.file_stamp(path)
   if stamp is None:self.match_states[part]='missing';continue
   if stamp==self.link_stamps.get(part) and not force:continue
   if stamp!=self.link_pending.get(part) and not force:
    self.link_pending[part]=stamp;self.link_attempts[part]=0;self.match_states[part]='waiting';continue
   if self.link_attempts.get(part,0)>=3 and not force:self.match_states[part]='invalid';continue
   try:U.import_texture(candidate,part,path)
   except Exception:
    self.link_attempts[part]=self.link_attempts.get(part,0)+1;self.match_states[part]='invalid';continue
   self.link_stamps[part]=stamp;self.link_pending.pop(part,None);self.link_attempts.pop(part,None);self.match_states[part]='updated';changed=True
  if changed:self.snapshot();self.project=U.apply_shared(candidate);self.changed();self.populate()
  self.update_match_labels()
 def update_paint_message(self):
  if not self.workspace:return
  message=str(self.workspace.folder)
  if 'mapping' in self.match_states.values():message=tr('外形已改变；旧绘画文件不再匹配，请生成适配副本。')+'\n'+str(self.workspace.folder)
  if self.paint_message.get()!=message:self.paint_message.set(message)
 def model_status(self):return '贴图修改仅在应用后写入当前项目'
 def update_match_labels(self):
  labels={'embedded':'已内嵌贴图','shared':'共用左侧贴图','external':'使用单独绘画文件','ready':'绘画文件已连接','updated':'贴图已更新','waiting':'等待文件保存完成','missing':'绘画文件缺失','invalid':'文件暂不可读，保留上次贴图','mapping':'需要更新绘画模板','matched':'匹配当前布局','unknown':'尺寸符合，来源未知','adapted':'贴图已适配，请检查细节'}
  for part,var in self.match_vars.items():
   resource=self.project['textures'][part]
   state='shared' if part in self.project.get('shared_textures',{}) else self.match_states.get(part,resource.get('provenance',''))
   if state=='external':state=resource.get('provenance','unknown')
   if state=='ready' and resource.get('provenance')=='unknown':state='unknown'
   text=labels.get(state,'已内嵌贴图' if resource.get('png') else '内置贴图')
   if var.get()!=text:var.set(text)
