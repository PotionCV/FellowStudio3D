import importlib.util,json,os,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import engine as E,rounded_scene as S
ROOT=Path(__file__).resolve().parent

class ReleaseTests(unittest.TestCase):
 def test_itch_archive_is_flat_has_actions_and_recomputed_hashes(self):
  import hashlib,tomllib
  from tools.build_itch_release import build
  with tempfile.TemporaryDirectory() as folder:
   portable=Path(folder)/'portable.zip';out=Path(folder)/'itch.zip'
   files={'runtime/pythonw.exe':b'fake-runtime','launch.py':b'# launcher','docs/GUIDE.en.html':b'<p>guide</p>','VERSION':b'0.2.0\n','SHA256.json':b'{}'}
   with zipfile.ZipFile(portable,'w') as z:
    for name,data in files.items():z.writestr('FellowStudio3D/'+name,data)
   build(portable,out)
   with zipfile.ZipFile(out) as z:
    self.assertFalse(any(name.startswith('FellowStudio3D/') for name in z.namelist()))
    actions=tomllib.loads(z.read('.itch.toml').decode())['actions'];self.assertEqual(actions[0]['args'],['-I','launch.py'])
    for action in actions:self.assertIn(action['path'],z.namelist())
    for name,digest in json.loads(z.read('SHA256.json')).items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
   with self.assertRaises(FileExistsError):build(portable,out)
   with zipfile.ZipFile(portable,'a') as z:z.writestr('FellowStudio3D/../outside',b'bad')
   with self.assertRaises(ValueError):build(portable,Path(folder)/'bad.zip')

 def test_custom_character_and_model_contain_the_same_portable_painted_appearance(self):
  import model_data as M,uv_assets as U
  character=E.load(ROOT/'examples/characters/CustomCharacter.json')
  model=M.load_resource(ROOT/'examples/models/CustomModel.json')
  self.assertEqual(character['model'],model['model']);self.assertEqual(character['assets3d'],model['assets3d'])
  for part in U.PARTS:
   texture=model['assets3d']['textures'][part];self.assertTrue(texture.get('png'),part)
   self.assertFalse({'source_path','path','workspace'} & set(texture))
   self.assertEqual(U.texture_image(model['assets3d'],part).size,tuple(texture['layout']['size']))

 def test_published_motion_defaults_match_examples_without_personal_appearance(self):
  for kind,title in (('walk','Walk'),('run','Run')):
   expected=json.loads((ROOT/'examples/motions'/(title+'.json')).read_text(encoding='utf-8'))
   expected['render'].setdefault('textures',True)
   actual=E.new_project(kind,name=title)
   self.assertEqual(actual,expected)
   self.assertFalse({'model','assets3d','auto_name_key'} & set(actual))
   self.assertEqual(actual['render'],E.RENDER_DEFAULTS)

 def test_offline_guides_have_matching_sections_and_valid_local_links(self):
  from html.parser import HTMLParser
  from tools.build_manuals import build
  build()
  class Page(HTMLParser):
   def __init__(self):super().__init__();self.ids=[];self.links=[];self.sections=0
   def handle_starttag(self,tag,attrs):
    attrs=dict(attrs)
    if 'id' in attrs:self.ids.append(attrs['id'])
    if tag=='a':self.links.append(attrs['href'])
    if tag=='h2':self.sections+=1
  for suffix in ('en','zh-CN','ja'):
   path=ROOT/'docs'/('GUIDE.'+suffix+'.html');page=Page();text=path.read_text(encoding='utf-8');page.feed(text)
   self.assertEqual(page.sections,11);self.assertEqual(len(page.ids),len(set(page.ids)))
   self.assertNotIn('<script',text);self.assertNotIn('src="http',text)
   for link in page.links:
    if link.startswith('#'):self.assertIn(link[1:],page.ids)
    else:self.assertTrue((path.parent/link).exists(),link)

 @unittest.skipUnless(sys.platform=='win32','Windows launcher')
 def test_launcher_resolves_local_runtime_and_quotes_paths(self):
  import time
  from tools.build_release import build_launcher
  with tempfile.TemporaryDirectory(prefix='Fellow launcher ') as td:
   root=Path(td)/'Character tool with spaces';root.mkdir();(root/'runtime').mkdir()
   build_launcher(root/'FellowStudio3D.exe');(root/'launch.py').write_text('# test entry',encoding='utf-8')
   source=root/'Probe.cs'
   source.write_text('using System;using System.IO;using System.Diagnostics;class Probe { static void Main(string[] args) { string path=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"probe.txt"); File.WriteAllLines(path+".tmp",new[]{Environment.CurrentDirectory,string.Join("|",args),Process.GetCurrentProcess().Id.ToString()}); File.Move(path+".tmp",path); } }',encoding='utf-8')
   compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
   subprocess.run([str(compiler),'/nologo','/target:winexe','/out:'+str(root/'runtime/pythonw.exe'),str(source)],check=True)
   subprocess.run([str(root/'FellowStudio3D.exe')],cwd=td,check=True,timeout=10)
   probe=root/'runtime/probe.txt';deadline=time.monotonic()+5
   while not probe.exists() and time.monotonic()<deadline:time.sleep(.05)
   lines=probe.read_text().splitlines();self.assertEqual(Path(lines[0]),root);self.assertEqual(lines[1],'-I|'+str(root/'launch.py'))
   # Wait for our detached probe to exit before removing its executable on Windows.
   import ctypes
   kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=ctypes.c_void_p
   kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
   handle=kernel.OpenProcess(0x100000,False,int(lines[2]))
   if handle:
    try:self.assertEqual(kernel.WaitForSingleObject(handle,5000),0)
    finally:kernel.CloseHandle(handle)

 def test_character_examples_match_presets_and_keep_embedded_textures(self):
  import model_data as M,uv_assets as U
  for name in ('Default','Custom'):
   p=E.load(ROOT/'examples'/'characters'/(name+'Character.json'))
   self.assertEqual(p['model'],M.load(ROOT/'examples'/'models'/(name+'Model.json')))
   self.assertEqual(p['assets3d'],M.load_resource(ROOT/'examples'/'models'/(name+'Model.json'))['assets3d'])
   self.assertEqual(p['base']['kind'],'stand');self.assertFalse(p['layers']);self.assertFalse(p['controls']);self.assertFalse(p['physics'])
   self.assertEqual(p['assets3d'],S.assets(p))
   for part in U.PARTS:self.assertEqual(U.texture_image(p['assets3d'],part).mode,'RGBA')
 def test_model_resources_support_legacy_shape_only_and_embedded_pngs(self):
  import model_data as M
  example=M.load_resource(ROOT/'examples'/'models'/'CustomModel.json')
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'model.json';M.save(example['model'],path,assets=example['assets3d'])
   self.assertEqual(M.load_resource(path),example)
   path.write_text(json.dumps({'type':'FellowStudioModel','model':example['model']}),encoding='utf-8')
   self.assertEqual(M.load_resource(path),{'model':example['model']})
   bad=json.loads((ROOT/'examples'/'models'/'CustomModel.json').read_text(encoding='utf-8'));bad['assets3d']['textures']['head']['png']='broken image'
   path.write_text(json.dumps(bad),encoding='utf-8')
   with self.assertRaises(Exception):M.load_resource(path)
 def test_fast_chain_matches_full_geometry_with_offsets_and_camera(self):
  for kind in ('walk','run'):
   poses=E.authored(E.new_project(kind))
   for pose in poses[::3]:
    pose.update(rot=12,lean=20,chest_yaw=15,pelvis_yaw=-10,off_armL=[2,-1],off_legR=[-1,2])
    for limb in E.LIMBS:np.testing.assert_allclose(S.limb_chain(pose,limb),S.geometry(pose)[2][limb],atol=1e-10)
 def test_source_release_is_self_contained_and_excludes_local_work(self):
  spec=importlib.util.spec_from_file_location('build_release',ROOT/'tools'/'build_release.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'source.zip';builder.build(out)
   with zipfile.ZipFile(out) as z:
    files=z.namelist();self.assertFalse(any('/user_data/' in name or 'studio3d_motion.json' in name or '_audit' in name or '/archive_first_3d/' in name for name in files))
    from motion_resources import BUILTIN_MOTIONS
    prefix='FellowStudio3D/examples/motions/'
    self.assertEqual({name[len(prefix):] for name in files if name.startswith(prefix) and name.endswith('.json')},set(BUILTIN_MOTIONS))
    from model_data import BUILTIN_MODELS
    prefix='FellowStudio3D/examples/models/'
    self.assertEqual({name[len(prefix):] for name in files if name.startswith(prefix) and name.endswith('.json')},set(BUILTIN_MODELS))
    z.extractall(Path(td)/'clean checkout')
   clean=Path(td)/'clean checkout'/'FellowStudio3D'
   result=subprocess.check_output([sys.executable,'-c',"import engine as E; p=E.new_project('walk'); p['seconds']=.2; print(E.rgba(E.poses(p)[0],p['render']).shape)"],cwd=clean,text=True)
   self.assertIn('(64, 64, 4)',result)
   manifest=json.loads((clean/'SHA256.json').read_text())
   import hashlib
   for name,digest in manifest.items():self.assertEqual(hashlib.sha256((clean/name).read_bytes()).hexdigest(),digest)
   with self.assertRaises(FileExistsError):builder.build(out)
 def test_legacy_sessions_are_copied_without_overwrite(self):
  import data_paths
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);old=root/'old';old.mkdir();(old/'studio3d_motion.json').write_text('legacy')
   dest=root/'data'
   with patch.object(data_paths,'ROOT',old),patch.dict(os.environ,{'FELLOWSTUDIO3D_DATA_DIR':str(dest)}):
    state,prefs=data_paths.workspace_paths();self.assertEqual(state.read_text(),'legacy');state.write_text('new')
    data_paths.workspace_paths();self.assertEqual(state.read_text(),'new');self.assertEqual((old/state.name).read_text(),'legacy')

if __name__=='__main__':unittest.main()
