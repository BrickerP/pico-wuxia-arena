# Stage IBL 资源与公开接口核对

2026-11-10核对，项目BOM为6.1.9，本机官方资料线为6.1。本阶段没有加入运行IBL资源，配光与接地影可独立交付。

## 当前资源结论

当前仓库和已安装SDK6.1库存没有可直接接入的 `.ktx` 或 `.ktx2` 环境图。PATH没有 `cmgen`、`toktx`、`ktx`、`ktxinfo`，SDK、primer缓存、CLI vendor与已安装应用中也未找到可确认的官方IBL转换器或Spatial Editor。

可追溯的候选源图来自官方stage-editor模板。

- 路径为 `/Users/yupeng/Library/PICO/sdk/6.1/templates/spatial/stage-editor/editor-asset/src/main/res3d/SpatialPackContent/Sources/Assets/museum_day_ibl.exr`。
- 512×256，RGB 16-bit float，PIZ，409,956字节。
- SHA-256为 `e89a8a43fd875aaf69b5e03ee2fa8418ffc2956372b24a4eff05c9037c1566e6`。
- 同模板 `Sources/Scenes/Main.usda` 第59至75行把它设置为StageEnvironmentLightingComponent的Editor源纹理，当前源描述含 `textureShape=TEXTURE_2D` 与 `mipmapMode=DEFAULT`。
- 模板范围未找到独立资源许可文件，本阶段没有复制或重新分发该EXR。

官方Editor纹理配置说明，在IBL组件使用纹理时，应使用Cube形状与ENV_LIGHTING mipmap。现有EXR仍需要经过支持的IBL处理与运行格式检查。本阶段未将普通2D纹理或源EXR包装成运行IBL，也没有产生占位KTX。

## 公开API合同

公开类型均在 `com.pico.spatial.core.ecs`，纹理在 `com.pico.spatial.core.ecs.resource`。

- `StageEnvironmentLightingComponent(source: ImageBasedLightSource, intensityExponent: Float)` 及含 `rotation: Quat` 的重载。
- `ImageBasedLightSource.Single(resource: TextureResource)`。文档要求HDR environment texture，当前支持 `.ktx`，通常为cubemap。
- `intensityExponent` 范围−24至24，实际强度为2的该指数次方。官方示例8f对应乘256，需要结合正式环境图调音。
- StageStyle.Full提供完整自定义环境光，Mixed下自定义Stage环境光不生效，Progressive按沉浸程度与系统IBL混合。
- 局部IBL通过 `ImageBasedLightComponent` 加 `ImageBasedLightReceiverComponent` 绑定，环境与局部IBL的混合权重由 `EnvironmentLightingSettingsComponent` 控制，未添加时默认0.5。该权重本身无法证明当前系统环境图内容或实际端内亮度。

## 加载与生命周期

`TextureResource.load(path, LoadType.FROM_ASSETS)` 为公开同步加载入口，官方RoomLighting样例在Dispatchers.IO中加载，返回主线程后把Single源与Stage环境组件挂到场景Entity。资源提供close，Entity／组件操作为主线程操作。

官方样例采用组件挂载后TextureResource.use的模式，公开API文字没有说明内部引用保留机制。若采用显式SceneOwner所有权，应保存纹理句柄，初始化失效或取消时关闭未交付句柄，释放时先销毁环境Entity再close一次所持纹理，保留重入与取消的一致出口。无需额外toGlobal持久化。

当前HomeStage没有显式自定义Stage IBL，此阶段保留其既有环境贡献。默认IBL贡献是否足够，需要Root以实际端内画面对照。

## 依据与交叉检查

- 官方指南 `spatial-sdk_rendering_image-based-lighting.md`。
- 官方指南 `spatial-toolkit_pico-spatial-editor_textures_configure-texture-files.md` 第14至19行。
- 官方样例 `spatial-sdk_spatial-container_sample-welcome-to-pico-os-6!.md` 第310至329行。
- 公开API `com.pico.spatial.core.ecs.md` 第2803、2919、4673行。
- 公开API `com.pico.spatial.core.ecs.resource.md` 第2801至2873行。
- 从已安装 `core-6.1.9.aar` 提取classes.jar后，仅用javap -public核对上述已文档化构造、属性、TextureResource.load及close，签名存在。没有使用适配器内部成员或私有接口。

具体阻塞是当前缺少经过验证的IBL-ready KTX和可用的官方生成路径。后续有官方工具时，先完成源图许可、Cube／ENV_LIGHTING配置及运行KTX校验，再由Root接入最终场景与专项截图。

## 运行曝光与Editor预览的边界

本次检索范围为本机SDK6.1官方documentation和全部公开api-reference，检索exposure、tone mapping及tonemap。该范围内未找到可供现有Full Stage应用设置全局曝光或全局tone-mapper曲线的公开setter，此结论限定于已核对资料。

已找到的端内接口为 `UnlitMaterial.isApplyToneMapping()` 和 `setApplyToneMapping(Boolean)`，控制某个Unlit材质是否参加场景tone mapper，默认开启。它是材质参与开关，不能据此推出可调整全局曝光、曲线或阈值。该两方法已用core-6.1.9.aar的公有签名交叉核对。依据为 `com.pico.spatial.core.ecs.resource.md` 第2970至2984行及 `spatial-sdk_resource-management_material.md` 第44行。

`spatial-toolkit_pico-spatial-editor_scenes_manage-views.md` 第55至63行描述Environment Preview的Exposure，且明确该环境仅用于Spatial Editor预览。该设置不能作为现有应用全局曝光能力的证据。`StageEnvironmentLightingComponent.intensityExponent` 的2次幂规则属于IBL光源强度，维持其照明含义。
