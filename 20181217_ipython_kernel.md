## jupyter

有時為了展示不同的環境，我們會需要建立新的 kernel，特別是針對不同專案的 python venv 建立。

可以在 venv 內，先安裝 `ipykernel` 並使用 `ipython` 指令安裝 kernel

```
pip install ipykernel
ipython kernel install --user --name=my-sandbox
```


可以使用下列指令查詢 kernel

```
qty:~ qrtt1$ jupyter kernelspec list
Available kernels:
  abc        /Users/qrtt1/Library/Jupyter/kernels/abc
  xxxyyy     /Users/qrtt1/Library/Jupyter/kernels/xxxyyy
```

若不再需要這個 kernel 時，那就把它的目錄刪掉就行了
