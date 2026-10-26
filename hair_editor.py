"""A staged hairstyle tab; appearance here, bone animation in body controls."""
import copy,tkinter as tk
import hair
from pixel_ui import PixelButton,PixelOption,PixelScale,PixelCheck,FlowBar
from localized_ui import Label
from i18n import tr

def sync(editor):
    import rounded_scene as S
    archive=getattr(editor,'hair_texture_archive',{})
    before=editor.draft_assets or S.assets(editor.source)
    archive.update({k:copy.deepcopy(v) for k,v in before['textures'].items() if k.startswith('hair')});editor.hair_texture_archive=archive
    bundle=copy.deepcopy(before);bundle['textures'].update(copy.deepcopy(archive))
    editor.draft_assets=S.assets({'model':editor.draft,'assets3d':bundle});editor.replace_assets=True

def apply_style(editor,style):
    settings=hair.normalize_style({'style':style})
    candidate=copy.deepcopy(editor.draft)
    try:hair.rebuild(candidate,settings)
    except ValueError as ex:
        from tkinter import messagebox
        messagebox.showerror(tr('操作失败'),tr(str(ex)),parent=editor);return
    editor.draft=candidate;sync(editor);editor.show_params();editor.request_preview()

def set_value(editor,key,value):
    settings=dict(editor.draft['hairstyle']);settings[key]=float(value);hair.rebuild(editor.draft,settings);editor.request_preview()

def remove(editor):
    editor.draft.pop('hairstyle',None);editor.draft['attachments']=[p for p in editor.draft.get('attachments',[]) if p.get('kind')!='hair']
    if not editor.draft['attachments']:editor.draft.pop('attachments')
    sync(editor);editor.show_params();editor.request_preview()

def set_lock(editor,section,key,value):
    settings=copy.deepcopy(editor.draft['hairstyle']);locks=settings.setdefault('locks',{})
    locks.setdefault(section,{})[key]=float(value)
    other=hair.counterpart(section)
    if getattr(editor,'hair_link',True) and other:
        locks.setdefault(other,{})[key]=float(value)*(-1 if key in ('x','outward','yaw','twist') else 1)
    hair.rebuild(editor.draft,settings);editor.request_preview()

def reset_lock(editor,section):
    settings=copy.deepcopy(editor.draft['hairstyle']);locks=settings.get('locks',{});locks.pop(section,None)
    if getattr(editor,'hair_link',True):locks.pop(hair.counterpart(section),None)
    hair.rebuild(editor.draft,settings);editor.show_params();editor.request_preview()

def mirror_lock(editor,source):
    other=hair.counterpart(source)
    if not other:return
    item=next((p for p in editor.draft['attachments'] if p.get('kind')=='hair' and p['section']==source),None)
    if item is None:return
    settings=copy.deepcopy(editor.draft['hairstyle']);values=hair.lock_values(item,settings)
    settings.setdefault('locks',{})[other]={k:(-v if k in ('x','outward','yaw','twist') else v) for k,v in values.items()}
    hair.rebuild(editor.draft,settings);editor.show_params();editor.request_preview()

def edit_twins(editor):
    editor.hair_edit_scope='lock';editor.hair_section='ponyL';editor.hair_piece='hair1ponyL';editor.hair_link=True;editor.show_params()

def mount(editor):
    import hair_assembly as HA
    box=editor.params
    Label(box,text='头发部件',anchor='w').pack(fill='x',padx=12,pady=(8,4))
    bar=FlowBar(box,compact=True);bar.pack(fill='x',padx=12,pady=5)
    choices={tr(label):key for key,label in hair.ROLES.items()};role=getattr(editor,'hair_add_role','cap')
    value=tk.StringVar(master=editor,value=tr(hair.ROLES[role]));editor.hair_add_value=value
    def choose(label):editor.hair_add_role=choices[label]
    PixelOption(bar,value,*choices,command=choose).pack(side='left',fill='x',expand=True)
    PixelButton(bar,text='添加部件',command=lambda:HA.safe(editor,lambda:HA.add(editor,choices[value.get()])),compact=True).pack(side='left')
    current=HA.items(editor);order={role:i for i,role in enumerate(hair.ROLES)}
    current=sorted(current,key=lambda p:order[hair.role(p)])
    Label(box,text='已添加部件',anchor='w').pack(fill='x',padx=12,pady=(8,3))
    component_list=tk.Listbox(box,height=min(6,max(3,len(current))),exportselection=False,activestyle='none',font=editor.owner.caption_font)
    component_list.pack(fill='x',padx=12,pady=(0,6));editor.hair_component_list=component_list
    selected=hair.resolve(current,getattr(editor,'hair_piece',None)) or (current[0] if current else None)
    for index,item in enumerate(current):
        component_list.insert('end',hair.name(item))
        if selected and item['id']==selected['id']:component_list.selection_set(index);component_list.see(index)
    def pick(event=None):
        indices=component_list.curselection()
        if not indices:return
        key=current[indices[0]]['id']
        if key!=getattr(editor,'hair_piece',None):editor.hair_piece=key;editor.show_params()
    component_list.bind('<<ListboxSelect>>',pick)
    def toggle_templates():editor.hair_templates_open=not getattr(editor,'hair_templates_open',False);editor.show_params()
    PixelButton(box,text='收起发型模板' if getattr(editor,'hair_templates_open',False) else '发型模板…',command=toggle_templates).pack(fill='x',padx=12,pady=5)
    if getattr(editor,'hair_templates_open',False):
        templates={tr(label):key for key,label in hair.STYLES.items()};style=getattr(editor,'new_hair_style','short');choice=tk.StringVar(master=editor,value=tr(hair.STYLES[style]))
        def choose_template(label):editor.new_hair_style=templates[label]
        PixelOption(box,choice,*templates,command=choose_template).pack(fill='x',padx=12,pady=4)
        def use_template():editor.hair_templates_open=False;apply_style(editor,templates[choice.get()])
        PixelButton(box,text='替换为模板',command=use_template).pack(fill='x',padx=12,pady=4)
        Label(box,text='模板只负责一次生成部件；应用模板会替换当前头发，模型应用前仍可取消。',wrap=True,justify='left').pack(fill='x',padx=12,pady=5)
    if selected:
        editor.hair_piece=selected['id'];Label(box,text=hair.name(selected),anchor='w').pack(fill='x',padx=12,pady=6)
        HA.mount(editor,selector=False)
    else:Label(box,text='从头发主体、左右刘海或左右中发束开始添加。',wrap=True,justify='left').pack(fill='x',padx=12,pady=8)
