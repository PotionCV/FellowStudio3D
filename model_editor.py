"""Staged parametric model editor with independent four-view animation preview."""
import copy,json,math,time,tkinter as tk,multiprocessing,queue
from tkinter import filedialog,messagebox
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from PIL import Image,ImageTk
import engine as E
import render_options as O
import model_data as MD
import sculpt
import plush,plush_editor
from preview_worker import compile_preview,init_progress,progressive_preview,frame_images
from pixel_ui import PixelButton,PixelOption,PixelScale,PixelCheck,ScrollPanel,FlowBar
import localized_ui as UI
from i18n import tr
BG='#ece4d8';PANEL='#f8f0df';FIELD='#e5d6bd';INK='#493c32';ACC='#e7a34c';CELL='#5a4d42'
VIEWS=((0,0),(90,0),(45,0),(45,30));NAMES=('正面','侧面','斜面','斜俯')
CATEGORIES={'shape':'外形','hair':'头发','ears':'耳朵','tail':'尾巴','props':'物品'}
PARTS={'torso':'腰 / 躯干','head':'头颈','armL':'左臂','armR':'右臂','legL':'左腿','legR':'右腿'}
class ModelEditor(tk.Toplevel):
    # One navigation state. Legacy helper names are aliases, not independent
    # booleans that can accidentally activate several panels at once.
    def _mode(self,key):return getattr(self,'model_category','shape')==key
    def _set_mode(self,key,enabled):
        if enabled:self.model_category=key
        elif self._mode(key):self.model_category='shape'
    hair_mode=property(lambda s:s._mode('hair'),lambda s,v:s._set_mode('hair',v))
    ear_mode=property(lambda s:s._mode('ears'),lambda s,v:s._set_mode('ears',v))
    prop_mode=property(lambda s:s._mode('props'),lambda s,v:s._set_mode('props',v))
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.ui_scale=owner.ui_scale;self.ui_font=owner.ui_font;self.caption_font=owner.caption_font
        self.title(tr('角色模型'));self.transient(owner);self.configure(bg=BG);self.minsize(1000,660)
        w=min(self.winfo_screenwidth()-60,max(1200,round(1400*self.ui_scale)));h=min(self.winfo_screenheight()-90,max(760,round(850*self.ui_scale)))
        self.geometry(f'{w}x{h}+{max(20,owner.winfo_rootx()+(owner.winfo_width()-w)//2)}+{max(20,owner.winfo_rooty()+(owner.winfo_height()-h)//2)}')
        self.source=copy.deepcopy(owner.project);self.draft=MD.normalize(self.source.get('model'));self.model_category='shape';self.part='torso';self.focus=owner.focus_view
        self.draft_assets=copy.deepcopy(self.source.get('assets3d'));self.replace_assets=False
        self.seq=copy.deepcopy(owner.seq);self.raw=dict(owner.raw_images);self.photos={};self.refs=[];self.cells=[];self.frame=owner.frame
        if self.source!=owner.active_project:
            import rounded_scene as S
            self.seq=E.authored(self.source);bundle=S.assets(self.source)
            self.seq=E.visible(self.seq,self.source,bundle)
            self.frame%=len(self.seq);self.raw=frame_images(self.seq,self.source.get('render'),self.frame)
        self.frame%=len(self.seq)
        self.original_seq=self.seq;self.original_raw=dict(self.raw);self.original_photos={};self.before_mode=False
        self.single_view=tk.BooleanVar(master=self,value=False);self.cell_views=[]
        self.playing=False;self.link=tk.BooleanVar(master=self,value=True);self.jobs=set();self.pending=None;self.poll_job=None;self.resize_job=None;self.closed=False;self.revision=0;self.latest=None;self.running=None;self.pool=None
        self._build();self.show_params();self.request_preview();self.protocol('WM_DELETE_WINDOW',self.cancel);self.bind('<MouseWheel>',self.wheel)
        self.play_job=None;self.grab_set();self.later(0,self.draw)
        self.preview_control=multiprocessing.Value('q',0);self.preview_progress=multiprocessing.Queue()
    def later(self,ms,fn):
        holder=[]
        def run():
            self.jobs.discard(holder[0])
            if not self.closed:fn()
        job=self.after(ms,run);holder.append(job);self.jobs.add(job);return job
    def stop_job(self,job):
        if job in self.jobs:self.after_cancel(job);self.jobs.discard(job)
    def button(self,parent,text,cmd,accent=False):return PixelButton(parent,text=text,command=cmd,accent=accent)
    def _build(self):
        top=FlowBar(self,compact=True,bg=PANEL);top.pack(fill='x',padx=12,pady=10)
        UI.Label(top,text='角色模型',fg=INK,font=self.ui_font).pack(side='left',padx=8)
        self.comparison_button(top).pack(side='left',padx=4)
        for label,fn in (('重置全部',self.reset_all),('保存模型',self.save_preset),('角色库…',self.browse_models)):
            self.button(top,label,fn).pack(side='right',padx=4)
        footer=FlowBar(self,compact=True,bg=PANEL);footer.pack(side='bottom',fill='x',padx=12,pady=10)
        self.status=tk.StringVar(master=self,value='模型修改仅在应用后写入当前项目')
        UI.Label(footer,textvariable=self.status,wrap=True,anchor='w',justify='left').pack(side='left',fill='x',expand=True,padx=6)
        self.button(footer,'取消',self.cancel).pack(side='right',padx=4);self.button(footer,'应用模型',self.apply,True).pack(side='right',padx=4)
        body=tk.PanedWindow(self,orient='horizontal',sashwidth=14,bg='#8d7257',bd=0,opaqueresize=False);body.pack(fill='both',expand=True,padx=12)
        center=tk.Frame(body,bg=BG);body.add(center,minsize=480,stretch='always')
        self.canvas=tk.Canvas(center,bg=CELL,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',self.resize);self.canvas.bind('<Button-1>',self.pick)
        self.canvas.bind('<Double-Button-1>',self.toggle_single_view)
        bar=FlowBar(center,compact=True,bg=BG);bar.pack(fill='x',pady=6)
        self.play_button=self.button(bar,'▶ 播放',self.toggle_play,True);self.play_button.pack(side='left')
        PixelCheck(bar,text='单视图',variable=self.single_view,command=self.draw).pack(side='left',padx=8)
        self.time_text=tk.StringVar(master=self)
        UI.Label(bar,textvariable=self.time_text,bg=BG,anchor='e',font=self.ui_font).pack(side='right')
        self.scrub=PixelScale(center,from_=0,to=1000,resolution=1,bg=BG,command=self.seek);self.scrub.pack(fill='x')
        shell=tk.Frame(body,bg=PANEL);body.add(shell,width=round(410*self.ui_scale),minsize=320,stretch='never')
        self.scroll=ScrollPanel(shell);self.scroll.pack(fill='both',expand=True);content=self.scroll.content
        tabs=FlowBar(content,compact=True,bg=PANEL);tabs.pack(fill='x',padx=10,pady=8)
        self.category_tabs={}
        for key,label in CATEGORIES.items():
            button=PixelButton(tabs,text=label,compact=True,command=lambda k=key:self.select_category(k));button.pack(side='left');self.category_tabs[key]=button
        self.shape_shell=tk.Frame(content,bg=PANEL);self.shape_shell.pack(fill='x')
        plush_editor.structure_control(self,self.shape_shell)
        grid=tk.Frame(self.shape_shell,bg=PANEL);grid.pack(fill='x',padx=8,pady=8);grid.columnconfigure((0,1),weight=1,uniform='parts');self.part_buttons={}
        for i,(key,name) in enumerate(PARTS.items()):
            b=PixelButton(grid,text=name,compact=True,command=lambda k=key:self.select(k));b.grid(row=i//2,column=i%2,sticky='ew',padx=3,pady=3);self.part_buttons[key]=b
        self.link_check=PixelCheck(content,text='左右联动',variable=self.link,command=self.link_limbs)
        self.params=tk.Frame(content,bg=PANEL);self.params.pack(fill='x')
    def wheel(self,event):
        node=self.winfo_containing(event.x_root,event.y_root)
        while node is not None:
            if isinstance(node,ScrollPanel):return node.wheel(event)
            node=getattr(node,'master',None)
    def select_category(self,key):
        if key not in CATEGORIES:raise ValueError('Invalid model category')
        self.model_category=key
        if key=='props' and self.part not in E.LIMBS[:2]:self.part='armR'
        self.show_params();self.scroll.canvas.yview_moveto(0);self.draw()
    def select(self,key):
        self.face_mode=False;self.model_category='shape';self.hair_mode=False;self.ear_mode=False;self.prop_mode=False
        self.part='torso' if key=='head' and plush.active(self.draft) else key;self.show_params();self.draw()
    def mirror_limb(self):
        if self.part not in E.LIMBS:return
        other=self.part[:-1]+('R' if self.part.endswith('L') else 'L')
        self.draft[other]=copy.deepcopy(self.draft[self.part])
        if 'curve' in self.draft[other]:self.draft[other]['curve']=-self.draft[other]['curve']
        self.request_preview()
    def link_limbs(self):
        if self.link.get():self.mirror_limb()

    def show_params(self):
        if plush.active(self.draft) and self.part=='head':self.part='torso'
        category=self.model_category
        self.model_category=category
        if category=='shape':
            if not self.shape_shell.winfo_manager():self.shape_shell.pack(fill='x',before=self.params)
        else:self.shape_shell.pack_forget()
        self.link_check.pack_forget()
        plush_editor.refresh(self)
        for child in self.params.winfo_children():child.destroy()
        for key,b in self.category_tabs.items():b.accent=key==category;b.draw()
        for key,b in self.part_buttons.items():b.accent=key==self.part and category=='shape';b.draw()
        if category in ('hair','ears','tail','props'):
            if category=='hair':
                import hair_editor
                hair_editor.mount(self)
            elif category=='ears':
                import attachment_editor
                attachment_editor.mount(self)
            elif category=='tail':
                import tail_editor
                tail_editor.mount(self)
            else:
                import hand_prop_editor
                if self.part not in ('armL','armR'):self.part='armR'
                choices={tr('左手'):'armL',tr('右手'):'armR'}
                value=tk.StringVar(master=self,value=next(k for k,v in choices.items() if v==self.part))
                UI.Label(self.params,text='所属手',anchor='w').pack(fill='x',padx=12,pady=(8,2))
                def choose(label):self.part=choices[label];self.show_params()
                PixelOption(self.params,value,*choices,command=choose).pack(fill='x',padx=12,pady=4)
                hand_prop_editor.mount(self)
            return
        if self.part in E.LIMBS:
            self.link_check.pack(fill='x',padx=10,pady=6,before=self.params)
            PixelButton(self.params,text='对称到另一侧',command=self.mirror_limb).pack(fill='x',padx=12,pady=6)
        if plush.active(self.draft) and self.part=='torso':plush_editor.panel(self);return
        UI.Label(self.params,text=PARTS[self.part],fg=INK,anchor='w').pack(fill='x',padx=12,pady=8)
        UI.Label(self.params,text='基础形状',anchor='w').pack(fill='x',padx=12,pady=(6,2))
        choices={tr(MD.SHAPE_LABELS[key]):key for key in MD.SHAPES[self.part]}
        self.shape_value=tk.StringVar(master=self,value=tr(MD.SHAPE_LABELS[self.draft[self.part]['shape']]))
        PixelOption(self.params,self.shape_value,*choices,command=lambda value:self.set_value('shape',choices[value])).pack(fill='x',padx=12,pady=(0,8))
        if self.part=='torso':specs=[('height','躯干高度',.65,1.35,.025),('shoulder','肩部宽度',.65,1.6,.025),('thickness','躯干厚度',.5,2.,.025),('waist','腰部宽度',.4,1.5,.025),('hip','胯部宽度',.65,1.5,.025),('pelvis_depth','胯部覆盖（px）',0,5,.25)]
        elif self.part=='head':specs=[('size','头部大小',.6,1.6,.05),('gap','头部间距',-6,6,.25),('depth','头部前后位置（px）',-8,8,.25)]
        else:
            specs=[('upper','上段长度（px）',2,12,.2),('lower','下段长度（px）',2,12,.2),('thickness','肢体粗细',.5,1.6,.05),('spread','关节内外偏移（px）',-6,6,.25),('vertical','关节上下偏移（px）',-4,4,.25),('gap','接合间距（px）',-6,6,.25)]
        self.button(self.params,'收起塑形参数' if getattr(self,'sculpt_open',False) else '展开塑形参数',self.toggle_sculpt).pack(fill='x',padx=12,pady=8)
        if getattr(self,'sculpt_open',False):
            tabs={'profile':'截面比例','contour':'前后轮廓','bulge':'局部凸起'}
            self.sculpt_tab=getattr(self,'sculpt_tab','profile');self.sculpt_var=tk.StringVar(master=self,value=tr(tabs[self.sculpt_tab]))
            def choose_tab(value):self.sculpt_tab=next(k for k,v in tabs.items() if tr(v)==value);self.show_params()
            PixelOption(self.params,self.sculpt_var,*[tr(v) for v in tabs.values()],command=choose_tab).pack(fill='x',padx=12,pady=4)
            specs += [(k,label,lo,hi,step) for k,label,lo,hi,step,default,group in sculpt.SPECS if group==self.sculpt_tab]
        for key,label,lo,hi,step in specs:
            row=tk.Frame(self.params,bg=PANEL);row.pack(fill='x',padx=12,pady=(8,0));row.columnconfigure(0,weight=1)
            UI.Label(row,text=label,wrap=True,anchor='w',justify='left').grid(row=0,column=0,sticky='ew')
            current=self.draft[self.part].get(key,sculpt.DEFAULTS.get(key,0))
            value=tk.StringVar(master=self,value=f'{current:g}');UI.Label(row,textvariable=value,width=5,anchor='e').grid(row=0,column=1,sticky='ne')
            control=PixelScale(self.params,from_=lo,to=hi,resolution=step);control.set(current);control.pack(fill='x',padx=12)
            def update(v,k=key,out=value):out.set(f'{float(v):g}');self.set_value(k,float(v))
            control.configure(command=update)
        if self.part in E.LIMBS:
            self.connected=tk.BooleanVar(master=self,value=self.draft[self.part]['connected'])
            PixelCheck(self.params,text='贴合接合',variable=self.connected,command=lambda:self.set_value('connected',self.connected.get())).pack(fill='x',padx=12,pady=8)
        self.button(self.params,'重置这个部位',self.reset_part).pack(fill='x',padx=12,pady=10)
        UI.Label(self.params,text='偏移可为负：关节向内、接合重叠；正值向外、分离。长度按原始像素计算。',wraplength=360,anchor='w',justify='left',fg='#8a7967').pack(fill='x',padx=12,pady=8)
    def toggle_sculpt(self):self.sculpt_open=not getattr(self,'sculpt_open',False);self.show_params()
    def set_value(self,key,value):
        self.draft[self.part][key]=value
        if self.link.get() and self.part in E.LIMBS:
            other=self.part[:-1]+('R' if self.part.endswith('L') else 'L');self.draft[other][key]=-value if key=='curve' else value
        self.request_preview()
    def reset_part(self):
        self.draft[self.part]=copy.deepcopy(MD.DEFAULT[self.part])
        if self.link.get() and self.part in E.LIMBS:
            other=self.part[:-1]+('R' if self.part.endswith('L') else 'L');self.draft[other]=copy.deepcopy(MD.DEFAULT[other])
        self.show_params();self.request_preview()
    def reset_all(self):
        self.draft=MD.normalize()
        for key in ('last_plush_body','structure_assets'):
            if hasattr(self,key):delattr(self,key)
        self.show_params();self.request_preview()
    def request_preview(self):
        self.revision+=1
        self.latest=None
        if hasattr(self,'preview_control'):self.preview_control.value=self.revision
        if self.pending:self.stop_job(self.pending)
        self.pending=self.later(100,self.submit)
    def submit(self):
        self.pending=None;project=self.preview_project();self.latest=(self.revision,project)
        self.start_latest()
    def preview_project(self):
        project=copy.deepcopy(self.source);project['model']=MD.normalize(self.draft)
        if self.draft_assets is not None:project['assets3d']=copy.deepcopy(self.draft_assets)
        return project
    def start_latest(self):
        if self.running or not self.latest:return
        version,project=self.latest;self.latest=None
        self.preview_control.value=version
        if self.pool is None:self.pool=ProcessPoolExecutor(max_workers=1,initializer=init_progress,initargs=(self.preview_control,self.preview_progress))
        self.running=(version,self.pool.submit(progressive_preview,project,version,self.frame));self.status.set('正在更新动作… 可继续调整');self.poll_job=self.later(15,self.poll)
    def poll(self):
        if not self.running:return
        version,future=self.running
        partial=None;merged={}
        try:
            while True:
                revision,seq,raw,physical=self.preview_progress.get_nowait()
                if revision==self.revision:
                    partial=seq;merged.update(raw)
        except queue.Empty:pass
        if partial is not None:self.receive_preview(partial,merged);self.frame%=len(partial);self.draw()
        if not future.done():self.poll_job=self.later(25,self.poll);return
        self.running=None
        try:
            result=future.result()
            if result is not None and version==self.revision:
                seq,raw=result
                self.receive_preview(seq,raw);self.frame%=len(seq);self.draw();self.status.set(self.model_status())
        except Exception as ex:self.status.set(str(ex))
        self.start_latest()
    def model_status(self):
        import rounded_scene as S,uv_assets as U
        before=self.draft_assets or S.assets(self.source);after=S.assets(self.preview_project())
        if any(before['textures'][p].get('png') and U.surface_record(before,p)!=U.surface_record(after,p) for p in U.parts(after) if p in before['textures']):
            return '贴图已适配新外形；按住查看修改前，继续绘画前请生成新素材。'
        return '模型修改仅在应用后写入当前项目'
    def receive_preview(self,seq,raw):
        if getattr(self,'accepted_revision',None)!=self.revision:
            self.accepted_revision=self.revision;self.raw={};self.photos.clear()
        self.seq=seq;self.raw.update(raw)
        self.photos={k:v for k,v in self.photos.items() if (k[0],k[1]) not in raw}
    def resize(self,event):
        if self.resize_job:self.stop_job(self.resize_job)
        self.resize_job=self.later(120,self.draw)
    def draw(self):
        if self.before_mode:
            current=self.seq,self.raw,self.photos
            try:
                self.seq=self.original_seq;self.raw=self.original_raw;self.photos=self.original_photos;self.draw_scene()
            finally:self.seq,self.raw,self.photos=current
        else:self.draw_scene()
    def comparison_button(self,parent):
        button=self.button(parent,'按住看修改前',lambda:None)
        button.bind('<ButtonPress-1>',lambda e:self.compare_before(True),add='+')
        button.bind('<ButtonRelease-1>',lambda e:self.compare_before(False),add='+')
        button.bind('<Leave>',lambda e:self.compare_before(False),add='+')
        return button
    def compare_before(self,value):
        self.before_mode=value;self.draw()
    def draw_scene(self):
        self.resize_job=None
        if not self.seq or self.closed:return
        w,h=self.canvas.winfo_width(),self.canvas.winfo_height();count=1 if self.single_view.get() else 2;settings=self.source.get('render');cw,ch=O.size(settings);size,cell_height=O.fit(w/count,h/count,settings)
        x=(w-size*count)//2;y=(h-cell_height*count)//2;self.cells=[];self.cell_views=[];self.refs=[];self.canvas.delete('all')
        for position,v in enumerate((self.focus,) if self.single_view.get() else range(4)):
            yaw,pitch=VIEWS[v]
            cx=x+(position%count)*size;cy=y+(position//count)*cell_height;self.cells.append((cx,cy,size));self.cell_views.append(v);key=(v,self.frame,size)
            if key not in self.photos:
                a=self.raw.get((v,self.frame))
                if a is None:
                    available=[i for view,i in self.raw if view==v]
                    if not available:continue
                    a=self.raw[v,min(available,key=lambda i:abs(i-self.frame))]
                self.photos[key]=ImageTk.PhotoImage(Image.fromarray(a).resize((size,cell_height),Image.Resampling.NEAREST),master=self)
                while len(self.photos)>8 and sum(k[2]*k[2]*4 for k in self.photos)>64*1024*1024:self.photos.pop(next(iter(self.photos)))
            image=self.photos[key];self.refs.append(image);self.canvas.create_image(cx,cy,anchor='nw',image=image)
            self.canvas.create_rectangle(cx,cy,cx+size,cy+cell_height,outline=ACC if v==self.focus else '#8a7967',width=3 if v==self.focus else 1)
            self.canvas.create_text(cx+10,cy+10,anchor='nw',text=tr(NAMES[v]),font=self.ui_font,fill=ACC if v==self.focus else '#d9cbb6')
            if not self.playing and getattr(self,'show_handles',True):
                pose=dict(self.seq[self.frame],yaw=self.seq[self.frame]['yaw']+yaw,pitch=self.seq[self.frame]['pitch']+pitch);j=O.joints(pose,settings)
                points=[j[self.part][k] for k in ('root','mid','tip')] if self.part in E.LIMBS else [j[k]['tip'] for k in ('waist','neck','head')]
                for px,py in points:self.canvas.create_rectangle(cx+px*size/cw-4,cy+py*size/cw-4,cx+px*size/cw+4,cy+py*size/cw+4,fill=ACC,outline=INK)
        self.time_text.set(f'{self.frame/self.source["fps"]:.2f} / {self.source["seconds"]:g}'+tr(' 秒'))
        self.scrub.set(self.frame/max(1,len(self.seq)-1)*1000)
    def pick(self,event):
        if self.playing:return
        settings=self.source.get('render');cw,ch=O.size(settings)
        for v,(x,y,size) in zip(self.cell_views,self.cells):
            if x<=event.x<x+size and y<=event.y<y+size*ch/cw:
                self.focus=v;pose=dict(self.seq[self.frame],yaw=self.seq[self.frame]['yaw']+VIEWS[v][0],pitch=self.seq[self.frame]['pitch']+VIEWS[v][1]);j=O.joints(pose,settings)
                candidates=[]
                for key in PARTS:
                    for joint in (('root','mid','tip') if key in E.LIMBS else ('tip',)):
                        px,py=j[key][joint];candidates.append((math.hypot(x+px*size/cw-event.x,y+py*size/cw-event.y),key))
                distance,key=min(candidates)
                if distance<30:self.select(key)
                self.draw();return
    def toggle_single_view(self,event=None):
        self.single_view.set(not self.single_view.get());self.draw()
    def toggle_play(self):
        self.stop_job(self.play_job);self.play_job=None
        self.playing=not self.playing;self.play_button.configure(text='■ 暂停' if self.playing else '▶ 播放')
        if self.playing and E.MT.mode(self.source)!='loop' and self.frame==len(self.seq)-1:self.frame=0
        if self.playing:self.started=time.perf_counter()-self.frame/self.source['fps'];self.tick()
        else:self.draw()
    def tick(self):
        if not self.playing:return
        frame,finished=E.MT.preview_frame(time.perf_counter()-self.started,self.source['fps'],len(self.seq),self.source)
        if finished:self.frame=frame;self.playing=False;self.play_button.configure(text='▶ 播放');self.draw();return
        if frame!=self.frame:self.frame=frame;self.draw()
        self.play_job=self.later(30,self.tick)
    def seek(self,value):
        self.stop_job(self.play_job);self.play_job=None
        self.playing=False;self.play_button.configure(text='▶ 播放');self.frame=min(len(self.seq)-1,int(float(value)/1000*len(self.seq)));self.draw()
    def save_preset(self):
        folder=self.owner.state_path.parent/'models';folder.mkdir(parents=True,exist_ok=True)
        path=filedialog.asksaveasfilename(parent=self,initialdir=folder,initialfile='model.json',defaultextension='.json',filetypes=[(tr('角色模型'),'*.json')])
        if path:
            try:
                import rounded_scene as S
                MD.save(self.draft,path,assets=S.assets(self.preview_project()))
            except Exception as ex:messagebox.showerror(tr('保存失败'),str(ex),parent=self)
    def load_preset(self):
        folder=self.owner.state_path.parent/'models'
        path=filedialog.askopenfilename(parent=self,initialdir=folder if folder.is_dir() else E.ROOT/'examples'/'models',filetypes=[(tr('角色模型'),'*.json')])
        if path:
            try:
                resource=MD.load_resource(path);self.draft=resource['model']
                if 'assets3d' in resource:self.draft_assets=resource['assets3d'];self.replace_assets=True
                self.show_params();self.request_preview()
            except Exception as ex:messagebox.showerror(tr('无法打开'),str(ex),parent=self)
    def browse_models(self):
        import resource_browser
        return resource_browser.show(self.owner,self)
    def apply(self):
        model=MD.normalize(self.draft);self.owner.snapshot();self.owner.project['model']=model
        if self.replace_assets:
            import rounded_scene as S
            self.owner.project['assets3d']=S.assets(self.preview_project())
        self.owner.changed();self.destroy()
    def cancel(self):self.destroy()
    def destroy(self):
        if self.closed:return
        self.closed=True;self.playing=False
        if hasattr(self,'preview_control'):self.preview_control.value=-1
        for job in list(self.jobs):self.stop_job(job)
        if self.pool:self.pool.shutdown(wait=False,cancel_futures=True)
        self.owner.model_editor=None
        super().destroy()
        self.photos.clear();self.original_photos.clear();self.refs=[]
        for key,value in list(vars(self).items()):
            if isinstance(value,tk.Variable):setattr(self,key,None)
