"""作業會使用的自製資料結構：Stack、Queue 與 MinHeap。"""


class Node:
    """節點儲存一個值，以及下一個節點的參照。"""

    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node


class Stack:
    """後進先出：在 head 加入及取出。"""

    def __init__(self):
        self.head = None
        self._size = 0

    def push(self, item):
        # 新節點接在原本的頭節點前面。
        self.head = Node(item, self.head)
        self._size += 1

    def pop(self):
        if self.is_empty():
            raise IndexError("無法從空 Stack 取出元素")
        value = self.head.value
        self.head = self.head.next
        self._size -= 1
        return value

    def peek(self):
        if self.is_empty():
            raise IndexError("無法查看空 Stack 的元素")
        return self.head.value

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def clear(self):
        self.head = None
        self._size = 0


class Queue:
    """先進先出：在 tail 加入，在 head 取出。"""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def enqueue(self, item):
        node = Node(item)
        if self.is_empty():
            self.head = node
        else:
            self.tail.next = node
        self.tail = node
        self._size += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("無法從空 Queue 取出元素")
        value = self.head.value
        self.head = self.head.next
        self._size -= 1
        # 最後一個節點取出後，尾指標也必須清空。
        if self.is_empty():
            self.tail = None
        return value

    def peek(self):
        if self.is_empty():
            raise IndexError("無法查看空 Queue 的元素")
        return self.head.value

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def clear(self):
        self.head = None
        self.tail = None
        self._size = 0


class MinHeap:
    """以動態陣列實作的最小堆積，不使用 Python 的 heapq。

    priority 越小的項目越早取出；priority 相同時，依插入順序取出，
    因此 value 本身不需要支援大小比較。
    """

    def __init__(self):
        self._data = []
        self._size = 0
        self._next_order = 0

    def push(self, priority, value):
        """加入一個 (priority, value)，時間複雜度為 O(log n)。"""
        entry = (priority, self._next_order, value)
        self._next_order += 1
        self._data.append(entry)
        self._size += 1
        self._sift_up(self._size - 1)

    def pop_min(self):
        """移除並回傳最小的 (priority, value)，時間複雜度為 O(log n)。"""
        if self.is_empty():
            raise IndexError("無法從空 MinHeap 取出元素")

        minimum = self._data[0]
        last = self._data.pop()
        self._size -= 1

        if not self.is_empty():
            self._data[0] = last
            self._sift_down(0)

        return minimum[0], minimum[2]

    def peek_min(self):
        """查看但不移除最小的 (priority, value)。"""
        if self.is_empty():
            raise IndexError("無法查看空 MinHeap 的元素")
        minimum = self._data[0]
        return minimum[0], minimum[2]

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def clear(self):
        self._data.clear()
        self._size = 0
        self._next_order = 0

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._data[parent][:2] <= self._data[index][:2]:
                break
            self._swap(parent, index)
            index = parent

    def _sift_down(self, index):
        while True:
            left = 2 * index + 1
            right = left + 1
            smallest = index

            if (
                left < self._size
                and self._data[left][:2] < self._data[smallest][:2]
            ):
                smallest = left
            if (
                right < self._size
                and self._data[right][:2] < self._data[smallest][:2]
            ):
                smallest = right

            if smallest == index:
                return

            self._swap(index, smallest)
            index = smallest

    def _swap(self, first, second):
        self._data[first], self._data[second] = (
            self._data[second],
            self._data[first],
        )
