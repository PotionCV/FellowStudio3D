import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import engine as E,rounded_scene as S,uv_assets as U
ROOT=Path(__file__).resolve().parent
class Studio3DTests(unittest.TestCase):
 def test_default_names_are_english_and_legacy_auto_names_migrate(self):
  import i18n
  original=i18n.language
  try:
   for language in ('en','zh','ja'):
    i18n.set_language(language)
    self.assertEqual(E.new_project()['name'],'Idle')
    self.assertEqual(E.new_project('walk')['name'],'Walk')
    self.assertEqual(E.new_project('run')['name'],'Run')
   for name in ('站姿','待機','Idle'):
    p=E.new_project();p.update(name=name,auto_name_key='站姿')
    self.assertEqual(E.normalize_project_name(p)['name'],'Idle')
   p=E.new_project();p.update(name='我的角色',auto_name_key='站姿')
   self.assertEqual(E.normalize_project_name(p)['name'],'我的角色')
  finally:i18n.set_language(original)

 def test_torso_thickness_changes_depth_and_uv_without_widening_front(self):
  import model_data as M
  legacy=M.normalize({'torso':{}});self.assertEqual(legacy['torso']['thickness'],1.)
  self.assertEqual(M.normalize()['torso']['thickness'],1.15)
  for shape in M.SHAPES['torso']:
   thin=copy.deepcopy(legacy);thin['torso']['shape']=shape
   thick=copy.deepcopy(thin);thick['torso']['thickness']=1.5
   vertices=[]
   for model in (thin,thick):
    _,mesh,_=S.pose_meshes({'_model':model})
    vertices.append(np.concatenate([v for p,face,v,uv in mesh if p=='torso']))
   np.testing.assert_allclose(vertices[0][:,:2],vertices[1][:,:2])
   np.testing.assert_allclose(vertices[0][:,2]*1.5,vertices[1][:,2])
   self.assertEqual(S.part_dimensions(thick)['torso'][2],10.5)
   before=S.assets({'model':thin});after=S.assets({'model':thick})
   self.assertNotEqual(before['textures']['torso']['layout'],after['textures']['torso']['layout'])
   record=U.surface_record(before,'torso');self.assertNotIn('thickness',record['geometry'])
   self.assertEqual(U.surface_record(after,'torso')['geometry']['thickness'],1.5)

 def test_head_can_hold_facing_while_chest_turns(self):
  pose=E.norm({'chest_yaw':35.,'head_yaw':10.})
  follow=S.geometry(pose)[-1][1]@np.array((0.,0.,1.))
  fixed=S.geometry(dict(pose,head_follow_chest=False))[-1][1]@np.array((0.,0.,1.))
  np.testing.assert_allclose(follow,S.ry(45)@np.array((0.,0.,1.)),atol=1e-7)
  np.testing.assert_allclose(fixed,S.ry(10)@np.array((0.,0.,1.)),atol=1e-7)
  p=E.new_project('walk');p['controls']={'head':{'follow_chest':False}}
  self.assertTrue(all(pose['head_follow_chest'] is False for pose in E.authored(p)))
 def test_outline_is_always_one_native_pixel_and_uses_custom_color(self):
  pose=E.poses(E.new_project())[0];settings=dict(parts=False,gaps=False,outline=False,perfect=False)
  mask=E.rgba(pose,settings)[:,:,3]>0
  settings.update(outline=True,outline_color='#24586c');image=E.rgba(pose,settings)
  edges=(np.roll(mask,1,0)|np.roll(mask,-1,0)|np.roll(mask,1,1)|np.roll(mask,-1,1))&~mask
  np.testing.assert_array_equal(np.all(image==[36,88,108,255],axis=2)&~mask,edges)
  np.testing.assert_array_equal(image,E.rgba(pose,{**settings,'perfect':True}))
  p=E.new_project();p['seconds']=.1;p['render']=settings
  with tempfile.TemporaryDirectory() as td:
   for scale in (4,8):
    dest=E.export(p,td,f'Color{scale}',formats=['png'],create_folder=False,scale=scale)
    np.testing.assert_array_equal(np.array(Image.open(dest/f'Color{scale}_00.png')),image.repeat(scale,0).repeat(scale,1))
 def test_paired_limbs_share_png_and_render_as_mirrors(self):
  from core3d import raster
  import model_data as M
  pose=E.norm({});pose.update(armL=[-25,30,20,10],armR=[25,-30,20,10],legL=[-10,10,-20,15],legR=[10,-10,-20,15])
  for shape in ('capsule','cylinder','box'):
   pose['_model']=M.normalize()
   for key in E.LIMBS:pose['_model'][key]['shape']=shape
   _,triangles,bundle=S.pose_meshes(pose)
   for first,second in (('upperArmL','upperArmR'),('lowerArmL','lowerArmR'),('thighL','thighR'),('shinL','shinR')):
    self.assertEqual(bundle['textures'][first]['layout'],bundle['textures'][second]['layout'])
    w,h=bundle['textures'][first]['layout']['size'];yy,xx=np.indices((h,w));tex=np.zeros((h,w,4),np.uint8);tex[:,:,0]=xx*7;tex[:,:,1]=yy*9;tex[:,:,2]=(xx+yy)*3;tex[:,:,3]=255
    settings=dict(colors=True,gaps=False,outline=False,onepx=True)
    for yaw in (0,25,60):
     left,_=raster([t for t in triangles if t[0]==first],{first:tex},(yaw,0),settings)
     right,_=raster([t for t in triangles if t[0]==second],{second:tex},(-yaw,0),settings)
     np.testing.assert_array_equal(left[:,::-1],right,err_msg=f'{shape} / {first} / {yaw}')
 def cross_face_project(self):
  import model_data as M
  p=E.new_project();p['model']=M.normalize();p['model']['head']['shape']='box'
  p['assets3d']=S.assets(p);r=p['assets3d']['textures']['head'];im=U.texture_image(p['assets3d'],'head');im.paste((180,130,100,255),(0,0,*im.size))
  pixels=[]
  for face in ('front','right'):
   x,y,w,h=r['layout']['rects'][face]
   for py in range(y+h//2-1,y+h//2+2):
    px=x+w-1 if face=='front' else x
    pixels.append([px,py]);im.putpixel((px,py),(255 if face=='front' else 0,255 if face=='right' else 0,30,255))
  r['png']=U.encode(im);r['protected_groups']=[dict(faces=['front','right'],pixels=pixels,angle=25.)]
  return p
 def test_copied_protection_groups_keep_pair_mirroring(self):
  from core3d import raster
  pose=E.norm({});pose.update(armL=[-20,0,10,0],armR=[20,0,10,0])
  _,triangles,bundle=S.pose_meshes(pose);textures={}
  for part in ('upperArmL','upperArmR'):
   resource=bundle['textures'][part];x,y,w,h=resource['layout']['rects']['front']
   image=U.texture_image(bundle,part);image.paste((180,130,100,255),(0,0,*image.size))
   pixels=[[x+w//2-1,y+h//2],[x+w//2,y+h//2],[x+w//2,y+h//2+1]]
   for pixel in pixels:image.putpixel(tuple(pixel),(9,200,101,255))
   resource['protected_groups']=[dict(face='front',pixels=pixels)];textures[part]=np.array(image)
  pose['_assets3d']=bundle;context=S.protection_context(pose,bundle);settings=dict(colors=True,gaps=False,outline=False,onepx=True)
  for yaw in (0,20):
   frames=[]
   for part,angle in (('upperArmL',yaw),('upperArmR',-yaw)):
    image,_=raster([t for t in triangles if t[0]==part],{part:textures[part]},(angle,0),settings,protection=bundle['textures'],protection_context={part:context[part]});frames.append(image)
   np.testing.assert_array_equal(frames[0][:,::-1],frames[1])
 def test_cross_face_group_has_one_stable_reference_and_angle_release(self):
  from pixel_protection import valid_groups
  p=self.cross_face_project();pose=E.poses(p)[0];groups=valid_groups(p['assets3d']['textures']['head'])
  self.assertEqual(groups[0]['faces'],['front','right']);self.assertEqual(len(groups[0]['pixels']),6)
  refs=S.protection_context(pose,pose['_assets3d'])['head']['references'];self.assertEqual(len(refs),1)
  reference=refs[0];self.assertIsNotNone(reference);self.assertEqual(len(set(map(tuple,reference['offsets']))),6)
  first=None
  for yaw in (-48,-45,-42):
   a=E.rgba(dict(pose,yaw=yaw),dict(parts=True,gaps=False,outline=False))
   red=np.argwhere(np.all(a==[255,0,30,255],axis=2));green=np.argwhere(np.all(a==[0,255,30,255],axis=2))
   self.assertEqual(len(red),3);self.assertEqual(len(green),3)
   relative=np.vstack((red,green))-red[0]
   if first is None:first=relative
   else:np.testing.assert_array_equal(relative,first)
  plain=copy.deepcopy(pose);plain['_assets3d']['textures']['head']['protected_groups']=[]
  for yaw,roll in ((30,0),(-45,70)):
   np.testing.assert_array_equal(E.rgba(dict(pose,yaw=yaw,head=roll)),E.rgba(dict(plain,yaw=yaw,head=roll)))
  with tempfile.TemporaryDirectory() as td:
   U.export_pack(p['assets3d'],td);other=copy.deepcopy(p['assets3d']);other['textures']['head']['protected_groups']=[];U.import_pack(other,td)
   self.assertEqual(other['textures']['head']['protected_groups'],groups)
  p['model']['head']['size']=1.2;resized=S.assets(p)['textures']['head'];self.assertEqual(len(resized['protected_groups']),1);self.assertEqual(resized['protected_groups'][0]['faces'],['front','right']);self.assertEqual(resized['protected_groups'][0]['angle'],25.)
  for shape in ('ellipsoid','cylinder','rounded_box'):
   p=self.cross_face_project();p['model']['head']['shape']=shape;pose=E.poses(p)[0]
   for yaw in (-48,-45,-42):
    a=E.rgba(dict(pose,yaw=yaw),dict(parts=True,gaps=False,outline=False))
    self.assertEqual(np.all(a==[255,0,30,255],axis=2).sum(),3,shape)
    self.assertEqual(np.all(a==[0,255,30,255],axis=2).sum(),3,shape)
 def test_shape_choices_change_geometry_and_preserve_model_presets(self):
  import model_data as M
  p=E.new_project();p['model']=M.normalize();seen=[]
  for shape in M.SHAPES['head']:
   p['model']['head']['shape']=shape
   frames=[E.rgba(E.poses(p)[0],p['render'],cam) for cam in ((0,0),(45,30),(90,0))]
   seen.append(b''.join(a.tobytes() for a in frames))
  self.assertEqual(len(set(seen)),len(M.SHAPES['head']))
  for part in ('torso','armR','legL'):
   results=[]
   for shape in M.SHAPES[part]:
    p['model'][part]['shape']=shape;results.append(E.rgba(E.poses(p)[0],p['render'],(45,30)).tobytes())
   self.assertEqual(len(set(results)),len(M.SHAPES[part]),part)
  with tempfile.TemporaryDirectory() as td:
   M.save(p['model'],Path(td)/'model.json');self.assertEqual(M.load(Path(td)/'model.json'),p['model'])
  with self.assertRaises(ValueError):M.normalize({'head':{'shape':'unknown'}})
 def test_pelvis_fills_center_between_leg_roots(self):
  import model_data as M
  p=E.new_project();p['model']=M.normalize();p['model']['torso']['pelvis_depth']=0
  plain=E.rgba(E.poses(p)[0],dict(parts=False,gaps=False,outline=False))
  p['model']['torso']['pelvis_depth']=3
  filled=E.rgba(E.poses(p)[0],dict(parts=False,gaps=False,outline=False))
  self.assertTrue(np.any((filled[:,30:34,3]>0)&(plain[:,30:34,3]==0)))
 def test_negative_model_offsets_move_inward_and_overlap(self):
  import model_data as M
  m=M.normalize({key:{'spread':-2.,'gap':-3.,'vertical':-1.} for key in E.LIMBS})
  pose=E.norm(E.F.POSES['stand']);base=S.geometry(pose);g,j,chains,*_=S.geometry(dict(pose,_model=m))
  for side in ('L','R'):
   for kind in ('arm','leg'):
    key=kind+side;root=chains[key][0];original=base[2][key][0]
    self.assertLess(abs(root[0]),abs(original[0]))
    self.assertEqual(m[key]['gap'],-3.)
    direction=S.direction(*((pose[key][0],pose[key][2])))
    self.assertLess(np.dot(chains[key][1]-root,direction),0)
  with tempfile.TemporaryDirectory() as td:
   M.save(m,Path(td)/'offsets.json');self.assertEqual(M.load(Path(td)/'offsets.json'),m)
 def test_original_defaults_and_motion_composition_are_preserved(self):
  reference=json.loads((ROOT/'fixtures'/'motion_reference.json').read_text(encoding='utf-8'))
  for kind,ref in reference.items():
   # Historical recipes remain a fixed oracle even when published defaults
   # are retuned. Compare the composition engine against their original poses.
   p=copy.deepcopy(ref['project'])
   self.assertEqual(p['base']['kind'],kind)
   # New 3D yaw/depth channels extend the original recipes; existing limb,
   # timing, layer-mixing and body-height channels must stay unchanged.
   excluded={'head_yaw','head_depth','head_follow_chest','chest_yaw','pelvis_yaw'}
   # Idle breathing now plants feet instead of lifting the whole character.
   # Its new root/leg behavior is covered by the foot-contact regressions.
   if kind=='stand':excluded.update(('dy','legL','legR','_foot_targets','_breath_ik','_breath_dy'))
   if kind=='bounce':excluded.add('_ground')
   original=[{k:v for k,v in pose.items() if k not in excluded} for pose in E.authored(p)]
   expected=[{k:v for k,v in pose.items() if k not in excluded} for pose in ref['poses']]
   self.assertEqual(original,expected)
 def test_head_depth_and_yaw_controls_are_independent(self):
  import model_data as M
  pose=E.norm({});pose['_model']=M.normalize();g0=S.geometry(pose)
  moved=copy.deepcopy(pose);moved['_model']['head']['depth']=-3.;moved['head_depth']=1.;moved['head_yaw']=40.
  g1=S.geometry(moved);np.testing.assert_allclose(g1[-1][0]-g0[-1][0],(0,0,-2),atol=1e-7)
  for limb in E.LIMBS:np.testing.assert_allclose(g1[1][limb]['tip'],g0[1][limb]['tip'])
  front=g1[-1][1]@np.array((0,0,1));self.assertGreater(front[0],.5)
  p=E.new_project();p['controls']={'head':dict(depth=-2.,turn=35.)};seq=E.authored(p)
  self.assertEqual(seq[0]['head_depth'],-2.);self.assertEqual(seq[0]['head_yaw'],35.)
  with tempfile.TemporaryDirectory() as td:
   M.save(moved['_model'],Path(td)/'depth.json');self.assertEqual(M.load(Path(td)/'depth.json')['head']['depth'],-3.)
 def test_gait_twists_chest_and_pelvis_in_opposition(self):
  for kind in ('walk','run'):
   p=E.new_project(kind);p['controls']={};p['physics']={};seq=E.authored(p)
   chest=np.array([pose['chest_yaw'] for pose in seq]);hips=np.array([pose['pelvis_yaw'] for pose in seq])
   self.assertGreater(np.ptp(chest),8.);self.assertTrue(np.all(chest*hips<=1e-8))
   pose=max(seq,key=lambda pose:pose['pelvis_yaw']);j=S.geometry(pose)[1]
   self.assertGreater(j['legL']['root'][2],j['legR']['root'][2]);self.assertLess(j['armL']['root'][2],j['armR']['root'][2])
   p['base']['params']['twist']=0.;flat=E.authored(p)
   self.assertTrue(all(pose['chest_yaw']==0 and pose['pelvis_yaw']==0 for pose in flat))
   for original,straight in zip(seq,flat):
    for limb in E.LIMBS:self.assertEqual(original[limb],straight[limb])
 def test_single_face_groups_use_their_uv_anchor_not_selection_centroid(self):
  import model_data as M
  p=E.new_project();p['model']=M.normalize();p['model']['torso'].update(shoulder=1.6,waist=1.5,hip=1.5);p['model']['head'].update(size=.8,shape='cylinder')
  p['assets3d']=S.assets(p)
  for part,color in (('torso',(0,255,50,255)),('head',(250,10,100,255))):
   r=p['assets3d']['textures'][part];x,y,w,h=r['layout']['rects']['front'];image=U.texture_image(p['assets3d'],part);image.paste((180,130,100,255),(0,0,*image.size))
   if part=='torso':
    center=x+(w-1)/2;pixels=[]
    for row,width in enumerate((2,4,6,8,6,4)):
     pixels.extend([[px,y+4+row] for px in range(round(center-(width-1)/2),round(center+(width-1)/2)+1)])
   else:pixels=[[x+w//2,y+h//2]]
   for pixel in pixels:image.putpixel(tuple(pixel),color)
   r['png']=U.encode(image);r['protected_groups']=[dict(face='front',pixels=pixels)]
  a=E.rgba(E.poses(p)[0],dict(parts=True,gaps=False,outline=False))
  gem=np.argwhere(np.all(a==[0,255,50,255],axis=2));mouth=np.argwhere(np.all(a==[250,10,100,255],axis=2))
  self.assertTrue(len(gem));self.assertEqual(int(gem[:,1].min()+gem[:,1].max()),63)
  self.assertEqual(len(mouth),1);self.assertEqual(mouth[0,1],31)
 def test_new_body_controls_preserve_foot_lock_uv_and_export(self):
  p=E.new_project();p['pose']=E.norm({'legL':[0,0,25,-50],'legR':[0,0,25,-50]});p['seconds']=.2;p['controls']={};p['physics']={}
  before=E.authored(p)[0];p['controls']={'torso':{'hips_turn':15,'pin_feet':True}};after=E.authored(p)[0]
  for key in ('legL','legR'):self.assertLess(np.linalg.norm(S.geometry(before)[1][key]['tip']-S.geometry(after)[1][key]['tip']),.1)
  p=E.new_project('walk');p['seconds']=.25;p['controls']={'head':dict(turn=25,depth=-2),'torso':dict(turn=5,hips_turn=10,pin_feet=False)};p['assets3d']=S.assets(p)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);U.export_pack(p['assets3d'],root/'uv');p['assets3d']['model']['head']['depth']=-2;U.import_pack(p['assets3d'],root/'uv')
   p['export_view']={'yaw':45,'pitch':0};pose=E.poses(p)[1];expected=E.rgba(pose,p['render'],(45,0))
   self.assertNotEqual(pose['pelvis_yaw'],0)
   for scale in (1,3):
    dest=E.export(p,root,f'Body{scale}',formats=['png','recipe'],create_folder=False,scale=scale)
    np.testing.assert_array_equal(np.array(Image.open(dest/f'Body{scale}_01.png')),expected.repeat(scale,0).repeat(scale,1))
    self.assertEqual(E.load(dest/f'Body{scale}.json')['controls'],p['controls'])
 def test_yaw_changes_no_world_height_and_ik_matches_renderer(self):
  p=E.norm(E.F.POSES['stand']);p.update(lean=20,armL=[0,0,35,0],armR=[0,0,-35,0])
  reference=E.R.joints(p)
  for yaw in (0,45,90,135,180):
   q=dict(p,yaw=yaw);j=E.R.joints(q);self.assertAlmostEqual(j['armL']['root'][1],j['armR']['root'][1])
   for key in E.LIMBS:self.assertAlmostEqual(j[key]['tip'][1],reference[key]['tip'][1])
  q=dict(p,yaw=45);target=np.array(E.R.joints(q)['armR']['tip'])+np.array((1.,-1.));solution=E.R.ik(q,'armR',target);np.testing.assert_allclose(E.R.chain(q,'armR',solution)[3],target,atol=.12)
 def test_head_is_round_and_limbs_have_caps(self):
  mesh=S.head_mesh(1.);points=np.concatenate([tri for face,tri,uv in mesh]);radii=np.array((8,7.5,7.5));np.testing.assert_allclose(np.linalg.norm(points/radii,axis=1),1)
  cap,bounds=S.capsule(5.8,2.9,2.55);vertices=np.concatenate([tri for face,tri in cap]);self.assertGreater(vertices[:,1].max(),2.5);self.assertLess(vertices[:,1].min(),-8)
 def test_uv_roundtrip_with_original_model(self):
  p=E.new_project('walk');bundle=S.assets(p)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);U.export_pack(bundle,root);im=U.texture_image(bundle,'head');x,y,w,h=bundle['textures']['head']['layout']['rects']['front'];im.paste((255,0,0,255),(x,y,x+w,y+h));im.save(root/'head.png');U.import_pack(bundle,root);p['assets3d']=bundle
   E.save(p,root/'project.json');q=E.load(root/'project.json');self.assertEqual(q,p);pose=E.poses(q)[0];a=E.rgba(pose,p['render']);self.assertTrue(np.any(np.all(a==[255,0,0,255],axis=2)))
   q['model']={'head':{'size':1.3}};resized=S.assets(q);self.assertNotEqual(resized['textures']['head']['layout']['rects'],bundle['textures']['head']['layout']['rects'])
 def test_export_uses_3d_preview_and_names(self):
  p=E.new_project('walk');p['seconds']=.2;p['assets3d']=S.assets(p);p['export_view']={'yaw':45,'pitch':0}
  with tempfile.TemporaryDirectory() as td:
   dest=E.export(p,td,name='Walk',formats=['png','recipe'],create_folder=False);np.testing.assert_array_equal(np.array(Image.open(dest/'Walk_00.png')),E.rgba(E.poses(p)[0],p['render'],(45,0)));self.assertIn('assets3d',E.load(dest/'Walk.json'))
 def test_batch_raster_preserves_pixels_and_alpha(self):
  from core3d import raster,raster_reference
  p=E.new_project();pose=E.poses(p)[0];j,triangles,bundle=S.pose_meshes(pose);textures={part:np.array(U.texture_image(bundle,part)) for part in U.PARTS}
  textures['head'][::3,::3,3]=0
  for cam in ((0,0),(45,0),(90,0),(45,30)):
   for colors in (False,True):
    settings=dict(colors=colors,outline=True,gaps=True,onepx=True)
    fast,owner=raster(triangles,textures,cam,settings);reference,refowner=raster_reference(triangles,textures,cam,settings)
    np.testing.assert_array_equal(fast,reference);np.testing.assert_array_equal(owner,refowner)
 def test_elbow_separation_exemption_is_pair_and_joint_specific(self):
  from core3d import finish_raster,unproject
  owner=np.full((64,64),-1,np.int16);depth=np.full((64,64),-np.inf);rgb=np.zeros((64,64,4),np.uint8)
  upper=U.PARTS.index('upperArmL');lower=U.PARTS.index('lowerArmL');owner[20:42,20:32]=upper;owner[20:42,32:44]=lower;depth[20:42,20:32]=1;depth[20:42,32:44]=2;rgb[owner>=0]=255
  settings=dict(colors=False,outline=True,gaps=True,onepx=True);point=unproject((32,31,2),0,0)
  before,_=finish_raster(rgb.copy(),owner.copy(),depth,(0,0),settings)
  after,_=finish_raster(rgb.copy(),owner.copy(),depth,(0,0),settings,connections=[(upper,lower,point,4)])
  self.assertEqual(tuple(before[31,32]),(128,128,128,255));self.assertEqual(tuple(after[31,32]),(255,255,255,255))
  self.assertEqual(tuple(after[21,32]),(128,128,128,255))
  torso=U.PARTS.index('torso');owner[20:42,20:32]=torso
  other,_=finish_raster(rgb.copy(),owner,depth,(0,0),settings,connections=[(upper,lower,point,4)])
  self.assertEqual(tuple(other[31,32]),(128,128,128,255))
 def test_occlusion_outline_works_without_gaps_in_all_four_directions(self):
  from core3d import finish_raster,unproject
  torso=U.PARTS.index('torso');upper=U.PARTS.index('upperArmL');forearm=U.PARTS.index('lowerArmL')
  owner=np.full((64,64),-1,np.int16);depth=np.full((64,64),-np.inf);rgb=np.zeros((64,64,4),np.uint8)
  owner[16:48,16:48]=torso;depth[16:48,16:48]=0;owner[25:35,25:35]=forearm;depth[25:35,25:35]=2;rgb[owner>=0]=255
  settings=dict(colors=False,outline=True,gaps=False,onepx=True,outline_color='#202020');near=unproject((30,25,2),0,0)
  image,_=finish_raster(rgb.copy(),owner,depth,(0,0),settings,selected=[near],connections=[(upper,forearm,near,4)])
  for y,x in ((25,30),(34,30),(30,25),(30,34)):self.assertEqual(tuple(image[y,x]),(32,32,32,255))
  self.assertEqual(tuple(image[30,30]),(255,255,255,255))
  # Only the actual shoulder pair is continuous in its socket disk.
  owner[25:35,25:35]=upper;image,_=finish_raster(rgb.copy(),owner,depth,(0,0),settings,connections=[(torso,upper,near,2.2)])
  self.assertEqual(tuple(image[25,30]),(255,255,255,255));self.assertEqual(tuple(image[34,30]),(32,32,32,255))
  # Gaps without outlines stay transparent, with both switches off no marks.
  image,_=finish_raster(rgb.copy(),owner,depth,(0,0),{**settings,'outline':False,'gaps':True})
  self.assertEqual(tuple(image[34,30]),(0,0,0,0))
  image,_=finish_raster(rgb.copy(),owner,depth,(0,0),{**settings,'outline':False})
  self.assertEqual(tuple(image[34,30]),(255,255,255,255))
 def test_surface_intersections_have_no_line_and_occlusions_keep_depth_order(self):
  from core3d import raster,unproject
  settings=dict(colors=True,outline=True,gaps=False,onepx=True,outline_color='#202020')
  torso='torso';arm='upperArmR';textures={torso:np.array([[[210,90,70,255]]],np.uint8),arm:np.array([[[80,140,210,255]]],np.uint8)}
  def quad(part,bounds,z):
   x0,y0,x1,y1=bounds;points=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
   world=np.array([unproject((x,y,z(x,y)),0,0) for x,y in points])
   return [(part,'front',world[list(indices)],np.zeros((3,2))) for indices in ((0,1,2),(0,2,3))]
  def draw(triangles):return raster(triangles,textures,(0,0),settings)
  # Both solids continue across the boundary and exchange depth: a join,
  # not an occluding silhouette. No internal line in either front order.
  for sign in (-1,1):
   triangles=quad(torso,(16,16,48,48),lambda x,y:0)+quad(arm,(16,16,48,48),lambda x,y:sign*(x-31.4))
   image,owner=draw(triangles)
   self.assertFalse(np.any(np.all(image[20:44,20:44,:3]==32,axis=2)))
   self.assertNotEqual(owner[30,30],owner[30,33])
  # Steep depth slopes used to place the line on the background, because
  # neighboring depths were compared instead of depths at the same pixel.
  for front,back in ((arm,torso),(torso,arm)):
   triangles=quad(back,(16,16,48,48),lambda x,y:3*x)+quad(front,(25,25,35,35),lambda x,y:3*x+6)
   image,owner=draw(triangles);plain,plain_owner=raster(triangles,textures,(0,0),{**settings,'outline':False})
   np.testing.assert_array_equal(owner,plain_owner)
   for y,x in ((25,30),(35,30),(30,25),(30,35)):
    self.assertEqual(owner[y,x],U.PARTS.index(front));self.assertEqual(tuple(image[y,x]),(32,32,32,255))
   self.assertEqual(tuple(image[30,36]),tuple(plain[30,36]))
   reverse,reverse_owner=draw(list(reversed(triangles)))
   np.testing.assert_array_equal(image,reverse);np.testing.assert_array_equal(owner,reverse_owner)
  # Near-contact rims should blend, including at a grazing angle where a
  # large camera-depth difference still means a tiny normal separation.
  for slope,gap,has_line in ((0,.2,False),(0,.7,False),(0,1.4,False),(0,2,True),(3,1,False),(3,4,False),(3,6,True)):
   triangles=quad(torso,(16,16,48,48),lambda x,y:slope*x)+quad(arm,(25,25,35,35),lambda x,y:slope*x+gap)
   image,owner=draw(triangles)
   for y,x in ((25,30),(35,30),(30,25),(30,35)):
    self.assertEqual(owner[y,x],U.PARTS.index(arm))
    self.assertEqual(tuple(image[y,x]),(32,32,32,255) if has_line else tuple(textures[arm][0,0]))
 def test_painted_character_chin_blends_at_contact_but_detached_head_keeps_outline(self):
  import model_data as M,core3d as C
  from unittest.mock import patch
  p=E.new_project();p.update(M.load_resource(ROOT/'examples/models/CustomModel.json'))
  pose=E.poses(p)[0];settings={**p['render'],'outline_color':'#13579b'};line=np.array((19,87,155,255),np.uint8)
  total=0
  for cam in ((0,0),(45,0),(90,0),(45,30)):
   with patch.object(C,'CONTACT_DISTANCE',.75):old=E.rgba(pose,settings,cam)
   with patch.object(C,'finish_raster',wraps=C.finish_raster) as finish:
    new=E.rgba(pose,settings,cam)
   owner=finish.call_args.args[1];head=U.PARTS.index('head');torso=U.PARTS.index('torso')
   chin=(owner==head)&(np.roll(owner,-1,axis=0)==torso)
   removed=chin&np.all(old==line,axis=2)&~np.all(new==line,axis=2)
   total+=int(removed.sum())
   plain=E.rgba(pose,{**settings,'outline':False,'gaps':False},cam)
   np.testing.assert_array_equal(new[removed],plain[removed])
   self.assertTrue(np.any(np.all(new==line,axis=2)&(owner<0)))
  self.assertGreater(total,8)
  # A real gap below the chin is an outer silhouette, which remains 1px.
  p['model']['head']['gap']+=4;detached=E.poses(p)[0]
  with patch.object(C,'finish_raster',wraps=C.finish_raster) as finish:image=E.rgba(detached,settings)
  owner=finish.call_args.args[1];below=(owner<0)&(np.roll(owner,1,axis=0)==U.PARTS.index('head'))
  self.assertTrue(np.any(below&np.all(image==line,axis=2)))
 def painted_pixel_face(self):
  p=E.new_project();p['model']={'head':{'size':.8}};bundle=S.assets(p)
  im=U.texture_image(bundle,'head');x,y,w,h=bundle['textures']['head']['layout']['rects']['front']
  im.paste((206,139,75,255),(x,y,x+w,y+h))
  im.putpixel((x+w//2-2,y+h//2-1),(255,255,255,255));im.putpixel((x+w//2+2,y+h//2-1),(255,255,255,255));im.putpixel((x+w//2,y+h//2+1),(184,60,23,255))
  bundle['textures']['head']['png']=U.encode(im)
  bundle['textures']['head']['protected_groups']=[{'face':'front','pixels':[[px,py] for px in range(x+w//2-3,x+w//2+4) for py in range(y+h//2-2,y+h//2+3)]}]
  p['assets3d']=bundle
  return E.poses(p)[0]
 def test_protected_face_pattern_survives_small_nods(self):
  pose=self.painted_pixel_face()
  relative=None
  for nod in (-22,-18,-15,-12,-8,0,8,12):
   a=E.rgba(dict(pose,head_pitch=nod,dy=.37))
   self.assertTrue(np.any(np.all(a==[184,60,23,255],axis=2)),nod)
   self.assertEqual(np.all(a==[255,255,255,255],axis=2).sum(),2,nod)
   nose=np.argwhere(np.all(a==[184,60,23,255],axis=2));eyes=np.argwhere(np.all(a==[255,255,255,255],axis=2))
   self.assertEqual(len(nose),1,nod)
   offsets=eyes-nose[0]
   if relative is None:relative=offsets
   else:np.testing.assert_array_equal(offsets,relative)
  back=E.rgba(dict(pose,yaw=180));self.assertFalse(np.any(np.all(back==[184,60,23,255],axis=2)))
 def test_protected_groups_work_on_all_body_parts_without_duplicate_marks(self):
  from core3d import raster,unproject
  for part in U.PARTS:
   bundle=S.assets(E.new_project());resource=bundle['textures'][part]
   x,y,w,h=resource['layout']['rects']['front'];cx=x+w//2;cy=y+h//2
   points=[(cx-1,cy),(cx,cy),(cx,cy+1)];colors=[(9,202,101,255),(190,8,229,255),(9,63,230,255)]
   im=U.texture_image(bundle,part);im.paste((180,130,100,255),(0,0,*im.size))
   for point,color in zip(points,colors):im.putpixel(point,color)
   resource['protected_groups']=[dict(face='front',pixels=points)]
   uv=np.array(((x,y),(x+w-1,y),(x+w-1,y+h-1),(x,y+h-1)),float)
   # Minify the UV chart: independent inverse samples would lose/merge texels.
   screen=np.array(((22,20,0),(22+(w-1)*.65,20,0),(22+(w-1)*.65,20+(h-1)*.7,0),(22,20+(h-1)*.7,0)))
   world=np.array([unproject(point,0,0) for point in screen]);triangles=[(part,'front',world[list(ids)],uv[list(ids)]) for ids in ((0,1,2),(0,2,3))]
   image,_=raster(triangles,{part:np.array(im)},(0,0),dict(colors=True,gaps=False,outline=False,onepx=True),protection={part:resource})
   locations=[]
   for color in colors:
    hits=np.argwhere(np.all(image==color,axis=2));self.assertEqual(len(hits),1,(part,color));locations.append(hits[0])
   np.testing.assert_array_equal(np.array(locations)-locations[0],np.array(((0,0),(0,1),(1,1))))
 def test_group_data_survives_project_uv_export_and_model_resize(self):
  pose=self.painted_pixel_face();bundle=pose['_assets3d'];groups=bundle['textures']['head']['protected_groups']
  with tempfile.TemporaryDirectory() as td:
   U.export_pack(bundle,td);other=S.assets(E.new_project());other['model']=bundle['model'];other['textures']=__import__('copy').deepcopy(bundle['textures']);other['textures']['head']['protected_groups']=[]
   U.import_pack(other,td);self.assertEqual(other['textures']['head']['protected_groups'],groups)
   p=E.new_project();p['model']=bundle['model'];p['assets3d']=bundle;path=Path(td)/'project.json';E.save(p,path);self.assertEqual(E.load(path)['assets3d']['textures']['head']['protected_groups'],groups)
  p['model']={'head':{'size':1.3}};resized=S.assets(p);resource=resized['textures']['head']
  self.assertTrue(resource['protected_groups'])
  from pixel_protection import valid_groups
  self.assertEqual(valid_groups(resource),resource['protected_groups'])
 def test_protected_groups_respect_occlusion_and_turn_back_to_uv(self):
  from core3d import raster,unproject
  from pixel_protection import apply
  rgb=np.zeros((64,64,4),np.uint8);owner=np.full((64,64),U.PARTS.index('torso'),np.int16)
  xy=np.array(((30,20),(31,20)));colors=np.array(((255,0,0,255),(0,255,0,255)),np.uint8)
  apply(rgb,owner,[('head',xy,colors)],U.PARTS);self.assertFalse(rgb.any())
  owner[20,30]=U.PARTS.index('head');apply(rgb,owner,[('head',xy,colors)],U.PARTS)
  np.testing.assert_array_equal(rgb[20,30],colors[0]);self.assertFalse(rgb[20,31].any())
  pose=self.painted_pixel_face();plain=__import__('copy').deepcopy(pose)
  plain['_assets3d']['textures']['head'].pop('protected_groups')
  for yaw in (65,90,180):np.testing.assert_array_equal(E.rgba(dict(pose,yaw=yaw)),E.rgba(dict(plain,yaw=yaw)))
 def test_protected_groups_export_matches_preview_at_integer_scales(self):
  pose=self.painted_pixel_face();p=E.new_project('walk');p['seconds']=.2;p['model']=pose['_assets3d']['model'];p['assets3d']=pose['_assets3d']
  expected=E.rgba(E.poses(p)[0],p['render'])
  with tempfile.TemporaryDirectory() as td:
   for scale in (1,2,3):
    dest=E.export(p,td,f'Protected{scale}',formats=['png','recipe'],create_folder=False,scale=scale)
    actual=np.array(Image.open(dest/f'Protected{scale}_00.png'))
    np.testing.assert_array_equal(actual,expected.repeat(scale,0).repeat(scale,1))
    self.assertEqual(E.load(dest/f'Protected{scale}.json')['assets3d'],p['assets3d'])
 def test_pixel_head_translation_does_not_resample_face(self):
  from core3d import raster
  pose=self.painted_pixel_face();base=None;settings=dict(colors=True,outline=True,gaps=False,onepx=True)
  for shift in (0,.1,.3,.7,1.1,1.4,1.8):
   q=dict(pose,dy=shift,dx=.23);j,triangles,bundle=S.pose_meshes(q);triangles=[t for t in triangles if t[0]=='head'];textures={part:np.array(U.texture_image(bundle,part)) for part in U.PARTS}
   image,_=raster(triangles,textures,(0,0),settings,stable_head=j['head']['tip']);center=S.project(np.array([j['head']['tip']]),0,0)[0];row=int(np.floor(center[1]+.5))
   if base is None:base=image;initial=row
   else:np.testing.assert_array_equal(image,np.roll(base,row-initial,axis=0))
 def test_original_size_frames_translate_as_whole_pixels(self):
  pose=self.painted_pixel_face();pose.update(dx=0.,dy=0.)
  for cam in ((0,0),(45,0),(90,0),(45,30)):
   base=E.rgba(pose,cam=cam)
   self.assertEqual(base.shape,(64,64,4))
   for dx,dy in ((.1,.2),(.4,.4),(.7,1.2),(1.1,1.8),(-.8,-1.3)):
    moving=E.rgba(dict(pose,dx=dx,dy=dy),cam=cam)
    projected=S.project(np.array(((dx,-dy,0.),(0.,0.,0.))),*cam);shift=np.floor(projected[0,:2]-projected[1,:2]+.5).astype(int)
    np.testing.assert_array_equal(moving,np.roll(base,(shift[1],shift[0]),axis=(0,1)))
class PaintingWorkflowTests(unittest.TestCase):
 def test_png_matching_uses_layout_provenance_not_transparency(self):
  from paint_workspace import prepare
  bundle=S.assets(E.new_project())
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);folder=root/'paint';prepare(bundle,folder);path=folder/'head.png'
   self.assertEqual(U.texture_match(bundle,'head',path),'matched')
   shifted=copy.deepcopy(bundle);shifted['model']['head'].update(depth=-2,gap=2)
   self.assertEqual(U.texture_match(shifted,'head',path),'matched')
   changed=copy.deepcopy(bundle);changed['model']['head']['shape']='cylinder'
   self.assertEqual(U.texture_match(changed,'head',path),'mapping')
   swapped=copy.deepcopy(bundle);rects=swapped['textures']['head']['layout']['rects'];rects['left'],rects['right']=rects['right'],rects['left']
   self.assertEqual(U.texture_match(swapped,'head',path),'mapping')
   # Identical alpha footprints do not identify a UV layout or surface.
   raw=root/'raw.png';U.texture_image(bundle,'head').save(raw)
   self.assertEqual(U.texture_match(bundle,'head',raw),'unknown');self.assertEqual(U.texture_match(changed,'head',raw),'unknown')
   # Editors may strip PNG text; the adjacent manifest remains authoritative.
   U.texture_image(bundle,'head').save(path);self.assertEqual(U.texture_match(bundle,'head',path),'matched')
   with self.assertRaises(ValueError):U.import_texture(changed,'head',path)
   self.assertEqual(U.texture_match(bundle,'head',folder/'head_Guide.png'),'guide')
 def test_live_painting_waits_for_stable_files_and_retains_last_good_image(self):
  from paint_workspace import prepare
  bundle=S.assets(E.new_project())
  with tempfile.TemporaryDirectory() as td:
   workspace=prepare(bundle,Path(td)/'paint');path=workspace.folder/'head.png'
   painted=U.texture_image(bundle,'head');painted.paste((10,30,90,255),(0,0,*painted.size));painted.save(path)
   self.assertIsNone(workspace.poll(bundle));self.assertEqual(workspace.states['head'],'waiting')
   updated=workspace.poll(bundle);self.assertIsNotNone(updated)
   np.testing.assert_array_equal(np.array(U.texture_image(updated,'head')),np.array(painted))
   path.write_bytes(b'partial save');self.assertIsNone(workspace.poll(updated));self.assertIsNone(workspace.poll(updated));self.assertEqual(workspace.states['head'],'invalid')
   np.testing.assert_array_equal(np.array(U.texture_image(updated,'head')),np.array(painted))
   changed=copy.deepcopy(updated);changed['model']['head']['shape']='cylinder'
   self.assertIsNone(workspace.poll(changed));self.assertEqual(workspace.states['head'],'mapping')
 def test_adaptation_creates_a_new_workspace_without_overwriting_drawings(self):
  from paint_workspace import prepare,adapted_folder
  bundle=S.assets(E.new_project())
  with tempfile.TemporaryDirectory() as td:
   workspace=prepare(bundle,Path(td)/'paint')
   latest=U.texture_image(bundle,'head');latest.paste((42,90,120,255),(0,0,*latest.size));latest.save(workspace.folder/'head.png')
   original=(workspace.folder/'head.png').read_bytes()
   p=E.new_project();p['assets3d']=bundle;p['model']={'head':{'shape':'cylinder','size':1.2}};changed=S.assets(p)
   new=adapted_folder(changed,workspace.folder)
   self.assertNotEqual(new.folder,workspace.folder);self.assertEqual((workspace.folder/'head.png').read_bytes(),original)
   self.assertTrue(all(new.compatible(changed,p) for p in U.PARTS));self.assertEqual(U.texture_match(changed,'head',new.folder/'head.png'),'matched')
   x,y,_,_=changed['textures']['head']['layout']['rects']['front']
   with Image.open(new.folder/'head.png') as image:self.assertEqual(image.getpixel((x,y)),(42,90,120,255))
 def test_shared_textures_follow_edits_and_unlink_without_losing_paint(self):
  bundle=S.assets(E.new_project());left='upperArmL';right='upperArmR'
  self.assertEqual(bundle['shared_textures'][right],left)
  x,y,_,_=bundle['textures'][left]['layout']['rects']['front']
  self.assertNotEqual(U.texture_image(bundle,left).getpixel((x,y)),U.texture_image(bundle,right).getpixel((x,y)))
  image=U.texture_image(bundle,left);image.paste((20,80,150,255),(0,0,*image.size));bundle['textures'][left]['png']=U.encode(image)
  U.apply_shared(bundle);self.assertEqual(bundle['textures'][left]['png'],bundle['textures'][right]['png'])
  independent=bundle['textures'][right]['png'];bundle['shared_textures'].pop(right);image.paste((200,10,10,255),(0,0,*image.size));bundle['textures'][left]['png']=U.encode(image);U.apply_shared(bundle)
  self.assertEqual(bundle['textures'][right]['png'],independent)

if __name__=='__main__':unittest.main()

