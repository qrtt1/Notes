# 重讀 Kubernetes Concepts

在 kubernetes 官方的入門文件，有一講解 [Concepts](https://kubernetes.io/docs/concepts/) 的文件。

先前讀過一次，也跟著 kata 練習過大致能『感覺』到 kubernetes 怎麼使用。想要重讀 Concepts 文件主要是：

* 上一次讀是去年的事了，太具體的部分忘得差不多囉！該來複習一下內容了
* 在看了 source code 後，一些以前覺得模糊的概念更加具體了些。

## Control Plane

第一次看到 Control Plane 時，隱約覺得它是個抽象的機制，也許不是真實存在的東西。在追過程式碼候，他其實由 3 個軟體元件組成的，在[cmd/kubeadm/app/constants/constants.go](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kubeadm/app/constants/constants.go#L387)內也可以看得到：

```go
// ControlPlaneComponents defines the control-plane component names
ControlPlaneComponents = []string{KubeAPIServer, KubeControllerManager, KubeScheduler}
```

這 3 個元件也有各別的參數說明頁面：[Customizing control plane configuration with kubeadm](https://kubernetes.io/docs/setup/independent/control-plane-flags/) 與[設計文件](https://github.com/kubernetes/kubernetes/blob/release-1.4/docs/design/architecture.md?fbclid=IwAR2xPNrGSTVSNOHcZsIHkxxgVMSgutq9gvtTauRcRgVVKKnMUyICjdJ5Z6k#the-kubernetes-control-plane)。

這些概念在 overview 的部分並沒有清楚的交待，但在後續的文件有說明，只是並沒有很直接地與 control plane 關聯起來。變成在讀文件時，知道：

* API Server 會接受 API 或 kubectl 的 request
* Controller Manager 會替我們做一些事
* Scheduler 的角色在開始並未多說明些什麼

透過設計文件，我們可以知道。給 API Server 的資料會變存入 etcd 內，而透過 etcd 提供的 watch 機制，來通知關注特定 keyspace 的 client 端。

其中無論是 controller manager (所啟動 controllers) 或 scheduler (它其實也是一種 controller 只是它特別關注 pod 的建立的事件)，都是透過 kubernetes 實作的 Informer (包裝過的 watcher) 來訂閱通知。
