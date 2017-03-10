### AWS Lmabda AMI

查 `ap-northeast-1` 的 Lambda Image Id

```
aws ec2 describe-images --cli-input-json \
'{"Filters":[{"Name":"name", "Values":["amzn-ami-hvm-2016.03.3.x86_64-gp2"]}]}' \
--region ap-northeast-1 | \
jq -r .Images[0].ImageId
```

* ami 的名稱在文件寫是 [amzn-ami-hvm-2016.03.3.x86_64-gp2](http://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html)。(至於何給名稱呢？我想應該是每 region 的 image id 不會一樣，然後寫 image id 又很容意 out of dated 而需要更新文件，只好留個名稱讓大家自己查吧)
