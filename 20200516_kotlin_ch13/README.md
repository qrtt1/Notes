# Kotlin 讀書會 - CH 13 :: Initialization

接續著第 12 章，講解如何使用 class 關鍵字定義類別，在第 13 章專注在初始化的問題。

## 關鍵字

* class header (n)
* initialization (n)
  * everything required to make a variable, property, or class instance ready to use
  * creating an instance of a class

### Constructors (n)

* primary constructor (n)
* class header (n)
  * Player's header (n)
* Defining properties in a primary constructor (n)
* Secondary constructors (n)
* *this* keyword (n)

### Initialization

* initializer block (n)
* property initialization (n)
* initialization order (n)
* late initialization (n)
* lazy initialization (n)
* delegate (v)


## 引言::回顧 class 的定義方式 

* 定義一組 class
* 呼叫建構子
* 何為初始化 (Initialization)

https://www.youtube.com/watch?v=hqt6KML8YeE


## 關於建構子

* 什麼是主要建構子？
* 如何在主要建構子中定義 property？
* 什麼是次要建構子？
* this 關鍵字的用途是什麼？

https://www.youtube.com/watch?v=RlPm-9W-3Rk

https://www.youtube.com/watch?v=apUY9LetRrY

https://www.youtube.com/watch?v=l6cP0XALL6I

## 關於初始化 

* 什麼是 initializer block？能做什麼？
* property 初始化 
* 解說 initialization order
* 說明 initialization 的 late 與 lazy 的不同

https://www.youtube.com/watch?v=8Tpcf-xxqVw


# 總結一下重點

class 的基本結構為：

* HEADER: class `類別名稱`
* BODY: `{ }`

Primary Constructor 定義在 class header 上，在名稱後接著 `()` 就是了。

Primary Constructor 的參數列，可以定義一般的變數，或加上 `var` `val` 成為 class property，就如同直接寫在 class body 內的 class property 一樣。

Secondary Constructor 定義在 class body 內，以 `constructor` 作為名稱後接 `()` 引數列，與 Primary Constructor 的引數不同的是，它只能宣告一般的變數，並不能將變數設定為 class property (大概是因為它是初始化位階的最後一組唄)，而 Secondary Constructor 必需呼叫 Primary Constructor。

接著 Initialization 重點在初始化順序：

* Primary Constructor
* class property
* init block
* Secondary Constructor

另外，接續著遲延初始化，分為 late init (用在 var) 與 lazy init (用在 val) 二類。會有這需求是因為 Kotlin 對於 Null Safety 的保證，當我們建立好物件後，就應該要讓 non-null 的 property 都有值了，但有些情況特殊有些值在我們建立物件實體時並不存在，或它的開銷比較在，會希望真的用上時再來初始化，於是就有了這二類的延遲用法。




