# cod_simulation

基于 ROS 2 和 Gazebo Sim 的 RoboMaster 哨兵仿真工作区，集成了
`rmu_gazebo_simulator`、RMOSS 机器人控制/模型组件以及 `cod2027_sentry`
机器人描述，主要用于 RM2027 哨兵底盘、传感器、定位建图和导航算法的调试。

> 当前代码按 **ROS 2 Jazzy + Gazebo Sim 8** 配置，已在 Ubuntu 24.04
> 环境验证。机器人控制和传感器话题采用**单机器人、无机器人名前缀**的约定。

## 当前默认配置

启动 `bringup_sim.launch.py` 时，程序会读取
[gz_world.yaml](rmu_gazebo_simulator/rmu_gazebo_simulator/config/gz_world.yaml)
并执行以下配置：

| 项目 | 当前值 |
| --- | --- |
| 默认世界 | `rmul_2027` |
| 默认机器人描述 | `cod2027_sentry/resource/xmacro/cod27_sentry.sdf.xmacro` |
| Gazebo 机器人名 | `robot` |
| 阵营/颜色 | `red` |
| 出生点 | `(-4.53172579, 2.50133224, 0.15)` |
| 初始朝向 | `yaw = pi / 2` |
| 底盘控制 | `PointMassControl`，水平速度和偏航角速度直接控制，竖直方向使用物理仿真 |
| 初始底盘跟随 | `follow_yaw: false`，收到 `FOLLOW_GIMBAL` 指令后才进入跟随模式 |

`bringup_sim.launch.py` 会同时启动 Gazebo、机器人模型、机器人控制节点、
`robot_state_publisher`、Gazebo/ROS 话题桥、传感器坐标系规范化节点、
`/Odometry -> TF` 转换节点和 1v1 裁判系统。**不会自动启动 RViz2**。

默认的 `cod27_sentry` 模型包含工业相机和 Livox MID360，不包含可运动的云台、
射击机构或 2D 雷达。需要这些部件时，可通过 `robot_xmacro` 参数切换到其他
机器人描述。

## 功能

- `rmul_2024`、`rmuc_2024`、`rmul_2025`、`rmuc_2025`、`rmul_2026`、
  `rmuc_2026`、`rmul_2027`、`rmuc_2027` 世界模型。
- 工业相机、Livox MID360 点云/IMU 及可选 RPLIDAR A2 数据接入。
- 底盘速度、云台角度和射击接口。
- URDF/TF、Gazebo 传感器 frame_id 和导航里程计之间的坐标树适配。
- 1v1 简化裁判系统，以及保留在源码中的网页控制工具。
- 无需启动仿真的地图网格到 PCD 点云转换工具。

## 工作区结构

```text
cod_simulation/
├── cod2027_sentry/              # 哨兵 XMacro 模型、RViz 和机器人描述 launch
├── rmoss_interfaces/            # ChassisCmd、GimbalCmd、ShootCmd 等接口
├── rmoss_core/                  # RMOSS 基础库和通用算法
├── rmoss_gazebo/                # Gazebo 控制器、桥接、相机和插件
├── rmoss_gz_resources/          # RoboMaster 公共模型资源
├── rmu_gazebo_simulator/        # 仿真主包、世界模型、launch 和辅助脚本
├── sdformat_tools/              # SDF 宏展开和 SDF -> URDF 工具
├── rmul2026.pgm                 # 仓库附带的 RMUL 2026 2D 栅格地图
└── rmul2026.yaml                # 上述栅格地图的元数据
```

## 环境依赖

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Sim 8
- `colcon`、`rosdep`、`vcstool`
- Python 3、`numpy`
- Python 包 `xmacro`
- 可选：`open3d`，用于 PCD 转换的泊松盘采样

安装 Python 依赖：

```bash
python3 -m pip install --user xmacro numpy
```

地图转 PCD 时可再安装：

```bash
python3 -m pip install --user open3d
```

## 构建

在包含源码的工作空间根目录执行。当前目录布局下，外层工作区是
`cod_sim`，源码位于 `cod_simulation`：

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths cod_simulation --ignore-src -r -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

本工作区已经包含 `rmoss_core`、`rmoss_gazebo`、`rmoss_gz_resources`、
`cod2027_sentry` 等源码，不依赖 `vcs import` 才能编译。若将这些包拆分到其他
工作区，可参考 [dependencies.repos](rmu_gazebo_simulator/dependencies.repos)
和 [cod2027_sentry/dependencies.repos](cod2027_sentry/dependencies.repos)。

## 启动仿真

```bash
source install/setup.bash
ros2 launch rmu_gazebo_simulator bringup_sim.launch.py
```

仿真启动后会直接进入运行状态。需要查看话题时：

```bash
ros2 topic list
ros2 topic echo /livox/lidar --once
ros2 topic echo /front_industrial_camera/image --once
```

单独启动 RViz2：

```bash
ros2 launch rmu_gazebo_simulator rviz.launch.py
```

RViz 配置的 Fixed Frame 是 `odom`，并显示 RobotModel、TF、点云、2D 雷达和
工业相机。当前仿真不桥接 Gazebo 真值里程计，必须由导航程序发布
`/Odometry`，通过 `odom_to_tf` 建立 `odom -> baselink` 后才能完整显示
机器人及传感器 TF。

只查看机器人模型、不启动 Gazebo 时：

```bash
ros2 launch cod2027_sentry robot_description_launch.py
```

## 切换世界和机器人

### 切换世界

编辑
[gz_world.yaml](rmu_gazebo_simulator/rmu_gazebo_simulator/config/gz_world.yaml)
中的 `world` 字段，然后重新启动仿真。当前可选：

```text
rmul_2024  rmuc_2024  rmul_2025  rmuc_2025
rmul_2026  rmuc_2026  rmul_2027  rmuc_2027
```

机器人名、颜色和出生点也由同一文件中的 `robots.<world>` 配置决定。

### 切换机器人描述

`bringup_sim.launch.py` 默认使用 `cod27_sentry`，可以通过 `robot_xmacro`
传入其他 XMacro 文件的绝对路径。例如：

```bash
ros2 launch rmu_gazebo_simulator bringup_sim.launch.py \
  robot_xmacro:=$(ros2 pkg prefix cod2027_sentry)/share/cod2027_sentry/resource/xmacro/simple_chassis_robot.sdf.xmacro
```

`simple_chassis_robot` 包含 RPLIDAR A2 和 MID360，适合测试 2D/3D 雷达和底盘
运动；它同样使用 `PointMassControl`。`cod27_sentry` 是当前默认的完整外观模型。

## ROS 接口

默认机器人节点的名称为 `/robot_base`。当前为单机器人调试模式，以下话题均不带
机器人名前缀。

| 名称 | 类型 | 方向/说明 |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 输入，直接控制底盘速度 |
| `/robot_base/chassis_cmd` | `rmoss_interfaces/msg/ChassisCmd` | 输入，底盘速度或跟随云台模式 |
| `/robot_base/gimbal_cmd` | `rmoss_interfaces/msg/GimbalCmd` | 输入，云台绝对/相对角度 |
| `/robot_base/gimbal_state` | `rmoss_interfaces/msg/Gimbal` | 输出，云台角度 |
| `/robot_base/shoot_cmd` | `rmoss_interfaces/msg/ShootCmd` | 输入，发射数量和速度 |
| `/joint_states` | `sensor_msgs/msg/JointState` | 输出，Gazebo 关节状态 |
| `/front_industrial_camera/image` | `sensor_msgs/msg/Image` | 输出，工业相机图像 |
| `/front_industrial_camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 输出，相机内参 |
| `/livox/lidar` | `sensor_msgs/msg/PointCloud2` | 输出，MID360 点云，frame=`mid360` |
| `/livox/imu` | `sensor_msgs/msg/Imu` | 输出，MID360 IMU，frame=`mid360` |
| `/rplidar_a2/scan` | `sensor_msgs/msg/LaserScan` | 输出，仅机器人模型包含 RPLIDAR A2 时有效 |
| `/Odometry` | `nav_msgs/msg/Odometry` | 输入，供 `odom_to_tf` 发布导航 TF |
| `/tf`、`/tf_static` | `tf2_msgs/msg/TFMessage` | 输出，机器人关节和传感器坐标变换 |
| `/clock` | `rosgraph_msgs/msg/Clock` | 输出，Gazebo 仿真时间 |
| `/referee_system/<robot_name>/robot_status` | `rmoss_interfaces/msg/RobotStatus` | 输出，仅机器人名与裁判系统配置一致时有效 |

Gazebo 原始传感器先桥接为 `/livox/lidar_raw`、`/livox/imu_raw` 和
`/rplidar_a2/scan_raw`，再由 `normalize_mid360_frames.py` 统一改写 frame_id
并发布到上表中的最终话题。

当前 1v1 裁判节点使用 `red_standard_robot1` 和 `blue_standard_robot1` 两组
机器人名，而默认世界生成的是 `robot`。因此默认配置可以正常使用底盘和传感器，
但不会把裁判状态发送到 `/referee_system/robot/robot_status`。若需要裁判联动，
应同步修改 `gz_world.yaml` 中的机器人名和
`simple_competition_1v1.py` 中的机器人列表。

### 键盘控制底盘

```bash
ros2 run rmoss_gz_base test_chassis_cmd.py --ros-args \
  --remap chassis_cmd:=/robot_base/chassis_cmd \
  -p v:=0.3 -p w:=0.3
```

也可以用 ROS 命令行直接发送速度：

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.3}}"
```

默认的 `cod27_sentry` 云台关节是固定关节，也没有射击机构，因此针对默认模型
发送 `gimbal_cmd` 或 `shoot_cmd` 不会产生可见动作。切换为包含对应机构的机器人
描述后，可用 `test_gimbal_cmd.py` 和 `test_shoot_cmd.py` 测试，并使用以下话题
重映射：

```bash
ros2 run rmoss_gz_base test_gimbal_cmd.py --ros-args \
  --remap gimbal_cmd:=/robot_base/gimbal_cmd

ros2 run rmoss_gz_base test_shoot_cmd.py --ros-args \
  --remap shoot_cmd:=/robot_base/shoot_cmd
```

## 定位、TF 和导航约定

默认机器人模型不发布 Gazebo 真值里程计。导航系统需要发布 `/Odometry`，
`odom_to_tf.py` 将其转换成 `odom -> baselink`：

- 默认 `child_frame_id` 为 `baselink`。
- `zero_on_start=true`，收到第一帧里程计后把该帧位置作为 `odom` 原点；朝向保留
  世界姿态。
- 输入 frame_id 和 child_frame_id 中的 `/` 前缀会被去掉。
- `robot_state_publisher` 根据 XMacro 生成的 URDF 发布 `baselink` 到各传感器和
  云台坐标系的变换。

对应关系如下：

```text
Gazebo -> ros_gz_bridge -> *_raw -> normalize_mid360_frames -> /livox/*, /rplidar_a2/scan
导航定位 -> /Odometry -> odom_to_tf -> odom -> baselink
robot_state_publisher -> baselink -> mid360 / front_industrial_camera / ...
```

当前 launch 根据机器人名替换 Gazebo 侧话题，但 ROS 侧统一使用
`/robot_base/chassis_cmd` 和全局 TF 名称。因此当前配置只适合单机器人；
同时启动两台机器人会在 `odom -> baselink` 上发生 TF 冲突。

## 地图转 PCD 点云

`mesh_to_pcd.py` 可以不启动 Gazebo，直接把世界模型中的 mesh 和基本几何体采样
成 PCD：

```bash
# 使用 gz_world.yaml 当前选中的世界
ros2 run rmu_gazebo_simulator mesh_to_pcd.py

# 指定世界并输出预览图
ros2 run rmu_gazebo_simulator mesh_to_pcd.py --world rmul_2027 --preview

# 裁掉地面，按 0.02 m 体素降采样，并对齐机器人出生点
ros2 run rmu_gazebo_simulator mesh_to_pcd.py \
  --world rmul_2027 \
  --z-min 0.1 --voxel 0.02 --align-to-spawn \
  --out ~/maps/rmul_2027.pcd --preview
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--world` | 世界名（如 `rmul_2027`）或 world SDF 路径；默认读取 `gz_world.yaml` |
| `--out` | 输出路径，默认 `resource/maps/<world>.pcd` |
| `--density` | 每平方米采样点数，默认 1000 |
| `--points` | 直接指定总点数，并覆盖 `--density` |
| `--voxel` | 体素降采样尺寸，默认 0.02 m；设为 0 可关闭 |
| `--z-min` / `--z-max` | 按高度裁剪点云，裁掉地面常用 `--z-min 0.1` |
| `--align-to-spawn` | 将原点平移到当前世界第一台机器人的出生点 |
| `--offset X Y Z` | 手动平移输出点云 |
| `--sampler` | `numpy`（默认）、`open3d` 或 `poisson` |
| `--preview` | 额外输出俯视密度预览 PNG |
| `--ascii` | 输出 ASCII 格式 PCD，默认二进制 |

脚本只支持 `stl`/`obj` mesh 以及 `box`、`cylinder`、`sphere`、`plane`，
遇到 `.dae` 会跳过。采样得到的是完整模型表面，用于重定位或栅格转换前通常需要
使用 `--z-min` 去除地面。

## 可选工具

仓库根目录的 `rmul2026.pgm` 和 `rmul2026.yaml` 是一组已经生成的 RMUL 2026
2D 栅格地图，当前 launch 不会自动加载它们。

`rmu_gazebo_simulator/.../scripts/player_web` 和 `referee_web` 中保留了网页
操作手及裁判端源码。它们未通过 `colcon` 安装，并且仍采用旧的多机器人话题命名
约定，不能直接匹配当前的单机器人 bringup，使用前需要同步修改话题。

## 常见问题

**RViz 中没有机器人或传感器**

确认已经 `source install/setup.bash`，并检查是否有节点发布 `/Odometry`。
没有 `/Odometry` 时不会生成 `odom -> baselink`，Fixed Frame 为 `odom` 的 RViz
无法显示完整 TF 树。

**`/rplidar_a2/scan` 一直没有数据**

默认 `cod27_sentry` 没有 2D 雷达。切换到
`simple_chassis_robot.sdf.xmacro`，或使用包含 RPLIDAR A2 的机器人描述。

**底盘收到指令但不运动**

确认 `/cmd_vel` 或 `/robot_base/chassis_cmd` 有发布者；检查
[base_params.yaml](rmu_gazebo_simulator/rmu_gazebo_simulator/config/base_params.yaml)
中的底盘模式和 PID 参数，并确认当前模型使用的是 `PointMassControl`。

**如何查看 launch 参数**

```bash
ros2 launch rmu_gazebo_simulator bringup_sim.launch.py --show-args
```

## 许可证

各子包沿用其目录中的许可证，例如 `rmu_gazebo_simulator` 为 Apache-2.0，
`cod2027_sentry` 为 MIT。模型、贴图和第三方资源的版权归对应作者所有。
