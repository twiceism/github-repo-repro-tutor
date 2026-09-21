# 资源与文献附录的收集与核验

指导书附录 B 分四块：**B.1 工具**、**B.2 学习资源**、**B.3 GitHub 仓库**、**B.4 论文与 DOI**。

## 从哪里找

1. **仓库自身**：README 的引用/致谢、`requirements.txt` 里的每个核心库、代码注释里提到的论文或算法名、`docs/` 里的参考文献。
2. **方法溯源**：项目用到的每个关键技术（例如自编码器、小波、注意力、某种激活函数、优化器），各找一篇奠基论文。
3. **领域综述**：该领域 × 深度学习的综述 1~2 篇，再加近几年的相关应用论文 2~4 篇（用 WebSearch 搜）。
4. **教材与课程**：中文友好的优先（如《动手学深度学习》zh.d2l.ai），再加领域经典教材。
5. **相关仓库**：核心依赖的源码仓库、同类方法的官方实现、可以用来扩展的库。

## DOI 核验规则（重要）

编造或记错的 DOI 会直接误导学生，所以：

- **只写你确认过的 DOI**。确认的方法（按可行性排序）：
  1. WebSearch 搜"论文标题 + doi"，在出版社页面、Semantic Scholar、PubMed、HAL 等处核对；
  2. 如果网络允许，访问 `https://api.crossref.org/works/<DOI>` 或 `https://doi.org/<DOI>`（部分环境会被代理拦截，不要反复重试）；
  3. 对于非常经典、你有把握的论文（如 Hinton & Salakhutdinov 2006 *Science*），可以直接写，但仍然要保证标题、期刊、年份准确。
- 没有 DOI 的（JMLR、NeurIPS、ICLR 等）：给官方页面或 arXiv 号，**不要硬造 DOI**。
- 只核实到页面、没核实到 DOI 的：给页面链接（如 IEEE Xplore 文档号），在表里写"链接"而不是"DOI"。
- 近期论文作者信息不确定时，只写标题 + 期刊 + 链接，不要猜作者。

## 表格格式

```markdown
| 主题 | 文献 | DOI / 链接 |
|---|---|---|
| 自编码器降维 | G. E. Hinton, R. R. Salakhutdinov, "Reducing the Dimensionality of Data with Neural Networks," *Science*, 313(5786): 504–507, 2006 | [10.1126/science.1127647](https://doi.org/10.1126/science.1127647) |
```

论文分两组列：**"方法的理论基础"** 和 **"领域 × 深度学习"**。每组 5~10 篇就够了，重在相关，不在数量。

## 常用、可靠的通用资源（按需选用）

| 类别 | 资源 |
|---|---|
| 深度学习入门（中文） | 《动手学深度学习》https://zh.d2l.ai/ ；源码 https://github.com/d2l-ai/d2l-zh |
| PyTorch | 官方教程 https://pytorch.org/tutorials/ ；GPU 版安装命令生成器 https://pytorch.org/get-started/locally/ |
| CNN | Stanford CS231n https://cs231n.github.io/ |
| 深度学习教材 | Goodfellow et al., *Deep Learning* https://www.deeplearningbook.org/ |
| 优化器 / 正则 | Adam arXiv:1412.6980；BatchNorm arXiv:1502.03167；Dropout https://jmlr.org/papers/v15/srivastava14a.html |
| 频谱偏置 | Rahaman et al., ICML 2019, arXiv:1806.08734 |
| 科学机器学习 | PINN: Raissi et al., *J. Comput. Phys.* 2019, DOI 10.1016/j.jcp.2018.10.045；DeepONet: Lu et al., *Nat. Mach. Intell.* 2021, DOI 10.1038/s42256-021-00302-5 |
| 小波 | PyWavelets 文档 https://pywavelets.readthedocs.io/ ；Mallat 1989 TPAMI DOI 10.1109/34.192463；Daubechies 1988 DOI 10.1002/cpa.3160410705 |

（这些条目在一次实际辅导中核对过；遇到新领域时，按上面的方法补充。）
