import tempfile,time,unittest
from pathlib import Path
import app,engine as E,uv_assets as U
from pixel_ui import PixelButton
class UITests(unittest.TestCase):
 def test_plush_structure_panel_stages_applies_loads_and_exposes_one_body_uv(self):
  import copy,plush_editor as PE,model_data as M
  from pixel_ui import PixelScale
  a=self.a;before=copy.deepcopy(a.project);a.edit_model();e=a.model_editor;PE.change(e,'plush');a.update()
  self.assertEqual(a.project,before);self.assertEqual(e.part,'torso');self.assertFalse(e.part_buttons['head'].winfo_ismapped())
  scales=[w for w in e.params.winfo_children() if isinstance(w,PixelScale)];self.assertEqual(len(scales),5)
  scales[2].command(34);self.assertEqual(e.draft['body']['belly_width'],34)
  path=Path(self.temp.name)/'plush.json';M.save(e.draft,path);self.assertEqual(M.load(path)['body']['belly_width'],34)
  e.apply();a.update();self.assertEqual(a.project['model']['structure'],'plush')
  a.edit_textures();e=a.texture_editor;a.update();self.assertEqual(len(e.card_photos),9);self.assertIn('body',e.project['textures']);self.assertNotIn('head',e.project['textures'])
  d=e.inspect_uv('body');a.update();d.destroy();e.cancel()
  a.edit_model();e=a.model_editor;self.assertEqual(e.part_buttons['torso'].text,'主体');PE.change(e,'humanoid');a.update()
  self.assertTrue(e.part_buttons['head'].winfo_ismapped());e.cancel();self.assertEqual(a.project['model']['structure'],'plush')
  a.undo();self.assertEqual(a.project,before)

 def test_ear_editor_stages_mirroring_removal_and_dynamic_uv_cards(self):
  import copy,attachment_editor as AE,attachments as A,model_data as M
  a=self.a;before=copy.deepcopy(a.project)
  a.edit_model();e=a.model_editor;e.select('head');AE.add(e,'cat');a.update()
  self.assertEqual(a.project,before);self.assertEqual(len(e.draft['attachments']),2)
  AE.set_value(e,'lean',-25)
  self.assertEqual([p['lean'] for p in e.draft['attachments']],[-25,-25])
  AE.set_link(e,False);AE.set_value(e,'height',8)
  self.assertEqual([p['height'] for p in e.draft['attachments']],[8,5.5])
  AE.set_link(e,True);self.assertEqual([p['height'] for p in e.draft['attachments']],[8,8])
  e.apply();a.update();self.assertEqual(len(a.project['model']['attachments']),2)
  a.edit_textures();e=a.texture_editor;a.update();self.assertEqual(len(e.card_photos),12)
  self.assertEqual(e.project['shared_textures']['ear1R'],'ear1L')
  e.set_shared('ear1R',False);self.assertNotIn('ear1R',e.project.get('shared_textures',{}))
  image=U.texture_image(e.project,'ear1R');image.paste((13,24,35,255),(0,0,*image.size));path=Path(self.temp.name)/'ear.png';image.save(path)
  e.replace_texture('ear1R',path);self.assertTrue(e.project['textures']['ear1R']['png'])
  d=e.inspect_uv('ear1R');a.update();self.assertEqual(d.part,'ear1R');d.destroy();e.apply();a.update()
  a.edit_model();e=a.model_editor;e.select('head');e.attachment_id='ear1L';AE.remove(e,False)
  self.assertEqual([p['id'] for p in e.draft['attachments']],['ear1R'])
  e.attachment_id='ear1R';AE.remove(e,True);self.assertNotIn('attachments',e.draft)
  e.cancel();self.assertEqual(len(a.project['model']['attachments']),2)
  a.undo();self.assertFalse(a.project['assets3d']['textures']['ear1R'].get('png'))
  a.undo();self.assertEqual(a.project,before)
  a.edit_model();e=a.model_editor;e.select('head');AE.add(e,'human');AE.remove(e,False);e.apply();a.update()
  a.edit_textures();e=a.texture_editor;e.advanced.set(True);e.populate();a.update()
  self.assertEqual(len(e.card_photos),11)
  card=e.cards.grid_slaves(row=5,column=0)[0].winfo_children()[0]
  self.assertFalse(any(isinstance(w,PixelButton) and w.text=='复制另一侧' for w in card.winfo_children()))
  e.cancel()

 def test_signed_bow_squat_spread_and_joint_controls(self):
  from pixel_ui import PixelScale
  a=self.a;a.change_base('弯腰');a.update()
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==-70 and w.hi==70)
  scale.command(-35);self.assertEqual(a.project['base']['params']['deep'],-35)
  a.change_base('蹲下');a.update()
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==-30 and w.hi==65)
  scale.command(35);self.assertEqual(a.project['base']['params']['spread'],35)
  a.select('body','arms');a.update()
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==-135 and w.hi==135)
  scale.command(-60);self.assertEqual(a.project['controls']['arms']['fold'],-60)
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==-2 and w.hi==2)
  scale.command(-1);self.assertEqual(a.project['controls']['arms']['range'],-1)

 def test_custom_idle_thrust_and_body_drive_refresh_without_waiting_for_all_frames(self):
  import copy,model_data as M
  a=self.a;a.project.update(M.load_resource(E.ROOT/'examples/models/CustomModel.json'))
  a.project.update(seconds=2,fps=12);a.change_base('站姿');events=[];accept=a.accept_preview
  def record(seq,images,project,complete=False):
   events.append((a.revision,time.perf_counter(),complete));accept(seq,images,project,complete)
  a.accept_preview=record
  def first():
   deadline=time.perf_counter()+8
   while not any(e[0]==a.revision for e in events) and time.perf_counter()<deadline:a.update();time.sleep(.003)
   self.assertTrue(any(e[0]==a.revision for e in events))
   return next(t for rev,t,complete in events if rev==a.revision)
  first();a.add('thrust');start=time.perf_counter();first_add=first()-start;changes=[]
  for value in (.8,1.2,1.4):
   a.project['layers'][0]['params']['twist']=value;start=time.perf_counter();a.changed();changes.append(first()-start)
  print(' custom idle + thrust first / drive edits:',round(first_add,3),[round(v,3) for v in changes],flush=True)
  self.assertLess(first_add,2.5);self.assertLess(max(changes),2.5)
  deadline=time.perf_counter()+25
  while (a.future_job or a.latest_request or a.pending) and time.perf_counter()<deadline:a.update();time.sleep(.003)
  self.assertIsNone(a.future_job);self.assertEqual(a.active_project['layers'][0]['params']['twist'],1.4)

 def test_twist_lift_overhead_and_raise_direction_controls(self):
  from pixel_ui import PixelOption,PixelScale
  a=self.a;a.change_base('扭腰回正');a.update();self.assertEqual(a.project['base']['kind'],'twist')
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==-120 and w.hi==120)
  scale.command(-80);self.assertEqual(a.project['base']['params']['angle'],-80)
  a.change_base('取放物品');a.update();self.assertEqual(a.project['playback'],'hold')
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '放回地面' in w.values)
  option.pick('放回地面');a.update();self.assertEqual(a.project['base']['operation'],'putdown')
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==0 and w.hi==180)
  scale.command(180);self.assertEqual(a.project['base']['params']['height'],180)
  a.add('raise');a.update();self.assertEqual(a.project['layers'][-1]['plane'],'front')
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '向两侧' in w.values)
  option.pick('向两侧');a.update();self.assertEqual(a.project['layers'][-1]['plane'],'side')
  a.add('thrust');a.update()
  self.assertTrue(any(isinstance(w,PixelScale) and w.lo==-3 and w.hi==3 for w in a.params.winfo_children()))
  scales=[w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==0 and w.hi==1.5]
  scales[-1].command(1.25);self.assertEqual(a.project['layers'][-1]['params']['windup'],1.25)

 def test_kick_style_switch_on_base_and_layer(self):
  from pixel_ui import PixelOption
  a=self.a;a.change_base('踢击');a.update()
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '踹腿' in w.values)
  option.pick('踹腿');a.update();self.assertEqual(a.project['base']['style'],'push')
  a.add('kick');a.update()
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '踹腿' in w.values)
  option.pick('踹腿');a.update();self.assertEqual(a.project['layers'][-1]['style'],'push')
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '摆踢' in w.values)
  option.pick('摆踢');a.update();self.assertEqual(a.project['layers'][-1]['style'],'swing')

 def test_combat_facing_has_one_degree_control_separate_from_pelvis(self):
  from pixel_ui import PixelScale
  a=self.a;a.select('body','torso');a.update()
  sliders=[w for w in a.params.winfo_children() if isinstance(w,PixelScale)]
  facing=next(w for w in sliders if w.lo==0 and w.hi==360);facing.command(17)
  hips=next(w for w in sliders if w.lo==-45 and w.hi==45);hips.command(25)
  self.assertEqual(a.project['yaw'],17);self.assertEqual(a.yaw.get(),'17')
  self.assertEqual(a.project['controls']['torso']['hips_turn'],25)
  self.assertEqual(E.authored(a.project)[0]['pelvis_yaw'],25)
 def test_frame_count_fps_texture_preferences_and_end_position(self):
  import json
  from pixel_ui import PixelScale
  a=self.a;a.frame_count.set('18');a.set_frame_count();self.assertEqual(len(E.authored(a.project)),18)
  a.set_fps('24');self.assertEqual(a.project['fps'],24);self.assertEqual(len(E.authored(a.project)),18);self.assertEqual(a.project['seconds'],.75)
  a.frame_count.set('0');a.set_frame_count();self.assertEqual(a.frame_count.get(),'18')
  a.camera_y.set('6');a.set_camera_y();self.assertEqual(a.project['camera_y'],6)
  a.parts.set(True);a.textures.set(False);a.display();a.change_base('跑步');a.update()
  self.assertTrue(a.project['render']['parts']);self.assertFalse(a.project['render']['textures'])
  self.assertEqual(a.project['camera_y'],6)
  self.assertFalse(json.loads(a.preferences_path.read_text())['render']['textures'])
  a.add('wave');self.assertEqual(a.project['layers'][-1]['blend'],'add')
  a.motion_details=True;a.show_params();a.update();e=a.project['layers'][-1]
  # The two interval sliders share validated absolute positions.
  scales=[w for w in a.params.winfo_children() if isinstance(w,PixelScale)]
  end=next(w for w in scales if w.lo==.025 and w.hi==1);end.command(.6)
  start=next(w for w in scales if w.lo==0 and w.hi==.95);start.command(.2)
  self.assertAlmostEqual(e['start'],.2);self.assertAlmostEqual(e['end'],.6);self.assertNotIn('span',e)
  end.command(.1);self.assertGreater(e['end'],e['start'])
 def test_game_layers_masks_pose_resources_and_playback_controls(self):
  from unittest.mock import patch
  from pixel_ui import PixelOption
  a=self.a
  for label,kind in (('起跳与落地','jump'),('倒地','fall'),('翻滚','roll')):
   a.change_base(label);a.update();self.assertEqual(a.project['base']['kind'],kind)
   options=[w for w in a.params.winfo_children() if isinstance(w,PixelOption)]
   self.assertTrue(any('保持末帧' in w.values for w in options))
  a.add('swing');a.update();e=a.project['layers'][-1]
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '左侧' in w.values)
  option.pick('双侧');a.update();self.assertEqual(e['side'],'both')
  self.assertTrue(any('交替' in w.values for w in a.params.winfo_children() if isinstance(w,PixelOption)))
  a.toggle_motion_details();a.update()
  self.assertTrue(any('替换选中部位' in w.values for w in a.params.winfo_children() if isinstance(w,PixelOption)))
  a.add('pose');a.update();e=a.project['layers'][-1];self.assertNotIn('_assets3d',e['pose'])
  e['scope']='lower';a.show_params();a.update();a.pose_ground.set(True)
  next(w for w in a.params.winfo_children() if getattr(w,'text',None)=='保持地面接触').command()
  self.assertTrue(e['ground'])
  with patch('studio_ui.filedialog.askopenfilename',return_value=str(E.ROOT/'examples/poses/Carry.json')):a.pose_resource(e,'load')
  self.assertIn('armR',e['pose']);a.undo();a.update()
  appearance=a.project.get('model');display=a.project['render'].copy()
  with patch('studio_ui.filedialog.askopenfilename',return_value=str(E.ROOT/'examples/motions/game/Jump.json')):a.load_motion_resource()
  self.assertEqual(a.project['base']['kind'],'jump');self.assertEqual(a.project.get('model'),appearance);self.assertEqual(a.project['render'],display)
  a.edit_model();a.update();editor=a.model_editor;editor.select('head');editor.toggle_sculpt();a.update();editor.set_value('top_width',1.4)
  self.assertEqual(editor.draft['head']['top_width'],1.4);editor.cancel()
  a.edit_model();a.update();editor=a.model_editor;editor.select('armL');editor.link.set(True);editor.set_value('curve',1.5)
  self.assertEqual(editor.draft['armR']['curve'],-1.5);editor.cancel()
 def test_language_switch_keeps_english_default_and_custom_project_names(self):
  a=self.a
  for language in ('简体中文','日本語','English'):
   a.set_language(language);a.new();self.assertEqual(a.project['name'],'Idle')
   a.change_base('跑步');self.assertEqual(a.project['name'],'Run')
  a.name.set('My runner');a.set_language('简体中文')
  self.assertEqual(a.project['name'],'My runner')

 def test_user_guide_follows_current_language_and_f1(self):
  from unittest.mock import patch
  import i18n
  a=self.a;original=i18n.language
  try:
   for language,suffix in (('en','en'),('zh','zh-CN'),('ja','ja')):
    i18n.set_language(language)
    with patch('webbrowser.open') as opened:
     self.assertEqual(a.open_guide(),'break')
     opened.assert_called_once_with((E.ROOT/'docs'/('GUIDE.'+suffix+'.html')).as_uri())
   self.assertTrue(a.bind('<F1>'))
  finally:i18n.set_language(original)

 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();path=Path(self.temp.name)/'state.json';p=E.new_project();p['seconds']=.2;E.save(p,path);self.a=app.App(state=path);self.errors=[];self.a.report_callback_exception=lambda *e:self.errors.append(e);self.a.update()
 def tearDown(self):
  import gc
  self.a.close();del self.a;gc.collect();self.temp.cleanup();self.assertEqual(self.errors,[])
 def test_original_three_pane_workflow_and_controls(self):
  a=self.a;self.assertEqual(len(a.panes.panes()),3);self.assertTrue(hasattr(a,'stack'));self.assertTrue(hasattr(a,'part_buttons'));self.assertEqual(len(a.cells),4)
  a.frame=1;a.render();self.assertGreater(a.scrub.get(),0)
  a.add('raise');self.assertEqual(a.project['layers'][0]['kind'],'raise');a.undo();self.assertEqual(a.project['layers'],[])
  a.select('body','torso');a.edit_model();a.update();self.assertIsNotNone(a.model_editor);a.model_editor.cancel();a.set_language('简体中文');a.zoom(.25);a.update()
 def test_follow_color_angles_export_choices_and_panel_fonts(self):
  from pixel_ui import PixelCheck,PixelOption
  from localized_ui import Label
  import studio_ui as UI
  a=self.a
  def children(w):return [c for child in w.winfo_children() for c in [child]+children(child)]
  self.assertFalse(any(isinstance(w,PixelCheck) and w.text=='1px' for w in children(a)))
  yaw=next(w for w in children(a) if isinstance(w,PixelOption) and w.var is a.yaw)
  self.assertIn('30',yaw.values);self.assertIn('60',yaw.values);yaw.pick('30');self.assertEqual(a.project['yaw'],30.)
  a.select('body','head');a.update();follow=next(w for w in children(a.params) if isinstance(w,PixelCheck) and w.text=='跟随胸腔转动');follow.toggle()
  self.assertFalse(a.project['controls']['head']['follow_chest'])
  d=a.choose_outline_color();a.update();d.value.set('invalid');d.apply();self.assertTrue(d.winfo_exists());d.value.set('#24586c');d.apply()
  self.assertEqual(a.project['render']['outline_color'],'#24586c');a.change_base('走路');self.assertEqual(a.project['render']['outline_color'],'#24586c')
  a.export();a.update();export=next(w for w in a.winfo_children() if isinstance(w,UI.tk.Toplevel));options=[w for w in children(export) if isinstance(w,PixelOption)]
  self.assertTrue(any(tuple(w.values)==('1x','4x','8x') for w in options));export.destroy()
  original=a.option_get('font','Font');a.edit_textures();e=a.texture_editor;a.update();p=e.inspect_uv('head');a.update();p.destroy();e.populate();a.update()
  self.assertEqual(a.option_get('font','Font'),original)
  labels=[w for w in children(e) if isinstance(w,Label)];self.assertTrue(labels)
  self.assertTrue(all(str(w.cget('font'))==str(e.ui_font) for w in labels));e.cancel();a.edit_model();a.update();e=a.model_editor
  self.assertTrue(all(str(w.cget('font'))==str(e.ui_font) for w in children(e) if isinstance(w,Label)));e.cancel()
  import json
  prefs=json.loads(a.preferences_path.read_text());self.assertEqual(prefs['render']['outline_color'],'#24586c')
 def test_head_turn_depth_and_stride_twist_controls_are_available(self):
  from pixel_ui import PixelScale
  a=self.a;a.select('body','head');a.update()
  sliders=[w for w in a.params.winfo_children() if isinstance(w,PixelScale)]
  next(w for w in sliders if w.lo==-90 and w.hi==90).command(35)
  next(w for w in sliders if w.lo==-8 and w.hi==8).command(-2)
  self.assertEqual(a.project['controls']['head']['turn'],35);self.assertEqual(a.project['controls']['head']['depth'],-2)
  a.select('body','torso');a.update();sliders=[w for w in a.params.winfo_children() if isinstance(w,PixelScale)]
  next(w for w in sliders if w.lo==-60 and w.hi==60).command(15)
  self.assertEqual(a.project['controls']['torso']['turn'],15)
  a.change_base('走路');a.selection=('base',None);a.show_params();a.update()
  self.assertTrue(any(d['key']=='twist' for d in E.L.KINDS['walk'].params));a.project['base']['params']['twist']=.5
  a.edit_model();e=a.model_editor;e.select('head');a.update();e.set_value('depth',-1.5);e.apply()
  self.assertEqual(a.project['model']['head']['depth'],-1.5)
 def test_shape_picker_and_negative_offsets_are_staged_linked_and_undoable(self):
  from pixel_ui import PixelOption,PixelScale
  a=self.a;a.edit_model();e=a.model_editor;e.select('head');a.update()
  e.select('torso');a.update()
  thickness=next(w for w in e.params.winfo_children() if isinstance(w,PixelScale) and w.lo==.5 and w.hi==2.)
  thickness.set(1.3);thickness.command('1.3');self.assertEqual(e.draft['torso']['thickness'],1.3)
  e.select('head');a.update()
  picker=next(w for w in e.params.winfo_children() if isinstance(w,PixelOption));picker.pick(app.UI.tr('圆柱形'))
  self.assertEqual(e.draft['head']['shape'],'cylinder');self.assertNotIn('model',a.project)
  e.select('legR');a.update();picker=next(w for w in e.params.winfo_children() if isinstance(w,PixelOption));picker.pick(app.UI.tr('方形'))
  e.set_value('spread',-2);e.set_value('gap',-2)
  self.assertEqual(e.draft['legL']['shape'],'box');self.assertEqual(e.draft['legL']['spread'],-2)
  sliders=[w for w in e.params.winfo_children() if isinstance(w,PixelScale)]
  self.assertTrue(any(w.lo==-6 and w.hi==6 for w in sliders));e.apply();self.assertEqual(a.project['model']['head']['shape'],'cylinder');self.assertEqual(a.project['model']['torso']['thickness'],1.3)
  a.undo();self.assertNotIn('model',a.project)
 def test_uv_window_is_staged_and_uses_real_3d_preview(self):
  a=self.a;a.edit_textures();e=a.texture_editor;a.update();self.assertEqual(len(e.card_photos),10);self.assertEqual(len(e.cells),4)
  path=Path(self.temp.name)/'painted head.png';im=U.texture_image(e.project,'head');im.paste((255,0,0,255),(0,0,*im.size));im.save(path)
  e.drop_texture('head',a.tk.call('list',str(path)));self.assertNotIn('assets3d',a.project);e.apply();a.update();self.assertTrue(a.project['assets3d']['textures']['head']['png'])
  a.undo();self.assertNotIn('assets3d',a.project)
 def test_model_with_textures_is_staged_preserves_motion_and_undoes_together(self):
  import copy,model_data as M,model_editor as ME
  from unittest.mock import patch
  a=self.a;a.change_base('跑步');a.add('raise');before=copy.deepcopy(a.project)
  path=E.ROOT/'examples'/'models'/'CustomModel.json';expected=M.load_resource(path)
  a.edit_model();editor=a.model_editor
  with patch.object(ME.filedialog,'askopenfilename',return_value=str(path)):editor.load_preset()
  self.assertEqual(a.project,before);self.assertEqual(editor.preview_project()['assets3d'],expected['assets3d'])
  saved=Path(self.temp.name)/'saved model.json'
  with patch.object(ME.filedialog,'asksaveasfilename',return_value=str(saved)):editor.save_preset()
  self.assertEqual(M.load_resource(saved),expected);editor.cancel();self.assertEqual(a.project,before)
  a.edit_model();editor=a.model_editor
  with patch.object(ME.filedialog,'askopenfilename',return_value=str(path)):editor.load_preset()
  editor.apply();self.assertEqual(a.project['assets3d'],expected['assets3d']);self.assertEqual(a.project['model'],expected['model'])
  for key in ('base','layers','controls','physics','yaw','seconds','fps'):self.assertEqual(a.project[key],before[key])
  a.undo();self.assertEqual(a.project,before)
  a.project['assets3d']=expected['assets3d'];a.edit_model();editor=a.model_editor
  M.save(M.normalize(),saved)
  with patch.object(ME.filedialog,'askopenfilename',return_value=str(saved)):editor.load_preset()
  self.assertEqual(editor.draft_assets,expected['assets3d']);editor.cancel()
 def test_uv_cancel_and_animation_switch_keep_resources(self):
  a=self.a;a.edit_textures();a.texture_editor.cancel();self.assertNotIn('assets3d',a.project)
  import rounded_scene as S
  a.project['assets3d']=S.assets(a.project);before=a.project['assets3d'];a.change_base('跑步');self.assertEqual(a.project['assets3d'],before);self.assertEqual(a.project['base'],E.new_project('run')['base'])
 def test_protection_brush_zoom_pan_cross_face_edit_and_copy(self):
  from types import SimpleNamespace
  a=self.a;a.edit_textures();e=a.texture_editor;d=e.inspect_uv('head');a.update()
  x,y,w,h=d.resource['layout']['rects']['front'];r=d.resource['layout']['rects']['right']
  def event(px,py,state=0):
   ox,oy=d.offset;z=d.zoom;return SimpleNamespace(x=ox+px*z+z//2,y=oy+py*z+z//2,state=state)
  d.set_tool('brush');d.begin(event(x+w-2,y+3));d.drag(event(r[0]+2,y+3));d.end(event(r[0]+2,y+3))
  self.assertEqual(len(d.selection),5)
  d.begin(event(x+w-2,y+3),erase=True);d.end(event(x+w-2,y+3));self.assertEqual(len(d.selection),4)
  d.undo();self.assertEqual(len(d.selection),5)
  chosen=set(d.selection);zoom=d.zoom;d.change_zoom(1);self.assertGreater(d.zoom,zoom);self.assertEqual(d.selection,chosen)
  lines=[d.canvas.coords(item) for item in d.canvas.find_all() if d.canvas.type(item)=='line']
  self.assertTrue(any(p[1]==p[3] and p[0]!=p[2] for p in lines));self.assertTrue(any(p[0]==p[2] and p[1]!=p[3] for p in lines))
  origin=d.offset;d.begin_pan(SimpleNamespace(x=30,y=30));d.move_pan(SimpleNamespace(x=80,y=65));d.end_pan();self.assertEqual(d.offset,(origin[0]+50,origin[1]+35))
  d.set_angle(25);d.add_group();self.assertEqual(d.groups[0]['faces'],['front','right']);self.assertEqual(d.groups[0]['angle'],25)
  d.edit_group(0);d.selection.add((x+w-3,y+3));d.set_angle(30);d.add_group();self.assertEqual(len(d.groups),1);self.assertEqual(len(d.groups[0]['pixels']),6);d.apply()
  e.copy_other_side('upperArmR');self.assertEqual(U.texture_image(e.project,'upperArmR').tobytes(),U.texture_image(e.project,'upperArmL').tobytes())
  e.undo_texture();self.assertFalse(e.project['textures']['upperArmR'].get('png'));e.cancel()
 def test_uv_protection_selection_is_staged_and_undoable(self):
  from types import SimpleNamespace
  a=self.a;a.edit_textures();e=a.texture_editor;d=e.inspect_uv('head');a.update()
  x,y,w,h=d.resource['layout']['rects']['front'];x+=2;y+=2;ox,oy=d.offset;z=d.zoom
  def event(px,py,state=0):return SimpleNamespace(x=ox+px*z+z//2,y=oy+py*z+z//2,state=state)
  d.begin(event(x,y));d.end(event(x+2,y+1));self.assertEqual(len(d.selection),6)
  d.begin(event(x+4,y,1));d.end(event(x+4,y,1));self.assertEqual(len(d.selection),7)
  d.begin(event(x+4,y,4));d.end(event(x+4,y,4));self.assertEqual(len(d.selection),6)
  d.add_group();self.assertEqual(len(d.groups),1);self.assertFalse(e.project['textures']['head'].get('protected_groups'))
  d.remove_group(0);d.undo();self.assertEqual(len(d.groups),1)
  d.apply();self.assertEqual(len(e.project['textures']['head']['protected_groups']),1);self.assertNotIn('assets3d',a.project)
  e.undo_texture();self.assertFalse(e.project['textures']['head'].get('protected_groups'))
  d=e.inspect_uv('head');a.update();d.selection={(x,y),(x+1,y)};d.add_group();d.apply();e.apply();self.assertEqual(len(a.project['assets3d']['textures']['head']['protected_groups']),1)
  a.undo();self.assertNotIn('assets3d',a.project)
 def test_current_frame_arrives_before_complete_animation_and_latest_wins(self):
  a=self.a;events=[];accept=a.accept_preview;started=time.perf_counter()
  def record(seq,images,project,complete=False):
   events.append((time.perf_counter()-started,complete,project['controls'].get('armR',{}).get('raise',0),len(images)));accept(seq,images,project,complete)
  a.accept_preview=record;a.change_base('走路');a.request_preview()
  deadline=time.perf_counter()+20
  while (a.future_job or a.latest_request or a.pending) and time.perf_counter()<deadline:a.update();time.sleep(.005)
  self.assertIsNone(a.future_job);self.assertTrue(any(not event[1] and event[3]==4 for event in events));self.assertTrue(events[-1][1]);self.assertLess(events[0][0],events[-1][0])
  print(' preview first/full:',round(events[0][0],3),round(events[-1][0],3),flush=True)
  a.project['controls'].setdefault('armR',{})['raise']=30;a.changed();a.request_preview();a.project['controls']['armR']['raise']=65;a.changed();a.request_preview()
  deadline=time.perf_counter()+20
  while (a.future_job or a.latest_request or a.pending) and time.perf_counter()<deadline:a.update();time.sleep(.005)
  self.assertEqual(a.active_project['controls']['armR']['raise'],65);self.assertTrue(events[-1][1]);self.assertEqual(events[-1][2],65)
 def test_narrow_toolbars_keep_all_actions_inside_their_rows(self):
  from pixel_ui import FlowBar
  a=self.a;a.geometry('1100x850');a.zoom(.25);a.update()
  for bar in (w for w in a.winfo_children() if isinstance(w,FlowBar)):
   for child in bar.winfo_children():
    self.assertEqual(child.winfo_manager(),'place')
    self.assertLessEqual(child.winfo_x()+child.winfo_width(),bar.winfo_width()+1)
    self.assertLessEqual(child.winfo_y()+child.winfo_height(),bar.winfo_height()+1)
   if bar.pin_right:
    language=next(w for w in bar.winfo_children() if getattr(w,'var',None) is a.language_var)
    self.assertLessEqual(abs(bar.winfo_width()-language.winfo_x()-language.winfo_width()),1)
    self.assertEqual(language.winfo_y(),0)
  self.assertGreater(a.canvas.winfo_width(),360)
 def test_incomplete_preview_never_rasterizes_missing_frames_on_ui_thread(self):
  from unittest.mock import patch
  a=self.a;seq=a.seq;images={(v,0):E.rgba(seq[0],a.project['render'],cam) for v,cam in enumerate(app.UI.VIEWS)}
  a.revision+=1;a.accept_preview(seq,images,a.project);a.frame=1;a.photos.clear()
  with patch.object(E,'rgba',side_effect=AssertionError('UI thread rasterized a missing frame')):a.render()
  self.assertEqual(len(a.raw_images),4)
  a.accept_preview(seq,{(v,1):im for (v,_),im in images.items()},a.project)
  self.assertEqual(len(a.raw_images),8)
 def test_export_keeps_event_loop_alive_and_blocks_duplicate_submission(self):
  from unittest.mock import patch
  from concurrent.futures import ProcessPoolExecutor
  import tkinter as tk
  a=self.a;a.export_directory=self.temp.name;a.export_pool=ProcessPoolExecutor(max_workers=1)
  def children(w):return [c for child in w.winfo_children() for c in [child]+children(child)]
  with patch.object(a.export_pool,'submit',wraps=a.export_pool.submit) as submitted:
   a.export();a.update();dialog=next(w for w in a.winfo_children() if isinstance(w,tk.Toplevel))
   start=next(w for w in children(dialog) if isinstance(w,PixelButton) and w.text=='开始导出')
   start.invoke();start.invoke();heartbeat=[];a.after(10,lambda:heartbeat.append(True))
   deadline=time.perf_counter()+1
   while not heartbeat and time.perf_counter()<deadline:a.update();time.sleep(.005)
   self.assertTrue(heartbeat);self.assertEqual(start.state,'disabled')
   deadline=time.perf_counter()+15
   while dialog.winfo_exists() and time.perf_counter()<deadline:a.update();time.sleep(.005)
   self.assertFalse(dialog.winfo_exists());self.assertEqual(submitted.call_count,1)
 def test_painting_folder_refresh_sharing_and_before_preview_are_staged(self):
  import copy
  a=self.a;a.edit_textures();editor=a.texture_editor;folder=Path(self.temp.name)/'paint'
  original=copy.deepcopy(a.project);editor.start_painting(folder);a.update()
  self.assertTrue((folder/'UV_Model.json').exists());self.assertEqual(a.project,original)
  image=U.texture_image(editor.project,'head');image.paste((80,40,150,255),(0,0,*image.size));image.save(folder/'head.png')
  editor.reload_textures();self.assertTrue(editor.project['textures']['head']['png']);self.assertEqual(a.project,original)
  editor.compare_before(True);self.assertTrue(editor.before_mode);editor.compare_before(False)
  editor.single_view.set(True);editor.draw();self.assertEqual(len(editor.cells),1);editor.single_view.set(False);editor.draw();self.assertEqual(len(editor.cells),4)
  editor.set_shared('upperArmR',False);self.assertNotIn('upperArmR',editor.project.get('shared_textures',{}))
  editor.undo_texture();self.assertIn('upperArmR',editor.project['shared_textures'])
  editor.apply();self.assertTrue(a.project['assets3d']['textures']['head']['png']);a.undo();self.assertEqual(a.project,original)
  a.edit_model();editor=a.model_editor;editor.set_value('shoulder',1.2);editor.compare_before(True);editor.compare_before(False);editor.cancel()
  old_image=(folder/'head.png').read_bytes();a.project['model']={'head':{'size':1.2}};a.changed();a.edit_textures();editor=a.texture_editor;editor.start_painting(folder)
  self.assertEqual(editor.match_states['head'],'mapping');editor.adapt_painting()
  self.assertNotEqual(editor.workspace.folder,folder);self.assertEqual((folder/'head.png').read_bytes(),old_image)
  self.assertTrue(all(editor.workspace.compatible(editor.project,p) for p in U.PARTS));editor.cancel()
 def test_separate_png_link_refreshes_without_being_overwritten_by_workspace(self):
  a=self.a;a.edit_textures();editor=a.texture_editor;folder=Path(self.temp.name)/'paint';editor.start_painting(folder)
  path=Path(self.temp.name)/'head artwork.png';image=U.texture_image(editor.project,'head');image.paste((20,90,140,255),(0,0,*image.size));image.save(path)
  editor.replace_texture('head',path);self.assertEqual(editor.project['textures']['head']['provenance'],'unknown')
  (folder/'head.png').write_bytes(b'partial old file')
  image.paste((150,40,10,255),(0,0,*image.size));image.save(path)
  editor.watch_painting();editor.watch_painting()
  self.assertEqual(U.texture_image(editor.project,'head').getpixel((0,0)),(150,40,10,255))
  self.assertEqual(editor.match_states['head'],'updated');self.assertNotIn('assets3d',a.project);editor.cancel()

if __name__=='__main__':unittest.main()
