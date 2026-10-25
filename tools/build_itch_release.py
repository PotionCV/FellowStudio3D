"""Make a flat itch desktop-app ZIP from an already verified Windows ZIP."""
import argparse,hashlib,json,zipfile
from pathlib import Path,PurePosixPath

ITCH='''[[actions]]
name = "play"
path = "runtime/pythonw.exe"
args = ["-I", "launch.py"]
platform = "windows"

[[actions]]
name = "manual"
path = "docs/GUIDE.en.html"
'''

def build(portable,output):
 output=Path(output).resolve()
 if output.exists():raise FileExistsError(f'Refusing to overwrite {output}')
 files={}
 with zipfile.ZipFile(portable) as source:
  for entry in source.infolist():
   if entry.is_dir():continue
   parts=PurePosixPath(entry.filename).parts
   if len(parts)<2 or parts[0]!='FellowStudio3D' or '..' in parts or '\\' in entry.filename:raise ValueError('Unexpected archive path')
   name='/'.join(parts[1:])
   if name in files:raise ValueError('Duplicate archive path')
   files[name]=source.read(entry)
 for required in ('runtime/pythonw.exe','launch.py','docs/GUIDE.en.html','VERSION'):
  if required not in files:raise ValueError('Not a portable FellowStudio3D archive')
 files['.itch.toml']=ITCH.encode('utf-8');files.pop('SHA256.json',None)
 manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
 files['SHA256.json']=json.dumps(manifest,indent=2).encode('utf-8')
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
  for name,data in sorted(files.items()):archive.writestr(name,data)
 return output

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('portable',type=Path);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();print(build(args.portable,args.output))
