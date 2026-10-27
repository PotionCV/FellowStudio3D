"""Hand props live in the existing left/right arm model panels."""
import tkinter as tk
import hand_props as H,attachments as A
import localized_ui as UI
from pixel_ui import PixelButton,PixelOption,PixelScale,FlowBar
from i18n import tr

def sync(editor):
 import rounded_scene as S
 editor.draft_assets=S.assets(editor.preview_project());editor.replace_assets=True

def add(editor,preset='box'):
 if len(editor.draft.get('attachments',[]))>=32:return
 editor.prop_id=H.add(editor.draft,preset,editor.part);editor.prop_mode=True;sync(editor);editor.show_params();editor.request_preview()

def set_value(editor,key,value):A.record(editor.draft,editor.prop_id)[key]=float(value);editor.request_preview()

def remove(editor):
 editor.draft['attachments']=[item for item in editor.draft['attachments'] if item['id']!=editor.prop_id]
 if not editor.draft['attachments']:editor.draft.pop('attachments')
 sync(editor);editor.show_params();editor.request_preview()

def transfer(editor):
 item=A.record(editor.draft,editor.prop_id);item['parent']='armL' if item['parent']=='armR' else 'armR'
 editor.part=item['parent'];editor.prop_mode=True;editor.show_params();editor.request_preview()

def reset_grip(editor):
 item=A.record(editor.draft,editor.prop_id);defaults=H.normalize(dict(id=item['id'],preset=item['preset'],parent=item['parent']))
 for key in ('pitch','yaw','roll','x','y','z'):item[key]=defaults[key]
 editor.show_params();editor.request_preview()

def mount(editor):
 box=tk.Frame(editor.params);box.pack(fill='x',padx=12,pady=10)
 UI.Label(box,text='手持道具',anchor='w').pack(fill='x',pady=6)
 bar=FlowBar(box,compact=True);bar.pack(fill='x')
 choices={tr(label):key for key,label in H.LABELS.items()};choice=tk.StringVar(master=editor,value=tr('长方体'))
 PixelOption(bar,choice,*choices).pack(side='left',fill='x',expand=True)
 button=PixelButton(bar,text='添加道具',command=lambda:add(editor,choices[choice.get()]))
 button.pack(side='left');button.configure(state='disabled' if len(editor.draft.get('attachments',[]))>=32 else 'normal')
 items=[item for item in editor.draft.get('attachments',[]) if item.get('kind')=='prop' and item['parent']==editor.part]
 if not items:return
 if getattr(editor,'prop_id',None) not in [item['id'] for item in items]:editor.prop_id=items[0]['id']
 names={A.name(item['id'],editor.draft):item['id'] for item in items};selected=tk.StringVar(master=editor,value=A.name(editor.prop_id,editor.draft))
 def choose(value):editor.prop_id=names[value];editor.show_params()
 if len(items)>1:PixelOption(box,selected,*names,command=choose).pack(fill='x',pady=6)
 UI.Label(box,text='随手腕移动和转动，独立绘画；尺寸影响UV，握持角度不改变UV。',wrap=True,anchor='w',justify='left',font=editor.owner.caption_font).pack(fill='x',pady=6)
 item=A.record(editor.draft,editor.prop_id);details=getattr(editor,'prop_details',False)
 UI.Label(box,text='物品形状',anchor='w',font=editor.owner.caption_font).pack(fill='x',pady=(6,2))
 shape=tk.StringVar(master=editor,value=tr(H.LABELS.get(item['preset'],'长方体')))
 def change_shape(value):
  item['preset']=choices[value];item['shape']=choices[value];sync(editor);editor.show_params();editor.request_preview()
 PixelOption(box,shape,*choices,command=change_shape).pack(fill='x',pady=4)
 for key,label,lo,hi,step in H.SPECS[:3]+(H.SPECS[3:] if details else ()):
  row=tk.Frame(box);row.pack(fill='x',pady=(6,0));row.columnconfigure(0,weight=1)
  UI.Label(row,text=label,anchor='w',wrap=True).grid(row=0,column=0,sticky='ew')
  value=tk.StringVar(master=editor,value=f'{item[key]:g}');UI.Label(row,textvariable=value,width=5,anchor='e').grid(row=0,column=1)
  slider=PixelScale(box,from_=lo,to=hi,resolution=step);slider.set(item[key]);slider.pack(fill='x')
  def changed(v,k=key,label=value):label.set(f'{float(v):g}');set_value(editor,k,float(v))
  slider.configure(command=changed)
 def toggle():editor.prop_details=not details;editor.show_params()
 PixelButton(box,text='收起握持细节' if details else '握持位置与细节',command=toggle).pack(fill='x',pady=6)
 if details:PixelButton(box,text='复位握持',command=lambda:reset_grip(editor)).pack(fill='x',pady=4)
 bar=FlowBar(box,compact=True);bar.pack(fill='x')
 PixelButton(bar,text='换到另一只手',command=lambda:transfer(editor)).pack(side='left')
 PixelButton(bar,text='删除道具',command=lambda:remove(editor)).pack(side='left')
