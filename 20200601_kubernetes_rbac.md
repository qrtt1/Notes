# Kubernetes RBAC 筆記

當我們開發 Kubernetes 的應用程式或是打算在 Kubernetes pod 內呼叫 Kubernetes API (例如：使用 kubectl)，若沒有對權限做特殊的處理時，會遇到系統阻擋訊息：

```
Error: configmaps is forbidden: User "system:serviceaccount:kube-system:default" cannot list resource "configmaps" in API group "" in the namespace "kube-system"
```

對於剛接觸 Kubernetes 的新手，還沒學會如何使用 Kubernetes RBAC 的時期，可能有點不知所措而卡關了好一陣子。莫驚慌、莫害怕！先記住主要症狀的關鍵字 `forbidden`。若你遇到它，那先研究 rbac 有沒有設定錯誤。

先由上面的 error message (這是我在網上搜尋後作為範例之用)，我們可以先簡單區分出：

* 案發地點：在 `configmaps`
* 行為者：`system:serviceaccount:kube-system:default` user
* 動作：*list resource*

其中，行為者要特別注意一下，去掉固定的 *system:serviceaccount* 後，它給我們的資訊是：

* namespace：kube-system
* service account：default

所以，我們得去『喬』一下 rbac 設定，讓這個動作可以被允許。


## RBAC

在 Kubernetes 官方文件 [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) 為 RBAC 概念介紹的主要文件。RBAC (唸 R back) 的全名為：Role-based access control。所以，只要有個基本的認知：

* 生而為人，只要角色對了，做這件事就被允許。
* Role 即權限 (Permissions)
* 透過 Binding 賦予權限

## Role & ClusterRole

直接取用文件中的範例，Kubernetes 提供 Role 與 ClusterRole 二種資源。因為，對於任何存在於 Kubernetes 中的資源可以分為二類，是 namespace 下的資源或是非 namespace 下的資源 (屬於 Cluster 層級的資源)。Role 即代表了 namespace 下的資源的權限，ClusterRole 則是 Cluster 層級資源的權限。

這也是為什麼你在這目 `pod-reader` 的 Role 權限中會看到 `namespace`，因為它屬於某個 namespace：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

對比 ClusterRole 則不需要填寫 namespace，因為它不是屬於 namespace 下的資源：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  # "namespace" omitted since ClusterRoles are not namespaced
  name: secret-reader
rules:
- apiGroups: [""]
  #
  # at the HTTP level, the name of the resource for accessing Secret
  # objects is "secrets"
  resources: ["secrets"]
  verbs: ["get", "watch", "list"]
```

不管是 Role 或 ClusterRole 都代表了『權限』的集合，所以重點在 `rules`，rules 是一個 list，它可以設定多組的權限，最終這些權限會以被加總起來成為最後能使用的權限。(不支援減少權限的設定，所以要保持最小權限設定的習慣)

## RoleBinding & ClusterRoleBinding

有了特定的角色後，透過 Binding 的動作賦權。

```yaml
apiVersion: rbac.authorization.k8s.io/v1
# This role binding allows "jane" to read pods in the "default" namespace.
# You need to already have a Role named "pod-reader" in that namespace.
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
# You can specify more than one "subject"
- kind: User
  name: jane # "name" is case sensitive
  apiGroup: rbac.authorization.k8s.io
roleRef:
  # "roleRef" specifies the binding to a Role / ClusterRole
  kind: Role #this must be Role or ClusterRole
  name: pod-reader # this must match the name of the Role or ClusterRole you wish to bind to
  apiGroup: rbac.authorization.k8s.io
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
# This cluster role binding allows anyone in the "manager" group to read secrets in any namespace.
kind: ClusterRoleBinding
metadata:
  name: read-secrets-global
subjects:
- kind: Group
  name: manager # Name is case sensitive
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

我們同樣使用官方文件的範例，它的重點在：

* subjects：被授權的對象，它最開頭的範例使用了 User 與 Group。
* roleRef：即為前一段定義好的角色

開發者最常見的為 Service Account 作為授權對象，在文件中也有提供範例：

```yaml
subjects:
- kind: ServiceAccount
  name: default
  namespace: kube-system
```

## 實戰練習

看完了官方文件導讀後，要如何與實際的情境結合呢？直接拿經典的 helm v2 來練習吧！因為 helm 在 Kubernetes 還沒支援 RBAC 時就開始開發，中間歷經了 RBAC 成為 Kubernetes Cluster 預設配置時期。在 Kubernetes 1.6 後才加入的使用者，可能會困惑為什麼 helm v2 的安裝前，要特別先設定 RBAC 呢？

實際上，我們有了上述的知識後，已經有能力來組合需要的 RBAC。實作練習環境如下：


```
$ helm version --client
Client: &version.Version{SemVer:"v2.16.7", GitCommit:"5f2584fd3d35552c4af26036f0c464191287986b", GitTreeState:"clean"}
```

```
$ kind version
kind v0.8.1 go1.14.2 darwin/amd64

$ kind create cluster
Creating cluster "kind" ...
 ✓ Ensuring node image (kindest/node:v1.18.2) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-kind"
You can now use your cluster with:

kubectl cluster-info --context kind-kind

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
```

這次，我們故意忘記要先設定 RBAC，直接初始化 helm：

```
$ helm init --service-account tiller
Creating /Users/qrtt1/.helm
Creating /Users/qrtt1/.helm/repository
Creating /Users/qrtt1/.helm/repository/cache
Creating /Users/qrtt1/.helm/repository/local
Creating /Users/qrtt1/.helm/plugins
Creating /Users/qrtt1/.helm/starters
Creating /Users/qrtt1/.helm/cache/archive
Creating /Users/qrtt1/.helm/repository/repositories.yaml
Adding stable repo with URL: https://kubernetes-charts.storage.googleapis.com
Adding local repo with URL: http://127.0.0.1:8879/charts
$HELM_HOME has been configured at /Users/qrtt1/.helm.

Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.

Please note: by default, Tiller is deployed with an insecure 'allow unauthenticated users' policy.
To prevent this, run `helm init` with the --tiller-tls-verify flag.
For more information on securing your installation see: https://v2.helm.sh/docs/securing_installation/
```

顯然地，它並沒有順利啟動：

```
$ helm ls
Error: could not find tiller

$ k -n kube-system get deploy
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
coredns         2/2     2            2           5m45s
tiller-deploy   0/1     0            0           73s
```

若直接查看它的 status，能看到問題出在 Service Account *tiller* 並不存在：

```
$ k -n kube-system get deploy tiller-deploy -o yaml
```

```
  - lastTransitionTime: "2020-05-31T14:40:53Z"
    lastUpdateTime: "2020-05-31T14:40:53Z"
    message: 'pods "tiller-deploy-66fccb9847-" is forbidden: error looking up service
      account kube-system/tiller: serviceaccount "tiller" not found'
    reason: FailedCreate
    status: "True"
    type: ReplicaFailure
```

在剛才的說明文件中，並沒有特別提到 Service Account 要怎麼用 yaml 定義，那直接參考系統內的 Service Account 修改即可：

```yaml
$ k -n kube-system get sa coredns -o yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  creationTimestamp: "2020-05-31T14:36:21Z"
  name: coredns
  namespace: kube-system
  resourceVersion: "219"
  selfLink: /api/v1/namespaces/kube-system/serviceaccounts/coredns
  uid: e00b549f-2a8f-4aa2-bcbf-19bb752ab559
secrets:
- name: coredns-token-rn8f7
```

修改為：

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
```

建出了 Service Account，將 `tiller-deploy` deployment 先 scale 至 0，再 scale 回 1。讓它能偵測到新的 Service Account，tiller 終於順利起動囉：

```
$ k get pod -A
NAMESPACE            NAME                                         READY   STATUS    RESTARTS   AGE
kube-system          coredns-66bff467f8-2rvdm                     1/1     Running   0          13m
kube-system          coredns-66bff467f8-5krpr                     1/1     Running   0          13m
kube-system          etcd-kind-control-plane                      1/1     Running   0          13m
kube-system          kindnet-vmd9g                                1/1     Running   0          13m
kube-system          kube-apiserver-kind-control-plane            1/1     Running   0          13m
kube-system          kube-controller-manager-kind-control-plane   1/1     Running   0          13m
kube-system          kube-proxy-vwfvw                             1/1     Running   0          13m
kube-system          kube-scheduler-kind-control-plane            1/1     Running   0          13m
kube-system          tiller-deploy-66fccb9847-kzf7h               1/1     Running   0          22s
local-path-storage   local-path-provisioner-bd4bb6b75-x8cm9       1/1     Running   0          13m
```

但事情沒那麼簡單，因為我們只是符合了它需要 Service Account 的條件，但還沒有授權給 Service Account：

```
$ helm ls
Error: configmaps is forbidden: User "system:serviceaccount:kube-system:tiller" cannot list resource "configmaps" in API group "" in the namespace "kube-system"
```

接著，我們應該要建立 ClusterRole 作為權限設定的容器，以及 ClusterRoleBinding 建立 ClusterRole 與 ServiceAccount 二者的關係。由 error message 可以知道：

* resource name：configmaps
* verb：list
* api group：""

由上述蒐集的資訊，建立出對應的 ClusterRole 與 ClusterRoleBinding：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list"] # 只加需要的 verb
```


```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tiller
subjects:
- kind: ServiceAccount
  name: tiller
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: tiller
  apiGroup: rbac.authorization.k8s.io
```

再執行一次 ls 就成功了，但這只是做 list 的動作，我們沒有給任何寫入的權限。來試著裝新東西唄！

```
$ helm ls
$ helm install stable/wordpress
Error: no available release name found
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/
"stable" has been added to your repositories
$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Skip local chart repository
...Successfully got an update from the "stable" chart repository
Update Complete.
$ helm install stable/wordpress
Error: no available release name found
$ helm repo
```

做了一連串的東西都沒反應，這表示一定有什麼問題阻擋了我們，來看一下 tiller pod 的 log 有無可疑之處：

```
[storage] 2020/05/31 15:05:55 getting release "lumpy-platypus.v1"
[storage/driver] 2020/05/31 15:05:55 get: failed to get "lumpy-platypus.v1": configmaps "lumpy-platypus.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "configmaps" in API group "" in the namespace "kube-system"
[tiller] 2020/05/31 15:05:55 info: generated name lumpy-platypus is taken. Searching again.
[storage] 2020/05/31 15:05:55 getting release "doltish-wolverine.v1"
[storage/driver] 2020/05/31 15:05:55 get: failed to get "doltish-wolverine.v1": configmaps "doltish-wolverine.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "configmaps" in API group "" in the namespace "kube-system"
[tiller] 2020/05/31 15:05:55 info: generated name doltish-wolverine is taken. Searching again.
[storage] 2020/05/31 15:05:55 getting release "tailored-sabertooth.v1"
[storage/driver] 2020/05/31 15:05:55 get: failed to get "tailored-sabertooth.v1": configmaps "tailored-sabertooth.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "configmaps" in API group "" in the namespace "kube-system"
[tiller] 2020/05/31 15:05:55 info: generated name tailored-sabertooth is taken. Searching again.
[storage] 2020/05/31 15:05:55 getting release "nonplussed-squirrel.v1"
[storage/driver] 2020/05/31 15:05:55 get: failed to get "nonplussed-squirrel.v1": configmaps "nonplussed-squirrel.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "configmaps" in API group "" in the namespace "kube-system"
[tiller] 2020/05/31 15:05:55 info: generated name nonplussed-squirrel is taken. Searching again.
[storage] 2020/05/31 15:05:55 getting release "nosy-ocelot.v1"
[storage/driver] 2020/05/31 15:05:55 get: failed to get "nosy-ocelot.v1": configmaps "nosy-ocelot.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "configmaps" in API group "" in the namespace "kube-system"
```

同樣地分析一下問題：

* resource name：configmaps
* verb：get
* apiGroups：同上

依需求修改 ClusterRole，加入 `get` verb：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get"]
```

再次試著安裝：

```
helm install stable/wordpress --name wp
Error: release wp failed: namespaces "default" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot get resource "namespaces" in API group "" in the namespace "default"
```

分析一下問題：

* resource name：namespaces
* verb：get
* apiGroups：""

追加 namespaces：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
```

執行安裝：

```
helm install stable/wordpress --name wp
Error: release wp failed: secrets is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "secrets" in API group "" in the namespace "default"
```

分析一下問題：

* resource name：secrets
* verb：create
* apiGroups：""

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create"]
```

新的錯誤：

```
helm install stable/wordpress --name wp
Error: release wp failed: configmaps is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "configmaps" in API group "" in the namespace "default"
```

分析一下問題：

* resource name：configmaps
* verb：create
* apiGroups：""

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create"]
```

終於沒有被擋權限了，但因為它其實是建立到一半的半成品，把它移除看看：

```
$ helm install stable/wordpress --name wp
Error: release wp failed: secrets "wp-wordpress" already exists
$ helm ls
$ helm delete wp --purge
Error: configmaps "wp.v1" is forbidden: User "system:serviceaccount:kube-system:tiller" cannot delete resource "configmaps" in API group "" in the namespace "kube-system"
```

經過多次反覆地分析，已能熟練地在 configmaps 與 secrets 加上 `delete` verb：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create", "delete"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create", "delete"]
```

```
$ helm delete wp --purge
release "wp" deleted
```

```
helm install stable/wordpress --name wp
Error: release wp failed: persistentvolumeclaims is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "persistentvolumeclaims" in API group "" in the namespace "default"
```

追加 resource `persistentvolumeclaims`：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create", "delete"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["persistentvolumeclaims"]
  verbs: ["create", "delete"]
```

再重建它：

```
$ helm delete wp --purge
release "wp" deleted
$ helm install stable/wordpress --name wp
Error: release wp failed: services is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "services" in API group "" in the namespace "default"
```

追加 services：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create", "delete"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["persistentvolumeclaims"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["services"]
  verbs: ["create", "delete"]
```

```
$ helm delete wp --purge
release "wp" deleted
$ helm install stable/wordpress --name wp
Error: release wp failed: deployments.apps is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "deployments" in API group "apps" in the namespace "default"
```

追加 deployments：


```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create", "delete"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["persistentvolumeclaims"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["services"]
  verbs: ["create", "delete"]
- apiGroups: ["apps"] 
  resources: ["deployments"]
  verbs: ["create", "delete"]
```

```
$ helm install stable/wordpress --name wp
Error: release wp failed: statefulsets.apps is forbidden: User "system:serviceaccount:kube-system:tiller" cannot create resource "statefulsets" in API group "apps" in the namespace "default"
```

追加 statefulsets


```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tiller
rules:
- apiGroups: [""] 
  resources: ["configmaps"]
  verbs: ["list", "get", "create", "delete"]
- apiGroups: [""] 
  resources: ["namespaces"]
  verbs: ["get"]
- apiGroups: [""] 
  resources: ["secrets"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["persistentvolumeclaims"]
  verbs: ["create", "delete"]
- apiGroups: [""] 
  resources: ["services"]
  verbs: ["create", "delete"]
- apiGroups: ["apps"] 
  resources: ["deployments"]
  verbs: ["create", "delete"]
- apiGroups: ["apps"] 
  resources: ["statefulsets"]
  verbs: ["create", "delete"]
```

終於成功將它安裝完成：

```
$ helm install stable/wordpress --name wp
NAME:   wp
LAST DEPLOYED: Sun May 31 23:37:25 2020
NAMESPACE: default
STATUS: PENDING_INSTALL

RESOURCES:
==> v1/ConfigMap
NAME              DATA  AGE
wp-mariadb        1     1s
wp-mariadb-tests  1     1s

==> MISSING
KIND                                    NAME
/v1, Resource=secrets                   wp-wordpress
/v1, Resource=secrets                   wp-mariadb
/v1, Resource=persistentvolumeclaims    wp-wordpress
/v1, Resource=services                  wp-wordpress
/v1, Resource=services                  wp-mariadb
apps/v1, Resource=deployments           wp-wordpress
apps/v1, Resource=statefulsets          wp-mariadb
/v1, Resource=secrets                   wp-wordpress
/v1, Resource=secrets                   wp-mariadb
/v1, Resource=persistentvolumeclaims    wp-wordpress
/v1, Resource=services                  wp-wordpress
/v1, Resource=services                  wp-mariadb
apps/v1, Resource=deployments           wp-wordpress
apps/v1, Resource=statefulsets          wp-mariadb

NOTES:
This Helm chart is deprecated

(...skip...)
```


## 結語

看完了概念介紹與實戰練習後，RBAC 的使用有沒有很簡單呢？摘要一下重點：

* 角色即權限 (Role, Clusterrole)
* 行為者被賦予角色才有權力 (subjects: User, Role, ServiceAccount)
* 透過 Binding 賦予角色 (RoleBinding, ClusterRoleBinding)

在實戰中，只是看著 error message 內提到的 resource、api group 與 verb 來進行修補。我們只是這樣做來反覆完成 helm 所需要的權限。要提醒的事，如果你希望用 helm 來安裝符合總情境的 package，請用官方建議的 RBAC 設定呦！

```yaml
kubectl apply -f - << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
EOF
```

在有了 RBAC 的概念後，我們這時再來看所謂的 `cluster-admin`，它的 rules 是填了什麼就會比較有感覺：

```yaml
rules:
- apiGroups:
  - '*'
  resources:
  - '*'
  verbs:
  - '*'
- nonResourceURLs:
  - '*'
  verbs:
  - '*'
```

也就是 `*` 全開，包含不是 resource 的部分。這也是為什麼有些情況，想要自訂 RBAC 而不使用 `cluster-admin` 的原因囉。