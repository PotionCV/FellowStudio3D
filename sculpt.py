"""Continuous, seam-consistent surface deformation in a part's local space."""
import numpy as np

SPECS=[
 ('top_width','顶部宽度',.15,2.,.05,1.,'profile'),('mid_width','中部宽度',.15,2.,.05,1.,'profile'),('bottom_width','底部宽度',.15,2.,.05,1.,'profile'),
 ('top_depth','顶部厚度',.15,2.,.05,1.,'profile'),('mid_depth','中部厚度',.15,2.,.05,1.,'profile'),('bottom_depth','底部厚度',.15,2.,.05,1.,'profile'),
 ('front_top','前侧顶部（px）',-3.,6.,.25,0.,'contour'),('front_mid','前侧中部（px）',-3.,6.,.25,0.,'contour'),('front_bottom','前侧底部（px）',-3.,6.,.25,0.,'contour'),
 ('back_top','后侧顶部（px）',-3.,6.,.25,0.,'contour'),('back_mid','后侧中部（px）',-3.,6.,.25,0.,'contour'),('back_bottom','后侧底部（px）',-3.,6.,.25,0.,'contour'),
 ('curve','中段弯曲（px）',-5.,5.,.25,0.,'contour'),
 ('bulge_length','凸起长度（px）',0.,8.,.25,0.,'bulge'),('bulge_width','凸起宽度',.2,1.2,.05,.7,'bulge'),('bulge_height','凸起高度',.15,1.2,.05,.5,'bulge'),
 ('bulge_y','凸起上下位置',-.8,.8,.05,-.2,'bulge'),('bulge_tip','凸起末端宽度',0.,.85,.05,.45,'bulge')]
DEFAULTS={s[0]:s[5] for s in SPECS}

def values(data):return {k:data.get(k,v) for k,v in DEFAULTS.items()}
def active(data):return any(data.get(k,v)!=v for k,v in DEFAULTS.items())
def record(data):return {k:data[k] for k,v in DEFAULTS.items() if k in data and data[k]!=v}

def deform(local,bounds,data,profile_t=None):
 if not active(data):return local
 v=values(data);lo,hi=bounds;center=(lo+hi)/2;half=np.maximum((hi-lo)/2,.001)
 p=(local-center).copy();original=p.copy();t=np.clip((hi[1]-local[:,1])/(hi[1]-lo[1]),0,1) if profile_t is None else np.clip(profile_t,0,1)
 width=np.interp(t,[0,.5,1],[v['top_width'],v['mid_width'],v['bottom_width']]);depth=np.interp(t,[0,.5,1],[v['top_depth'],v['mid_depth'],v['bottom_depth']])
 p[:,0]*=width;p[:,2]*=depth
 front=np.interp(t,[0,.5,1],[v['front_top'],v['front_mid'],v['front_bottom']]);back=np.interp(t,[0,.5,1],[v['back_top'],v['back_mid'],v['back_bottom']])
 # Clamp inward edits so surfaces cannot cross the center plane.
 p[:,2]+=np.where(original[:,2]>=0,front*np.maximum(0,original[:,2])/half[2],-back*np.maximum(0,-original[:,2])/half[2])
 p[:,2]=np.where(original[:,2]>=0,np.maximum(0,p[:,2]),np.minimum(0,p[:,2]))
 if v['bulge_length']:
  distance=np.maximum(abs(original[:,0])/(half[0]*v['bulge_width']),abs(original[:,1]/half[1]-v['bulge_y'])/v['bulge_height'])
  amount=np.clip((1-distance)/max(.05,1-v['bulge_tip']),0,1);amount=amount*amount*(3-2*amount)
  p[:,2]+=v['bulge_length']*amount*np.clip(original[:,2]/half[2],0,1)**2
 p[:,0]+=v['curve']*np.sin(np.pi*t)
 return p+center

def dimensions(dims,data):
 if not active(data):return dims
 v=values(data);w,h,d=dims
 return (w*max(v[k] for k in ('top_width','mid_width','bottom_width'))+2*abs(v['curve']),h,
         d*max(v[k] for k in ('top_depth','mid_depth','bottom_depth'))+max(0,v['front_top'],v['front_mid'],v['front_bottom'])+max(0,v['back_top'],v['back_mid'],v['back_bottom'])+v['bulge_length'])
