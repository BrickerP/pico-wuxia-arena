# Goal

从分支 `cursor/clean-steel-hold-2d0f` 开始。这份 goal 只做玩家刀的接触形状。做完就停，不要接着打三轮，不要回到草稿 PR #13。

成品 Demo 未完成。产品仍是雨夜庭院、一把刀、三名顺序对手。这份 goal 不改手感数值，不改场景，不改人物。

## 结果

玩家刀只有一个接触形状。它从正式资产 `asset://models/dao_grip.glb`（`app/src/main/assets/models/dao_grip.glb`）的 Steel 顶点派生，存成握点局部坐标里的一组胶囊。运行时只做刚体变换，不在每帧重读 GLB。

下面三处必须读这同一份，不准留一根旧的 12mm 单胶囊当回退：

- 接触：`playerBlade`、`firstRigidBladeContact`、`WeaponContactConstraint`、`separatingSteelSweep`
- 恢复：`ActorWithdrawalPlan.create` 拿到的玩家刀
- 显示：仍然画 `dao_grip.glb`。接触体不要另做一把可见的刀。覆盖检查对这把网格的 Steel 顶点，不对另一份简化模型

## 现状

不要把这段再调查成一份新报告。

- 玩家刀现在是一根胶囊。局部端点 `PLAYER_BLADE_BASE = (0.022, 0, -0.129)`，`PLAYER_BLADE_TIP = (0.0532, 0, -0.849)`，半径 `PLAYER_BLADE_RADIUS_METERS = 0.012`。定义在 `WeaponContactConstraint.kt` 的 `playerBlade()`。
- 正式 dao 默认 scene 的 Steel 顶点 5533 个，4469 个在这根胶囊外，最大离轴 56.994mm。漏的是刀面宽度，不是刀长。沿中线再排一串同样的 12mm 胶囊解决不了。
- 敌人刀仍是 `ArenaSession` 里 `AttackPoseSample.blade()` 的 12.5mm 单胶囊。这次不改它，也不改身体胶囊。
- 不可证的钢交叠已经有 220ms 强制回守：`STEEL_HOLD_LIMIT_NANOS`、`releaseWeaponHold()`、同一次重叠的 latch。保留这些行为，不要加回永久顶住。

## 做法

在握点局部空间用胶囊铺满刀面，而不是用一根租胶囊把宽度包进去。

- 只统计 Steel 顶点。握柄、缆绳、皮革顶点不进覆盖分母，否则会做出一根包住整把刀的大胶囊。
- 每段半径 ≤ 6mm。段数 ≤ 16，固定、可复现，写进测试。每个 Steel 顶点到形状联合体的外侧距离 ≤ 2mm。
- 16 段或 6mm 做不到 2mm，就停下来，写明还差多少。不要悄悄改成 60mm 半径，也不要改成上百段。
- `playerBlade()` 如果只能返回一段，就改成返回这条链。`firstRigidBladeContact` 对每段取最早接触。`WeaponContactConstraint` 的锁定和松开用同一条链上的最近点。`ActorWithdrawalPlan.create` 也吃这条链。不准再留一根旧胶囊专门做松开或卸力。
- 伤害、精力、弹反窗口、220ms 回守、SDK、Gradle 都不动。普通/要害仍是 25/30，敌血 100/125/150，出刀 12，格挡 28，弹反 180ms，硬直 550ms。

## 完成才能停

- 测试写出覆盖前最大离轴，以及覆盖后每个 Steel 顶点的外侧距离。后者必须 ≤ 2mm。同时写出形状表面到最近 Steel 顶点的最大距离，不许只报一句通过。
- 现有钢接触测试仍要表达原来的安全：玩家手不被敌人拖走，同一次重叠不连打出伤，不可证不会永久冻住。
- PR 说明里只留：改了哪些文件、段数、每段半径、覆盖前后两个距离。不要新建文档，不要提交 review 图、`.blend`、npz。
- 没有模拟器录像也停。不要为了这份 goal 去打三轮。

## 不做

- 不改敌人刀、身体胶囊、手、衣片、60k、Tripo、IBL、灯笼、HUD、弹反、头闪、技能、处决。
- 不恢复 `docs/agents/01` 到 `12`，不新建 `docs/agents/0N-*.md`。
- 不升级 SDK 或 Gradle。
- 不把「安全保持」加回去。证不出来就回守，不要冻住。
