# Conda 與多版本 Python

Conda 是目前最廣泛使用的 Python 安裝與套件管理工具，特別是要裝多種不同的 Python 版本時它會特別的可靠。

即使，你的系統中預套自帶了 Python，也不要輕易去變更它的版本，應該要用 Conda 裝一套把開發與日常使用分別開來，才不會想重建開發環境時，也把系統弄壞了。

## 建立參考流程

使用 `conda create` 建立新的環境，並指定 Python 版本：

```
(base) (⎈ |microk8s:default)➜  ~ conda create --name py311 python=3.11
Collecting package metadata (current_repodata.json): done
Solving environment: done


==> WARNING: A newer version of conda exists. <==
  current version: 22.9.0
  latest version: 22.11.1

Please update conda by running

    $ conda update -n base -c conda-forge conda



## Package Plan ##

  environment location: /Users/qrtt1/miniforge3/envs/py311

  added / updated specs:
    - python=3.11


The following packages will be downloaded:

    package                    |            build
    ---------------------------|-----------------
    ca-certificates-2022.12.7  |       h4653dfc_0         142 KB  conda-forge
    libsqlite-3.40.0           |       h76d750c_0         804 KB  conda-forge
    openssl-3.0.7              |       h03a7124_1         2.0 MB  conda-forge
    python-3.11.0              |h93c2e33_0_cpython        14.9 MB  conda-forge
    setuptools-65.6.3          |     pyhd8ed1ab_0         619 KB  conda-forge
    tzdata-2022g               |       h191b570_0         106 KB  conda-forge
    ------------------------------------------------------------
                                           Total:        18.5 MB

The following NEW packages will be INSTALLED:

  bzip2              conda-forge/osx-arm64::bzip2-1.0.8-h3422bc3_4 None
  ca-certificates    conda-forge/osx-arm64::ca-certificates-2022.12.7-h4653dfc_0 None
  libffi             conda-forge/osx-arm64::libffi-3.4.2-h3422bc3_5 None
  libsqlite          conda-forge/osx-arm64::libsqlite-3.40.0-h76d750c_0 None
  libzlib            conda-forge/osx-arm64::libzlib-1.2.13-h03a7124_4 None
  ncurses            conda-forge/osx-arm64::ncurses-6.3-h07bb92c_1 None
  openssl            conda-forge/osx-arm64::openssl-3.0.7-h03a7124_1 None
  pip                conda-forge/noarch::pip-22.3.1-pyhd8ed1ab_0 None
  python             conda-forge/osx-arm64::python-3.11.0-h93c2e33_0_cpython None
  readline           conda-forge/osx-arm64::readline-8.1.2-h46ed386_0 None
  setuptools         conda-forge/noarch::setuptools-65.6.3-pyhd8ed1ab_0 None
  tk                 conda-forge/osx-arm64::tk-8.6.12-he1e0b03_0 None
  tzdata             conda-forge/noarch::tzdata-2022g-h191b570_0 None
  wheel              conda-forge/noarch::wheel-0.38.4-pyhd8ed1ab_0 None
  xz                 conda-forge/osx-arm64::xz-5.2.6-h57fd34a_0 None


Proceed ([y]/n)? y
```

按下同意後繼續：

```
Downloading and Extracting Packages
python-3.11.0        | 14.9 MB   | ################################################################################################################################################################################################################################### | 100%
tzdata-2022g         | 106 KB    | ################################################################################################################################################################################################################################### | 100%
ca-certificates-2022 | 142 KB    | ################################################################################################################################################################################################################################### | 100%
libsqlite-3.40.0     | 804 KB    | ################################################################################################################################################################################################################################### | 100%
setuptools-65.6.3    | 619 KB    | ################################################################################################################################################################################################################################### | 100%
openssl-3.0.7        | 2.0 MB    | ################################################################################################################################################################################################################################### | 100%
Preparing transaction: done
Verifying transaction: done
Executing transaction: done
#
# To activate this environment, use
#
#     $ conda activate py311
#
# To deactivate an active environment, use
#
#     $ conda deactivate

Retrieving notices: ...working... done
(base) (⎈ |microk8s:default)➜  ~ conda env list
# conda environments:
#
base                  *  /Users/qrtt1/miniforge3
osx-arm64                /Users/qrtt1/miniforge3/envs/osx-arm64
py311                    /Users/qrtt1/miniforge3/envs/py311
py38                     /Users/qrtt1/miniforge3/envs/py38
                         /Users/qrtt1/opt/anaconda3/envs/osx-arm64
```

## 驗證版本與路徑

由於，我們沒有變更預設的 env，可以透過 `activate` 來臨時切換它：

```
(base) (⎈ |microk8s:default)➜  ~ conda activate py311
```

檢查一下版號與直譯器路徑：

```
(py311) (⎈ |microk8s:default)➜  ~ command -v python
/Users/qrtt1/miniforge3/envs/py311/bin/python
(py311) (⎈ |microk8s:default)➜  ~ /Users/qrtt1/miniforge3/envs/py311/bin/python -V
Python 3.11.0
(py311) (⎈ |microk8s:default)➜  ~
```

若是 Windows 使用者，沒有 `command` 可以查，應該也有對應的 PowerShell 指令。較簡單的方式，是看預設的 Python Path：

```bash
python -c "import sys; print(sys.path)"
['', '/Users/qrtt1/miniforge3/envs/py311/lib/python311.zip', '/Users/qrtt1/miniforge3/envs/py311/lib/python3.11', '/Users/qrtt1/miniforge3/envs/py311/lib/python3.11/lib-dynload', '/Users/qrtt1/miniforge3/envs/py311/lib/python3.11/site-packages']
```

## 後續設定

1. 目前是以 `Python 3.11` 為例，但你可以自己指定需要的版本。
2. 無論使用哪一種 IDE/Editor，只要你的 Python interpreter 有指到對的路徑就會是對的版本

比較有潔癖一點的人，也許會想替每一個專案建立獨立的 conda env，但這其實不是必要的。只要 Python 版本符合需求，可以後續選用任一一種習慣的隔離方案：

* virtualenv
* poetry
* pyenv
