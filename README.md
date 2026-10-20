# Maze Pathfinding

使用 Python 實作迷宮生成、四種路徑搜尋、視覺化與效能比較。支援格子障礙及相鄰格之間的牆壁，使用稀疏字典與方向 bitmask 表示迷宮。

## 功能

- 自行實作 linked-list Stack、Queue 與陣列式 MinHeap。
- DFS、BFS、Greedy Best-First Search、A*。
- Imperfect Maze 與含障礙的 Braid Maze 生成，支援固定 seed。
- 座標路徑、文字矩陣，以及 PNG／SVG／PDF 靜態圖片。
- 展開節點數、搜尋時間、Python 尖峰配置記憶體比較。
- 多尺寸、多 seed 批次實驗、CSV 彙整與比較圖表。

| 命令參數 | 搜尋方法 | 是否保證最短路徑 |
|---|---|---|
| `dfs` | 深度優先，使用自製 Stack | 否 |
| `bfs` | 廣度優先，使用自製 Queue | 是 |
| `greedy` | 以 Manhattan distance 排序 | 否 |
| `astar` | 以目前成本 + Manhattan distance 排序 | 是 |

最短路徑保證適用於本專案的上下左右、每步成本為 1 的迷宮。

## 安裝與快速開始

需要 Python 3；正式實驗使用 Python 3.14.7。請先登入有權存取此私人 repository 的 GitHub 帳號，再下載或 clone：

```powershell
git clone https://github.com/Macause/maze-pathfinding.git
cd maze-pathfinding
python -m pip install -r requirements.txt
```

Matplotlib 僅供圖片與圖表使用；文字搜尋、生成器及 benchmark 使用 Python 標準函式庫。Windows 也可將下列命令的 `python` 改為 `py`。

先生成迷宮，再搜尋並輸出圖片：

```powershell
python maze_generator.py imperfect 20 20 inputs/manual/imperfect.txt --loop-rate 0.15 --seed 42
python main.py inputs/manual/imperfect.txt bfs --stats --image outputs/manual/imperfect__bfs__path.png
```

輸入資料、實驗結果、圖片和報告未納入 repository；上述生成步驟會建立所需資料。生成器、CSV 與圖片輸出會自動建立父資料夾。

## 搜尋與圖片

```powershell
python main.py inputs/manual/imperfect.txt dfs
python main.py inputs/manual/imperfect.txt bfs
python main.py inputs/manual/imperfect.txt greedy
python main.py inputs/manual/imperfect.txt astar --stats
python main.py inputs/manual/imperfect.txt astar --show --image outputs/manual/imperfect__astar__path.png
```

- `--stats`：顯示有效取出並處理的節點數，包含起點與終點檢查，排除 A* 的失效 heap 項目。
- `--image FILE`：依副檔名輸出 PNG、SVG 或 PDF。
- `--show`：開啟 Matplotlib 視窗；只儲存圖片時不需要此選項。

找到時輸出座標字串、移動步數與矩陣，無解時顯示「沒有路徑」。圖片中綠色 S 為起點、紅色 T 為終點、深灰格為障礙、黑線為牆、藍線為路徑。

`main.py` 結束碼：0 表示找到路徑、1 表示無解、2 表示輸入或檔案等錯誤。

## 輸入格式

座標為 1-based `(row, column)`。第一行是列數與欄數，接著每列描述非空白格，最後讀取單位牆：

```text
rows cols
<第 1 列的 column state 配對，以 0 結束>
...
<第 rows 列的 column state 配對，以 0 結束>
wall_count
row column U/R/D/L
...
```

- 未列出的格子預設空白；狀態配對使用 `x`（障礙）、`s`（起點）、`t`（終點）。
- 恰好一個起點、一個終點；每列以 `0` 結束。
- 牆方向：U 上、R 右、D 下、L 左；每面牆只需描述一次，程式同步更新兩側。
- 無牆時仍須輸入牆數 `0`。不接受朝迷宮外側的牆；長牆拆成多面單位牆。
- 這是單位牆格式，不直接解析幾何線段端點。

例如，將以下文字存成 UTF-8 檔案：

```text
2 3
1 s 0
3 t 0
1
1 1 R
```

起點右側被牆阻擋，BFS 可得到：

```text
(1,1)(2,1)(2,2)(2,3)
路徑長度：3

s 0 0
1 2 t
```

## 迷宮生成

Imperfect Maze：先加滿內部牆，randomized DFS 拆牆建立連通樹，再拆除部分剩餘牆形成環。

```powershell
python maze_generator.py imperfect 20 20 inputs/manual/imperfect.txt --loop-rate 0.15 --seed 42
```

Braid with Obstacles：逐格選擇障礙並維持非障礙區域連通，建立連通樹後消除非端點死路。

```powershell
python maze_generator.py braid 20 20 inputs/manual/braid.txt --obstacle-rate 0.15 --braid-rate 1.0 --seed 42
```

| 參數 | 意義 |
|---|---|
| `--seed` | 固定亂數種子，同版本與相同參數可重現 |
| `--loop-rate` | Imperfect 額外拆除剩餘牆壁的比例 |
| `--obstacle-rate` | Braid 障礙數為 round((rows × cols − 2) × rate) |
| `--braid-rate` | 處理非起終點死路的比例；1 表示全部處理 |

起點固定在左上角，終點固定在右下角。成功生成時兩者連通。小尺寸、單列／單欄或拆牆數為零時，Imperfect 可能仍無環；Braid 的起終點可保留死路。無法滿足障礙配置時會報錯，不會降低指定比例。

## 效能比較

```powershell
python benchmark.py inputs/manual/imperfect.txt --repeat 20 --csv outputs/manual/imperfect__benchmark__repeat020.csv
```

比較四種演算法的路徑長度、節點數、平均／中位時間及尖峰配置記憶體。

- 時間使用 `perf_counter()`，包含搜尋、節點計數與路徑重建，不含生成、解析、列印與繪圖。
- 記憶體使用 `tracemalloc` 另執行一次，不包含事先建立的 Maze，也不是整個程序的 RAM。
- 終端時間單位為 ms、記憶體為 KiB；CSV 使用秒與 bytes。
- 無解時路徑長度為空值，仍保留節點與資源統計。

## 批次實驗與比較圖

先以小規模確認流程：

```powershell
python experiment.py --sizes 20 --seeds 0 1 --repeat 5
```

完整預設設定：

```powershell
python experiment.py --sizes 20 50 100 --seeds 0 1 2 3 4 --repeat 20
```

兩類迷宮共 30 個案例，四種演算法共 120 筆紀錄。每次執行建立獨立實驗 ID，保存：

- `__config.json`：參數、Python 與系統版本。
- `__results.csv`：逐迷宮逐演算法的量測。
- `__summary.csv`：同類型、同尺寸的跨 seed 平均與樣本標準差。
- 每個迷宮對應的 benchmark CSV。

檔名範例：

```text
maze__imperfect__r0020_c0020__loop0p15__seed0000.txt
maze__braid__r0020_c0020__obs0p15__braid1p0__seed0000.txt
maze__braid__r0020_c0020__obs0p15__braid1p0__seed0000__benchmark__repeat020.csv
```

`p` 代表小數點。使用實際生成的 summary 路徑畫圖，請替換下列 `<run_id>`：

```powershell
python plot_experiments.py "outputs/experiments/<run_id>/<run_id>__summary.csv"
```

預設輸出至 `outputs/charts/<run_id>/`，每類四張圖，各提供 PNG、SVG。可用 `--output-dir` 指定目錄。誤差棒為跨 seed 的樣本標準差，並非信賴區間。

## 專案結構

| 檔案 | 職責 |
|---|---|
| `data_structures.py` | Node、Stack、Queue、穩定 MinHeap |
| `maze.py` | Cell、稀疏 Maze、雙向牆與合法鄰居 |
| `maze_parser.py` | UTF-8 輸入與格式驗證 |
| `search.py` | DFS、BFS、Greedy、A*、前驅重建及選用統計 |
| `maze_generator.py` | 兩類迷宮生成與文字序列化 |
| `maze_display.py` | 座標字串與文字矩陣 |
| `maze_visualizer.py` | 靜態迷宮及路徑繪圖 |
| `main.py` | 單次搜尋命令列入口 |
| `benchmark.py` | 單一迷宮效能比較 |
| `experiment.py` | 批次生成、量測與彙整 |
| `plot_experiments.py` | 實驗比較圖 |

執行後的資料目錄（由 `.gitignore` 排除）：

```text
inputs/
├── experiments/<run_id>/    批次生成的迷宮
└── manual/                  手動輸入或單次生成的迷宮
outputs/
├── experiments/<run_id>/    批次 CSV 與設定
├── charts/<run_id>/         效能比較圖
└── manual/                  手動執行的圖片與 CSV
```

一般命令的相對路徑以目前工作目錄為準；批次實驗及預設圖表目錄則相對於程式所在目錄。

## 程式介面

```python
from maze_parser import parse_maze_file
from search import bfs

maze = parse_maze_file("inputs/manual/imperfect.txt")
metrics = {}
path = bfs(maze, metrics=metrics)

if path is not None:
    print("步數：", len(path) - 1)
print("處理節點：", metrics["expanded_count"])
```

DFS、Greedy 與 A* 同樣回傳座標列表或 `None`，也支援選用的 `metrics`。未傳入字典時可直接使用 `bfs(maze)`。

## 設計與限制

- bitmask 使用 UP=1、RIGHT=2、DOWN=4、LEFT=8；請透過 Maze 方法修改牆壁以維持雙向一致。
- MinHeap 的上浮／下沉自行實作，Python list 僅作儲存，不使用 `heapq`。
- 稀疏字典只存非預設格，但牆密集時仍可占用接近整張網格的空間。
- Braid 的逐格連通檢查最壞約為 O((rows × cols)²)，大型迷宮生成可能較慢。
- Benchmark 無暖機且依固定順序執行，時間可能受背景負載影響。
- 兩類迷宮同時改變通道與障礙，不能將效能差異單獨歸因於某一項因素。
