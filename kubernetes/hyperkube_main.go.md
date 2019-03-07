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

## proxy

proxy 是來自 kubeproxy package 的功能：

```go
proxy := func() *cobra.Command {
    ret := kubeproxy.NewProxyCommand()
    // add back some unfortunate aliases that should be removed
    ret.Aliases = []string{"proxy"}
    return ret
}
```

[NewProxyCommand 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-proxy/app/server.go#L441-L483) 內的重點如下：

```go
opts := NewOptions()

cmd := &cobra.Command{
    Use: "kube-proxy",
    Long: `The Kubernetes network proxy runs on each node. This
reflects services as defined in the Kubernetes API on each node and can do simple
TCP, UDP, and SCTP stream forwarding or round robin TCP, UDP, and SCTP forwarding across a set of backends.
Service cluster IPs and ports are currently found through Docker-links-compatible
environment variables specifying ports opened by the service proxy. There is an optional
addon that provides cluster DNS for these cluster IPs. The user must create a service
with the apiserver API to configure the proxy.`,
    Run: func(cmd *cobra.Command, args []string) {
        verflag.PrintAndExitIfRequested()
        utilflag.PrintFlags(cmd.Flags())

        if err := initForOS(opts.WindowsService); err != nil {
            klog.Fatalf("failed OS init: %v", err)
        }

        if err := opts.Complete(); err != nil {
            klog.Fatalf("failed complete: %v", err)
        }
        if err := opts.Validate(args); err != nil {
            klog.Fatalf("failed validate: %v", err)
        }
        klog.Fatal(opts.Run())
    },
}
```

將 Run 綁在 opts 雖然看起來不太直覺，但它就是這麼寫的啊！不過，整體的功能委派流程比 controller manager 簡單許多：

```go
func NewOptions() *Options {
	return &Options{
		config:      new(kubeproxyconfig.KubeProxyConfiguration),
		healthzPort: ports.ProxyHealthzPort,
		metricsPort: ports.ProxyStatusPort,
		scheme:      scheme.Scheme,
		codecs:      scheme.Codecs,
		CleanupIPVS: true,
		errCh:       make(chan error),
	}
}
```
```go
func (o *Options) Run() error {
	defer close(o.errCh)
	if len(o.WriteConfigTo) > 0 {
		return o.writeConfigFile()
	}

	proxyServer, err := NewProxyServer(o)
	if err != nil {
		return err
	}
	o.proxyServer = proxyServer
	return o.runLoop()
}
```

接著只要探索 [NewProxyServer 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-proxy/app/server_others.go#L54-L284) 在做些什麼就行了，它其實會呼叫內部的 newProxyServer 函式，實作上是一個 factory method，它會依 proxyMode 去建立不同的 proxy server。實作上透過 *getProxyMode* 函式決定要建立哪一種 proxy：

```go
func getProxyMode(proxyMode string, iptver iptables.IPTablesVersioner, khandle ipvs.KernelHandler, ipsetver ipvs.IPSetVersioner, kcompat iptables.KernelCompatTester) string {
	switch proxyMode {
	case proxyModeUserspace:
		return proxyModeUserspace
	case proxyModeIPTables:
		return tryIPTablesProxy(iptver, kcompat)
	case proxyModeIPVS:
		return tryIPVSProxy(iptver, khandle, ipsetver, kcompat)
	}
	klog.Warningf("Flag proxy-mode=%q unknown, assuming iptables proxy", proxyMode)
	return tryIPTablesProxy(iptver, kcompat)
}
```

proxy 元件的功能在於，如何反應使用者透過 kubectl 宣示目前要變更 service 狀態。所以 proxy 的實作得看得到這一塊的實作，在決定 proxy 之前，先建好了 recorder：

```go
	eventBroadcaster := record.NewBroadcaster()
	recorder := eventBroadcaster.NewRecorder(scheme, v1.EventSource{Component: "kube-proxy", Host: hostname})
```

到各別 proxy 的初始化時，綁定 event handler，以 iptables 為例：

```go
serviceEventHandler = proxierIPTables
endpointsEventHandler = proxierIPTables
```

在正式 [Run](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-proxy/app/server.go#L660-L677) 的時候，透過 informerFactory 綁定要接收的事件：

```go
informerFactory := informers.NewSharedInformerFactoryWithOptions(s.Client, s.ConfigSyncPeriod,
    informers.WithTweakListOptions(func(options *v1meta.ListOptions) {
        options.LabelSelector = "!" + apis.LabelServiceProxyName
    }))
    
// Create configs (i.e. Watches for Services and Endpoints)
// Note: RegisterHandler() calls need to happen before creation of Sources because sources
// only notify on changes, and the initial update (on process start) may be lost if no handlers
// are registered yet.
serviceConfig := config.NewServiceConfig(informerFactory.Core().V1().Services(), s.ConfigSyncPeriod)
serviceConfig.RegisterEventHandler(s.ServiceEventHandler)
go serviceConfig.Run(wait.NeverStop)

endpointsConfig := config.NewEndpointsConfig(informerFactory.Core().V1().Endpoints(), s.ConfigSyncPeriod)
endpointsConfig.RegisterEventHandler(s.EndpointsEventHandler)
go endpointsConfig.Run(wait.NeverStop)

// This has to start after the calls to NewServiceConfig and NewEndpointsConfig because those
// functions must configure their shared informer event handlers first.
go informerFactory.Start(wait.NeverStop)

// Birth Cry after the birth is successful
s.birthCry()
```

其中 birthCry：

```go
func (s *ProxyServer) birthCry() {
	s.Recorder.Eventf(s.NodeRef, api.EventTypeNormal, "Starting", "Starting kube-proxy.")
}
```

目前看起來可以推測 Recorder 能用來發 event 而 informers 能用來收 event。

## scheduler

經過前的探索後，對於它的寫法有些熟悉感了，在 kubescheduler package 下能找得到 [NewSchedulerCommand 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-scheduler/app/server.go#L62-L106)

```go
scheduler := func() *cobra.Command {
    ret := kubescheduler.NewSchedulerCommand()
    // add back some unfortunate aliases that should be removed
    ret.Aliases = []string{"scheduler"}
    return ret
}
```

同樣的 trace 流程，我們可以略過 Command 本身的 Run callback 找到它派委的對象 [Run 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kube-scheduler/app/server.go#L159)。

在最開頭有個超巨大的 *New 方法*，塞了超多 informer 跟一堆參數：

```go
// Create the scheduler.
sched, err := scheduler.New(cc.Client,
    cc.InformerFactory.Core().V1().Nodes(),
    cc.PodInformer,
    cc.InformerFactory.Core().V1().PersistentVolumes(),
    cc.InformerFactory.Core().V1().PersistentVolumeClaims(),
    cc.InformerFactory.Core().V1().ReplicationControllers(),
    cc.InformerFactory.Apps().V1().ReplicaSets(),
    cc.InformerFactory.Apps().V1().StatefulSets(),
    cc.InformerFactory.Core().V1().Services(),
    cc.InformerFactory.Policy().V1beta1().PodDisruptionBudgets(),
    cc.InformerFactory.Storage().V1().StorageClasses(),
    cc.Recorder,
    cc.ComponentConfig.AlgorithmSource,
    stopCh,
    scheduler.WithName(cc.ComponentConfig.SchedulerName),
    scheduler.WithHardPodAffinitySymmetricWeight(cc.ComponentConfig.HardPodAffinitySymmetricWeight),
    scheduler.WithPreemptionDisabled(cc.ComponentConfig.DisablePreemption),
    scheduler.WithPercentageOfNodesToScore(cc.ComponentConfig.PercentageOfNodesToScore),
    scheduler.WithBindTimeoutSeconds(*cc.ComponentConfig.BindTimeoutSeconds))
if err != nil {
    return err
```

實際可以執行時是呼叫 run callback (它同樣也是要通過 leader election 才會執行到)：

```go
run := func(ctx context.Context) {
    sched.Run()
    <-ctx.Done()
}
```

所以，要知道 scheduler 在忙什麼，我們得看一下它的 [Run 方法](https://github.com/kubernetes/kubernetes/blob/release-1.14/pkg/scheduler/scheduler.go#L248) 才行了。

```go
// Run begins watching and scheduling. It waits for cache to be synced, then starts a goroutine and returns immediately.
func (sched *Scheduler) Run() {
	if !sched.config.WaitForCacheSync() {
		return
	}

	go wait.Until(sched.scheduleOne, 0, sched.config.StopEverything)
}
```

看起來是會一直呼叫 callback [scheduleOne](https://github.com/kubernetes/kubernetes/blob/release-1.14/pkg/scheduler/scheduler.go#L434)：

```go
// scheduleOne does the entire scheduling workflow for a single pod.  It is serialized on the scheduling algorithm's host fitting.
func (sched *Scheduler) scheduleOne() {
	plugins := sched.config.PluginSet
	// Remove all plugin context data at the beginning of a scheduling cycle.
	if plugins.Data().Ctx != nil {
		plugins.Data().Ctx.Reset()
	}
```
在一開始，先重設 plugins 的 context data (目前還不知道 plugin 是做什麼用的)

```go
	pod := sched.config.NextPod()
	// pod could be nil when schedulerQueue is closed
	if pod == nil {
		return
	}
	if pod.DeletionTimestamp != nil {
		sched.config.Recorder.Eventf(pod, v1.EventTypeWarning, "FailedScheduling", "skip schedule deleting pod: %v/%v", pod.Namespace, pod.Name)
		klog.V(3).Infof("Skip schedule deleting pod: %v/%v", pod.Namespace, pod.Name)
		return
	}
```

透過 `.NextPod()` 取得下一個需要調度的 schedule

```go
	klog.V(3).Infof("Attempting to schedule pod: %v/%v", pod.Namespace, pod.Name)

	// Synchronously attempt to find a fit for the pod.
	start := time.Now()
    scheduleResult, err := sched.schedule(pod)
```

透過 *schedule 方法* 來調度 pod，如果有錯過則做：

```go
	if err != nil {
		// schedule() may have failed because the pod would not fit on any host, so we try to
		// preempt, with the expectation that the next time the pod is tried for scheduling it
		// will fit due to the preemption. It is also possible that a different pod will schedule
		// into the resources that were preempted, but this is harmless.
		if fitError, ok := err.(*core.FitError); ok {
			if !util.PodPriorityEnabled() || sched.config.DisablePreemption {
				klog.V(3).Infof("Pod priority feature is not enabled or preemption is disabled by scheduler configuration." +
					" No preemption is performed.")
			} else {
				preemptionStartTime := time.Now()
				sched.preempt(pod, fitError)
				metrics.PreemptionAttempts.Inc()
				metrics.SchedulingAlgorithmPremptionEvaluationDuration.Observe(metrics.SinceInSeconds(preemptionStartTime))
				metrics.DeprecatedSchedulingAlgorithmPremptionEvaluationDuration.Observe(metrics.SinceInMicroseconds(preemptionStartTime))
				metrics.SchedulingLatency.WithLabelValues(metrics.PreemptionEvaluation).Observe(metrics.SinceInSeconds(preemptionStartTime))
				metrics.DeprecatedSchedulingLatency.WithLabelValues(metrics.PreemptionEvaluation).Observe(metrics.SinceInSeconds(preemptionStartTime))
			}
			// Pod did not fit anywhere, so it is counted as a failure. If preemption
			// succeeds, the pod should get counted as a success the next time we try to
			// schedule it. (hopefully)
			metrics.PodScheduleFailures.Inc()
		} else {
			klog.Errorf("error selecting node for pod: %v", err)
			metrics.PodScheduleErrors.Inc()
		}
		return
    }
```

如果調度成功了，那就繼續後續的處理：

```go
	metrics.SchedulingAlgorithmLatency.Observe(metrics.SinceInSeconds(start))
	metrics.DeprecatedSchedulingAlgorithmLatency.Observe(metrics.SinceInMicroseconds(start))
	// Tell the cache to assume that a pod now is running on a given node, even though it hasn't been bound yet.
	// This allows us to keep scheduling without waiting on binding to occur.
	assumedPod := pod.DeepCopy()

	// Assume volumes first before assuming the pod.
	//
	// If all volumes are completely bound, then allBound is true and binding will be skipped.
	//
	// Otherwise, binding of volumes is started after the pod is assumed, but before pod binding.
	//
	// This function modifies 'assumedPod' if volume binding is required.
	allBound, err := sched.assumeVolumes(assumedPod, scheduleResult.SuggestedHost)
	if err != nil {
		klog.Errorf("error assuming volumes: %v", err)
		metrics.PodScheduleErrors.Inc()
		return
	}

	// Run "reserve" plugins.
	for _, pl := range plugins.ReservePlugins() {
		if err := pl.Reserve(plugins, assumedPod, scheduleResult.SuggestedHost); err != nil {
			klog.Errorf("error while running %v reserve plugin for pod %v: %v", pl.Name(), assumedPod.Name, err)
			sched.recordSchedulingFailure(assumedPod, err, SchedulerError,
				fmt.Sprintf("reserve plugin %v failed", pl.Name()))
			metrics.PodScheduleErrors.Inc()
			return
		}
    }
```

上面的 volumes 與 plugin 部分，還沒追進去看。接著透過 *assume 方法* 指定 node 名稱 (但還沒開始 binding node)

```go
	// assume modifies `assumedPod` by setting NodeName=scheduleResult.SuggestedHost
	err = sched.assume(assumedPod, scheduleResult.SuggestedHost)
	if err != nil {
		klog.Errorf("error assuming pod: %v", err)
		metrics.PodScheduleErrors.Inc()
		return
    }
```

真正的 binding node 是在 go runtine 內做：

```go
	// bind the pod to its host asynchronously (we can do this b/c of the assumption step above).
	go func() {
		// Bind volumes first before Pod
		if !allBound {
			err := sched.bindVolumes(assumedPod)
			if err != nil {
				klog.Errorf("error binding volumes: %v", err)
				metrics.PodScheduleErrors.Inc()
				return
			}
		}

		// Run "prebind" plugins.
		for _, pl := range plugins.PrebindPlugins() {
			approved, err := pl.Prebind(plugins, assumedPod, scheduleResult.SuggestedHost)
			if err != nil {
				approved = false
				klog.Errorf("error while running %v prebind plugin for pod %v: %v", pl.Name(), assumedPod.Name, err)
				metrics.PodScheduleErrors.Inc()
			}
			if !approved {
				sched.Cache().ForgetPod(assumedPod)
				var reason string
				if err == nil {
					msg := fmt.Sprintf("prebind plugin %v rejected pod %v.", pl.Name(), assumedPod.Name)
					klog.V(4).Infof(msg)
					err = errors.New(msg)
					reason = v1.PodReasonUnschedulable
				} else {
					reason = SchedulerError
				}
				sched.recordSchedulingFailure(assumedPod, err, reason, err.Error())
				return
			}
		}

		err := sched.bind(assumedPod, &v1.Binding{
			ObjectMeta: metav1.ObjectMeta{Namespace: assumedPod.Namespace, Name: assumedPod.Name, UID: assumedPod.UID},
			Target: v1.ObjectReference{
				Kind: "Node",
				Name: scheduleResult.SuggestedHost,
			},
		})
		metrics.E2eSchedulingLatency.Observe(metrics.SinceInSeconds(start))
		metrics.DeprecatedE2eSchedulingLatency.Observe(metrics.SinceInMicroseconds(start))
		if err != nil {
			klog.Errorf("error binding pod: %v", err)
			metrics.PodScheduleErrors.Inc()
		} else {
			klog.V(2).Infof("pod %v/%v is bound successfully on node %v, %d nodes evaluated, %d nodes were found feasible", assumedPod.Namespace, assumedPod.Name, scheduleResult.SuggestedHost, scheduleResult.EvaluatedNodes, scheduleResult.FeasibleNodes)
			metrics.PodScheduleSuccesses.Inc()
		}
	}()
}
```

* 透過每 1 個 `plugins.PrebindPlugins()` 確認，是否能執行 binding。每 1 個都同意才會執行到 bind 的動作
* sched.bind 會將 pod 與 node 綁定



### schedule 演算法

在 schedule 方法中，它會呼叫 `sched.config.Algorithm.Schedule` 來進行調度：

```go
// schedule implements the scheduling algorithm and returns the suggested result(host,
// evaluated nodes number,feasible nodes number).
func (sched *Scheduler) schedule(pod *v1.Pod) (core.ScheduleResult, error) {
	result, err := sched.config.Algorithm.Schedule(pod, sched.config.NodeLister)
	if err != nil {
		pod = pod.DeepCopy()
		sched.recordSchedulingFailure(pod, err, v1.PodReasonUnschedulable, err.Error())
		return core.ScheduleResult{}, err
	}
	return result, err
}
```

## kubelet

kubelet 部分，直接委派給 [NewKubeletCommand 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kubelet/app/server.go#L108)

```go
kubelet := func() *cobra.Command { return kubelet.NewKubeletCommand(stopCh) }
```

實作委派給了 [run 函式](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/kubelet/app/server.go#L479)

(TBD)