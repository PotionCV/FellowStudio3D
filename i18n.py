"""UI text catalogs; recipe keys and user names stay language-independent."""
LANGUAGES={'en':'English','zh':'简体中文','ja':'日本語'}
language='en'
ROWS=r"""
部件|Part|パーツ
后发|Back hair|後ろ髪
头部外形|Head shape|頭部の外形
主体外形|Body shape|本体の外形
头发主体|Hair body|髪の本体
左中发束|Left middle lock|左の中間髪束
右中发束|Right middle lock|右の中間髪束
自由发束|Free lock|自由な髪束
头发部件|Hair components|髪のパーツ
已添加部件|Added components|追加済みパーツ
添加部件|Add component|パーツを追加
发型模板…|Hairstyle templates…|髪型テンプレート…
收起发型模板|Hide hairstyle templates|髪型テンプレートを閉じる
替换为模板|Replace with template|テンプレートに置き換え
发束类型|Lock type|髪束の種類
耳朵|Ears|耳
模板只负责一次生成部件；应用模板会替换当前头发，模型应用前仍可取消。|Templates generate components once. Applying one replaces the current hair; cancel the model editor to discard changes.|テンプレートはパーツを一度生成します。適用すると現在の髪を置き換え、モデルを確定するまではキャンセルできます。
从头发主体、左右刘海或左右中发束开始添加。|Start with a hair body, left/right fringe or middle locks.|髪の本体、左右の前髪、左右の中間髪束から追加できます。
自由组合的位置相对头部；发顶跟随头部，发束各有独立骨骼。使用发型模板会替换当前头发部件。|Positions are head-local. Hair bodies follow the head; each lock has independent bones. Applying a template replaces the current hair components.|位置は頭を基準にします。本体は頭に追従し、髪束はそれぞれ独立した骨格を持ちます。テンプレートを適用すると現在の髪パーツを置き換えます。
单独添加发顶|Add cap only|頭頂パーツを追加
单独添加发束|Add independent lock|独立した髪束を追加
发顶造型|Cap shape|頭頂部の形
独立发束|Independent lock|独立した髪束
自定义组合|Custom assembly|自由な組み合わせ
复制发片|Duplicate part|髪パーツを複製
镜像复制发片|Mirror duplicate|対称パーツを追加
删除发片|Delete part|髪パーツを削除
将此束对称到另一侧|Mirror this lock to its partner|この髪束を相手側に対称コピー
发片位置与细节|Part placement & details|髪パーツの位置と詳細
收起发片细节|Hide part details|髪パーツの詳細を閉じる
发顶宽度（px）|Cap width (px)|頭頂部の幅 (px)
发顶高度（px）|Cap height (px)|頭頂部の高さ (px)
发顶厚度（px）|Cap depth (px)|頭頂部の厚さ (px)
前额发际线|Front hairline|前の生え際
后侧覆盖|Back coverage|後ろの覆い
顶部平缓|Crown flatness|頭頂部の平坦さ
顶部宽度比例|Crown width ratio|頭頂の幅の比率
发顶左右（px）|Cap X (px)|頭頂部の左右 (px)
发顶上下（px）|Cap Y (px)|頭頂部の上下 (px)
发顶前后（px）|Cap depth offset (px)|頭頂部の前後 (px)
圆润发顶|Rounded crown|丸い頭頂部
圆角发顶|Soft square crown|角丸の頭頂部
方形发顶|Square crown|四角い頭頂部
平顶发型|Flat crown|平らな頭頂部
尖顶发型|Pointed crown|尖った頭頂部
可以单独添加发顶或发束，自由组合。|Add caps or locks independently to build your hairstyle.|頭頂パーツと髪束を個別に追加して自由に組み合わせられます。
自由组合的位置相对头部；发顶跟随头部，发束各有独立骨骼。切换整套发型会替换当前组合。|Assembly positions are head-local. Caps follow the head; each lock has its own bones. Changing a full style replaces this assembly.|自由な組み合わせの位置は頭を基準にします。頭頂部は頭に追従し、各髪束は独立した骨格を持ちます。髪型を切り替えると現在の組み合わせを置き換えます。
双马尾对称编辑|Edit twin tails symmetrically|ツインテールを対称編集
以左侧对称|Mirror left to right|左から右へ対称コピー
以右侧对称|Mirror right to left|右から左へ対称コピー
整体发型|Whole hairstyle|髪型全体
单束造型|Individual lock|髪束の形
同步左右发束|Link left / right locks|左右の髪束を連動
单束长度（px）|Lock length (px)|髪束の長さ (px)
单束宽度（px）|Lock width (px)|髪束の幅 (px)
单束厚度（px）|Lock depth (px)|髪束の厚さ (px)
单束弯曲（度）|Lock curl (deg)|髪束の曲げ (度)
发梢饱满|Tip fullness|毛先の丸み
发根宽度比例|Root width ratio|根元の幅の比率
发中宽度比例|Middle width ratio|中間の幅の比率
发束侧倾（度）|Side tilt (deg)|横への傾き (度)
发束前后倾（度）|Forward / back tilt (deg)|前後の傾き (度)
发束转向（度）|Lock yaw (deg)|髪束の向き (度)
发片扭转（度）|Lock twist (deg)|髪束のひねり (度)
发束左右偏移（px）|Lock X offset (px)|髪束の左右オフセット (px)
发束上下偏移（px）|Lock Y offset (px)|髪束の上下オフセット (px)
发束前后偏移（px）|Lock depth offset (px)|髪束の前後オフセット (px)
收起单束细节|Hide lock details|髪束の詳細を閉じる
单束轮廓与位置|Lock profile & placement|髪束の輪郭と位置
重置此发束|Reset this lock|この髪束をリセット
造型独立于动画骨骼。常用项调整轮廓，展开细节可调整根中宽度、朝向和位置。|Shape is separate from animated bones. Expand details for root/middle widths, orientation and placement.|造形とアニメーションの骨格は独立しています。詳細を開くと根元・中間の幅、向き、位置を調整できます。
偏移相对发型默认位置；重置回到当前发型。切换整套发型会重置单束造型，保留原贴图。|Offsets are relative to this style. Reset restores the style defaults. Changing style resets lock shapes and retains textures.|オフセットは髪型の標準位置からの相対値です。髪型を切り替えると髪束の造形をリセットし、テクスチャを保持します。
尾尖粗细|Tip thickness|尾先の太さ
头发|Hair|髪
头发与发型|Hair & hairstyle|髪と髪型
头部形状|Head shape|頭の形
发型|Hairstyle|髪型
短碎发|Short crop|ショート
波波头|Bob cut|ボブ
长直发|Long straight|ロングストレート
高马尾|High ponytail|ハイポニーテール
双马尾|Twin tails|ツインテール
发顶|Hair cap|頭頂部
左刘海|Left fringe|左前髪
右刘海|Right fringe|右前髪
左鬓发|Left side lock|左横髪
右鬓发|Right side lock|右横髪
后发 / 马尾|Back lock / ponytail|後ろ髪・ポニーテール
左马尾|Left ponytail|左テール
右马尾|Right ponytail|右テール
发根|Hair root|髪の根元
发中|Hair middle|髪の中間
发梢|Hair tip|毛先
发根松软|Root softness|根元の柔らかさ
发中松软|Middle softness|中間の柔らかさ
发梢松软|Tip softness|毛先の柔らかさ
头发飘动|Hair sway|髪の揺れ
飘动幅度（度）|Sway (deg)|揺れ幅 (度)
向后扬起（度）|Backward lift (deg)|後方への持ち上げ (度)
发梢跟随|Tip follow-through|毛先の追従
发束长度（px）|Lock length (px)|髪束の長さ (px)
头发蓬松（px）|Hair volume (px)|髪のボリューム (px)
刘海长度（px）|Fringe length (px)|前髪の長さ (px)
分缝偏向|Parting|分け目
发束张开（度）|Lock spread (deg)|髪束の開き (度)
头发左右（px）|Hair X (px)|髪の左右 (px)
头发上下（px）|Hair Y (px）|髪の上下 (px)
头发前后（px）|Hair depth (px)|髪の前後 (px)
添加头发|Add hair|髪を追加
移除头发|Remove hair|髪を削除
收起头发细节|Hide hair details|髪の詳細を閉じる
发束与位置细节|Lock & placement details|髪束と位置の詳細
当前发型没有可动发束。|This hairstyle has no movable locks.|この髪型には可動する髪束がありません。
独立发顶、刘海和发束，不替换脸部贴图。应用后可在整体控制中调整头发骨骼与松软。|Separate cap, fringe and locks keep your face texture. After Apply, use Hair controls for bones and softness.|頭頂・前髪・髪束は独立し、顔のテクスチャを保持します。適用後に髪の骨格と柔らかさを調整できます。
发顶固定跟随头部；发束使用三节骨骼。换发型保留已有绘画，新增发片提供可改画的基础发色。|The cap follows the head; locks have three bones. Switching styles retains existing painting; new parts start with an editable base color.|頭頂部は頭に追従し、髪束には3関節があります。髪型を変えても既存の描画を保持し、新しい部分には編集可能な基本色が入ります。
动画：整体控制 → 头发。主动飘动可添加“头发飘动”动作层；各发片在UV窗口独立绘画。长发仍需检查肩背穿插。|Animate via Body controls → Hair, or add Hair sway. Paint each part in UV. Check long hair for shoulder/back intersections.|全体調整 → 髪、または髪の揺れレイヤーで動かせます。各部分はUVで描画できます。長髪と肩・背中の交差を確認してください。
发顶固定跟随头部。发束可以单独摆姿势，叠加“头发飘动”后继续融合。|The cap follows the head. Pose locks independently and blend with a Hair sway layer.|頭頂部は頭に追従します。髪束を個別にポーズ調整し、髪の揺れレイヤーと合成できます。
短发默认更硬，长发和马尾更柔软。松软为0时仅保留主动动作；尚无肩背碰撞。|Short hair is stiffer; long hair and tails are softer. Zero softness keeps authored motion only. Shoulder/back collisions are not simulated.|短髪は硬め、長髪とテールは柔らかめです。柔らかさ0では手動の動作のみを保持します。肩・背中との衝突判定はありません。
时间安排|Timing overview|時間の配置
动作保留已选角色，角色保留已选动作；应用后可继续编辑。|Motion keeps your character; character keeps your motion. Edit further after applying.|動作はキャラクターを保持し、キャラクターは動作を保持します。適用後も編集できます。
制作动画…|Create animation…|アニメーションを作成…
保存动画…|Save animation…|アニメーションを保存…
保存动画|Save animation|アニメーションを保存
动作顺序|Action order|動作の順序
我的角色|My characters|自分のキャラクター
我的动画|My animations|自分のアニメーション
物品形状|Object shape|物の形状
旧版物品|Legacy object|旧形式の物
长方体|Box|直方体
圆柱体|Cylinder|円柱
球体|Sphere|球体
圆锥体|Cone|円錐
尾巴摆动|Tail motion|しっぽの動作
尾根|Tail root|しっぽの根元
尾中|Tail middle|しっぽの中間
尾尖|Tail tip|しっぽの先端
上下弯曲（度）|Pitch (deg)|上下の曲げ (度)
左右弯曲（度）|Yaw (deg)|左右の曲げ (度)
扭转（度）|Roll (deg)|ひねり (度)
左右摆动（度）|Side sway (deg)|左右の揺れ (度)
上下摆动（度）|Vertical sway (deg)|上下の揺れ (度)
尾尖跟随|Tip follow-through|先端の追従
三段独立骨骼。应用后在整体控制选择尾巴；叠加尾巴摆动可与其他动作融合。|Three independent joints. After Apply, select Tail in body controls; add Tail motion to blend it with other actions.|独立した3関節です。適用後に全体調整のしっぽを選び、しっぽ動作を他の動作と合成できます。
尾根、尾中、尾尖分别控制；可叠加尾巴摆动，并使用影响比例、时段与融合方式。|Control root, middle and tip separately. Tail motion supports mix, timing and blend modes.|根元・中間・先端を個別に調整し、しっぽ動作に影響度・時間・合成方式を設定できます。
创作资源库…|Creation library…|制作ライブラリ…
创作资源库|Creation library|制作ライブラリ
角色库…|Character library…|キャラクターライブラリ…
动作|Motion|動作
角色|Character|キャラクター
快速搭配|Quick combinations|クイック組み合わせ
搜索名称或关键词|Search names or keywords|名前やキーワードで検索
全部|All|すべて
基础步态|Basic locomotion|基本の移動
游戏动作|Game actions|ゲーム動作
动作融合|Motion blends|動作の合成
姿势表演|Pose performances|ポーズの演技
表情角色|Expressive characters|表情付きキャラクター
装备角色|Equipped characters|装備キャラクター
布偶伙伴|Plush buddies|ぬいぐるみの仲間
基础造型|Basic shapes|基本形状
当前角色|Current character|現在のキャラクター
当前动作|Current motion|現在の動作
应用搭配|Apply combination|組み合わせを適用
还原本次选择|Reset selections|選択をリセット
载入文件…|Load file…|ファイルを読み込む…
选择资源后先预览，应用后才修改项目。|Preview resources first; the project changes only on Apply.|素材をプレビューし、適用するとプロジェクトを変更します。
点击条目，使用当前搭配预览。|Select an item to preview it in your current combination.|項目を選ぶと現在の組み合わせでプレビューします。
预览就绪；应用可撤销。|Preview ready. Applying can be undone.|プレビュー完了。適用後は元に戻せます。
动作保留已选角色；角色保留已选动作。快速搭配同时选择两者，之后仍可分别替换。|Motion keeps your chosen character; character keeps your motion. Quick combinations choose both; each can still be replaced.|動作は選択中のキャラクターを保持し、キャラクターは動作を保持します。クイック組み合わせは両方を選び、後から個別に変更できます。
为新贴图准备绘画|Prepare painting for new texture|新しい画像の描画を準備
新贴图尚未连接绘画文件；开始绘画会创建项目副本，旧文件保留。|The new texture is not connected to painting files yet. Start painting creates a project copy and keeps old files.|新しい画像はまだ描画ファイルと接続していません。開始すると現在の画像をコピーし、旧ファイルを保持します。
脸部正由像素表情覆盖；要手绘眼口，请在角色模型中关闭表情或转为绘画贴图。|Pixel face currently overlays the face. To paint eyes/mouth, disable it or convert it to a painted texture in Character model.|現在はピクセル表情が顔に重なっています。目や口を描くにはモデル画面で無効にするか描画テクスチャへ変換してください。
像素表情…|Pixel face…|ピクセル表情…
像素表情|Pixel face|ピクセル表情
启用像素表情|Enable pixel face|ピクセル表情を有効にする
平静|Neutral|通常
开心|Happy|笑顔
生气|Angry|怒り
惊讶|Surprised|驚き
困倦|Sleepy|眠い
每段眨眼次数|Blinks per clip|動作ごとのまばたき回数
每段说话次数|Mouth beats per clip|動作ごとの口の開閉回数
脸部左右位置|Face horizontal position|顔の左右位置
脸部上下位置|Face vertical position|顔の上下位置
脸部大小|Face size|顔の大きさ
眼睛间距|Eye spacing|目の間隔
脸部位置与颜色|Face placement and colors|顔の位置と色
收起脸部细节|Hide face details|顔の詳細を閉じる
眼口颜色…|Eye/mouth color…|目と口の色…
脸部底色…|Face background…|顔の背景色…
自动取脸部底色|Sample face background|顔の背景色を自動取得
转为绘画贴图|Convert to painted texture|描画テクスチャに変換
在脸部区域覆盖眼口；原贴图保留，关闭可恢复。绘画PNG仍是原图。|Overlays eyes/mouth in the face region. Disable to restore the original. Painting PNGs remain unchanged.|顔の範囲に目と口を重ねます。無効にすると元に戻り、描画PNGは変更しません。
眨眼和说话按整段动画重复，次数为0时关闭；关闭显示贴图时表情隐藏。|Blink/mouth beats repeat over the clip; set 0 to disable. Hiding textures hides the face.|まばたきと口の開閉は動作全体で繰り返し、0で無効です。テクスチャ非表示で顔も隠れます。
转换后关闭自动表情，可继续用UV绘画修改；应用前可取消。|Conversion disables the automatic face so you can paint it in UV. Cancel before Apply to discard.|変換後は自動表情を無効にし、UV描画で編集できます。適用前ならキャンセルできます。
手持道具|Held objects|手持ちの物
手臂外形|Arm shape|腕の形状
复位握持|Reset grip|持ち方をリセット
剑|Sword|剣
法杖|Staff|杖
盾牌|Shield|盾
添加道具|Add object|物を追加
道具长度（px）|Prop length (px)|アイテムの長さ (px)
道具宽度（px）|Prop width (px)|アイテムの幅 (px)
道具厚度（px）|Prop depth (px)|アイテムの厚み (px)
握持俯仰（度）|Grip pitch (deg)|持ち方の前後角度 (度)
握持转向（度）|Grip yaw (deg)|持ち方の向き (度)
握持侧倾（度）|Grip roll (deg)|持ち方の傾き (度)
握点左右（px）|Grip side offset (px)|握り位置の左右 (px)
握点上下（px）|Grip height offset (px)|握り位置の上下 (px)
握点前后（px）|Grip depth offset (px)|握り位置の前後 (px)
握持位置与细节|Grip placement and details|握り位置と詳細
收起握持细节|Hide grip details|握りの詳細を閉じる
换到另一只手|Move to other hand|反対の手に移す
删除道具|Remove prop|アイテムを削除
随手腕移动和转动，独立绘画；尺寸影响UV，握持角度不改变UV。|Follows the wrist and has its own painting. Size affects UVs; grip angles do not.|手首に追従し、個別に描画できます。寸法はUVに影響しますが、持ち方の角度では変わりません。
姿势动画|Pose animation|ポーズアニメーション
姿势动画…|Pose animation…|ポーズアニメーション…
编辑姿势卡…|Edit pose cards…|ポーズカードを編集…
姿势卡|Pose card|ポーズカード
原动作帧|Source frame|元のフレーム
基础动作帧|Base frame|基本動作のフレーム
卡片视图显示原姿势；播放时显示叠加和整体修改。拍数控制相对节奏，时长控制总长度。|Cards show raw poses; playback includes layers and overall edits. Beats set relative timing; duration sets the clip length.|カードは元のポーズを表示し、再生時はレイヤーと全体調整を含めます。拍は相対的なタイミング、長さは全体の秒数です。
采集为姿势卡|Capture pose card|ポーズカードとして取得
应用姿势动画|Apply pose animation|ポーズアニメーションを適用
姿势卡修改仅在应用后写入项目|Pose cards are saved to the project only when applied.|適用するまでポーズカードはプロジェクトに保存されません。
用二至六张姿势卡生成动作；选择卡片后可拖动手脚或调整角度。|Animate two to six pose cards. Select a card, then drag limbs or adjust angles.|2〜6枚のポーズカードから動作を作成します。カードを選び、手足をドラッグするか角度を調整します。
新建时替换原动作与整体修改；已有姿势动画保留叠加与整体修改。应用可撤销。|A new clip replaces motion and overall edits. Editing an existing pose clip retains layers and overall edits. Apply can be undone.|新規作成は動作と全体調整を置き換えます。既存のポーズ動作ではレイヤーと全体調整を保持します。適用は取り消せます。
停留（拍）|Hold (beats)|保持（拍）
过渡（拍）|Transition (beats)|補間（拍）
时长（秒）|Duration (seconds)|長さ（秒）
复制|Duplicate|複製
镜像|Mirror|左右反転
身体高低（px）|Body height (px)|体の高さ (px)
身体左右（px）|Body side offset (px)|体の左右位置 (px)
胸腔转向|Chest turn|胸の向き
骨盆转向|Pelvis turn|骨盤の向き
请选择二至六张姿势卡。|Choose two to six pose cards.|2〜6枚のポーズカードを選んでください。
无效的姿势卡。|Invalid pose card.|無効なポーズカードです。
姿势停留应为0至4拍，过渡应为0.25至4拍。|Hold must be 0–4 beats and transition 0.25–4 beats.|保持は0〜4拍、補間は0.25〜4拍にしてください。
无效的姿势过渡。|Invalid pose transition.|無効なポーズ補間です。
动画时长应为0.25至10秒。|Duration must be 0.25–10 seconds.|長さは0.25〜10秒にしてください。
无效的播放方式。|Invalid playback mode.|無効な再生方式です。
姿势动画需要2至120帧，请缩短时长或调整FPS。|Pose animation needs 2–120 frames. Shorten the duration or adjust FPS.|2〜120フレームが必要です。長さを短くするかFPSを調整してください。
四方向（水平）|Four directions (level)|4方向（水平）
八方向（水平）|Eight directions (level)|8方向（水平）
PNG 方向图集 · 透明背景|Directional PNG atlas · transparent|方向別PNGアトラス・透過
每个方向一行，自动附带帧信息JSON；大图集自动分页。|One row per direction, with frame metadata JSON. Large atlases split into pages automatically.|各方向が1行になり、フレーム情報JSONを付属します。大きな画像は自動で分割します。
方向数必须为4或8。|Use four or eight directions.|4方向または8方向を選んでください。
方向数必须为1、4或8。|Use one, four or eight directions.|1方向・4方向・8方向を選んでください。
尾巴|Tail|しっぽ
长尾|Long tail|長いしっぽ
蓬松尾|Fluffy tail|ふさふさのしっぽ
短圆尾|Bobtail|丸いしっぽ
添加尾巴|Add tail|しっぽを追加
尾根跟随胯部；摆动按整段循环。幅度为0时静止。|The root follows the pelvis; wagging repeats over the clip. Set amplitude to 0 to keep it still.|根元は骨盤に追従し、動作全体に合わせて揺れます。振幅0で静止します。
尾巴长度（px）|Tail length (px)|しっぽの長さ (px)
尾巴粗细（px）|Tail width (px)|しっぽの太さ (px)
尾巴弯曲（度）|Tail curl (deg)|しっぽの曲がり (度)
摆尾幅度（度）|Wag amplitude (deg)|しっぽの振幅 (度)
尾巴厚度（px）|Tail depth (px)|しっぽの厚み (px)
尾巴抬起（度）|Tail lift (deg)|しっぽの持ち上げ (度)
尾根左右（px）|Tail root side (px)|根元の左右 (px)
尾根上下（px）|Tail root height (px)|根元の高さ (px)
尾根前后（px）|Tail root depth (px)|根元の前後 (px)
尾巴朝向（度）|Tail direction (deg)|しっぽの向き (度)
每轮摆尾次数|Wags per clip|動作ごとの揺れ回数
尾巴位置与细节|Tail placement and details|しっぽの位置と詳細
收起尾巴细节|Hide tail details|しっぽの詳細を閉じる
重置尾巴|Reset tail|しっぽをリセット
删除尾巴|Remove tail|しっぽを削除
游泳|Swim|泳ぐ
悬浮|Hover|浮遊
游泳方式|Swimming style|泳ぎ方
蛙泳|Breaststroke|平泳ぎ
自由泳|Front crawl|クロール
踩水|Tread water|立ち泳ぎ
划臂幅度|Arm stroke|腕のかき幅
蹬腿幅度|Kick strength|キックの強さ
浮动幅度（px）|Float bob (px)|浮き沈み (px)
泳姿前后倾（度）|Swimming tilt (deg)|泳ぐ姿勢の傾き (度)
身体滚转（度）|Body roll (deg)|体のロール (度)
离地高度（px）|Hover height (px)|浮遊の高さ (px)
手臂展开（度）|Arm spread (deg)|腕の広がり (度)
拍臂幅度（度）|Arm beat (deg)|羽ばたき幅 (度)
悬空屈腿（度）|Airborne leg bend (deg)|空中の膝曲げ (度)
不锁定地面；可叠加头部、挥手或脱力。|No floor lock; add head motion, waving or softness.|地面には固定しません。頭の動き・手振り・柔らかさを重ねられます。
动作串联…|Action sequence…|動作をつなぐ…
动作串联|Action sequence|動作をつなぐ
选择动作、调整顺序，自动安排先后和过渡。|Choose and reorder actions; timing and transitions are arranged for you.|動作を選んで並べると、順番とつなぎを自動で設定します。
右手直拳|Right straight punch|右ストレート
左手直拳|Left straight punch|左ストレート
右腿踹击|Right push kick|右前蹴り
左腿踹击|Left push kick|左前蹴り
鞠躬|Bow|お辞儀
每步帧数|Frames per step|動作ごとのフレーム数
动作过渡|Transition|つなぎ
柔和|Soft|柔らかく
利落|Snappy|素早く
直接|Direct|直接
生成串联动作|Create sequence|連続動作を作成
保留角色、基础动作和姿态控制；替换叠加动作，可撤销。生成后仍可逐项修改。|Keep the character, base motion and pose controls; replace motion layers. Undo and further editing remain available.|キャラクター・基本動作・姿勢設定は保持し、重ねる動作を置き換えます。元に戻す・個別編集が可能です。
请选择一至六步动作。|Choose one to six actions.|1〜6個の動作を選択してください。
每步帧数应为6至20。|Use 6 to 20 frames per step.|動作ごとに6〜20フレームを指定してください。
继续上次绘制|Resume last painting|前回の描画を再開
上次绘画文件夹：|Last painting folder:|前回の描画フォルダー：
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
尾根松软|Tail root softness|しっぽの根元の柔らかさ
尾中松软|Tail middle softness|しっぽの中間の柔らかさ
尾尖松软|Tail tip softness|しっぽの先端の柔らかさ
保存 PNG…|Save PNG…|PNGを保存…
复制贴图（Ctrl+C）|Copy texture (Ctrl+C)|画像をコピー (Ctrl+C)
粘贴替换（Ctrl+V）|Paste to replace (Ctrl+V)|貼り付けて置換 (Ctrl+V)
贴图已保存|Texture saved|画像を保存しました
贴图已复制；保留原始尺寸与透明度。|Texture copied with original size and transparency.|元のサイズと透明度でコピーしました。
贴图已替换；应用后写入项目，可撤销。|Texture replaced. Apply to keep it; Undo is available.|画像を置換しました。適用すると保存され、元に戻せます。
剪贴板贴图|Clipboard texture|クリップボードの画像
剪贴板正被占用，请重试。|Clipboard is busy. Please try again.|クリップボードを使用中です。もう一度お試しください。
剪贴板中没有图片，请先复制一张 UV 贴图。|Clipboard does not contain an image. Copy a UV image first.|クリップボードに画像がありません。先にUV画像をコピーしてください。
剪贴板图片过大。|Clipboard image is too large.|クリップボードの画像が大きすぎます。
画幅与光照…|Canvas and lighting…|キャンバスと光源…
画幅尺寸…|Canvas size…|キャンバスサイズ…
光照设置…|Lighting settings…|光源設定…
光照|Lighting|照明
自阴影|Self shadows|セルフシャドウ
光照和自阴影开关位于主窗口的显示选项中。|Lighting and self-shadow switches are in the main display options.|照明とセルフシャドウの切り替えはメイン画面の表示設定にあります。
原生像素画幅|Native pixel canvas|ピクセルキャンバス
应用画幅|Apply canvas size|キャンバスサイズを適用
GIF尺寸与帧数过大，请降低输出倍率或帧数；PNG支持分页输出。|GIF size and frame count are too large. Reduce scale or frames, or use paged PNG output.|GIFが大きすぎます。倍率かフレーム数を減らすか、分割PNGを使用してください。
宽|Width|幅
高|Height|高さ
完成|Done|完了
实时预览；可在主窗口撤销。|Live preview; Undo in the main window.|即時プレビュー。メイン画面で元に戻せます。
32–256 px；扩大画幅不缩放模型或贴图，底部留白保持。|32–256 px. More canvas space preserves model and texture scale, with the same bottom margin.|32–256 px。モデルや画像を拡大せず、下余白を維持してキャンバスを広げます。
宽、高须为32–256之间的整数。|Width and height must be integers from 32 to 256.|幅と高さは32〜256の整数にしてください。
开启像素光照|Enable pixel lighting|ピクセル照明を有効化
模型自阴影|Self shadows|セルフシャドウ
光照角度（度）|Light direction (deg)|光の方向 (度)
光照高度（度）|Light elevation (deg)|光の高さ (度)
光照强度|Light strength|光の強さ
自阴影强度|Self-shadow strength|セルフシャドウの強さ
绘制感|Painted|描き込み風
立体感|Faceted|立体的
光照颜色|Light color|光の色
阴影颜色|Shadow color|影の色
方向固定在三维空间；分档明暗保留像素边缘。颜色只影响渲染，不改原贴图。|World-space light direction, with stepped pixel shading. Colors affect rendering and preserve your original textures.|光の方向は3D空間で固定し、段階的な明暗でピクセルの輪郭を保ちます。元の画像は変更しません。
仅整数倍最近邻放大。|Integer nearest-neighbor scaling only.|整数倍の最近傍拡大のみ。
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
