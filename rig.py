"""骨架几何 —— 从姿势反算出各关节在画布上的位置，外加 IK。

编辑器靠这个在预览上画关节手柄、把鼠标拖动翻译成角度。

**这里每一行都必须和 fellow.render 里那段逐字对齐。** 差一点，手柄就会飘在肢体旁边
（画布上表现为"点和胳膊没对上"）。改 fellow.py 的几何时这一份要跟着改 ——
probe.py 会拿真实像素去量，见文件末尾的 __main__。

坐标一律是 64×64 画布坐标，**已经按 pose['flip'] 镜像过**，和画布上看到的对得上。
"""
import math

import fellow as F

N = F.N
KEYS = ('armL', 'armR', 'legL', 'legR')


def spec4(spec):
    """补齐成 4 元组 —— render 允许写成 (lat, bend) 这种短的。"""
    s = tuple(float(x) for x in spec) + (0.0,) * 4
    return s[:4]


# ---------------------------------------------------------------- 骨架
def frame(pose):
    """复刻 render() 里「附着点 → 前倾 → 整体旋转 → 平移」那一段。

    返回 (T, base, shift, yaw, sho, hip)：
      T(p)       中性坐标 → 画布坐标
      base       画面内的整体倾角（直接加在四肢方向角上）
      shift(s)   近侧手臂往身前的横向推量（SIDE_PUSH）
      sho / hip  已经算好的肩/髋附着点（中性空间，未过 T）
    """
    geometry=F.model_geometry(pose);SHO=geometry['sho'];HIP=geometry['hip']
    yaw = F.yaw_of(pose)             # ← 必须走这个函数，见 fellow.CAM_YAW
    pitch = F.pitch_of(pose)         # ← 同理，见 fellow.CAM_PITCH
    psc = F.pitch_scale(pitch)
    lean = pose.get('lean', 0.0)
    rot_d = pose.get('rot', 0.0)
    dx, dy = pose.get('dx', 0.0), pose.get('dy', 0.0)
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    push = F.SIDE_PUSH * sa * abs(sa)

    def anc(d, s, floor):
        off = d[s][0] - F.BODY_X
        return (F.BODY_X + off * ca + math.copysign(floor * abs(sa), off), d[s][1])

    pivot = ((HIP['L'][0] + HIP['R'][0]) / 2, (HIP['L'][1] + HIP['R'][1]) / 2)
    hip = {s: F.add(F.rot(anc(HIP, s, F.FLOOR_HIP), pose.get('pelvis', 0.0), pivot),
                    F.sock(pose, 'off_leg', s)) for s in ('L', 'R')}
    sc = tuple((anc(SHO, 'L', F.FLOOR_SHO)[i] + anc(SHO, 'R', F.FLOOR_SHO)[i]) / 2
               for i in (0, 1))
    sho = {s: F.add(F.rot(anc(SHO, s, F.FLOOR_SHO), pose.get('shoulder', 0.0), sc),
                    F.sock(pose, 'off_arm', s)) for s in ('L', 'R')}

    # 前倾拆成「画面内转角 + 剩下的垂直压缩」，逐字照抄 render（见 fellow.lean_split）
    lean_s, lean_k = F.lean_split(lean, yaw)

    def T(p):
        # ← 垂直前缩（俯仰 × 前倾），见 render
        return F.upper_transform(pose,p,pivot,yaw,pitch)

    near = F.near_arm(pose, yaw, pitch)  # ← 和 render 同一判据（见 fellow.near_arm）

    def shift(side):
        return push if side == near else -push

    return T, -rot_d, shift, yaw, sho, hip, pivot


def _rig(pose, key):
    """'armL' → (根点(含推量), (L1,L2), (r0,r1), yaw, base)"""
    T, base, shift, yaw, sho, hip, _ = frame(pose)
    side = key[-1];limb=F.model_geometry(pose)['limbs'][key]
    if key.startswith('arm'):
        s = tuple(pose.get('arm_scale', (1.0, 1.0))) + (1.0,) * 2
        r = T(sho[side])
        return ((r[0] + shift(side), r[1]),
                (limb['lengths'][0] * s[0], limb['lengths'][1] * s[1]), limb['radii'], yaw, base)
    s = tuple(pose.get('leg_scale', (1.0, 1.0))) + (1.0,) * 2
    return (F.lower_transform(pose, hip[side], F.pitch_of(pose)), (limb['lengths'][0] * s[0], limb['lengths'][1] * s[1]), limb['radii'], yaw, -pose.get("rot", 0.0))


def chain(pose, key, spec=None):
    """(根, 起点, 肘/膝, 手/脚) —— 和 F.limb 逐行同式，只是不画像素。"""
    root, (L1, L2), _, yaw, base = _rig(pose, key)
    pitch = F.pitch_of(pose)                 # ← 俯仰也要进投影，见 fellow.CAM_PITCH
    lat, bend, sag, sbend = spec4(pose.get(key, (0.0, 0.0)) if spec is None else spec)
    lean=pose.get('lean',0) if key.startswith('arm') else 0
    p1, k1 = F.project(lat, sag, yaw, pitch,lean)
    p2, k2 = F.project(lat + bend, sag + sbend, yaw, pitch,lean)
    u = F.direc(p1 + base)
    gap=F.model_geometry(pose)['limbs'][key]['gap']*k1
    s = (root[0] + u[0] * gap, root[1] + u[1] * gap)
    e = (s[0] + u[0] * L1 * k1, s[1] + u[1] * L1 * k1)
    v = F.direc(p2 + base)
    h = (e[0] + v[0] * L2 * k2, e[1] + v[1] * L2 * k2)
    return root, s, e, h


def flip_pt(p, flip):
    """render 是最后一句 cov[:, ::-1]，等价于 x → N-1-x。"""
    return (N - 1 - p[0], p[1]) if flip else p


def joints(pose):
    """所有手柄的位置（画布坐标，已镜像）。

    {'armL': {'root': 肩, 'mid': 肘, 'tip': 手}, ..., 'head':, 'torso':}
    """
    out = {}
    for key in KEYS:
        root, _s, e, h = chain(pose, key)
        out[key] = {'root': root, 'mid': e, 'tip': h}
    T, _base, _shift, yaw, _sho, _hip, pivot = frame(pose)
    hc, _ = F.head_geometry(pose, T, yaw, F.pitch_of(pose))
    out['head'] = {k: hc for k in ('root', 'mid', 'tip')}
    out['waist'] = {k: T(pivot) for k in ('root', 'mid', 'tip')}
    out['neck'] = {k: T((F.BODY_X, F.model_geometry(pose)['neck_y'])) for k in ('root', 'mid', 'tip')}
    out['torso'] = {k: T(F.model_geometry(pose)['torso_c']) for k in ('root', 'mid', 'tip')}
    if pose.get('flip'):
        for d in out.values():
            for k in ('root', 'mid', 'tip'):
                d[k] = flip_pt(d[k], True)
    return out


# ---------------------------------------------------------------- IK
OFFKEY = {'armL': 'off_armL', 'armR': 'off_armR',
          'legL': 'off_legL', 'legR': 'off_legR', 'head': 'off_head'}


def _at(pose, key, prm, joint='tip', rg=None):
    """给一组 (lat,bend,sag,sbend) 算肘/膝（mid）或手/脚（tip）落在画布的哪。"""
    root, (L1, L2), _, yaw, base = rg if rg else _rig(pose, key)
    pitch = F.pitch_of(pose)
    lean=pose.get('lean',0) if key.startswith('arm') else 0
    p1, k1 = F.project(prm[0], prm[2], yaw, pitch,lean)
    u = F.direc(p1 + base)
    gap=F.model_geometry(pose)['limbs'][key]['gap']*k1
    s = (root[0] + u[0] * gap, root[1] + u[1] * gap)
    e = (s[0] + u[0] * L1 * k1, s[1] + u[1] * L1 * k1)
    if joint == 'mid':
        return e
    p2, k2 = F.project(prm[0] + prm[1], prm[2] + prm[3], yaw, pitch,lean)
    v = F.direc(p2 + base)
    return (e[0] + v[0] * L2 * k2, e[1] + v[1] * L2 * k2)


def ik(pose, key, target, seed=None, joint='tip', free=(0, 1, 2, 3), weight=None):
    """拖端点 → 反解角度，让手/脚（或肘/膝）落到 target。

    **四个角一起解**（阻尼最小范数），不是只解 lat/bend —— 这正是"侧身之后拖不动、
    或者拖了往侧面跑"的根子：yaw≈90 时屏幕上的前后本来就归 sag 管，只准动 lat/bend
    等于逼解算器去动一个屏幕上几乎看不见的自由度，雅可比退化，结果要么纹丝不动、
    要么把腿甩到身体侧面去。

    `weight` 是每个参数的"自由度"：sag/sbend 按 |sin(yaw)| 缩放 —— 正面时它们几乎
    不可见，权重压到 0.15，解算器自然优先用 lat/bend（和旧版手感一致）；正侧面时
    权重拉满，拖动就走 sag。**这是偏好不是限制** —— lat/bend 够不着时照样会用。

    数值解而不是闭式（余弦定理）：屏幕上的骨长要乘前缩系数 k，而 k 自己随角度变，
    闭式会变成一个难看的四次方程。从当前值出发还有个好处：肘朝哪边弯不会在拖的
    过程中突然翻面。

    target 用 joints() 那套坐标（含 flip）。返回补上原来的 sag/sbend。
    """
    tgt = flip_pt(target, pose.get('flip'))
    prm = list(spec4(pose.get(key, (0.0, 0.0)) if seed is None else seed))
    rg = _rig(pose, key)
    if weight is None:
        yaw = rg[3]
        w = 0.15 + 0.85 * abs(math.sin(math.radians(yaw)))
        weight = (1.0, 1.0, w, w)
    lim = (180.0, 180.0, 90.0, 90.0)
    step = (12.0, 12.0, 8.0, 8.0)
    eps = 0.25
    for _ in range(40):
        p0 = _at(pose, key, prm, joint, rg)
        rx, ry = p0[0] - tgt[0], p0[1] - tgt[1]
        if rx * rx + ry * ry < 0.0025:              # 0.05px，够了
            break
        cols = []
        for j in range(4):
            q = list(prm)
            q[j] += eps
            pj = _at(pose, key, q, joint, rg)
            cols.append(((pj[0] - p0[0]) / eps, (pj[1] - p0[1]) / eps))
        s2 = [weight[j] ** 2 if j in free else 0.0 for j in range(4)]
        m11 = sum(s2[j] * cols[j][0] ** 2 for j in range(4)) + 1e-3   # 阻尼：伸直时退化
        m12 = sum(s2[j] * cols[j][0] * cols[j][1] for j in range(4))
        m22 = sum(s2[j] * cols[j][1] ** 2 for j in range(4)) + 1e-3
        det = m11 * m22 - m12 * m12
        if abs(det) < 1e-12:
            break
        u1 = (-rx * m22 + m12 * ry) / det
        u2 = (m12 * rx - m11 * ry) / det
        dlt, mx = [0.0] * 4, 0.0
        for j in range(4):
            if j not in free:
                continue
            dlt[j] = weight[j] * (cols[j][0] * u1 + cols[j][1] * u2)
            mx = max(mx, abs(dlt[j]) / step[j])
        if mx > 1:                                   # 单步限幅，别蹦到另一支解
            dlt = [v / mx for v in dlt]
        for j in range(4):
            prm[j] = max(-lim[j], min(lim[j], prm[j] + dlt[j]))
    return tuple(prm)


def aim(pose, key, target, seed=None):
    """拖身体上那一块 = 整条绕根转。

    做法是把光标**投到肘/膝本来就在的那个半径上**，再当普通 IK 的目标 ——
    于是"往哪拖，肢体就往哪指"，但肘不会被从身上拽出去（那正是直接拿光标当
    目标会出的事：手一抖，肩跟着平移）。
    """
    fl = pose.get('flip')
    t = flip_pt(target, fl)
    root, _s, knee, _h = chain(pose, key)
    r = math.hypot(knee[0] - root[0], knee[1] - root[1])
    vx, vy = t[0] - root[0], t[1] - root[1]
    n = math.hypot(vx, vy) or 1.0
    return ik(pose, key, flip_pt((root[0] + vx / n * r, root[1] + vy / n * r), fl),
              seed=seed, joint='mid', free=(0, 2))


def root_jac(pose, key):
    """根点对 pose['off_*'] 那两个分量的雅可比 —— 拖根手柄时把画布位移换成偏移量。

    映射是"加偏移 → 再被 T 转一次"的刚体旋转，闭式写得出来；这里**数值求**是为了
    和 render 里那段永远对齐 —— 抄公式才是会漂的那种。
    返回两**列**（对 ox、oy 的偏导），每列是 (Δx, Δy)（画布坐标，已含 flip）。
    """
    pref = OFFKEY[key]
    r0 = joints(pose)[key]['root']
    cols = []
    for i in (0, 1):
        q = dict(pose)
        v = list(tuple(q.get(pref, (0.0, 0.0))) + (0.0, 0.0))[:2]
        v[i] += 1.0
        q[pref] = tuple(v)
        r1 = joints(q)[key]['root']
        cols.append((r1[0] - r0[0], r1[1] - r0[1]))
    return cols


if __name__ == '__main__':
    """拿真实像素验收：每个关节都得落在对应的部件里（不许飘出去）。"""
    import numpy as np

    F.NO_CARVE = True                # 关掉挖缝，各部件的原始形状才是完整的
    bad = 0
    for name in sorted(F.POSES):
        p = F.POSES[name]
        F.render(p)
        parts = dict(F.LAST_PARTS)
        js = joints(p)
        for key in KEYS:
            m = parts.get(key)
            if m is None:
                continue
            for jn, pt in js[key].items():
                x, y = int(round(pt[0])), int(round(pt[1]))
                ok = 0 <= x < N and 0 <= y < N and m[y, x]
                if not ok:
                    # 关节在骨头的圆帽里，边界上差 1px 很正常，允许邻域
                    nb = m[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
                    ok = bool(nb.any())
                if not ok:
                    print(f'  ✗ {name:16s} {key}.{jn} = ({pt[0]:.1f},{pt[1]:.1f}) 不在部件里')
                    bad += 1
    # **基准是 7，不是 0**（第 14 轮量过：旧渲染器也是这 7 处）—— 全在趴/躺那几
    # 个姿势上（crawl / dead / dead_top_se / dead_top_sw / sleep 的 armL·armR），
    # 手伸到画布外或者压在身子底下了，和挖缝没关系。换句话说：看到 7 是正常的，
    # 变了才要看一眼。
    print('验收：%d 处关节飘出部件' % bad, '（基准 7，见上：趴/躺那几个姿势）')



def _limb_tip_projector(pose,key,target_views):
    """Build FK and cameras once; only joint angles vary inside an IK solve."""
    import numpy as np
    root=S.limb_chain(pose,key)[0]
    limb=F.model_geometry(pose)['limbs'][key]
    scales=tuple(pose.get('arm_scale' if key.startswith('arm') else 'leg_scale',(1,1)))
    length1=limb['gap']+limb['lengths'][0]*scales[0];length2=limb['lengths'][1]*scales[1]
    transform=S.root_rotation(pose)
    transform=transform@S.rx(pose.get('lean',0))@S.ry(pose.get('chest_yaw',0)) if key.startswith('arm') else transform@S.ry(pose.get('pelvis_yaw',0))
    camera=np.concatenate([np.array((S.ry(yaw)[0],-S.ry(yaw)[1])) for yaw,target in target_views])
    matrix=camera@transform
    origin=camera@root+np.tile((31.5,55.5+math.floor(pose.get('_camera_y',0)+.5)),len(target_views))
    def positions(spec):
        lat,bend,sag,sbend=spec
        return origin+matrix@(S.direction(lat,sag)*length1+S.direction(lat+bend,sag+sbend)*length2)
    return positions

def solve_multi(pose, key, target_views):
    """Fit a limb in two anatomical views so foot locking isn't camera-dependent."""
    import numpy as np
    q=np.array(spec4(pose[key]),dtype=float)
    if abs(q[3])<1:q[2]+=10;q[3]-=20
    positions=_limb_tip_projector(pose,key,target_views)
    goal=np.array([v for yaw,target in target_views for v in target])
    precise=bool(pose.get('_breath_ik'))
    for _ in range(60 if precise else 25):
        current=positions(q);error=goal-current
        if np.linalg.norm(error)<(.003 if precise else .05):break
        cols=[]
        for j in (0,2,3):
            probe=q.copy();probe[j]+=.25;cols.append((positions(probe)-current)/.25)
        jac=np.array(cols).T
        delta=np.linalg.solve(jac.T@jac+np.diag([.02,.002,.002]),jac.T@error)
        delta*=min(1.,10/max(10,np.max(abs(delta))))
        q[[0,2,3]]+=delta
        initial=spec4(pose[key])
        q[0]=float(np.clip(q[0],initial[0]-5,initial[0]+5))
        q[2:4]=np.clip(q[2:4],[-90,-150],[90,0])
    return q.tolist()


def aim_body(pose,key,target,joint='tip'):
    """Fit a torso or head handle in the active projected view."""
    import numpy as np
    keys=('head_pitch','head') if key=='head' else ('lean','rot')
    values=np.array([pose.get(k,0.) for k in keys],dtype=float)
    def point(v):return np.array(joints(dict(pose,**dict(zip(keys,v))))[key][joint])
    for _ in range(20):
        current=point(values);error=np.array(target)-current
        if np.linalg.norm(error)<.08:break
        cols=[]
        for i in range(2):
            probe=values.copy();probe[i]+=.5;cols.append((point(probe)-current)/.5)
        jac=np.array(cols).T
        delta=np.linalg.solve(jac.T@jac+np.eye(2)*.002,jac.T@error)
        values=np.clip(values+np.clip(delta,-12,12),[-75,-60],[85,60])
    return dict(zip(keys,values.tolist()))

# Three-dimensional geometry is shared with the renderer. The existing IK solver,
# body handles and multi-view foot locking retain their UI/API and use this FK.
import numpy as np
import rounded_scene as S
from core3d import project as project3d

def _project(pose,point):
 q=project3d(np.array([point]),pose.get('yaw',0),pose.get('pitch',0))[0];return flip_pt((float(q[0]),float(q[1])+math.floor(pose.get('_camera_y',0)+.5)),pose.get('flip'))
def chain(pose,key,spec=None):
 p=dict(pose)
 if spec is not None:p[key]=spec
 result=S.limb_chain(p,key)
 # chain historically returns unmirrored points; joints handles final flip.
 offset=np.array((0.,math.floor(pose.get('_camera_y',0)+.5)))
 return tuple(tuple(project3d(np.array([point]),pose.get('yaw',0),pose.get('pitch',0))[0][:2]+offset) for point in result)
def joints(pose):return {key:{name:_project(pose,point) for name,point in chain.items()} for key,chain in S.geometry(pose)[1].items()}
def _rig(pose,key):
 limb=F.model_geometry(pose)['limbs'][key];scales=tuple(pose.get('arm_scale' if key.startswith('arm') else 'leg_scale',(1,1)))
 return chain(pose,key)[0],tuple(limb['lengths'][i]*scales[i] for i in (0,1)),limb['radii'],pose.get('yaw',0),-pose.get('rot',0)
def _at(pose,key,prm,joint='tip',rg=None):return chain(pose,key,prm)[2 if joint=='mid' else 3]

# Foot constraints depend only on this leg and the body transform. Arm/face edits
# must not solve the exact same leg targets again for every animation frame.
from functools import lru_cache
import json as _json
_solve_multi_uncached=solve_multi
@lru_cache(maxsize=512)
def _locked_leg(pose_key,key,target_key):return _solve_multi_uncached(_json.loads(pose_key),key,_json.loads(target_key))
def solve_multi(pose,key,target_views):
 relevant={k:pose[k] for k in (key,'_model','_camera_y','_breath_ik','leg_scale','pelvis','pelvis_yaw','rot','body_pitch','body_axis','body_pivot','dx','dy','dz','off_legL','off_legR','flip') if k in pose}
 return list(_locked_leg(_json.dumps(relevant,sort_keys=True,default=lambda v:v.tolist()),key,_json.dumps(target_views,default=lambda v:v.tolist())))
