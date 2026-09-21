# -*- coding: utf-8 -*-
"""
tkinter 空桩（只用于无图形界面的测试环境，让"顶部 import 了 tkinter 的训练代码"能被导入）
用法：把 stubs/ 目录加入 PYTHONPATH，例如  PYTHONPATH=<skill>/scripts/stubs python xxx.py
⚠️ 不要交给用户使用，也不要用它运行真正的 GUI——所有调用都是空操作。
"""


class _Any:
    """任意属性、任意调用都返回自身的"万能空对象" """
    def __init__(self, *a, **k): pass
    def __getattr__(self, name): return _Any()
    def __call__(self, *a, **k): return _Any()
    def __iter__(self): return iter(())
    def __bool__(self): return False
    def get(self, *a, **k): return None
    def set(self, *a, **k): return None


def __getattr__(name):          # 模块级兜底：from tkinter import 任意名字
    return _Any


Tk = Toplevel = Frame = Label = Button = Entry = Text = Canvas = Menu = _Any
StringVar = IntVar = DoubleVar = BooleanVar = _Any
END = "end"; LEFT = "left"; RIGHT = "right"; TOP = "top"; BOTTOM = "bottom"
BOTH = "both"; X = "x"; Y = "y"; W = "w"; E = "e"; N = "n"; S = "s"; NSEW = "nsew"
TclError = RuntimeError
