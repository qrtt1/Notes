# Gradle 的 @Inject

讀 Gradle 的實作可以看到內部有支援 JSR-330 風格的 injection 功能，於是好奇心爆發，突然想知道他是在哪做的！身為一個熱愛 Gradle 的阿宅，隨時有 source code 在手邊是在正常不過的事了！立馬找一下哪些檔案會透過 reflection 使用它：

```
qty:src qrtt1$ grep -r "Inject.class" *
core/org/gradle/api/internal/AbstractClassGenerator.java:            if (method.getAnnotation(Inject.class) != null) {
core/org/gradle/api/internal/AbstractClassGenerator.java:            if (getters.add(method) && method.getAnnotation(Inject.class) != null) {
core/org/gradle/api/internal/DependencyInjectingInstantiator.java:            if (constructor.getAnnotation(Inject.class) != null) {
```


AbstractClassGenerator 看起來是某種自動產生 Class 的工具先不理它。目標很明顯，應該就是 DependencyInjectingInstantiator 了！
它實作 Instantiator，而建構子參數吃一個 ServiceRegistry 看來做 Depdendency Injection 的角色都到齊了！

```java
public class DependencyInjectingInstantiator implements Instantiator {
    private final ServiceRegistry services;

    public DependencyInjectingInstantiator(ServiceRegistry services) {
        this.services = services;
    }
    
    /// ...
}
```

## @Inject

對於 `@Inject` 識別的實作為 [DependencyInjectingInstantiator](https://github.com/gradle/gradle/blob/REL_2.12/subprojects/core/src/main/groovy/org/gradle/api/internal/DependencyInjectingInstantiator.java)，在 Source Code 內跟它有關的 class 有：

```
qty:src qrtt1$ grep -r DependencyInjectingInstantiator *| sed 's/.java.*/.java/g'|sort|uniq
core/org/gradle/api/internal/DependencyInjectingInstantiator.java
core/org/gradle/internal/service/scopes/GradleScopeServices.java
core/org/gradle/internal/service/scopes/ProjectScopeServices.java
core/org/gradle/internal/service/scopes/SettingsScopeServices.java
```

在這些 `*ScopeServices` 內，與它相依的類別是：

* [DefaultPluginManager](https://github.com/gradle/gradle/blob/REL_2.12/subprojects/core/src/main/groovy/org/gradle/api/internal/plugins/DefaultPluginManager.java)
* ITaskFactory

## PluginManager

PluginManager 在引用 Plugin 時會負責建立 Plugin 的 instance，在 Script Plugin 或 Standalone Plugin 我們會這麼寫：

```java
project.getPluginManager().apply(JavaPlugin.class);
```

或是你在 Build Script 裡這麼寫：

```groovy
apply plugin: 'java'
```

這二個寫法是最終都會對應到某個 Plugin 的 Class，在 PluginManager 內透過 Instantiator（它的實作實際上就是 DependencyInjectingInstantiator）建出新的 instance，它的實作在 [instantiatePlugin 方法](https://github.com/gradle/gradle/blob/REL_2.12/subprojects/core/src/main/groovy/org/gradle/api/internal/plugins/DefaultPluginManager.java#L57)：

```java
private <T> T instantiatePlugin(Class<T> type) {
    try {
        return instantiator.newInstance(type);
    } catch (ObjectInstantiationException e) {
        throw new PluginInstantiationException(String.format("Could not create plugin of type '%s'.", type.getSimpleName()), e.getCause());
    }
}
```

看來 injection 的地點是發生在 Instantiator 內部。

## DependencyInjectingInstantiator


```
public <T> T newInstance(Class<? extends T> type, Object... parameters) {
    try {
        validateType(type);
        Constructor<?> constructor = selectConstructor(type);
        constructor.setAccessible(true);
        Object[] resolvedParameters = convertParameters(type, constructor, parameters);
        try {
            return type.cast(constructor.newInstance(resolvedParameters));
        } catch (InvocationTargetException e) {
            throw e.getCause();
        }
    } catch (Throwable e) {
        throw new ObjectInstantiationException(type, e);
    }
}
```

追入 DependencyInjectingInstantiator 內後，會發現使用它的幾個前提：

### validateType

由 [validateType()](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/DependencyInjectingInstantiator.java#L120) 能知：

1. `@Inject` 它不能用在 interface、enum、annotation 之上。合理的 precondition！
2. `@Inject` 能用在 inner class，但必需是 static 的 inner class
3. `@Inject` 不能用在抽象類別。（反正也無法實體化）

### selectConstructor

由 [selectConstructor()](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/DependencyInjectingInstantiator.java#L82) 可知：

1. `@Inject` 只用在建構子
1. 目前的 type 可以有多個建構子，但只能有一個標上 `@Inject`

### convertParameters

實際做相依性注入的動作是由 [convertParameters()](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/DependencyInjectingInstantiator.java#L57) 執行的，它發生在呼叫建構子之前，透過這個方法它由 ServiceRegistry 查出對應參數的物件：

```java
private <T> Object[] convertParameters(Class<T> type, Constructor<?> match, Object[] parameters) {
    Class<?>[] parameterTypes = match.getParameterTypes();
    if (parameterTypes.length < parameters.length) {
        throw new IllegalArgumentException(String.format("Too many parameters provided for constructor for class %s. Expected %s, received %s.", type.getName(), parameterTypes.length, parameters.length));
    }
    Object[] resolvedParameters = new Object[parameterTypes.length];
    int pos = 0;
    for (int i = 0; i < resolvedParameters.length; i++) {
        Class<?> targetType = parameterTypes[i];
        if (targetType.isPrimitive()) {
            targetType = JavaReflectionUtil.getWrapperTypeForPrimitiveType(targetType);
        }
        if (pos < parameters.length && targetType.isInstance(parameters[pos])) {
            resolvedParameters[i] = parameters[pos];
            pos++;
        } else {
            resolvedParameters[i] = services.get(match.getGenericParameterTypes()[i]);
        }
    }
    if (pos != parameters.length) {
        throw new IllegalArgumentException(String.format("Unexpected parameter provided for constructor for class %s.", type.getName()));
    }
    return resolvedParameters;
}
```

看到這就踏實了許多，終於知道它實作 `@Inject` 的方法了！


## ITaskFactory

在另一條線索的 `ProjectScopeServices.createTaskFactory()`：

``` java
protected ITaskFactory createTaskFactory(ITaskFactory parentFactory) {
    return parentFactory.createChild(project, new ClassGeneratorBackedInstantiator(get(ClassGenerator.class), new DependencyInjectingInstantiator(this)));
}
```

可以看得出來，在同一個類別內並有人呼叫這個方法，在 ProjectScopeServices 不是抽象類別與方法屬於 protected 權限的前提下，能呼叫它的會是 Sub Class 或是同 package 的 Class。
進一步查一下 ProjectScopeServices 另外出現在同一個 package 的 GradleScopeServices 類別內：

```
qty:src qrtt1$ grep -r ProjectScopeServices *
core/org/gradle/internal/service/scopes/GradleScopeServices.java:                    ProjectScopeServices projectScopeServices = new ProjectScopeServices(services, (ProjectInternal) domainObject);
core/org/gradle/internal/service/scopes/ProjectScopeServices.java:public class ProjectScopeServices extends DefaultServiceRegistry {
core/org/gradle/internal/service/scopes/ProjectScopeServices.java:    public ProjectScopeServices(final ServiceRegistry parent, final ProjectInternal project) {
```

可是在 GradleScopeServices 卻沒有人呼叫到這個方法，而整個專案也沒有人呼叫。只能先懷疑這是改版後的遺跡尚未清除：

```
qty:src qrtt1$ grep -r createTaskFactory *
core/org/gradle/internal/service/scopes/ProjectScopeServices.java:    protected ITaskFactory createTaskFactory(ITaskFactory parentFactory) {
```

那麼可以換一種想法去 trace 它，找出實作它的類別就行了：

```
qty:src qrtt1$ grep -r ITaskFactory * | grep impl
core/org/gradle/api/internal/project/taskfactory/AnnotationProcessingTaskFactory.java:public class AnnotationProcessingTaskFactory implements ITaskFactory {
core/org/gradle/api/internal/project/taskfactory/DependencyAutoWireTaskFactory.java:public class DependencyAutoWireTaskFactory implements ITaskFactory {
core/org/gradle/api/internal/project/taskfactory/TaskFactory.java:public class TaskFactory implements ITaskFactory {
```

運氣不錯，查出來只有三個類別，那麼哪一個會是我們需要研究的呢？稍為看一下它們的實作就會發現，[TaskFactory](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/project/taskfactory/TaskFactory.java) 類別才是本體，而 [DependencyAutoWireTaskFactory](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/project/taskfactory/DependencyAutoWireTaskFactory.java) 與 [AnnotationProcessingTaskFactory](https://github.com/gradle/gradle/blob/REL_2.11/subprojects/core/src/main/groovy/org/gradle/api/internal/project/taskfactory/AnnotationProcessingTaskFactory.java) 都是裝飾者，因為它們在建構子都必需包含一個 ITaskFactory 物件，而方法主要的實作都是包裝本體之用。

```java
public <S extends TaskInternal> S create(String name, final Class<S> type) {
    if (!Task.class.isAssignableFrom(type)) {
        throw new InvalidUserDataException(String.format(
                "Cannot create task of type '%s' as it does not implement the Task interface.",
                type.getSimpleName()));
    }

    final Class<? extends Task> generatedType;
    if (type.isAssignableFrom(DefaultTask.class)) {
        generatedType = generator.generate(DefaultTask.class);
    } else {
        generatedType = generator.generate(type);
    }

    return type.cast(AbstractTask.injectIntoNewInstance(project, name, new Callable<Task>() {
        public Task call() throws Exception {
            try {
                return instantiator.newInstance(generatedType);
            } catch (ObjectInstantiationException e) {
                throw new TaskInstantiationException(String.format("Could not create task of type '%s'.", type.getSimpleName()),
                        e.getCause());
            }
        }
    }));
}
```

我們再次看到，就明白它是怎麼一回事：

```java
instantiator.newInstance(...)
```
