# 酒馆试炼 HUD 设计

## 当前实现范围

既有 Full Stage 的两块 AttachmentPanel 承载轮次控制和战斗反馈。场景、刀客和玩家刀保持在中心视线，HUD 读取同一个 ArenaViewState。当前设计对应 revision 13。

用户本轮要求专注开发，暂不自测。本轮没有执行浏览器、构建、测试或设备验证。此前版本的通过记录只适用于其原始版本，新版运行效果与完整布局仍需后续确认。

## 两区域布局

| 区域 | 逻辑尺寸 | 内容 |
| --- | --- | --- |
| 场边控制面板 | 400×400dp | 真实试炼状态、输入来源、开始／暂停恢复／重开、简短教学、桌面动作预演或结算 |
| 对手上方状态面板 | 500×260dp | 轮次与剩时、双方气血、体力、气势、阶段与招向、即时反馈、得分／连击／最佳 |

物理位置与米制缩放由 HomeStage 挂接时统一处理。两面板继承当前 arena-root，使用中心锚点。状态面板底边应保持在敌人头部上方。没有新增容器、独立窗口或场景。

控制面板顶部的标题、状态与轮次控制固定可见，下方教学、动作预演或结算在面板内纵向滚动，避免内容被裁切。胜负标签优先于暂停标签。

两个 bounded surface 各使用一份已声明的 app-owned 墨色底和米色前景。保留原生 PicoTheme ColorScheme。正文、按钮和资源条使用 SpatialUI built-ins，组件内部状态颜色由其颜色参数统一配置。方向印只使用同一平面上的文字及颜色高亮。

## 真实数据契约

ArenaViewState 是唯一呈现数据源。

- TrialResult 区分 READY、COUNTDOWN、FIGHTING、ROUND_CLEAR、VICTORY、DEFEAT。
- pauseReason、pauseId 和 resumeReady 决定暂停及显式恢复入口。
- playerHealth、playerStamina、focus 和敌人 health／initialHealth 决定资源条。
- roundNumber／roundCount、remainingSeconds、countdownSeconds 决定轮次及倒数。
- score、bestScore、combo 和 feedback 决定战斗与结算反馈。
- executionAvailable 或 focus 满值共同决定统一的“破势 / 处决”预演入口。对手虚弱时，同一个双手蓄势前推动作自动处决。
- inputOrigin 与 DesktopCombatInput.enabled 区分桌面预演和设备头手来源。

UI 不建立第二份战斗规则，也不改变血量、分数或胜负。界面资源条显示真实数值，非法最大值时进度显示为空。

## 控制与完整流程

1. READY 时，仅在场景、输入与控制对象可用时开放开始。
2. COUNTDOWN 显示真实倒数，FIGHTING 显示当前资源、阶段及反馈。
3. ROUND_CLEAR 显示后续场次的真实倒数，保留暂停与重新开局。
4. 暂停后仅在新基线就绪且当前 pauseId 有效时开放继续。观察重新到齐不会直接触发确认恢复。
5. VICTORY／DEFEAT 展示实际得分、最佳分与连战结果，再挑战通过同一 onRestart 回调重置。
6. 未结算时重新开局保留确认对话框，确认后由既有输入队列生产 ROUND_RESET。

## 桌面动作预演

桌面输入来源下显示五个动作按钮，依次覆盖斩击、前刺、架刀、侧闪、破势 / 处决。按钮调用 onDesktopAction，后续由输入层生成连续头手轨迹，再进入与 VR 相同的战斗判定。

键位提示覆盖1/J斩击、4/K刺击、5/V架刀、8/Z左闪、9/X右闪、C下蹲、G破势 / 虚弱时自动处决。预演区仅在桌面来源或已启用桌面预演时显示。设备输入下显示举刀、挥刀、侧移／下蹲和双手蓄势前推的动作教学。

预演按钮只在 FIGHTING、输入及动作基线就绪且未暂停时可用。统一的破势 / 处决入口在气势满值或 executionAvailable 时开放。结算页面用真实结果替代预演区。

## 完成与未验证范围

本轮已写入HUD、文案和单一设计IR。JSON 内嵌到 preview.html，与当前规格使用同一节点及字段。结构保留两块 bounded surface 和平面方向印。

本轮尚未执行运行自测，不能据静态源码认定射线命中、像素溢出、设备舒适度或游戏胜负闭环已经通过。根目录旧 designer receipt 的既有通过记录不代表 revision 13 已运行验证，主控需在后续验收时更新。
