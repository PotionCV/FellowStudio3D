import importlib,json,tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
import app,engine as E
from pixel_ui import PixelButton,PixelCheck,PixelEntry

class ExportPreferencesTests(unittest.TestCase):
 def test_session_options_and_overwrite_confirmation(self):
  import studio_ui as ui
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';prefs=Path(td)/'prefs.json';p=E.new_project();p['seconds']=.2;E.save(p,state);a=app.App(state=state,preferences=prefs)
   def children(w):return [c for child in w.winfo_children() for c in [child]+children(child)]
   try:
    d=a.export();a.update();fields=d.export_fields;fields['scale'].set('4x');fields['view'].set('四方向（水平）');fields['create_folder'].set(True);fields['formats']['gif'].set(True);d.destroy()
    d=a.export();a.update();fields=d.export_fields;self.assertEqual(fields['scale'].get(),'4x');self.assertEqual(fields['view'].get(),'四方向（水平）');self.assertTrue(fields['create_folder'].get());self.assertTrue(fields['formats']['gif'].get())
    self.assertIs(a.export(),d);fields['scale'].set('1x');fields['view'].set('正面');fields['create_folder'].set(False);fields['directory'].set(td);fields['name'].set('Repeat')
    for key,var in fields['formats'].items():var.set(key=='png')
    E.export(p,td,'Repeat',formats=['png'],create_folder=False);target=Path(td)/'Repeat_00.png';target.write_bytes(b'keep original')
    start=next(w for w in children(d) if isinstance(w,PixelButton) and w.text=='开始导出')
    with patch.object(ui.messagebox,'askyesno',return_value=False) as question:
     start.invoke();deadline=time.perf_counter()+20
     while start.state=='disabled' and time.perf_counter()<deadline:a.update();time.sleep(.01)
     question.assert_called_once();self.assertEqual(target.read_bytes(),b'keep original');self.assertTrue(d.winfo_exists())
    with patch.object(ui.messagebox,'askyesno',return_value=True) as question:
     start.invoke();deadline=time.perf_counter()+20
     while d.winfo_exists() and time.perf_counter()<deadline:a.update();time.sleep(.01)
     question.assert_called_once();self.assertFalse(d.winfo_exists());self.assertNotEqual(target.read_bytes(),b'keep original')
    a.save_preferences();self.assertNotIn('export_session',json.loads(prefs.read_text()))
   finally:a.close()

 def test_default_scale_export_location_and_remembered_path(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';prefs=Path(td)/'prefs.json';p=E.new_project();p['seconds']=.2;E.save(p,state)
   a=app.App(state=state,preferences=prefs)
   ui=importlib.import_module('studio_ui') if (E.ROOT/'studio_ui.py').exists() else app
   def children(w):return [c for child in w.winfo_children() for c in [child]+children(child)]
   try:
    self.assertEqual(a.ui_scale,1.5);a.export();a.update()
    d=next(w for w in a.winfo_children() if isinstance(w,ui.tk.Toplevel));all_widgets=children(d)
    entries=[w.field for w in all_widgets if isinstance(w,PixelEntry)]
    self.assertEqual(entries[0].get(),str(E.ROOT))
    self.assertFalse(next(w for w in all_widgets if isinstance(w,PixelCheck) and w.text=='创建同名子文件夹').var.get())
    chosen=Path(td)/'Saved exports';chosen.mkdir()
    with patch.object(ui.filedialog,'askdirectory',return_value=str(chosen)) as browse:
     next(w for w in all_widgets if isinstance(w,PixelButton) and w.text=='选择…').invoke()
     self.assertEqual(browse.call_args.kwargs['initialdir'],str(E.ROOT))
    d.destroy();self.assertEqual(json.loads(prefs.read_text())['export_directory'],str(chosen))
    a.export();a.update();d=next(w for w in a.winfo_children() if isinstance(w,ui.tk.Toplevel));all_widgets=children(d)
    entries=[w.field for w in all_widgets if isinstance(w,PixelEntry)]
    self.assertEqual(entries[0].get(),str(chosen));entries[1].delete(0,'end');entries[1].insert(0,'Remembered')
    next(w for w in all_widgets if isinstance(w,PixelButton) and w.text=='开始导出').invoke()
    deadline=time.perf_counter()+15
    while d.winfo_exists() and time.perf_counter()<deadline:a.update();time.sleep(.01)
    self.assertTrue((chosen/'Remembered_00.png').exists());self.assertFalse((chosen/'Remembered').exists())
    a.zoom(.25)
   finally:a.close()
   a=app.App(state=state,preferences=prefs)
   try:self.assertEqual(a.export_directory,str(chosen));self.assertEqual(a.ui_scale,1.75)
   finally:a.close()

if __name__=='__main__':unittest.main()
