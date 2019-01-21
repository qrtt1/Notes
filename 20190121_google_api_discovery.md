## Google API 文件

最近在使用一些 google api 時找不到文件說明，找不到文件並不是什麼新鮮事。由於得呼叫的 nodejs client 內也沒實作，那就得自己組一下 Request 來發送囉。由於文件沒有寫到底要用什麼樣的 Request URL，這有點難猜但還是可以找出來的。

針對『動態』語言，Google API 的 Client 多半是依賴 Service Discovery 來生出對應的 method 與 request，所以我們可以先碰運氣，直接去 `grep` library 內含有 discovery 字串的部分，看有沒有 URL 來替我們引路。


```
qty:qcdn-lab qrtt1$ grep -r discovery *
node_modules/gaxios/README.md:  url: 'https://www.googleapis.com/discovery/v1/apis/'
```

這看起來就很像是它了，開啟瀏覽器來看一下，觀察後發現它有各種 service 的列表，我們可以找出相關的。像是我需要的是 cloud compute engine 的部分：

```
qty:qcdn-lab qrtt1$ curl -s 'https://www.googleapis.com/discovery/v1/apis/' | grep compute |grep discoveryRestUrl
   "discoveryRestUrl": "https://www.googleapis.com/discovery/v1/apis/compute/alpha/rest",
   "discoveryRestUrl": "https://www.googleapis.com/discovery/v1/apis/compute/beta/rest",
   "discoveryRestUrl": "https://www.googleapis.com/discovery/v1/apis/compute/v1/rest",
```

這樣我們就有 3 個版本可以挑選了，先由正式版的功能開始看唄。目標是得找出文件上有的 `Instance Group Resize` 功能，但它只寫了 zone 版的，我們需要 region 版本的：

```
qty:qcdn-lab qrtt1$ curl -s 'https://www.googleapis.com/discovery/v1/apis/compute/v1/rest' | grep resize | grep path
     "path": "{project}/zones/{zone}/disks/{disk}/resize",
     "path": "{project}/zones/{zone}/instanceGroupManagers/{instanceGroupManager}/resize",
     "path": "{project}/regions/{region}/disks/{disk}/resize",
     "path": "{project}/regions/{region}/instanceGroupManagers/{instanceGroupManager}/resize",
```

這樣查完後，即可知道它其實 2 個版本的 API 在 server 端都有實作，回頭看整版 json 文件，確認一下有哪些參數就能上工囉。