# CQRS & Event Sourcing References

* [Apache Ignite](https://ignite.apache.org/)
* [Apache Kafka](https://kafka.apache.org/)
* [KeyCloak](http://www.keycloak.org/)
* [Cassandra](http://cassandra.apache.org/)
* [kubernetes](https://kubernetes.io/) Docker cluster

## 相關概念

* [The LMAX Architecture](https://martinfowler.com/articles/lmax.html)
* [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)

## 學習材料

### Event Sourcing

* [Building Scalable Applications Using Event Sourcing and CQRS](https://medium.com/technology-learning/event-sourcing-and-cqrs-a-look-at-kafka-e0c1b90d17d8)
* [Event Sourcing In practice](http://ookami86.github.io/event-sourcing-in-practice/index.html)
* [Event sourcing, CQRS, stream processing and Apache Kafka: What’s the connection?](https://www.confluent.io/blog/event-sourcing-cqrs-stream-processing-apache-kafka-whats-connection/)


### Apache Ignite


#### Apache Ignite™ Coding Examples - Part 1

https://www.youtube.com/watch?v=4CQalha3MyY

有安裝與寫 code 比較有趣一點

#### Introduction to Apache Ignite (TM) (incubating) by Nikita Ivanov of GridGain

(真的很閒再看完它，其實挺無聊的)

* 引言，講資料成長與 RAM 價格遞減帶來的 In Memory Data Grid 使用動機 https://youtu.be/FFlwdRp1jnc?t=2m44s
* 簡介 Data Fabric，它是個 middleware 的概念，放在 application 層與 database 層之間 https://youtu.be/FFlwdRp1jnc?t=14m25s
* Data Fabric 不是只有 Cache 還有許多其它功能，大致上宣傳一下 https://youtu.be/FFlwdRp1jnc?t=17m11s
* Clustering 與 Deployment，大部分在講古時後其他軟體 deploy 的不好經驗，然後說 ignite 的 deploy 很簡單 https://youtu.be/FFlwdRp1jnc?t=18m47s
* In Memory Computing Grid，先談比較少聽眾注意到的 computing 部分，這邊有較多提問。還有人問與 Spark 的比較，不過 Spark 主要不是 storage 功能。 https://youtu.be/FFlwdRp1jnc?t=25m18s
* In Memory Data Grid https://youtu.be/FFlwdRp1jnc?t=37m7s
* In Memory Service Grid https://youtu.be/FFlwdRp1jnc?t=46m31s
* In Memory Streaming and CEP https://youtu.be/FFlwdRp1jnc?t=47m47s
* In Memory Hadoop Accelerator https://youtu.be/FFlwdRp1jnc?t=50m5s
* Management & Monitoring https://youtu.be/FFlwdRp1jnc?t=56m45s
