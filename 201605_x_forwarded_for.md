# X-Forwarded-For On Cloud

當使用雲端服務時，常要搭配 Load Balancer 的使用，當在 Servlet 內呼叫：

```java
request.getRemoteAddr();
```

我們不一定會取得真實的 Client IP，不過還好有 HTTP Header 的 `X-Forwarded-For` 可以查詢，但最近觀察到一個現象，那就是那個欄位可能會回傳多個 IP。


## GCE

在 GCE 的 [load balancing 文件](https://cloud.google.com/compute/docs/load-balancing/http/) 提到

>> X-Forwarded-For: <client IP(s)>, <global forwarding rule external IP>

>> The `first` element in the <client IP(s)> section shows the `origin address`.

不過為什麼會多數其他的 client IP*s* 卻沒特別說明什麼。

## AWS

在 [ELB 的文件](http://docs.aws.amazon.com/ElasticLoadBalancing/latest/DeveloperGuide/x-forwarded-headers.html#x-forwarded-for) 提到的是：

>> X-Forwarded-For: OriginatingClientIPAddress, proxy1-IPAddress, proxy2-IPAddress

看規則與 GCE 一樣第 1 個是原始 IP，後面的則是經過的 proxy 的 IP。
