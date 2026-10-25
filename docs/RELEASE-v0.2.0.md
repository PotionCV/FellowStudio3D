# FellowStudio3D v0.2.0

## English

- More editable shapes: tapered head/body/limb profiles, cones and pyramids,
  curved limbs and projecting faces, with seven new model examples.
- Reusable pose resources, body-region masks, timed action layers and
  additive/posture/replace blending. New layers default to Add changes.
- Game actions including jump/landing, thrust, swing, push kick, hit reaction,
  fall/get-up, roll, climb, turn, waist twist and pickup/put-down. Lifts can
  reach overhead; pickup reach adapts to body proportions.
- Thrust and Swing have real wind-up poses with separate amount and timing.
  Default Thrust uses a compact shoulder/hip drive and recovers the input guard.
- Directional controls now support negative values where useful. Bow can lean
  backward, squat has inward/outward leg spread, and joint bend and motion
  range can be reversed. Existing motion defaults remain unchanged.
- Airborne blends preserve jump height. Idle breathing plants the feet.
  Frame count, FPS and whole-pixel vertical framing are directly editable.
- Texture display and part colors are independent. Updated painted character
  examples include matching model, embedded PNGs and pixel protection groups.
- Faster interactive preview: direct FK inside foot IK, shared authoring and
  cancellation of obsolete jobs. Local CustomCharacter + Idle + Thrust checks
  displayed edits in about 0.65–0.76 seconds instead of multi-second waits.
- English, Chinese and Japanese controls and offline guides updated together.

**Windows:** download the Windows x64 ZIP, extract everything and run
`FellowStudio3D.exe`. No Python installation is needed. For the painted example,
choose Character model → Load model → `examples/models/CustomModel.json` → Apply.
Try Motion examples for editable recipes, including `LeanBack` and `WideSquat`.

The itch.io build includes launch and manual actions for the itch desktop app.
The source archive is for developers and has no bundled runtime. MIT licensed.

## 简体中文

- 增加锥形、角锥、上下收放、曲线肢体及凸起脸部等塑形参数和七个模型案例。
- 增加可复用姿势、部位遮罩、动作时间范围和融合控制，默认叠加变化。
- 补充游戏常用动作，以及扭腰回正、踹腿、取物、放下和举过头顶。
- 刺击与挥击具备真实收臂、屈肘和反向转体蓄力，幅度与时间独立可调。
- 多个方向参数支持负值；弯腰可变为后仰，下蹲可控制双腿内收、外展。
- 修复跳跃融合被拉回地面、站姿呼吸锁脚等问题；支持直接设置帧数、
  播放速度和像素级画幅上下偏移。
- 贴图与分色独立；更新自定义角色案例的模型、贴图及像素保护设置。
- 优化 IK 和预览计算，取消过期任务，减少调参后的等待。
- 同步更新中英日界面与离线说明。现有走路、跑步默认参数保持不变。

解压完整 Windows 包后运行 `FellowStudio3D.exe`。通过“角色模型 → 载入模型”
选择 `examples/models/CustomModel.json` 并应用，即可试用绘制好的角色。
itch.io 包支持 itch 桌面客户端启动。源码包供开发者使用，不含运行时。

## 日本語

- 上下の幅・厚み、曲がった手足、突き出した顔などの形状編集と七つのモデル例。
- 再利用できるポーズ、部位マスク、レイヤーの時間範囲、加算・姿勢・置換合成。
- ジャンプ、攻撃、前蹴り、腰ひねり、拾う・置く、頭上への持ち上げなどの動作。
- 突き・振り攻撃の実際の溜め姿勢。大きさと時間を別々に調整できます。
- 方向パラメーターの負値、後屈、しゃがむときの脚の開閉に対応。
- 空中合成の高さ、呼吸中の足の固定を修正。フレーム数・FPS・画面Yを設定可能。
- テクスチャと部位色を個別に表示。塗装済みキャラクター例を更新。
- IK・プレビューを高速化し、古い計算を中断。三言語の説明書も更新。

Windows ZIP をすべて展開し、`FellowStudio3D.exe` を実行してください。
モデル編集で `examples/models/CustomModel.json` を読み込むと作例を試せます。
itch.io 版は itch デスクトップアプリの起動に対応。ソース版に実行環境は含みません。
