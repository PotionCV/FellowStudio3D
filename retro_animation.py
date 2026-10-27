"""Deterministic local cels: reuse small pose changes instead of rasterizing them.

No image history, blending or palette changes. Each cel is an authored/physical
sample; bounded native-pixel motion groups consecutive samples independently.
The coupled lower-body group preserves sampled foot/contact and breathing IK.
"""
import copy
import math
import numpy as np
import model_data as M
import motion_timing as MT
import render_options as O
import hair

PIXEL_BUDGET = 1.4
CELS_PER_SECOND = 8


def pixel_anchors(pose,bundle):
    """Give each connected group one integer-grid phase, not each triangle.

    Upper/lower segments share an offset, so no artificial crack is introduced
    at their elbow/knee. Head groups retain the existing head pixel lock.
    """
    import rounded_scene as S
    import plush
    g,j,chains,parts,torso,head=S.geometry(pose)
    anchors={'torso':torso[0]}
    for limb in ('armL','armR','legL','legR'):
        names=('upperArm','lowerArm') if limb.startswith('arm') else ('thigh','shin')
        point=chains[limb][-1] if limb.startswith('leg') else chains[limb][0]
        for name in names:anchors[name+limb[-1]]=point
    if plush.active(bundle['model']):
        point=plush.bottom(g);anchors['body']=point
        for item in bundle['model'].get('attachments',[]):
            if item.get('parent','head')=='head':anchors[item['id']]=point
    return anchors


def _timed_cels(seq,project):
    """A drawing rhythm independent of file FPS; retain contact and strike keys.

    Every sampled slot still exists. This is a stepped drawing sequence, not a
    playback speed change. Sparse source clips are never interpolated upwards.
    """
    n=len(seq);seconds=max(.001,float(project.get('seconds',2)))
    loop=MT.mode(project)=='loop'
    duration=seconds/(n if loop else max(1,n-1))
    contacts=[(p.get('_ground'),p.get('_feet_ground')) for p in seq]
    cuts={0,n}
    for i in range(1,n):
        if int(i*duration*CELS_PER_SECOND+1e-9)!=int((i-1)*duration*CELS_PER_SECOND+1e-9) or contacts[i]!=contacts[i-1]:cuts.add(i)
    # Explicit thrust solvers identify their strongest sampled extension.
    strength=[max(p.get('_thrust_strength',{}).values(),default=0.) for p in seq]
    if max(strength)>0:
        peak=int(np.argmax(strength));cuts.update((peak,min(n,peak+1)))
    if not loop:
        # A one-frame recoil/strike apex must survive the lower drawing rate,
        # including older action generators without explicit strike metadata.
        keys=('armL','armR','legL','legR','rot','lean','body_pitch')
        values=np.array([np.concatenate([np.asarray(p.get(k,0.),dtype=float).reshape(-1) for k in keys]) for p in seq])
        peak=int(np.argmax(np.linalg.norm(values-values[0],axis=1)))
        cuts.update((peak,min(n,peak+1)))
    cuts=sorted(cuts);result=[dict(p) for p in seq]
    for first,last in zip(cuts,cuts[1:]):
        for i in range(first,last):
            j=i if not loop and i in (0,n-1) else first
            result[i]=dict(seq[j])
            # Whole-pixel travel may continue between drawings: pixel shapes
            # should not need redrawing just because the sprite changes place.
            for key in ('dx','dz'):
                if key in seq[i]:result[i][key]=seq[i][key]
    return result


def _groups(seq):
    model=M.normalize(seq[0].get('_model'))
    radians=math.pi/180
    limb=lambda key:sum(model[key][k] for k in ('upper','lower'))
    radius=max(24.,model.get('body',{}).get('height',32.))
    # (channel, estimated native-pixel displacement per unit). All four lower
    # joints stay with their body transform and vertical contact correction.
    body=[(k,radius*radians) for k in ('rot','body_pitch','pelvis_yaw','pelvis','yaw')]
    body += [('dy',1.),('_breath_dy',1.),('leg_scale',max(limb('legL'),limb('legR')))]
    body += [(k,limb(k)*radians) for k in ('legL','legR')]
    yield 'lower',body
    # Do not let a walking leg force tiny chest twists to redraw the whole face.
    yield 'torso',[(k,radius*radians) for k in ('lean','chest_yaw','shoulder')]
    yield 'head',[(k,9*model['head']['size']*radians) for k in ('head','head_pitch','head_yaw')]+[('head_depth',1.)]
    for key in ('armL','armR'):
        yield key,[(key,limb(key)*radians)]
    items=model.get('attachments',[])
    tails=[p for p in items if p.get('kind')=='tail']
    if tails:
        length=max(p.get('length',12.) for p in tails)
        yield 'angles',[('tail',length*radians),('_motion_phase',length*2*math.pi*max(abs(p.get('wag',0)) for p in tails)*radians)]
    for item in items:
        if item.get('kind')=='hair' and item['section']!='cap':
            yield 'angles',[(hair.channel(item),item.get('length',12.)*radians)]


def _extent(low,high):
    return float(np.max(np.linalg.norm(high-low,axis=-1)))


def _signature(seq,channels,kind):
    """Measure geometry, not joint angles: bent knees can cancel one another."""
    if kind=='angles':
        return np.array([np.concatenate([np.asarray(p[k],dtype=float).reshape(-1)*w for k,w in channels])[:,None] for p in seq])
    import rounded_scene as S
    from core3d import ry
    keys=[k for k,w in channels];result=[]
    for p in seq:
        q=dict(seq[0]);q.update({k:p[k] for k in keys})
        g,j,chains,parts,torso,head=S.geometry(q)
        points=[]
        def frame(origin,rotation,dimensions):
            points.append(origin)
            for axis,radius in enumerate(dimensions):
                points.extend((origin+rotation[:,axis]*radius,origin-rotation[:,axis]*radius))
        if kind in ('lower','torso'):
            frame(*torso,(8,12,5));frame(*head,(9,8,8))
            limbs=('legL','legR') if kind=='lower' else ()
            if kind=='torso':points.extend((j['armL']['root'],j['armR']['root']))
        elif kind=='head':
            frame(*head,np.array((8,7.5,7.5))*M.normalize(q.get('_model'))['head']['size']);limbs=()
        else:limbs=(kind,)
        for limb in limbs:
            points.extend(chains[limb])
            for part in (('thigh','shin') if limb.startswith('leg') else ('upperArm','lowerArm')):
                origin,rotation,length,r0,r1=parts[part+limb[-1]]
                frame(origin,rotation,(r0,0,r0));frame(origin-rotation[:,1]*length,rotation,(r1,0,r1))
        result.append(np.array(points)@ry(q.get('yaw',0)).T)
    return np.array(result)


def _cells(values,loop,contacts):
    """Bound the entire interval, not just adjacent frames (no slow drift)."""
    cells=[];start=0;low=high=values[0].copy()
    for i in range(1,len(values)):
        lo=np.minimum(low,values[i]);hi=np.maximum(high,values[i])
        if _extent(lo,hi)>PIXEL_BUDGET or contacts[i]!=contacts[i-1]:
            cells.append(list(range(start,i)));start=i;low=high=values[i].copy()
        else:low,high=lo,hi
    cells.append(list(range(start,len(values))))
    if loop and len(cells)>1 and contacts[0]==contacts[-1]:
        joined=cells[-1]+cells[0];v=values[joined]
        if _extent(v.min(axis=0),v.max(axis=0))<=PIXEL_BUDGET:
            cells=[joined]+cells[1:-1]
    return cells


def stylize(seq,project):
    if not O.normalized(project.get('render'))['retro_animation'] or len(seq)<2:return seq
    seq=_timed_cels(seq,project)
    result=[dict(p) for p in seq];loop=MT.mode(project)=='loop'
    contacts=[(p.get('_ground'),p.get('_feet_ground'),p.get('_breath_ik')) for p in seq]
    for kind,group in _groups(seq):
        channels=[(k,w) for k,w in group if w>0 and all(k in p for p in seq)]
        if not channels:continue
        values=_signature(seq,channels,kind)
        if not np.isfinite(values).all():continue
        for indices in _cells(values,loop,contacts):
            v=values[indices];center=v.mean(axis=0)
            source=indices[int(np.argmin(np.sum(abs(v-center),axis=(1,2))))]
            for i in indices:
                # Preserve exact start/end poses for one-shot/held actions.
                j=i if not loop and i in (0,len(seq)-1) else source
                for k,w in channels:result[i][k]=copy.deepcopy(seq[j][k])
    # Upper-body simplification can change the lowest surface in ground moves
    # (bow/fall/roll), even though the leg/contact drawing remains coupled.
    import engine as E
    for p in result:
        if p.get('_ground'):E.ground_pose(p)
    return result
