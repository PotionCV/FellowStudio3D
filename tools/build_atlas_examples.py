"""Generate three neutral eight-direction sprite packs into an empty folder."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import engine as E

def build(output):
 output=Path(output)
 if output.exists() and any(output.iterdir()):raise FileExistsError('Choose an empty atlas example folder')
 output.mkdir(parents=True,exist_ok=True)
 examples=ROOT/'examples'
 for name,source in (('TailWalk',examples/'characters/LongTailMascot.json'),
                     ('HoverWave',examples/'motions/fusions/HoverWave.json'),
                     ('FrontCrawl',examples/'motions/game/SwimFrontCrawl.json')):
  project=E.load(source);project.update(seconds=1.5,fps=8)
  E.export(project,out=output,name=name,formats={'strip','recipe'},create_folder=False,scale=1,directions=8)
 (output/'README.md').write_text('''# Eight-direction atlas examples

TailWalk, HoverWave and FrontCrawl each contain a transparent 768×512 PNG atlas,
a `*_atlas.json` frame descriptor and an editable project JSON. Twelve native
64×64 frames run at 8 FPS. Each row is one level camera angle: 0°, 45°, 90°,
135°, 180°, 225°, 270°, 315°. Frames run left to right.

Open the project JSON to edit the motion. Use the frame descriptor's image,
rect, duration_ms and pivot to slice/align the sprites in your game workflow.
The descriptor is an engine-neutral format documented in
[Directional atlas format](../../docs/DIRECTIONAL-ATLASES.md).

中文：每套包含透明八方向图集、帧信息及可编辑项目。每行一个方向、
每列一帧，原生64×64，12帧、8 FPS。按JSON的image/rect切片，按duration_ms
播放，用统一pivot对齐。项目用更新后的工具打开。

日本語：各セットに透過8方向アトラス、フレーム情報、編集可能なプロジェクトを
含みます。各行が方向、各列がフレームです。元画像64×64、12フレーム、8 FPS。
JSONのimage/rectで切り出し、duration_msで再生し、pivotで位置を合わせます。
''',encoding='utf-8')
 return output

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'build/atlas-examples')
 print(build(parser.parse_args().output))
