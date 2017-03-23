## 安裝 Spark 與 Connector


1. 下載 Spark
1. 下載對應版本的 [gcs connector](https://cloud.google.com/hadoop/google-cloud-storage-connector)。
2. 放在 spark 的 libs 資料夾
  ```
qrtt1@bot:~/poc$ ls spark-2.1.0-bin-hadoop2.7/jars/ | grep gcs
gcs-connector-latest-hadoop2.jar
  ```


## 啟動 Spark 

在 gce 開機時授權 instance 可以使用 gcs 或透過 OAuth 登入來取得權限。在 pyspark 後，要先設 project-id

```py
sc._jsc.hadoopConfiguration().set("fs.gs.project.id", "sao-c8763")
```

```py
sc.textFile("gs://myproject/weblogs/2017/03/*").map( lambda line : (line.split("\t")[1], 1)).reduceByKey(lambda a, b : a + b).collect()
```
