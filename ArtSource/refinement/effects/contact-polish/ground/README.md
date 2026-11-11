# 庭院闪避与落地低尘候选

**素材制作阶段结束，交Root统一接入与验收。** 本模块只向调用者传入的候选目录发布。`build_ground.build(output_dir)` 由上层 `build_contact_polish.py` 唯一制作入口调用，无独立制作main。

## 实物

| 资源 | mesh节点 | 三角数 | 几何高度 | 粒子寿命 |
| --- | ---: | ---: | --- | --- |
| dodge_ground_polish.glb | 8 | 192 | 2–2.8厘米 | 260–380毫秒 |
| landing_ground_polish.glb | 8 | 192 | 2–2.8厘米 | 300–420毫秒 |

两份资源均无动画、骨骼、贴图或扩展，每个 `dust_00` 至 `dust_07` 都是独立mesh。每个mesh由两张垂直alpha扇面组成，原点在体积底部，全部局部Z非负。普通低亮灰暖PBR、roughness为1、metallic为0、材质alpha为0.28，顶点边缘与运行透明度再衰减。没有白爆核心或大烟环，`waves=[]`。

闪避粒子沿真实地面位移的负切向拖尾，初始T位移−4至−11.7厘米；落地粒子低速径向散开。参考采样得到最大活跃水平包围盒对角线约22.2厘米和32.9厘米。数值基于已交GLB和运动合同，实际可辨性及遮挡由Root端内验证。

## 底面与运动

`dodge_motion.json` 和 `landing_motion.json` 均使用现有particles／opacity_keys合同。坐标基为T实际切向、B为N叉乘T、N真实地面法线。锚点由Root沿N外移2毫米，particle初始局部Z为0。Stage重力保持 `(0,−9.81,0)`，先算实际Stage轨迹，再沿真实N将粒子base限制到锚平面之上。

体积姿态固定于TBN，可只绕N旋转。按三维速度倾倒会失去底部Z非负保证，当前合同保持固定姿态。接地面不依赖Stage Y等于0，参考测试也覆盖位于非零高度的倾斜平面。

## 触发语义

闪避由Root确认的成功闪避与真实近地位移触发，落地由实际脚／身体和当前地面接触触发。点、法线、材质和切向由Root提供。UI提示和固定DEAD秒数不是本候选的触发来源。尘层面向现有庭院石路的少量松散泥尘，场景湿润程度与具体材质选择由Root判断。

## 检查

`verify_ground.py` 读取实际GLB并调用Root的 `sample_ground_particle`。它核对独立节点、局部Z、几何高度、索引／单位法线、寿命与opacity，以及三种地面法线下的base-clamp。两个正常／边界用例实际通过，包括倾斜平面、切向缺失和粒子过期。最低平面距离约−1.9e−16米，为双精度计算误差。

本目录 `metrics.json` 记录发布字节数与SHA，`verification.json` 记录实际采样结果。未进行SDK、设备或整局验证。统一离线渲染在Root指定的render_ground.py／review路径，由独立呈现任务负责。
