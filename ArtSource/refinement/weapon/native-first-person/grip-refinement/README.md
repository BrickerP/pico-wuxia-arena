# 原生右手闭握修复首件

**可见首件阶段结束，等待对应 Root review。** 独立结构契约验证通过，三图确认有可见收益，可交 Root 接入现有 PlayerHands 做原生评审；最终握持质量为 **`REQUEST_CHANGES_FOR_FINAL_GRIP`**，保留一项 MEDIUM（小指末节缺支撑且 Ring/Pinky 中节新增交面），未获正式发布批准，未改正式资产或运行代码。

[四遍 review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/review.json)／[固定收件索引](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/handoff.json)。

- 完整候选：[right_hand_refined.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined.glb)，SHA `0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef`。
- 九指骨增量：[pose_delta.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/pose_delta.json)。
- 独立核验：[verification.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/verification.json)。
- 0.3 m 实际 KTX 图：[正](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_front.png)／[反](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_back.png)／[斜](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_oblique.png)。

## 原生接入点

由 Root 选择并替换 `app/src/main/assets/models/player_hands/right_hand.glb`。现消费者为 `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/PlayerHands.kt` 的 `asset://models/player_hands/right_hand.glb`，保持 identity `RightGripRoot`、单一蒙皮实体／骨架和唯一 `grip` 动画 0→1 秒。无需改 Kotlin、左手、独立刀具或识别规则。本路没有执行替换、构建、安装、设备操作或 Git。

基线右手 SHA `5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d`；正式 dao SHA `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0`。

## 修改与保持

只改 9 个 R finger 的闭握 rotation：Thumb1/2/3、Pinky1/2/3、Ring2/3、Mid3。先核对旧同源已审核修正的基线姿态／选中几何与当前 5fb 一致，再将八骨 `q_delta_post` 作用一次；Pinky3 另作一次 18° 限幅末节屈曲。没有复制旧网格，没有重复叠加已烘焙校准。`pose_delta.json` 给逐骨 source open／closed、post 增量、新 closed 及来源 SHA。

默认 Rclosed 与新 `grip@1` 一致；15 指 `grip@0` 原始数据逐字节保持。原 BIN 前缀完整保留，几何、NORMAL、UV、权重／骨索引、78 骨／IBM、骨长和节点 T/S、腕、Grip／Blade Base／Tip、材质及三张 1536² KTX 载荷均不变。没有整体转动手／刀；未修改左侧骨、左手文件或父目录发布物。

## 实际接触结果

在相同 7,167 个原 vertex／edge-midpoint／face-centroid 样本和正式 dao 上测真实闭合 Handle core，结果为：

| 支持区域 | 原最深／核内样本 | 候选最深／核内样本 |
| --- | ---: | ---: |
| Thumb | 11.486 mm／171 | 0／0 |
| Index | 0.0925 mm／2 | 0.0925 mm／2 |
| Mid | 1.685 mm／19 | 0／0 |
| Ring | 4.209 mm／35 | 0／0 |
| Pinky | 7.982 mm／50 | 0／0 |

合计核内 277→2；深于 0.25 mm 的样本 256→0。两个保留点都是 Index 原有极浅入，不称零穿透。离散样本不保证完整连续表面无穿插。

拇指末节到 Index 表面最近约 0.0438 mm，24 个样本在 1 mm 内，有对向近接触证据。小指末节到绳最近仍约 **5.061 mm**，到 Ring 最近约 **3.841 mm**，两者 3 mm 内样本均为 0；虽已收弯并退核，末节悬空风险没有清除，不能将小指其它段约 0.67 mm 的近柄距离冒称末节已贴柄。

原始 index 的指面交叉指标为 Thumb/Index 108→105、Mid/Ring 166→164、Ring/Pinky 77→87。进一步按真实位置焊接排除 UV seam 的合法相邻面后，实际非邻接指标为 Thumb/Index **50→47**、Mid/Ring **64→62**、Ring/Pinky **0→10**。不能把最后 10 对解释为源 seam；这是新增邻指交面，仍需 Root 判断，当前不称无自交或最终握持合格。新增／移除完整 face sets 见独立核验。

## 三图与边界

只运行一个 Blender 进程、两 CPU 线程，单次渲染三张图。相机到实际 Grip 均为 0.3 m，手／刀根均 identity，未调整模型比例。手部像素从候选三张逐字节未变的 KTX 实际 level 0 解码得到；刀也来自正式 db28 的实际 KTX 解码。派生 PNG companion 保留新候选的全部非 image 语义及 38 个 accessor／bufferView，不是旧姿态网格。

正面可读四指收回及握柄包覆，拇指侧斜视补查对向夹持。源手部硬折面和指面交叠保留。腕口暗色不规则边仍可见；该边界、衣袖与 cap 几何未改，三图不能替连续手姿下的腕口／前臂裁边验收。近端 cap 部分出画，不据此认定裁边通过。

这些是供原生接入评审的离线制作图，使用 Blender 的过滤与光照；Root 仍需将候选接入现有 APK，在 PICO Emulator 检查实际握柄、肤色及腕口。图片不代替 SDK／实机验收。

## 检查与复建

`verify_grip.py` 从导出文件独立读取，仅允许 R 闭握／default rotation 的白名单变化；检查全部 open0 原行、原 BIN 前缀、几何与纹理载荷、骨长／IBM、腕／根、同一真实表面样本及 companion 保持。腕、open 行、KTX 改动三个负例全部拒绝。`make_render_companion.py` 四项测试通过。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/build_grip.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/verify_grip.py --candidate ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined.glb --sha256 0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/make_render_companion.py --candidate-sha256 0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef
```

Blender 图使用 `render_grip.py`，显式 pin 候选／decoded SHA 与掌心方向，`--threads 2` 且脚本内固定两线程。实际输入、姿态、相机和三图 SHA 见 `previews/render_manifest.json`。本首件没有改识别或新增 SDK 探针，没有网页交付。
