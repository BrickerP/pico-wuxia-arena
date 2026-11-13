# PICO CLI 开发手册

这份手册给第一次做 PICO 空间应用的人，以及替他们写代码的 Agent。阅读器、设置页、模型看馆、培训、导览和游戏走的是同一套命令。产品不同，是人在空间里要完成的事不同，不是 CLI 不同。命令和参数按 `pico-cli` 0.6 这一代整理。真正执行前，以当前安装的帮助文本为准。

```bash
pico-cli --help
pico-cli <command> --help
pico-cli <command> <subcommand> --help
```

人用一句话说明要看到的结果。这句话可以是「面前有一块能点的目录」，也可以是「房间里能转着看一个模型」，也可以是「走进一段连续的空间」。Agent 自己检查环境、改工程、构建并安装，再把命令原文和一张能打开的画面交回来。如果这轮改的是交互，还要有一段日志，证明一次真实输入进了程序，并且程序因此发生了对应的变化。人不需要先学会 Gradle。一份还没跑过的命令清单不算做完。构建成功只说明安装包打出来了，头显里有没有跑起来要另说。

## 这是什么

PICO 是头戴显示器。人戴上之后，软件出现在眼前的空间里。头的朝向、手柄的按钮和位置，就是输入。这样的软件叫空间应用。它可能是面前的一块面板，可能是放在真实房间里的一件模型，也可能是一整段把真实房间换掉的体验。游戏只是最后这种体验里的一种。面板工具、内容浏览器和培训场景用同样的工程、同样的构建和同样的安装。

Spatial SDK 用 Kotlin 写这类应用。平面上的按钮、文字和菜单走 SpatialUI。空间里的模型、位移和动画走 Entity 与组件。`pico-cli` 管环境、工程、模拟器、安装、日志和性能。人要完成什么，仍要人先说清楚，命令行不会从「做个 PICO 应用」里猜出产品。

CLI 就是终端里的命令。这里说的 vibe coding，是人描述结果，Agent 按这份手册改工程并自己把命令跑完。

本手册统一使用 Kotlin 与 PICO Spatial SDK 的原生工程路径。

## 先决定人转头时看见什么

写功能之前先定容器。容器决定头转开以后，人看见的是系统房间还是你做出的空间。这个选择写进创建命令，后面很难靠界面补救。

人只需要一块能阅读和点击的面板时，用 `planar`。面板留在面前，头转出去就回到真实房间。目录、设置、阅读和信息页通常是这样。人要在自己的房间里观看或摆弄一件立体物时，用 `volumetric`。房间还是真实的，物体放进来。模型预览、产品和说明物体通常是这样。人要留在你做出的整段空间里，转头看见的仍是这段空间时，用 `stage`。导览、培训、叙事和游戏都可能需要它。决定因素是转头以后还要不要看见你的世界，不是这个项目算不算游戏。

头的物理转动，和内容里设计的「回头看」，是两件事。Stage 里回头，看到的仍是这段空间。Planar 里回头，看到的是系统环境。如果内容依赖人转头去看自己布置的后方，创建时就用 `stage`。

## 环境

只要这轮要跑 `pico-cli`、查询 PICO 开发知识，或者启动模拟器，就先做一次只读检查。只读代码和讨论结构时不用检查。同一次会话里没有装过插件、没有改过 SDK、也没有新的报错，就沿用上一次的检查结果。

```bash
command -v pico-cli || echo "pico-cli not on PATH"
pico-cli --version
pico-cli doctor --help
pico-cli doctor --format json --platform spatial
```

`doctor` 只报告现状。它不安装插件，也不升级工程里的 Spatial SDK。输出里有 error，就把原文和它建议的修复命令交给人，停住。人明确要求修复之后，才运行 `pico-cli doctor --fix`、`pico-cli setup` 或 `pico-cli plugin update`。warning 和 `PARTIAL` 说明有缺项，交付里写上缺的是哪一项。缺项还在，就不要把环境说成已经全部就绪。

工程使用的 Spatial SDK 和本机知识数据要在同一个 `major.minor` 上。工程是 6.1，知识线也是 6.1。发现两边不一致，只报告差异。升级工程 BOM 等人单独提出。

工具靠环境变量找到 JDK、Android SDK、PICO SDK 和设备。具体目录以这次 `doctor` 的输出为准，不要猜一个路径写死。

| 变量 | 作用 |
| --- | --- |
| `JAVA_HOME` | 跑 Gradle 的 JDK。Spatial 6.1 模板用 JDK 21 跑构建，Kotlin 字节码目标仍可以是 11。两处各自保留。 |
| `ANDROID_HOME`、`ANDROID_SDK_ROOT` | Android SDK。Platform 与工程的 `compileSdk` 一致。 |
| `PICO_HOME` | PICO SDK 根目录。 |
| `PATH` | 能找到 `pico-cli`、`java` 和 `adb`。 |
| `PICO_CLI_DEVICE`、`ADB_SERIAL` | 多设备时的默认目标。单次命令更稳妥的是显式 `--device`。 |
| `PICO_CLI_NO_TELEMETRY=1` | 关闭 CLI 遥测。 |

官方模拟器要求 Apple Silicon、macOS 14 或更高、16GB 内存和足够磁盘。Windows 走官方支持的那条模拟器路径。启动时调用本机已经安装的模拟器程序。会改写或重签可执行文件的沙箱会破坏 macOS 上的 Hypervisor 权限，随后出现 `HV_DENIED`。这时换一条保留原签名的本机通道再启动，重装模拟器解决不了签名问题。

Android Studio 不在模拟器检查里。只有要做 Android Studio 插件时才需要它。

## 命令怎么选

先判断这轮要改变的是主机环境、工程文件，还是已经连上的设备。环境问题用 `doctor`、`setup`、`plugin` 和 `knowledge`。新建工程用 `project`。模拟器的一生用 `emulator`。已经连上的头显或模拟器用 `device` 查看，用 `app` 安装和启动，用 `files` 传文件，用 `capture` 取画面，用 `log` 或 `app logcat` 读日志。卡顿和掉帧用 `perf`。设备上的视觉或机器学习管线用 `spatialml`。

高层家族能完成的事就停在那里。`pico-cli shell` 只在需要一条设备上的 shell 时使用。`pico-cli adb` 是最后的退路，留给高层命令没有覆盖的操作。

```bash
pico-cli doctor
pico-cli setup
pico-cli plugin update
pico-cli knowledge
pico-cli project create
pico-cli project context
pico-cli emulator
pico-cli device list
pico-cli app
pico-cli files
pico-cli capture screenshot
pico-cli capture record
pico-cli log
pico-cli app logcat
pico-cli perf
pico-cli spatialml
pico-cli editor
```

会写主机、写设备，或一直占着终端的命令，执行前先说清楚它的效果。删除模拟器、删除已下载镜像、删除设备文件、卸载应用、改设备属性，都等人明确说了再做。

```bash
pico-cli emulator delete
pico-cli emulator delete-image
pico-cli files rm
pico-cli app uninstall
pico-cli adb setprop
pico-cli adb root
```

需要一直看输出时，才使用 `--follow`、`app watch-crash`、`emulator start --watch`、`perf live` 和 `perf trace record`。只取一次证据时，用有限时长和明确的输出路径，命令结束后确认那个文件还在。

后续步骤还要读取这次结果时，加上 `--format json`。给人看一眼时，普通文本就够。

## 创建工程

在空目录里创建。工程名放在 `--name`，包名放在 `--package`。这两个值不要写成命令末尾的位置参数。目录里已经有 Gradle 工程、而且人同意覆盖时，才加 `--force`。

```bash
pico-cli project create \
  --template planar \
  --name demo \
  --package com.example.demo
```

面板应用保持 `planar`。整段沉浸空间换成 `stage`。房间里的单件模型用 `volumetric`。`--template` 只接受帮助文本里列出的名字。原生模板为 `planar`、`volumetric`、`stage`。`--sdk <version>` 只在人指定了 SDK 版本时使用，否则跟随当前平台记录。

工程生成之后，先读这版 SDK 模板里的 `.mustache` 骨架，再读工程自己的 `gradle/libs.versions.toml`、`app/build.gradle.kts` 和入口 Kotlin。模板是这版工具实际打出来的结构，比网页上的概述更接近你手里的工程。`pico-cli` 附带的 Agent skills 按主题拆开：SDK 用法、SpatialUI、场景、模拟器和性能各看各的。网页用来补概念。中文文档在 `https://developer-cn.picoxr.com/document/`，英文文档在 `https://developer.picoxr.com/document/`。模板、当前工程和 `--help` 说的不一样时，以后三者为准。

二维界面沿 SpatialUI。入口包在 `PicoTheme` 里，颜色和字号用主题角色。模板如果排除了普通 Compose UI 包，新的依赖保持这个排除。`androidx.compose.material` 和 `material3` 会把另一套主题带进来，和 SpatialUI 的焦点、音效与触觉不是一条路。

一个应用模块就够开始。平台生命周期、二维界面、三维实体和输入适配分成能读完的几块。过早拆成多模块，只会让第一次构建更难查。

## 构建

在工程根目录打调试包。

```bash
./gradlew :app:assembleDebug
```

产物在 `app/build/outputs/apk/debug/app-debug.apk`。失败时停在这份日志上改。另开一个目录重做，会把同一次失败复制出去。

Spatial 6.1 模板里，`compileSdk`、`minSdk` 和 `targetSdk` 通常是 35，ABI 只有 `arm64-v8a`。以生成出来的 Gradle 为准。包的 ABI 跟头显一致。模拟器帮助没有要求 x86 时，不要为了桌面架构再加一套。

## 模拟器

没有设备时，先让模拟器启动完成，再安装应用。`pico-cli shell` 看到没有设备，只会失败，它不会自己创建一台模拟器。

```bash
pico-cli emulator doctor --format json
pico-cli emulator list --managed-only --format json
pico-cli emulator start --help
```

模拟器版本和工程的 Spatial SDK 线用同一个 `major.minor`。先安装对应的包，再创建 AVD，然后启动。这样启动不会悄悄选到机器上另一条已经下过的版本。

```bash
pico-cli emulator install --version <major.minor> -y
pico-cli emulator create --version <major.minor> -y
pico-cli emulator start --version <major.minor> --format json -y
pico-cli emulator status --format json
```

读启动结果时看进程是否还在、`adbOnline`、`bootCompleted`、AVD 名字、`adbDeviceId` 和 `bundleVersion`。`PARTIAL` 的意思是这一台还没好。继续查同一台的状态。再启动第二台，两台会抢同一套锁和端口。`adbOnline` 只说明调试通道通了。对该设备执行 `getprop sys.boot_completed`，返回 `1` 才是系统启动完成。同一次启动结果里如果已经有 `bootCompleted=true`，可以直接当作就绪。

名单里没有你要的那个 AVD 名字，就不要用这个名字去启动。从返回的可用名单里选版本匹配的一台。一台都没有，回到 `install` 和 `create`。

工作结束用 `pico-cli emulator stop`。崩溃之后用 `pico-cli emulator dump-logs`，或者 `pico-cli emulator log --last`，先看模拟器自己的日志。黑屏、闪退、GPU 和 Hypervisor 问题，多数先出在这里，然后才轮到应用代码。

## 真机和多台设备

```bash
pico-cli device list --format json
```

命令上的 `--device <id>` 优先于 `PICO_CLI_DEVICE`，再优先于 `ADB_SERIAL`。都没写时，CLI 自己选一台。旁边还有别的设备时，自己选会把包装进旁边那台。选定之后记住这个 id，后面的安装、文件、截图、日志和 shell 都带上同一个 `--device`。这台掉线了，再重新列一次设备。少数命令写的是 `--adb-device`，以那条命令的帮助为准。

模拟器用来提前看界面、文字、模型和桌面上的替代输入。头显上才看真实的头和手柄：面板是否跟着视线，物体是否拿得起来，空间是否让人愿意多留一会。发热、持续佩戴和舒适度也在头显上记录。模拟器里的帧率只说明这一次桌面跑得怎样。

## 安装、日志和画面

设备就绪以后安装并启动。包名来自工程的 `applicationId`，Activity 来自 Manifest。启动了别的包，等于这轮没有启动。

```bash
pico-cli app install <apk> --device <id>
pico-cli app launch <package> --device <id>
pico-cli app info <package> --device <id> --format json
```

看这个应用的日志时带上包名。不带包名时，`app logcat` 读的是整机日志，信号会淹没掉。崩溃监视会一直占着终端，只在需要盯崩溃时开。第一遍日志用高层命令，不必落到 `pico-cli adb logcat`。

```bash
pico-cli app logcat --package <package> --device <id>
pico-cli app watch-crash <package> --device <id>
```

截图和录屏都写出一个明确的文件。命令返回之后，确认这个文件存在而且打得开。

```bash
pico-cli capture screenshot --device <id> --out <path>
pico-cli capture record --device <id> --time <seconds> --out <path>
```

空间截图有时会失败。这时改用模拟器窗口、系统录屏或其他能打开的画面，并写明换了哪条路径。模型的包围盒、顶点数量和「加载成功」只说明资源进了内存，人还没有看见画面。

`pico-cli shell input tap x y` 点的是普通二维屏幕坐标。它适合还躺在普通 Android 画面上的界面。Stage 和 Volumetric 里的空间点击、手柄射线和手势不走这块屏幕缓冲，所以换一组坐标再点，不会变成一次空间里的选择。验证被这个限制挡住时，直接说明。

## 输入为什么要先证明一次

头显上的确认、点选、抓取和移动，来自头的朝向、手柄按钮和手柄位置。桌面如果要提前试，就制造同一种输入，送进同一段处理。键盘若直接改应用内部的结果，桌面上能看见变化，戴上头显却没有对应的按钮或姿态，这条变化到了设备上就不会发生。

所以第一件要证明的事很小，而且跟产品种类无关。一次真实的点击、按键、视线停留或手柄动作，出现在日志里，并且应用因此打开了下一页、选中了物体，或移动了内容。日志里没有这次输入，后面的灵敏度、碰撞范围和测试用例都没有依据。面板应用证明的是点击进了界面。看模型的应用证明的是抓取或旋转进了物体。沉浸空间证明的是头或手柄进了这段空间。证明的是「输入到了，结果跟着变了」，不是某一种玩法。

追踪丢失、离开界面和重新进入时，把上一轮还没处理完的输入清掉。否则下一次进入会接着上一次的手势或点击继续。

## 模型怎样进到空间里

没有三维内容的面板应用，可以跳过这一节。需要模型时，运行时文件放进 APK 的 assets，异步加载，离开当前界面或空间时释放。GLB 和 glTF 可以直接加载。进空间之前收成米制：需要站在地面上的物体，底部贴地；+Y 朝上；正面朝 +Z。再按它在房间里应有的真实尺寸缩放。原始导出、加工文件和打进包里的那一份分开存放。加工只解决单位、轴向、原点和它与人的手或房间的相对位置。

界面和空间共用一套生命周期。人离开、追踪丢失或重新打开时，画面、动画和还没处理完的输入一起收起来。只停逻辑、不停画面，人会看到物体还在做已经结束的动作。

用外部服务生成模型时，先分清网页订阅和 API 是不是两套账户。很多服务里，网页积分不能调用 API，在网页里生成也不会减少 API 余额。Agent 和批量生产走该服务的 CLI 或 API，并且显式选择账户区域。区域猜错，查到的是另一个余额为 0 的账户。生成前先跑不扣费的估价。任务失败会退回冻结额度。等待超时只说明结果还没回来，先继续查同一个任务。立刻再提交一次，会再冻一笔，并且得到两个不知道哪个算数的结果。密钥留在本机的 CLI 配置或环境变量里。免费网页套餐常常把模型公开，并限制导出或商用。需要对外发布时，用来源和许可已经写明的那一次生成。

场景编辑器还没装时，代码直接加载 GLB。编辑器以后负责摆放、材质和打包，再走 `pico-cli editor`。缺编辑器的时候，继续用现在这条加载路径，不必换一套渲染。

## 性能和端侧模型

人感到卡、掉帧、启动慢，或者 CPU 与 GPU 持续很高时，先跑 `pico-cli perf doctor`，再按帮助录一条 Perfetto。结论引用 trace 里的时间段。头显上的发热、能戴多久、舒不舒服，要在头显上另记。这和是不是游戏无关，只和人要在这段空间里停留多久有关。模拟器的帧率只说明桌面这次跑得怎样。

应用确实要在设备上跑视觉或机器学习时，才进入 `pico-cli spatialml`。先做 `spatialml onboard` 和 `spatialml doctor`，再安装和导入。这条命令族用于当前 Kotlin 工程。模型包和 Python 侧工具的版本，以医生输出和子命令帮助为准。

## 一轮是怎样推进的

先用一句话写清这轮结束时人能看见什么、能做什么。这句话如果涉及运行，就先做环境检查，有 error 就停。新工程用 `project create` 生在一个空目录里。已有工程就在原目录继续，同一条功能不再复制出一个新仓库。不认识的命令先看帮助。要交给下一步解析的结果用 JSON。

改完就打调试包。模拟器或头显就绪后安装并启动同一个包名。然后取日志，并拿到一张打得开的画面。这轮如果改了点击、抓取、视线或手柄，还要有一条日志证明这次输入进了程序，而且界面或空间因此变了。交付里留下命令原文、产物在哪，以及这轮还没在设备上验证的部分。多设备时全程带着同一个 `--device`。破坏性命令等人说了再执行。模拟器若因为沙箱签名起不来，换一条保留原程序的本机通道再试一次。

这些失败往往连在一起。输入还没进应用就去调灵敏度或范围，调完也无法知道是参数错了，还是这次操作根本没到。用二维点击去点空间里的物体，日志会安静，因为那一下没有打到空间内容上。用编译成功或模型尺寸代替画面，人仍然不知道空间里长什么样。空间截图失败后如果没有任何替代画面，这轮就停在「可能显示了」。启动结果已经是 `PARTIAL` 再开一台，后面的安装会不知道自己进了哪一台。多设备却不写目标，包装进当时被选中的那一台，常常是旁边的模拟器。网页订阅和 API 混用，或者让 Agent 按语言猜测区域，扣费和余额会对不上。密钥进了仓库，就无法再靠轮换单点挽回。医生还报着 error 就去写产品行为，行为会建在缺的那项工具上。知识线版本不同就去改工程 SDK，会把一次环境差异变成一次依赖升级。一次普通的启动失败就去删模拟器镜像，下次还要从下载开始。

## 怎样说这轮在设备上跑过

调试包要打成功，并且说得出 APK 在哪。`app info` 或启动日志要证明目标包名已经装上并启动。还要有一张打得开的画面。这轮如果包含交互，还要有一段日志证明真实输入进了程序，并且产生了人能理解的变化：翻到下一页、选中物体，或内容跟着头和手移动。发热、持续佩戴和舒适度如果这轮没在头显上测，就写成没测。少了其中任何一项，这轮就还没在设备上跑过，下一步只给补上这一项的那条命令。
