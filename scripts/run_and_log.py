#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_and_log.py —— 批量运行复现命令，保存完整日志，并生成"测试验证报告"可直接粘贴的 Markdown

用法示例:
    python run_and_log.py --cwd path/to/repo --log-dir repro_logs \\
        --env PYTHONPATH=/tmp/stubs --env MPLBACKEND=Agg \\
        --grep "最终指标|RMSE|Error" \\
        --cmd "python my_repro/step0_env_check.py" \\
        --cmd "python my_repro/step5_train.py --quick"

    # 也可以把命令写在文件里（每行一条，# 开头为注释）:
    python run_and_log.py --cwd repo --cmds-file cmds.txt

产物（在 --log-dir 下）:
    env.md                 测试环境（Python/平台/torch/CUDA/关键包版本）
    NN_<名字>.log          每条命令的完整 stdout+stderr
    results.json           结构化结果（命令、退出码、耗时、摘录）
    summary.md             Markdown 汇总表 + 每条命令的关键输出摘录（可粘进 03_测试验证报告.md）
只依赖 Python 标准库。
"""
import argparse
import datetime as dt
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time

KEY_PKGS = ["torch", "numpy", "scipy", "pandas", "matplotlib", "sklearn", "pywt", "ptwt",
            "tensorflow", "jax", "cv2", "PIL", "h5py"]


def env_report(python):
    code = r"""
import platform, sys, importlib
print(f"- Python: {sys.version.split()[0]} ({sys.executable})")
print(f"- 平台: {platform.platform()}")
for m in %r:
    try:
        mod = importlib.import_module(m)
        print(f"- {m}: {getattr(mod, '__version__', 'installed')}")
    except Exception:
        pass
try:
    import torch
    print(f"- CUDA 可用: {torch.cuda.is_available()}" + (f" ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else ""))
except Exception:
    pass
""" % KEY_PKGS
    try:
        out = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=120)
        return out.stdout
    except Exception as e:
        return f"- 无法获取环境信息: {e}\n"


def slug(cmd, i):
    s = re.sub(r"[^\w.-]+", "_", cmd.split("#")[0].strip())[:50].strip("_")
    return f"{i:02d}_{s or 'cmd'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", default=".", help="在哪个目录执行命令（一般是仓库根目录）")
    ap.add_argument("--log-dir", default="repro_logs")
    ap.add_argument("--cmd", action="append", default=[], help="要运行的命令，可重复")
    ap.add_argument("--cmds-file", help="每行一条命令的文本文件")
    ap.add_argument("--env", action="append", default=[], help="额外环境变量 KEY=VALUE，可重复")
    ap.add_argument("--timeout", type=int, default=3600, help="单条命令超时秒数")
    ap.add_argument("--grep", default=r"Error|Traceback|✅|❌|最终|RMSE|MSE|loss|耗时|saved|保存",
                    help="从输出中摘录匹配这些正则的行")
    ap.add_argument("--tail", type=int, default=8, help="每条命令额外摘录最后几行")
    ap.add_argument("--python", default=sys.executable, help="用于环境检查的解释器")
    ap.add_argument("--stop-on-fail", action="store_true")
    args = ap.parse_args()

    cmds = list(args.cmd)
    if args.cmds_file:
        for line in open(args.cmds_file, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                cmds.append(line)
    if not cmds:
        ap.error("没有命令：用 --cmd 或 --cmds-file 指定")

    os.makedirs(args.log_dir, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("MPLBACKEND", "Agg")
    for kv in args.env:
        k, v = kv.split("=", 1)
        if k == "PYTHONPATH" and env.get("PYTHONPATH"):
            v = v + os.pathsep + env["PYTHONPATH"]
        env[k] = v

    with open(os.path.join(args.log_dir, "env.md"), "w", encoding="utf-8") as f:
        f.write(f"# 测试环境\n\n- 记录时间: {dt.datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"- 工作目录: `{os.path.abspath(args.cwd)}`\n")
        extra = [kv for kv in args.env]
        if extra:
            f.write(f"- 额外环境变量: {', '.join(f'`{e}`' for e in extra)}\n")
        f.write(env_report(args.python))

    pat = re.compile(args.grep) if args.grep else None
    results = []
    for i, cmd in enumerate(cmds, 1):
        name = slug(cmd, i)
        log_path = os.path.join(args.log_dir, name + ".log")
        print(f"[{i}/{len(cmds)}] {cmd}", flush=True)
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, shell=True, cwd=args.cwd, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=args.timeout)
            out, code = (proc.stdout or "") + (proc.stderr or ""), proc.returncode
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or "") if isinstance(e.stdout, str) else ""
            out += f"\n[TIMEOUT after {args.timeout}s]"
            code = "timeout"
        dur = time.time() - t0
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"$ {cmd}\n# exit={code}  duration={dur:.1f}s\n\n{out}")
        lines = out.splitlines()
        picked = [l for l in lines if pat and pat.search(l)][-15:]
        tail = lines[-args.tail:] if args.tail else []
        status = "✅" if code == 0 else "❌"
        results.append({"idx": i, "cmd": cmd, "exit": code, "seconds": round(dur, 1),
                        "status": status, "log": os.path.basename(log_path),
                        "highlights": picked, "tail": tail})
        print(f"    -> {status} exit={code} {dur:.1f}s  log={log_path}", flush=True)
        if code != 0 and args.stop_on_fail:
            break

    with open(os.path.join(args.log_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    md = ["# 命令运行记录\n", "| # | 命令 | 结果 | 退出码 | 耗时 | 日志 |", "|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['idx']} | `{r['cmd']}` | {r['status']} | {r['exit']} | {r['seconds']}s | `{r['log']}` |")
    md.append("")
    for r in results:
        md.append(f"### {r['idx']}. `{r['cmd']}`\n")
        body = r["highlights"] or r["tail"]
        if r["tail"] and r["highlights"]:
            body = r["highlights"] + ["..."] + [l for l in r["tail"] if l not in r["highlights"]]
        md.append("```\n" + "\n".join(body) + "\n```\n")
    with open(os.path.join(args.log_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    ok = sum(r["exit"] == 0 for r in results)
    print(f"\n完成：{ok}/{len(results)} 条成功。汇总见 {os.path.join(args.log_dir, 'summary.md')}")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
