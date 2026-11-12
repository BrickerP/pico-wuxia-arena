# 透明交战 HUD · 源码候选

仅提交 `ArenaHud.kt` 的候选源码与 `../ui-polish.patch`。未改正式app、Palette、ArenaPresentation、Main/Adapter/TrackingSession/LaunchActivity、资源、Git、Gradle或设备。parent负责10号交接与同机位视觉审核。

## 视觉选择

正常FIGHTING左侧控制区完全透明：28dp非交互“试”印＋原生Small40dp暂停/重开。暂停朱砂，重开使用现有inkVeil作为低优先级颜色，点击目标均为标准Small40dp。删除正常交战固定标题、目标与重复轮次；保留400×160 Attachment。

COUNTDOWN/ROUND_CLEAR保留原controlStateLabel及真实秒数；controlPending保留处理中说明；场景或输入未就绪保留原等待/输入摘要。纸色READY/PAUSED/结算继续400×400，原开始/恢复门槛、ranchu等待帮助、教学页码、重开确认与结算不变。

上牌保持500×260，但移除整块墨色背景。敌名/轮次/血条、阶段/方向、全部三资源保持原层次和数值；主要文字沿现palette加轻墨阴影，四个数值用原生Badge作76×22dp小范围承托。原生Badge背景属于组件处理，没有添加app装饰边框或自制玻璃。没有新增poise/架势HP、状态字段、阈值或时钟。

默认“目标在范围内”不再生成末行。feedbackLabel只在最后默认兜底返回null：所有原status优先级、14种实际feedback、执行/满气就绪、护身、范围不足文本均保留。只要feedback或可见combo存在，末行仍绘制；仅combo时右对齐。phaseHint全部战术提示、release/蓄势/处决优先级及原incoming/combo/首帧强调门原样保留，不将“待机”和近期“受到攻击”当作重复文本删除。低资源仍走原LOW_STAMINA/LOW_FOCUS事件与生命≤25显色，未自创阈值。

## 实现与验证

- `source-snapshot/`、`source-shas.json`：原ArenaHud/Palette/Presentation及SHA，基线变化时生成脚本会拒绝覆盖。
- `src/app/src/.../content/ArenaHud.kt`：唯一候选改动。
- `build_candidate.py`：只写本候选和patch，用Python difflib输出unified patch，不执行Git。
- `compile_candidate.py`：Kotlin2.1.20＋Compose compiler孤立编译，读取已存在依赖及冻结class/R输入，不调用Gradle，不写旧candidate。
- `candidate-kotlin-compose.log` / `compile-driver.log`：编译退出0。
- `design-style.log`：candidate源码＋未修改Palette快照一起检查，0 errors / 0 warnings。native PicoTheme角色无替换；标准Button/Badge/LinearProgressIndicator/AlertDialog继续拥有交互、hover及前景色；没有自制hover。没有新增容器或修改根玻璃开关。R10来源追踪因未提交新的完整设计IR而跳过，不能把此门当作新的画面一致性验收。

四轮自审：保留所有准备/暂停/倒计时/换轮/终局与输入gates；清除死compact标题路径；沿全部stringResource与标准触控语义；未改依赖、配置、schema、Palette或业务时间线。独立只读审查确认默认兜底可空，其余反馈优先级不应删。

## 未验证

本次仅有实际候选源码、类型编译与样式门，没有运行Native renderer、浏览器、共享构建或设备。正常视距下的亮檐对比度、数字承托的观感、最大文本行高、头动和射线/触觉仍需parent按同机位审核；ImageGen mock不能代替端内证据。尤其需检查满蓄势＋方向＋长反馈＋combo同屏时的260dp容量，以及COUNTDOWN/ROUND_CLEAR秒数与pending/input等待同屏时的160dp容量。
