"""Create a clean source archive or an offline Windows x64 distribution.

Run from any directory. Only allowlisted files are copied; never local sessions.
"""
import argparse,hashlib,json,platform,shutil,sys,tempfile,zipfile,subprocess,os
from importlib.metadata import distribution
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULES=('attachment_binding','runtime_diagnostics','ui_layout','platform_support','export_delivery','retro_animation','hair_assembly','hair','hair_editor','hair_controls','resource_library','resource_browser','tail_motion','hand_props','hand_prop_editor','pose_animation','pose_animation_editor','directional_export','tails','tail_editor','aerial_actions','action_sequence','plush','plush_editor','attachments','attachment_editor','app','core3d','data_paths','engine','fellow','gaitdata','i18n','layers',
 'localized_ui','model_data','model_editor','outline_color','pixel_protection',
 'pixel_ui','preview_worker','protection_editor','rig','rounded_scene','studio_ui','paint_workspace',
 'texture_editor','image_clipboard','render_options','render_options_editor','pixel_lighting','uv_assets','uv_i18n','uv_panel_legacy','game_actions','motion_timing','motion_resources','sculpt')
PUBLIC=('README.md','LICENSE','VERSION','THIRD_PARTY_NOTICES.md','requirements.txt','requirements-lock.txt',
 'FellowStudio3D.sh','FellowStudio3D.bat','FellowStudio3D.ico','launch.py','Boutique9.ttf','Boutique9_Bold.ttf','Boutique9_OFL.txt',
 '.gitignore','.gitattributes')

def copy_application(dest,source=False):
    dest.mkdir(parents=True,exist_ok=True)
    files=[*(f'{name}.py' for name in MODULES),*PUBLIC]
    if source:files += ['test_attachment_binding.py','test_pixel_density.py','test_platform_support.py','tests.py','test_ui.py','test_export_preferences.py','test_release.py','test_extensions.py']
    for name in files:shutil.copy2(ROOT/name,dest/name)
    # Windows text editors can restore CRLF in an otherwise LF-tracked script.
    # Direct source ZIPs must work on macOS before Git normalization happens.
    script=dest/'FellowStudio3D.sh'
    script.write_bytes(script.read_bytes().replace(b'\r\n',b'\n'))
    for name in ('source','defaults','docs','examples/poses','examples/UV','examples/atlases'):
        shutil.copytree(ROOT/name,dest/name)
    for name in ('DefaultCharacter.json','CustomCharacter.json','README.md'):
        target=dest/'examples/characters'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'examples/characters'/name,target)
    sys.path.insert(0,str(ROOT))
    from motion_resources import BUILTIN_MOTIONS
    from model_data import BUILTIN_MODELS
    for name in (*BUILTIN_MODELS,'README.md'):
        target=dest/'examples/models'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'examples/models'/name,target)
    for name in (*BUILTIN_MOTIONS,'README.md','posecards/README.md'):
        target=dest/'examples/motions'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'examples/motions'/name,target)
    if source:
        shutil.copytree(ROOT/'fixtures',dest/'fixtures')
        shutil.copytree(ROOT/'tools',dest/'tools',ignore=shutil.ignore_patterns('__pycache__'))
        if (ROOT/'.github').is_dir():shutil.copytree(ROOT/'.github',dest/'.github')

def copy_runtime(dest):
    if sys.platform!='win32' or platform.machine().lower() not in ('amd64','x86_64'):
        raise RuntimeError('Portable builds require Windows x64.')
    python=Path(sys.base_prefix);dest.mkdir()
    for pattern in ('python*.exe','python*.dll','vcruntime*.dll','LICENSE.txt'):
        for f in python.glob(pattern):shutil.copy2(f,dest/f.name)
    for name in ('DLLs','tcl'):
        shutil.copytree(python/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(python/'Lib',dest/'Lib',ignore=shutil.ignore_patterns('site-packages','__pycache__','test','tests','idlelib','ensurepip'))
    site=dest/'Lib'/'site-packages';site.mkdir()
    for package in ('numpy','Pillow','tkinterdnd2'):
        dist=distribution(package)
        for entry in dist.files or ():
            # Wheels can include ../../../Scripts entries; runtime needs only
            # paths inside site-packages, never executable entry-point scripts.
            if '..' in entry.parts or '__pycache__' in entry.parts:continue
            src=Path(dist.locate_file(entry));target=site/entry
            if src.is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    version=f'python{sys.version_info.major}{sys.version_info.minor}'
    (dest/f'{version}._pth').write_text(f'{version}.zip\n.\nLib\nDLLs\nLib/site-packages\nimport site\n',encoding='utf-8')

def build_launcher(dest):
    compiler=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET'/'Framework64'/'v4.0.30319'/'csc.exe'
    if not compiler.is_file():raise RuntimeError('Windows .NET Framework C# compiler is required to build the launcher.')
    subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64','/optimize+',
        '/reference:System.Windows.Forms.dll',f'/win32icon:{ROOT/"FellowStudio3D.ico"}',
        f'/out:{Path(dest).resolve()}',str(ROOT/'tools'/'Launcher.cs')],check=True)

def build(output,portable=False,personal=False):
    output=Path(output).resolve()
    if output.exists():raise FileExistsError(f'Refusing to overwrite {output}')
    # Keep packaged offline instructions synchronized with their editable sources.
    import runpy
    runpy.run_path(str(ROOT/'tools'/'build_manuals.py'),run_name='__main__')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fellow-release-') as td:
        pack=Path(td)/'FellowStudio3D';copy_application(pack,source=not portable)
        if personal:
            # Explicit private delivery only. Never part of the public build.
            for name in ('KumamonBag','CatBag'):
                source=ROOT/'user_data/models'/(name+'.json')
                if source.is_file():
                    target=pack/'local_characters'/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        if portable:
            copy_runtime(pack/'runtime')
            build_launcher(pack/'FellowStudio3D.exe')
            (pack/'FellowStudio3D.bat').write_bytes(b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"%~dp0runtime\\python.exe" -I "%~dp0launch.py"\r\nif errorlevel 1 pause\r\n')
        manifest={str(f.relative_to(pack)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(pack.rglob('*')) if f.is_file()}
        (pack/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for file in pack.rglob('*'):
                if file.is_file():z.write(file,file.relative_to(pack.parent))
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable',action='store_true',help='Include a Windows x64 Python runtime')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--personal',action='store_true',help='Private local delivery: include the two curated personal mascot models')
    args=parser.parse_args()
    path=args.output or ROOT/'dist'/('FellowStudio3D-Windows-x64.zip' if args.portable else 'FellowStudio3D-source.zip')
    print(build(path,args.portable,args.personal))
