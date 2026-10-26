"""Structure choice and a compact replacement for head/torso shape panels."""
import tkinter as tk
import copy
import plush
import localized_ui as UI
from pixel_ui import PixelOption,PixelScale,PixelCheck,PixelButton
from i18n import tr

def structure_control(editor,parent):
 UI.Label(parent,text='身体结构',anchor='w').pack(fill='x',padx=12,pady=(8,2))
 editor.structure_var=tk.StringVar(master=editor,value=tr('一体布偶' if plush.active(editor.draft) else '分体人形'))
 choices={tr('分体人形'):'humanoid',tr('一体布偶'):'plush'}
 PixelOption(parent,editor.structure_var,*choices,command=lambda v:change(editor,choices[v])).pack(fill='x',padx=12,pady=6)

def refresh(editor):
 active=plush.active(editor.draft)
 if hasattr(editor,'structure_var'):editor.structure_var.set(tr('一体布偶' if active else '分体人形'))
 for key,button in editor.part_buttons.items():
  if key=='head':
   if active:button.grid_remove()
   else:button.grid()
  if key=='torso':button.configure(text='主体' if active else '腰 / 躯干');button.grid_configure(columnspan=2 if active else 1)

def change(editor,value):
 current='plush' if plush.active(editor.draft) else 'humanoid'
 if value==current:return
 import rounded_scene as S
 cache=getattr(editor,'structure_assets',{})
 cache[current]=S.assets(editor.preview_project());editor.structure_assets=cache
 if value=='plush':editor.draft.update(structure='plush',body=copy.deepcopy(getattr(editor,'last_plush_body',plush.DEFAULT)))
 else:
  editor.last_plush_body=copy.deepcopy(editor.draft['body']);editor.draft.pop('structure',None);editor.draft.pop('body',None)
 if value in cache:editor.draft_assets=copy.deepcopy(cache[value])
 editor.draft_assets=S.assets(editor.preview_project());editor.replace_assets=True
 editor.part='torso';refresh(editor);editor.show_params();editor.request_preview()

def panel(editor):
 box=editor.params;body=editor.draft['body']
 UI.Label(box,text='主体',anchor='w').pack(fill='x',padx=12,pady=8)
 UI.Label(box,text='头身使用连续外形和一张贴图。四肢与耳朵保持独立。',wrap=True,anchor='w',justify='left').pack(fill='x',padx=12,pady=6)
 specs=list(plush.SPECS)
 for key,label,lo,hi,step in specs:
  row=tk.Frame(box);row.pack(fill='x',padx=12,pady=(8,0));row.columnconfigure(0,weight=1)
  UI.Label(row,text=label,anchor='w',wrap=True).grid(row=0,column=0,sticky='ew')
  out=tk.StringVar(master=editor,value=f'{body[key]:g}');UI.Label(row,textvariable=out,width=5,anchor='e').grid(row=0,column=1)
  scale=PixelScale(box,from_=lo,to=hi,resolution=step);scale.set(body[key]);scale.pack(fill='x',padx=12)
  def changed(v,k=key,text=out):text.set(f'{float(v):g}');editor.draft['body'][k]=float(v);editor.request_preview()
  scale.configure(command=changed)
 linked=tk.BooleanVar(master=editor,value=body['head_link'])
 def link():body['head_link']=linked.get();editor.show_params();editor.request_preview()
 PixelCheck(box,text='头身一起动',variable=linked,command=link).pack(fill='x',padx=12,pady=10)
 if not body['head_link']:
  UI.Label(box,text='上部柔和转动',anchor='w').pack(fill='x',padx=12)
  control=PixelScale(box,from_=0,to=1,resolution=.05);control.set(body['flex']);control.pack(fill='x',padx=12)
  def flex(v):body['flex']=float(v);editor.request_preview()
  control.configure(command=flex)
 import tail_editor
 tail_editor.mount(editor)
 def reset():editor.draft['body']=dict(plush.DEFAULT);editor.show_params();editor.request_preview()
 PixelButton(box,text='重置这个部位',command=reset).pack(fill='x',padx=12,pady=10)
