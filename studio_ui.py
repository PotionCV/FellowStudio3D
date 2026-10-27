"""FellowStudio — direct a body, not a timeline."""
import copy, ctypes, json, math, os, sys, time, tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, font
from pathlib import Path
from PIL import Image, ImageTk
import engine as E
import render_options as O
import i18n
from i18n import tr
import localized_ui as UI
from concurrent.futures import ProcessPoolExecutor
from preview_worker import compile_preview
from pixel_ui import PixelScale,PixelCheck,PixelOption,PixelScroll,PixelButton,PixelEntry,ScrollPanel,FlowBar
BG='#ece4d8'; PANEL='#f8f4ec'; FIELD='#e8dfd1'; INK='#493c32'; DIM='#8a7967'; ACC='#e7a34c'; CELL='#5a4d42'
VIEWS=((0,0),(90,0),(45,0),(45,30));VN=('正面','侧面','斜面','斜俯')
STATE=E.ROOT/'studio_v2.json'

class App(tk.Tk):
    def __init__(self,state=STATE,preferences=None):
        # Register before Tk initializes its native font manager/cache.
        from platform_support import register_fonts,pixel_font_family
        register_fonts(E.ROOT)
        super().__init__();self.state_path=Path(state);self.title('FellowStudio · 动作工坊');self.configure(bg=BG)
        self.option_add('*Font',('Microsoft YaHei UI',10));self.option_add('*Background',PANEL);self.option_add('*Foreground',INK)
        pixel_family=pixel_font_family(font.families(self),font.nametofont('TkDefaultFont',root=self).actual('family'))
        self.project=E.new_project('stand');self.load_error=''
        if self.state_path.exists():
            try:self.project=E.load(self.state_path)
            except Exception as ex:self.load_error=str(ex)
        self.preferences_path=Path(preferences) if preferences else (E.ROOT/'ui_settings.json' if self.state_path==STATE else self.state_path.parent/'ui_settings.json')
        try:prefs=json.loads(self.preferences_path.read_text(encoding='utf-8'))
        except (OSError,ValueError,TypeError):prefs={}
        if not isinstance(prefs,dict):prefs={}
        try:self.ui_scale=max(.75,min(2.,float(prefs.get('scale',1.5))))
        except (ValueError,TypeError):self.ui_scale=1.5
        if not math.isfinite(self.ui_scale):self.ui_scale=1.5
        self.preferred_ui_scale=self.ui_scale
        from ui_layout import fitted_scale
        width,height=self.fit_window()
        self.ui_scale=fitted_scale(self.preferred_ui_scale,width,height)
        self.adapt_job=None;self._adapt_size=(width,height)
        self.export_directory=str(prefs.get('export_directory') or E.ROOT)
        self.paint_directory=str(prefs.get('painting_directory') or '')
        bindings=prefs.get('painting_bindings',{})
        self.paint_bindings={k:v for k,v in list(bindings.items())[-32:] if isinstance(k,str) and len(k)==64 and isinstance(v,str)} if isinstance(bindings,dict) else {}
        if not Path(self.export_directory).is_dir():self.export_directory=str(E.ROOT)
        self.panel_widths=prefs.get('panels',[340,400])
        if not isinstance(self.panel_widths,list) or len(self.panel_widths)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) and 150<=x<=900 for x in self.panel_widths):self.panel_widths=[340,400]
        self.display_preferences={**E.RENDER_DEFAULTS,**(prefs.get('render') if isinstance(prefs.get('render'),dict) else {})}
        self.display_preferences['perfect']=True
        self.language=prefs.get('language','en');i18n.set_language(self.language);self.language=i18n.language
        self.title(tr('FellowStudio · 动作工坊'))
        if not self.state_path.exists():self.project=self.make_project('stand')
        if self.display_preferences:
            # Frame and lighting belong to a saved project, rather than silently
            # inheriting another project's personal display preferences.
            saved=self.project.get('render',{});self.project['render']=copy.deepcopy(self.display_preferences)
            for key in O.DEFAULTS:
                if key in saved:self.project['render'][key]=saved[key]
                elif self.state_path.exists():self.project['render'].pop(key,None)
        self.ui_font=font.Font(family=pixel_family,size=-round(24*self.ui_scale));self.option_add('*Font',self.ui_font)
        self.caption_font=font.Font(family=pixel_family,size=-round(18*self.ui_scale))
        self.executor=None;self.future_job=None;self.latest_request=None;self.revision=0;self.raw_images={};self.resize_job=None;self.resizing=False;self.focus_view=0;self.active_project=copy.deepcopy(self.project)
        self.model_editor=None
        self.history=[];self.future=[];self.frame=0;self.playing=False;self.play_job=None;self.epoch=0;self.pending=None;self.save_job=None
        self.selection=('body','arms');self.seq=[];self.photos={};self.cells=[];self.refs=[];self.drag=None;self.drag_physics=None;self.compare=False
        self._build();self.restore_panel_widths();self.refresh_lists();self.show_params();self.refresh_control_styles();self.rebuild()
        self.bind('<Configure>',self.queue_adapt_layout,add='+')
        self.bind('<Control-z>',lambda e:self.undo());self.bind('<Control-y>',lambda e:self.undo(True));self.bind('<Control-s>',lambda e:self.save_as())
        if sys.platform=='darwin':
            self.bind('<Command-z>',lambda e:self.undo());self.bind('<Command-Shift-z>',lambda e:self.undo(True));self.bind('<Command-s>',lambda e:self.save_as())
        self.protocol('WM_DELETE_WINDOW',self.close);self.after(200,self.render)
        if self.load_error:self.status.set('未覆盖原配方：'+self.load_error)

    def make_project(self,kind='stand'):
        project=E.new_project(kind)
        if hasattr(self,'parts'):project['render']=self.current_display()
        if self.project.get('model') is not None:project['model']=copy.deepcopy(self.project['model'])
        if 'camera_y' in self.project:project['camera_y']=self.project['camera_y']
        project['auto_name_key']=E.ACTIONS[kind]
        return project

    def button(self,p,text,cmd,accent=False):
        return PixelButton(p,text=text,command=cmd,accent=accent)
    def label(self,p,text,**kw):return UI.Label(p,text=text,anchor='w',**kw)
    def _build(self):
        top=FlowBar(self,compact=True,pin_right=True,bg=PANEL);top.pack(fill='x',padx=8,pady=(8,4))
        options=FlowBar(self,compact=True,bg=PANEL);options.pack(fill='x',padx=8,pady=(0,6))
        self.name=tk.StringVar(value=self.project['name']);PixelEntry(top,textvariable=self.name,width=15,bd=0,bg=FIELD).pack(side='left',padx=8)
        self.name.trace_add('write',lambda *_:self.rename())
        for t,c in [('A−',lambda:self.zoom(-.25)),('A＋',lambda:self.zoom(.25)),('新建',self.new),('打开',self.open),('保存',self.save_as),('撤销',self.undo)]:self.button(top,t,c).pack(side='left',padx=3)
        self.language_var=tk.StringVar(value=i18n.LANGUAGES[self.language]);PixelOption(top,self.language_var,*i18n.LANGUAGES.values(),command=self.set_language).pack(side='right',padx=6)
        self.button(options,'导出序列帧',self.export,True).pack(side='right',padx=8)
        self.button(options,'角色模型',self.edit_model).pack(side='left',padx=8)
        self.parts=tk.BooleanVar(value=self.project.get('render',{}).get('parts',True));self.gaps=tk.BooleanVar(value=self.project.get('render',{}).get('gaps',True))
        self.textures=tk.BooleanVar(value=self.project.get('render',{}).get('textures',True))
        self.outline=tk.BooleanVar(value=self.project.get('render',{}).get('outline',True))
        self.outline_color=tk.StringVar(value=self.project.get('render',{}).get('outline_color','auto'))
        self.button(options,'创作资源库…',self.load_motion_resource).pack(side='left',padx=4)
        self.light_enabled=tk.BooleanVar(value=O.normalized(self.project.get('render'))['lighting']);self.self_shadow=tk.BooleanVar(value=O.normalized(self.project.get('render'))['self_shadow'])
        self.retro_animation=tk.BooleanVar(value=O.normalized(self.project.get('render'))['retro_animation'])
        self.render_flag_checks={}
        body=tk.PanedWindow(self,orient='horizontal',bg='#8d7257',bd=0,sashwidth=14,sashpad=2,showhandle=True,handlesize=22,handlepad=16,opaqueresize=False);self.panes=body;body.pack(fill='both',expand=True,padx=8)
        body.bind('<ButtonRelease-1>',lambda e:self.after_idle(self.remember_panel_widths))
        body.bind('<Configure>',lambda e:self.fit_panels(e.width))
        left_shell=tk.Frame(body,bg=PANEL);self.left=left_shell;body.add(left_shell,minsize=200,width=round(340*self.ui_scale),stretch='never')
        self.left_scroll=ScrollPanel(left_shell);self.left_scroll.pack(fill='both',expand=True);left=self.left_scroll.content
        self.label(left,'基础动作',fg=DIM).pack(fill='x',padx=10,pady=(12,5))
        self.base_name=tk.StringVar();self.base_menu=PixelOption(left,self.base_name,*[v for k,v in E.ACTIONS.items() if k!='pose'],command=self.change_base);self.base_menu.configure(bd=0,highlightthickness=0,bg=FIELD);self.base_menu.pack(fill='x',padx=10)
        self.button(left,'调整基础动作',lambda:self.select('base',0)).pack(fill='x',padx=10,pady=5)
        creation=tk.StringVar(value='动画工具…')
        creation_actions={'从姿势开始…':self.choose_pose,'姿势动画…':self.edit_pose_animation,'动作串联…':self.arrange_actions,'保存动画…':self.save_motion_resource}
        def create_motion(label):creation.set('动画工具…');creation_actions[label]()
        PixelOption(left,creation,*creation_actions,command=create_motion).pack(fill='x',padx=10,pady=4)
        self.label(left,'叠加动作',fg=DIM).pack(fill='x',padx=10,pady=(18,5))
        stack_frame=tk.Frame(left,bg=INK,padx=4,pady=4);stack_frame.pack(fill='x',padx=10)
        self.stack=tk.Listbox(stack_frame,height=4,bd=0,bg=FIELD,selectbackground=ACC,selectforeground=INK,exportselection=False,activestyle='none');self.stack.pack(fill='x');self.stack.bind('<<ListboxSelect>>',self.pick_layer)
        r=tk.Frame(left);r.pack(fill='x',padx=10,pady=5)
        add_value=tk.StringVar(value='＋ 添加')
        def add_selected(label):
            key=next(k for k,v in E.ACTIONS.items() if v==label);self.add(key);add_value.set('＋ 添加')
        PixelOption(r,add_value,*[E.ACTIONS[k] for k in ('pose','raise','wave','bow','nod','shake','stretch','squat','bounce','thrust','swing','kick','hit','jump','fall','getup','roll','climb','turn','swim','hover','tail','hair')],command=add_selected).pack(side='left',fill='x',expand=True)
        actions=FlowBar(left,compact=True);actions.pack(fill='x',padx=10,pady=4);self.layer_actions={}
        for text,fn in (('上移',lambda:self.move_layer(-1)),('下移',lambda:self.move_layer(1)),('移除',self.remove)):
            button=PixelButton(actions,text=text,command=fn,compact=True);button.pack(side='left');self.layer_actions[text]=button
        effects=tk.Frame(left,bg=PANEL);effects.pack(fill='x',padx=10,pady=(12,0));self.animation_effects=effects
        self.label(effects,'动画表现',fg=DIM).pack(fill='x',pady=(0,4))
        check=PixelCheck(effects,text='复古动画',variable=self.retro_animation,command=lambda:self.toggle_render_flag('retro_animation',self.retro_animation));check.pack(fill='x');self.render_flag_checks['retro_animation']=check
        self.label(left,'整体控制',fg=DIM).pack(fill='x',padx=10,pady=(18,5))
        grid=tk.Frame(left);grid.pack(fill='x',padx=8);self.part_buttons={}
        for i,(k,t) in enumerate(E.LABELS.items()):
            button=PixelButton(grid,text=t,command=lambda k=k:self.select('body',k),compact=True,accent=self.selection==('body',k));button.grid(row=i//2,column=i%2,sticky='ew',padx=2,pady=3);self.part_buttons[k]=button
            if k=='tail' and not any(p.get('kind')=='tail' for p in (self.project.get('model') or {}).get('attachments',[])):button.grid_remove()
            if k=='hair' and not any(p.get('kind')=='hair' for p in (self.project.get('model') or {}).get('attachments',[])):button.grid_remove()
        grid.columnconfigure((0,1),weight=1,uniform='parts')
        self.label(left,'控制作用于整段动作\n基础件始终保留',fg=DIM,justify='left',wraplength=200).pack(side='bottom',fill='x',padx=10,pady=12)
        center=tk.Frame(body,bg=BG);body.add(center,minsize=360,stretch='always',padx=8)
        viewbar=FlowBar(center,compact=True,bg=BG);self.viewbar=viewbar;viewbar.pack(fill='x',pady=(0,6))
        self.handles=tk.BooleanVar(value=True);PixelCheck(viewbar,text='IK 手柄',variable=self.handles,command=self.render,bg=BG).pack(side='left')
        self.ab=self.button(viewbar,'按住看基础',lambda:None);self.ab.pack(side='left')
        self.display_options_button=self.button(viewbar,'显示选项…',self.toggle_display_options);self.display_options_button.pack(side='left')
        self.button(viewbar,'画幅尺寸…',self.edit_render_options).pack(side='left')
        self.display_options=FlowBar(center,compact=True,bg=PANEL);self.display_options_shown=False
        for t,v in [('显示贴图',self.textures),('部位分色',self.parts),('外边线',self.outline),('交叠留缝',self.gaps)]:PixelCheck(self.display_options,text=t,variable=v,command=self.display).pack(side='left')
        for text,key,var in (('光照','lighting',self.light_enabled),('自阴影','self_shadow',self.self_shadow)):
            check=PixelCheck(self.display_options,text=text,variable=var,command=lambda k=key,v=var:self.toggle_render_flag(k,v));check.pack(side='left');self.render_flag_checks[key]=check
        self.button(self.display_options,'边线颜色',self.choose_outline_color).pack(side='left')
        self.button(self.display_options,'光照设置…',lambda:self.edit_render_options('lighting')).pack(side='left')
        camera=FlowBar(center,compact=True,bg=BG);camera.pack(fill='x',pady=(0,6))
        direction=tk.Frame(camera,bg=BG);direction.pack(side='left')
        self.label(direction,'角色朝向',bg=BG,fg=DIM).pack(side='left',padx=(0,4))
        self.yaw=tk.StringVar(value=str(int(self.project.get('yaw',0))));PixelOption(direction,self.yaw,*[str(v) for v in sorted(set(range(0,360,30))|set(range(0,360,45)))],command=self.turn).pack(side='left')
        framing=tk.Frame(camera,bg=BG);framing.pack(side='left')
        self.label(framing,'取景上下（px）',bg=BG,fg=DIM).pack(side='left',padx=(10,4))
        self.camera_y=tk.StringVar(value=str(int(self.project.get('camera_y',0))))
        self.camera_entry=PixelEntry(framing,textvariable=self.camera_y,width=4,bg=FIELD);self.camera_entry.pack(side='left')
        self.camera_entry.field.bind('<Return>',self.set_camera_y);self.camera_entry.field.bind('<FocusOut>',self.set_camera_y)
        self.export_view=tk.StringVar(value='焦点视图')
        self.ab.bind('<ButtonPress-1>',lambda e:self.ab_view(True));self.ab.bind('<ButtonRelease-1>',lambda e:self.ab_view(False));self.ab.bind('<Leave>',lambda e:self.ab_view(False))
        self.canvas=tk.Canvas(center,bg=CELL,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',self.resize_preview);self.canvas.bind('<ButtonPress-1>',self.start_drag);self.canvas.bind('<B1-Motion>',self.move_drag);self.canvas.bind('<ButtonRelease-1>',self.end_drag)
        bar=FlowBar(center,compact=True,bg=BG);bar.pack(fill='x',pady=8)
        self.playbtn=self.button(bar,'▶ 播放',self.play,True);self.playbtn.pack(side='left')
        self.button(bar,'◀',lambda:self.step(-1)).pack(side='left',padx=5);self.button(bar,'▶',lambda:self.step(1)).pack(side='left')
        self.time_label=tk.StringVar();count_group=tk.Frame(bar,bg=BG);count_group.pack(side='left');self.label(count_group,'总帧数',bg=BG).pack(side='left',padx=(12,4))
        self.seconds=tk.StringVar(value=str(self.project.get('seconds',2)))
        self.frame_count=tk.StringVar(value=str(max(1,min(120,round(self.project.get('seconds',2)*self.project.get('fps',12))))))
        self.frame_entry=PixelEntry(count_group,textvariable=self.frame_count,width=4,bg=FIELD);self.frame_entry.pack(side='left')
        self.frame_entry.field.bind('<Return>',self.set_frame_count);self.frame_entry.field.bind('<FocusOut>',self.set_frame_count)
        fps_group=tk.Frame(bar,bg=BG);fps_group.pack(side='left');self.label(fps_group,'FPS',bg=BG).pack(side='left',padx=(8,4))
        self.fps_value=tk.StringVar(value=str(self.project.get('fps',12)))
        PixelOption(fps_group,self.fps_value,*map(str,(6,8,10,12,15,20,24,30,60)),command=self.set_fps).pack(side='left')
        UI.Label(bar,textvariable=self.time_label,bg=BG,fg=DIM).pack(side='right')
        self.scrub=PixelScale(center,from_=0,to=1000,showvalue=False,orient='horizontal',bd=0,highlightthickness=0,bg=BG,troughcolor=FIELD,command=self.seek);self.scrub.pack(fill='x')
        right_shell=tk.Frame(body,bg=PANEL);self.right=right_shell;body.add(right_shell,minsize=240,width=round(400*self.ui_scale),stretch='never')
        self.right_scroll=ScrollPanel(right_shell);self.right_scroll.pack(fill='both',expand=True);right=self.right_scroll.content
        self.param_title=tk.StringVar();UI.Label(right,textvariable=self.param_title,fg=INK,anchor='w',wraplength=360).pack(fill='x',padx=12,pady=12)
        self.params=tk.Frame(right,bg=PANEL);self.params.pack(fill='x')
        self.param_canvas=self.right_scroll.canvas
        self.bind('<MouseWheel>',self.scroll_params)
        self.status=tk.StringVar(value='选择部位调整整段动作；暂停后拖动手脚，四个视图同步。')
        self.status_label=UI.Label(self,textvariable=self.status,anchor='w',fg=DIM,bg=BG,font=self.caption_font,wrap=True)
        self.status_label.pack(fill='x',padx=12,pady=6)

    def zoom(self,delta):
        self.ui_scale=max(.75,min(2.0,self.ui_scale+delta))
        self.preferred_ui_scale=self.ui_scale
        self._adapt_size=(self.winfo_width(),self.winfo_height())
        self.ui_font.configure(size=-round(24*self.ui_scale))
        self.caption_font.configure(size=-round(18*self.ui_scale))
        self.save_preferences()
        self.restore_panel_widths()
        self.refresh_control_styles()
        self.render()

    def queue_adapt_layout(self,event):
        if event.widget is not self:return
        size=(event.width,event.height)
        if min(size)<100 or size==self._adapt_size:return
        if self.adapt_job:self.after_cancel(self.adapt_job)
        self.adapt_job=self.after(180,lambda:self.adapt_layout(*size))

    def adapt_layout(self,width,height):
        from ui_layout import fitted_scale
        self.adapt_job=None;self._adapt_size=(width,height)
        scale=fitted_scale(self.preferred_ui_scale,width,height)
        if abs(scale-self.ui_scale)>.01:
            self.ui_scale=scale
            self.ui_font.configure(size=-round(24*scale));self.caption_font.configure(size=-round(18*scale))
            self.refresh_control_styles()
        self.fit_panels(self.panes.winfo_width())

    def restore_panel_widths(self):
        if not hasattr(self,'panes'):return
        self.panes.paneconfigure(self.left,width=round(self.panel_widths[0]*self.ui_scale))
        self.panes.paneconfigure(self.right,width=round(self.panel_widths[1]*self.ui_scale))
        self.after_idle(lambda:self.fit_panels(self.panes.winfo_width()))
    def fit_panels(self,width):
        if not hasattr(self,'right') or width<600:return
        from ui_layout import panel_sizes
        left,right,left_min,right_min=panel_sizes(width,self.ui_scale,self.panel_widths)
        for pane,size,minimum in ((self.left,left,left_min),(self.right,right,right_min)):
            if (int(self.panes.panecget(pane,'width')),int(self.panes.panecget(pane,'minsize')))!=(size,minimum):
                self.panes.paneconfigure(pane,width=size,minsize=minimum)
    def remember_panel_widths(self):
        if not self.left.winfo_exists():return
        self.panel_widths=[self.left.winfo_width()/self.ui_scale,self.right.winfo_width()/self.ui_scale];self.save_preferences()

    def save_preferences(self):
        self.preferences_path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.preferences_path.with_suffix('.tmp');tmp.write_text(json.dumps({'scale':self.preferred_ui_scale,'export_directory':self.export_directory,'painting_directory':self.paint_directory,'painting_bindings':self.paint_bindings,'language':self.language,'panels':self.panel_widths,'render':self.current_display()}),encoding='utf-8');tmp.replace(self.preferences_path)
    def refresh_control_styles(self):
        def visit(widget):
            if hasattr(widget,'refresh_style'):widget.refresh_style()
            if isinstance(widget,(tk.Button,tk.Menubutton)):
                widget.configure(padx=round(10*self.ui_scale),pady=round(6*self.ui_scale),highlightthickness=max(1,round(2*self.ui_scale)))
            for child in widget.winfo_children():visit(child)
        visit(self)
    def set_language(self,label):
        code=next((k for k,v in i18n.LANGUAGES.items() if v==label),label)
        if code not in i18n.LANGUAGES:return
        was_playing=self.playing;self.stop();self.language=code;i18n.set_language(code)
        self.save_preferences()
        if self.resize_job:self.after_cancel(self.resize_job);self.resize_job=None
        for child in list(self.winfo_children()):child.destroy()
        self.resizing=False;self._build();self.refresh_lists();self.show_params();self.refresh_control_styles()
        self.restore_panel_widths()
        self.title(tr('FellowStudio · 动作工坊'));self.layout_key=None;self.render()
        if was_playing:self.play()

    def scroll_params(self,event):
        widget=self.winfo_containing(event.x_root,event.y_root)
        while widget is not None:
            if isinstance(widget,ScrollPanel):return widget.wheel(event)
            widget=getattr(widget,'master',None)

    def snapshot(self):
        self.history.append(copy.deepcopy(self.project));self.history=self.history[-60:];self.future.clear()
    def undo(self,redo=False):
        src,dst=(self.future,self.history) if redo else (self.history,self.future)
        if not src:return
        dst.append(copy.deepcopy(self.project));self.project=src.pop();self.sync();self.changed()
    def toggle_display_options(self):
        self.display_options_shown=not self.display_options_shown
        if self.display_options_shown:self.display_options.pack(fill='x',pady=(0,6),after=self.viewbar)
        else:self.display_options.pack_forget()
        self.display_options_button.configure(text='收起显示选项' if self.display_options_shown else '显示选项…')
    def current_display(self):
        if hasattr(self,'parts'):
            result={**self.project.get('render',{}),**dict(parts=self.parts.get(),textures=self.textures.get(),gaps=self.gaps.get(),outline=self.outline.get(),perfect=True)}
            if self.outline_color.get()!='auto':result['outline_color']=self.outline_color.get()
            else:result.pop('outline_color',None)
            return result
        return copy.deepcopy(self.project.get('render',{}))

    def sync(self,selection=None):
        # Restored/opened project values are authoritative; old checkboxes must not overwrite them.
        self.project.setdefault('render',{})
        self.name.set(self.project['name']);self.seconds.set(str(self.project['seconds']));self.yaw.set(str(int(self.project.get('yaw',0))))
        self.parts.set(self.project['render'].get('parts',True));self.gaps.set(self.project['render'].get('gaps',True));self.outline.set(self.project['render'].get('outline',True));self.selection=selection or ('body','arms');self.refresh_lists();self.show_params()
        self.textures.set(self.project['render'].get('textures',True));self.outline_color.set(self.project['render'].get('outline_color','auto'))
        self.frame_count.set(str(max(1,min(120,round(self.project['seconds']*self.project.get('fps',12))))));self.fps_value.set(str(self.project.get('fps',12)))
        self.camera_y.set(str(int(self.project.get('camera_y',0))))
        self.sync_render_flags()
        for dialog in getattr(self,'render_settings_editors',{}).values():dialog.refresh()
    def rename(self):
        self.project['name']=self.name.get()
        if self.project.get('auto_name_key') and self.project['name']!=E.automatic_name(self.project['auto_name_key']):self.project.pop('auto_name_key',None)
        self.schedule_save()
    def schedule_save(self):
        if self.save_job:self.after_cancel(self.save_job)
        self.save_job=self.after(900,self.autosave)
    def autosave(self):
        self.save_job=None
        if self.load_error:return
        try:E.save(self.project,self.state_path)
        except OSError as ex:self.status.set('保存失败：'+str(ex))
    def changed(self):
        if hasattr(self,'part_buttons') and 'hair' in self.part_buttons:
            button=self.part_buttons['hair']
            if any(p.get('kind')=='hair' for p in (self.project.get('model') or {}).get('attachments',[])):button.grid()
            else:button.grid_remove()
        if hasattr(self,'part_buttons') and 'tail' in self.part_buttons:
            button=self.part_buttons['tail']
            if any(p.get('kind')=='tail' for p in (self.project.get('model') or {}).get('attachments',[])):button.grid()
            else:button.grid_remove()
        self.schedule_save()
        if self.pending:self.after_cancel(self.pending)
        self.revision+=1;self.pending=self.after(100,self.request_preview)
    def request_preview(self):
        self.pending=None;self.latest_request=(self.revision,copy.deepcopy(self.project))
        self.epoch+=1
        self.submit_latest()
    def submit_latest(self):
        if self.future_job is not None or self.latest_request is None:return
        revision,project=self.latest_request;self.latest_request=None
        if self.executor is None:self.executor=ProcessPoolExecutor(max_workers=1)
        self.future_job=(revision,project,self.executor.submit(compile_preview,project))
        self.status.set('正在更新动作… 可继续调整')
        self.after(20,self.poll_preview)
    def poll_preview(self):
        if self.future_job is None:return
        revision,project,future=self.future_job
        if not future.done():self.after(20,self.poll_preview);return
        self.future_job=None
        try:
            seq,images=future.result()
            if revision==self.revision:
                self.seq=seq;self.raw_images=images;self.active_project=project;self.photos.clear();self.layout_key=None;self.frame%=len(seq);self.render()
                if self.playing:self.started=time.perf_counter()-self.frame/project['fps']
                self.status.set('动作已更新 · 点击视图切换焦点，导出默认跟随焦点')
        except Exception as ex:self.status.set('预览更新失败：'+str(ex))
        self.submit_latest()
    def rebuild(self):
        self.pending=None;self.seq,self.raw_images=compile_preview(self.project);self.active_project=copy.deepcopy(self.project)
        self.photos.clear();self.layout_key=None;self.frame%=len(self.seq);self.render();self.epoch+=1
    def warm(self,epoch,index):
        return
    def fit_window(self):
        try:
            from ctypes import wintypes
            rect=wintypes.RECT();ctypes.windll.user32.SystemParametersInfoW(48,0,ctypes.byref(rect),0)
            x,y,w,h=rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top
        except (AttributeError,OSError):x,y,w,h=0,0,self.winfo_screenwidth(),self.winfo_screenheight()
        width=min(w-24,max(1400,round(w*.92)));height=min(h-50,max(900,round(h*.9)))
        if sys.platform=='darwin':height=min(height,h-110)  # Menu bar, title bar and Dock.
        self.minsize(min(820,width),min(560,height))
        self.geometry(f'{width}x{height}+{x+(w-width)//2}+{y+max(0,(h-height-32)//2)}')
        return width,height
    def resize_preview(self,event):
        self.resizing=True
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(130,self.finish_resize)
    def finish_resize(self):
        self.resize_job=None;self.resizing=False;self.render()
    def update_layer_actions(self):
        index=self.selection[1] if self.selection[0]=='layer' else -1;count=len(self.project['layers'])
        for text,enabled in (('上移',0<index<count),('下移',0<=index<count-1),('移除',0<=index<count)):
            if hasattr(self,'layer_actions'):self.layer_actions[text].configure(state='normal' if enabled else 'disabled')
    def move_layer(self,delta):
        if self.selection[0]!='layer':return
        i=self.selection[1];j=i+delta
        if not 0<=j<len(self.project['layers']):return
        self.snapshot();items=self.project['layers'];items[i],items[j]=items[j],items[i];self.selection=('layer',j)
        self.refresh_lists();self.show_params();self.changed()
    def refresh_lists(self):
        self.base_name.set('自选姿势' if 'pose' in self.project else E.ACTIONS[self.project['base']['kind']]);self.stack.delete(0,'end')
        for e in self.project['layers']:self.stack.insert('end',tr(('● ' if e.get('enabled',True) else '○ ')+E.ACTIONS[e['kind']]))
        if self.selection[0]=='layer' and self.selection[1]<len(self.project['layers']):self.stack.selection_set(self.selection[1]);self.stack.see(self.selection[1])
        self.update_layer_actions()
    def select(self,kind,key):
        self.selection=(kind,key);self.update_layer_actions()
        for part,button in self.part_buttons.items():button.accent=(kind=='body' and part==key);button.draw()
        self.show_params();self.right_scroll.canvas.yview_moveto(0);self.render()
    def pick_layer(self,event=None):
        if self.stack.curselection():self.select('layer',self.stack.curselection()[0])
    def add(self,kind):
        self.snapshot();e=E.entry(kind)
        if kind=='raise':e['scope']='armR'
        if kind=='pose':
            import motion_resources as MR
            e['pose']=MR.pose_channels(self.seq[self.frame]);e['scope']='upper'
        self.project['layers'].append(e);self.selection=('layer',len(self.project['layers'])-1);self.refresh_lists();self.show_params();self.changed()
    def load_motion_resource(self):
        import resource_browser
        return resource_browser.show(self)
    def arrange_actions(self):
        import action_sequence
        return action_sequence.show(self)
    def save_motion_resource(self):
        import motion_resources as MR
        folder=self.state_path.parent/'motions';folder.mkdir(parents=True,exist_ok=True)
        path=filedialog.asksaveasfilename(parent=self,title=tr('保存动画'),initialdir=folder,initialfile='MyMotion.json',defaultextension='.json',filetypes=[(tr('动作配方'),'*.json')])
        if not path:return
        try:MR.save_motion(self.project,path);self.status.set('已保存：'+str(path))
        except Exception as ex:messagebox.showerror(tr('保存失败'),str(ex),parent=self)
    def edit_pose_animation(self):
        if getattr(self,'pose_editor',None) is not None and self.pose_editor.winfo_exists():self.pose_editor.lift();return self.pose_editor
        self.stop()
        from pose_animation_editor import PoseAnimationEditor
        self.pose_editor=PoseAnimationEditor(self)
        return self.pose_editor
    def pose_resource(self,e,action):
        import motion_resources as MR
        try:
            if action=='capture':pose=MR.pose_channels(self.seq[self.frame])
            elif action=='load':
                path=filedialog.askopenfilename(parent=self,initialdir=E.ROOT/'examples'/'poses',filetypes=[(tr('姿势层'),'*.json')])
                if not path:return
                pose=MR.load_pose(path)
            else:
                path=filedialog.asksaveasfilename(parent=self,defaultextension='.json',initialfile='Pose.json',filetypes=[(tr('姿势层'),'*.json')])
                if path:MR.save_pose(e.get('pose',{}),path)
                return
            self.snapshot();e['pose']=pose;self.show_params();self.changed()
        except Exception as ex:messagebox.showerror(tr('姿势层'),str(ex),parent=self)
    def remove(self):
        if self.selection[0]!='layer':return
        self.snapshot();self.project['layers'].pop(self.selection[1]);self.selection=('body','arms');self.refresh_lists();self.show_params();self.changed()
    def change_base(self,value):
        kind=next(k for k,v in E.ACTIONS.items() if v==value);self.snapshot();self.stop();self.project=self.make_project(kind);self.frame=0;self.sync(('base',0));self.changed()
    def edit_model(self):
        if self.model_editor is not None and self.model_editor.winfo_exists():self.model_editor.lift();return
        self.stop();self.render()
        from model_editor import ModelEditor
        self.model_editor=ModelEditor(self)

    def choose_pose(self):
        w=tk.Toplevel(self);w.title(tr('选择基础姿势'));w.transient(self)
        for i,(name,key) in enumerate(E.POSES.items()):
            def choose(key=key,name=name):
                self.snapshot();self.project['pose']=E.norm(E.F.POSES[key]);self.project['base']=E.entry('stand');self.project['layers']=[];self.project['controls']={};self.project['physics']={};self.project['name']=E.automatic_name(name);self.project['auto_name_key']=name;self.sync();self.changed();w.destroy()
            self.button(w,name,choose).grid(row=i//3,column=i%3,padx=8,pady=8,sticky='ew')
    def slide(self,label,obj,key,lo,hi,default=0,step=1,onchange=None):
        f=tk.Frame(self.params);f.pack(fill='x',padx=12,pady=5)
        value=tk.StringVar(value=f'{obj.get(key,default):g}');f.columnconfigure(0,weight=1);self.label(f,label,wrap=True,justify='left').grid(row=0,column=0,sticky='ew',padx=(0,8));UI.Label(f,textvariable=value,fg=DIM,width=6,anchor='e').grid(row=0,column=1,sticky='ne')
        s=PixelScale(self.params,from_=lo,to=hi,resolution=step,orient='horizontal',showvalue=False,bd=0,highlightthickness=0,troughcolor=FIELD,activebackground=ACC)
        s.set(obj.get(key,default));s.pack(fill='x',padx=12)
        s.bind('<ButtonPress-1>',lambda e:self.snapshot(),add='+')
        s.bind('<KeyPress>',lambda e:self.snapshot(),add='+')
        def update(v):
            number=float(v)
            if key=='start' and 'end' in obj:number=min(number,obj['end']-.025)
            if key=='end':number=max(number,obj.get('start',0)+.025)
            if number!=float(v):s.set(number)
            obj[key]=number;value.set(f'{number:g}')
            if onchange:onchange()
            self.changed()
        s.configure(command=update)
    def note(self,text):self.label(self.params,text,fg=DIM,font=self.caption_font,justify='left',wrap=True).pack(fill='x',padx=12,pady=8)
    def choice(self,label,obj,key,options):
        self.note(label);reverse={v:k for k,v in options.items()};v=tk.StringVar(value=options.get(obj.get(key),next(iter(options.values()))))
        def change(x):self.snapshot();obj[key]=reverse[x];self.changed();self.after_idle(self.show_params)
        PixelOption(self.params,v,*options.values(),command=change).pack(fill='x',padx=12)
    def show_params(self):
        for c in self.params.winfo_children():c.destroy()
        kind,key=self.selection
        if kind in ('base','layer'):
            if kind=='layer' and key>=len(self.project['layers']):return
            e=self.project['base'] if kind=='base' else self.project['layers'][key];C=E.L.KINDS[e['kind']]
            self.param_title.set(('基础 · ' if kind=='base' else '叠加 · ')+C.label)
            self.choice('播放方式',self.project if kind=='base' else e,'playback' if kind=='base' else 'mode',{'loop':'循环','once':'播放一次','hold':'保持末帧'})
            if e['kind']=='roll':self.choice('接触方式',e,'contact',{'auto':'跟随基础动作','ground':'地面翻滚','air':'空中翻滚'})
            if e['kind']=='kick':self.choice('踢腿方式',e,'style',{'swing':'摆踢','push':'踹腿'})
            if e['kind']=='swim':self.choice('游泳方式',e,'style',{'breast':'蛙泳','crawl':'自由泳','tread':'踩水'})
            if e['kind'] in ('swim','hover'):self.note('不锁定地面；可叠加头部、挥手或脱力。')
            if e['kind']=='poseclip':self.button(self.params,'编辑姿势卡…',self.edit_pose_animation).pack(fill='x',padx=12,pady=6)
            if e['kind']=='raise':self.choice('举手方向',e,'plane',{'side':'向两侧','front':'向前'})
            if e['kind']=='lift':self.choice('取放方向',e,'operation',{'pickup':'从地上捧起','putdown':'放回地面'})
            if e['kind']=='lift':self.note('高举时手肘会逐渐伸直；取物下蹲会按模型比例适配。')
            if e['kind']=='bow':self.note('负值后仰，正值弯腰。')
            if e['kind']=='squat':self.note('双腿开合：负值内收，正值外展。')
            if e['kind']=='pose':
                for label,action in (('载入姿势…','load'),('保存姿势…','save'),('使用当前帧姿势','capture')):
                    self.button(self.params,label,lambda action=action:self.pose_resource(e,action)).pack(fill='x',padx=12,pady=4)
                if e.get('scope','all') in ('all','lower','legs'):
                    self.pose_ground=tk.BooleanVar(master=self,value=e.get('ground',False))
                    def ground_changed():self.snapshot();e['ground']=self.pose_ground.get();self.changed()
                    PixelCheck(self.params,text='保持地面接触',variable=self.pose_ground,command=ground_changed).pack(fill='x',padx=12,pady=6)
            if getattr(C,'unilateral',False):
                self.choice('动作侧',e,'side',{'right':'右侧','left':'左侧','both':'双侧'})
                if e.get('side')=='both':self.choice('双侧配合',e,'alternating',{False:'同步',True:'交替'})
            if e['kind']=='wave':
                # Legacy scope=armL was a broken filter; make it a true mirrored action.
                e.setdefault('side',{'armL':'left','arms':'both'}.get(e.get('scope'),'right'))
                if e.get('scope') in ('armL','armR','arms'):e['scope']='all'
                self.choice('挥手部位',e,'side',{'right':'右臂','left':'左臂','both':'双臂'})
                if e.get('side')=='both':self.choice('双侧配合',e,'alternating',{False:'同步',True:'交替'})
            if kind=='layer':
                e.setdefault('blend','posture' if e['kind'] in ('raise','wave') else 'add')
                self.button(self.params,'暂时关闭' if e.get('enabled',True) else '启用动作',lambda:self.toggle_layer(e)).pack(fill='x',padx=12)
                self.slide('影响比例',e,'mix',0,1,1,.05)
                if e.get('blend') in ('posture','replace'):
                    self.slide('保留原摆动',e,'retain',0,1,1,.05)
                if e['kind'] not in ('tail','hair'):self.choice('作用部位',e,'scope',{'all':'相关部位','upper':'上半身','lower':'下半身','head':'头颈','hair':'头发','torso':'腰 / 躯干','armL':'左臂','armR':'右臂','arms':'双臂','legs':'双腿','legL':'左腿','legR':'右腿'})
                self.note('叠加选定部位的改动，原动画保留。' if e.get('blend')=='add' else '姿态和摆动分别混合。比例为 0 时完全回到原动作。')
                if e['kind'] in ('thrust','swing','kick'):self.note('需要完整身体带动时，将作用部位设为“相关部位”。')
            for d in C.params:
                if e['kind']=='swim' and d['key']=='roll' and e.get('style','breast')!='crawl':continue
                if not d.get('hide'):self.slide(d['label'],e['params'],d['key'],d['lo'],d['hi'],d['dflt'],d['step'])
            if e['kind'] not in ('raise','pose') and (E.MT.mode(self.project) if kind=='base' else e.get('mode',E.MT.mode(self.project)))=='loop':self.slide('这一轮做几次',e,'cycles',1,8,1,1)
            if kind=='layer':
                self.button(self.params,'时间与融合设置',self.toggle_motion_details).pack(fill='x',padx=12,pady=6)
                if getattr(self,'motion_details',False):
                    self.choice('融合方式',e,'blend',{'posture':'姿态与摆动','replace':'替换选中部位','add':'叠加变化'})
                    start,span=E.MT.interval(e);timing=dict(start=min(.95,start),end=max(.025,min(1,start+span)))
                    def timing_changed():e.update(timing);e.pop('span',None)
                    self.slide('开始位置',timing,'start',0,.95,0,.025,onchange=timing_changed)
                    self.slide('结束位置',timing,'end',.025,1,1,.025,onchange=timing_changed)
                    self.slide('淡入淡出',e,'fade',0,.4,0,.025)
            self.note('直接调动作的整体感觉，不需要编辑关键帧。')
        else:
            self.param_title.set('整体控制 · '+E.LABELS[key]);c=self.project['controls'].get(key,{}) if key=='hair' else self.project['controls'].setdefault(key,{})
            if key=='hair':
                import hair_controls
                hair_controls.mount(self,c)
            elif key=='tail':
                bones={'尾根':'root','尾中':'middle','尾尖':'tip'}
                selected=getattr(self,'selected_tail_bone','尾根')
                value=tk.StringVar(master=self,value=selected)
                def pick_bone(label):self.selected_tail_bone=label;self.show_params();self.render()
                PixelOption(self.params,value,*bones,command=pick_bone).pack(fill='x',padx=12,pady=8)
                for axis,label in (('pitch','上下弯曲（度）'),('yaw','左右弯曲（度）'),('roll','扭转（度）')):self.slide(label,c,bones[selected]+'_'+axis,-120,120,0,1)
                self.slide('摆动幅度',c,'range',-2,2,1,.05)
                self.note('尾根、尾中、尾尖分别控制；可叠加尾巴摆动，并使用影响比例、时段与融合方式。')
            elif key in ('head','torso'):
                if key=='head':
                    self.slide('低头 / 抬头',c,'nod',-65,65);self.slide('左右转头',c,'turn',-90,90);self.slide('左右歪头',c,'tilt',-45,45);self.slide('头部前后位置（px）',c,'depth',-8,8,0,.25)
                    follow=tk.BooleanVar(value=c.get('follow_chest',True));self.head_follow_var=follow
                    def follow_changed():self.snapshot();c['follow_chest']=follow.get();self.changed()
                    PixelCheck(self.params,text='跟随胸腔转动',variable=follow,command=follow_changed).pack(fill='x',padx=12,pady=8)
                else:
                    self.slide('整体朝向',self.project,'yaw',0,360,0,1,onchange=lambda:self.yaw.set(str(int(self.project.get('yaw',0)))))
                    self.slide('弯腰 / 后仰',c,'lean',-40,70);self.slide('身体高低',c,'height',-8,8,0,.25);self.slide('左右倾斜',c,'tilt',-30,30);self.slide('胸腔转向',c,'turn',-60,60);self.slide('骨盆转向',c,'hips_turn',-45,45)
                    self.note('整体朝向转动全身；胸腔和骨盆分别扭转。锁脚时脚的位置保持。')
                if key=='torso':
                    pin=tk.BooleanVar(value=c.get('pin_feet',True));self.pin_var=pin
                    def pin_changed():self.snapshot();c['pin_feet']=pin.get();self.changed()
                    PixelCheck(self.params,text='调整身体时保持脚的位置',variable=pin,command=pin_changed).pack(fill='x',padx=10,pady=8)
                    self.note('脚部锁定受腿长限制；小幅调整身体高低时更自然。')
            elif key!='tail':
                self.slide('抬起 / 放下',c,'raise',-90,160);self.slide('前伸 / 后摆',c,'forward',-90,90)
                self.slide('侧向弯曲',c,'bend',-100,100);self.slide('前后屈伸',c,'fold',-135,135)
                self.slide('摆动幅度',c,'range',-2,2,1,.05)
                self.note('摆动幅度为负值时，围绕原姿态反向摆动。')
                self.note('摆幅围绕动作的平均姿势变化；抬起手臂也会保留原来的摆动。')
                if key in E.LIMBS:
                    self.button(self.params,'翻转肘 / 膝弯向',lambda:self.reverse_bend(key)).pack(fill='x',padx=12,pady=6)
            self.button(self.params,'重置这个部位',lambda:self.reset_part(key)).pack(fill='x',padx=12,pady=8)
            if key in E.LIMBS or key in ('head','tail'):
                phy=self.project['physics'].setdefault(key,{})
                self.note('物理跟随 · 随身体运动产生惯性')
                if key=='tail':
                    for bone,label in (('root','尾根松软'),('middle','尾中松软'),('tip','尾尖松软')):
                        self.slide(label,phy,bone,0,1,phy.get('strength',0),.05)
                elif key in E.LIMBS:
                    self.slide('上段松软',phy,'upper',0,1,phy.get('strength',0),.05)
                    self.slide('下段松软',phy,'lower',0,1,phy.get('strength',0),.05)
                else:self.slide('头颈松软',phy,'strength',0,1,0,.05)
                self.slide('回弹',phy,'bounce',0,1,.4,.05)
                self.note('先用较小松软程度。强度为 0 时恢复原动作，导出与预览使用同一模拟结果。')
            elif key in ('arms','legs','body'):self.note('物理跟随请选左 / 右单个部位设置。')
    def toggle_motion_details(self):self.motion_details=not getattr(self,'motion_details',False);self.show_params()
    def reverse_bend(self,key):
        self.snapshot();p=self.seq[self.frame];c=self.project['controls'].setdefault(key,{});o=c.setdefault('offset',[0,0,0,0]);o[1]-=2*p[key][1];o[3]-=2*p[key][3];self.changed()
    def toggle_layer(self,e):
        self.snapshot();e['enabled']=not e.get('enabled',True);self.refresh_lists();self.show_params();self.changed()
    def reset_part(self,key):
        self.snapshot();self.project['controls'].pop(key,None);self.project['physics'].pop(key,None);self.show_params();self.changed()
    def display(self):
        self.snapshot();self.project['render']=self.current_display();self.save_preferences();self.changed()
    def choose_outline_color(self):
        from outline_color import OutlineColorDialog
        return OutlineColorDialog(self)
    def sync_render_flags(self):
        settings=O.normalized(self.project.get('render'))
        self.light_enabled.set(settings['lighting']);self.self_shadow.set(settings['self_shadow']);self.retro_animation.set(settings['retro_animation'])
    def toggle_render_flag(self,key,var):
        self.snapshot();settings=self.project.setdefault('render',{});settings.setdefault('self_shadow',self.self_shadow.get());settings[key]=var.get();self.save_preferences();self.changed()
    def edit_render_options(self,section='canvas'):
        if not hasattr(self,'render_settings_editors'):self.render_settings_editors={}
        if section in self.render_settings_editors:self.render_settings_editors[section].lift();return self.render_settings_editors[section]
        from render_options_editor import RenderOptionsEditor
        return RenderOptionsEditor(self,section)
    def duration(self,v):self.snapshot();self.project['seconds']=float(v);self.changed()
    def set_frame_count(self,event=None):
        old=max(1,min(120,round(self.project['seconds']*self.project.get('fps',12))))
        try:value=int(self.frame_count.get());assert 1<=value<=120
        except (ValueError,AssertionError):self.frame_count.set(str(old));return
        if value==old:return
        self.snapshot();self.stop();self.project['seconds']=value/self.project.get('fps',12);self.seconds.set(str(self.project['seconds']));self.frame=0;self.changed()
    def set_fps(self,value):
        count=max(1,min(120,round(self.project['seconds']*self.project.get('fps',12))))
        self.snapshot();self.stop();self.project['fps']=int(value);self.project['seconds']=count/int(value);self.seconds.set(str(self.project['seconds']));self.frame=0;self.changed()
    def set_camera_y(self,event=None):
        old=int(self.project.get('camera_y',0))
        try:value=int(self.camera_y.get());assert -256<=value<=256
        except (ValueError,AssertionError):self.camera_y.set(str(old));return
        if value==old:return
        self.snapshot();self.project['camera_y']=value;self.changed()
    def turn(self,v):self.snapshot();self.project['yaw']=float(v);self.changed()
    def photo(self,v,i):
        size=self.cells[v][2];key=(v,i,size,self.compare)
        if key not in self.photos:
            seq=self.base_seq if self.compare else self.seq
            a=self.raw_images.get((v,i)) if not self.compare else None
            if a is None and not self.compare and getattr(self,'preview_incomplete',False):
                available=[f for view,f in self.raw_images if view==v]
                if available:a=self.raw_images[v,min(available,key=lambda f:abs(f-i))]
                else:return None
            if a is None:a=E.rgba(seq[i%len(seq)],self.active_project['render'],VIEWS[v])
            image=Image.fromarray(a);target=(size,round(size*image.height/image.width))
            source=ImageTk.PhotoImage(image.resize(target,Image.Resampling.NEAREST),master=self);self.photos[key]=source
            while len(self.photos)>8 and sum(k[2]*k[2]*4 for k in self.photos)>96*1024*1024:self.photos.pop(next(iter(self.photos)))
        return self.photos[key]
    def render(self):
        if not self.seq or self.resizing:return
        position=self.frame/max(1,len(self.seq)-1)*1000
        if abs(self.scrub.get()-position)>.1:self.scrub.set(position)
        w,h=self.canvas.winfo_width(),self.canvas.winfo_height()
        settings=self.active_project.get('render');size,cell_height=O.fit(w/2,(h-44)/2,settings);x=(w-size*2)//2;y=(h-cell_height*2)//2
        self.cells=[(x+(v%2)*size,y+(v//2)*cell_height,size) for v in range(4)]
        layout_key=(w,h,size,self.handles.get(),self.compare,self.focus_view,self.playing)
        if self.playing and getattr(self,'layout_key',None)==layout_key and hasattr(self,'image_items'):
            for v,item in enumerate(self.image_items):self.canvas.itemconfigure(item,image=self.photo(v,self.frame))
            self.time_label.set(f'{self.frame/self.project.get("fps",12):.2f} / {self.project["seconds"]:g}'+tr(' 秒'))
            return
        self.layout_key=layout_key;self.canvas.delete('all');self.refs=[];self.image_items=[]
        for v,(x,y,size) in enumerate(self.cells):
            im=self.photo(v,self.frame);self.refs.append(im);self.image_items.append(self.canvas.create_image(x,y,anchor='nw',image=im))
            self.canvas.create_rectangle(x,y,x+size,y+cell_height,outline=ACC if v==self.focus_view else '#776554',width=3 if v==self.focus_view else 1);self.canvas.create_text(x+10,y+12,text=tr(VN[v])+((' · '+tr('焦点')) if v==self.focus_view and size>=256 else (' *' if v==self.focus_view else '')),anchor='nw',width=max(40,size-20),fill=ACC if v==self.focus_view else '#d7c5ac',font=self.caption_font)
            if self.handles.get() and not self.playing and not self.compare:
                p=self.view_pose(v);j=O.joints(p,settings);scale=size/O.size(settings)[0]
                for key in E.LIMBS:
                    selected=self.selection==('body',key);color='#f2b95c' if selected else '#b7ac99'
                    points=[j[key][q] for q in ('root','mid','tip')]
                    if selected:self.canvas.create_line(*[a for pt in points for a in (x+pt[0]*scale,y+pt[1]*scale)],fill=color,dash=(3,3))
                    for joint in ('mid','tip'):
                        px,py=j[key][joint];cx,cy=x+px*scale,y+py*scale;r=4 if joint=='mid' else 5
                        self.canvas.create_rectangle(cx-r,cy-r,cx+r,cy+r,outline=color,fill=CELL)
                pts=[j[k]['tip'] for k in ('waist','torso','neck','head')]
                self.canvas.create_line(*[a for pt in pts for a in (x+pt[0]*scale,y+pt[1]*scale)],fill='#b7ac99',width=2)
                for key in ('waist','torso','head'):
                    px,py=j[key]['tip'];cx,cy=x+px*scale,y+py*scale
                    color=ACC if self.selection==('body','torso' if key=='waist' else key) else '#b7ac99'
                    self.canvas.create_rectangle(cx-5,cy-5,cx+5,cy+5,outline=color,fill=CELL,width=2)
                if self.selection==('body','tail'):
                    tail=self.tail_points(v)
                    if tail:
                        points=[(x+px*scale,y+py*scale) for px,py in tail]
                        self.canvas.create_line(*[value for point in points for value in point],fill=ACC,width=2)
                        active={'尾根':0,'尾中':1,'尾尖':2}.get(getattr(self,'selected_tail_bone','尾根'),0)
                        for index,(px,py) in enumerate(points[:3]):self.canvas.create_oval(px-6,py-6,px+6,py+6,fill=ACC if index==active else CELL,outline=ACC,width=2)
                if self.selection==('body','hair'):
                    import hair_controls
                    points=[(x+px*scale,y+py*scale) for px,py in hair_controls.points(self,v)]
                    if points:
                        self.canvas.create_line(*[a for p in points for a in p],fill=ACC,width=2)
                        for index,(px,py) in enumerate(points[:3]):self.canvas.create_oval(px-5,py-5,px+5,py+5,fill=ACC if index==getattr(self,'hair_bone',0) else CELL,outline=ACC,width=2)
        self.time_label.set(f'{self.frame/self.project.get("fps",12):.2f} / {self.project["seconds"]:g}'+tr(' 秒'))
    def view_pose(self,v):
        p=copy.deepcopy(self.seq[self.frame]);p['yaw']+=VIEWS[v][0];p['pitch']+=VIEWS[v][1];return p
    def tail_points(self,view):
        import tails
        pose=self.view_pose(view);model=pose.get('_model') or {}
        item=next((p for p in model.get('attachments',[]) if p.get('kind')=='tail'),None)
        dx,dy=O.offset(self.active_project.get('render'))
        return [(x+dx,y+dy) for x,y in (E.R._project(pose,p) for p in tails.joints(item,model,pose))] if item else []
    def start_drag(self,event):
        if self.compare:return
        settings=self.active_project.get('render');cw,ch=O.size(settings)
        for v,(x,y,size) in enumerate(self.cells):
            if x<=event.x<x+size and y<=event.y<y+size*ch/cw:
                if self.selection==('body','hair') and self.handles.get():
                    import hair_controls
                    points=hair_controls.points(self,v)
                    if points:
                        distance,index=min((math.hypot(x+px*size/cw-event.x,y+py*size/cw-event.y),i) for i,(px,py) in enumerate(points[:3]))
                        if distance<20:
                            self.stop();self.snapshot();self.hair_bone=index;self.drag=('hair',index,v,size,self.hair_channel);self.drag_origin=(event.x,event.y,copy.deepcopy(self.project['controls'].get('hair',{})));self.drag_physics=copy.deepcopy(self.project['physics'].get('hair',hair_controls.hair.DEFAULT_PHYSICS));self.project['physics']['hair']={'strength':0};self.show_params();self.render();return
                if self.selection==('body','tail') and self.handles.get():
                    points=self.tail_points(v)
                    if points:
                        distance,index=min((math.hypot(x+px*size/cw-event.x,y+py*size/cw-event.y),i) for i,(px,py) in enumerate(points[:3]))
                        if distance<20:
                            self.stop();self.snapshot();self.selected_tail_bone=('尾根','尾中','尾尖')[index]
                            self.drag=('tail',index,v,size);self.drag_origin=(event.x,event.y,copy.deepcopy(self.project['controls'].get('tail',{})));self.drag_physics=None
                            self.show_params();self.render();return
                self.focus_view=v;self.layout_key=None;self.render()
                if not self.handles.get() or self.playing:return
                p=self.view_pose(v);j=O.joints(p,settings);scale=size/cw
                opts=[(math.hypot(x+d[q][0]*scale-event.x,y+d[q][1]*scale-event.y),k,q) for k,d in j.items() if k in E.LIMBS for q in ('mid','tip')]
                for body_key,handle_key,joint_key in (('torso','waist','root'),('torso','torso','tip'),('head','head','tip')):
                    px,py=j[handle_key]['tip'];opts.append((math.hypot(x+px*scale-event.x,y+py*scale-event.y),body_key,joint_key))
                dist,key,joint=min(opts)
                if dist>18:return
                self.stop();self.snapshot();self.selection=('body',key);self.show_params();self.drag=(v,key,joint,p);self.drag_origin=(event.x,event.y,copy.deepcopy(self.project['controls'].get(key,{})));self.drag_physics=copy.deepcopy(self.project['physics'].get(key));self.render();return
    def move_drag(self,event):
        if not self.drag:return
        if self.drag[0]=='hair':
            _,index,view,size,channel=self.drag;ox,oy,original=self.drag_origin;prefix=channel+'_'+('root','middle','tip')[index];control=self.project['controls'].setdefault('hair',{});sensitivity=180/size*O.size(self.active_project.get('render'))[0]/64;axis='roll' if view==1 else 'yaw'
            control[prefix+'_'+axis]=max(-90,min(90,original.get(prefix+'_'+axis,0)+(event.x-ox)*sensitivity));control[prefix+'_pitch']=max(-90,min(90,original.get(prefix+'_pitch',0)-(event.y-oy)*sensitivity));self.update_drag_preview();self.schedule_save();return
        if self.drag[0]=='tail':
            _,index,view,size=self.drag;ox,oy,original=self.drag_origin;prefix=('root','middle','tip')[index]
            control=self.project['controls'].setdefault('tail',{});axis='roll' if view==1 else 'yaw'
            sensitivity=180/size*O.size(self.active_project.get('render'))[0]/64
            control[prefix+'_'+axis]=max(-120,min(120,original.get(prefix+'_'+axis,0)+(event.x-ox)*sensitivity))
            control[prefix+'_pitch']=max(-120,min(120,original.get(prefix+'_pitch',0)-(event.y-oy)*sensitivity))
            self.update_drag_preview();self.schedule_save();return
        v,key,joint,start=self.drag;x,y,size=self.cells[v];cw=O.size(self.active_project.get('render'))[0];target=O.target(((event.x-x)*cw/size,(event.y-y)*cw/size),self.active_project.get('render'))
        p=self.view_pose(v)
        c=self.project['controls'].setdefault(key,{})
        if key in ('torso','head'):
            ox,oy,original=self.drag_origin
            if key=='torso' and joint=='root':
                c['height']=max(-8,min(8,original.get('height',0)+(event.y-oy)*cw/size))
                c['shift']=max(-12,min(12,original.get('shift',0)+(event.x-ox)*cw/size))
            else:
                solution=E.R.aim_body(p,key,target)
                mapping={'lean':'lean','rot':'tilt'} if key=='torso' else {'head_pitch':'nod','head':'tilt'}
                for pose_key,control_key in mapping.items():c[control_key]=c.get(control_key,0)+solution[pose_key]-p.get(pose_key,0)
        else:
            solution=E.R.ik(p,key,target,joint=joint,free=(0,2) if joint=='mid' else (0,1,2,3))
            offset=c.setdefault('offset',[0,0,0,0]);c['offset']=[offset[i]+solution[i]-p[key][i] for i in range(4)]
        # Physics is a post-process. Suspend it on this limb while directly posing it.
        self.project['physics'].pop(key,None)
        self.update_drag_preview();self.schedule_save()
        self.status.set('已调整整段动作的姿态；其他视图同步。拖腰可移动身体，拖躯干 / 头可转动。')
    def update_drag_preview(self):
        self.seq=E.poses(self.project);self.active_project=copy.deepcopy(self.project);self.raw_images={};self.photos.clear();self.epoch+=1;self.render()
    def end_drag(self,event):
        if self.drag:
            if self.drag_physics is not None:self.project['physics']['hair' if self.drag[0]=='hair' else self.drag[1]]=self.drag_physics
            self.drag=None;self.drag_physics=None;self.show_params();self.changed()
    def ab_view(self,on):
        if on==self.compare:return
        self.compare=on
        if on:
            p=copy.deepcopy(self.project);p['layers']=[];p['controls']={};p['physics']={};self.base_seq=E.poses(p)
        self.render()
    def play(self):
        if self.playing:self.stop();self.render();return
        if E.MT.mode(self.project)!='loop' and self.frame==len(self.seq)-1:self.frame=0
        self.playing=True;self.layout_key=None;self.started=time.perf_counter()-self.frame/self.project['fps'];self.playbtn.configure(text='■ 暂停');self.tick()
    def stop(self):
        self.playing=False;self.playbtn.configure(text='▶ 播放')
        if self.play_job:self.after_cancel(self.play_job);self.play_job=None
    def tick(self):
        if not self.playing:return
        frame,finished=E.MT.preview_frame(time.perf_counter()-self.started,self.project['fps'],len(self.seq),self.project)
        if finished:self.frame=frame;self.stop();self.render();return
        if frame!=self.frame:self.frame=frame;self.render()
        self.play_job=self.after(15,self.tick)
    def step(self,d):
        self.stop();self.frame=(self.frame+d)%len(self.seq) if E.MT.mode(self.project)=='loop' else max(0,min(len(self.seq)-1,self.frame+d));self.render()
    def seek(self,v):
        if not self.seq:return
        self.stop();self.frame=min(len(self.seq)-1,int(float(v)/1000*len(self.seq)));self.render()
    def new(self):
        self.snapshot();self.stop();self.project=self.make_project();self.frame=0;self.sync();self.changed()
    def open(self):
        path=filedialog.askopenfilename(parent=self,initialdir=E.ROOT/'examples',filetypes=[(tr('动作配方'),'*.json')])
        if not path:return
        try:p=E.load(path)
        except Exception as ex:messagebox.showerror(tr('无法打开'),tr(str(ex)));return
        self.snapshot();self.stop();self.project=p;self.frame=0;self.sync();self.changed()
    def save_as(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile=self.project.get('name','Animation')+'.json',filetypes=[(tr('动作配方'),'*.json')])
        if path:
            try:E.save(self.project,path);self.status.set('已保存：'+path)
            except Exception as ex:messagebox.showerror(tr('保存失败'),tr(str(ex)))
    def export(self):
        if getattr(self,'export_dialog',None) is not None and self.export_dialog.winfo_exists():self.export_dialog.lift();return self.export_dialog
        self.stop();self.render()
        dialog=tk.Toplevel(self);self.export_dialog=dialog;dialog.title(tr('导出序列帧'));dialog.transient(self);dialog.configure(bg=PANEL)
        width=min(self.winfo_screenwidth()-80,round(720*self.ui_scale));height=min(self.winfo_screenheight()-100,round(760*self.ui_scale))
        x=max(20,min(self.winfo_screenwidth()-width-20,self.winfo_rootx()+(self.winfo_width()-width)//2));y=max(20,min(self.winfo_screenheight()-height-40,self.winfo_rooty()+(self.winfo_height()-height)//2))
        dialog.geometry(f'{width}x{height}+{x}+{y}');dialog.minsize(540,440);dialog.grab_set()
        dialog.bind('<MouseWheel>',self.scroll_params)
        shell=dialog
        footer=tk.Frame(shell,bg=PANEL);footer.pack(side='bottom',fill='x',padx=20,pady=16)
        export_scroll=ScrollPanel(shell);export_scroll.pack(fill='both',expand=True,padx=12,pady=12)
        dialog=export_scroll.content
        directory=tk.StringVar(value=self.export_directory if Path(self.export_directory).is_dir() else str(E.ROOT));name=tk.StringVar(value=self.project.get('name','Animation'));create_folder=tk.BooleanVar(value=False);output_scale=tk.StringVar(value=str(self.project.get('export_scale',1) if self.project.get('export_scale',1) in (1,4,8) else 1)+'x')
        selected=self.focus_view if self.export_view.get()=='焦点视图' else VN.index(self.export_view.get())
        batch_views={'四方向（水平）':4,'八方向（水平）':8}
        view=tk.StringVar(value=next((label for label,count in batch_views.items() if count==self.project.get('export_directions')),VN[selected]));types={key:tk.BooleanVar(value=key in ('png','strip')) for key in ('png','strip','gif','recipe')}
        session=getattr(self,'export_session',{})
        if session:
            create_folder.set(session.get('create_folder',False));output_scale.set(session.get('scale','1x'));view.set(session.get('view',view.get()))
            if session.get('project_name')==self.project.get('name'):name.set(session.get('name',name.get()))
            for key,var in types.items():var.set(key in session.get('formats',('png','strip')))
        def remember(*_):
            self.export_session=dict(project_name=self.project.get('name'),name=name.get(),create_folder=create_folder.get(),scale=output_scale.get(),view=view.get(),formats=[key for key,var in types.items() if var.get()])
        for var in (name,create_folder,output_scale,view,*types.values()):var.trace_add('write',remember)
        shell.export_fields=dict(directory=directory,name=name,create_folder=create_folder,scale=output_scale,view=view,formats=types)
        format_controls={};export_hint=tk.StringVar()
        def update_view(_=None):
            batch=view.get() in batch_views
            if 'strip' in format_controls:
                control=format_controls['strip'];control.text='PNG 方向图集 · 透明背景' if batch else 'PNG 横向条带 · 透明背景';control.draw()
            cw,ch=O.size(self.project.get('render'));export_hint.set(f'1x = {cw} × {ch} px · '+tr('仅整数倍最近邻放大。')+('\n'+tr('每个方向一行，自动附带帧信息JSON；大图集自动分页。') if batch else ''))
        self.label(dialog,'导出目录').pack(fill='x',padx=20,pady=(20,4))
        row=tk.Frame(dialog);row.pack(fill='x',padx=20)
        PixelEntry(row,textvariable=directory,bg=FIELD,bd=0).pack(side='left',fill='x',expand=True)
        def browse():
            path=filedialog.askdirectory(parent=shell,title=tr('选择导出目录'),initialdir=directory.get() if Path(directory.get()).is_dir() else str(E.ROOT))
            if path:
                directory.set(path);self.export_directory=str(Path(path).resolve());self.save_preferences()
        self.button(row,'选择…',browse).pack(side='right',padx=(10,0))
        self.label(dialog,'导出名称',wraplength=580).pack(fill='x',padx=20,pady=(18,4))
        PixelEntry(dialog,textvariable=name,bg=FIELD,bd=0).pack(fill='x',padx=20)
        PixelCheck(dialog,text='创建同名子文件夹',variable=create_folder).pack(fill='x',padx=20,pady=8)
        self.label(dialog,'导出视角').pack(fill='x',padx=20,pady=(18,4));PixelOption(dialog,view,*VN,*batch_views,command=update_view).pack(fill='x',padx=20)
        self.label(dialog,'输出比例').pack(fill='x',padx=20,pady=(18,4))
        PixelOption(dialog,output_scale,'1x','4x','8x').pack(fill='x',padx=20)
        UI.Label(dialog,textvariable=export_hint,wrap=True,justify='left',anchor='w').pack(fill='x',padx=20,pady=5)
        for key,label in (('png','PNG 序列 · 透明背景'),('strip','PNG 横向条带 · 透明背景'),('gif','GIF 动画预览'),('recipe','JSON 项目副本')):
            control=PixelCheck(dialog,text=label,variable=types[key]);control.pack(fill='x',padx=20,pady=5);format_controls[key]=control
        update_view()
        error=tk.StringVar();UI.Label(dialog,textvariable=error,fg='#a34d35',wraplength=590,justify='left').pack(fill='x',padx=20,pady=8)
        def submit():
            if getattr(shell,'exporting',False):return
            if not directory.get().strip():error.set('请选择导出目录');return
            formats=[key for key,value in types.items() if value.get()]
            if not formats:error.set('请至少选择一种文件类型');return
            project=copy.deepcopy(self.project);directions=batch_views.get(view.get(),1)
            project['export_directions']=directions
            index=VN.index(view.get()) if directions==1 else 0;project['export_view']=dict(name=view.get(),yaw=VIEWS[index][0],pitch=VIEWS[index][1])
            output=directory.get().strip();folder=create_folder.get()
            options=dict(out=output,name=name.get(),formats=formats,create_folder=folder,scale=int(output_scale.get()[:-1]),directions=directions)
            shell.exporting=True;start.configure(state='disabled');cancel.configure(state='disabled');error.set('正在导出…')
            if not hasattr(self,'export_pool'):self.export_pool=ProcessPoolExecutor(max_workers=1)
            task=self.export_pool.submit(E.export,project,**options)
            def poll():
                nonlocal task
                if not task.done():self.after(40,poll);return
                try:dest=task.result()
                except Exception as ex:
                    if isinstance(ex,FileExistsError) and not options.get('overwrite') and shell.winfo_exists():
                        if messagebox.askyesno(tr('覆盖已有导出？'),tr('同名导出已存在。是否覆盖本次所选格式？其他文件会保留。'),parent=shell,default='no'):
                            options['overwrite']=True;task=self.export_pool.submit(E.export,project,**options);self.after(40,poll);return
                        text=tr('已保留原文件，可修改名称后重试。');self.status.set(text);shell.exporting=False;start.configure(state='normal');cancel.configure(state='normal');error.set(text);return
                    text=('同名文件夹已存在，请更换名称或目录' if folder else '同名文件已存在，请更换名称或目录') if isinstance(ex,FileExistsError) else str(ex)
                    self.status.set(text)
                    if shell.winfo_exists():shell.exporting=False;start.configure(state='normal');cancel.configure(state='normal');error.set(text)
                    return
                self.export_directory=str(Path(output).resolve());self.save_preferences();self.status.set('已导出：'+str(dest))
                if shell.winfo_exists():shell.destroy()
            self.after(40,poll)
        row=footer
        cancel=self.button(row,'取消',shell.destroy);cancel.pack(side='right');start=self.button(row,'开始导出',submit,True);start.pack(side='right',padx=10)
        shell.protocol('WM_DELETE_WINDOW',lambda:None if getattr(shell,'exporting',False) else shell.destroy())
        self.refresh_control_styles()
        return shell
    def close(self):
        self.stop();self.autosave()
        if self.executor:self.executor.shutdown(wait=False,cancel_futures=True)
        if hasattr(self,'export_pool'):self.export_pool.shutdown(wait=False,cancel_futures=True)
        # A child widget owns its registered Tcl command. Cancel the timer
        # without deleting that command through the root; each owner removes
        # its own commands during destroy (otherwise toolbar teardown fails).
        for job in self.tk.call('after','info'):self.tk.call('after','cancel',job)
        self.destroy()

if __name__=='__main__':
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError,OSError):pass
    import multiprocessing
    multiprocessing.freeze_support()
    App().mainloop()
