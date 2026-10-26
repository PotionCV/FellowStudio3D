# Eight-direction atlas examples

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
