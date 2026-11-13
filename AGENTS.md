开工先读 `docs/collaboration-boundaries.md`。原生任务再读 `docs/agent-start.md`；独立Web任务读 `prototype/web-v0.18/README.md`。

本仓库维护两条独立工作线：

- 参赛原生Demo：Kotlin + PICO Spatial SDK6.1.9 → APK → PICO Emulator → Space Pro/OS6，Full Stage。Root及原生subagents继续走这条验收路径；Web试玩、HTML或Three.js不能代替原生开发/设备证据。
- 独立探索原型：`prototype/web-v0.18/`，允许`web/**`分支继续探索、美术与敌群试验并提独立PR。Web版本号和功能不计为原生完成度；进入原生的内容另经Root选择、移植和验证。

两条线都保留已有成果和回归测试，禁止为集成另一条线而覆盖或整目录删除。手册修改只提交文档差异，不用旧分支树替换main。Root统一审核合入、正式原生资源、构建、设备和发布。

原生玩法/构建入口见`README.md`，验收事实见`docs/acceptance.md`，各路工程交接见`docs/agents/`。不复制仓库，不修改pico或个人网站仓库。新Web任务须来自其独立工作线，原生agent不因本协议自动切回网页。
