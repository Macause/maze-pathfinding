"""比較四種迷宮搜尋演算法的時間、節點數與尖峰記憶體。"""

import argparse
import csv
import gc
import statistics
import tracemalloc
from pathlib import Path
from time import perf_counter

from maze_parser import MazeParseError, parse_maze_file
from search import a_star, bfs, dfs, greedy_best_first


ALGORITHMS = (
    ("DFS", dfs),
    ("BFS", bfs),
    ("Greedy", greedy_best_first),
    ("A*", a_star),
)


def benchmark_algorithm(maze, name, algorithm, repeat=20):
    """在同一迷宮上重複執行演算法並回傳彙整結果。"""
    if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat <= 0:
        raise ValueError("repeat 必須是正整數")

    elapsed_times = []
    path_length = None
    expanded_count = None

    for _ in range(repeat):
        metrics = {}
        start_time = perf_counter()
        path = algorithm(maze, metrics=metrics)
        elapsed_times.append(perf_counter() - start_time)

        current_path_length = None if path is None else len(path) - 1
        current_expanded_count = metrics["expanded_count"]

        if path_length is None and expanded_count is None:
            path_length = current_path_length
            expanded_count = current_expanded_count
        elif (
            current_path_length != path_length
            or current_expanded_count != expanded_count
        ):
            raise RuntimeError(f"{name} 在重複執行時產生不一致的結果")

    peak_memory_bytes = _measure_peak_memory(maze, algorithm)

    return {
        "algorithm": name,
        "path_length": path_length,
        "expanded_count": expanded_count,
        "mean_seconds": statistics.fmean(elapsed_times),
        "median_seconds": statistics.median(elapsed_times),
        "peak_memory_bytes": peak_memory_bytes,
        "repeat": repeat,
    }


def benchmark_maze(maze, repeat=20):
    """依固定順序比較 DFS、BFS、Greedy 與 A*。"""
    return [
        benchmark_algorithm(maze, name, algorithm, repeat)
        for name, algorithm in ALGORITHMS
    ]


def _measure_peak_memory(maze, algorithm):
    """獨立執行一次搜尋，量測搜尋期間的 Python 尖峰配置記憶體。"""
    if tracemalloc.is_tracing():
        raise RuntimeError("請先停止外部 tracemalloc，再執行記憶體比較")
    gc.collect()
    tracemalloc.start()
    try:
        algorithm(maze)
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak_memory_bytes


def format_results_table(results):
    """將比較結果格式化成純文字表格。"""
    headers = (
        "Algorithm",
        "Path Length",
        "Expanded",
        "Mean (ms)",
        "Median (ms)",
        "Peak (KiB)",
    )
    rows = []

    for result in results:
        path_length = result["path_length"]
        rows.append(
            (
                result["algorithm"],
                "N/A" if path_length is None else str(path_length),
                str(result["expanded_count"]),
                f"{result['mean_seconds'] * 1000:.4f}",
                f"{result['median_seconds'] * 1000:.4f}",
                f"{result['peak_memory_bytes'] / 1024:.2f}",
            )
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def format_row(row):
        return " | ".join(
            value.ljust(widths[index])
            for index, value in enumerate(row)
        )

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join(
        [format_row(headers), separator, *(format_row(row) for row in rows)]
    )


def write_results_csv(results, file_path, maze_file=None):
    """將單一迷宮的比較結果寫入 CSV。"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "maze_file",
        "algorithm",
        "path_length",
        "expanded_count",
        "mean_seconds",
        "median_seconds",
        "peak_memory_bytes",
        "repeat",
    )

    with open(file_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "maze_file": "" if maze_file is None else str(maze_file),
                    **result,
                }
            )


def create_argument_parser():
    parser = argparse.ArgumentParser(
        description="比較 DFS、BFS、Greedy 與 A* 的搜尋效能。"
    )
    parser.add_argument("input_file", help="迷宮輸入檔路徑")
    parser.add_argument(
        "--repeat",
        type=int,
        default=20,
        help="每個演算法的計時重複次數，預設為 20",
    )
    parser.add_argument(
        "--csv",
        metavar="FILE",
        help="將結果另存為 CSV",
    )
    return parser


def main(argv=None):
    arguments = create_argument_parser().parse_args(argv)

    try:
        maze = parse_maze_file(arguments.input_file)
        results = benchmark_maze(maze, repeat=arguments.repeat)
        print(f"迷宮：{arguments.input_file}")
        print(f"計時重複次數：{arguments.repeat}")
        print()
        print(format_results_table(results))

        if arguments.csv:
            write_results_csv(
                results,
                arguments.csv,
                maze_file=arguments.input_file,
            )
            print(f"\nCSV：{arguments.csv}")
    except FileNotFoundError:
        raise SystemExit(f"找不到輸入檔案：{arguments.input_file}")
    except (MazeParseError, OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"效能比較失敗：{error}") from error


if __name__ == "__main__":
    main()
