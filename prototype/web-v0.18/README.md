# 酒馆探索原型

本目录是独立的Web探索线，允许在`web/**`分支继续进行场景、美术、敌群和交互试验并提交独立PR。现有v0.34–v0.37成果保留，不因原生集成被封存或覆盖。

本次PICO参赛Demo仍以Kotlin原生APK、PICO Emulator和Space Pro验收。本目录的版本号、浏览器画面和玩法不能代替原生完成度；需要移植的内容由Root逐项选择和验证。原生制作队列不会自动迁回Web。

`tests/held-grip.mjs`已按历史版本恢复。它针对旧`firstPersonVisuals/hands.update`接口，当前v0.37重构了`renderFreeHand`，原测试暂不兼容，不能宣称护栏已通过。后续Web握持PR须针对当前真实实现迁移测试，覆盖持刀侧自动闭握、空手放松、左右手、失效边界和不篡改输入；不得删断言或复制被测实现取得绿灯。

两线边界、分支和合入规则见[协作协议](../../docs/collaboration-boundaries.md)。
