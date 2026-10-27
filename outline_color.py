"""Pixel-style outline palette and exact RGB input, without native widgets."""
import re
import tkinter as tk
from localized_ui import Label
from pixel_ui import PixelButton,PixelEntry,PANEL,INK
from i18n import tr

class OutlineColorDialog(tk.Toplevel):
    def __init__(self,owner):
        super().__init__(owner)
        self.owner=owner;self.ui_scale=owner.ui_scale;self.ui_font=owner.ui_font
        self.title(tr('边线颜色'));self.transient(owner);self.configure(bg=PANEL)
        self.geometry(f'{min(self.winfo_screenwidth()-60,round(610*self.ui_scale))}x{min(self.winfo_screenheight()-80,round(610*self.ui_scale))}')
        self.minsize(500,500);self.grab_set()
        self.value=tk.StringVar(master=self,value=owner.outline_color.get())
        self.error=tk.StringVar(master=self)
        footer=tk.Frame(self,bg=PANEL);footer.pack(side='bottom',fill='x',padx=14,pady=12)
        PixelButton(footer,text='取消',command=self.destroy).pack(side='right',padx=4)
        PixelButton(footer,text='应用',command=self.apply,accent=True).pack(side='right',padx=4)
        from pixel_ui import ScrollPanel
        panel=ScrollPanel(self);panel.pack(fill='both',expand=True,padx=12,pady=10);body=panel.content
        Label(body,text='边线颜色',anchor='w').pack(fill='x',padx=8,pady=5)
        self.preview=tk.Canvas(body,height=round(80*self.ui_scale),highlightthickness=0,bg='#5a4d42');self.preview.pack(fill='x',padx=8,pady=6)
        PixelButton(body,text='自动灰色',command=lambda:self.value.set('auto')).pack(fill='x',padx=8,pady=6)
        palette=tk.Frame(body,bg=PANEL);palette.pack(fill='x',padx=8,pady=6);palette.columnconfigure((0,1,2,3),weight=1,uniform='colors')
        for i,color in enumerate(('#202020','#484848','#808080','#c0c0c0','#ffffff','#583c32','#995a46','#e7a34c','#2e556d','#405c42','#66517c','#b45365')):
            swatch=tk.Canvas(palette,width=round(60*self.ui_scale),height=round(38*self.ui_scale),highlightthickness=round(3*self.ui_scale),highlightbackground=INK,bg=color,cursor='hand2',takefocus=True)
            swatch.grid(row=i//4,column=i%4,sticky='ew',padx=4,pady=4)
            swatch.bind('<Button-1>',lambda e,c=color:self.value.set(c));swatch.bind('<Return>',lambda e,c=color:self.value.set(c))
        Label(body,text='RGB 色值（#RRGGBB）',anchor='w').pack(fill='x',padx=8,pady=(8,4))
        self.entry=PixelEntry(body,textvariable=self.value);self.entry.pack(fill='x',padx=8)
        Label(body,textvariable=self.error,fg='#a34d35',wrap=True,anchor='w').pack(fill='x',padx=8,pady=8)
        self.value.trace_add('write',lambda *_:self.draw());self.preview.bind('<Configure>',self.draw);self.draw()
    def draw(self,event=None):
        value=self.value.get().strip();color='#484848' if value=='auto' else value
        if not re.fullmatch('#[0-9a-fA-F]{6}',color):return
        c=self.preview;w=max(100,c.winfo_width());h=int(c.cget('height'));c.delete('all')
        c.create_rectangle(w//2-28,12,w//2+28,h-12,fill='#e5d6bd',outline=color,width=6)
    def apply(self):
        value=self.value.get().strip().lower()
        if value!='auto' and not re.fullmatch('#[0-9a-f]{6}',value):self.error.set(tr('请输入 #RRGGBB 格式的颜色'));return
        self.owner.outline_color.set(value);self.owner.display();self.destroy()
