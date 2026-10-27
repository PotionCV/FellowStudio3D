"""FellowStudio3D keeps FellowStudio's interaction and tuned motion recipes."""
import copy,ctypes,multiprocessing,queue
from concurrent.futures import ProcessPoolExecutor
from preview_worker import init_progress,progressive_preview,frame_images,drain_progress
from pathlib import Path
import engine as E
import studio_ui as UI
import i18n,uv_i18n
from pixel_ui import PixelButton
try:
 from tkinterdnd2 import TkinterDnD
except ImportError:TkinterDnD=None
# Same source keys, with additional UV-only controls.
for key,value in uv_i18n.CATALOG.items():i18n.CATALOG.setdefault(key,value)
i18n.CATALOG.update({'UV 贴图':{'zh':'UV 贴图','en':'UV textures','ja':'UVテクスチャ'},'应用贴图':{'zh':'应用贴图','en':'Apply textures','ja':'画像を適用'}})
STATE=E.ROOT/'user_data'/'studio3d_motion.json'
class App(UI.App):
 def __init__(self,state=None,preferences=None):
  if state is None:
   from data_paths import workspace_paths
   state,default_preferences=workspace_paths();preferences=preferences or default_preferences
  self.texture_editor=None;self.dnd_available=False
  self.preview_control=multiprocessing.Value('q',0);self.preview_progress=multiprocessing.Queue()
  super().__init__(state=state,preferences=preferences)
  if TkinterDnD:
   try:TkinterDnD._require(self);self.dnd_available=True
   except RuntimeError:self.status.set('PNG drag/drop unavailable; use Swap instead.')
  self.title('FellowStudio3D')
  from platform_support import set_icon
  set_icon(self,E.ROOT)
  self.bind('<F1>',self.open_guide)
  from runtime_diagnostics import install
  self.watchdog=install(self)
 def _build(self):
  super()._build()
  model=next(w for shell in self.winfo_children() for w in shell.winfo_children() if isinstance(w,PixelButton) and w.text=='角色模型')
  self.button(model.master,'UV 贴图',self.edit_textures).pack(side='left',padx=4)
  self.button(model.master,'使用说明',self.open_guide).pack(side='left',padx=4)
 def open_guide(self,event=None):
  import webbrowser
  suffix={'en':'en','zh':'zh-CN','ja':'ja'}.get(i18n.language,'en')
  path=E.ROOT/'docs'/('GUIDE.'+suffix+'.html')
  if path.is_file():webbrowser.open(path.as_uri())
  else:self.status.set(str(path))
  return 'break'
 def make_project(self,kind='stand'):
  p=super().make_project(kind)
  if self.project.get('assets3d') is not None:p['assets3d']=copy.deepcopy(self.project['assets3d'])
  return p
 def edit_textures(self):
  if self.texture_editor is not None and self.texture_editor.winfo_exists():self.texture_editor.lift();return
  self.stop();self.render()
  from texture_editor import TextureEditor
  self.texture_editor=TextureEditor(self)
 def set_language(self,value):
  super().set_language(value);self.title('FellowStudio3D')
 def rebuild(self):
  import rounded_scene as S
  self.seq=E.authored(self.project);bundle=S.assets(self.project)
  self.seq=E.visible(self.seq,self.project,bundle)
  self.frame%=len(self.seq);self.raw_images=frame_images(self.seq,self.project['render'],self.frame)
  self.active_project=copy.deepcopy(self.project);self.preview_incomplete=True
  self.photos.clear();self.layout_key=None;self.render();self.revision+=1
  self.pending=self.after_idle(self.request_preview)
 def changed(self):
  super().changed();self.preview_control.value=self.revision
 def update_drag_preview(self):
  import rounded_scene as S
  if self.pending:self.after_cancel(self.pending);self.pending=None
  self.revision+=1;self.preview_control.value=self.revision;self.latest_request=None
  self.seq=E.authored(self.project);bundle=S.assets(self.project)
  self.seq=E.visible(self.seq,self.project,bundle)
  self.active_project=copy.deepcopy(self.project);self.preview_incomplete=True
  self.raw_images=frame_images(self.seq,self.project['render'],self.frame)
  self.photos.clear();self.layout_key=None;self.render()
 def submit_latest(self):
  if self.future_job is not None or self.latest_request is None:return
  revision,project=self.latest_request;self.latest_request=None;self.preview_control.value=revision
  if self.executor is None:self.executor=ProcessPoolExecutor(max_workers=1,initializer=init_progress,initargs=(self.preview_control,self.preview_progress))
  self.future_job=(revision,project,self.executor.submit(progressive_preview,project,revision,self.frame));self.after(15,self.poll_preview)
 def accept_preview(self,seq,images,project,complete=False):
  same=getattr(self,'accepted_revision',None)==self.revision
  redraw=not same or complete or any(index==self.frame for view,index in images)
  if same:
   self.raw_images.update(images)
   touched=set(images);self.photos={k:v for k,v in self.photos.items() if (k[0],k[1]) not in touched}
  else:
   self.accepted_revision=self.revision;self.raw_images=dict(images);self.photos.clear()
  self.seq=seq;self.active_project=project;self.preview_incomplete=not complete;self.frame%=len(seq)
  if redraw:self.layout_key=None;self.render()
  if complete:self.status.set('动作已更新 · 点击视图切换焦点，导出默认跟随焦点')
  else:self.status.set('正在更新动作… 可继续调整')
 def poll_preview(self):
  if self.future_job is None:return
  revision,project,future=self.future_job
  partial,merged=drain_progress(self.preview_progress,self.revision)
  if partial is not None:self.accept_preview(partial,merged,project)
  if not future.done():self.after(15,self.poll_preview);return
  self.future_job=None
  try:
   result=future.result()
   if result is not None and revision==self.revision:self.accept_preview(*result,project,complete=True)
  except Exception as ex:self.status.set('预览更新失败：'+str(ex))
  self.submit_latest()
 def close(self):
  if getattr(self,'watchdog',None):self.watchdog.close()
  self.preview_control.value=-1
  super().close()
if __name__=='__main__':
 multiprocessing.freeze_support()
 try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
 except (AttributeError,OSError):pass
 App().mainloop()
