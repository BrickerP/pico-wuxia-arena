# 原生命中反馈：局部呈现私有候选

本目录是2026-11-13 Root委派的候选，不是已安装的效果。app、正式资源、Core、输入、HMD／双手、伤害和时钟没有被本会话修改；没有Gradle、Git或设备操作。

## 原帧与根因

原VFR是`artifacts/native-controller-burst/contact-attempt.mp4`，不是presentation的CFR转码。原frame47 PTS为926695/90000，即10.296611s；邻帧为10.227067和10.535400s。三张PNG与原视频解码逐像素一致。脸部与衣料呈近乎常色，主色RGB196/194/179，不是RGB255曝光裁切。证据见`frame-evidence/evidence.json`与唯一PTS对照板。没有共同时间锚，未将该帧绑定某个contact id，也未用238.8ms采样间隙冒充28ms闪白时长或38ms局部core寿命。

`EnemyHitFlash`会把9个body/head/eyes/neck的`tripo_*` PBR槽换成同色OPAQUE Unlit，跳过原baseColor纹理、normal、roughness及灯光响应。这是整个人形平涂的直接路径；Unlit不受点光照明，因此点光不是把该Unlit人形“照白”的原因。点光另会作用于PBR恢复后或其它受光物体。

## 选择与补丁

可只让普通BODY跳过白闪，也可退出整身替换机制。选择后者，避免保留其它事件抹材质的路径和原材质restore失败后仍被close的风险。致命／弹反的更强层次由现有局部core/碎屑/单盏短点光承担。

主补丁：`01-local-native-impact.patch`。

- HomeStage移除flash field／初始化／present／close；删除EnemyHitFlash.kt、BodyFlashMaterial.kt及锁定旧白闪行为的两份测试。
- 新增纯`NativeImpactLight.kt`事件数值策略，继续使用原contactLight Entity及6.1.9公有PointLightComponent构造器。
- 普通SOFT BODY不新启或延长接触点光；已有更强短灯可按原截止时间结束。
- 点光仍在真实point+0.035*N，不构造新接触、不改N/T；强度／半径／时长按下表分级。
- 改为轮次内ID集合去重，保持先消费再暂停清理。迟到时只取`max(duration-age,0)`，未来／负时刻拒绝；NPC hitstop不会重启已经消费的灯。
- CombatEffects、ContactParticleEmitter、SoftContactEnvelope、8颗粒、切向、cleanup、资源均保持原字节。

## 事件到数值

强度是SDK原参数，不把公有签名未证明的单位写成流明。半径沿现工程米制约定填写，是衰减参数，不是表面mask或硬裁剪。

| 示例事件 | 原整身Unlit | 原点光 强度/半径/时长 | 候选整身Unlit | 候选点光 强度/半径/时长 |
|---|---:|---|---:|---|
| SOFT BODY，25伤，strength .625 | 28ms | 222.5 / .60 / 60ms | 0 | 关闭 |
| SOFT HEAD，强调后strength .75 | 28ms | 245 / .60 / 75ms | 0 | 35 / .18 / 45ms |
| HARD，strength .8 | 28ms | 254 / .60 / 60ms | 0 | 54 / .22 / 45ms |
| GUARDED，strength .65 | 28ms | 227 / .60 / 60ms | 0 | 49.5 / .22 / 45ms |
| BLOCK，strength .65，0伤 | 0 | 227 / .60 / 60ms | 0 | 49.5 / .22 / 45ms |
| PARRY，strength 1，0伤 | 0 | 290 / .60 / 90ms | 0 | 120 / .35 / 70ms |
| 致命BODY，强调后strength 1 | 40ms | 290 / .60 / 100ms | 0 | 160 / .45 / 90ms |
| PLAYER_HIT | 0 | 227 / .60 / 60ms | 0 | 关闭 |
| SKILL，已有事件 | 28ms | 290 / .60 / 60ms | 0 | 120 / .35 / 60ms |
| EXECUTION，已有致命事件 | 40ms | 290 / .60 / 100ms | 0 | 160 / .45 / 90ms |

完整例值及边界解释在`event_values.json`。表是策略示例，不是伪造的原生事件或该视频帧的ID配对。BODY的38ms薄core、60ms scar和最多8片／250ms cleanup不变；PARRY的90ms核心与来刃切向、颗粒不变。其它已存在局部包络不变。未扩技能、没有camera shake、没有冻结HMD或双手。

## 6.1.9 API证据

BOM为gradle/libs.versions.toml的6.1.9。项目没有.pico-env.json；host selector为6.1。知识MCP不可用，本轮读取本机6.1参考和exact AAR公有签名，记录在`api-review/api_evidence.json`及`public-signatures.txt`：PointLightComponent(Color4,float,float)、setIntensity/setColor/setAttenuationRadius均存在。未发现可据以实现局部表面mask的公有合同，本候选不发明此能力、不修改共享PBR材质。灯为root子Entity，由root销毁，未引入新Resource持有。

## 无witness的表面入口

`surface-preload/route_evidence.json`从Main→ArenaSession presenter→HomeStage→effects.present走完。presentResolvedSurface只有定义，没有生产caller；湿衣缺材质witness，闪避只有MISSED/DODGE反馈，落地没有实际骨骼／地面接触witness。没有为它们造触发。

建议单独采用`surface-preload/02-remove-unused-surface-route.patch`，删除无caller入口／gate及三类运行预设和生成job，预载实例9→6，减少3模型实例／26个逐mesh opacity控制器。此数是结构预算，不是帧率实测。01只过滤loader、留下无法发射入口，作为被否决的最小对照，不建议成为正式实现；两者互斥。该建议不删除04源资产或正式资源本身。主补丁与02的代码文件互不重叠，可由Root分别审入。

## 验证与边界

- `python3 prepare_patch.py`仅写本目录候选／diff，记录输入与候选SHA。
- `python3 run_isolated_tests.py`：独立JDK21/Kotlin2.1.20，NativeImpactLight新7例＋原SoftContactEnvelope7例，14/14通过；不启动Gradle。
- `python3 check_patch.py`：在本目录临时的5份输入文件fixture中dry-run和apply，再逐项核候选SHA／删除项，均通过。BSD patch使用-E移除空删除文件；没有在app目录应用补丁。
- 源锁`source_lock.json`、`patch_check.json`核app输入未变；独立审查确认材质全覆盖路径退出，暂停／换轮／过期边界保持。
- 可选02清理另有独立15/15纯测试与源锁，见其verification.json。

未验证：HomeStage完整SDK/UI编译、Root组合构建、原生曝光／像素／短粒子捕获。候选数值仍需真实场景审校。Root应在managed build锁结束后按输入SHA审补丁，再用实际输入和原VFR采样核PBR细节保留；本目录没有制作或宣称任何新的“原生修复后”画面。
