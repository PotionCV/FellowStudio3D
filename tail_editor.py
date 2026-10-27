"""Tail controls on an independent model category."""
import tkinter as tk
import tails,attachments as A
import localized_ui as UI
from i18n import tr
from pixel_ui import PixelButton,PixelOption,PixelScale,FlowBar

def sync(editor):
 import rounded_scene as S
 editor.draft_assets=S.assets(editor.preview_project());editor.replace_assets=True

def add(editor,preset='long_tail'):
 if len(editor.draft.get('attachments',[]))>=32:return
 editor.tail_id=tails.add(editor.draft,preset);editor.model_category='tail';editor.hair_mode=False;editor.ear_mode=False;editor.prop_mode=False;sync(editor);editor.show_params();editor.request_preview()

def set_value(editor,key,value):
 item=A.record(editor.draft,editor.tail_id);item[key]=float(round(value)) if key=='cycles' else float(value)
 editor.request_preview()

def remove(editor):
 editor.draft['attachments']=[p for p in editor.draft.get('attachments',[]) if p['id']!=editor.tail_id]
 if not editor.draft['attachments']:editor.draft.pop('attachments')
 sync(editor);editor.show_params();editor.request_preview()

def mount(editor):
 box=tk.Frame(editor.params);box.pack(fill='x',padx=12,pady=10)
 UI.Label(box,text='尾巴',anchor='w').pack(fill='x',pady=6)
 bar=FlowBar(box,compact=True);bar.pack(fill='x')
 choices={tr(label):key for key,label in tails.LABELS.items()}
 choice=tk.StringVar(master=editor,value=tr('长尾'))
 PixelOption(bar,choice,*choices).pack(side='left',fill='x',expand=True)
 button=PixelButton(bar,text='添加尾巴',command=lambda:add(editor,choices[choice.get()]),compact=True)
 button.pack(side='left');button.configure(state='disabled' if len(editor.draft.get('attachments',[]))>=32 else 'normal')
 items=[p for p in editor.draft.get('attachments',[]) if p.get('kind')=='tail']
 if not items:
  UI.Label(box,text='选择尾巴形状后添加，再调整尺寸和位置。',wrap=True,anchor='w').pack(fill='x',pady=8);return
 if getattr(editor,'tail_id',None) not in [p['id'] for p in items]:editor.tail_id=items[0]['id']
 keys={A.name(item['id'],editor.draft):item['id'] for item in items}
 selected=tk.StringVar(master=editor,value=A.name(editor.tail_id,editor.draft))
 def choose(value):editor.tail_id=keys[value];editor.show_params()
 if len(items)>1:PixelOption(box,selected,*keys,command=choose).pack(fill='x',pady=6)
 UI.Label(box,text='动画与松软在主窗口的尾巴控制中调整。',wrap=True,anchor='w',justify='left',font=editor.owner.caption_font).pack(fill='x',pady=6)
 item=A.record(editor.draft,editor.tail_id);details=getattr(editor,'tail_details',False)
 UI.Label(box,text='当前部件',anchor='w').pack(fill='x',pady=(8,2))
 if len(items)==1:UI.Label(box,text=A.name(editor.tail_id,editor.draft),anchor='w').pack(fill='x',pady=4)
 shape=tk.StringVar(master=editor,value=tr(tails.LABELS[item['preset']]))
 def change_shape(label):
  preset=choices[label];item.update(preset=preset,shape=tails.PRESETS[preset]['shape']);sync(editor);editor.show_params();editor.request_preview()
 PixelOption(box,shape,*choices,command=change_shape).pack(fill='x',pady=4)
 specs=[spec for spec in tails.SPECS if spec[0] not in ('wag','cycles') and not (spec[0]=='tip' and item['shape']=='bob')]
 common=[s for s in specs if s[0] in ('length','width','thickness','curl','tip')];extra=[s for s in specs if s not in common]
 for key,label,lo,hi,step in common+(extra if details else []):
  row=tk.Frame(box);row.pack(fill='x',pady=(6,0));row.columnconfigure(0,weight=1)
  UI.Label(row,text=label,anchor='w',wrap=True).grid(row=0,column=0,sticky='ew')
  out=tk.StringVar(master=editor,value=f'{item[key]:g}');UI.Label(row,textvariable=out,width=5,anchor='e').grid(row=0,column=1)
  scale=PixelScale(box,from_=lo,to=hi,resolution=step);scale.set(item[key]);scale.pack(fill='x')
  def changed(value,k=key,text=out):text.set(f'{float(value):g}');set_value(editor,k,float(value))
  scale.configure(command=changed)
 def toggle():editor.tail_details=not details;editor.show_params()
 PixelButton(box,text='收起尾巴细节' if details else '尾巴位置与细节',command=toggle).pack(fill='x',pady=6)
 def reset():
  item.update(tails.normalize({'id':item['id'],'preset':item['preset']}));editor.show_params();editor.request_preview()
 bar=FlowBar(box,compact=True);bar.pack(fill='x',pady=6)
 PixelButton(bar,text='重置尾巴',command=reset,compact=True).pack(side='left')
 PixelButton(bar,text='删除尾巴',command=lambda:remove(editor),compact=True).pack(side='left')
