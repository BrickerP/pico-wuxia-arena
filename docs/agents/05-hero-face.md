# 05 · 写实人物面部与头发

## 当前状态

2026-11-11会话已接手，实际工程与源SHA核对通过。正在制作独立成熟头脸高精源，并准备保留原78骨rest与身体流的候选装配工具。仅改本路目录与本文件，未动正式producer／manifest／library／app。

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

### 首轮制作中

- 已读取设计母版 `ArtSource/refinement/character/design/concept/unified_board_v2_final.png` 与真实基线 `baseline/face.png`，二维目标与实际模型分开。
- 实际问题：原模型只有一个头身材质／primitive；R_Eye和L_Eye骨没有顶点权重，眼球仍粘在头脸网格。Head影响6634顶点。头UV跨整个4K atlas，不能矩形裁脸。
- Tripo已使用本机已安装0.11.2，ov doctor通过，余额4290，冻结0。显式 `tripo-v3.1`、detailed几何、extreme贴图、PBR预检60credits，无warnings；本轮250credits上限内已提交**唯一一次**头部源任务 `a834e461-fbc6-40db-9ce6-447b0c3dbc9b`。见本路 `cli/head_dry_run.json`、`cli/head_progress.log`。不重提、不用@last。
- 当前产物为制作请求与本地装配代码，尚未宣称3D完成、已入APK或头显验收。下一步查看生成实物，做三视角／0.8m、1.5m、3m同机位对比与颈部接缝评审。

