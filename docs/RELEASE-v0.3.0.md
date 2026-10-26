# FellowStudio3D v0.3.0

Create character animation from poses and reusable motions, with a compact pixel interface and transparent sprite export.

- Creation library with three distinct starting characters and searchable motion examples.
- Seamless mascot body, editable ears, three-joint tails with controllers, per-joint softness and bounce, and generic held-object shapes.
- Pose cards and a larger action-sequence editor with a timing overview; swimming, hovering and editable performance examples.
- Save animation separately from appearance, then apply it to another character.
- Single UV window: Save PNG, Copy (Ctrl+C), Paste to replace (Ctrl+V), native size and alpha, protection groups, Undo and Cancel.
- Four/eight-direction sprite atlases with frame timing and pivot metadata; 64×64 native pixels and integer output scaling.
- Repetitive character variants and automatic face overlays removed. Existing painted PNGs remain intact; legacy object resources still load.

## Windows / itch.io

Upload `FellowStudio3D-v0.3.0-itch-Windows-x64.zip` as a Windows downloadable application. The ZIP is flat and includes `.itch.toml`, an offline Python runtime, the launcher, English/Chinese/Japanese manuals, licenses and SHA256 hashes. Extract everything and run `FellowStudio3D.exe`; no Python installation is required. The itch app also has a launch action.

The public package excludes private mascot artwork, personal sessions and unregistered user examples. Copy existing project JSONs separately to continue editing; do not overwrite your old `user_data` folder when unpacking a new version.

## 使用入口

- 找角色与动作：**创作资源库…**。
- 自编动作、串联或保存可迁移动画：**制作动画…**。
- 尾巴松软：角色有尾巴后，**整体控制 → 尾巴 → 物理跟随**。
- 单张贴图保存／复制／粘贴：**UV贴图 → 点击部位贴图**。
- 游戏方向图集：导出时选择**四／八方向**。

Limits: tails use deterministic secondary motion without collision; multiple tails share a channel. Different character proportions still need contact checks after animation transfer. Pose editing and layer composition remain the animation model; action sequences do not solve continuous combat footwork.
