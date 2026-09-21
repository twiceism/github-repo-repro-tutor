# 空桩：弹窗函数全部静默；询问类默认返回 False（不做破坏性确认）
def showinfo(*a, **k): return "ok"
def showwarning(*a, **k): return "ok"
def showerror(*a, **k): return "ok"
def askyesno(*a, **k): return False
def askokcancel(*a, **k): return False
def askquestion(*a, **k): return "no"
def askyesnocancel(*a, **k): return None
