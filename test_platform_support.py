import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import platform_support as P
import image_clipboard as C


class PlatformTests(unittest.TestCase):
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
