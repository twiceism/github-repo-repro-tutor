# 完整示例：RCS 小波-自编码器仓库（2026-09）

这个技能就是从这次辅导中提炼出来的。遇到类似的"个人科研仓库 + 本科生复现"场景时，可以参考这里的决策过程。

## 输入

- 仓库：https://github.com/huatanshaonian/rcs-wavelet-neural-network （飞行器 RCS 代理模型：9 个几何参数 → 91×91×2 的 RCS 方向图）
- 学生：985 电子信息专业大二，Windows + conda + PyTorch，有 NVIDIA GPU
- 偏好（阶段 2 确认）：脚本为主、GUI 为辅；理论"只要会用"

## 阶段 1 的发现（体现"相信代码，不全信文档"）

| 发现 | 怎么发现的 |
|---|---|
| 原始 FEKO 数据不在仓库（只有 `feko_data.lnk` → `G:\feko_data`），但 `cache/` 里有 8 个 pkl 可直接用 | 打开 .lnk 字符串，pickle.load 缓存检查 shape |
| 缓存文件名是原始 CSV 的哈希签名，没有 CSV 时 GUI 找不到缓存 | 读 `data_cache.py` 的 `_get_data_signature` |
| README 写 `pip install pywt`，实际包名是 PyWavelets；漏写 `ptwt`，不装的话任何模型都 import 失败 | 在干净环境里 import 一次 |
| `main.py` 导入不存在的 `wavelet_network`、`training` | repo_scan + 实际运行 |
| `standalone_trainer` 的 `MinimalGUI` 缺 3 个属性，第 1 个 epoch 就崩 | grep `self.gui.` 的所有访问，对照假 GUI 的属性 |
| 模板 json 对 wavelet 模式开了 dB 变换，会把 37% 的负小波系数截断成 1e-10 | 读 `RCS_DataAdapter.adapt_rcs_data` + 实测负系数比例 |
| README 参数量与实测不符（10.0M vs 1.2M） | 实际构建模型后数参数 |

## 阶段 3 的实测（云端 2 核 CPU；用户本机的 Cowork VM 没有 torch）

- 本地副本与 GitHub 的 107 个 .py 文件做 md5 比对，完全一致 → 在云端 `git clone` 后测试
- 容器没有 tkinter → 用 stubs/tkinter 放进 PYTHONPATH
- 脚本：`common / step0_env_check / step2_explore / step3_wavelet / step4_model / step5_train / step6_eval / export_cache_to_csv`
- 关键结果（38 个验证样本，最近邻基线 7.53 dB）：
  - direct + cnn + 256 → 参数→RCS RMSE **4.40 dB**（打败基线）
  - wavelet + cnn + 256（README 推荐的模式）→ 15.33 dB，并且有 9% 的负值
  - wavelet + dual_branch + 32 → 8.41 dB
- 结论：在这份数据上，README 推荐的模式反而更差（原因：在线性域做小波，Z-score 之后峰值变成 ±40 的离群值，主导了 MSE）。这一点被写进指导书，作为"如何对待文档声明"的教学案例。
- 预测图能学到镜面反射亮带，但学不到高频干涉条纹 → 在指导书中引出"频谱偏置"。

## 值得复用的做法

1. **评估脚本里带一个最近邻基线**：一行 numpy 就能写，但能立刻判断模型是否真的学到了东西。
2. **dB 指标设下限截断**（1e-8），并在报告里写明这个评估约定，否则负值会把误差放大得离谱。
3. **导出脚本用作者自己的读取函数验证逐位还原**（误差为 0），再交给 GUI 使用。
4. **HeadlessGUI 用 SimpleNamespace 补属性**：不改源码，同时顺便给学生讲了鸭子类型。
5. 每个配置先跑 `--quick`（每阶段 3 个 epoch），确认整条链路通了再正式训练。
6. 交付时如果和用户电脑的连接断开：先在会话里给附件（zip），重连后再写入文件夹，并在转接报告里更新文件位置。

## 当时交付物的规模参考

- 01 规划：约 110 行
- 02 指导书：约 1040 行（10 个阶段 + 两个附录 + 7 道思考题）
- 转接报告：约 105 行
- repro 脚本：8 个文件，合计约 600 行
