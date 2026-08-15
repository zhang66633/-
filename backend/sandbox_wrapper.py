"""沙箱包装脚本 — 在 Docker 容器内执行用户代码。

用法:
    docker run --rm --network=none --memory=512m \\
        -v /path/to/code.py:/code.py:ro \\
        -v /path/to/output:/output \\
        mathmodel-sandbox /code.py /output

安全:
    - 网络由 Docker --network=none 彻底阻断（不依赖 socket monkey-patch）
    - 内存由 Docker --memory 硬限制（不受 OS 影响）
    - 超时由 docker run --timeout 或 subprocess timeout 控制
    - 环境变量已由 Docker 隔离
"""

import os
import sys
import traceback
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("Usage: python wrapper.py <code_file> <output_dir>", file=sys.stderr)
        sys.exit(1)

    code_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not code_file.exists():
        print(f"Code file not found: {code_file}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(output_dir))

    # matplotlib 非交互后端（必须在 import pyplot 之前）
    import matplotlib
    matplotlib.use("Agg")

    # 中文字体自动配置：按可用性选择 CJK 字体（容器内 Noto Sans CJK），
    # 图表中文标题/轴标签不再变豆腐块
    try:
        import matplotlib.font_manager as fm

        candidates = [
            "Noto Sans CJK SC", "Microsoft YaHei", "SimHei",
            "PingFang SC", "WenQuanYi Micro Hei", "Source Han Sans SC",
        ]
        available = {f.name for f in fm.fontManager.ttflist}
        for c in candidates:
            if c in available:
                matplotlib.rcParams["font.sans-serif"] = [
                    c
                ] + list(matplotlib.rcParams["font.sans-serif"])
                break
        matplotlib.rcParams["axes.unicode_minus"] = False
        del fm
    except Exception:
        pass

    # 读取并执行用户代码
    code = code_file.read_text(encoding="utf-8")

    # 记录用户手动 savefig 过的 figure（自动保存时跳过，避免同图落盘两份——
    # 手动保存与自动保存往往只是 dpi/bbox 不同，内容 MD5 去重会失效）
    import matplotlib.figure as _mfig

    _orig_savefig = _mfig.Figure.savefig
    _saved_figs = set()

    def _tracked_savefig(self, *args, **kwargs):
        _saved_figs.add(id(self))
        return _orig_savefig(self, *args, **kwargs)

    _mfig.Figure.savefig = _tracked_savefig

    try:
        exec(code, {"__name__": "__main__"})
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    # 自动保存所有 matplotlib 图表（跳过用户已手动保存过的）
    try:
        import matplotlib.pyplot as plt
        for i in plt.get_fignums():
            fig = plt.figure(i)
            if id(fig) in _saved_figs:
                continue
            fig.savefig(
                str(output_dir / f"figure_{i}.png"),
                dpi=150,
                bbox_inches="tight",
            )
        plt.close("all")
    except Exception:
        pass  # 图表保存失败不影响退出码


if __name__ == "__main__":
    main()
