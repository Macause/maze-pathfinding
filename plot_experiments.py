"""將批次實驗 summary CSV 畫成報告用比較圖。"""

import argparse
import csv
import math
from pathlib import Path


ALGORITHMS = ("DFS", "BFS", "Greedy", "A*")
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
METRICS = (
    ("path_length", "Path length (steps)", 1),
    ("expanded_count", "Expanded nodes", 1),
    ("mean_seconds", "Search time (ms)", 1000),
    ("peak_memory_bytes", "Peak Python allocations (KiB)", 1 / 1024),
)


def load_summary(path):
    """讀取彙整結果，拒絕重複或不完整的資料組。"""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("summary 沒有資料")
    seen = set()
    for row in rows:
        key = (row["maze_type"], int(row["rows"]), int(row["cols"]), row["algorithm"])
        if key in seen:
            raise ValueError(f"重複資料：{key}")
        seen.add(key)
        if int(row["seed_count"]) < 1:
            raise ValueError("seed_count 必須大於零")
        for metric, _, _ in METRICS:
            for prefix in ("mean_", "stdev_"):
                value = float(row[prefix + metric])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"無效量測值：{prefix + metric}")
    groups = {key[:3] for key in seen}
    for group in groups:
        if {key[3] for key in seen if key[:3] == group} != set(ALGORITHMS):
            raise ValueError(f"演算法資料不完整：{group}")
    return rows


def plot_experiments(summary_file, output_dir=None):
    """每種類型輸出四張 PNG 與 SVG，誤差棒為跨 seed 樣本標準差。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary_file = Path(summary_file)
    rows = load_summary(summary_file)
    experiment_id = summary_file.stem.removesuffix("__summary")
    output_dir = (
        Path(output_dir) if output_dir
        else Path(__file__).resolve().parent / "outputs" / "charts" / experiment_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for kind in sorted({row["maze_type"] for row in rows}):
        selected = [row for row in rows if row["maze_type"] == kind]
        sizes = sorted({(int(row["rows"]), int(row["cols"])) for row in selected})
        seed_counts = sorted({int(row["seed_count"]) for row in selected})
        repeats = sorted({int(row["repeat"]) for row in selected})
        for metric, ylabel, scale in METRICS:
            figure, axis = plt.subplots(figsize=(8, 5.5))
            for algorithm, color, marker in zip(ALGORITHMS, COLORS, ("o", "s", "^", "D")):
                values = sorted(
                    (row for row in selected if row["algorithm"] == algorithm),
                    key=lambda row: (int(row["rows"]), int(row["cols"])),
                )
                means = [float(row["mean_" + metric]) * scale for row in values]
                deviations = [float(row["stdev_" + metric]) * scale for row in values]
                axis.errorbar(
                    range(len(sizes)), means, yerr=deviations,
                    label=algorithm, color=color, marker=marker, linewidth=2,
                    linestyle="--" if algorithm == "A*" else "-",
                    markerfacecolor="none" if algorithm == "A*" else color,
                    capsize=4, markersize=5,
                )
            title = "Imperfect Maze" if kind == "imperfect" else "Braid Maze with Obstacles"
            axis.set_title(title, fontsize=14, pad=12)
            axis.set_xticks(range(len(sizes)), [f"{r} × {c}" for r, c in sizes])
            axis.set_xlabel("Maze size (rows × columns)")
            axis.set_ylabel(ylabel)
            axis.grid(axis="y", alpha=0.25)
            axis.spines[["top", "right"]].set_visible(False)
            axis.legend(ncol=4, loc="upper left", fontsize=9)
            axis.margins(x=0.12, y=0.2)
            figure.text(
                0.5, 0.025,
                f"Mean ± sample SD across seeds; n={','.join(map(str, seed_counts))}. "
                f"Timing repeats per seed: {','.join(map(str, repeats))}.",
                ha="center", fontsize=8,
            )
            figure.tight_layout(rect=(0, 0.06, 1, 1))
            name = f"{experiment_id}__{kind}__{metric}__mean_sd"
            try:
                for extension in ("png", "svg"):
                    path = output_dir / f"{name}.{extension}"
                    figure.savefig(path, dpi=220, facecolor="white")
                    generated.append(path)
            finally:
                plt.close(figure)
    return generated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary_file", help="experiment.py 產生的 __summary.csv")
    parser.add_argument("--output-dir", help="預設為專案 outputs/charts/實驗ID")
    args = parser.parse_args(argv)
    try:
        paths = plot_experiments(args.summary_file, args.output_dir)
    except (OSError, ValueError, KeyError, ImportError) as error:
        parser.exit(2, f"繪圖失敗：{error}\n")
    print(f"Generated {len(paths)} files in {paths[0].parent}")


if __name__ == "__main__":
    main()
