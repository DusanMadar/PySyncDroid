# PySyncDroid
PySyncDroid is a Python 2.7 powered CLI tool providing a simple way to synchronize an Android device connected to a Linux PC via MTP over USB.

## System requirements
PySyncDroid leverages `gvfs` and `mtp`. Make sure you have both installed on your system. `pytest` is required for running tests.

### gvfs
gvfs *should* be installed by default. This applies for recent (14.04 or later) Ubuntu based systems.

### mtp
Run the following command in your terminal to add necesseary mtp suport.
``` bash
sudo apt-get install mtpfs mtp-tools
```

## Installation
Run following commands to download, extract and install PySyncDroid.
``` bash
cd ~/Downloads
wget https://github.com/DusanMadar/PySyncDroid/archive/master.zip -O PySyncDroid.zip
unzip PySyncDroid.zip
cd PySyncDroid-master/
python setup.py install
```
