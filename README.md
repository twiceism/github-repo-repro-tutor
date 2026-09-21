# github-repo-repro-tutor

> 让 Claude 以"资深讲师"的身份带你复现任意 GitHub 仓库，最后交付 **四份 Markdown 文档 + 一套实测跑通的 repro 脚本**。

## 它会做什么

| 阶段 | Claude 做的事 | 交付物 |
|---|---|---|
| 1 深读 | 读完整个 README、文档和关键源码，用脚本扫描依赖与缺失文件，整理出"文档说的 vs 代码实际的"对照表 | — |
| 2 规划 | 写出复现规划，**停下来**用选择题跟你确认 GPU、路线、理论深度 | `01_复现规划.md` |
| 3 探路 | 在 `仓库根目录/my_repro/` 写好分阶段脚本，并亲自跑通（冒烟测试 + 正式训练 + 评估） | `my_repro/*.py` |
| 4 教材 | 编写分阶段指导书：原理 + 例子 + 命令 + 实测输出 + 坑点 + 验收 + 思考题 + 资源/论文 DOI | `02_复现指导书.md` |
| 5 证据 | 记录测试环境、每条命令的结果、数值、发现的问题、未验证项 | `03_测试验证报告.md` |
| 6 交接 | 写给下一次会话的"交接班记录"，并存进 Project | `04_任务转接报告.md` |

## 安装

**方式一：Claude 桌面版 / claude.ai**
把整个 `github-repo-repro-tutor` 文件夹打包成 zip（zip 里的第一层就是这个文件夹），然后在 Claude 设置中的 Skills（技能）页面上传；也可以直接点击会话里技能卡片上的“保存”按钮。

**方式二：Claude Code**
把文件夹复制到下面任一位置：
- 个人：`~/.claude/skills/github-repo-repro-tutor/`（Windows：`C:\Users\<你>\.claude\skills\github-repo-repro-tutor\`）
- 项目：`<项目>/.claude/skills/github-repo-repro-tutor/`

装好后，新会话里给出仓库链接并说"带我复现"即可自动触发，也可以直接点名："用 github-repo-repro-tutor 的流程……"

## 怎么提问

完整的提问模板在 [`references/prompt_template.md`](references/prompt_template.md)，最短的用法是：

```text
用 github-repo-repro-tutor 的流程带我复现 https://github.com/xxx/yyy ，
本地代码在 C:\Users\me\Desktop\proj\yyy-master，我是电子信息大二，有 NVIDIA GPU。
```

续做上次没完成的任务：

```text
继续上次的复现任务，转接报告在 C:\Users\me\Desktop\proj\04_任务转接报告.md，我做到了阶段 5，输出如下：……
```

**建议**：在 Cowork 里把项目文件夹连接给 Claude（Add folder），并把会话挂到一个 Project 上，这样文件会直接写进你的文件夹，转接报告也会存进 Project。

## 文件夹结构

```
github-repo-repro-tutor/
├── SKILL.md                         # 给 Claude 的主流程说明（触发条件 + 六个阶段）
├── README.md                        # 本文件（给人看）
├── references/
│   ├── prompt_template.md           # 润色后的提问模板 + 每条要求背后的意图
│   ├── repo_audit_checklist.md      # 深读仓库检查清单 + 跨项目通用的坑
│   ├── guide_writing_style.md       # 指导书写作规范（六段式、深度分级、结果表写法）
│   ├── resources_and_citations.md   # 附录资源的收集方法 + DOI 核验规则
│   └── case_study_rcs.md            # 完整示例：RCS 小波自编码器仓库
├── assets/templates/
│   ├── 01_plan_template.md          # 复现规划骨架
│   ├── 02_guide_template.md         # 复现指导书骨架
│   ├── 03_test_report_template.md   # 测试验证报告骨架
│   └── 04_handoff_template.md       # 任务转接报告骨架
└── scripts/
    ├── repo_scan.py                 # 仓库体检：数据文件、入口、import/依赖、README 引用了但不存在的文件、包名陷阱
    ├── run_and_log.py               # 批量运行命令 → 完整日志 + env.md + summary.md（直接用于 03）
    └── stubs/tkinter/               # tkinter 空桩：让依赖 GUI 的训练代码能在无显示器环境里 import（仅测试用）
```

## 脚本也可以单独使用

```bash
# 体检一个仓库
python scripts/repo_scan.py path/to/repo --check-installed --out repo_scan.md

# 批量跑命令并生成测试记录
python scripts/run_and_log.py --cwd path/to/repo --log-dir repro_logs \
    --cmd "python my_repro/step0_env_check.py" --cmd "python my_repro/step5_train.py --quick"
```

两个脚本都只依赖 Python 标准库，已在一个真实仓库（rcs-wavelet-neural-network）上测试过。

## 适用范围与限制

- 最适合 Python 科研/深度学习仓库（PyTorch/TensorFlow/JAX、信号处理、电磁、通信、CV 等）。
- 如果数据需要申请或下载量很大，Claude 会先说明情况，并提出替代方案（缓存、公开子集、合成数据）。
- 云端测试环境通常没有 GPU，Claude 会用较少的 epoch 实测，并在 03 中标注与你本机环境的差异。
- GUI 类操作一般无法在测试环境里实际点击，指导书中会明确标注"依据源码整理，未实测"。
