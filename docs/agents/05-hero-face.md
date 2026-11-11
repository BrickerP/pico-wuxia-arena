# 05 · 写实人物面部与头发

## 当前状态

2026-11-11已按Root补充要求完成本轮候选：面部裂缝修复、旧颈部皮肤尖片清理、完整闭合眼球／透明角膜与眼睑开口。46项检查及完整本地复建通过，正式资源仍未发布。Root已接受成年骨相与发束方向，下一项为原生光影与实际动作下审核新SHA。

## 目标

把当前刀客偏光滑、年轻和卡通的面部提升到可信的成年写实中式人物。参考《黑神话》的骨相、皮肤层次和有因果的材质细节，保持本项目原创身份。优先眉弓／眼窝、鼻翼／唇线、耳廓、眼球与角膜、发际线和束髻，0.8m正常视距能辨别成熟骨相和细节。

## 所有权

负责 ArtSource/refinement/hero-face/ 与本文件。03负责衣物领襟与扣具，02负责武器握持，07负责端内光照。现raw rig位于 ArtSource/tripo-warrior/refined-base60k/rig.glb，源SHA43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6。先读取实际模型及设计母版，身体、手、原78骨rest和已制动作作为共同基准。

## 制作队列

1. 做实际面部正／侧／斜事实图，选一个强方向，直接进入3D头脸修形、分件或贴图制作。面部须有可信轮廓、眼睑体积、唇鼻结构和分层发束。
2. 必要时用已安装tripo-cli制作高质量头部或局部源，账号区域ov，生成显式tripo-v3.1。先doctor确认余额，余额0停止收费部分并报告。先dry-run核参数，再按用户既有全授权执行，无需再问用户。你是这轮唯一新增付费Tripo任务负责人，新增总额上限250credits，逐task_id恢复，不使用@last，不写API Key或带授权URL。
3. 以现人物为装配基准。优先头部独立高精源、局部重拓／烘焙与原身体颈部连续装配，给顶点／面映射、材质分工和绑定方案。现身体手部与78骨rest保持来源可追溯，头部新网格可绑定现Head／Eye骨，Root合成。主体材质名保留tripo_前缀以便独占白闪识别。
4. 独立头部材质给足有效像素密度，真实皮肤粗糙度、角膜反光、唇鼻过渡与发束方向共同评审。只调几个factor不足以交付本轮目标。
5. 交raw body-only或头部可组合GLB、可复建脚本、原／候选正常视距对照和装配说明。继续做眼睑／发际线／颈部接缝收口。

## 首轮交付

一份实际3D高质量头脸候选及三视角，或局部源已成功生成和可见精修模型。设计图与已完成模型分开标记，不能用设计图充当成品。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

### 当前交付（以此块为准）

- 可组合头部：`ArtSource/refinement/hero-face/head-component.glb`，SHA `25f32a2e2d4618de7cebe0b8359d9e5722387cab01f958d8970e4eaa40c7f1cb`。
- 原78骨完整身体候选：`ArtSource/refinement/hero-face/hero-face-candidate.glb`，SHA **`5954552f451efbc4df764d2cfacf5e6b0b03084049140a7f3fc9fc2dbf267d35`**，约39.0MB。候选待Root正式集成，未发布。
- 正常视距同机位前后：`review/normal-distance-comparison.png`（0.8m／1.5m／3m，60°透视，每帧原始960px）；单张 `review/first-visible-upgrade.png`。
- 正／侧／斜前后：`review/detail-comparison.png`；单图 `review/after_front.png`、`after_right.png`、`after_oblique.png`。全部为真实GLB离线渲染，未修图；细节正交机位只作补充。
- 来源与最终SHA：`candidate-summary.json`。原身体面映射、材质和蒙皮分工：`graft-report.json`。眼区初分件与原眼骨坐标：`eye-report.json`；完整眼球／角膜、开口与材质证据：`ocular-report.json`。

### 可见结果与接线

眉弓／眼窝更有体积，鼻翼、唇线与颌骨更明确；新头为独立4K PBR atlas，发际线与多层束发已进入真实网格。重回高精源焊接后减面，首版脸颊／额头的几何裂缝已消除。左右各有一个真实闭合球形眼球（每只2208面）与独立角膜壳（每只1488面）。原眼区中央已开孔，剩余20／27面作为Head绑定眼睑边缘；只有眼球／角膜绑定既有L_Eye／R_Eye。眼球使用原atlas棕色虹膜，角膜使用无白色漫反射的低alpha PBR，已目视排除早期灰白角膜遮挡。

最终模型为50401个保留身体三角形 + 47288个新头／眼球／角膜三角形，8个primitive。原身体双手、78骨rest、原材质与原图像、7条原accessor流保持字节／JSON一致；删除旧Head区域并额外去掉55个原颈部皮肤三角形以消除下颌下的旧皮肤尖片。领口按实际原basecolor语义保护，白／灰衣物不进入皮肤清理。颈段只延伸实际下颌以下（raw Y<.815），原下颌不被拉长。

Root接入点是本路的**raw body-only候选**，frame与原rig完全相同（+Y up、+X front、原mesh-local单位）。可把它作为正式producer的body source，沿原规范化、握持、动作与角色变体合成流程接入；不重新rig、不替换78骨rest。所有新增主体／眼区材质均有`tripo_`前缀，供现有独占白闪识别。Main、HomeStage和manifest最终接线仍由Root维护。

### 来源与费用

| 来源 | task_id／SHA | 实耗 |
| --- | --- | --- |
| 原raw身体 | `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6` | 既有 |
| 高精头：ov、显式tripo-v3.1、detailed几何、extreme、PBR | `a834e461-fbc6-40db-9ce6-447b0c3dbc9b` | 60 credits |
| 颜色／PBR修正：texture v3.5、extreme、明确肤色／黑发指导 | `165609e9-dce0-45e3-8994-0c7486a87814` | 30 credits |

本路合计**90／250 credits**，没有重roll、额外rig或新动作收费。高精源 `source/head-high-source.glb` SHA `fc44714e8f12a739570a110c881133d057344d8f9fad45a46b0703f1ecc196ab`；彩色源 `source/head-textured-source.glb` SHA `ba0086a8cf7a94c050f65fdd705138ae2238886004557e361b6a86743a5d8f88`。已保存prompt、doctor、dry-run与脱敏task记录，无API Key或授权URL。

### 复建与验证

从唯一工程根目录运行：

```sh
python3 ArtSource/refinement/hero-face/build_candidate.py --render
```

已完整执行成功，日志为`review/rebuild.log`。只读本地不可变源，校验source SHA，依次焊接／减面、贴图分工、raw对齐、颈段、眼睑开口／闭合眼球／透明角膜、原身体合成与旧颈皮肤清理，然后渲染前后对照。不会调用付费服务、正式producer、共享Gradle、设备或Git写操作。`BLENDER`可指向本机Blender4.5；同一时刻只启动一个本路Blender。

**46项测试全部通过**：原binary／流／rest保留，语义切口与整数权重，仿射与颈部normal／tangent，左右眼映射和刚性绑定、闭合眼球拓扑／绕序／法线、角膜边界与眼睑开口、皮肤与白灰衣领区分，错误来源与空选区拒绝。完整本地复建与导出的实际GLB渲染均通过；没有用这些证明设备画质或VR手感。

### 真实限制与Root下一项

1. 这是成熟骨相与发束的可组合升级候选，皮肤仍较平滑，尚不等同目标游戏的最终写实皮肤层次。保留了生成normal与UV，未做专用高低模normal重烘焙。
2. 完整球形眼球与透明角膜壳已完成；角膜是普通alphaBLEND、无折射的PBR近似，不能当作物理折射已通过。真实PICO透明排序仍待Root验证。保持原眼骨rest，因此球心与原Eye枢轴X差约.0032 raw（约6mm实际尺度），自由眼转和实际动作下的眼睑边界需要Root验收。
3. 颈领静态轮廓已收口，但颈部内侧采用覆盖装配，未做拓扑焊接。V领深处仍有细小色调／边缘差异；动态大角度头转、现三方向完整动作及03的新衣领组合尚未验收。
4. 4K新头贴图的端侧内存、真实PICO原生光照、白闪材质、Space Pro性能和整体1.5m／3m战斗画面，均待Root的共享安装与同机位端内验证。

### 阶段轨迹（已被当前交付取代）

- 首轮查明原R_Eye／L_Eye无任何顶点权重、没有独立眼球，Head影响6634点；UV跨整张atlas，不能矩形裁脸。
- 首次高精任务成功但basecolor接近灰泥塑。旧灰色候选已清理，`review/after-v1_*`保留为结构检查，不可发布；后续30credits贴图修正后得到彩色源。
- 首次直接减面导致UV岛边界实际开裂：高精源按位置焊接后仅11条边界，旧40k仍25582条。最终使用高精源先焊接，再减面，复用已验证同布局的彩色材质；没有再生成付费任务。
- 早期颜色候选与颈部前移实验已废弃，旧文中的`8e4c37…`等SHA不再指向当前交付。当前唯一审核入口为本页顶部完整SHA与`candidate-summary.json`。


### Root追加审核后的眼球／角膜收口

Root接受骨相／发束方向后，本路继续制作真实球体和角膜，无新增收费。`build_eyes.py`在眼睑中央开孔，生成封闭眼球（边界0、非流形0、零面积0、Euler=2），独立角膜保留预期48边圆周。完整旧body原始7条stream、skin、nodes/rest、material/images仍一致，原78骨不变。

白色alpha=.08角膜的实际渲染出现灰色遮罩，已用无角膜对照定位为漫反射薄层而非UV／眼球几何问题；当前固定采用RGB0、alpha=.025、roughness=.04的无折射透明近似。`review/eyes-preview_*`是失败旧角膜检查；`review/eyes-clear-cornea_*`为修正专项检查；最终统一正常视距与三视角以`review/after_*`和本页顶部SHA为准。

最终代码与静态实物复核无阻断问题；已清理失败／过时的GLB候选，只保留当前复建链与必要不可变源。历史诊断图／JSON仍可审计。验收依据为46项测试、完整复建、文件身份与目视检查。

## Root本轮组合审核与续派（2026-11-11）

审核：正常视距的成年骨相、发束、闭合眼球方向接受；5954552候选在prepared idle出现真实颈部黑口和皮肤锯齿，未进入正式app。

下一步：以实际组合姿态修连续颈部几何／权重，重交SHA与同机位图。禁止以加黑材质遮开口；透明角膜还需避免opaque受击白片。
