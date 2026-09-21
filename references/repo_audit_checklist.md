# 仓库深读检查清单（阶段 1）

目标：交付 01 规划之前，你应该能填满下面每一项。能用代码验证的，就用代码验证。

## A. 文档层

- [ ] README **全文**读完（包括更新日志、FAQ、性能表）
- [ ] 其他说明文档：`CLAUDE.md`、`AGENTS.md`、`docs/`、`CONTRIBUTING.md`、`PARAMETERS*.md`、`DESIGN*.md`
- [ ] 依赖声明：`requirements*.txt`、`environment.yml`、`setup.py`、`pyproject.toml`（注意 Python/torch 版本要求）
- [ ] 配置模板：`configs/`、`experiments/*.json|yaml`
- [ ] 论文/引用：README 里有没有 paper 链接、BibTeX（附录要用）
- [ ] Issues（能联网时）：别人踩过的坑往往就在里面

## B. 结构与入口

- [ ] 运行 `scripts/repo_scan.py <repo> --check-installed`，并复核它的每一条提示
- [ ] README 里的启动命令逐条核对：文件存在吗？import 能通吗？（`python -c "import xxx"`）
- [ ] 找到"真正在用"的训练/评估函数。README 推荐的入口可能已经坏了，真正可用的逻辑可能藏在 GUI 管理器、trainer 类或 notebook 里
- [ ] 无 GUI 的调用路径：有没有 standalone/CLI 函数？它依赖的"假 GUI"对象属性齐不齐（逐个 grep `self.gui.`）
- [ ] 配置必填键：训练器里 `config['xxx']`（不是 `.get`）的都是必填，缺了就 KeyError

## C. 数据

- [ ] 原始数据在哪？是否在仓库里？`.lnk`、绝对路径（`G:\`、`/home/author/`）说明数据在作者本机
- [ ] 有没有缓存/中间产物（`cache/*.pkl`、`*.npz`、`*.h5`）可以替代？打开看 key、shape、dtype、min/max、元信息
- [ ] 缓存的命名/签名机制：比如文件名是原始文件的哈希，没有原始文件 GUI 就找不到缓存
- [ ] 数据规模是否足够（样本数、类别数）？和 README 声称的规模一致吗？
- [ ] 物理/任务含义：每一维代表什么？单位？坐标网格？（去画图代码里找 extent / axis label）
- [ ] 如果需要，能否写导出脚本把缓存还原成原始格式（用作者自己的读取函数验证能逐位还原）

## D. 关键代码路径（最容易出坑的地方）

- [ ] **预处理顺序**：变换（FFT/小波/对数）与标准化谁先谁后；有没有对负值取 log 这类会被 clip 静默吞掉的错误
- [ ] **逆变换**：评估和可视化时，是否正确地从模型输出空间回到物理空间
- [ ] **数据划分**：随机种子、比例、各阶段是否用同一份划分；评估脚本要复刻同一份划分
- [ ] **train/eval 模式**：Dropout/BatchNorm；推理时有没有 `model.eval()`
- [ ] **保存/加载**：checkpoint 里存了什么（权重、标准化统计量、配置）；加载时能否重建出完全相同的模型
- [ ] **损失计算**：在哪个空间算；batch 平均还是按样本加权；多通道时是否被某个通道主导
- [ ] **参数量**：实际构建一次模型数参数，和 README 对比
- [ ] **硬编码**：频率数、输入尺寸、路径、设备（`cuda` 写死？）

## E. 产出：差异表（写进 01 和 02）

| README / 文档里说 | 实际情况（怎么验证的） | 影响 | 处理办法 |
|---|---|---|---|
| 例：`pip install pywt` | PyPI 上包名是 PyWavelets | 装不上 | 改用正确包名 |
| 例：`python main.py` | 导入不存在的模块 | 入口不可用 | 改走 xxx 函数 |
| 例：参数量 1.2M | 实测 10.0M（latent=256） | 过拟合风险评估不同 | 以实测为准 |

## F. 常见坑速查（跨项目通用）

| 现象 | 常见原因 |
|---|---|
| README 命令报 ModuleNotFoundError | 依赖漏写；包名与 import 名不同；模块文件没上传 |
| `pip install` 之后 GPU 不可用 | 某个依赖 torch 的包把 GPU 版 torch 升级成了 CPU 版 |
| 训练 loss 一直 ≈ 1（标准化空间） | 预处理错误、学习率不当、输入被 clip 毁掉 |
| 评估数值离谱（负数、量级不对） | 忘了逆标准化 / 逆变换 |
| 每次推理结果不同 | 没有 `model.eval()` |
| 无显示器环境 import 失败 | 训练代码顶部 import 了 tkinter/Qt → 用 `scripts/stubs/` |
| Windows 控制台 `UnicodeEncodeError: 'gbk'` | 日志里有 emoji → `set PYTHONIOENCODING=utf-8` |
| matplotlib 中文显示为方块 | 缺中文字体 → rcParams 设置 Microsoft YaHei / SimHei |
