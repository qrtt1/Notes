
## 尋找 plugin library 內的 plugin

以 android plugin 為例，先把它當一般的 library 用：

```groovy
apply plugin: 'java'
apply plugin: 'maven'
repositories {
    jcenter()
}
dependencies {
    compile 'com.android.tools.build:gradle:2.3.0'
}

task unzipPlugin(type: Copy) {
  configurations.compile.each {
    if("${it}".contains("/gradle-2.3.0.jar")) {
      from zipTree(it)
      into "android-plugin"
    }
  }
}
```

然後，把它的檔案抓來 unzip 一下，接著看它的 META-INF 目錄
```
qty:lab qrtt1$ ls -lh android-plugin/META-INF/gradle-plugins/
total 72
-rw-------  1 qrtt1  staff    59B  3 29 12:26 android-library.properties
-rw-------  1 qrtt1  staff    61B  3 29 12:26 android-reporting.properties
-rw-------  1 qrtt1  staff    55B  3 29 12:26 android.properties
-rw-------  1 qrtt1  staff    55B  3 29 12:26 com.android.application.properties
-rw-------  1 qrtt1  staff    56B  3 29 12:26 com.android.atom.properties
-rwx------  1 qrtt1  staff   693B  3 29 12:26 com.android.external.build.properties
-rw-------  1 qrtt1  staff    62B  3 29 12:26 com.android.instantapp.properties
-rw-------  1 qrtt1  staff    59B  3 29 12:26 com.android.library.properties
-rw-------  1 qrtt1  staff   661B  3 29 12:26 com.android.test.properties
qty:lab qrtt1$
```

這些就是平常在使用的 `apply plugin: ""` 內所填的值，檔案內容就是它的實作類別，例如：

```
qrtt1$ cat android-plugin/META-INF/gradle-plugins/com.android.application.properties ; echo;
implementation-class=com.android.build.gradle.AppPlugin
```
