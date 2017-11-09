
## 設定使用者 SSH PublicKey

```groovy
def username = 'your-account'
def user = Jenkins.instance.getUser(username)
def property = user.getProperty(Class.forName('org.jenkinsci.main.modules.cli.auth.ssh.UserPropertyImpl'))
property.authorizedKeys='ssh-rsa ....'
user.save(property)
```
