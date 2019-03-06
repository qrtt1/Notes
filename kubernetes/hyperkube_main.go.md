# hyperkube

hyperkube 是 kubernetes project 內的一個聚合式的指令，在先前的 [local-up-cluster.sh_service_staring.md](local-up-cluster.sh_service_staring.md) 筆記，我們可以看到各種的元件透過它啟動。可以作為我們研究 kubernetes 原始碼的進入點。

但得提醒一下的是，若是使用 `managed` kubernetes cluster 通常是無法直接看到 master node，所以還是在 local 端啟動 cluster 來研究比較方面。以 GKE 為例，它的一般 node 上的 kubelet 與 proxy 並不會看到 hyperkube 的字樣，但只要記得哪些是必要安裝的元件，一樣可以輕易找出來在非 master node 下得安裝:

* kubelet：負責管理 allocate resource 的代理程式 (例如：叫 docker 啟動 application)
* kube-proxy：負責開通 service (對應的 port 與 endponint) 的程式。

```
qrtt1@gke-standard-cluster-1-default-pool-750b3531-k155 ~ $ ps aux|grep kubelet
root         982  0.0  0.0   9560  3112 ?        Ss   02:09   0:00 bash /home/kubernetes/bin/health-monitor.sh kubelet
root        1142  2.8  2.7 834400 102848 ?       Ssl  02:10   0:45 /home/kubernetes/bin/kubelet --v=2 --cloud-provider=gce --experimental-mounter-path=/home/kubernetes/containerized_mounter/mounter --experimental-check-node-capabilities-before-mount=true --cert-dir=/var/lib/kubelet/pki/ --cni-bin-dir=/home/kubernetes/bin --allow-privileged=true --kubeconfig=/var/lib/kubelet/kubeconfig --experimental-kernel-memcg-notification=true --max-pods=110 --network-plugin=kubenet --node-labels=beta.kubernetes.io/fluentd-ds-ready=true,cloud.google.com/gke-nodepool=default-pool,cloud.google.com/gke-os-distribution=cos --volume-plugin-dir=/home/kubernetes/flexvolume --registry-qps=10 --registry-burst=20 --bootstrap-kubeconfig=/var/lib/kubelet/bootstrap-kubeconfig --node-status-max-images=25 --config /home/kubernetes/kubelet-config.yaml
qrtt1       8311  0.0  0.0   6272   792 pts/0    S+   02:38   0:00 grep --colour=auto kubelet
```
```
qrtt1@gke-standard-cluster-1-default-pool-750b3531-k155 ~ $ ps aux|grep proxy
root        1320  0.3  0.8 230588 32468 ?        Ssl  02:11   0:05 kube-proxy --master=https://35.221.171.12 --kubeconfig=/var/lib/kube-proxy/kubeconfig --cluster-cidr=10.4.0.0/14 --resource-container= --oom-score-adj=-998 --v=2 --feature-gates=DynamicKubeletConfig=false,ExperimentalCriticalPodAnnotation=true --iptables-sync-period=1m --iptables-min-sync-period=10s --ipvs-sync-period=1m --ipvs-min-sync-period=10s
qrtt1       8922  0.0  0.0   6272   792 pts/0    S+   02:40   0:00 grep --colour=auto proxy
qrtt1@gke-standard-cluster-1-default-pool-750b3531-k155 ~ $
```

由 kubelet 的參數也可以看到，它有指定 `--kubeconfig` 但不像 `local-up-master.sh` 有指定 `--master` 去覆蓋 kube-config 的設定。同樣以 GKE 環境為例，我們能進去偷看一下它設了些什麼：

```yaml
# qrtt1@gke-standard-cluster-1-default-pool-750b3531-bggq ~ $ sudo cat /var/lib/kubelet/kubeconfig
apiVersion: v1
clusters:
- cluster:
    certificate-authority: /etc/srv/kubernetes/pki/ca-certificates.crt
    server: https://35.221.171.12
  name: default-cluster
contexts:
- context:
    cluster: default-cluster
    namespace: default
    user: default-auth
  name: default-context
current-context: default-context
kind: Config
preferences: {}
users:
- name: default-auth
  user:
    client-certificate: /var/lib/kubelet/pki/kubelet-client-current.pem
    client-key: /var/lib/kubelet/pki/kubelet-client-current.pem
```