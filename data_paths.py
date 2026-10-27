"""Keep mutable local work separate from distributable application files."""
import os,shutil,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def workspace_paths():
    requested=Path(os.environ.get('FELLOWSTUDIO3D_DATA_DIR',ROOT/'user_data'))
    try:
        requested.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryFile(dir=requested):pass
    except OSError:
        base=Path.home()/'Library'/'Application Support' if sys.platform=='darwin' else Path(os.environ.get('LOCALAPPDATA',Path.home()))
        requested=base/'FellowStudio3D'
        requested.mkdir(parents=True,exist_ok=True)
    # Copy, never move or overwrite, existing local work from older versions.
    for filename in ('studio3d_motion.json','ui_settings.json'):
        old=ROOT/filename;new=requested/filename
        if old.is_file() and not new.exists():shutil.copy2(old,new)
    return requested/'studio3d_motion.json',requested/'ui_settings.json'
