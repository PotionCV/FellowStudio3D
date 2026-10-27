"""Native canvas and pixel-light settings shared by preview, controls and export."""
import math

DEFAULTS=dict(canvas_width=64,canvas_height=64,retro_animation=False,lighting=False,self_shadow=False,shadow_strength=.65,
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
    for key in ('lighting','self_shadow','retro_animation'):
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

def point(point,pose,settings=None):
    """Map base rig pixels to native canvas pixels without changing IK units."""
    import model_data as M
    density=M.pixel_density(pose.get('_model'));dx,dy=offset(settings)
    camera=math.floor(pose.get('_camera_y',0)+.5);x,y=point
    if density==1:return x+dx,y+dy
    return 31.5+(x-31.5)*density+dx,55.5+(y-55.5-camera)*density+camera+dy


def joints(pose,settings=None):
    import rig
    return {k:{name:point(value,pose,settings) for name,value in chain.items()} for k,chain in rig.joints(pose).items()}


def target(value,settings=None,pose=None):
    import model_data as M
    pose=pose or {};density=M.pixel_density(pose.get('_model'));dx,dy=offset(settings)
    camera=math.floor(pose.get('_camera_y',0)+.5);x,y=value
    if density==1:return x-dx,y-dy
    return 31.5+(x-dx-31.5)/density,55.5+(y-dy-55.5-camera)/density+camera
