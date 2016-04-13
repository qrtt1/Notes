# Android Plugin 的 productFlavors

當我們引用一些 Plugin 時，會發現它有一些有趣的 DSL 用法，像是能動態新增設定的。以 Android Plugin 為例，它提供 [Product flavors](http://tools.android.com/tech-docs/new-build-system/user-guide#TOC-Product-flavors) 的功能，讓開發者客製化最終結果的產出：

```groovy
android {
    ....


    productFlavors {
        flavor1 {
            ...
        }


        flavor2 {
            ...
        }
    }
}
```

寫在 `productFlavors{}` block 內的 `flavor1` 與 `flavor2` 是動態新增的，而其中的 `flavor*{}` block 是個 Closure 它會接受 [ProductFlavor](https://android.googlesource.com/platform/tools/base/+/tools_r22.6/build-system/builder-model/src/main/java/com/android/builder/model/ProductFlavor.java) 作為參數傳入，因此在裡面的 property access 都是針對當下的 ProductFlavor 物件的操作。那麼 `productFlavors` block 實際是何種類別，允許我們能在 Gradle DSL 內動態增加新的物件又能透過 Closure 設定它的內容呢？


## productFlavors

要探索 productFlavors 為何物有二個直覺的選擇：

1. Android Plugin 是有原始碼的，我們能直接看它的原始碼
1. Gradle Build Script 實際上是 Groovy Script，在 Groovy 的世界觀裡它就是個物件罷了

這二個方向是可以相互印證的，那麼可以先由簡單地來！在 Android 專案裡 app 的 build.gradle 試著把它印出來：

```
println android.productFlavors.class
```

能觀察到它是來 [org.gradle.api.internal.FactoryNamedDomainObjectContainer](https://github.com/gradle/gradle/blob/REL_2.12/subprojects/core/src/main/groovy/org/gradle/api/internal/FactoryNamedDomainObjectContainer.java)：

```
qty:app qrtt1$ ../gradlew
class org.gradle.api.internal.FactoryNamedDomainObjectContainer_Decorated
```


另一方面我們能由 source code 裡找到解答，由於它是被包在 `android {}` block 內的，我們能期待在 Android Plugin 內有建立一個 Extension 名稱為 `android`。在 [BasePlugin.createExtension()](https://android.googlesource.com/platform/tools/base/+/master/build-system/gradle/src/main/groovy/com/android/build/gradle/BasePlugin.java#412) 能看到下列實作：

```java
private void createExtension() {
    final NamedDomainObjectContainer<BuildType> buildTypeContainer = project.container(
            BuildType.class,
            new BuildTypeFactory(instantiator, project, project.getLogger()));
    final NamedDomainObjectContainer<ProductFlavor> productFlavorContainer = project.container(
            ProductFlavor.class,
            new ProductFlavorFactory(instantiator, project, project.getLogger()));
    final NamedDomainObjectContainer<SigningConfig>  signingConfigContainer = project.container(
            SigningConfig.class,
            new SigningConfigFactory(instantiator));

    extension = project.getExtensions().create("android", getExtensionClass(),
            project, instantiator, androidBuilder, sdkHandler,
            buildTypeContainer, productFlavorContainer, signingConfigContainer,
            extraModelInfo, isLibrary());

    //  ....(skip)....
}
```

在這實作裡可以看到 `android {}` block 被建立出來，目前它實際的 extension class 未知（由 subclass 提供），在它之後的是 extension class 的建構子參數。同時我們也看到『可疑』的 productFlavorContainer，它八成是我們想要找到 `productFlavors{}` block，但得由 extension class 的實作來驗證。

以 [AppPlugin.getExtensionClass()](https://android.googlesource.com/platform/tools/base/+/master/build-system/gradle/src/main/groovy/com/android/build/gradle/AppPlugin.groovy#43) 來說，它回傳的是 [AppExtension](https://android.googlesource.com/platform/tools/base/+/master/build-system/gradle/src/main/groovy/com/android/build/gradle/AppExtension.java)，繼續追下去會發現它繼承自 TestedExtension，而 TestedExtension 又繼承自 [BaseExtension](https://android.googlesource.com/platform/tools/base/+/master/build-system/gradle/src/main/groovy/com/android/build/gradle/BaseExtension.java)。


繼續看 source code 之前，我們回頭看一下 Android Plugin 設計的 DSL 的寫法，對應至 Groovy 的意義，例如：

```groovy
android {
    productFlavors
}
```

以上寫法，它不是 method call 的語法，所以會是 property access，其實是對某個 Groovy Object `android` 呼叫 getProductFlavors() 的動作，再換一個寫法：

```groovy
android {
    productFlavors {}
}
```

加了 `{}` Closure，那麼它會被解讀為對某個 Groovy Object `android` 呼叫 `productFlavors(Closure c)` 的動作。因此能期待在 Extension Class 內可能會有：

* def getProductFlavors()
* def productFlavors(Closure c)

在 source code 確實看到了：

```groovy
/** {@inheritDoc} */
@Override
public Collection<? extends CoreProductFlavor> getProductFlavors() {
    return productFlavors;
}
```

與：

```groovy
/**
 * Configures the product flavors.
 */
public void productFlavors(Action<? super NamedDomainObjectContainer<CoreProductFlavor>> action) {
    checkWritability();
    action.execute(productFlavors);
}
```

特別看一下 `productFlavors(...)` 方法的參數跟期望有點不同，但已經接近了 `FactoryNamedDomainObjectContainer`。在一些我們還沒注意到的地方，Gradle 做了一些轉換，讓原本的 Closure 變為 `Action<? super NamedDomainObjectContainer<CoreProductFlavor>> action` 傳了進來。


## Closure to Action

單純使用『眼睛』的靜態方析已經到極限，特別是充滿黑魔法的 Gradle 來說，難以簡單地看透它。小結一下目前的發現：

1. `productFlavors {}` 是使用 `project.container(...)` 建立出來的 `FactoryNamedDomainObjectContainer`
1. `productFlavors {}` 的 `{}` Closure 似乎被轉換成 `Action<? super NamedDomainObjectContainer<CoreProductFlavor>> action`

那麼我們得設法找出，它真的被轉換成 Action 的地方。靜態觀察追蹤的手法太沒效率時，試著動態一點的方式唄，例如加工一下 Gradle Script：

```
android.productFlavors {
    foo {
        for (StackTraceElement e : Thread.currentThread().getStackTrace()) {
            System.out.println(e);
        }
    }
}
```

```
qty:app qrtt1$ ../gradlew
java.lang.Thread.getStackTrace(Thread.java:1552)
java_lang_Thread$getStackTrace$0.call(Unknown Source)
org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:45)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:108)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:112)
build_25ay3wowy4sjizjdkr9wls4yt$_run_closure3_closure7.doCall(/Users/qrtt1/temp/MyApplication/app/build.gradle:35)
sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
java.lang.reflect.Method.invoke(Method.java:497)
org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:90)
groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:324)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:292)
groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1015)
groovy.lang.Closure.call(Closure.java:423)
groovy.lang.Closure.call(Closure.java:439)
org.gradle.api.internal.ClosureBackedAction.execute(ClosureBackedAction.java:67)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:59)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:52)
org.gradle.api.internal.NamedDomainObjectContainerConfigureDelegate._configure(NamedDomainObjectContainerConfigureDelegate.java:39)
org.gradle.api.internal.ConfigureDelegate.invokeMethod(ConfigureDelegate.java:73)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeOnDelegationObjects(ClosureMetaClass.java:428)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:369)
groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1015)
org.codehaus.groovy.runtime.callsite.PogoMetaClassSite.callCurrent(PogoMetaClassSite.java:66)
org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCallCurrent(CallSiteArray.java:49)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.callCurrent(AbstractCallSite.java:133)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.callCurrent(AbstractCallSite.java:141)
build_25ay3wowy4sjizjdkr9wls4yt$_run_closure3.doCall(/Users/qrtt1/temp/MyApplication/app/build.gradle:34)
sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
java.lang.reflect.Method.invoke(Method.java:497)
org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:90)
groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:324)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:292)
groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1015)
groovy.lang.Closure.call(Closure.java:423)
groovy.lang.Closure.call(Closure.java:439)
org.gradle.api.internal.ClosureBackedAction.execute(ClosureBackedAction.java:67)
org.gradle.util.ConfigureUtil.configure(ConfigureUtil.java:130)
org.gradle.util.ConfigureUtil.configure(ConfigureUtil.java:91)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.configure(AbstractNamedDomainObjectContainer.java:68)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.configure(AbstractNamedDomainObjectContainer.java:24)
org.gradle.api.internal.ClosureBackedAction.execute(ClosureBackedAction.java:59)
org.gradle.api.Action$execute.call(Unknown Source)
org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:45)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:108)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:116)
com.android.build.gradle.BaseExtension.productFlavors(BaseExtension.groovy:335)
com.android.build.gradle.AppExtension_Decorated.productFlavors(Unknown Source)
com.android.build.gradle.AppExtension_Decorated$productFlavors$0.call(Unknown Source)
org.codehaus.groovy.runtime.callsite.CallSiteArray.defaultCall(CallSiteArray.java:45)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:108)
org.codehaus.groovy.runtime.callsite.AbstractCallSite.call(AbstractCallSite.java:116)
build_25ay3wowy4sjizjdkr9wls4yt.run(/Users/qrtt1/temp/MyApplication/app/build.gradle:33)
org.gradle.groovy.scripts.internal.DefaultScriptRunnerFactory$ScriptRunnerImpl.run(DefaultScriptRunnerFactory.java:74)
org.gradle.configuration.DefaultScriptPluginFactory$ScriptPluginImpl$1.run(DefaultScriptPluginFactory.java:148)
org.gradle.configuration.DefaultScriptPluginFactory$ScriptPluginImpl.apply(DefaultScriptPluginFactory.java:156)
org.gradle.configuration.project.BuildScriptProcessor.execute(BuildScriptProcessor.java:39)
org.gradle.configuration.project.BuildScriptProcessor.execute(BuildScriptProcessor.java:26)
org.gradle.configuration.project.ConfigureActionsProjectEvaluator.evaluate(ConfigureActionsProjectEvaluator.java:34)
org.gradle.configuration.project.LifecycleProjectEvaluator.evaluate(LifecycleProjectEvaluator.java:55)
org.gradle.api.internal.project.AbstractProject.evaluate(AbstractProject.java:487)
org.gradle.api.internal.project.AbstractProject.evaluate(AbstractProject.java:85)
org.gradle.execution.TaskPathProjectEvaluator.configureHierarchy(TaskPathProjectEvaluator.java:47)
org.gradle.configuration.DefaultBuildConfigurer.configure(DefaultBuildConfigurer.java:35)
org.gradle.initialization.DefaultGradleLauncher.doBuildStages(DefaultGradleLauncher.java:129)
org.gradle.initialization.DefaultGradleLauncher.doBuild(DefaultGradleLauncher.java:106)
org.gradle.initialization.DefaultGradleLauncher.run(DefaultGradleLauncher.java:86)
org.gradle.launcher.exec.InProcessBuildActionExecuter$DefaultBuildController.run(InProcessBuildActionExecuter.java:90)
org.gradle.tooling.internal.provider.ExecuteBuildActionRunner.run(ExecuteBuildActionRunner.java:28)
org.gradle.launcher.exec.ChainingBuildActionRunner.run(ChainingBuildActionRunner.java:35)
org.gradle.launcher.exec.InProcessBuildActionExecuter.execute(InProcessBuildActionExecuter.java:41)
org.gradle.launcher.exec.InProcessBuildActionExecuter.execute(InProcessBuildActionExecuter.java:28)
org.gradle.launcher.exec.DaemonUsageSuggestingBuildActionExecuter.execute(DaemonUsageSuggestingBuildActionExecuter.java:50)
org.gradle.launcher.exec.DaemonUsageSuggestingBuildActionExecuter.execute(DaemonUsageSuggestingBuildActionExecuter.java:27)
org.gradle.launcher.cli.RunBuildAction.run(RunBuildAction.java:40)
org.gradle.internal.Actions$RunnableActionAdapter.execute(Actions.java:169)
org.gradle.launcher.cli.CommandLineActionFactory$ParseAndBuildAction.execute(CommandLineActionFactory.java:237)
org.gradle.launcher.cli.CommandLineActionFactory$ParseAndBuildAction.execute(CommandLineActionFactory.java:210)
org.gradle.launcher.cli.JavaRuntimeValidationAction.execute(JavaRuntimeValidationAction.java:35)
org.gradle.launcher.cli.JavaRuntimeValidationAction.execute(JavaRuntimeValidationAction.java:24)
org.gradle.launcher.cli.CommandLineActionFactory$WithLogging.execute(CommandLineActionFactory.java:206)
org.gradle.launcher.cli.CommandLineActionFactory$WithLogging.execute(CommandLineActionFactory.java:169)
org.gradle.launcher.cli.ExceptionReportingAction.execute(ExceptionReportingAction.java:33)
org.gradle.launcher.cli.ExceptionReportingAction.execute(ExceptionReportingAction.java:22)
org.gradle.launcher.Main.doAction(Main.java:33)
org.gradle.launcher.bootstrap.EntryPoint.run(EntryPoint.java:45)
sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
java.lang.reflect.Method.invoke(Method.java:497)
org.gradle.launcher.bootstrap.ProcessBootstrap.runNoExit(ProcessBootstrap.java:54)
org.gradle.launcher.bootstrap.ProcessBootstrap.run(ProcessBootstrap.java:35)
org.gradle.launcher.GradleMain.main(GradleMain.java:23)
sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
java.lang.reflect.Method.invoke(Method.java:497)
org.gradle.wrapper.BootstrapMainStarter.start(BootstrapMainStarter.java:33)
org.gradle.wrapper.WrapperExecutor.execute(WrapperExecutor.java:130)
org.gradle.wrapper.GradleWrapperMain.main(GradleWrapperMain.java:48)
:app:help
```

看到這長長的 stacktraces 先別嚇傻了，回頭理解一下目標：

1. productFlavors 可以動態增加元素，但 stacktraces 沒看到 FactoryNamedDomainObjectContainer，也許被被表示成某個父類別了
1. Closure 會被轉成 Action，可在 stacktraces 找到與 Action 相關的類別

由這些線索來縮小一下 stacktrace 範圍：

```
qty:app qrtt1$ ../gradlew
...
groovy.lang.Closure.call(Closure.java:423)
groovy.lang.Closure.call(Closure.java:439)
org.gradle.api.internal.ClosureBackedAction.execute(ClosureBackedAction.java:67)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:59)
org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:52)
org.gradle.api.internal.NamedDomainObjectContainerConfigureDelegate._configure(NamedDomainObjectContainerConfigureDelegate.java:39)
org.gradle.api.internal.ConfigureDelegate.invokeMethod(ConfigureDelegate.java:73)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeOnDelegationObjects(ClosureMetaClass.java:428)
org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:369)
...
build_25ay3wowy4sjizjdkr9wls4yt$_run_closure3.doCall(/Users/qrtt1/temp/MyApplication/app/build.gradle:34)
```

1. FactoryNamedDomainObjectContainer 似乎就成了 AbstractNamedDomainObjectContainer
1. `AbstractNamedDomainObjectContainer.create(...)` 後會呼叫 `ClosureBackedAction.execute(...)`

試著在 Gradle 原始碼內找到同一版的 [AbstractNamedDomainObjectContainer.create(...)](https://github.com/gradle/gradle/blob/e130fefc03efa3ad8e578bd83bbecfcaaf6b2a61/subprojects/core/src/main/groovy/org/gradle/api/internal/AbstractNamedDomainObjectContainer.java#L51)：

```
public T create(String name, Closure configureClosure) {
// org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:52)
    return create(name, new ClosureBackedAction<T>(configureClosure));
}

public T create(String name, Action<? super T> configureAction) throws InvalidUserDataException {
    assertCanAdd(name);
    T object = doCreate(name);
    add(object);
// org.gradle.api.internal.AbstractNamedDomainObjectContainer.create(AbstractNamedDomainObjectContainer.java:59)    
    configureAction.execute(object);
    return object;
}
```

將原始碼對上 stacktraces 就說得通了，一開始確實是 Closure 只是它被包進 ClosureBackedAction 內再傳遞了一次。 


## AbstractNamedDomainObjectContainer

由先前的 trace 能知道 `productFlavors{}` block 在執行期是 AbstractNamedDomainObjectContainer，那麼它應該與動態建立內部元素的功能較為相關，特別它的名稱含有 **Container** 似乎挺接近案答的。

繼續追蹤它的繼承關係會看到 [NamedDomainObjectCollection](https://docs.gradle.org/current/dsl/org.gradle.api.NamedDomainObjectCollection.html)，要放進這 Collection 的元素需要有 `name` property，那麼使用此容器的 Closure 時，會自動建出新的元素。

```groovy
android {
    productFlavors {
        flavor1 {}
    }
}
```

再追入實作類別 [DefaultNamedDomainObjectCollection](https://github.com/gradle/gradle/blob/REL_2.12/subprojects/core/src/main/groovy/org/gradle/api/internal/DefaultNamedDomainObjectCollection.java#L339)，可以看到在 `flavor1 {}` 部分以 Groovy 的角度看它是個 method invoke，透過 MetaObjectProtocol 攔截 invokeMethod 時，代換為 `getByName()` 取得實際的 ProductFlavor。 


## NamedDomainObjectCollection 實作模式

經過上述的原始碼閱讀後，能簡單規納出經驗：

1. 使用 `project.container(...)` 建出 NamedDomainObjectCollection 讓 DSL block 有動態增加元素的能力
1. 在 extension 需支援 getXXXXContainer() 與 XXXXContinaer(Action) 二種方法
1. XXXXContainer 內的元素類別，需有 `name` property

以下簡單寫個 `build.gradle` 展示一下用法：

```groovy
class Bar {
    def name
    def value
}

class FooExtension {

    def bars;

    FooExtension(Project project) {
        bars = project.container(Bar.class, {name -> def bar = new Bar(); bar.name = name; bar })
    }

    NamedDomainObjectContainer<Bar> getBars() {
        return bars;
    }

    def bars(Action<? super NamedDomainObjectContainer<Bar>> action) {
        action.execute(bars);
    }

}

project.extensions.create('foo', FooExtension.class, project)

foo {
    bars {
        first {
            value = "1st value"
        }
        second {
            value = "2nd value"
        }
    }
}
```


