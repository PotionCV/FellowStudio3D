# -*- coding: utf-8 -*-
"""元动作层 —— 这个工具的全部"动作词汇"。

一个层是一个**纯函数**：

    at(相位 t, 参数 P, 朝向 yaw) -> {关节: 值}

- `t` 是这一层自己的相位，0..1 一整个循环（`motion.py` 按"跑几趟"把它算出来）。
- 返回的关节写在 `claims` 里。**引擎按"上面的层接管下面的层"合成**，
  所以一个层只要声明它要动哪些关节，不用管别人在做什么。
- `add` 里列出的关节是**叠加**（在别人算好的结果上加），其余是**接管**（直接覆盖）。
  摇头、点头这种"不管身体在干嘛，我都要摇"的，就该是叠加。

参数表 `params` 里 `hide=True` 的是**内置微调**：界面上折在「更多」里，
不挡普通人的视线，但测试和较真的时候够得着。
"""

import math

import gaitdata as GD

TAU = math.pi * 2.0


# ---------------------------------------------------------------- 小工具
def P(key, label, lo, hi, dflt, step=0.05, hide=False, unit=''):
    return dict(key=key, label=label, lo=float(lo), hi=float(hi),
                dflt=float(dflt), step=float(step), hide=hide, unit=unit)


def sample(vals, t):
    """8 个相位上的环形线性插值。`t` 恰好落在采样点上时**精确返回采样值** ——
    "新引擎在 0° / 90° 两端等于旧工具那两套数据"这条就是靠它成立的。"""
    x = (t % 1.0) * len(vals)
    i = int(math.floor(x))
    f = x - i
    a, b = vals[i % len(vals)], vals[(i + 1) % len(vals)]
    return a + (b - a) * f


def sat(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


class Layer:
    kind = ''
    label = '层'
    period = 8                     # 一个循环几帧（用来算默认"跑几趟"）
    hint = ''                      # 界面上的一行说明
    claims = ()                    # 这一层会返回的关节
    add = ()                       # 其中这些是"叠加"，其余是"接管"
    params = ()

    @classmethod
    def defaults(cls):
        return {p['key']: p['dflt'] for p in cls.params}

    @classmethod
    def touches(cls, key):
        """这个参数管着哪几个关节 —— 界面上"被上面的层接管了"就是拿它算的。
        默认：整层管什么，每个参数就管什么（大多数层都成立）。"""
        return tuple(cls.claims)


# ================================================================ 底座
class Stand(Layer):
    kind, label, period = 'stand', '站姿', 24
    hint = '永远是底下那一层。它让小人活着：轻轻地呼吸。'
    claims = ('dy', 'head')
    params = (P('breath', '呼吸', 0.0, 2.0, 0.9, 0.05, unit='×'),
              P('sway', '重心晃', 0.0, 2.0, 0.0, 0.05, unit='×'))
    TOUCH = {'breath': ('dy',), 'sway': ('head',)}

    @classmethod
    def touches(cls, key):
        return cls.TOUCH.get(key, tuple(cls.claims))

    @classmethod
    def at(cls, t, p, yaw):
        b = p['breath'] * (0.5 - 0.5 * math.cos(TAU * t))
        s = p['sway'] * math.sin(TAU * t)
        return {'dy': -b, 'head': s * 0.5}


# ================================================================ 走 / 跑
# **数据就是原工具当前那两套：侧身卡通档（`WALK_S_C` / `RUN_S_C`）。**
#
# 原工具有三套走姿数据（正面 / 45° / 侧面），但 `make_side(yaw=N)` 只往姿势里
# 写一个 `yaw`、**关节值逐位相同** —— 所以这里根本不用按朝向混合：一层加姿势
# 自己的「朝向」就够，任何朝向都逐位等于原工具那三套里的对应一套。
#
# ⚠ **我踩过的坑，别再犯**：第一版这里把"正面那两套"（`WALK_C` / `RUN_C`）当 0°
# 那端、用 |sin yaw| 跟侧身混。那正是原工具 `anim.py` 里标着「备用」、用户
# 2026-10-15 明确否掉的一对（"我不是让你换回去，是把当前的转一下方向"）——
# 用户一眼看出"走路跑步怎么又用回最早的了"。数据源是
# `editor/editor_saves.json` 里那两条覆盖（= `WALK_S_C` / `RUN_S_C` 关节值，
# `yaw`/`lean` 归零，跑那条右臂手调过）。
#
# 代价（用户当年拍板时就认了）：侧身数据摆到正面，前后摆投影成 0，正面看着像
# 站着微微起伏。要正面看出在走，只有换正面数据或留 20~30° 角。
#
# 另一件必须照抄的：**原工具那两条覆盖上还挂着一条「整体增益」**（编辑器右栏那六条
# 滑杆，`anim.py` 的 `MOD_DFLT` / `apply_mod`）。用户手调过的正是这条 —— 跑的
# 腿摆 ×1.5、抬手臂 60°、前甩 75°、脱力 0.4、前倾 20°。不抄它，走路跑步就只是
# "数据对、样子不对"。这里把它整个搬成 `MOD`（见下），摆幅那几路连**绕均值放大**
# 的细节一起照抄 —— 那是用户当年投诉过"摆臂好像在打拳"之后才改对的，
# 绕 0 放大就又会打拳。
class Gait(Layer):
    DATA = 'walk'
    GAIN = {}                     # 这套数据当年量的增益（照抄 mocap_keys 的 *C 表）
    MOD = {}                      # 原工具那条覆盖上的整体增益，键名同 anim.MOD_DFLT
    LAT_MEAN = 0.0                # 手调张角 `arm_lat` 的 8 拍平均值（见 `swing`）
    SCALE = ()                    # ((参数键, 增益键...), ...) 用户参数怎么缩增益

    claims = ('legL', 'legR', 'armL', 'armR', 'dy', 'lean', 'yaw',
              'neck', 'head','chest_yaw','pelvis_yaw')
    add = ('neck', 'head')        # 脱力的头/脖子是"加一手"，不接管站姿的呼吸
    params = (P('stride', '步幅', 0.0, 2.0, 1.0, unit='×'),
              P('knee', '抬腿', 0.0, 2.0, 1.0, unit='×'),
              P('swing', '摆臂', 0.0, 2.0, 1.0, unit='×'),
              P('bob', '上下颠', 0.0, 2.0, 1.0, unit='×'),
              P('elbow', '肘弯', 0.0, 2.0, 1.0, 0.05, hide=True, unit='×'),
              P('twist','跨步扭转',0.0,2.0,1.0,.05,unit='×'))

    TOUCH = {'stride': ('legL', 'legR'), 'knee': ('legL', 'legR'),
             'swing': ('armL', 'armR'), 'bob': ('dy',),
             'elbow': ('armL', 'armR'),'twist':('chest_yaw','pelvis_yaw')}

    @classmethod
    def touches(cls, key):
        return cls.TOUCH.get(key, tuple(cls.claims))

    @classmethod
    def gains(cls, p):
        """数据当年量的增益再乘用户参数。这几个是**倍数**不是绝对值 ——
        1.0 就是"和原工具交付的一模一样"。"""
        g = dict(cls.GAIN)
        for key, ks in cls.SCALE:
            u = p[key]
            for k in ks:
                g[k] = g.get(k, 0.0) * u
        g['elbow'] = g.get('elbow', 0.0) * p['elbow']
        return g

    @classmethod
    def arm_lat(cls, t, p):
        """右臂的左右张角。侧身那套数据全在矢状面、这里是 0；跑的 8 个数是
        用户在编辑器里手调出来的，照抄在 `gaitdata.RUN_ARMR_LAT`。"""
        return 0.0

    @classmethod
    def at(cls, t, p, yaw):
        """`yaw` 参数不参与计算 —— 朝向由 `motion.pose_at` 写进姿势里（和原工具一致）。"""
        run=cls.DATA=='run'
        a=math.sin(TAU*t);b=-a
        stride=(42 if run else 25)*p['stride']
        knee=(90 if run else 42)*p['knee']
        swing=(42 if run else 24)*p['swing']
        legs=[(0.,0.,stride*v,-(8+max(0.,v)*knee)) for v in (a,b)]
        # One symmetric rise/fall per step; both legs use the same phase function.
        vertical=[6*math.cos(math.radians(v[2]))+6*math.cos(math.radians(v[2]+v[3])) for v in legs]
        dy=(11.8-max(vertical))*p['bob']
        return dict(legL=legs[0],legR=legs[1],
                    armL=(-12.,0.,-swing*a,(65 if run else 15)*p['elbow']),
                    armR=(12.,0.,swing*a,(65 if run else 15)*p['elbow']),
                    dy=dy,lean=10. if run else 0.,yaw=0.,
                    chest_yaw=-(10. if run else 6.)*a*p.get('twist',1.),
                    pelvis_yaw=(12. if run else 8.)*a*p.get('twist',1.))


class Walk(Gait):
    kind, label, period = 'walk', '走路', 8
    hint = '左右交替是这一层自带的 —— 不用摆，也不用镜像。'
    DATA = 'walk'
    # mocap_keys.CART_S —— 走路侧身那套用的增益
    GAIN = dict(leg=1.35, knee=1.25, arm=1.60, dy=7.5, elbow=34.0)
    MOD = dict(dy=0.5)            # editor_saves 里 `anims.walk.mod`
    SCALE = (('stride', ('leg',)), ('knee', ('knee',)),
             ('swing', ('arm',)), ('bob', ('dy',)))


class Run(Gait):
    kind, label, period = 'run', '跑步', 6
    hint = '和走路同一套数据，只是抬腿更高、摆臂更大。'
    DATA = 'run'
    # mocap_keys.CART_RUN_S —— 跑步侧身那套用的增益
    GAIN = dict(leg=1.35, knee=1.35, arm=1.75, dy=6.5, elbow=84.0)
    # editor_saves 里 `anims.run.mod` —— 用户手调的那一版：腿摆更大、胳膊收小
    # 抬起来往前甩、脱力甩小臂、整体前倾一点。
    MOD = dict(leg=1.5, knee=1.05, arm=0.6, dy=0.4,
               up=60.0, back=-75.0, limp=0.4, lean=20.0, yaw=-5.0)
    LAT_MEAN = sum(GD.RUN_ARMR_LAT) / len(GD.RUN_ARMR_LAT)
    SCALE = (('stride', ('leg',)), ('knee', ('knee',)),
             ('swing', ('arm',)), ('bob', ('dy',)))

    @classmethod
    def arm_lat(cls, t, p):
        return sample(list(GD.RUN_ARMR_LAT), t)

    @classmethod
    def _source_at(cls, t, p, yaw):
        """`yaw` 参数不参与计算 —— 朝向由 `motion.pose_at` 写进姿势里（和原工具一致）。"""
        ph, av = GD.DATA[cls.DATA]['ph'], GD.DATA[cls.DATA]['av']
        mv, m = GD.MEAN8DEV[cls.DATA], cls.MOD
        g = cls.gains(p)

        def s(key):
            return sample([r[key] for r in ph], t)

        def dev(key):                 # 偏离平均值 = 矢状面上的真角度
            return s(key) - av[key]

        def amp(key):
            return m.get(key, 1.0)

        def swing(v, mu, gain, amp_key, user=1.0):
            """一路摆动量。**两个分量都要**：

            第一个是值 —— 绕这 8 拍的均值放大（原工具 `apply_mod` 的做法；绕 0 放大
            就会打拳，见 `anim.mod_means`）。`gains()` 已经把用户倍数折进 `gain` 了，
            别再乘一次。绕均值放大写成"乘 `a` 加常数"之后，就能和增益的乘除叠在一起。
            第二个是**相对均值的那一份**，脱力要拖的正是它。"""
            a = amp(amp_key)
            if abs(a) < 1e-9:
                return 0.0, 0.0
            return ((v + mu * (1.0 - a) / a) * gain * a * user,
                    (v - mu) * gain * a * user)

        up, back, limp = m.get('up', 0.0), m.get('back', 0.0), m.get('limp', 0.0)
        # 左右张角：数据本身全在矢状面，这一路只有"抬手臂"和用户手调的右臂张角
        hinge, dHinge = swing(cls.arm_lat(t, p), cls.LAT_MEAN, 1.0, 'arm',
                              p['swing'])
        latL, dLatL = -up, -up
        latR, dLatR = up + hinge, up + dHinge
        # 矢状面：摆动 ± 前甩/后甩（`back` 正 = 甩到身后，和原工具同号）
        sagL, dSagL = swing(dev('afL'), mv['afL'], g['arm'], 'arm')
        sagR, dSagR = swing(dev('afR'), mv['afR'], g['arm'], 'arm')
        sagL, sagR = sagL - back, sagR - back
        dSagL, dSagR = dSagL - back, dSagR - back
        # 膝盖**不带 `amp('knee')`**：原工具那条 `knee` 增益乘的是肢体四元组的第 2 位
        # （`bend`），而侧身数据的那一位恒为 0（`mocap_keys.side_at` 只往第 3 位写膝盖），
        # 所以它在原工具里对这一套是**空转的** —— 抄上它反而和原工具不一样。
        # 用户的「抬腿」滑杆走的是 `g['knee']`（数据增益 × 用户倍数），照常有效。
        kn = g['knee']
        lean = m.get('lean', 0.0)
        out = {
            'legL': (0.0, 0.0, swing(dev('fxL'), mv['fxL'], g['leg'], 'leg')[0],
                     -max(0.0, s('knL')) * kn),
            'legR': (0.0, 0.0, swing(dev('fxR'), mv['fxR'], g['leg'], 'leg')[0],
                     -max(0.0, s('knR')) * kn),
            # 脱力：小臂拖大臂，拖的是**套过抬臂/前甩之后**的偏离（原工具注释：
            # 这样"摆臂调大 + 脱力"才一起放大，读出来是甩鞭子；不摆时它什么也不做）
            'armL': (latL, -limp * dLatL, sagL,
                     g['elbow'] * p['elbow'] - limp * dSagL),
            'armR': (latR, -limp * dLatR, sagR,
                     g['elbow'] * p['elbow'] - limp * dSagR),
            'dy': swing(dev('y'), mv['y'], -g['dy'], 'dy')[0],
            'lean': lean,
            'yaw': m.get('yaw', 0.0),
        }
        if limp:
            # 脱力也管头：脖子松掉（头不跟着前倾整个甩出去）+ 头自己往后仰一点。
            # 原工具那两份都取**最终**的 lean，所以这里也带上这一层的前倾。
            out['neck'] = 0.8 * limp
            out['head'] = -0.6 * limp * lean
        return out


    @classmethod
    def at(cls, t, p, yaw):
        out=cls._source_at(t,p,yaw)
        # Preserve the original support/recovery and body-height timing.
        # Remove the old raised/forward arm posture while retaining its swing waveform.
        refs=[cls._source_at(i/8,p,yaw) for i in range(8)]
        for key,lat in (('armL',-12.),('armR',12.)):
            mean=sum(q[key][2] for q in refs)/8
            out[key]=(lat,0.,out[key][2]-mean,65.*p['elbow'])
        out.pop('neck',None);out.pop('head',None)
        out['yaw']=0.
        # Derive torso timing from the retained run stride, not a new sine wave.
        deltas=[q['legL'][2]-q['legR'][2] for q in refs];mean=sum(deltas)/len(deltas)
        phase=(out['legL'][2]-out['legR'][2]-mean)/max(1.,max(abs(v-mean) for v in deltas))
        out['chest_yaw']=-10.*phase*p.get('twist',1.)
        out['pelvis_yaw']=12.*phase*p.get('twist',1.)
        return out


# ================================================================ 上身动作
class Wave(Layer):
    kind, label, period = 'wave', '挥手', 12
    hint = '举一只手摆。抬多高、挥几下都能调，摆的是手，不是整条胳膊。'
    claims = ('armR',)
    params = (P('raise', '举多高', 40.0, 175.0, 140.0, 2.0, unit='°'),
              P('times', '挥几下', 1, 4, 2, 1, unit=' 次'),
              P('amp', '摆多开', 4.0, 45.0, 22.0, 1.0, unit='°'))

    @classmethod
    def at(cls, t, p, yaw):
        k = int(round(p['times']))
        s = math.sin(TAU * k * t)
        # 冠状面上摆（正面看得见：手在头顶左右摇）＋矢状面上摆（侧身看得见：
        # 手在身前前后摇）。**两条都要** —— 只给一条的话，转到另一个朝向就成
        # 一尊举着手的雕像了。
        return {'armR': (p['raise'],
                         -p['amp'] * s,
                         14.0,
                         p['amp'] * 0.9 * s)}


class RaiseArms(Layer):
    kind, label, period = 'raise', '举手', 24
    hint = '两只手举起来。和「站姿」叠在一起就是"站着举东西"。'
    claims = ('armL', 'armR')
    params = (P('up', '举多高', 0.0, 175.0, 150.0, 2.0, unit='°'),
              P('open', '分开', 0.0, 60.0, 10.0, 1.0, unit='°'))

    @classmethod
    def at(cls, t, p, yaw):
        u, o = p['up'], p['open']
        return {'armL': (-u - o * 0.35, -8.0, 0.0, 0.0),
                'armR': (u + o * 0.35, 8.0, 0.0, 0.0)}


class ShakeHead(Layer):
    kind, label, period = 'shake', '摇头', 8
    hint = '左右摇头。叠加层 —— 走路、挥手都照做，它只管头。'
    claims = ('head_side',)
    add = ('head_side',)
    params = (P('amp', '幅度', 0.0, 4.0, 2.6, 0.1, unit='×'),
              P('times', '摇几下', 1, 4, 2, 1, unit=' 次'))

    @classmethod
    def at(cls, t, p, yaw):
        value=p['amp']*math.sin(TAU*int(round(p['times']))*t)
        return {'head_side':value,'head_yaw':value*10.}


class Nod(Layer):
    kind, label, period = 'nod', '点头', 8
    hint = '上下点头。也是叠加层。'
    claims = ('head', 'off_head')
    add = ('head', 'off_head')
    params = (P('amp', '幅度', 0.0, 1.0, 0.6, 0.05, unit='×'),
              P('times', '点几下', 1, 4, 2, 1, unit=' 次'))

    @classmethod
    def at(cls, t, p, yaw):
        s = p['amp']
        u = 0.5 - 0.5 * math.cos(TAU * int(round(p['times'])) * t)
        return {'head_pitch': 35.0 * s * u}


class Bow(Layer):
    kind, label, period = 'bow', '弯腰', 14
    hint = '弯下去再起来。只动上身，手该干嘛干嘛。'
    claims = ('lean', 'dy')
    params = (P('deep', '弯多少', 0.0, 45.0, 28.0, 1.0, unit='°'),
              P('hold', '停一下', 0.0, 0.6, 0.15, 0.05, unit='×'))

    @classmethod
    def at(cls, t, p, yaw):
        u = 0.5 - 0.5 * math.cos(TAU * t)
        u = sat((u - p['hold']) / max(1e-6, 1.0 - p['hold']))
        return {'lean': p['deep'] * u}


class Stretch(Layer):
    kind, label, period = 'stretch', '伸展', 20
    hint = '伸个懒腰：手举高、身子往后仰，再放下来。'
    claims = ('armL', 'armR', 'lean')
    params = (P('open', '伸多开', 0.0, 1.0, 0.85, 0.05, unit='×'),
              P('back', '后仰', 0.0, 18.0, 7.0, 1.0, unit='°'))
    TOUCH = {'open': ('armL', 'armR'), 'back': ('lean',)}

    @classmethod
    def touches(cls, key):
        return cls.TOUCH.get(key, tuple(cls.claims))

    @classmethod
    def at(cls, t, p, yaw):
        u = 0.5 - 0.5 * math.cos(TAU * t)
        a = p['open'] * u
        return {'armL': (-(22.0 + 140.0 * a), -6.0 - 20.0 * a, 0.0, 0.0),
                'armR': (22.0 + 140.0 * a, 6.0 + 20.0 * a, 0.0, 0.0),
                'lean': -p['back'] * u}


class Squat(Layer):
    kind, label, period = 'squat', '蹲下', 16
    hint = '蹲下去再站起来。'
    claims = ('legL', 'legR', 'dy', 'lean')
    params = (P('deep', '蹲多深', 0.0, 1.0, 0.75, 0.05, unit='×'),)

    @classmethod
    def at(cls, t, p, yaw):
        u = 0.5 - 0.5 * math.cos(TAU * t)
        d = p['deep'] * u
        return {'legL': (0.0, 0.0, 55.0*d, -110.0*d),
                'legR': (0.0, 0.0, 55.0*d, -110.0*d),
                'dy': 12.0*(1-math.cos(math.radians(55*d))),
                'lean': 6.0 * d}


class Bounce(Layer):
    kind, label, period = 'bounce', '弹跳', 12
    hint = '原地一上一下地弹。'
    claims = ('legL', 'legR', 'dy')
    params = (P('high', '弹多高', 0.0, 8.0, 4.0, 0.25, unit=' 像素'),
              P('tuck', '收腿', 0.0, 1.0, 0.5, 0.05, unit='×'))
    TOUCH = {'high': ('dy', 'legL', 'legR'), 'tuck': ('legL', 'legR')}

    @classmethod
    def touches(cls, key):
        return cls.TOUCH.get(key, tuple(cls.claims))

    @classmethod
    def at(cls, t, p, yaw):
        u = 0.5 - 0.5 * math.cos(TAU * t)          # 0 落地 → 1 最高
        h = p['high']
        tuck = p['tuck'] * u
        return {'dy': -h * u - 1.0 * (1.0 - u) * p['tuck'],
                'legL': (0.0, 0.0, 35.0*tuck, -70.0*tuck),
                'legR': (0.0, 0.0, 35.0*tuck, -70.0*tuck)}


# ================================================================ 注册表
KINDS = {}
for _C in (Stand, Walk, Run, Wave, RaiseArms, ShakeHead, Nod, Bow, Stretch, Squat, Bounce):
    KINDS[_C.kind] = _C

# 菜单里按这个顺序排（好懂的在前，底座单独拎出来）
MENU = ('walk', 'run', 'wave', 'raise', 'stretch', 'squat', 'bounce',
        'bow', 'shake', 'nod')
