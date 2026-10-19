"""迷宮搜尋演算法。

各搜尋函數可傳入 metrics 字典，取得 expanded_count：實際從 frontier
取出並處理的節點數，包含起點與終點，但排除 A* 的失效 heap 項目。
"""

from data_structures import MinHeap, Queue, Stack


def reconstruct_path(parent, start, target):
    """根據前驅紀錄，重建並回傳 start 到 target 的座標列表。

    如果 target 不在 parent 中，代表搜尋沒有到達終點，回傳 None。
    """
    if target not in parent:
        return None

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    if not path or path[0] != start:
        return None
    return path


def manhattan_distance(first, second):
    """計算兩個格子的 Manhattan distance。"""
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _require_endpoints(maze):
    """確認迷宮具有起點和終點。"""
    if maze.start is None:
        raise ValueError("迷宮缺少起點")
    if maze.target is None:
        raise ValueError("迷宮缺少終點")


def _initialize_metrics(metrics):
    """重設本次搜尋的計數，保留字典中的其他資料。"""
    if metrics is not None:
        metrics["expanded_count"] = 0


def _count_expanded(metrics):
    """記錄一次有效節點處理。"""
    if metrics is not None:
        metrics["expanded_count"] += 1


def bfs(maze, metrics=None):
    """使用 BFS 尋找起點到終點的最短路徑。

    找到時回傳包含起點與終點的座標列表；沒有路徑時回傳 None。
    由於每次移動的成本相同，BFS 第一次發現終點時得到的路徑必為最短。
    """
    _require_endpoints(maze)
    _initialize_metrics(metrics)

    frontier = Queue()
    frontier.enqueue(maze.start)

    # parent 同時作為 visited 使用；出現在 parent 中就代表已經發現過。
    parent = {maze.start: None}

    while not frontier.is_empty():
        current = frontier.dequeue()
        _count_expanded(metrics)

        if current == maze.target:
            return reconstruct_path(parent, maze.start, maze.target)

        for neighbor in maze.neighbors(current):
            if neighbor in parent:
                continue

            parent[neighbor] = current
            frontier.enqueue(neighbor)

    return None


def dfs(maze, metrics=None):
    """使用 DFS 尋找一條可行路徑，找到時回傳座標列表。"""
    _require_endpoints(maze)
    _initialize_metrics(metrics)

    frontier = Stack()
    frontier.push(maze.start)
    parent = {maze.start: None}

    while not frontier.is_empty():
        current = frontier.pop()
        _count_expanded(metrics)

        if current == maze.target:
            return reconstruct_path(parent, maze.start, maze.target)

        # Stack 是 LIFO，因此反向放入，實際拜訪順序仍維持上、右、下、左。
        for neighbor in reversed(maze.neighbors(current)):
            if neighbor in parent:
                continue

            parent[neighbor] = current
            frontier.push(neighbor)

    return None


def greedy_best_first(maze, metrics=None):
    """使用 Greedy Best-First Search 尋找一條可行路徑。

    優先選擇 Manhattan distance 最接近終點的格子，不保證路徑最短。
    """
    _require_endpoints(maze)
    _initialize_metrics(metrics)

    frontier = MinHeap()
    frontier.push(manhattan_distance(maze.start, maze.target), maze.start)
    parent = {maze.start: None}

    while not frontier.is_empty():
        _, current = frontier.pop_min()
        _count_expanded(metrics)

        if current == maze.target:
            return reconstruct_path(parent, maze.start, maze.target)

        for neighbor in maze.neighbors(current):
            if neighbor in parent:
                continue

            parent[neighbor] = current
            priority = manhattan_distance(neighbor, maze.target)
            frontier.push(priority, neighbor)

    return None


def a_star(maze, metrics=None):
    """使用 A* Search 尋找最短路徑。

    每一步成本為 1，啟發值使用 Manhattan distance，因此 priority 為
    ``目前成本 g + 預估剩餘成本 h``。
    """
    _require_endpoints(maze)
    _initialize_metrics(metrics)

    frontier = MinHeap()
    start_cost = 0
    start_priority = manhattan_distance(maze.start, maze.target)
    frontier.push(start_priority, (maze.start, start_cost))

    parent = {maze.start: None}
    cost = {maze.start: start_cost}

    while not frontier.is_empty():
        _, (current, current_cost) = frontier.pop_min()

        # 同一格可能以較高成本先加入 MinHeap；若後來找到更短路徑，
        # 舊項目仍在 heap 中，取出時直接略過。
        if current_cost != cost.get(current):
            continue

        _count_expanded(metrics)

        if current == maze.target:
            return reconstruct_path(parent, maze.start, maze.target)

        for neighbor in maze.neighbors(current):
            new_cost = current_cost + 1

            if neighbor in cost and new_cost >= cost[neighbor]:
                continue

            cost[neighbor] = new_cost
            parent[neighbor] = current
            priority = new_cost + manhattan_distance(neighbor, maze.target)
            frontier.push(priority, (neighbor, new_cost))

    return None
