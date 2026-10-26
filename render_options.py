"""Native canvas and pixel-light settings shared by preview, controls and export."""
import math

DEFAULTS=dict(canvas_width=64,canvas_height=64,lighting=False,self_shadow=False,shadow_strength=.65,
              light_style='painted',light_angle=315.,light_height=55.,light_strength=.65,
              light_color='#fff0ce',shadow_color='#655478')

def number(value,default,lo,hi):
    try:value=float(value)
    except (TypeError,ValueError):return default
    return max(lo,min(hi,value)) if math.isfinite(value) else default

def normalized(settings=None):
    result={**DEFAULTS,**(settings or {})}
    if result['light_style'] not in ('painted','facet'):result['light_style']='painted'
    # Earlier local lighting projects implicitly enabled self shadows.
    if settings and 'self_shadow' not in settings and settings.get('lighting') is True:result['self_shadow']=True
    for key in ('lighting','self_shadow'):
        if not isinstance(result[key],bool):result[key]=DEFAULTS[key]
    for key in ('canvas_width','canvas_height'):result[key]=int(number(result[key],64,32,256))
    for key,lo,hi in (('light_angle',0,360),('light_height',5,85),('light_strength',0,1),('shadow_strength',0,1)):
        result[key]=number(result[key],DEFAULTS[key],lo,hi)
    for key in ('light_color','shadow_color'):
        value=result[key]
        try:assert isinstance(value,str) and len(value)==7 and value[0]=='#';int(value[1:],16)
        except (AssertionError,ValueError,TypeError):result[key]=DEFAULTS[key]
    return result

def size(settings=None):
    s=normalized(settings);return s['canvas_width'],s['canvas_height']

def offset(settings=None):
    w,h=size(settings);return ((w-64)/2,h-64)

def fit(width,height,settings=None):
    w,h=size(settings);ratio=max(.01,min(width/w,height/h))
    factor=max(1,math.floor(ratio)) if ratio>=1 else 1/math.ceil(1/ratio)
    return max(1,round(w*factor)),max(1,round(h*factor))

def joints(pose,settings=None):
    import rig
    dx,dy=offset(settings)
    return {k:{name:(x+dx,y+dy) for name,(x,y) in chain.items()} for k,chain in rig.joints(pose).items()}

def target(point,settings=None):
    dx,dy=offset(settings);return point[0]-dx,point[1]-dy
