LANGUAGES={'en':'English','zh':'简体中文','ja':'日本語'}
language='en'
ROWS='''
新建|New|新規
打开|Open|開く
保存|Save|保存
撤销|Undo|元に戻す
导出|Export|書き出す
动画|Motion|動作
身体|Body|体型
贴图|Textures|テクスチャ
正面|Front|正面
侧面|Side|側面
斜面|Three-quarter|斜め
斜俯|Elevated|斜め上
四视图|Four views|四分割
焦点视图|Focused view|選択した視点
播放|Play|再生
暂停|Pause|一時停止
站立|Idle|待機
走路|Walk|歩く
跑步|Run|走る
下蹲|Squat|しゃがむ
跳跃|Jump|ジャンプ
步幅|Stride|歩幅
摆臂|Arm swing|腕振り
上下起伏|Body bounce|上下動
速度|Speed|速度
时长（秒）|Duration (seconds)|長さ（秒）
每秒帧数|Frames per second|フレームレート
左臂举起|Raise left arm|左腕を上げる
右臂举起|Raise right arm|右腕を上げる
姿势混合|Posture mix|姿勢の混合
身体前倾|Body lean|体の前傾
低头 / 抬头|Head pitch|頭の上下
上臂跟随|Upper arm follow|上腕の追従
前臂跟随|Forearm follow|前腕の追従
肩宽|Shoulder width|肩幅
腰宽|Waist width|腰幅
胯宽|Hip width|腰骨の幅
躯干高度|Torso height|胴体の高さ
头部大小|Head size|頭の大きさ
头部间距|Head gap|頭と胴体の間隔
上臂长度|Upper arm length|上腕の長さ
前臂长度|Forearm length|前腕の長さ
大腿长度|Thigh length|太ももの長さ
小腿长度|Shin length|すねの長さ
手臂粗细|Arm width|腕の太さ
腿部粗细|Leg width|脚の太さ
肩部间距|Arm gap|腕の間隔
头部|Head|頭
躯干|Torso|胴体
左上臂|Left upper arm|左上腕
左前臂|Left forearm|左前腕
右上臂|Right upper arm|右上腕
右前臂|Right forearm|右前腕
左大腿|Left thigh|左太もも
左小腿|Left shin|左すね
右大腿|Right thigh|右太もも
右小腿|Right shin|右すね
替换 PNG|Replace PNG|PNGを交換
换图|Swap|差し替え
恢复|Reset|リセット
查看 UV|Inspect UV|UVを確認
导出整套 UV|Export UV pack|UV一式を出力
导入整套 UV|Import UV pack|UV一式を読み込む
重载已替换贴图|Reload linked PNGs|交換したPNGを再読込
拖入 PNG 或点击替换；图片尺寸需与模板相同。|Drop a PNG or click Replace. Match the template dimensions.|PNGをドロップするか交換をクリック。テンプレートと同じ画像サイズを使用。
绘画 PNG 与参考线图分别导出。项目内嵌贴图，可独立保存。|Paint images and guides export separately. Projects embed textures.|描画用PNGとガイドは別に出力。プロジェクトに画像を内包します。
导出到空目录，再编辑部位 PNG；不要修改画布尺寸。|Export to an empty folder. Paint each part PNG without resizing it.|空のフォルダーへ出力し、画像サイズを変えずに部位PNGを編集。
模型修改会保留各面图案，并按新尺寸重排 UV。|Body edits preserve face artwork and repack UVs to fit.|体型の変更では各面の絵を保ち、新しい寸法にUVを再配置。
基础动作始终保留，举臂改变姿势中心并保留摆臂。|The base motion stays intact. Raised arms keep their swing.|基本動作を維持し、腕を上げても腕振りを残します。
头颈与躯干控制|Head and body|頭と胴体
跟随效果|Motion follow|動きの追従
这是可调节的周期跟随，尚未接入物理弹簧。|Periodic motion follow; spring physics is not implemented yet.|周期的な追従です。ばね物理は未実装。
父部位带动弹簧与惯性；上臂与前臂可分别设置。|Parent motion drives springs and inertia. Adjust upper and forearm separately.|親部位の動きでばねと慣性を駆動。上腕と前腕を個別に調整。
纹理 / 分色|Textures / colors|テクスチャ・色
外边线|Outline|輪郭線
重叠分隔|Overlap lines|重なりの境界
骨骼|Bones|骨格
恢复基础形体|Reset body|体型をリセット
显示参考线|Show guide|ガイドを表示
取消|Cancel|キャンセル
关闭|Close|閉じる
开始导出|Export|書き出す
选择目录|Choose directory|出力先を選択
导出名称|Export name|書き出し名
创建子文件夹|Create a subfolder|サブフォルダーを作成
PNG 序列|PNG frames|PNG連番
PNG 条带|PNG strip|PNGシート
GIF 预览|GIF preview|GIFプレビュー
项目 JSON|Project JSON|プロジェクトJSON
输出视角|Output view|出力する視点
导出失败|Export failed|書き出し失敗
操作失败|Operation failed|操作失敗
选择一个 PNG 文件|Choose one PNG file|PNGを一つ選択してください
关闭会丢弃未保存的修改吗？|Discard unsaved changes?|未保存の変更を破棄しますか？
另存项目|Save project|プロジェクトを保存
未保存|Unsaved|未保存
就绪|Ready|準備完了
正在更新预览，可继续操作|Updating preview; controls remain available|プレビュー更新中・操作を続けられます
预览已更新|Preview updated|プレビュー更新完了
所有贴图使用默认资源|All parts use default textures|すべて既定の画像を使用中
恢复全部贴图|Reset all textures|全画像をリセット
'''
CATALOG={r.split('|')[0]:dict(zip(('zh','en','ja'),r.split('|'))) for r in ROWS.strip().splitlines()}
for row in '''
框选|Select|矩形
画笔|Brush|ブラシ
替换选区|Replace|置換
加选|Add|追加
减选|Remove|除外
适合窗口|Fit|全体表示
网格|Grid|グリッド
选区|Selection|選択範囲
保护角度|Angle limit|保護角度
超过角度时整组恢复普通 UV。|Beyond this angle the group uses normal UV.|この角度を超えると通常のUV表示に戻ります。
更新保护组|Update group|グループを更新
编辑|Edit|編集
删除|Delete|削除
复制另一侧|Copy other side|反対側からコピー
可跨 UV 面选择。\\n滚轮缩放；中键或空格拖动。\\n右键减选；Shift 加选，Ctrl 减选。|Selection can cross UV faces.\\nWheel: zoom. Middle drag or Space: pan.\\nRight mouse: erase. Shift: add. Ctrl: remove.|UV面をまたいで選択できます。\\nホイールで拡縮。中ボタンかSpaceで移動。\\n右ボタンで除外。Shiftで追加、Ctrlで除外。
'''.strip().splitlines():
 key,en,ja=row.replace('\\n','\n').split('|');CATALOG[key]={'zh':key,'en':en,'ja':ja}
for row in '''
像素保护|Pixel groups|ピクセル保護
框选像素；Shift 追加，Ctrl 减选。每组须位于同一个 UV 面。|Drag to select pixels. Shift adds; Ctrl subtracts. Keep each group on one UV face.|ドラッグで選択。Shiftで追加、Ctrlで除外。グループは同じUV面内で作成。
保护所选像素|Protect selection|選択を保護
清除选择|Clear selection|選択を解除
应用保护组|Apply groups|グループを適用
保护组|Pixel groups|保護グループ
删除组|Delete group|グループ削除
朝向镜头时保护排列；转侧恢复 UV。轮廓外或被遮挡的像素不强制显示。|Preserves the pattern when facing the camera; turns use UV. Silhouette and occlusion still apply.|正面では配置を保持し、横向きではUV表示に戻ります。輪郭と遮蔽は維持します。
每组只能包含同一个 UV 面的像素。|A group must stay within one UV face.|同じUV面内のピクセルを選択してください。
像素已属于其他保护组，请先删除旧组。|Some pixels already belong to a group. Delete that group first.|既存グループと重複しています。先に削除してください。
保护组已建立；应用后在角色预览中查看。|Group created. Apply to see it on the character.|グループを作成しました。適用して確認できます。
还有未建立保护组的选择，请先保护或清除。|Protect or clear the remaining selection before applying.|残りの選択を保護するか解除してください。
'''.strip().splitlines():
 key,en,ja=row.split('|');CATALOG[key]={'zh':key,'en':en,'ja':ja}
def set_language(code):
 global language
 language=code if code in LANGUAGES else 'en'
def tr(text):return CATALOG.get(str(text),{}).get(language,str(text))
