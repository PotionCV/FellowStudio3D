import tempfile,time,unittest
from pathlib import Path
import app,engine as E,uv_assets as U
from pixel_ui import PixelButton
class UITests(unittest.TestCase):
 def test_framework_categories_display_restoration_and_layer_order(self):
  import copy
  a=self.a;a.toggle_display_options();a.update();self.assertTrue(a.display_options.winfo_ismapped())
  old=copy.deepcopy(a.project['render']);a.outline.set(False);a.textures.set(False);a.display();a.undo()
  self.assertEqual(a.project['render'],old);self.assertEqual(a.outline.get(),old.get('outline',True));self.assertEqual(a.textures.get(),old.get('textures',True))
  a.project['render'].update(outline=False,textures=False,outline_color='#112233');a.sync()
  self.assertFalse(a.outline.get());self.assertFalse(a.textures.get());self.assertEqual(a.outline_color.get(),'#112233')
  a.add('wave');a.add('nod');a.select('layer',1);a.move_layer(-1)
  self.assertEqual([e['kind'] for e in a.project['layers']],['nod','wave']);self.assertEqual(a.stack.curselection(),(0,));self.assertEqual(a.layer_actions['上移'].state,'disabled')
  a.undo();self.assertEqual([e['kind'] for e in a.project['layers']],['wave','nod'])
  a.edit_model();e=a.model_editor;self.assertEqual(set(e.category_tabs),{'shape','hair','ears','tail','props'})
  for key in ('hair','ears','tail','props'):
   e.select_category(key);a.update();self.assertFalse(e.shape_shell.winfo_manager());self.assertFalse(e.link_check.winfo_manager());self.assertTrue(e.category_tabs[key].accent)
  e.select_category('shape');a.update();self.assertTrue(e.shape_shell.winfo_manager());e.select('armL');self.assertTrue(e.link_check.winfo_manager());e.cancel()

 def test_symmetric_shapes_hair_ears_and_pose_links_are_explicit(self):
  import copy,model_data as M,hair_assembly as HA,hair,attachment_editor as AE,attachments as A
  a=self.a;a.project['model']=M.normalize();before=copy.deepcopy(a.project);a.edit_model();e=a.model_editor
  e.select('armL');e.link.set(False);e.set_value('curve',2);e.set_value('upper',8);e.mirror_limb()
  self.assertEqual(e.draft['armR']['curve'],-2);self.assertEqual(e.draft['armR']['upper'],8)
  e.select_category('hair');left=HA.add(e,'sideL');right=HA.add(e,'sideR');HA.set_link(e,left,False);HA.set_value(e,left,'width',7)
  HA.set_link(e,left,True);self.assertEqual(hair.resolve(HA.items(e),right)['width'],7)
  e.select_category('ears');AE.add(e,'cat');source=e.attachment_id;opposite=source[:-1]+('R' if source.endswith('L') else 'L')
  e.draft['attachments']=[p for p in e.draft['attachments'] if p['id']!=opposite];AE.mirror(e)
  self.assertEqual(A.record(e.draft,source)['width'],A.record(e.draft,opposite)['width']);e.cancel();self.assertEqual(a.project,before)
  editor=a.edit_pose_animation();editor.select('armR');old=copy.deepcopy(editor.cards[0]['pose']['armL']);editor.set_pose(0,35)
  self.assertEqual(editor.cards[0]['pose']['armL'],old);editor.link_pose_pair(True);self.assertEqual(editor.cards[0]['pose']['armL'][0],-35)
  editor.set_pose(1,50);self.assertEqual(editor.cards[0]['pose']['armL'][1],-50);editor.cancel();self.assertEqual(a.project,before)

 def test_responsive_dropdown_keeps_actions_whole_and_has_no_overlap(self):
  import tkinter as tk
  from pixel_ui import FlowBar,PixelOption
  a=self.a;dialog=tk.Toplevel(a);dialog.ui_scale=a.ui_scale;dialog.ui_font=a.caption_font;dialog.caption_font=a.caption_font;dialog.geometry('360x240')
  bar=FlowBar(dialog,compact=True);bar.pack(fill='x');value=tk.StringVar(master=dialog,value='A very long resource name')
  option=PixelOption(bar,value,'A very long resource name','Short');option.pack(side='left',fill='x',expand=True)
  button=PixelButton(bar,text='添加',compact=True);button.pack(side='left');a.update()
  self.assertEqual(option.winfo_y(),button.winfo_y());self.assertGreater(option.winfo_width(),80)
  for width in (260,500,360):
   dialog.geometry(f'{width}x240');a.update();rects=[]
   for child in bar.winfo_children():
    rect=(child.winfo_x(),child.winfo_y(),child.winfo_x()+child.winfo_width(),child.winfo_y()+child.winfo_height())
    self.assertLessEqual(rect[2],bar.winfo_width()+1);self.assertLessEqual(rect[3],bar.winfo_height()+1)
    for other in rects:self.assertFalse(min(rect[2],other[2])>max(rect[0],other[0]) and min(rect[3],other[3])>max(rect[1],other[1]))
    rects.append(rect)
    if isinstance(child,PixelButton):
     for item in child.find_all():
      if child.type(item)=='text':self.assertNotIn('\n',child.itemcget(item,'text'))
  dialog.destroy()

 def test_retro_switch_is_saved_undoable_and_matches_display_group(self):
  a=self.a
  self.assertIs(a.render_flag_checks['retro_animation'].master,a.animation_effects)
  self.assertIsNot(a.animation_effects,a.render_flag_checks['lighting'].master)
  self.assertFalse(a.retro_animation.get());a.retro_animation.set(True);a.toggle_render_flag('retro_animation',a.retro_animation)
  self.assertTrue(a.current_display()['retro_animation']);a.display();self.assertTrue(a.project['render']['retro_animation'])
  a.autosave();self.assertTrue(E.load(a.state_path)['render']['retro_animation'])
  a.undo();a.undo();self.assertFalse(a.retro_animation.get())

 def test_hair_editor_bones_pose_cards_and_undo(self):
  import copy,hair,hair_editor,model_data as M,hair_controls,types
  a=self.a;a.project['model']=M.normalize();a.changed();before=copy.deepcopy(a.project)
  a.edit_model();editor=a.model_editor;editor.part='head';editor.hair_mode=True;editor.show_params();hair_editor.apply_style(editor,'pony')
  self.assertNotIn('hairstyle',a.project['model']);self.assertEqual(editor.draft['hairstyle']['style'],'pony');editor.apply();a.update()
  a.select('body','hair');a.update();self.assertNotIn('hair',a.project['physics'])
  deadline=time.perf_counter()+25
  while (a.active_project!=a.project or a.preview_incomplete) and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertEqual(a.active_project,a.project);a.render();a.update();self.assertTrue(a.part_buttons['hair'].winfo_ismapped())
  a.hair_channel='hair_back';a.show_params();a.render();x,y,size=a.cells[1];px,py=hair_controls.points(a,1)[1]
  start=types.SimpleNamespace(x=x+px*size/64,y=y+py*size/64);a.start_drag(start);self.assertIsNotNone(a.drag)
  a.move_drag(types.SimpleNamespace(x=start.x+25,y=start.y-10));a.end_drag(None);self.assertGreater(a.project['controls']['hair']['hair_back_middle_roll'],0)
  a.undo();self.assertFalse(a.project['controls'].get('hair'))
  editor=a.edit_pose_animation();editor.select('hair');editor.hair_channel='hair_back';editor.show_params();editor.set_pose(1,25)
  self.assertEqual(editor.cards[0]['pose']['hair_back'][1],25);editor.apply();a.update();self.assertEqual(a.project['base']['cards'][0]['pose']['hair_back'][1],25)

 def test_tail_tip_can_be_staged_and_applied(self):
  import tail_editor,attachments as A
  a=self.a;a.edit_model();editor=a.model_editor;editor.part='torso';tail_editor.add(editor);tail_editor.set_value(editor,'tip',.8)
  self.assertEqual(A.record(editor.draft,editor.tail_id)['tip'],.8);self.assertFalse(any(p.get('kind')=='tail' for p in a.project.get('model',{}).get('attachments',[])))
  editor.apply();a.update();self.assertEqual(a.project['model']['attachments'][0]['tip'],.8)

 def test_individual_hair_controls_link_reset_cancel_apply_and_undo(self):
  import copy,hair,hair_editor,model_data as M
  a=self.a;a.project['model']=M.normalize();hair.rebuild(a.project['model'],{'style':'twins'});a.changed();before=copy.deepcopy(a.project)
  a.edit_model();editor=a.model_editor;editor.part='head';editor.hair_mode=True;editor.hair_edit_scope='lock';editor.show_params();editor.hair_lock_details=True;editor.show_params()
  hair_editor.set_lock(editor,'ponyL','width',7.);hair_editor.set_lock(editor,'ponyL','x',-2.)
  self.assertEqual(editor.draft['hairstyle']['locks']['ponyR']['width'],7.);self.assertEqual(editor.draft['hairstyle']['locks']['ponyR']['x'],2.)
  editor.hair_link=False;hair_editor.set_lock(editor,'ponyL','width',5.);self.assertEqual(editor.draft['hairstyle']['locks']['ponyR']['width'],7.)
  hair_editor.mirror_lock(editor,'ponyL');self.assertEqual(editor.draft['hairstyle']['locks']['ponyR']['width'],5.);self.assertEqual(editor.draft['hairstyle']['locks']['ponyR']['x'],2.)
  hair_editor.edit_twins(editor);self.assertEqual(editor.hair_section,'ponyL');self.assertTrue(editor.hair_link)
  editor.hair_link=False
  hair_editor.reset_lock(editor,'ponyL');self.assertNotIn('ponyL',editor.draft['hairstyle']['locks']);self.assertIn('ponyR',editor.draft['hairstyle']['locks']);editor.cancel();self.assertEqual(a.project,before)
  a.edit_model();editor=a.model_editor;hair_editor.set_lock(editor,'ponyL','tip',.8);editor.apply();a.update();self.assertEqual(a.project['model']['hairstyle']['locks']['ponyL']['tip'],.8)
  a.undo();self.assertEqual(a.project,before)

 def test_hair_free_parts_caps_and_extra_bones_are_staged(self):
  import copy,hair,hair_assembly as HA,model_data as M,hair_controls
  a=self.a;a.project['model']=M.normalize();a.changed();before=copy.deepcopy(a.project)
  a.edit_model();editor=a.model_editor;editor.part='head';editor.hair_mode=True;editor.show_params();cap=HA.add(editor,'cap');first=HA.add(editor,'lock');second=HA.duplicate(editor,first,True)
  HA.set_value(editor,cap,'shape','box');HA.set_value(editor,cap,'crown_flat',.7);HA.set_value(editor,first,'tip',.6)
  self.assertEqual(len(editor.draft['attachments']),3);self.assertEqual(a.project,before);editor.hair_edit_scope='cap';editor.show_params();editor.hair_cap_details=True;editor.show_params();editor.apply();a.update();a.select('body','hair');a.changed()
  deadline=time.perf_counter()+25
  while (a.active_project!=a.project or a.preview_incomplete) and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertEqual(a.active_project,a.project);self.assertEqual(len(hair_controls.active(a.project['model'])),2)
  a.hair_channel=hair.channel(hair.resolve(a.project['model']['attachments'],second));a.show_params();self.assertEqual(len(hair_controls.points(a,0)),4)
  pose=a.edit_pose_animation();pose.select('hair');pose.hair_channel=a.hair_channel;pose.show_params();pose.set_pose(1,25);self.assertEqual(pose.cards[0]['pose'][a.hair_channel][1],25);pose.cancel()

 def test_hair_components_replace_template_hierarchy_and_ears_have_own_page(self):
  import copy,hair,hair_editor,hair_assembly as HA,attachment_editor as AE,model_data as M,i18n
  def texts(widget):
   result=[getattr(widget,'text','')]
   try:result.append(widget.cget('text'))
   except Exception:pass
   for child in widget.winfo_children():result.extend(texts(child))
   return [i18n.tr(' '.join(str(v).split())) for v in result]
  a=self.a;a.project['model']=M.normalize();hair.rebuild(a.project['model'],{'style':'twins'});a.changed();before=copy.deepcopy(a.project)
  a.edit_model();editor=a.model_editor;editor.part='head';editor.hair_mode=True;editor.show_params();a.update()
  labels=texts(editor.params);self.assertNotIn(i18n.tr('双马尾'),labels);self.assertNotIn(i18n.tr('整体发型'),labels);self.assertIn(i18n.tr('已添加部件'),labels);self.assertFalse(editor.link_check.winfo_manager())
  self.assertIn(i18n.tr('头发主体'),editor.hair_component_list.get(0,'end'));self.assertEqual(a.project,before)
  left=HA.add(editor,'sideL');right=HA.add(editor,'sideR');self.assertEqual(hair.role(hair.resolve(HA.items(editor),left)),'sideL');self.assertEqual(hair.role(hair.resolve(HA.items(editor),right)),'sideR')
  editor.hair_mode=False;editor.ear_mode=True;editor.show_params();AE.add(editor,'human');editor.show_params();a.update()
  labels=texts(editor.params);self.assertNotIn(i18n.tr('基础形状'),labels);self.assertNotIn(i18n.tr('头发部件'),labels);self.assertIn(i18n.tr('收起耳朵参数'),labels)
  editor.ear_mode=False;editor.show_params();labels=texts(editor.params);self.assertIn(i18n.tr('基础形状'),labels);self.assertNotIn(i18n.tr('编辑耳朵参数'),labels);self.assertNotIn(i18n.tr('收起耳朵参数'),labels)
  editor.apply();a.update();self.assertEqual(len([p for p in a.project['model']['attachments'] if p.get('kind')=='ear']),2);a.undo();self.assertEqual(a.project,before)

 def test_canvas_and_lighting_have_separate_entries_and_display_switches(self):
  from pixel_ui import PixelCheck
  a=self.a;canvas=a.edit_render_options();light=a.edit_render_options('lighting');a.update()
  self.assertIsNot(canvas,light);self.assertTrue(canvas.canvas_body.winfo_ismapped());self.assertFalse(canvas.light_body.winfo_ismapped())
  self.assertFalse(light.canvas_body.winfo_ismapped());self.assertTrue(light.light_body.winfo_ismapped())
  group=a.render_flag_checks['lighting'].master
  self.assertTrue(any(isinstance(w,PixelCheck) and w.text=='显示贴图' for w in group.winfo_children()))
  self.assertIs(a.render_flag_checks['self_shadow'].master,group)
  self.assertFalse(a.project['render'].get('lighting',False));a.light_enabled.set(True);a.toggle_render_flag('lighting',a.light_enabled)
  self.assertTrue(a.project['render']['lighting']);a.undo();self.assertFalse(a.light_enabled.get())
  light.set_option('light_angle',45);a.display();self.assertEqual(a.project['render']['light_angle'],45)
  canvas.destroy();light.destroy()

 def test_canvas_and_lighting_settings_preview_handles_undo_and_save(self):
  import copy,render_options as O
  from types import SimpleNamespace
  a=self.a;before=copy.deepcopy(a.project);d=a.edit_render_options();self.assertIs(a.edit_render_options(),d)
  d.width.set('96');d.height.set('128');self.assertTrue(d.apply_canvas());d.set_option('lighting',True);d.set_option('light_angle',45);d.set_option('shadow_color','#443355')
  self.assertEqual(O.size(a.project['render']),(96,128));a.display();self.assertTrue(a.project['render']['lighting'])
  d.width.set('999');self.assertFalse(d.apply_canvas());self.assertEqual(O.size(a.project['render']),(96,128));d.destroy()
  deadline=time.perf_counter()+25
  while (a.active_project!=a.project or a.preview_incomplete) and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertEqual(a.active_project,a.project);self.assertTrue(all(im.shape==(128,96,4) for im in a.raw_images.values()))
  a.select('body','armR');a.render();x,y,size=a.cells[0];j=O.joints(a.view_pose(0),a.project['render']);px,py=j['armR']['tip'];event=SimpleNamespace(x=x+px*size/96,y=y+py*size/96)
  a.start_drag(event);self.assertIsNotNone(a.drag);self.assertEqual(a.drag[1],'armR');a.move_drag(SimpleNamespace(x=event.x+4,y=event.y-4));a.end_drag(None)
  a.edit_model();editor=a.model_editor;a.update();editor.single_view.set(True);editor.draw();self.assertEqual(editor.photos[next(iter(editor.photos))].height()/editor.photos[next(iter(editor.photos))].width(),128/96);editor.cancel()
  a.autosave();saved=E.load(a.state_path);self.assertEqual(saved['render'],a.project['render']);self.assertEqual(saved['render']['shadow_color'],'#443355')
  a.undo();self.assertEqual(O.size(a.project['render']),(96,128))

 def test_uv_clipboard_replacement_survives_link_refresh_and_can_resume_painting(self):
  import copy,image_clipboard as C
  from unittest.mock import patch
  from PIL import Image
  a=self.a;a.edit_textures();e=a.texture_editor;folder=Path(self.temp.name)/'painting';e.start_painting(folder)
  old=U.texture_image(e.project,'head');linked=Path(self.temp.name)/'old-head.png';old.save(linked);e.replace_texture('head',linked)
  image=old.copy();image.putpixel((0,0),(12,34,56,78));d=e.inspect_uv('head');a.update()
  with patch.object(C,'read_image',return_value=image):self.assertTrue(d.paste_texture())
  d.apply();e.watch_linked_files(force=True);e.reload_textures();self.assertEqual(U.texture_image(e.project,'head').tobytes(),image.tobytes())
  e.start_painting(folder);self.assertNotEqual(e.workspace.folder,folder)
  self.assertEqual(Image.open(e.workspace.folder/'head.png').convert('RGBA').tobytes(),image.tobytes())
  self.assertNotIn('painting_override',e.project['textures']['head']);e.apply()
  saved=Path(self.temp.name)/'pasted-project.json';E.save(a.project,saved);self.assertEqual(U.texture_image(E.load(saved)['assets3d'],'head').tobytes(),image.tobytes())
  a.undo();self.assertNotIn('assets3d',a.project)

 def test_uv_single_texture_save_copy_paste_cancel_apply_and_undo(self):
  import copy,image_clipboard as C
  from unittest.mock import patch
  from PIL import Image
  a=self.a;a.edit_textures();e=a.texture_editor;before=copy.deepcopy(e.project);d=e.inspect_uv('head');a.update()
  original=U.texture_image(e.project,'head');image=original.copy();image.putpixel((0,0),(12,34,56,0));image.putpixel((1,1),(78,90,12,123))
  with patch.object(C,'read_image',return_value=image),patch.object(C,'copy_image') as copied:
   d.canvas.focus_force();a.update();d.event_generate('<Control-v>');a.update();self.assertTrue(d.texture_dirty);self.assertEqual(e.project,before)
   self.assertTrue(d.copy_texture());self.assertEqual(copied.call_args.args[0].tobytes(),image.tobytes())
   saved=Path(self.temp.name)/'single.png';self.assertTrue(d.save_texture(saved));self.assertEqual(Image.open(saved).convert('RGBA').tobytes(),image.tobytes())
   self.assertEqual(U.texture_match(d.current_bundle(),'head',saved),'matched')
   d.undo();self.assertEqual(U.texture_image(d.current_bundle(),'head').tobytes(),original.tobytes())
   self.assertTrue(d.paste_texture());d.destroy();self.assertEqual(e.project,before)
   d=e.inspect_uv('head');a.update();d.transfer_buttons['paste'].invoke();d.apply()
  self.assertEqual(U.texture_image(e.project,'head').tobytes(),image.tobytes());self.assertTrue(e.project['textures']['head']['painting_override'])
  e.undo_texture();self.assertEqual(e.project,before)
  d=e.inspect_uv('head');a.update()
  with patch.object(C,'read_image',return_value=Image.new('RGBA',(1,1))),patch.object(d,'report_error') as error:
   self.assertFalse(d.paste_texture());self.assertEqual(len(d.history),0);self.assertEqual(e.project,before);error.assert_called_once()
  d.destroy();e.cancel();self.assertNotIn('assets3d',a.project)

 def test_tail_softness_controls_reset_and_undo(self):
  import copy,tails as T,model_data as M
  a=self.a;a.project['model']=M.normalize();T.add(a.project['model']);a.changed();a.select('body','tail');a.update()
  def labels(widget):
   result=[]
   try:result.append(widget.cget('text'))
   except Exception:pass
   for child in widget.winfo_children():result.extend(labels(child))
   return result
  import i18n
  for text in ('尾根松软','尾中松软','尾尖松软','回弹'):self.assertIn(i18n.tr(text),[' '.join(value.split()) for value in labels(a.params)])
  a.project['physics']['tail']=dict(root=.2,middle=.5,tip=.7,bounce=.4);before=copy.deepcopy(a.project)
  a.reset_part('tail');self.assertEqual(a.project['physics'].get('tail',{}),{});a.undo();self.assertEqual(a.project,before)

 def test_tail_handles_wait_for_matching_model_when_switching_characters(self):
  import model_data as M,tails as T
  a=self.a;a.project['model']=M.normalize({'structure':'plush'});T.add(a.project['model']);a.changed()
  # Current preview can still be the old humanoid while the new clip queues.
  a.seq=[E.norm(E.F.POSES['stand'])];a.frame=0;a.select('body','tail')
  self.assertEqual(a.tail_points(0),[])

 def test_tail_controllers_drag_and_pose_cards_work_with_undo(self):
  import copy,types,tails as T,model_data as M
  a=self.a;a.project['model']=M.normalize();T.add(a.project['model']);a.changed();a.select('body','tail')
  deadline=time.perf_counter()+15
  while (a.active_project!=a.project or a.preview_incomplete) and time.perf_counter()<deadline:a.update();time.sleep(.01)
  a.render();a.update();self.assertTrue(a.part_buttons['tail'].winfo_ismapped());before=copy.deepcopy(a.project)
  x,y,size=a.cells[1];px,py=a.tail_points(1)[1];start=types.SimpleNamespace(x=x+px*size/64,y=y+py*size/64)
  a.start_drag(start);self.assertIsNotNone(a.drag);self.assertEqual(a.selected_tail_bone,'尾中')
  a.move_drag(types.SimpleNamespace(x=start.x+35,y=start.y-15));a.end_drag(None);a.update()
  self.assertGreater(a.project['controls']['tail']['middle_roll'],0);self.assertGreater(a.project['controls']['tail']['middle_pitch'],0)
  a.undo();self.assertEqual(a.project,before)
  editor=a.edit_pose_animation();editor.select('tail');editor.set_pose(1,35)
  self.assertEqual(editor.cards[editor.card_index]['pose']['tail'][1],35);editor.apply();a.update()
  self.assertEqual(a.project['base']['cards'][0]['pose']['tail'][1],35)

 def test_sequence_window_has_fixed_rows_and_visible_footer_at_normal_scaling(self):
  import i18n
  a=self.a;dialog=a.arrange_actions();a.update()
  deadline=time.perf_counter()+.4
  while time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertGreaterEqual(dialog.winfo_width(),920);self.assertGreaterEqual(dialog.winfo_height(),660)
  self.assertGreaterEqual(dialog.sequence_panels[1].winfo_width(),dialog.winfo_width()*.3)
  def descendants(w):return [child for c in w.winfo_children() for child in (c,*descendants(c))]
  buttons=[w for w in descendants(dialog) if isinstance(w,PixelButton)]
  for button in buttons:
   text=[button.itemcget(item,'text') for item in button.find_all() if button.type(item)=='text']
   self.assertNotIn('\n',''.join(text),button.text)
   self.assertLess(button.winfo_rooty()+button.winfo_height(),dialog.winfo_rooty()+dialog.winfo_height()+1)
  dialog.destroy()

 def test_kumamon_library_keeps_original_png_and_animation_save_is_separate(self):
  import copy,json,shutil,motion_resources as MR,model_data as M
  from unittest.mock import patch
  folder=Path(self.temp.name)/'models';folder.mkdir();source=E.ROOT/'user_data/models/KumamonBag.json'
  # The local personal model is deliberately absent in clean public builds.
  if source.is_file():shutil.copy2(source,folder/source.name)
  else:M.save(M.normalize(),folder/'KumamonBag.json')
  a=self.a;original=copy.deepcopy(a.project);browser=a.load_motion_resource();browser.change_kind('models');browser.query.set('熊本熊')
  self.assertEqual(len(browser.filtered),1);browser.choose(browser.filtered[0]);self.wait_library(browser)
  resource=M.load_resource(folder/'KumamonBag.json');self.assertEqual(browser.candidate['assets3d'],resource.get('assets3d',__import__('rounded_scene').assets(browser.candidate)))
  browser.apply();a.update();a.add('wave');a.add('tail');destination=Path(self.temp.name)/'motions/MyMotion.json'
  with patch('studio_ui.filedialog.asksaveasfilename',return_value=str(destination)):a.save_motion_resource()
  recipe=E.load(destination);self.assertEqual(len(recipe['layers']),2);self.assertNotIn('model',recipe);self.assertNotIn('assets3d',recipe)
  browser=a.load_motion_resource();browser.query.set('MyMotion');self.assertEqual(len(browser.filtered),1);browser.cancel()

 def test_painting_resume_is_bound_to_artwork_and_survives_preferences_reload(self):
  import copy,json
  from unittest.mock import patch
  from paint_workspace import painting_key
  a=self.a;first=copy.deepcopy(a.project);folder1=Path(self.temp.name)/'first-paint'
  a.edit_textures();e=a.texture_editor;e.start_painting(folder1);e.cancel()
  second=copy.deepcopy(first);second['assets3d']=__import__('rounded_scene').assets(second)
  im=U.texture_image(second['assets3d'],'head');im.putpixel((1,1),(220,50,80,255));second['assets3d']['textures']['head']['png']=U.encode(im)
  a.project=second;a.changed();a.edit_textures();e=a.texture_editor
  self.assertIsNone(e.last_painting_folder());self.assertNotIn(str(folder1),e.paint_message.get())
  with patch('texture_editor.filedialog.askdirectory',return_value='') as picker:e.start_painting();picker.assert_called_once()
  self.assertIsNone(e.workspace);self.assertEqual(U.texture_image(e.project,'head').tobytes(),im.tobytes())
  folder2=Path(self.temp.name)/'second-paint';e.start_painting(folder2);e.apply()
  second=copy.deepcopy(a.project);saved=json.loads(a.preferences_path.read_text());self.assertEqual(saved['painting_bindings'][painting_key(second)],str(folder2.resolve()))
  a.paint_bindings=saved['painting_bindings'];a.project=first;a.changed();a.edit_textures();e=a.texture_editor
  self.assertEqual(e.last_painting_folder(),folder1);e.cancel()
  a.project=second;a.changed();a.edit_textures();e=a.texture_editor;self.assertEqual(e.last_painting_folder(),folder2);e.cancel()

 def wait_library(self,browser):
  deadline=time.perf_counter()+25
  while browser.apply_button.state=='disabled' and time.perf_counter()<deadline:self.a.update();time.sleep(.01)
  self.assertEqual(browser.apply_button.state,'normal',browser.status.get())

 def test_resource_browser_search_combine_cancel_apply_undo_and_preview(self):
  import copy,resource_library as L,numpy as np
  a=self.a;before=copy.deepcopy(a.project);browser=a.load_motion_resource();a.update()
  browser.query.set('游泳');self.assertEqual(len(browser.filtered),4)
  browser.query.set('not a resource');self.assertEqual(len(browser.filtered),0)
  browser.query.set('');browser.change_kind('models');browser.query.set('CustomModel');browser.choose(browser.filtered[0])
  browser.change_kind('motions');browser.query.set('ShyGreeting');browser.choose(browser.filtered[0])
  self.assertEqual(a.project,before);self.assertEqual(browser.apply_button.state,'disabled');browser.apply();self.assertTrue(browser.winfo_exists())
  heartbeat=[];a.after(10,lambda:heartbeat.append(True));self.wait_library(browser)
  self.assertTrue(heartbeat);self.assertEqual(browser.candidate['base']['kind'],'poseclip');self.assertTrue(browser.candidate['assets3d']['textures']['head']['png'])
  expected=E.poses(browser.candidate)
  for view,cam in enumerate(((0,0),(90,0),(45,0),(45,30))):np.testing.assert_array_equal(browser.raw[view,0],E.rgba(expected[0],browser.candidate.get('render'),cam))
  candidate=copy.deepcopy(browser.candidate);browser.cancel();self.assertEqual(a.project,before)
  browser=a.load_motion_resource();browser.choose(next(r for r in browser.resources if r.key=='CustomModel'));browser.reset_selection()
  self.assertEqual(browser.candidate,before)
  browser.choose(next(r for r in browser.resources if r.key=='CustomModel'));self.wait_library(browser);candidate=copy.deepcopy(browser.candidate);browser.apply();a.update()
  self.assertEqual(a.project,candidate);a.undo();self.assertEqual(a.project,before)

 def test_model_library_stays_inside_model_draft_and_external_files_are_staged(self):
  import copy
  from unittest.mock import patch
  a=self.a;before=copy.deepcopy(a.project);a.edit_model();editor=a.model_editor;editor.set_value('height',1.2);draft=copy.deepcopy(editor.draft)
  browser=editor.browse_models();a.update();self.assertEqual(set(browser.tabs),{'models'});self.assertEqual(browser.candidate['model'],draft)
  browser.query.set('CustomModel');browser.choose(browser.filtered[0]);self.wait_library(browser);browser.apply();a.update()
  self.assertIs(a.model_editor,editor);self.assertEqual(a.project,before);self.assertNotEqual(editor.draft,draft);self.assertTrue(editor.replace_assets)
  self.assertIs(editor.grab_current(),editor);editor.cancel();self.assertEqual(a.project,before)
  browser=a.load_motion_resource()
  with patch('resource_browser.filedialog.askopenfilename',return_value=str(E.ROOT/'examples/motions/game/Jump.json')):browser.load_file()
  self.assertEqual(browser.candidate['base']['kind'],'jump');self.assertEqual(a.project,before)
  candidate=copy.deepcopy(browser.candidate);broken=Path(self.temp.name)/'broken.json';invalid=copy.deepcopy(candidate);invalid['seconds']='2';E.save(invalid,broken)
  with patch('resource_browser.filedialog.askopenfilename',return_value=str(broken)),patch('resource_browser.messagebox.showerror') as error:
   browser.load_file();error.assert_called_once()
  self.assertEqual(browser.candidate,candidate);browser.cancel()



 def test_hand_prop_editor_stages_transfer_and_uv_resources_with_undo(self):
  import copy,hand_prop_editor as HP
  a=self.a;before=copy.deepcopy(a.project);a.edit_model();e=a.model_editor;e.select('armR');a.update()
  e.select_category('props')
  self.assertTrue(e.prop_mode);HP.add(e,'sword');a.update()
  self.assertEqual(a.project,before);HP.set_value(e,'pitch',-75);HP.transfer(e);a.update()
  self.assertEqual(e.part,'armL');self.assertEqual(e.draft['attachments'][0]['parent'],'armL')
  e.apply();a.update();self.assertEqual(a.project['model']['attachments'][0]['pitch'],-75)
  a.edit_textures();uv=a.texture_editor;a.update();self.assertIn('prop1',uv.project['textures']);self.assertEqual(len(uv.card_photos),11);uv.cancel()
  a.edit_model();e=a.model_editor;e.select('armL');e.select_category('props');HP.remove(e);e.cancel();self.assertEqual(len(a.project['model']['attachments']),1)
  a.undo();self.assertEqual(a.project,before)

 def test_pose_card_source_capture_and_four_view_ik_edit_only_selected_card(self):
  import copy,types
  a=self.a;a.project=E.new_project('walk');a.project['controls']={'head':{'turn':22}};a.project['seconds']=.5;a.project['fps']=8;a.changed()
  editor=a.edit_pose_animation();a.update();editor.capture_frame.set('3');editor.capture_card()
  np_pose=editor.cards[-1]['pose'];self.assertAlmostEqual(np_pose['head_yaw'],22)
  original=copy.deepcopy(editor.cards[0]);editor.select('armR');deadline=time.perf_counter()+10
  while getattr(editor,'accepted_revision',None)!=editor.revision and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertEqual(editor.accepted_revision,editor.revision);editor.draw()
  x,y,size=editor.cells[0];p=editor.seq[0];tip=E.R.joints(p)['armR']['tip']
  start=types.SimpleNamespace(x=x+tip[0]*size/64,y=y+tip[1]*size/64)
  before=copy.deepcopy(editor.cards[-1]['pose']['armR']);editor.pick(start)
  self.assertIsNotNone(editor.drag_pose);editor.move_pose(types.SimpleNamespace(x=start.x+size/12,y=start.y-size/10));editor.end_pose(None)
  self.assertNotEqual(editor.cards[-1]['pose']['armR'],before);self.assertEqual(editor.cards[0],original)
  editor.cancel()

 def test_pose_cards_editor_is_staged_editable_playable_and_undoable(self):
  import copy
  a=self.a;original=copy.deepcopy(a.project);editor=a.edit_pose_animation();a.update()
  self.assertEqual(a.project,original);self.assertEqual(len(editor.cards),2)
  editor.select('armR');editor.set_pose(2,65);editor.duplicate_card();editor.mirror_card();editor.move_card(-1)
  self.assertEqual(len(editor.cards),3);self.assertEqual(editor.cards[0]['pose']['armL'][2],65)
  editor.set_timing('hold',1.);editor.duration.set('1.0');editor.mode.set('播放一次');editor.toggle_play()
  heart=[];a.after(10,lambda:heart.append(True));deadline=time.perf_counter()+15
  while (not editor.raw or editor.queued_play) and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertTrue(heart);self.assertTrue(editor.raw);self.assertFalse(editor.queued_play)
  self.assertEqual(a.project,original);editor.apply();a.update()
  self.assertEqual(a.project['base']['kind'],'poseclip');self.assertEqual(a.project['playback'],'once');self.assertEqual(len(a.project['base']['cards']),3)
  a.project['layers']=[E.entry('nod')];a.project['controls']={'head':{'turn':22}};saved=copy.deepcopy(a.project)
  editor=a.edit_pose_animation();editor.capture_card();self.assertEqual(editor.cards[-1]['pose']['head_yaw'],0)
  editor.set_timing('ease','snappy');editor.cancel();self.assertEqual(a.project,saved)
  a.project['layers']=[];a.undo();self.assertEqual(a.project,original)

 def test_directional_export_uses_existing_dialog_and_background_worker(self):
  import tkinter as tk,json
  from pixel_ui import PixelOption,PixelCheck,PixelEntry
  a=self.a;a.export();a.update();dialog=next(w for w in a.winfo_children() if isinstance(w,tk.Toplevel))
  def children(widget):return [w for child in widget.winfo_children() for w in [child]+children(child)]
  widgets=children(dialog);choice=next(w for w in widgets if isinstance(w,PixelOption) and '八方向（水平）' in w.values)
  choice.pick('八方向（水平）');choice.pick('正面');a.update()
  self.assertTrue(any(isinstance(w,PixelCheck) and w.text=='PNG 横向条带 · 透明背景' for w in widgets))
  choice.pick('四方向（水平）');a.update()
  self.assertTrue(any(isinstance(w,PixelCheck) and w.text=='PNG 方向图集 · 透明背景' for w in widgets))
  entries=[w.field for w in widgets if isinstance(w,PixelEntry)];entries[0].delete(0,'end');entries[0].insert(0,self.temp.name);entries[1].delete(0,'end');entries[1].insert(0,'Directions')
  start=next(w for w in widgets if isinstance(w,PixelButton) and w.text=='开始导出');start.invoke();self.assertEqual(start.state,'disabled')
  heartbeat=[];a.after(10,lambda:heartbeat.append(True));deadline=time.perf_counter()+15
  while dialog.winfo_exists() and time.perf_counter()<deadline:a.update();time.sleep(.005)
  self.assertTrue(heartbeat);self.assertFalse(dialog.winfo_exists())
  data=json.loads((Path(self.temp.name)/'Directions_atlas.json').read_text());self.assertEqual(len(data['directions']),4)
  self.assertTrue((Path(self.temp.name)/'Directions_atlas.png').is_file())

 def test_tail_editor_is_staged_with_dynamic_uv_and_undo(self):
  import copy,tail_editor as TE,attachment_editor as AE
  a=self.a;before=copy.deepcopy(a.project);a.edit_model();e=a.model_editor;e.select('torso');TE.add(e,'fluffy_tail');a.update()
  self.assertEqual(a.project,before);self.assertEqual(e.tail_id,'tail1');TE.set_value(e,'wag',-30);TE.set_value(e,'curl',-25)
  e.select('head');AE.add(e,'cat');a.update();self.assertEqual(len(e.draft['attachments']),3)
  e.select('torso');e.apply();a.update();self.assertEqual(a.project['model']['attachments'][0]['wag'],-30)
  a.edit_textures();uv=a.texture_editor;a.update();self.assertIn('tail1',uv.project['textures']);self.assertEqual(len(uv.card_photos),13)
  panel=uv.inspect_uv('tail1');a.update();self.assertEqual(panel.part,'tail1');panel.destroy();uv.cancel()
  a.edit_model();e=a.model_editor;e.select_category('tail');TE.remove(e);self.assertEqual(len(e.draft['attachments']),2);e.cancel()
  self.assertEqual(len(a.project['model']['attachments']),3);a.undo();self.assertEqual(a.project,before)
  import plush_editor as PE
  a.edit_model();e=a.model_editor;PE.change(e,'plush');TE.add(e,'bob_tail');e.apply();a.update()
  a.edit_textures();uv=a.texture_editor;a.update();self.assertIn('tail1',uv.project['textures']);self.assertEqual(len(uv.card_photos),10);uv.cancel()
  a.undo();self.assertEqual(a.project,before)

 def test_swim_hover_use_existing_base_layer_and_style_controls(self):
  from pixel_ui import PixelOption,PixelScale
  import copy
  a=self.a;model=copy.deepcopy(a.project.get('model'));a.change_base('游泳');a.update()
  self.assertEqual(a.project['base']['kind'],'swim');self.assertEqual(a.project.get('model'),model)
  self.assertEqual(a.project['playback'],'loop')
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '自由泳' in w.values)
  option.pick('自由泳');a.update();self.assertEqual(a.project['base']['style'],'crawl')
  a.add('swim');a.update()
  option=next(w for w in a.params.winfo_children() if isinstance(w,PixelOption) and '踩水' in w.values)
  option.pick('踩水');a.update();self.assertEqual(a.project['layers'][-1]['style'],'tread')
  a.change_base('悬浮');a.update();self.assertEqual(a.project['base']['kind'],'hover')
  scale=next(w for w in a.params.winfo_children() if isinstance(w,PixelScale) and w.lo==0 and w.hi==14)
  scale.command(9);self.assertEqual(a.project['base']['params']['height'],9)
  a.undo();self.assertEqual(a.project['base']['kind'],'swim')

 def test_action_sequence_cancel_reorder_apply_and_undo(self):
  import copy
  a=self.a;original=copy.deepcopy(a.project);dialog=a.arrange_actions();a.update()
  self.assertEqual(a.project,original);dialog.destroy()
  dialog=a.arrange_actions();a.update();dialog.step_list.selection_clear(0,'end');dialog.step_list.selection_set(1);dialog.move_step(-1)
  self.assertEqual(dialog.steps[:2],['punchL','punchR']);dialog.apply_sequence();a.update()
  self.assertEqual(len(a.project['layers']),3);self.assertEqual(a.project['layers'][0]['side'],'left')
  self.assertEqual(a.project['playback'],'once');a.undo();self.assertEqual(a.project,original)

 def test_resume_last_painting_without_picker_and_switch_explicitly(self):
  from unittest.mock import patch
  import copy
  a=self.a;original=copy.deepcopy(a.project);folder=Path(self.temp.name)/'paint'
  a.edit_textures();e=a.texture_editor;e.start_painting(folder);e.cancel()
  a.edit_textures();e=a.texture_editor;a.update()
  self.assertIn(str(folder),e.paint_message.get());self.assertIsNone(e.workspace)
  # Opening the editor alone must not import last folder's artwork.
  self.assertEqual(a.project,original)
  with patch('texture_editor.filedialog.askdirectory') as picker,patch.object(e,'open_painting_folder') as opened:
   e.start_painting();picker.assert_not_called();opened.assert_called_once()
  self.assertEqual(e.workspace.folder,folder);e.cancel()
  a.project['model']={'head':{'size':1.2}};a.changed();a.edit_textures();e=a.texture_editor
  with patch('texture_editor.filedialog.askdirectory') as picker,patch.object(e,'open_painting_folder'):
   e.start_painting();picker.assert_not_called()
  self.assertEqual(e.match_states['head'],'mapping')
  other=Path(self.temp.name)/'other'
  with patch('texture_editor.filedialog.askdirectory',return_value=str(other)) as picker,patch.object(e,'open_painting_folder'):
   e.start_painting(reuse_last=False);picker.assert_called_once()
  self.assertEqual(e.workspace.folder,other);e.cancel()
  (other/'UV_Model.json').unlink();a.edit_textures();e=a.texture_editor
  with patch('texture_editor.filedialog.askdirectory',return_value='') as picker:
   e.start_painting();picker.assert_called_once()
  self.assertIsNone(e.workspace);e.cancel()

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
  browser=a.load_motion_resource()
  with patch('resource_browser.filedialog.askopenfilename',return_value=str(E.ROOT/'examples/motions/game/Jump.json')):browser.load_file()
  deadline=time.perf_counter()+20
  while browser.apply_button.state=='disabled' and time.perf_counter()<deadline:a.update();time.sleep(.01)
  self.assertEqual(browser.apply_button.state,'normal');browser.apply();a.update()
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
  self.assertTrue(all(str(w.cget('font')) in (str(e.ui_font),str(e.caption_font)) for w in labels));e.cancel();a.edit_model();a.update();e=a.model_editor
  self.assertTrue(all(str(w.cget('font')) in (str(e.ui_font),str(e.caption_font)) for w in children(e) if isinstance(w,Label)));e.cancel()
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
