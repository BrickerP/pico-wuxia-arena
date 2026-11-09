# Tripo角色与动作库

当前运行资产为 `library/base.glb`、`library/indigo.glb`和`library/veteran.glb`，主控复制到 `app/src/main/assets/models/opponents/`，供三轮依次选择试刀客、青衫护院和玄甲守擂。人物沿ov区域Tripo CLI与 `tripo-v3.1` 管线生成，保存PBR、独立骨架与原始任务记录。

玄甲源候选在离线展示中发现颅顶／束发生成缺损，现已替换为颅顶完整的修订资产。最终角色数据由 `motion_library.json`、`library/characters.json`与各角色alignment确定。

## 当前人物与资产

| 角色 | 身体三角面 | 运行骨架 | 运行文件 |
| --- | --- | --- | --- |
| 试刀客 | 18,833 | 78关节 | base.glb |
| 青衫护院 | 27,515 | 78关节 | indigo.glb |
| 玄甲守擂 | 25,113三角 | 78关节 | veteran.glb |

每个带刀GLB在身体同一mesh／skin中加入3,722三角的DAO，刚性绑定R_Hand。原刀客Base Color为2K，Normal与Metallic-Roughness为1K，青衫源PBR图为4K。各目标贴图与几何沿其来源文件保存，运行加载与内存预算由主控在Space Pro阶段记录。

角色统一约1.78m、米制、+Y向上、朝+Z，脚面归零。生产整理处理轴向、共同父框架、原点、握点和刀具对齐，身体与骨架保持同一归一变换。

## 动作与重定向

每名角色包含8个动作资源。

| Clip | 来源处理与当前用途 |
| --- | --- |
| idle | 41骨源重定向，待机 |
| walk | 41骨源重定向，距离驱动步法 |
| turn | 41骨源重定向，保留在动作库 |
| hit_body | 41骨站立身体受击源重定向 |
| hit_head | 41骨头部受击源重定向，处决第一段也使用 |
| hit_side | 41骨侧向受击源重定向，用于弹反后仰 |
| fall | 41骨倒地源重定向，普通死亡和处决第二段 |
| slash | 各自78骨原生斩击，保持原曲线与2.117秒接触标记 |

41骨与78骨的局部rest frame存在差异。生产器逐源关键时刻采样世界姿态，以世界空间旋转／位移delta转移到目标bind frame，再经目标父节点反求局部变换。目标骨长、蒙皮权重与逆绑定矩阵保留，肘膝share骨混合相邻段的运动delta。

每个目标的30个指骨从其原生slash在2.117秒采样握刀姿态，用于转移动作中的持刀。原生slash保留自己的全部曲线。此资产处理仍需各体型握点、足底、变形和交叉淡化的视觉确认。

运行步法使用walk源0.333333–1.5秒的近循环，累计有符号位移每1.45m推进一周期。身体／头部受击与弹反后仰分开播放。处决先播放0.45秒头部受创，再进入fall，当前没有制作专用双人配对动画。

## 生产重建

输入清单为 `motion_library.json`，每个原始rig、动作及握刀源带SHA-256。所有路径相对本目录。完整数据合同见[character_library.md](character_library.md)。

将 `BLENDER`设为本机Blender4.5可执行路径，从仓库根目录运行。

```bash
"$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python ArtSource/tripo-warrior/prepare_character_library.py -- \
  --manifest ArtSource/tripo-warrior/motion_library.json
```

`prepare_character_library.py`复用 `prepare_rigged_warrior.py`的归一、通道打包、同皮肤DAO与分组发布逻辑。`library/`同时提供body-only GLB、带刀GLB、alignment、重定向中间源及角色索引。运行目录由主控从完整产物复制。

`expanded/`保存本轮CLI来源、预检计划、任务结果和原始模型／动作。未采用的中间绑定与旧候选留在本地缓存，活动来源由manifest固定。此前四动作整理资产和`rigged_alignment.json`保留其原始来源身份，当前运行路径使用新的角色库。

## 制作展示与完成条件

`review/character_library_preview.png`为实际GLB的原生斩击姿态，`review/character_motion_preview.png`展示待机、步法和站立受击的资产时刻。展示随修订资产更新，图内使用离线棚景说明。它们用于资产制作交流，设备画面、握点、足底接触、动画过渡和性能继续按主控验收清单记录。

本轮已进行生产导出与接线，主控完成整合版编译。按用户要求，本轮未运行游戏自测、测试套件或设备验收。当前资产包含重定向与源握姿采样，专用双人配对动作和足底IK继续作为质量工作。

## 来源与凭据

CLI任务结果记录生成、绑定与动作费用，最终修订链消耗及账户余额由主控按实际账户结果汇总。API凭据沿CLI标准本机配置管理，仓库保存可重建资产、来源ID及输出身份。

DAO来源见[刀具说明](../dao/README.md)。Tripo账号与产物条款沿官方ov文档核对。[ov API条款](https://developers.tripo3d.ai/en/terms)，[API账单](https://developers.tripo3d.ai/en/docs/billing)

## 本轮制作费用与展示

本轮CLI实际消耗380credits，完成后余额4465、冻结0。其中100credits属于颅顶缺损的弃用候选，修订版本追加75credits。明细见 `expanded/production_receipt.json`，当前运行模型均由 `motion_library.json` 指定。

`review/character_library_preview.png`、`review/character_motion_preview.png`与`review/character_motion_preview.mp4`使用最终实际GLB进行离线制作展示。动作短片按运行步法的循环区间采样，展示环境与相机属于制作棚景。
