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

PS. 相似的 kube-proxy 卻有指定 `--master` 參數，覺得應該是重構時沒拿掉唄？

## hyperkube

[hyperkube/main.go](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/hyperkube/main.go) 只有 200 行不到，因為它單純只是組合 commandline 參數，實作上是很標準的 Command Pattern：

```go
func main() {
	rand.Seed(time.Now().UnixNano())

	hyperkubeCommand, allCommandFns := NewHyperKubeCommand(server.SetupSignalHandler())

	// TODO: once we switch everything over to Cobra commands, we can go back to calling
	// cliflag.InitFlags() (by removing its pflag.Parse() call). For now, we have to set the
	// normalize func and add the go flag set by hand.
	pflag.CommandLine.SetNormalizeFunc(cliflag.WordSepNormalizeFunc)
	pflag.CommandLine.AddGoFlagSet(goflag.CommandLine)
	// cliflag.InitFlags()
	logs.InitLogs()
	defer logs.FlushLogs()

	basename := filepath.Base(os.Args[0])
	if err := commandFor(basename, hyperkubeCommand, allCommandFns).Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
}
```

其中的 `commandFor` 只是比對指令的名稱罷了：

```go
func commandFor(basename string, defaultCommand *cobra.Command, commands []func() *cobra.Command) *cobra.Command {
	for _, commandFn := range commands {
		command := commandFn()
		if command.Name() == basename {
			return command
		}
		for _, alias := range command.Aliases {
			if alias == basename {
				return command
			}
		}
	}

	return defaultCommand
}
```

而 commands 則是事先註冊好的 callback 陣列：

```go
	commandFns := []func() *cobra.Command{
		apiserver,
		controller,
		proxy,
		scheduler,
		kubectlCmd,
		kubelet,
		cloudController,
	}
```

以 `proxy` 為例，它的定義為：

```go
	proxy := func() *cobra.Command {
		ret := kubeproxy.NewProxyCommand()
		// add back some unfortunate aliases that should be removed
		ret.Aliases = []string{"proxy"}
		return ret
	}
```

所以，我們能透過 kubeproxy package 找到 `NewProxyCommand()` 函式繼續研究 proxy 在做些什麼。接下來有興趣的部分是，apiserver 扮演著被大家 follow 的角色，其他元件都隱含著或直接指定了 `--master` 位置，目標就是為了與 apiserver 搭上線。而它們都聊些什麼呢？

## controller

[controller](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/hyperkube/main.go#L96-L101) 的定義如下：

```go
	controller := func() *cobra.Command {
		ret := kubecontrollermanager.NewControllerManagerCommand()
		// add back some unfortunate aliases that should be removed
		ret.Aliases = []string{"controller-manager"}
		return ret
	}
```

由 import 的宣告，可以知道它來自的 package：

```go
kubecontrollermanager "k8s.io/kubernetes/cmd/kube-controller-manager/app"
```

[NewControllerManagerCommand 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/controllermanager.go#L82-L140) 定義了一個 command 所需要的內容，對我們來說重點在部分在 `Run` callback：

```go
	cmd := &cobra.Command{
		Use: "kube-controller-manager",
		Long: `The Kubernetes controller manager is a daemon that embeds
the core control loops shipped with Kubernetes. In applications of robotics and
automation, a control loop is a non-terminating loop that regulates the state of
the system. In Kubernetes, a controller is a control loop that watches the shared
state of the cluster through the apiserver and makes changes attempting to move the
current state towards the desired state. Examples of controllers that ship with
Kubernetes today are the replication controller, endpoints controller, namespace
controller, and serviceaccounts controller.`,
		Run: func(cmd *cobra.Command, args []string) {
			verflag.PrintAndExitIfRequested()
			utilflag.PrintFlags(cmd.Flags())

			c, err := s.Config(KnownControllers(), ControllersDisabledByDefault.List())
			if err != nil {
				fmt.Fprintf(os.Stderr, "%v\n", err)
				os.Exit(1)
			}

			if err := Run(c.Complete(), wait.NeverStop); err != nil {
				fmt.Fprintf(os.Stderr, "%v\n", err)
				os.Exit(1)
			}
		},
	}
```

在 Run callback 內進行參數初始化，[最後委派給另一個 Run 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/controllermanager.go#L153-L267)，它顯然在同一個 package 內(這個例子是在同一個檔案內)。在 [s.Config(..)](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/options/options.go#L370-L411) 函式內，會建立大部分需要的 client 與 apiserver 開啟對話的連線：

```go
c, err := s.Config(KnownControllers(), ControllersDisabledByDefault.List())
```

### Config 與 client 們

在看 Config 的時候，可以順便學習各種常用 client 的建立方式 (之後也許能做做有趣的小實驗)，目標是建立 Config 結構的 instance：

```go
// Config is the main context object for the controller manager.
type Config struct {
	ComponentConfig kubectrlmgrconfig.KubeControllerManagerConfiguration

	SecureServing *apiserver.SecureServingInfo
	// LoopbackClientConfig is a config for a privileged loopback connection
	LoopbackClientConfig *restclient.Config

	// TODO: remove deprecated insecure serving
	InsecureServing *apiserver.DeprecatedInsecureServingInfo
	Authentication  apiserver.AuthenticationInfo
	Authorization   apiserver.AuthorizationInfo

	// the general kube client
	Client *clientset.Clientset

	// the client only used for leader election
	LeaderElectionClient *clientset.Clientset

	// the rest config for the master
	Kubeconfig *restclient.Config

	// the event sink
	EventRecorder record.EventRecorder
}
```

在上面結構的定義裡，有 3 個 client 端：

* Client
* LeaderElectionClient
* EventRecorder

先看第 1 個一般用途的 Client 如何建立：

```go
	kubeconfig, err := clientcmd.BuildConfigFromFlags(s.Master, s.Kubeconfig)
	if err != nil {
		return nil, err
	}
	kubeconfig.ContentConfig.ContentType = s.Generic.ClientConnection.ContentType
	kubeconfig.QPS = s.Generic.ClientConnection.QPS
	kubeconfig.Burst = int(s.Generic.ClientConnection.Burst)

	client, err := clientset.NewForConfig(restclient.AddUserAgent(kubeconfig, KubeControllerManagerUserAgent))
	if err != nil {
		return nil, err
	}
```

[BuildConfigFromFlags 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/staging/src/k8s.io/client-go/tools/clientcmd/client_config.go#L542-L559) 的實很簡短，參數就是來自 `--master` 與 `--kubeconfig`：

```go
// BuildConfigFromFlags is a helper function that builds configs from a master
// url or a kubeconfig filepath. These are passed in as command line flags for cluster
// components. Warnings should reflect this usage. If neither masterUrl or kubeconfigPath
// are passed in we fallback to inClusterConfig. If inClusterConfig fails, we fallback
// to the default config.
func BuildConfigFromFlags(masterUrl, kubeconfigPath string) (*restclient.Config, error) {
	if kubeconfigPath == "" && masterUrl == "" {
		klog.Warningf("Neither --kubeconfig nor --master was specified.  Using the inClusterConfig.  This might not work.")
		kubeconfig, err := restclient.InClusterConfig()
		if err == nil {
			return kubeconfig, nil
		}
		klog.Warning("error creating inClusterConfig, falling back to default config: ", err)
	}
	return NewNonInteractiveDeferredLoadingClientConfig(
		&ClientConfigLoadingRules{ExplicitPath: kubeconfigPath},
		&ConfigOverrides{ClusterInfo: clientcmdapi.Cluster{Server: masterUrl}}).ClientConfig()
}
```

有了 kubeconfig 就能使用 [clientset.NewForConfig(...)](https://github.com/kubernetes/kubernetes/blob/release-1.14/staging/src/k8s.io/client-go/kubernetes/clientset.go#L317-L467) 建出 client *set*：

```go
client, err := clientset.NewForConfig(restclient.AddUserAgent(kubeconfig, KubeControllerManagerUserAgent))
```

這 clientset 真不是叫假的，裡面真的有一堆的 client 啊！接下來的 `leaderElectionClient` 看起來也是 clientset 但使用的 user-agent 不一樣：

```go
leaderElectionClient := clientset.NewForConfigOrDie(restclient.AddUserAgent(&config, "leader-election"))
```

至於它為什麼叫 `NewForConfigOrDie` 看註解就會明白了，會丟 panics 出來：

```go
// NewForConfigOrDie creates a new Clientset for the given config and
// panics if there is an error in the config.
func NewForConfigOrDie(c *rest.Config) *Clientset {
    // ... skip ...
}
```

最後一個 EventRecorder 的建立是：

```go
eventRecorder := createRecorder(client, KubeControllerManagerUserAgent)
```

看實作，它是能接收某個 user-agent 來的 event：

```go
func createRecorder(kubeClient clientset.Interface, userAgent string) record.EventRecorder {
	eventBroadcaster := record.NewBroadcaster()
	eventBroadcaster.StartLogging(klog.Infof)
	eventBroadcaster.StartRecordingToSink(&v1core.EventSinkImpl{Interface: kubeClient.CoreV1().Events("")})
	return eventBroadcaster.NewRecorder(clientgokubescheme.Scheme, v1.EventSource{Component: userAgent})
}
```

PS. 目前我還沒能力分辨出它是收還是發 event。

### Run


```go
if err := Run(c.Complete(), wait.NeverStop); err != nil {
    fmt.Fprintf(os.Stderr, "%v\n", err)
    os.Exit(1)
}
```

```go
// Complete fills in any fields not set that are required to have valid data. It's mutating the receiver.
func (c *Config) Complete() *CompletedConfig {
	cc := completedConfig{c}

	apiserver.AuthorizeClientBearerToken(c.LoopbackClientConfig, &c.Authentication, &c.Authorization)

	return &CompletedConfig{&cc}
}
```

執行真實的 Run 之前，它先呼叫了 Complete，它做的事情是加上 Bearer Token。實際的 Run 實作真的挺複雜的，感覺上不插 debugger 會看不太懂了，先以肉眼追看看唄。

若不理會條件檢查與 leader election 的事情，主要工作會在 [run callback](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/controllermanager.go#L191-L225)：

```go
run := func(ctx context.Context) {
    rootClientBuilder := controller.SimpleControllerClientBuilder{
        ClientConfig: c.Kubeconfig,
    }
    var clientBuilder controller.ControllerClientBuilder
    if c.ComponentConfig.KubeCloudShared.UseServiceAccountCredentials {
        if len(c.ComponentConfig.SAController.ServiceAccountKeyFile) == 0 {
            // It'c possible another controller process is creating the tokens for us.
            // If one isn't, we'll timeout and exit when our client builder is unable to create the tokens.
            klog.Warningf("--use-service-account-credentials was specified without providing a --service-account-private-key-file")
        }
        clientBuilder = controller.SAControllerClientBuilder{
            ClientConfig:         restclient.AnonymousClientConfig(c.Kubeconfig),
            CoreClient:           c.Client.CoreV1(),
            AuthenticationClient: c.Client.AuthenticationV1(),
            Namespace:            "kube-system",
        }
    } else {
        clientBuilder = rootClientBuilder
    }    
    controllerContext, err := CreateControllerContext(c, rootClientBuilder, clientBuilder, ctx.Done())
    if err != nil {
        klog.Fatalf("error building controller context: %v", err)
    }
    saTokenControllerInitFunc := serviceAccountTokenControllerStarter{rootClientBuilder: rootClientBuilder}.startServiceAccountTokenController

    if err := StartControllers(controllerContext, saTokenControllerInitFunc, NewControllerInitializers(controllerContext.LoopMode), unsecuredMux); err != nil {
        klog.Fatalf("error starting controllers: %v", err)
    }

    controllerContext.InformerFactory.Start(controllerContext.Stop)
    close(controllerContext.InformersStarted)

    select {}
}
```

略過前半段建 clientBuilder 的話，那事情其實是由 CreateControllerContext 開始的，它建出 controllerContext 再來呼叫 [StartControllers](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/controllermanager.go#L461-L501) 本身就是跑個 loop 把給它的 controllers 啟動，而有哪些 controller 要看參數 [NewControllerInitializers 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-controller-manager/app/controllermanager.go#L341-L384)

```go
// NewControllerInitializers is a public map of named controller groups (you can start more than one in an init func)
// paired to their InitFunc.  This allows for structured downstream composition and subdivision.
func NewControllerInitializers(loopMode ControllerLoopMode) map[string]InitFunc {
	controllers := map[string]InitFunc{}
	controllers["endpoint"] = startEndpointController
	controllers["replicationcontroller"] = startReplicationController
	controllers["podgc"] = startPodGCController
	controllers["resourcequota"] = startResourceQuotaController
	controllers["namespace"] = startNamespaceController
	controllers["serviceaccount"] = startServiceAccountController
	controllers["garbagecollector"] = startGarbageCollectorController
	controllers["daemonset"] = startDaemonSetController
	controllers["job"] = startJobController
	controllers["deployment"] = startDeploymentController
	controllers["replicaset"] = startReplicaSetController
	controllers["horizontalpodautoscaling"] = startHPAController
	controllers["disruption"] = startDisruptionController
	controllers["statefulset"] = startStatefulSetController
	controllers["cronjob"] = startCronJobController
	controllers["csrsigning"] = startCSRSigningController
	controllers["csrapproving"] = startCSRApprovingController
	controllers["csrcleaner"] = startCSRCleanerController
	controllers["ttl"] = startTTLController
	controllers["bootstrapsigner"] = startBootstrapSignerController
	controllers["tokencleaner"] = startTokenCleanerController
	controllers["nodeipam"] = startNodeIpamController
	controllers["nodelifecycle"] = startNodeLifecycleController
	if loopMode == IncludeCloudLoops {
		controllers["service"] = startServiceController
		controllers["route"] = startRouteController
		controllers["cloud-node-lifecycle"] = startCloudNodeLifecycleController
		// TODO: volume controller into the IncludeCloudLoops only set.
	}
	controllers["persistentvolume-binder"] = startPersistentVolumeBinderController
	controllers["attachdetach"] = startAttachDetachController
	controllers["persistentvolume-expander"] = startVolumeExpandController
	controllers["clusterrole-aggregation"] = startClusterRoleAggregrationController
	controllers["pvc-protection"] = startPVCProtectionController
	controllers["pv-protection"] = startPVProtectionController
	controllers["ttl-after-finished"] = startTTLAfterFinishedController
	controllers["root-ca-cert-publisher"] = startRootCACertPublisher

	return controllers
}
```

雖然沒有完全理解 controller manager 如何運作 (leader election)，但看到上面的 map 應該有一種：『所有謎底都解開了的感覺』。那些在文件上看過得名稱，在這裡都出現了。