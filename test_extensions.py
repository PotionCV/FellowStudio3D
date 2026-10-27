"""Behavior checks for editable shapes and game-oriented motion extensions."""
import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
import engine as E,model_data as M,rounded_scene as S

class ExtensionTests(unittest.TestCase):
 def test_export_keeps_backup_when_the_os_blocks_rollback(self):
  from unittest.mock import patch
  import export_delivery as D
  p=E.new_project();p.update(seconds=.25,fps=8)
  with tempfile.TemporaryDirectory() as td:
   dest=E.export(p,td,'Recovery',formats=['png'],create_folder=False);before={f.name:f.read_bytes() for f in dest.iterdir()}
   copy_original=D.shutil.copyfileobj;replace_original=Path.replace
   def fail_publish(source,output,*args,**kw):
    if Path(output.name).parent==dest:raise OSError('write blocked')
    return copy_original(source,output,*args,**kw)
   def fail_restore(source,target):
    if source.parent.name=='backup':raise OSError('restore blocked')
    return replace_original(source,target)
   with patch.object(D.shutil,'copyfileobj',side_effect=fail_publish),patch.object(Path,'replace',fail_restore):
    with self.assertRaisesRegex(OSError,'backup'):E.export(p,td,'Recovery',formats=['png'],create_folder=False,overwrite=True)
   recovery=next(dest.glob('.fellow-replace-*/backup'))
   self.assertEqual({f.name:f.read_bytes() for f in recovery.iterdir()},before)

 def test_explicit_export_overwrite_removes_stale_selected_frames_only(self):
  p=E.new_project('stand');p.update(seconds=.5,fps=8)
  for folder in (False,True):
   for directions in (1,4):
    with tempfile.TemporaryDirectory() as td:
     dest=E.export(p,td,'Repeat',formats=['png','strip','gif'],create_folder=folder,directions=directions)
     (dest/'notes.txt').write_text('keep');old_gif=next(dest.glob('*.gif'));original=old_gif.read_bytes()
     with self.assertRaises(FileExistsError):E.export(p,td,'Repeat',formats=['png'],create_folder=folder,directions=directions)
     shorter={**p,'seconds':.25}
     E.export(shorter,td,'Repeat',formats=['png','strip'],create_folder=folder,directions=directions,overwrite=True)
     frames=[f for f in dest.glob('*.png') if 'strip' not in f.name and 'atlas' not in f.name]
     self.assertEqual(len(frames),2*directions);self.assertEqual((dest/'notes.txt').read_text(),'keep');self.assertEqual(old_gif.read_bytes(),original)
     if directions==4:
      metadata=dest/'Repeat_atlas.json';saved=metadata.read_bytes()
      E.export(shorter,td,'Repeat',formats=['recipe'],create_folder=folder,directions=1,overwrite=True)
      self.assertEqual(metadata.read_bytes(),saved) # JSON-only cannot delete image metadata

 def test_export_overwrite_rolls_back_render_and_partial_publication_failure(self):
  from unittest.mock import patch
  import export_delivery as D
  p=E.new_project('stand');p.update(seconds=.25,fps=8)
  for directions in (1,4):
   with tempfile.TemporaryDirectory() as td:
    dest=E.export(p,td,'Rollback',formats=['png','strip'],create_folder=False,directions=directions)
    before={f.name:f.read_bytes() for f in dest.iterdir()}
    with patch.object(E,'rgba',side_effect=RuntimeError('render failure')):
     with self.assertRaises(RuntimeError):E.export(p,td,'Rollback',formats=['png','strip'],create_folder=False,directions=directions,overwrite=True)
    self.assertEqual({f.name:f.read_bytes() for f in dest.iterdir()},before)
    original=D.shutil.copyfileobj;count=[]
    def interrupted(source,output,*args,**kwargs):
     if Path(output.name).parent==dest:
      count.append(output.name)
      if len(count)==2:raise OSError('publication interrupted')
     return original(source,output,*args,**kwargs)
    with patch.object(D.shutil,'copyfileobj',side_effect=interrupted):
     with self.assertRaises(OSError):E.export(p,td,'Rollback',formats=['png','strip'],create_folder=False,directions=directions,overwrite=True)
    self.assertEqual(len(count),2);self.assertEqual({f.name:f.read_bytes() for f in dest.iterdir()},before)

 def test_retro_animation_holds_local_cels_without_mutating_motion(self):
  import retro_animation as RA,render_options as O
  p=E.new_project('stand');p.update(seconds=1,fps=12)
  original=copy.deepcopy(p);a=E.poses(p)
  self.assertIs(RA.stylize(a,p),a);self.assertFalse(O.normalized({'retro_animation':'yes'})['retro_animation'])
  p['render']['retro_animation']=True;b=E.poses(p);again=E.poses(p)
  self.assertEqual(len(a),len(b));self.assertEqual(p,{**original,'render':{**original['render'],'retro_animation':True}})
  images=[[E.rgba(f,proj['render']) for f in seq] for seq,proj in ((a,original),(b,p))]
  changes=lambda ims:sum(np.any(im!=ims[i-1],axis=2).sum() for i,im in enumerate(ims))
  self.assertLess(changes(images[1]),changes(images[0]))
  self.assertLess(len({im.tobytes() for im in images[1]}),len({im.tobytes() for im in images[0]}))
  for x,y in zip(b,again):
   for key in ('dy','legL','head','armR'):np.testing.assert_array_equal(x[key],y[key])
  # A small head motion can be held while a large independent hand action moves.
  seq=[E.norm({'head':i*.05,'armR':[i*12,20,0,0]}) for i in range(12)]
  styled=RA.stylize(seq,p)
  self.assertEqual(len({f['head'] for f in styled}),1)
  self.assertGreater(len({tuple(f['armR']) for f in styled}),4)
  self.assertGreater(max(f['armR'][0] for f in styled)-min(f['armR'][0] for f in styled),100)
  self.assertEqual(seq[0]['head'],0.)

 def test_retro_drawing_rhythm_preserves_apex_and_parent_regions(self):
  import retro_animation as RA
  p=E.new_project('stand');p.update(seconds=1,fps=24,render={'retro_animation':True})
  seq=[E.norm({'armR':[i*5,0,0,0],'chest_yaw':.1*np.sin(i),'legL':[i*4,0,0,0]}) for i in range(24)]
  styled=RA.stylize(seq,p)
  self.assertLessEqual(len({tuple(f['armR']) for f in styled}),8)
  self.assertEqual(len({f['chest_yaw'] for f in styled}),1) # legs cannot force chest redraws
  p['playback']='once';seq=[E.norm({'armR':[0,0,0,0]}) for _ in range(24)];seq[11]['armR']=[130,20,0,0]
  styled=RA.stylize(seq,p);self.assertEqual(styled[11]['armR'],seq[11]['armR'])

 def test_retro_pixel_phase_keeps_translated_patterns_and_joint_groups(self):
  import retro_animation as RA
  p=E.new_project('stand');p['pose']=E.norm({'dx':0,'dy':0});pose=E.poses(p)[0]
  anchors=RA.pixel_anchors(pose,S.assets(p))
  np.testing.assert_array_equal(anchors['upperArmL'],anchors['lowerArmL'])
  np.testing.assert_array_equal(anchors['thighR'],anchors['shinR'])
  settings={**p['render'],'retro_animation':True,'outline':False,'gaps':False}
  a=E.rgba(pose,settings);q={**pose,'dx':1.};b=E.rgba(q,settings)
  np.testing.assert_array_equal(a[:,:-1],b[:,1:])
  # Pixel-grid phase correction must also keep protected UV overlays attached.
  resource=M.load_resource('examples/models/CustomModel.json');p.update(model=resource['model'],assets3d=resource.get('assets3d'))
  pose=E.poses(p)[0];a=E.rgba(pose,settings);b=E.rgba({**pose,'dx':1.},settings)
  np.testing.assert_array_equal(a[:,:-1],b[:,1:])

 def test_retro_contacts_endpoints_loop_and_hair_are_coherent(self):
  import retro_animation as RA,hair
  p=E.new_project('jump');p.update(seconds=.5,render={'retro_animation':True})
  a=E.poses({**p,'render':{}});b=E.poses(p)
  for i in (0,len(a)-1):
   for k in ('dy','legL','legR','armR','head'):np.testing.assert_array_equal(a[i][k],b[i][k])
  self.assertEqual([f.get('_ground') for f in a],[f.get('_ground') for f in b])
  for pose in b:
   if pose.get('_ground'):self.assertLess(abs(S.ground_y(pose,('thighL','shinL','thighR','shinR'))-E._ground_level(json.dumps(M.normalize(),sort_keys=True))),.01)
  # Adjacent loop ends may share a cel, but contact boundaries never do.
  values=np.array([[[0.]],[[2.]],[[.1]]]);contacts=[(True,)]*3
  cells=RA._cells(values,True,contacts);self.assertIn([2,0],cells)
  cells=RA._cells(values,True,[(True,),(True,),(False,)]);self.assertNotIn([2,0],cells)
  p=E.new_project('stand');p.update(seconds=.5,model=M.normalize(),render={'retro_animation':True})
  hair.rebuild(p['model'],{'style':'twins'});p['layers']=[E.entry('hair')]
  seq=E.poses(p);self.assertTrue(all(np.isfinite(f['hair_ponyL']).all() for f in seq))

 def test_retro_preview_save_export_and_random_seek_match(self):
  from PIL import Image
  import preview_worker as PW
  p=E.new_project('stand');p.update(seconds=.5,fps=8,render={'retro_animation':True,'canvas_width':96,'canvas_height':96,'lighting':True,'self_shadow':True})
  seq,images=PW.compile_preview(p)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'retro.json';E.save(p,path);restored=E.load(path)
   self.assertTrue(restored['render']['retro_animation'])
   E.export(restored,td,'Retro',formats=['png'],create_folder=False,directions=4)
   files=list(Path(td).rglob('*.png'));self.assertEqual(len(files),len(seq)*4)
   for i in reversed(range(len(seq))):
    for v,cam in enumerate(PW.VIEWS):np.testing.assert_array_equal(images[v,i],E.rgba(seq[i],p['render'],cam))
   rendered={E.rgba(f,p['render'],cam).tobytes() for f in seq for cam in ((0,0),(90,0),(180,0),(270,0))}
   self.assertTrue(all(np.array(Image.open(f).convert('RGBA')).tobytes() in rendered for f in files))

 def test_hair_styles_preserve_character_art_and_have_distinct_chains(self):
  import hair
  resource=M.load_resource('examples/models/CustomModel.json');original=copy.deepcopy(resource)
  previous=S.assets({'model':resource['model'],'assets3d':resource.get('assets3d')})
  counts=[]
  for style in hair.STYLES:
   model=copy.deepcopy(resource['model']);hair.rebuild(model,{'style':style});normalized=M.normalize(model)
   self.assertEqual(normalized,model);self.assertTrue(all(item in normalized['attachments'] for item in original['model']['attachments']))
   bundle=S.assets({'model':normalized,'assets3d':previous})
   for part,data in previous['textures'].items():self.assertEqual(bundle['textures'][part]['png'],data['png'])
   sections={p['section'] for p in normalized['attachments'] if p.get('kind')=='hair'};counts.append(sections)
   self.assertIn('cap',sections)
   for part in normalized['attachments']:
    if part.get('kind')!='hair':continue
    self.assertIn(part['id'],bundle['textures'])
    mesh,bounds=hair.mesh(part);self.assertTrue(all(np.isfinite(t).all() for _,t in mesh))
  self.assertEqual(len({tuple(sorted(c)) for c in counts}),4) # bob and long share a skeleton, different lengths
  self.assertEqual(resource,original)

 def test_hair_fk_uv_mirror_and_body_cache_are_independent(self):
  import hair,attachments as A
  model=M.normalize();hair.rebuild(model,{'style':'twins'});p=E.new_project('stand');p.update(model=model,seconds=.25,fps=8,physics={'hair':{'strength':0}})
  pose=E.poses(p)[0];bundle=S.assets(p);item=next(a for a in model['attachments'] if a['id']=='hair1ponyL')
  first=S.attachment_triangles(item,model,S.geometry(pose)[-1],pose,bundle['textures'][item['id']]['layout'])
  changed=copy.deepcopy(pose);changed['hair_ponyL']=[15,20,0,30,0,0,10,0,0]
  self.assertIs(S.geometry(changed),S.geometry(pose))
  second=S.attachment_triangles(item,model,S.geometry(changed)[-1],changed,bundle['textures'][item['id']]['layout'])
  self.assertFalse(np.allclose(np.concatenate([t[2] for t in first]),np.concatenate([t[2] for t in second])))
  np.testing.assert_array_equal(np.concatenate([t[3] for t in first]),np.concatenate([t[3] for t in second]))
  mirror=E.mirror_pose(changed);np.testing.assert_allclose(mirror['hair_ponyR'],[15,-20,0,30,0,0,10,0,0])
  np.testing.assert_allclose(hair.joints(item,model,S.geometry(changed)[-1],changed)[0],hair.joints(item,model,S.geometry(pose)[-1],pose)[0])

 def test_hair_blend_softness_save_and_motion_transfer(self):
  import hair,motion_resources as MR
  p=E.new_project('stand');p.update(model=M.normalize(),seconds=.5,fps=8,physics={'hair':{'strength':0}});hair.rebuild(p['model'],{'style':'pony'})
  baseline=E.poses(p);p['layers']=[E.entry('hair')];p['controls']={'hair':{'hair_back_middle_pitch':20}}
  authored=E.poses(p);self.assertTrue(any(abs(f['hair_back'][1])>0 for f in authored));self.assertTrue(all(f['hair_back'][3]>15 for f in authored))
  for a,b in zip(baseline,authored):
   for key in E.LIMBS:np.testing.assert_array_equal(a[key],b[key])
  p['layers'][0]['mix']=0;p['controls']={};disabled=E.poses(p)
  for frame in disabled:np.testing.assert_array_equal(frame['hair_back'],[0]*9)
  p['layers'][0]['mix']=1
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'hair.json';E.save(p,path);loaded=E.load(path)
   for a,b in zip(E.poses(p),E.poses(loaded)):np.testing.assert_allclose(a['hair_back'],b['hair_back'])
  recipe=MR.motion_recipe(p);self.assertNotIn('model',recipe);target=E.new_project('run');target['model']=M.normalize();hair.rebuild(target['model'],{'style':'twins'});p=MR.apply_motion(target,recipe);transferred=E.poses(p)
  self.assertTrue(any(abs(f['hair_ponyL'][1])>0 for f in transferred))

 def test_hair_inertia_is_deterministic_and_preserves_grounding(self):
  import hair
  p=E.new_project('run');p.update(seconds=.5,fps=8,model=M.normalize());hair.rebuild(p['model'],{'style':'pony'})
  p['controls']={'head':{'nod':20}};p['physics']['hair']={'strength':0};authored=E.poses(p)
  p['physics'].pop('hair');dynamic=E.poses(p);again=E.poses(p)
  self.assertTrue(any(np.max(abs(np.array(a['hair_back'])-b.get('hair_back',[0]*9)))>.01 for a,b in zip(dynamic,authored)))
  for a,b,c in zip(dynamic,authored,again):
   np.testing.assert_allclose(a['hair_back'],c['hair_back']);self.assertTrue(np.isfinite(a['hair_back']).all());self.assertLessEqual(max(abs(v) for v in a['hair_back']),120)
   for key in ('dx','dy','dz'):self.assertEqual(a.get(key),b.get(key))

 def test_tail_tip_rounding_preserves_legacy_and_texture_layout(self):
  import tails
  from rounded_scene import surface_rings
  item=tails.normalize({'id':'tail1'});mesh,bounds=tails.mesh(item)
  rings=[]
  for t in np.linspace(0,1,13):
   radius=min(1.,t/.06)*(1-t)**.45
   if t==0 or t==1:radius=0.
   rings.append((float(t*item['length']),float(radius*item['width']/2),float(radius*item['thickness']/2)))
  old=surface_rings(rings,12)
  np.testing.assert_array_equal(np.concatenate([t for _,t in mesh]),np.concatenate([t for _,t in old]))
  p=E.new_project();p['model']=M.normalize();key=tails.add(p['model']);original=S.assets(p);record=p['model']['attachments'][0];record['tip']=1.;rounded=S.assets(dict(p,assets3d=original))
  self.assertEqual(original['textures'][key],rounded['textures'][key]);vertices=np.concatenate([v for _,v in tails.mesh(record)[0]])
  near=vertices[np.isclose(vertices[:,1],record['length']*.9166666666666666)];self.assertGreater(np.max(abs(near[:,0])),record['width']*.4)
  self.assertEqual(M.normalize(p['model'])['attachments'][0]['tip'],1.)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'roundtail.json';E.save(p,path);self.assertEqual(E.load(path)['model']['attachments'][0]['tip'],1.)

 def test_individual_hair_profiles_survive_normalize_and_keep_uv_during_fk(self):
  import hair
  p=E.new_project('stand');p.update(model=M.normalize(),seconds=.25,fps=8,physics={'hair':{'strength':0}})
  settings={'style':'twins','locks':{'ponyL':dict(length=26.,width=6.,thickness=1.2,curl=45.,tip=.8,root_scale=.5,mid_scale=1.4,x=-2.,y=1.,z=-1.,outward=-40.,lean=15.,yaw=20.,twist=30.)}}
  hair.rebuild(p['model'],settings);self.assertEqual(M.normalize(p['model']),p['model'])
  left=next(a for a in p['model']['attachments'] if a['id']=='hair1ponyL');right=next(a for a in p['model']['attachments'] if a['id']=='hair1ponyR')
  self.assertEqual(left['length'],26.);self.assertEqual(right['length'],20.);self.assertEqual(left['tip'],.8)
  pose=E.poses(p)[0];bundle=S.assets(p);net=bundle['textures'][left['id']]['layout'];original=S.attachment_triangles(left,p['model'],S.geometry(pose)[-1],pose,net)
  bent=copy.deepcopy(pose);bent['hair_ponyL']=[10,15,0,20,10,0,5,0,0];changed=S.attachment_triangles(left,p['model'],S.geometry(bent)[-1],bent,net)
  self.assertFalse(np.allclose(np.concatenate([t[2] for t in original]),np.concatenate([t[2] for t in changed])))
  np.testing.assert_array_equal(np.concatenate([t[3] for t in original]),np.concatenate([t[3] for t in changed]))
  self.assertTrue(np.isfinite(np.concatenate([t[2] for t in changed])).all())
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'hairshape.json';E.save(p,path);self.assertEqual(E.load(path)['model'],p['model'])
  with self.assertRaises(ValueError):hair.normalize_style({'locks':{'ponyL':{'width':float('nan')}}})

 def test_hair_mirror_copies_complete_shape_and_reflects_geometry(self):
  import hair,hair_editor,types
  model=M.normalize();hair.rebuild(model,{'style':'twins','locks':{'ponyL':{'width':6.,'length':26.,'thickness':1.4,'tip':.8,'root_scale':.5,'mid_scale':1.3,'curl':35.,'outward':-30.,'lean':15.,'yaw':20.,'twist':25.,'x':-2.,'y':1.,'z':-2.}}})
  editor=types.SimpleNamespace(draft=model,show_params=lambda:None,request_preview=lambda:None)
  hair_editor.mirror_lock(editor,'ponyL');self.assertEqual(model['hairstyle']['locks']['ponyR']['twist'],-25.)
  points=[]
  for section in ('ponyL','ponyR'):
   item=next(p for p in model['attachments'] if p.get('section')==section);raw=np.concatenate([v for _,v in hair.mesh(item)[0]]);origin,rotation=hair.frame(item,model,(np.zeros(3),np.eye(3)),{})
   points.append(hair.deform(raw,item)@rotation.T+origin)
  reflected=points[0].copy();reflected[:,0]*=-1
  def ordered(values):
   values=np.round(values,6);return values[np.lexsort(values.T[::-1])]
  np.testing.assert_allclose(ordered(reflected),ordered(points[1]),atol=1e-5)

 def test_free_hair_assembly_has_independent_channels_and_caps(self):
  import hair,hair_assembly as HA,types,uv_assets as U,pose_animation as PA
  p=E.new_project('stand');p.update(model=M.normalize(),seconds=.25,fps=8,physics={'hair':{'strength':0}})
  editor=types.SimpleNamespace(draft=p['model'],source=p,draft_assets=None,show_params=lambda:None,request_preview=lambda:None)
  cap=HA.add(editor,'cap');self.assertEqual(len(editor.draft['attachments']),1)
  first=HA.add(editor,'lock');HA.set_value(editor,first,'width',5.);HA.set_value(editor,first,'x',-8.)
  second=HA.duplicate(editor,first,True);self.assertNotEqual(first,second);self.assertEqual(HA.items(editor)[-1]['x'],8.)
  self.assertEqual(editor.draft_assets['textures'][first]['png'],editor.draft_assets['textures'][second]['png'])
  HA.set_value(editor,first,'length',18.);self.assertEqual(hair.resolve(HA.items(editor),second)['length'],18.)
  HA.set_value(editor,cap,'shape','ellipsoid');HA.set_value(editor,cap,'width',24.);HA.set_value(editor,cap,'crown_flat',.7);HA.set_value(editor,cap,'front_cut',-.2)
  p['model']=editor.draft;p['assets3d']=editor.draft_assets;self.assertEqual(M.normalize(p['model']),p['model'])
  channels=hair.channels_for(p['model']);self.assertEqual(len(set(channels)),2)
  p['controls']={'hair':{channels[0]+'_middle_pitch':30}};pose=E.poses(p)[0]
  self.assertEqual(pose[channels[0]][3],30.);self.assertEqual(pose[channels[1]][3],0.)
  mirrored=E.mirror_pose(pose);self.assertEqual(mirrored[channels[1]][3],30.)
  cap_item=hair.resolve(HA.items(editor),cap);vertices=np.concatenate([v for _,v in hair.mesh(cap_item)[0]]);self.assertTrue(np.isfinite(vertices).all())
  p['layers']=[E.entry('hair')];wind=E.poses(p)[0];self.assertTrue(any(abs(v)>0 for v in wind[channels[1]]))
  cards=PA.normalize_cards([dict(pose=pose),dict(pose=E.norm(E.F.POSES['stand']))]);self.assertIn(channels[0],PA.sample(cards,.6,True))
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'assembly.json';E.save(p,path);saved=E.load(path);self.assertEqual(saved['model'],p['model']);np.testing.assert_array_equal(E.rgba(E.poses(saved)[0],saved['render']),E.rgba(wind,p['render']))
  HA.delete(editor,cap);self.assertFalse(any(a['section']=='cap' for a in HA.items(editor)));self.assertEqual(len(HA.items(editor)),2)

 def test_semantic_hair_components_add_separately_and_pair_without_renaming_rig(self):
  import hair,hair_assembly as HA,types
  p=E.new_project();p['model']=M.normalize();editor=types.SimpleNamespace(draft=p['model'],source=p,draft_assets=None,show_params=lambda:None,request_preview=lambda:None)
  cap=HA.add(editor,'cap');self.assertEqual(len(HA.items(editor)),1)
  left=HA.add(editor,'bangL');HA.set_value(editor,left,'width',5.);HA.set_value(editor,left,'x',-3.)
  right=HA.add(editor,'bangR');self.assertEqual(len(HA.items(editor)),3)
  a=hair.resolve(HA.items(editor),left);b=hair.resolve(HA.items(editor),right)
  self.assertEqual((hair.role(a),hair.role(b)),('bangL','bangR'));self.assertEqual(b['width'],5.);self.assertEqual(b['x'],3.)
  self.assertEqual(hair.channel(a),'hair_bangL');self.assertEqual(hair.channel(b),'hair_bangR');self.assertIs(hair.paired(HA.items(editor),a),b)
  midleft=HA.add(editor,'sideL');midright=HA.add(editor,'sideR');self.assertEqual(len(HA.items(editor)),5)
  self.assertEqual({hair.role(p) for p in HA.items(editor)},{'cap','bangL','bangR','sideL','sideR'})
  self.assertEqual(editor.draft,M.normalize(editor.draft));HA.delete(editor,cap);self.assertEqual(len(HA.items(editor)),4)
  before=hair.channel(hair.resolve(HA.items(editor),midleft));HA.set_value(editor,midleft,'role','ponyL');self.assertEqual(hair.channel(hair.resolve(HA.items(editor),midleft)),before);self.assertEqual(hair.role(hair.resolve(HA.items(editor),midright)),'ponyR')
  HA.add(editor,'ponyL');self.assertEqual(len({hair.name(p) for p in HA.items(editor)}),len(HA.items(editor)))

 def test_zigzag_tail_is_closed_paintable_and_supports_fk(self):
  import tails,collections
  item=tails.normalize(dict(id='tail1',preset='zigzag_tail',width=22.));mesh,bounds=tails.mesh(item);edges=collections.Counter()
  for _,triangle in mesh:
   self.assertGreater(np.linalg.norm(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])),1e-8)
   vertices=[tuple(np.round(p,6)) for p in triangle]
   for a,b in zip(vertices,vertices[1:]+vertices[:1]):edges[tuple(sorted((a,b)))]+=1
  self.assertTrue(all(count==2 for count in edges.values()));raw=np.concatenate([v for _,v in mesh]);bent=tails.skin(raw,item,[10,15,0,5,0,0,0,0,0]);self.assertTrue(np.isfinite(bent).all());self.assertFalse(np.allclose(raw,bent))

 def test_rounded_mascot_keeps_legacy_profile_and_models_round_side_volume(self):
  import plush
  old=M.normalize({'structure':'plush'});explicit=M.normalize({'structure':'plush','body':{'profile':'bag'}})
  self.assertEqual(old,explicit);np.testing.assert_array_equal(np.concatenate([v for _,v in plush.mesh(old)[0]]),np.concatenate([v for _,v in plush.mesh(explicit)[0]]))
  rounded=M.normalize({'structure':'plush','body':{'profile':'rounded','depth':22.}});b=rounded['body']
  self.assertGreater(plush.profile(b,.8)[1],plush.profile(b,.65)[1]);self.assertGreater(plush.profile(b,.34)[1],plush.profile(b,.65)[1])
  self.assertEqual(M.normalize(rounded),rounded)

 def test_painted_lighting_ignores_triangle_facets(self):
  import pixel_lighting as L
  vertices=np.array([[-8,-8,0],[8,-8,0],[8,8,0],[-8,8,0]],float);uv=np.zeros((3,2))
  triangles=[('head','front',vertices[list(ids)],uv) for ids in ((0,1,2),(0,2,3))]
  textures={'head':np.array([[[180,120,80,255]]],np.uint8)};positions=np.array([[0,-6,0],[-4,5,0],[3,0,0]],float)
  def image(style,normals):
   rgb=np.full((1,3,4),(180,120,80,255),np.uint8);settings=dict(lighting=True,self_shadow=False,light_style=style,light_strength=1)
   L.shade(rgb,np.ones(3,bool),positions,np.array(normals,float),L.context(triangles,textures,settings));return rgb
  front=[[0,0,1]]*3;back=[[0,0,-1]]*3
  np.testing.assert_array_equal(image('painted',front),image('painted',back))
  self.assertFalse(np.array_equal(image('facet',front),image('facet',back)))

 def test_large_canvas_export_streams_and_gif_budget_is_checked_before_creation(self):
  import directional_export as D
  from unittest.mock import patch
  p=E.new_project();p.update(seconds=2.5,fps=8);p['render'].update(canvas_width=256,canvas_height=256)
  with patch.object(D,'export',return_value='streamed') as stream:
   self.assertEqual(E.export(p,scale=8,formats={'png','strip'}),'streamed');self.assertEqual(stream.call_args.kwargs['directions'],1)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'absent'
   with self.assertRaises(ValueError):D.export(p,out=path,scale=8,formats={'gif'})
   self.assertFalse(path.exists())

 def test_native_canvas_preserves_pixel_scale_uv_and_default_render(self):
  import render_options as O
  p=E.new_project('stand');pose=E.poses(p)[0];original=E.rgba(pose,p['render']);assets=S.assets(p)
  expanded=E.rgba(pose,dict(p['render'],canvas_width=96,canvas_height=128))
  self.assertEqual(expanded.shape,(128,96,4));np.testing.assert_array_equal(expanded[64:128,16:80],original)
  self.assertEqual(S.assets(p),assets);np.testing.assert_array_equal(original,E.rgba(pose,dict(p['render'],lighting=False,self_shadow=False)))
  j=O.joints(pose,{'canvas_width':96,'canvas_height':128})
  for key,chain in E.R.joints(pose).items():
   for name,(x,y) in chain.items():np.testing.assert_allclose(j[key][name],(x+16,y+64));np.testing.assert_allclose(O.target(j[key][name],{'canvas_width':96,'canvas_height':128}),(x,y))

 def test_pixel_light_self_shadow_is_alpha_aware_and_world_space(self):
  import pixel_lighting as L
  # Horizontal receiver, with a smaller canopy six units above it.
  floor=np.array([[-8,0,-8],[8,0,-8],[8,0,8],[-8,0,8]],float);canopy=np.array([[-2,6,-2],[2,6,-2],[2,6,2],[-2,6,2]],float)
  uv=np.zeros((3,2));triangles=[]
  for part,vertices in (('floor',floor),('canopy',canopy)):
   for ids in ((0,2,1),(0,3,2)):triangles.append((part,'front',vertices[list(ids)],uv))
  tex={'floor':np.array([[[180,160,140,255]]],np.uint8),'canopy':np.array([[[180,160,140,255]]],np.uint8)}
  s=dict(lighting=True,self_shadow=True,light_angle=0,light_height=85,light_strength=1,light_color='#ffffff',shadow_color='#201030')
  positions=np.array([[0,0,0],[5,0,0]],float);normals=np.array([[0,1,0],[0,1,0]],float);filled=np.ones(2,bool)
  def shaded(textures,settings):
   rgb=np.full((1,2,4),(180,160,140,255),np.uint8);L.shade(rgb,filled,positions,normals,L.context(triangles,textures,settings));return rgb
  on=shaded(tex,s);self.assertLess(on[0,0,0],on[0,1,0]);off=shaded(tex,dict(s,self_shadow=False));np.testing.assert_array_equal(off[0,0],off[0,1])
  zero=shaded(tex,dict(s,light_strength=0));self.assertLess(zero[0,0,0],zero[0,1,0])
  np.testing.assert_array_equal(zero,shaded(tex,dict(s,lighting=False)))
  no_effect=shaded(tex,dict(s,lighting=False,shadow_strength=0));np.testing.assert_array_equal(no_effect,np.full((1,2,4),(180,160,140,255),np.uint8))
  self.assertGreater(shaded(tex,dict(s,lighting=False,shadow_strength=.2))[0,0,0],shaded(tex,dict(s,lighting=False,shadow_strength=.9))[0,0,0])
  tex['canopy'][0,0,3]=0;np.testing.assert_array_equal(shaded(tex,s),off)

 def test_pixel_lighting_preserves_alpha_paint_and_zero_strength(self):
  import pixel_lighting as L
  p=E.load(E.ROOT/'examples/characters/CustomCharacter.json');pose=E.poses(p)[0];before=copy.deepcopy(p['assets3d'])
  base=E.rgba(pose,p['render']);settings=dict(p['render'],lighting=True,self_shadow=True,light_strength=.85,light_angle=315,light_height=45)
  lit=E.rgba(pose,settings);np.testing.assert_array_equal(base[:,:,3],lit[:,:,3]);self.assertGreater(np.count_nonzero(base!=lit),100)
  np.testing.assert_array_equal(base,E.rgba(pose,dict(settings,light_strength=0,self_shadow=False)));self.assertEqual(p['assets3d'],before)
  hits=L._shadow.cache_info().hits;E.rgba(pose,settings,(90,0));self.assertGreater(L._shadow.cache_info().hits,hits)
  self.assertFalse(np.array_equal(lit,E.rgba(pose,dict(settings,light_angle=135))))

 def test_rectangular_lit_export_and_atlas_paging_match_native_pixels(self):
  import directional_export as D
  from PIL import Image
  p=E.new_project('stand');p.update(seconds=.25,fps=8);p['render'].update(canvas_width=96,canvas_height=128,lighting=True)
  plan=D.page_layout(3,8,8,(256,256));self.assertEqual(len(plan),8);self.assertTrue(all(max(page['size'])<=4096 for page in plan))
  seq=E.poses(p)
  with tempfile.TemporaryDirectory() as folder:
   out=E.export(p,out=folder,name='Tall',formats={'png','strip','gif','recipe'},scale=2)
   image=np.array(Image.open(out/'Tall_00.png'));self.assertEqual(image.shape,(256,192,4));np.testing.assert_array_equal(image,E.rgba(seq[0],p['render']).repeat(2,0).repeat(2,1))
   with Image.open(out/'Tall_strip.png') as image:self.assertEqual(image.size,(384,256))
   with Image.open(out/'Tall.gif') as image:self.assertEqual(image.size,(192,256))
   out=E.export(p,out=folder,name='FourTall',formats={'png','strip','gif'},directions=4)
   data=json.loads((out/'FourTall_atlas.json').read_text());self.assertEqual(data['native_cell'],[96,128]);self.assertEqual(data['pivot'],[48,120])
   for direction in data['directions']:
    frame=direction['frames'][0];x,y,w,h=frame['rect'];np.testing.assert_array_equal(np.array(Image.open(out/frame['image']).crop((x,y,x+w,y+h))),E.rgba(seq[0],p['render'],(direction['yaw'],0)))

 @unittest.skipUnless(__import__('os').name=='nt','Windows clipboard memory')
 def test_uv_clipboard_native_memory_roundtrip_without_changing_desktop_clipboard(self):
  import image_clipboard as C,io
  from unittest.mock import patch
  from PIL import Image
  _,kernel=C._api()
  class Clipboard:
   def __init__(self):self.data={};self.opened=False
   def RegisterClipboardFormatW(self,name):return 49152
   def OpenClipboard(self,hwnd):self.opened=True;return True
   def CloseClipboard(self):self.opened=False;return True
   def EmptyClipboard(self):return True
   def SetClipboardData(self,kind,handle):self.data[kind]=handle;return handle
   def GetClipboardData(self,kind):return self.data.get(kind)
  user=Clipboard();image=Image.new('RGBA',(3,2),(12,34,56,78));image.putpixel((0,0),(77,88,99,0))
  try:
   with patch.object(C,'_api',return_value=(user,kernel)):
    C.copy_image(image,123,'test');restored=C.read_image()
   self.assertEqual(restored.tobytes(),image.tobytes());self.assertEqual(restored.info['FellowStudio3D'],'test')
   self.assertEqual(set(user.data),{49152,17});self.assertFalse(user.opened)
  finally:
   for handle in user.data.values():kernel.GlobalFree(handle)

 def test_uv_clipboard_image_validation_alpha_metadata_and_no_resize(self):
  import image_clipboard as C,io,struct
  from PIL import Image
  import uv_assets as U
  p=S.assets(E.new_project());part='head';im=U.texture_image(p,part)
  im.putpixel((0,0),(12,34,56,0));im.putpixel((1,1),(76,54,32,123))
  raw=C.png_bytes(im,json.dumps(U.painting_info(p,part)));image=Image.open(io.BytesIO(raw))
  x,y,w,h=p['textures'][part]['layout']['rects']['front'];p['textures'][part]['protected_groups']=[{'pixels':[[x,y]],'angle':40}]
  groups=copy.deepcopy(p['textures'][part]['protected_groups']);U.import_image(p,part,image)
  self.assertEqual(U.texture_image(p,part).tobytes(),im.tobytes());self.assertEqual(p['textures'][part]['protected_groups'],groups)
  self.assertEqual(p['textures'][part]['provenance'],'matched');before=copy.deepcopy(p)
  with self.assertRaises(ValueError):U.import_image(p,part,Image.new('RGBA',(1,1)))
  self.assertEqual(p,before)
  for change in ({'guide':True},{'part':'torso'},{'surface':{}}):
   bad=im.copy();bad.info['FellowStudio3D']=json.dumps(dict(U.painting_info(p,part),**change))
   with self.assertRaises(ValueError):U.import_image(p,part,bad)
   self.assertEqual(p,before)
  dib=C.dib_bytes(im);self.assertEqual(struct.unpack_from('<IiiHHI',dib), (124,im.width,-im.height,1,32,3))
  self.assertEqual(dib[124:],im.tobytes('raw','BGRA'))

 def test_clipboard_override_survives_workspace_poll_until_explicit_reconnect(self):
  import uv_assets as U
  from paint_workspace import prepare
  p=S.assets(E.new_project())
  with tempfile.TemporaryDirectory() as folder:
   workspace=prepare(p,folder);im=U.texture_image(p,'head');im.paste((17,89,111,77),(0,0,*im.size));U.import_image(p,'head',im)
   p['textures']['head'].update(painting_override=True,painting_pending=True);before=copy.deepcopy(p)
   self.assertIsNone(workspace.poll(p,force=True));self.assertEqual(p,before);self.assertEqual(workspace.states['head'],'embedded')
   U.import_texture(p,'head',Path(folder)/'head.png');self.assertNotIn('painting_override',p['textures']['head'])

 def test_tail_softness_is_independent_deterministic_and_saved(self):
  import tails as T,motion_resources as MR
  p=E.new_project('walk');p['physics']={};p['model']=M.normalize();T.add(p['model']);p['layers']=[E.entry('tail')]
  base=E.poses(p);p['physics']={'tail':dict(root=0,middle=0,tip=0,bounce=.6)}
  self.assertEqual(base,E.poses(p))
  p['physics']['tail']['tip']=.7;soft=E.poses(p)
  np.testing.assert_array_equal([q['tail'][:6] for q in base],[q['tail'][:6] for q in soft])
  self.assertGreater(np.max(np.abs(np.array([q['tail'][6:] for q in soft])-np.array([q['tail'][6:] for q in base]))),.1)
  for a,b in zip(base,soft):
   for limb in E.LIMBS:np.testing.assert_array_equal(a[limb],b[limb])
  p['physics']['tail'].update(root=.35,middle=.55);soft=E.poses(p)
  self.assertTrue(np.isfinite([q['tail'] for q in soft]).all())
  E._compiled.cache_clear();self.assertEqual(soft,E.poses(p))
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'tail.json';MR.save_motion(p,path);recipe=E.load(path)
   self.assertEqual(recipe['physics'],p['physics'])
   target=MR.apply_motion(p,recipe);self.assertEqual(E.poses(target),soft)
  p['physics']['tail']=dict(root=0,middle=0,tip=0);self.assertEqual(E.poses(p),base)

 def test_tail_softness_follows_body_without_motion_layer_and_skips_missing_tail(self):
  import tails as T
  p=E.new_project('run');p['model']=M.normalize();T.add(p['model']);p['physics']={'tail':dict(root=.5,middle=.65,tip=.8)}
  seq=E.poses(p);self.assertTrue(any(np.linalg.norm(q['tail'])>.1 for q in seq))
  p['playback']='once';one=E.poses(p);self.assertTrue(np.isfinite([q['tail'] for q in one]).all())
  p['model']['attachments']=[];self.assertTrue(all('tail' not in q for q in E.poses(p)))

 def test_tail_bones_skin_closed_mesh_and_keep_uvs_and_body_cache(self):
  import tails as T,attachments as A
  from collections import Counter
  model=M.normalize();key=T.add(model);item=A.record(model,key);pose={'_model':model,'tail':[0.]*9}
  mesh,bounds=T.mesh(item);raw=np.concatenate([triangle for face,triangle in mesh]);rest=T.deform(raw,item)
  np.testing.assert_array_equal(rest,T.skin(raw,item,[0.]*9))
  angles=[10,25,-5,-30,40,15,50,-25,0];skinned=T.skin(raw,item,angles).reshape(-1,3,3)
  edges=Counter()
  for triangle in skinned:
   for i,j in ((0,1),(1,2),(2,0)):edges[tuple(sorted((tuple(np.round(triangle[i],7)),tuple(np.round(triangle[j],7)))))]+=1
  self.assertEqual(set(edges.values()),{2})
  original=T.joints(item,model,pose);changed=T.joints(item,model,dict(pose,tail=angles))
  S.geometry(pose);hits=S._geometry.cache_info().hits;S.geometry(dict(pose,tail=angles));self.assertGreater(S._geometry.cache_info().hits,hits)
  np.testing.assert_allclose(original[0],changed[0]);self.assertGreater(np.linalg.norm(original[-1]-changed[-1]),1)
  middle=T.joints(item,model,dict(pose,tail=[0,0,0,0,50,0,0,0,0]))
  np.testing.assert_allclose(original[1],middle[1]);self.assertFalse(np.allclose(original[-1],middle[-1]))
  net=S.assets({'model':model})['textures'][key]['layout'];head=S.geometry(pose)[-1]
  first=S.attachment_triangles(item,model,head,pose,net);second=S.attachment_triangles(item,model,head,dict(pose,tail=angles),net)
  for a,b in zip(first,second):np.testing.assert_array_equal(a[3],b[3])
  np.testing.assert_allclose(S.ground_y(dict(pose,tail=angles),{key}),min(t[2][:,1].min() for t in second))

 def test_tail_motion_blends_times_and_controllers_without_changing_body(self):
  import tails as T
  p=E.new_project('walk');p['model']=M.normalize();T.add(p['model']);base=E.poses(p)
  e=E.entry('tail');e.update(start=.25,end=.75,fade=.1,mix=0.);p['layers']=[e]
  off=E.poses(p);e['mix']=1.;on=E.poses(p)
  np.testing.assert_allclose(on[0].get('tail',[0]*9),np.zeros(9));self.assertTrue(any(np.linalg.norm(q['tail'])>1 for q in on))
  for before,after in zip(base,on):
   for limb in E.LIMBS:np.testing.assert_allclose(before[limb],after[limb])
  self.assertTrue(all(np.linalg.norm(q['tail'])==0 for q in off))
  p['controls']={'tail':{'middle_yaw':30,'range':0}};controlled=E.poses(p)
  for q in controlled:np.testing.assert_allclose(q['tail'],[0,0,0,0,30,0,0,0,0])

 def test_saved_animation_retargets_tail_pose_layers_and_preserves_target_paint(self):
  import motion_resources as MR,tails as T,pose_animation as PA,uv_assets as U
  source=E.new_project('walk');source['model']=M.normalize();T.add(source['model']);source['layers']=[E.entry('tail')];source['controls']={'tail':{'tip_pitch':25}}
  target=E.new_project();target['model']=self.plush_model();T.add(target['model']);target['assets3d']=S.assets(target);target['render']['parts']=False
  image=U.texture_image(target['assets3d'],'body');image.putpixel((0,0),(123,77,55,255));target['assets3d']['textures']['body']['png']=U.encode(image)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'motion.json';MR.save_motion(source,path);recipe=E.load(path)
   self.assertFalse({'model','assets3d','render','camera_y'}&recipe.keys())
   transferred=MR.apply_motion(target,recipe)
   for key in ('model','assets3d','render'):self.assertEqual(transferred[key],target[key])
   for a,b in zip(E.poses(source),E.poses(transferred)):np.testing.assert_allclose(a['tail'],b['tail'])
  pose=PA.capture_pose(E.poses(source)[3]);self.assertEqual(len(pose['tail']),9)
  clip=PA.build(source,[dict(pose=pose),dict(pose=E.mirror_pose(pose))]);self.assertEqual(len(E.poses(clip)[0]['tail']),9)

 def test_removed_face_metadata_never_overrides_existing_paint(self):
  import uv_assets as U
  p=E.new_project();p['model']=M.normalize();p['assets3d']=S.assets(p);im=U.texture_image(p['assets3d'],'head');im.putpixel((1,1),(99,5,55,255));p['assets3d']['textures']['head']['png']=U.encode(im)
  baseline=E.rgba(E.poses(p)[0]);p['model']['face']={'enabled':True,'style':'angry','blink':3,'talk':8}
  self.assertNotIn('face',M.normalize(p['model']));np.testing.assert_array_equal(E.rgba(E.poses(p)[0]),baseline)

 def test_painting_binding_tracks_artwork_but_not_motion_or_model_sizing(self):
  from paint_workspace import painting_key
  original=E.new_project();original['assets3d']=S.assets(original)
  changed=copy.deepcopy(original);changed['base']=E.entry('run');changed['model']={'head':{'size':1.3}}
  self.assertEqual(painting_key(original),painting_key(changed))
  import uv_assets as U
  image=U.texture_image(changed['assets3d'],'head');image.putpixel((0,0),(9,30,70,255));changed['assets3d']['textures']['head']['png']=U.encode(image)
  self.assertNotEqual(painting_key(original),painting_key(changed))
  self.assertEqual(painting_key(changed),painting_key(json.loads(json.dumps(changed))))

 def test_resource_catalog_is_public_complete_localized_and_searchable(self):
  import resource_library as L,motion_resources as MR,i18n
  catalog=L.catalog()
  self.assertEqual({r.path for r in catalog if r.kind=='motions'},set(MR.BUILTIN_MOTIONS))
  self.assertEqual({r.path for r in catalog if r.kind=='models'},set(M.BUILTIN_MODELS))
  self.assertFalse(any('CombatStance2' in r.path or 'JumpPunch' in r.path or 'RunAtk' in r.path for r in catalog))
  for resource in catalog:
   self.assertIn(resource.key,L.NAMES)
   for language in ('zh','ja'):
    if resource.kind!='combinations':self.assertNotEqual(L.label(resource.key,language),resource.key)
   self.assertTrue(L.label(resource.key,'en'))
  self.assertEqual(len(L.search(catalog,'motions','游泳')),4)
  self.assertEqual(len(L.search(catalog,'models','weapon')),0)
  self.assertEqual(len(L.search(catalog,'motions','swim','动作串联')),0)
  self.assertEqual(len(L.search(catalog,'models','nonexistent')),0)

 def test_resource_combinations_keep_independent_appearance_motion_and_render(self):
  import resource_library as L,motion_resources as MR
  original=E.new_project('walk');original['camera_y']=2;original['render']['outline']=False
  before=copy.deepcopy(original);catalog=L.catalog()
  mage=next(r for r in catalog if r.key=='CustomModel')
  project=L.combine(original,mage);self.assertEqual(project['base'],original['base']);self.assertIn('assets3d',project)
  motion=next(r for r in catalog if r.key=='HoverWave')
  hover=L.combine(project,motion)
  for key in ('model','assets3d','render','camera_y'):self.assertEqual(hover[key],project[key])
  default=L.combine(hover,next(r for r in catalog if r.key=='DefaultModel'))
  self.assertEqual(default['base'],hover['base']);self.assertNotEqual(default['model'],hover['model'])
  for resource in catalog:
   if resource.kind!='combinations':continue
   combined=L.combine(original,resource);self.assertEqual(combined['render'],original['render']);self.assertEqual(combined['camera_y'],2)
   poses=E.poses(combined);self.assertGreater(len(poses),1)
   np.testing.assert_array_equal(E.rgba(poses[0],combined['render']),E.rgba(E.poses(copy.deepcopy(combined))[0],combined['render']))
  self.assertEqual(original,before)





 def test_hand_props_use_scene_depth_in_front_of_and_behind_the_body(self):
  import hand_props as H,attachments as A,uv_assets as U
  model=M.normalize();key=H.add(model,'shield');item=A.record(model,key);item.update(length=8,width=6,pitch=0,x=-8,y=8)
  bundle=S.assets({'model':model});image=U.texture_image(bundle,key);image.paste((255,0,255,255),(0,0,*image.size));bundle['textures'][key]['png']=U.encode(image)
  counts=[]
  for depth in (8,-8):
   item['z']=depth;pose=E.norm(E.F.POSES['stand']);pose.update(_model=model,_assets3d=bundle,armR=[0,0,0,0])
   rendered=E.rgba(pose);counts.append(int(np.all(rendered[:,:,:3]==[255,0,255],axis=2).sum()))
  self.assertGreater(counts[0],10);self.assertEqual(counts[1],0)

 def test_hand_props_are_closed_validated_and_coexist_with_ears_and_tails(self):
  import hand_props as H,attachments as A,tails as T
  from collections import Counter
  model=M.normalize();A.add_pair(model,'cat');T.add(model)
  for preset in H.PRESETS:
   key=H.add(model,preset);item=A.record(model,key);mesh,bounds=A.mesh(item);edges=Counter()
   for face,triangle in mesh:
    self.assertGreater(np.linalg.norm(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])),1e-8)
    for a,b in ((0,1),(1,2),(2,0)):edges[tuple(sorted((tuple(triangle[a]),tuple(triangle[b]))))]+=1
   self.assertEqual(set(edges.values()),{2});np.testing.assert_allclose(bounds[1]-bounds[0],H.dimensions(item))
  self.assertEqual(len(M.normalize(model)['attachments']),7)
  for invalid in ({'id':'prop0'},{'id':'prop1','parent':'head'},{'id':'prop1','pitch':True},{'id':'prop1','x':float('nan')}):
   with self.assertRaises(ValueError):H.normalize(invalid)
  with self.assertRaises(ValueError):A.normalize([model['attachments'][-1]]*2)

 def test_hand_prop_frames_follow_wrists_continuously_without_head_or_ground_effects(self):
  import hand_props as H,attachments as A
  for model in (M.normalize(),self.plush_model()):
   key=H.add(model,'staff');item=A.record(model,key)
   for arm in ('armL','armR'):
    item['parent']=arm
    p={'_model':model,arm:[30,-12,45,80], 'lean':15,'chest_yaw':25,'rot':12}
    origin,rot=H.frame(item,model,p);np.testing.assert_allclose(origin,S.geometry(p)[2][arm][-1])
    changed=H.frame(item,model,dict(p,head_yaw=70,head_pitch=40))
    np.testing.assert_allclose(changed[0],origin);np.testing.assert_allclose(changed[1],rot)
    a=H.frame(item,model,dict(p,**{arm:[89.999,0,0,0]}))[1]
    b=H.frame(item,model,dict(p,**{arm:[90.001,0,0,0]}))[1]
    self.assertLess(np.linalg.norm(a-b),.001);self.assertAlmostEqual(np.linalg.det(rot),1,places=10)
   plain=copy.deepcopy(model);plain.pop('attachments')
   self.assertAlmostEqual(S.ground_y({'_model':model}),S.ground_y({'_model':plain}),places=8)
   self.assertAlmostEqual(E._roll_pivot(json.dumps(model,sort_keys=True)),E._roll_pivot(json.dumps(plain,sort_keys=True)),places=8)

 def test_hand_prop_uv_and_pixel_protection_survive_transfer_save_and_export(self):
  import hand_props as H,attachments as A,uv_assets as U
  from PIL import Image
  model=M.normalize();key=H.add(model,'shield','armL');p=E.new_project('wave');p.update(model=model,seconds=.5,fps=8)
  bundle=S.assets(p);image=U.texture_image(bundle,key);x,y,w,h=bundle['textures'][key]['layout']['rects']['front']
  image.paste((55,120,190,255),(x,y,x+w,y+h));bundle['textures'][key].update(png=U.encode(image),protected_groups=[{'pixels':[[x+w//2,y+h//2]],'angle':60}]);p['assets3d']=bundle
  moved=copy.deepcopy(bundle);A.record(moved['model'],key).update(parent='armR',pitch=-75,x=2)
  self.assertEqual(U.surface_record(bundle,key),U.surface_record(moved,key))
  A.record(moved['model'],key)['width']+=1;self.assertNotEqual(U.surface_record(bundle,key),U.surface_record(moved,key))
  seq=E.poses(p);context=S.protection_context(seq[0],bundle);self.assertIn(key,context)
  with tempfile.TemporaryDirectory() as folder:
   folder=Path(folder);M.save(model,folder/'prop.json',bundle);loaded=M.load_resource(folder/'prop.json')
   self.assertEqual(loaded['model'],model);self.assertEqual(U.texture_image(loaded['assets3d'],key).tobytes(),image.tobytes())
   U.export_pack(bundle,folder/'paint');restored=copy.deepcopy(bundle);U.import_pack(restored,folder/'paint')
   self.assertEqual(U.texture_image(restored,key).tobytes(),image.tobytes())
   E.export(p,out=folder,name='Shield',formats={'png'},create_folder=False)
   with Image.open(folder/'Shield_00.png') as output:np.testing.assert_array_equal(np.array(output),E.rgba(seq[0],p['render']))

 def test_pose_capture_bakes_independent_head_without_changing_geometry(self):
  import pose_animation as PA
  source=E.norm(E.F.POSES['stand']);source.update(head_follow_chest=False,chest_yaw=32,head_yaw=-18,head_pitch=20,head=-12,lean=10)
  captured=E.norm(PA.capture_pose(source));self.assertEqual(captured['head_yaw'],-50)
  for actual,expected in zip(S.geometry(source)[5],S.geometry(captured)[5]):np.testing.assert_allclose(actual,expected,atol=1e-10)
  for cam in ((0,0),(90,0),(45,0),(45,30)):np.testing.assert_array_equal(E.rgba(source,cam=cam),E.rgba(captured,cam=cam))

 def test_pose_cards_interpolate_holds_endpoints_loop_and_mirror(self):
  import pose_animation as PA
  cards=PA.default_cards();cards[0].update(hold=1.,travel=1.,ease='linear');cards[1].update(hold=1.,travel=1.)
  cards=PA.normalize_cards(cards);a,b=cards[0]['pose'],cards[1]['pose']
  self.assertEqual(PA.sample(cards,0,False),a);self.assertEqual(PA.sample(cards,1,False),b)
  self.assertEqual(PA.sample(cards,.25,False),a)
  np.testing.assert_allclose(PA.sample(cards,.5,False)['armR'],(np.array(a['armR'])+b['armR'])/2)
  for card in cards:card['hold']=0
  self.assertEqual(PA.sample(cards,0,True),PA.sample(cards,1,True))
  np.testing.assert_allclose(PA.sample(cards,1-1e-7,True)['armR'],a['armR'],atol=1e-6)
  mirror=E.mirror_pose(PA.sample(cards,.2,True));double=E.mirror_pose(mirror)
  self.assertEqual(double,PA.sample(cards,.2,True))

 def test_pose_cards_validate_input_and_preserve_appearance_with_one_bake(self):
  import pose_animation as PA
  p=E.new_project('run');p.update(yaw=23,camera_y=3,model={'head':{'size':1.1}},assets3d={'test':'portable'})
  p['controls']={'armR':{'raise':30}};p['layers']=[E.entry('wave')];original=copy.deepcopy(p)
  result=PA.build(p,PA.default_cards(),2,'once',False)
  self.assertEqual(p,original)
  for key in ('model','assets3d','yaw','camera_y','render'):self.assertEqual(result[key],p[key])
  for key in ('controls','physics'):self.assertEqual(result[key],{})
  self.assertEqual(result['layers'],[]);self.assertNotIn('base_playback',result)
  result['layers']=[E.entry('wave')];result['controls']={'head':{'tilt':20}}
  edited=PA.build(result,result['base']['cards'],1.5,'hold',True)
  self.assertEqual(edited['layers'],result['layers']);self.assertEqual(edited['controls'],result['controls'])
  for invalid in ([],[{}]*7,[{'pose':{'armR':[0,float('nan'),0,0]}}]*2):
   with self.assertRaises((ValueError,TypeError)):PA.normalize_cards(invalid)
  for field,value in (('hold',-1),('travel',0),('ease','unknown')):
   cards=PA.default_cards();cards[0][field]=value
   with self.assertRaises(ValueError):PA.normalize_cards(cards)
  with self.assertRaises(ValueError):PA.build(dict(p,fps=24),PA.default_cards(),10)
  with tempfile.TemporaryDirectory() as folder:
   invalid=Path(folder)/'bad.json';broken=copy.deepcopy(result);broken['base']['cards']=[];E.save(broken,invalid)
   with self.assertRaises(ValueError):E.load(invalid)

 def test_pose_card_pipeline_roundtrip_grounding_blending_preview_and_export(self):
  import pose_animation as PA
  from preview_worker import compile_preview
  from PIL import Image
  p=PA.build(E.new_project(),PA.default_cards(),.5,'hold',True);p['fps']=8
  p['model']={'structure':'plush'};p['yaw']=25
  seq=E.poses(p);self.assertEqual(len(seq),4)
  self.assertTrue(all(pose.get('_feet_ground') for pose in seq))
  for pose in seq:
   reference=E._ground_level(json.dumps(M.normalize(p['model']),sort_keys=True))
   self.assertAlmostEqual(S.ground_y(pose,('thighL','shinL','thighR','shinR')),reference,places=5)
  overlay=E.entry('nod');p['layers']=[overlay];seq,raw=compile_preview(p)
  self.assertNotEqual(seq[1]['head_pitch'],E.poses(dict(p,layers=[]))[1]['head_pitch'])
  with tempfile.TemporaryDirectory() as folder:
   recipe=Path(folder)/'roundtrip.json';E.save(p,recipe);self.assertEqual(E.load(recipe),p)
   output=E.export(p,out=folder,name='Cards',formats={'png','recipe'},create_folder=False)
   for i in range(4):
    with Image.open(output/f'Cards_{i:02}.png') as im:np.testing.assert_array_equal(np.array(im),raw[0,i])
  p['base']['ground']=False;p['base']['cards'][1]['pose']['dy']=-6
  self.assertTrue(all(pose.get('_ground') is False for pose in E.poses(p)))

 def test_directional_atlas_metadata_and_pixels_match_all_views(self):
  from PIL import Image
  p=E.new_project('hover');p.update(seconds=.5,fps=8,yaw=17,camera_y=3,playback='hold')
  seq=E.poses(p)
  with tempfile.TemporaryDirectory() as folder:
   dest=E.export(p,out=folder,name='Four',formats={'png','strip','recipe'},create_folder=False,directions=4)
   data=json.loads((dest/'Four_atlas.json').read_text());self.assertEqual(data['frame_count'],4)
   self.assertEqual(data['playback'],'hold');self.assertEqual(data['pivot'],[32,59]);self.assertEqual(data['character_yaw'],17)
   self.assertEqual([view['yaw'] for view in data['directions']],[0,90,180,270])
   with Image.open(dest/'Four_atlas.png') as atlas:
    self.assertEqual(atlas.size,(256,256))
    for view in data['directions']:
     for frame in view['frames']:
      x,y,w,h=frame['rect'];expected=E.rgba(seq[frame['index']],p['render'],(view['yaw'],0))
      np.testing.assert_array_equal(np.array(atlas.crop((x,y,x+w,y+h))),expected)
      with Image.open(dest/frame['png']) as png:np.testing.assert_array_equal(np.array(png),expected)
      self.assertEqual(frame['duration_ms'],125)
   self.assertEqual(E.load(dest/'Four.json')['export_directions'],4)

 def test_directional_atlas_paging_is_bounded_and_upscaling_exact(self):
  import directional_export as D
  from PIL import Image
  from unittest.mock import patch
  plan=D.page_layout(120,8,8);self.assertEqual(len(plan),15)
  self.assertTrue(all(max(page['size'])<=4096 for page in plan))
  image=np.zeros((64,64,4),np.uint8);image[8:12,20:24]=(123,45,67,255)
  p=E.new_project();p.update(seconds=9/8,fps=8)
  with tempfile.TemporaryDirectory() as folder,patch.object(E,'rgba',return_value=image):
   dest=E.export(p,out=folder,name='Paged',formats={'strip'},create_folder=False,scale=8,directions=4)
   data=json.loads((dest/'Paged_atlas.json').read_text());self.assertEqual(len(data['pages']),2)
   self.assertEqual([page['first_frame'] for page in data['pages']],[0,8])
   frame=data['directions'][3]['frames'][8];self.assertEqual(frame['rect'],[0,1536,512,512])
   with Image.open(dest/frame['image']) as atlas:
    np.testing.assert_array_equal(np.array(atlas.crop((0,1536,512,2048))),np.repeat(np.repeat(image,8,axis=0),8,axis=1))

 def test_directional_export_collision_render_failure_and_publish_race_preserve_files(self):
  from unittest.mock import patch
  p=E.new_project();p.update(seconds=.25,fps=8)
  with tempfile.TemporaryDirectory() as folder:
   dest=Path(folder);existing=dest/'Existing_atlas.json';existing.write_text('keep')
   with patch.object(E,'poses',side_effect=AssertionError('rendered before collision check')):
    with self.assertRaises(FileExistsError):E.export(p,out=folder,name='Existing',formats={'strip'},create_folder=False,directions=4)
   self.assertEqual(existing.read_text(),'keep')
   with patch.object(E,'rgba',side_effect=RuntimeError('render failed')):
    with self.assertRaises(RuntimeError):E.export(p,out=folder,name='Failed',formats={'png','strip'},create_folder=False,directions=4)
   self.assertEqual(sorted(f.name for f in dest.iterdir()),['Existing_atlas.json'])
   foreign=dest/'Race_d000_00.png'
   def racing_render(*args):
    if not foreign.exists():foreign.write_bytes(b'other writer')
    return np.zeros((64,64,4),np.uint8)
   with patch.object(E,'rgba',side_effect=racing_render):
    with self.assertRaises(FileExistsError):E.export(p,out=folder,name='Race',formats={'png','strip'},create_folder=False,directions=4)
   self.assertEqual(foreign.read_bytes(),b'other writer');self.assertFalse((dest/'Race_atlas.png').exists());self.assertFalse((dest/'Race_atlas.json').exists())
   self.assertFalse(any(f.name.startswith('.fellow-export-') for f in dest.iterdir()))

 def test_directional_recipe_only_skips_render_and_gifs_keep_playback(self):
  from unittest.mock import patch
  from PIL import Image
  p=E.new_project('hover');p.update(seconds=.25,fps=8,playback='once')
  with tempfile.TemporaryDirectory() as folder:
   with patch.object(E,'poses',side_effect=AssertionError('rendered recipe-only export')):
    dest=E.export(p,out=folder,name='RecipeOnly',formats={'recipe'},create_folder=True,directions=8)
   self.assertTrue((dest/'recipe.json').is_file());data=json.loads((dest/'RecipeOnly_atlas.json').read_text())
   self.assertEqual(len(data['directions']),8);self.assertIsNone(data['directions'][0]['frames'][0]['image'])
   p['export_directions']=8
   E.export(p,out=folder,name='Single',formats={'recipe'},create_folder=False,directions=1)
   self.assertEqual(E.load(Path(folder)/'Single.json')['export_directions'],1);self.assertEqual(p['export_directions'],8)
   dest=E.export(p,out=folder,name='Preview',formats={'gif'},create_folder=False,directions=4)
   for angle in (0,90,180,270):
    with Image.open(dest/f'Preview_d{angle:03}.gif') as gif:self.assertNotIn('loop',gif.info)
   for count in (True,0,3,4.,'8'):
    with self.assertRaises(ValueError):E.export(p,out=folder,name='Invalid',directions=count)

 def test_tails_validate_closed_meshes_and_keep_legacy_ears(self):
  import tails as T,attachments as A
  from collections import Counter
  legacy=M.normalize();A.add_pair(legacy,'cat');ears=copy.deepcopy(legacy['attachments'])
  for preset in T.PRESETS:
   model=copy.deepcopy(legacy);key=T.add(model,preset);model=M.normalize(model)
   self.assertEqual(model['attachments'][:2],ears);item=A.record(model,key)
   edges=Counter()
   for face,local in A.mesh(item)[0]:
    points=A.taper_depth(local,item);self.assertTrue(np.isfinite(points).all())
    vertices=[tuple(np.round(q,9)) for q in points]
    for i,j in ((0,1),(1,2),(2,0)):edges[tuple(sorted((vertices[i],vertices[j])))]+=1
   self.assertTrue(edges);self.assertEqual(set(edges.values()),{2})
  for bad in ({'id':'tail0'},{'id':'tail1','parent':'head'},{'id':'tail1','length':float('nan')},{'id':'tail1','wag':True}):
   with self.assertRaises(ValueError):A.normalize([bad])
  with self.assertRaises(ValueError):A.normalize([T.normalize({'id':'tail1'}),T.normalize({'id':'tail1'})])

 def test_tail_follows_pelvis_not_head_and_wags_deterministically(self):
  import tails as T,attachments as A
  for model in (M.normalize(),self.plush_model()):
   if model.get('structure')=='plush':model['body']['head_link']=False
   key=T.add(model);item=A.record(model,key);item['wag']=18.;q={'_model':model,'_motion_phase':.25}
   origin,rotation=T.frame(item,model,q)
   origin2,rotation2=T.frame(item,model,dict(q,head_yaw=80,head_pitch=40))
   np.testing.assert_allclose(origin,origin2,atol=1e-10);np.testing.assert_allclose(rotation,rotation2,atol=1e-10)
   start=T.frame(item,model,dict(q,_motion_phase=0));end=T.frame(item,model,dict(q,_motion_phase=1))
   np.testing.assert_allclose(start[1],end[1],atol=1e-10);self.assertGreater(np.linalg.norm(rotation-start[1]),.2)
   turned=T.frame(item,model,dict(q,pelvis_yaw=45));self.assertGreater(np.linalg.norm(turned[1]-rotation),.2)
   item['wag']=0;np.testing.assert_allclose(T.frame(item,model,q)[1],T.frame(item,model,dict(q,_motion_phase=.8))[1])
  model=M.normalize();T.add(model);p=E.new_project('walk');p['model']=model
  a=E.poses(p);b=E.poses(p);self.assertEqual(a,b)

 def test_tail_uv_resources_protection_and_grounding_roundtrip(self):
  import tails as T,attachments as A,uv_assets as U
  import paint_workspace as PW
  from PIL import Image
  for model in (M.normalize(),self.plush_model()):
   key=T.add(model,'fluffy_tail');p=E.new_project('walk');p['model']=model;bundle=S.assets(p)
   image=U.texture_image(bundle,key);x,y,w,h=bundle['textures'][key]['layout']['rects']['front']
   image.paste((210,110,55,255),(x,y,x+w,y+h));bundle['textures'][key].update(png=U.encode(image),protected_groups=[{'pixels':[[x+w//2,y+h//2]],'angle':50}]);p['assets3d']=bundle
   # Placement and animation do not invalidate painting files; shape does.
   changed=copy.deepcopy(bundle);item=A.record(changed['model'],key);item.update(wag=-30,cycles=3,x=2)
   self.assertEqual(U.surface_record(bundle,key),U.surface_record(changed,key));item['curl']+=10
   self.assertNotEqual(U.surface_record(bundle,key),U.surface_record(changed,key))
   with tempfile.TemporaryDirectory() as folder:
    folder=Path(folder);U.export_pack(bundle,folder/'paint');restored=copy.deepcopy(bundle);U.import_pack(restored,folder/'paint')
    self.assertEqual(U.texture_image(restored,key).tobytes(),image.tobytes())
    M.save(model,folder/'tail.json',bundle);loaded=M.load_resource(folder/'tail.json');self.assertEqual(loaded['model'],model)
    context=S.protection_context(E.poses(p)[0],bundle);self.assertIn(key,context)
    E.export(p,out=folder/'out',name='Tail',formats={'png'},create_folder=False,scale=1)
    with Image.open(folder/'out'/'Tail_00.png') as im:np.testing.assert_array_equal(np.array(im),E.rgba(E.poses(p)[0],p['render']))
   without=copy.deepcopy(model);without.pop('attachments');q={'_model':model}
   self.assertAlmostEqual(S.ground_y(q),S.ground_y({'_model':without}),places=8)

 def test_attachment_surface_cache_reuses_uvs_during_tail_animation(self):
  import tails as T,attachments as A,uv_assets as U
  from unittest.mock import patch
  model=M.normalize();key=T.add(model);item=A.record(model,key);net=S.assets({'model':model})['textures'][key]['layout']
  S._attachment_local.cache_clear();first=S.attachment_triangles(item,model,S.geometry({'_model':model})[-1],{'_model':model},net)
  with patch.object(S,'uv_tri',side_effect=AssertionError('UV rebuilt for animation')):
   moved=S.attachment_triangles(item,model,S.geometry({'_model':model})[-1],{'_model':model,'tail':[0,30,0,20,-20,0,0,10,0]},net)
  self.assertFalse(np.allclose(first[-1][2],moved[-1][2]))

 def test_swimming_styles_are_distinct_periodic_and_unplanted(self):
  from aerial_actions import Swim,Hover
  for C in (Swim,Hover):
   for style in ('breast','crawl','tread') if C is Swim else ('hover',):
    params=dict(C.defaults(),_style=style)
    self.assertEqual(C.at(0,params,0),C.at(1,params,0))
    for t in np.linspace(0,1,41):
     pose=C.at(t,params,0);self.assertIs(pose['_ground'],False)
     for limb in E.LIMBS:self.assertTrue(np.isfinite(pose[limb]).all())
  params=dict(Swim.defaults(),_style='breast');frog=Swim.at(.4,params,0)
  for key in ('arm','leg'):
   np.testing.assert_allclose(np.array(frog[key+'L'])*[-1,-1,1,1],frog[key+'R'])
  params['_style']='crawl';crawl=Swim.at(.15,params,0)
  self.assertGreater(abs(crawl['armL'][2]-crawl['armR'][2]),50)
  params['_style']='tread';self.assertEqual(Swim.at(.15,params,0)['body_pitch'],0)
  self.assertGreater(frog['body_pitch'],70)

 def test_hover_height_and_free_physics_survive_grounded_base_and_kick(self):
  p=E.new_project('hover');before=E.authored(p);p['base']['params']['height']+=4;after=E.authored(p)
  for a,b in zip(before,after):self.assertAlmostEqual(b['dy'],a['dy']-4)
  p=E.new_project('stand');p['layers']=[E.entry('hover')]
  # Breathing on an idle base must not pin feet in a floating layer.
  p['physics']={'legL':{'strength':.35,'bounce':.2}}
  authored=E.authored(p);physical=E.physical(authored,p)
  self.assertTrue(all(q.get('_ground') is False and not q.get('_breath_ik') for q in authored))
  self.assertTrue(all(q.get('_ground') is False for q in physical))
  self.assertGreater(max(np.linalg.norm(np.array(a['legL'])-b['legL']) for a,b in zip(authored,physical)),1e-4)
  p=E.new_project('hover');base=E.authored(p);p['layers']=[E.entry('kick')]
  for a,b in zip(base,E.authored(p)):self.assertIs(b['_ground'],False);self.assertAlmostEqual(a['dy'],b['dy'])
  p=E.new_project('hover');base=E.authored(p);p['controls']={'torso':{'height':-3}}
  for a,b in zip(base,E.authored(p)):
   self.assertAlmostEqual(b['dy'],a['dy']-3)
   for leg in ('legL','legR'):np.testing.assert_allclose(a[leg],b[leg],atol=1e-10)
  p['controls']={};p['layers']=[E.entry('thrust')]
  for a,b in zip(base,E.authored(p)):
   self.assertIs(b['_ground'],False)
   for leg in ('legL','legR'):np.testing.assert_allclose(a[leg],b[leg],atol=1e-10)

 def test_aerial_model_compatibility_preview_and_export_match(self):
  import preview_worker as W
  from PIL import Image
  for model in (M.normalize(),self.plush_model()):
   p=E.new_project('swim');p.update(model=model,seconds=.5,fps=12);p['base']['style']='crawl'
   seq,images=W.compile_preview(p);self.assertEqual(len(seq),6)
   self.assertTrue(all(q['_model']==model and q.get('_ground') is False for q in seq))
   with tempfile.TemporaryDirectory() as folder:
    E.export(p,out=folder,name='Swim',formats={'png'},create_folder=False,scale=1)
    for i in range(6):
     with Image.open(Path(folder)/f'Swim_{i:02}.png') as im:
      np.testing.assert_array_equal(np.array(im),images[(0,i)])
    path=Path(folder)/'swim.json';E.save(p,path);self.assertEqual(E.load(path),p)

 def test_action_sequence_keeps_appearance_and_edits_without_mutating_source(self):
  import action_sequence as A
  current=E.new_project('stand');current.update(model=self.plush_model(),camera_y=8)
  current['assets3d']=S.assets(current);current['controls']={'torso':{'turn':12}}
  original=copy.deepcopy(current);result=A.build(current,['punchR','punchL','pushR'])
  self.assertEqual(current,original);self.assertEqual(result['playback'],'once')
  self.assertEqual(round(result['seconds']*result['fps']),36)
  for key in ('model','assets3d','controls','camera_y','render'):self.assertEqual(result[key],current[key])
  self.assertEqual([e['kind'] for e in result['layers']],['thrust','thrust','kick'])
  self.assertEqual([e['side'] for e in result['layers']],['right','left','right'])
  self.assertEqual(result['layers'][-1]['style'],'push')
  for i,entry in enumerate(result['layers']):
   self.assertEqual(entry['start'],i/3);self.assertEqual(entry['end'],(i+1)/3)
  poses=E.authored(result);self.assertEqual(len(poses),36)
  reference=copy.deepcopy(result);reference['layers']=[];base=E.authored(reference)
  self.assertGreater(max(np.linalg.norm(np.array(p['armR'])-q['armR']) for p,q in zip(poses[:12],base[:12])),10)
  self.assertGreater(max(np.linalg.norm(np.array(p['armL'])-q['armL']) for p,q in zip(poses[12:24],base[12:24])),10)
  self.assertGreater(max(np.linalg.norm(np.array(p['legR'])-q['legR']) for p,q in zip(poses[24:],base[24:])),10)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'combo.json';E.save(result,path);self.assertEqual(E.load(path),result)
  for args in (([],12),(['unknown'],12),(['bow']*7,12),(['bow'],5),(['bow'],True)):
   with self.assertRaises(ValueError):A.build(current,*args)

 def test_action_sequence_preserves_walking_cadence_and_native_export(self):
  import action_sequence as A
  current=E.new_project('walk');result=A.build(current,['wave','bow','wave'],12)
  seq=E.authored(result);reference=copy.deepcopy(result);reference['layers']=[]
  walking=E.authored(reference);period=round(current['seconds']*current['fps']/current['base'].get('cycles',1))
  for i in range(len(walking)-period):np.testing.assert_allclose(walking[i]['legL'],walking[i+period]['legL'],atol=1e-8)
  self.assertGreater(np.max(np.ptp([p['legL'] for p in seq],axis=0)),1)
  with tempfile.TemporaryDirectory() as folder:
   output=E.export(result,out=folder,name='Combo',formats={'png'},create_folder=False,scale=1)
   from PIL import Image
   paths=list(Path(output).glob('*.png'));self.assertEqual(len(paths),36)
   for path in paths:
    with Image.open(path) as image:self.assertEqual(image.size,(64,64))

 def plush_model(self):
  return M.normalize({'structure':'plush',**{limb:{'upper':3,'lower':3,'gap':0} for limb in E.LIMBS}})

 def test_plush_structure_validates_and_leaves_old_models_unchanged(self):
  import plush as P
  self.assertNotIn('structure',M.normalize());self.assertNotIn('body',M.normalize())
  model=self.plush_model();self.assertEqual(model['body'],P.DEFAULT)
  for bad in ({'structure':'other'},{'structure':'plush','body':[]},{'structure':'plush','body':{'depth':float('nan')}},{'structure':'plush','body':{'head_link':1}}):
   with self.assertRaises(ValueError):M.normalize(bad)
  model=M.normalize({'structure':'plush','body':{'height':100,'upper_width':-10}})
  self.assertEqual(model['body']['height'],46);self.assertEqual(model['body']['upper_width'],12)

 def test_plush_body_is_one_closed_continuous_surface_during_deformation(self):
  import plush as P
  model=self.plush_model()
  for motion in ({},{'lean':65,'chest_yaw':45,'pelvis_yaw':-30},{'head_yaw':55,'head_pitch':-25}):
   model['body']['head_link']=False;pose={'_model':model,**motion};triangles=S.pose_meshes(pose)[1]
   self.assertFalse(any(p in ('head','torso') for p,f,v,uv in triangles))
   edges={}
   for part,face,points,uv in triangles:
    if part!='body':continue
    self.assertTrue(np.isfinite(points).all())
    for a,b in ((0,1),(1,2),(2,0)):
     edge=tuple(sorted((tuple(np.round(points[a],7)),tuple(np.round(points[b],7)))))
     if edge[0]!=edge[1]:edges[edge]=edges.get(edge,0)+1
   self.assertTrue(edges);self.assertEqual(set(edges.values()),{2})

 def test_plush_width_and_depth_change_front_and_side_without_a_neck(self):
  import plush as P
  model=self.plush_model();base=P.mesh(model)[0]
  cloud=np.concatenate([v for f,v in base]);width=np.ptp(cloud[:,0]);depth=np.ptp(cloud[:,2])
  model['body'].update(upper_width=34,belly_width=36,depth=28)
  cloud=np.concatenate([v for f,v in P.mesh(model)[0]])
  self.assertGreater(np.ptp(cloud[:,0]),width);self.assertGreater(np.ptp(cloud[:,2]),depth)
  widths=[P.profile(model['body'],t)[0] for t in (.45,.55,.65,.75,.85)]
  self.assertGreater(min(widths),max(widths)*.85)

 def test_plush_head_link_and_soft_upper_turn_are_explicit(self):
  model=self.plush_model();plain={'_model':model};turned=dict(plain,head_yaw=60,head_pitch=30)
  def body(q):return np.concatenate([v for p,f,v,uv in S.pose_meshes(q)[1] if p=='body'])
  np.testing.assert_allclose(body(plain),body(turned))
  model['body']['head_link']=False
  a=body(plain);b=body(turned);self.assertGreater(np.max(abs(a-b)),1)
  import plush as P
  np.testing.assert_allclose(P.deform(np.array([[0,0,0]]),plain),P.deform(np.array([[0,0,0]]),turned))

 def test_plush_uv_resources_export_protection_and_portable_model_roundtrip(self):
  import uv_assets as U,attachments as A
  model=self.plush_model();A.add_pair(model,'cat');bundle=S.assets({'model':model})
  self.assertEqual(U.parts(bundle)[0],'body');self.assertNotIn('head',bundle['textures']);self.assertNotIn('torso',bundle['textures'])
  x,y,w,h=bundle['textures']['body']['layout']['rects']['front'];im=U.texture_image(bundle,'body');im.putpixel((x+w//2,y+5),(1,2,3,255))
  bundle['textures']['body'].update(png=U.encode(im),protected_groups=[{'face':'front','pixels':[[x+w//2,y+5]],'angle':35}])
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'body.json';M.save(model,path,bundle);restored=M.load_resource(path);self.assertEqual(restored['assets3d'],bundle)
   U.export_pack(bundle,Path(td)/'uv');candidate=copy.deepcopy(bundle);U.import_pack(candidate,Path(td)/'uv')
   self.assertEqual(U.texture_image(candidate,'body').tobytes(),im.tobytes())
   q={'_model':model,'_assets3d':bundle,'chest_yaw':20,'head_yaw':30};self.assertEqual(S.render(q).shape,(64,64,4))

 def test_plush_fast_ik_and_ground_cloud_match_full_render_geometry(self):
  import attachments as A
  model=self.plush_model();A.add_pair(model,'cat')
  for kind in ('stand','walk','run','jump','bow','roll'):
   p=E.new_project(kind);p.update(model=model,seconds=.5,fps=8)
   for q in E.authored(p):
    g,j,chains,limbs,torso,head=S.geometry(q)
    for limb in E.LIMBS:np.testing.assert_allclose(S.limb_chain(q,limb),chains[limb])
    bottom=min(v[:,1].min() for part,face,v,uv in S.pose_meshes(q)[1])
    self.assertAlmostEqual(S.ground_y(q),bottom,places=6)

 def test_ear_depth_thickens_root_without_thickening_tip_or_moving_uvs(self):
  import attachments as A
  for preset in A.PRESETS:
   for depth in (.5,8):
    model=M.normalize();A.add_pair(model,preset)
    for item in model['attachments']:item['thickness']=depth
    q={'_model':model};head=S.geometry(q)[-1];_,triangles,bundle=S.pose_meshes(q)
    for item in model['attachments']:
     origin,rotation=A.frame(item,model,head)
     actual=np.concatenate([(v-origin)@rotation for p,f,v,uv in triangles if p==item['id']])
     tip=actual[np.isclose(actual[:,1],item['height'])]
     self.assertGreater(len(tip),0);np.testing.assert_allclose(tip[:,2],0,atol=1e-9)
     if item['shape']=='pointed':
      root=actual[np.isclose(actual[:,1],0)];self.assertAlmostEqual(np.ptp(root[:,2]),depth)
     mesh,bounds=A.mesh(item);net=bundle['textures'][item['id']]['layout']
     actual_uv=[uv for p,f,v,uv in triangles if p==item['id']]
     for (face,local),uv in zip(mesh,actual_uv):
      chart=local.copy()
      if item['id'].endswith('R'):
       chart[:,0]*=-1;face={'left':'right','right':'left'}.get(face,face)
      np.testing.assert_array_equal(uv,S.uv_tri(face,chart,bounds,net))

 def test_ear_presets_are_closed_mirrored_meshes_and_follow_head(self):
  import attachments as A,uv_assets as U
  for preset in A.PRESETS:
   model=M.normalize();A.add_pair(model,preset);model=M.normalize(model)
   q={'_model':model};head=S.geometry(q)[-1];bundle=S.assets({'model':model})
   self.assertEqual(U.parts(bundle)[-2:],('ear1L','ear1R'))
   self.assertEqual(bundle['shared_textures']['ear1R'],'ear1L')
   _,triangles,_=S.pose_meshes(q)
   points={p:np.concatenate([v for part,f,v,uv in triangles if part==p]) for p in ('ear1L','ear1R')}
   def cloud(a):return np.unique(np.round(a,7),axis=0)
   np.testing.assert_allclose(cloud(points['ear1L']*[-1,1,1]),cloud(points['ear1R']))
   # The same PNG maps to anatomically mirrored texels, including side faces.
   for face in U.FACES:
    left=np.concatenate([np.column_stack((v*[-1,1,1],uv)) for part,f,v,uv in triangles if part=='ear1L' and f==face])
    right=np.concatenate([np.column_stack((v,uv)) for part,f,v,uv in triangles if part=='ear1R' and f==face])
    np.testing.assert_allclose(cloud(left),cloud(right),atol=1e-7)
   for item in model['attachments']:
    mesh,bounds=A.mesh(item)
    for face,v in mesh:
     self.assertTrue(np.isfinite(v).all())
    origin,rot=A.frame(item,model,head)
    moved=dict(q,head_yaw=65,head_pitch=-20,chest_yaw=30)
    head2=S.geometry(moved)[-1];origin2,rot2=A.frame(item,model,head2)
    np.testing.assert_allclose((origin-head[0])@head[1],(origin2-head2[0])@head2[1],atol=1e-8)
    np.testing.assert_allclose(head[1].T@rot,head2[1].T@rot2,atol=1e-8)
   self.assertAlmostEqual(S.ground_y(q),S.ground_y({'_model':M.normalize()}))

 def test_ear_model_roundtrip_embeds_shared_texture_and_protection(self):
  import attachments as A,uv_assets as U
  model=M.normalize();A.add_pair(model,'cat');bundle=S.assets({'model':model})
  image=U.texture_image(bundle,'ear1L');x,y,w,h=bundle['textures']['ear1L']['layout']['rects']['front']
  image.putpixel((x,y),(12,34,56,255));bundle['textures']['ear1L'].update(png=U.encode(image),protected_groups=[{'pixels':[[x,y],[x+1,y]],'angle':60}])
  U.apply_shared(bundle)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'ears.json';M.save(model,path,bundle);restored=M.load_resource(path)
   self.assertEqual(restored['model'],model)
   self.assertEqual(restored['assets3d'],bundle)
   self.assertEqual(U.texture_image(restored['assets3d'],'ear1R').getpixel((x,y)),(12,34,56,255))
   q={'_model':model,'_assets3d':restored['assets3d'],'head_yaw':35}
   self.assertEqual(S.render(q).shape,(64,64,4))

 def test_ear_uv_pack_adapts_old_painting_workspace_and_removes_stale_parts(self):
  import attachments as A,uv_assets as U,paint_workspace as W
  old=S.assets({});model=M.normalize();A.add_pair(model,'long');new=S.assets({'model':model,'assets3d':old})
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'old';workspace=W.prepare(old,path)
   self.assertFalse(workspace.compatible(new,'ear1L'))
   with self.assertRaises(ValueError):U.import_pack(new,path)
   workspace=W.adapted_folder(new,path);self.assertTrue(workspace.compatible(new,'ear1L'))
   self.assertTrue((workspace.folder/'ear1R_Guide.png').is_file())
   U.import_pack(new,workspace.folder)
   self.assertEqual(U.texture_match(new,'ear1R',workspace.folder/'ear1L.png'),'matched')
   shifted=copy.deepcopy(model);shifted['attachments'][0].update(x=.9,lean=30)
   updated=S.assets({'model':shifted,'assets3d':new})
   self.assertEqual(U.surface_record(updated,'ear1L'),U.surface_record(new,'ear1L'))
   cleaned=S.assets({'model':M.normalize(),'assets3d':new})
   self.assertEqual(set(cleaned['textures']),set(U.PARTS))
   self.assertNotIn('ear1R',cleaned.get('shared_textures',{}))

 def test_ear_depth_sort_hides_far_surface_inside_head(self):
  import attachments as A,uv_assets as U
  model=M.normalize();A.add_pair(model,'human');model['attachments']=model['attachments'][:1]
  item=model['attachments'][0];item.update(x=0,y=-.25,width=3,height=3,z=-1)
  def red_pixels():
   bundle=S.assets({'model':model});image=U.texture_image(bundle,'ear1L');image.paste((255,0,0,255),(0,0,*image.size));bundle['textures']['ear1L']['png']=U.encode(image)
   a=S.render({'_model':model,'_assets3d':bundle},{'outline':False,'gaps':False})
   return np.count_nonzero(np.all(a[:,:,:3]==(255,0,0),axis=2))
  self.assertEqual(red_pixels(),0)
  item['z']=1;self.assertGreater(red_pixels(),2)

 def test_ear_validation_rejects_paths_duplicates_nonfinite_and_bad_parent(self):
  import attachments as A
  for bad in (dict(id='../ear1L'),dict(id='ear1L',parent='unknown'),dict(id='ear1L',width=float('nan'))):
   with self.assertRaises(ValueError):M.normalize({'attachments':[bad]})
  item=dict(A.PRESETS['cat'],id='ear1L')
  with self.assertRaises(ValueError):M.normalize({'attachments':[item,item]})
  self.assertNotIn('attachments',M.normalize({'attachments':[]}))
  plain={'_model':M.normalize()};before=S.pose_meshes(plain)[1]
  model=M.normalize();A.add_pair(model,'cat');after=[t for t in S.pose_meshes({'_model':model})[1] if not t[0].startswith('ear')]
  self.assertEqual(len(before),len(after))
  for a,b in zip(before,after):
   self.assertEqual(a[:2],b[:2]);np.testing.assert_array_equal(a[2],b[2]);np.testing.assert_array_equal(a[3],b[3])

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
