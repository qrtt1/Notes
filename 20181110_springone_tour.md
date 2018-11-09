《CLoud Native Java - Josh Long》

Josh 不仅介绍了云原生 Java，同时深入介绍了 Spring Cloud 对现代微服务开发的支持，重点关注真正重要的功能以及我们已经着手在 Spring Boot 2.0 和 Spring Cloud Finchley 中实现的功能。

投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Josh.pdf
演講影片：https://v.qq.com/x/page/k0782bocg8j.html


* Cloud Native Java
  * {06:50 ~ 12:10} 使用 start.spring.io 建立 reservation 專案，相關功能如下： 
    * Reactive Cloud Stream
    * Lombok
    * Reactive Web
    * Actuator
  * {06:50 ~ 12:10} Reactive Spring Data API 
    * 使用經典的 Reservation 範例來示範
    * 相關教學文件 Going reactive with Spring Data 
  * {15:20 ~ 17:00} 建立 endpoint 接受 client 端的 request 
    * 相關教學文件 New in Spring 5: Functional Web Framework https://spring.io/blog/2016/09/22/new-in-spring-5-functional-web-framework
  * {17:10 ~} 建立一個新的 Spring Boot 專案，當作 Reservation Service 的 Client
    * 使用 start.spring.io 建立 reservation-client 專案，相關功能如下
      * Lombok
      * Reactive Web
      * Hystrix
      * Gateway
      * Security
      * Reactive Redis 
    * {18:10} Spring Cloud Gateway 
      * RouteLocatorBuilder
      * RouteSpec
        * {21:38} CORS 設定
        * {22:20} rate limiter
          * {22:37} RedisRateLimiter
      * Spring Security
        * {24:00} authentication
          * MapReactiveUserDetailsService
        * {24:50} authorization
          * SecurityWebFilterChain
    * {27:00} API Adapter
      * RouterFunction
      * {30:00} HystrixCommands
    * {35:00} 改用 rsocket 作為 service 間的通訊協定
      * 這是一個 demo preview Spring 5.x 的功能
      * 利用 jackson ObjectMapper 進行 json 與 java object 間的轉換


《Spring and Pivotal Application Service - Li Gang》
我们介绍了什么让Spring Boot、Spring Cloud和Spring Cloud Data Flow工作负载非常适合在Cloud Foundry上运行。

投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Li.pdf

《Knative, Riff and Serverless - Liu Fan》
我们分享了一系列概念术语“服务”—基础架构即服务、容器即服务、平台即服务、软件即服务… 为您掌握 FaaS 大局打下坚实基础。

投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Liu.pdf

《Full Stack Reactive Java - Mark Heckler》
在这个演讲中，我们介绍了新的基于Netty的万维网运行环境；如何在此新环境中运行Servlet代码，以及如何将其与现有的Spring堆栈技术融合。

投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Mark.pdf

《BJ-K8s+Spinnaker - Paul Czarkowski》
介绍容器和Kubernetes以及它支持的默认开发/部署工作流。然后他将展示如何使用Spinnaker来简化和精简工作流，帮助提供一个完全#gitops风格的CI/CD

投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Paul.pdf

《Spring Cloud Gateway - Spencer Gibb》
我们演示了首个新一代API Gateway：Spring Cloud Gateway以及它的架构和开发人员体验。帮助您了解路由匹配和筛选，以及与Zuul 1体验的不同之处。
投影片：http://icampaign.com.cn/pivotal/SpringOne_Tour/Spencer.pdf