import copy,tempfile,unittest
from pathlib import Path
import numpy as np
import engine as E,model_data as M,rounded_scene as S,uv_assets as U

class PixelDensityTests(unittest.TestCase):
    def test_density_adds_native_pixels_and_uv_texels_not_a_resized_bitmap(self):
        from PIL import Image
        m=M.normalize();high=M.normalize({'pixel_density':2})
        lo=S.assets({'model':m});hi=S.assets({'model':high})
        for part in U.PARTS:
            for face,rect in lo['textures'][part]['layout']['rects'].items():
                high_rect=hi['textures'][part]['layout']['rects'][face]
                self.assertGreaterEqual(high_rect[2],rect[2]*2-1)
                self.assertGreaterEqual(high_rect[3],rect[3]*2-1)
        p=E.new_project('stand');p.update(model=m,seconds=.25,fps=8)
        original=E.rgba(E.poses(p)[0],p['render'])
        p['model']=high;p['render'].update(canvas_width=128,canvas_height=128)
        native=E.rgba(E.poses(p)[0],p['render'])
        self.assertEqual(native.shape,(128,128,4))
        self.assertGreater((native[:,:,3]>0).sum(),(original[:,:,3]>0).sum()*3)
        self.assertFalse(np.array_equal(native,np.array(Image.fromarray(original).resize((128,128),Image.Resampling.NEAREST))))

    def test_density_handle_mapping_roundtrips_camera_and_canvas(self):
        import render_options as O,rig
        p=E.new_project('walk');p.update(model=M.normalize({'pixel_density':2}),seconds=.25,fps=8,camera_y=3)
        pose=E.poses(p)[0];settings={'canvas_width':128,'canvas_height':128}
        base=rig.joints(pose);mapped=O.joints(pose,settings)
        for part,chain in base.items():
            for name,value in chain.items():np.testing.assert_allclose(O.target(mapped[part][name],settings,pose),value,atol=1e-10)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model.json';M.save(p['model'],path,S.assets(p))
            import resource_library as L
            imported=L.apply_model(E.new_project('wave'),path)
            self.assertEqual(O.size(imported['render']),(128,128))
            self.assertEqual(imported['base']['kind'],'wave')

