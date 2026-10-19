"""將作業的文字輸入格式解析成 ``Maze`` 物件。"""

from maze import Cell, Maze


class MazeParseError(ValueError):
    """輸入內容不符合迷宮格式。"""


DIRECTION_MAP = {
    "U": Maze.UP,
    "R": Maze.RIGHT,
    "D": Maze.DOWN,
    "L": Maze.LEFT,
}


def parse_maze(stream):
    """從文字串流讀取迷宮並回傳 ``Maze``。

    格式：
        rows cols
        <每列的 column state 配對，以 0 結束，共 rows 列>
        wall_count
        <row column U/R/D/L，共 wall_count 列>
    """
    line_number = 1
    dimension_line = stream.readline()
    if dimension_line == "":
        raise MazeParseError("輸入是空的，缺少迷宮尺寸")

    dimension_tokens = dimension_line.split()
    if len(dimension_tokens) != 2:
        raise MazeParseError("第 1 行必須是：rows cols")

    try:
        rows, cols = map(int, dimension_tokens)
        maze = Maze(rows, cols)
    except (TypeError, ValueError) as error:
        raise MazeParseError(f"第 1 行的迷宮尺寸無效：{error}") from error

    for row in range(1, rows + 1):
        line_number += 1
        row_line = stream.readline()
        if row_line == "":
            raise MazeParseError(f"輸入提前結束，缺少第 {row} 列的格子資料")

        tokens = row_line.split()
        if not tokens or tokens[-1] != "0":
            raise MazeParseError(f"第 {line_number} 行必須以 0 結束")
        if len(tokens) % 2 == 0:
            raise MazeParseError(
                f"第 {line_number} 行必須包含 column-state 配對，最後再加 0"
            )

        used_columns = set()
        for index in range(0, len(tokens) - 1, 2):
            try:
                column = int(tokens[index])
            except ValueError as error:
                raise MazeParseError(
                    f"第 {line_number} 行的欄號必須是整數：{tokens[index]}"
                ) from error

            state = tokens[index + 1]
            if state not in {Cell.OBSTACLE, Cell.START, Cell.TARGET}:
                raise MazeParseError(
                    f"第 {line_number} 行包含無效狀態：{state}"
                )
            if column in used_columns:
                raise MazeParseError(
                    f"第 {line_number} 行重複描述第 {column} 欄"
                )
            used_columns.add(column)

            try:
                maze.set_state((row, column), state)
            except (IndexError, TypeError, ValueError) as error:
                raise MazeParseError(f"第 {line_number} 行無效：{error}") from error

    line_number += 1
    wall_count_line = stream.readline()
    if wall_count_line == "":
        raise MazeParseError("輸入提前結束，缺少牆壁數量")

    wall_count_tokens = wall_count_line.split()
    if len(wall_count_tokens) != 1:
        raise MazeParseError(f"第 {line_number} 行必須只包含牆壁數量")

    try:
        wall_count = int(wall_count_tokens[0])
    except ValueError as error:
        raise MazeParseError(f"第 {line_number} 行的牆壁數量必須是整數") from error
    if wall_count < 0:
        raise MazeParseError(f"第 {line_number} 行的牆壁數量不能是負數")

    for wall_index in range(1, wall_count + 1):
        line_number += 1
        wall_line = stream.readline()
        if wall_line == "":
            raise MazeParseError(
                f"輸入提前結束，缺少第 {wall_index} 面牆的資料"
            )

        wall_tokens = wall_line.split()
        if len(wall_tokens) != 3:
            raise MazeParseError(
                f"第 {line_number} 行必須是：row column direction"
            )

        try:
            row = int(wall_tokens[0])
            column = int(wall_tokens[1])
        except ValueError as error:
            raise MazeParseError(
                f"第 {line_number} 行的牆壁座標必須是整數"
            ) from error

        direction_text = wall_tokens[2].upper()
        if direction_text not in DIRECTION_MAP:
            raise MazeParseError(
                f"第 {line_number} 行的方向必須是 U、R、D 或 L"
            )

        try:
            maze.add_wall(
                (row, column),
                DIRECTION_MAP[direction_text],
            )
        except (IndexError, TypeError, ValueError) as error:
            raise MazeParseError(f"第 {line_number} 行無效：{error}") from error

    for remaining_line in stream:
        line_number += 1
        if remaining_line.strip():
            raise MazeParseError(f"第 {line_number} 行含有未預期的額外資料")

    if maze.start is None:
        raise MazeParseError("迷宮缺少起點 s")
    if maze.target is None:
        raise MazeParseError("迷宮缺少終點 t")

    return maze


def parse_maze_file(file_path):
    """從 UTF-8 文字檔讀取迷宮。"""
    with open(file_path, "r", encoding="utf-8-sig") as stream:
        return parse_maze(stream)

