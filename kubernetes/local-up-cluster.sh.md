# local-up-cluster.sh

對於要開始學習 kubernetes 需要哪些元件才能啟動一個完整的 cluster，閱讀 [Getting started locally](https://github.com/kubernetes/community/blob/master/contributors/devel/running-locally.md) 是一個很好的開始，它提供一個 script [https://github.com/kubernetes/kubernetes/blob/master/hack/local-up-cluster.sh](hack/local-up-cluster.sh)，能協助開發者在 local 端建出單 1 node 的 kubernetes cluster。

安裝好需要的工具：

* docker
* cfssl
* etcd 這版本不能太舊，通常使用系統安裝的會不夠新。kubernetes 會提示你有第三方的預編版本可以下載。

只要再 root 下執行 local-up-cluster.sh 就能有個最簡版本的 kubernetes cluster 可以使用囉。單純會動之後，就可以來改它的 code 或在這上面練習一般 kubernetes 的使用方式。身為工程師還是得它到底做了什麼要保持好奇心探索一下。所以，這篇文章是記錄 local-up-cluster.sh 的探索記錄。

拉下來的筆記是基於 [release-1.14](https://github.com/kubernetes/kubernetes/blob/release-1.14/hack/local-up-cluster.sh) 的版本進行記錄。

## 1 ~ 17

[https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/local-up-cluster.sh#L1-L17](Line 1 ~ 17)

```bash
#!/usr/bin/env bash

# Copyright 2014 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

KUBE_ROOT=$(dirname "${BASH_SOURCE}")/..
```

身為一個每次寫 shell 都要 google 半天的人來說，看到了許多沒學過的寫法。好在第一段並沒有太大的意外，因為 script 位置是放在 repo root 下的 `hack` 子目錄，用 `BASH_SOURCE` 變數配合 dirname 找到專案的 root 是挺合理的。

## 19 ~ 145

[Line 19 ~ 145](https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/local-up-cluster.sh#L19-L145) 主要在宣告變數與確認系統環境。

```bash
# This command builds and runs a local kubernetes cluster.
# You may need to run this as root to allow kubelet to open docker's socket,
# and to write the test CA in /var/run/kubernetes.
DOCKER_OPTS=${DOCKER_OPTS:-""}
DOCKER=(docker ${DOCKER_OPTS})
DOCKER_ROOT=${DOCKER_ROOT:-""}
ALLOW_PRIVILEGED=${ALLOW_PRIVILEGED:-""}
DENY_SECURITY_CONTEXT_ADMISSION=${DENY_SECURITY_CONTEXT_ADMISSION:-""}
PSP_ADMISSION=${PSP_ADMISSION:-""}
NODE_ADMISSION=${NODE_ADMISSION:-""}
RUNTIME_CONFIG=${RUNTIME_CONFIG:-""}
KUBELET_AUTHORIZATION_WEBHOOK=${KUBELET_AUTHORIZATION_WEBHOOK:-""}
KUBELET_AUTHENTICATION_WEBHOOK=${KUBELET_AUTHENTICATION_WEBHOOK:-""}
POD_MANIFEST_PATH=${POD_MANIFEST_PATH:-"/var/run/kubernetes/static-pods"}
KUBELET_FLAGS=${KUBELET_FLAGS:-""}
KUBELET_IMAGE=${KUBELET_IMAGE:-""}
# ...(略)...
```

其中，有個 `:-` 放在變數中，這倒底是什麼呢？試著使用 google 查一下：

> bash colon minus

獲得了 [stackoverflow 鄉民的解說](https://stackoverflow.com/a/27445490/90909)：

> It's a parameter expansion, it means if the third argument is null or unset, replace it with what's after :-

原來是一個預設值的概念啊！如果環境中沒有預先提供這個變數，那就用 `:-` 的值取代它。

## 147 ~ 203

[Line 147 ~ 203](https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/local-up-cluster.sh#L147-L203) 則是開始尋找 *kyperkube*。預設會每次啟動都重新 build。

```bash
# Stop right away if the build fails
set -e

source "${KUBE_ROOT}/hack/lib/init.sh"
kube::util::ensure-gnu-sed
```

### hack/lib/init.sh

[hack/lib/init.sh](https://github.com/kubernetes/kubernetes/blob/release-1.14/hack/lib/init.sh) 其實就是一個引用 library 的概念。將預先寫好的許多共用的功能引入，方便接下來的使用。

```bash
# Unset CDPATH so that path interpolation can work correctly
# https://github.com/kubernetes/kubernetes/issues/52255
unset CDPATH
```

在最開頭的 `unset CDPATH` 這也是對於我這種不太會寫 shell script 感到新奇的地方。[Something all bash scripters need to know (and most of us don’t)](https://bosker.wordpress.com/2012/02/12/bash-scripters-beware-of-the-cdpath/) 文章有解說當 CDPATH 變數有值時會帶來的副作用，所以它會是一個搭配 `cd` 使用時的『慣用語』了。

ps. 用 `unset CDPATH` 去 Google 搜尋可以發現有許多專案都有遇到這個問題。

### function name

在引用的 library 中，function 名稱都會是 `kube::` 開頭的，例如：

```bash
kube::log::install_errexit
```

順便學到 bash 可以用 `::` 當作函式名稱的一部分，這應該是來自 [Google 的 Shell Style Guide](https://google.github.io/styleguide/shell.xml?showone=Function_Names#Function_Names) 的習慣。


## 153 ~ 203

[Line 153 ~ 203](https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/local-up-cluster.sh#L153-L203)

```bash
function usage {
            echo "This script starts a local kube cluster. "
            echo "Example 0: hack/local-up-cluster.sh -h  (this 'help' usage description)"
            echo "Example 1: hack/local-up-cluster.sh -o _output/dockerized/bin/linux/amd64/ (run from docker output)"
            echo "Example 2: hack/local-up-cluster.sh -O (auto-guess the bin path for your platform)"
            echo "Example 3: hack/local-up-cluster.sh (build a local copy of the source)"
}
```

usage 函式會在下錯參數時才出現 (由下面的 switch case 決定)，它有幾個常見的用法：

```
./hack/local-up-cluster.sh -O
```

官網是推薦使用 `-O` 自動偵測有沒有編譯好的執行檔，就不用每次都重新編譯囉。

```bash
# This function guesses where the existing cached binary build is for the `-O`
# flag
function guess_built_binary_path {
  local hyperkube_path=$(kube::util::find-binary "hyperkube")
  if [[ -z "${hyperkube_path}" ]]; then
    return
  fi
  echo -n "$(dirname "${hyperkube_path}")"
}
```

guess_built_binary_path 函式其實就是 `-O` 參數的實作，它來自 `hack/lib/init.sh` 引入的其他檔案，看內容推測是在尋找 hyperkube。據[鄉民](https://stackoverflow.com/q/33953254/90909)與[原始碼](https://github.com/kubernetes/kubernetes/blob/release-1.14/cmd/hyperkube/main.go)來看，hyperkube 則是 kubernetes 的主要執行檔，透過不同的參數決定它要開啟哪個元件。


```bash
### Allow user to supply the source directory.
GO_OUT=${GO_OUT:-}
while getopts "ho:O" OPTION
do
    case ${OPTION} in
        o)
            echo "skipping build"
            GO_OUT="${OPTARG}"
            echo "using source ${GO_OUT}"
            ;;
        O)
            GO_OUT=$(guess_built_binary_path)
            if [ "${GO_OUT}" == "" ]; then
                echo "Could not guess the correct output directory to use."
                exit 1
            fi
            ;;
        h)
            usage
            exit
            ;;
        ?)
            usage
            exit
            ;;
    esac
done
```

```bash
if [ "x${GO_OUT}" == "x" ]; then
    make -C "${KUBE_ROOT}" WHAT="cmd/kubectl cmd/hyperkube"
else
    echo "skipped the build."
fi

# Shut down anyway if there's an error.
set +e
```

執行 local-up-cluster.sh 未給定任何參數時，上面的 while 不會進入，會執行 `make` 編譯出 

* kubectl
* hyperkube

最後，它回復了 error 就終止 script 的設定到有 error 也不理會，繼續執行。

## 208 ~ 257

[Line 208 ~ 257](https://github.com/kubernetes/kubernetes/blob/release-1.14/hack/local-up-cluster.sh#L208-L257) 又是一連串的變數宣告，但我們可以順便由這些變數知道他有哪些預設值，與要依賴哪些元件：

```bash
API_PORT=${API_PORT:-8080}
API_SECURE_PORT=${API_SECURE_PORT:-6443}
```

API 的 http 與 https 分別是 8080 與 6443

```bash
# WARNING: For DNS to work on most setups you should export API_HOST as the docker0 ip address,
API_HOST=${API_HOST:-localhost}
API_HOST_IP=${API_HOST_IP:-"127.0.0.1"}
ADVERTISE_ADDRESS=${ADVERTISE_ADDRESS:-""}
NODE_PORT_RANGE=${NODE_PORT_RANGE:-""}
API_BIND_ADDR=${API_BIND_ADDR:-"0.0.0.0"}
EXTERNAL_HOSTNAME=${EXTERNAL_HOSTNAME:-localhost}

KUBELET_HOST=${KUBELET_HOST:-"127.0.0.1"}
# By default only allow CORS for requests on localhost
API_CORS_ALLOWED_ORIGINS=${API_CORS_ALLOWED_ORIGINS:-/127.0.0.1(:[0-9]+)?$,/localhost(:[0-9]+)?$}
KUBELET_PORT=${KUBELET_PORT:-10250}
LOG_LEVEL=${LOG_LEVEL:-3}
# Use to increase verbosity on particular files, e.g. LOG_SPEC=token_controller*=5,other_controller*=4
LOG_SPEC=${LOG_SPEC:-""}
LOG_DIR=${LOG_DIR:-"/tmp"}
```

container 的 runtime 預設是 docker，似乎也能是 rkt。

```bash
CONTAINER_RUNTIME=${CONTAINER_RUNTIME:-"docker"}
CONTAINER_RUNTIME_ENDPOINT=${CONTAINER_RUNTIME_ENDPOINT:-""}
IMAGE_SERVICE_ENDPOINT=${IMAGE_SERVICE_ENDPOINT:-""}
CHAOS_CHANCE=${CHAOS_CHANCE:-0.0}
CPU_CFS_QUOTA=${CPU_CFS_QUOTA:-true}
ENABLE_HOSTPATH_PROVISIONER=${ENABLE_HOSTPATH_PROVISIONER:-"false"}
CLAIM_BINDER_SYNC_PERIOD=${CLAIM_BINDER_SYNC_PERIOD:-"15s"} # current k8s default
ENABLE_CONTROLLER_ATTACH_DETACH=${ENABLE_CONTROLLER_ATTACH_DETACH:-"true"} # current default
```

接著，它設定了 `CERT_DIR` 要用來產生自簽憑證的目錄

```bash
# This is the default dir and filename where the apiserver will generate a self-signed cert
# which should be able to be used as the CA to verify itself
CERT_DIR=${CERT_DIR:-"/var/run/kubernetes"}
ROOT_CA_FILE=${CERT_DIR}/server-ca.crt
ROOT_CA_KEY=${CERT_DIR}/server-ca.key
CLUSTER_SIGNING_CERT_FILE=${CLUSTER_SIGNING_CERT_FILE:-"${ROOT_CA_FILE}"}
CLUSTER_SIGNING_KEY_FILE=${CLUSTER_SIGNING_KEY_FILE:-"${ROOT_CA_KEY}"}
# Reuse certs will skip generate new ca/cert files under CERT_DIR
# it's useful with PRESERVE_ETCD=true because new ca will make existed service account secrets invalided
REUSE_CERTS=${REUSE_CERTS:-false}
```

當使用 docker 作為 container runtime 時，它要微調一下 cgroup driver 的參數

```bash
# name of the cgroup driver, i.e. cgroupfs or systemd
if [[ ${CONTAINER_RUNTIME} == "docker" ]]; then
  # default cgroup driver to match what is reported by docker to simplify local development
  if [[ -z ${CGROUP_DRIVER} ]]; then
    # match driver with docker runtime reported value (they must match)
    CGROUP_DRIVER=$(docker info | grep "Cgroup Driver:" | cut -f3- -d' ')
    echo "Kubelet cgroup driver defaulted to use: ${CGROUP_DRIVER}"
  fi
  if [[ -f /var/log/docker.log && ! -f ${LOG_DIR}/docker.log ]]; then
    ln -s /var/log/docker.log ${LOG_DIR}/docker.log
  fi
fi
```

## 265 ~ 962

[Line 265 ~ 962](https://github.com/kubernetes/kubernetes/blob/6e8b574d270c1681716b0b8153477c2fa847d9b5/hack/local-up-cluster.sh#L265-L962) 在定義函式。定義完成了，就開始是主要程式的部分囉：

```bash
function test_apiserver_off { }
function detect_binary { }
function healthcheck { }
function print_color { }
function warning_log { }
function start_etcd { }
function set_service_accounts { }
function generate_certs { }
function generate_kubelet_certs { }
function start_apiserver { }
function start_controller_manager { }
function start_cloud_controller_manager { }
function start_kubelet { }
function start_kubeproxy { }
function start_kubescheduler { }
function start_kubedns { }
function start_nodelocaldns { }
function start_kubedashboard { }
function create_psp_policy { }
function create_storage_class { }
function print_success { }
```

## 964 ~ 1070

[Line 964 ~ 1070](https://github.com/kubernetes/kubernetes/blob/release-1.14/hack/local-up-cluster.sh#L964-L1070) 主要的執行邏輯開始

```bash
# If we are running in the CI, we need a few more things before we can start
if [[ "${KUBETEST_IN_DOCKER:-}" == "true" ]]; then
  echo "Preparing to test ..."
  ${KUBE_ROOT}/hack/install-etcd.sh
  export PATH="${KUBE_ROOT}/third_party/etcd:${PATH}"
  KUBE_FASTBUILD=true make ginkgo cross

  apt-get update && apt-get install -y sudo
  apt-get remove -y systemd

  # configure shared mounts to prevent failure in DIND scenarios
  mount --make-rshared /

  # kubekins has a special directory for docker root
  DOCKER_ROOT="/docker-graph"
fi
```

在最開頭，先判斷有沒有在 docker 內，這情境是假設跑在 `CI` 的環境。若是在 docker 內的話，那就多安裝一些程式，並完成一些系統設定。`KUBETEST_IN_DOCKER` 在整個 repo 內，只有這個地方有出現。也許是在 CI 時，有設定環境變數才會進這個 condition 了。

### START MODE

```bash
# validate that etcd is: not running, in path, and has minimum required version.
if [[ "${START_MODE}" != "kubeletonly" ]]; then
  kube::etcd::validate
fi
```

確認 **START_MODE** 不是 kubeletonly 時，就要檢查 etcd 的狀態，透過 git grep 可以看到相關的訊息：

```
qty:kubernetes qrtt1$ git grep START_MODE
hack/local-up-cluster.sh:# START_MODE can be 'all', 'kubeletonly', or 'nokubelet'
hack/local-up-cluster.sh:START_MODE=${START_MODE:-"all"}
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "kubeletonly" ]]; then
hack/local-up-cluster.sh:if [[ "${START_MODE}" == "all" ]]; then
hack/local-up-cluster.sh:elif [[ "${START_MODE}" == "nokubelet" ]]; then
hack/local-up-cluster.sh:  echo "No kubelet was started because you set START_MODE=nokubelet"
hack/local-up-cluster.sh:  echo "Run this script again with START_MODE=kubeletonly to run a kubelet"
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "kubeletonly" ]]; then
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "kubeletonly" ]]; then
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "kubeletonly" ]]; then
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "kubeletonly" ]]; then
hack/local-up-cluster.sh:if [[ "${START_MODE}" != "nokubelet" ]]; then
```

以目前的程式來說 **START_MODE** 可以是下列 3 種其一：

* all
* kubeletonly
* nokubelet

我們可以由 [Basic Concept](https://kubernetes.io/docs/concepts/#overview) 知道，需要的元件有

* kube-apiserver (master)
* kube-controller-manager (master)
* kube-scheduler (master)
* kubelet
* kube-proxy

所以 `kubeletonly` 或 `nokubelet` 應該是由上述的元件中去變更啟動狀態的。

### CHECK DOCKER

```bash
if [ "${CONTAINER_RUNTIME}" == "docker" ] && ! kube::util::ensure_docker_daemon_connectivity; then
  exit 1
fi
```

當 CONTAINER_RUNTIME 為 docker 時，得檢查 docker 有沒有辦法連上。`kube::util::ensure_docker_daemon_connectivity` 在檔案 *hack/lib/util.sh* 中能找到，

其實要做的事，就只是執行 `docker info` 指令，看一下有沒有正常輸出結果：

```bash
function kube::util::ensure_docker_daemon_connectivity {
  DOCKER=(docker ${DOCKER_OPTS})
  if ! "${DOCKER[@]}" info > /dev/null 2>&1 ; then
    cat <<'EOF' >&2
Can't connect to 'docker' daemon.  please fix and retry.

Possible causes:
  - Docker Daemon not started
    - Linux: confirm via your init system
    - macOS w/ docker-machine: run `docker-machine ls` and `docker-machine start <name>`
    - macOS w/ Docker for Mac: Check the menu bar and start the Docker application
  - DOCKER_HOST hasn't been set or is set incorrectly
    - Linux: domain socket is used, DOCKER_* should be unset. In Bash run `unset ${!DOCKER_*}`
    - macOS w/ docker-machine: run `eval "$(docker-machine env <name>)"`
    - macOS w/ Docker for Mac: domain socket is used, DOCKER_* should be unset. In Bash run `unset ${!DOCKER_*}`
  - Other things to check:
    - Linux: User isn't in 'docker' group.  Add and relogin.
      - Something like 'sudo usermod -a -G docker ${USER}'
      - RHEL7 bug and workaround: https://bugzilla.redhat.com/show_bug.cgi?id=1119282#c8
EOF
    return 1
  fi
}
```

### ! kubeletonly

```bash
if [[ "${START_MODE}" != "kubeletonly" ]]; then
  test_apiserver_off
fi
```

看 test_apiserver_off 實作是檢查有沒有其他程式佔據了需要的 port

```bash
function test_apiserver_off {
    # For the common local scenario, fail fast if server is already running.
    # this can happen if you run local-up-cluster.sh twice and kill etcd in between.
    if [[ "${API_PORT}" -gt "0" ]]; then
        curl --silent -g $API_HOST:$API_PORT
        if [ ! $? -eq 0 ]; then
            echo "API SERVER insecure port is free, proceeding..."
        else
            echo "ERROR starting API SERVER, exiting. Some process on $API_HOST is serving already on $API_PORT"
            exit 1
        fi
    fi

    curl --silent -k -g $API_HOST:$API_SECURE_PORT
    if [ ! $? -eq 0 ]; then
        echo "API SERVER secure port is free, proceeding..."
    else
        echo "ERROR starting API SERVER, exiting. Some process on $API_HOST is serving already on $API_SECURE_PORT"
        exit 1
    fi
}
```

### openssl & cfssl

```bash
kube::util::test_openssl_installed
kube::util::ensure-cfssl
```
`kube::util::test_openssl_installed` 簡單執行 `openssl version` 確認一下有正常結束。

```bash
function kube::util::test_openssl_installed {
    openssl version >& /dev/null
    if [ "$?" != "0" ]; then
      echo "Failed to run openssl. Please ensure openssl is installed"
      exit 1
    fi

    OPENSSL_BIN=$(command -v openssl)
}
```

比起 openssl 檢查 `kube::util::ensure-cfssl` 的實作就複雜了許多。因為當發現 cfssl 相關工具不存在的情況，它就會下載回來：

```bash
# Downloads cfssl/cfssljson into $1 directory if they do not already exist in PATH
#
# Assumed vars:
#   $1 (cfssl directory) (optional)
#
# Sets:
#  CFSSL_BIN: The path of the installed cfssl binary
#  CFSSLJSON_BIN: The path of the installed cfssljson binary
#
function kube::util::ensure-cfssl {
  if command -v cfssl &>/dev/null && command -v cfssljson &>/dev/null; then
    CFSSL_BIN=$(command -v cfssl)
    CFSSLJSON_BIN=$(command -v cfssljson)
    return 0
  fi

  host_arch=$(kube::util::host_arch)

  if [[ "${host_arch}" != "amd64" ]]; then
    echo "Cannot download cfssl on non-amd64 hosts and cfssl does not appear to be installed."
    echo "Please install cfssl and cfssljson and verify they are in \$PATH."
    echo "Hint: export PATH=\$PATH:\$GOPATH/bin; go get -u github.com/cloudflare/cfssl/cmd/..."
    exit 1
  fi

  # Create a temp dir for cfssl if no directory was given
  local cfssldir=${1:-}
  if [[ -z "${cfssldir}" ]]; then
    kube::util::ensure-temp-dir
    cfssldir="${KUBE_TEMP}/cfssl"
  fi

  mkdir -p "${cfssldir}"
  pushd "${cfssldir}" > /dev/null

    echo "Unable to successfully run 'cfssl' from ${PATH}; downloading instead..."
    kernel=$(uname -s)
    case "${kernel}" in
      Linux)
        curl --retry 10 -L -o cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
        curl --retry 10 -L -o cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
        ;;
      Darwin)
        curl --retry 10 -L -o cfssl https://pkg.cfssl.org/R1.2/cfssl_darwin-amd64
        curl --retry 10 -L -o cfssljson https://pkg.cfssl.org/R1.2/cfssljson_darwin-amd64
        ;;
      *)
        echo "Unknown, unsupported platform: ${kernel}." >&2
        echo "Supported platforms: Linux, Darwin." >&2
        exit 2
    esac

    chmod +x cfssl || true
    chmod +x cfssljson || true

    CFSSL_BIN="${cfssldir}/cfssl"
    CFSSLJSON_BIN="${cfssldir}/cfssljson"
    if [[ ! -x ${CFSSL_BIN} || ! -x ${CFSSLJSON_BIN} ]]; then
      echo "Failed to download 'cfssl'. Please install cfssl and cfssljson and verify they are in \$PATH."
      echo "Hint: export PATH=\$PATH:\$GOPATH/bin; go get -u github.com/cloudflare/cfssl/cmd/..."
      exit 1
    fi
  popd > /dev/null
}
```

在這個函式的實作學到了一些新知，我們能利用 command 指令查出目前執行的程式的絕對路徑：

```
qty:~ qrtt1$ command -v python
/Users/qrtt1/anaconda3/bin/python
```

另外，在實作函式需要換目錄時，可以利用 `pushd` `popd` 來將目錄的路徑塞入 stack：

```
qty:kubernetes qrtt1$ pushd vendor/github.com/pelletier/go-toml
~/temp/kubernetes/vendor/github.com/pelletier/go-toml ~/temp/kubernetes
qty:go-toml qrtt1$ popd
~/temp/kubernetes
```

這樣移動起來很有效率，也不用一個變數來存上一個位置，只是還不清楚它跟 `cd -` 的差異或優點是什麼。


PS. 看完這一段後，驚覺似乎不用自己麻煩地自編 cfssl 相關工具啊！！！ 

### Starting Services

來到檔案的最後，我們終於要進入正題了！

```bash
### IF the user didn't supply an output/ for the build... Then we detect.
if [ "${GO_OUT}" == "" ]; then
  detect_binary
fi
```

一直覺得 GO_OUT (出去！！！) 這變數太有梗了。它主要是指 kubernetes 編譯後輸出的位置。`detect_binary` 的實作其實就是抓出 os 代號與 CPU 架構後組出路徑而已，看起來目前並無支援 Windows，而 CPU 架構支援得挺多的：

```bash
function detect_binary {
    # Detect the OS name/arch so that we can find our binary
    case "$(uname -s)" in
      Darwin)
        host_os=darwin
        ;;
      Linux)
        host_os=linux
        ;;
      *)
        echo "Unsupported host OS.  Must be Linux or Mac OS X." >&2
        exit 1
        ;;
    esac

    case "$(uname -m)" in
      x86_64*)
        host_arch=amd64
        ;;
      i?86_64*)
        host_arch=amd64
        ;;
      amd64*)
        host_arch=amd64
        ;;
      aarch64*)
        host_arch=arm64
        ;;
      arm64*)
        host_arch=arm64
        ;;
      arm*)
        host_arch=arm
        ;;
      i?86*)
        host_arch=x86
        ;;
      s390x*)
        host_arch=s390x
        ;;
      ppc64le*)
        host_arch=ppc64le
        ;;
      *)
        echo "Unsupported host arch. Must be x86_64, 386, arm, arm64, s390x or ppc64le." >&2
        exit 1
        ;;
    esac

   GO_OUT="${KUBE_ROOT}/_output/local/bin/${host_os}/${host_arch}"
}
```




```bash
echo "Detected host and ready to start services.  Doing some housekeeping first..."
echo "Using GO_OUT ${GO_OUT}"
KUBELET_CIDFILE=/tmp/kubelet.cid
if [[ "${ENABLE_DAEMON}" = false ]]; then
  trap cleanup EXIT
fi
```

完成前面的各種檢查與變數宣告後，我們終於來到了啟動服務的時刻了：

```bash
echo "Starting services now!"
if [[ "${START_MODE}" != "kubeletonly" ]]; then
  start_etcd
  set_service_accounts
  start_apiserver
  start_controller_manager
  if [[ "${EXTERNAL_CLOUD_PROVIDER:-}" == "true" ]]; then
    start_cloud_controller_manager
  fi
  start_kubeproxy
  start_kubescheduler
  start_kubedns
  if [[ "${ENABLE_NODELOCAL_DNS:-}" == "true" ]]; then
    start_nodelocaldns
  fi
  start_kubedashboard
fi
```

看起來 cluster 啟動的元件依序是：

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

這些項目比先前 Basic Concept 內提到的多，得再研究多出來的部分是做了什麼。

```bash
if [[ "${START_MODE}" != "nokubelet" ]]; then
  ## TODO remove this check if/when kubelet is supported on darwin
  # Detect the OS name/arch and display appropriate error.
    case "$(uname -s)" in
      Darwin)
        print_color "kubelet is not currently supported in darwin, kubelet aborted."
        KUBELET_LOG=""
        ;;
      Linux)
        start_kubelet
        ;;
      *)
        print_color "Unsupported host OS.  Must be Linux or Mac OS X, kubelet aborted."
        ;;
    esac
fi

if [[ -n "${PSP_ADMISSION}" && "${AUTHORIZATION_MODE}" = *RBAC* ]]; then
  create_psp_policy
fi

if [[ "${DEFAULT_STORAGE_CLASS}" = "true" ]]; then
  create_storage_class
fi

if [[ "${FEATURE_GATES:-}" == "AllAlpha=true" || "${FEATURE_GATES:-}" =~ "CSIDriverRegistry=true" ]]; then
  create_csi_crd "csidriver"
fi

if [[ "${FEATURE_GATES:-}" == "AllAlpha=true" || "${FEATURE_GATES:-}" =~ "CSINodeInfo=true" ]]; then
  create_csi_crd "csinodeinfo"
fi

print_success

if [[ "${ENABLE_DAEMON}" = false ]]; then
  while true; do sleep 1; healthcheck; done
fi

if [[ "${KUBETEST_IN_DOCKER:-}" == "true" ]]; then
  cluster/kubectl.sh config set-cluster local --server=https://localhost:6443 --certificate-authority=/var/run/kubernetes/server-ca.crt
  cluster/kubectl.sh config set-credentials myself --client-key=/var/run/kubernetes/client-admin.key --client-certificate=/var/run/kubernetes/client-admin.crt
  cluster/kubectl.sh config set-context local --cluster=local --user=myself
  cluster/kubectl.sh config use-context local
fi
```

在這個筆記，過完 local-up-cluster.sh 的流程，服務啟動的細節再開另一篇來記錄好了。