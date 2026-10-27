"""Independent caps and locks, staged inside the existing model editor."""
import copy,tkinter as tk
import hair
from pixel_ui import PixelButton,PixelOption,PixelScale,PixelCheck,FlowBar
from localized_ui import Label
from i18n import tr

FLIPPED=('x','outward','yaw','twist')

def items(editor):return [p for p in editor.draft.get('attachments',[]) if p.get('kind')=='hair']

def assemble(editor):
    settings=copy.deepcopy(editor.draft.get('hairstyle',hair.normalize_style({})))
    settings.update(assembly=True,pieces=copy.deepcopy(items(editor)));settings.pop('locks',None);settings.pop('cap',None)
    return settings

def commit(editor,settings,refresh=False):
    hair.rebuild(editor.draft,settings)
    if refresh:
        import hair_editor
        hair_editor.sync(editor);editor.show_params()
    editor.request_preview()

def add(editor,kind):
    if kind not in hair.ROLES:raise ValueError('Invalid hair role')
    if len(editor.draft.get('attachments',[]))>=32:raise ValueError('Maximum 32 attachments')
    settings=assemble(editor);used={p['id'] for p in settings['pieces']}
    opposite=hair.counterpart(kind)
    other=next((p for p in settings['pieces'] if hair.role(p)==opposite and hair.paired(settings['pieces'],p) is None),None) if opposite else None
    if other is not None:return duplicate(editor,other['id'],True)
    slot=next(i for i in range(1,33) if 'hair'+str(i)+'cap' not in used and 'hair'+str(i)+'lock' not in used)
    if kind!='lock':
        source_style='twins' if kind.startswith('pony') else 'long' if kind=='back' else 'bob' if kind.startswith('side') else 'short'
        template=copy.deepcopy(next(p for p in hair.records(editor.draft,{'style':source_style}) if p['section']==kind))
        if template['id'] in used:template.update(id='hair'+str(slot)+('cap' if kind=='cap' else 'lock'),section='cap' if kind=='cap' else 'lock')
        template['role']=kind
    else:
        template=hair.normalize(dict(id='hair'+str(slot)+'lock',section='lock',role='lock',shape='lock',length=12.,width=4.,thickness=2.,x=-7.,y=3.,z=0.))
    settings['pieces'].append(template);editor.hair_piece=template['id'];commit(editor,settings,True)
    return template['id']

def set_value(editor,key,field,value):
    settings=assemble(editor);item=hair.resolve(settings['pieces'],key)
    if item is None:raise ValueError('Invalid hair part')
    item[field]=value
    other=hair.paired(settings['pieces'],item)
    if item['section']!='cap' and getattr(editor,'hair_link',True) and other:
        other[field]=(hair.counterpart(value) or value) if field=='role' else -value if field in FLIPPED else value
    commit(editor,settings,field=='role')

def set_link(editor,key,enabled):
    editor.hair_link=enabled
    if enabled:
        settings=assemble(editor);source=hair.resolve(settings['pieces'],key)
        other=hair.paired(settings['pieces'],source) if source else None
        if other:
            for field,*_ in hair.LOCK_SPECS:other[field]=-source[field] if field in FLIPPED else source[field]
            commit(editor,settings,True);return
    editor.show_params()

def duplicate(editor,key,mirrored=False):
    if len(editor.draft.get('attachments',[]))>=32:raise ValueError('Maximum 32 attachments')
    settings=assemble(editor);source=hair.resolve(settings['pieces'],key)
    if source is None:raise ValueError('Invalid hair part')
    used={p['id'] for p in settings['pieces']};slot=next(i for i in range(1,33) if 'hair'+str(i)+'cap' not in used and 'hair'+str(i)+'lock' not in used)
    clone=copy.deepcopy(source);target_role=hair.counterpart(hair.role(source)) if mirrored else hair.role(source);target_role=target_role or hair.role(source);core='hair1'+target_role
    clone.update(role=target_role,section=target_role if target_role!='lock' and core not in used else 'cap' if source['section']=='cap' else 'lock');clone['id']=core if target_role!='lock' and core not in used else 'hair'+str(slot)+clone['section'];clone.pop('mirror',None)
    if mirrored:
        for field in FLIPPED:clone[field]=-clone.get(field,0.)
        # A lock has one linked partner; detach any former partner first.
        previous=hair.paired(settings['pieces'],source)
        if previous:previous.pop('mirror',None)
        clone['mirror']=source['id'];source['mirror']=clone['id'];clone['uv_mirror']=not source.get('uv_mirror',source['id'].endswith('R'))
    settings['pieces'].append(clone)
    import rounded_scene as S
    bundle=copy.deepcopy(editor.draft_assets or S.assets(editor.source));bundle['textures'][clone['id']]=copy.deepcopy(bundle['textures'][source['id']]);editor.draft_assets=bundle
    editor.hair_piece=clone['id'];commit(editor,settings,True)
    return clone['id']

def delete(editor,key):
    settings=assemble(editor);settings['pieces']=[p for p in settings['pieces'] if p['id']!=key]
    for p in settings['pieces']:
        if p.get('mirror')==key:p.pop('mirror')
    commit(editor,settings,True)

def mirror(editor,key):
    settings=assemble(editor);source=hair.resolve(settings['pieces'],key);other=hair.paired(settings['pieces'],source) if source else None
    if other is None:return duplicate(editor,key,True)
    identity=other['id'];section=other['section'];target_role=hair.role(other);other.clear();other.update(copy.deepcopy(source));other.update(id=identity,section=section,role=target_role,mirror=source['id'],uv_mirror=not source.get('uv_mirror',source['id'].endswith('R')))
    for field in FLIPPED:other[field]=-source.get(field,0.)
    source['mirror']=identity;commit(editor,settings,True)

def safe(editor,fn):
    try:return fn()
    except (ValueError,StopIteration) as ex:
        from tkinter import messagebox
        messagebox.showerror(tr('操作失败'),tr(str(ex) or 'Maximum 32 attachments'),parent=editor)

def mount(editor,kind=None,selector=True):
    box=editor.params;all_items=items(editor);available=[p for p in all_items if kind is None or (p['section']=='cap')==(kind=='cap')]
    if not available:
        Label(box,text='可以单独添加发顶或发束，自由组合。',wrap=True).pack(fill='x',padx=12,pady=8);return
    item=hair.resolve(available,getattr(editor,'hair_piece',None)) or available[0];key=item['id'];editor.hair_piece=key;choices={hair.name(p):p['id'] for p in available}
    value=tk.StringVar(master=editor,value=hair.name(item))
    def choose(label):editor.hair_piece=choices[label];editor.show_params()
    if selector:PixelOption(box,value,*choices,command=choose).pack(fill='x',padx=12,pady=8)
    bar=FlowBar(box,compact=True);bar.pack(fill='x',padx=12)
    actions={tr('复制发片'):lambda:duplicate(editor,key),tr('镜像复制发片'):lambda:duplicate(editor,key,True),tr('删除发片'):lambda:delete(editor,key)}
    operation=tk.StringVar(master=editor,value=tr('部件操作…'))
    def operate(label):
        operation.set(tr('部件操作…'));safe(editor,actions[label])
    PixelOption(bar,operation,*actions,command=operate).pack(side='left',fill='x',expand=True)
    if item['section']=='cap':
        labels={tr(v):k for k,v in hair.CAP_SHAPES.items()};current=hair.CAP_SHAPES.get(item['shape'],'角锥形');labels[tr(current)]=item['shape'];value=tk.StringVar(master=editor,value=tr(current))
        def shape(label):set_value(editor,key,'shape',labels[label])
        PixelOption(box,value,*labels,command=shape).pack(fill='x',padx=12,pady=8)
        details=getattr(editor,'hair_cap_details',False);specs=hair.CAP_SPECS[:7]+(hair.CAP_SPECS[7:] if details else ())
    else:
        other=hair.paired(all_items,item)
        if other:
            linked=tk.BooleanVar(master=editor,value=getattr(editor,'hair_link',True))
            PixelCheck(box,text='左右联动',variable=linked,command=lambda:set_link(editor,key,linked.get())).pack(fill='x',padx=12,pady=5)
            Label(box,text=tr('关联部件')+'：'+hair.name(other),wrap=True,anchor='w').pack(fill='x',padx=12,pady=3)
            PixelButton(box,text='对称到另一侧',command=lambda:mirror(editor,key)).pack(fill='x',padx=12)
        elif hair.counterpart(hair.role(item)):
            PixelButton(box,text='补齐另一侧',command=lambda:safe(editor,lambda:mirror(editor,key))).pack(fill='x',padx=12,pady=5)
        details=getattr(editor,'hair_lock_details',False);specs=hair.LOCK_SPECS[:5]+(hair.LOCK_SPECS[5:] if details else ())
    if item['section']!='cap' and details:
        labels={tr(label):role for role,label in hair.ROLES.items() if role!='cap'};value=tk.StringVar(master=editor,value=tr(hair.ROLES[hair.role(item)]))
        Label(box,text='发束类型',anchor='w').pack(fill='x',padx=12,pady=(8,2))
        PixelOption(box,value,*labels,command=lambda label:set_value(editor,key,'role',labels[label])).pack(fill='x',padx=12,pady=4)
    for field,label,lo,hi,step in specs:
        row=tk.Frame(box);row.pack(fill='x',padx=12,pady=(7,0));Label(row,text=label).pack(side='left')
        out=tk.StringVar(master=editor,value=f'{item[field]:g}');Label(row,textvariable=out).pack(side='right')
        scale=PixelScale(box,from_=lo,to=hi,resolution=step);scale.set(item[field]);scale.pack(fill='x',padx=12)
        def change(value,k=field,text=out):text.set(f'{float(value):g}');set_value(editor,key,k,float(value))
        scale.configure(command=change)
    def toggle():setattr(editor,'hair_cap_details' if item['section']=='cap' else 'hair_lock_details',not details);editor.show_params()
    PixelButton(box,text='收起发片细节' if details else '发片位置与细节',command=toggle).pack(fill='x',padx=12,pady=8)
    Label(box,text='自由组合的位置相对头部；发顶跟随头部，发束各有独立骨骼。使用发型模板会替换当前头发部件。',wrap=True,justify='left').pack(fill='x',padx=12,pady=8)
