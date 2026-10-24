"""Build offline HTML guides from our limited Markdown subset, without dependencies."""
import html,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GUIDES=(('en','en','User guide'),('zh-CN','zh-CN','使用说明'),('ja','ja','使い方'))

def inline(value):
    value=html.escape(value)
    value=re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
    value=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',value)

def render(markdown):
    blocks=[];toc=[];paragraph=[];listing=None
    def flush():
        if paragraph:blocks.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
    def close_list():
        nonlocal listing
        if listing:blocks.append('</'+listing+'>');listing=None
    for line in markdown.splitlines()+['']:
        if not line.strip():flush();close_list();continue
        if line.startswith('#'):
            flush();close_list();level=len(line)-len(line.lstrip('#'));title=line[level:].strip()
            anchor='section-'+str(len(toc)+1) if level==2 else 'guide-title'
            if level==2:toc.append((anchor,title))
            blocks.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>');continue
        match=re.match(r'^(?:([-]) |(\d+)\. )(.*)',line)
        if match:
            flush();kind='ul' if match[1] else 'ol'
            if listing!=kind:
                close_list();listing=kind;blocks.append('<'+kind+'>')
            blocks.append('<li>'+inline(match[3])+'</li>');continue
        close_list();paragraph.append(line)
    return '\n'.join(blocks),toc

def build():
    for suffix,lang,label in GUIDES:
        path=ROOT/'docs'/('GUIDE.'+suffix+'.md');body,toc=render(path.read_text(encoding='utf-8'))
        links=''.join(f'<a href="#'+anchor+'">'+html.escape(title)+'</a>' for anchor,title in toc)
        page='''<!doctype html>
<html lang="LANG"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FellowStudio3D — LABEL</title><style>
:root{color-scheme:light;--ink:#493c32;--paper:#fcf6e9;--line:#d8c8b0;--accent:#825018}
*{box-sizing:border-box}body{margin:0;background:#ece4d8;color:var(--ink);font:16px/1.8 system-ui,"Yu Gothic",sans-serif}
header{padding:14px 24px;background:#493c32;color:#fff2d4;border-bottom:4px solid #e7a34c;font-weight:700}
.layout{max-width:1280px;margin:auto;display:grid;grid-template-columns:255px minmax(0,1fr);gap:24px;padding:28px 24px}
nav{position:sticky;top:20px;align-self:start;max-height:calc(100vh - 40px);overflow:auto;padding:16px;background:var(--paper);border:1px solid var(--line)}
nav a{display:block;padding:5px 0;font-size:14px}main{min-width:0;background:var(--paper);padding:24px 36px;border:1px solid var(--line)}
h1{font-size:30px;line-height:1.4;margin:0 0 16px}h2{font-size:22px;margin:40px 0 16px;padding-top:16px;border-top:2px solid var(--line);scroll-margin-top:20px}
a{color:var(--accent);text-underline-offset:3px}a:hover{color:#a55e0d}a:focus-visible{outline:3px solid #e7a34c;outline-offset:3px}
p{margin:14px 0}li{margin:9px 0}code{background:#e8ddc9;border:1px solid var(--line);padding:1px 5px;font-size:.9em;overflow-wrap:anywhere}strong{font-weight:750}
@media(max-width:800px){.layout{display:block;padding:12px}nav{position:static;max-height:none;margin-bottom:16px}main{padding:20px}h1{font-size:26px}}
@media print{header,nav{display:none}.layout{display:block;padding:0}body,main{background:white}main{border:0;padding:0}a{color:inherit}}
</style></head><body><header>FellowStudio3D · LABEL</header><div class="layout"><nav aria-label="LABEL">LINKS</nav><main>BODY</main></div></body></html>
'''
        page=page.replace('LANG',lang).replace('LABEL',html.escape(label)).replace('LINKS',links).replace('BODY',body)
        path.with_suffix('.html').write_text(page,encoding='utf-8')

if __name__=='__main__':build()
