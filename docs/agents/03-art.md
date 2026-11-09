# 角色、动作与场景交付

## 当前范围与职责

保持单一酒馆院落、刀客和DAO。角色使用ov区域Tripo CLI来源，Blender处理米制、轴向、原点、握点及允许的DAO对齐，主控负责程序接线与最终验收。协作者交付后结束，当前不维持等待循环。

## 上一轮产出

Tripo角色完成PBR、低模烘焙与绑定，身体18,833三角、78关节、身高约1.78m。Base Color为2K，Normal／Metallic-Roughness为1K。单GLB保留idle、slash、hurt、fall四个原始具名动作。

上一轮实际SDK播放暴露普通R_Hand Entity子树不随GPU骨骼更新，武器因此悬空。该问题已经改为资产级刚性蒙皮。

## 本轮 review 修正与代码交付

- DAO的3,722三角面进入同一skinned mesh，顶点在身体bind坐标系中刚性绑定到现有R_Hand调色板索引，沿同一GPU骨架运动。
- `rigged_alignment.json`记录身体primitive与武器primitive的区分。Grip／Weapon_Root等空节点保留整理锚点含义，实际渲染几何由蒙皮承担。
- `EnemyAnimator`按实际阶段选择待机、斩击、站立短受击与倒地，注册晚于场景时同步当前状态，暂停与hit-stop停止对应动画推进。
- 斩击使用1.55s后的准备段，主要下劈2.067–2.167s，避免原准备片段中左手碰刃。敌人当前主攻下劈，HUD方向保持一致。
- 原hurt全片为坐地负伤，站立受击借用fall开头。低血处决复用倒地资源并放慢播放，新的专用配对处决动画仍属后续美术交付。
- `HomeStage`复用 `forecourt.glb` 补充玩家侧石铺地，来源为既有酒馆Paving模块，保持其材质、UV和贴图。
- HUD扩展到400×400dp控制区与500×260dp状态区，维持两个ECS锚定面板。方向印使用平面强调，删除疑似造成蓝色覆盖的纵深偏移；该候选修复尚未现场验证。
- 命中／弹反／技能等反馈接光脉冲、原始短音效与手柄触觉调用。

主要资产入口为 `ArtSource/tripo-warrior/prepare_rigged_warrior.py`、`rigged_alignment.json`、`ArtSource/tavern/extend_forecourt.py` 及 `ArtSource/audio/`。

## 下一步交付条件

本轮主控编译成功，按用户要求无自测与设备验收。后续需观察三轮中的握姿、刀随手、交叉淡化、倒地与脚下铺地拼接，确认移动后的蓝色覆盖候选是否消除。专用站立受击与处决动作的制作质量、极端姿态穿插、材质近景和真机性能继续作为美术验收条件。

原始高模、动作来源与CLI任务记录保留在各自资产路径。API凭据由CLI标准本机配置管理，源文件来源与实时账户状态分别核对。
