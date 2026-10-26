"""Quantized directional lighting and alpha-aware world-space self shadows."""
import math
from functools import lru_cache
import numpy as np
from render_options import normalized

def basis(angle,height):
    a,h=map(math.radians,(angle,height));light=np.array((math.sin(a)*math.cos(h),math.sin(h),math.cos(a)*math.cos(h)))
    right=np.cross((0,1,0),light);right/=np.linalg.norm(right);up=np.cross(light,right)
    return np.array((right,up,light))

def context(triangles,textures,settings,cam=(0,0)):
    s=normalized(settings)
    if not (s['lighting'] and s['light_strength']>0) and not (s['self_shadow'] and s['shadow_strength']>0):return None
    frame=basis(s['light_angle'],s['light_height']);shadow=None
    from core3d import rx,ry
    camera=(rx(cam[1])@ry(cam[0]))[:2];names=tuple(textures);bounds=np.zeros((len(names),4))
    if s['lighting'] and s['light_style']=='painted':
        # Broad sprite-space color blocks, independent of mesh triangulation.
        for index,name in enumerate(names):
            vertices=[t[2] for t in triangles if t[0]==name]
            if vertices:
                q=np.concatenate(vertices)@camera.T;bounds[index]=(*q.min(axis=0),*q.max(axis=0))
    if s['self_shadow'] and s['shadow_strength']>0 and triangles:
        names=tuple(textures);world=np.stack([t[2] for t in triangles]);uv=np.stack([t[3] for t in triangles])
        parts=np.array([names.index(t[0]) for t in triangles],np.int32)
        alphas=tuple((textures[name].shape[:2],textures[name][:,:,3].tobytes()) for name in names)
        shadow=_shadow(world.astype(np.float64).tobytes(),uv.astype(np.float64).tobytes(),parts.tobytes(),alphas,s['light_angle'],s['light_height'])
    return s,frame,shadow,camera,bounds

@lru_cache(maxsize=12)
def _shadow(world_bytes,uv_bytes,parts_bytes,alphas,angle,height):
    world=np.frombuffer(world_bytes,dtype=np.float64).reshape(-1,3,3);uv=np.frombuffer(uv_bytes,dtype=np.float64).reshape(-1,3,2)
    parts=np.frombuffer(parts_bytes,dtype=np.int32);frame=basis(angle,height);points=world@frame.T
    low=points[:,:,:2].min(axis=(0,1))-1;span=points[:,:,:2].max(axis=(0,1))-low+1
    density=min(2.,1020/max(1,float(span.max())));wh=np.ceil(span*density).astype(int)+1
    q=points.copy();q[:,:,:2]=(q[:,:,:2]-low)*density;depth=np.full((wh[1],wh[0]),-np.inf)
    textures=[np.frombuffer(data,dtype=np.uint8).reshape(shape) for shape,data in alphas]
    # Small batches keep raster sample storage bounded for large models.
    for first in range(0,len(q),128):
        v=q[first:first+128];a,b,c=v[:,0],v[:,1],v[:,2]
        lo=np.maximum(0,np.floor(v[:,:,:2].min(axis=1)).astype(int));hi=np.minimum(wh-1,np.ceil(v[:,:,:2].max(axis=1)).astype(int));sizes=np.maximum(0,hi-lo+1)
        den=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1]);areas=sizes[:,0]*sizes[:,1];areas[np.abs(den)<1e-9]=0
        ids=np.repeat(np.arange(len(v)),areas)
        if not len(ids):continue
        local=np.arange(len(ids))-np.repeat(np.cumsum(areas)-areas,areas);x=lo[ids,0]+local%sizes[ids,0];y=lo[ids,1]+local//sizes[ids,0]
        u=((b[ids,1]-c[ids,1])*(x-c[ids,0])+(c[ids,0]-b[ids,0])*(y-c[ids,1]))/den[ids]
        t=((c[ids,1]-a[ids,1])*(x-c[ids,0])+(a[ids,0]-c[ids,0])*(y-c[ids,1]))/den[ids];r=1-u-t
        inside=(u>=-1e-7)&(t>=-1e-7)&(r>=-1e-7);ids=ids[inside];x=x[inside];y=y[inside];u=u[inside];t=t[inside];r=r[inside]
        coords=u[:,None]*uv[first+ids,0]+t[:,None]*uv[first+ids,1]+r[:,None]*uv[first+ids,2]
        opaque=np.zeros(len(ids),bool)
        for index,tex in enumerate(textures):
            mask=parts[first+ids]==index;co=coords[mask]
            ix=np.clip(np.floor(co[:,0]+.5).astype(int),0,tex.shape[1]-1);iy=np.clip(np.floor(co[:,1]+.5).astype(int),0,tex.shape[0]-1);opaque[mask]=tex[iy,ix]>=128
        z=u*a[ids,2]+t*b[ids,2]+r*c[ids,2];np.maximum.at(depth,(y[opaque],x[opaque]),z[opaque])
    return depth,low,density

def shade(rgb,filled,positions,normals,context,parts=None):
    if context is None:return
    settings,frame,shadow,camera,bounds=context;light=frame[2]
    normals=normals/np.maximum(1e-9,np.linalg.norm(normals,axis=1))[:,None];lambert=normals@light
    occluded=np.zeros(len(lambert),bool)
    if shadow is not None:
        depth,low,density=shadow;projected=positions@frame.T;xy=np.floor((projected[:,:2]-low)*density+.5).astype(int)
        valid=(xy[:,0]>=0)&(xy[:,0]<depth.shape[1])&(xy[:,1]>=0)&(xy[:,1]<depth.shape[0])
        # Geometric normal/slope bias avoids stippled shadow acne on slanted faces.
        bias=.6+.45*(1-np.clip(lambert,0,1))
        occluded[valid]=projected[valid,2]+bias[valid]<depth[xy[valid,1],xy[valid,0]]
    strength=settings['light_strength'] if settings['lighting'] else 0
    colors=rgb.reshape(-1,4)[filled,:3].astype(float)
    tint=lambda key:np.array([int(settings[key][i:i+2],16) for i in (1,3,5)],float)
    if settings['light_style']=='painted':
        part_ids=np.zeros(len(positions),int) if parts is None else parts
        boxes=bounds[part_ids];half=np.maximum((boxes[:,2:]-boxes[:,:2])/2,1)
        local=(positions@camera.T-(boxes[:,:2]+boxes[:,2:])/2)/half
        direction=camera@light;direction/=max(.01,np.linalg.norm(direction))
        tone=local@direction
        dark=tone<-.3
        # A single restrained painted highlight; small limbs do not sparkle.
        center=direction*.55;delta=(local-center)/(.38,.30)
        bright=((delta*delta).sum(axis=1)<1)&(tone>.25)&(half[:,0]>=5)&(half[:,1]>=5)
        dark_amount=.28*strength;bright_amount=.18*strength
    else:
        dark=lambert<.2;bright=lambert>=.6;dark_amount=.55*strength;bright_amount=.3*strength
    colors[dark]=colors[dark]*(1-dark_amount)+tint('shadow_color')*dark_amount
    colors[bright]=colors[bright]*(1-bright_amount)+tint('light_color')*bright_amount
    shadow=settings['shadow_strength']*.75
    colors[occluded]=colors[occluded]*(1-shadow)+tint('shadow_color')*shadow
    rgb.reshape(-1,4)[filled,:3]=np.clip(np.floor(colors+.5),0,255).astype(np.uint8)
