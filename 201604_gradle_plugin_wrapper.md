# 包裝 Gradle Plugin 的 Plugin

我們能在 [Gradle plugins](https://plugins.gradle.org/) 找到許多好用的 Plugin，不同的 Plugin 替你解決不用領域的問題，而它設計的觀點與風格具有蠻大的差異，當然包含使用上的難易程度，文件齊不齊全都會影響到 Plugin 上手的成本。

當你找到一個能處理當前問題的 Plugin 是開心的，但卻可能因為複雜的使用方式卻令人感到挫折，甚至得放棄它，重新找找是否有其他 Plugin 能解決同樣的問題。也可能就此放棄，選擇自行實作簡易的 Task 與適當的 DSL。

## Wrapper Plugin

最近在使用 [gradle-bintray-plugin](https://github.com/bintray/gradle-bintray-plugin) 發現它要填非常多的欄位，即使它有設計一套完整的 DSL 出來，但對剛認識 bintray 服務的人可能不是那麼方便，再加上他提供三種不同的 artifacts 定義方法更加使得新手困惑。

下面是個『完整』的 DSL 範例，實際上使用時不會真的每個都填上，但可看它真的挺有彈性 :)

```groovy
bintray {
    user = 'bintray_user'
    key = 'bintray_api_key'

    configurations = ['deployables'] //When uploading configuration files
    // - OR -
    publications = ['mavenStuff'] //When uploading Maven-based publication files
    // - AND/OR -
    filesSpec { //When uploading any arbitrary files ('filesSpec' is a standard Gradle CopySpec)
        from 'arbitrary-files'
        into 'standalone_files/level1'
        rename '(.+)\\.(.+)', '$1-suffix.$2'
    }
    dryRun = false //Whether to run this as dry-run, without deploying
    publish = true //If version should be auto published after an upload
    //Package configuration. The plugin will use the repo and name properties to check if the package already exists. In that case, there's no need to configure the other package properties (like userOrg, desc, etc).
    pkg {
        repo = 'myrepo'
        name = 'mypkg'
        userOrg = 'myorg' //An optional organization name when the repo belongs to one of the user's orgs
        desc = 'what a fantastic package indeed!'
        websiteUrl = 'https://github.com/bintray/gradle-bintray-plugin'
        issueTrackerUrl = 'https://github.com/bintray/gradle-bintray-plugin/issues'
        vcsUrl = 'https://github.com/bintray/gradle-bintray-plugin.git'
        licenses = ['Apache-2.0']
        labels = ['gear', 'gore', 'gorilla']
        publicDownloadNumbers = true
        attributes= ['a': ['ay1', 'ay2'], 'b': ['bee'], c: 'cee'] //Optional package-level attributes

        githubRepo = 'bintray/gradle-bintray-plugin' //Optional Github repository
        githubReleaseNotesFile = 'README.md' //Optional Github readme file

        //Optional version descriptor
        version {
            name = '1.3-Final' //Bintray logical version name
            desc = //Optional - Version-specific description'
            released  = //Optional - Date of the version release. 2 possible values: date in the format of 'yyyy-MM-dd'T'HH:mm:ss.SSSZZ' OR a java.util.Date instance
            vcsTag = '1.3.0'
            attributes = ['gradle-plugin': 'com.use.less:com.use.less.gradle:gradle-useless-plugin'] //Optional version-level attributes
            //Optional configuration for GPG signing
            gpg {
                sign = true //Determines whether to GPG sign the files. The default is false
                passphrase = 'passphrase' //Optional. The passphrase for GPG signing'
            }
            //Optional configuration for Maven Central sync of the version
            mavenCentralSync {
                sync = true //Optional (true by default). Determines whether to sync the version to Maven Central.
                user = 'userToken' //OSS user token
                password = 'paasword' //OSS user password
                close = '1' //Optional property. By default the staging repository is closed and artifacts are released to Maven Central. You can optionally turn this behaviour off (by puting 0 as value) and release the version manually.
            }            
        }
    }
}
```

是否有個簡單一點的方法呢？能把使用 gradle-bintray-plugin 當作是一種進階的選項，而需要一個簡化版的方式來達成同樣的目標。確實有人寫了另一個 [bintray-release plugin](https://github.com/novoda/bintray-release) 把 gradle-bintray-plugin 重新包裝起來，它提供了單層的 publish closure 設定必要選項：

```
publish {
    userOrg = 'novoda'
    groupId = 'com.novoda'
    artifactId = 'bintray-release'
    publishVersion = '0.3.4'
    desc = 'Oh hi, this is a nice description for a project, right?'
    website = 'https://github.com/novoda/bintray-release'
}
```

單純以這組設定來說，要上傳至 bintray 並能同步至 jcenter 已經夠用了，即使比對『真實世界』的需求，那再加個 License 宣告與選擇 bintray 上的 Maven-Repo 名稱只多了二行設定。

[bintray-release plugin](https://github.com/novoda/bintray-release) 所做的事情，就只對 [gradle-bintray-plugin](https://github.com/bintray/gradle-bintray-plugin) 進行包裝並提供一個較為簡化的 DSL 出來（也就是 `publish {}`）。


## Implementation

實作 Wrapper Plugin 與一般的 Plugin 沒什麼差別，只是把原本 Plugin 需要填寫的部分隱藏至 Wrapper Plugin 內而已。

以命名慣例來說，我們能尋找檔名含 **Plugin** 字串的檔案，在這專案僅有 [ReleasePlugin.groovy](https://github.com/novoda/bintray-release/blob/0.3.5/core/src/main/groovy/com/novoda/gradle/release/ReleasePlugin.groovy)，它的 apply 方法是這麼寫的：

```groovy
void apply(Project project) {
    PublishExtension extension = project.extensions.create('publish', PublishExtension)
    project.afterEvaluate {
        project.apply([plugin: 'maven-publish'])
        attachArtifacts(project)
        new BintrayPlugin().apply(project)
        new BintrayConfiguration(extension).configure(project)
    }
}
```

這裡就能看到 `publish {}` 被建立出來，若想知道 PublishExtension 的內容可以追入，而在 `afterEvaluate {}` 內是它實際做事的地方，它這主要做二件事：

1. 引用 mave-publish plugin，並 [建立適當的 MavenPublication](https://github.com/novoda/bintray-release/blob/0.3.5/core/src/main/groovy/com/novoda/gradle/release/ReleasePlugin.groovy#L20)（一組 MavenPublication 就是一個待上傳的 library）

    ```groovy
    project.apply([plugin: 'maven-publish'])
    attachArtifacts(project)
    ```

1. 引用 [gradle-bintray-plugin](https://github.com/bintray/gradle-bintray-plugin)，並且 [幫使用者填寫 DSL](https://github.com/novoda/bintray-release/blob/0.3.5/core/src/main/groovy/com/novoda/gradle/release/BintrayConfiguration.groovy#L13)。

    ```groovy
    new BintrayPlugin().apply(project)
    new BintrayConfiguration(extension).configure(project)
    ```

PS. 直接 `new` 既有的 Plugin 的方式產生 instance 不太建議，在它的實作如果使用到 JSR-330 `@Inject` 的部分就沒法正常運作，只是目前這例子，恰好沒問題罷了，建議自行實作時寫成這樣：


```groovy
plugin.apply(BintrayPlugin.class)
```

### BintrayConfiguration

BintrayConfiguration 是產生設定的主要地方，它建構子吃使用者填的 `publish {}` 並呼叫 [configure](https://github.com/novoda/bintray-release/blob/0.3.5/core/src/main/groovy/com/novoda/gradle/release/BintrayConfiguration.groovy#L13) 方法把 project 物件丟進去：

```groovy
void configure(Project project) {
    initDefaults()
    deriveDefaultsFromProject(project)

    PropertyFinder propertyFinder = new PropertyFinder(project, extension)

    project.bintray {
        user = propertyFinder.getBintrayUser()
        key = propertyFinder.getBintrayKey()
        publish = extension.autoPublish
        dryRun = propertyFinder.getDryRun()

        publications = extension.publications ?: project.plugins.hasPlugin('com.android.library') ? project.android.libraryVariants.collect { it.name } : [ 'maven' ]

        pkg {
            repo = extension.repoName
            userOrg = extension.userOrg
            name = extension.uploadName
            desc = extension.desc ?: extension.description
            websiteUrl = extension.website
            issueTrackerUrl = extension.issueTracker
            vcsUrl = extension.repository

            licenses = extension.licences
            version {
                name = propertyFinder.getPublishVersion()
                attributes = extension.versionAttributes
            }
        }
    }
    project.tasks.bintrayUpload.mustRunAfter(project.tasks.uploadArchives)
}
```

看到這有沒有很熟悉的感覺，跟 [gradle-bintray-plugin](https://github.com/bintray/gradle-bintray-plugin) 讓使用者填的是同一組東西，只是它額外幫你自動區分專案類型是一般的 Java 專案或者是 Android Library 專案。


## Plugin 風格

之所以有 Wrapper Plugin 的出現是為了更簡化的使用方法，更容易使人上手。當然也關係到 Gradle Plugin 風格的設計。有些 Plugin 是以提供 Task Type 為主的，讓你自行實作相關的 Task 以符合你的需求，
但這種風格通常沒有比提供 DSL 透過 **設定** 的方法改變專案的編譯功能來得方便。在撰寫上也不太好上手。

以 [gradle-aws-plugin](https://github.com/classmethod/gradle-aws-plugin) 為例，它的設計風格是將 Amazon Web Service 的功能做出一組一組的 Task Type。若是運用這個 Plugin 來執行：

1. 上傳 lambda package file 至 S3
1. 使用 S3 上的 lambda package file 註冊若干組 Lambda Function

可以這麼寫：

```groovy
apply plugin: "jp.classmethod.aws.s3"
apply plugin: "jp.classmethod.aws.lambda"

aws {
    profileName = 'qty'
    region = 'ap-northeast-1'
}

import jp.classmethod.aws.gradle.s3.AmazonS3FileUploadTask
task uploadLambdaPackage(type: AmazonS3FileUploadTask, dependsOn: buildZip) {
    file file("build/distributions/${project.name}.zip")
    bucketName 'qty.lambda'
    key 'def2.zip'
    overwrite true
}

import jp.classmethod.aws.gradle.lambda.AWSLambdaUpdateFunctionCodeTask
import jp.classmethod.aws.gradle.lambda.S3File
['HelloLambda', 'VideoPreviewTaskGenerator', 'VideoPreviewGenerator'].each { name ->
    task "updateLambdaFunction$name" (type: AWSLambdaUpdateFunctionCodeTask, dependsOn: uploadLambdaPackage) {
        description = "Update labmda function $name"
        functionName = name
        s3File = new S3File()
        s3File.bucketName = 'qty.lambda'
        s3File.key = 'def2.zip'
    }
}
```

`aws{}` 是它提供的主要 DSL 設計，用來設定一些服務的帳號與區域的訊息，而要建立新的 Task 來使用必需先做一些 `import` 類別的動作（目前 Gradle 似乎還沒有讓 Plugin 下的類能 auto import 的功能）。因此在撰寫新的 Task 時，得先查一下文件或原始碼得 import 哪些類別，再來查看 Task Type 有哪些 property 能填寫或是 setter 能呼叫，然後開始填入你的參數。


## 風格調整

若在我們的專案只是想針對 Lambda Function 更新的問題，似乎可以做個 Wrapper Plugin 把它重包即可。目前沒有實作，單純能『想像』一下怎麼設計比較好用，例如：提供一組 `lambda {}` DSL

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

以上是在我們『想像』中的 Wrapper 會提供的，針對 Lambda Function 更新的功能所做，在語意上更為具焦並且自動產生原本『手工』加入的 Task，也無需接觸到實際的類別引用的細節。

PS. 雖然只是構想，但有時間的話生一隻出來用應該挺好的。
