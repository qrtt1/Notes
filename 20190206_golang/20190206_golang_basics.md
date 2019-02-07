因為過年閒閒沒事，開始來看一點 Go Lang 的書，從官網連結中找到一本『小』書 [The Little Go Book](https://www.openmymind.net/The-Little-Go-Book/)，它是 2014 年發佈的，僅介紹基礎的部分，整份 PDF 只有 84 頁，用來入門的負擔應該不會太大。

另外，可以觀察到這本書的一個特色，作者應該很喜歡七龍珠。一些變數或自訂結構的名稱如：

* Saiyan 賽亞人
* Goku 悟空

所以，才會在第 1 個例子有戰鬥力的數值。

## The Basics (1)

1. 變數宣告
2. 型態推論
3. 函式

第 1 章是介紹基礎知識，除了如何開始跑出第 1 隻 hello world 程式，並開始使用 `import` 來使用 standard library 的功能，還有語法的一些基本常識之外沒有太多難以理解的部分。

### 變數

只是變數宣告或函式宣告的順序跟以外習慣的 Java 或 Python 不太相同。這點可以透過 language specification 中的[語法規則](https://golang.org/ref/spec#Variable_declarations)來說明：

```bnf
VarDecl     = "var" ( VarSpec | "(" { VarSpec ";" } ")" ) .
VarSpec     = IdentifierList ( Type [ "=" ExpressionList ] | "=" ExpressionList ) .
```

能看得出在關鍵字 `var` 後要先接著 `IdentifierList` (簡單說就是一堆變數名稱)，最後才是接到 `Type`，如果有 assignment 的情況，才會再有 `=` 出現。書上的第 1 個宣告變數並開始使用它的範例為：

```go
var power int
power = 9000
```

其實也能寫成同一行，因為 golang 並不允許我們有未使用的變數或其它東西 (例如：import 了卻沒有使用)，它們會是編譯期的錯誤。在這一章，書會也介紹了比較短的宣告型式，並且我們可以省略 `Type` 的部分：

```go
power := 9000
```

同樣地，我們能回到官網找出對應的語法規格：

```bnf
ShortVarDecl = IdentifierList ":=" ExpressionList .
```

由於不再需要寫 `Type` 了，就是透過 golang 自行做型態推論，並且會自動檢查 `:=` 左方的變數 `有新的名字出現`，像我們無法連續寫 2 次的：

```go
power := 9000
power := 5566
```

在寫第 1 組的 `power :=` 前，power 不存在，它是新出現的變數可以宣告。第 2 組的 `:=` 左式，僅有 power 它出現過了，沒有其他新的變數了，編譯會失敗。要讓它合乎語法，我們得加入 `新` 的變數，把上面的例子改寫一下：

```go
power := 9000
power, action := 5566, 8787
```

第 2 組宣告出現了新變數，在語法上就合法了。對已出現過的 power 來說，就是重新賦值的動作而已 (但只能指定一相型態的 int)


### 函式

在第 1 章尾，開始介紹函式如何使用。內容相當簡單，我們截取一下官關的[語法規則](https://golang.org/ref/spec#Function_types)補充：

```bnf
FunctionType   = "func" Signature .
Signature      = Parameters [ Result ] .
Result         = Parameters | Type .
Parameters     = "(" [ ParameterList [ "," ] ] ")" .
ParameterList  = ParameterDecl { "," ParameterDecl } .
ParameterDecl  = [ IdentifierList ] [ "..." ] Type .
```

由上面的規則，可能衍生出下列的例子：

```go
func()
func(x int) int
func(a, _ int, z float32) bool
func(a, b int, z float32) (bool)
func(prefix string, values ...int)
func(a, b int, z float64, opt ...interface{}) (success bool)
func(int, int, float64) (float64, *[]int)
func(n int) func(p *T)
```

比對後可以知道，如同變數宣告一樣，函式的型態也是放在最後，或著可以沒有宣告回傳型態 (因為回傳的 Result 被 `[ ]` 包圍，表示它是 optional 的)：

```
FunctionType   = "func" Signature .
Signature      = Parameters [ Result ] .
```

在書上有提到一個接函式結果時，可以使用 `_` 作為不需要的值的慣例：

```go
_, exists := power("goku")
if exists == false {
// handle this error case
}
```

power 回傳的值為 `(戰鬥力, 是否有此人物)`，它問了 `悟空` 的 power 結果，在這段程式它只在意悟空存不存在，所以使用 `_` 來接目前情境下不重要的戰鬥力。另外做了一個小實驗 `_` 不會被視為 `new variables`，所以使用 `:=` 時不能單獨存在。

## Structures (2)

書上的第 2 部分為結構，並開宗明義表示 Go 並非 OOP 語言，它沒有物件的階層，所以也不會有承繼與多形。它會是一種以 structure 作為資料載體，並將 method 關聯到此結構的實作型式。

```go
type Saiyan struct {
	Name string
	Power int
}
```

結構的第 1 個範例是宣告了『賽亞人』，它有名子，有戰力數值。對寫過 C/C++ 的朋友，對這結構應該不算陌生，雖然語言有點變化，但意義上大致是一樣的。接下來有趣的例子是經驗的將 struct 傳進 function 後，並無法改變原始值的問題：

```go
func Super(s Saiyan) {
	s.Power += 10000
}

func main() {
	goku := Saiyan{
		Name:  "Goku",
		Power: 9000,
	}

	// 悟空要變超級賽亞人囉～～～
	Super(goku)
	fmt.Println(goku)
}
```

輸出結果為

```
{Goku 9000}
```

少了 1 萬點的戰力數值怎麼好意思叫超級賽亞人呢？於是要透過在 C/C++ 已經用到很熟的 `&` 與 `*`，透過傳址與指標來搞定它：

```go
func Super(s *Saiyan) {
	s.Power += 10000
}

func main() {
	goku := &Saiyan{
		Name:  "Goku",
		Power: 9000,
	}

	// 真的變超級賽亞人囉！！！共 19000 的戰力數值
	Super(goku)
	fmt.Println(goku)
}
```

接著，我們還差一點把 function 變得好看一點，實際上我們期望的會是：


```go
goku.Super()
```

而不是

```go
Super(goku)
```

這件事需要稍為改寫一下 Super 函式的宣告，有沒有很像 Python class 在定義 method 時，第 1 個參數要填 self 的感覺：

```go
func (s *Saiyan) Super() {
	s.Power += 10000
}

func main() {
	goku := &Saiyan{
		Name:  "Goku",
		Power: 9000,
	}

	goku.Super()
	fmt.Println(goku)
}
```

在[語法規格](https://golang.org/ref/spec#Method_declarations)上，被提出去的 `(s *Saiyan)` 稱作 Receiver：

```bnf
MethodDecl = "func" Receiver MethodName Signature [ FunctionBody ] .
Receiver   = Parameters .
```

它其實就是 `Parameters`，換句話說，是有變數名稱與 Type 的 list。一旦 function 有了 Receiver，我們就改稱它叫 Method 囉！覺得這詞語慣例其實也挺 OOP 的就是，雖然它沒不支援繼承。 

在這裡需注意一下，書上雖然用 struct 來示範，但作為 Receiver 的型態，並沒有限制在 struct，請見[golang patterns 的範例](http://www.golangpatterns.info/object-oriented/classes)

### 建構子

建構子的概念來自 OOP，即使 golang 不支援我們定義 class，但仍有自訂型態可以用，像 structure 就是一種。所以，慣例上會替 structure 實作 factory method 來建立它：

```go
func NewSaiyan(name string, power int) *Saiyan {
	return &Saiyan{name, power}
}
```

其實就是傳回一個建立好的 Saiyan 結構的位置罷了 (目前的範例不夠大，若建構流程比較多事要做的話，準備 factory method 是合理的選項)。在關於建構子的話題，書上也順便介紹了 `new` 內建函式，它其實是簡化語法用的：


```go
s := &Saiyan{}
s := new(Saiyan)
```

可以直接看 `new` 的定義，僅僅配置好空間，並回傳一個指標：

```go
// The new built-in function allocates memory. The first argument is a type,
// not a value, and the value returned is a pointer to a newly
// allocated zero value of that type.
func new(Type) *Type
```

由於使用 new 函式建立物件，仍要各別指定欄位的內容，跟直接寫在結構內初始參數沒太大差異。本書的作者認為，後者比較被多人接受：

```go
goku := new(Saiyan)
goku.name = "goku"
goku.power = 9001
//vs
goku := &Saiyan {
name: "goku",
power: 9000,
}
```

### 聚合

基於 golang 不支援 class 語法，一些相應用使用方式都會以 structure 為主，例如過去常在 OOP 內把物件嵌入某個物件之內，並透過委派 (delegation) 來間接使用聚合物件的功能。在 golang 裡，要成為聚合 (composition) 只要 `不宣告欄位名稱` 即可：

```go
type Person struct {
	Name string
}

type Saiyan struct {
	*Person
	Power  int
}
```

改寫賽亞人，把名字的部分拆出去到 Person 結構之中，為了讓 Person 在 Saiyan 內是個聚合的型式，我們宣告它的名稱。接下來我們能針對 Person 提供 method

```go
func (p *Person) Introduce() {
	fmt.Printf("Hi, I'm %s\n", p.Name)
}
```

神奇的事發生了，我們能直接對 Saiyan 使用這個 method：

```go
goku.Introduce()
// 會印出 Hi, I'm Goku
```

雖然 Receiver 並非針對 Saiyan，但在 Saiyan 內隱含著有 Person，於是它就會被呼叫到了。

## Maps, Arrays and Slices (3)

書上的第 3 部分為常見的容器介紹，這部分大致上就熟悉語法為主。其中比較特別的大概就 slice 的部分了，在其它靜態語言比較少在初學書籍就介紹這一塊，也許要先猜測這東西在 golang 中被廣泛地使用。若是學過 Python 的朋友，應該蠻習慣在 list 變數旁用 slice operation，概念上相似但 golang 中的用法不太一樣就是了。

### Array

陣列是多數語言都提供這個型態：一個固定長度的容器，完成配置就不能變更大小，像我們可以用 var 來宣告它，並指定第 1 個位置 87 分不能再高了：

```go
var scores [4]int
scores[0] = 87
```

我們也可以用 `:=` 同時完成宣告與配置，並利用 `for` 配合 `range` 

```go
scores := [4]int{55, 66, 87, 87}

for index, value := range scores {
	fmt.Println(index, value)
}
```

這裡值得注意的地方是 `range` 是 golang 的關鍵字，不像 Python 是提供 range generator 來進行 iteration。另外，若是用 GoLand 開發的話，它的 [Postfix Completion](https://www.jetbrains.com/help/go/settings-postfix-completion.html) 有支援 `for range` 的樣版，名稱為 `forr`：

![](postfix_forr.png)

若單純想知道陣列的長度，有 len 函式可以使用：

```go
len(scores)
```

附帶一提由[語法規則](https://golang.org/ref/spec#Array_types)可以看出 `[]` 標註是在型態的前方：

```bnf
ArrayType   = "[" ArrayLength "]" ElementType .
ArrayLength = Expression .
ElementType = Type .
```

由陣列的語法來看，它似乎是只有 1 維，對話規格書的解說：

>  The elements can be addressed by integer indices 0 through len(a)-1. Array types are always one-dimensional but may be composed to form multi-dimensional types.

但英文文件的重點常在 `but` 轉折語之後：

> may be composed to form multi-dimensional types.

這句的玄機就是，看到 `[]` 起頭的宣告時，第 1 組會被當作陣列長度，之後的會變成 `ElementType`，所以，這樣寫是合法的：

```go
var test [3][3][3]int
test[0][0][0] = 9
test[0][0][1] = 7
test[0][0][2] = 8
fmt.Println(test)
```

### Slice

直接上 code !!! 在 golang 中用 make 函式來定義 slice (慣例的寫法)：

```go
scores := make([]int, 0, 10)
fmt.Println(scores)
```

make 函式配合 slice 使用，後面接著 `長度` 與 `容量`：

```go
make([]T, length, capacity)
```

語法規格有提到下面 2 者是等價的：

> produces the same slice as allocating an array and slicing it, so these two expressions are equivalent:

```go
make([]int, 50, 100)
new([100]int)[0:50]
```

另外 [make](https://golang.org/ref/spec#Making_slices_maps_and_channels) 其實有 overloading，會因為第 1 個參數不同而有不同的效果，它分別對於 slice、map 與 channel 有不同的意義。

### Map

Map 的[語法規格](https://golang.org/ref/spec#Map_types)如下：

```bnf
MapType     = "map" "[" KeyType "]" ElementType .
KeyType     = Type .
```

宣告 map 時，就使用 `map` 關鍵字，配合 `[]` 在中間放 key 的型態，尾端放 value 的型態即可，書中簡單的例子如下：

```go
func main() {
	lookup := make(map[string]int)
	lookup["goku"] = 9001

	power, exists := lookup["vegeta"]
	fmt.Println(power, exists)
}
```

它查了一個不存在 map 的人物 vegeta (經 google 查詢，似乎是達爾)，獲得：

```
0 false
```

學會使用 map 後，書上提供了與 `struct` 併用的例子：

```go
goku := &Saiyan{
	Name:    "Goku",
	Friends: make(map[string]*Saiyan),
}
goku.Friends["krillin"] = &Saiyan{
	Name:    "Krillin",
	Friends: nil,
}
```

其它常用的功能：

* 用 `len(m)` 來問 key 的數量
* 用 `delete(m, k)` 來刪除 key
* 一樣支援 `for` 與 `range` 的搭配

## Code Organization and Interfaces (4)

### package

在第 4 章裡，主要是講述 `package` 與 `import` 的使用方法，另外也介紹 `interface`。由於這部分的概念在許多語言都有，其實不算太新鮮的事，若不去問 golang 如何做的，單純需要能理解語法怎麼用的程度，區分上不會太大。

由於 golang 不像 Java 有 class 或 也不像 Python 有 module，能作為變數或 method 的載體的容器，觀察看起 `檔名` 對於 golang 是沒有意義的，它會將所有的變數或函式儲放在 `package name` 的空間內，所以 `package name` 會成為一個 reference，能用來存取相關的變數或函式。

由 [package 的語法規格](https://golang.org/ref/spec#Packages) 可以知道：

> Go programs are constructed by linking together packages. A package in turn is constructed from one or more source files that ...

相同 package name 的 source code 會被連結在一起最後生出 Go 應用程式：

```bnf
SourceFile       = PackageClause ";" { ImportDecl ";" } { TopLevelDecl ";" } .
```

我們可以看出，在一個原始檔內，需要由 `package` 子句開頭的規則。需注意的是，不像 Java 需要寫完整的 package 名稱，golang 宣告 package 時只需要該相對錄路的名稱即可。

此外，書本上有介紹到 `Cyclical Imports` 的問題需要注意，還有 `Visibility` 的問題，這也終於解開了我對於為何 Golang 都是大寫開頭的命名慣例的疑問：

> Go uses a simple rule to define what types and functions are visible outside of a package. If the name of the type or function starts with an uppercase letter, it’s visible. If it starts with a lowercase letter, it isn’t.

大寫開頭的變數或函式才能被 export 出來，讓其它人使用。

### import

書上對於 import 的介紹不算多，但在看語法規格時發現了個實用的用法，可以替 [import](https://golang.org/ref/spec#Import_declarations) 的 `package name` 改變名稱：

```
ImportDecl       = "import" ( ImportSpec | "(" { ImportSpec ";" } ")" ) .
ImportSpec       = [ "." | PackageName ] ImportPath .
ImportPath       = string_lit .
```

在比較單純的情況，我們的 ImportSpec 只有單純寫 ImportPath 而已，但有些情況我們會希望替它改名稱，它給了我們些範例：

```go
Import declaration          Local name of Sin

import   "lib/math"         math.Sin
import m "lib/math"         m.Sin
import . "lib/math"         Sin
```

* 第 1 個例子是原本的寫法，需要使用 `math` package name 作為 reference 來使用 Sin 函式
* 第 2 個例子，將 package name 定義為 `m`，使用 `m.Sin` 來呼叫 Sin 函式
* 第 3 個例子將 package name 指定為當前的 package，在同一個 scope 下，不用額外加 reference

### import _

在 import 的語法規格，還有介紹到一個特殊的 package name：

```go
import _ "lib/math"
```

它的功能描述如下：

> An import declaration declares a dependency relation between the importing and imported package. It is illegal for a package to import itself, directly or indirectly, or to directly import a package without referring to any of its exported identifiers. To import a package solely for its side-effects (initialization), use the blank identifier as explicit package name

大意是說，因為 golang 不能讓我們 import 了又不使用它，但有些情況我們需要 import 它，舉個 Java 程式設計師懂得例子：

```java
Class.forName("com.mysql.jdbc.Driver");
```

我們透過 ClassLoader 來註冊 JDBC Driver，而 golang 沒有 class 的設計，但它有 [Package initialization](https://golang.org/ref/spec#Package_initialization)，所以對 golang 的資料庫相關的函式庫，透過這個機制來初始化 Driver，只需要 import 它就行。以 [lib/pq 的 conn.go](https://github.com/lib/pq/blob/v1.0.0/conn.go#L48) 為例：

```go
func init() {
	sql.Register("postgres", &Driver{})
}
```

當我們寫下 import 時，它完成了 postgres driver 的註冊：

```go
import (
  "database/sql"
  _ "github.com/lib/pq"
)
```

如同 `_` blank identify 的意義，它用來承接需要接下的變數，接下後丟棄。我們單純為了運用 import 後自動呼叫 `init()` 的副作用罷了。這例子取自於 [Why we import SQL drivers as the blank identifier ( _ ) in Go](https://www.calhoun.io/why-we-import-sql-drivers-with-the-blank-identifier/)

### interface

這章介紹的 interface 用法很平常，但在第 5 章的 `Empty Interface and Conversions` 看到偽 overloading 的希望。


