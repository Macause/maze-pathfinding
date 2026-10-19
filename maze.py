"""迷宮的稀疏資料結構。

座標使用題目規定的 1-based ``(row, column)``。完全空白且四周沒有牆的
格子不會存入 ``Maze.cells``，查詢時預設為空白格且牆壁 bitmask 為 0。
"""


class Cell:
    """保存單一非預設格子的狀態與四周牆壁。"""

    EMPTY = "0"
    OBSTACLE = "x"
    START = "s"
    TARGET = "t"
    VALID_STATES = {EMPTY, OBSTACLE, START, TARGET}

    def __init__(self, state=EMPTY, walls=0):
        if state not in self.VALID_STATES:
            raise ValueError(f"無效的格子狀態：{state}")
        self.state = state
        self.walls = walls


class Maze:
    """以稀疏字典和牆壁 bitmask 表示迷宮。"""

    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8

    _DIRECTION_INFO = {
        UP: ((-1, 0), DOWN),
        RIGHT: ((0, 1), LEFT),
        DOWN: ((1, 0), UP),
        LEFT: ((0, -1), RIGHT),
    }

    def __init__(self, rows, cols):
        if not isinstance(rows, int) or isinstance(rows, bool) or rows <= 0:
            raise ValueError("rows 必須是正整數")
        if not isinstance(cols, int) or isinstance(cols, bool) or cols <= 0:
            raise ValueError("cols 必須是正整數")

        self.rows = rows
        self.cols = cols
        self.cells = {}
        self.start = None
        self.target = None

    def in_bounds(self, position):
        """判斷座標是否位於迷宮內。"""
        row, col = self._validate_position_shape(position)
        return 1 <= row <= self.rows and 1 <= col <= self.cols

    def get_state(self, position):
        """取得格子狀態；未儲存的格子視為空白。"""
        self._require_in_bounds(position)
        cell = self.cells.get(position)
        return Cell.EMPTY if cell is None else cell.state

    def get_walls(self, position):
        """取得牆壁 bitmask；未儲存的格子視為沒有牆。"""
        self._require_in_bounds(position)
        cell = self.cells.get(position)
        return 0 if cell is None else cell.walls

    def set_state(self, position, state):
        """設定格子狀態，並維護唯一的起點與終點。"""
        self._require_in_bounds(position)
        if state not in Cell.VALID_STATES:
            raise ValueError(f"無效的格子狀態：{state}")

        old_state = self.get_state(position)
        if state == Cell.START and self.start not in (None, position):
            raise ValueError(f"迷宮已經有起點：{self.start}")
        if state == Cell.TARGET and self.target not in (None, position):
            raise ValueError(f"迷宮已經有終點：{self.target}")

        if old_state == Cell.START:
            self.start = None
        elif old_state == Cell.TARGET:
            self.target = None

        cell = self._get_or_create_cell(position)
        cell.state = state

        if state == Cell.START:
            self.start = position
        elif state == Cell.TARGET:
            self.target = position

        self._remove_cell_if_default(position)

    def add_wall(self, position, direction):
        """在指定方向加入牆，並同步更新相鄰格子的反方向。"""
        neighbor, opposite = self._neighbor_in_direction(position, direction)

        cell = self._get_or_create_cell(position)
        neighbor_cell = self._get_or_create_cell(neighbor)
        cell.walls |= direction
        neighbor_cell.walls |= opposite

    def remove_wall(self, position, direction):
        """移除指定方向的牆，並同步更新相鄰格子的反方向。"""
        neighbor, opposite = self._neighbor_in_direction(position, direction)

        cell = self.cells.get(position)
        if cell is not None:
            cell.walls &= ~direction

        neighbor_cell = self.cells.get(neighbor)
        if neighbor_cell is not None:
            neighbor_cell.walls &= ~opposite

        self._remove_cell_if_default(position)
        self._remove_cell_if_default(neighbor)

    def has_wall(self, position, direction):
        """判斷指定格子的某個方向是否有牆。"""
        self._neighbor_in_direction(position, direction)
        return bool(self.get_walls(position) & direction)

    def is_passable(self, position):
        """判斷格子是否位於迷宮內且不是障礙。"""
        return self.in_bounds(position) and self.get_state(position) != Cell.OBSTACLE

    def neighbors(self, position):
        """依上、右、下、左順序回傳可移動到的相鄰格子。"""
        self._require_in_bounds(position)
        if not self.is_passable(position):
            return []

        result = []
        row, col = position

        for direction in (self.UP, self.RIGHT, self.DOWN, self.LEFT):
            (row_change, col_change), _ = self._DIRECTION_INFO[direction]
            neighbor = (row + row_change, col + col_change)

            if not self.in_bounds(neighbor):
                continue
            if not self.is_passable(neighbor):
                continue
            if self.get_walls(position) & direction:
                continue

            result.append(neighbor)

        return result

    def _neighbor_in_direction(self, position, direction):
        self._require_in_bounds(position)
        if direction not in self._DIRECTION_INFO:
            raise ValueError("direction 必須是 Maze.UP、RIGHT、DOWN 或 LEFT")

        (row_change, col_change), opposite = self._DIRECTION_INFO[direction]
        row, col = position
        neighbor = (row + row_change, col + col_change)
        if not self.in_bounds(neighbor):
            raise ValueError("不能在迷宮邊界外側加入或移除牆壁")
        return neighbor, opposite

    def _get_or_create_cell(self, position):
        cell = self.cells.get(position)
        if cell is None:
            cell = Cell()
            self.cells[position] = cell
        return cell

    def _remove_cell_if_default(self, position):
        cell = self.cells.get(position)
        if cell is not None and cell.state == Cell.EMPTY and cell.walls == 0:
            del self.cells[position]

    def _require_in_bounds(self, position):
        if not self.in_bounds(position):
            raise IndexError(f"格子座標超出迷宮範圍：{position}")

    @staticmethod
    def _validate_position_shape(position):
        if (
            not isinstance(position, tuple)
            or len(position) != 2
            or not all(
                isinstance(value, int) and not isinstance(value, bool)
                for value in position
            )
        ):
            raise TypeError("position 必須是包含兩個整數的 (row, column) tuple")
        return position
