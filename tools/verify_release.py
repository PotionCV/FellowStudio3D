"""Use the archive's Python to verify an extracted tool: <folder> [--gui]."""
import sys,tempfile
from pathlib import Path
tool=Path(sys.argv[1]).resolve();sys.path.insert(0,str(tool))

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import engine as E,fellow as F,numpy as np
    from PIL import Image
    assert Path(F.SRC).resolve().is_relative_to(tool)
    if (tool/'runtime').is_dir():assert Path(np.__file__).resolve().is_relative_to(tool/'runtime')
    project=E.new_project('walk',name='Walk');project['seconds']=.2
    expected=E.rgba(E.poses(project)[0],project['render'])
    with tempfile.TemporaryDirectory(prefix='fellow-release-check-') as td:
        for scale in (1,4,8):
            dest=E.export(project,td,f'Walk{scale}',formats=['png','strip','gif'],create_folder=False,scale=scale)
            actual=np.array(Image.open(dest/f'Walk{scale}_00.png'))
            np.testing.assert_array_equal(actual,expected.repeat(scale,0).repeat(scale,1))
        if '--gui' in sys.argv:
            import app
            state=Path(td)/'session.json';E.save(project,state)
            window=app.App(state=state,preferences=Path(td)/'preferences.json');errors=[];done=[]
            window.report_callback_exception=lambda *error:errors.append(error)
            def check():
                if window.future_job or window.latest_request or window.pending:
                    window.after(50,check);return
                assert len(window.raw_images)==4*len(window.seq)
                if (tool/'runtime').is_dir():assert window.dnd_available
                from unittest.mock import patch
                import model_data as M
                example=tool/'examples'/'models'/'CustomModel.json';expected_model=M.load_resource(example)
                window.edit_model()
                with patch('model_editor.filedialog.askopenfilename',return_value=str(example)):window.model_editor.load_preset()
                window.model_editor.apply()
                assert window.project['assets3d']==expected_model['assets3d']
                assert window.project['base']==project['base']
                window.edit_textures();editor=window.texture_editor
                editor.start_painting(Path(td)/'Painting files');editor.single_view.set(True);editor.draw();assert len(editor.cells)==1
                editor.compare_before(True);editor.compare_before(False)
                groups=editor.inspect_uv('head');window.update()
                x,y,w,h=groups.resource['layout']['rects']['front'];groups.selection={(x+2,y+2),(x+3,y+2)};groups.add_group();groups.apply();editor.apply()
                assert window.project['assets3d']['textures']['head']['protected_groups']
                window.export();window.update()
                import tkinter as tk
                next(w for w in window.winfo_children() if isinstance(w,tk.Toplevel)).destroy()
                done.append(True);window.close()
            window.after(300,check);window.after(30000,window.close);window.mainloop()
            assert done and not errors,(done,errors)
    print('Internal resources, 1x/4x/8x export'+(', GUI, workers and editors' if '--gui' in sys.argv else '')+' OK')
