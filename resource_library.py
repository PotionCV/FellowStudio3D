"""Public, searchable creation catalog and pure staged combination operations.

Only registered resources are indexed. Personal files require explicit selection.
"""
import copy
from dataclasses import dataclass
from pathlib import Path
import engine as E,model_data as MD,motion_resources as MR,i18n

# Labels are deliberately separate from stable filenames and project data.
LABELS='''
DefaultModel|默认角色|Default character|標準キャラクター
CustomModel|彩绘角色|Painted character|ペイントキャラクター
TaperedCylinder|锥柱造型|Tapered cylinders|テーパー円柱
MuzzleHead|短吻角色|Short muzzle|短いマズル
LongMuzzleHead|长吻角色|Long muzzle|長いマズル
ConeHead|圆锥头|Cone head|円錐の頭
PyramidHead|棱锥头|Pyramid head|角錐の頭
BarrelBody|桶形身体|Barrel body|樽型の体
CurvedLimbs|弯曲四肢|Curved limbs|曲がった手足
PlushModel|基础布偶|Basic plush|基本ぬいぐるみ
LongTailMascot|长尾猫咪|Long-tail cat|長いしっぽの猫
FluffyTailMascot|蓬松尾伙伴|Fluffy-tail buddy|ふわふわしっぽ
BobtailMascot|短尾长耳伙伴|Bobtail long-ear buddy|短いしっぽと長い耳
SwordShieldAdventurer|剑盾冒险者|Sword and shield adventurer|剣と盾の冒険者
StaffMage|持杖法师|Staff mage|杖の魔法使い
TwinBladeDancer|双剑舞者|Twin-blade dancer|双剣の踊り手
BlinkingBuddy|眨眼伙伴|Blinking buddy|まばたきの仲間
ChattyMascot|聊天布偶|Chatty mascot|おしゃべりマスコット
SurprisedJumper|惊讶伙伴|Surprised buddy|びっくりの仲間
Idle|待机|Idle|待機
Walk|行走|Walk|歩く
Run|奔跑|Run|走る
ComboPunchKick|出拳接踢腿|Punch then kick|パンチからキック
WalkGreetBow|走近招手鞠躬|Walk, greet and bow|歩いて挨拶とお辞儀
JumpThenRoll|跳跃接翻滚|Jump then roll|ジャンプから回転
SideStepDance|侧步舞蹈|Side-step dance|サイドステップの踊り
GuardSignal|防守示意|Guard signal|防御の合図
ShyGreeting|害羞问候|Shy greeting|照れた挨拶
SwimBreaststroke|蛙泳|Breaststroke|平泳ぎ
SwimFrontCrawl|自由泳|Front crawl|クロール
TreadWater|踩水|Tread water|立ち泳ぎ
Hover|空中悬浮|Hover|空中浮遊
HoverWave|悬浮招手|Hover and wave|浮遊して手を振る
FloatingMage|空中施法|Floating mage|空中で魔法
SwimLookAround|游泳环顾|Swim and look around|泳いで見回す
Climb|攀爬|Climb|登る
Fall|倒地|Fall|倒れる
Getup|起身|Get up|起き上がる
Hitreaction|受击|Hit reaction|被弾
Jump|跳跃|Jump|ジャンプ
Kick|踢腿|Kick|キック
PushKick|蹬踢|Push kick|押し蹴り
Roll|翻滚|Roll|回転
Swingattack|挥击|Swing attack|振り攻撃
Thrust|突刺|Thrust|突き
Turn|转身|Turn|旋回
Waisttwist|扭腰|Waist twist|腰をひねる
Pickup|拾起|Pick up|拾う
PutDown|放下|Put down|置く
LiftOverhead|举过头顶|Lift overhead|頭上に持ち上げる
LeanBack|后仰|Lean back|後ろに反る
WideSquat|宽站深蹲|Wide squat|開脚スクワット
Backpedal|后退步|Backpedal|後退ステップ
CombatStance|战斗架势|Combat stance|戦闘の構え
CombatStraightPunch|直拳攻击|Straight punch|ストレートパンチ
CrouchWalk|蹲伏行走|Crouch walk|しゃがみ歩き
GuardAndThrust|防守突刺|Guard and thrust|防御と突き
JumpKick|跳踢|Jump kick|ジャンプキック
RunAim|奔跑瞄准|Run and aim|走って狙う
RunJumpRoll|跑跳翻滚|Run, jump and roll|走ってジャンプと回転
RunTimedSwing|奔跑挥击|Run and swing|走って振り攻撃
RunWaveLeft|奔跑左手招呼|Run and wave left|走って左手を振る
StrafeWalk|侧向行走|Strafe walk|横歩き
WalkCarry|行走搬运|Walk and carry|歩いて運ぶ
WalkGuard|行走防守|Walk and guard|歩いて防御
CombatTwist|扭腰战斗|Combat twist|腰をひねって戦う
CombatPushKick|战斗蹬踢|Combat push kick|戦闘の押し蹴り
ForwardCarry|前进搬运|Forward carry|前進して運ぶ
'''
NAMES={row.split('|')[0]:tuple(row.split('|')[1:]) for row in LABELS.strip().splitlines()}
TAGS={
 'SwimBreaststroke':'游泳 水中 swim swimming water 泳ぐ 水中',
 'SwimFrontCrawl':'游泳 水中 swim swimming water 泳ぐ 水中',
 'TreadWater':'游泳 水中 swim swimming water 泳ぐ 水中',
 'Hover':'飞行 空中 floating flying 飛行 空中',
 'FloatingMage':'飞行 空中 施法 magic flying 魔法 空中',
 'HoverWave':'飞行 空中 问候 greeting flying 挨拶 空中',
 'StaffMage':'武器 魔法 装备 weapon magic equipment 杖 魔法 装備',
 'SwordShieldAdventurer':'武器 战斗 装备 weapon combat equipment 武器 戦闘 装備',
 'TwinBladeDancer':'武器 战斗 装备 weapon combat equipment 武器 戦闘 装備',
 'BlinkingBuddy':'表情 眨眼 face blink 顔 まばたき',
 'ChattyMascot':'表情 眨眼 说话 face blink talk 顔 まばたき 会話',
 'SurprisedJumper':'表情 face 顔'}

def label(key,language=None):
 values=NAMES.get(key,(key,key,key))
 return values[{'zh':0,'en':1,'ja':2}.get(language or i18n.language,1)]

@dataclass(frozen=True)
class Resource:
 kind:str
 path:str
 category:str
 @property
 def key(self):return Path(self.path).stem
 @property
 def title(self):return label(self.key)


def catalog(personal_folder=None,motion_folder=None):
 result=[]
 for path in MR.BUILTIN_MOTIONS:
  category={'game':'游戏动作','fusions':'动作融合','sequences':'动作串联','posecards':'姿势表演'}.get(Path(path).parent.name,'基础步态')
  result.append(Resource('motions',path,category))
 for path in MD.BUILTIN_MODELS:
  stem=Path(path).stem
  category='布偶伙伴' if stem=='PlushModel' else '基础造型'
  result.append(Resource('models',path,category))
 if personal_folder:
  folder=Path(personal_folder)
  # Explicitly curated complete characters, not every experimental local file.
  for name in ('KumamonBag','CatBag'):
   path=folder/(name+'.json')
   if not path.is_file():path=E.ROOT/'local_characters'/(name+'.json')
   if path.is_file():result.append(Resource('models',str(path.resolve()),'我的角色'))
 if motion_folder and Path(motion_folder).is_dir():
  result.extend(Resource('motions',str(path.resolve()),'我的动画') for path in sorted(Path(motion_folder).glob('*.json')))
 return tuple(result)

NAMES.update(KumamonBag=('熊本熊','Kumamon','くまモン'),CatBag=('猫咪布偶','Painted cat mascot','猫のマスコット'))

def search(resources,kind,query='',category='全部'):
 words=query.casefold().split()
 return [r for r in resources if r.kind==kind and (category=='全部' or r.category==category)
         and all(word in ' '.join((r.path,r.category,*NAMES.get(r.key,()),TAGS.get(r.key,''),i18n.tr(r.category))).casefold() for word in words)]

def apply_model(current,path):
 resource=MD.load_resource(path);result=copy.deepcopy(current)
 density=MD.pixel_density(resource['model'])
 if density>1:
  result.setdefault('render',{}).update(canvas_width=max(64*density,result.get('render',{}).get('canvas_width',64)),canvas_height=max(64*density,result.get('render',{}).get('canvas_height',64)))
 result['model']=resource['model']
 # No embedded paint means the new model uses its defaults. Never borrow the
 # previous character's face/paint/attachment IDs by accident.
 result.pop('assets3d',None)
 if 'assets3d' in resource:result['assets3d']=resource['assets3d']
 return result

def combine(current,resource):
 if resource.kind=='motions':return MR.apply_motion(current,E.load(E.ROOT/'examples/motions'/resource.path))
 if resource.kind=='models':return apply_model(current,E.ROOT/'examples/models'/resource.path)
 raise ValueError('Unknown resource type')
