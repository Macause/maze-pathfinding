"""產生可重現的 Imperfect Maze 與 Braid Maze with Obstacles。"""

import argparse
import random
from pathlib import Path

from data_structures import Stack
from maze import Cell, Maze


_DIRECTIONS = (
    (Maze.UP, -1, 0),
    (Maze.RIGHT, 0, 1),
    (Maze.DOWN, 1, 0),
    (Maze.LEFT, 0, -1),
)


def generate_imperfect_maze(rows, cols, loop_rate=0.15, seed=None):
    """產生連通迷宮，再按 loop_rate 拆除剩餘牆；拆除數為 0 時仍無環。"""
    _validate_rate("loop_rate", loop_rate)
    randomizer = random.Random(seed)
    maze = _create_base_maze(rows, cols)

    _add_all_internal_walls(maze)
    _carve_spanning_tree(maze, randomizer)

    remaining_walls = _list_internal_walls(maze)
    randomizer.shuffle(remaining_walls)
    remove_count = round(len(remaining_walls) * loop_rate)

    for position, direction in remaining_walls[:remove_count]:
        maze.remove_wall(position, direction)

    return maze


def generate_braid_obstacle_maze(
    rows,
    cols,
    obstacle_rate=0.15,
    braid_rate=1.0,
    seed=None,
):
    """產生含障礙、連通且儘可能消除死路的 Braid Maze。"""
    _validate_rate("obstacle_rate", obstacle_rate)
    _validate_rate("braid_rate", braid_rate)
    randomizer = random.Random(seed)

    # 先建立一次 Maze，以便統一驗證 rows、cols。
    maze = _create_base_maze(rows, cols)
    obstacle_count = round((rows * cols - 2) * obstacle_rate)
    obstacles = _choose_connected_obstacles(
        rows,
        cols,
        obstacle_count,
        randomizer,
    )

    for position in obstacles:
        maze.set_state(position, Cell.OBSTACLE)

    _add_all_internal_walls(maze)
    _carve_spanning_tree(maze, randomizer)
    _remove_dead_ends(maze, braid_rate, randomizer)
    return maze


def maze_to_text(maze):
    """將 Maze 轉換成 maze_parser 可讀取的文字格式。"""
    lines = [f"{maze.rows} {maze.cols}"]

    for row in range(1, maze.rows + 1):
        row_values = []
        for col in range(1, maze.cols + 1):
            state = maze.get_state((row, col))
            if state != Cell.EMPTY:
                row_values.extend((str(col), state))
        row_values.append("0")
        lines.append(" ".join(row_values))

    walls = _list_internal_walls(maze)
    lines.append(str(len(walls)))

    direction_text = {
        Maze.RIGHT: "R",
        Maze.DOWN: "D",
    }
    for (row, col), direction in walls:
        lines.append(f"{row} {col} {direction_text[direction]}")

    return "\n".join(lines) + "\n"


def write_maze_file(maze, file_path):
    """將迷宮以 UTF-8 編碼寫入文字檔。"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as output_file:
        output_file.write(maze_to_text(maze))


def _create_base_maze(rows, cols):
    maze = Maze(rows, cols)
    if rows * cols < 2:
        raise ValueError("迷宮至少需要兩個格子，才能放置不同的起點與終點")

    maze.set_state((1, 1), Cell.START)
    maze.set_state((rows, cols), Cell.TARGET)
    return maze


def _add_all_internal_walls(maze):
    """在每對相鄰的非障礙格之間加入一面牆。"""
    for row in range(1, maze.rows + 1):
        for col in range(1, maze.cols + 1):
            position = (row, col)
            if not maze.is_passable(position):
                continue

            if col < maze.cols and maze.is_passable((row, col + 1)):
                maze.add_wall(position, Maze.RIGHT)
            if row < maze.rows and maze.is_passable((row + 1, col)):
                maze.add_wall(position, Maze.DOWN)


def _carve_spanning_tree(maze, randomizer):
    """使用 randomized DFS 拆牆，連接所有非障礙格。"""
    frontier = Stack()
    frontier.push(maze.start)
    visited = {maze.start}

    while not frontier.is_empty():
        current = frontier.peek()
        candidates = []

        for direction, neighbor in _geometric_neighbors(maze, current):
            if neighbor not in visited:
                candidates.append((direction, neighbor))

        if not candidates:
            frontier.pop()
            continue

        direction, neighbor = randomizer.choice(candidates)
        maze.remove_wall(current, direction)
        visited.add(neighbor)
        frontier.push(neighbor)

    passable_count = maze.rows * maze.cols - _count_obstacles(maze)
    if len(visited) != passable_count:
        raise ValueError("非障礙區域不連通，無法建立完整迷宮")


def _remove_dead_ends(maze, braid_rate, randomizer):
    """依 braid_rate 處理非起終點死路；拆牆不會產生新的死路。"""
    dead_ends = []

    for row in range(1, maze.rows + 1):
        for col in range(1, maze.cols + 1):
            position = (row, col)
            if position in (maze.start, maze.target):
                continue
            if maze.is_passable(position) and len(maze.neighbors(position)) == 1:
                dead_ends.append(position)

    randomizer.shuffle(dead_ends)
    remove_count = round(len(dead_ends) * braid_rate)

    for position in dead_ends[:remove_count]:
        if len(maze.neighbors(position)) != 1:
            continue

        closed_walls = []
        for direction, _ in _geometric_neighbors(maze, position):
            if maze.has_wall(position, direction):
                closed_walls.append(direction)

        if closed_walls:
            direction = randomizer.choice(closed_walls)
            maze.remove_wall(position, direction)


def _choose_connected_obstacles(
    rows,
    cols,
    obstacle_count,
    randomizer,
    max_attempts=10,
):
    """選擇障礙，並保持所有非障礙格連通且具有可編織的幾何結構。"""
    start = (1, 1)
    target = (rows, cols)
    candidates = [
        (row, col)
        for row in range(1, rows + 1)
        for col in range(1, cols + 1)
        if (row, col) not in (start, target)
    ]

    if obstacle_count == 0:
        return set()

    for _ in range(max_attempts):
        obstacles = set()
        randomizer.shuffle(candidates)
        for position in candidates:
            obstacles.add(position)
            # 新障礙只會影響相鄰格的幾何 degree，先做便宜的局部檢查。
            valid = True
            for _, dr, dc in _DIRECTIONS:
                neighbor = (position[0] + dr, position[1] + dc)
                if not _position_in_bounds(neighbor, rows, cols):
                    continue
                if neighbor in obstacles:
                    continue
                degree = sum(
                    _position_in_bounds((neighbor[0] + nr, neighbor[1] + nc), rows, cols)
                    and (neighbor[0] + nr, neighbor[1] + nc) not in obstacles
                    for _, nr, nc in _DIRECTIONS
                )
                minimum = 1 if neighbor in (start, target) else 2
                if degree < minimum:
                    valid = False
                    break
            if not valid or not _passable_cells_are_connected(rows, cols, obstacles, start):
                obstacles.remove(position)
                continue
            if len(obstacles) == obstacle_count:
                return obstacles

    raise ValueError(
        "無法在指定障礙比例下建立連通的 Braid Maze；請降低 obstacle_rate"
    )


def _passable_cells_are_connected(rows, cols, obstacles, start):
    expected_count = rows * cols - len(obstacles)
    visited = {start}
    frontier = [start]

    while frontier:
        row, col = frontier.pop()
        for _, row_change, col_change in _DIRECTIONS:
            neighbor = (row + row_change, col + col_change)
            if not _position_in_bounds(neighbor, rows, cols):
                continue
            if neighbor in obstacles or neighbor in visited:
                continue
            visited.add(neighbor)
            frontier.append(neighbor)

    return len(visited) == expected_count


def _has_braidable_geometry(rows, cols, obstacles, start, target):
    """確保非端點格至少有兩個非障礙鄰居，避免不可消除的死路。"""
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            position = (row, col)
            if position in obstacles or position in (start, target):
                continue

            neighbor_count = 0
            for _, row_change, col_change in _DIRECTIONS:
                neighbor = (row + row_change, col + col_change)
                if (
                    _position_in_bounds(neighbor, rows, cols)
                    and neighbor not in obstacles
                ):
                    neighbor_count += 1

            if neighbor_count < 2:
                return False

    return True


def _geometric_neighbors(maze, position):
    """回傳不考慮牆壁、但排除邊界與障礙的鄰居。"""
    row, col = position
    result = []

    for direction, row_change, col_change in _DIRECTIONS:
        neighbor = (row + row_change, col + col_change)
        if maze.in_bounds(neighbor) and maze.is_passable(neighbor):
            result.append((direction, neighbor))

    return result


def _list_internal_walls(maze):
    """每面內部牆只以右牆或下牆列出一次。"""
    walls = []

    for row in range(1, maze.rows + 1):
        for col in range(1, maze.cols + 1):
            position = (row, col)

            if col < maze.cols and maze.has_wall(position, Maze.RIGHT):
                walls.append((position, Maze.RIGHT))
            if row < maze.rows and maze.has_wall(position, Maze.DOWN):
                walls.append((position, Maze.DOWN))

    return walls


def _count_obstacles(maze):
    return sum(
        1 for cell in maze.cells.values() if cell.state == Cell.OBSTACLE
    )


def _position_in_bounds(position, rows, cols):
    row, col = position
    return 1 <= row <= rows and 1 <= col <= cols


def _validate_rate(name, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} 必須是 0 到 1 之間的數字")
    if not 0 <= value <= 1:
        raise ValueError(f"{name} 必須介於 0 和 1 之間")


def create_argument_parser():
    parser = argparse.ArgumentParser(description="產生 Assignment 3 的迷宮輸入檔。")
    parser.add_argument("maze_type", choices=("imperfect", "braid"))
    parser.add_argument("rows", type=int)
    parser.add_argument("cols", type=int)
    parser.add_argument("output_file")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--loop-rate", type=float, default=0.15)
    parser.add_argument("--obstacle-rate", type=float, default=0.15)
    parser.add_argument("--braid-rate", type=float, default=1.0)
    return parser


def main(argv=None):
    arguments = create_argument_parser().parse_args(argv)

    try:
        if arguments.maze_type == "imperfect":
            maze = generate_imperfect_maze(
                arguments.rows,
                arguments.cols,
                loop_rate=arguments.loop_rate,
                seed=arguments.seed,
            )
        else:
            maze = generate_braid_obstacle_maze(
                arguments.rows,
                arguments.cols,
                obstacle_rate=arguments.obstacle_rate,
                braid_rate=arguments.braid_rate,
                seed=arguments.seed,
            )

        write_maze_file(maze, arguments.output_file)
    except (OSError, TypeError, ValueError) as error:
        raise SystemExit(f"產生迷宮失敗：{error}") from error

    print(f"已產生 {arguments.maze_type} maze：{arguments.output_file}")


if __name__ == "__main__":
    main()
