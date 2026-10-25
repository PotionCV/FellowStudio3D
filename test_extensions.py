"""Behavior checks for editable shapes and game-oriented motion extensions."""
import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
import engine as E,model_data as M,rounded_scene as S

class ExtensionTests(unittest.TestCase):
 def test_signed_bend_nod_and_stretch_change_actual_direction(self):
  for kind,key,channel,amount in (('bow','deep','lean',35),('nod','amp','head_pitch',.8),('stretch','back','lean',20),('shake','amp','head_yaw',3)):
   e=E.entry(kind);e['mode']='once';e['params'][key]=amount;forward=E.samples(e,17)
   e['params'][key]=-amount;reverse=E.samples(e,17)
   np.testing.assert_allclose([q[channel] for q in reverse],[-q[channel] for q in forward])
   self.assertGreater(max(abs(q[channel]) for q in reverse),1)
   for i in (0,16):self.assertAlmostEqual(reverse[i][channel],0,places=10)

 def test_squat_leg_spread_changes_width_keeps_floor_and_preserves_legacy_zero(self):
  from layers import Squat
  params=Squat.defaults()
  for t in (0,.125,.5,.875,1):
   q=Squat.at(t,params,0);d=params['deep']*(.5-.5*np.cos(np.pi*2*t))
   np.testing.assert_allclose(q['legR'],[0,0,55*d,-110*d]);self.assertNotIn('_ground',q)
   self.assertAlmostEqual(q['dy'],12*(1-np.cos(np.radians(55*d))))
  spans={}
  for spread in (-15,0,35):
   p=E.new_project('squat');p['base']['params']['spread']=spread;p.update(fps=25,seconds=2)
   q=E.authored(p)[25];chain=S.geometry(q)[2];spans[spread]=chain['legR'][-1][0]-chain['legL'][-1][0]
   np.testing.assert_allclose(chain['legL'][-1]*[-1,1,1],chain['legR'][-1],atol=1e-10)
  self.assertLess(spans[-15],spans[0]);self.assertGreater(spans[35],spans[0]+6)
  for model in (M.normalize(),M.load(E.ROOT/'examples/models/CustomModel.json')):
   p=E.new_project('squat');p.update(model=model,seconds=2,fps=25);p['base']['params'].update(spread=65,deep=1)
   seq=E.authored(p);reference=E._ground_level(json.dumps(model,sort_keys=True))
   for q in seq[1:-1]:self.assertAlmostEqual(S.ground_y(q,('thighL','shinL','thighR','shinR')),reference,places=6)
   jump=E.new_project('jump');before=E.authored(jump);e=E.entry('squat');e['params']['spread']=45;jump['layers']=[e]
   for a,b in zip(before,E.authored(jump)):
    if a.get('_ground') is False:self.assertIs(b['_ground'],False);self.assertAlmostEqual(a['dy'],b['dy'])

 def test_signed_body_follow_pelvis_and_travel_reverse_without_reversing_attack(self):
  for kind,key,channels in (('thrust','twist',('chest_yaw','pelvis_yaw')),('swing','twist',('chest_yaw','pelvis_yaw')),('kick','twist',('chest_yaw','pelvis_yaw')),('twist','hips',('pelvis_yaw',)),('roll','distance',('dx','dz')),('climb','bob',('dy',)),('turn','lead',('chest_yaw','pelvis_yaw'))):
   e=E.entry(kind);e['params'][key]=.8;positive=E.samples(e,21);e['params'][key]=-.8;negative=E.samples(e,21)
   for channel in channels:np.testing.assert_allclose([q.get(channel,0) for q in negative],[-q.get(channel,0) for q in positive],atol=1e-12)
   if kind in ('thrust','swing','kick'):
    for limb in E.LIMBS:
     if limb in positive[0]:np.testing.assert_allclose([q[limb] for q in negative],[q[limb] for q in positive])

 def test_signed_raise_and_motion_range_and_json_roundtrip(self):
  e=E.entry('raise');e['params'].update(up=-120,open=15,fold=-40);q=E.samples(e,2)[0]
  np.testing.assert_allclose(q['armR'][2:],[-120,-40]);self.assertLess(S.geometry(q)[2]['armR'][-1][2],0)
  p=E.new_project('walk');p.update(physics={},controls={'armR':{'range':1}});normal=E.authored(p)
  p['controls']['armR']['range']=-1;reverse=E.authored(p)
  a=np.array([q['armR'] for q in normal]);b=np.array([q['armR'] for q in reverse]);np.testing.assert_allclose(b,2*a.mean(axis=0)-a,atol=1e-10)
  p['controls']['armR']['fold']=-45
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'Reverse.json';E.save(p,path);saved=E.load(path)
   self.assertEqual(saved['controls']['armR'],p['controls']['armR']);self.assertTrue(E.poses(saved))

 def test_ik_inner_fk_matches_rendered_chain_without_rebuilding_model(self):
  import rig as R
  from unittest.mock import patch
  rng=np.random.default_rng(812)
  p=E.norm(E.F.POSES['stand']);p.update(_model=M.load(E.ROOT/'examples/models/CustomModel.json'),
   lean=25,rot=-12,body_pitch=35,body_axis=45,body_pivot=10,chest_yaw=32,pelvis_yaw=-20,
   pelvis=7,shoulder=-9,dx=2,dy=3,dz=-1,_camera_y=4,leg_scale=[1.1,.9],arm_scale=[.9,1.2],off_legL=[2,-1],off_armR=[-1,2])
  views=[(angle,(0,0)) for angle in (0,45,135)]
  for limb in E.LIMBS:
   project=R._limb_tip_projector(p,limb,views)
   for _ in range(12):
    spec=rng.uniform([-50,-25,-70,-130],[50,25,110,80])
    expected=np.array([v for yaw,target in views for v in R.chain(dict(p,yaw=yaw,pitch=0),limb,spec)[3]])
    with patch.object(S,'limb_chain',side_effect=AssertionError('IK rebuilt FK')),patch.object(M,'normalize',side_effect=AssertionError('IK normalized model')):
     np.testing.assert_allclose(project(spec),expected,atol=1e-12)

 def test_progressive_preview_reuses_authored_sequence_and_matches_export(self):
  import preview_worker as W
  from unittest.mock import patch
  for physics in (False,True):
   p=E.new_project();p.update(seconds=.5,camera_y=3);p['layers']=[E.entry('thrust')]
   if physics:p['physics']={'armR':{'lower':.4}}
   with patch.object(E,'authored',wraps=E.authored) as authored:
    seq,images=W.progressive_preview(p,1,frame=2)
   # One normal authoring pass plus the no-breath reference, shared by physics.
   self.assertEqual(authored.call_count,2)
   exact=E.poses(p)
   for i,q in enumerate(seq):
    for key in (*E.LIMBS,'dy','chest_yaw','pelvis_yaw'):np.testing.assert_allclose(q[key],exact[i][key])
    for v,cam in enumerate(W.VIEWS):np.testing.assert_array_equal(images[v,i],E.rgba(exact[i],p['render'],cam))

 def test_obsolete_preview_cancels_during_authoring_not_after_whole_sequence(self):
  import preview_worker as W
  from unittest.mock import patch
  p=E.new_project();p.update(seconds=5,fps=24);p['layers']=[E.entry('thrust')]
  with patch.object(W,'current',side_effect=[True]*6+[False]*1000),patch.object(W,'frame_images',side_effect=AssertionError('Rendered stale frame')):
   self.assertIsNone(W.progressive_preview(p,7))

 def test_default_jab_has_compact_body_drive_instead_of_a_quarter_turn(self):
  from game_actions import Thrust
  params=Thrust.defaults();guard=[22,-6,55,85]
  drives=[Thrust.from_guard(t,params,guard,'right')[1] for t in np.linspace(0,1,201)]
  chest=[d['chest_yaw'] for d in drives];hips=[d['pelvis_yaw'] for d in drives]
  self.assertLessEqual(max(abs(x) for x in chest),22)
  self.assertLessEqual(max(abs(x) for x in hips),10)
  self.assertLess(max(chest)-min(chest),33)
  arm,drive,_=Thrust.from_guard(params['prepare']+params['release'],params,guard,'right')
  self.assertEqual(arm[2],90);self.assertEqual(arm[3],0);self.assertEqual(drive['chest_yaw'],-22)

 def test_punch_windup_retracts_arm_before_extension_and_recovers_guard(self):
  from game_actions import Thrust,Swing,REST
  for cls in (Thrust,Swing):
   params=cls.defaults();guard=[22,-6,55,85];t=params['prepare']
   arm,drive,_=cls.from_guard(t,params,guard,'right')
   self.assertLess(arm[2],guard[2]-25);self.assertGreater(arm[3],guard[3]+15)
   self.assertGreater(drive['chest_yaw'],9 if cls is Thrust else 25);self.assertGreater(drive['pelvis_yaw'],4 if cls is Thrust else 10)
   # The elbow and fist actually move back in world space, before body drive.
   a=S.geometry({'armR':arm})[2]['armR'];b=S.geometry({'armR':guard})[2]['armR']
   self.assertLess(a[2][2],b[2][2]-2);self.assertLess(a[3][2],b[3][2]-2)
   for phase in (0,1):np.testing.assert_allclose(cls.from_guard(phase,params,guard,'right')[0],guard)
   params['windup']=0;still,drive,_=cls.from_guard(t,params,guard,'right')
   np.testing.assert_allclose(still,guard);self.assertEqual(drive['chest_yaw'],0)
   params['windup']=1;params['prepare']=.4
   np.testing.assert_allclose(cls.from_guard(.4,params,guard,'right')[0],arm)
   p=E.load(E.ROOT/'examples/motions/fusions/CombatStance.json');p.update(playback='once',seconds=2,fps=25)
   before=E.authored(p);entry=E.entry(cls.kind);entry.update(side='left',scope='armL');p['layers']=[entry]
   seq=E.authored(p);i=round(entry['params']['prepare']*(len(seq)-1))
   self.assertLess(seq[i]['armL'][2],before[i]['armL'][2]-25)
   np.testing.assert_allclose([q['armR'] for q in seq],[q['armR'] for q in before])

 def test_waist_twist_returns_to_guard_and_supports_signed_angle_and_mask(self):
  p=E.load(E.ROOT/'examples/motions/fusions/CombatStance.json');p.update(playback='once',fps=21,seconds=2)
  before=E.authored(p);e=E.entry('twist');e['params'].update(angle=80,hips=.5);p['layers']=[e];seq=E.authored(p)
  peak=max(range(len(seq)),key=lambda i:seq[i]['chest_yaw']-before[i]['chest_yaw'])
  self.assertGreater(seq[peak]['chest_yaw']-before[peak]['chest_yaw'],79)
  self.assertGreater(seq[peak]['pelvis_yaw']-before[peak]['pelvis_yaw'],39)
  for i in (0,len(seq)-1):
   for key in ('chest_yaw','pelvis_yaw',*E.LIMBS):np.testing.assert_allclose(seq[i][key],before[i][key],atol=.001)
  e['params']['angle']=-80;other=E.authored(p)
  self.assertLess(other[peak]['chest_yaw']-before[peak]['chest_yaw'],-79)
  e['scope']='arms';masked=E.authored(p)
  np.testing.assert_allclose([q['chest_yaw'] for q in masked],[q['chest_yaw'] for q in before])

 def test_attack_follow_through_has_pelvis_and_chest_and_scales_to_three(self):
  for kind in ('thrust','swing','kick'):
   for style in (('swing','push') if kind=='kick' else (None,)):
    p=E.new_project();p['base']['params']['breath']=0;p.update(playback='once',fps=24,seconds=1.5)
    e=E.entry(kind);self.assertEqual(e['scope'],'all')
    if style:e['style']=style
    p['layers']=[e];e['params']['twist']=0;zero=E.authored(p)
    for key in ('chest_yaw','pelvis_yaw'):np.testing.assert_allclose([q[key] for q in zero],0)
    e['params']['twist']=1;normal=E.authored(p);e['params']['twist']=3;strong=E.authored(p)
    for key in ('chest_yaw','pelvis_yaw'):
     self.assertGreater(max(abs(q[key]) for q in normal),9 if kind=='thrust' else 19)
     np.testing.assert_allclose([q[key] for q in strong],[q[key]*3 for q in normal])
    e['scope']='arms' if kind!='kick' else 'legs';masked=E.authored(p)
    for key in ('chest_yaw','pelvis_yaw'):np.testing.assert_allclose([q[key] for q in masked],0)

 def test_forward_raise_preserves_legacy_side_raise_and_bends_elbows(self):
  from layers import RaiseArms
  e=E.entry('raise');self.assertEqual(e['plane'],'front');e['params'].update(up=80,fold=30,open=8)
  front=E.samples(e,2)[0]
  for key in ('armL','armR'):np.testing.assert_allclose(front[key][2:],[80,30])
  e['params']['fold']=0;e.pop('plane');old=E.samples(e,2)
  e['plane']='side';self.assertEqual(old,E.samples(e,2))
  self.assertEqual(old[0],RaiseArms.at(0,e['params'],0))

 def test_lift_putdown_reverses_endpoints_and_overhead_straightens_arms(self):
  for side in ('left','right','both'):
   e=E.entry('lift');self.assertEqual(e['mode'],'hold');e['side']=side
   up=E.samples(e,41);e['operation']='putdown';down=E.samples(e,41)
   for a,b in zip(up,reversed(down)):
    for key in ('lean','dy',*E.LIMBS):np.testing.assert_allclose(a[key],b[key],atol=1e-10)
   e.update(operation='pickup');e['params'].update(height=180,fold=110)
   q=E.samples(e,2)[-1]
   for key in (('armL','armR') if side=='both' else ('armL',) if side=='left' else ('armR',)):
    self.assertEqual(q[key][2],180);self.assertEqual(q[key][3],0)
    self.assertGreater(S.geometry(q)[2][key][-1][1],S.geometry(q)[2][key][0][1]+10)

 def test_lift_reach_adapts_to_custom_proportions_without_lifting_feet(self):
  for model in (M.normalize(),M.load(E.ROOT/'examples/models/CustomModel.json')):
   p=E.new_project('lift');p.update(model=model,fps=25,seconds=2)
   seq=E.authored(p)
   for q in seq:
    feet=S.ground_y(q,('thighL','shinL','thighR','shinR'))
    self.assertAlmostEqual(S.ground_y(q),feet,places=6)
   contact=seq[round(.4*(len(seq)-1))]
   delta=S.ground_y(contact,('lowerArmL','lowerArmR'))-S.ground_y(contact,('shinL','shinR'))
   self.assertGreaterEqual(delta,0);self.assertLess(delta,.25)

 def test_push_kick_chambers_extends_retracts_and_mirrors(self):
  from game_actions import Kick
  param=Kick.defaults();param['_style']='push';a=param['prepare'];b=a+param['release'];c=b+(1-b)*.5
  poses=[Kick.at(t,param,0) for t in (0,a,b,c,1)]
  np.testing.assert_allclose([q['legR'][3] for q in poses],[0,-135,0,-135,0])
  self.assertEqual(poses[2]['legR'][2],95)
  self.assertEqual(poses[0],poses[-1])
  e=E.entry('kick');legacy=E.samples(e,61);e['style']='swing'
  self.assertEqual(legacy,E.samples(e,61))
  e['style']='push';right=E.samples(e,61);e['side']='left'
  self.assertEqual(E.samples(e,61),[E.mirror_pose(q) for q in right])
  e['side']='both';both=E.samples(e,61)
  for q in both:np.testing.assert_allclose(q['legL'][2:],q['legR'][2:])
  e['alternating']=True;alternating=E.samples(e,61)
  self.assertLess(min(q['legR'][3] for q in alternating[:30]),-120)
  self.assertLess(min(q['legL'][3] for q in alternating[30:]),-120)
  param['reach']=0
  for t in np.linspace(0,1,31):np.testing.assert_allclose(Kick.at(t,param,0)['legR'],[6,-4,0,0])

 def test_push_kick_preserves_airborne_height_and_roundtrips_style(self):
  for blend in ('add','replace','posture'):
   p=E.new_project('jump');p.update(fps=24,seconds=1.5)
   original=E.authored(p);e=E.entry('kick');e.update(style='push',start=.2,end=.75,blend=blend,scope='all');p['layers']=[e]
   seq=E.authored(p)
   for before,after in zip(original,seq):
    if before.get('_ground') is False:
     self.assertIs(after['_ground'],False);self.assertAlmostEqual(after['dy'],before['dy'])
   with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'kick.json';E.save(p,path)
    self.assertEqual(E.load(path)['layers'][0]['style'],'push')

 def test_every_pose_action_preserves_jump_height_and_airborne_contact(self):
  actions=('stand','walk','run','raise','wave','stretch','squat','bow','shake','nod','thrust','swing','kick','hit','fall','getup','roll','climb','turn','pose','twist','lift')
  for base in ('jump','bounce'):
   p=E.new_project(base);p['physics']={};before=E.authored(p);air=[i for i,q in enumerate(before) if q.get('_ground') is False]
   self.assertTrue(air)
   for kind in actions:
    for blend in ('add','replace','posture'):
     entry=E.entry(kind);entry.update(scope='all',blend=blend)
     if kind=='pose':entry.update(pose={'legR':[6,-4,70,-30],'dy':0},ground=True)
     p['layers']=[entry];seq=E.authored(p)
     for i in air:
      self.assertIs(seq[i].get('_ground'),False,(base,kind,blend,i))
      self.assertAlmostEqual(seq[i]['dy'],before[i]['dy'],places=8,msg=str((base,kind,blend,i)))

 def test_run_jump_kick_order_partial_mix_and_physics_preserve_flight(self):
  for mode in ('loop','once'):
   p=E.new_project('run');p.update(playback=mode,seconds=1.5,fps=16)
   jump=E.entry('jump');jump['mix']=.35;p['layers']=[jump]
   before=E.poses(p);air=[i for i,q in enumerate(before) if q.get('_ground') is False];self.assertTrue(air)
   for kind in ('kick','hit','roll','fall','pose'):
    action=E.entry(kind);action.update(blend='replace',scope='all',start=.2,end=.8)
    if kind=='pose':action.update(pose={'dy':0},ground=True)
    for layers in ([jump,action],[action,jump]):
     p['layers']=layers;seq=E.poses(p)
     for i in air:
      self.assertIs(seq[i].get('_ground'),False,(mode,kind,i))
      self.assertAlmostEqual(seq[i]['dy'],before[i]['dy'],places=8,msg=str((mode,kind,i)))
  p=E.new_project('jump');p['layers']=[dict(E.entry('roll'),contact='ground')]
  self.assertTrue(all(q['_ground'] for q in E.authored(p)))
 def test_run_thrust_straightens_despite_default_lower_arm_softness(self):
  p=E.new_project('run');p['layers']=[E.entry('thrust')];seq=E.poses(p);q=seq[4]['armR']
  self.assertGreater(np.dot(S.direction(q[0],q[2]),S.direction(q[0]+q[1],q[2]+q[3])),.999)
 def test_combat_thrust_extends_elbow_and_recovers_guard_in_all_blend_modes(self):
  import rig as R
  p=E.load(E.ROOT/'examples/motions/fusions/CombatStance.json');p.update(playback='once',seconds=1.5,fps=16)
  before=E.authored(p)
  for mode in ('add','replace','posture'):
   for side,arm,other in (('right','armR','armL'),('left','armL','armR')):
    e=E.entry('thrust');e.update(side=side,blend=mode);p['layers']=[e];seq=E.authored(p);peak=9
    q=seq[peak][arm];v1=S.direction(q[0],q[2]);v2=S.direction(q[0]+q[1],q[2]+q[3])
    self.assertGreater(np.dot(v1,v2),.999, (mode,side,q))
    self.assertAlmostEqual(q[2],90,delta=.5)
    for i in (0,len(seq)-1):np.testing.assert_allclose(seq[i][arm],before[i][arm],atol=1e-10)
    np.testing.assert_allclose([q[other] for q in seq],[q[other] for q in before])
    for leg in ('legL','legR'):
     for q,ref in zip(seq,before):np.testing.assert_allclose(R.chain(dict(q,yaw=45,pitch=0),leg)[3],R.chain(dict(ref,yaw=45,pitch=0),leg)[3],atol=.02)
   p['layers']=[]

 def test_context_thrust_respects_interval_mix_side_mask_and_layer_order(self):
  p=E.load(E.ROOT/'examples/motions/fusions/CombatStance.json');p.update(playback='once',seconds=2,fps=24)
  base=E.authored(p);e=E.entry('thrust');e.update(start=.25,end=.75,side='left',scope='armL');p['layers']=[e]
  seq=E.authored(p)
  for i in range(len(seq)):
   np.testing.assert_allclose(seq[i]['armR'],base[i]['armR'])
   if i/(len(seq)-1)<.25 or i/(len(seq)-1)>.75:np.testing.assert_allclose(seq[i]['armL'],base[i]['armL'])
  peak=min(range(len(seq)),key=lambda i:abs(seq[i]['armL'][3]));self.assertLess(abs(seq[peak]['armL'][3]),2)
  e['mix']=0;zero=E.authored(p);np.testing.assert_allclose([q['armL'] for q in zero],[q['armL'] for q in base])
  e['mix']=.5;half=E.authored(p);self.assertAlmostEqual(half[peak]['armL'][3],(base[peak]['armL'][3]+seq[peak]['armL'][3])/2)
  e['mix']=1;pose=E.entry('pose');pose.update(blend='replace',scope='armL',pose={'armL':[-10,0,20,30]});p['layers'].append(pose)
  np.testing.assert_allclose(E.authored(p)[peak]['armL'],[-10,0,20,30])
 def test_idle_breathing_plants_feet_in_all_views_with_custom_proportions(self):
  import rig as R
  for custom in (False,True):
   p=E.new_project();p['base']['params']['breath']=2;p['camera_y']=5
   if custom:
    p['model']=M.normalize();p['model']['legL'].update(upper=4,lower=7);p['model']['legR'].update(upper=4,lower=7)
    p['controls']={'torso':dict(hips_turn=20,turn=-10,height=1,lean=5)}
   reference=copy.deepcopy(p);reference['base']['params']['breath']=0
   rest=E.authored(reference);seq=E.authored(p)
   self.assertGreater(np.ptp([q['dy'] for q in seq]),1.9)
   for q,ref in zip(seq,rest):
    for leg in ('legL','legR'):
     for yaw in (0,45,90,135):
      np.testing.assert_allclose(R.chain(dict(q,yaw=yaw,pitch=0),leg)[3],R.chain(dict(ref,yaw=yaw,pitch=0),leg)[3],atol=.012)
  p=E.new_project();p['base']['params']['breath']=2
  for cam in ((0,0),(45,0),(90,0),(45,30)):
   rows=[]
   for q in E.poses(p):
    a=E.rgba(q,dict(parts=True,textures=False,gaps=False,outline=False),cam)
    mask=(a[:,:,:3]==S.U.COLORS['shinL']).all(2)&(a[:,:,3]>0)
    rows.append(np.where(mask)[0].max())
   self.assertEqual(len(set(rows)),1,cam)

 def test_idle_breathing_with_soft_legs_and_jump_does_not_ground_flight(self):
  import rig as R
  p=E.new_project();p['physics']={'legL':dict(upper=.5,lower=.5),'armR':dict(lower=.5)}
  seq=E.poses(p)
  for q in seq:
   for leg,views in q['_foot_targets'].items():
    for yaw,target in views:np.testing.assert_allclose(R.chain(dict(q,yaw=yaw,pitch=0),leg)[3],target,atol=.012)
  jump=E.entry('jump');p['layers']=[jump];p['physics']={}
  seq=E.authored(p);mid=seq[len(seq)//2]
  self.assertFalse(mid['_ground'])
  self.assertLess(R.chain(dict(mid,yaw=0,pitch=0),'legL')[3][1],R.chain(dict(seq[0],yaw=0,pitch=0),'legL')[3][1]-3)

 def test_pelvis_turn_changes_lower_mesh_and_facing_turns_whole_character(self):
  p=E.new_project();p['base']['params']['breath']=0
  before=E.authored(p)[0];p['controls']={'torso':dict(hips_turn=35,pin_feet=False)};after=E.authored(p)[0]
  self.assertEqual(after['pelvis_yaw'],35);np.testing.assert_allclose(S.geometry(before)[-1][1],S.geometry(after)[-1][1])
  self.assertGreater(np.max(abs(np.array(S.limb_chain(before,'legL'))-S.limb_chain(after,'legL'))),1)
  def mesh(q):return np.concatenate([v for part,f,v,uv in S.pose_meshes(q)[1] if part=='torso'])
  self.assertGreater(np.max(abs(mesh(after)-mesh(before))),.5)
  a=E.rgba(after,p['render']);p['yaw']=17;turned=E.authored(p)[0]
  self.assertFalse(np.array_equal(a,E.rgba(turned,p['render'])))
 def test_camera_y_is_integer_framing_shared_with_handles_and_export(self):
  import rig as R,motion_resources as MR
  from PIL import Image
  p=E.new_project();p['seconds']=.1;normal=E.poses(p)[0];plain=E.rgba(normal,p['render']);j=R.joints(normal)
  cache=E._compiled.cache_info();p['camera_y']=4;shifted=E.poses(p)[0];image=E.rgba(shifted,p['render'])
  self.assertEqual(E._compiled.cache_info().misses,cache.misses)
  np.testing.assert_array_equal(image[4:],plain[:-4]);self.assertFalse(image[:4,:,3].any())
  for key in j:
   for joint in j[key]:np.testing.assert_allclose(R.joints(shifted)[key][joint],np.array(j[key][joint])+[0,4])
  self.assertIs(S.geometry(normal),S.geometry(shifted))
  with tempfile.TemporaryDirectory() as td:
   E.export(p,td,'Framed',['png','recipe'],False)
   np.testing.assert_array_equal(np.array(Image.open(Path(td)/'Framed_00.png')),image)
   self.assertEqual(E.load(Path(td)/'Framed.json')['camera_y'],4)
  self.assertEqual(MR.apply_motion(p,dict(E.new_project('jump'),camera_y=8))['camera_y'],4)
  demo=E.load(E.ROOT/'examples/motions/fusions/RunJumpRoll.json')
  for pose in E.poses(demo):
   v=np.concatenate([v for part,f,v,uv in S.pose_meshes(pose)[1]])
   from core3d import project
   q=project(v,45,0);q[:,1]+=pose['_camera_y']
   self.assertGreater(q[:,1].min(),1);self.assertLess(q[:,1].max(),63)
 def test_end_position_matches_legacy_span_and_aerial_roll_keeps_jump(self):
  old=dict(mode='once',start=.2,span=.55);new=dict(mode='once',start=.2,end=.75)
  for i in range(101):
   self.assertAlmostEqual(E.MT.sample_time(old,i,101),E.MT.sample_time(new,i,101))
   self.assertAlmostEqual(E.MT.layer_weight(old,i,101),E.MT.layer_weight(new,i,101))
  p=E.new_project('run');p.update(playback='once',physics={},controls={});jump=E.entry('jump');p['layers']=[jump];before=E.authored(p)
  roll=E.entry('roll');roll.update(start=.2,end=.75,blend='replace');p['layers'].append(roll);seq=E.authored(p)
  flight=[i for i,q in enumerate(before) if q.get('_ground') is False]
  self.assertTrue(flight)
  for i in flight:
   self.assertFalse(seq[i]['_ground']);self.assertAlmostEqual(seq[i]['dy'],before[i]['dy'])
  self.assertGreater(max(seq[i].get('body_pitch',0) for i in flight),270)
  self.assertGreater(seq[flight[len(flight)//2]]['body_pivot'],0)
  roll['contact']='ground';self.assertTrue(all(q.get('_ground') for i,q in enumerate(E.authored(p)) if i in flight))
 def test_new_layers_default_to_add_and_explicit_posture_still_works(self):
  for kind in ('pose','wave','raise','swing','thrust','kick','hit'):
   self.assertEqual(E.entry(kind)['blend'],'add')
  p=E.new_project('run');p['physics']={};base=E.authored(p);e=E.entry('wave');e.update(side='left',mix=.5);p['layers']=[e]
  seq=E.authored(p);delta=E.samples(e,len(seq),p)
  # Run's saved arm range is applied after layers; check a neutral control set.
  p['controls']={};p['layers']=[];base=E.authored(p);p['layers']=[e];seq=E.authored(p)
  neutral=E.norm(E.F.POSES['stand'])['armL']
  np.testing.assert_allclose([q['armL'] for q in seq],np.array([q['armL'] for q in base])+.5*(np.array([q['armL'] for q in delta])-neutral))

 def test_textures_and_part_colors_are_independent_in_preview_and_export(self):
  import uv_assets as U
  from PIL import Image
  p=E.new_project();p['seconds']=.1;p['assets3d']=S.assets(p)
  resource=p['assets3d']['textures']['head'];resource['png']=U.encode(Image.new('RGBA',resource['layout']['size'],(13,29,47,255)))
  before=copy.deepcopy(p['assets3d']);pose=E.poses(p)[0]
  images={}
  for textures in (True,False):
   for parts in (True,False):images[textures,parts]=E.rgba(pose,dict(textures=textures,parts=parts,outline=False,gaps=False))
  for parts in (True,False):self.assertTrue(np.any(np.all(images[True,parts]==[13,29,47,255],axis=2)))
  self.assertFalse(np.any(np.all(images[False,True]==[13,29,47,255],axis=2)))
  self.assertTrue(np.any(np.all(images[False,True]==[*U.COLORS['head'],255],axis=2)))
  white=images[False,False];self.assertTrue(np.all(white[white[:,:,3]>0,:3]==255))
  np.testing.assert_array_equal(white[:,:,3],images[False,True][:,:,3]);self.assertEqual(p['assets3d'],before)
  painted=E.rgba(pose,dict(textures=True,parts=False,outline=True,gaps=False))
  self.assertTrue(np.any(np.all(painted==[72,72,72,255],axis=2)))
  example=M.load_resource(E.ROOT/'examples/models/CustomModel.json')
  full=E.new_project();full.update(example);full_pose=E.poses(full)[0]
  np.testing.assert_array_equal(E.rgba(full_pose,dict(textures=True,parts=False)),E.rgba(full_pose,dict(textures=True,parts=True)))
  p['render']=dict(textures=False,parts=True,outline=False,gaps=False)
  with tempfile.TemporaryDirectory() as td:
   E.export(p,td,'Colors',['png'],False)
   np.testing.assert_array_equal(np.array(Image.open(Path(td)/'Colors_00.png')),images[False,True])

 def test_one_shot_physics_follows_rotating_parent_without_loop_warmup(self):
  p=E.new_project('fall');p['playback']='once';p['physics']={'armR':{'upper':.9,'lower':.8,'bounce':.6},'head':{'strength':.8}}
  base=E.authored(p);seq=E.physical(base,p)
  self.assertGreater(np.max(np.abs(np.array([q['armR'] for q in seq])-np.array([q['armR'] for q in base]))),10)
  self.assertGreater(max(abs(q['head_pitch']-b['head_pitch']) for q,b in zip(seq,base)),5)
  self.assertTrue(all(np.isfinite(q['armR']).all() for q in seq))
  np.testing.assert_allclose([q['armL'] for q in seq],[q['armL'] for q in base])
  again=E.physical(E.authored(p),p)
  np.testing.assert_allclose([q['armR'] for q in seq],[q['armR'] for q in again])
 def test_fast_ground_contact_matches_shaped_mesh_and_root_rotations(self):
  for shape in M.SHAPES['torso']:
   model=M.normalize();model['torso'].update(shape=shape,front_mid=1.,curve=.7,bulge_length=2.);model['head'].update(bulge_length=3.)
   model['armL'].update(curve=-1.,top_width=1.3)
   for angle in (0,47,90,180,270):
    p=E.norm(E.F.POSES['stand']);p.update(_model=model,body_pitch=angle,body_axis=60,body_pivot=9,rot=12,chest_yaw=-20,pelvis_yaw=18,lean=12,dy=2,dz=3)
    expected=min(v[:,1].min() for part,face,v,uv in S.pose_meshes(p)[1])
    self.assertAlmostEqual(S.ground_y(p),expected,places=6)
 def test_game_actions_land_and_roll_returns_upright_in_every_direction(self):
  for kind in ('jump','thrust','swing','kick','hit','fall','getup','roll','climb','turn'):
   p=E.new_project(kind);seq=E.authored(p)
   self.assertTrue(all(np.isfinite(v).all() for q in seq for k,v in q.items() if isinstance(v,(list,int,float))))
   self.assertTrue(any(not np.allclose(seq[0].get(k,0),q.get(k,0)) for q in seq[1:] for k in E.POSE_CHANNELS),kind)
   for q in seq[::5]:
    if q.get('_ground'):
     bottom=min(v[:,1].min() for part,face,v,uv in S.pose_meshes(q)[1])
     self.assertAlmostEqual(bottom,E._ground_level(json.dumps(M.normalize(),sort_keys=True)),places=6)
  for angle in (-135,-45,0,60,120,180):
   p=E.new_project('roll');p['base']['params']['direction']=angle
   q=E.authored(p)[-1];np.testing.assert_allclose(S.root_rotation(q),np.eye(3),atol=1e-10)
  jump=E.authored(E.new_project('jump'))
  self.assertFalse(jump[len(jump)//2]['_ground']);self.assertTrue(jump[-1]['_ground'])
  fall=E.authored(E.new_project('fall'));up=E.authored(E.new_project('getup'))
  self.assertAlmostEqual(fall[-1]['body_pitch'],90);self.assertAlmostEqual(up[-1]['body_pitch'],0)

 def test_timed_attack_and_pose_mask_preserve_unaffected_motion(self):
  p=E.new_project('run');p['physics']={};base=E.authored(p)
  layer=E.entry('swing');layer.update(scope='armL',side='left',start=.25,span=.5,fade=.1);p['layers']=[layer]
  seq=E.authored(p)
  for k in ('legL','legR','armR'):
   np.testing.assert_allclose([q[k] for q in seq],[q[k] for q in base])
  for i in (0,1,len(seq)-2,len(seq)-1):np.testing.assert_allclose(seq[i]['armL'],base[i]['armL'])
  self.assertFalse(np.allclose(seq[len(seq)//2]['armL'],base[len(seq)//2]['armL']))
  layer=E.entry('pose');layer.update(scope='arms',pose={'armR':[70,-6,0,0]},retain=.5,blend='posture');p['layers']=[layer]
  seq=E.authored(p)
  np.testing.assert_allclose([q['legL'] for q in seq],[q['legL'] for q in base])
  np.testing.assert_allclose(np.std([q['armR'] for q in seq],axis=0),np.std([q['armR'] for q in base],axis=0)*.5,atol=1e-10)

 def test_portable_library_and_motion_import_keep_current_appearance(self):
  import motion_resources as MR
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'Pose.json';MR.save_pose({**E.norm(E.F.POSES['stand']),'_assets3d':{'secret':'none'},'_model':M.normalize()},path)
   pose=MR.load_pose(path);self.assertNotIn('_model',pose);self.assertNotIn('_assets3d',pose)
  current=E.new_project();current.update(model=M.normalize(),assets3d={'marker':True},render={'parts':False})
  result=MR.apply_motion(current,E.new_project('jump'))
  for k in ('model','assets3d','render'):self.assertEqual(result[k],current[k])
  self.assertEqual(result['base']['kind'],'jump');self.assertEqual(result['playback'],'once')
  for relative in MR.BUILTIN_MOTIONS:
   file=E.ROOT/'examples'/'motions'/relative
   p=E.load(file);self.assertFalse({'model','assets3d'}&set(p));self.assertTrue(E.authored(p),str(file))

 def test_tapered_cylinder_and_muzzle_are_geometry_and_portable_parameters(self):
  def vertices(model):return np.concatenate([v for part,face,v,uv in S.pose_meshes({'_model':model})[1] if part=='head'])
  model=M.normalize();model['head']['shape']='cylinder';old=vertices(model)
  model['head'].update(top_width=1.5,bottom_width=.5,bulge_length=4.)
  new=vertices(model);top=old[:,1]>np.max(old[:,1])-1;bottom=old[:,1]<np.min(old[:,1])+1
  self.assertGreater(np.ptp(new[top,0]),np.ptp(old[top,0]));self.assertLess(np.ptp(new[bottom,0]),np.ptp(old[bottom,0]))
  self.assertGreater(np.max(new[:,2]),np.max(old[:,2])+1)
  p={'model':model};bundle=S.assets(p)
  import uv_assets as U
  self.assertEqual(U.surface_record(bundle,'head')['geometry']['bulge_length'],4.)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'model.json';M.save(model,path,assets=bundle);self.assertEqual(M.load_resource(path)['model'],M.normalize(model))

 def test_nonloop_timing_and_physics_do_not_wrap_end_to_start(self):
  entry=E.entry('wave');entry['mode']='once'
  self.assertEqual(E.MT.sample_time(entry,11,12),1.)
  self.assertEqual(E.MT.preview_frame(3,12,12,{'playback':'hold'}),(11,True))
  entry.update(start=.25,span=.5)
  self.assertEqual(E.MT.layer_weight(entry,0,101),0.)
  self.assertEqual(E.MT.layer_weight(entry,100,101),0.)
  entry['mode']='hold';self.assertEqual(E.MT.layer_weight(entry,100,101),1.)
  roots=np.zeros((24,2));target=np.zeros(24);target[18:]=40
  result=E._spring_track(target,roots,6,1,.7,.3,False)
  np.testing.assert_allclose(result[:18],0.)
  p=E.new_project('wave');p['playback']='once';p['seconds']=.25
  with tempfile.TemporaryDirectory() as td:
   E.export(p,td,'Once',formats=['gif'],create_folder=False)
   from PIL import Image
   with Image.open(Path(td)/'Once.gif') as im:self.assertNotIn('loop',im.info)

 def test_waving_left_is_a_real_mirror_and_preserves_other_arm(self):
  p=E.new_project('run');p['physics']={};original=E.authored(p)
  layer=E.entry('wave');layer.update(scope='armL',retain=.4,mix=.7);p['layers']=[layer]
  seq=E.authored(p)
  self.assertGreater(np.max(np.abs(np.array([q['armL'] for q in seq])-np.array([q['armL'] for q in original]))),20)
  np.testing.assert_allclose([q['armR'] for q in seq],[q['armR'] for q in original])
  right=E.samples(E.entry('wave'),24);left=E.samples({**E.entry('wave'),'side':'left'},24)
  np.testing.assert_allclose([q['armL'] for q in left],np.array([q['armR'] for q in right])*[-1,-1,1,1])
  both=E.samples({**E.entry('wave'),'side':'both','alternating':True},24)
  self.assertTrue(all('armL' in q and 'armR' in q for q in both))
  self.assertFalse(np.allclose([q['armL'][1] for q in both],[-q['armR'][1] for q in both]))

if __name__=='__main__':unittest.main()
