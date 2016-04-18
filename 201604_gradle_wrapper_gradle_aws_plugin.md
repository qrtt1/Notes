# 實作 gradle-aws-plugin Lambda Wrapper

在 [包裝 Gradle Plugin 的 Plugin](201604_gradle_plugin_wrapper.md) 文章中，我們提出一個『想像』中的 DSL 規劃，僅針對 Amazon Lambda Update 的功能：

```groovy
aws { ... }
lambda {
    defaultConfig {
        bucketName = 'qty.lambda'
        key = 'defaultPackage.zip'
    }

    HelloLambda
    VideoPreviewTaskGenerator
    VideoPreviewGenerator {
        bucketName = 'foo.lambda'
        key = 'barPackage.zip'
    }
}
```

趁著週末有時間，試著來實作看看。首先遇到的問題是 `lambda` 已經在 [gradle-aws-plugin](https://github.com/classmethod/gradle-aws-plugin) 被註冊為 Extension，所以我們無法重新註冊同樣名字的 Extension（除非考慮非 Wrapper Plugin 的實作方式，不引用原先的 Plugin）。
另外，為了重新思考了是不是讓 Lambda Function 覆寫預設設定呢？像是：

```groovy
VideoPreviewGenerator {
    bucketName = 'foo.lambda'
    key = 'barPackage.zip'
}
```

以自己的經驗來說多數的情況同一個專案只會產生一個 zip 檔，我們可以暫時不考慮要覆寫預設設定的問題，那麼 DSL 可以簡化並將 `lambda{}` 改為不衝名的 `lambdaConfig` 為：

```groovy
aws { ... }
lambdaConfig {
    source {
        bucketName = 'qty.lambda'
        key = 'defaultPackage.zip'
        // or ..
        file = 'build/distributions/defaultPackage.zip'
    }

	function {
		HelloLambda
	    VideoPreviewTaskGenerator
	    VideoPreviewGenerator
	}

}
```

其中 `aws {}` 是原先 [gradle-aws-plugin](https://github.com/classmethod/gradle-aws-plugin) 提供的，讓我們填些 API 證認資訊與 Region。在這組 Extension 內，我們能利用：

1. `source {}` 指定檔案來源是使用 S3 上的檔案，或專案打包好的檔案
1. `function {}` 利用 Gradle 動態容器能建立出隨意的元素

## 建構 `lambdaConfig` Extension

```groovy
class LambdaConfigExtension {

    private Project project;
    private SourceBlock source = new SourceBlock();
    private NamedDomainObjectContainer<LambdaFunction> function;

    public LambdaConfigExtension(Project project) {
        this.project = project;
        this.function = project.container(LambdaFunction.class, { name -> new LambdaFunction(name) });
    }

    public Project getProject() {
        return project;
    }

    public void setProject(Project project) {
        this.project = project;
    }

    public SourceBlock getSource() {
        return source;
    }

    public void setSource(SourceBlock source) {
        this.source = source;
    }

    public void source(Closure<Void> configure){
        configure.setDelegate(source)
        configure.call(configure)
    }
    
    NamedDomainObjectContainer<LambdaFunction> getFunction() {
        return function;
    }

    def function(Action<? super NamedDomainObjectContainer<LambdaFunction>> action) {
        action.execute(function);
    }
}
```

在上面的程式，關於 Extension 內動態容器的實作在 [Android Plugin 的 productFlavors](201604_gradle_android_plugin_nameddomaincontainer.md) 已經討論過了，所以下面的寫法即為讓 `function{}` 能動態增刪容器的部分：

```groovy
NamedDomainObjectContainer<LambdaFunction> getFunction() {
    return function;
}

def function(Action<? super NamedDomainObjectContainer<LambdaFunction>> action) {
    action.execute(function);
}
``` 

而容器本身是這樣建立出來的：

```groovy
this.function = project.container(LambdaFunction.class, { name -> new LambdaFunction(name) });
```

另外，在 `source {}` 的部分，除了物件本身的 getter/setter 特別加一組接受 Closure 的 `source(...)` 讓它能接受 `{}` 作為參數：

```groovy
public void source(Closure<Void> configure){
    configure.setDelegate(source)
    configure.call(configure)
}
```

## 產生 Update Functions

相關的程式請參閱 [generate no-ops lambda-updater functions](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/1b500fcb13351d2ddd5c4eba7c35e2f8c902a955)。

我們利用 RuleSource 來建立相關 Task，相關資料參考 [Chapter 67. Rule based model configuration](https://docs.gradle.org/2.12/userguide/software_model.html) 與 Gradle Source Code：

```groovy
class AwsWrapperRule extends RuleSource {

    @Model
    public LambdaConfigExtension lambdaConfig(ExtensionContainer container) {
        return container.getByType(LambdaConfigExtension.class)
    }

    @Mutate
    public void generateUpdateTask(ModelMap<Task> tasks, LambdaConfigExtension extension) {
        extension.function.each { function -> 
            tasks.create("updateLambdaFunction${function.name}", {
                group = "Amazon Lambda Updater tasks"
                description = "update Lambda Function [${function.name}]"
                doLast {
                    println "do nothing function ${function.name}"
                }
            })
        }
    }
}
```

為了讓 Model Space 能運用到 LambdaConfigExtension 的資料，我們先建立一條 creation rule，透過 ExtensionContainer 將 LambdaConfigExtension 的 instance 轉為 Model：

```groovy
@Model
public LambdaConfigExtension lambdaConfig(ExtensionContainer container) {
    return container.getByType(LambdaConfigExtension.class)
}
```

一旦在 Model Space 有了 LambdaConfigExtension 的 instance 後，我們就能針對它修改或產生新的物件，例如用它來修改 `ModelMap<Task>`：

```groovy
@Mutate
public void generateUpdateTask(ModelMap<Task> tasks, LambdaConfigExtension extension) {
    extension.function.each { function -> 
        tasks.create("updateLambdaFunction${function.name}", {
            group = "Amazon Lambda Updater tasks"
            description = "update Lambda Function [${function.name}]"
            doLast {
                println "do nothing function ${function.name}"
            }
        })
    }
}
```

在 `generateUpdateTask(...)` 內，透過 LambdaConfigExtension 的內容產生若干個 lambda update task，實作的部分後續再補上。到目前為止我們有了基本的 DSL 與自動產生的 Task。


## lambdaConfig 語法驗證

語法驗證能透過 `@Validate` Rule 達成，相關的程式碼請參閱：

* [validate source block settings](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/534a6b635a1dab2645c4a47deedc7bf759a5c091)
* [validate the s3 source settings](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/0fb30200245fe60b9cd3661e3e6903d4d8aa909f)
* [validate local file source settings](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/99ddd3c3b39c9e02f6c5acac577bce86eafc3f9f)


### 基本 null 檢查

在 RuleSource 內的 method 只要標上 `@Validate` 就會進行驗證，在初步的實作中，簡單地做一些 null 值檢查：

```
@Validate
public void validateSourceBlock(LambdaConfigExtension extension){
    SourceBlock source = extension.source;
    Preconditions.checkState(source != null, "lambdaConfig.source{} cannot be null.")
    
    if(source.file != null) {
        Preconditions.checkState(source.bucketName == null && source.key == null, 
            "lambdaConfig.source{} should be one of the (file, bucketName with key)")
    }
}
```

### local file 或 s3 檢查

有基本檢查後，我們能分為 2 組：

1. 有 file 時，s3 設定應為空的
1. 有 s3 設定時，它的 bucketName 與 key 都不能是空的

```groovy
@Validate
public void validateSourceBlock(LambdaConfigExtension extension){
    SourceBlock source = extension.source;
    Preconditions.checkState(source != null, "lambdaConfig.source{} cannot be null.")

    if(source.file != null) {
        Preconditions.checkState(source.bucketName == null && source.key == null,
                "lambdaConfig.source{} should be one of the (file, bucketName with key)")
    } else {
        Preconditions.checkState(source.bucketName != null,
                "lambdaConfig.source{} property bucketName cannot be null ")
        Preconditions.checkState(source.key != null,
                "lambdaConfig.source{} property key cannot be null ")
    }
}
```

### local file 存在檢查

```groovy
@Validate
public void validateSourceBlock(LambdaConfigExtension extension){
    SourceBlock source = extension.source;
    Preconditions.checkState(source != null, "lambdaConfig.source{} cannot be null.")

    if(source.file != null) {
		/* ...(略)... */
		
		File path = new File(source.file).getAbsoluteFile()
        Preconditions.checkState(path.exists(),
            "lambdaConfig.source{} file not found: " + path)
        
    } else {
		/* ...(略)... */
    }
}

```


## 完成 update task 實作

* [finish the update-tasks](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/c199e0fb1e108353aa26158e76250dac1ecfffe1)
* [introduce BeforeLambdaUpdateTask and fix typo for the update task](https://github.com/qrtt1/AwsWrapperGradlePlugin/commit/e7ee07a196fcac4b4c8d7024ddde90a96a8e4b81)

update task 的實作沒有太特別之處，只是單純滿足 `AWSLambdaUpdateFunctionCodeTask` 的要求：

```groovy
@Mutate
public void generateUpdateTask(ModelMap<Task> tasks, LambdaConfigExtension extension) {
    SourceBlock source = extension.source;
    
    extension.function.each { function -> 
        tasks.create("updateLambdaFunction${function.name}", AWSLambdaUpdateFunctionCodeTask.class, {
            group = AwsWrapperPlugin.GROUP
            description = "update Lambda Function [${function.name}]"
            dependsOn = [BeforeLambdaUpdateTask.NAME]
            
            if(source.file != null) {
                zipFile = new File(source.file)
            } else {
                s3File = new S3File()
                s3File.bucketName = source.bucketName
                s3File.key = source.key
            }
            
            functionName = function.name
        })
    }

    tasks.create("updateAllLambdaFunctions", {
        group = AwsWrapperPlugin.GROUP
        description = "update All Lambda Functions"
        dependsOn = extension.function.collect { function -> "updateLambdaFunction${function.name}" }
    })
}
```

除了 update task 本身，我們額外提供：

1. beforeLambdaUpdate task
1. updateAllLambdaFunctions task

`updateAllLambdaFunctions` 的內容很簡單，單純相依所有的 `updateLambdaFunction*` task，就是它會呼叫每一個 update task。而 [beforeLambdaUpdate](https://github.com/qrtt1/AwsWrapperGradlePlugin/blob/e7ee07a196fcac4b4c8d7024ddde90a96a8e4b81/src/main/groovy/org/qty/aws/wrapper/lambda/BeforeLambdaUpdateTask.java) 實際上是一個空白實作：

```java
public class BeforeLambdaUpdateTask extends DefaultTask {
    
    public final static String NAME = "beforeLambdaUpdate";

    public BeforeLambdaUpdateTask() {
        setGroup(AwsWrapperPlugin.GROUP);
    }

    @TaskAction
    public void action() {

    }

}
```

它的功能單純是被 `updateLambdaFunction*` task 相依，這樣也預留使用上的彈性，例如我們能在 `build.gradle` 這麼寫：

```groovy

task buildZip(type: Zip, dependsOn: build) {
    from compileJava
    from processResources
    into('lib') {
        from configurations.runtime
    }
    eachFile {
        if (it.name.contains(".so.")) fileMode 0755
        if (it.name.contains("ffprobe")) fileMode 0755
        if (it.name.contains("ffmpeg")) fileMode 0755
    }
}

beforeLambdaUpdate {
    dependsOn = [buildZip]
}
```

這樣在進行 update 動作前，會先相依於 `buildZip`。這樣的設計能應付各種不同類型專案的打包需求。

## 參考專案

1. [AwsWrapperGradlePlugin](https://github.com/qrtt1/AwsWrapperGradlePlugin) 本篇文章所描述的 plugin 實作專案的原始碼
1. [TWJUG20150801](https://github.com/qrtt1/TWJUG20150801) 先前在 TWJUG 介紹 AWS Lambda 的專案，在 branch [using-wrapper-plugin](https://github.com/qrtt1/TWJUG20150801/tree/using-wrapper-plugin) 即使用本文介紹的 wrapper plugin 實作