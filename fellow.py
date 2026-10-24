"""
Fellow — 64x64 白色小人姿势生成器

素材来源：随工具附带的 source/Fellow1.png（用户手绘）
  · 头 (24,8)-(39,22) 16x15   ┐ 三个 Fellow 里逐像素一致，直接取用
  · 躯干 (26,24)-(37,38) 12x15 ┘
  · 四肢：按手绘的粗细（宽约 5~6px）程序化重画，这样才能摆任意角度

坐标：64x64，y 向下。
角度：0 = 朝下，+90 = 朝小人自己的右（+x），180 = 朝上。
"""
import math
import os
import sys
import numpy as np
from PIL import Image

N = 64          # 画布
SS = 4          # 超采样倍率
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), 'source'))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))   # 成品目录（editor/out 是草稿）

# ---- 全局摄影机方位角 ---------------------------------------------------
# 用户 2026-10-14："还需要一个整体的角度旋转，摄影机的旋转，这样就能整体调整渲染角度"。
#
# 姿势自己的 `yaw` 是**小人转过去多少**（正面 0 / 侧身 90 / 背对 180）；这个是
# **镜头绕竖轴转了多少**。投影上两者是同一条轴、直接相加即可 —— [project] 里
# yaw 本来就只出现在 sin/cos 里，加一个常数等于把镜头转过去，数学上完全等价。
#
# **为什么要有**：姿势的 yaw 是逐个写死的（walk_side 写 90、walk_qtr 写 45），
# 想让整套素材换个观察角度得改几十处；有了这个常数，一行都不动就整体换角度。
# 所以它是**加在姿势自己的 yaw 之后**的偏移，不是替代。
#
# 注意：改这个值，**所有**导出都会跟着变（立绘 + 动画 + 编辑器预览）。
# 编辑器里有滑杆可以实时看，`python fellow.py --cam 30` / `anim.py --cam 30`
# 是批量重出。0 = 不转（默认，和以前逐像素一致）。
CAM_YAW = 0.0

# 摄影机的**俯仰**（2026-10-15 加，四视图里的「45° + 俯视 30°」要用）。正 = 镜头抬高
# 往下看。和 CAM_YAW 同构，是**加在姿势自己的 pitch 之后**的偏移；默认 0 时整条渲染
# 路径一像素都不变（所有式子都退化成老样子）。
#
# 它管两件事，缺一不可：
#   ① `project()` 里把肢体方向按俯仰再转一次 —— 竖着的肢体缩短（×cos p）、朝镜头的
#      肢体在画面里往下垂（×sin p）；
#   ② 身体上离髋轴越远的**点**（肩、头）在画面上往中间收（见 pitch_scale），
#      不然头会飘到四肢接缝的外面去。
# **头本身不压**（球的正交投影轮廓与观察角无关 —— 和横向那条规矩同一个理由）。
CAM_PITCH = 0.0


def yaw_of(pose, cam=None):
    """姿势朝向 + 全局摄影机偏移。**render 和 rig.frame 都必须走这个函数**，
    否则编辑器的手柄会和渲染出来的肢体错开。

    `cam=(yaw, pitch)` 是给**非选中视图**的一次性镜头覆盖（见 editor 的四视图）：
    不动全局，只这一次渲染换个角度。
    """
    return pose.get('yaw', 0.0) + (CAM_YAW if cam is None else cam[0])


def pitch_of(pose, cam=None):
    """姿势俯仰 + 全局摄影机俯仰（正 = 镜头抬高往下看）。"""
    return pose.get('pitch', 0.0) + (CAM_PITCH if cam is None else cam[1])


def pitch_scale(pitch):
    """俯视的**垂直前缩**：离髋轴越远的地方在画面上越往中间收。

    正交投影下就是个纯 ×cos：镜头抬 30°，头顶就该往下挪 13%。
    """
    return math.cos(math.radians(max(-80.0, min(80.0, pitch))))


def foreshorten(p, about, psc):
    """俯仰的**垂直前缩**：离 `about` 越远的点越往它收（见 `pitch_scale`）。

    `render` 和 `rig` 两侧都用这一个（手柄要和渲染出来的骨架对得上）。
    """
    if psc == 1.0:
        return p
    return (p[0], about[1] + (p[1] - about[1]) * psc)


def lean_split(lean, yaw):
    """「上半身前倾 lean 度」拆成 **画面内的转角 + 剩下的垂直压缩** 两半。

    身体上的点 (x, y) 绕髋轴前倾 λ（往镜头方向倒）、再转 yaw 投到屏幕上：

        屏幕 X = x·cosψ − y·sinλ·sinψ
        屏幕 Y = y·cosλ

    老写法是**画面内旋转** rot(·, λ)：

        屏幕 X = x·cosλ − y·sinλ
        屏幕 Y = x·sinλ + y·cosλ

    两者只在 ψ=±90（正侧身）重合。正面 ψ=0 时老写法的 X 里带着 −y·sinλ ——
    整个上半身往一边倒，这就是用户 2026-10-15 报的「正视图整体向左右歪」
    （`anim.py` 里那两套正面走/跑干脆把 lean 全归零绕开它，是同一个病的另一面）。

    所以这里按真投影拆开：

        θ = λ·sinψ          画面内转多少。ψ=±90 时 θ=λ，**正侧身逐像素不变**；
                            ψ=0 时 θ=0，不再左右歪。
        k = cosλ / cosθ     剩下那一截垂直压缩。ψ=±90 时 k=1（同样是恒等），
                            ψ=0 时 k=cosλ。

    正面剩下的效果就是**绕髋轴纵向压 cosλ**：上半身矮下去、头往下掉一点，左右对称。
    这和俯仰（`pitch_scale`）在正面的表现是同一种 —— 正交投影下正面本来就
    看不出前后倾，能看出来的只有那点纵缩。

    返回 (θ, k)。lean=0 时返回 (0.0, 1.0)，恒等。
    """
    if lean == 0.0:
        return 0.0, 1.0
    lam = max(-80.0, min(80.0, lean))
    th = lam * math.sin(math.radians(yaw))
    # cosθ 兜底：λ 钳到 80° 之后 cosθ 最低也有 0.17，正常走不到这里；留一条不至于
    # 把 k 炸到无穷（`squash` 拿到 0 会算出 0 像素宽的图）。
    c = max(0.25, math.cos(math.radians(th)))
    return th, math.cos(math.radians(lam)) / c


def cli_cam(argv=None):
    """认 `--cam <度>` / `--pitch <度>`，写进 CAM_YAW / CAM_PITCH 并返回剩下的参数
    （fellow.py / anim.py 共用）。"""
    global CAM_YAW, CAM_PITCH
    a = list(sys.argv[1:] if argv is None else argv)
    for flag, name in (('--cam', 'CAM_YAW'), ('--pitch', 'CAM_PITCH')):
        if flag in a:
            i = a.index(flag)
            globals()[name] = float(a[i + 1])
            del a[i:i + 2]
    return a


# ---- 中性骨架（64x64 空间，站立姿态）------------------------------------
HEAD_C = (31.5, 15.0)
TORSO_C = (31.5, 31.0)
# 肩关节（2026-10-14 往外挪 1.5px：原来 x=25.5 时手臂根的圆帽会埋进躯干边缘
# 2px 深，"四肢在前"的合成就会在躯干两侧各啃掉一条 2px 的竖沟。挪到 24.0/39.0
# 后手臂根落在躯干外，缝只剩 SEP 那一圈 —— 和用户手绘里"手臂贴着躯干但不相交"
# 的做法一致。IoU 对 orig1 反而从 0.704 微升到 0.707。）
SHO = {'L': (24.0, 25.5), 'R': (39.0, 25.5)}     # 肩关节
HIP = {'L': (28.5, 38.0), 'R': (35.0, 38.0)}     # 髋关节
ARM = (5.8, 5.8)                                  # 上臂 / 前臂  → 总长 11.6
LEG = (5.8, 5.8)                                  # 大腿 / 小腿  → 总长 11.6
R_ARM = (2.9, 2.2)                                # 上臂根→手 半径
R_LEG = (3.0, 2.2)
GAP = 1.6           # 肢体与躯干之间留的空隙（手绘里也有这个缝）


# ---- 素材 ---------------------------------------------------------------
def _load_mask(path, box):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)[:, :, 3] > 0
    x0, y0, x1, y1 = box
    sub = a[y0:y1 + 1, x0:x1 + 1]
    return sub, ((x0 + x1) / 2, (y0 + y1) / 2)


HEAD_M, HEAD_MC = _load_mask(f'{SRC}/Fellow1.png', (24, 8, 39, 22))
TORSO_M, TORSO_MC = _load_mask(f'{SRC}/Fellow1.png', (26, 24, 37, 38))

def clean_torso_mask(mask):
    """Extract only the central body run, excluding neighboring sprite pixels.
    The neutral body is symmetric; motion/projection remain free to be asymmetric.
    """
    core=np.zeros_like(mask);middle=mask.shape[1]//2
    for y,row in enumerate(mask):
        if not row[middle]:continue
        left=right=middle
        while left>0 and row[left-1]:left-=1
        while right+1<len(row) and row[right+1]:right+=1
        core[y,left:right+1]=True
    return core & core[:,::-1]

TORSO_M=clean_torso_mask(TORSO_M)



from functools import lru_cache
import json as _model_json
import model_data as MD
@lru_cache(maxsize=32)
def _model_geometry(key):
    m=MD.normalize(_model_json.loads(key));t=m['torso'];height=t['height'];pivot_y=(HIP['L'][1]+HIP['R'][1])/2
    # Shoulder width changes the chest contour and socket by the same amount.
    # Scaling the socket's distance from BODY_X also scaled its original clearance.
    shoulder_half=max(TORSO_M[1:4].sum(axis=1))/2
    shoulder_delta=shoulder_half*(t['shoulder']-1)
    sho={};hip={};limbs={}
    for side in ('L','R'):
        sign=-1 if side=='L' else 1
        a=m['arm'+side];l=m['leg'+side]
        sho[side]=(SHO[side][0]+sign*(shoulder_delta+a['spread']),pivot_y+(SHO[side][1]-pivot_y)*height+a['vertical'])
        hip[side]=(BODY_X+(HIP[side][0]-BODY_X)*t['hip']+sign*l['spread'],HIP[side][1]+l['vertical'])
        for kind,radii in (('arm',R_ARM),('leg',R_LEG)):
            limb=m[kind+side];limbs[kind+side]={'lengths':(limb['upper'],limb['lower']),'radii':tuple(v*limb['thickness'] for v in radii),
                'gap':GAP+limb['gap']+(0 if limb['connected'] else 1.),'bridge':limb['connected'] and limb['gap']==0 and limb['spread']==0}
    if all(t[k]==MD.DEFAULT['torso'][k] for k in ('height','shoulder','waist','hip')):torso=TORSO_M
    else:
        h=max(5,round(TORSO_M.shape[0]*height));width=max(6,math.ceil(TORSO_M.shape[1]*max(t['shoulder'],t['waist'],t['hip'])));width+=width%2
        torso=np.zeros((h,width),bool)
        for y in range(h):
            phase=y/max(1,h-1);source=TORSO_M[round(phase*(len(TORSO_M)-1))].sum()
            # Preserve the neck cap; widen a shoulder band, then taper to waist
            # and hips. Multiplying each original row barely widened the narrow
            # shoulder cap and produced an uneven, pinched upper chest.
            extra=float(np.interp(phase,[0,2/14,4/14,.5,12/14,1],
                [0,2*shoulder_delta,2*shoulder_delta,12*(t['waist']-1),10*(t['hip']-1),6*(t['hip']-1)]))
            n=max(2,round((source+extra)/2)*2);left=(width-n)//2;torso[y,max(0,left):min(width,left+n)]=True
    head=HEAD_M if m['head']['size']==1 else np.array(Image.fromarray((HEAD_M*255).astype('uint8')).resize((max(4,round(HEAD_M.shape[1]*m['head']['size'])),max(4,round(HEAD_M.shape[0]*m['head']['size']))),Image.Resampling.NEAREST))>0
    shoulder_y=pivot_y+(SHO['L'][1]-pivot_y)*height
    head_c=(HEAD_C[0],shoulder_y+(HEAD_C[1]-SHO['L'][1])-m['head']['gap']-(m['head']['size']-1)*7)
    return {'sho':sho,'hip':hip,'torso_c':(BODY_X,pivot_y+(TORSO_C[1]-pivot_y)*height),'head_c':head_c,'neck_y':shoulder_y-2,'torso_mask':torso,'head_mask':head,'limbs':limbs}

def model_geometry(pose):
    return _model_geometry(_model_json.dumps(pose.get('_model',{}),sort_keys=True))


# ---- 几何 ---------------------------------------------------------------
def direc(deg):
    r = math.radians(deg)
    return (math.sin(r), math.cos(r))


def rot(p, deg, about):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y = p[0] - about[0], p[1] - about[1]
    return (about[0] + x * c - y * s, about[1] + x * s + y * c)


def add(p, v):
    return (p[0] + v[0], p[1] + v[1])


def sock(pose, pref, s):
    """手调的"根装在身上的哪"—— pose['off_armL'] = (左右, 上下)，单位是画布像素。

    加在**转 pelvis / shoulder 之后**：挪一个肩不该把胯线的转轴也带跑。
    偏移写在中性空间里，所以它会跟着身体一起前倾 / 旋转 —— 跟"本来就长在那儿"
    是一回事。老姿势没有这几个键，取到的就是 (0,0)，渲染结果一像素不变。
    """
    v = pose.get(pref + s, (0.0, 0.0))
    return (float(v[0]), float(v[1]))


_YS, _XS = np.mgrid[0:N * SS, 0:N * SS]
_X = (_XS + 0.5) / SS
_Y = (_YS + 0.5) / SS


def bone(p0, p1, r0, r1):
    """锥形胶囊的覆盖掩码（超采样分辨率）。

    **只在包围盒那一小块上算**（2026-10-14 改）。整个网格是 256×256 = 65536 点，
    而一条骨头连半径算进去也就 20×20 上下 —— 原来每条骨头都在整张网格上算一遍
    `hypot`，**一条 4ms，一次 render 有 8 条就是 32ms**（占 render 的 85%，编辑器
    卡、8 倍速播不动的根因）。改成先框格子、再在框里算，顺带把 `hypot` 换成平方
    比较（胶囊判据 `d ≤ r` 两边平方等价，半径恒非负），一条骨头 ~0.1ms。
    **逐像素结果和原来逐字节一致**（_chk.py 对过）。
    """
    rmax = r0 if r0 > r1 else r1
    if rmax <= 0:
        return np.zeros((N * SS, N * SS), bool)
    W = N * SS
    # **p0/p1 是"画布单位"（1 单位 = 1 像素 = SS 格），框出来的是"格号"** ——
    # 别漏了乘 SS，漏了框就缩到画布左上角那一小块（改这版时踩过：整个小人
    # 只剩 347 个像素）。
    x0 = max(0, int(math.floor((min(p0[0], p1[0]) - rmax) * SS)) - 1)
    x1 = min(W, int(math.ceil((max(p0[0], p1[0]) + rmax) * SS)) + 2)
    y0 = max(0, int(math.floor((min(p0[1], p1[1]) - rmax) * SS)) - 1)
    y1 = min(W, int(math.ceil((max(p0[1], p1[1]) + rmax) * SS)) + 2)
    out = np.zeros((W, W), bool)
    if x1 <= x0 or y1 <= y0:
        return out
    X, Y = _X[y0:y1, x0:x1], _Y[y0:y1, x0:x1]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        out[y0:y1, x0:x1] = (X - p0[0]) ** 2 + (Y - p0[1]) ** 2 <= r0 * r0
        return out
    t = np.clip(((X - p0[0]) * dx + (Y - p0[1]) * dy) / L2, 0, 1)
    cx, cy = p0[0] + t * dx, p0[1] + t * dy
    r = r0 + t * (r1 - r0)
    out[y0:y1, x0:x1] = (X - cx) ** 2 + (Y - cy) ** 2 <= r * r
    return out


# ---- 转身（yaw）：0 = 正面朝屏幕，+90 = 朝屏幕右侧（侧身）--------------------
#
# 2D 立绘没有真 3D，但"转过去"这件事可以按正交投影算。肢体在身体坐标里有两个角：
#   lat = 冠状面角（0=朝下，+=朝小人自己的右侧）—— 就是原来那个肢体角度
#   sag = 矢状面角（0=朝下，+=朝前）—— 原来根本没有这一维
# 镜头绕竖直轴偏 yaw 之后：
#     屏幕 x = sin(lat)·cos(sag)·cos(yaw) + sin(sag)·sin(yaw)
#     屏幕 y = cos(lat)·cos(sag)
# yaw=0 就是原来的正面（sag 完全看不见 —— 这正是"正面走路看不出迈步"的原因，
# 所以正面走只能靠两条腿对称撇开去假装）；yaw=90 时 lat 看不见、sag 直接变成屏幕
# 上的左右（侧身走路腿是真前后摆的）。骨骼长度再乘 |屏幕方向|（前缩），
# 朝镜头伸的肢体自然变短。
# yaw=90（正侧身）时躯干保留的横向比例 —— 也就是"身体的前后厚度 / 肩膀宽度"。
# 0.85（11px → 9px）。**不能照搬真人比例往下压**：这是 Q 版身材，身体本来就是个
# 圆墩墩的方块，侧面比正面窄一点点就够了；压到 0.72 时 8px 的躯干配 15px 的脑袋，
# 侧身读起来是"大圆头插在纸片上"（2026-10-14 用户："身体的部分也有点怪"）。
MIN_W_TORSO = 0.85
#
# **头不压，一点都不压**（2026-10-14 用户指出"侧面头都瘪了"）。
# 之前按 |cos|³ 压到 0.72，理由是"转头要看得出来"——**这个理由是错的**：
# 脑袋是个球，正交投影下球的轮廓跟转多少度没有关系，正面多宽侧面就多宽。
# 压扁之后侧身变成一个竖椭圆，读起来是"头被门夹了"，不是"人转过去了"。
# 转身该由别的东西表达：躯干变窄、四肢换前后顺序、近侧手往前挪 —— 这些够了。
# 侧身时把近侧手臂往"身前"、远侧往"身后"在屏幕上再错开一点。
#
# **为什么需要**：正侧身时肩/髋的横向偏移按 cos(90°)=0 全部并到中线上，两条手臂会
# 叠在躯干正中、把 9px 宽的躯干啃成 3px。真人侧影里那条近侧手臂是画在躯干前缘的，
# 所以这里手工把它推开。
#
# **为什么是 sin²**：幅度要"越接近正侧身越大"（|sin|），符号要"朝哪边转"（sin），
# 两者相乘就是 sin·|sin|。**绝不能挂在"哪侧是近侧"这个身份上** —— 过了 90° 近远侧
# 互换，身份一翻就是硬跳；sin² 的符号翻转发生在 0°/180°（那两个角度本来就分不出
# 远近），全程连续。只推手臂不推腿：腿的前后分靠矢状面摆角就够，硬推会变成八字站。
SIDE_PUSH = 1.0
# 正侧身时肩/髋收拢到中线上的**保底横向偏移**（见 render 里的 anc）。
#
# **髋必须是 0**：真侧影里两条腿是一前一后叠着的（站着时只看得见一条）。给髋留保底，
# 两条腿就会在侧身并排站着、中间空一道 —— 那是正面感，一眼看过去像没转身。
# 腿的前后分靠 mocap 的矢状摆角去分，不需要手工撑开。
#
# 肩留一点点，纯粹是为了侧身时两条手臂不完全重合（完全重合的话近侧手把远侧手全遮住，
# 摆臂的幅度在侧身看不见）。1.0 够用：手臂半径 2.9，错开 2px 就能读出两条。
FLOOR_HIP, FLOOR_SHO = 0.0, 0.8
BODY_X = 31.5                          # 身体中线，附着点绕着它收拢
MIN_K = 0.45                           # 前缩系数的下限：芭蕾转圈时二位手有两帧正对镜头，
                                       # 0.32 那截短桩看着像手臂断了，0.45 才读成"伸向镜头的手"


def yaw_scale(yaw, floor):
    """躯干/腿的横向保留比例：yaw=0 → 1，yaw=±90 → floor。
    线性混合（不是 cos²）—— 躯干是个扁盒子，斜 45° 时看到的对角线本来就接近正面宽度，
    实测真人侧影也是这个规律：45° 不比正面窄多少。"""
    return floor + (1.0 - floor) * abs(math.cos(math.radians(yaw)))


def project(lat, sag, yaw, pitch=0.0, lean=0.0):
    """身体坐标的 (冠状角, 矢状角) → 屏幕上的 (角度, 前缩系数)。

    背后的 3D：一个肢体方向写成身体坐标的 (bX 横向, bY 向下, bZ 朝镜头)，
    bX = sin(lat)cos(sag)、bY = cos(lat)cos(sag)、bZ = sin(sag)。先绕竖轴转 yaw：

        x1 = bX·cos(y) + bZ·sin(y)          ← 横向（就是老代码里的 sx）
        y1 = bY                              ← 上下，转 yaw 不动它
        z1 = −bX·sin(y) + bZ·cos(y)          ← 深度（见 limb_depth，那边同一个式子）

    再把镜头抬高 pitch（绕画面的横轴转一次）：竖直方向缩短 cos、朝镜头的方向在画面里
    往下垂 sin：

        x2 = x1
        y2 = y1·cos(p) + z1·sin(p)

    pitch=0 时 y2 = y1、x2 = x1，**逐位退化成老式子**（所以默认值下所有已验收的
    素材一个像素都不变）。
    """
    lr, sr, yr = math.radians(lat), math.radians(sag), math.radians(yaw)
    bx=math.sin(lr)*math.cos(sr);by=math.cos(lr)*math.cos(sr);bz=math.sin(sr)
    tilt=math.radians(lean)
    sy=by*math.cos(tilt)+bz*math.sin(tilt)
    bz=-by*math.sin(tilt)+bz*math.cos(tilt)
    sx = bx * math.cos(yr) + bz * math.sin(yr)
    if pitch:
        pr = math.radians(pitch)
        sz = -bx * math.sin(yr) + bz * math.cos(yr)
        sy = sy * math.cos(pr) + sz * math.sin(pr)
    if abs(sx) < 1e-9 and abs(sy) < 1e-9:
        return 0.0, MIN_K      # 正对镜头的肢体（芭蕾二位手转到侧身时就是）：不缩成 0，
    #                        留一小截短桩，否则整条手臂会凭空消失

    return math.degrees(math.atan2(sx, sy)), max(math.hypot(sx, sy), MIN_K)


def squash(mask, sx, sy=1.0):
    """横向 / 纵向压缩。横向是转身（侧面比正面窄），纵向是俯视（躯干矮下去）。

    **头不走这里** —— 球的正交投影轮廓与观察角无关，压了就成"瘪头"（第 8 轮用户
    为横向那条已经报过一次，纵向同理）。
    """
    if abs(sx - 1.0) < 1e-6 and abs(sy - 1.0) < 1e-6:
        return mask
    h, w = mask.shape
    im = Image.fromarray((mask * 255).astype('uint8')).resize(
        (max(1, int(round(w * sx))), max(1, int(round(h * sy)))), Image.BOX)
    out = np.array(im) >= 128
    if abs(sy - 1.0) < 1e-6:
        return out                              # 只压横向 —— 尺寸变化交给 part_mask 补方
    pad = np.zeros((h, w), bool)                # 压完要放回原来的格子里（居中）
    oh, ow = out.shape
    y0, x0 = (h - oh) // 2, (w - ow) // 2
    pad[max(0, y0):max(0, y0) + oh, max(0, x0):max(0, x0) + ow] = \
        out[max(0, -y0):max(0, -y0) + h, max(0, -x0):max(0, -x0) + w]
    return pad


def limb(cov, root, spec, lens, radii, yaw=0.0, base=0.0, pitch=0.0, gap=None, lean=0.0):
    """一条两节肢体。

    spec = (lat, bend) | (lat, bend, sag) | (lat, bend, sag, sbend)
    bend 是冠状面的相对弯折，sbend 是矢状面的相对弯折（膝盖就是 sbend）。
    先投影到屏幕，再叠 base（身体在画面里的整体倾角）—— 顺序不能反：
    base 是画面内的旋转，不是身体坐标里的角度。根端往回收 GAP，留缝。
    """
    lat, bend = spec[0], spec[1]
    sag = spec[2] if len(spec) > 2 else 0.0
    sbend = spec[3] if len(spec) > 3 else 0.0
    L1, L2 = lens
    r0, r1 = radii
    rm = (r0 + r1) / 2
    p1, k1 = project(lat, sag, yaw, pitch, lean)
    p2, k2 = project(lat + bend, sag + sbend, yaw, pitch, lean)
    u = direc(p1 + base)
    spacing=(GAP if gap is None else gap)*k1
    s = (root[0] + u[0] * spacing, root[1] + u[1] * spacing)      # 收进去一点，和躯干分开
    e = (s[0] + u[0] * L1 * k1, s[1] + u[1] * L1 * k1)
    v = direc(p2 + base)
    h = (e[0] + v[0] * L2 * k2, e[1] + v[1] * L2 * k2)
    cov |= bone(s, e, r0, rm)
    cov |= bone(e, h, rm, r1)


def part_mask(mask, deg, centered=False):
    """Rotate around the part's own center, without asymmetric square padding."""
    if not centered:
        h,w=mask.shape;size=max(h,w);pad=np.zeros((size,size),bool)
        pad[(size-h)//2:(size-h)//2+h,(size-w)//2:(size-w)//2+w]=mask
        mask=pad
    k=deg/90.0
    if abs(k-round(k))<1e-6:return np.rot90(mask,-int(round(k))%4)
    scale=8;h,w=mask.shape
    im=Image.fromarray((mask*255).astype('uint8')).resize((w*scale,h*scale),Image.NEAREST)
    im=im.rotate(-deg,resample=Image.BICUBIC,expand=True,fillcolor=0)
    im=im.resize((math.ceil(im.width/scale),math.ceil(im.height/scale)),Image.BOX)
    return np.array(im)>=128


def place(arr, mask, at):
    """把一个小掩码按自身中心对齐贴到画布的 at（像素中心 = (w-1)/2）"""
    h, w = mask.shape
    x0 = int(round(at[0] - (w - 1) / 2))
    y0 = int(round(at[1] - (h - 1) / 2))
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(N, x0 + w), min(N, y0 + h)
    if xs0 >= xs1 or ys0 >= ys1:
        return
    arr[ys0:ys1, xs0:xs1] |= mask[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]


# ---- 部件分离（用户手绘的逻辑：头/躯干/四肢之间必须留白）------------------
SEP = 1             # 留白宽度（像素）

# 两个部件重叠到这个比例以上就认定"同一坨"，不挖缝（见 render 里的分离循环）。
# 正面：手臂与躯干 0.14、左右腿 0；侧身 45°：近臂 ~0.5。都远低于 0.7，照常分家。
MERGE_RATIO = 0.7

# 横向包含判据的容差（px）：`key` 探出 `k2` 轮廓不超过这么多像素就算没探出去。
MERGE_SPAN_TOL = 1

# 最后填洞的尺寸上限（见 fill_holes）。1 = 只填孤点，别动"两头封住"的缝。
FILL_MAX = 1

# 挖缝时要不要连纵向一起膨胀。
# 纵向膨胀会在"搭在下一截上面"的地方多啃一行：正侧身时近臂的手梢（末行 y39）会
# 顺着 y40 啃掉大腿右半边，啃出一个 4px 宽、1 行高的豁口。横向膨胀没有这个问题，
# 而且正面髋部那条 1px 的孤点（躯干底沿被两条腿的膨胀啃剩正中间一列）也一并消失
# —— 用户参考图里躯干和腿本来就是连成一坨的，没有髋线。所以取 False。
# 置 True 可以退回"横向+纵向"，正面的差别只在髋部那一行。
CARVE_VERT = False

# 从前到后的图层顺序（用户 2026-10-14 定的：**四肢排在前面**）。
# 前面的部件形状原样保留，留白只挖在它后面那些部件上 —— 所以手臂压到头/躯干上时，
# 手臂轮廓仍然完整，被啃掉的是它后面的躯干。
#
# 每一层是一"组"：组内的部件互不相啃，组的并集去啃后面的组。
# 头 + 躯干必须同组 —— 它们上下紧挨着（头到 y22、躯干从 y24），分开排的话
# 躯干那圈 dilate 会顺着缝啃掉头底，头会凭空少一圈。
Z_ORDER = (('armL',), ('armR',), ('legL',), ('legR',), ('torso', 'head'))

# 调试用：render() 每次跑完把逐部件的最终 mask 留在这里，方便量"谁被谁啃了多少"
LAST_PARTS = {}
PIXEL_PERFECT = False
NO_CARVE = False    # 调试开关：置 True 时跳过挖缝，LAST_PARTS 里就是各部件的原始形状


def dilate(m, k=SEP):
    out = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            if dx or dy:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def dilate4(mask):
    padded=np.pad(mask,1);out=mask.copy()
    out |= padded[:-2,1:-1];out |= padded[2:,1:-1];out |= padded[1:-1,:-2];out |= padded[1:-1,2:]
    return out


def drop_specks(m, minpx=5):
    """去掉分离后留下的小碎块。

    **只遍历有像素的那些格**（`np.argwhere` + set），不扫整张 64×64 —— 一块肢体
    也就几百个像素，扫满 4096 格的空转占了大头（一次 render 里这个函数要跑 6 遍）。
    8 连通、保留 ≥ minpx 的连通块，结果和原来逐字节一致。
    """
    n8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    todo = set(map(tuple, np.argwhere(m)))       # {(y, x)}
    keep = np.zeros_like(m, bool)
    while todo:
        seed = todo.pop()
        st, comp = [seed], [seed]
        while st:
            cy, cx = st.pop()
            for dy, dx in n8:
                p = (cy + dy, cx + dx)
                if p in todo:
                    todo.discard(p)
                    st.append(p)
                    comp.append(p)
        if len(comp) >= minpx:
            for cy, cx in comp:
                keep[cy, cx] = True
    return keep


def dilate_h(m, k=SEP):
    """只在横向膨胀 —— 用来挖缝（见 CARVE_VERT）"""
    out = m.copy()
    for dx in range(-k, k + 1):
        if dx:
            out |= np.roll(m, dx, 1)
    return out


def fill_holes(m, maxpx=FILL_MAX):
    """把被白像素围死的背景点填上 —— 只填极小的那种（默认 1px）。

    挖缝是按部件挖的，两个部件各让一步时会正好剩下一个 1px 的洞（正侧身：
    近臂手梢从大腿上挖走的那一列，上下都被填住了）。轮廓里的孤洞永远不是有意的。

    **只能填小的**：手臂横在身上时，臂与躯干之间那条缝两头都会被白封住（"环"），
    按"填掉所有非外部背景"去填会把整条缝抹平、手臂糊回身体里。所以加个尺寸上限；
    那条缝几十像素起，这里只填 ≤maxpx 的。
    """
    h, w = m.shape
    bg = ~m
    # 外部背景用**整块 numpy 逐格外扩**找，不再用 Python 栈做洪水填充 ——
    # 后者要把整张 64×64 的背景一格一格走过（~5ms，一次 render 只跑一遍但很显眼）。
    # 外扩的轮数 = 离边框的最远距离，最多 h/2 轮，每轮只有 8 次切片或运算。
    outside = np.zeros_like(bg)
    outside[0, :] = bg[0, :]
    outside[-1, :] = bg[-1, :]
    outside[:, 0] |= bg[:, 0]
    outside[:, -1] |= bg[:, -1]
    while True:
        nxt = outside.copy()
        nxt[1:, :] |= outside[:-1, :]
        nxt[:-1, :] |= outside[1:, :]
        nxt[:, 1:] |= outside[:, :-1]
        nxt[:, :-1] |= outside[:, 1:]
        nxt &= bg
        if np.array_equal(nxt, outside):
            break
        outside = nxt
    holes = bg & ~outside
    if not holes.any():
        return m
    # 洞的连通块也**只遍历有洞的格**（洞通常就一两个像素）。
    todo = set(map(tuple, np.argwhere(holes)))
    while todo:
        seed = todo.pop()
        st, comp = [seed], [seed]
        while st:
            cy, cx = st.pop()
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                p = (cy + dy, cx + dx)
                if p in todo:
                    todo.discard(p)
                    st.append(p)
                    comp.append(p)
        if len(comp) <= maxpx:
            for cy, cx in comp:
                m[cy, cx] = True
    return m


def inside(a, b, tol=MERGE_SPAN_TOL):
    """a 在"两份都有像素"的那些行上，横向是不是完全落在 b 的轮廓里。

    是 → 两条轮廓在同一根柱子上，挖缝只会啃出豁口，该并成一块。
    两份没有共同行 → False（没压上，照常挖缝）。
    """
    ys = np.nonzero(a.any(axis=1) & b.any(axis=1))[0]
    for y in ys:
        xa = np.nonzero(a[y])[0]
        xb = np.nonzero(b[y])[0]
        if xa[0] < xb[0] - tol or xa[-1] > xb[-1] + tol:
            return False
    return len(ys) > 0


# ---- 前后深度（图层顺序）------------------------------------------------
# 一条肢体"离镜头多近"，用和 project() 同一套 3D 约定算。
#
# **判据读的是肢体末端（手/脚）的深度，不是附着点。** 摆臂的时候手才是在身上
# 横跨、压住躯干的那一头：肩关节偏离中线 7.5px，比一条 11.6px 的肢体指向镜头的
# 位移还小，只看附着点的话"伸手够镜头"会被判成"在背后"（用户 2026-10-15：
# "walk_qtr 第 3、4 帧右臂排序不正确"—— 那两帧右手正伸向镜头）。
#
# 深度的正负号是**被 project() 钉死的**，不是可调参数：
#   project() 里 sx = bX·cos(yaw) + bZ·sin(yaw)
#   就是绕竖轴转 yaw（bX = 身体横向、bZ = 朝向分量），
#   同一个旋转给出的"朝向镜头"分量只能是 depth = −bX·sin(yaw) + bZ·cos(yaw)。
#   2026-10-14 那版写成了 +sin(yaw)·bX − cos(yaw)·bZ，正好是它的相反数 ——
#   于是 |yaw| 一过 DEPTH_TIE（2.7°）远近整个反过来：远侧手臂画在前面。
#   表现就是用户连着两轮报的"稍微旋转一下躯干，左臂排序就跑到后面去了"。
#
# 朝向那项**乘了 |sin(yaw)|**：yaw=0 时矢状面完全看不见（正对镜头的方向不产生画面
# 位移），那点深度差没有任何视觉依据，留它在判据里只会让正面姿势/动画的层序随着
# 看不见的 sag 乱跳。乘掉之后正面永远退回 Z_ORDER，和以前逐像素一致。
DEPTH_TIE = 0.35        # 和躯干"贴在一起"的判定带：|深度| 不到这里就算贴着躯干 → 排前面
CROSS_MERGE = False     # 深度明显不同的两份（"近臂压在躯干前"）要不要也合并成一块。
                        # 10-15 关掉：合并了近臂就没轮廓，侧身读不出"有胳膊"（见挖缝那段）。
                        # 改回 True 就退回 10-14 那版"侧身一只手并进身体轮廓"的样子。
LEG_FLOOR = 0.35        # 腿的深度下限 —— 见 layer_order 里那段"腿永远在前"
Z_PRI = {'armL': 0, 'armR': 1, 'legL': 2, 'legR': 3, 'torso': 4}   # 同深度时的先后
SHO_OFF = SHO['R'][0] - BODY_X          # 肩的横向偏移（7.5）
HIP_OFF = HIP['R'][0] - BODY_X          # 髋的横向偏移（3.5）


def limb_depth(spec, off, yaw, lens=(0.0, 0.0), pitch=0.0):
    """一条肢体**末端**离镜头多近（大 = 近）。

    起点是附着点（横向偏移 `off`），再按两节各自的 (lat, sag) 累加位移 ——
    `lens` 是两节的长度（px，已乘比例）。spec 允许写成短的 (lat, bend)。

    镜头抬起来（pitch）之后，"离镜头多近"里**竖直方向也算数**了：往上伸的肢体离
    俯视的镜头更近（depth 里那一项 −bY·sin p）。pitch=0 时这一项正好是 0，式子
    逐位退回老样子。

    **俯仰那一项乘了 |sin(yaw)|**（2026-10-15）：和上一段"朝向那项"同一个理由。
    判据只管"两份重叠时谁在前面"，而**正对镜头时俯仰不改变任何横向关系** ——
    垂着的手臂末端天然比躯干中心低 12px，镜头一抬就整个被判到躯干**后面**，正面
    "四肢在前"这条定死的规矩当场被推翻（实测 pitch=30、yaw=0 时 79 → 69px，
    手臂被躯干啃掉一块）。乘掉之后正面任何俯仰都逐位退回 pitch=0 的样子；
    转过身后俯仰照旧起作用（那里"往上伸的离俯视镜头更近"是真看得见的）。

    实测：把排序键的 pitch 强制成 0 再渲一遍，896 张（姿势/动画帧 × 4 个镜头）
    里有 328 张变了 —— 这就是俯仰项单独造成的层序变化，也是用户 2026-10-15 报的
    "不同摄影机角度看排序还是有问题"。
    """
    y = math.radians(yaw)
    sy, cy = math.sin(y), math.cos(y)
    pr = math.radians(pitch)
    sp, cp = math.sin(pr), math.cos(pr)
    sp *= abs(sy)                                   # 见上：正面不允许俯仰改层序
    d = -sy * off * cp                              # 附着点（横向偏移，也带一点深度）
    lat, bend = spec[0], spec[1]
    sag = spec[2] if len(spec) > 2 else 0.0
    sbend = spec[3] if len(spec) > 3 else 0.0
    for ln, la, sa in zip(lens, (lat, lat + bend), (sag, sag + sbend)):
        if ln:
            la_r, sa_r = math.radians(la), math.radians(sa)
            d += ln * (-(math.cos(la_r) * math.cos(sa_r)) * sp
                       + (-sy * math.sin(la_r) * math.cos(sa_r)
                          + cy * math.sin(sa_r) * abs(sy)) * cp)
    return d


def _limb_v(pose,k,yaw,pitch):
    g=model_geometry(pose);side=k[-1];anchor=g['sho' if k.startswith('arm') else 'hip'][side]
    lens=g['limbs'][k]['lengths'];scale=pose.get('arm_scale' if k.startswith('arm') else 'leg_scale',(1.,1.))
    return limb_depth(pose.get(k,(0.,0.)),anchor[0]-BODY_X,yaw,(lens[0]*scale[0],lens[1]*scale[1]),pitch)


# 俯仰把**近臂**推到躯干后面多少个键以上才算"出问题"。0 就是"一旦为负就抬回来"。
NEAR_ARM_FLOOR = DEPTH_TIE


def _depth_key(pose, k, yaw, pitch=None):
    """部件 k 的排序键（大 = 近）。值本身只是相对量，硬要求有三条：
    torso 恒为 0、腿恒 ≥ LEG_FLOOR、**俯仰之下近臂不落到躯干后面**。

    `pitch=None` = 用姿势自己那套（`pitch_of`）。非选中视图要显式给 —— 那时全局
    的 CAM_PITCH 是**选中视图**的，不是这一次渲染的。"""
    if k == 'torso':
        return 0.0
    p = pitch_of(pose) if pitch is None else pitch
    v = _limb_v(pose, k, yaw, p)
    if k.startswith('leg'):
        # **腿永远排在躯干前面**：髋在躯干宽度**之内**（±3.5 对 4.5），转身不到 ~55°
        # 两条腿都嵌在躯干的轮廓里，一旦排到躯干后面，躯干那圈膨胀就会啃掉腿根
        # （正面/斜身会读出"脱臼"）。远侧的腿该有的纵深，靠"排在近腿后面"就够 ——
        # 侧身时两条腿本来就叠在一起。
        return max(v, LEG_FLOOR)
    if p and k.startswith('arm'):
        # **近臂不许被俯仰推到躯干后面**（2026-10-15，用户："俯视下排序依然会出错"）。
        #
        # limb_depth 里那项 `−bY·sin(p)` 让**往下垂的肢体离俯视的镜头更远** —— 物理上
        # 对，但整条键会因此翻负：pitch=60、yaw=45 时垂着的 armL 从 +7.97 掉到 −2.72，
        # 层序当场变成 `腿 腿 躯干 臂 臂`（实测量过），于是躯干那圈膨胀把近臂从中间啃穿，
        # 画面上就是"胳膊从身上飘出去一小块"。
        #
        # 判据取的是**近臂**（键比较大的那条），不是无脑给所有手臂加保底：侧身时远臂
        # 本来就该埋在躯干后面，给全臂加保底会把那层纵深抹平（idle 90° 就是这么坏的）。
        # 近臂则是"往身前推"（SIDE_PUSH）的那一条 —— 推出去的手臂却画在身子后面，
        # 自相矛盾。
        #
        # **只在 p≠0 时生效**：pitch=0 下这一支整个跳过，已验收的正面/侧身素材一个
        # 像素都不动（那是这一版最要紧的约束）。
        other = 'armR' if k == 'armL' else 'armL'
        if v > _limb_v(pose, other, yaw, p):
            return max(v, NEAR_ARM_FLOOR)
    return v if abs(v) > DEPTH_TIE else DEPTH_TIE      # 贴着躯干 → 算在躯干前面


def layer_order(pose=None, yaw=None, pitch=None):
    """按**实际的前后深度**给图层顺序。

    正面（yaw≈0）：四肢一律在前 —— 用户 2026-10-14 定的，手臂压到头/躯干上时手臂
    轮廓要完整可见。深度判据在 yaw=0 处全部退化到"贴着躯干"，自然落回 Z_ORDER。
    侧身：近侧的手臂在最前，远侧的手臂在最后，躯干夹在中间 —— 这才有纵深。
    腿一律排在躯干前面（理由见 _depth_key），两条腿之间仍按深度分前后。

    兼容老写法 layer_order(yaw)：只给一个角度时退回 2026-10-14 之前那套
    |yaw|>25° 一刀切的规则（audit.py / 旧脚本还在这么调）。
    """
    if not isinstance(pose, dict):
        pose, yaw = None, pose
    if pose is None:
        a = (yaw + 180.0) % 360.0 - 180.0
        if abs(a) < 25 or abs(a) > 155:
            return Z_ORDER
        near, far = ('R', 'L') if a > 0 else ('L', 'R')
        return ((f'arm{near}',), (f'leg{near}',), ('torso', 'head'),
                (f'leg{far}',), (f'arm{far}',))
    if yaw is None:
        yaw = yaw_of(pose)
    order = sorted(Z_PRI, key=lambda k: (-_depth_key(pose, k, yaw, pitch), Z_PRI[k]))
    return tuple(('torso', 'head') if k == 'torso' else (k,) for k in order)


def near_arm(pose, yaw=None, pitch=None):
    """近侧手臂是 'L' 还是 'R' —— **和 layer_order 用同一个键**。

    渲染里"近臂往身前推"（SIDE_PUSH）必须推的就是画在最前的那条，所以这里不能另
    写一套判据（按 yaw 正负判断的老写法在 |yaw|<25° 会和图层顺序打架：层序退回
    Z_ORDER 把 armL 放最前，推的却是 armR）。
    """
    if yaw is None:
        yaw = yaw_of(pose)
    kr = _depth_key(pose, 'armR', yaw, pitch)
    kl = _depth_key(pose, 'armL', yaw, pitch)
    if abs(kr - kl) < 1e-9:                 # 完全对称（正面）→ 和 Z_PRI 一致
        return 'L'
    return 'R' if kr > kl else 'L'


def lower_transform(pose, point, pitch):
    hips=model_geometry(pose)['hip'];pivot=((hips['L'][0]+hips['R'][0])/2, (hips['L'][1]+hips['R'][1])/2)
    q=rot(foreshorten(point,pivot,pitch_scale(pitch)),pose.get('rot',0),pivot)
    return q[0]+pose.get('dx',0),q[1]+pose.get('dy',0)

def upper_transform(pose,point,pivot,yaw,pitch):
    # Apply forward lean before yaw/pitch. A screen-space rotation incorrectly
    # converted the shoulder's lateral offset into a vertical offset at 45°.
    tilt=math.radians(pose.get('lean',0));yr=math.radians(yaw);pr=math.radians(pitch)
    height=point[1]-pivot[1]
    q=(point[0]-height*math.sin(tilt)*math.sin(yr),
       pivot[1]+height*(math.cos(tilt)*math.cos(pr)-math.sin(tilt)*math.cos(yr)*math.sin(pr)))
    q=rot(q,pose.get('rot',0),pivot)
    return q[0]+pose.get('dx',0),q[1]+pose.get('dy',0)


def head_geometry(pose, transform, yaw, pitch):
    geometry=model_geometry(pose);neck_origin = (BODY_X, geometry['neck_y']);head_center=geometry['head_c']
    angle = pose.get('lean', 0.0) + pose.get('head_pitch', 0.0)
    screen, shrink = lean_split(angle, yaw)
    delta = (head_center[0] - neck_origin[0], (head_center[1] - neck_origin[1]) * pitch_scale(pitch) * shrink)
    delta = rot(delta, screen + pose.get('head',0.0) + pose.get('rot', 0.0), (0, 0))
    anchor = transform(neck_origin)
    off = sock(pose, 'off_head', '')
    center = (anchor[0] + delta[0] + math.sin(math.radians(yaw))*1.5 + pose.get('head_side', 0) + off[0],
              anchor[1] + delta[1] + off[1])
    return center, screen + pose.get('head', 0.0) + pose.get('rot', 0.0)


LAST_SILHOUETTE = np.zeros((N,N),bool)
LAST_ATTACHMENTS = {}
LAST_CONTACTS = {}

def joint_zone(root, radius=4.0):
    yy,xx=np.ogrid[:N,:N]
    return (xx-root[0])**2+(yy-root[1])**2<=radius**2

def attachment_zone(root,anchor,radius=3.0):
    """Protect the actual socket contact, including asymmetric source edges."""
    yy,xx=np.ogrid[:N,:N];vx,vy=anchor[0]-root[0],anchor[1]-root[1]
    t=np.clip(((xx-root[0])*vx+(yy-root[1])*vy)/max(1e-6,vx*vx+vy*vy),0,1)
    capsule=(xx-root[0]-vx*t)**2+(yy-root[1]-vy*t)**2<=radius**2
    return joint_zone(root,4.0) | capsule

def separate_parts(raw_parts, order, attachments):
    """Separate occlusions while preserving socket continuity and material ownership."""
    parts={key:mask.copy() for key,mask in raw_parts.items()}
    flat=[key for group in order for key in group]
    if not NO_CARVE:
        for i,key in enumerate(flat):
            carver=np.zeros((N,N),bool)
            for front in flat[:i]:
                edge=dilate4(parts[front]) if PIXEL_PERFECT else dilate(parts[front])
                limb=front if key=='torso' else key if front=='torso' else None
                if limb in attachments:edge=edge & ~attachments[limb]
                carver |= edge
            visible=parts[key] & ~carver
            parts[key]=visible if PIXEL_PERFECT else drop_specks(visible)
    # Socket protection prevents a transparent seam; it must not change depth.
    # Give shared pixels to whichever part is actually in front in this frame.
    rank={key:i for i,key in enumerate(flat)}
    for limb,zone in attachments.items():
        if limb not in parts:continue
        overlap=parts['torso'] & parts[limb] & zone
        back=limb if rank['torso']<rank[limb] else 'torso'
        parts[back] &= ~overlap
    return parts


def render(pose, cam=None):
    """pose: dict(rot=整体旋转, dx=, dy=, lean=上半身前倾, head=头再转, yaw=转身,
                 armL=(冠状角,肘弯[,矢状角[,矢状弯]]), armR=, legL=, legR=, flip=False,
                 arm_scale / leg_scale 可选，用来压缩透视, pitch=俯仰
    头/躯干用用户原像素（转身时只做横向压缩）；四肢画完后按 SEP 像素从别的部件上削开。

    `cam=(yaw, pitch)` 是**这一次渲染**的镜头覆盖（非选中视图用；不传就走全局
    CAM_YAW / CAM_PITCH，也就是老行为）。"""
    geometry=model_geometry(pose);SHO=geometry['sho'];HIP=geometry['hip']
    rot_d = pose.get('rot', 0.0)
    yaw = yaw_of(pose, cam)          # ← 姿势朝向 + 全局摄影机偏移（见 CAM_YAW）
    pitch = pitch_of(pose, cam)      # ← 俯仰（见 CAM_PITCH）
    psc = pitch_scale(pitch)         # 垂直前缩：离髋轴越远越往中间收
    dx, dy = pose.get('dx', 0.0), pose.get('dy', 0.0)
    lean = pose.get('lean', 0.0)
    head_a = pose.get('head', 0.0)
    arm_scale = pose.get('arm_scale', (1.0, 1.0))
    leg_scale = pose.get('leg_scale', (1.0, 1.0))

    # 肩/髋的横向偏移按 cos(yaw) 收拢 —— **带符号**：转过 90° 之后小人的左肩
    # 要换到镜头的右边，不换符号的话远侧的臂会朝身体中线合拢、在背上啃出一个 V 形
    # 大缺口（正对 yaw=180 时最明显）。cos 在主视面天然连续，90° 处自然归零。
    ca = math.cos(math.radians(yaw))
    tw = yaw_scale(yaw, MIN_W_TORSO)
    sa = math.sin(math.radians(yaw))
    push = SIDE_PUSH * sa * abs(sa)                  # 近侧 +、远侧 −（见 SIDE_PUSH）

    # 前倾按真投影拆成「画面内的转角 lean_s」+「剩下那点垂直压缩 lean_k」（见 lean_split）。
    # ψ=±90 时 lean_s=lean、lean_k=1 ⇒ 正侧身逐像素不变；ψ=0 时 lean_s=0 ⇒ 不再左右歪。
    lean_s, lean_k = lean_split(lean, yaw)
    psc_l = psc * lean_k            # 俯仰与前倾的纵向压缩合成一个系数（都绕同一个髋轴）

    def anc(d, s, floor):
        """附着点横向位置 = 身体中线 + 自身偏移×cos(yaw) + 保底偏移×|sin(yaw)|。

        后半截是**保底**：cos 收拢到 0 时肩会缩到脑袋正下方，抬起的胳膊其根部圆帽
        （半径 2.9，GAP 又把它顺着胳膊方向往上推）就正好啃进头左下角。保底项按
        **自身偏移的符号**给方向，所以 90° 处连续、180° 处不跳（右边那项才是换边的）。
        保底的大小分肩/髋两档，理由见 FLOOR_HIP / FLOOR_SHO。
        """
        off = d[s][0] - BODY_X
        return (BODY_X + off * ca + math.copysign(floor * abs(sa), off), d[s][1])

    pivot = ((HIP['L'][0] + HIP['R'][0]) / 2, (HIP['L'][1] + HIP['R'][1]) / 2)

    # 胯 / 肩各自的转动：把左右两个附着点绕各自中点转，一侧抬高一侧压低。
    # 这是走路"交叉"的来源 —— 髋线一转，两条腿的起点就一高一低、一前一后。
    # 注意腿/臂的方向角**不跟着转**（保持相对躯干），只有附着点在动，
    # 这样摆幅才是可控的、不会一转就整体甩过去。
    pelvis_a = pose.get('pelvis', 0.0)
    shoulder_a = pose.get('shoulder', 0.0)
    hip = {s: add(rot(anc(HIP, s, FLOOR_HIP), pelvis_a, pivot), sock(pose, 'off_leg', s))
           for s in ('L', 'R')}
    sho_c = tuple((anc(SHO, 'L', FLOOR_SHO)[i] + anc(SHO, 'R', FLOOR_SHO)[i]) / 2 for i in (0, 1))
    sho = {s: add(rot(anc(SHO, s, FLOOR_SHO), shoulder_a, sho_c), sock(pose, 'off_arm', s))
           for s in ('L', 'R')}

    def fs(p):
        """**垂直前缩**：离髋轴越远的点越往髋轴收。俯仰、前倾各出一点（见 pitch_scale）。

        只收位置、不动姿势本身 —— 要收的是"肩/头在画面里的高度"，不是它们相对
        彼此的角度。`psc_l=1` 时这是个恒等变换。
        """
        return foreshorten(p, pivot, psc_l)

    def T(p):
        """中性坐标 → 画布坐标：先垂直前缩（俯仰+前倾），再绕髋部前倾转，再整体旋转，最后平移"""
        return upper_transform(pose,p,pivot,yaw,pitch)

    # rot() 把方向角 a 映射成 a-θ，所以这里要减号，否则整体旋转后四肢会朝反方向。
    # **用的是 lean_s 不是 lean** —— 正面时 lean_s=0，四肢就绝不跟着"往一边倒"。
    base = -rot_d

    def limb_mask(root, spec, lens, radii, shift=0.0, limb_base=None, gap=None, limb_lean=0.0):
        cov = np.zeros((N * SS, N * SS), bool)
        limb(cov, (root[0] + shift, root[1]), spec, lens, radii, yaw, base if limb_base is None else limb_base, pitch, gap=gap,lean=limb_lean)
        # 降采样用**整数求和**比 mean 快（不转 float）——`sum ≥ SS²/2` 和
        # `mean ≥ 0.5` 完全等价（SS 是偶数，SS² 也是偶数）。
        return cov.reshape(N, SS, N, SS).sum(axis=(1, 3)) >= (SS * SS) // 2

    # 每个部件单独出图，才能逐个留缝
    # 转身之后脑袋往朝向那侧探出去一点 —— 侧脸本来就不在肩膀正上方，
    # 正中顶着的话侧身像"扭着头"，探 1.5px 就顺了。
    head_dx = math.sin(math.radians(yaw)) * 1.5
    # 脖子 / 摆头（2026-10-14 用户："头部现在好像没啥控制，前倾的时候头弹出去太远了，
    # 也不能左右摆头"）。头心在髋轴上方约 23px，lean=20° 时光是绕髋转就让头横move 8px ——
    # 那是"整个人往前扑"的读法，不是"低头"。所以给一个**脖子**旋钮：
    #   neck = 0（缺省）→ 头跟着前倾整个甩出去，和以前逐像素一样
    #   neck = 1        → 脖子支住，头基本留在髋部正上方，只有躯干倒出去
    # 摆头 head_side 是**画面里的横向像素**（在 T() 之后加），所以不跟着 lean / rot 转。
    neck = max(0.0, min(1.0, pose.get('neck', 0.0) or 0.0))
    head_side = pose.get('head_side', 0.0) or 0.0
    lean_h = lean * (1.0 - neck)

    parts = {
        'torso': np.zeros((N, N), bool),
        'head': np.zeros((N, N), bool),
    }
    # 躯干是**扁盒子**：转身收横向（tw）、俯视/前倾收纵向（psc_l），和头不一样。
    place(parts['torso'], part_mask(squash(geometry['torso_mask'], tw, psc_l), lean_s + rot_d, centered=True), T(geometry['torso_c']))
    # 头永远是用户画的那些像素本身（不压横向 —— 见 MIN_W_TORSO 上面那段），
    # 转身只让它跟着身体转、并朝朝向那侧探一点。
    # **头原来被 lean 转了两次**（`T()` 里已经转过一次，外面又 `rot(HC, lean, pivot)`
    # 了一次）—— 躯干和四肢都只转一次，所以前倾时头是以**两倍**的角度甩出去的，
    # 这正是用户 2026-10-14 说的"前倾的时候头弹出去太远"。这里和躯干对齐，只转一次。
    hc, head_angle = head_geometry(pose, T, yaw, pitch)
    place(parts['head'], part_mask(geometry['head_mask'], head_angle), hc)

    # 近侧往身前挪 push、远侧往身后挪 push（sqrt 之前算好的，见 SIDE_PUSH）。
    # 近侧用 near_arm() —— 和图层顺序同一个判据，保证"推到身前的"就是"画在最前的"。
    near_side = near_arm(pose, yaw, pitch)

    limbs_map = {}
    for side in ('L', 'R'):
        sh = push if side == near_side else -push
        arm=geometry['limbs']['arm'+side];leg=geometry['limbs']['leg'+side]
        limbs_map[f'arm{side}'] = limb_mask(
            T(sho[side]), pose[f'arm{side}'],
            (arm['lengths'][0] * arm_scale[0], arm['lengths'][1] * arm_scale[1]), arm['radii'], sh, gap=arm['gap'],limb_lean=lean)
        limbs_map[f'leg{side}'] = limb_mask(          # 腿不推（见 SIDE_PUSH）
            lower_transform(pose, hip[side], pitch), pose[f'leg{side}'],
            (leg['lengths'][0] * leg_scale[0], leg['lengths'][1] * leg_scale[1]), leg['radii'], limb_base=-rot_d, gap=leg['gap'])

    parts.update(limbs_map)
    attachments={}
    # Protect existing socket contact from carving, without inventing geometry
    # between projected parts. A screen-space bridge can falsely reconnect
    # separated parts in oblique views and protrude beyond the chest silhouette.
    torso_pixels=np.argwhere(parts['torso']);LAST_CONTACTS.clear()
    for side in ('L','R'):
        for kind in ('arm','leg'):
            key=kind+side
            if not geometry['limbs'][key]['bridge']:continue
            root=T(sho[side]) if kind=='arm' else lower_transform(pose,hip[side],pitch)
            if kind=='arm':root=(root[0]+(push if side==near_side else -push),root[1])
            zone=joint_zone(root,4.0);attachments[key]=zone
            if len(torso_pixels):
                nearest=torso_pixels[np.argmin((torso_pixels[:,1]-root[0])**2+(torso_pixels[:,0]-root[1])**2)]
                anchor=(float(nearest[1]),float(nearest[0]))
                if math.hypot(anchor[0]-root[0],anchor[1]-root[1])<=5.0:
                    zone=attachment_zone(root,anchor);attachments[key]=zone;LAST_CONTACTS[key]=(root,anchor)
    global LAST_SILHOUETTE
    LAST_SILHOUETTE=np.logical_or.reduce(list(parts.values()))
    LAST_ATTACHMENTS.clear();LAST_ATTACHMENTS.update(attachments)
    parts=separate_parts(parts,layer_order(pose,yaw,pitch),attachments)
    LAST_PARTS.clear()
    LAST_PARTS.update(parts)

    cov = np.zeros((N, N), bool)
    for m in parts.values():
        cov |= m
    # Keep alpha exactly equal to the union of owned part pixels.
    # cov = fill_holes(cov)                   # 挖缝偶尔会剩一个 1px 的洞（见 fill_holes）

    if pose.get('flip'):
        cov = cov[:, ::-1]
    return cov


# ---- 姿势表 -------------------------------------------------------------
# 角度：0=朝下, 90=朝小人右侧, 180=朝上。(肩角, 肘弯) / (髋角, 膝弯)
# 角度是「相对躯干」的：躯干前倾多少（画面内那一份，见 lean_split），四肢就跟着转多少。
# 垂下来的手臂要往外撇至少 20°，否则会糊进躯干（头比躯干宽，肩膀几乎在躯干边缘）。
POSES = {
    'stand':    dict(armL=(-22, 6),  armR=(22, -6),  legL=(-6, 4),   legR=(6, -4)),
    'jump':     dict(dy=-2,  armL=(-146, -10), armR=(146, 10), legL=(-16, 32), legR=(16, -32), arm_scale=(1.32, 1.32)),
    'crouch':   dict(dy=4, lean=6, armL=(-42, 62), armR=(42, -62), legL=(-40, 68), legR=(40, -68)),
    'wallhug':  dict(armL=(-150, -18), armR=(150, 18), legL=(-8, 4), legR=(8, -4), arm_scale=(1.32, 1.32)),
    'point':    dict(armL=(-20, 6), armR=(88, -10), legL=(-5, 4), legR=(5, -4)),
    'salute':   dict(armL=(-24, 8), armR=(130, 62), legL=(-5, 4), legR=(5, -4)),
    'punch':    dict(lean=4, armL=(-52, 28), armR=(88, -4), legL=(-24, 18), legR=(20, -10)),
    'kick':     dict(lean=-6, armL=(-70, 16), armR=(62, -30), legL=(-12, 8), legR=(98, -14)),
    'dance':    dict(lean=-4, armL=(-148, 30), armR=(40, -60), legL=(-24, 28), legR=(28, -38)),
    'climb':    dict(armL=(-144, -26), armR=(138, 30), legL=(-34, 52), legR=(-8, 30), arm_scale=(1.32, 1.32)),
    'peek':     dict(dx=2, lean=6, armL=(-32, 22), armR=(12, 86), legL=(-8, 10), legR=(10, -6)),
    'carry':    dict(armL=(-142, -14), armR=(142, 14), legL=(-10, 10), legR=(10, -10), arm_scale=(1.32, 1.32)),
    'push':     dict(lean=8, armL=(-104, -4), armR=(98, -8), legL=(-26, 30), legR=(28, -12)),
    'shrug':    dict(lean=-3, armL=(-104, -32), armR=(104, 32), legL=(-8, 6), legR=(8, -6)),
    'cheer':    dict(dy=-1, armL=(-142, -8), armR=(142, 8), legL=(-12, 6), legR=(12, -6), arm_scale=(1.26, 1.26)),
    'talk':     dict(lean=4, armL=(-118, -50), armR=(16, -10), legL=(-6, 4), legR=(6, -4)),
    'highfive': dict(lean=8, armL=(-140, -14), armR=(46, 22), legL=(-16, 14), legR=(12, -8)),
    'flail':    dict(rot=-12, dy=-1, lean=-8, armL=(-138, -18), armR=(138, 22), legL=(-62, 24), legR=(40, -14)),

    # ---- 顶视角死亡姿势 ----
    # 底形 = 俯视一具摊在地上的尸体：四肢朝四方摊开的大字型。再用 rot 让整具尸体
    # 绕自身中心转到八个罗盘方向（rot=0 头朝上，顺时针每 45° 一格），于是"朝哪边倒"
    # 各有一张。四肢用 arm_scale/leg_scale 拉长一点，摊开的手脚才好认。
}


def save_pose(name, mask, outdir):
    """透明像素写成 (0,0,0,0)，和用户手绘的 Fellow1-3 一致（写成白+alpha0 容易起白边）"""
    a = np.zeros((N, N, 4), np.uint8)
    a[mask] = (255, 255, 255, 255)
    Image.fromarray(a).save(os.path.join(outdir, f'{name}.png'))


def montage(items, cols, scale, path, bg=(70, 70, 70), label=False):
    from PIL import ImageDraw
    rows = (len(items) + cols - 1) // cols
    cw, ch = N * scale, N * scale + (12 if label else 0)
    sheet = Image.new('RGB', (cw * cols, ch * rows), bg)
    dr = ImageDraw.Draw(sheet)
    for k, (name, mask) in enumerate(items):
        im = Image.new('RGBA', (N, N), (255, 255, 255, 0))
        a = np.array(im); a[mask] = (255, 255, 255, 255)
        im = Image.fromarray(a).resize((N * scale, N * scale), Image.NEAREST)
        x, y = (k % cols) * cw, (k // cols) * ch
        if label:
            dr.text((x + 3, y + 1), name, fill=(210, 210, 210))
        sheet.paste(im, (x, y + (12 if label else 0)), im)
    sheet.save(path)
    return sheet


if __name__ == '__main__':
    cli_cam()                        # python fellow.py --cam 30 → 整套立绘换观察角度
    print(f'摄影机方位角 CAM_YAW = {CAM_YAW:g}')
    os.makedirs(OUT, exist_ok=True)
    masks = {}
    for name, p in POSES.items():
        m = render(p)
        masks[name] = m
        if name != 'orig1':          # orig1 只是用来比对用户原图的，不当作成品导出
            save_pose(name, m, OUT)
        print(f'{name:10s} px={m.sum():4d}')

    # 对照：原图 vs 生成
    orig = {}
    for i in (1, 2, 3):
        a = np.array(Image.open(f'{SRC}/Fellow{i}.png').convert('RGBA'))[:, :, 3] > 0
        orig[f'ORIG{i}'] = a
    items = [(f'ORIG{i}', orig[f'ORIG{i}']) for i in (1, 2, 3)] + list(masks.items())
    # 草稿总览只写 _agent_tmp，交付目录里只留 _poses_overview.png 这一张
    montage(items, 7, 3, os.path.join(OUT, '_sheet.png'), label=True)
    montage(items, 8, 2, os.path.join(OUT, '_poses_overview.png'), label=True)
    print('sheet -> out/_sheet.png;  overview ->', os.path.join(OUT, '_poses_overview.png'),
          len(items), 'tiles')

