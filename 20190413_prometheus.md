# DevOps Taiwan - Prometheus 工作坊

* [活動頁面](https://devops.kktix.cc/events/prometheus-workshop)
* [投影片](https://docs.google.com/presentation/d/1nbqa-mDEFM3OM-BlT6D7en5sS44wlHyECH_QAxOS46Q/edit#slide=id.g5640965e52_0_186)
* [lab 所在的 github](https://github.com/Taipei-HUG/Prometheus-workshop)

## 安裝 prometheus

使用 prometheus operator 專案內的 kube-prometheus：

```
git clone https://github.com/coreos/prometheus-operator.git
```

取得 prometheus-operator 專案後：

```
cd contrib/kube-prometheus
kubectl apply -f manifests/
# 等一下，也許 5 秒
kubectl apply -f manifests/
```

kube-prometheus 原先是另一個專案，它看到 prometheus-operator 簡化了 prometheus 在 kubernetes 上安裝的步驟，但缺少一些預設的設定，配合 prometheus-operator 提供的 CRD 寫了許多的針對 kubernetes 預先可以監控的部分。

PS. apply 下了 2 次，因為第 1 次下時，有些 resource 還沒建好，部分的 resource 還沒成功，它們有相依關係，所以會 fail。只要再下第 2 次就能安裝好了。



裝好後，看起來會是這些東西：

```
qty:kube-prometheus qrtt1$ k get all -n monitoring
NAME                                       READY   STATUS    RESTARTS   AGE
pod/alertmanager-main-0                    2/2     Running   0          4m52s
pod/alertmanager-main-1                    0/2     Pending   0          2m49s
pod/grafana-b6bd6d987-rnh5k                1/1     Running   0          5m37s
pod/kube-state-metrics-79c85cd8c-mc4cf     4/4     Running   0          5m36s
pod/kube-state-metrics-8b8ddf445-xtbj2     0/4     Pending   0          2m52s
pod/node-exporter-8kwtv                    2/2     Running   0          5m36s
pod/prometheus-adapter-57c497c557-vh8xw    1/1     Running   0          5m35s
pod/prometheus-k8s-0                       3/3     Running   1          4m49s
pod/prometheus-k8s-1                       0/3     Pending   0          4m49s
pod/prometheus-operator-747d7b67dc-s2ctv   1/1     Running   0          5m37s

NAME                            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
service/alertmanager-main       ClusterIP   10.104.112.195   <none>        9093/TCP            5m39s
service/alertmanager-operated   ClusterIP   None             <none>        9093/TCP,6783/TCP   4m52s
service/grafana                 ClusterIP   10.101.223.132   <none>        3000/TCP            5m38s
service/kube-state-metrics      ClusterIP   None             <none>        8443/TCP,9443/TCP   5m38s
service/node-exporter           ClusterIP   None             <none>        9100/TCP            5m37s
service/prometheus-adapter      ClusterIP   10.110.166.84    <none>        443/TCP             5m36s
service/prometheus-k8s          ClusterIP   10.103.113.201   <none>        9090/TCP            5m35s
service/prometheus-operated     ClusterIP   None             <none>        9090/TCP            4m50s
service/prometheus-operator     ClusterIP   None             <none>        8080/TCP            5m39s

NAME                           DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR                 AGE
daemonset.apps/node-exporter   1         1         1       1            1           beta.kubernetes.io/os=linux   5m37s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/grafana               1/1     1            1           5m38s
deployment.apps/kube-state-metrics    1/1     1            1           5m38s
deployment.apps/prometheus-adapter    1/1     1            1           5m36s
deployment.apps/prometheus-operator   1/1     1            1           5m39s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/grafana-b6bd6d987                1         1         1       5m38s
replicaset.apps/kube-state-metrics-79c85cd8c     1         1         1       5m38s
replicaset.apps/kube-state-metrics-8b8ddf445     1         1         0       2m52s
replicaset.apps/prometheus-adapter-57c497c557    1         1         1       5m36s
replicaset.apps/prometheus-operator-747d7b67dc   1         1         1       5m38s

NAME                                 READY   AGE
statefulset.apps/alertmanager-main   1/3     4m52s
statefulset.apps/prometheus-k8s      1/2     4m50s
qty:kube-prometheus qrtt1$
```

## 試玩 promethus

由上面的資訊，我們可以透過 port forward 來連線：

```
kubectl --namespace monitoring port-forward svc/prometheus-k8s 9090
```

預設會連上 graph editor 可以透過 PromQL 查詢：

```
http://127.0.0.1:9090/graph
```

再來就是要學習

* 定義 service monitor 來監測需要關心的服務囉
* 並適當地在 grafana 中建出對應的 dashboard
* 設定 alertmanager