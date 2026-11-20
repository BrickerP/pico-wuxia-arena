# 原生刀客对决验收

**11 月 20 日当前开发预览：[接刀还锋 APK](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-shoulder-counter-2026-11-20/arena.apk)。** 首敌真正被挡住后，提示玩家先收手、从空出的肩侧回击。发布包能进入准备页；宿主窗口遮挡导致本次开始点击未送达，尚无此包胜负记录。

攻防基准由一正一反两条轨迹组成。正例使用 50 Hz 合成头手观察，经正式输入和战斗判定，先架住首敌再沿肩线还击、对第二人改变刀路、在玄甲上举时进刀；通过三场并重新开始。演练约 69 秒，右握点到肩的最大距离约 69 cm。这证明当前源码中的三场路线可达，不证明 PICO 模拟器、头显或真人已经打通此包。维护者可单跑 `./gradlew :app:testDebugUnitTest --tests '*DeliberateDuelTrialTest'`；重复横扫的反例见 `RepeatedSweepTrialTest`。正常发版无需为同一包反复重跑。

| 对局里要看什么 | 对应版本的证据 |
| --- | --- |
| 读招是否真的有效 | [收刀迎锋：首刀实录](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-compact-guard-2026-11-20/compact-guard.mp4)。在有效下劈期发生 `BLOCK / braced=true`，随后第一次还刀碰到收势中的钢刃，不算命中。该局打过首敌，第二场落败、150 分，并成功重开。 |
| 擦钢是否还会冒充格挡 | [擦钢与格挡声音对照](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-steel-accent-2026-11-20/touch-touch-block.wav)是制作音频，不是头显收音。对应包原生实战记录到真正的格挡和单独的轻擦事件；轻擦没有强火花或人为的全局顿帧。 |
| 首次启动 | 首场迎刀包在这台 Mac 的模拟器上遇到一次启动无响应。系统主线程栈停留在 Android 绑定应用、加载 PICO 原生运行时；选择等待后同一进程进入 Full Stage。未归因于游戏模型，亦未声称该问题已消失。 |

**动作对照：[送刀、短腕切与轻擦](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-committed-cut-2026-11-18)**（APK `1353185f…`）。同一包、同一原生入口，固定握点 64 次左右摆动：24 次轻擦、0 有效伤害，首敌仍为 100/100，玩家 0 分。主动送手：4 次有效命中，打败首敌，第二场落败、145 分。[实伤](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-committed-cut-2026-11-18/committed-cut.mp4) · [轻擦](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-committed-cut-2026-11-18/fixed-wrist-graze.mp4)。这些证据没有显示新版三场通关。

场景单变量：119→87 个不透明图元实例；固定开局八秒，空间帧间隔 P50 48.34→40.96 ms、P95 83.61→66.96 ms、最大 279.45→156.70 ms。单次、接触数和宿主负载并非完全一致。不能将改善折算为头显帧率，或称卡顿已消失。

**上一版对照：[架势提示与再挑战](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-arena-preview-2026-11-18)**（代码 `47aaf2c`，APK SHA256 `22ea58d3cbeaa34a33505ace04173fd9b78dd24252faa861fdb759b850b1911c`）。

- [跟随对手位置的攻防实录](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-arena-preview-2026-11-18/native-arena-victory.mp4)：829 分，余血 100，三场通关。Boss 有四次软命中，不代表出现了弹反。[同进程重开](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-arena-preview-2026-11-18/native-arena-replay.mp4)进入首场倒计时。
- [固定左右横扫](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-arena-preview-2026-11-18/native-arena-fixed-sweep.mp4)：也能打通三场，782 分、余血 80，无弹反。**流程通过，抗重复挥刀的玩法验收不通过。**
- 此包在固定交战开局八秒的应用空间帧回调间隔 P50 48.34 ms、P95 83.61 ms、最大 279.45 ms。**不能称为流畅。** 尚无 Space Pro 实机帧时。

以下为较早版本的证据，不代表当前包。

**11 月 18 日原包的流程可达，可玩性不通过。** 下表原包通关记录保留作为负例。
进攻负例是在同一站位反复做两方向的横扫；它不应稳定通关。正例须能打出合法横斩，并能看懂敌人挡住或露出破绽的原因。
左右玩家手、敌人持刀手与空手分别看张开、握刀、起手、接触及回收的手背和掌面；单看握点位置不足以证明关节正确。
卡顿按实际交战的原生帧间隔和长帧比较，另看切换敌人时的停顿。录像封装的帧率和通关时长都不能作流畅度成绩。

| 检查项 | 如何判定 | 状态 |
| --- | --- | --- |
| 刀面与交接 | 用正式刀刃的 5533 个 Steel 顶点检查七段接触体；停刀、退刀与回守使用同一形状 | 最大外侧距离 0.416 mm，几何验算通过 |
| 入场与实战 | 从 Full Stage 点击开始；真实模拟手柄打中对手或挡刀；连续录像看得见敌我与刀 | 通过。首局接受 25 个接触事件，含 7 次格挡、8 次软命中、2 次玩家受击；本次没有弹反记录。 |
| 对方收刀 | 收势中再遇钢，继续原动画，下一招仍可出 | 回归通过：旧版在 1.381 s 处截断，新版在距离 1.750 s 末端一个测试步长内收回；三场实战均可继续。未逐帧量测 GPU 蒙皮接点。 |
| 结算与重开 | 不改血量或时钟，在同一 APK 打完三场并重新开局 | 通过。首局 3/3、1010 分、余血 80；同一进程先后接受第 0、3 代的开始请求，均从 READY 进入 COUNTDOWN。本轮未演示败局。 |
| 头显手感 | Space Pro / OS 6 上实际架刀、迎击并撤手；检查触觉同步、舒适度及持续帧时 | 待真机 |

录像保留原始时间顺序，记录 APK 标识；宿主录屏只用于评估可见动作，不用于估算头显帧率。

2026-11-18：[原包与连续录像](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-2026-11-18)。原生代码 `1244f83`，安装包 SHA256 `dcafb901aa8e8f61fdfe25fd0cc4e5bfc6644ec2ab58aebefce605c2c44a1527`。

## 第一轮修复对照

| 检查项 | 证据与判定 |
| --- | --- |
| 玩家手 | [同机位左右手：旧闭握、新闭握、新空手](../ArtSource/refinement/presentation/native-player-grip-pose-comparison-2026-11-18.jpg)。每只手闭握的非相邻三角面自交 136→0，柄芯交叉 10→0。指腹仍与表层缠绳局部相交，关节外观和材质未作最终验收。 |
| 对手 | [三招空手腕对照](../ArtSource/refinement/presentation/opponent-empty-wrist-2026-11-18.jpg)。三名对手重导，4,281 行碰撞采样未变；原有老兵前臂/胸甲一处相交仍在。持刀右腕的候选未过刀路/穿插检查，没有采用。 |
| 同样横扫 64 次 | 原包通关 1010 分、余血 80。候选 A（`70e9b4bd`）仍通关 767 分、余血 60，失败。候选 B（`08b48fce`）一轮首场落败、35 分；只能证明这条轨迹不保证赢。这局没到第三人，不能证明其护甲玩法可读或好玩。 |
| 流畅度 | **未通过。** 同机同段、首敌固定动作 10 秒：原包→A 的应用空间帧间隔 P50 39.08→42.28 ms，P95 88.03→79.08 ms，最大 106.71→348.31 ms。最慢帧中 relayout 的 Binder 调用用了 323.7 ms。这不是 GPU 帧率，亦不能用作 B 或头显的成绩。 |

候选 B 的原生代码为 `dd04b19`。另一次按来招操纵模拟手柄的实战中，首敌在格挡后 380 ms 受到还击；玩家打败前两名，第三名仍为 150/150，最终落败。**没有证明这个版本的 Boss 能在模拟器里被合理击败。** 同一局的独立十秒采样中，应用空间帧间隔中位 33.21 ms、P95 67.19 ms、最大 162.55 ms（288 个间隔中 39 个超过 50 ms）。输入不同，不能据此宣称相比 A 提速。
