# Assignment 3 - Shortest Path in a Maze

這個程式使用稀疏格子資料、bitmask 牆壁，以及 DFS、BFS、Greedy
Best-First Search 和 A* 尋找迷宮路徑。

## 檔案結構

| 檔案 | 用途 |
|---|---|
| `data_structures.py` | 自製 linked-list Stack、Queue 與 MinHeap |
| `maze.py` | Cell、稀疏 Maze 與 bitmask 牆壁 |
| `maze_parser.py` | 將文字輸入解析成 Maze |
| `maze_generator.py` | 產生 Imperfect Maze 或含障礙的 Braid Maze |
| `search.py` | DFS、BFS、Greedy 與 A* |
| `maze_display.py` | 座標字串與文字矩陣輸出 |
| `maze_visualizer.py` | Matplotlib 靜態視覺化 |
| `benchmark.py` | 搜尋節點、執行時間與尖峰記憶體比較 |
| `experiment.py` | 多種尺寸與 seed 的批次實驗 |
| `plot_experiments.py` | 將 summary 畫成平均值與標準差比較圖 |
| `main.py` | 正式命令列入口 |

## 輸入格式

資料依用途分為以下目錄：

```text
inputs/
├── experiments/                 批次生成的實驗迷宮，依實驗 ID 分組
└── manual/                      手動輸入及單次生成的迷宮
outputs/
├── experiments/                 批次實驗 CSV 與 config，依實驗 ID 分組
├── charts/
│   ├── experiment__時間戳/      效能比較 PNG、SVG
│   └── report_figures/          報告用迷宮原圖及搜尋路徑圖
└── manual/                      手動執行的圖片或 benchmark CSV
```

`manual` 表示非批次實驗資料，也包含先前單次生成的迷宮。
手動指令仍使用明確路徑，請按下列範例指定分類資料夾。
`requirements.txt` 是套件清單，保留在專案根目錄。
命令中的相對路徑以目前工作目錄為準，請先切換至 `Assignment3`。
生成器與視覺化會自動建立輸出路徑的父資料夾。

```text
rows cols
<第 1 列的 column state 配對，以 0 結束>
...
<第 rows 列的 column state 配對，以 0 結束>
wall_count
row column U/R/D/L
...
```

每面單位牆只需輸入一次，解析器會同步更新相鄰格子的反方向。

## 產生迷宮

Imperfect Maze：

```powershell
python maze_generator.py imperfect 20 20 inputs/manual/imperfect.txt --loop-rate 0.15 --seed 42
```

Braid Maze with Obstacles：

```powershell
python maze_generator.py braid 20 20 inputs/manual/braid.txt --obstacle-rate 0.15 --braid-rate 1.0 --seed 42
```

## 搜尋迷宮

```powershell
python main.py inputs/manual/imperfect.txt dfs
python main.py inputs/manual/imperfect.txt bfs
python main.py inputs/manual/imperfect.txt greedy
python main.py inputs/manual/imperfect.txt astar
```

找到路徑時會輸出座標列表、移動步數與矩陣。沒有路徑時輸出
`沒有路徑`。

## 視覺化

使用 `--stats` 顯示實際取出並處理的搜尋節點數，包含起點與終點，
但不包含 A* 已失效的 heap 項目。無解時也會顯示計數。

```powershell
python main.py inputs/manual/imperfect.txt bfs --stats
```

搜尋函數也可直接接收選用的統計字典，回傳值仍為座標列表或 None：

```python
metrics = {}
path = bfs(maze, metrics=metrics)
print(metrics["expanded_count"])
```

安裝選用套件：

```powershell
python -m pip install -r requirements.txt
```

儲存圖片：

```powershell
python main.py inputs/manual/imperfect.txt bfs --image outputs/manual/bfs_result.png
```

顯示視窗並同時儲存：

```powershell
python main.py inputs/manual/braid.txt astar --show --image outputs/manual/astar_result.png
```

路徑長度定義為座標列表長度減一：

```python
path_length = len(path) - 1
```

## 效能比較

對同一個迷宮比較四種演算法。計時只包含搜尋，不包含讀檔、解析、
文字輸出或視覺化；每個演算法預設重複 20 次並顯示平均值與中位數。
尖峰記憶體以 `tracemalloc` 另外執行一次搜尋量測。

```powershell
python benchmark.py inputs/manual/imperfect.txt
```

指定重複次數並輸出 CSV：

```powershell
python benchmark.py inputs/manual/braid.txt --repeat 50 --csv outputs/manual/braid_benchmark.csv
```

## 批次實驗與命名

```powershell
python experiment.py --sizes 20 50 100 --seeds 0 1 2 3 4 --repeat 20
```

兩類迷宮均會生成，每次執行建立帶時間戳的獨立實驗目錄：
`inputs/experiments/experiment__時間戳/` 保存迷宮，
`outputs/experiments/experiment__時間戳/` 保存結果與設定。

檔名範例：

```text
maze__imperfect__r0020_c0020__loop0p15__seed0000.txt
maze__braid__r0020_c0020__obs0p15__braid1p0__seed0000.txt
maze__braid__r0020_c0020__obs0p15__braid1p0__seed0000__benchmark__repeat020.csv
```

`p` 代表小數點。圖片建議沿用迷宮檔案主名稱，加上演算法與 `path`，
例如 `maze__imperfect__r0020_c0020__loop0p15__seed0000__bfs__path.png`。
既有手動指定檔名的命令仍可使用，舊資料不會改名。

每次實驗保存 `__config.json`（參數、Python 與系統版本）、
`__results.csv`（逐迷宮逐演算法結果）與 `__summary.csv`
（同類型同尺寸跨 seed 的平均值與樣本標準差）。
時間單位為秒，記憶體單位為 bytes；記憶體量測為搜尋的 Python
配置尖峰，非整個程序的記憶體。各 seed 的計時與記憶體分開執行。
批次流程不會自動畫出所有迷宮圖片。

Braid 使用逐格加入障礙的方式，保留連通性與非端點格至少兩個
幾何鄰居。此方式在大型迷宮可能耗時，最壞情況約 O((rows*cols)^2)。
障礙數量為 round((rows*cols-2)*obstacle_rate)，若無法達到指定
數量會報錯，不會偷偷降低比例。生成方式已更新，因此相同 seed
的 Braid 結果可能不同於舊版。

## 設計與正確性說明

比較圖表使用方式：

```powershell
python plot_experiments.py outputs/experiments/experiment__20261012_225827_842042/experiment__20261012_225827_842042__summary.csv
```

每類迷宮產生路徑長度、展開節點數、時間、記憶體四張圖，各存 PNG
與 SVG。預設存入 `outputs/charts/實驗ID/`，可用 `--output-dir` 指定。
檔名包含實驗 ID、迷宮類型、指標與 `mean_sd`。誤差棒是跨 seed 的
樣本標準差，不是信賴區間。時間採每個 seed 的平均秒數再跨 seed
彙整，繪圖時轉為 ms；記憶體轉為 KiB。BFS 與 A* 路徑線可能重疊。

- 座標為 1-based `(row, column)`，格子狀態為 `0/x/s/t`。
  空白且無牆的格子不存入 `Maze.cells`；key 為座標，value 為 Cell。
- 牆壁使用 `UP=1, RIGHT=2, DOWN=4, LEFT=8`，新增或移除時同步兩側。
  邊界由範圍檢查處理，不儲存外框牆。請透過 Maze 方法修改資料。
- BFS 使用自製 Queue；DFS 使用自製 Stack；Greedy、A* 使用自製
  MinHeap。Heap 底層為 Python list，相同 priority 依插入順序取出。
- 搜尋回傳起點至終點的座標列表，無解回傳 None。BFS 和 A* 在本程式
  四方向、單位成本的條件下保證最短；DFS、Greedy 不保證最短。
- Manhattan distance 不會高估剩餘成本，且具有一致性。A* 以較小 g
  更新前驅，取出 heap 時略過舊成本項目。
- `expanded_count` 的實作定義為有效取出並處理的次數，包含終點檢查；
  不是僅計算真正列舉鄰居的格子數。
- Imperfect：先加滿內部牆，以 randomized DFS 建立 spanning tree，
  再拆除 `round(剩餘牆數 * loop_rate)` 面牆。拆牆保留連通性。
  比例為 0、尺寸過小或只有單列／單欄時，可能沒有環；不保證保留死路。
- Braid：非障礙區域先保持連通，再建立 spanning tree 並消除死路。
  起點和終點排除在死路消除之外。`braid_rate=1` 處理全部非端點死路；
  較小比例是部分編織。單列／單欄且無障礙時無法形成環。

令 V 為可通行格數、E 為通道數；四方向網格 E=O(V)。BFS、DFS 的
最壞搜尋時間為 O(V+E)、額外空間 O(V)。本程式 Greedy、A* 使用
二元 heap，在此網格與一致啟發函數條件下可用 O(V log V) 時間、
O(V) 空間描述最壞搜尋成本。路徑重建為 O(路徑格數)。
Maze 稀疏儲存為 O(k)，k 是非預設格數；牆壁密集時 k 可接近 rows*cols，
而且 Python dict/Cell 有物件成本，不能宣稱一定比完整矩陣省記憶體。

## 實驗解讀與報告收尾

預設實驗為兩類、三種尺寸、五個 seed，共 30 個迷宮、120 筆演算法
紀錄。每筆重複計時 20 次，另執行一次記憶體量測。計時包含選用節點
計數與路徑重建；不包含生成、解析、顯示。沒有暖機，演算法以固定順序
執行，系統負載可能影響結果。summary 的標準差是跨 seed 的樣本標準差，
不是同一迷宮 20 次計時的標準差。記憶體不包含事先建立的 Maze。

目前比較兩類時同時改變了通道結構與障礙，結果只能描述這兩種資料集，
不能把差異單獨歸因於環或障礙。固定角落端點也會影響啟發式搜尋表現。

提交前尚需完成：

- 選定同一次完整實驗的 config、results、summary，保留原始量測資料。
- 製作路徑長度、節點數、時間、記憶體圖表，標示單位與跨 seed 變異。
- 選兩類迷宮的代表性圖片及有解／無解／錯誤輸入輸出，附文字說明。
- 中文報告依序撰寫作者資訊、問題描述、程式設計與資料結構、主要程式、
  正確性與複雜度、執行結果、效能評估、結論、AI 使用聲明及參考來源。
- 問題描述以自己的文字撰寫，設計中採用 AI 協助的部分據實揭露。
- 使用 A4、至少 12 pt，附完整程式碼或附錄；提交前不需包含 __pycache__。

程式已可進入報告階段；搜尋動畫屬選用擴充，不影響目前核心交付。

