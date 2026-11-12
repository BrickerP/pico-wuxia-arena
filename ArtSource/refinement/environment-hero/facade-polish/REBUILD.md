# 正立面成套精修候选

唯一输出为本目录完整`courtyard_facade_polish.glb`；不修改正式app或上游9b/2fb输入。

```bash
python3 ArtSource/refinement/environment-hero/facade-polish/build_facade.py
python3 ArtSource/refinement/environment-hero/facade-polish/verify_facade.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/facade-polish/courtyard_facade_polish.glb ArtSource/refinement/environment-hero/facade-polish/review/gltf-validator.json
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/facade-polish/render_facade.py
python3 ArtSource/refinement/environment-hero/facade-polish/make_boards.py
```

地层共享9b内已审窗核心的原始accessor/索引，四个节点都使用同一个mesh。上层从2fb命名分件改变长度：保留框截面、窗棂厚度、止口与半搭接带宽，调整宽/矮跨度，重新计算米制UV；五个节点共享同一个上层mesh，均无非等比node scale。只在新几何最终float32数据上清理退化面，再补切线。

共享墙逐三角形裁掉八个owned区，精确保留外侧；新墙片合为一个mesh，材质仍用25。门洞/门五金、柱梁、地面receiver、灯位和战斗净空保留。原9b第一窗的墙与窗核心仅拆分引用，不改变其几何。

檐口只移除前封边190三角；保留瓦面/木椽/其它屋顶。新增59个薄壁半圆瓦口、58个居间滴水，整排合为一个mesh/primitive，全部复用屋瓦PBR材质5。接触高度逐顶点采样冻结瓦面。早期“圆钮串”方案已废弃，不在最终候选中；不加纹样雕饰或图片。

全部32个材质、50张图片及texture表与9b完全相同。预算把节点展开三角与唯一mesh三角分开；唯一VB按活跃mesh引用的不同属性bufferView字节并集计，POSITION数量按不同accessor计，不是焊接点数或VRAM实测。primitive×node提交数是假定逐primitive提交的保守估算，不代表硬件实例化、单draw或实际SDK绘制次数。瓦口批次避免了59独立节点。

仅渲染两个视角，前后同灯、同机位、无景深。人物用当前ac7d正式KTX对应b3fb PNG源，idle@0锁定姿态；不是旧722/b732。PNG对应源用于Blender，源/正式双SHA写入收据。站立眼高1.6m是离线审图基准，不冒称实测HMD pose或原生流明等价。

Root按显式SHA选择后替换唯一courtyard资源，不能叠加到9b上。格式0错误、4条继承的运行时切线生成警告仍是原生检查项；Space Pro内存、帧率和舒适性尚未实测，不宣称预算通过。
