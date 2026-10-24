"""Pixel-grid controls. All geometry follows the application's UI scale."""
import tkinter as tk
from i18n import tr
FIELD='#e5d6bd';PANEL='#f8f0df';INK='#493c32';ACC='#e7a34c';EDGE='#aa957d';LIGHT='#fff9eb';SHADOW='#8d7257'
def wrap_text(text,font,width):
    import re
    lines=[]
    for paragraph in str(text).split('\n'):
        line=''
        for token in re.findall(r'[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*|[ \t]+|.',paragraph):
            if not line and token.isspace():continue
            if font.measure(line+token)>width and line.strip():lines.append(line.rstrip());line=''
            if not line and token.isspace():continue
            if font.measure(token)>width:
                while token and font.measure(token+'…')>width:token=token[:-1]
                token+='…'
            line+=token
        lines.append(line.rstrip())
    return '\n'.join(lines)
def ellipsize(text,font,width):
    if font.measure(text)<=width:return text
    while text and font.measure(text+'…')>width:text=text[:-1]
    return text+'…'

class PixelBase(tk.Canvas):
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw)
        self.bind('<Destroy>',self.release_command,add='+')
    def release_command(self,event):
        # Dialog callbacks often close over their own controls and Tk variables.
        # Break those cycles on the UI thread, before worker-side GC can run.
        if event.widget is self and hasattr(self,'command'):self.command=None
    def owner(self):
        node=self
        while node is not None:
            if hasattr(node,'ui_scale') and hasattr(node,'ui_font') and not callable(node.ui_font):return node
            node=getattr(node,'master',None)
        return self.winfo_toplevel()
    def px(self,n):return max(1,round(n*getattr(self.owner(),'ui_scale',1.)))
    def ui_font(self):return getattr(self.owner(),'ui_font','TkDefaultFont')
    def plate(self,x,y,w,h,fill=FIELD,pressed=False):
        b=self.px(4);cut=self.px(4)
        self.create_polygon(x+cut,y,x+w-cut,y,x+w,y+cut,x+w,y+h-cut,x+w-cut,y+h,x+cut,y+h,x,y+h-cut,x,y+cut,fill=INK,outline='')
        self.create_rectangle(x+b,y+b,x+w-b,y+h-b,fill=fill,outline='')
        self.create_rectangle(x+b,y+b,x+w-b,y+b+self.px(3),fill=SHADOW if pressed else LIGHT,outline='')
        self.create_rectangle(x+b,y+h-b-self.px(4),x+w-b,y+h-b,fill=LIGHT if pressed else SHADOW,outline='')

    def refresh_style(self):self.draw()
class PixelScale(PixelBase):
    def __init__(self,parent,from_=0,to=1,resolution=1,command=None,**kw):
        super().__init__(parent,bg=kw.get('bg',PANEL),highlightthickness=0,takefocus=1,cursor='hand2')
        self.lo=float(from_);self.hi=float(to);self.step=float(resolution);self.value=self.lo;self.command=command
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.move);self.bind('<B1-Motion>',self.move)
        self.bind('<Left>',lambda e:self.user_set(self.value-self.step));self.bind('<Right>',lambda e:self.user_set(self.value+self.step));self.draw()
    def configure(self,cnf=None,**kw):
        if 'command' in kw:self.command=kw.pop('command')
        if kw:return super().configure(cnf,**kw)
    config=configure
    def set(self,v):self.value=max(self.lo,min(self.hi,float(v)));self.draw()
    def get(self):return self.value
    def user_set(self,v):
        v=max(self.lo,min(self.hi,self.lo+round((v-self.lo)/self.step)*self.step))
        if v==self.value:return
        self.set(v)
        if self.command:self.command(str(self.value))
    def move(self,e):self.focus_set();pad=self.px(18);self.user_set(self.lo+(self.hi-self.lo)*max(0,min(1,(e.x-pad)/max(1,self.winfo_width()-pad*2))))
    def draw(self):
        self.configure(height=self.px(46));self.delete('all');w=max(self.px(48),self.winfo_width());pad=self.px(18);cy=self.px(23)
        x=round(pad+(w-pad*2)*(self.value-self.lo)/max(.0001,self.hi-self.lo))
        self.create_rectangle(pad,cy-self.px(7),w-pad,cy+self.px(7),fill=INK,outline='')
        self.create_rectangle(pad+self.px(4),cy-self.px(3),w-pad-self.px(4),cy+self.px(3),fill=SHADOW,outline='')
        self.create_rectangle(pad+self.px(4),cy-self.px(3),max(pad+self.px(4),x),cy+self.px(3),fill=ACC,outline='')
        self.plate(x-self.px(13),cy-self.px(18),self.px(26),self.px(36),PANEL)
        for dx in (-3,3):self.create_rectangle(x+self.px(dx)-self.px(1),cy-self.px(5),x+self.px(dx)+self.px(1),cy+self.px(5),fill=SHADOW,outline='')
class PixelCheck(PixelBase):
    def __init__(self,parent,text,variable,command=None,bg=PANEL,**kw):
        self.var=variable;self.command=command;self.text=text
        super().__init__(parent,bg=bg,highlightthickness=0,takefocus=1,cursor='hand2')
        self.trace=variable.trace_add('write',lambda *_:self.draw())
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.toggle);self.bind('<space>',self.toggle)
        self.bind('<Destroy>',self.cleanup,add='+');self.draw()
    def cleanup(self,e):
        if e.widget is self:self.var.trace_remove('write',self.trace)
    def toggle(self,e=None):
        self.focus_set();self.var.set(not self.var.get())
        if self.command:self.command()
    def draw(self):
        import tkinter.font as ft
        f=ft.Font(font=self.ui_font());label=tr(self.text);requested=f.measure(label)+self.px(52)
        width=self.winfo_width() if self.winfo_width()>1 else requested;available=max(self.px(24),width-self.px(52))
        text=wrap_text(label,f,available);textheight=len(text.split('\n'))*f.metrics('linespace')
        h=max(self.px(44),textheight+self.px(16));self.configure(width=requested,height=h);self.delete('all');cy=h//2;left=self.px(4);top=cy-self.px(15)
        self.plate(left,top,self.px(30),self.px(30),ACC if self.var.get() else FIELD,pressed=True)
        if self.var.get():
            for x,y,w,hh in ((7,13,5,5),(11,17,5,5),(15,12,5,6),(19,7,5,6)):
                self.create_rectangle(left+self.px(x),top+self.px(y),left+self.px(x+w),top+self.px(y+hh),fill=INK,outline='')
        self.create_text(self.px(46),cy,anchor='w',text=text,font=self.ui_font(),fill=INK,justify='left')
class PixelOption(PixelBase):
    def __init__(self,parent,variable,*values,command=None,**kw):
        self.var=variable;self.values=values;self.command=command
        super().__init__(parent,bg=FIELD,highlightthickness=0,takefocus=1,cursor='hand2')
        self.trace=variable.trace_add('write',lambda *_:self.draw());self.bind('<Configure>',lambda e:self.draw())
        self.bind('<Button-1>',self.post);self.bind('<space>',self.post);self.bind('<Return>',self.post);self.bind('<Destroy>',self.cleanup,add='+');self.draw()
    def cleanup(self,e):
        if e.widget is self:self.var.trace_remove('write',self.trace)
    def pick(self,value):
        self.var.set(value)
        if self.command:self.command(value)
    def post(self,e=None):
        self.focus_set()
        if hasattr(self,'popup') and self.popup.winfo_exists():return
        self.old_grab=self.grab_current();popup=tk.Toplevel(self);self.popup=popup;popup.overrideredirect(True);popup.configure(bg=INK)
        width=max(self.winfo_width(),self.winfo_reqwidth());height=min(self.px(420),len(self.values)*self.px(50)+self.px(12),self.winfo_screenheight()-40)
        x=min(self.winfo_rootx(),self.winfo_screenwidth()-width);y=min(self.winfo_rooty()+self.winfo_height(),self.winfo_screenheight()-height-20)
        popup.geometry(f'{width}x{height}+{x}+{max(0,y)}')
        panel=ScrollPanel(popup);panel.pack(fill='both',expand=True,padx=self.px(4),pady=self.px(4))
        def close():
            popup.destroy()
            if self.old_grab is not None and self.old_grab.winfo_exists():self.old_grab.grab_set()
        self.close_popup=close
        def pick(v):close();self.pick(v)
        for value in self.values:PixelButton(panel.content,text=value,command=lambda v=value:pick(v),accent=value==self.var.get()).pack(fill='x',pady=self.px(2))
        popup.bind('<Escape>',lambda e:close());popup.bind('<ButtonPress-1>',lambda e:close() if e.x_root<x or e.x_root>x+width or e.y_root<y or e.y_root>y+height else None)
        popup.bind('<MouseWheel>',panel.wheel);popup.grab_set();popup.focus_set()
    def draw(self):
        import tkinter.font as ft
        f=ft.Font(font=self.ui_font());w=max(f.measure(tr(v)) for v in self.values)+self.px(64);h=max(self.px(48),f.metrics('linespace')+self.px(22))
        self.configure(width=w,height=h);self.delete('all');width=max(self.px(60),self.winfo_width() if self.winfo_width()>1 else w);cy=h//2
        self.plate(0,0,width,h,FIELD,pressed=True)
        self.create_text(self.px(14),cy,anchor='w',text=ellipsize(tr(self.var.get()),f,max(self.px(20),width-self.px(62))),font=self.ui_font(),fill=INK)
        x=width-self.px(33)
        for j in range(3):self.create_rectangle(x+self.px(j*3),cy-self.px(5)+self.px(j*3),x+self.px(18-j*3),cy-self.px(2)+self.px(j*3),fill=INK,outline='')
class PixelScroll(PixelBase):
    def __init__(self,parent,command,**kw):
        super().__init__(parent,bg=FIELD,highlightthickness=0);self.command=command;self.first=0;self.last=1
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.move);self.bind('<B1-Motion>',self.move);self.draw()
    def set(self,first,last):self.first=float(first);self.last=float(last);self.draw()
    def move(self,e):self.command('moveto',max(0,min(1,e.y/max(1,self.winfo_height())-(self.last-self.first)/2)))
    def draw(self):
        self.configure(width=self.px(24));self.delete('all');h=self.winfo_height();y=int(h*self.first);height=max(self.px(32),int(h*(self.last-self.first)));self.plate(0,y,self.px(24),height,FIELD)


class PixelButton(PixelBase):
    def __init__(self,parent,text='',command=None,accent=False,compact=False,**kw):
        self.compact=compact;self.text=text;self.command=command;self.accent=accent;self.pressed=False;self.hover=False;self.state='normal'
        super().__init__(parent,bg=parent.cget('bg'),highlightthickness=0,takefocus=1,cursor='hand2')
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Enter>',lambda e:self.enter(True));self.bind('<Leave>',lambda e:self.enter(False))
        self.bind('<ButtonPress-1>',self.down);self.bind('<ButtonRelease-1>',self.up)
        self.bind('<space>',lambda e:self.invoke());self.bind('<Return>',lambda e:self.invoke());self.draw()
    def enter(self,on):self.hover=on;self.draw()
    def down(self,e):self.pressed=True;self.focus_set();self.draw()
    def up(self,e):
        pressed=self.pressed;self.pressed=False;self.draw()
        if pressed and 0<=e.x<self.winfo_width() and 0<=e.y<self.winfo_height():self.invoke()
    def invoke(self):
        if self.state!='disabled' and self.command:return self.command()
    def configure(self,cnf=None,**kw):
        redraw=False
        for key in ('text','command','state'):
            if key in kw:setattr(self,key,kw.pop(key));redraw=True
        if kw:super().configure(cnf,**kw)
        if redraw:self.draw()
    config=configure
    def draw(self):
        import tkinter.font as ft
        f=ft.Font(font=self.ui_font());text=tr(self.text);w=self.px(64) if self.compact else f.measure(text)+self.px(36)
        width=max(self.px(40),self.winfo_width() if self.winfo_width()>1 else w);available=max(self.px(20),width-self.px(28))
        text=wrap_text(text,f,available)
        self.delete('all');item=self.create_text(width//2,0,anchor='n',text=text,font=self.ui_font())
        bbox=self.bbox(item);textheight=bbox[3]-bbox[1] if bbox else f.metrics('linespace')
        h=max(self.px(48),textheight+self.px(22));self.configure(width=w,height=h);self.delete('all')
        self.plate(0,0,width,h,ACC if self.accent else LIGHT if self.hover else FIELD,self.pressed)
        self.create_text(width//2,h//2+(self.px(2) if self.pressed else 0),text=text,font=self.ui_font(),fill='#8a7967' if self.state=='disabled' else INK,justify='center')

class PixelEntry(tk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,bg=INK)
        self.field=tk.Entry(self,bd=0,relief='flat',highlightthickness=0,insertbackground=INK,**{k:v for k,v in kw.items() if k!='bd'})
        self.field.pack(fill='both',expand=True);self.refresh_style()
    def refresh_style(self):
        node=self.master
        while node is not None and not hasattr(node,'ui_scale'):node=getattr(node,'master',None)
        scale=getattr(node,'ui_scale',1.)
        self.configure(padx=max(3,round(4*scale)),pady=max(3,round(4*scale)))
        self.field.configure(font=getattr(node,'ui_font','TkDefaultFont'),insertwidth=max(2,round(2*scale)))

class FlowBar(tk.Frame):
    """Wrap toolbar items onto complete rows instead of clipping actions."""
    def __init__(self,parent,compact=False,pin_right=False,**kw):
        super().__init__(parent,**kw);self.compact=compact;self.pin_right=pin_right;self.layout_job=None;self.sides={}
        self.bind('<Configure>',self.schedule)
        self.bind('<Destroy>',self.cleanup)
    @property
    def ui_scale(self):return self.winfo_toplevel().ui_scale*(.8 if self.compact else 1)
    @property
    def ui_font(self):
        root=self.winfo_toplevel();return getattr(root,'caption_font',root.ui_font) if self.compact else root.ui_font
    def cleanup(self,event):
        if event.widget is self:
            if self.layout_job:self.after_cancel(self.layout_job);self.layout_job=None
            self.sides.clear()
    def schedule(self,event=None):
        if self.layout_job is None:self.layout_job=self.after_idle(self.reflow)
    def reflow(self):
        self.layout_job=None;width=self.winfo_width()
        if width<20:return
        children=self.winfo_children()
        for child in children:
            if child.winfo_manager()=='pack':
                self.sides[child]=child.pack_info().get('side','left');child.pack_forget()
                child.bind('<Configure>',self.schedule,add='+')
        left=[w for w in children if self.sides.get(w)=='left'];right=list(reversed([w for w in children if self.sides.get(w)=='right']))
        items=left if self.pin_right else left+right
        reserve=sum(min(width,w.winfo_reqwidth())+6 for w in right) if self.pin_right else 0
        x=0;y=0;row=max((w.winfo_reqheight() for w in right),default=0) if self.pin_right else 0
        rx=max(0,width-reserve+6)
        if self.pin_right:
            for child in right:
                w=min(width,child.winfo_reqwidth());child.place(x=rx,y=0,width=w,height=child.winfo_reqheight());rx+=w+6
        for child in items:
            w=min(width,child.winfo_reqwidth());h=child.winfo_reqheight()
            available=width-reserve if y==0 else width
            if (x or reserve and y==0) and x+w>available:y+=row+4;x=0;row=0
            child.place(x=x,y=y,width=w,height=h);x+=w+6;row=max(row,h)
        height=y+row
        if int(self.cget('height'))!=height:self.configure(height=height)

class ScrollPanel(tk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,bg=PANEL,**kw)
        self.canvas=tk.Canvas(self,bg=PANEL,highlightthickness=0,width=1,height=1)
        self.scrollbar=PixelScroll(self,command=self.canvas.yview);self.scrollbar.pack(side='right',fill='y')
        self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content=tk.Frame(self.canvas,bg=PANEL);self.item=self.canvas.create_window(0,0,anchor='nw',window=self.content)
        self.content.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',self.fit)
        self.bind('<MouseWheel>',self.wheel)
    def fit(self,e):
        self.canvas.itemconfigure(self.item,width=max(1,e.width))
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    def wheel(self,e):self.canvas.yview_scroll(-int(e.delta/120),'units');return 'break'
