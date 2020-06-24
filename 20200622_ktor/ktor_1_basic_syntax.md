# ktor 是怎麼打造出來的 [1]

最近跟著 kotlin 讀書會一起研讀 [Kotlin Programming: The Big Nerd Ranch Guide](https://www.amazon.com/Kotlin-Programming-Nerd-Ranch-Guide/dp/0135161630)，沒想到一週一週讀下來，還是有點進步的，由還不太會寫 kotlin 到能看懂一些基本的語法，到後面被廣告使用的 Lambda 與 Receiver 併用的語法都能略懂略懂，總算是對花下去的時間有所交待。

那麼書讀完了之後要做些什麼呢？依讀書會後續的計劃會有不同的學習小組給「畢業生」們有地方可以精進，其中有個主題是 [ktor](https://ktor.io/) 相關的。ktor 是一個以 kotlin 特性打造出來的 (Web) Framework，它高度利用了 kotlin 的幾個特性：

* Coroutines
* Function Type
* Extension Function
* Receiver

配合了經典的 [Intercepting filter pattern](https://en.wikipedia.org/wiki/Intercepting_filter_pattern) 完成了 ktor 的核心。設計的核心僅圍繞著 [Pipeline 與 Interceptor](https://ktor.io/advanced/pipeline.html) 為主軸，因此我們可以透過簡單地實驗來展示它，體驗它是如何運作的。

# 先由基礎語法談起

```kotlin
package com.example

import io.ktor.application.*
import io.ktor.features.*
import io.ktor.html.respondHtml

import io.ktor.response.*
import io.ktor.request.*
import io.ktor.routing.*
import io.ktor.http.*
import io.ktor.locations.*
import io.ktor.sessions.sessions
import kotlinx.html.*

fun main(args: Array<String>): Unit = io.ktor.server.netty.EngineMain.main(args)

@Suppress("unused") // Referenced in application.conf
@kotlin.jvm.JvmOverloads
fun Application.module(testing: Boolean = false) {
    install(DefaultHeaders)
    install(CallLogging)
    routing {
        get("/") {
            call.respondHtml {
                head {
                    title { +"Ktor: netty" }
                }
                body {
                    p {
                        +"Hello from Ktor Netty engine sample application"
                    }
                }

            }
        }
    }
}
```

上面這段程式是建立專案時產生的範例，滿滿的 DSL (domain specific language) 風格，是不是讓人覺得很 easy 呢？如果，我們先不管它背後的 domain，先單純看一下語法，你會發現 (特別是已經讀完一本書的書友們)，原來這些東西我們都在書上學過了。

```kotlin
fun Application.module(testing: Boolean = false) {
}
```

先來看看開頭的 `module`，它是一個 function 但被寫在了某個類別之後，這顯然是個 Extension Function。所以，我們意料之中的事：

* 這名為 module 的 function 屬於 Application 類別，在 Application 被實體化後能使用它。所以，在這 function 內，最初的 this 即為 Application 物件。

## install 函式 

接著，我們看第 1 層的 function：

```kotlin
fun Application.module(testing: Boolean = false) {
    install(DefaultHeaders)
    install(CallLogging)
    routing {
        // ... (skip) ...
    }
}
```

首先會遇到 install 函式，它的定義如下：

```kotlin
fun <P : Pipeline<*, ApplicationCall>, B : Any, F : Any> P.install(
    feature: ApplicationFeature<P, B, F>,
    configure: B.() -> Unit = {}
): F {
    // ... (skip) ...
}
```

我們可以看到，它是一個 extension function，並且依附在 Generic Type `P`，而 `P` 是 Pipeline 類別。換句話說，它是屬於 Pipeline 類別的 extension function。回頭看一下程式，我們期望的 this 是個 Application，但卻用了 Pipeline 類別的 extension function，合理的解釋就是它們有繼承的關係。

我們有幾個簡單的方式能驗證它們具有繼承關係。第一種最直覺簡單，即使沒有 IDE 輔助也能做，直接用 `is` operator 看是不是屬於 Pipeline 類別：

```kotlin
fun Application.module(testing: Boolean = false) {
    println(this is Pipeline<*, *>)
    install(DefaultHeaders)
    // ... (skip) ...
}
```

或是直接追入原始碼，看 Application 是否繼承 Pipeline，在追了 2 層後，我們找到了它繼承自 Pipeline 的證據 (如果你有使用 IDE 可以直接使用顯示繼承樹的功能，例如 IDEA 在 Application 類別上按 Ctrl + H)：

```kotlin
class Application(val environment: ApplicationEnvironment) : ApplicationCallPipeline(), CoroutineScope {
    // ... (skip) ...
}

open class ApplicationCallPipeline : Pipeline<Unit, ApplicationCall>(Setup, Monitoring, Features, Call, Fallback) {
    // ... (skip) ...
}
```

因此，在 install 的例子上，我們看到幾個學習過的語法被混搭使用：

* Extenstion Function
* Generic Type
* Inheritance (繼承)

## routing 函式 

```kotlin
fun Application.routing(configuration: Routing.() -> Unit): Routing =
    featureOrNull(Routing)?.apply(configuration) ?: install(Routing, configuration)
```

接著，另一個 routing 它是怎麼定義的呢？它使用了 Receiver！我們會稱呼一個 Function Type 是 Receiver 是因為在此  Function Type 前多加了 `Type.`，就是表示接下來此 Function Type 做的動作的「主詞」就是這個 Receiver。

簡單複習了 Receiver 後，我們就能看明白 routing `{ }` 內做的事，就是對 `Routing` 物件來做的：

```kotlin
    routing {
        get("/") {
            call.respondHtml {
                head {
                    title { +"Ktor: netty" }
                }
                body {
                    p {
                        +"Hello from Ktor Netty engine sample application"
                    }
                }

            }
        }
    }
```

那麼 Routing 物件是怎麼生出來的呢？顯然就是來自：

```kotlin
fun Application.routing(configuration: Routing.() -> Unit): Routing =
    featureOrNull(Routing)?.apply(configuration) ?: install(Routing, configuration)
```

我們先不深入其它函式，直接說明它的功用：

* featureOrNull 檢查是不是曾經註冊過此 Feature
* install 註冊這個 Feature

我們注意到 featureOrNull 表示會回傳 null 表示沒有人註冊過，因此，在它後面的 `?.` safe call operator 就顯得重要，如果它不是 null，就會執行 scope function `apply` 後，回傳 Routing 物件。若沒有人註冊過，那就會使用 `?:` null coalescing operator 期望的預設行為，呼叫 install 函式。

## 語法總複習

在初探 ktor 的這一小步，我們先由基礎語法的視角來欣賞它。摘要一下複習到的語法：

* Function Type
* Extension Function
* Receiver
* Generic Type
* Null Safety (`?.` `?:`)

在下一篇，我們會進行 install 內部的機制來欣賞 ktor 的實作。