## Jenkins Workflow Library 設定筆記

要讓 workflow library 的設定能動要先滿足：

1. 有裝 git plugin
2. 啟用 sshd 並設好 port
3. 使用者設好 ssh public key

### sshd

預設是沒有填 port 填所以不會啟用。

1. 管理 Jenkins
1. 設定系統
1. 在設定頁內找到 SSHD 節

### 設定使用者

要有使用者設定才能操作 git，在介面上的操作路徑為：

1. 使用者
1. 點選 XXX 使用者
1. 點選設定
1. 設定頁填寫 SSH Public Keys


### 設定 SSH Config

當準備好後，為了便使用 git 通常會改寫 `~/.ssh/config`

```
Host jenkins-c8763
HostName 127.0.0.1
Port 9487
User nobody
IdentityFile ~/.ssh/c8763
```


完成設定後，就可以進行 clone 並開始提交程式囉：

```
git clone ssh://jenkins-c8763/workflowLibs.git
```


