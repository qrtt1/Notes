# Java 初學的 package 與 import 筆記

當我們初學 Java 時，package 與 import 的概念在語法上不算困難，但是配合 classpath 一起來操作時可就困擾了一些新手。Java 語介提供 package 語法解決命名空間的問題，提供 import 來簡化使用不同命名空間的類別。

## 命名空間

對剛接觸程式語言的人，可能會對這個名詞覺得抽象。先舉個例子，拿我們從小到大的好朋友來說『陳怡君』，相信不少朋友有跟陳怡君同屆或同班的經驗，還很可能在不同的階段跟不同的陳怡君同班。為了要能區別是哪一個陳怡君，我們可以多加一點描述：

* 跟我國小五年級同班 的 陳怡君
* 跟我研究所時同班 的 陳怡君

這樣的例子是以『求學階段』的分野也作為區別，不過這東西是相對的概念，因為別人可能會繼續問，你是哪間小學，哪一年入學的？或什麼學校的研究所，哪一屆畢業的？所以，我們要選擇一個好的『絕對』參考點，並不太容易。單純以我國的例子，也許可以用身份證字號用來描述（雖然，通常我們並不知道同學的身份證字號）。

回到 Java 語言本身，使用 `package` 就是提供一個參考點來描述你的 `類別`，透過這個參考點來區別 `同名` 的類別。

## package

`package` 關鍵字必需寫在 java 原始檔的首行（通常我們不考慮有沒有註解，因為它在編譯後會消失），以 Thinking in java 2/e 的例子來說 (中文版 248 頁)，它提供了 2 個簡單的範例：

```java
package com.bruceeckel.simple;

public class Vector {
    public Vector() {
        System.out.println("com.bruceeckel.util.Vector");
    }
}
```

```java
package com.bruceeckel.simple;

public class List {
    public List() {
        System.out.println("com.bruceeckel.util.List");
    }
}
```

書上是這麼描述的：

![](tij_249.png)

它的陳述方式其實不太清楚，因為還沒有完成編譯為 `.class` 的動作時，以這個例子來說 classpath 並沒有意義。除非這 2 隻 class 有引用到其他類別需要加入 classpath 好讓我們執行 `javac` 時能引用得到。它在前一段其實是在描述一個『慣例』，我們習慣讓 `.java` 原始檔，依 `package` 的結構擺放。

具體來說，我們會這麼做：

1. 以你的專案根目錄為起點
2. 查出 package 名字 `com.bruceeckel.simple`
3. 將 package 名字中的 `.` 換成路徑用的反斜線 com/bruceeckel/simple 當作檔案放至的目錄
4. 最後組合出檔名

```
./com/bruceeckel/simple/Vector.java
./com/bruceeckel/simple/List.java
```

以樹狀的結構來看，會像是這樣：

```
qty:learning_java_package_import qrtt1$ tree .
.
├── com
│   └── bruceeckel
│       └── simple
│           ├── List.java
│           └── Vector.java
├── learning_java_package_import.md
└── tij_249.png
```

經過我們手工的編輯後，檔案也出現在同樣的結構下：

```
qty:learning_java_package_import qrtt1$ javac ./com/bruceeckel/simple/List.java
qty:learning_java_package_import qrtt1$ javac ./com/bruceeckel/simple/Vector.java
qty:learning_java_package_import qrtt1$ tree
.
├── com
│   └── bruceeckel
│       └── simple
│           ├── List.class
│           ├── List.java
│           ├── Vector.class
│           └── Vector.java
├── learning_java_package_import.md
└── tij_249.png

3 directories, 6 files
```

## package 目錄慣例的部分

> .java 配合 package 的位置是慣例，.class 配合 package 的位置是規定

先前用 javac 編譯出 .class 檔，它預設是將 .class 檔放在給他的 .java 的同一個目錄。它並不會特別去放置到符合 package 結構的位置。

### 實驗，改掉 package name

為了驗證上面的陳述，我們保留 Vector.java 在目錄結構中的位置，修改它的 package 名稱為 `com.bruceeckel.simple.another_package_name`

```
qty:learning_java_package_import qrtt1$ cat ./com/bruceeckel/simple/Vector.java
```
```java
package com.bruceeckel.simple.another_package_name;

public class Vector {
    public Vector() {
        System.out.println("com.bruceeckel.util.Vector");
    }
}
```

再次編譯 Vector.java 檔：

```
qty:learning_java_package_import qrtt1$ javac ./com/bruceeckel/simple/Vector.java
```

目錄結構完全沒有變化：

```
qty:learning_java_package_import qrtt1$ tree
.
├── com
│   └── bruceeckel
│       └── simple
│           ├── List.class
│           ├── List.java
│           ├── Vector.class
│           └── Vector.java
├── learning_java_package_import.md
└── tij_249.png

3 directories, 6 files
qty:learning_java_package_import qrtt1$
```

因此，可以知道 Java Compiler (javac) 並不在意 `.java` 的結構是不是與 package name 一致。至少由他輸出的位置來看，他並不在意這件事。然後，我們有辦法知道他有編譯正確嗎？可以使用先前教過的 disassembler，但我們這回先不列出完整的內容，只需要 signature 的部分，使用 `-s` 指令。

先來看符合慣例的 List.class，它被編譯為 `com.bruceeckel.simple.List`：

```
qty:learning_java_package_import qrtt1$ javap -s ./com/bruceeckel/simple/List.class
Compiled from "List.java"
public class com.bruceeckel.simple.List {
  public com.bruceeckel.simple.List();
    descriptor: ()V
}
```

實驗的 Vector.class，它被編譯為 `com.bruceeckel.simple.another_package_name.Vector`：

```
qty:learning_java_package_import qrtt1$ javap -s ./com/bruceeckel/simple/Vector.class
Compiled from "Vector.java"
public class com.bruceeckel.simple.another_package_name.Vector {
  public com.bruceeckel.simple.another_package_name.Vector();
    descriptor: ()V
}
```

由此可知對於 Java Compiler 來說，它只是把 package 與 class 組合成一個全名而已（規格上的正式名稱為 fully qualified name，若不含 package name 則為 simple name）。

### javac 的 -d 參數

javac 還有一個參數 `-d` 可以指定輸出 `.class` 的目錄，接續著上面的實驗，我們可以建一個 output 目錄，並輸出到它上面試試。我們編譯每一個 `.java` 檔，並輸出至 `output` 目錄（要事先建好）：

```
qty:learning_java_package_import qrtt1$ find . -name "*.java" | xargs javac -d output
```

javac 幫我們放了正確的位置：

```
qty:learning_java_package_import qrtt1$ tree output/
output/
└── com
    └── bruceeckel
        └── simple
            ├── List.class
            └── another_package_name
                └── Vector.class
```

這樣的位置才是規定的位置，當我們使用 `-d` 參數時，它就有了不同的結果。不過，結果的影響會在用 java 指令執行時才看得到。

## package 目錄規定的部分

剛剛展示了原始碼擺放位置只是『慣例』這件事，而執行 java 應用程式時，若目錄結構不對，那就會找不到 class 而發生錯誤，所以應該以 package name 的結構去放置 `.class` 檔。

> 當我們要引用別人的 class 時，不管是編譯它的時候(javac)，或執行它的時候(java)，只要它的結構是正確的，並且可以在 classpath 內尋找得到，我們就能正確使用。

所以，初學者『手工地』編譯、執行可能遇到的就是：

* 檔案位置正確，package name 正確，classpath 正確
* 檔案位置 `不` 正確，package name 正確，classpath 正確
* 檔案位置正確，package name `不` 正確，classpath 正確
* 檔案位置正確，package name 正確，classpath `不` 正確
* 檔案位置 `不` 正確，package name `不` 正確，classpath 正確
* 檔案位置正確，package name `不` 正確，classpath `不` 正確
* 檔案位置 `不` 正確，package name 正確，classpath `不` 正確

練習中有出錯是正常的，不過現實中我們不太會手工地編譯它，假設 package name 與檔案位置會一致，所以問題大致簡化為：

* 檔案位置正確，classpath 正確
* 檔案位置 `不` 正確，classpath 正確
* 檔案位置正確，classpath `不` 正確

### 由錯誤中學習

我們先建立一個 Main class 來引用先前實作的 Vector 與 List：

```java
import com.bruceeckel.simple.*;

public class Main {

    public static void main(String[] args) {
        new Vector();
        new List();
    }
}
```

PS. 我們另外建立了一個 `lab` 目錄，在裡面實作 Main.java 避免它順便編譯了原來的 List.java 與 Vector.java，以便製造出錯誤。

#### 直接編譯它：

```
Main.java:2: error: package com.bruceeckel.simple does not exist
import com.bruceeckel.simple.*;
^
Main.java:7: error: cannot find symbol
        new Vector();
            ^
  symbol:   class Vector
  location: class Main
Main.java:8: error: cannot find symbol
        new List();
            ^
  symbol:   class List
  location: class Main
3 errors
```

可以看到，它給了我們二種錯誤訊息：

* Main.java:2: error: package com.bruceeckel.simple does not exist
* error: cannot find symbol

但主因還是因為在 classpath 上找不到 class，我們試著開啟囉囌模式(`-verbose`)：

```
qty:lab qrtt1$ javac -verbose Main.java
[parsing started RegularFileObject[Main.java]]
[parsing completed 21ms]
[search path for source files: .,/Users/qrtt1/app/aspectj1.7/lib/aspectjrt.jar]
[search path for class files: /Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/resources.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/rt.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/sunrsasign.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jsse.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jce.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/charsets.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jfr.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/classes,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/cldrdata.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/dnsns.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/jaccess.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/jfxrt.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/localedata.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/nashorn.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunec.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunjce_provider.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunpkcs11.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/zipfs.jar,/System/Library/Java/Extensions/MRJToolkit.jar,.,/Users/qrtt1/app/aspectj1.7/lib/aspectjrt.jar]
Main.java:2: error: package com.bruceeckel.simple does not exist
import com.bruceeckel.simple.*;
^
[loading ZipFileIndexFileObject[/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/lib/ct.sym(META-INF/sym/rt.jar/java/lang/Object.class)]]
[loading ZipFileIndexFileObject[/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/lib/ct.sym(META-INF/sym/rt.jar/java/lang/String.class)]]
[checking Main]
[loading ZipFileIndexFileObject[/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/lib/ct.sym(META-INF/sym/rt.jar/java/io/Serializable.class)]]
[loading ZipFileIndexFileObject[/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/lib/ct.sym(META-INF/sym/rt.jar/java/lang/AutoCloseable.class)]]
Main.java:7: error: cannot find symbol
        new Vector();
            ^
  symbol:   class Vector
  location: class Main
Main.java:8: error: cannot find symbol
        new List();
            ^
  symbol:   class List
  location: class Main
[total 246ms]
3 errors
```

主要是看 `search path for class files` 這一段：

> [search path for class files: /Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/resources.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/rt.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/sunrsasign.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jsse.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jce.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/charsets.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/jfr.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/classes,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/cldrdata.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/dnsns.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/jaccess.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/jfxrt.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/localedata.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/nashorn.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunec.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunjce_provider.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/sunpkcs11.jar,/Library/Java/JavaVirtualMachines/jdk1.8.0_111.jdk/Contents/Home/jre/lib/ext/zipfs.jar,/System/Library/Java/Extensions/MRJToolkit.jar,.,/Users/qrtt1/app/aspectj1.7/lib/aspectjrt.jar]

它列出了目前 classpath 內有的路徑或檔案，在那些檔案或路徑上，沒有一個包含我們剛剛實作的 class，所以它發生了錯誤。一旦我們修正好 classpath 後，就能正確使用自製的 class 了。

### 修正 classpath

我們將利用先前 `javac -d output` 產出的 class 讓 Main.java 能邊編譯。由於它是自動生出來的結構，我們可以排除 package name 與目錄結構有問題的試誤路徑。省下的工就只是通知 javac 有新的 classpath 路徑需要考慮進去。

加入 classpath 的方式有 2 種，一種是通過 `環境變數` 一種是透過 `-cp` 參數，我們比較常使用 `-cp` 參數的方式加在啟動的 script 裡。原因是你可能有不同的 Java 應用程式，要引用不同版本的函式庫，如果設定在環境變數就大家都被指定成特定版本了。[二種 classpath 設定的方法在官方教學都有](https://docs.oracle.com/javase/tutorial/essential/environment/paths.html)，但對於初學者來說，最的問題是不知道怎麼設定它的值。

#### 實驗目錄的結構

目前在 lab 下有個 Main.java，在同層的 output 目錄有已編譯好的 `.class`

```
qty:lab qrtt1$ tree ../output/
../output/
└── com
    └── bruceeckel
        └── simple
            ├── List.class
            └── Vector.class

3 directories, 2 files
qty:lab qrtt1$
```

#### 加入 classpath

那麼我只需要把 output 加入 classpath 就行了：

```
qty:lab qrtt1$ javac -cp ../output Main.java
```

透過 verbose 取得的 log 可以知道它在什麼位置讀到 `.class` 檔：

```
[loading RegularFileObject[../output/com/bruceeckel/simple/Vector.class]]
[loading RegularFileObject[../output/com/bruceeckel/simple/List.class]]
```

若將設定的 classpath 放上去比對，就知道我們設定的是搜尋的起點：

```
../output <== 我們的設定
../output/com/bruceeckel/simple/Vector.class
../output/com/bruceeckel/simple/List.class
```

所以，你可以想像，若我們設定是 /aaa/bbb/ccc 那麼它會試著去找：

```
/aaa/bbb/ccc/com/bruceeckel/simple/Vector.class
/aaa/bbb/ccc/com/bruceeckel/simple/List.class
```

### 來包個 jar

[官方教學文件有教如何用 jar 指令來打包 jar 檔案](https://docs.oracle.com/javase/tutorial/deployment/jar/build.html)，不過這其實沒那麼好用，jar 檔案其實只是一個 zip 壓縮格式的檔案而已。所以，我們有個 jar 只需要把它 zip 起來就好，先來個 **錯誤** 的示範：

```
qty:learning_java_package_import qrtt1$ zip -r library.jar output
updating: output/ (stored 0%)
  adding: output/com/ (stored 0%)
  adding: output/com/bruceeckel/ (stored 0%)
  adding: output/com/bruceeckel/simple/ (stored 0%)
  adding: output/com/bruceeckel/simple/List.class (deflated 27%)
  adding: output/com/bruceeckel/simple/Vector.class (deflated 28%)
```

上面指令，將 output 目錄直接打包成 zip，當我們使用它的，你會永遠找不到要的 class。因為依 zip 內的路徑去還原為 package name 時，它是對不上的：

```
qty:learning_java_package_import qrtt1$ unzip -l library.jar
Archive:  library.jar
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  07-06-2018 13:47   output/
        0  07-05-2018 23:19   output/com/
        0  07-05-2018 23:19   output/com/bruceeckel/
        0  07-06-2018 13:47   output/com/bruceeckel/simple/
      381  07-06-2018 13:47   output/com/bruceeckel/simple/List.class
      387  07-06-2018 13:47   output/com/bruceeckel/simple/Vector.class
---------                     -------
      768                     6 files
```

以 Vector 為例：

```
output/com/bruceeckel/simple/Vector.class
```

將 `/` 取代為 `.`，並去掉 `.class` 即為原來的 fully qualified name：

```java
output.com.bruceeckel.simple.Vector
```

這明顯與我們期望是不同的：

```java
com.bruceeckel.simple.Vector
```

所以，應該要在打包時不含 `output` 那層的路徑。

#### 將 jar 加入 classpath

我們重新打包一份正確的 jar：

```
qty:learning_java_package_import qrtt1$ unzip -l library.jar
Archive:  library.jar
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  07-05-2018 23:19   com/
        0  07-05-2018 23:19   com/bruceeckel/
        0  07-06-2018 13:47   com/bruceeckel/simple/
      381  07-06-2018 13:47   com/bruceeckel/simple/List.class
      387  07-06-2018 13:47   com/bruceeckel/simple/Vector.class
---------                     -------
      768                     5 files
```

編譯它：

```
javac -verbose -cp ../library.jar Main.java
```

可以觀察到，它是由 ../library.jar 內讀取的：

```
[loading ZipFileIndexFileObject[../library.jar(com/bruceeckel/simple/Vector.class)]]
[loading ZipFileIndexFileObject[../library.jar(com/bruceeckel/simple/List.class)]]
```

### 執行程式

java 與 javac 的 `-cp` 用法是一樣的，所以我們可以這檔執行它：

```
qty:lab qrtt1$ java -cp ../library.jar:. Main
com.bruceeckel.util.Vector
com.bruceeckel.util.List
```

PS. 除了 library 本身，目前目錄有 Main.class，所以也要把 `.` 加進去，讓它可以搜尋到 Main.class


## classpath 冷知識

### 同名的 class，先載入的先使用

為了實驗同名 class 的使用順序，我們修改一下原始碼，加印了 `第2版`：

```patch
diff --git a/misc/learning_java_package_import/com/bruceeckel/simple/List.java b/misc/learning_java_package_import/com/bruceeckel/simple/List.java
index a86892c..33cf133 100644
--- a/misc/learning_java_package_import/com/bruceeckel/simple/List.java
+++ b/misc/learning_java_package_import/com/bruceeckel/simple/List.java
@@ -2,6 +2,6 @@ package com.bruceeckel.simple;

 public class List {
     public List() {
-        System.out.println("com.bruceeckel.util.List");
+        System.out.println("com.bruceeckel.util.List 第2版");
     }
 }
diff --git a/misc/learning_java_package_import/com/bruceeckel/simple/Vector.java b/misc/learning_java_package_import/com/bruceeckel/simple/Vector.java
index fde08ba..9b07640 100644
--- a/misc/learning_java_package_import/com/bruceeckel/simple/Vector.java
+++ b/misc/learning_java_package_import/com/bruceeckel/simple/Vector.java
@@ -2,6 +2,6 @@ package com.bruceeckel.simple;

 public class Vector {
     public Vector() {
-        System.out.println("com.bruceeckel.util.Vector");
+        System.out.println("com.bruceeckel.util.Vector 第二版");
     }
 }
```

我們沒有重編 Main.java，但換了不同的 library 執行看看：

```
qty:lab qrtt1$ java -cp ../library_v1.jar:. Main
com.bruceeckel.util.Vector
com.bruceeckel.util.List
```

```
qty:lab qrtt1$ java -cp ../library_v2.jar:. Main
com.bruceeckel.util.Vector 第二版
com.bruceeckel.util.List 第2版
```

那麼現在問題來了，如果它們同時在 classpath 上會怎麼樣呢？

#### v1 在前的效果

```
qty:lab qrtt1$ java -cp ../library_v1.jar:../library_v2.jar:. Main
com.bruceeckel.util.Vector
com.bruceeckel.util.List
```

#### v2 在前的效果

```
qty:lab qrtt1$ java -cp ../library_v2.jar:../library_v1.jar:. Main
com.bruceeckel.util.Vector 第二版
com.bruceeckel.util.List 第2版
```

由上面的實驗可以知道，先被發現的就先使用了。這個的延伸知識就是，當我們覺得使用的函式庫行為不如預期時，或編譯得過，但執行不過。那可能有不同版本在 classpath 內影響了。

### class shadowing

基於上面的問題，就會產生 `class shadowing` 經典的面試題目，就是因為載入順序問題，而讓某些 class 的行為不同了。本質上就是解說前一段的效果而結案。

同時，因為這個副作用，我們可以拿它來做點 patch 的動作，例如我們仿版友的提問 [如何加入新檔案到現有的jar檔？](https://www.ptt.cc/bbs/java/M.1528181565.A.99F.html)

```
qty:class-loading qrtt1$ tree
.
├── CssLoader.class
├── CssLoader.java
├── base.css
├── css-library.jar
└── patched
    └── base.css
```

實作一個簡單的讀取 css 檔，並印出來的動作：

```java
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class CssLoader {

    public CssLoader() throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (InputStream input = CssLoader.class.getResourceAsStream("/base.css")) {
            while (true) {
                int data = input.read();
                if (data == -1) {
                    break;
                }
                output.write(data);
            }
        }
        System.out.println(new String(output.toByteArray(), StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws IOException {
        new CssLoader();
    }
}
```

```css
body {
  color: red;
}
```

打包並執行：

```
qty:class-loading qrtt1$ zip css-library.jar CssLoader.class base.css
  adding: CssLoader.class (deflated 39%)
  adding: base.css (stored 0%)
```

可以看到，它讀入的原在 jar 內的檔案：

```
qty:class-loading qrtt1$ java -cp css-library.jar CssLoader
body {
  color: red;
}
```

現在我們在 classpath 上動一下手腳，加了 patched 目錄：

```
qty:class-loading qrtt1$ cat patched/base.css
body {
  color: green;
}
```

紅色就換成了綠色：

```
qty:class-loading qrtt1$ java -cp patched:css-library.jar CssLoader
body {
  color: green;
}
```

透過 shadowing 的功能，連打包在 jar 內的靜態檔也是能替換的。