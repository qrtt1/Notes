一般開發會先用 `conda` 開出一個 base env，然後在自己的專案下開 `venv` 或是 `poetry` 的環境來使用 (這部分就看喜好，也可以挑別的想用的)。

conda 開新的 env 主要是非 `Windows` 的系統中，常會 OS 內自帶了一組 Python 環境了，它跟系統內的一些管理工具是相關的。如果開發時裝的一些函式庫相衝時，想要重裝有可能不小心弄壞了系統預設的那組。

因此，我們常會在開專案之前的環境，先準備 conda env。而 conda env 很方便可以準備不同版本的 Python 基礎環境。像我自己的就有多組環境：

```
$ conda env list
# conda environments:
#
base                  *  /Users/qrtt1/miniforge3
osx-arm64                /Users/qrtt1/miniforge3/envs/osx-arm64
py311                    /Users/qrtt1/miniforge3/envs/py311
py38                     /Users/qrtt1/miniforge3/envs/py38
                         /Users/qrtt1/opt/anaconda3/envs/osx-arm64
```

> 即使你是在 Windows 下開發，也很鼓勵使用 conda 作為基礎環境。同樣的，記得在開新專案或執行時，得用到正確的 Python 執譯器就是了。



## 查詢 Python 環境

以 OSX 或 Linux 相容的環境來說，有簡單的 `command` 指令可以指出現在用哪一個 Python

```
$ command -v python
/Users/qrtt1/miniforge3/bin/python
```

> 如果是 Windows 使用者，你就去問一下 ChatGPT 怎麼查唄。



在啟用 venv 的情境下，它會 clone 一份迷你的環境至指定安裝的 `venv` 目錄 (你按裝時自己指定的)

```
$ (venv) piperider git:(feature/sc-31723/cli-show-stats) command -v python
/Users/qrtt1/temp/piperider/venv/bin/python
```

近年也流行使用 poetry 來管理專案的 Python 環境，但這就先以 `venv` 為例。多數的 IDE 或開發環境都可以讓你指定 Python 環境的位置，但 vscode 預設是認 `.venv` 如果你不是用這個，記得去改設定讓它自動抓得到 `venv` 或直接指定 `python` 指令的路徑。

而所謂的 IDE 能認出 venv 或是其它的 Python 環境管理工具，並不是它真的得知道 **你使用了什麼開發環境管理工具** 而是它透過不同工具的「安裝慣例」去自動搜尋 `python` 指令的位置。

找到這個位置是最重要的事，因為 Python Package 的搜尋路徑 (**PYTHONPATH** 變數可以追加新位置) 都是以它的位置推算出來的。

## 查看目前的搜尋路徑

知道如何查看目前的 Python 會去查訪哪些路徑是重要的，因為

> 當你覺得自己安裝好了函式庫 foo.bar 後，但你的 Python 一直跟你說它找不到 foo.bar 時。



> 非常有可能，你安裝函式庫的 Python 環境，與你「執行時」的 Python 環境是不同一個。



### 在 Python 內查詢搜尋路徑

```
$ python
Python 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:41:22) [Clang 13.0.1 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.path
['', '/Users/qrtt1/miniforge3/lib/python310.zip', '/Users/qrtt1/miniforge3/lib/python3.10', '/Users/qrtt1/miniforge3/lib/python3.10/lib-dynload', '/Users/qrtt1/miniforge3/lib/python3.10/site-packages']
>>>
```

用上面可以知道，我執行 `python` 指令，去列出它目前的搜尋位置。其中的 `''` 空字串為 `現在執行目錄`，可以推測使用的是單純的 conda 預設環境。那麼，我啟用了 `venv` 後，你會看到路徑有了點變化，多了 `venv` 的部分：

```
$ (venv) piperider git:(feature/sc-31723/cli-show-stats) python
Python 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:41:22) [Clang 13.0.1 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.path
['', '/Users/qrtt1/miniforge3/lib/python310.zip', '/Users/qrtt1/miniforge3/lib/python3.10', '/Users/qrtt1/miniforge3/lib/python3.10/lib-dynload', '/Users/qrtt1/temp/piperider/venv/lib/python3.10/site-packages']
>>>
```

我們透過純 conda 環境，與在 conda 環境下再進入個別專案的 `venv` 可以觀察到「搜尋路徑」是不同的。所以，你在 `venv` 安裝的函式庫在 conda 下是「看不到的」。除非，你在 conda 下又安裝一次，但這通常不是個好主意。

因為特定建了一個 venv 就是要避免去污染 conda 下的套件，我們不會特定把個別專案用的函式庫去安裝在 conda 環境上。除非，你很確定「其它專案」也都需要用到。

## 相關資源

* [在 VSCode 中指定 Python 環境](https://code.visualstudio.com/docs/python/environments)
* [在 VSCode 中設定 PYTHONPATH](https://code.visualstudio.com/docs/python/environments#_use-of-the-pythonpath-variable)
* [在 VSCode 中設定 Test Runner](https://code.visualstudio.com/docs/python/testing)

***

在 PyCharm 中，只要確認 Python 直譯器的位置是對的就行了，不太有設定的需求。
