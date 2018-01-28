## Maven Metadata Cache

### 相依管理上的卡卡讓工作不順了嗎？

上個月看到臉友發佈了一個工具 [可以把 gradle dependency 抓到 local 的 tool](https://www.facebook.com/jintinlin/posts/2109657829051314)，第一個念頭是為什麼有這個需求呢？經過討論後，是使用一些特定的 Maven Repository 時，要重拉相依函式庫的情況可能會有些慢。所以 [syndle](https://github.com/Jintin/syndle) 就被創造了出來。

在相近的時間，也替不同的網友看了使用 Gradle 在 Android Stdio 執行 Sync 時會住的問題。是因為 https://jitpack.io/ 在一些情境下會連線過久，或是當 Gradle 試著打 `HTTP HEAD` 詢問有沒有檔案時，進入了無限的 302 重新導向。

即使都有檔案存在，當沒有指定 `gradle --offline` 時，在確認相依關係的必要動作都會向遠端的 Server 詢問讓檔案的 `sha1 hex`。只要相依的檔案一多，那就會發出發次的 `HTTP GET` 取得檔案的 `sha1 hex`，用來確定是否需要下載新的檔案更新 local 端的檔案。

雖然重新整理相依關係不是那麼常做的事，但一需要做通常是比較想要獲得立即的結果。所以，[jintinlin](https://www.facebook.com/jintinlin) 的想法是先將檔案下載回來，再讓 Gradle 設定吃 local 的 Maven Repository。模擬一下 Build Script 大致需要這麼寫：

```groovy
repositories {
    maven {
        url = '/path/to/syndle/downloaded/maven-repo'
    }
    mavenCentral()
}
dependencies {
    ...
}
```

### 思考同一個題目的不同解法

在最初的時候，還不太能同理為何需這樣的工具誕生。直到我週間台北新竹來回開會的時候，在高鐵上用飄忽不定的手機網路，要重新更新相依性的 metadata 時：

```
gradle cleanEclipse eclipse
```

它就會要進行所有的 `.jar` `-source.jar` 的 `sha1 hex` 確認，不巧我正在處理 Spark 的專案，相依性列出接近 7 百多個函式庫，那麼加上 source jar 就可能有 1400 多個 HTTP Request 要被執行。在網路順暢的時候，我也許要花上 2 分多鐘來等待它完成。那天在高鐵上，我只能放棄了這個動作。

先前與 [jintinlin](https://www.facebook.com/jintinlin) 討論給的建議是，若是要解決公司內拉檔案的效率，那直接架一個 [Nexus Repository OSS](https://www.sonatype.com/nexus-repository-oss) 解決若干的 Maven Repository 拖慢速度的問題。相較於我的情況，也許我該在自己的工作環境上架一個，以適應網路品質不穩定時的情況。

若我真的這麼做了，我的 Build Script 大概會像是：

```groovy
repositories {
    maven {
        url = 'http://127.0.0.1/1234/nexus/...'
    }
}
dependencies {
    ...
}
```

那麼每回把專案由 SCM 取回來時，我得先修改一下設定。要 commit code 時，得記得不要把它弄上去了。或是「恥力」高一點，把這個設定給 commit 進去，讓同事中招。理性地想想，這樣似乎不是辦法，我需要一個臨時的 Maven Proxy 並且它能自動地掛進 Build Script 內。基於這個基本的想法，我建了個新的 side project [gradle-maven-metadata-cache-plugin](https://github.com/qrtt1/gradle-maven-metadata-cache-plugin)，它是一個 Gradle Plugin：

```groovy
buildscript {
    repositories {
        maven { url 'https://jitpack.io' }
        mavenCentral()
    }
    dependencies {
        classpath 'com.github.qrtt1:gradle-maven-metadata-cache-plugin:v0.1-alpha.3'
    }
}

apply plugin: org.qrtt1.gradle.MavenCacheRuleSource
```

運作方式其實挺簡單的，就當 Build Script 執行時，去掃所有的 `repositories` 設定，在執行期把它換成一個 local 的 http server：

```
repositories {
    maven { url 'http://127.0.0.1:5566' }
}
```

這個 http server 它的 port 總是隨機的，它的行為就如同 Maven Repository 一致，但實際上它會把 HTTP Request 傳給原來開發者寫的那些 Maven Repository。那麼剛剛提到的 Spark 相關的專案，它的重新建立相依性資料由 2 分多鐘，降低至 6 秒鐘。其他的小專案可能沒有感覺，但當網路變糟時，你真心會覺得得救了。

### Side Project 實作模式

去年讀了朋友推薦的《學徒模式》後，反省了一下真的太久沒專程為自己寫 code 了。工作上有很多有趣的東西能玩（剛開始做時都不覺得有趣，但工作好像會黏人，第一人稱視角下總人發現有趣的『點』），但自己專程寫點新的 idea 也挺好的。

在書中描述到，side project 的重要性，我們能專注在一個主題上，實踐過去學到的技能，或在熟悉的領域上投入新的東西（新的、想學的、剛學的）加以應用，這樣的過程讓我們能在相對安全的範圍內「有效練習」(PS. 《刻意練習》也很推薦呦)，在這新的 side project 內，舊有的東西是 Gradle Plugin 開發的知識：

* [Gradle RuleSource Plugin 筆記](https://github.com/qrtt1/Notes/blob/master/20170312_gradle.rule.source.plugin.md)
* [Gradle 整合測試](https://github.com/qrtt1/Notes/blob/master/201604_gradle_testcase.md)

新的東西是：

* [《Kotlin in Action》](https://www.manning.com/books/kotlin-in-action) 書也買了，也看了二、三週，把基本章節都看完了，該用它來寫點具體的東西了
* [Gradle 支援了 kotlin dsl](https://github.com/gradle/kotlin-dsl)，算是基本的功能用了，但還很陽春，若真的看 samples 要多加應用會覺得還是放棄吧。所以，專案 Build Script 內的 Maven Publish 部分是用 groovy dsl 寫的。
* [IntelliJ CE](https://www.jetbrains.com/idea/download/) 寫 kotlin 還是用它比較順，雖然 JetBrains 有提供 Eclipse Plugin，可是實作挺陽春的，不算是堪用的東西。
* 使用 [jitpack.io](https://jitpack.io/) 發佈 Plugin，相較於 bintray 方便很多但連註冊都省了，這樣好像有點浮濫？
* [使用 Github Release](https://github.com/qrtt1/gradle-maven-metadata-cache-plugin/releases) 寫發佈資訊，剛好它也直接能跟 jitpack 整合，算是挺方便的。

綜合來說，我得到了一個被 Github 視為 `100 %` kotlin 實作的專案，終於有點跟得上潮流的感覺了。