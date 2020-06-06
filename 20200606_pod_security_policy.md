
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

它被命名為 `privileged`，顧名思義這是一個權限全開的例子，同時，我們觀察到了，它並沒有定義 namespace，它是個 Cluster Resource。

在我們學習 RBAC 獲得的概念是，即使在系統定義了這屬 Pod Security Policy 仍是沒有作用的，因為它還沒有被任何的 RoleBinding 與特定的 Subject 及 Role 關聯起來。在把它關聯起來前，我們還要定義一下 Role 宣示我們要授權 Subject 使用這組 Pod Security Policy，但要怎麼做呢？

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

上述就是對於 Pod Security Policy 的簡述。接著，我們透過實戰來認識各種 error messages。

## 建立實作環境

由於 `Pod Security Policy` 在預設的情況下並不會被啟用，為了準備一個能用來練習的環境。這功能得要求 kube-apiserver 的 `--enable-admission-plugins` 參數啟用它。

(TBD 查詢參數的過程)


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

利用準備好的設定檔建出 Kubernetes Cluster：

```
$ kind create cluster --config cfg.yaml
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

## 實作環境的現況

```
$ kubectl get all -A
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
```

啟後 Kubernetes 後，我們先觀察一下整體的狀態，會發現整組壞光光：DaemonSet 與 Deployment 都無法正常啟動。未看先猜，他們被 Pod Security Policy 給阻擋了。然後，對於學習新事物的重點在於：該判斷我落入了目前的情境？它的特徵是什麼呢？直接看一下 coredns Deployment 的狀態：

```
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    deployment.kubernetes.io/revision: "1"
  creationTimestamp: "2020-06-06T12:24:03Z"
  generation: 1
  labels:
    k8s-app: kube-dns
  name: coredns
  namespace: kube-system
  resourceVersion: "1750"
  selfLink: /apis/apps/v1/namespaces/kube-system/deployments/coredns
  uid: 7a7ca03e-8846-4efa-8467-0743de6d9e58
spec:
  progressDeadlineSeconds: 600
  replicas: 2
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: kube-dns
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 1
    type: RollingUpdate
  template:
    metadata:
      creationTimestamp: null
      labels:
        k8s-app: kube-dns
    spec:
      containers:
      - args:
        - -conf
        - /etc/coredns/Corefile
        image: k8s.gcr.io/coredns:1.6.5
        imagePullPolicy: IfNotPresent
        livenessProbe:
          failureThreshold: 5
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 60
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 5
        name: coredns
        ports:
        - containerPort: 53
          name: dns
          protocol: UDP
        - containerPort: 53
          name: dns-tcp
          protocol: TCP
        - containerPort: 9153
          name: metrics
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /ready
            port: 8181
            scheme: HTTP
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 1
        resources:
          limits:
            memory: 170Mi
          requests:
            cpu: 100m
            memory: 70Mi
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            add:
            - NET_BIND_SERVICE
            drop:
            - all
          readOnlyRootFilesystem: true
        terminationMessagePath: /dev/termination-log
        terminationMessagePolicy: File
        volumeMounts:
        - mountPath: /etc/coredns
          name: config-volume
          readOnly: true
      dnsPolicy: Default
      nodeSelector:
        beta.kubernetes.io/os: linux
      priorityClassName: system-cluster-critical
      restartPolicy: Always
      schedulerName: default-scheduler
      securityContext: {}
      serviceAccount: coredns
      serviceAccountName: coredns
      terminationGracePeriodSeconds: 30
      tolerations:
      - key: CriticalAddonsOnly
        operator: Exists
      - effect: NoSchedule
        key: node-role.kubernetes.io/master
      volumes:
      - configMap:
          defaultMode: 420
          items:
          - key: Corefile
            path: Corefile
          name: coredns
        name: config-volume
status:
  conditions:
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
  - lastTransitionTime: "2020-06-06T12:34:18Z"
    lastUpdateTime: "2020-06-06T12:34:18Z"
    message: ReplicaSet "coredns-6955765f44" has timed out progressing.
    reason: ProgressDeadlineExceeded
    status: "False"
    type: Progressing
  observedGeneration: 1
  unavailableReplicas: 2
```

我們發現了一個 pod request 的 event 被阻擋了，它的特徵為 `no providers available to validate`：

> message: 'pods "coredns-6955765f44-" is forbidden: no providers available to validate

比對一下 Kubernetes 的原始碼，確實是在 [Pod Security Policy 內吐出的 error messages](https://github.com/kubernetes/kubernetes/blob/v1.18.3/plugin/pkg/admission/security/podsecuritypolicy/admission.go#L247)，我們確實未建立任何的 Pod Security Policy 並與 coredns Service Account 關聯：

```
$ git grep "no providers available to validate"
plugin/pkg/admission/security/podsecuritypolicy/admission.go:           return nil, "", nil, fmt.Errorf("no providers available to validate pod request")
```



## 修復 Cluster

我們先選擇簡單一點的修法，先將目前系統預設的 pod 都設成 privileged 的，建立一個 `psp-privileged` 的 ClusterRole：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: psp-privileged
rules:
- apiGroups: ['policy']
  resources: ['podsecuritypolicies']
  verbs:     ['use']
  resourceNames:
  - privileged
```

替相關的 ServiceAccount 綁定權限：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: psp-kind
roleRef:
  kind: ClusterRole
  name: psp-privileged
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: coredns
  namespace: kube-system
- kind: ServiceAccount
  name: kindnet
  namespace: kube-system
- kind: ServiceAccount
  name: kube-proxy
  namespace: kube-system
- kind: ServiceAccount
  name: local-path-provisioner-service-account
  namespace: local-path-storage
```

將 Deployment 重啟 (sacle 至 0，再 scale 到原先的數值) 後，服務就正常了：

```
(base) ($ |kind-kind:default)➜  lab k get all -A
NAMESPACE            NAME                                          READY   STATUS    RESTARTS   AGE
kube-system          pod/coredns-6955765f44-qr2k9                  1/1     Running   0          49s
kube-system          pod/kindnet-h4wqv                             1/1     Running   0          80s
kube-system          pod/kube-proxy-bt5q5                          1/1     Running   0          80s
local-path-storage   pod/local-path-provisioner-7745554f7f-97lgs   1/1     Running   0          83s

NAMESPACE     NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
default       service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP                  90m
kube-system   service/kube-dns     ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   90m

NAMESPACE     NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR                 AGE
kube-system   daemonset.apps/kindnet      1         1         1       1            1           <none>                        89m
kube-system   daemonset.apps/kube-proxy   1         1         1       1            1           beta.kubernetes.io/os=linux   90m

NAMESPACE            NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
kube-system          deployment.apps/coredns                  1/1     1            1           90m
local-path-storage   deployment.apps/local-path-provisioner   1/1     1            1           89m

NAMESPACE            NAME                                                DESIRED   CURRENT   READY   AGE
kube-system          replicaset.apps/coredns-6955765f44                  1         1         1       89m
local-path-storage   replicaset.apps/local-path-provisioner-7745554f7f   1         1         1       89m
```






