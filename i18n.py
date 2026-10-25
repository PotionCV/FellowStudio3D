"""UI text catalogs; recipe keys and user names stay language-independent."""
LANGUAGES={'en':'English','zh':'简体中文','ja':'日本語'}
language='en'
ROWS=r"""
身体结构|Body structure|体の構造
一体布偶|Seamless mascot|一体型マスコット
分体人形|Separate head / body|頭と胴体が分離
主体|Main body|本体
整体高度（px）|Total height (px)|全体の高さ (px)
上部宽度（px）|Upper width (px)|上部の幅 (px)
肚子宽度（px）|Belly width (px)|お腹の幅 (px)
底部宽度（px）|Base width (px)|底部の幅 (px)
主体厚度（px）|Body depth (px)|本体の厚み (px)
头身一起动|Move head and body together|頭と体を一緒に動かす
上部柔和转动|Upper-body flexibility|上部の柔らかい回転
头身使用连续外形和一张贴图。四肢与耳朵保持独立。|Head and torso share one continuous surface and texture. Limbs and ears stay separate.|頭と胴体は連続した形と1枚の画像を共有します。手足と耳は独立しています。
附属部件|Attachments|追加パーツ
位置按头部比例；尺寸按原始像素。耳朵固定跟随头部。|Positions use head proportions; sizes use source pixels. Ears follow the head rigidly.|位置は頭部の比率、寸法は元画像のピクセル単位です。耳は頭部に固定して追従します。
人耳|Human ears|人の耳
猫耳|Cat ears|猫耳
长耳|Long ears|長い耳
左侧|Left|左
右侧|Right|右
编辑耳朵参数|Edit ear shape|耳の形状を編集
收起耳朵参数|Hide ear details|耳の詳細を閉じる
删除这一只|Remove ear|この耳を削除
删除这一对|Remove pair|両耳を削除
左右位置|Side position|左右位置
上下位置|Height position|上下位置
前后位置|Depth position|前後位置
耳根宽度（px）|Root width (px)|根元の幅 (px)
耳朵长度（px）|Ear length (px)|耳の長さ (px)
耳朵厚度（px）|Ear depth (px)|耳の厚み (px)
耳尖宽度|Tip width|先端の幅
向外张开|Outward angle|外向きの角度
前后倾斜|Forward lean|前後の傾き
耳朵扭转|Ear twist|耳のひねり
圆锥形|Cone|円錐
角锥形|Pyramid|角錐
展开塑形参数|Shape details|形状の詳細
收起塑形参数|Hide shape details|形状の詳細を閉じる
截面比例|Section profile|断面の比率
前后轮廓|Front / back profile|前後の輪郭
局部凸起|Local projection|局所の突起
顶部宽度|Top width|上部の幅
中部宽度|Middle width|中央の幅
底部宽度|Bottom width|下部の幅
顶部厚度|Top depth|上部の厚み
中部厚度|Middle depth|中央の厚み
底部厚度|Bottom depth|下部の厚み
前侧顶部（px）|Upper front (px)|前面上部 (px)
前侧中部（px）|Middle front (px)|前面中央 (px)
前侧底部（px）|Lower front (px)|前面下部 (px)
后侧顶部（px）|Upper back (px)|背面上部 (px)
后侧中部（px）|Middle back (px)|背面中央 (px)
后侧底部（px）|Lower back (px)|背面下部 (px)
中段弯曲（px）|Curve (px)|中央の曲がり (px)
凸起长度（px）|Projection length (px)|突起の長さ (px)
凸起宽度|Projection width|突起の幅
凸起高度|Projection height|突起の高さ
凸起上下位置|Projection height offset|突起の上下位置
凸起末端宽度|Tip fullness|先端の幅
播放方式|Playback|再生方法
循环|Loop|ループ
播放一次|Play once|1回再生
保持末帧|Hold last frame|最後の姿勢を維持
时间与融合设置|Timing and blend|タイミングと合成
开始位置|Start position|開始位置
占整段比例|Active duration|動作の長さ
淡入淡出|Fade in / out|フェード
挥手部位|Waving arm|手を振る腕
双侧配合|Both sides|左右の連携
同步|Together|同時
交替|Alternating|交互
使用说明|User guide|使い方
按住看修改前|Hold: before|長押しで変更前
单视图|Single view|単一ビュー
贴图已适配新外形；按住查看修改前，继续绘画前请生成新素材。|Textures adapted. Hold Before to compare; prepare new painting files before editing.|画像を新形状に調整しました。変更前と比較し、描画を続ける前に新しい素材を作成してください。
开始 / 继续绘制|Start / resume painting|描画を開始・再開
打开绘画文件夹|Open painting folder|描画フォルダーを開く
切换绘画文件夹|Change painting folder|描画フォルダーを変更
选择绘画文件夹|Choose painting folder|描画フォルダーを選択
重新读取|Reload files|ファイルを再読込
自动刷新|Auto refresh|自動更新
高级贴图操作|Advanced texture tools|テクスチャ詳細操作
选择绘画文件夹，保存 PNG 后自动更新。|Choose a painting folder. Save a PNG to update the preview.|描画フォルダーを選択し、PNGを保存すると表示が更新されます。
适配到新绘画文件夹|Create adapted painting copy|調整した描画コピーを作成
共用左侧贴图|Share left texture|左の画像を共有
请先关闭共用左侧贴图，再独立绘制右侧。|Disable Share left texture to paint this side independently.|右側を個別に描くには、左の画像共有を解除してください。
绘画文件已连接|Painting file connected|描画ファイル接続済み
贴图已更新|Texture updated|画像更新済み
等待文件保存完成|Waiting for file save|ファイル保存を待機中
绘画文件缺失|Painting file missing|描画ファイルがありません
文件暂不可读，保留上次贴图|Unreadable file; keeping last texture|読込不可：前の画像を維持
需要更新绘画模板|Painting template needs updating|描画テンプレートの更新が必要
匹配当前布局|Matches current layout|現在の配置と一致
尺寸符合，来源未知|Size fits; UV source unknown|サイズ一致・UV情報なし
贴图已适配，请检查细节|Adapted texture; check details|画像を調整済み：細部を確認
已内嵌贴图|Embedded texture|埋め込み画像
内置贴图|Built-in texture|標準画像
使用单独绘画文件|Separate painting file|個別の描画ファイル
贴图修改仅在应用后写入当前项目|Texture changes stay in preview until applied.|画像の変更は適用するまでプレビューのみです。
外形已改变；旧绘画文件不再匹配，请生成适配副本。|Shape changed. Create an adapted copy before continuing to paint.|形状が変更されました。描画を続けるには調整コピーを作成してください。
正在导出…|Exporting…|書き出し中…
新建|New|新規
打开|Open|開く
保存|Save|保存
撤销|Undo|元に戻す
取消|Cancel|キャンセル
导出序列帧|Export frames|フレームを書き出す
基础动作|Base motion|基本モーション
调整基础动作|Edit base motion|基本モーションを調整
从姿势开始…|Start from a pose…|ポーズから開始…
叠加动作|Motion layers|追加モーション
＋ 添加|+ Add|＋ 追加
移除|Remove|削除
整体控制|Body controls|全体の調整
全身|Whole body|全身
双臂|Both arms|両腕
双腿|Both legs|両脚
左臂|Left arm|左腕
右臂|Right arm|右腕
左腿|Left leg|左脚
右腿|Right leg|右脚
腰 / 躯干|Torso|胴体
头颈|Head / neck|頭・首
部位分色|Part colors|部位別の色
交叠留缝|Overlap gaps|重なりの隙間
灰色外边线|Gray outline|グレーの輪郭線
完美像素（1px）|Pixel perfect (1px)|ピクセルパーフェクト（1px）
IK 手柄|IK handles|IK ハンドル
朝向|Direction|向き
导出视角|Export view|書き出す視点
焦点视图|Focused view|選択中の視点
按住看基础|Hold: base|長押しで基本を表示
一轮|Duration|長さ
▶ 播放|▶ Play|▶ 再生
■ 暂停|■ Pause|■ 一時停止
正面|Front|正面
侧面|Side|側面
斜面|3/4|斜め
斜俯|Elevated|斜め上
焦点|Focused|選択中
自选姿势|Custom pose|カスタムポーズ
动作|Motion|モーション
站姿|Idle|待機
站立|Stand|立つ
走路|Walk|歩く
跑步|Run|走る
挥手|Wave|手を振る
举手|Raise arms|腕を上げる
伸展|Stretch|伸び
蹲下|Squat|しゃがむ
下蹲|Crouch|しゃがみ姿勢
弹跳|Jump|ジャンプ
弯腰|Bow|お辞儀
摇头|Shake head|首を横に振る
点头|Nod|うなずく
伸手|Reach|手を伸ばす
搬物|Carry|物を運ぶ
推东西|Push|押す
敬礼|Salute|敬礼
踢腿|Kick|キック
挥拳|Punch|パンチ
攀爬|Climb|登る
影响比例|Influence|影響度
保留原摆动|Keep base swing|元の振りを残す
作用部位|Affects|対象部位
相关部位|All relevant parts|関連する部位
暂时关闭|Disable layer|一時的に無効
启用动作|Enable layer|有効にする
抬起 / 放下|Raise / lower|上げる・下げる
前伸 / 后摆|Forward / back|前方・後方
弯曲|Bend|曲げる
摆动幅度|Swing range|振り幅
低头 / 抬头|Look down / up|下を向く・上を向く
左右歪头|Head tilt|頭を傾ける
弯腰 / 后仰|Lean forward / back|前屈・後屈
身体高低|Body height|体の高さ
左右倾斜|Body tilt|体を傾ける
调整身体时保持脚的位置|Keep feet planted|足の位置を固定
翻转肘 / 膝弯向|Flip elbow / knee|肘・膝の曲がる向きを反転
重置这个部位|Reset this part|この部位をリセット
上段松软|Upper softness|上側の柔らかさ
下段松软|Lower softness|下側の柔らかさ
头颈松软|Head / neck softness|頭・首の柔らかさ
回弹|Bounce|弾み
这一轮做几次|Cycles|繰り返し回数
步幅|Stride|歩幅
抬腿|Knee lift|脚の持ち上げ
摆臂|Arm swing|腕の振り
上下颠|Body bounce|体の上下動
肘弯|Elbow bend|肘の曲げ
呼吸|Breathing|呼吸
重心晃|Sway|体の揺れ
举多高|Raise height|上げる高さ
挥几下|Waves|振る回数
摆多开|Swing width|振る広さ
分开|Spread|広げる
幅度|Amount|大きさ
摇几下|Shakes|横振りの回数
点几下|Nods|うなずく回数
弯多少|Bend amount|曲げる量
停一下|Hold|止める長さ
伸多开|Stretch amount|伸ばす量
后仰|Lean back|後ろに反る
蹲多深|Squat depth|しゃがむ深さ
弹多高|Jump height|跳ぶ高さ
收腿|Tuck legs|脚を引き寄せる
导出目录|Output directory|出力先
导出名称|Export name|書き出し名
输出比例|Output scale|出力倍率
1x = 64 × 64；仅整数倍最近邻放大。|1x = 64 × 64. Integer nearest-neighbor scaling only.|1x = 64 × 64。整数倍率・最近傍で拡大。
输出比例必须是 1 到 8 的整数|Output scale must be an integer from 1 to 8.|出力倍率は1～8の整数を指定してください。
创建同名子文件夹|Create a subfolder with this name|同名のサブフォルダーを作成
同名文件已存在，请更换名称或目录|A file with this name exists. Choose another name or directory.|同名のファイルがあります。名前か出力先を変更してください。
选择…|Browse…|選択…
选择导出目录|Choose output directory|出力先を選択
名称（将在所选目录内创建同名文件夹）|Name (creates a folder with this name)|名前（同名のフォルダーを作成）
PNG 序列 · 透明背景|PNG frames · transparent|PNG 連番・透過背景
PNG 横向条带 · 透明背景|PNG strip · transparent|PNG 横並びシート・透過背景
GIF 动画预览|Animated GIF preview|GIF プレビュー
JSON 动作配方|JSON motion recipe|JSON モーション設定
开始导出|Export|書き出す
请选择导出目录|Choose an output directory.|出力先を選択してください。
请至少选择一种文件类型|Select at least one file type.|形式を一つ以上選択してください。
同名文件夹已存在，请更换名称或目录|That folder exists. Choose another name or directory.|同名のフォルダーがあります。名前か出力先を変更してください。
动作配方|Motion recipe|モーション設定
选择基础姿势|Choose a base pose|基本ポーズを選択
无法打开|Cannot open|開けません
保存失败|Save failed|保存に失敗
未知基础动作|Unknown base motion|不明な基本モーション
请换一个导出名称|Choose another export name.|別の名前を指定してください。
请选择至少一种有效的导出类型|Select at least one valid export format.|有効な形式を一つ以上選択してください。
名称不能为空，或包含路径与文件名禁用字符|Enter a valid name without path characters.|パス文字を含まない有効な名前を入力してください。
请选择新版动作工坊的配方；旧版文件保留在原工具中。|Choose a current Studio recipe. Open older files in the original tool.|現在の工房の設定を選択してください。旧形式は元のツールで開けます。
控制作用于整段动作\n基础件始终保留|Edits affect the whole motion.\nThe base stays available.|調整はモーション全体に適用。\n基本モーションは保持されます。
物理跟随 · 随身体运动产生惯性|Physics · inertia from body motion|物理追従・体の動きによる慣性
物理跟随请选左 / 右单个部位设置。|Select an individual limb to adjust physics.|物理設定は左右の部位を個別に選択してください。
直接调动作的整体感觉，不需要编辑关键帧。|Adjust the whole motion without keyframes.|キーフレームなしで動き全体を調整できます。
脚部锁定受腿长限制；小幅调整身体高低时更自然。|Foot locking is limited by leg length. Use small height changes.|足の固定には脚の長さの制限があります。高さは少しずつ調整してください。
姿态和摆动分别混合。比例为 0 时完全回到原动作。|Pose and swing blend separately. Zero influence restores the base motion.|姿勢と振りを個別に混合します。影響度 0 で元の動きに戻ります。
摆幅围绕动作的平均姿势变化；抬起手臂也会保留原来的摆动。|Swing scales around the average pose. Raised arms retain their motion.|平均姿勢を中心に振り幅を調整します。腕を上げても元の振りは残ります。
先用较小松软程度。强度为 0 时恢复原动作，导出与预览使用同一模拟结果。|Start with low softness. Zero restores the motion. Preview and export share the simulation.|柔らかさは小さめから。0 で元の動きに戻り、プレビューと出力は同じシミュレーションを使います。
选择部位调整整段动作；暂停后拖动手脚，四个视图同步。|Select a part to edit the whole motion. Pause to drag handles in any view.|部位を選んで動き全体を調整。一時停止してハンドルをドラッグできます。
正在更新动作… 可继续调整|Updating motion… You can keep editing.|更新中… 引き続き調整できます。
动作已更新 · 点击视图切换焦点，导出默认跟随焦点|Motion updated · Click a view to focus it. Export follows focus.|更新完了・視点をクリックして選択。書き出しは選択中の視点を使用。
已调整整段动作的姿态；其他视图同步。拖腰可移动身体，拖躯干 / 头可转动。|Pose updated in every view. Drag the waist to move, torso or head to rotate.|全視点を更新。腰をドラッグして移動、胴体・頭をドラッグして回転。
FellowStudio · 动作工坊|FellowStudio · Motion Workshop|FellowStudio · モーション工房
角色模型|Character model|キャラクターモデル
载入模型|Load model|モデルを読み込む
保存模型|Save model|モデルを保存
重置全部|Reset all|すべてリセット
应用模型|Apply model|モデルを適用
左右联动|Link left / right|左右を連動
躯干高度|Torso height|胴体の高さ
肩部宽度|Shoulder width|肩幅
躯干厚度|Torso thickness|胴体の厚み
腰部宽度|Waist width|ウエスト幅
胯部宽度|Hip width|腰幅
头部大小|Head size|頭の大きさ
头部间距|Head gap|頭と胴体の間隔
上段长度（px）|Upper length (px)|上側の長さ（px）
下段长度（px）|Lower length (px)|下側の長さ（px）
肢体粗细|Limb thickness|手足の太さ
关节向外偏移（px）|Socket outward (px)|関節を外へ（px）
关节上下偏移（px）|Socket height (px)|関節の高さ（px）
接合间距（px）|Joint gap (px)|接合部の間隔（px）
贴合接合|Connected socket|接合部をつなぐ
模型修改仅在应用后写入当前项目|Changes stay in preview until you apply them.|変更は適用するまでプレビュー内に留まります。
长度和间距按原始像素计算；主动留出的间距不会自动补齐。|Lengths and gaps use source pixels. Deliberate gaps are not bridged.|長さと間隔は元画像のピクセル単位です。意図的な隙間は自動で埋めません。

"""
CATALOG={}
for row in ROWS.strip().splitlines():
    zh,en,ja=row.split('|');CATALOG[zh.replace('\\n','\n')]={'en':en.replace('\\n','\n'),'ja':ja.replace('\\n','\n'),'zh':zh.replace('\\n','\n')}
def set_language(code):
    global language
    language=code if code in LANGUAGES else 'en'
def tr(text):
    text=str(text)
    if text in CATALOG:return CATALOG[text][language]
    for prefix,en,ja in [('已导出：','Exported: ','書き出し完了: '),('已保存：','Saved: ','保存完了: '),('保存失败：','Save failed: ','保存に失敗: '),('预览更新失败：','Preview failed: ','プレビュー更新に失敗: '),('未覆盖原配方：','Original recipe preserved: ','元の設定を保持: ')]:
        if text.startswith(prefix):return (prefix if language=='zh' else en if language=='en' else ja)+text[len(prefix):]
    for prefix,en,ja in [('整体控制 · ','Body · ','部位 · '),('基础 · ','Base · ','基本 · '),('叠加 · ','Layer · ','追加 · ')]:
        if text.startswith(prefix):return (prefix if language=='zh' else en if language=='en' else ja)+tr(text[len(prefix):])
    if text.startswith(('● ','○ ')):return text[:2]+tr(text[2:])
    if text.endswith(' · 焦点'):return tr(text[:-5])+' · '+tr('焦点')
    if text.endswith(' 秒'):return text[:-2]+{'en':' s','zh':' 秒','ja':' 秒'}[language]
    return text

CATALOG.update({
 '跟随胸腔转动':{'zh':'跟随胸腔转动','en':'Follow chest turn','ja':'胸の回転に追従'},
 '边线颜色':{'zh':'边线颜色','en':'Outline color','ja':'輪郭の色'},
 '外边线':{'zh':'外边线','en':'Outline','ja':'輪郭線'},
 '自动灰色':{'zh':'自动灰色','en':'Automatic gray','ja':'自動グレー'},
 'RGB 色值（#RRGGBB）':{'zh':'RGB 色值（#RRGGBB）','en':'RGB color (#RRGGBB)','ja':'RGB 色 (#RRGGBB)'},
 '请输入 #RRGGBB 格式的颜色':{'zh':'请输入 #RRGGBB 格式的颜色','en':'Enter a color as #RRGGBB','ja':'#RRGGBB 形式で入力してください'},
 '应用':{'zh':'应用','en':'Apply','ja':'適用'},
 '头部前后位置（px）':{'zh':'头部前后位置（px）','en':'Head forward / back (px)','ja':'頭の前後位置 (px)'},
 '左右转头':{'zh':'左右转头','en':'Turn head','ja':'首を左右に回す'},
 '胸腔转向':{'zh':'胸腔转向','en':'Chest turn','ja':'胸の回転'},
 '骨盆转向':{'zh':'骨盆转向','en':'Pelvis turn','ja':'骨盤の回転'},
 '跨步扭转':{'zh':'跨步扭转','en':'Stride twist','ja':'歩行のひねり'},
 '基础形状':{'zh':'基础形状','en':'Base shape','ja':'基本形状'},
 '椭圆头':{'zh':'椭圆头','en':'Ellipsoid','ja':'楕円体'},
 '圆柱形':{'zh':'圆柱形','en':'Cylinder','ja':'円柱'},
 '圆角方形':{'zh':'圆角方形','en':'Rounded box','ja':'角丸ボックス'},
 '方形':{'zh':'方形','en':'Box','ja':'ボックス'},
 '收腰躯干':{'zh':'收腰躯干','en':'Tapered torso','ja':'くびれ胴体'},
 '筒形躯干':{'zh':'筒形躯干','en':'Barrel torso','ja':'筒形胴体'},
 '胶囊形':{'zh':'胶囊形','en':'Capsule','ja':'カプセル'},
 '胯部覆盖（px）':{'zh':'胯部覆盖（px）','en':'Pelvis coverage (px)','ja':'骨盤の深さ (px)'}
})

CATALOG.update({
 '关节内外偏移（px）':{'zh':'关节内外偏移（px）','en':'Socket in / out (px)','ja':'関節の内外移動 (px)'},
 '偏移可为负：关节向内、接合重叠；正值向外、分离。长度按原始像素计算。':{
 'zh':'偏移可为负：关节向内、接合重叠；正值向外、分离。长度按原始像素计算。',
 'en':'Negative offsets move sockets inward or overlap joints; positive values move outward or separate them. Lengths use source pixels.',
 'ja':'負の値で関節を内側へ、接合を重ねます。正の値で外側へ、間隔を広げます。長さは元画像のpx単位です。'}
})

# Game actions and reusable motion resources.
for row in '''姿势层|Pose layer|ポーズレイヤー
起跳与落地|Jump and land|ジャンプと着地
刺击|Thrust|突き
挥击|Swing attack|振り攻撃
踢击|Kick|キック
受击|Hit reaction|被弾
倒地|Fall|倒れる
起身|Get up|起き上がる
翻滚|Roll|ローリング
攀爬循环|Climb cycle|登るループ
原地转身|Turn in place|その場で振り向く
动作案例…|Motion examples…|動作のサンプル…
载入姿势…|Load pose…|ポーズを読み込む…
保存姿势…|Save pose…|ポーズを保存…
使用当前帧姿势|Capture current pose|現在のポーズを取得
保持地面接触|Keep ground contact|地面との接触を維持
显示贴图|Show textures|テクスチャを表示
总帧数|Frames|総フレーム数
画幅 Y（px）|Frame Y (px)|画面 Y (px)
整体朝向|Whole-body facing|全身の向き
整体朝向转动全身；胸腔和骨盆分别扭转。锁脚时脚的位置保持。|Facing turns the whole character; chest and pelvis twist separately. Foot locking keeps the feet in place.|全身の向きと胸・骨盤のひねりは別です。足の固定中は足位置を保ちます。
结束位置|End position|終了位置
接触方式|Contact mode|接地方法
踢腿方式|Kick style|キックの種類
摆踢|Swing kick|振り上げキック
踹腿|Push kick|前蹴り
扭腰回正|Waist twist|腰ひねり
扭腰角度（度）|Twist angle (deg)|ひねり角度 (度)
骨盆跟随|Pelvis follow|骨盤の追従
后仰 / 弯腰（度）|Back / forward bend (deg)|後屈 / 前屈 (度)
前倾 / 后仰（度）|Forward / backward lean (deg)|前傾 / 後傾 (度)
双腿开合（度）|Leg spread (deg)|脚の開閉 (度)
骨盆 / 上身先行|Pelvis / upper-body lead|骨盤 / 上半身の先行
侧向弯曲|Side bend|横方向の曲げ
前后屈伸|Forward / backward joint bend|前後方向の関節曲げ
负值后仰，正值弯腰。|Negative bends backward; positive bends forward.|負は後屈、正は前屈です。
双腿开合：负值内收，正值外展。|Leg spread: negative brings legs inward; positive opens them.|脚の開閉：負は内側、正は外側です。
摆动幅度为负值时，围绕原姿态反向摆动。|Negative motion range reverses movement around the original pose.|振り幅が負の場合、元の姿勢を中心に動きを反転します。
取放物品|Pick up / put down|拾う・置く
取放方向|Action direction|動作の方向
从地上捧起|Pick up|拾い上げる
放回地面|Put down|地面に置く
取物弯腰（度）|Reach bend (deg)|拾うときのお辞儀 (度)
取物下蹲|Reach crouch|拾うときのしゃがみ
向前够取（度）|Forward reach (deg)|前へ伸ばす角度 (度)
举起高度（度）|Lift height (deg)|持ち上げる高さ (度)
举起屈肘（度）|Lift elbow bend (deg)|持ち上げるときの肘の曲げ (度)
双手间距（度）|Hand spacing (deg)|両手の間隔 (度)
够到物品的时刻|Reach timing|物に触れる時点
举手方向|Raise direction|腕を上げる方向
向两侧|Sideways|横へ
向前|Forward|前へ
屈肘（度）|Elbow bend (deg)|肘の曲げ (度)
高举时手肘会逐渐伸直；取物下蹲会按模型比例适配。|Elbows straighten for overhead lifts. Ground reach adapts to body proportions.|高く上げるほど肘を伸ばします。拾う姿勢は体型に合わせて調整します。
需要完整身体带动时，将作用部位设为“相关部位”。|Choose All relevant parts to include the full body follow-through.|体全体を連動させるには、作用部位を「関連部位」にしてください。
跟随基础动作|Follow base motion|基本動作に従う
地面翻滚|Ground roll|地上ローリング
空中翻滚|Aerial roll|空中回転
叠加选定部位的改动，原动画保留。|Adds changes to selected parts while keeping the base motion.|選択部位の変化を加算し、元の動作を保ちます。
动作侧|Action side|動作する側
右侧|Right|右
左侧|Left|左
双侧|Both|両側
上半身|Upper body|上半身
下半身|Lower body|下半身
融合方式|Blend mode|合成方法
姿态与摆动|Pose and motion|姿勢と動き
替换选中部位|Replace selected parts|選択部位を置換
叠加变化|Add changes|変化を加算
跳跃高度（px）|Jump height (px)|ジャンプの高さ (px)
准备下蹲|Preparation crouch|準備のしゃがみ
腾空收腿|Airborne tuck|空中で脚を畳む
准备时间|Preparation time|準備時間
落地时间|Landing time|着地時間
腾空前倾|Airborne lean|空中の前傾
攻击幅度|Attack reach|攻撃の大きさ
攻击仰角|Attack elevation|攻撃の仰角
蓄力时间|Anticipation time|溜め時間
蓄力幅度|Wind-up amount|溜め動作の大きさ
发力时间|Strike time|攻撃時間
身体带动|Body follow-through|体の連動
横扫 / 下劈|Sweep / overhead|横振り / 振り下ろし
受击强度|Impact strength|衝撃の強さ
受力方向（度）|Impact direction (deg)|衝撃方向 (度)
冲击时间|Impact time|衝撃時間
恢复程度|Recovery amount|回復量
倒地方向（度）|Fall direction (deg)|倒れる方向 (度)
失衡准备|Loss of balance|崩れの準備
蜷缩程度|Curl amount|体を丸める
翻滚方向（度）|Roll direction (deg)|転がる方向 (度)
移动距离（px）|Travel distance (px)|移動距離 (px)
攀爬幅度|Climbing reach|登る動きの幅
手脚张开|Hand / foot spacing|手足の間隔
身体起伏|Body bob|体の上下動
转身角度|Turn angle|旋回角度
上身先行|Upper-body lead|上半身を先行
移动方向（度）|Travel direction (deg)|移動方向 (度)
脚步间距|Stance width|足の間隔
支撑时间比例|Support time|支持時間の割合'''.splitlines():
 zh,en,ja=row.split('|');CATALOG[zh]={'zh':zh,'en':en,'ja':ja}

# Painting file validation messages.
CATALOG.update({'Use a PNG image': {'en': 'Use a PNG image', 'zh': '请选择 PNG 图片', 'ja': 'PNG画像を選択してください'}, 'PNG size does not match. Prepare painting files for this model.': {'en': 'PNG size does not match. Prepare painting files for this model.', 'zh': 'PNG 尺寸不匹配，请为当前模型生成绘画素材。', 'ja': 'PNGサイズが一致しません。現在のモデル用に描画素材を作成してください。'}, 'Choose the painting PNG, not the guide image.': {'en': 'Choose the painting PNG, not the guide image.', 'zh': '请选择绘画 PNG，不要选择参考线图片。', 'ja': 'ガイド画像ではなく描画用PNGを選択してください。'}, 'This texture belongs to another body part.': {'en': 'This texture belongs to another body part.', 'zh': '这张贴图属于其他身体部位。', 'ja': 'この画像は別の部位用です。'}, 'This texture uses another model surface or UV layout. Adapt the painting files first.': {'en': 'This texture uses another model surface or UV layout. Adapt the painting files first.', 'zh': '这张贴图的模型表面或 UV 布局不匹配，请先生成适配副本。', 'ja': 'モデル表面またはUV配置が異なります。先に調整コピーを作成してください。'}, 'Choose a FellowStudio3D painting folder': {'en': 'Choose a FellowStudio3D painting folder', 'zh': '请选择本工具生成的绘画文件夹', 'ja': '本ツールの描画フォルダーを選択してください'}, 'This painting folder uses another model. Prepare a new folder for the current appearance.': {'en': 'This painting folder uses another model. Prepare a new folder for the current appearance.', 'zh': '绘画文件夹对应其他模型，请为当前外形生成新的素材文件夹。', 'ja': '別のモデル用フォルダーです。現在の形状用に新しい描画フォルダーを作成してください。'}, 'This UV pack belongs to different model surfaces. Restore the matching appearance or adapt the painting files first.': {'en': 'This UV pack belongs to different model surfaces. Restore the matching appearance or adapt the painting files first.', 'zh': '这套贴图对应其他表面形状，请恢复匹配外形或先适配绘画文件。', 'ja': '表面形状が異なります。対応する形状に戻すか描画素材を調整してください。'}})
