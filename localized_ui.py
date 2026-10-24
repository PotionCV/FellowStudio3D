import tkinter as tk
from i18n import tr
def inherited_font(parent):
    node=parent
    while node is not None:
        value=getattr(node,'ui_font',None)
        if value is not None and not callable(value):return value
        node=getattr(node,'master',None)
    return None
class Label(tk.Label):
    def __init__(self,parent,**kw):
        face=inherited_font(parent)
        if face is not None:kw.setdefault('font',face)
        self.auto_wrap=kw.pop('wrap',False) or float(kw.get('wraplength',0))>0
        self.source_var=kw.pop('textvariable',None);self.source_text=kw.get('text','');self.last_text=None
        if 'text' in kw:kw['text']=tr(kw['text'])
        if self.source_var is not None:
            self.display_var=tk.StringVar(master=parent,value=tr(self.source_var.get()));kw['textvariable']=self.display_var
        super().__init__(parent,**kw)
        if self.source_var is not None:self.trace=self.source_var.trace_add('write',lambda *_:self.update_text())
        self.bind('<Destroy>',self.cleanup,add='+')
        if self.auto_wrap:self.bind('<Configure>',lambda e:self.update_text(e.width),add='+')
    def update_text(self,width=None):
        text=tr(self.source_var.get() if self.source_var is not None else self.source_text)
        if self.auto_wrap:
            import tkinter.font as ft
            from pixel_ui import wrap_text
            width=width or self.winfo_width()
            if width>8:
                text=wrap_text(text,ft.Font(font=self.cget('font')),max(12,width-4))
                if float(self.cget('wraplength')):self.configure(wraplength=0)
        if text==self.last_text:return
        self.last_text=text
        if self.source_var is not None:self.display_var.set(text)
        else:self.configure(text=text)
    def cleanup(self,event):
        if event.widget is self and self.source_var is not None:self.source_var.trace_remove('write',self.trace)
class Button(tk.Button):
    def __init__(self,parent,**kw):
        face=inherited_font(parent)
        if face is not None:kw.setdefault('font',face)
        if 'text' in kw:kw['text']=tr(kw['text'])
        super().__init__(parent,**kw)
    def configure(self,cnf=None,**kw):
        if 'text' in kw:kw['text']=tr(kw['text'])
        return super().configure(cnf,**kw)
    config=configure
class Menu(tk.Menu):
    def add_command(self,cnf=None,**kw):
        if 'label' in kw:kw['label']=tr(kw['label'])
        return super().add_command(cnf,**kw)
