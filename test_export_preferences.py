import importlib,json,tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
import app,engine as E
from pixel_ui import PixelButton,PixelCheck,PixelEntry

class ExportPreferencesTests(unittest.TestCase):
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
