"""使用 Matplotlib 繪製迷宮與搜尋結果。"""

from pathlib import Path

from maze import Cell, Maze


def visualize_maze(
    maze,
    path=None,
    title=None,
    output_file=None,
    show=True,
):
    """繪製迷宮，可選擇顯示視窗或儲存成圖片。

    ``path`` 為 None 時只畫迷宮；提供路徑時會以藍線連接各格中心。
    函數回傳建立的 Matplotlib figure。
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError as error:
        raise RuntimeError(
            "視覺化需要 Matplotlib，請先安裝 matplotlib"
        ) from error

    if path is not None:
        _validate_path(maze, path)

    figure_width = min(16, max(4, maze.cols * 0.55))
    figure_height = min(16, max(4, maze.rows * 0.55))
    figure, axis = plt.subplots(figsize=(figure_width, figure_height))

    _draw_obstacles(axis, maze, Rectangle)
    if path is not None:
        _draw_path(axis, maze, path)
    _draw_internal_walls(axis, maze)
    _draw_outer_border(axis, maze, Rectangle)
    _draw_endpoints(axis, maze)

    axis.set_xlim(0, maze.cols)
    axis.set_ylim(0, maze.rows)
    axis.set_aspect("equal")
    axis.axis("off")

    if title:
        axis.set_title(title, fontsize=14, pad=12)

    figure.tight_layout()

    if output_file is not None:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            output_file,
            dpi=200,
            bbox_inches="tight",
            facecolor="white",
        )

    if show:
        plt.show()
    else:
        plt.close(figure)

    return figure


def _draw_obstacles(axis, maze, rectangle_class):
    for row in range(1, maze.rows + 1):
        for col in range(1, maze.cols + 1):
            if maze.get_state((row, col)) != Cell.OBSTACLE:
                continue

            x, y = _cell_bottom_left(maze, (row, col))
            obstacle = rectangle_class(
                (x, y),
                1,
                1,
                facecolor="#37474F",
                edgecolor="none",
                zorder=1,
            )
            axis.add_patch(obstacle)


def _draw_path(axis, maze, path):
    x_values = []
    y_values = []

    for position in path:
        x, y = _cell_center(maze, position)
        x_values.append(x)
        y_values.append(y)

    axis.plot(
        x_values,
        y_values,
        color="#1976D2",
        linewidth=3,
        marker="o",
        markersize=4,
        solid_capstyle="round",
        zorder=2,
    )


def _draw_internal_walls(axis, maze):
    # 每面牆在相鄰兩格的 bitmask 中各出現一次；只畫右牆和下牆避免重複。
    for row in range(1, maze.rows + 1):
        for col in range(1, maze.cols + 1):
            position = (row, col)
            x, y = _cell_bottom_left(maze, position)

            if col < maze.cols and maze.has_wall(position, Maze.RIGHT):
                axis.plot(
                    [x + 1, x + 1],
                    [y, y + 1],
                    color="black",
                    linewidth=1.8,
                    zorder=3,
                )

            if row < maze.rows and maze.has_wall(position, Maze.DOWN):
                axis.plot(
                    [x, x + 1],
                    [y, y],
                    color="black",
                    linewidth=1.8,
                    zorder=3,
                )


def _draw_outer_border(axis, maze, rectangle_class):
    border = rectangle_class(
        (0, 0),
        maze.cols,
        maze.rows,
        fill=False,
        edgecolor="black",
        linewidth=2.5,
        zorder=4,
    )
    axis.add_patch(border)


def _draw_endpoints(axis, maze):
    endpoint_styles = (
        (maze.start, "#2E7D32", "S"),
        (maze.target, "#C62828", "T"),
    )

    for position, color, label in endpoint_styles:
        if position is None:
            continue

        x, y = _cell_center(maze, position)
        axis.scatter(
            [x],
            [y],
            s=180,
            color=color,
            edgecolors="white",
            linewidths=1.5,
            zorder=5,
        )
        axis.text(
            x,
            y,
            label,
            color="white",
            fontsize=9,
            fontweight="bold",
            horizontalalignment="center",
            verticalalignment="center",
            zorder=6,
        )


def _validate_path(maze, path):
    if not path:
        raise ValueError("視覺化路徑不能是空列表")
    if path[0] != maze.start or path[-1] != maze.target:
        raise ValueError("視覺化路徑必須從起點開始並在終點結束")

    for current, neighbor in zip(path, path[1:]):
        if neighbor not in maze.neighbors(current):
            raise ValueError(f"路徑包含不合法移動：{current} -> {neighbor}")


def _cell_bottom_left(maze, position):
    row, col = position
    return col - 1, maze.rows - row


def _cell_center(maze, position):
    x, y = _cell_bottom_left(maze, position)
    return x + 0.5, y + 0.5
