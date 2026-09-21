#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo_scan.py —— 复现前的仓库"体检"（启发式，结果需人工复核）

用法:
    python repo_scan.py <仓库路径> [--out repo_scan.md] [--check-installed]

输出一份 Markdown，包含:
  1. 目录概览（文件类型统计、最大文件）
  2. 数据/模型/缓存文件（.pkl .npz .h5 .pth .csv .mat ... 以及 .lnk 快捷方式）
  3. 入口脚本（含 __main__ 或 argparse 的文件）
  4. import 分析：标准库 / 本地模块 / 第三方；requirements 是否覆盖；
     "看起来是本地模块但仓库里找不到"的导入（常见于 README 过时、文件未上传）
  5. README 中提到但不存在的文件/目录、`python xxx.py` 命令
  6. 包名陷阱（import 名 ≠ pip 名，如 pywt → PyWavelets）
只依赖 Python 标准库。
"""
import argparse
import ast
import importlib.util
import os
import re
import sys
from collections import Counter, defaultdict

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "node_modules", ".idea",
             ".vscode", ".mypy_cache", ".pytest_cache", "build", "dist", ".claude"}
DATA_EXT = {".pkl", ".pickle", ".npz", ".npy", ".h5", ".hdf5", ".mat", ".csv", ".pt",
            ".pth", ".ckpt", ".onnx", ".json", ".parquet", ".zip", ".tar", ".gz", ".lnk"}
# import 名 -> pip 包名（常见不一致）
PIP_NAME = {
    "pywt": "PyWavelets", "cv2": "opencv-python", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "PIL": "Pillow", "yaml": "PyYAML", "bs4": "beautifulsoup4",
    "Crypto": "pycryptodome", "dateutil": "python-dateutil", "serial": "pyserial",
    "usb": "pyusb", "OpenGL": "PyOpenGL", "wx": "wxPython", "attr": "attrs",
    "google.protobuf": "protobuf", "tensorflow_addons": "tensorflow-addons",
    "torch_geometric": "torch-geometric", "ptwt": "ptwt", "mpl_toolkits": "matplotlib",
    "tkinter": "(Python 自带；Linux 需 apt install python3-tk)",
}
GUI_MODULES = {"tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "kivy"}


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def human(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def stdlib_names():
    names = set(getattr(sys, "stdlib_module_names", ()))
    names.add("__future__")
    return names


def local_module_names(root):
    """返回 (strict, loose)：
    strict = 仓库顶层 .py / 顶层目录 / 任意深度 .py 文件名（兼容 sys.path.append 的写法）
    loose  = 任意深度的目录名（只有在代码改了 sys.path 时才可能被顶层 import）"""
    strict, loose = set(), set()
    for p in walk(root):
        if p.endswith(".py"):
            strict.add(os.path.splitext(os.path.basename(p))[0])
    for x in os.listdir(root):
        if os.path.isdir(os.path.join(root, x)) and x not in SKIP_DIRS:
            strict.add(x)
    for d, dirs, _ in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        loose.update(dirs)
    return strict, loose - strict


def parse_imports(path):
    src = open(path, encoding="utf-8", errors="ignore").read()
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return [], src
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.append(a.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.append(node.module)
    return mods, src


def read_requirements(root):
    req = set()
    for p in walk(root):
        b = os.path.basename(p).lower()
        if b.startswith("requirements") and b.endswith(".txt"):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.split("#")[0].strip()
                if line and not line.startswith("-"):
                    req.add(re.split(r"[<>=!~\[; ]", line)[0].strip().lower())
        elif b in ("setup.py", "pyproject.toml", "environment.yml", "environment.yaml"):
            txt = open(p, encoding="utf-8", errors="ignore").read()
            for m in re.findall(r"['\"\s-]([A-Za-z0-9_.\-]+)\s*(?:[<>=~!]=?[^'\"\n]*)?['\"\n]", txt):
                req.add(m.lower())
    return req


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default=None, help="输出 Markdown 路径（默认打印到终端）")
    ap.add_argument("--check-installed", action="store_true",
                    help="额外检查第三方包在当前 Python 环境是否已安装")
    args = ap.parse_args()
    root = os.path.abspath(args.repo)
    out = []
    P = out.append

    files = list(walk(root))
    rel = lambda p: os.path.relpath(p, root).replace("\\", "/")
    P(f"# 仓库扫描报告：`{os.path.basename(root)}`\n")
    P("> 由 repo_scan.py 自动生成，属启发式结果，**请人工复核**。\n")

    # 1. 概览
    ext = Counter(os.path.splitext(p)[1].lower() or "(无扩展名)" for p in files)
    P("## 1. 目录概览\n")
    P(f"- 文件总数：{len(files)}")
    P("- 类型分布：" + "，".join(f"`{e}`×{n}" for e, n in ext.most_common(12)))
    top = sorted(files, key=lambda p: os.path.getsize(p), reverse=True)[:8]
    P("- 最大的文件：")
    for p in top:
        P(f"  - `{rel(p)}` ({human(os.path.getsize(p))})")
    tops = sorted({rel(p).split("/")[0] for p in files if "/" in rel(p)})
    P("- 顶层目录：" + "、".join(f"`{t}/`" for t in tops))
    P("")

    # 2. 数据文件
    P("## 2. 数据 / 模型 / 缓存文件\n")
    data = [p for p in files if os.path.splitext(p)[1].lower() in DATA_EXT]
    if data:
        by_dir = defaultdict(list)
        for p in data:
            by_dir[os.path.dirname(rel(p)) or "."].append(p)
        for d, ps in sorted(by_dir.items()):
            tot = sum(os.path.getsize(p) for p in ps)
            exts = Counter(os.path.splitext(p)[1].lower() for p in ps)
            P(f"- `{d}/`：{len(ps)} 个（{', '.join(f'{e}×{n}' for e, n in exts.items())}），共 {human(tot)}")
        lnk = [p for p in data if p.lower().endswith(".lnk")]
        if lnk:
            P(f"- ⚠️ 发现 Windows 快捷方式 {[rel(p) for p in lnk]}：通常指向作者本机的数据目录，**数据本身不在仓库里**。")
    else:
        P("- 未发现常见数据文件。原始数据可能需要另外下载，去 README / Issues 里找链接。")
    P("")

    # 3/4. Python 分析
    py = [p for p in files if p.endswith(".py")]
    std = stdlib_names()
    local, local_loose = local_module_names(root)
    third = defaultdict(set)
    unresolved = defaultdict(set)
    path_hack = defaultdict(set)
    entry = []
    gui_users = defaultdict(set)
    for p in py:
        mods, src = parse_imports(p)
        if "__main__" in src or "argparse" in src:
            entry.append(p)
        for m in mods:
            top_name = m.split(".")[0]
            if top_name in GUI_MODULES:
                gui_users[top_name].add(rel(p))
            if top_name in std or top_name in local:
                continue
            if top_name in local_loose:                # 只有子目录同名：依赖 sys.path 改写才能 import
                path_hack[top_name].add(rel(p))
                continue
            if importlib.util.find_spec(top_name) is None and top_name not in PIP_NAME \
                    and top_name.islower() and "_" in top_name and len(top_name) > 12:
                unresolved[top_name].add(rel(p))       # 长名字 + 下划线 + 找不到：高度疑似缺失的本地模块
            else:
                third[top_name].add(rel(p))

    P("## 3. 入口脚本（含 `__main__` 或 argparse）\n")
    for p in sorted(entry, key=lambda x: (rel(x).count("/"), rel(x)))[:30]:
        P(f"- `{rel(p)}`")
    if len(entry) > 30:
        P(f"- …… 共 {len(entry)} 个")
    P("")

    P("## 4. import 分析\n")
    req = read_requirements(root)
    P(f"- requirements/setup 中声明的包（{len(req)}）：" + (", ".join(sorted(req)) or "（未找到）"))
    P("")
    P("| 第三方 import | pip 包名 | requirements 已声明 | 已安装 | 使用文件数 |")
    P("|---|---|---|---|---|")
    for m in sorted(third):
        pip_name = PIP_NAME.get(m, m)
        declared = "✅" if pip_name.lower() in req or m.lower() in req else "❌"
        inst = ""
        if args.check_installed:
            inst = "✅" if importlib.util.find_spec(m) is not None else "❌"
        P(f"| `{m}` | `{pip_name}` | {declared} | {inst or '—'} | {len(third[m])} |")
    P("")
    P("> ❌ 未声明的包：要么是 README/requirements 漏写（很常见），要么只在可选/实验代码里用到。"
      "用 `grep -rn \"import 包名\"` 看它被谁导入、是否在主路径上。")
    if unresolved:
        P("\n**⚠️ 疑似缺失的本地模块**（仓库中找不到对应文件，也不是已知的第三方包）：\n")
        for m, ps in sorted(unresolved.items()):
            P(f"- `{m}` ← {sorted(ps)[:5]}")
    if path_hack:
        P("\n**⚠️ 依赖 sys.path 改写的导入**（顶层 import 了一个只在子目录里存在的名字；"
          "要么代码里有 `sys.path.append`，要么这个导入本身就会失败——逐个确认）：\n")
        for m, ps in sorted(path_hack.items()):
            P(f"- `{m}` ← {sorted(ps)[:5]}")
    if gui_users:
        P("\n**GUI 依赖**（无显示器 / 容器环境下 import 会失败，可用桩模块）：")
        for m, ps in gui_users.items():
            P(f"- `{m}`：{len(ps)} 个文件，例如 {sorted(ps)[:3]}")
    mismatch = [m for m in third if m in PIP_NAME and PIP_NAME[m] != m]
    if mismatch:
        P("\n**包名陷阱**（import 名 ≠ pip 名）：" + "；".join(f"`import {m}` → `pip install {PIP_NAME[m]}`" for m in mismatch))
    P("")

    # 5. README 引用检查
    P("## 5. README 提到但仓库中不存在的东西\n")
    readmes = [p for p in files if os.path.basename(p).lower().startswith("readme")]
    all_rel = {rel(p) for p in files}
    all_dirs = {os.path.dirname(r) for r in all_rel}
    base_names = {os.path.basename(r) for r in all_rel}
    found_any = False
    for rp in readmes:
        txt = open(rp, encoding="utf-8", errors="ignore").read()
        cands = set(re.findall(r"`([\w./\\-]+\.(?:py|sh|bat|ipynb|json|yaml|yml|txt|md|csv))`", txt))
        cands |= set(re.findall(r"python\s+(?:-m\s+)?([\w./\\-]+\.py)", txt))
        cands |= set(re.findall(r"^[\s│├└─]*([\w\-]+\.py)\b", txt, flags=re.M))
        dirs = set(re.findall(r"^[\s│├└─]*([\w\-]+)/\s", txt, flags=re.M))
        missing = sorted(c for c in cands
                         if c.replace("\\", "/") not in all_rel and os.path.basename(c) not in base_names)
        missing_dirs = sorted(d for d in dirs if not any(x == d or x.startswith(d + "/") or ("/" + d) in "/" + x
                                                          for x in all_dirs))
        pips = re.findall(r"pip3? install ([^\n`]+)", txt)
        if missing or missing_dirs or pips:
            found_any = True
            P(f"**{rel(rp)}**")
            if missing:
                P("- 提到但不存在的文件：" + "、".join(f"`{m}`" for m in missing[:25]))
            if missing_dirs:
                P("- 目录树里有但不存在的目录：" + "、".join(f"`{d}/`" for d in missing_dirs[:25]))
            for line in pips:
                bad = [w for w in line.split() if w in PIP_NAME and PIP_NAME[w] != w]
                if bad:
                    P(f"- ⚠️ `pip install {line.strip()}` 中包名可能写错：" +
                      "、".join(f"`{b}` 应为 `{PIP_NAME[b]}`" for b in bad))
            P("")
    if not found_any:
        P("- 未发现明显问题。")

    text = "\n".join(out)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写入 {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
