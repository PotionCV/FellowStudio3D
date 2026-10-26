# Directional sprite atlases

In **Export frames → Export view**, choose **Four directions (level)** or
**Eight directions (level)**. PNG sequences use angle-coded filenames; the strip
option becomes a directional atlas. GIF creates a preview for each direction.
The existing **JSON recipe** option still saves an editable project. A separate
`NAME_atlas.json` descriptor is always included with directional exports.

## Layout and playback

- Each row is a direction; each column is a frame. Four rows use camera angles
  0°, 90°, 180°, 270°; eight rows add the intermediate 45° angles. All are level
  orthographic cameras. The project's static character yaw is retained.
- Cells are fixed 64×64 native pixels, or integer nearest-neighbor scaling.
  Transparent PNGs are never cropped, smoothed or independently recentered.
- Atlases wider than 4096 pixels split into consecutive frame pages. Each page
  retains all direction rows; the last page can contain fewer columns. The JSON
  tells you which image/rectangle belongs to every frame.
- `fps` and `duration_ms` describe the actual frame rate. For `loop`, restart
  after the last frame. `once` ends playback; `hold` keeps its last pose.
- `pivot` is a shared integer cell-space alignment point: native x=32,
  y=56 plus the integer framing-Y offset, multiplied by output scale. It is a
  fixed sprite anchor, not a fitted foot position for each individual pose.
- Direction IDs encode camera yaw (`d045`, for example), rather than prescribing
  your game's compass convention. An animation can itself turn the character.

## Descriptor fields (version 1)

| Field | Meaning |
| --- | --- |
| `type`, `version` | `FellowStudioDirectionalAtlas`, `1` |
| `name`, `fps`, `playback`, `frame_count` | Clip identity and timing |
| `native_cell`, `cell`, `scale`, `pivot` | Pixel dimensions and common anchor |
| `character_yaw`, `camera_pitch` | Static project yaw; level camera pitch 0 |
| `pages` | Image filename, size, first frame and frame count of each atlas page |
| `directions` | ID, yaw, pitch, row and frame records for each camera angle |
| `frames[].index`, `duration_ms` | Frame index and duration |
| `frames[].image`, `rect` | PNG filename and `[x,y,width,height]` crop |
| `frames[].png` | Optional independent frame PNG when sequence output was selected |

For atlas output, `image` and `rect` reference a page. With only independent PNG
output, they reference the whole frame PNG. With GIF/recipe-only output there is
no PNG to slice, so `image`/`rect` are null. No original drawing path or absolute
local file path is recorded.

## Reliability and size

Rendering runs in the existing background export process. A page is processed
and released before the next one; at 8× with eight directions its RGBA pixel
buffer is at most 64 MiB. GIF previews are assembled one direction at a time
using paletted frames. Source poses are calculated once for all directions.

The exporter checks planned filenames before rendering, stages the output and
creates destination files exclusively. A collision preserves the existing file
and rolls back files created by that publish attempt. The descriptor is published
last. Single-view export keeps its existing filenames and behavior.

Three ready examples live in `examples/atlases`: TailWalk, HoverWave, FrontCrawl.
To regenerate into a new empty folder:

```powershell
python tools/build_atlas_examples.py --output build/atlas-demo
```

中文：在原导出视角菜单选择四／八方向（水平）。每行一个方向、每列一帧，
大图集自动分页；按帧记录中的图片和矩形切片，用时长播放、用统一锚点对齐。
JSON是通用帧描述，需要由你的游戏素材流程读取；PNG可单独使用。

日本語：従来の書き出し画面で4方向／8方向（水平）を選択します。各行が方向、
各列がフレームで、大きな画像は自動分割します。フレーム情報の画像・矩形で
切り出し、時間で再生し、共通の基準点で位置を合わせてください。
