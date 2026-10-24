"""Zoomable UV selection workspace with paint, erase and cross-face groups."""
import copy
import tkinter as tk
from tkinter import font
import numpy as np
from PIL import Image,ImageTk
import uv_assets as U
from pixel_protection import valid_groups,group_faces,pixel_face
from pixel_ui import PixelButton,PixelCheck,PixelScale,ScrollPanel,PANEL,INK,ACC
from localized_ui import Label
from i18n import tr

class ProtectionEditor(tk.Toplevel):
    def __init__(self,owner,part):
        super().__init__(owner)
        self.owner=owner;self.part=part;self.ui_scale=owner.ui_scale
        self.ui_font=font.Font(self,family=owner.ui_font.actual('family'),size=-round(18*self.ui_scale))
        self.resource=copy.deepcopy(owner.project['textures'][part]);self.groups=valid_groups(self.resource)
        self.selection=set();self.start=None;self.history=[];self.editing=None
        self.zoom=1;self.offset=None;self.auto_fit=True;self.photo_zoom=None;self.space=False;self.pan_start=None
        self.tool='box';self.operation='replace';self.last_pixel=None
        self.title(tr('像素保护')+' · '+part);self.transient(owner);self.configure(bg=PANEL)
        w=min(self.winfo_screenwidth()-60,round(1200*self.ui_scale));h=min(self.winfo_screenheight()-90,round(820*self.ui_scale))
        self.geometry(f'{w}x{h}');self.minsize(920,620)
        header=tk.Frame(self,bg=PANEL);header.pack(fill='x',padx=12,pady=8)
        Label(header,text='像素保护',font=self.ui_font,anchor='w').pack(side='left')
        self.counter=tk.StringVar(master=self,value='0 px');Label(header,textvariable=self.counter,anchor='e').pack(side='right')
        footer=tk.Frame(self,bg=PANEL);footer.pack(side='bottom',fill='x',padx=12,pady=10)
        PixelButton(footer,text='应用保护组',command=self.apply,accent=True).pack(side='right',padx=4)
        PixelButton(footer,text='取消',command=self.destroy).pack(side='right',padx=4)
        self.status=tk.StringVar(master=self);Label(footer,textvariable=self.status,wrap=True,anchor='w').pack(side='left',fill='both',expand=True,padx=5)
        body=tk.PanedWindow(self,orient='horizontal',sashwidth=12,bg='#8d7257',bd=0,opaqueresize=False);body.pack(fill='both',expand=True,padx=12)
        left=tk.Frame(body,bg=PANEL);body.add(left,minsize=460,stretch='always')
        tools=tk.Frame(left,bg=PANEL);tools.pack(fill='x',pady=(0,6));self.tool_buttons={}
        for key,label in (('box','框选'),('brush','画笔')):
            b=PixelButton(tools,text=label,command=lambda k=key:self.set_tool(k));b.pack(side='left',padx=3);self.tool_buttons[key]=b
        self.button(tools,'撤销',self.undo).pack(side='right',padx=3)
        modes=tk.Frame(left,bg=PANEL);modes.pack(fill='x',pady=(0,6));self.mode_buttons={}
        for key,label in (('replace','替换选区'),('add','加选'),('subtract','减选')):
            b=self.button(modes,label,lambda k=key:self.set_operation(k));b.pack(side='left',padx=3);self.mode_buttons[key]=b
        view=tk.Frame(left,bg='#493c32');view.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(view,bg='#5a4d42',highlightthickness=0,cursor='crosshair');self.canvas.pack(fill='both',expand=True,padx=3,pady=3)
        zoom_bar=tk.Frame(left,bg=PANEL);zoom_bar.pack(fill='x',pady=6)
        for label,fn in (('−',lambda:self.change_zoom(-1)),('＋',lambda:self.change_zoom(1)),('适合窗口',self.fit)):
            self.button(zoom_bar,label,fn).pack(side='left',padx=3)
        self.zoom_label=tk.StringVar(master=self,value='1x');Label(zoom_bar,textvariable=self.zoom_label,anchor='w').pack(side='left',padx=10)
        self.grid=tk.BooleanVar(master=self,value=True);PixelCheck(zoom_bar,text='网格',variable=self.grid,command=self.draw).pack(side='right')
        side=tk.Frame(body,bg=PANEL);body.add(side,width=round(300*self.ui_scale),minsize=280,stretch='never')
        self.group_scroll=ScrollPanel(side);self.group_scroll.pack(fill='both',expand=True);self.group_panel=self.group_scroll.content
        self.angle=tk.DoubleVar(master=self,value=40.);self.angle_text=tk.StringVar(master=self,value='40°')
        self.refresh_groups()
        self.canvas.bind('<Configure>',self.draw);self.canvas.bind('<Button-1>',self.begin);self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',self.end)
        self.canvas.bind('<Button-3>',lambda e:self.begin(e,erase=True));self.canvas.bind('<B3-Motion>',self.drag);self.canvas.bind('<ButtonRelease-3>',self.end)
        self.canvas.bind('<Button-2>',self.begin_pan);self.canvas.bind('<B2-Motion>',self.move_pan);self.canvas.bind('<ButtonRelease-2>',self.end_pan)
        self.canvas.bind('<MouseWheel>',self.wheel);self.canvas.bind('<Motion>',self.hover)
        self.bind('<KeyPress-space>',lambda e:setattr(self,'space',True));self.bind('<KeyRelease-space>',lambda e:setattr(self,'space',False))
        self.bind('<Escape>',lambda e:self.destroy());self.bind('<Control-z>',lambda e:(self.undo(),'break')[1]);self.bind('<Delete>',lambda e:self.clear_selection())
        self.bind('<KeyPress-b>',lambda e:self.set_tool('brush'));self.bind('<KeyPress-m>',lambda e:self.set_tool('box'))
        self.set_tool('box');self.set_operation('replace')
        im=U.texture_image({'textures':{part:self.resource}},part);yy,xx=np.indices((im.height,im.width))
        a=np.full((im.height,im.width,4),(211,199,181,255),np.uint8);a[((xx//4+yy//4)%2)==0]=(234,224,207,255)
        self.image=Image.fromarray(a);self.image.alpha_composite(im)

    def button(self,parent,text,fn):return PixelButton(parent,text=text,command=fn)
    def checkpoint(self):self.history.append((copy.deepcopy(self.groups),set(self.selection),self.editing,self.angle.get()))
    def set_tool(self,key):
        self.tool=key
        for k,b in self.tool_buttons.items():b.accent=k==key;b.draw()
        if key=='brush' and self.operation=='replace':self.set_operation('add')
    def set_operation(self,key):
        self.operation=key
        for k,b in self.mode_buttons.items():b.accent=k==key;b.draw()
    def refresh_groups(self):
        for child in self.group_panel.winfo_children():child.destroy()
        Label(self.group_panel,text='选区',anchor='w').pack(fill='x',padx=10,pady=(8,4))
        self.button(self.group_panel,'更新保护组' if self.editing is not None else '保护所选像素',self.add_group).pack(fill='x',padx=10,pady=4)
        self.button(self.group_panel,'清除选择',self.clear_selection).pack(fill='x',padx=10,pady=4)
        row=tk.Frame(self.group_panel,bg=PANEL);row.pack(fill='x',padx=10,pady=(14,3))
        Label(row,text='保护角度',anchor='w').pack(side='left');Label(row,textvariable=self.angle_text).pack(side='right')
        control=PixelScale(self.group_panel,from_=5,to=75,resolution=5);control.set(self.angle.get());control.configure(command=self.set_angle);control.pack(fill='x',padx=10)
        Label(self.group_panel,text='超过角度时整组恢复普通 UV。',wrap=True,anchor='w').pack(fill='x',padx=10,pady=5)
        Label(self.group_panel,text='保护组',anchor='w').pack(fill='x',padx=10,pady=(14,4))
        for i,group in enumerate(self.groups):
            card=tk.Frame(self.group_panel,bg='#e5d6bd');card.pack(fill='x',padx=8,pady=5)
            title=f'{i+1} · {len(group["pixels"])} px · {group.get("angle",40):g}°'
            Label(card,text=title,anchor='w',bg='#e5d6bd').pack(fill='x',padx=6,pady=4)
            Label(card,text=' + '.join(f[:1].upper() if f!='bottom' else 'D' for f in group_faces(group)),anchor='w',bg='#e5d6bd').pack(fill='x',padx=6)
            row=tk.Frame(card,bg='#e5d6bd');row.pack(fill='x',padx=3,pady=4);row.columnconfigure((0,1),weight=1)
            self.button(row,'编辑',lambda j=i:self.edit_group(j)).grid(row=0,column=0,sticky='ew',padx=2)
            self.button(row,'删除',lambda j=i:self.remove_group(j)).grid(row=0,column=1,sticky='ew',padx=2)
        Label(self.group_panel,text='可跨 UV 面选择。\n滚轮缩放；中键或空格拖动。\n右键减选；Shift 加选，Ctrl 减选。',wrap=True,anchor='w',justify='left',fg='#75695b').pack(fill='x',padx=10,pady=14)
    rebuild_groups=refresh_groups
    def set_angle(self,value):self.angle.set(float(value));self.angle_text.set(f'{float(value):g}°')
    def edit_group(self,index):
        self.checkpoint();self.editing=index;self.selection=set(map(tuple,self.groups[index]['pixels']));self.set_angle(self.groups[index].get('angle',40.));self.refresh_groups();self.draw()
    def clear_selection(self):
        self.checkpoint();self.selection=set();self.editing=None;self.refresh_groups();self.draw();self.status.set('')
    def fit(self):self.auto_fit=True;self.draw()
    def set_zoom(self,value,center=None):
        center=center or (self.canvas.winfo_width()/2,self.canvas.winfo_height()/2)
        self.auto_fit=False;old=self.zoom;ox,oy=self.offset or (0,0)
        point=((center[0]-ox)/old,(center[1]-oy)/old);self.zoom=max(1,min(64,int(value)))
        self.offset=(round(center[0]-point[0]*self.zoom),round(center[1]-point[1]*self.zoom));self.draw()
    def change_zoom(self,delta,center=None):
        steps=(1,2,3,4,6,8,12,16,24,32,48,64)
        candidates=[z for z in steps if z>self.zoom] if delta>0 else [z for z in steps if z<self.zoom]
        if candidates:self.set_zoom(min(candidates) if delta>0 else max(candidates),center)
    def wheel(self,event):self.change_zoom(1 if event.delta>0 else -1,(event.x,event.y));return 'break'
    def draw(self,event=None):
        if not self.winfo_exists() or not hasattr(self,'image'):return
        w,h=self.image.size;cw,ch=max(1,self.canvas.winfo_width()),max(1,self.canvas.winfo_height())
        if self.offset is None or self.auto_fit:
            rects=list(self.resource['layout']['rects'].values())
            x0=min(x for x,y,fw,fh in rects);y0=min(y for x,y,fw,fh in rects)
            x1=max(x+fw for x,y,fw,fh in rects);y1=max(y+fh for x,y,fw,fh in rects)
            self.zoom=max(1,min(64,(cw-24)//(x1-x0),(ch-24)//(y1-y0)))
            self.offset=(round(cw/2-(x0+x1)*self.zoom/2),round(ch/2-(y0+y1)*self.zoom/2))
        z=self.zoom;ox,oy=self.offset;c=self.canvas
        if self.photo_zoom!=z:self.photo=ImageTk.PhotoImage(self.image.resize((w*z,h*z),Image.Resampling.NEAREST),master=self);self.photo_zoom=z
        c.delete('all');c.create_image(ox,oy,anchor='nw',image=self.photo)
        if self.grid.get() and z>=5:
            for x in range(max(0,(-ox)//z),min(w,(cw-ox)//z)+1):c.create_line(ox+x*z,max(0,oy),ox+x*z,min(ch,oy+h*z),fill='#8a8175')
            for y in range(max(0,(-oy)//z),min(h,(ch-oy)//z)+1):c.create_line(max(0,ox),oy+y*z,min(cw,ox+w*z),oy+y*z,fill='#8a8175')
        for face,(x,y,fw,fh) in self.resource['layout']['rects'].items():c.create_rectangle(ox+x*z,oy+y*z,ox+(x+fw)*z,oy+(y+fh)*z,outline='#e7a34c',width=2)
        for i,group in enumerate(self.groups):
            if i==self.editing:continue
            for x,y in group['pixels']:
                if -z<ox+x*z<cw and -z<oy+y*z<ch:c.create_rectangle(ox+x*z+1,oy+y*z+1,ox+(x+1)*z-1,oy+(y+1)*z-1,outline='#4ee2d4',width=2 if z>=7 else 1)
        for x,y in self.selection:
            if -z<ox+x*z<cw and -z<oy+y*z<ch:c.create_rectangle(ox+x*z+1,oy+y*z+1,ox+(x+1)*z-1,oy+(y+1)*z-1,fill=ACC,stipple='gray50',outline='#fff9eb')
        self.counter.set(f'{len(self.selection)} px');self.zoom_label.set(f'{z}x')
    def pixel(self,event):
        if self.offset is None:return None
        x=(event.x-self.offset[0])//self.zoom;y=(event.y-self.offset[1])//self.zoom
        w,h=self.resource['layout']['size']
        return (x,y) if 0<=x<w and 0<=y<h else None
    def hover(self,event):
        point=self.pixel(event)
        if point:
            face=pixel_face(self.resource,point)
            self.status.set(f'{face or "—"}  {point[0]}, {point[1]}')
    def begin_pan(self,event):self.pan_start=(event.x,event.y,self.offset);self.auto_fit=False;return 'break'
    def move_pan(self,event):
        if self.pan_start:
            x,y,(ox,oy)=self.pan_start;self.offset=(ox+event.x-x,oy+event.y-y);self.draw()
        return 'break'
    def end_pan(self,event=None):self.pan_start=None;return 'break'
    def begin(self,event,erase=False):
        self.canvas.focus_set()
        if self.space:return self.begin_pan(event)
        point=self.pixel(event)
        if point is None:return
        self.checkpoint();self.start=point;self.last_pixel=point
        self.mode='subtract' if erase or event.state&4 else 'add' if event.state&1 else self.operation
        if self.tool=='brush':
            if self.mode=='replace':self.selection=set()
            self.paint(point,point);self.draw()
        else:self.drag(event)
    def paint(self,a,b):
        count=max(abs(b[0]-a[0]),abs(b[1]-a[1]))+1
        pixels={tuple(map(int,p)) for p in np.floor(np.linspace(a,b,count)+.5).astype(int)}
        pixels={p for p in pixels if pixel_face(self.resource,p)}
        if self.mode=='subtract':self.selection-=pixels
        else:self.selection|=pixels
    def drag(self,event):
        if self.pan_start:return self.move_pan(event)
        point=self.pixel(event)
        if self.start is None or point is None:return
        if self.tool=='brush':self.paint(self.last_pixel,point);self.last_pixel=point;self.draw();return
        self.last_pixel=point
        x,y=self.start;tx,ty=point;z=self.zoom;ox,oy=self.offset;self.canvas.delete('drag')
        self.canvas.create_rectangle(ox+min(x,tx)*z,oy+min(y,ty)*z,ox+(max(x,tx)+1)*z,oy+(max(y,ty)+1)*z,outline='#ffffff',width=2,tags='drag')
    def end(self,event):
        if self.pan_start:return self.end_pan(event)
        if self.start is None:return
        point=self.pixel(event) or self.last_pixel
        if self.tool=='box':
            x,y=self.start;tx,ty=point
            pixels={(px,py) for px in range(min(x,tx),max(x,tx)+1) for py in range(min(y,ty),max(y,ty)+1) if pixel_face(self.resource,(px,py))}
            if self.mode=='subtract':self.selection-=pixels
            elif self.mode=='add':self.selection|=pixels
            else:self.selection=pixels
        else:self.paint(self.last_pixel,point)
        self.start=None;self.draw()
    def add_group(self):
        if not self.selection:return
        occupied={tuple(p) for i,g in enumerate(self.groups) if i!=self.editing for p in g['pixels']}
        if self.selection&occupied:self.status.set(tr('像素已属于其他保护组，请先删除旧组。'));return
        candidate=valid_groups({**self.resource,'protected_groups':[{'pixels':[list(p) for p in sorted(self.selection)],'angle':self.angle.get()}]})
        if not candidate:return
        self.checkpoint()
        if self.editing is None:self.groups.append(candidate[0])
        else:self.groups[self.editing]=candidate[0]
        self.editing=None;self.selection=set();self.refresh_groups();self.draw();self.status.set(tr('保护组已建立；应用后在角色预览中查看。'))
    def remove_group(self,index):
        self.checkpoint();del self.groups[index]
        if self.editing==index:self.editing=None;self.selection=set()
        elif self.editing is not None and self.editing>index:self.editing-=1
        self.refresh_groups();self.draw()
    def undo(self):
        if self.history:
            self.groups,self.selection,self.editing,angle=self.history.pop();self.set_angle(angle);self.refresh_groups();self.draw()
    def apply(self):
        if self.selection:self.status.set(tr('还有未建立保护组的选择，请先保护或清除。'));return
        self.owner.snapshot();self.owner.project['textures'][self.part]['protected_groups']=copy.deepcopy(self.groups)
        self.owner.changed();self.owner.populate();self.destroy()
