## osx *image not found*

在 osx 編譯出的執行檔用 dylib 時可能會找不到它的位置

```
qty:OUT qrtt1$ ./a.out
dyld: Library not loaded: @rpath/libbinlogevents.dylib
  Referenced from: /Users/qrtt1/temp/MYWORKS/mysql-binary-log-events-1.0.2-labs/OUT/./a.out
  Reason: image not found
Abort trap: 6
```

用 otool 檢查一下

```
qty:OUT qrtt1$ otool -L a.out
a.out:
    @rpath/libbinlogevents.dylib (compatibility version 0.0.0, current version 0.0.0)
    @rpath/libmysqlstream.1.dylib (compatibility version 1.0.0, current version 0.1.0)
    /usr/lib/libc++.1.dylib (compatibility version 1.0.0, current version 307.4.0)
    /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1238.0.0)
```

在網路上找到一篇文章 [How to copy (and relink) binaries on OSX using otool and install_name_tool](http://thecourtsofchaos.com/2013/09/16/how-to-copy-and-relink-binaries-on-osx/)，可以修改編好的 link 位置：

```
install_name_tool -change @rpath/libbinlogevents.dylib @executable_path/lib/libbinlogevents.dylib a.out
install_name_tool -change @rpath/libmysqlstream.1.dylib @executable_path/lib/libmysqlstream.1.dylib a.out
```

跑完後，神奇的可以用囉！

```
qty:OUT qrtt1$ otool -L a.out
a.out:
    @executable_path/lib/libbinlogevents.dylib (compatibility version 0.0.0, current version 0.0.0)
    @executable_path/lib/libmysqlstream.1.dylib (compatibility version 1.0.0, current version 0.1.0)
    /usr/lib/libc++.1.dylib (compatibility version 1.0.0, current version 307.4.0)
    /usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1238.0.0)
```

```
qty:OUT qrtt1$ ./a.out
Usage: a.out <uri>
```
