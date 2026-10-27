"""Arrange ordinary motion layers into an editable sequence, without keyframes."""
import copy
import engine as E

STEPS={
 'punchR':('右手直拳','thrust',{'side':'right'}),
 'punchL':('左手直拳','thrust',{'side':'left'}),
 'pushR':('右腿踹击','kick',{'side':'right','style':'push'}),
 'pushL':('左腿踹击','kick',{'side':'left','style':'push'}),
 'swing':('挥击','swing',{}),
 'jump':('跳跃','jump',{}),
 'roll':('翻滚','roll',{'contact':'auto'}),
 'wave':('挥手','wave',{'side':'right'}),
 'bow':('鞠躬','bow',{})}

def build(current,steps,frames=12,fade=.12):
 """Keep appearance/base/controls; replace layers with evenly spaced actions."""
 if not isinstance(steps,(list,tuple)) or not 1<=len(steps)<=6 or any(k not in STEPS for k in steps):
  raise ValueError('请选择一至六步动作。')
 if isinstance(frames,bool) or not isinstance(frames,int) or not 6<=frames<=20:
  raise ValueError('每步帧数应为6至20。')
 if not isinstance(fade,(int,float)) or isinstance(fade,bool) or not 0<=fade<=.3:
  raise ValueError('Invalid transition')
 result=copy.deepcopy(current);count=len(steps);total=count*frames
 seconds=total/result.get('fps',12)
 # Preserve a walking/running base's cadence when the sequence gets longer.
 if result['base']['kind'] in ('walk','run'):
  result['base']['cycles']=result['base'].get('cycles',1)*seconds/max(.01,result.get('seconds',2))
  result['base_playback']='loop'
 else:result.pop('base_playback',None)
 result.pop('pose',None);result.pop('auto_name_key',None)
 result.update(name='ActionSequence',seconds=seconds,playback='once',layers=[])
 for index,key in enumerate(steps):
  _,kind,options=STEPS[key];entry=E.entry(kind);entry.update(options)
  entry.update(start=index/count,end=(index+1)/count,mode='once',cycles=1,phase=0.,
               scope='all',blend='add',mix=1.,retain=0.,fade=float(fade))
  result['layers'].append(entry)
 return result

def show(owner):
 import tkinter as tk
 from tkinter import messagebox
 import localized_ui as UI
 from pixel_ui import PixelButton,PixelOption,ScrollPanel,ellipsize
 from i18n import tr
 dialog=tk.Toplevel(owner);dialog.title(tr('动作串联'));dialog.transient(owner)
 dialog.ui_scale=owner.ui_scale;dialog.ui_font=owner.caption_font;dialog.caption_font=owner.caption_font
 dialog.configure(bg='#ece4d8')
 sw,sh=owner.winfo_screenwidth(),owner.winfo_screenheight()
 width=min(sw-80,max(1040,round(1040*owner.ui_scale)));height=min(sh-100,max(720,round(720*owner.ui_scale)))
 dialog.geometry(f'{width}x{height}+{max(20,(sw-width)//2)}+{max(20,(sh-height)//2)}')
 dialog.minsize(min(sw-80,max(920,round(880*owner.ui_scale))),min(sh-100,660))
 selected=['punchR','punchL','pushR']
 summary=tk.StringVar(master=dialog)
 header=tk.Frame(dialog,bg='#f8f0df');header.pack(fill='x',padx=18,pady=(16,10))
 UI.Label(header,text='动作串联',font=owner.ui_font,anchor='w').pack(fill='x',padx=12,pady=(10,4))
 UI.Label(header,text='选择动作、调整顺序，自动安排先后和过渡。',wrap=True,justify='left',anchor='w',font=owner.caption_font).pack(fill='x',padx=12,pady=(0,10))
 footer=tk.Frame(dialog,bg='#f8f0df');footer.pack(side='bottom',fill='x',padx=18,pady=(10,16))
 body=tk.Frame(dialog,bg='#ece4d8');body.pack(fill='both',expand=True,padx=18)
 body.columnconfigure(0,weight=3,uniform='sequence');body.columnconfigure(1,weight=2,uniform='sequence');body.rowconfigure(0,weight=1)
 left=tk.Frame(body,bg='#f8f0df');left.grid(row=0,column=0,sticky='nsew',padx=(0,12))
 settings_shell=tk.Frame(body,bg='#f8f0df');settings_shell.grid(row=0,column=1,sticky='nsew')
 dialog.sequence_panels=(left,settings_shell)
 settings_scroll=ScrollPanel(settings_shell);settings_scroll.pack(fill='both',expand=True);settings=settings_scroll.content
 UI.Label(left,text='动作顺序',anchor='w',font=owner.caption_font).pack(fill='x',padx=14,pady=(12,8))
 bar=tk.Frame(left,bg='#f8f0df');bar.pack(fill='x',padx=12,pady=(0,8));bar.columnconfigure(0,weight=1)
 choices={tr(label):key for key,(label,_,_) in STEPS.items()}
 choice=tk.StringVar(master=dialog,value=tr(STEPS['punchR'][0]))
 PixelOption(bar,choice,*choices).grid(row=0,column=0,sticky='ew',padx=(0,8))
 listing=tk.Listbox(left,height=6,exportselection=False,activestyle='none',font=owner.ui_font,bg='#e5d6bd',fg='#493c32',selectbackground='#e7a34c',selectforeground='#493c32',bd=0,highlightthickness=0)
 def refresh(index=0):
  listing.delete(0,'end')
  for i,key in enumerate(selected):listing.insert('end',f'{i+1}. {tr(STEPS[key][0])}')
  if selected:listing.selection_set(max(0,min(index,len(selected)-1)))
  add_button.configure(state='disabled' if len(selected)>=6 else 'normal')
  apply_button.configure(state='normal' if selected else 'disabled')
  for button,disabled in ((up_button,not selected or index<=0),(down_button,not selected or index>=len(selected)-1),(remove_button,not selected)):button.configure(state='disabled' if disabled else 'normal')
  total=len(selected)*int(frames.get());fps=owner.project.get('fps',12)
  summary.set(f"{tr('总帧数')}  {total}\n{total/fps:g} s  ·  {fps} FPS")
  draw_timeline()
 def add():
  if len(selected)<6:selected.append(choices[choice.get()]);refresh(len(selected)-1)
 def move(delta):
  if not listing.curselection():return
  index=listing.curselection()[0];target=index+delta
  if 0<=target<len(selected):selected[index],selected[target]=selected[target],selected[index];refresh(target)
 def remove():
  if listing.curselection():index=listing.curselection()[0];selected.pop(index);refresh(index)
 add_button=PixelButton(bar,text='＋ 添加',command=add);add_button.grid(row=0,column=1,sticky='ew')
 listing.pack(fill='x',padx=14,pady=(0,10))
 order=tk.Frame(left,bg='#f8f0df');order.pack(fill='x',padx=12,pady=(0,12));order.columnconfigure((0,1,2),weight=1,uniform='order')
 up_button=PixelButton(order,text='上移',command=lambda:move(-1));down_button=PixelButton(order,text='下移',command=lambda:move(1));remove_button=PixelButton(order,text='移除',command=remove)
 for column,button in enumerate((up_button,down_button,remove_button)):button.grid(row=0,column=column,sticky='ew',padx=3)
 UI.Label(left,text='时间安排',anchor='w',font=owner.caption_font).pack(fill='x',padx=14,pady=(8,2))
 timeline=tk.Canvas(left,height=round(96*owner.ui_scale),bg='#f8f0df',highlightthickness=0);timeline.pack(fill='x',padx=14,pady=(0,12))
 def draw_timeline(event=None):
  timeline.delete('all');width=timeline.winfo_width();height=timeline.winfo_height()
  if width<10 or not selected:return
  active=listing.curselection()[0] if listing.curselection() else 0;cell=width/len(selected);pad=round(5*owner.ui_scale)
  for i,key in enumerate(selected):
   x0=i*cell+2;x1=(i+1)*cell-2
   timeline.create_rectangle(x0,4,x1,height-4,fill='#e7a34c' if i==active else '#e5d6bd',outline='#aa957d')
   title=ellipsize(f'{i+1}. {tr(STEPS[key][0])}',owner.caption_font,max(8,cell-pad*2))
   timeline.create_text(x0+pad,height*.32,text=title,font=owner.caption_font,fill='#493c32',anchor='w')
   timeline.create_text(x0+pad,height*.7,text=f'{int(frames.get())} f',font=owner.caption_font,fill='#493c32',anchor='w')
 timeline.bind('<Configure>',draw_timeline)
 timeline.bind('<Button-1>',lambda event:refresh(min(len(selected)-1,max(0,int(event.x/max(1,timeline.winfo_width())*len(selected))))) if selected else None)
 listing.bind('<<ListboxSelect>>',lambda _:refresh(listing.curselection()[0] if listing.curselection() else 0))
 UI.Label(settings,text='每步帧数',anchor='w',font=owner.caption_font).pack(fill='x',padx=14,pady=(14,4))
 frames=tk.StringVar(master=dialog,value='12')
 PixelOption(settings,frames,*map(str,(6,8,10,12,16,20)),command=lambda _:refresh(listing.curselection()[0] if listing.curselection() else 0)).pack(fill='x',padx=14,pady=(0,12))
 UI.Label(settings,text='动作过渡',anchor='w',font=owner.caption_font).pack(fill='x',padx=14,pady=(4,4))
 transitions={tr('柔和'):.18,tr('利落'):.08,tr('直接'):0.}
 transition=tk.StringVar(master=dialog,value=tr('利落'))
 PixelOption(settings,transition,*transitions).pack(fill='x',padx=14,pady=(0,14))
 UI.Label(settings,textvariable=summary,font=owner.caption_font,anchor='w',justify='left',bg='#e5d6bd').pack(fill='x',padx=14,pady=10,ipadx=8,ipady=12)
 UI.Label(settings,text='保留角色、基础动作和姿态控制；替换叠加动作，可撤销。生成后仍可逐项修改。',wrap=True,justify='left',anchor='w',font=owner.caption_font).pack(fill='x',padx=14,pady=12)
 def apply():
  try:project=build(owner.project,selected,int(frames.get()),transitions[transition.get()])
  except (ValueError,KeyError) as ex:messagebox.showerror(tr('动作串联'),tr(str(ex)),parent=dialog);return
  owner.snapshot();owner.stop();owner.project=project;owner.frame=0
  owner.sync(('layer',0));owner.changed();dialog.destroy()
 PixelButton(footer,text='取消',command=dialog.destroy).pack(side='right',padx=4,pady=8)
 apply_button=PixelButton(footer,text='生成串联动作',command=apply,accent=True);apply_button.pack(side='right',padx=10,pady=8)
 refresh();dialog.grab_set()
 # Expose semantic actions for real-widget regression checks.
 dialog.steps=selected;dialog.apply_sequence=apply;dialog.move_step=move;dialog.step_list=listing
 return dialog
