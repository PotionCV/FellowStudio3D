"""Windowed entry point shared by the source and portable launchers."""
import ctypes,multiprocessing,runpy,sys,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))

if __name__=='__main__':
    multiprocessing.freeze_support()
    try:
        runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
    except Exception:
        detail=traceback.format_exc()
        try:
            from data_paths import workspace_paths
            state,_=workspace_paths();log=state.parent/'startup-error.log'
            log.write_text(detail,encoding='utf-8')
            message='Could not start FellowStudio3D. Error details:\n'+str(log)
        except Exception:
            message='Could not start FellowStudio3D.\n'+detail[-1500:]
        print(message+'\n'+detail,file=sys.stderr)
        try:
            if sys.platform=='win32':ctypes.windll.user32.MessageBoxW(None,message,'FellowStudio3D',16)
            else:
                import tkinter as tk
                from tkinter import messagebox
                root=tk.Tk();root.withdraw()
                try:messagebox.showerror('FellowStudio3D',message,parent=root)
                finally:root.destroy()
        except Exception:pass  # Keep the original error when Tk itself is unavailable.
        sys.exit(1)
