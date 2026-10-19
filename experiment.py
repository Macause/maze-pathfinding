"""批次生成迷宮並保存逐案例與跨 seed 的效能結果。"""

import argparse
import csv
import json
import platform
import statistics
from datetime import datetime
from pathlib import Path

from benchmark import benchmark_maze
from maze_generator import (
    generate_imperfect_maze,
    generate_braid_obstacle_maze,
    write_maze_file,
)
from maze_parser import parse_maze_file


def maze_name(kind, size, seed, loop_rate, obstacle_rate, braid_rate):
    """以完整浮點表示保留參數，避免不同比例產生相同名稱。"""
    def token(value):
        return str(float(value)).replace(".", "p")
    parameters = (
        f"loop{token(loop_rate)}" if kind == "imperfect"
        else f"obs{token(obstacle_rate)}__braid{token(braid_rate)}"
    )
    return f"maze__{kind}__r{size:04d}_c{size:04d}__{parameters}__seed{seed:04d}"


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 100])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(5)))
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--loop-rate", type=float, default=0.15)
    parser.add_argument("--obstacle-rate", type=float, default=0.15)
    parser.add_argument("--braid-rate", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.repeat < 1 or any(size < 2 for size in args.sizes):
        parser.error("repeat 必須大於 0，尺寸必須至少為 2")
    for rate in (args.loop_rate, args.obstacle_rate, args.braid_rate):
        if not 0 <= rate <= 1:
            parser.error("比例必須介於 0 與 1")
    args.sizes = list(dict.fromkeys(args.sizes))
    args.seeds = list(dict.fromkeys(args.seeds))
    # 每次實驗建立獨立目錄，保留既有結果。
    run_id = "experiment__" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    root = Path(__file__).resolve().parent
    inputs = root / "inputs" / "experiments" / run_id
    outputs = root / "outputs" / "experiments" / run_id
    outputs.mkdir(parents=True)
    manifest = {**vars(args), "python": platform.python_version(), "platform": platform.platform()}
    with (outputs / f"{run_id}__config.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
    results = []
    for kind in ("imperfect", "braid"):
        for size in args.sizes:
            for seed in args.seeds:
                name = maze_name(kind, size, seed, args.loop_rate, args.obstacle_rate, args.braid_rate)
                print(f"Generating: {name}", flush=True)
                if kind == "imperfect":
                    maze = generate_imperfect_maze(size, size, args.loop_rate, seed)
                else:
                    maze = generate_braid_obstacle_maze(size, size, args.obstacle_rate, args.braid_rate, seed)
                path = inputs / f"{name}.txt"
                write_maze_file(maze, path)
                maze = parse_maze_file(path)
                measured = benchmark_maze(maze, args.repeat)
                metadata = {
                    "maze_file": str(path.relative_to(root)), "maze_type": kind,
                    "rows": size, "cols": size, "seed": seed,
                    "loop_rate": args.loop_rate if kind == "imperfect" else "",
                    "obstacle_rate": args.obstacle_rate if kind == "braid" else "",
                    "braid_rate": args.braid_rate if kind == "braid" else "",
                    "actual_obstacles": sum(cell.state == "x" for cell in maze.cells.values()),
                }
                records = [{**metadata, **result} for result in measured]
                write_csv(outputs / f"{name}__benchmark__repeat{args.repeat:03d}.csv", records)
                results.extend(records)
                write_csv(outputs / f"{run_id}__results.csv", results)
    summary = []
    for kind in ("imperfect", "braid"):
        for size in args.sizes:
            for algorithm in ("DFS", "BFS", "Greedy", "A*"):
                group = [r for r in results if r["maze_type"] == kind and r["rows"] == size and r["algorithm"] == algorithm]
                row = {"maze_type": kind, "rows": size, "cols": size, "algorithm": algorithm, "seed_count": len(group), "repeat": args.repeat}
                for metric in ("path_length", "expanded_count", "mean_seconds", "median_seconds", "peak_memory_bytes"):
                    values = [r[metric] for r in group if r[metric] is not None]
                    row[f"mean_{metric}"] = statistics.fmean(values) if values else ""
                    row[f"stdev_{metric}"] = statistics.stdev(values) if len(values) > 1 else 0
                summary.append(row)
    write_csv(outputs / f"{run_id}__summary.csv", summary)
    print(f"Results: {outputs}")


if __name__ == "__main__":
    main()
