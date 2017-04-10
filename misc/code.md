
### jq 製作 ansible inventory

用 jq 來生 gce 的 ansible inventory

```
#!/bin/env sh
gcloud compute instances list  --regexp .*bott.* --format json \
    | jq '{"bott":{"vars": {"ansible_ssh_user":"my", "ansible_ssh_private_key_file":"/home/bott/.ssh/my.pem"}, "hosts": [.[].networkInterfaces[].accessConfigs[].natIP]}}'
exit 0
```

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

### AWS iam-roles

* [Delegating API Access to AWS Services Using IAM Roles](https://aws.amazon.com/tw/blogs/aws/delegating-api-access-to-aws-services-using-iam-roles/)
* [kaif: 原來 aws java sdk 已經有自動 renew AssumeRoleSession 的功能](https://kaif.io/z/programming/debates/eMepQ4JKw1)

```
心血來潮想在新專案使用 STS 的 assumeRole，翻了一下手冊相關的教學 Making Requests Using IAM User Temporary Credentials - AWS SDK for Java1 看起來動作都挺「手工」的，這樣還要另外開一個 TimerTask 來更新 session，於是立馬動手寫了個簡單的版本 STSAssumeRoleAWSCredentialsProvider2，弄好後看起來運作大致正常，想回 aws java sdk 的 github 問看看能不能整合，就發現原來已經一模一樣的東西了 !!!

因為曾有人發 bug report STSAssumeRoleSessionCredentialsProvider does not support passing an external id3 順便這名，找到了它： STSAssumeRoleSessionCredentialsProvider4。一週的第一天，就在浪費青春了。

所以，該發另一個 bug 去靠北手冊太舊了 orz

1. http://docs.aws.amazon.com/AmazonS3/latest/dev/AuthUsingTempSessionTokenJava.html
2. https://gist.github.com/qrtt1/d6046802f5bb10630aa9
3. https://github.com/aws/aws-sdk-java/issues/290
4. https://github.com/aws/aws-sdk-java/blob/master/aws-java-sdk-sts/src/main/java/com/amazonaws/auth/STSAssumeRoleSessionCredentialsProvider.java
```

### AWSCredentialsProviderChain

[kaif: How a bug in Visual Studio 2015 exposed my source code on GitHub and cost me $6,500 in a few hours](https://kaif.io/z/compiling/debates/gGmBnjUmoT)

```java
AWSCredentialsProvider provider = new AWSCredentialsProviderChain(
  new ProfileCredentialsProvider("devProfile"),
  new EnvironmentVariableCredentialsProvider(), 
  new SystemPropertiesCredentialsProvider(),
  new ProfileCredentialsProvider(), 
  new InstanceProfileCredentialsProvider());
```
