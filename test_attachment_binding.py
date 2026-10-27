import copy,tempfile,unittest
from pathlib import Path
import numpy as np
import engine as E,model_data as M,rounded_scene as S,uv_assets as U
import attachments as A,hand_props as H,tails as T,attachment_binding as B

class BindingTests(unittest.TestCase):
 def test_retired_clothing_records_do_not_break_old_local_projects(self):
  model=M.normalize({'attachments':[dict(id='garment1',kind='garment',parent='torso'),dict(id='prop1',parent='back')]})
  self.assertEqual([item['id'] for item in model['attachments']],['prop1'])
  p=E.new_project();p.update(model=model,seconds=.25,fps=8)
  self.assertEqual(E.rgba(E.poses(p)[0],p['render']).shape,(64,64,4))

 def test_all_bones_are_valid_rigid_frames_and_save_with_textures(self):
  model=M.normalize();A.add_pair(model,'cat');H.add(model);T.add(model)
  p=E.new_project('walk');p.update(model=model,seconds=.25,fps=8)
  for parent in B.LABELS:
   for item in model['attachments']:B.rebind(item,parent)
   normalized=M.normalize(model);self.assertEqual(normalized,model)
   bundle=S.assets(p)
   for part,resource in bundle['textures'].items():
    resource['png']=U.encode(U.template(part,resource['layout']))
   bundle=U.apply_shared(bundle);p['assets3d']=bundle
   for pose in E.poses(p):
    origin,rotation=B.frame(parent,model,pose)
    self.assertTrue(np.isfinite(origin).all());np.testing.assert_allclose(rotation.T@rotation,np.eye(3),atol=1e-9)
    for item in model['attachments']:
     frame=A.frame(item,model,S.geometry(pose)[-1],pose)
     self.assertTrue(np.isfinite(frame[0]).all())
    self.assertEqual(E.rgba(pose,p['render']).shape,(64,64,4))
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'bound.json';M.save(model,path,p['assets3d']);loaded=M.load_resource(path)
   self.assertEqual(loaded['model'],model)
   for part,resource in p['assets3d']['textures'].items():self.assertEqual(loaded['assets3d']['textures'][part]['png'],resource['png'])

 def test_back_is_chest_relative_and_ignores_arm_animation(self):
  model=M.normalize();item=H.normalize(dict(id='prop1',parent='back',preset='shield'))
  pose={'_model':model,'lean':15,'chest_yaw':30,'rot':12}
  origin,rotation=H.frame(item,model,pose)
  other=H.frame(item,model,dict(pose,armL=[80,40,20,30],armR=[-60,90,0,20]))
  np.testing.assert_allclose(other[0],origin);np.testing.assert_allclose(other[1],rotation)
  chest=S.geometry(pose)[4]
  self.assertLess((chest[1].T@(origin-chest[0]))[2],-3.5)
  moved=H.frame(item,model,dict(pose,chest_yaw=60))
  self.assertGreater(np.linalg.norm(moved[1]-rotation),.1)

 def test_limb_frames_follow_authored_bones_without_axial_flips(self):
  model=M.normalize();pose={'_model':model,'armR':[30,-12,45,80],'legL':[20,30,15,10],'chest_yaw':25,'pelvis_yaw':-15,'lean':10}
  for parent,chain,index in (('upperArmR','armR',1),('lowerArmR','armR',2),('armR','armR',3),('thighL','legL',1),('shinL','legL',2),('legL','legL',3)):
   origin,rotation=B.frame(parent,model,pose);np.testing.assert_allclose(origin,S.geometry(pose)[2][chain][index])
   other=B.frame(parent,model,dict(pose,head_yaw=60,head_pitch=30))
   np.testing.assert_allclose(other[0],origin);np.testing.assert_allclose(other[1],rotation)
  frames=[B.frame('armR',model,dict(pose,armR=[v,0,0,0]))[1] for v in (89.999,90.001)]
  self.assertLess(np.linalg.norm(frames[1]-frames[0]),.001)

 def test_rebinding_keeps_uv_and_tail_motion_and_uses_local_parent(self):
  model=M.normalize();key=T.add(model);item=A.record(model,key);bundle=S.assets({'model':model})
  surface=U.surface_record(bundle,key);item.update(tip=.7,length=20)
  bundle=S.assets({'model':model,'assets3d':bundle});surface=U.surface_record(bundle,key)
  B.rebind(item,'back');after=S.assets({'model':model,'assets3d':bundle})
  self.assertEqual(surface,U.surface_record(after,key));self.assertEqual((item['x'],item['y'],item['z']),(0,0,0))
  pose={'_model':model,'tail':[15,10,0,0,20,0,0,0,0],'chest_yaw':20}
  joints=np.asarray(T.joints(item,model,pose));changed=np.asarray(T.joints(item,model,dict(pose,chest_yaw=50)))
  self.assertGreater(np.linalg.norm(joints-changed),1)
  changed2=np.asarray(T.joints(item,model,dict(pose,tail=[0]*9)))
  self.assertGreater(np.linalg.norm(joints-changed2),1)
  for kind in (H,T):
   with self.assertRaises(ValueError):kind.normalize({'id':'prop1' if kind is H else 'tail1','parent':'not-a-bone'})

 def test_default_bindings_remain_legacy_defaults(self):
  self.assertEqual(H.normalize({'id':'prop1'})['parent'],'armR')
  self.assertEqual(T.normalize({'id':'tail1'})['parent'],'pelvis')
  self.assertEqual(A.normalize([{'id':'ear1L'}])[0]['parent'],'head')
  model=M.normalize();pose={'_model':model,'armR':[30,-12,45,80],'lean':15,'chest_yaw':25,'rot':12}
  from core3d import rx,ry,rz
  item=H.normalize({'id':'prop1'});origin,rotation=H.frame(item,model,pose)
  expected=S.root_rotation(pose)@rx(15)@ry(25)@rz(18)@rx(-125)
  np.testing.assert_allclose(rotation,expected);np.testing.assert_allclose(origin,S.geometry(pose)[2]['armR'][-1])
