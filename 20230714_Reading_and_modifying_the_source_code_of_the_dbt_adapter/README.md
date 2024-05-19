## 預想的大綱

- ****[Reading and modifying the source code of the dbt adapter](https://volunteer.coscup.org/schedule/2023/track/286e3/%E5%B8%B6%E6%82%A8%E8%AE%80%E6%BA%90%E7%A2%BC#HL88HZ)****
- 什麼是 dbt
- piperider → code review → data pipeline
- 讀與修改程式碼需要哪些技能？
  - 基礎 Python 語法
- 什麼是 dbt-adapter
  - 動機：這樣跑下去會花多少錢？
  - 怎麼計算它花了多少？
  - 動手修改它
  - ~~整合成 dbt-adapter~~ (時間肯定不夠的)

***

*以下為原始 idea 的文字稿*

***

> 待改寫成 Reading and modifying the source code of the dbt adapter 的投影片



## 突發奇想

事情是這樣的，前陣子開始學習 dbt (data build tool) 時，跟著入門教學，設定好 BigQuery 連線並執行完第 1 個專案後，開始好奇有沒有辦法知道執行一回的成本呢？想知道成本有哪些方法？最簡單的就是先放個幾天，然後回 Google Cloud 上看帳單資料就會知道了。

可是，我只是單人在實驗使用，如果是一個團隊，多個使用者的情況。要怎麼知道不同人的使用成本呢？這件事引發了我的好奇。

依據 <https://cloud.google.com/bigquery/docs/estimate-costs> 文件標示的，當我們在 BigQuery 的操作介面上敲上想要下的 Query 時，它會有個資料用量的預估：

![](images/B1PTxsaYn.png)

這功能是怎麼做到的呢？其實 BigQuery 有提供 `--dry-run` 的選項，當用上它時會進行 Query 資料用量估算，寫法如下面範例所示：

```bash
from google.cloud import bigquery

client = bigquery.Client()

# Set your query string
query_string = "SELECT COUNT(*) FROM my_dataset.my_table"

# Configure the query job
job_config = bigquery.QueryJobConfig(dry_run=True)

# Run the query job
query_job = client.query(query_string, job_config=job_config)

# Print the estimated bytes processed by the query
print(f"Estimated bytes processed: {query_job.total_bytes_processed}")
```

Query 的價格是總使用量加總而來的，所以我們只要能加總執行一次 `dbt build` 所下的 Query 總量，就可以用它來比較不同工作之間的成本囉！

## 基本思路

<https://github.com/dbt-labs/dbt-bigquery>

我們知道 dbt 透過 `dbt-bigquery` adapter 的能力與 BigQuery 溝通，那只要我們能找到它下 Query 的地方，再多下一組 Query 並帶著 `dry_run=True` 的參數，取得資料用量的結果就行了。

不過，再回頭看一下 dbt 的 message，可以發現一般的 Query 會附的資料用量它已經列出來了，那麼我們其實只需要吧這些資訊匯整起來就行了囉！

![](images/S1_CgsTFh.png)

## 徒手開挖

dbt-bigquery 對我來說是個新的專案，但沒有太多的擔心，儘管專案是陌生的，但程式語言的語法本身是個相當穩定的存在，特別是具有 identify 性質的 `package` 或 `module` 撇開在 Python 中特殊的意義，它們是不會被改變的**字串**。

在任何追 bug 或讀源始碼的活動來說，沒有比有「字串」這般穩定的存在更可靠的依賴。依據上述的範例程式，我們知道要使用 BigQuery 的起手式為：

```bash
from google.cloud import bigquery

client = bigquery.Client()
```

儘管在不同的專案，可能被寫作不同的用法，但脫離不了這些「字串」。試著直接在 GitHub 上搜尋： `bigquery.Client`

![](images/S1OResTF2.png)

除了測試程式的部分，只剩下 `connections.py` 有建立 Client 的痕跡了，那麼接著我們來查一下它何時會呼叫到如同範例中的 `query` 呢？

```bash
# Run the query job
query_job = client.query(query_string, job_config=job_config)
```

![](images/ByORloTYh.png)

在 `connections.py` 內，Client 建立後被指派給了 `handle` 變數。因此，我們應該期待查詢的寫法，可能出現新的變型：

```bash
query_job = client.query(query_string, job_config=job_config)
query_job = handle.query(query_string, job_config=job_config)
```

分別在 GitHub 上搜尋，最後確認了依然是 `client.query` 的型式：

![](images/SkmFZsath.png)

## 加點髒東西

由於，我們只是想要快速地驗證想法，我們先不管後續維護的問題，直接修改安裝好的 `dbt-bigquery` 函式庫即可。目標明顯是修改 `_query_and_results` 方法。

有了明確的目標後，先別急著飛撲上去！讓我們先確定沒有弄錯對象：

```diff
diff --git a/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py b/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
index a561eb5..9934a98 100644
--- a/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
+++ b/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
@@ -648,6 +648,7 @@ class BigQueryConnectionManager(BaseConnectionManager):
         """Query the client and wait for results."""
         # Cannot reuse job_config if destination is set and ddl is used
         job_config = google.cloud.bigquery.QueryJobConfig(**job_params)
+        print(sql)
         query_job = client.query(query=sql, job_config=job_config, timeout=job_creation_timeout)
         iterator = query_job.result(timeout=job_execution_timeout)
```

簡單地，把要執行的 sql 印出來，確定我們在執行 `dbt` 時，真的會經過段 code。在加料後的程式裡，我們可以看到多出了不少 sql 查詢：

![](images/BJXt-iatn.png)

透過 `執行期` 的行為確認找到了最後下 Query 的發生地，那我們往上由尋找可以發現 `execute` 最後回應的 `BigQueryAdapterResponse` 就有我們需要的內容：

```python
def execute(
        self, sql, auto_begin=False, fetch=None
    ) -> Tuple[BigQueryAdapterResponse, agate.Table]:
        sql = self._add_query_comment(sql)
        # auto_begin is ignored on bigquery, and only included for consistency
        query_job, iterator = self.raw_execute(sql, fetch=fetch)

    # ... skipped ...
    return ....
```

```python
@dataclass
class BigQueryAdapterResponse(AdapterResponse):
    bytes_processed: Optional[int] = None
    bytes_billed: Optional[int] = None
    location: Optional[str] = None
    project_id: Optional[str] = None
    job_id: Optional[str] = None
    slot_ms: Optional[int] = None
```

`BigQueryAdapterResponse` 是個簡單的 data class，只要我們將一次 dbt 執行會產生的所有 response 內的數值都記錄起來，就算是完成目標了。以下是經過我們簡單修改後取得的資料：

```json
[
  {
    "dbt_project_name": "jaffle_shop",
    "bytes_processed": 0,
    "bytes_billed": 0,
    "location": "US",
    "project_id": "infuseai-dev",
    "job_id": "5455499f-88a9-40ee-bdbe-5f88b6e15968",
    "slot_ms": 0,
    "message": "CREATE VIEW (0 processed)",
    "service_account_email": "alan-dbt-lab@infuseai-dev.iam.gserviceaccount.com",
    "current_user": "qrtt1"
  },
  {
    "dbt_project_name": "jaffle_shop",
    "bytes_processed": 0,
    "bytes_billed": 0,
    "location": "US",
    "project_id": "infuseai-dev",
    "job_id": "1032dbc3-6a08-4bbb-9a82-ae3fd47db9f8",
    "slot_ms": 0,
    "message": "CREATE VIEW (0 processed)",
    "service_account_email": "alan-dbt-lab@infuseai-dev.iam.gserviceaccount.com",
    "current_user": "qrtt1"
  },
  {
    "dbt_project_name": "jaffle_shop",
    "bytes_processed": 6170,
    "bytes_billed": 31457280,
    "location": "US",
    "project_id": "infuseai-dev",
    "job_id": "f5c2554d-ff65-4ac7-bd0e-6e2f25be21b2",
    "slot_ms": 22642,
    "message": "CREATE TABLE (100.0 rows, 6.0 KiB processed)",
    "service_account_email": "alan-dbt-lab@infuseai-dev.iam.gserviceaccount.com",
    "current_user": "qrtt1"
  },
  {
    "dbt_project_name": "jaffle_shop",
    "bytes_processed": 6660,
    "bytes_billed": 20971520,
    "location": "US",
    "project_id": "infuseai-dev",
    "job_id": "5dad33e7-6fe8-49c0-b25f-059c4a8c0517",
    "slot_ms": 12159,
    "message": "CREATE TABLE (99.0 rows, 6.5 KiB processed)",
    "service_account_email": "alan-dbt-lab@infuseai-dev.iam.gserviceaccount.com",
    "current_user": "qrtt1"
  }
]
```

## 中間產物檢視

目前概念驗證的部分算是完成了，但是跟最初的動機有一點不同。最初是以「預估」的角度來查資料，但實際上我們不打算變更 dbt 既有的行為，所以查詢(Query) 是必然會發生的，在追原始碼的過程中，我們看到了更有用的資料 `bytes_billed`，舉其中一筆來看：

```json
{
  "dbt_project_name": "jaffle_shop",
  "bytes_processed": 6660,
  "bytes_billed": 20971520,
  "location": "US",
  "project_id": "infuseai-dev",
  "job_id": "5dad33e7-6fe8-49c0-b25f-059c4a8c0517",
  "slot_ms": 12159,
  "message": "CREATE TABLE (99.0 rows, 6.5 KiB processed)",
  "service_account_email": "alan-dbt-lab@infuseai-dev.iam.gserviceaccount.com",
  "current_user": "qrtt1"
}
```

你可以看到 `bytes_billed` 與 `bytes_processed` 的差距是相當大的。而 BigQuery 查詢的計價是每 TB 計費 5 美元，最小單位是 10 MB。儘管第 1 個 TB 是免費的，但只要用量足以累計到一個最小計費單位 10 MB 就是值得關注的。有了這樣的概念後，後續我們的目標就不在是「估預」，而是以「稽核」的想法來看它，特別是知道不同的團隊，不同的開發者，不同的專案下它的用量評估。

在完成 Proof of concept 後，就可以來開始思考怎麼讓它由動手修改的 `dbt-bigquery` 變成一個能正常使用的 dbt adapter 了。

<https://docs.getdbt.com/guides/dbt-ecosystem/adapter-development/3-building-a-new-adapter>

在 Adapter 的開發參考文件中，有提及許多要開發一個新的 Adapter 會用到的概念，但具體要去弄懂它，其實「追原始碼」回來搭文件說明才是最快的。

## 實作 dbt-adapter

> 這段 talk 中大概不會有，因為時間塞不下。有錄完整版時再講解吧！



> 實作參考 https://github.com/qrtt1/dbt-bqcost-adapter



- 利用 exception 觀察 dbt-core 的行為
- 試著把行為轉接至 dbt-bigquery
- 建立 `proxy` 與 monkey patch

### [參考資料] Patch 的部分

```python
diff --git a/lib/python3.10/site-packages/dbt/adapters/bigquery/__pycache__/connections.cpython-310.pyc b/lib/python3.10/site-packages/dbt/adapters/bigquery/__pycache__/connections.cpython-310.pyc
index 489b608..fe5bd74 100644
Binary files a/lib/python3.10/site-packages/dbt/adapters/bigquery/__pycache__/connections.cpython-310.pyc and b/lib/python3.10/site-packages/dbt/adapters/bigquery/__pycache__/connections.cpython-310.pyc differ
diff --git a/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py b/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
index a561eb5..79ba976 100644
--- a/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
+++ b/lib/python3.10/site-packages/dbt/adapters/bigquery/connections.py
@@ -457,7 +457,41 @@ class BigQueryConnectionManager(BaseConnectionManager):
         return query_job, iterator
 
     def execute(
-        self, sql, auto_begin=False, fetch=None
+            self, sql, auto_begin=False, fetch=None
+    ) -> Tuple[BigQueryAdapterResponse, agate.Table]:
+        response, table = self.origin_execute(sql, auto_begin, fetch)
+
+        import json
+        def to_dict(response: BigQueryAdapterResponse) -> dict:
+            return {
+                "dbt_project_name": self.profile.project_name,
+                "bytes_processed": response.bytes_processed,
+                "bytes_billed": response.bytes_billed,
+                "location": response.location,
+                "project_id": response.project_id,
+                "service_account_email": self.service_account_email,
+                "job_id": response.job_id,
+                "slot_ms": response.slot_ms,
+                "message": response._message
+            }
+
+        def dump_at_exit():
+            print(json.dumps(getattr(self, '_usage')))
+
+        if not hasattr(self, '_usage'):
+            # initial usage keeper
+            self._usage = []
+
+            import atexit
+            atexit.register(dump_at_exit)
+            self.service_account_email = self.get_thread_connection().handle.get_service_account_email()
+        else:
+            self._usage.append(to_dict(response))
+
+        return response, table
+
+    def origin_execute(
+            self, sql, auto_begin=False, fetch=None
     ) -> Tuple[BigQueryAdapterResponse, agate.Table]:
         sql = self._add_query_comment(sql)
         # auto_begin is ignored on bigquery, and only included for consistency
```

### [參考資料] 建立新 adapter

<https://docs.getdbt.com/guides/dbt-ecosystem/adapter-development/3-building-a-new-adapter#implementation-details>

```python
cookiecutter gh:dbt-labs/dbt-database-adapter-scaffold
```
