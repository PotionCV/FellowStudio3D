import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import platform_support as P
import image_clipboard as C


class PlatformTests(unittest.TestCase):
    def test_preview_queue_drain_yields_and_discards_stale_revisions(self):
        import queue
        from preview_worker import drain_progress
        progress=queue.Queue()
        for i in range(30):progress.put((1 if i==0 else 2,['pose'],{i:'image'},True))
        seq,images=drain_progress(progress,2,limit=4,budget=1)
        self.assertEqual(seq,['pose']);self.assertEqual(set(images),{1,2,3})
        self.assertEqual(progress.qsize(),26)
        self.assertEqual(drain_progress(progress,2,budget=0),(None,{}))

    def test_watchdog_records_environment_and_restores_handler(self):
        from unittest.mock import Mock
        import runtime_diagnostics as D
        with tempfile.TemporaryDirectory() as folder:
            root=Mock();root.state_path=Path(folder)/'state.json'
            root.tk.call.return_value='test-Tk';original=root.report_callback_exception
            root.after.return_value='timer'
            with patch.object(D.faulthandler,'dump_traceback_later') as arm,patch.object(D.faulthandler,'cancel_dump_traceback_later') as cancel:
                watchdog=D.Watchdog(root);arm.assert_called_once()
                watchdog.close();watchdog.close();cancel.assert_called_once()
                self.assertIs(root.report_callback_exception,original)
                text=(Path(folder)/'runtime-diagnostics.log').read_text(encoding='utf-8')
                self.assertIn('test-Tk',text)
                second=D.Watchdog(root);second.close()
                self.assertEqual((Path(folder)/'runtime-diagnostics.previous.log').read_text(encoding='utf-8'),text)

    def test_layout_caps_scale_and_reserves_preview_space(self):
        from ui_layout import fitted_scale,panel_sizes
        for width,height in ((820,560),(1024,640),(1280,720),(1440,900),(1920,1080)):
            scale=fitted_scale(1.5,width,height)
            self.assertGreaterEqual(scale,.75);self.assertLessEqual(scale,1.5)
            left,right,_,_=panel_sizes(width,scale,[900,900])
            self.assertGreaterEqual(width-left-right-64,280)
        self.assertLess(fitted_scale(1.5,1280,720),1.5)
        self.assertEqual(fitted_scale(.8,1920,1080),.8)
        self.assertEqual(fitted_scale(1.5,1920,1080),1.5)

    def test_pixel_font_matches_mac_typographic_and_localized_names(self):
        for name in P.PIXEL_FAMILIES:
            self.assertEqual(P.pixel_font_family(('Helvetica',name),'Helvetica'),name)
        self.assertEqual(P.pixel_font_family(('BOUTIQUEBITMAP9X9 1.9',),'Helvetica'),'BOUTIQUEBITMAP9X9 1.9')
        self.assertEqual(P.pixel_font_family(('Helvetica',),'Helvetica'),'Helvetica')
        self.assertEqual(P.pixel_font_family(('BoutiqueBitmap9x9 1.9 B',),'Helvetica'),'Helvetica')

    def test_mac_trackpad_and_mouse_and_windows_wheel(self):
        with patch.object(P.sys,'platform','darwin'):
            self.assertEqual([P.wheel_units(x) for x in (1,-1,0,120,-120,.25)],[-1,1,0,-1,1,-1])
        with patch.object(P.sys,'platform','win32'):
            self.assertEqual(P.wheel_units(120),-1)
            self.assertEqual(P.wheel_units(-240),2)

    def test_folder_paths_are_separate_arguments(self):
        with patch.object(P.sys,'platform','darwin'),patch.object(P.subprocess,'Popen') as run:
            P.open_folder('folder with spaces; harmless')
            self.assertEqual(run.call_args.args[0],['open',str(Path('folder with spaces; harmless').resolve())])

    def test_mac_clipboard_copy_preserves_alpha_and_cleans_temp(self):
        observed=[]
        def run(args,**kwargs):
            path=Path(args[-1]);observed.append(path)
            with Image.open(path) as image:
                self.assertEqual(image.getpixel((0,0)),(20,40,60,100))
                self.assertEqual(image.info['FellowStudio3D'],'metadata')
            self.assertEqual(args[:2],['osascript','-e'])
            self.assertNotIn('shell',kwargs)
        with patch.object(C.sys,'platform','darwin'),patch.object(C.subprocess,'run',side_effect=run):
            C.copy_image(Image.new('RGBA',(2,2),(20,40,60,100)),0,'metadata')
        self.assertFalse(observed[0].exists())

    def test_mac_paste_and_empty_clipboard(self):
        image=Image.new('RGBA',(2,3))
        with patch.object(C.sys,'platform','darwin'),patch.object(C.ImageGrab,'grabclipboard',return_value=image):
            self.assertIs(C.read_image(),image)
        with patch.object(C.sys,'platform','darwin'),patch.object(C.ImageGrab,'grabclipboard',return_value=None):
            with self.assertRaises(ValueError):C.read_image()

    def test_mac_writable_data_fallback(self):
        import data_paths as D
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder);blocked=home/'blocked';blocked.write_text('file')
            with patch.object(D.sys,'platform','darwin'),patch.object(D.Path,'home',return_value=home),patch.dict(D.os.environ,{'FELLOWSTUDIO3D_DATA_DIR':str(blocked)}):
                state,prefs=D.workspace_paths()
                self.assertEqual(state.parent,home/'Library/Application Support/FellowStudio3D')
                self.assertEqual(prefs.parent,state.parent)


if __name__=='__main__':unittest.main()
