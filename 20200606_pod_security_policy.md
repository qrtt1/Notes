
## Pod Security Policy

這次來介紹一個 `冷門` 的功能，因為它還在 **beta** 階段，是否會成為 Kubernetes 的預設設定呢？這點我無從得知，但在一些商用的 Kubernetes Cluster 上有著相似的設計，例如 OpenShift 的 Security Context Constraints 用法就蠻相像的 (並且，沒有關閉的選項)。所以，對於強調 `安全` 的環境，把它開打來，也許會成為必要的選項。

在前一篇文章，我們介紹了 Kubernetes RBAC 的用法，它的基本概念是：

> Role 代表了權限，Subject {User, Group, ServiceAccount} 代表行為者。
> RoleBinding 用來建立 Subject 與 Role 的關聯。當 Subject 與 Role 有關聯，就代表有了權限。

在這裡，我們先省略了 ClusterRole 與 Role，還有 ClusterRoleBinding 與 RoleBinding 的差別，選用字數較少的版本，方便閱讀。畢竟在上一篇文章有提過了。在這篇它並不是重點。

而 Pod Security Policy 在設計上，也是屬於權限的一種。所以，我們能把它用在 Role 之內。

以官方文件 [Pod Security Policies](https://kubernetes.io/docs/concepts/policy/pod-security-policy/) 提供的範例，Pod Security Policy 的樣貌如下：

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: privileged
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: '*'
spec:
  privileged: true
  allowPrivilegeEscalation: true
  allowedCapabilities:
  - '*'
  volumes:
  - '*'
  hostNetwork: true
  hostPorts:
  - min: 0
    max: 65535
  hostIPC: true
  hostPID: true
  runAsUser:
    rule: 'RunAsAny'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

它被命名為 `privileged`，顧名思義這是一個權限全開的例子。在我們學習 RBAC 獲得的概念是，即使在系統定義了這屬 Pod Security Policy 仍是沒有作用的，因為它還沒有被任何的 RoleBinding 與特定的 Subject 及 Role 關聯起來。在把它關聯起來前，我們還要定義一下 Role 宣示我們要授權 Subject 使用這組 Pod Security Policy，但要怎麼做呢？

舉先前用過的 `pod-reader` 為例，權限設定需要 3 個參數：apiGroups、resources 與 verbs。對 Pod Security Policy 也是，只是它用了個特殊的 verb `use`：

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

針對 `使用` Pod Security Policy 寫法上更為固定簡單，只有 `resourceNames` 是有變化的地方。與先前 RBAC 的差異就是 Policy 是自訂的，而不是使用系統內既有的 Resource。


```yaml
- apiGroups: ['policy']
  resources: ['podsecuritypolicies']
  verbs:     ['use']
  resourceNames:
  - privileged
```





(TBD...)
(TBD...)
(TBD...)
(TBD...)
(TBD...)









```yaml
status:
  conditions:
  - lastTransitionTime: "2020-06-06T12:24:18Z"
    lastUpdateTime: "2020-06-06T12:24:18Z"
    message: Created new replica set "coredns-6955765f44"
    reason: NewReplicaSetCreated
    status: "True"
    type: Progressing
  - lastTransitionTime: "2020-06-06T12:24:18Z"
    lastUpdateTime: "2020-06-06T12:24:18Z"
    message: Deployment does not have minimum availability.
    reason: MinimumReplicasUnavailable
    status: "False"
    type: Available
  - lastTransitionTime: "2020-06-06T12:24:18Z"
    lastUpdateTime: "2020-06-06T12:24:18Z"
    message: 'pods "coredns-6955765f44-" is forbidden: no providers available to validate
      pod request'
    reason: FailedCreate
    status: "True"
    type: ReplicaFailure
  observedGeneration: 1
  unavailableReplicas: 2
```



## 實戰 



```yaml
kind: Cluster
apiVersion: kind.sigs.k8s.io/v1alpha3
nodes:
  - role: control-plane
kubeadmConfigPatches:
  - |
    # v1beta2 only works for 1.15+
    apiVersion: kubeadm.k8s.io/v1beta2
    kind: ClusterConfiguration
    metadata:
      name: config
    apiServer:
      extraArgs:
        enable-admission-plugins: "NamespaceLifecycle,LimitRanger,ServiceAccount,TaintNodesByCondition,Priority,DefaultTolerationSeconds,DefaultStorageClass,StorageObjectInUseProtection,PersistentVolumeClaimResize,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,RuntimeClass,ResourceQuota,PodSecurityPolicy"
```

```
(base) ($ |N/A:default)➜  lab kind create cluster --config cfg.yaml
Creating cluster "kind" ...
 ✓ Ensuring node image (kindest/node:v1.17.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-kind"
You can now use your cluster with:

kubectl cluster-info --context kind-kind

Have a nice day! 👋
```

```
(base) ($ |kind-kind:default)➜  lab k get all -A
NAMESPACE     NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
default       service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP                  47s
kube-system   service/kube-dns     ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   45s

NAMESPACE     NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR                 AGE
kube-system   daemonset.apps/kindnet      0         0         0       0            0           <none>                        43s
kube-system   daemonset.apps/kube-proxy   0         0         0       0            0           beta.kubernetes.io/os=linux   45s

NAMESPACE            NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
kube-system          deployment.apps/coredns                  0/2     0            0           45s
local-path-storage   deployment.apps/local-path-provisioner   0/1     0            0           42s

NAMESPACE            NAME                                                DESIRED   CURRENT   READY   AGE
kube-system          replicaset.apps/coredns-6955765f44                  2         0         0       30s
local-path-storage   replicaset.apps/local-path-provisioner-7745554f7f   1         0         0       30s
(base) ($ |kind-kind:default)➜  lab
```


