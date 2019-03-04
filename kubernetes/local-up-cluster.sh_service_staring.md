# service starting

接續著 [local-up-cluster.sh.md](local-up-cluster.sh.md) 中的筆記，繼續探索服務啟動的流程：

* start_etcd
* set_service_accounts (不算是啟動，但在設定帳號)
* start_apiserver
* start_controller_manager
* start_cloud_controller_manager (EXTERNAL_CLOUD_PROVIDER)
* start_kubeproxy
* start_kubescheduler
* start_kubedns
* start_nodelocaldns (ENABLE_NODELOCAL_DNS)
* start_kubedashboard

## start_etcd

```bash
function start_etcd {
    echo "Starting etcd"
    ETCD_LOGFILE=${LOG_DIR}/etcd.log
    kube::etcd::start
}
```

其中 `kube::etcd::start` 來自 [hack/lib/etcd.sh](https://github.com/kubernetes/kubernetes/blob/release-1.14/hack/lib/etcd.sh)：

```bash
kube::etcd::start() {
  # validate before running
  kube::etcd::validate

  # Start etcd
  ETCD_DIR=${ETCD_DIR:-$(mktemp -d 2>/dev/null || mktemp -d -t test-etcd.XXXXXX)}
  if [[ -d "${ARTIFACTS_DIR:-}" ]]; then
    ETCD_LOGFILE="${ARTIFACTS_DIR}/etcd.$(uname -n).$(id -un).log.DEBUG.$(date +%Y%m%d-%H%M%S).$$"
  else
    ETCD_LOGFILE=${ETCD_LOGFILE:-"/dev/null"}
  fi
  kube::log::info "etcd --advertise-client-urls ${KUBE_INTEGRATION_ETCD_URL} --data-dir ${ETCD_DIR} --listen-client-urls http://${ETCD_HOST}:${ETCD_PORT} --debug > \"${ETCD_LOGFILE}\" 2>/dev/null"
  etcd --advertise-client-urls ${KUBE_INTEGRATION_ETCD_URL} --data-dir ${ETCD_DIR} --listen-client-urls ${KUBE_INTEGRATION_ETCD_URL} --debug 2> "${ETCD_LOGFILE}" >/dev/null &
  ETCD_PID=$!

  echo "Waiting for etcd to come up."
  kube::util::wait_for_url "${KUBE_INTEGRATION_ETCD_URL}/v2/machines" "etcd: " 0.25 80
  curl -fs -X PUT "${KUBE_INTEGRATION_ETCD_URL}/v2/keys/_test"
}
```

### kube::etcd::validate

```bash
kube::etcd::validate() {
  # validate if in path
  command -v etcd >/dev/null || {
    kube::log::usage "etcd must be in your PATH"
    kube::log::info "You can use 'hack/install-etcd.sh' to install a copy in third_party/."
    exit 1
  }
```

同樣使用 `command -v` 查看是否能找到 etcd。這真的超好用的啊！以前只會用 whereis 然後還找不到程式。

```bash

  # validate etcd port is free
  local port_check_command
  if command -v ss &> /dev/null && ss -Version | grep 'iproute2' &> /dev/null; then
    port_check_command="ss"
  elif command -v netstat &>/dev/null; then
    port_check_command="netstat"
  else
    kube::log::usage "unable to identify if etcd is bound to port ${ETCD_PORT}. unable to find ss or netstat utilities."
    exit 1
  fi
  if ${port_check_command} -nat | grep "LISTEN" | grep "[\.:]${ETCD_PORT:?}" >/dev/null 2>&1; then
    kube::log::usage "unable to start etcd as port ${ETCD_PORT} is in use. please stop the process listening on this port and retry."
    kube::log::usage "$(netstat -nat | grep "[\.:]${ETCD_PORT:?} .*LISTEN")"
    exit 1
  fi
```

在這一段要來驗證有沒有其他程式佔據了 `ETCD_PORT`，它試了 2 個指令，一個是 `ss` 另一個是我常用的 `netstat`。

對 `ss` 覺得比較陌生，osx 上預設沒裝，找了找 linux server 跑看看：

```
qrtt1@bot9:~$ ss -Version
ss utility, iproute2-ss180129
qrtt1@bot9:~$ ss -nat | grep :5566
LISTEN      0        128             127.0.0.1:5566              0.0.0.0:*
LISTEN      0        128                 [::1]:5566                 [::]:*
```


```bash

  # validate installed version is at least equal to minimum
  version=$(etcd --version | tail -n +1 | head -n 1 | cut -d " " -f 3)
  if [[ $(kube::etcd::version "${ETCD_VERSION}") -gt $(kube::etcd::version "${version}") ]]; then
   export PATH=${KUBE_ROOT}/third_party/etcd:${PATH}
   hash etcd
   echo "${PATH}"
   version=$(etcd --version | head -n 1 | cut -d " " -f 3)
   if [[ $(kube::etcd::version "${ETCD_VERSION}") -gt $(kube::etcd::version "${version}") ]]; then
    kube::log::usage "etcd version ${ETCD_VERSION} or greater required."
    kube::log::info "You can use 'hack/install-etcd.sh' to install a copy in third_party/."
    exit 1
   fi
  fi
}
```

這一段主要在檢查 etcd 的版本有沒有符合最低需求。

```
hash etcd
```

看起來是在檢查，etcd 有沒有在 PATH 路徑內而已，在一台未有 etcd 的機器試跑：

```
qty:~ qrtt1$ hash etcd
-bash: hash: etcd: not found
```

### etcd 啟動參數

```bash
  kube::log::info "etcd --advertise-client-urls ${KUBE_INTEGRATION_ETCD_URL} --data-dir ${ETCD_DIR} --listen-client-urls http://${ETCD_HOST}:${ETCD_PORT} --debug > \"${ETCD_LOGFILE}\" 2>/dev/null"
  etcd --advertise-client-urls ${KUBE_INTEGRATION_ETCD_URL} --data-dir ${ETCD_DIR} --listen-client-urls ${KUBE_INTEGRATION_ETCD_URL} --debug 2> "${ETCD_LOGFILE}" >/dev/null &
  ETCD_PID=$!
```

這主要是設定 etcd 啟動時，會透過 `KUBE_INTEGRATION_ETCD_URL` 位置起個 http 服務與資料存放位置的設定。不過，在目前閱讀的版本發現 log 與實際 command 部分長得不同，應該是[重構時忘了改 log 訊息引用的變數](https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/lib/etcd.sh#L78-L79)。

啟動完成後，利用 `$!` 取得 pid (又學到了新東西)。

### 等待 etcd 啟動

```bash
  echo "Waiting for etcd to come up."
  kube::util::wait_for_url "${KUBE_INTEGRATION_ETCD_URL}/v2/machines" "etcd: " 0.25 80
  curl -fs -X PUT "${KUBE_INTEGRATION_ETCD_URL}/v2/keys/_test"
```

```bash
kube::util::wait_for_url() {
  local url=$1
  local prefix=${2:-}
  local wait=${3:-1}
  local times=${4:-30}
  local maxtime=${5:-1}

  which curl >/dev/null || {
    kube::log::usage "curl must be installed"
    exit 1
  }

  local i
  for i in $(seq 1 "$times"); do
    local out
    if out=$(curl --max-time "$maxtime" -gkfs "$url" 2>/dev/null); then
      kube::log::status "On try ${i}, ${prefix}: ${out}"
      return 0
    fi
    sleep "${wait}"
  done
  kube::log::error "Timed out waiting for ${prefix} to answer at ${url}; tried ${times} waiting ${wait} between each"
  return 1
}
```

在這裡看到用 `which curl` 來查程式有沒有安裝，不道跟先前看過的 `command -v` 有沒有應用情境上的區別呢？而 curl 有 `--max-time` 參數可以指定最大等待的時間，挺實用新知 :D

而 curl 後加的 `-gkfs` 則是：

```
       -g, --globoff
              This option switches off the "URL globbing parser". When you set
              this  option, you can specify URLs that contain the letters {}[]
              without having them being interpreted by curl itself. Note  that
              these  letters are not normal legal URL contents but they should
              be encoded according to the URI standard.
```

看起來 `-g` 的用法，是不要對 URL 內的 `{}` 或 `[]` 做特殊的處理，通常它是用 pattern 來代表一堆 URL 用的。

```
       -k, --insecure
              (TLS) By default, every SSL connection curl makes is verified to
              be secure. This option allows curl to proceed and  operate  even
              for server connections otherwise considered insecure.

              The  server  connection  is verified by making sure the server's
              certificate contains the right name  and  verifies  successfully
              using the cert store.

              See this online resource for further details:
               https://curl.haxx.se/docs/sslcerts.html

              See also --proxy-insecure and --cacert.
```

`-k` 很好理解，這常用啊。特別是遇到一些自簽憑證的 URL 時。

```
       -f, --fail
              (HTTP)  Fail  silently (no output at all) on server errors. This is mostly done to better enable
              scripts etc to better deal with failed attempts. In normal cases when an HTTP  server  fails  to
              deliver  a  document, it returns an HTML document stating so (which often also describes why and
              more). This flag will prevent curl from outputting that and return error 22.

              This method is not fail-safe and there are occasions where non-successful  response  codes  will
              slip through, especially when authentication is involved (response codes 401 and 407).
```
```
       -s, --silent
              Silent  or  quiet  mode.  Don't show progress meter or error messages.  Makes Curl mute. It will
              still output the data you ask for, potentially even to the terminal/stdout unless  you  redirect
              it.

              Use  -S,  --show-error in addition to this option to disable progress meter but still show error
              messages.

              See also -v, --verbose and --stderr.
```

上面 2 個都是 slient 的用途唄。`-f` 是失敗時不出聲 `-s` 成功的情況也不要印出任何東西。

## set_service_accounts

```bash
function set_service_accounts {
    SERVICE_ACCOUNT_LOOKUP=${SERVICE_ACCOUNT_LOOKUP:-true}
    SERVICE_ACCOUNT_KEY=${SERVICE_ACCOUNT_KEY:-/tmp/kube-serviceaccount.key}
    # Generate ServiceAccount key if needed
    if [[ ! -f "${SERVICE_ACCOUNT_KEY}" ]]; then
      mkdir -p "$(dirname ${SERVICE_ACCOUNT_KEY})"
      openssl genrsa -out "${SERVICE_ACCOUNT_KEY}" 2048 2>/dev/null
    fi
}
```

看起來只是在指定的位置產生 rsa key，執行起來會是這樣的感覺：

```
qty:kubernetes qrtt1$ openssl genrsa -out k8s.key 2048
Generating RSA private key, 2048 bit long modulus
.........+++++
................+++++
e is 65537 (0x10001)
```

至於 kubernetes 要怎麼用它，得到找時間了解一下。目前的 script 可以知道它用在：

* apiserver
* controller-manager

以上二個元件的啟動參數

```
qty:kubernetes qrtt1$ grep -B10 -A3 SERVICE_ACCOUNT_KEY hack/local-up-cluster.sh

    APISERVER_LOG=${LOG_DIR}/kube-apiserver.log
    ${CONTROLPLANE_SUDO} "${GO_OUT}/hyperkube" apiserver ${swagger_arg} ${authorizer_arg} ${priv_arg} ${runtime_config} \
      ${cloud_config_arg} \
      ${advertise_address} \
      ${node_port_range} \
      --v=${LOG_LEVEL} \
      --vmodule="${LOG_SPEC}" \
      --cert-dir="${CERT_DIR}" \
      --client-ca-file="${CERT_DIR}/client-ca.crt" \
      --service-account-key-file="${SERVICE_ACCOUNT_KEY}" \
      --service-account-lookup="${SERVICE_ACCOUNT_LOOKUP}" \
      --enable-admission-plugins="${ENABLE_ADMISSION_PLUGINS}" \
      --disable-admission-plugins="${DISABLE_ADMISSION_PLUGINS}" \
--
--
    if [[ "${EXTERNAL_CLOUD_PROVIDER:-}" == "true" ]]; then
      cloud_config_arg="--cloud-provider=external"
      cloud_config_arg+=" --external-cloud-volume-plugin=${CLOUD_PROVIDER}"
      cloud_config_arg+=" --cloud-config=${CLOUD_CONFIG}"
    fi

    CTLRMGR_LOG=${LOG_DIR}/kube-controller-manager.log
    ${CONTROLPLANE_SUDO} "${GO_OUT}/hyperkube" controller-manager \
      --v=${LOG_LEVEL} \
      --vmodule="${LOG_SPEC}" \
      --service-account-private-key-file="${SERVICE_ACCOUNT_KEY}" \
      --root-ca-file="${ROOT_CA_FILE}" \
      --cluster-signing-cert-file="${CLUSTER_SIGNING_CERT_FILE}" \
      --cluster-signing-key-file="${CLUSTER_SIGNING_KEY_FILE}" \
```

## start_apiserver

start_apiserver 是一個很長的函式，瞄了一下大致分為 3 個部分：

* 準備啟動參數 (前面一堆的 `if` 是在做這件事) 與設定檔
* 啟動 api server
* 啟動後的配置

apiserver 的參數實在有多，到得再挖 [source code]((https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/hyperkube/main.go#L90)) 研究了。

```bash
function start_apiserver {
    security_admission=""
    if [[ -n "${DENY_SECURITY_CONTEXT_ADMISSION}" ]]; then
      security_admission=",SecurityContextDeny"
    fi
    if [[ -n "${PSP_ADMISSION}" ]]; then
      security_admission=",PodSecurityPolicy"
    fi
    if [[ -n "${NODE_ADMISSION}" ]]; then
      security_admission=",NodeRestriction"
    fi
    if [ "${ENABLE_POD_PRIORITY_PREEMPTION}" == true ]; then
      security_admission=",Priority"
      if [[ -n "${RUNTIME_CONFIG}" ]]; then
          RUNTIME_CONFIG+=","
      fi
      RUNTIME_CONFIG+="scheduling.k8s.io/v1alpha1=true"
    fi

    # Append security_admission plugin
    ENABLE_ADMISSION_PLUGINS="${ENABLE_ADMISSION_PLUGINS}${security_admission}"

    authorizer_arg=""
    if [[ -n "${AUTHORIZATION_MODE}" ]]; then
      authorizer_arg="--authorization-mode=${AUTHORIZATION_MODE} "
    fi
    priv_arg=""
    if [[ -n "${ALLOW_PRIVILEGED}" ]]; then
      priv_arg="--allow-privileged=${ALLOW_PRIVILEGED} "
    fi

    runtime_config=""
    if [[ -n "${RUNTIME_CONFIG}" ]]; then
      runtime_config="--runtime-config=${RUNTIME_CONFIG}"
    fi

    # Let the API server pick a default address when API_HOST_IP
    # is set to 127.0.0.1
    advertise_address=""
    if [[ "${API_HOST_IP}" != "127.0.0.1" ]]; then
        advertise_address="--advertise-address=${API_HOST_IP}"
    fi
    if [[ "${ADVERTISE_ADDRESS}" != "" ]] ; then
        advertise_address="--advertise-address=${ADVERTISE_ADDRESS}"
    fi
    node_port_range=""
    if [[ "${NODE_PORT_RANGE}" != "" ]] ; then
        node_port_range="--service-node-port-range=${NODE_PORT_RANGE}"
    fi

    if [[ "${REUSE_CERTS}" != true ]]; then
      # Create Certs
      generate_certs
    fi

    cloud_config_arg="--cloud-provider=${CLOUD_PROVIDER} --cloud-config=${CLOUD_CONFIG}"
    if [[ "${EXTERNAL_CLOUD_PROVIDER:-}" == "true" ]]; then
      cloud_config_arg="--cloud-provider=external"
    fi

    if [[ -n "${AUDIT_POLICY_FILE}" ]]; then
      cat <<EOF > /tmp/kube-audit-policy-file
# Log all requests at the Metadata level.
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
EOF
      AUDIT_POLICY_FILE="/tmp/kube-audit-policy-file"
    fi

    APISERVER_LOG=${LOG_DIR}/kube-apiserver.log
    ${CONTROLPLANE_SUDO} "${GO_OUT}/hyperkube" apiserver ${authorizer_arg} ${priv_arg} ${runtime_config} \
      ${cloud_config_arg} \
      ${advertise_address} \
      ${node_port_range} \
      --v=${LOG_LEVEL} \
      --vmodule="${LOG_SPEC}" \
      --audit-policy-file="${AUDIT_POLICY_FILE}" \
      --audit-log-path=${LOG_DIR}/kube-apiserver-audit.log \
      --cert-dir="${CERT_DIR}" \
      --client-ca-file="${CERT_DIR}/client-ca.crt" \
      --kubelet-client-certificate="${CERT_DIR}/client-kube-apiserver.crt" \
      --kubelet-client-key="${CERT_DIR}/client-kube-apiserver.key" \
      --service-account-key-file="${SERVICE_ACCOUNT_KEY}" \
      --service-account-lookup="${SERVICE_ACCOUNT_LOOKUP}" \
      --enable-admission-plugins="${ENABLE_ADMISSION_PLUGINS}" \
      --disable-admission-plugins="${DISABLE_ADMISSION_PLUGINS}" \
      --admission-control-config-file="${ADMISSION_CONTROL_CONFIG_FILE}" \
      --bind-address="${API_BIND_ADDR}" \
      --secure-port="${API_SECURE_PORT}" \
      --tls-cert-file="${CERT_DIR}/serving-kube-apiserver.crt" \
      --tls-private-key-file="${CERT_DIR}/serving-kube-apiserver.key" \
      --insecure-bind-address="${API_HOST_IP}" \
      --insecure-port="${API_PORT}" \
      --storage-backend=${STORAGE_BACKEND} \
      --storage-media-type=${STORAGE_MEDIA_TYPE} \
      --etcd-servers="http://${ETCD_HOST}:${ETCD_PORT}" \
      --service-cluster-ip-range="${SERVICE_CLUSTER_IP_RANGE}" \
      --feature-gates="${FEATURE_GATES}" \
      --external-hostname="${EXTERNAL_HOSTNAME}" \
      --requestheader-username-headers=X-Remote-User \
      --requestheader-group-headers=X-Remote-Group \
      --requestheader-extra-headers-prefix=X-Remote-Extra- \
      --requestheader-client-ca-file="${CERT_DIR}/request-header-ca.crt" \
      --requestheader-allowed-names=system:auth-proxy \
      --proxy-client-cert-file="${CERT_DIR}/client-auth-proxy.crt" \
      --proxy-client-key-file="${CERT_DIR}/client-auth-proxy.key" \
      --cors-allowed-origins="${API_CORS_ALLOWED_ORIGINS}" >"${APISERVER_LOG}" 2>&1 &
    APISERVER_PID=$!

    # Wait for kube-apiserver to come up before launching the rest of the components.
    echo "Waiting for apiserver to come up"
    kube::util::wait_for_url "https://${API_HOST_IP}:${API_SECURE_PORT}/healthz" "apiserver: " 1 ${WAIT_FOR_URL_API_SERVER} ${MAX_TIME_FOR_URL_API_SERVER} \
        || { echo "check apiserver logs: ${APISERVER_LOG}" ; exit 1 ; }

    # Create kubeconfigs for all components, using client certs
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" admin
    ${CONTROLPLANE_SUDO} chown "${USER}" "${CERT_DIR}/client-admin.key" # make readable for kubectl
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" kube-proxy
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" controller
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" scheduler

    if [[ -z "${AUTH_ARGS}" ]]; then
        AUTH_ARGS="--client-key=${CERT_DIR}/client-admin.key --client-certificate=${CERT_DIR}/client-admin.crt"
    fi

    # Grant apiserver permission to speak to the kubelet
    ${KUBECTL} --kubeconfig "${CERT_DIR}/admin.kubeconfig" create clusterrolebinding kube-apiserver-kubelet-admin --clusterrole=system:kubelet-api-admin --user=kube-apiserver

    ${CONTROLPLANE_SUDO} cp "${CERT_DIR}/admin.kubeconfig" "${CERT_DIR}/admin-kube-aggregator.kubeconfig"
    ${CONTROLPLANE_SUDO} chown $(whoami) "${CERT_DIR}/admin-kube-aggregator.kubeconfig"
    ${KUBECTL} config set-cluster local-up-cluster --kubeconfig="${CERT_DIR}/admin-kube-aggregator.kubeconfig" --server="https://${API_HOST_IP}:31090"
    echo "use 'kubectl --kubeconfig=${CERT_DIR}/admin-kube-aggregator.kubeconfig' to use the aggregated API server"

}
```

暫時略過 apiserver 本身，先關注在它之後發生的動作們：

> Create kubeconfigs for all components, using client certs

```bash
    # Create kubeconfigs for all components, using client certs
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" admin
    ${CONTROLPLANE_SUDO} chown "${USER}" "${CERT_DIR}/client-admin.key" # make readable for kubectl
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" kube-proxy
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" controller
    kube::util::write_client_kubeconfig "${CONTROLPLANE_SUDO}" "${CERT_DIR}" "${ROOT_CA_FILE}" "${API_HOST}" "${API_SECURE_PORT}" scheduler
```

### kube::util::write_client_kubeconfig

```bash
# creates a self-contained kubeconfig: args are sudo, dest-dir, ca file, host, port, client id, token(optional)
function kube::util::write_client_kubeconfig {
    local sudo=$1
    local dest_dir=$2
    local ca_file=$3
    local api_host=$4
    local api_port=$5
    local client_id=$6
    local token=${7:-}
    cat <<EOF | ${sudo} tee "${dest_dir}"/${client_id}.kubeconfig > /dev/null
apiVersion: v1
kind: Config
clusters:
  - cluster:
      certificate-authority: ${ca_file}
      server: https://${api_host}:${api_port}/
    name: local-up-cluster
users:
  - user:
      token: ${token}
      client-certificate: ${dest_dir}/client-${client_id}.crt
      client-key: ${dest_dir}/client-${client_id}.key
    name: local-up-cluster
contexts:
  - context:
      cluster: local-up-cluster
      user: local-up-cluster
    name: local-up-cluster
current-context: local-up-cluster
EOF

    # flatten the kubeconfig files to make them self contained
    username=$(whoami)
    ${sudo} /usr/bin/env bash -e <<EOF
    $(kube::util::find-binary kubectl) --kubeconfig="${dest_dir}/${client_id}.kubeconfig" config view --minify --flatten > "/tmp/${client_id}.kubeconfig"
    mv -f "/tmp/${client_id}.kubeconfig" "${dest_dir}/${client_id}.kubeconfig"
    chown ${username} "${dest_dir}/${client_id}.kubeconfig"
EOF
}
```

這部分是在設定 cluster 連線方式，可以參考官網文件 [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)，由於這是針對 client 端的設定，我們能在 [client-go 裡的 v1/types.go](https://github.com/kubernetes/kubernetes/blob/release-1.14/staging/src/k8s.io/client-go/tools/clientcmd/api/v1/types.go) 找到它的 struct 定義。


### apiserver to kubelet

```bash
    # Grant apiserver permission to speak to the kubelet
    ${KUBECTL} --kubeconfig "${CERT_DIR}/admin.kubeconfig" create clusterrolebinding kube-apiserver-kubelet-admin --clusterrole=system:kubelet-api-admin --user=kube-apiserver

    ${CONTROLPLANE_SUDO} cp "${CERT_DIR}/admin.kubeconfig" "${CERT_DIR}/admin-kube-aggregator.kubeconfig"
    ${CONTROLPLANE_SUDO} chown $(whoami) "${CERT_DIR}/admin-kube-aggregator.kubeconfig"
    ${KUBECTL} config set-cluster local-up-cluster --kubeconfig="${CERT_DIR}/admin-kube-aggregator.kubeconfig" --server="https://${API_HOST_IP}:31090"
    echo "use 'kubectl --kubeconfig=${CERT_DIR}/admin-kube-aggregator.kubeconfig' to use the aggregated API server"
```

使用 [kubectl create clusterrolebinding](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#kubectl-create-clusterrolebinding) 指令建立 `kube-apiserver` 使用者並給予適當的權限。


## start_controller_manager

```bash
function start_controller_manager {
    node_cidr_args=""
    if [[ "${NET_PLUGIN}" == "kubenet" ]]; then
      node_cidr_args="--allocate-node-cidrs=true --cluster-cidr=10.1.0.0/16 "
    fi

    cloud_config_arg="--cloud-provider=${CLOUD_PROVIDER} --cloud-config=${CLOUD_CONFIG}"
    if [[ "${EXTERNAL_CLOUD_PROVIDER:-}" == "true" ]]; then
      cloud_config_arg="--cloud-provider=external"
      cloud_config_arg+=" --external-cloud-volume-plugin=${CLOUD_PROVIDER}"
      cloud_config_arg+=" --cloud-config=${CLOUD_CONFIG}"
    fi

    CTLRMGR_LOG=${LOG_DIR}/kube-controller-manager.log
    ${CONTROLPLANE_SUDO} "${GO_OUT}/hyperkube" controller-manager \
      --v=${LOG_LEVEL} \
      --vmodule="${LOG_SPEC}" \
      --service-account-private-key-file="${SERVICE_ACCOUNT_KEY}" \
      --root-ca-file="${ROOT_CA_FILE}" \
      --cluster-signing-cert-file="${CLUSTER_SIGNING_CERT_FILE}" \
      --cluster-signing-key-file="${CLUSTER_SIGNING_KEY_FILE}" \
      --enable-hostpath-provisioner="${ENABLE_HOSTPATH_PROVISIONER}" \
      ${node_cidr_args} \
      --pvclaimbinder-sync-period="${CLAIM_BINDER_SYNC_PERIOD}" \
      --feature-gates="${FEATURE_GATES}" \
      ${cloud_config_arg} \
      --kubeconfig "${CERT_DIR}"/controller.kubeconfig \
      --use-service-account-credentials \
      --controllers="${KUBE_CONTROLLERS}" \
      --leader-elect=false \
      --cert-dir="${CERT_DIR}" \
      --master="https://${API_HOST}:${API_SECURE_PORT}" >"${CTLRMGR_LOG}" 2>&1 &
    CTLRMGR_PID=$!
}
```

start_controller_manager 單純由指令來看很單純，就是單數多了些，待理解的部分：

* NET_PLUGIN 為什麼是在這裡設定呢？它如在哪影響程式呢？
* 若要運用 clould provider 的設定，則可以透過 CLOUD_PROVIDER 與 EXTERNAL_CLOUD_PROVIDER 來設定
* 它指定了 `--master="https://${API_HOST}:${API_SECURE_PORT}"`，可以推測其他元件也都是這樣直接跟 apiserver 溝通

## start_cloud_controller_manager (EXTERNAL_CLOUD_PROVIDER)

後續得追一下不同的 cloud provider 要怎麼實作：

```bash
function start_cloud_controller_manager {
    if [ -z "${CLOUD_CONFIG}" ]; then
      echo "CLOUD_CONFIG cannot be empty!"
      exit 1
    fi
    if [ ! -f "${CLOUD_CONFIG}" ]; then
      echo "Cloud config ${CLOUD_CONFIG} doesn't exist"
      exit 1
    fi

    node_cidr_args=""
    if [[ "${NET_PLUGIN}" == "kubenet" ]]; then
      node_cidr_args="--allocate-node-cidrs=true --cluster-cidr=10.1.0.0/16 "
    fi

    CLOUD_CTLRMGR_LOG=${LOG_DIR}/cloud-controller-manager.log
    ${CONTROLPLANE_SUDO} ${EXTERNAL_CLOUD_PROVIDER_BINARY:-"${GO_OUT}/hyperkube" cloud-controller-manager} \
      --v=${LOG_LEVEL} \
      --vmodule="${LOG_SPEC}" \
      ${node_cidr_args} \
      --feature-gates="${FEATURE_GATES}" \
      --cloud-provider=${CLOUD_PROVIDER} \
      --cloud-config=${CLOUD_CONFIG} \
      --kubeconfig "${CERT_DIR}"/controller.kubeconfig \
      --use-service-account-credentials \
      --leader-elect=false \
      --master="https://${API_HOST}:${API_SECURE_PORT}" >"${CLOUD_CTLRMGR_LOG}" 2>&1 &
    CLOUD_CTLRMGR_PID=$!
}
```

## start_kubeproxy

proxy 的參數真少啊，到時得再挖 source code 看看了：

```bash
function start_kubeproxy {
    PROXY_LOG=${LOG_DIR}/kube-proxy.log

    cat <<EOF > /tmp/kube-proxy.yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
clientConnection:
  kubeconfig: ${CERT_DIR}/kube-proxy.kubeconfig
hostnameOverride: ${HOSTNAME_OVERRIDE}
mode: ${KUBE_PROXY_MODE}
EOF
    if [[ -n ${FEATURE_GATES} ]]; then
      echo "featureGates:"
      # Convert from foo=true,bar=false to
      #   foo: true
      #   bar: false
      for gate in $(echo ${FEATURE_GATES} | tr ',' ' '); do
        echo ${gate} | ${SED} -e 's/\(.*\)=\(.*\)/  \1: \2/'
      done
    fi >>/tmp/kube-proxy.yaml

    sudo "${GO_OUT}/hyperkube" proxy \
      --v=${LOG_LEVEL} \
      --config=/tmp/kube-proxy.yaml \
      --master="https://${API_HOST}:${API_SECURE_PORT}" >"${PROXY_LOG}" 2>&1 &
    PROXY_PID=$!
}
```

## start_kubescheduler

scheduler 的參數真少啊，到時得再挖 source code 看看了：

```bash
function start_kubescheduler {

    SCHEDULER_LOG=${LOG_DIR}/kube-scheduler.log
    ${CONTROLPLANE_SUDO} "${GO_OUT}/hyperkube" scheduler \
      --v=${LOG_LEVEL} \
      --leader-elect=false \
      --kubeconfig "${CERT_DIR}"/scheduler.kubeconfig \
      --feature-gates="${FEATURE_GATES}" \
      --master="https://${API_HOST}:${API_SECURE_PORT}" >"${SCHEDULER_LOG}" 2>&1 &
    SCHEDULER_PID=$!
}
```

## start_kubedns

Q: kube dns 跟 node local dns 在角色上有什麼不同呢？

```bash
function start_kubedns {
    if [[ "${ENABLE_CLUSTER_DNS}" = true ]]; then
        cp "${KUBE_ROOT}/cluster/addons/dns/kube-dns/kube-dns.yaml.in" kube-dns.yaml
        ${SED} -i -e "s/{{ pillar\['dns_domain'\] }}/${DNS_DOMAIN}/g" kube-dns.yaml
        ${SED} -i -e "s/{{ pillar\['dns_server'\] }}/${DNS_SERVER_IP}/g" kube-dns.yaml
        # TODO update to dns role once we have one.
        # use kubectl to create kubedns addon
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" --namespace=kube-system create -f kube-dns.yaml
        echo "Kube-dns addon successfully deployed."
        rm kube-dns.yaml
    fi
}
```

## start_nodelocaldns (ENABLE_NODELOCAL_DNS)

在啟用 node local dns 的情況，由於 [cluster/addons/dns/nodelocaldns/nodelocaldns.yaml](https://github.com/kubernetes/kubernetes/blob/release-1.14/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml) 檔案挺大的，就不再是直接利用 cat 來產生檔案，是用 sed 直接字串取代。生好設定檔後，直接 apply yaml：

```bash
function start_nodelocaldns {
  cp "${KUBE_ROOT}/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml" nodelocaldns.yaml
  sed -i -e "s/__PILLAR__DNS__DOMAIN__/${DNS_DOMAIN}/g" nodelocaldns.yaml
  sed -i -e "s/__PILLAR__DNS__SERVER__/${DNS_SERVER_IP}/g" nodelocaldns.yaml
  sed -i -e "s/__PILLAR__LOCAL__DNS__/${LOCAL_DNS_IP}/g" nodelocaldns.yaml
  # use kubectl to create nodelocaldns addon
  ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" --namespace=kube-system create -f nodelocaldns.yaml
  echo "NodeLocalDNS addon successfully deployed."
  rm nodelocaldns.yaml
}
```

## start_kubedashboard

dashboard 的部分是利用 cluster/addons/dashboard 下提供的 yaml 建立的。

```bash
function start_kubedashboard {
    if [[ "${ENABLE_CLUSTER_DASHBOARD}" = true ]]; then
        echo "Creating kubernetes-dashboard"
        # use kubectl to create the dashboard
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" apply -f ${KUBE_ROOT}/cluster/addons/dashboard/dashboard-secret.yaml
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" apply -f ${KUBE_ROOT}/cluster/addons/dashboard/dashboard-configmap.yaml
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" apply -f ${KUBE_ROOT}/cluster/addons/dashboard/dashboard-rbac.yaml
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" apply -f ${KUBE_ROOT}/cluster/addons/dashboard/dashboard-controller.yaml
        ${KUBECTL} --kubeconfig="${CERT_DIR}/admin.kubeconfig" apply -f ${KUBE_ROOT}/cluster/addons/dashboard/dashboard-service.yaml
        echo "kubernetes-dashboard deployment and service successfully deployed."
    fi
}
```

## 後續

* 大部分的 service 啟動都是單純的 hyperkube 呼叫，這部分得另外追 source code 研究 
* 除了 apiserver 之外，其它的服務都會設 `--master` 指向 apiserver
* 應該有機會研究其中一個比較簡單的 service 來理解，他們對 apiserver 主要的需求是什麼，未來若是要多一個新的 service 時，比較好下手。