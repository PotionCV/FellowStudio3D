"""Compact ear controls inside the model editor's head section."""
import tkinter as tk
import attachments as A
import localized_ui as UI
from pixel_ui import PixelButton,PixelOption,PixelCheck,PixelScale,FlowBar
from i18n import tr

def mount(editor):
 box=tk.Frame(editor.params);box.pack(fill='x',padx=12,pady=10)
 UI.Label(box,text='耳朵',anchor='w').pack(fill='x',pady=6)
 bar=FlowBar(box,compact=True);bar.pack(fill='x')
 for preset,label in A.LABELS.items():
  PixelButton(bar,text='+ '+tr(label),compact=True,command=lambda p=preset:add(editor,p)).pack(side='left')
 items=[p for p in editor.draft.get('attachments',[]) if p.get('kind','ear')=='ear']
 if not items:return
 keys={A.name(item['id'],editor.draft):item['id'] for item in items}
 selected=getattr(editor,'attachment_id',None)
 if selected not in keys.values():selected=items[0]['id']
 editor.attachment_id=selected
 value=tk.StringVar(master=editor,value=A.name(selected,editor.draft))
 def choose(label):editor.attachment_id=keys[label];editor.show_params()
 PixelOption(box,value,*keys,command=choose).pack(fill='x',pady=6)
 item=A.record(editor.draft,selected);other=selected[:-1]+('R' if selected.endswith('L') else 'L')
 linked=tk.BooleanVar(master=editor,value=item['linked'])
 if any(p['id']==other for p in items):
  PixelCheck(box,text='左右联动',variable=linked,command=lambda:set_link(editor,linked.get())).pack(fill='x',pady=4)
 details=getattr(editor,'attachment_details',False)
 def toggle():editor.attachment_details=not details;editor.show_params()
 PixelButton(box,text='收起耳朵参数' if details else '编辑耳朵参数',command=toggle).pack(fill='x',pady=4)
 if details:
  UI.Label(box,text='位置按头部比例；尺寸按原始像素。耳朵固定跟随头部。',wrap=True,anchor='w',justify='left').pack(fill='x',pady=6)
  for key,label,lo,hi,step in A.SPECS:
   row=tk.Frame(box);row.pack(fill='x',pady=(6,0));row.columnconfigure(0,weight=1)
   UI.Label(row,text=label,wrap=True,anchor='w').grid(row=0,column=0,sticky='ew')
   out=tk.StringVar(master=editor,value=f'{item[key]:g}')
   UI.Label(row,textvariable=out,width=5,anchor='e').grid(row=0,column=1)
   scale=PixelScale(box,from_=lo,to=hi,resolution=step);scale.set(item[key]);scale.pack(fill='x')
   def changed(v,k=key,text=out):text.set(f'{float(v):g}');set_value(editor,k,float(v))
   scale.configure(command=changed)
 bar=FlowBar(box,compact=True);bar.pack(fill='x',pady=6)
 PixelButton(bar,text='删除这一只',compact=True,command=lambda:remove(editor,False)).pack(side='left')
 PixelButton(bar,text='删除这一对',compact=True,command=lambda:remove(editor,True)).pack(side='left')

def sync_assets(editor):
 import rounded_scene as S
 editor.draft_assets=S.assets(editor.preview_project());editor.replace_assets=True

def add(editor,preset):
 if len(editor.draft.get('attachments',[]))>30:return
 editor.attachment_id=A.add_pair(editor.draft,preset);editor.attachment_details=True
 sync_assets(editor);editor.show_params();editor.request_preview()

def set_value(editor,key,value):
 item=A.record(editor.draft,editor.attachment_id);item[key]=value
 if item['linked']:
  other=item['id'][:-1]+('R' if item['id'].endswith('L') else 'L')
  for p in editor.draft['attachments']:
   if p['id']==other:p[key]=value
 editor.request_preview()

def set_link(editor,enabled):
 item=A.record(editor.draft,editor.attachment_id)
 other=item['id'][:-1]+('R' if item['id'].endswith('L') else 'L')
 for p in editor.draft['attachments']:
  if p['id'] in (item['id'],other):
   if enabled:
    for key in ('shape',*(s[0] for s in A.SPECS)):p[key]=item[key]
   p['linked']=enabled
 editor.show_params();editor.request_preview()

def remove(editor,pair):
 key=editor.attachment_id
 editor.draft['attachments']=[p for p in editor.draft['attachments'] if not (p['id']==key or pair and p['id'][:-1]==key[:-1])]
 if not editor.draft['attachments']:editor.draft.pop('attachments')
 sync_assets(editor);editor.show_params();editor.request_preview()
