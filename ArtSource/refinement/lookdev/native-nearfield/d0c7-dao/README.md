# d0c76247 原生正式刀：单变量金属度判别候选

只交一个可由Root装入现有APK的私有runtime GLB。未改正式app、producer、library、原生源码、灯、曝光、全局IBL或场景；没有浏览器／Blender／设备／构建／Git操作，没有端内收益声明。

## 对齐到实际包

- APK：`d0c76247ce0e6957e721e4840a0ea7a5311fe8ba931cb9b45214d0d09088be95`，源提交`c07cdf6d440ef02291a12615b393c9c399b3d48a`。
- 实际包内DAO仍是`db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0`；`64da2798…`是庭院，不是刀。
- 原PNG源`ArtSource/refinement/weapon/stage2/dao_grip_refined.glb`：`a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637`。
- 上次三行侧光已进该APK，SceneLighting SHA `8d54c3fccc3fb5370ae2153c4fb0af4c51eb1591d3b20ef9faec6af2ac8dc71a`：key X=-1.10、20,000lm，手／刀fill 8,000lm。旧三行补丁冻结为已合入历史，不再重复应用。

## 根因证据及边界

1. **文件层资产通路没有发现黑刀缺陷。** 从实际APK读取DAO后确认与正式db28逐字节相同。已用现有KTX4.4.2解码18张level0图：颜色为sRGB、MR/normal线性、无swizzle、rd方向；锻钢颜色均值RGB约116/124/129、刃口160/167/172，不是黑图。有效锻钢roughness中位.333／metallic1，刃口.212／1，暗脊.518／.871。所有factor为有效默认1，无重复压暗、Unlit或emission。钢／铜不使用normal map；NORMAL单位有限、无零值或反向绕序、节点determinant正，TANGENT在源和运行文件都缺省。不能用“缺切线”解释没有normal map的主钢面。
2. **黑刀不局限命中瞬间，几何反射仍未唯一定位。** ready尚未开局和final通关屏都黑刀，手与铜件仍可读。PNG文件时间与接触日志标签间隔约4.807／1.270／25.146s，但文件时间不是曝光时刻，没有本次截图精确时钟桥或pulse-off回执，不能把这些差值当严格关闭证明。宽面经Blade节点逆转置得到资产法线约±Y，而不是刀轴。条件例子用日志手姿及假设头位(0,1.6,0)时，主光／fill在受光半球，却偏离窄镜面半向量约64°／69°；头位和c07的实际消费链未完整读回，所以不是实测N·V，也不证明唯一灯位根因。
3. **皮肤对照存在角色混杂。** ready的BASE是独立新头材质，VETERAN/INDIGO仍用各自原全身材质的脸，三者albedo/MR/normal payload不同。不能把BASE ready与VETERAN倒身白脸当同材质的近远灯光A/B。trial3-36只有一张亮脸，final脸已离开有效区域，尚不能证明白脸持续。本件不改皮肤或主光。

详见`asset-audit.json`与`timing-light-audit.json`。当前工作树HomeStage已经与c07构建pin不同；这些报告没有用新源码冒充当包的完整控制器消费路径。SceneLighting及NativeImpactLight与本包pin一致。

## 唯一推荐候选

`dao_grip_forged_factor217_runtime.glb`

SHA **634e7b8aff412e53edff7a6cc73932c3c99a7dd607b3436bcc2ef17edd8a8fa5**，4,332,248字节。

唯一JSON变化：

```text
/materials/0/pbrMetallicRoughness/metallicFactor
有效默认1 -> 217/255 = 0.8509803921568627
```

只作用于`Steel | forged body`（mesh0/primitive0）。这给现有纯金属反射加入少量非金属贡献，检验当前灯／反射条件下宽面的可读性；不是声称metallic=1有错，也不是已经决定的最终材质。刃口仍全金属；颜色、粗糙度、暗脊、磨损、铜、绳、皮、法线、UV、锚点均不变。

**所有18张KTX、全部4,312,988个BIN字节、77个views和59个accessors逐字节相同。** 没有重编码器、没有间接G粗糙度量化变化。语义与几何验证严格只允许上述一个JSON pointer。

之前尝试把源MR B裁到217后按原UASTC配置重编码，发现小mip的G最多漂移9/255，无法称严格单变量。该路线已拒绝，四个生成候选文件已移除；只保留小的`rejected-reencode-budget.json`解释为何改为一个材质倍率。本目录只有一个推荐runtime GLB，没有扫多个金属度或粗糙度值。

## Root最小接入与判断

Root的私有A/B包只替换现有独立玩家刀`assets/models/dao_grip.glb`为上述候选，使用同一加载入口；不必新增Kotlin、灯或系统。保持c07灯值／皮肤／全局IBL／曝光及其余模型完全相同。私包资源identity应明确记录候选SHA，不能伪称仍为db28。

这是有意的glTF材质乘因子实验，不是意外重复调制。请勿在诊断重建时把该factor无意重置为1；完整预编码KTX都已保留，私包不需要再跑codec。Root仍独占正式producer／manifest／资源发布。

范围只限独立玩家刀；对手actor内置的蒙皮刀不自动改变，不能据此声称三角色武器都修复。先比较常用斜举与横持的宽面／亮刃／暗脊分层，避开短接触灯；近距手和脸不应因这个数据改变。若可读性改善，支持纯金属反射输入／方向在该姿态不足的假设，仍不唯一证明IBL布局正确或错误；若不变，停止加亮或再改其它参数，Root应补该包原生材质读回和实际视点／刀面几何再判断。

## 复现与检查

```sh
/usr/bin/python3 -B ArtSource/refinement/lookdev/native-nearfield/d0c7-dao/build_probe.py
/usr/bin/python3 -B -m unittest discover -s ArtSource/refinement/lookdev/native-nearfield/d0c7-dao -p 'test_*.py' -v
```

14项测试与两次无codec重建一致性通过；覆盖唯一变量、全部BIN/KTX不变，以及错误来源／材质／锚点／采样器／其它参数篡改拒绝。`probe_recipe.json`、`tests.json`记录配方、输入与输出身份。原生视觉效果仍未验证，不能以离线灯或数据测试代替APK收益。
