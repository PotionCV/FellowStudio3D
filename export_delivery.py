"""Explicit overwrite delivery: render first, back up owned files, then publish.

Only selected output formats with this exact export name are replaced. Other
files in an existing folder are left alone. Failed publication restores backups.
"""
import re,shutil,tempfile
from pathlib import Path


def replace_export(project,out,name,formats,create_folder,scale,directions,exporter):
    import engine as E
    if name is None:return exporter(project,out,name,formats,create_folder,scale,directions)
    name=E.export_name(project,name);parent=Path(out or E.ROOT/'out');parent.mkdir(parents=True,exist_ok=True)
    dest=parent/name if create_folder else parent
    if dest.is_symlink() or dest.exists() and not dest.is_dir():raise ValueError('导出目标必须是文件夹')
    formats=set(('png','strip','gif','recipe') if formats is None else formats)
    escaped=re.escape(name);patterns=[rf'{escaped}_atlas\.json'] if formats-{'recipe'} else []
    if 'png' in formats:patterns.append(rf'{escaped}_(?:d\d{{3}}_)?\d{{2,3}}\.png')
    if 'strip' in formats:patterns.append(rf'{escaped}_(?:strip|atlas(?:_\d+)?)\.png')
    if 'gif' in formats:patterns.append(rf'{escaped}(?:_d\d{{3}})?\.gif')
    if 'recipe' in formats:patterns.append(re.escape('recipe.json' if create_folder else name+'.json'))
    work=Path(tempfile.mkdtemp(prefix='.fellow-replace-',dir=parent)).resolve();preserve=False
    try:
        stage=work/'stage';stage.mkdir()
        ready=exporter(project,stage,name,formats,create_folder,scale,directions)
        generated=sorted(ready.iterdir(),key=lambda p:p.name)
        if any(not p.is_file() or p.is_symlink() for p in generated):raise ValueError('Invalid staged export')
        names={p.name for p in generated}
        owned=[p for p in dest.iterdir() if p.name in names or any(re.fullmatch(pattern,p.name) for pattern in patterns)] if dest.exists() else []
        if any(not p.is_file() or p.is_symlink() for p in owned):raise ValueError('同名目标不是普通文件，无法覆盖')
        backup=work/'backup';backup.mkdir();saved=[];published=[];created=not dest.exists()
        dest.mkdir(exist_ok=True)
        try:
            for target in owned:
                saved.append((target,target.replace(backup/target.name)))
            for source in generated:
                target=dest/source.name
                with target.open('xb') as output:
                    published.append(target)
                    with source.open('rb') as data:shutil.copyfileobj(data,output)
        except Exception:
            failures=set()
            for target in published:
                try:target.unlink(missing_ok=True)
                except OSError:failures.add(target.name)
            for target,original in saved:
                try:original.replace(target);failures.discard(target.name)
                except OSError:failures.add(target.name)
            if failures:
                preserve=True
                raise OSError('导出失败，部分文件恢复受阻；原文件备份保留于：'+str(backup))
            if created:
                try:dest.rmdir()
                except OSError:pass
            raise
    finally:
        if not preserve and work.parent==parent.resolve() and work.name.startswith('.fellow-replace-'):
            shutil.rmtree(work)
    return dest
