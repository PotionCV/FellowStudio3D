"""Compact live canvas and lighting controls; each edit supports project Undo."""
import tkinter as tk
from tkinter import colorchooser
from pixel_ui import PixelButton,PixelCheck,PixelScale,PixelOption,PixelEntry,ScrollPanel,PANEL
from localized_ui import Label
import render_options as O
from i18n import tr

class RenderOptionsEditor(tk.Toplevel):
    def __init__(self,owner,section='canvas'):
        super().__init__(owner);self.owner=owner;self.section=section;owner.render_settings_editors[section]=self
        self.ui_scale=owner.ui_scale;self.ui_font=owner.ui_font;self.caption_font=owner.caption_font;self.closed=False
        self.title(tr('画幅尺寸…' if section=='canvas' else '光照设置…'));self.configure(bg=PANEL);self.transient(owner)
        width=min(self.winfo_screenwidth()-60,round(520*self.ui_scale));height=min(self.winfo_screenheight()-90,round((440 if section=='canvas' else 620)*self.ui_scale))
        self.geometry(f'{width}x{height}+{max(10,owner.winfo_rootx()+owner.winfo_width()-width)}+{max(10,owner.winfo_rooty())}');self.minsize(390,330 if section=='canvas' else 440)
        footer=tk.Frame(self,bg=PANEL);footer.pack(side='bottom',fill='x',padx=12,pady=10)
        PixelButton(footer,text='完成',command=self.destroy).pack(side='right')
        Label(footer,text='实时预览；可在主窗口撤销。',wrap=True).pack(side='left',fill='x',expand=True)
        self.scroll=ScrollPanel(self);self.scroll.pack(fill='both',expand=True,padx=8,pady=8)
        self.bind('<MouseWheel>',self.scroll.wheel)
        body=tk.Frame(self.scroll.content,bg=PANEL);self.canvas_body=body
        if section=='canvas':body.pack(fill='x')
        Label(body,text='原生像素画幅',anchor='w',font=self.ui_font).pack(fill='x',padx=12,pady=8)
        self.preset=tk.StringVar(master=self,value='64 × 64');presets=('64 × 64','96 × 96','128 × 128','128 × 192','192 × 192','256 × 256')
        PixelOption(body,self.preset,*presets,command=self.choose_canvas).pack(fill='x',padx=12,pady=5)
        row=tk.Frame(body,bg=PANEL);row.pack(fill='x',padx=12,pady=6)
        self.width=tk.StringVar(master=self);self.height=tk.StringVar(master=self)
        for label,value in (('宽',self.width),('高',self.height)):
            Label(row,text=label).pack(side='left',padx=4);PixelEntry(row,textvariable=value,width=4).pack(side='left')
        PixelButton(body,text='应用画幅',command=self.apply_canvas).pack(fill='x',padx=12,pady=5)
        Label(body,text='32–256 px；扩大画幅不缩放模型或贴图，底部留白保持。',wrap=True,justify='left').pack(fill='x',padx=12,pady=6)
        self.message=tk.StringVar(master=self);Label(body,textvariable=self.message,wrap=True,fg='#a34d35').pack(fill='x',padx=12)
        self.light_body=tk.Frame(self.scroll.content,bg=PANEL);self.scales={};self.values={}
        if section=='lighting':self.light_body.pack(fill='x')
        Label(self.light_body,text='光照和自阴影开关位于主窗口的显示选项中。',wrap=True,justify='left').pack(fill='x',padx=12,pady=8)
        self.style=tk.StringVar(master=self)
        styles={'绘制感':'painted','立体感':'facet'}
        PixelOption(self.light_body,self.style,*styles,command=lambda label:self.set_option('light_style',styles[label])).pack(fill='x',padx=12,pady=6)
        for key,label,lo,hi,step in (('light_angle','光照角度（度）',0,360,5),('light_height','光照高度（度）',5,85,5),('light_strength','光照强度',0,1,.05),('shadow_strength','自阴影强度',0,1,.05)):
            value=tk.StringVar(master=self);self.values[key]=value
            row=tk.Frame(self.light_body,bg=PANEL);row.pack(fill='x',padx=12,pady=(12,3));Label(row,text=label).pack(side='left');Label(row,textvariable=value).pack(side='right')
            control=PixelScale(self.light_body,from_=lo,to=hi,resolution=step);control.pack(fill='x',padx=12);self.scales[key]=control
            control.bind('<ButtonPress-1>',lambda e:self.owner.snapshot(),add='+');control.bind('<KeyPress>',lambda e:self.owner.snapshot(),add='+')
            control.configure(command=lambda v,k=key:self.set_option(k,float(v),snapshot=False))
        self.color_buttons={}
        for key,label in (('light_color','光照颜色'),('shadow_color','阴影颜色')):
            b=PixelButton(self.light_body,text=label,command=lambda k=key:self.choose_color(k));b.pack(fill='x',padx=12,pady=(12,0));self.color_buttons[key]=b
        Label(self.light_body,text='方向固定在三维空间；分档明暗保留像素边缘。颜色只影响渲染，不改原贴图。',wrap=True,justify='left').pack(fill='x',padx=12,pady=12)
        self.refresh();self.protocol('WM_DELETE_WINDOW',self.destroy)

    def refresh(self):
        s=O.normalized(self.owner.project.get('render'));self.width.set(str(s['canvas_width']));self.height.set(str(s['canvas_height']));self.preset.set(f'{s["canvas_width"]} × {s["canvas_height"]}')
        self.style.set('绘制感' if s['light_style']=='painted' else '立体感')
        for key,scale in self.scales.items():scale.set(s[key]);self.values[key].set(f'{s[key]:g}')
    def set_option(self,key,value,snapshot=True):
        if self.owner.project.get('render',{}).get(key,O.DEFAULTS[key])==value:return
        if snapshot:self.owner.snapshot()
        self.owner.project.setdefault('render',{})[key]=value;self.refresh();self.owner.sync_render_flags();self.owner.save_preferences();self.owner.changed()
    def choose_canvas(self,label):
        w,h=label.split(' × ');self.width.set(w);self.height.set(h);self.apply_canvas()
    def apply_canvas(self):
        try:w,h=int(self.width.get()),int(self.height.get());assert 32<=w<=256 and 32<=h<=256
        except (ValueError,AssertionError):self.message.set(tr('宽、高须为32–256之间的整数。'));return False
        self.message.set('')
        if (w,h)!=O.size(self.owner.project.get('render')):
            self.owner.snapshot();self.owner.project['render'].update(canvas_width=w,canvas_height=h);self.owner.save_preferences();self.owner.changed()
        self.refresh();return True
    def choose_color(self,key):
        value=colorchooser.askcolor(color=O.normalized(self.owner.project.get('render'))[key],parent=self,title=tr('光照颜色' if key=='light_color' else '阴影颜色'))[1]
        if value:self.set_option(key,value.lower())
    def destroy(self):
        if self.closed:return
        self.closed=True;self.owner.render_settings_editors.pop(self.section,None);super().destroy()
        for key,value in list(vars(self).items()):
            if isinstance(value,tk.Variable):setattr(self,key,None)
        self.values.clear()
