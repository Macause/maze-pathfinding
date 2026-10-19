"""將迷宮與搜尋路徑轉換成容易閱讀的文字輸出。"""

from maze import Cell


def format_path(path):
    """將座標列表格式化成題目要求的連續座標字串。"""
    if path is None:
        return "沒有路徑"
    return "".join(f"({row},{col})" for row, col in path)


def format_path_matrix(maze, path):
    """以矩陣顯示迷宮，並將路徑中間格標上移動順序。

    起點維持 ``s``，終點維持 ``t``，障礙維持 ``x``。從起點移動後
    經過的第一個中間格標為 1，之後依序增加；沒有路徑時回傳
    ``沒有路徑``。
    """
    if path is None:
        return "沒有路徑"

    if not path or path[0] != maze.start or path[-1] != maze.target:
        raise ValueError("路徑必須從迷宮起點開始，並在終點結束")

    path_steps = {
        position: step
        for step, position in enumerate(path[1:-1], start=1)
    }

    largest_step = max(path_steps.values(), default=0)
    cell_width = max(1, len(str(largest_step)))
    lines = []

    for row in range(1, maze.rows + 1):
        values = []

        for col in range(1, maze.cols + 1):
            position = (row, col)
            state = maze.get_state(position)

            if state == Cell.START:
                value = Cell.START
            elif state == Cell.TARGET:
                value = Cell.TARGET
            elif state == Cell.OBSTACLE:
                value = Cell.OBSTACLE
            elif position in path_steps:
                value = str(path_steps[position])
            else:
                value = Cell.EMPTY

            values.append(value.rjust(cell_width))

        lines.append(" ".join(values))

    return "\n".join(lines)


def print_path_matrix(maze, path):
    """直接印出矩陣形式的搜尋結果。"""
    print(format_path_matrix(maze, path))
