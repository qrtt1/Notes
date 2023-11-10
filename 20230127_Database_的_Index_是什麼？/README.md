# Database 的 Index 是什麼？

Index 索引，它的用途就如同一些書籍的最後幾頁，標示了書中所提到的「詞彙」對應的頁數。下圖為 Thinking in Java 2/e 繁體中文版的索引頁：

<img src="https://i.imgur.com/XDHll8k.png" width="400"/>

而 Database 的 Index 也是相似的功能，只是它會針對 Key 或是獨立建立的 Index 來當成索引。以上圖為例，若是我想要尋找 `abstract` 相關的概念，我可以在圖上的這些頁數中找到：

<img src="https://i.imgur.com/2dKmlJQ.png" width="400"/>

試想一種情況，若是沒有 `index` 該如何找到它們呢？簡單暴力的方法

> 每一頁都去翻開來看，並且記錄下它們的頁數。



## 資料庫如何查找資料？

先不論特定廠牌或 engine 的實作，資料庫查找資料的原則就是：

- 如果「條件允許」且「有 index」，優先使用 index 取得資料
- 如果沒有能使用 index 的情況，那就每一筆都查看看

這裡要注意，使用 index 的情境是：

- 你想查的資料有對應的 index
- 你下的 QUERY 子句，符合使用 index 的條件

相反的情況，就是無法使用 index 的情境。這情境有個專有名詞 `full table scan`，也就是前面提到的，書沒有替讀者準備索引頁，所以讀者若想要知道哪些字詞的位置，只好每一頁翻開來看。

## 用程式碼來舉個例子

想像一下你有一個 `table` 裡面有 3 筆資料，每一筆資料有 2 個欄位，分別是 id 與 name。如果，我想找是不是 `name` 有 cat 的資料，它可以寫成這個樣子：

```python
table = [dict(id=1, name="cat"), dict(id=2, name="dog"), dict(id=3, name="bird")]

def find_by_name(name: str):
    result = []
    for x in table:
        if x['name'] == name:
            result.append(x)
    return result

if __name__ == '__main__':
    print(find_by_name("cat"))
    print(find_by_name("what?"))
```

由於，我們對於這個 table 沒有建立索引，所以它只好做 `full table scan` 囉！若是分析它的時間複雜度，那就是 `O(n)`。輸出的結果為：

```json
[{'id': 1, 'name': 'cat'}]
[]
```

現在開始想像，你的 `table` 其實不是只有 3 筆資料，而是百萬筆的時候，那麼 `O(n)` 就會因為 n 變大而讓查詢變久了。想要讓它變快，就是得靠建立 index。那麼 Database 有提供 `建立 index` 的功能，常見的 index 為 b-tree 與 hash。我們示範概念的話，用 hash 來實作會容易些，畢竟 b-tree 寫起來挺麻煩的。

我們簡單用個 dictionary 來存 index，而它的 `key` 就是 `name` 欄位的值，它的 `value` 用個 list 來存放，因為有機會同一個 key 有多筆資料：

```python
index_on_name = dict()

def build_index_on_name():
    for x in table:
        if x['name'] not in index_on_name:
            index_on_name[x['name']] = []
        index_on_name[x['name']].append(x)
```

我們可以簡單把它印出來感受一下：

```python
build_index_on_name()
print(index_on_name)
```

輸出結果為：

```python
{'cat': [{'id': 1, 'name': 'cat'}], 'dog': [{'id': 2, 'name': 'dog'}], 'bird': [{'id': 3, 'name': 'bird'}]}
```

接著，我們可以來實作 `使用 index` 的查詢了，用它的查詢結果會是與 full table scan 一致的，但查詢的效率轉成了 `O(1)`：

```python
def find_by_name_with_index(name: str):
    return index_on_name.get(name, [])
```

## Rebuild Index 與 Incremental build Index

我們重新看一下 `build_index_on_name` 的實作：

```python
index_on_name = dict()

def build_index_on_name():
    for x in table:
        if x['name'] not in index_on_name:
            index_on_name[x['name']] = []
        index_on_name[x['name']].append(x)
```

你會想要問，它明明也是 `O(n)` 為什麼能加速呢？首先，這是建立一個 `全新的` Index 的流程，建好一次後，後續可以用上 index 的查詢就是 `O(1)` 囉！那麼不是全新的建立 Index 的流程，會是怎麼樣呢？我們來改寫一下程式：

```python
table = []
index_on_name = dict()

def find_by_name(name: str):
    result = []
    for x in table:
        if x['name'] == name:
            result.append(x)
    return result

def find_by_name_with_index(name: str):
    return index_on_name.get(name, [])

def add_data(data: dict):
    table.append(data)

    # update index
    name = data['name']
    if name not in index_on_name:
        index_on_name[name] = []
    index_on_name[name].append(data)

if __name__ == '__main__':
    add_data(dict(id=1, name="cat"))
    add_data(dict(id=2, name="dog"))
    add_data(dict(id=3, name="bird"))

    print(find_by_name("cat"))
    print(find_by_name("what?"))

    print(find_by_name_with_index("cat"))
    print(find_by_name_with_index("what?"))
```

在這程式中，你會發現多出了 `add_data`，可以理解就是平時我們針 table 做 `insert` 的動作，而在增加資料的同時，它會去 `update index`。除非，我們想要重建，或第一次針對某些條件建立 index，才會呼叫到 `build_index_on_name` 函式了。

這裡有個得提醒的要點是，index 包含在 `insert` 的流程中，它會影響寫入的效率，所以「適量」的 index 才是好的，示意的程式如下。當你建立太多的 index 時，你新增資料不可避免地比原先慢：

```python
def add_data(data: dict):
    table.append(data)

    # update index 1
    # update index 2
    # update index 3
    # update index 4
    # update index 5
    # update index ...
```

同理，不是只有 `insert` 會需要更新 index，`update` 與 `delete` 也都有更新 index 的流程。

## Index 的適用條件

在最開始有提到，要在查詢用上 index 得條件適當才行，以目前的例子來說都是針對 `name` 這個欄位建立的 index，如果欄位擴充了，還多了電話：

```python
def find_by_name_with_index(name: str):
    return index_on_name.get(name, [])
```

由於，我們並沒有事先建好 `name` 與 `phone` 的組合，那麼資料庫會使用最原始的 full table scan：

```python
def find_by_name_and_phone_with_index(name: str, phone: str):
    return index_on_???????.get(name, [])
```

而 Index 的適用條件，要先過 `WHERE` 子句這一關，也就是：

```sql
WHERE name="cat" AND phone="9527"
```

當你的 QUERY 吃不到 index 時，通常可以靠資料庫的分析工具得到印證：

> MySQL 與 Postgres 都有的 EXPLAIN 查詢



對應的解決有 2 個選擇：

- 建新的 index，但記得考慮 `資料異動` 時對效能的影響
- 利用既有的 index 查出資料，再縮小範圍

舉例來說，目前這句因為有針對 `name` 的 index 而能快速找到結果，而且是 `O(1)`：

```sql
SELECT * FROM table WHERE name="cat"
```

那麼，只要先利用現用 index 的查詢 `O(1)` 快速縮小範圍，讓後續過濾資料 `O(n)` 的 n 變小就行了 (示範概念，我沒有驗過 SQL 能不能動)：

```sql
SELECT * FROM (SELECT * FROM table WHERE name="cat") a WHERE a.phone="9527"
```

PS. 要提醒這裡的 `O(1)` 只是舉例，如果是 [B-tree](https://en.wikipedia.org/wiki/B-tree) 那會是 `O(log n)`，要看選用的 index 類型而定，常理來說都比 full table scan 有效率。

## 相關練習

1. 真的使用 Database 去建立資料
2. 將 Python 的部分，改寫成自己喜歡的語言
3. 理解常用資料庫對`full table scan` 的描述，與 `沒有吃到 index` 的常見寫法
