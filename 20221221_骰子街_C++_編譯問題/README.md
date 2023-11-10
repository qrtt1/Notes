# 骰子街 C++ 編譯問題

### 前言

c/c++ 開發環境要比其他後出的語言稍為麻煩一點，但只要知道自己卡在哪就不會毫無解決的想法了。

標準的 c/c++ 其實是 `portable` 的，可以

> write once compile anywhere



所以，常會有接到工作說，可不可以幫忙 `porting` 到什麼平台。「不！」請說清楚，你沒有動到組語不要跟別人說 `porting` 啊！那只是 `compile` 的動作。

但要能正常的 compile，對專案使用到的「每一個相依函式庫」都得去各別的 `compile` (如果沒有直接的安裝方法)，或是去理解該函式庫使用的 toolchain 或編譯的方式。

通常有各自的「特色」，再加上它不像跑在 VM 的語言，可以假裝有一個世界大同的環境，才會處理起來比較麻煩。OS Distribution 的 Package Manager 中沒提供的，就是自己編譯啦！

昨日參與討論的過程，就是搞定編譯中常見的問題，其實撇開專案各自的 toolchain 選擇不同，說到底單純是搞定 Compiler 與 Linker 的參數而已。

### 處理的思路

看大家把焦點放在 cmake，但其實解決昨天的問題跟 cmake 本身的關係沒那麼直接，幫自己的思路 recap 一下。

> 問題的本質：要讓一組 c/c++ 的專案能夠編譯成功，就是搞定 compiler 的參數而已。

> > aka **缺什麼補什麼，多的就拿掉。** <= 湊答案





CMake 幫我們做什麼？CMake 是因為人工直接手刻的 Makefile 常常不能適用在不同的平台，刻 Linux 用的，不太考慮 Windows 用的開發者，刻 Windows 用的，不太考慮 Linux 的開發者，還有常常被遺忘的 Freedbsd 開發者。

因此，就會想要有一個幫忙產生 Makefile 的工具，雖然已經有 Autotools 系列的工具了，可是它對 Windows 不那麼友善，外加學習門檻不低。我自己也一直沒學會 Makefile 內的各種東西，但至少記得 target 的 indent 只能用 `TAB` 字元。

```
cmake -> makefile -> make -> (compiler 指令) -> 生出結果
```

我們使用 cmake，用它來生 makefile，再用 make 指令去間接執行 compiler 指令生出結果。為什麼要弄個像 pipeline 的東西呢？通常我們會把一個任務由出發到結果重要的環節「先準備好」，出事的時候先問自己，是哪一個環節，或哪二個之間出事了。

昨天的 2 個問題主要在 `(compiler 指令)` 階段出錯：

1. 找不到 header file
2. 沒辦法編譯出可執行的 test (有 error 產生)

知道 compiler 出錯，就要在腦中抓出相關的知識。對 c/c++ 來說有哪些常見的參數需要搞定？

1. `-I` header file 的 search path
2. `-L` (static/dynamic) library 的 search path
3. `-l` linker 參數

`找不到 header file` 就簡單對應到 `-I` 的問題，而 linker 階段出錯，就要研究 linker 的參數。

另一個問題是，得先知道 `compiler 指令` 具體下了什麼，我們對應回 `pipeline` 知，它的上一階段是 `make`，而 make 是依 makefile 定義的內容來的。只要回頭閱讀 makefile 內容，就會知道它下了什麼。但通常，我們不會人工去讀 code generator 生出來的東西 (除了組語之外)。

我需要它在 runtime 時的資料，有沒有像 `shell` 使用的 `-x` 能印出 debug info 的參數呢？試著上網 Google 有沒有讓 make 時也產生它下什麼指令的方法：

```
make VERBOSE=1
```

於是，我們得到最後 compiler 的指令是什麼。這時，我們就可以先透過這個指令，在跟他一樣的目錄 (test) 下執行，先看是不是 `reproducible`，只要能精準的重現問題，你的「實驗環境」就是建立成功了。

```
 $ /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/c++  -arch arm64 -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk -mmacosx-version-min=12.1 -Wl,-search_paths_first -Wl,-headerpad_max_install_names CMakeFiles/MachiKoroCPPTest.dir/test_main.cc.o -o /Users/qrtt1/temp/Machi-Koro-Cpp/bin/MachiKoroCPPTest  /opt/drogon/lib/libdrogon.a /opt/trantor/lib/libtrantor.a -lpthread -ldl /opt/homebrew/lib/libjsoncpp.dylib /opt/homebrew/lib/postgresql@14/libpq.dylib /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libsqlite3.tbd /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libz.tbd
Undefined symbols for architecture arm64:
  "MachiKoroGame::MachiKoroGame()", referenced from:
      drtest__BasicTest::doTest_(std::__1::shared_ptr<drogon::test::Case>) in test_main.cc.o
  "MachiKoroGame::~MachiKoroGame()", referenced from:
      drtest__BasicTest::doTest_(std::__1::shared_ptr<drogon::test::Case>) in test_main.cc.o
ld: symbol(s) not found for architecture arm64
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

指令很長，先用順手的工具把它切開方便閱讀：

```
(⎈ |microk8s:default)(base) ➜  test git:(main) ✗ python
Python 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:41:22) [Clang 13.0.1 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> for x in "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/c++  -arch arm64 -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk -mmacosx-version-min=12.1 -Wl,-search_paths_first -Wl,-headerpad_max_install_names CMakeFiles/MachiKoroCPPTest.dir/test_main.cc.o -o /Users/qrtt1/temp/Machi-Koro-Cpp/bin/MachiKoroCPPTest  /opt/drogon/lib/libdrogon.a /opt/trantor/lib/libtrantor.a -lpthread -ldl /opt/homebrew/lib/libjsoncpp.dylib /opt/homebrew/lib/postgresql@14/libpq.dylib /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libsqlite3.tbd /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libz.tbd".split(" "): print(x)
...
/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/c++

-arch
arm64
-isysroot
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk
-mmacosx-version-min=12.1
-Wl,-search_paths_first
-Wl,-headerpad_max_install_names
CMakeFiles/MachiKoroCPPTest.dir/test_main.cc.o
-o
/Users/qrtt1/temp/Machi-Koro-Cpp/bin/MachiKoroCPPTest

/opt/drogon/lib/libdrogon.a
/opt/trantor/lib/libtrantor.a
-lpthread
-ldl
/opt/homebrew/lib/libjsoncpp.dylib
/opt/homebrew/lib/postgresql@14/libpq.dylib
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libsqlite3.tbd
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX12.3.sdk/usr/lib/libz.tbd
>>>
```

實際上觀察，我們想要的 library 都有了，但在追加了 `MachiKoroGame` 類別後死掉的，所以它八成是少 link 了這個 obj 檔。在專案中需找一下它可能的位置：

```
(⎈ |microk8s:default)(base) ➜  test git:(main) ✗ find .. -name "*.o"
../test/CMakeFiles/MachiKoroCPPTest.dir/test_main.cc.o
../CMakeFiles/3.25.0/CompilerIdCXX/CMakeCXXCompilerId.o
../CMakeFiles/MachiKoroCPP.dir/models/src/player.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/main.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/landmark.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/machikoro_game.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/bank.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/card.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/architecture_market.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/hand.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/initial_building.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/building.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/important_building.cpp.o
../CMakeFiles/MachiKoroCPP.dir/models/src/general_building.cpp.o
```

發現了：

```
../CMakeFiles/MachiKoroCPP.dir/models/src/machikoro_game.cpp.o
```

將它補到 compiler 指令的最後一個參數，可編譯成功。最終得 `root cause` 是缺少了 linker 需要一起用的 obj 檔。到了這個步驟，我們才會再回頭看一下這個流程：

```
cmake -> makefile -> make -> (compiler 指令) -> 生出結果
```

需要回頭修幫我們產生 makefile 的 `CMakeLists.txt`：

```
CMakeLists.txt -> cmake -> makefile -> make -> (compiler 指令) -> 生出結果
```

畢竟，我們只是透過 cmake 來組出最後 Compiler 與 Linker 需要的參數，至少怎麼在 cmake 中組出常見的 3 個參數，還有必要的 2 類輸入檔案 (source code 還有 obj file) 那就是學到的時候，做好小抄下回拿來抄就夠了。
