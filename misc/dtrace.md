
某專案包裝的 ResourceBundle 當作設定檔讀取的工具用法如下：

```java
BundleManager.getManager("systemAbc");
```

在一些情況 `不知道` 它參數裡的 `systemAbc` 實際上會放在哪邊：

```
ERROR [main] (BundleManager.java:279) - BunndleManager.getManager: Resource Not Found: systemAbc:zh_TW
```

在 Linux 下可以用 strace 來追蹤實際開檔路徑。在 OSX 下能用 dtrace：

```
dtrace -n 'syscall::stat*:entry { printf("%s %s",execname,copyinstr(arg0)); }'
```

以 root 執行上述指令，他就會開始監控與 `stat*` 開頭的 syscall（僅列出相關訊息）：

```
  0    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_TW.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_TW.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_TW.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_TW.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_Hant.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_Hant.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_Hant.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_Hant.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_Hant_TW.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_Hant_TW.class
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build/classes/systemAbc_zh_Hant_TW.properties
  2    826                     stat64:entry java /Users/qrtt1/temp/MY_PROJECT/build_MY_PROJECT/WEB-INF/classes/systemAbc_zh_Hant_TW.properties
```

這樣就能知道它實際期望要讀的路徑了
