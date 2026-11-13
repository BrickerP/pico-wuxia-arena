# 原生Demo与探索原型协作边界

协作沟通与Web回归迁移跟踪：[Issue #12](https://github.com/BrickerP/pico-wuxia-arena/issues/12)。旧手册PR的清理回执：[PR #10评论](https://github.com/BrickerP/pico-wuxia-arena/pull/10#issuecomment-6844960438)。

## 工作线与验收

| 工作线 | 目录/分支 | 可以继续的工作 | 完成证据 |
| --- | --- | --- | --- |
| PICO参赛原生Demo | `app/`、`ArtSource/`；Root维护正式产线 | Kotlin + Spatial SDK6.1.9、Space Pro/OS6、Full Stage，既有短PVE三轮的模型/动作/手感/特效/UI | 对应APK、实际SDK输入与PICO Emulator/设备画面；真机项目另验 |
| 独立Web探索 | `prototype/web-v0.18/`、`web/**` PR | 探索场景、美术、敌群和交互实验；v0.38及以后可独立提交 | 对应Web版本的真实运行与回归，不声称原生已实现 |

本协议按2026-11-13用户提出的独立原型归属诉求更新：原生验收路线不变，取消对整个Web目录“停止维护/仅历史”的笼统限制。Root及当前原生subagent不会因而转做Web；Web成熟内容由Root另行选择、移植和原生验证，不自动重做整个城堡/敌群/boss进短Demo。

## 合入和文件保护

1. 两线共用本仓库，保留对方当前提交与文件；不复制仓库或另建同链路工作树。
2. 原生PR不得覆盖`prototype/web-v0.18/index.html`、其回归测试或Web证据；Web PR不得覆盖原生`app/`、正式`ArtSource/`与原生交接。跨线资源调整须明确列出并由Root审核。
3. 手册PR只改文档。从当前main出发查看merge-base后的提交差异；两个分支快照的全树diff不等于一次合并将执行的删除。
4. 不用checkout旧分支树、reset或整目录复制来“同步”main。合并前检查祖先关系、实际提交补丁和冲突；涉及上述受保护目录的删除必须单独审核。
5. Web版本`v0.x`与原生`native-*`检查点分开记录。浏览器截图、原生截图和测试结果不混用。

## 本次核验与处理

- `8c064c8 → a13af1f → 57d1fb9 → 76e5b89`均为main祖先；v0.37到本次main的`index.html`零diff，273703 B，SHA256 `a929fd446de8d4d8996349f24f03d1a07148a3939b8066e274596ed13e01c8b0`。
- `cf34487`合并保留v0.37原型内容。它没有覆盖原生线或Web线的当前实现。
- 旧`docs/pico-cli-handbook`远端分支60cf224已清理，手册保留在main的`docs/agent-start.md`。其提交实际只改3份Markdown（236行新增）；1021文件/164万删除是旧快照与main的差，不是该提交删除补丁。无工作树写入的三方合并模拟出现文档冲突，但app、ArtSource、原型三棵树均保持main，不能据快照diff断言正常合并必然删光项目。
- 本地同名旧分支另有未合入提交`49d6ef1`；其对象已用仅本地归档标签`codex/archive/local-handbook-native-49d6ef1`保留，不作为新合并入口，不推送该归档标签。远端文档分支与本地额外工作分别保护。
- 从`2f59db7`恢复`tests/held-grip.mjs`和`ArtSource/refinement/presentation/browser-main-2026-11-12.png/json`。三者按历史blob恢复，不代表旧测试已经适配v0.37。

## Web握持回归待办

原55行`held-grip.mjs`提取依赖已移除的`window.wuxiaFirstPerson`；当前实现也不再使用原`hands.update`/布尔返回接口。恢复后Node测试在提取边界失败；试验性适配边界后旧返回契约也不成立，因此本次保留精确历史文件，未通过修改游戏或放宽断言制造通过。

Web握持PR需将原保护目标迁移到当前真实实现：装备手自动闭握、另一手放松、左右切换、无装备、失效边界、输入状态不被呈现逻辑修改。此项归独立Web线，Root在合入前核对；旧构建证据只证明其原版本，不证明v0.37或原生APK。
