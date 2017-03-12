### AWS Lmabda AMI

查 `ap-northeast-1` 的 Lambda Image Id

```
aws ec2 describe-images --cli-input-json \
'{"Filters":[{"Name":"name", "Values":["amzn-ami-hvm-2016.03.3.x86_64-gp2"]}]}' \
--region ap-northeast-1 | \
jq -r .Images[0].ImageId
```

* ami 的名稱在文件寫是 [amzn-ami-hvm-2016.03.3.x86_64-gp2](http://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html)。(至於何給名稱呢？我想應該是每 region 的 image id 不會一樣，然後寫 image id 又很容意 out of dated 而需要更新文件，只好留個名稱讓大家自己查吧)

### Gradle Rule Models

在 gradle 2.3 下有這些預設的 model 可以使用 :)

```
qty:src qrtt1$ grep -r 'ModelReference.of' *
core/org/gradle/api/internal/project/AbstractProject.java:                ModelCreators.bridgedInstance(ModelReference.of("serviceRegistry", ServiceRegistry.class), services)
core/org/gradle/api/internal/project/AbstractProject.java:                ModelCreators.unmanagedInstance(ModelReference.of("buildDir", File.class), new Factory<File>() {
core/org/gradle/api/internal/project/AbstractProject.java:                ModelCreators.bridgedInstance(ModelReference.of("projectIdentifier", ProjectIdentifier.class), this)
core/org/gradle/api/internal/project/AbstractProject.java:                ModelCreators.unmanagedInstance(ModelReference.of("extensions", ExtensionContainer.class), new Factory<ExtensionContainer>() {
core/org/gradle/model/collection/internal/PolymorphicDomainObjectContainerModelProjection.java:                        ModelReference.of(modelPath, containerType),
model-core/org/gradle/model/internal/inspect/DefaultMethodRuleDefinition.java:        return ModelReference.of(path == null ? null : validPath(path), cast, String.format("parameter %s", i + 1));
model-core/org/gradle/model/internal/inspect/ManagedModelCreationRuleDefinitionHandler.java:        return ModelCreators.of(ModelReference.of(modelPath, managedType), transformer)
model-core/org/gradle/model/internal/inspect/ManagedModelInitializer.java:        return ModelCreators.of(ModelReference.of(path, schema.getType()), new ManagedModelInitializer<T>(descriptor, schema, modelInstantiator, schemaStore, proxyFactory, initializer))
model-core/org/gradle/model/internal/inspect/UnmanagedModelCreationRuleDefinitionHandler.java:        modelRegistry.create(ModelCreators.of(ModelReference.of(ModelPath.path(modelName), returnType), transformer)
platform-base/org/gradle/language/base/plugins/ComponentModelBasePlugin.java:                ModelCreators.bridgedInstance(ModelReference.of("components", DefaultComponentSpecContainer.class), components)
platform-base/org/gradle/language/base/plugins/LanguageBasePlugin.java:                ModelCreators.bridgedInstance(ModelReference.of("binaries", BinaryContainer.class), binaries)
platform-base/org/gradle/language/base/plugins/LanguageBasePlugin.java:                        .inputs(Collections.singletonList(ModelReference.of(ExtensionContainer.class)))
platform-base/org/gradle/platform/base/internal/registry/BinaryTasksRuleDefinitionHandler.java:            final ModelReference<TaskContainer> tasks = ModelReference.of(ModelPath.path("tasks"), new ModelType<TaskContainer>() {
platform-base/org/gradle/platform/base/internal/registry/BinaryTasksRuleDefinitionHandler.java:            super(subject, binaryType, ruleDefinition, ModelReference.of("binaries", BinaryContainer.class));
platform-base/org/gradle/platform/base/internal/registry/ComponentBinariesRuleDefinitionHandler.java:            final ModelReference<BinaryContainer> subject = ModelReference.of(ModelPath.path("binaries"), new ModelType<BinaryContainer>() {
platform-base/org/gradle/platform/base/internal/registry/ComponentBinariesRuleDefinitionHandler.java:            super(subject, componentType, ruleDefinition, ModelReference.of(ComponentSpecContainer.class));
platform-base/org/gradle/platform/base/internal/registry/ComponentModelRuleDefinitionHandler.java:            subject = ModelReference.of("extensions", ExtensionContainer.class);
platform-base/org/gradle/platform/base/internal/registry/ComponentModelRuleDefinitionHandler.java:            inputs = ImmutableList.<ModelReference<?>>of(ModelReference.of(ProjectIdentifier.class));
qty:src qrtt1$
```
