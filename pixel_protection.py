"""User-selected UV texels rendered as rigid integer-grid groups.

No color classification: the selection is the only definition of a motif.
Groups return to ordinary UV sampling when their surface turns edge-on.
"""
import numpy as np


def pixel_face(resource, pixel):
    px,py=pixel
    return next((face for face,(x,y,w,h) in resource['layout']['rects'].items() if x<=px<x+w and y<=py<y+h),None)


def group_faces(group):
    return group.get('faces') or [group.get('face')]


def valid_groups(resource):
    groups = []
    for group in resource.get('protected_groups', []):
        if not isinstance(group,dict):continue
        pixels = sorted({(int(p[0]), int(p[1])) for p in group.get('pixels', [])
                         if isinstance(p,(list,tuple)) and len(p)==2 and all(isinstance(v,(int,float)) and np.isfinite(v) for v in p) and pixel_face(resource,p)})
        if pixels:
            faces=sorted({pixel_face(resource,p) for p in pixels})
            item=dict(pixels=[list(p) for p in pixels])
            if len(faces)==1:item['face']=faces[0]
            else:item['faces']=faces
            if isinstance(group.get('angle'),(int,float)) and np.isfinite(group['angle']):item['angle']=max(5.,min(75.,float(group['angle'])))
            groups.append(item)
    return groups


def resize_groups(resource, layout):
    """Explicit nearest-neighbor mask resize follows the same UV face repack."""
    from PIL import Image
    result = []
    for group in valid_groups(resource):
        pixels=[]
        for face in group_faces(group):
            ox,oy,ow,oh=resource['layout']['rects'][face];x,y,w,h=layout['rects'][face]
            mask=np.zeros((oh,ow),np.uint8)
            for px,py in group['pixels']:
                if ox<=px<ox+ow and oy<=py<oy+oh:mask[py-oy,px-ox]=255
            mask=np.array(Image.fromarray(mask).resize((w,h),Image.Resampling.NEAREST));yy,xx=np.nonzero(mask)
            pixels.extend([list(p) for p in zip((xx+x).tolist(),(yy+y).tolist())])
        if pixels:result.extend(valid_groups({'layout':layout,'protected_groups':[{**group,'pixels':pixels}]}))
    return result


def _prepare_single(triangles, q, textures, resources, enabled=True):
    """Return cleaned sampling textures and rigid screen-space patches.

    q includes camera projection and all grid snapping used by the rasterizer.
    Only groups on sufficiently front-facing surfaces are activated.
    """
    if not enabled or not resources:
        return textures, []
    cleaned = dict(textures); patches = []
    for part, resource in resources.items():
        groups = valid_groups(resource)
        if not groups:
            continue
        original = textures[part]; active = []
        for group in groups:
            if len(group_faces(group))!=1:continue
            pixels = np.array(group['pixels'], int)
            anchor = (pixels.min(axis=0)+pixels.max(axis=0))//2
            candidates = []
            for i, (tri_part, face, world, uv) in enumerate(triangles):
                if tri_part != part or face != group['face']:
                    continue
                matrix = (uv[1:]-uv[0]).T
                if abs(np.linalg.det(matrix)) < 1e-9:
                    continue
                weights = np.linalg.solve(matrix, anchor-uv[0])
                if weights.min() < -1e-7 or weights.sum() > 1+1e-7:
                    continue
                tri = q[i]
                normal = np.cross(tri[1]-tri[0], tri[2]-tri[0])
                facing = abs(normal[2])/max(1e-9, np.linalg.norm(normal))
                limit=np.radians(group.get('angle',40.))
                if facing < np.cos(limit):
                    continue
                point = tri[0]+weights @ (tri[1:]-tri[0])
                derivative = (tri[1:]-tri[0]).T @ np.linalg.inv(matrix)
                # Snap in-plane orientation to quarter turns. Never resample a motif.
                angle = np.arctan2(derivative[1, 0], derivative[0, 0])
                if abs(np.arctan2(np.sin(angle),abs(np.cos(angle))))>limit:continue
                turn = int(np.floor(angle/(np.pi/2)+.5)) % 4
                rotations = (np.array(((1,0),(0,1))), np.array(((0,-1),(1,0))),
                             np.array(((-1,0),(0,-1))), np.array(((0,1),(-1,0))))
                rotation = rotations[turn]
                # UV charts can have opposite handedness on an inside/back surface.
                if np.linalg.det(derivative[:2]) < 0:
                    rotation = rotation @ np.diag((1,-1))
                screen = np.floor(point[:2]+.5).astype(int)+(pixels-anchor) @ rotation.T
                candidates.append((point[2], screen, pixels))
            if candidates:
                _, screen, pixels = max(candidates, key=lambda item:item[0])
                active.append(group)
                patches.append((part, screen, original[pixels[:,1], pixels[:,0]].copy()))
        if not active:
            continue
        tex = original.copy()
        # Remove each original motif only when its rigid replacement is active.
        # Fill from the nearest unprotected texel on the same UV face.
        for face in {g['face'] for g in active}:
            x,y,w,h = resource['layout']['rects'][face]
            mask = np.zeros((h,w),bool)
            for group in active:
                if group['face'] == face:
                    for px,py in group['pixels']:
                        mask[py-y,px-x] = original[py,px,3]>=128
            source = original[y:y+h,x:x+w]
            donors = np.argwhere(~mask & (source[:,:,3]>=128))
            targets = np.argwhere(mask)
            if len(donors):
                # Small face-local operation; no frame-sized nearest-neighbor search.
                for ty,tx in targets:
                    dy,dx = donors[np.argmin(((donors-(ty,tx))**2).sum(axis=1))]
                    tex[y+ty,x+tx] = source[dy,dx]
            else:
                from uv_assets import COLORS
                for ty,tx in targets:
                    tex[y+ty,x+tx] = (*COLORS[part],255)
        cleaned[part] = tex
    return cleaned, patches


def build_reference(triangles,group):
    """Bind a group once to the model surface, including atlas seams.

    Multi-face offsets are a single quantized reference projection, never the
    unfolded atlas coordinates. Single-face motifs retain native texel spacing.
    """
    pixels=np.array(group['pixels'],int);points=np.zeros((len(pixels),3));normals=np.zeros_like(points);scores=np.full(len(pixels),-np.inf)
    faces=group_faces(group);point_faces=np.empty(len(pixels),object);point_faces[:]=None
    derivatives={}
    for face,world,uv in triangles:
        if face not in faces:continue
        matrix=(uv[1:]-uv[0]).T;det=np.linalg.det(matrix)
        if abs(det)<1e-9:continue
        inverse=np.linalg.inv(matrix);weights=(pixels-uv[0])@inverse.T
        hit=(weights.min(axis=1)>=-1e-7)&(weights.sum(axis=1)<=1+1e-7)
        normal=np.cross(world[1]-world[0],world[2]-world[0]);normal/=max(1e-9,np.linalg.norm(normal))
        # A UV chart can cover a cap and a side: favor the less skewed triangle.
        derivative=(world[1:]-world[0]).T@inverse
        quality=abs(det)/max(1e-9,np.linalg.norm(np.cross(world[1]-world[0],world[2]-world[0])))
        hit&=quality>scores
        points[hit]=world[0]+weights[hit]@(world[1:]-world[0]);normals[hit]=normal;scores[hit]=quality;point_faces[hit]=face
        if hit.any():derivatives[face]=derivative
    mapped=np.isfinite(scores)
    if not mapped.any():return None
    # Equal face weights keep a seam centered even with an uneven selection.
    face_normals=[normals[mapped&(point_faces==face)].mean(axis=0) for face in faces if np.any(mapped&(point_faces==face))]
    normal=np.sum(face_normals,axis=0);length=np.linalg.norm(normal)
    if length<.1:return None
    normal/=length
    up=np.array((0.,1.,0.)) if abs(normal[1])<.9 else np.array((0.,0.,-1.))
    right=np.cross(up,normal);right/=np.linalg.norm(right);down=-np.cross(normal,right)
    # Texels on the hidden side of an over-wrapped selection stay ordinary UV.
    mapped&=normals@normal>.05
    if not mapped.any():return None
    points=points[mapped];pixels=pixels[mapped];anchor=points.mean(axis=0)
    if len(faces)==1:
        uv_anchor=(pixels.min(axis=0)+pixels.max(axis=0))//2
        native=pixels-uv_anchor
        # Anchor the same UV texel used by the integer motif offsets. A surface
        # centroid shifts asymmetric selections (e.g. a diamond) by whole pixels.
        best=-np.inf
        for face,world,uv in triangles:
            if face!=faces[0]:continue
            matrix=(uv[1:]-uv[0]).T;det=np.linalg.det(matrix)
            if abs(det)<1e-9:continue
            weights=np.linalg.solve(matrix,uv_anchor-uv[0])
            if weights.min() < -1e-7 or weights.sum()>1+1e-7:continue
            quality=abs(det)/max(1e-9,np.linalg.norm(np.cross(world[1]-world[0],world[2]-world[0])))
            if quality>best:anchor=world[0]+weights@(world[1:]-world[0]);best=quality
        derivative=derivatives[faces[0]]
        basis=np.array((right,down))@derivative
        basis/=np.maximum(1e-9,np.linalg.norm(basis,axis=0))
        transforms=[np.array(t) for t in (((1,0),(0,1)),((-1,0),(0,1)),((1,0),(0,-1)),((-1,0),(0,-1)),((0,1),(1,0)),((0,-1),(1,0)),((0,1),(-1,0)),((0,-1),(-1,0)))]
        rotation=min(transforms,key=lambda matrix:np.linalg.norm(matrix-basis))
        offsets=native@rotation.T
    else:
        continuous=(points-anchor)@np.array((right,down)).T
        # Resolve minification collisions once, in deterministic UV order. The
        # result is cached with the model, so no per-frame texel rearrangement.
        offsets=np.floor(continuous+.5).astype(int);used=set()
        for index,target in enumerate(continuous):
            preferred=offsets[index];candidate=tuple(preferred)
            if candidate in used:
                for radius in range(1,len(pixels)+1):
                    free=[(preferred[0]+dx,preferred[1]+dy) for dy in range(-radius,radius+1) for dx in range(-radius,radius+1) if max(abs(dx),abs(dy))==radius and (preferred[0]+dx,preferred[1]+dy) not in used]
                    if free:
                        candidate=min(free,key=lambda p:((np.array(p)-target)**2).sum());break
            offsets[index]=candidate;used.add(candidate)
    return dict(anchor=anchor,normal=normal,right=right,pixels=pixels,offsets=offsets,angle=group.get('angle',40.))


def prepare(triangles,q,textures,resources,enabled=True,frames=None):
    if not frames:return _prepare_single(triangles,q,textures,resources,enabled)
    if not enabled:return textures,[]
    cleaned=dict(textures);patches=[]
    for part,data in frames.items():
        resource=resources[part];original=textures[part];active=[]
        for index,reference in enumerate(data['references']):
            if reference is None:continue
            frame=data.get('reference_frames',[data]*len(data['references']))[index]
            matrix=frame['matrix'];normal=matrix@reference['normal'];limit=np.radians(reference['angle'])
            # Signed facing plus roll: both turning away and a large in-plane
            # rotation release the entire group instead of forcing a decal.
            if normal[2]/max(1e-9,np.linalg.norm(normal))<np.cos(limit):continue
            axis=matrix@reference['right'];roll=np.arctan2(axis[1],axis[0])
            if abs(roll)>limit:continue
            center=frame['origin']+matrix@reference['anchor'];rounded=np.floor(center[:2]+.5).astype(int)
            # An odd-width motif cannot center exactly on a 64px canvas. Resolve
            # half ties to the left for the body/head, mirrored on right limbs.
            rounded[0]=int(np.floor(center[0]+.5+(1e-7 if part.endswith('R') else -1e-7)))
            screen=rounded+reference['offsets']
            pixels=reference['pixels'];patches.append((part,screen,original[pixels[:,1],pixels[:,0]].copy()));active.extend(map(tuple,pixels))
        if not active:continue
        tex=original.copy();selected=set(active)
        for face,(x,y,w,h) in resource['layout']['rects'].items():
            targets=np.array([(py-y,px-x) for px,py in selected if x<=px<x+w and y<=py<y+h and original[py,px,3]>=128],int)
            if not len(targets):continue
            source=original[y:y+h,x:x+w];mask=np.zeros((h,w),bool);mask[targets[:,0],targets[:,1]]=True;donors=np.argwhere(~mask&(source[:,:,3]>=128))
            for ty,tx in targets:
                if len(donors):
                    dy,dx=donors[np.argmin(((donors-(ty,tx))**2).sum(axis=1))];tex[y+ty,x+tx]=source[dy,dx]
                else:
                    from uv_assets import COLORS
                    tex[y+ty,x+tx]=(*COLORS[part],255)
        cleaned[part]=tex
    return cleaned,patches


def apply(rgb, owner, patches, part_names):
    for part, screen, colors in patches:
        inside = (screen[:,0]>=0)&(screen[:,0]<64)&(screen[:,1]>=0)&(screen[:,1]<64)
        xy = screen[inside]; color = colors[inside]
        if not len(xy):
            continue
        visible = (owner[xy[:,1],xy[:,0]] == part_names.index(part)) & (color[:,3]>=128)
        xy = xy[visible]
        rgb[xy[:,1],xy[:,0]] = color[visible]
