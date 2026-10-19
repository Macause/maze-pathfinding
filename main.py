"""Assignment 3 的命令列主程式。"""

import argparse
import sys

from maze_display import format_path, format_path_matrix
from maze_parser import MazeParseError, parse_maze_file
from search import a_star, bfs, dfs, greedy_best_first


ALGORITHMS = {
    "dfs": ("DFS", dfs),
    "bfs": ("BFS", bfs),
    "greedy": ("Greedy Best-First Search", greedy_best_first),
    "astar": ("A* Search", a_star),
}


def create_argument_parser():
    """建立並回傳命令列參數解析器。"""
    parser = argparse.ArgumentParser(
        description="讀取迷宮並使用指定演算法尋找起點到終點的路徑。"
    )
    parser.add_argument(
        "input_file",
        help="迷宮輸入檔路徑",
    )
    parser.add_argument(
        "algorithm",
        choices=ALGORITHMS,
        help="搜尋演算法：dfs、bfs、greedy 或 astar",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="顯示搜尋節點數（包含起點與終點）",
    )
    parser.add_argument(
        "--image",
        metavar="FILE",
        help="將迷宮與路徑儲存成 PNG、SVG 或 PDF 圖片",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="開啟 Matplotlib 視窗顯示迷宮",
    )
    return parser


def run(input_file, algorithm_key, image_file=None, show_image=False, stats=False):
    """讀取迷宮、執行搜尋並印出結果。"""
    maze = parse_maze_file(input_file)
    algorithm_name, algorithm = ALGORITHMS[algorithm_key]
    metrics = {} if stats else None
    path = algorithm(maze, metrics=metrics)

    print(f"演算法：{algorithm_name}")
    if metrics is not None:
        print(f"搜尋節點數：{metrics['expanded_count']}")

    if path is None:
        print("沒有路徑")
        _visualize_result(
            maze,
            path=None,
            title=f"{algorithm_name} - No Path",
            image_file=image_file,
            show_image=show_image,
        )
        return False

    print(f"路徑：{format_path(path)}")
    print(f"路徑長度：{len(path) - 1}")
    print()
    print(format_path_matrix(maze, path))

    _visualize_result(
        maze,
        path=path,
        title=f"{algorithm_name} - Path Length: {len(path) - 1}",
        image_file=image_file,
        show_image=show_image,
    )
    return True


def _visualize_result(maze, path, title, image_file, show_image):
    """在使用者要求時才載入 Matplotlib 並繪製結果。"""
    if image_file is None and not show_image:
        return

    from maze_visualizer import visualize_maze

    visualize_maze(
        maze,
        path=path,
        title=title,
        output_file=image_file,
        show=show_image,
    )


def main(argv=None):
    """處理命令列參數與容易理解的錯誤訊息。"""
    parser = create_argument_parser()
    arguments = parser.parse_args(argv)

    try:
        path_found = run(
            arguments.input_file,
            arguments.algorithm,
            image_file=arguments.image,
            show_image=arguments.show,
            stats=arguments.stats,
        )
    except FileNotFoundError as error:
        print(f"檔案不存在：{error.filename}", file=sys.stderr)
        return 2
    except PermissionError as error:
        print(f"沒有檔案存取權限：{error.filename}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"檔案錯誤：{error}", file=sys.stderr)
        return 2
    except (MazeParseError, UnicodeError) as error:
        print(f"輸入錯誤：{error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"迷宮錯誤：{error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"視覺化錯誤：{error}", file=sys.stderr)
        return 2

    return 0 if path_found else 1


if __name__ == "__main__":
    raise SystemExit(main())
