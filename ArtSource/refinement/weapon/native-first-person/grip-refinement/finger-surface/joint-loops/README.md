# Right 真实关节环带候选

当前实物由 a980 重新制作，48e 保持冻结作为对照。数值检查通过，外观等待 Root 依据真实图审核；未替换正式左右手。

- 完整 GLB：`right_hand_joint.glb`，SHA `199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64`。
- 6,222 三角，预算 12,000；新增 660 indexed corners。
- 原点 P 改动 169、原 N 改动 192、原 J/W 改动 169。**不能沿用 48e 的原点／权重零变化结论。**
- 原 bind 位置最大变化 0.406 mm；真实 open 最大 0.738 mm，mid 0.971 mm，closed 1.463 mm。每个修改点的位置／法线／前后骨权／四态位移完整列在 `original_change_ledger.json`。
- 原 UV 逐值不变，新点 UV 保源父面 barycentric 语义；所有内掌／握柄指腹、拇指、已通过的 14 点掌背与腕口控制、78 骨／IBM／Grip／原动画及 3 KTX 保持既定保护。

## 实际制作

真实 open MCP／PIP／DIP 骨位建立四指中心线和背／侧 capsule，骨权主导项不充当解剖标签。MCP 远端支持环、PIP 五条截面环、DIP 五条截面环按实际关节平面裁切源三角；所有 UV chart 按同一焊接几何边共享切点。新片保留每个关节环边界，用约束 ear clipping 三角化，已彻底移除会引入独立 LBS 内泡的 centroid 星形 fan 路径。

四指源真实截面用随轴向变化的 Fourier 径向项及独立 PIP／DIP 体积项拟合；只在合法背／侧、非保护原点径向调整，保骨中心与骨长，不拟合圆管。图 `joint_loops_topology.png` 显示真正的 MCP／PIP／DIP 环带；三态 `*_joint_sections.png` 直接展示同一实际骨平面的 a980／48e／当前截面，区分几何与着色。

源实际 PIP 同轴点存在不一致骨权及跨指 spill，局部原控制骨权按同指、20 mm 轴向／1.2 rad 角域的最近六个源 anchor 做可重算插值，过滤明确的非本指 palette，并按解剖编辑场羽化。新切环点统一插值**最终更新后的原控制骨权**，不独立估计第二个内点场。新点造型强度不超过原父面控制场的 bary 上界；全零编辑父面和零场边不细分，避免没有造型收益却因 LBS 与细分不交换而自行弯曲。

法线以拟合截面的真实曲面导数为方向，与原作者 open normal 按同一编辑场融合，再接受四态全部 incident 子面的正向约束；不直接按细碎三角面积平均。合法域中的必要 N-only support 会精确列出，域外保护原 normal 不变；不翻 normal 掩盖几何。

实际发现的薄父面与 Mid↔Ring 接触区形成明确保护边界和空间羽化。旧 036f 曾出现三对新增 self，已保留其完整失败报告，不以恰好相同的净计数掩盖；实际父面定位与源码可在 `before-contact-normal-repair/` 检查。所有修复来自已见的 child／父面／角／接触证据，没有多参数扫描。

## 已执行检查

16 项测试全部通过；四态 default／open／mid／closed 实际重算全部 GLB 几何、逆转置 normal、新旧接缝、完整 self 与 13 个真实 DAO shape。保护区位置实际 LBS 误差为 0。内掌 P／N／骨权越界、伪报解剖 ROI、UV／Grip 改动、抬高新点编辑场、违反最终原控制插值等坏例会拒绝。

闭握 self：源 109 对，候选 raw 136，父面映射 109；新增父面对为空，移除的旧父面对为 `[]`。open／mid self 仍为 0。旧 DAO open／mid 的 core 132／64、cordwrap 114／67 与 open ferrule 19 等继承问题逐对披露；完整原／新集合、内部样本与深度在 `verification.json`，没有把握持描述成全局零穿入。

## 0.3 m 三列近景

- [open：a980／48e／关节环带](renders/open_three_way.png)
- [mid：a980／48e／关节环带](renders/mid_three_way.png)
- [closed：a980／48e／关节环带](renders/closed_three_way.png)

每组上排原材质，下排 neutral。相机、透视、距离与 source studio 配光一致；a980／48e 使用已冻结同机位原图，仅当前六张 after 重新渲染。原材质来自实际当前 GLB 的未改 KTX 解码。上述是离线 GLB／数学 LBS／Blender 证据，不证明 Spatial SDK TBN、原生观感、连续时间或性能。

## 复建入口

从仓库根目录运行；所有写入只在本候选 scope，Blender 使用现有全机锁。

```sh
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/build_joint.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/make_companion.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/verify_joint.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/test_verify_joint.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/inspect_sections.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/export_evidence.py
python3 ArtSource/refinement/hand-poses/run_blender.py -b --factory-startup --python ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/render_joint.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/assemble_review.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/finalize.py
```

带输入 SHA 的收件入口为 `handoff.json`。本路未动 48e 基线、02、正式资源、Left、app、SDK 坐标、公共 producer、设备或 Git。


## 生产依赖闭包（2026-11-17）

[`production_files.json`](production_files.json) 是本候选及匹配Left的最小生产打包清单：包含当前封件、评审图、冻结a980／ecc／48e输入，以及全部实际动态导入、AST提取数学函数来源、解码和镜像producer。每个仓库文件记录SHA、角色、调用用途及当前index复用／需stage状态；`git_add_paths`可直接交Root使用，本路未执行Git。

失败archives、临时日志、独立KTX缓存与可重建decoded大文件不在提交清单。被现有解码器实际读取的缓存逐项列在`excluded_rebuildable_runtime_inputs`，附来源、预期SHA和生成顺序；源码及冻结压缩GLB仍保留，因此不是把依赖省掉。重建前先按`regeneration_recipes`生成这些缓存，再用上面的现有入口；不要整目录add。旧48e渲染器中的失败archive仅是可选before图复用，干净checkout缺少它时会重新渲染，不是生产依赖。

已封GLB、handoff和Root收据均未修改。清单只证明输入存在／哈希与导入闭包，不重复资产、原生或碰撞验收。
