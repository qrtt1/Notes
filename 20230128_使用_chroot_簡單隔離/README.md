# 使用 chroot 簡單隔離

當 [Love Letter](https://github.com/Game-as-a-Service/LoveLetter) 製作到一個段落之後，已經適合將它實際部署出來，讓有興趣的人開始試玩囉！

目前手邊只有一台平時在用的迷你 Linux Server，放置日常生活用的各種小程式或爬蟲。為了保持最容易重建的狀態，幾乎只有裝了 Java SE 與定時安全更新，就沒有安裝多餘的套件了。在這麼 `純` 的環境下，自然也沒有安裝 docker 這類的容器管理工具。

那麼，要讓比較舊的 Ubuntu 上，使用近期用新的 Python 版本開發的專案，有沒有可以像 container 般的工具可以使用呢？

## Container 是什麼？

Container 具體來說並不是一種技術，它是一個概念：將 process 隔離起來，就好像整個執行環境 (OS) 就專門給這個 process 使用一樣。

想要隔離 process 這個想法，在 Linux kernel 開始支援 namespace 後更加地便利 (From  kernel version 2.6.24 in 2008)，但 namespace 只是控制 process 能「看到」什麼，但是資源用限制，得依賴 cgroup 來限制，例如：可以用多少記憶體或是能驅動多少 CPU 運算能力。

我們可以透過 [namespace](https://man7.org/linux/man-pages/man7/namespaces.7.html) 的說明文件得知，他支援的類別來思考 namesapce 可以隔離些什麼：

<img src="https://i.imgur.com/Qk4lkag.png" width="360" />

進一步精采地說明，相當推薦觀看：

[Cgroups, namespaces, and beyond: what are containers made from?](https://www.youtube.com/watch?v=sK5i-N34im8)

![](images/O8baDp5.jpg)

## 隔離的目標

想要有一個像使用 docker 開一個 container 的「感覺」，有一個不同於 host 的執行環境能夠執行我們新專案下指定的 Python 3.10 版，並且不會影響到原本 host 執行環境。

當然，我們可以利用 namespace 來達成目標，但在有個比 namespace 更久遠的指令，可以簡單在 filesystem 上隔離出新的執行環境，那就是 [chroot](https://en.wikipedia.org/wiki/Chroot)。

這對於曾經有 Linux 系統內「在特定子目錄，安裝一個新的 Linux 的流程」經驗的人，一定不陌生 `chroot` 的用法：

```shell
$ sudo chroot /path-to-base-system
```

## 具體做法

1. 準備好一個 base-system (具有完整 Linux 系統的子目錄)
2. 用 chroot 切換至子系統
3. 正常地在 chroot 之下使用它 (想像它，就是 container)

準備 base-system 可以利用 docker 來做，部署目標也許沒有 docker，但開發的機器上有裝 container tool 是合情合理的。

```shell
$ docker export container-id -o save.tar
```

我們利用 `export` 指令，將啟動好的 container 的 filesystem 備份起來。接著將備份檔 `save.tar` 複製至目錄機器，在工作目錄解開它：

```shell
$ sudo chroot /home/ubuntu/love-letter-working-directory
```

### in host

```shell
$ python3 -V
Python 3.8.10
```

### in chroot

```shell
$ python3 -V
Python 3.10.8
```

執行主程式 (在 host 內，當然沒有裝 poetry 囉！它只能在 chroot 內的 base system 中執行)：

```shell
root@ip-172-30-0-62:/app# poetry run uvicorn love_letter.web.app:app --host 0.0.0.0 --port 80
INFO:     Started server process [1396038]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:80 (Press CTRL+C to quit)
```
