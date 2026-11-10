# 酒馆试炼 HUD 设计

## 当前实现范围

既有 Full Stage 的两块 AttachmentPanel 承载轮次控制和战斗反馈。场景、刀客和玩家刀保持在中心视线，HUD 读取同一个 ArenaViewState。当前设计对应 revision 16。

用户本轮要求专注开发，暂不自测。当前修订交主控统一编译打包，本轮没有执行浏览器、测试或设备验证。此前版本的运行通过记录只适用于其原始版本，新版运行效果与完整布局仍需后续确认。

## 两区域布局

| 区域 | 逻辑尺寸 | 内容 |
| --- | --- | --- |
| 场边控制面板 | 400×400dp | 真实试炼状态、试炼目标／异常提示、开始／暂停恢复／重开、四条刀术要诀、桌面动作预演或结算 |
| 对手上方状态面板 | 500×260dp | 当前刀客名、轮次与剩时、阶段与招向、攻防提示／真实蓄势进度、双方资源、即时反馈和连击 |

物理位置与米制缩放由 HomeStage 挂接时统一处理。两面板继承当前 arena-root，使用中心锚点。状态面板底边应保持在敌人头部上方。没有新增容器、独立窗口或场景。

控制面板顶部的标题、场次、状态与轮次控制固定可见，下方教学、动作预演或结算在面板内纵向滚动，避免内容被裁切。胜负标签优先于暂停标签。

两个 bounded surface 各使用一份已声明的 app-owned 墨色底和米色前景。保留原生 PicoTheme ColorScheme。正文、按钮和资源条使用 SpatialUI built-ins，组件内部状态颜色由其颜色参数统一配置。方向印只显示当前实际来势，待机时收起，并保持平面文字及颜色高亮。

## 真实数据契约

ArenaViewState 是唯一呈现数据源。

- TrialResult 区分 READY、COUNTDOWN、FIGHTING、ROUND_CLEAR、VICTORY、DEFEAT。
- pauseReason、pauseId 和 resumeReady 决定暂停及显式恢复入口。
- playerHealth、playerStamina、focus 和敌人 health／initialHealth 决定资源条。
- roundNumber／roundCount、remainingSeconds、countdownSeconds 决定轮次及倒数。
- combo 和 feedback 决定战斗反馈，score 与 bestScore 在结算区显示。
- enemyName来自当前实际角色目录，作为状态牌标题。
- motionCharge是0到1的真实双手收刀蓄势进度，前推锁存后投影为0。motionReleaseRequired直接来自识别器的skillLatched，表示前推后仍待回收复位，界面显示中性“收刀复位 · 再起下一式”并收起进度条。真实技能结果继续读取feedback。
- 未前推时，满蓄势按executionAvailable和focus提示向前推刀处决／破势，气势不足时明确提示。暂停、失效、重开与恢复基线撤销这两项手势投影。
- executionAvailable 或 focus 满值共同决定统一的“破势 / 处决”预演入口。对手虚弱时，同一个双手蓄势前推动作自动处决。
- inputOrigin 与 DesktopCombatInput.enabled 区分桌面预演和设备头手来源。

UI 不建立第二份战斗规则，也不改变血量、分数或胜负。界面资源条显示真实数值，非法最大值时进度显示为空。

## 控制与完整流程

1. READY 时，仅在场景、输入与控制对象可用时开放开始。
2. COUNTDOWN 显示真实倒数，FIGHTING 显示当前资源、阶段及反馈。
3. ROUND_CLEAR 显示真实倒数，中间轮次提示调息后再战，最后一轮提示收刀后结算，保留暂停与重新开局。
4. 暂停后仅在新基线就绪且当前 pauseId 有效时开放继续。观察重新到齐不会直接触发确认恢复。
5. VICTORY／DEFEAT 展示实际得分、最佳分与连战结果，再挑战通过同一 onRestart 回调重置。
6. 未结算时重新开局保留确认对话框，确认后由既有输入队列生产 ROUND_RESET。

## 桌面动作预演

桌面输入来源下显示五个动作按钮，依次覆盖斩击、前刺、架刀、侧闪、破势 / 处决。按钮调用 onDesktopAction，后续由输入层生成连续头手轨迹，再进入与 VR 相同的战斗判定。

键位提示覆盖1/J斩击、4/K刺击、5/V架刀、8/Z左闪、9/X右闪、C下蹲、G破势 / 虚弱时自动处决。预演区仅在桌面来源或已启用桌面预演时显示。两种输入模式均可滚动查看“进刀、架刀、避锋、破势”四条要诀，逐条说明动作姿态和结果。

预演按钮只在 FIGHTING、输入及动作基线就绪且未暂停时可用。统一的破势 / 处决入口在气势满值或 executionAvailable 时开放。结算页面用真实结果替代预演区。

## 完成与未验证范围

本轮已写入HUD、文案和单一设计IR。JSON 内嵌到 preview.html，与当前规格使用同一节点及字段。结构保留两块 bounded surface 和平面方向印。

本轮尚未执行运行自测，不能据静态源码认定射线命中、像素溢出、设备舒适度或游戏胜负闭环已经通过。根目录旧 designer receipt 的既有通过记录不代表 revision 16 已运行验证，主控需在后续验收时更新。

## 主题呈现要求

中式写实刀术短竞技场以手感和攻防可读性为首要目标。应用与控制区显示名为“酒馆试炼”。正常VR输入就绪时显示“连胜三场 · 读招、架刀、反击”，桌面预演、控制处理中和追踪异常保留真实来源／就绪提示。战斗区集中于资源、来势、反馈和有效连击，得分与最佳成绩放在结算区。角色与武器占据核心视线，面板服务近身交战。

## 动作细节与视觉层次

- 控制区以“酒馆试炼”和实际场次为首行，状态与试炼目标为次层。下方同一滚动区域容纳四条要诀，标题与动作说明左右分列。
- 状态区依次显示实际刀客名与轮次时间、阶段与真实来势、攻防提示、气血和体力／气势、即时反馈与连击。资源名与数值左右分列，沿用既有进度条。
- PREPARING提示观察刀路，STARTUP提示迎锋／闪身，ACTIVE提示接锋防御，RECOVERING提示趁隙还刀。弹反受击阶段与普通失衡分别显示对应反击提示。
- 非零蓄势进度或待收势状态替换常规攻防提示。蓄势时使用4dp细进度条与真实百分比，前推锁存后显示收刀复位，进度条收起。场外、暂停、输入基线失效与结算阶段收起手势提示。
- 全局状态优先于旧事件反馈，执行中、局间、终局与超时可各自读清。最后一场清场倒计时使用“结算”。

## UI组件与设计色映射

`com.pico.spatial.ui.design`中的Text、Button、Badge、LinearProgressIndicator与windows.AlertDialog承担文字、控制、来势印、资源／蓄势与重开确认。两个入口分别包裹PicoTheme，原生ColorScheme角色保持由系统提供。现有四个app-owned颜色仍为ArenaPanelSurface #101010、ArenaPanelControl #49443F、ArenaPanelText #F6F0E6、ArenaPanelSecondary #D3CDC4，对应IR的同名theme.brandColors。结构节点透明，背景各绑定control-surface与status-surface一次，交互沿用built-ins的悬停和反馈。

当前按用户要求只完成源码、设计IR和预览生产。设计样式验证、浏览器布局与设备可读性未执行，receipt标记当前修订待主控编译／后续运行验收。普通数据样例展示设备模式，fallback与error样例保留桌面预演，样例内容用于设计表达。

## 收势表达

前推锁存表示识别到一次手势，结果可能为破势、条件不足或尚未消费。复位文案保持中性，实际结果由既有feedback独立呈现。正常数据样例的fighting状态展示满气势释放后气势为0、需要收刀复位的画面，其余中断和终局样例的锁存投影为false。
