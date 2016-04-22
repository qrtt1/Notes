# Gradle 整合測試

在開發 [AwsWrapperGradlePlugin](https://github.com/qrtt1/AwsWrapperGradlePlugin) 的過程中，多數的時間都花理解『實作』與目標 DSL『語法』的正確性上。一開始覺得不會花太多時間在實作 DSL 上，往往都是在將 plugin 安裝至 local 的 maven repo 讓另一個專案使用後才發現『現實與理想的差距』。

在近期幾版的 Gradle （註：開發時使用的是 2.12 版）開發支援 `maven-publish` plugin，透過簡單地設定我們能將專案發佈至 maven repo，在沒有特別的設定的情況下至少能發佈至 local maven repo：

```groovy
apply plugin: "maven-publish"

publishing {
    publications {
        mavenJava(MavenPublication) {
            groupId = 'org.qty.gradle.aws.lambda'
            artifactId = 'lambda.wrapper.plugin'
            version = "$VERSION-SNAPSHOT"
            from components.java
        }
    }
}
```

在最初，我是在開發 plugin 的專案手動執行 `publishToMavenLocal` task，讓專案被安裝至 local maven repo 上，然後在另一個專案宣告要引用 local maven repo 並 apply 此 plugin，再手動呼叫 `gradle tasks` 確認 DSL 都有正常運作。這樣的開發方式實在太『原始』也無法輕鬆達成不同情境的測試，即便仍只是做一樣的事情，單純由『手動』變『自動』也會讓開發的舒適感翻了好幾倍。

## TestKit

由於近期加了許多 incubating 的 API 或新功能，還沒重新看手冊。上論壇只能找到很久遠的討論，在挫折的手動測試後，休息時翻翻 Gradle 手冊的目錄，發現了重要的新功能 [Gradle TestKit](https://docs.gradle.org/2.12/userguide/test_kit.html)，只要加個相依性的宣告與相關的 test library：

```groovy
dependencies {
    testCompile gradleTestKit()
}
```

就能夠使用 [GradleRunner](https://docs.gradle.org/2.12/javadoc/org/gradle/testkit/runner/GradleRunner.html) 進行整合測試，下面的範例取自官方手冊搭配 Spock 的測試：

```java
import org.gradle.testkit.runner.GradleRunner
import static org.gradle.testkit.runner.TaskOutcome.*
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import spock.lang.Specification

class BuildLogicFunctionalTest extends Specification {
    @Rule final TemporaryFolder testProjectDir = new TemporaryFolder()
    File buildFile

    def setup() {
        buildFile = testProjectDir.newFile('build.gradle')
    }

    def "hello world task prints hello world"() {
        given:
        buildFile << """
            task helloWorld {
                doLast {
                    println 'Hello world!'
                }
            }
        """

        when:
        def result = GradleRunner.create()
            .withProjectDir(testProjectDir.root)
            .withArguments('helloWorld')
            .build()

        then:
        result.output.contains('Hello world!')
        result.task(":helloWorld").outcome == SUCCESS
    }
}
```

不過事情沒那麼單純，因為它的測試範例只含有 Gradle 內建的功能，我們得加工一下，讓測試案例裡的 `build.gradle` 能認得正在開發中的 plugin！

在 **43.2.1. Getting the code under test into the test build** 小節中，它描述了如何列出相依的 classpath 路徑並透過 [GradleRunner.withPluginClasspath()](https://docs.gradle.org/2.12/javadoc/org/gradle/testkit/runner/GradleRunner.html#withPluginClasspath(java.lang.Iterable)) 將 plugin 的 classpath 餵給 GradleRunner。他還貼心地提供了 1 個用來產生 classpath 資訊的 task：

```groovy
// Write the plugin's classpath to a file to share with the tests
task createClasspathManifest {
    def outputDir = file("$buildDir/$name")

    inputs.files sourceSets.main.runtimeClasspath
    outputs.dir outputDir

    doLast {
        outputDir.mkdirs()
        file("$outputDir/plugin-classpath.txt").text = sourceSets.main.runtimeClasspath.join("\n")
    }
}

// Add the classpath file to the test runtime classpath
dependencies {
    testRuntime files(createClasspathManifest)
}
```

不過在使用上遇到了幾個不便之處：

1. `createClasspathManifest` 在 Eclipse 會被建立成 classpath，但它卻不是 JAR 是個 .txt
1. 無法輕易地與 Eclipse 的 JUnit Runner 整合，並將 plugin classpath 內容有變動時就得再呼叫此 task 才會更新
1. `./build/createClasspathManifest/plugin-classpath.txt` 產生的 output 目錄位置，並不是 IDE 的位置而是 Gradle 的位置，所以不會包含 plugin classes 與 `META-INF`

除了上述的問題之外，我另外 hardcode 了 plugin classpath 在 [GradleRunner.withPluginClasspath()](https://docs.gradle.org/2.12/javadoc/org/gradle/testkit/runner/GradleRunner.html#withPluginClasspath(java.lang.Iterable)) 內，但 `build.gradle` 依然找不到開發中的 plugin。

## 自訂 maven repo

由於 TestKit 還未到完全可用的地步，那只好另想辦法讓我們的測試能自動化些。原先手動的方案是將 plugin 安裝至 local maven repo 也就是在 `$HOME/.m2` 的位置，那麼針對測測的需求，我若能客制化這個位置讓測試開發的 maven repo 有所隔離即可，例如裝在專案的 `build/repo` 目錄，將原先的 `publishing` 稍為改寫加上新的 maven repo 位置：

```groovy
publishing {
    publications {
        mavenJava(MavenPublication) {
            groupId = 'org.qty.gradle.aws.lambda'
            artifactId = 'lambda.wrapper.plugin'
            version = "$VERSION-SNAPSHOT"
            from components.java
        }
    }
    repositories {
        maven {
            url "$buildDir/repo"
        }
    }
}
```

經過調整後，能使用 `*PublicationToMavenRepository` task 發目至新的位置：

```
gradle publishMavenJavaPublicationToMavenRepository
```

先前的範例可以看到 GradleRunner 能讓我們以物件操作的方式指定需要執行的 `build.gradle`，這麼方便的功能用來執行 `publishMavenJavaPublicationToMavenRepository` task 再適合不過了。

於是我實作一個 [PluginInstaller](https://github.com/qrtt1/AwsWrapperGradlePlugin/blob/5539bbf7501720a9ca2ee101f88322f4c8dbae32/src/test/groovy/org/qty/aws/wrapper/lambda/PluginInstaller.java) 執行 task 並記錄 `build/repo` 的絕對路徑，那麼我們寫 Test Case 時，就能產生對應的 repositories 設定：

```groovy
class AwsWrapperPluginTest extends Specification {

    @Rule final TemporaryFolder testProjectDir = new TemporaryFolder()
    File buildFile
    
    def setup() {
        PluginInstaller.install();
        buildFile = testProjectDir.newFile('build.gradle')
        String mavenLocation = PluginInstaller.developMaven;
        buildFile << """
            buildscript {
                repositories {
                    jcenter()
                }
                dependencies {
                    classpath 'com.amazonaws:aws-java-sdk-lambda:1.+'
                    classpath 'com.amazonaws:aws-java-sdk-s3:1.10.8'
                }
            
                repositories {
                    maven {
                        url "$mavenLocation"
                    }
                }
                dependencies {
                    classpath "org.qty.gradle.aws.lambda:lambda.wrapper.plugin:0.0.2-SNAPSHOT"
                }
            }
            apply plugin: "org.qty.aws.wrapper.lambda"
        """
    }
    // ...(略)...   
}
```

其中的 `mavenLocation` 變數即是來自於 PluginInstaller 記錄的絕對路徑，而 `repositories` 裡也用上了它：

```groovy
String mavenLocation = PluginInstaller.developMaven;
```

```groovy
repositories {
    maven {
        url "$mavenLocation"
    }
}
```

## Spock 體驗

Gradle 原始碼內部的測試絕大多數是使用 Spock 的，為了實作這個 plugin 也試著用它來測試，以下例子是簡單地測試 DSL 沒有壞掉，並且有生出對應的 task：

```groovy
def testLambdaConfigSyntax() {
    given:
        buildFile << """
            lambdaConfig {
                source {
                    bucketName = 'abc'
                    key = 'def.zip'
                }
                function {
                    Function1
                    Function2
                }
            }
        """

    when:
        def result = invokeGradle()
        
    then:
        result.task(":tasks").outcome == SUCCESS
        result.output.contains("updateLambdaFunctionFunction1")
        result.output.contains("updateLambdaFunctionFunction2")
}
```

在 `given` 部分，是安裝測試資料，我們簡單在 `setup` 後的 `build.gradle` 加上 DSL，而 `when` 的部分則是觸發執行邏輯之處，也就是利用 GradleRunner 跑這個 `build.gradle`。最後的 `then` 就是進行結果驗證，看起來相當直覺易懂。

## 摘要

運用 GradleRunner 配合自定的 maven repo 路徑將原先手動測試的窘境改善，即能透過 Eclipse 的 JUnit Runner 執行，也相容於 `gradle test` 任務。在 Gradle TestKits 還成為正式且完整的功能前，這會是目前最推薦的 Gradle 整合測試方案。

另外，關於本篇的說例都取自於 AwsWrapperPlugin 專案，完整的 Test Case 可參考 [AwsWrapperPluginTest.groovy](https://github.com/qrtt1/AwsWrapperGradlePlugin/blob/5539bbf7501720a9ca2ee101f88322f4c8dbae32/src/test/groovy/org/qty/aws/wrapper/lambda/AwsWrapperPluginTest.groovy)。
