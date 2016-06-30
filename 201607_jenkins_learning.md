# Jenkins 簡易筆記

趁著 Jenkins 2.0 開始打廣告，還有畫面看起來很美好而開始學 Jenkins。看了官網大多是 Pipeline 的文件，一整個霧沙沙的感覺。只好寫寫這二天摸索與期望的使用方法。在 Jenkins 1.x 時，週遭已經許多朋友在使用，但我還沒太多注意到，曾有幾次相要『學學看』，翻了幾篇教學被『精美的』螢幕截圖所震懾了！只好默默地關上了教學，繼續著不相往來的人生。（大概是有點排斥太依賴 GUI 操作的工具）。

其實這回重新學習它的契機主要是 Pipeline 與遇見 `jenkins cli`，這篇比較著重於儘可能『純文字』來描述這些入門需要操作的動作（至於 pipeline 有空再另外寫心得好了）。


## 啟動 Jenkins

jenkins 的安裝很簡單，只要由官網下載一個 WAR 檔回來就行了。你可以丟進 tomcat 或其它你喜歡的 web container 直接使用。也可以當成可執行的 JAR 來跑，例如：


```
java -jar jenkins.war
```

除了直接啟動它，我們還可以微調一些參數，例如 http port 與工作目錄：


```
JENKINS_HOME=./jenkins_v1_lab java -jar jenkins.war --httpPort=1234 
```

1. [環境變數 `JENKINS_HOME`](https://wiki.jenkins-ci.org/display/JENKINS/Administering+Jenkins) 可以用來指定 jenkins 的工作目錄。這可以讓你不同的 jenkins 使用不用的工作目錄。
1. [參數 `--httpPort=`](https://wiki.jenkins-ci.org/display/JENKINS/Administering+Jenkins) 可以指定要使用的 http port（預設是 8080）


## 基本設定

在安裝完 jenkins 後，若不單單是為了『練習』之用，首先要做的是啟用相關的安裝設定。請參考 [Standard Security Setup](https://wiki.jenkins-ci.org/display/JENKINS/Standard+Security+Setup)：

1. 建立使用者
1. 啟用 Slave To Master 的 Access Control

其它細節就需要配合相關文件研讀，依實際的需求改寫設定。

## 取得 jenkins-cli.jar

多數 jenkins 的入門教學都有精美的圖片操作流程，我們換個比較符合『可自動化』精神的做法，儘可能使用 jenkins cli 來實作。
以 http port 為 1234 的 jenkins instance 為例，能使用下列網址下載 jenkins.jar：

```
http://127.0.0.1:1234/jnlpJars/jenkins-cli.jar
```

並能以下列指令查看使用說明：

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ help
```

多數的日常工作執行的功能都能由 jenkins cli 達成，這篇筆記大概只有安全設定的部分是需要手動的（還有為了產生 job definition）。

## Plugin 安裝

近期熱門的消息是 Jenkins 2.0 的畫面變好看了，但其實重點不是這個。以下文字引自 [Jenkins 2 Overview](https://jenkins.io/2.0/)：

> Jenkins 2 brings Pipeline as code, a new setup experience and other UI improvements all while maintaining total backwards compatibility with existing Jenkins installations.

重點摘要：

1. Pipeline as code（不用一直依賴 Web UI 來做事，並且 Job 可以方便地透過 SCM 管理）
1. 畫面有變好看（雖然很膚淺，我是看到這個消息才開始玩 jenkins）
1. 完全向後相容（偉哉 Java！佛心 Jenkins 團隊！）

若你使用的是 jenkins v2.x 版，那他一開始就會問你要不要安裝建議的 plugin，其中就含有 pipeline 相關的 plugin。本篇筆記是 v1.x 的例子，我們需要自行安裝。有 jenkins cli 做這事挺容易的：

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ install-plugin workflow-aggregator
```

你可以重複 `install-plugin` 指令安裝相關的 plugin，以我的使用情境為來，還加裝：

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ install-plugin ansible
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ install-plugin git
```

需要的 plugin 都安裝完畢後，需要重新啟動 jenkins：

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ restart
```

重新啟動完成，它會載入剛剛裝好的 plugin：

```
qty:Downloads qrtt1$ java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ list-plugins
[WARN] Failed to authenticate with your SSH keys. Proceeding as anonymous
ace-editor                 JavaScript GUI Lib: ACE Editor bundle plugin                     1.1
ansible                    Ansible plugin                                                   0.5
ant                        Ant Plugin                                                       1.2 (1.3)
antisamy-markup-formatter  OWASP Markup Formatter Plugin                                    1.1 (1.5)
branch-api                 Branch API Plugin                                                1.10
cloudbees-folder           Folders Plugin                                                   5.12
credentials                Credentials Plugin                                               2.1.4
cvs                        CVS Plug-in                                                      2.11 (2.12)
durable-task               Durable Task Plugin                                              1.11
external-monitor-job       External Monitor Job Type Plugin                                 1.4
git-client                 Git client plugin                                                1.19.6
git-server                 Git server plugin                                                1.6
git                        Git plugin                                                       2.5.0
handlebars                 JavaScript GUI Lib: Handlebars bundle plugin                     1.1.1
javadoc                    Javadoc Plugin                                                   1.1 (1.4)
jquery-detached            JavaScript GUI Lib: jQuery bundles (jQuery and jQuery UI) plugin 1.2.1
junit                      JUnit Plugin                                                     1.13
ldap                       LDAP Plugin                                                      1.11 (1.12)
mailer                     Mailer Plugin                                                    1.17
matrix-auth                Matrix Authorization Strategy Plugin                             1.1 (1.4)
matrix-project             Matrix Project Plugin                                            1.7.1
maven-plugin               Maven Integration plugin                                         2.7.1 (2.13)
momentjs                   JavaScript GUI Lib: Moment.js bundle plugin                      1.1.1
pam-auth                   PAM Authentication plugin                                        1.1 (1.3)
pipeline-build-step        Pipeline: Build Step                                             2.1
pipeline-input-step        Pipeline: Input Step                                             2.0
pipeline-rest-api          Pipeline: REST API Plugin                                        1.5
pipeline-stage-step        Pipeline: Stage Step                                             2.1
pipeline-stage-view        Pipeline: Stage View Plugin                                      1.5
scm-api                    SCM API Plugin                                                   1.2
script-security            Script Security Plugin                                           1.20
ssh-credentials            SSH Credentials Plugin                                           1.12
ssh-slaves                 SSH Slaves plugin                                                1.9 (1.11)
structs                    Structs Plugin                                                   1.2
subversion                 Subversion Plug-in                                               1.54 (2.6)
translation                Translation Assistance plugin                                    1.10 (1.15)
windows-slaves             Windows Slaves Plugin                                            1.0 (1.1)
workflow-aggregator        Pipeline                                                         2.2
workflow-api               Pipeline: API                                                    2.1
workflow-basic-steps       Pipeline: Basic Steps                                            2.0
workflow-cps-global-lib    Pipeline: Shared Groovy Libraries                                2.0
workflow-cps               Pipeline: Groovy                                                 2.8
workflow-durable-task-step Pipeline: Nodes and Processes                                    2.3
workflow-job               Pipeline: Job                                                    2.3
workflow-multibranch       Pipeline: Multibranch                                            2.8
workflow-scm-step          Pipeline: SCM Step                                               2.1
workflow-step-api          Pipeline: Step API                                               2.2
workflow-support           Pipeline: Supporting APIs                                        2.1
```

## 建立 Job

Jenkins 管理工作的基本單位是 Job，而新推的 pipeline 其實也是 1 種 Job。若您是很早採用 Jenkins 的使用者熟悉的 Job 型態應該還有 Free-Style Job 或是 Maven Project Job。


```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ help
```

```
  create-job
    建立新作業，由 stdin 讀取設定 XML 檔的內容。
```

在 jenkins cli 說明裡 `create-job` 需要由 stdin 讀一個 XML 檔案的內容。至於 XML 檔該長成什麼樣子，這其實依 Job 的類型有所區別（我也不確定它有沒有文件能參考）。觀察既有的 jenkins 工作目錄 `jobs/` 下是存放已建立 job 的資料，每一個 job 都有一個 config.xml 這就是我們需要的材料。

```
qty:jenkins_lab qrtt1$ find . -name "config.xml"
./config.xml
./jobs/a-freestyle-job/config.xml
./jobs/a-pipeline-job/config.xml
./users/qrtt1/config.xml
```

我們能利用這些透過 Web UI 產生出來的 XML 加以修改來建立新 Job，以 `a-freestyle-job/config.xml` 為例：

```xml
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>ls</command>
    </hudson.tasks.Shell>
    <hudson.tasks.Ant plugin="ant@1.2">
      <targets>build</targets>
    </hudson.tasks.Ant>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
```

它有 2 個建置動作：

1. 在 shell 裡呼叫 `ls`
1. 執行 ant target `build`

我們就利用這個 XML 建立另一個名為 `another-freestyle-job` 的 Job：

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ create-job another-freestyle-job <<EOF
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>ls</command>
    </hudson.tasks.Shell>
    <hudson.tasks.Ant plugin="ant@1.2">
      <targets>build</targets>
    </hudson.tasks.Ant>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
EOF
```

PS. 需注意，所有的值需要適當的 XML Escape 處理。


## 執行 Job

執行 Job 的方法以 Jenkins 的術語來說就是『建置』，所以我們找出最接近的字 `build` 來執行 Job

```
java -jar jenkins-cli.jar -s http://127.0.0.1:1234/ build another-freestyle-job
```

## 使用 Jenkins 初心得

重新整理了 jenkins cli 操作方式後，終於能放心地使用 jenkins 了！這一切都是為 **infrastructure as code**，只要能自動化的部分『絕不出手處理』。未來正式進入 jenkins 大量支援 pipeline 後，就能讓 **infrastructure as code** 的拼圖更加完整。

現行來說在能在 pipeline 內使用的 step 已包含核心的功能（註：step 是 pipeline 內的動作『單位』，可以透過安裝 plugin 獲得更多不同的 step），對 Java 開發者來說它還缺 [gradle 相容的 step](https://issues.jenkins-ci.org/browse/JENKINS-27393)，不過只要能叫呼 shell 其實還算可用（但就有一種 freestyle 的感覺）。

