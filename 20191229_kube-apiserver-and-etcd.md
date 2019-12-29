# Recovery Kubernetes Objects from ETCD

相對於使用公有雲的 Kubernetes，維運 On-Premise Kubernetes 有著較多的的眉角。不過，自建的 Kubernetes 也有它獨特的優點，特別是能直接摸得到 ETCD 這件事，這也是為什麼值得寫一篇文章來分享的小技巧。


## Kubernetes Objects 與它的 store

維運 kubernetes cluster 時，最常用的指令為 kubectl。kubectl 其實就是個 HTTP Client，透過它來與 kubernetes 的 kube-apiserver 溝通。kube-apiserver 提供 HTTP 端點，接收 kubernetes object 的 CRUD 與各種的功能。

這些 CRUD 的動作，會反應在 kubernetes 的 key-value store 內，其實就是對 ETCD 進行操作。因此，我們使用 kubectl 進行各種 object 的修改，並不是直接去變更 kubernetes cluster 的狀態，而是向 kubernetes 宣告期望的狀態。因此，kubernetes object 的內容，其實是對於系統狀態的許願。

那麼誰會去滿足這個願望呢？在 kubernetes 內有著各式各樣的 controller，不同的 controller 會關注不同的 kubernetes object 內容，並做出適當的反應來改變 cluster 的狀態，這其實就是個簡單的訂閱與通知的模型。為了實現這樣的模型，巧妙地運用了 ETCD 的 Watcher 獲得 object 更新的事件來及時反應期望狀態的改變。

## Kubernetes Disaster Recovery

在維運中，儘管再小心，反覆注意還是有機會失手誤刪 Kubernetes Object，通常重要的設定檔因此消失。為了避免這樣的情況發生，會建議 Operation 執行者，重大修改前先備份資料。

```yaml
kubectl get cm my-config -o yaml > my-config.yaml
```

它可能是個簡單的 ConfigMap 或一個客製化的 CRD 內容。不過，我們仍難以完全避免意外發生，因為能修改狀態的不只直接執行 `kubectl` 的情況。例如：

* 一個升級用的 script
* 使用 package manager (helm upgrade)

變更的範圍有時不是那麼容易確認，這是有機會漏掉該備份的資訊的。這也是為什麼，若有辦法透過 ETCD 的備份來回復資料成為 On-Premise Kubernetes 終極救星。

試著在 Google 搜尋 "Kubernetes Disaster Recovery"，內容多為教你如何備份 ETCD，並由 ETCD 範例還原狀態。其實已經接近我們需要的內容了，但是有幾個問題：

* ETCD Snapshot 保存著 Kubernetes Cluster 全局的狀態，但 operation 做到一個不上不下的階段時，全部回溯似乎不太對。
* 完整的 Recovery 需要重啟每一個 control plane 的 component，這是期望避免的。

因此，需求應該是能否保持 Kubernetes 持續運作，另外使用 ETCD Snapshot 取得需要的 Kubernetes Object 內容就好。

## 運用 docker 建立 kube-apiserver

在前一段落我們探索出來的需求其實是：

* 能有另一組 kubernetes cluster 讓維運人員操作 kubectl 取得 yaml 檔 (就是 dump 出來的 kubernetes object)

要達成這個目標，其實就是：

* 建立出相同的網路環境 (IP 至少要許 certificate 內登記的相同)
* 透過 ETCD Snapshot 建立出一組新的 ETCD Service (使用與原 cluster 一樣的 IP)
* 啟動 kube-apiserver 並接上 ETCD Service (使用與原 cluster 一樣的 certificate)
* kubectl 使用原 cluster 的 kubeconfig 進行操作

### 網路環境

要擬刻出一個相近的網路環境，docker 就是個相關便利的環境了。況且，目前 kubernetes 的 container runtime 還是以 docker 為大宗，我們能利用 `docker network create` 的功能，建出需要的 subnet：

```
$ docker network create --help

Usage:	docker network create [OPTIONS] NETWORK

Create a network

Options:
      --attachable           Enable manual container attachment
      --aux-address map      Auxiliary IPv4 or IPv6 addresses used by Network driver (default map[])
      --config-from string   The network from which copying the configuration
      --config-only          Create a configuration only network
  -d, --driver string        Driver to manage the Network (default "bridge")
      --gateway strings      IPv4 or IPv6 Gateway for the master subnet
      --ingress              Create swarm routing-mesh network
      --internal             Restrict external access to the network
      --ip-range strings     Allocate container ip from a sub-range
      --ipam-driver string   IP Address Management Driver (default "default")
      --ipam-opt map         Set IPAM driver specific options (default map[])
      --ipv6                 Enable IPv6 networking
      --label list           Set metadata on a network
  -o, --opt map              Set driver specific options (default map[])
      --scope string         Control the network's scope
      --subnet strings       Subnet in CIDR format that represents a network segment
```

### ETCD 啟動參數

透過 `docker inspect` 取得 ETCD 的啟動參數是相當容易的：

```
$ docker inspect etcd | jq .[].Args
[
  "--peer-client-cert-auth",
  "--client-cert-auth",
  "--listen-client-urls=https://0.0.0.0:2379",
  "--listen-peer-urls=https://0.0.0.0:2380",
  "--trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem",
  "--cert-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11.pem",
  "--peer-cert-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11.pem",
  "--peer-key-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11-key.pem",
  "--data-dir=/var/lib/rancher/etcd/",
  "--name=etcd-k8s01",
  "--election-timeout=5000",
  "--initial-advertise-peer-urls=https://10.40.0.11:2380",
  "--peer-trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem",
  "--key-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11-key.pem",
  "--heartbeat-interval=500",
  "--advertise-client-urls=https://10.40.0.11:2379,https://10.40.0.11:4001",
  "--initial-cluster=etcd-k8s01=https://10.40.0.11:2380,etcd-k8s02=https://10.40.0.12:2380",
  "--initial-cluster-token=etcd-cluster-1",
  "--initial-cluster-state=new"
]
```

值得注意的是

*  `--initial-cluster` 列表中，可能會有多台 ETCD，它們的設定會有一些不同，請個別取得它們的設定。

### kube-apiserver 啟動參數

kube-apiserver 參數的取消也如同 ETCD 一樣：

```
$ docker inspect kube-apiserver | jq .[].Args
[
  "kube-apiserver",
  "--insecure-port=0",
  "--etcd-prefix=/registry",
  "--kubelet-client-certificate=/etc/kubernetes/ssl/kube-apiserver.pem",
  "--runtime-config=authorization.k8s.io/v1beta1=true",
  "--authorization-mode=Node,RBAC",
  "--allow-privileged=true",
  "--requestheader-allowed-names=kube-apiserver-proxy-client",
  "--etcd-cafile=/etc/kubernetes/ssl/kube-ca.pem",
  "--etcd-keyfile=/etc/kubernetes/ssl/kube-node-key.pem",
  "--etcd-servers=https://10.40.0.11:2379,https://10.40.0.12:2379",
  "--proxy-client-key-file=/etc/kubernetes/ssl/kube-apiserver-proxy-client-key.pem",
  "--audit-log-path=-",
  "--bind-address=0.0.0.0",
  "--requestheader-extra-headers-prefix=X-Remote-Extra-",
  "--secure-port=6443",
  "--client-ca-file=/etc/kubernetes/ssl/kube-ca.pem",
  "--tls-private-key-file=/etc/kubernetes/ssl/kube-apiserver-key.pem",
  "--tls-cert-file=/etc/kubernetes/ssl/kube-apiserver.pem",
  "--delete-collection-workers=3",
  "--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname",
  "--requestheader-username-headers=X-Remote-User",
  "--service-account-lookup=true",
  "--storage-backend=etcd3",
  "--service-node-port-range=30000-32767",
  "--tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305",
  "--v=4",
  "--anonymous-auth=false",
  "--profiling=false",
  "--requestheader-group-headers=X-Remote-Group",
  "--service-account-key-file=/etc/kubernetes/ssl/kube-service-account-token-key.pem",
  "--service-cluster-ip-range=10.233.0.0/18",
  "--enable-admission-plugins=NamespaceLifecycle,LimitRanger,ServiceAccount,TaintNodesByCondition,Priority,DefaultTolerationSeconds,DefaultStorageClass,PersistentVolumeClaimResize,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota,NodeRestriction",
  "--cloud-provider=",
  "--etcd-certfile=/etc/kubernetes/ssl/kube-node.pem",
  "--requestheader-client-ca-file=/etc/kubernetes/ssl/kube-apiserver-requestheader-ca.pem",
  "--kubelet-client-key=/etc/kubernetes/ssl/kube-apiserver-key.pem",
  "--proxy-client-cert-file=/etc/kubernetes/ssl/kube-apiserver-proxy-client.pem",
  "--advertise-address=10.40.0.11"
]
```

## 用 docker-compose 組裝 kube-apiserver

將參數整理與複製檔案的工作，寫成簡單的 script (這是以 rke 建立出來的 kubernetes 作為測試對象)：

```
$ ls -l
total 16
-rwxrwxr-x 1 phuser phuser  928 Dec 31 04:00 build-compose.sh
-rw-rw-r-- 1 phuser phuser 2487 Dec 31 04:00 compose-generator.py
-rw-rw-r-- 1 phuser phuser  507 Dec 31 04:00 README.md
-rw-rw-r-- 1 phuser phuser 2100 Dec 31 04:00 script-generator.py
```

透過 script 產生出的 compose 目錄，結構如下：

```
$ tree compose
compose
├── docker-compose.yml
├── k8s01
│   ├── env.json
│   ├── etcd-restore-and-up.sh
│   ├── ip.txt
│   └── net.txt
├── k8s02
│   ├── env.json
│   ├── etcd-restore-and-up.sh
│   ├── ip.txt
│   └── net.txt
├── kube-api
│   └── entrypoint.sh
├── README.md
└── ssl
    ├── kube-apiserver-key.pem
    ├── kube-apiserver.pem
    ├── kube-apiserver-proxy-client-key.pem
    ├── kube-apiserver-proxy-client.pem
    ├── kube-apiserver-requestheader-ca-key.pem
    ├── kube-apiserver-requestheader-ca.pem
    ├── kube-ca-key.pem
    ├── kube-ca.pem
    ├── kubecfg-kube-apiserver-proxy-client.yaml
    ├── kubecfg-kube-apiserver-requestheader-ca.yaml
    ├── kubecfg-kube-controller-manager.yaml
    ├── kubecfg-kube-node.yaml
    ├── kubecfg-kube-proxy.yaml
    ├── kubecfg-kube-scheduler.yaml
    ├── kube-controller-manager-key.pem
    ├── kube-controller-manager.pem
    ├── kube-etcd-10-40-0-11-key.pem
    ├── kube-etcd-10-40-0-11.pem
    ├── kube-etcd-10-40-0-12-key.pem
    ├── kube-etcd-10-40-0-12.pem
    ├── kube-node-key.pem
    ├── kube-node.pem
    ├── kube-proxy-key.pem
    ├── kube-proxy.pem
    ├── kube-scheduler-key.pem
    ├── kube-scheduler.pem
    ├── kube-service-account-token-key.pem
    └── kube-service-account-token.pem
```

在 compose 中，共有 3 個 service

* 2 個 ETCD
* 1 個 kube-apiserver

```yaml
version: "2"
services:
  kube-api:
    image: rancher/hyperkube:v1.15.3-rancher1
    entrypoint:
      - sh
      - -c
      - sleep 5; sh /data/kube-api/entrypoint.sh
    networks:
      k8s: {}
    volumes:
      - ./ssl:/etc/kubernetes/ssl
      - ./:/data

  k8s01:
    image: rancher/coreos-etcd:v3.3.10-rancher1
    entrypoint: sh /data/k8s01/etcd-restore-and-up.sh
    networks:
      k8s:
        ipv4_address: 10.40.0.11
    volumes:
      - ./ssl:/etc/kubernetes/ssl
      - ./:/data
    environment:
      - ETCDCTL_API=3
      - ETCDCTL_CACERT=/etc/kubernetes/ssl/kube-ca.pem
      - ETCDCTL_CERT=/etc/kubernetes/ssl/kube-etcd-10-40-0-11.pem
      - ETCDCTL_KEY=/etc/kubernetes/ssl/kube-etcd-10-40-0-11-key.pem
      - ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
      - ETCD_UNSUPPORTED_ARCH=x86_64
      - PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin


  k8s02:
    image: rancher/coreos-etcd:v3.3.10-rancher1
    entrypoint: sh /data/k8s02/etcd-restore-and-up.sh
    networks:
      k8s:
        ipv4_address: 10.40.0.12
    volumes:
      - ./ssl:/etc/kubernetes/ssl
      - ./:/data
    environment:
      - ETCDCTL_API=3
      - ETCDCTL_CACERT=/etc/kubernetes/ssl/kube-ca.pem
      - ETCDCTL_CERT=/etc/kubernetes/ssl/kube-etcd-10-40-0-12.pem
      - ETCDCTL_KEY=/etc/kubernetes/ssl/kube-etcd-10-40-0-12-key.pem
      - ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
      - ETCD_UNSUPPORTED_ARCH=x86_64
      - PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

networks:
  k8s:
    ipam:
      config:
        - subnet: 10.40.0.0/16
```

## 操作迷你的 kubernetes cluster

有了 docker-compose 之後，我們只差 ETCD Snapshot 就能還原出 kubernetes cluster。以 rke 建出的 cluster 為例，它每日都會產生一份備份，我們能使用它，並將解壓縮的檔放入 `compose/etcd_snapshot.db` 

```
phuser@dev-gce-qrtt1-1:~$ ls -l /opt/rke/etcd-snapshots/*
-rw------- 1 root root 1060553 Dec 28 09:42 /opt/rke/etcd-snapshots/2019-12-28T09:42:08Z_etcd.zip
-rw------- 1 root root 1046622 Dec 28 21:42 /opt/rke/etcd-snapshots/2019-12-28T21:42:08Z_etcd.zip
-rw------- 1 root root 1050976 Dec 29 09:42 /opt/rke/etcd-snapshots/2019-12-29T09:42:08Z_etcd.zip
-rw------- 1 root root 1062207 Dec 29 21:42 /opt/rke/etcd-snapshots/2019-12-29T21:42:08Z_etcd.zip
-rw------- 1 root root 1061092 Dec 30 09:42 /opt/rke/etcd-snapshots/2019-12-30T09:42:08Z_etcd.zip
-rw------- 1 root root 1070693 Dec 30 21:42 /opt/rke/etcd-snapshots/2019-12-30T21:42:08Z_etcd.zip
```


將 compose 目錄複製回你的操作環境後，啟動服務：

```
docker-compose up
```

這就是一個能直接用 kubectl 操作的迷你版的 kubernetes cluster 囉：

```
docker-compose top
compose_k8s01_1
PID    USER   TIME                                                                             COMMAND
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
5429   root   0:00   sh /data/k8s01/etcd-restore-and-up.sh
5786   root   0:06   etcd --data-dir=/opt/nobody_knows_where_is --name=etcd-k8s01 --initial-advertise-peer-urls=https://10.40.0.11:2380 --initial-
                     cluster=etcd-k8s01=https://10.40.0.11:2380,etcd-k8s02=https://10.40.0.12:2380 --initial-cluster-token=etcd-cluster-1 --listen-client-
                     urls=https://0.0.0.0:2379 --listen-peer-urls=https://0.0.0.0:2380 --trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem --cert-file=/etc/kubernetes/ssl/kube-
                     etcd-10-40-0-11.pem --peer-cert-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11.pem --peer-key-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11-key.pem --peer-
                     trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem --key-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-11-key.pem --advertise-client-
                     urls=https://10.40.0.11:2379,https://10.40.0.11:4001

compose_k8s02_1
PID    USER   TIME                                                                             COMMAND
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
5365   root   0:00   sh /data/k8s02/etcd-restore-and-up.sh
5784   root   0:05   etcd --data-dir=/opt/nobody_knows_where_is --initial-advertise-peer-urls=https://10.40.0.12:2380 --initial-
                     cluster=etcd-k8s01=https://10.40.0.11:2380,etcd-k8s02=https://10.40.0.12:2380 --name=etcd-k8s02 --initial-cluster-token=etcd-cluster-1 --cert-
                     file=/etc/kubernetes/ssl/kube-etcd-10-40-0-12.pem --peer-cert-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-12.pem --advertise-client-
                     urls=https://10.40.0.12:2379,https://10.40.0.12:4001 --listen-client-urls=https://0.0.0.0:2379 --key-file=/etc/kubernetes/ssl/kube-etcd-10-40-0-12-key.pem
                     --listen-peer-urls=https://0.0.0.0:2380 --peer-trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem --peer-key-file=/etc/kubernetes/ssl/kube-
                     etcd-10-40-0-12-key.pem --trusted-ca-file=/etc/kubernetes/ssl/kube-ca.pem

compose_kube-api_1
PID    USER   TIME                                                                             COMMAND
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
5423   root   0:00   sh -c sleep 5; sh /data/kube-api/entrypoint.sh
5828   root   0:00   sh /data/kube-api/entrypoint.sh
5829   root   0:12   kube-apiserver --insecure-port=0 --etcd-prefix=/registry --kubelet-client-certificate=/etc/kubernetes/ssl/kube-apiserver.pem --runtime-
                     config=authorization.k8s.io/v1beta1=true --authorization-mode=Node,RBAC --allow-privileged=true --requestheader-allowed-names=kube-apiserver-proxy-client
                     --etcd-cafile=/etc/kubernetes/ssl/kube-ca.pem --etcd-keyfile=/etc/kubernetes/ssl/kube-node-key.pem --etcd-
                     servers=https://10.40.0.11:2379,https://10.40.0.12:2379 --proxy-client-key-file=/etc/kubernetes/ssl/kube-apiserver-proxy-client-key.pem --audit-log-path=-
                     --bind-address=0.0.0.0 --requestheader-extra-headers-prefix=X-Remote-Extra- --secure-port=6443 --client-ca-file=/etc/kubernetes/ssl/kube-ca.pem --tls-
                     private-key-file=/etc/kubernetes/ssl/kube-apiserver-key.pem --tls-cert-file=/etc/kubernetes/ssl/kube-apiserver.pem --delete-collection-workers=3 --kubelet-
                     preferred-address-types=InternalIP,ExternalIP,Hostname --requestheader-username-headers=X-Remote-User --service-account-lookup=true --storage-backend=etcd3
                     --service-node-port-range=30000-32767 --tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_W
                     ITH_CHACHA20_POLY1305,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305 --v=4 --anonymous-
                     auth=false --profiling=false --requestheader-group-headers=X-Remote-Group --service-account-key-file=/etc/kubernetes/ssl/kube-service-account-token-key.pem
                     --service-cluster-ip-range=10.233.0.0/18 --enable-admission-plugins=NamespaceLifecycle,LimitRanger,ServiceAccount,TaintNodesByCondition,Priority,DefaultTol
                     erationSeconds,DefaultStorageClass,PersistentVolumeClaimResize,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota,NodeRestriction --cloud-
                     provider= --etcd-certfile=/etc/kubernetes/ssl/kube-node.pem --requestheader-client-ca-file=/etc/kubernetes/ssl/kube-apiserver-requestheader-ca.pem
                     --kubelet-client-key=/etc/kubernetes/ssl/kube-apiserver-key.pem --proxy-client-cert-file=/etc/kub
```

接著取得原 cluster 的 KUBECONFIG (因為，我們並沒有特別將 kube-apiserver 放在原先的 IP，需將 server 位置改為 127.0.0.1，直接在 kube-api container 內使用)：

```
$ compose docker-compose exec kube-api bash
root@a2b7e4bd5ec0:/# export KUBECONFIG=/data/k8s-config

root@a2b7e4bd5ec0:/# kubectl get node
NAME    STATUS   ROLES                      AGE     VERSION
k8s01   Ready    controlplane,etcd,worker   4d21h   v1.15.3
k8s02   Ready    controlplane,etcd,worker   4d21h   v1.15.3
k8s03   Ready    worker                     4d21h   v1.15.3
```

## 最後的提醒

針對自建 kubernetes 的情境，由 ETCD 回復部分資料是可行的，但仍希望這「最終手段」沒有被用上的時候。至於，Managed kubernetes 下要怎麼處理誤刪後的救援呢？這也許得再研究研究了。